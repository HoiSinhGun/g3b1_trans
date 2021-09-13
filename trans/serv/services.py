from random import shuffle
from typing import Callable

from telegram import ParseMode, Message

import tg_db
import trans.data
from g3b1_log.g3b1_log import *
from g3b1_serv import utilities
from generic_mdl import TgColumn, TableDef
from subscribe.data import db as subscribe_db
from subscribe.serv.services import for_user
from tg_reply import bold, cmd_err
from trans.data.enums import ActTy, Sus
from trans.data.model import Txtlc, TxtlcMp, TxtlcOnym, TxtSeq, TstRun
from trans.serv.internal import *

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
    txt_mapping: TxtlcMp = db.fi_txt_mapping(txtlc_find, lc2, translator).result  # -> TxtLCMapping
    if not txt_mapping:
        # noinspection PyTypeChecker,PyArgumentList
        txt_mapping = TxtlcMp(txtlc_find, None, lc2)
    return txt_mapping


def txtlc_cp_txt(lc_pair: tuple[Lc, Lc], txt: str) -> list[TxtlcMp]:
    txtlc_li = db.txtlc_txt_cp(txt, lc_pair[0].value)
    txt_map_li: list[TxtlcMp] = []
    for txtlc in txtlc_li:
        txt_map: TxtlcMp = find_or_ins_translation(txtlc.txt, lc_pair).result
        txt_map_li.append(txt_map)
    return txt_map_li


def find_or_ins_translation(txt: str, lc_pair: tuple[Lc, Lc]) -> G3Result[TxtlcMp]:
    """Return text and translation, if not exists, create them with Google"""
    lc = lc_pair[0]
    lc2 = lc_pair[1]
    txt_mapping = find_or_ins_txtlc_with_txtlc2(txt, lc, lc2)
    if txt_mapping.txtlc_trg:
        return G3Result(0, txt_mapping)

    # next: Google translate
    trg_txt: str = translate_google(txt, lc.value, lc2.value)
    txt_mapping.translator = 'google'
    txt_mapping.score = 10

    return set_trg_of_map_and_save(txt_mapping, trg_txt)


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
    g3r: G3Result = db.iup_txt_mapping(txt_mapping)
    return g3r


def translate_google(text: str, lc_str, lc2_str) -> str:
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
    return result["translatedText"]


def i_tst_ans_mode_edit(upd: Update, tst_tplate: TstTplate, tst_tplate_it: TstTplateIt, ans_str: str):
    """Add answer to the current item"""
    tst_tplate_it, tst_tplate_it_ans = tst_tplate_it_ans_01(tst_tplate, tst_tplate_it, ans_str)
    if not tst_tplate_it:
        tg_reply.cmd_err(upd)
        upd.effective_message.reply_html(f'Does the answer already exist for the question of the current tst_item?')
        return
    db.iup_tst_tplate_it_ans(tst_tplate_it, tst_tplate_it_ans)


def i_execute_split_and_send(chat_id, lc_pair: tuple[Lc, Lc], split_str, src_msg_text, upd, user_id):
    row_li, txt_map_li = i_execute_split(lc_pair, split_str, src_msg_text)
    # noinspection PyUnusedLocal
    txt_seq: TxtSeq = ins_seq_if_new(src_msg_text, lc_pair, txt_map_li, chat_id, user_id)
    tbl_def = TableDef(
        [TgColumn('src', -1, 'src', 30), TgColumn('trg', -1, 'trg', 30)])
    reply_str = f'Split positions: {tg_reply.bold(split_str)}\n\n'
    tg_reply.send_table(upd, tbl_def, row_li, reply_str)


def i_execute_split(lc_pair: tuple[Lc, Lc], split_str, src_msg_text) \
        -> (list[dict[str, str]], list[TxtlcMp]):
    split_li: list[str] = split_str.split(',')
    word_li = src_msg_text.split(' ')
    word_li_len = len(word_li)
    if int(split_li[len(split_li) - 1]) < word_li_len:
        # to simplify the algorithm
        split_li.append(str(word_li_len + 1))
    start_index = 0
    row_li = list[dict[str, str]]()
    word_li_remain: list[str]
    txt_map_li: list[TxtlcMp] = []
    for count, split_after in enumerate(split_li):
        split_after = int(split_after)
        if split_after >= word_li_len:
            split_after = word_li_len
            word_li_remain = []
        else:
            word_li_remain = word_li[split_after:word_li_len]
        words_to_join_li = word_li[start_index:split_after]
        src_str = ' '.join(words_to_join_li)
        translation: TxtlcMp = find_or_ins_translation(
            src_str, lc_pair).result
        txt_map_li.append(translation)
        trg_str = translation.txtlc_trg.txt
        word_dct = dict(
            src=src_str,
            trg=trg_str
        )
        row_li.append(word_dct)
        start_index = split_after
        if len(word_li_remain) == 0:
            break
    return row_li, txt_map_li


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


def i_reply_str_from_txt_map_li(user_id: int, idx_src_syn_last: int, lc: str, lc2: str, txt_map_li: list[TxtlcMp],
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
            reply_str = f'{bold(lc)}\n'
        elif verbosity == 'u':
            uname = subscribe_db.read_uname(user_id)
            reply_str = f'{bold(uname)}\n'
        else:
            reply_str = ''
        if verbosity in ['v', 'b']:
            reply_str += f'{src_str}\n'
        if verbosity == 'v':
            reply_str += f'\n{bold(lc2)}\n'
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


def hdl_cmd_setng_cmd_prefix(upd: Update, cmd_prefix: str):
    """Set the cmd prefix which replaces triple dot"""
    chat_id, user_id = utilities.upd_extract_chat_user_id(upd)
    setng_dct = settings.chat_user_setting(chat_id, user_id,
                                           ELE_TY_cmd_prefix, cmd_prefix)
    db.iup_setting(setng_dct)

    tg_reply.send_settings(upd, setng_dct)


def i_tst_qt_mode_edit(upd: Update, chat_id, user_id, tst_tplate: TstTplate, qt_str: str):
    it_wo_ans_li = tst_tplate.items_wo_ans()
    len_wo_ans = len(it_wo_ans_li)
    # noinspection PyTypeChecker
    tst_tplate_it: TstTplateIt = None

    if len_wo_ans > 0:
        tst_tplate_it = it_wo_ans_li[0]

    if not qt_str:
        if len_wo_ans == 0:
            upd.effective_message.reply_html(f'{tst_tplate.label()}\n\n'
                                             f'You can add more questions with /tst_tplate_qt %question%!')
            return
        upd.effective_message.reply_html(f'{tst_tplate.label()}\n\n'
                                         f'{len_wo_ans} questions have no answers yet.\n'
                                         f'Provide answers with /tst_tplate_ans %ans_str%!\n\nNext missing:\n'
                                         f'{tst_tplate_it.label()}')
        if tst_tplate_it and tst_tplate_it.id_:
            iup_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_it_id, str(tst_tplate_it.id_)))
        return

    tst_tplate_it = tst_new_qt(chat_id, tst_tplate, qt_str)
    tst_tplate.it_li.append(tst_tplate_it)
    g3r: [(TstTplate, TstTplateIt)] = db.ins_tst_tplate_item(tst_tplate, tst_tplate_it)
    if g3r.retco != 0:
        cmd_err(upd)
        return
    tst_tplate, tst_tplate_it = g3r.result

    if tst_tplate_it and tst_tplate_it.id_:
        iup_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_it_id, str(tst_tplate_it.id_)))
    tst_item_lbl = tst_tplate_it.label() + '\n'
    reply_str = f'Question added to test {tst_tplate.bkey}\n\n' \
                f'{tst_item_lbl}'
    upd.effective_message.reply_html(reply_str)


def i_tst_ans_mode_exe(upd: Update, tst_tplate: TstTplate, tst_tplate_it: TstTplateIt, ans_str: str):
    ans_str_li = ans_str.split('\n')
    if len(ans_str_li) != len(tst_tplate_it.ans_li):
        tg_reply.reply(upd, f'Sorry bro/sis, your answer is wrong!')
        return
    for idx, ans_i in enumerate(ans_str_li):
        ans_i_comp = ans_i.strip().lower()
        ans_correct = tst_tplate_it.ans_li[idx].txtlc_src().txt
        if ans_i_comp != ans_correct:
            tg_reply.reply(upd, f'Sorry bro/sis, your answer is wrong!')
            return
    tg_reply.reply(upd, 'Excellent!')
    tst_tplate_it_next = tst_tplate.item_next(tst_tplate_it.itnum)
    if tst_tplate_it_next:
        tg_reply.reply(upd, f'Please proceed to the next question with /tst_tplate_qt')
    else:
        tg_reply.reply(upd, f'Test {tst_tplate.bkey} finished!')
    return tst_tplate_it_next


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
            parse_mode=ParseMode.HTML
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


def ins_seq_if_new(src_str: str, lc_pair: tuple[Lc, Lc], txt_map_li: list[TxtlcMp],
                   chat_id: int, user_id: int) -> TxtSeq:
    # src_str = src_str.lower()
    txt_map: TxtlcMp = find_or_ins_translation(src_str, lc_pair).result
    # noinspection PyArgumentList
    txt_seq = TxtSeq(txt_map.txtlc_src)
    txt_seq.convert_to_it_li(txt_map_li)
    txt_seq = db.sel_txt_seq_by_uq(txt_seq)
    if not txt_seq.id_:
        txt_seq = db.ins_seq(txt_seq).result
    db.iup_setting(
        chat_user_setting(chat_id, user_id,
                          elements.ELE_TY_txt_seq_id, str(txt_seq.id_))
    )
    return txt_seq


def find_curr_txt_seq(chat_id: int, user_id: int) -> TxtSeq:
    txt_seq_id = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_txt_seq_id)).result
    if not txt_seq_id:
        # noinspection PyTypeChecker
        return
    txt_seq: TxtSeq = db.sel_txt_seq(txt_seq_id).result
    return txt_seq


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


def setng_read_lc_pair(chat_id: int, user_id: int) -> (Lc, Lc):
    lc_str_pair = read_lc_settings_w_fback(chat_id, user_id)
    return Lc.find_lc(lc_str_pair[0]), Lc.find_lc(lc_str_pair[1])


def tst_new_qt(chat_id: int, tst_tplate: TstTplate, qt_str: str) -> TstTplateIt:
    if qt_str == f'.{ENT_TY_txt_seq.id_}.':
        txt_seq: TxtSeq = find_curr_txt_seq(chat_id, tst_tplate.user_id)
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


def tst_tplate_it_ans_01(tst_tplate: TstTplate, tst_tplate_it: TstTplateIt, ans_str: str) -> (
        TstTplateIt, TstTplateItAns):
    if ans_str.startswith(f'.{ENT_TY_txt_seq_it.id_}-'):
        itnum = ans_str.split('-')[1][:-1]
        txt_seq_it = tst_tplate_it.txt_seq.it(int(itnum))
        # noinspection PyTypeChecker
        txtlc_ans = None
    else:
        # noinspection PyTypeChecker
        txt_seq_it = None
        txtlc_ans: Txtlc = find_or_ins_translation(ans_str, tst_tplate.lc_pair()).result.txtlc_src
        if txtlc_ans in tst_tplate_it.ans_li:
            return None, None
    tst_tplate_it_ans = tst_tplate_it.add_answer(txt_seq_it, txtlc_ans)
    return tst_tplate_it, tst_tplate_it_ans


def tst_tplate_info(tst_tplate: TstTplate, f_trans=False, f_ans_shuffle=False) -> str:
    reply_str = tst_tplate.label() + '\n\n'
    ans_li: list[TstTplateItAns] = list[TstTplateItAns]()
    for i in tst_tplate.it_li:
        # noinspection PyTypeChecker
        txtlc_mapping: TxtlcMp = None
        if f_trans:
            txtlc = i.txt_seq.txtlc_src if i.txt_seq else i.txtlc_qt
            if txtlc:
                txtlc_mapping = find_or_ins_translation(txtlc.txt, tst_tplate.lc_pair()).result
        reply_str += i.label(txtlc_mapping) + '\n'
        if f_ans_shuffle:
            ans_li.extend(i.ans_li)
        else:
            for ans in i.ans_li:
                # noinspection PyTypeChecker
                txtlc_mapping = None
                if f_trans:
                    if ans.txtlc_src():
                        txtlc_mapping = find_or_ins_translation(ans.txtlc_src().txt, tst_tplate.lc_pair()).result
                reply_str += ans.label(txtlc_mapping)
        reply_str += '\n\n'
    if f_ans_shuffle:
        reply_str += ', '.join([i.txtlc_src().txt for i in ans_li])
    return reply_str


def tst_run_by_setng(upd: Update) -> TstRun:
    g3r = settings.ent_by_setng(
        utilities.upd_extract_chat_user_id(upd), ELE_TY_tst_run_id,
        db.sel_tst_run)
    tst_run: TstRun = g3r.result
    tst_run.propagate_tst_tplate(db.sel_tst_tplate(tst_run.tst_tplate.id_).result)
    return tst_run


def tst_run_to_setng(upd: Update, tst_run: TstRun) -> G3Result:
    return settings.ent_to_setng(
        utilities.upd_extract_chat_user_id(upd), tst_run)


def tst_run_01(upd: Update, tst_tplate: TstTplate):
    # noinspection PyArgumentList
    tst_run: TstRun = TstRun(tst_tplate, *utilities.upd_extract_chat_user_id(upd))
    tst_run = db.ins_tst_run(tst_run).result
    tst_run_to_setng(upd, tst_run)
    tst_run_tinfo(upd, tst_run)


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
    tbl_def = utilities.TableDef(col_li=col_li)
    tg_reply.send_table(upd, tbl_def, hint_dct)
    tst_run.act_add(ActTy.help)
    db.ins_tst_run_act(tst_run)


def tst_run_qans(upd: Update, tst_run: TstRun, tst_tplate_it_ans: TstTplateItAns, act_ty: ActTy):
    if not tst_tplate_it_ans:
        upd.effective_message.reply_html(f'No question found!',
                                         reply_to_message_id=None)
        return
    info_str = i_tst_run_q_ans_info(tst_tplate_it_ans)
    tg_reply.send(upd, info_str)
    tst_run.ans_act_add(tst_tplate_it_ans, act_ty)
    db.ins_tst_run_act(tst_run)


def tst_run_qnext(upd: Update, tst_run: TstRun):
    tst_tplate_it_ans = tst_run.ans_next()
    tst_run_qans(upd, tst_run, tst_tplate_it_ans, ActTy.qnext)


def tst_run_qprev(upd: Update, tst_run: TstRun):
    tst_tplate_it_ans = tst_run.ans_prev()
    tst_run_qans(upd, tst_run, tst_tplate_it_ans, ActTy.prev)


def tst_run_qinfo(upd: Update, tst_run: TstRun):
    tst_tplate_it_ans = tst_run.ans_current()
    tst_run_qans(upd, tst_run, tst_tplate_it_ans, ActTy.qinfo)


def tst_run_qhint(upd: Update, tst_run: TstRun):
    tst_tplate_it_ans = tst_run.ans_current()
    tst_tplate_it = tst_tplate_it_ans.tst_tplate_it
    g3r = find_or_ins_translation(
        tst_tplate_it.text(), tst_run.tst_tplate.lc_pair()
    )
    all_ans_li = tst_run.tst_tplate.all_ans_li()
    shuffle(all_ans_li)
    send_str = tst_tplate_it.label(g3r.result) + '\n\n'
    send_str += ', '.join([i.txtlc_src().txt for i in all_ans_li])
    tg_reply.send(upd, send_str)
    tst_run.ans_act_add(tst_tplate_it_ans, ActTy.qhint)
    db.ins_tst_run_act(tst_run)


def tst_run_qansw(upd: Update, tst_run: TstRun, text: str):
    tst_tplate_it_ans = tst_run.ans_current()

    sus: Sus
    if text == tst_tplate_it_ans.txtlc.txt:
        sus = Sus.sccs
    else:
        sus = Sus.fail

    tg_reply.send(upd, str(sus))
    tst_run.ans_act_sus_add(tst_tplate_it_ans, ActTy.qansw, sus)
    db.ins_tst_run_act(tst_run)

    if sus == Sus.sccs:
        tst_run = tst_run_by_setng(upd)
        tst_run_qnext(upd, tst_run)


def tst_run_tinfo(upd: Update, tst_run: TstRun):
    tinfo_str = tst_tplate_info(tst_run.tst_tplate, f_trans=False, f_ans_shuffle=True)
    tg_reply.reply(upd, tinfo_str)
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
        txtlc_mp = find_or_ins_translation(ans.txtlc_src().txt, tst_tplate.lc_pair()).result
        row_dct_li.append({'lc': txtlc_mp.txtlc_src.txt, 'lc2': txtlc_mp.txtlc_trg.txt})
    tg_reply.send_table(upd, TableDef(col_li), row_dct_li)
    tst_run.act_add(ActTy.thint)
    db.ins_tst_run_act(tst_run)


def tst_run_tfnsh(upd: Update, tst_run: TstRun):
    tst_run.act_add(ActTy.tfnsh)
    db.upd_tst_run__end(tst_run)
    tst_run = db.sel_tst_run(tst_run.id_).result
    tg_reply.send(upd, f'Start: {tst_run.sta_tst}\nEnd: {tst_run.end_tst}')
