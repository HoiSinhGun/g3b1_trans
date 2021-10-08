from random import shuffle
from typing import Callable, Any

from telegram import ParseMode, Message

import tg_db
import trans.data
from config.model import TransConfig
from g3b1_cfg.tg_cfg import G3Ctx, g3_cmd_by
from g3b1_log.log import *
from g3b1_serv import utilities
from g3b1_ui.model import TgUIC
from generic_hdl import send_menu_keyboard
from icon import I_PREV, I_HINT, I_NEXT, I_ANSWER
from model import MenuIt, G3Command, Menu
from settings import read_setng, cu_setng
from subscribe.data import db as subscribe_db
from subscribe.serv.services import for_user
from tg_reply import cmd_err
from trans.data import ELE_TY_txt_seq_id, ELE_TY_tst_run_id
from trans.data import ENT_TY_tst_run, ENT_TY_txt_seq
from trans.data.enums import ActTy, Sus, LcPair
from trans.data.model import Txtlc, TxtlcOnym, TxtSeq, TxtSeqIt
from trans.serv.internal import *
from utilities import upd_extract_chat_user_id, str_uncapitalize

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def reg_user_if_new(chat_id: int, user_id: int):
    tg_db.externalize_chat_id(trans.data.BOT_BKEY_TRANS, chat_id)
    tg_db.externalize_user_id(trans.data.BOT_BKEY_TRANS, user_id)
    # db.ins_user_setting_default(user_id)


def fiby_txt_lc(text: str, lc: Lc) -> Txtlc:
    """Find text in DB"""
    # noinspection PyArgumentList
    return db.fiby_txt_lc(Txtlc(text, lc)).result


def find_or_ins_txtlc_with_txtlc2(txt: str, lc: Lc, lc2: Lc, translator=None) -> TxtlcMp:
    txt_mapping = find_txtlc_with_txtlc2(txt, lc, lc2, translator)
    if not txt_mapping.txtlc_src:
        # noinspection PyArgumentList
        txtlc = db.ins_txtlc(Txtlc(txt, lc)).result
        txt_mapping.txtlc_src = txtlc
    return txt_mapping


def find_txtlc_with_txtlc2(txt: str, lc: Lc, lc2: Lc, translator=None) -> TxtlcMp:
    """Find text in DB and if exist return it along with translation of translator for lc2"""
    txtlc_find = fiby_txt_lc(txt, lc)
    if not txtlc_find:
        # noinspection PyTypeChecker,PyArgumentList
        return TxtlcMp(None, None, lc2)
    txt_mapping: TxtlcMp = db.fin_txtlc_mp(txtlc_find, lc2, translator).result  # -> TxtLCMapping
    if not txt_mapping:
        # noinspection PyTypeChecker,PyArgumentList
        txt_mapping = TxtlcMp(txtlc_find, None, lc2)
    return txt_mapping


def txtlc_cp_txt(lc_pair: tuple[Lc, Lc], txt: str) -> list[TxtlcMp]:
    txtlc_li = db.txtlc_txt_cp(txt, lc_pair[0])
    txt_map_li: list[TxtlcMp] = []
    for txtlc in txtlc_li:
        txt_map: TxtlcMp = find_or_ins_translation(txtlc.txt, lc_pair).result
        txt_map_li.append(txt_map)
    return txt_map_li


def find_or_ins_translation(txt: str, lc_pair: Union[LcPair, tuple[Lc, Lc]]) -> G3Result[TxtlcMp]:
    """Return text and translation, if not exists, create them with Google"""
    if isinstance(lc_pair, tuple):
        lc_pair = LcPair.from_tup(lc_pair)
    lc = lc_pair.lc
    lc2 = lc_pair.lc2
    txtlc_mp = find_or_ins_txtlc_with_txtlc2(txt, lc, lc2)
    if txtlc_mp.txtlc_trg:
        return G3Result(0, txtlc_mp)

    # next: Google translate
    trg_txt, txtlc_mp.translator, txtlc_mp.score = TransConfig.translate_func(txt, lc.value, lc2.value)

    return set_trg_of_map_and_save(txtlc_mp, trg_txt)


def iup_translation(txtlc: Txtlc, txtlc2: Txtlc, translator: str, score: int = 80) -> G3Result:
    """Update or insert txtlc pair"""
    txt_mapping = find_or_ins_txtlc_with_txtlc2(txtlc.txt, txtlc.lc, txtlc2.lc, translator)
    if txt_mapping.txtlc_trg and txt_mapping.txtlc_trg.txt == txtlc2.txt \
            and txt_mapping.score == score:
        return G3Result(0, txt_mapping)
    txt_mapping.score = score
    txt_mapping.translator = translator

    return set_trg_of_map_and_save(txt_mapping, txtlc2.txt)


def set_trg_of_map_and_save(txt_mapping: TxtlcMp, txt) -> G3Result:
    txtlc_find = fiby_txt_lc(txt, txt_mapping.lc2)
    if not txtlc_find:
        # noinspection PyArgumentList
        txtlc_find = db.ins_txtlc(Txtlc(txt, txt_mapping.lc2)).result
    txt_mapping.txtlc_trg = txtlc_find
    g3r: G3Result = db.iup_txtlc_mp(txt_mapping)
    return g3r


def translate_google(text: str, lc_str, lc2_str) -> (str, str, int):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    import six
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()
    # text = text.lower()
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, source_language=lc_str, target_language=lc2_str)
    # noinspection PyTypeChecker
    txt_trans_str = result["translatedText"]
    return txt_trans_str, 'google', 10


def txt_seq_01(lc_pair: tuple[Lc, Lc], txt: str) -> TxtSeq:
    chat_id, user_id = upd_extract_chat_user_id()

    txt_seq: TxtSeq = db.fin_txt_seq(chat_id, txt)
    if not txt_seq:
        txt_seq = TxtSeq.new(chat_id, txt, lc_pair)

        txt_it_li = txt.split('|')
        src_txt = ''
        for idx, txt_it in enumerate(txt_it_li):
            src_txt += txt_it + ' '
            txtlc_mp: TxtlcMp = find_or_ins_translation(txt_it, lc_pair).result
            txt_seq.it_li.append(TxtSeqIt(txt_seq, txtlc_mp, idx + 1))
        src_txt = TxtSeq.output_format(src_txt)

        txt_seq.txtlc_mp = find_or_ins_translation(src_txt, lc_pair).result

        txt_seq = db.ins_txt_seq(txt_seq).result
    txt_seq: TxtSeq = db.sel_txt_seq(txt_seq.id_).result
    return txt_seq


def txt_seq_03(upd, txt_seq: TxtSeq):
    i_send_txtlc_mp(upd, txt_seq.txtlc_mp)
    i_send_txtlc_mp_li(upd, [it.txtlc_mp for it in txt_seq.it_li])


def conv_onym_str_li(src_txt: str, trg_txt: str) -> (list[str], list[str], list[str], list[str]):
    src_syn_li: list = []
    src_ant_li: list = []
    trg_syn_li: list = []
    trg_ant_li: list = []
    src_tup = (src_syn_li, src_ant_li)
    trg_tup = (trg_syn_li, trg_ant_li)
    tup_tup = (src_tup, trg_tup)

    src_split_li = src_txt.split(' = ')
    trg_split_li = []
    if trg_txt:
        trg_split_li = trg_txt.split(' = ')
    for is_trg, split_li in enumerate((src_split_li, trg_split_li)):
        syn_li = tup_tup[is_trg][0]
        ant_li = tup_tup[is_trg][1]
        if len(split_li) == 1:
            ant_split_li = split_li[0].split(' # ')
            syn_li.append(ant_split_li[0].strip())
            for ant in ant_split_li:
                ant_li.append(ant.strip())
        else:
            for idx, item in enumerate(split_li):
                ant_split_li = item.strip().split(' # ')
                syn_li.append(ant_split_li[0].strip())
                if idx == 0:
                    ant_li.append(ant_split_li[0].strip())
                if len(ant_split_li) > 1:
                    for ant in ant_split_li[1:]:
                        ant_li.append(ant.strip())
    if len(src_ant_li) == 1:
        src_ant_li.clear()
    if len(trg_ant_li) == 1:
        trg_ant_li.clear()
    return src_syn_li, src_ant_li, trg_syn_li, trg_ant_li


def onyms_strs_from_txt_maps(txt_map: TxtlcMp) -> (str, str):
    src_txtlc = txt_map.txtlc_src
    onym_tup = li_all_onym(src_txtlc)
    syn_str = ''
    ant_str = ''
    last_idx_of_tuple = len(onym_tup[0]) - 1
    for idx, onym in enumerate(onym_tup[0]):
        syn_str += onym.other_pair_ele(src_txtlc).txt
        if last_idx_of_tuple > idx:
            syn_str += ', '
    last_idx_of_tuple = len(onym_tup[1]) - 1
    for idx, onym in enumerate(onym_tup[1]):
        ant_str += onym.other_pair_ele(src_txtlc).txt
        if last_idx_of_tuple > idx:
            ant_str += ', '
    return syn_str, ant_str


def i_reply_str_from_txt_map_li_repl_ta(*p_li, **kw_p_li) -> str:
    reply_str = i_reply_str_from_txt_map_li(*p_li, **kw_p_li)
    # tôi
    reply_str = reply_str. \
        replace('tôi', 'anh').replace('Tôi', 'Anh'). \
        replace('bạn', 'em').replace('Bạn', 'Em')

    return reply_str


def i_reply_str_from_txt_map_li_v(*p_li, **kw_p_li) -> str:
    reply_str = i_reply_str_from_txt_map_li(*p_li, **kw_p_li, verbosity='v')
    return reply_str


def i_reply_str_from_txt_map_li_vb(*p_li, **kw_p_li) -> str:
    reply_str = i_reply_str_from_txt_map_li(*p_li, **kw_p_li, verbosity='b')
    return reply_str


def i_reply_str_from_txt_map_li_srcus(*p_li, **kw_p_li) -> str:
    reply_str = i_reply_str_from_txt_map_li(*p_li, **kw_p_li, verbosity='u')
    return reply_str


def i_reply_str_from_txt_map_li(user_id: int, idx_src_syn_last: int, lc: Lc, lc2: Lc, txt_map_li: list[TxtlcMp],
                                verbosity='') -> str:
    c = '='
    idx_all_last = len(txt_map_li) - 1
    src_str = ''
    trg_str = ''
    syn_str = ''
    ant_str = ''
    if len(txt_map_li) == 1:
        syn_str, ant_str = onyms_strs_from_txt_maps(txt_map_li[0])
    for idx, txt_map in enumerate(txt_map_li):
        src_str += txt_map.txtlc_src.txt
        trg_str += txt_map.txtlc_trg.txt
        if idx < idx_all_last:
            if idx >= idx_src_syn_last:
                c = '!'
            src_str += f' {c} '
            trg_str += f' {c} '
    if verbosity:
        if verbosity == 'v':
            reply_str = f'{bold(lc.value)}\n'
        elif verbosity == 'u':
            uname = subscribe_db.read_uname(user_id)
            reply_str = f'{bold(uname)}\n'
        else:
            reply_str = ''
        if verbosity in ['v', 'b']:
            reply_str += f'{src_str}\n'
        if verbosity == 'v':
            reply_str += f'\n{bold(lc2.value)}\n'
        reply_str += f'{trg_str}'
        if verbosity == 'v':
            if syn_str or ant_str:
                reply_str += '\n\n'
            if syn_str:
                reply_str += f'{bold("Synonyms")}: {syn_str}\n'
            if ant_str:
                reply_str += f'{bold("Antonyms")}: {ant_str}'
    else:
        reply_str = trg_str
    return reply_str


def i_cmd_lc_view(upd: Update, chat_id, user_id, for_uname: str):
    """Displays %lc% -> %lc2%"""
    for_user_id = for_user(for_uname, user_id)
    if not for_user_id:
        tg_reply.cmd_err(upd)
        return
    if not for_uname:
        for_uname = subscribe_db.read_uname(for_user_id)
    lc = db.read_setting_w_fback(
        settings.chat_user_setting(chat_id, for_user_id, ELE_TY_lc))
    lc2 = db.read_setting_w_fback(
        settings.chat_user_setting(chat_id, for_user_id, ELE_TY_lc2))
    reply_str = f'{lc.result} -> {lc2.result}'
    if for_uname:
        reply_str = f'User: <b>{for_uname}</b>\n\n{reply_str}'

    upd.effective_message.reply_html(reply_str)


def hdl_cmd_languages(upd: Update):
    """Display supported languages"""
    reply_string = '\n'.join([i.value for i in Lc])
    reply_string = 'Supported languages: \n\n<code>' + reply_string + '</code>'
    upd.effective_message.reply_html(reply_string)


def i_cmd_lc(upd: Update, chat_id, user_id, lc: str, is_hdl_retco=True, fallback: str = None):
    reg_user_if_new(chat_id, user_id)
    if not lc:
        tg_reply.cmd_p_req(upd, 'lc')
        return
    lc = lc.upper()
    if not lc_check(upd, lc):
        hdl_cmd_languages(upd)
        return

    if fallback and fallback.lower() == 'x':
        g3r = db.iup_setting(settings.user_setting(user_id, ELE_TY_lc, lc))
    else:
        g3r = db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc, lc))
    if is_hdl_retco:
        tg_reply.hdl_retco(upd, logger, g3r)


def i_cmd_lc2(upd: Update, chat_id, user_id, lc2_str: str, is_handle_retco=True, fallback: str = None):
    reg_user_if_new(chat_id, user_id)
    if not lc2_str:
        tg_reply.cmd_p_req(upd, 'lc')
        hdl_cmd_languages(upd)
        return
    lc2_str = lc2_str.upper()

    if not (lc_check(upd, lc2_str)):
        hdl_cmd_languages(upd)
        return
    if fallback and fallback.lower() == 'x':
        g3r = db.iup_setting(settings.user_setting(user_id, ELE_TY_lc2, lc2_str))
    else:
        g3r = db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc2, lc2_str))
    if is_handle_retco:
        tg_reply.hdl_retco(upd, logger, g3r)


def cmd_string(cmd_str: str) -> str:
    cmd_prefix: str = setng_cmd_prefix()
    if cmd_str.startswith(cmd_prefix):
        return cmd_str.replace(cmd_prefix, '...')
    return cmd_str


def setng_cmd_prefix() -> str:
    chat_id, user_id = upd_extract_chat_user_id()
    setng_dct = settings.chat_user_setting(chat_id, user_id,
                                           ELE_TY_cmd_prefix)
    if cmd_prefix := db.read_setting(setng_dct).result:
        return cmd_prefix
    else:
        return ''


def hdl_cmd_setng_cmd_prefix(upd: Update, cmd_prefix: str, f_send=True):
    """Set the cmd prefix which replaces triple dot"""
    chat_id, user_id = upd_extract_chat_user_id()
    setng_dct = settings.chat_user_setting(chat_id, user_id,
                                           ELE_TY_cmd_prefix, cmd_prefix)
    if cmd_prefix:
        db.iup_setting(setng_dct)
    else:
        setng_dct['ele_val'] = db.read_setting(setng_dct).result

    if f_send:
        tg_reply.send_settings(upd, setng_dct)


def i_tst_qt_mode_edit(tst_tplate: TstTplate, qt_str: str) -> TstTplateIt:
    upd: Update = G3Ctx.upd
    it_wo_ans_li = tst_tplate.items_wo_ans()
    len_wo_ans = len(it_wo_ans_li)
    # noinspection PyTypeChecker
    tst_tplate_it: TstTplateIt = None

    if len_wo_ans > 0:
        tst_tplate_it = it_wo_ans_li[0]

    if not qt_str:
        if tst_tplate_it and tst_tplate_it.id_:
            write_to_setng(tst_tplate_it.txt_seq)
            write_to_setng(tst_tplate_it)
        # noinspection PyTypeChecker
        return

    tst_tplate_it = tst_new_qt(tst_tplate, qt_str)
    tst_tplate.it_li.append(tst_tplate_it)
    g3r: [(TstTplate, TstTplateIt)] = db.ins_tst_tplate_item(tst_tplate, tst_tplate_it)
    if g3r.retco != 0:
        cmd_err(upd)
        # noinspection PyTypeChecker
        return
    tst_tplate, tst_tplate_it = g3r.result

    if tst_tplate_it and tst_tplate_it.id_:
        write_to_setng(tst_tplate_it.txt_seq)
        write_to_setng(tst_tplate_it)
    reply_str = f'Question added to test {tst_tplate.bkey}'
    tg_reply.send(upd, reply_str)
    return tst_tplate_it


def hdl_cmd_reply_trans(upd: Update, src_msg: Message, user_id: int, text: str, lc_pair: tuple[Lc, Lc],
                        reply_string_builder: Callable = i_reply_str_from_txt_map_li_v,
                        is_send_reply=True) -> list[TxtlcMp]:
    """ Save translation of the source message which is either the replied to message
     or your last message (not counting commands).
     If a text is provided in 2 lines, the first line will be the lc text.
     The second line will be the lc2 text. Any source message will be ignored.
     If no text is provided, the source message will be translated by the bot instead """
    # Preparing the variables
    lc, lc2 = lc_pair

    if not lc or not lc2:
        tg_reply.reply(upd, 'Call /lc_pair XX-XX \nExamples:\n/lc_pair DE-EN\n/lc_pair RU-DE\n/lc_pair VI-EN')
        return []

    src_txt, trg_txt = '', ''
    # noinspection PyUnusedLocal
    reply_msg_id = None
    line_li = []
    if text:
        line_li = text.split('\n')
    if len(line_li) == 2:
        # 2 lines meaning: 2nd line is the translation of the 1st line
        src_txt = line_li[0]
        trg_txt = line_li[1]
    elif src_msg:
        # reply to message or last message of the chat-user
        src_txt = src_msg.text
        if utilities.is_msg_w_cmd(src_txt):
            src_txt = src_txt.split(' ', 1)[1]
        trg_txt = text
        # noinspection PyUnusedLocal
        reply_msg_id = src_msg.message_id
    else:
        src_txt = text

    # if src_txt:
    #    src_txt = src_txt.lower()
    # if trg_txt:
    #    trg_txt = trg_txt.lower()

    src_syn_li, src_ant_li, trg_syn_li, trg_ant_li = \
        conv_onym_str_li(src_txt, trg_txt)

    # if 0 < len(trg_syn_li) != len(src_syn_li):
    #     upd.effective_message.reply_html(f'Source contains {len(src_syn_li)} synonyms.'
    #                                      f'Target contains {len(trg_syn_li)} synonyms.')
    #     return []
    # if 0 < len(trg_ant_li) != len(src_ant_li):
    #     upd.effective_message.reply_html(f'Source contains {len(src_ant_li)} antonyms'
    #                                      f'Target contains{len(trg_ant_li)} antonyms.')
    #     return []

    reply_txt: str
    if not src_txt:  # and not trg_txt
        tg_reply.err_req_reply_to_msg(upd)
        logger.error('reply_to_msg now empty?')
        return []
    # ant_li ab idx 1
    # w/o trg: do translations, put in list of txtLCMapping
    # txt_map_li: use substring, join the text either with =, !
    # do last step for src and trg
    src_li = list(src_syn_li)
    trg_li = list(trg_syn_li)
    src_li.extend(src_ant_li[1:])
    trg_li.extend(trg_ant_li[1:])
    txt_map_li = []
    idx_trg_last = len(trg_li) - 1
    for idx, src in enumerate(src_li):
        if not trg_txt or idx_trg_last < idx:
            txt_map: TxtlcMp = find_or_ins_translation(src, lc_pair).result
            txt_map_li.append(txt_map)
        else:
            trg = trg_li[idx]
            # noinspection PyArgumentList
            g3r = iup_translation(Txtlc(src, lc), Txtlc(trg, lc2), str(user_id))
            txt_map_li.append(g3r.result)

    idx_src_syn_last = len(src_syn_li) - 1
    reply_str = reply_string_builder(user_id, idx_src_syn_last, lc, lc2, txt_map_li)
    ins_onyms_from_str_li(lc, src_syn_li, str(user_id), 'syn')
    ins_onyms_from_str_li(lc, src_ant_li, str(user_id), 'ant')
    if is_send_reply:
        # upd.effective_message.reply_html(reply_str, reply_to_message_id=reply_msg_id)
        upd.effective_message.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_str,
            parse_mode=ParseMode.HTML,
            timeout=10.0
        )
        # upd.effective_message.reply_html(reply_str, reply_to_message_id=None)
    return txt_map_li


def translate_all_since(reply_to_msg: Message, lc_pair: tuple[Lc, Lc]) \
        -> (list[TxtlcMp], list[dict]):
    chat_id = reply_to_msg.chat.id
    user_id = reply_to_msg.from_user.id
    from_msg_id = reply_to_msg.message_id
    msg_dct_li = tg_db.sel_msg_rng_by_chat_user(from_msg_id, chat_id, user_id).result
    txt_map_li: list[TxtlcMp] = []
    for msg_dct in msg_dct_li:
        translation: TxtlcMp = find_or_ins_translation(msg_dct['text'], lc_pair).result
        txt_map_li.append(translation)
    return msg_dct_li, txt_map_li


def li_all_onym(txtlc: Txtlc) -> tuple[list[TxtlcOnym]]:
    return db.li_onym_by_txtlc(txtlc).result


def ins_onyms_from_str_li(lc: Lc, str_li: list[str], creator: str, onym_ty='syn') -> None:
    if len(str_li) < 2:
        return
    # noinspection PyArgumentList
    txtlc_src = db.fiby_txt_lc(Txtlc(str_li[0], lc)).result
    for onym in str_li[1:]:
        # noinspection PyArgumentList
        txtlc_trg = db.fiby_txt_lc(Txtlc(onym, lc)).result
        # noinspection PyArgumentList
        g3r = db.ins_onym(TxtlcOnym(txtlc_src, txtlc_trg, creator, onym_ty))
        if g3r.retco == 0:
            id_ = g3r.result.id_
            logger.debug(f'Inserted Onym Mapping, ID:{id_}')


def split_on_split(seq_str: str, op: str) -> G3Result[str]:
    is_merging_mode = False
    if op.find('-'):
        is_merging_mode = True
    if is_merging_mode and op.find('.') >= 0:
        return G3Result(4, '')

    split_li = op.split(',')
    seq_str_li = seq_str.split(',')
    seq_str_li_len = len(seq_str_li)
    split_li.reverse()
    idx_li = []
    for i in split_li:
        from_idx = int(i.split('-')[0])
        to_idx = int(i.split('-')[1])
        if to_idx <= from_idx:
            return G3Result(4, '')
        if to_idx > seq_str_li_len:
            # OutOfBounds
            return G3Result(4, '')
        if (to_idx - 2) in idx_li:
            # overlapping
            return G3Result(4, '')
        for idx in range(to_idx - 2, from_idx - 2, -1):
            if idx in idx_li:
                # overlapping
                return G3Result(4, '')
            idx_li.append(idx)
    for rm_idx in idx_li:
        seq_str_li.pop(rm_idx)

    return G3Result(0, ','.join(seq_str_li))


def create_test(tst_type: str, bkey: str, user_id: int, txt_map_li: list[TxtlcMp],
                lc_pair: tuple[Lc, Lc]) -> TstTplate:
    g3r = db.sel_tst_tplate__bk(bkey)
    if g3r.retco == 0:
        # noinspection PyTypeChecker
        return None
    # noinspection PyArgumentList
    tst_template = TstTplate(tst_type, bkey, user_id, lc_pair[0], lc_pair[1])
    tst_template.add_items_from_map(txt_map_li)
    g3r = db.ins_tst_tplate(tst_template)

    return g3r.result


def read_lc_settings_w_fback(chat_id: int, user_id: int) -> (str, str):
    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc)).result
    lc2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc2)).result
    return lc, lc2


def read_setng_lc_pair() -> (Lc, Lc):
    return Lc.fin(read_setng(ELE_TY_lc).val), Lc.fin(read_setng(ELE_TY_lc2).val)


def tst_new_qt(tst_tplate: TstTplate, qt_str: str) -> TstTplateIt:
    if qt_str == f'.{ENT_TY_txt_seq.id}.':
        txt_seq: TxtSeq = txt_seq_by_setng()
        # noinspection PyTypeChecker
        txtlc_qt = None
    else:
        # noinspection PyTypeChecker
        txt_seq = None
        txtlc_qt: Txtlc = find_or_ins_translation(qt_str, tst_tplate.lc_pair()).result.txtlc_src
    # noinspection PyArgumentList
    tst_tplate_item: TstTplateIt = \
        TstTplateIt(tst_tplate, txt_seq, txtlc_qt, tst_tplate.nxt_num())
    return tst_tplate_item


def tst_tplate_it_ans_01(tst_tplate: TstTplate, tst_tplate_it: TstTplateIt, ans_str: str) -> Optional[TstTplateIt]:
    if tst_tplate_it.txt_seq:
        num_li: list[int] = [int(num.strip()) for num in ans_str.split(',')]
        for num in num_li:
            txt_seq_it = tst_tplate_it.txt_seq.it(num)
            tst_tplate_it_ans = tst_tplate_it.add_answer(txt_seq_it=txt_seq_it)
            db.iup_tst_tplate_it_ans(tst_tplate_it, tst_tplate_it_ans)
    else:
        txtlc_ans: Txtlc = find_or_ins_translation(ans_str, tst_tplate.lc_pair()).result.txtlc_src
        if txtlc_ans in tst_tplate_it.ans_li:
            return
        tst_tplate_it_ans = tst_tplate_it.add_answer(txtlc_ans=txtlc_ans)
        db.iup_tst_tplate_it_ans(tst_tplate_it, tst_tplate_it_ans)
    return tst_tplate_it


def tst_tplate_info(tst_tplate: TstTplate, f_trans=False, tst_run: TstRun = None) -> list[str]:
    reply_li: list[str] = [tst_tplate.label()]
    ans_li: list[TstTplateItAns] = list[TstTplateItAns]()
    for i in tst_tplate.it_li:
        # noinspection PyTypeChecker
        txtlc_mapping: TxtlcMp = None
        if f_trans:
            txtlc = i.txt_seq.txtlc_mp.txtlc_src if i.txt_seq else i.txtlc_qt
            if txtlc:
                txtlc_mapping = find_or_ins_translation(txtlc.txt, tst_tplate.lc_pair()).result
        reply_str = i.build_descr(txtlc_mapping, tst_run=tst_run) + '\n'
        if tst_run:
            ans_li.extend(i.ans_li)
        else:
            for ans in i.ans_li:
                # noinspection PyTypeChecker
                txtlc_mapping = None
                if f_trans:
                    if ans.txtlc_src():
                        txtlc_mapping = find_or_ins_translation(ans.txtlc_src().txt, tst_tplate.lc_pair()).result
                reply_str += ans.label(txtlc_mapping)
        reply_li.append(reply_str)
    if tst_run:
        reply_li.append(', '.join([str_uncapitalize(i.txtlc_src().txt) for i in ans_li]))
    return reply_li


def tst_run_by_setng() -> TstRun:
    g3r = settings.ent_by_setng(
        upd_extract_chat_user_id(), ELE_TY_tst_run_id,
        db.sel_tst_run)
    tst_run: TstRun = g3r.result
    if isinstance(tst_run.tst_tplate, int):
        tst_tplate_id = tst_run.tst_tplate
    else:
        tst_tplate_id = tst_run.tst_tplate.id_
    tst_run.propagate_tst_tplate(db.sel_tst_tplate(tst_tplate_id).result)
    return tst_run


def txt_seq_by_setng() -> TxtSeq:
    g3r = settings.ent_by_setng(
        upd_extract_chat_user_id(), ELE_TY_txt_seq_id,
        db.sel_txt_seq)
    ent: TxtSeq = g3r.result
    return ent


def tst_tplate_by_setng() -> TstTplate:
    g3r = settings.ent_by_setng(
        upd_extract_chat_user_id(), ELE_TY_tst_tplate_id,
        db.sel_tst_tplate)
    ent: TstTplate = g3r.result
    return ent


def tst_tplate_it_by_setng() -> (TstTplate, TstTplateIt):
    tst_tplate = tst_tplate_by_setng()
    g3r = db.read_setting(cu_setng(ELE_TY_tst_tplate_it_id))
    if g3r.retco != 0:
        # noinspection PyTypeChecker
        return tst_tplate, None
    item_id = int(g3r.result)
    tst_tplate_by_item = db.sel_tst_tplate_by_item_id(item_id).result
    if tst_tplate and tst_tplate != tst_tplate_by_item:
        # noinspection PyTypeChecker
        return tst_tplate, None
    return tst_tplate_by_item, tst_tplate_by_item.item_by_id(item_id)


def txt_13(txt: str):
    """Find %txt% in the dictionary of the users current source language (check with .lc.view)"""
    lc_pair = read_setng_lc_pair()
    txt_map_li = txtlc_cp_txt(lc_pair, txt)

    reply_str = ''
    for txt_map in txt_map_li:
        reply_str += f'{txt_map.txtlc_src.txt}\n{italic(txt_map.txtlc_trg.txt)}\n\n'

    if not reply_str:
        TgUIC.uic.info('Nothing found!')
        return
    TgUIC.uic.send(reply_str)


def write_to_setng(ent: Any) -> G3Result:
    if not ent:
        return G3Result(4)
    return settings.ent_to_setng(
        upd_extract_chat_user_id(), ent)


# noinspection PyDefaultArgument
def tst_run_menu(tst_run: TstRun, info_str: str):
    cmd_qhint: G3Command = g3_cmd_by('tst_run_qhint')
    cmd_qnext: G3Command = g3_cmd_by('tst_run_qnext')
    cmd_qprev: G3Command = g3_cmd_by('tst_run_qprev')
    mi_list: list[MenuIt] = [
        MenuIt(f'{cmd_qprev.name}', I_PREV, None, cmd_qprev, None, None),
        MenuIt(f'{cmd_qhint.name}', I_HINT, None, cmd_qhint, None, None),
        MenuIt(f'{cmd_qnext.name}', I_NEXT, None, cmd_qnext, None, None),
        MenuIt('777', '\n')
    ]
    cmd_qansw: G3Command = g3_cmd_by('tst_run_qansw')
    ans_li: list[TstTplateItAns] = tst_run.ans_open_li()
    shuffle(ans_li)
    menu_it_li: list[MenuIt] = []
    for idx, ans in enumerate(ans_li):
        ans_txt = ans.txtlc_src_alt().txt
        menu_it_li.append(MenuIt(f'{cmd_qansw.name} {ans_txt}', I_ANSWER + ans_txt, None, cmd_qansw, None, ans_txt))
        if (idx + 1) % 3 == 0 and idx < len(ans_li):
            menu_it_li.append(MenuIt('111-{idx}', '\n'))
    mi_list.extend(menu_it_li)

    # mi_list.extend([
    #     MenuIt('111', '\n'),
    #     MenuIt(f'txt_seq_it_merge', '➕', None, g3_cmd_by('txt_seq_it_merge'), None),
    #     MenuIt(f'txt_seq_it_translate', 'ℹ️', None, g3_cmd_by('txt_seq_it_translate'), None),
    #     MenuIt(f'txt_seq_it_13', '🔗', None, g3_cmd_by('txt_seq_it_13'), None),
    #     MenuIt(f'txt_seq_it_reset', '⏮', None, g3_cmd_by('txt_seq_it_reset'), None)
    # ])
    menu = Menu('tst_run', info_str)
    send_menu_keyboard(menu, mi_list)


def tst_run_01(tst_tplate: TstTplate) -> TstRun:
    # noinspection PyArgumentList
    tst_run: TstRun = TstRun(tst_tplate, *upd_extract_chat_user_id())
    tst_run = db.ins_tst_run(tst_run).result
    write_to_setng(tst_run)
    return tst_run_by_setng()


def tst_run_help(upd: Update, tst_run):
    """Show help"""
    col_li: list[TgColumn] = [
        TgColumn('c1', -1, 'Command', 8),
        TgColumn('c2', -1, 'Description', 50),
    ]
    hint_dct = {
        1: {'c1': '...help ', 'c2': 'Show help                                         '},
        2: {'c1': '...qnext', 'c2': 'Proceed to next question                          '},
        3: {'c1': '...qprev', 'c2': 'Back to previous question                         '},
        4: {'c1': '...qinfo', 'c2': 'Show current question                             '},
        5: {'c1': '...qhint', 'c2': 'Show a random hint or hint %num%                  '},
        6: {'c1': '...qansw', 'c2': 'Answer the question -> ...qansw %text%            '},
        7: {'c1': '...tinfo', 'c2': 'Show current test                                 '},
        8: {'c1': '...thint', 'c2': 'Show a random test hint or hint %num%             '},
        9: {'c1': '...tfnsh', 'c2': 'Finish the test. Enforce by: -> ...tfnsh finish   '}
    }
    tbl_def = TableDef(col_li=col_li)
    tg_reply.send_table(upd, tbl_def, hint_dct)
    tst_run.act_add(ActTy.help)
    db.ins_tst_run_act(tst_run)


def tst_run_qans(tst_run: TstRun, tst_tplate_it_ans: TstTplateItAns, act_ty: ActTy) -> str:
    if not tst_tplate_it_ans:
        TgUIC.uic.error(f'No question found!')
        return ''
    info_str = i_tst_run_q_ans_info(tst_run, tst_tplate_it_ans) + '\n\n'
    tst_run.ans_act_add(tst_tplate_it_ans, act_ty)
    db.ins_tst_run_act(tst_run)
    return info_str


def tst_run_qnext(tst_run: TstRun) -> str:
    tst_tplate_it_ans = tst_run.ans_next()
    info_str = tst_run_qans(tst_run, tst_tplate_it_ans, ActTy.qnext)
    return info_str


def tst_run_qprev(tst_run: TstRun) -> str:
    tst_tplate_it_ans = tst_run.ans_prev()
    return tst_run_qans(tst_run, tst_tplate_it_ans, ActTy.qprev)


def tst_run_qinfo(tst_run: TstRun) -> str:
    tst_tplate_it_ans = tst_run.ans_current()
    return tst_run_qans(tst_run, tst_tplate_it_ans, ActTy.qinfo)


def tst_run_qhint(tst_run: TstRun) -> str:
    cur_ans: TstTplateItAns = tst_run.ans_current()
    tst_tplate_it = cur_ans.tst_tplate_it
    g3r = find_or_ins_translation(
        tst_tplate_it.build_text(), tst_run.tst_tplate.lc_pair()
    )
    send_str = tst_tplate_it.build_descr(g3r.result, tst_run) + '\n\n'
    send_str += f'Answer for number: {bold(str(cur_ans.ans_num))}'

    tst_run.ans_act_add(cur_ans, ActTy.qhint)
    db.ins_tst_run_act(tst_run)

    return send_str


def init_4_kb() -> EntTy:
    ENT_TY_tst_run.cmd_prefix = '.tst.run.'
    ENT_TY_tst_run.but_cmd_def = 'qansw'
    ENT_TY_tst_run.but_cmd_li = [
        [('<<', 'qprev'), ('😶', 'qinfo'), ('🤔', 'qhint'), ('>>', 'qnext')],
        [('❗', 'tinfo'), ('❓', 'thint'), ('🔐', 'tfnsh')]
    ]
    ENT_TY_tst_run.keyboard_descr = 'Type the answer or choose an option!'
    return ENT_TY_tst_run


def tst_run_qansw(tst_run: TstRun, text: str) -> str:
    tst_tplate_it_ans = tst_run.ans_current()

    sus: Sus
    if text == tst_tplate_it_ans.txtlc_src().txt:
        sus = Sus.sccs
        TgUIC.uic.send('⭐')
    else:
        sus = Sus.fail
        TgUIC.uic.send('😔')

    tst_run.ans_act_sus_add(tst_tplate_it_ans, ActTy.qansw, sus)
    db.ins_tst_run_act(tst_run)

    if sus == Sus.sccs:
        tst_run = tst_run_by_setng()
        return tst_run_qnext(tst_run)


def tst_run_tinfo(tst_run: TstRun):
    # noinspection PyTypeChecker
    tinfo_li = tst_tplate_info(tst_run.tst_tplate, f_trans=False, tst_run=tst_run)
    tg_reply.li_send(G3Ctx.upd, tinfo_li)
    tst_run.act_add(ActTy.tinfo)
    db.ins_tst_run_act(tst_run)


def tst_run_thint(upd: Update, tst_run: TstRun):
    tst_tplate = tst_run.tst_tplate
    col_li: list[TgColumn] = [
        TgColumn('lc', -1, tst_tplate.lc.value, 22),
        TgColumn('lc2', -1, tst_tplate.lc2.value, 22),
    ]
    ans_li: list[TstTplateItAns] = tst_tplate.all_ans_li()
    shuffle(ans_li)
    row_dct_li: list[dict[str, str]] = []
    for ans in ans_li:
        txtlc_mp = find_or_ins_translation(str_uncapitalize(ans.txtlc_src().txt), tst_tplate.lc_pair()).result
        row_dct_li.append({'lc': txtlc_mp.txtlc_src.txt, 'lc2': txtlc_mp.txtlc_trg.txt})
    tg_reply.send_table(upd, TableDef(col_li), row_dct_li)
    tst_run.act_add(ActTy.thint)
    db.ins_tst_run_act(tst_run)


def tst_run_tfnsh(upd: Update, tst_run: TstRun):
    tst_run.act_add(ActTy.tfnsh)
    db.upd_tst_run__end(tst_run)
    tst_run = db.sel_tst_run(tst_run.id_).result
    tg_reply.send(upd, f'Start: {tst_run.sta_tst}\nEnd: {tst_run.end_tst}')
