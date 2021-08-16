import logging
from typing import Callable

from telegram import Update, Message

import trans.data
from g3b1_data import tg_db, elements, settings
from g3b1_data.elements import *
from g3b1_data.model import G3Result
from g3b1_data.settings import chat_user_setting
from g3b1_log.g3b1_log import cfg_logger
from g3b1_serv import tg_reply, utilities
from g3b1_serv.tg_reply import bold
from trans.data import db
from trans.data.model import TxtLC, TxtLCMapping, TxtLCOnym, TxtSeq, TstTemplate, TstTemplateIt, \
    TstTemplateItAns

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def reg_user_if_new(chat_id: int, user_id: int):
    tg_db.externalize_chat_id(trans.data.BOT_BKEY_TRANS, chat_id)
    tg_db.externalize_user_id(trans.data.BOT_BKEY_TRANS, user_id)
    # db.ins_user_setting_default(user_id)


def fiby_txt_lc(text, lc) -> TxtLC:
    """Find text in DB"""
    return db.fiby_txt_lc(TxtLC(text, lc)).result


def find_or_ins_txtlc_with_txtlc_2(txt, lc, lc_2, translator=None) -> TxtLCMapping:
    txt_mapping = find_txtlc_with_txtlc_2(txt, lc, lc_2, translator)
    if not txt_mapping.txtlc_src:
        txtlc = db.ins_txtlc(TxtLC(txt, lc)).result
        txt_mapping.txtlc_src = txtlc
    return txt_mapping


def find_txtlc_with_txtlc_2(txt, lc, lc_2, translator=None) -> TxtLCMapping:
    """Find text in DB and if exist return it along with translation of translator for lc_2"""
    txtlc_find = fiby_txt_lc(txt, lc)
    if not txtlc_find:
        return TxtLCMapping(None, None, lc_2)
    txt_mapping: TxtLCMapping = db.fi_txt_mapping(txtlc_find, lc_2, translator).result  # -> TxtLCMapping
    if not txt_mapping:
        txt_mapping = TxtLCMapping(txtlc_find, None, lc_2)
    return txt_mapping


def find_or_ins_translation(txt, lc, lc_2) -> G3Result[TxtLCMapping]:
    """Return text and translation, if not exists, create them with Google"""
    lc_2 = lc_2.upper()
    txt_mapping = find_or_ins_txtlc_with_txtlc_2(txt, lc, lc_2)
    if txt_mapping.txtlc_trg:
        return G3Result(0, txt_mapping)

    # next: Google translate
    trg_txt: str = translate_google(txt, lc, lc_2)
    txt_mapping.translator = 'google'
    txt_mapping.score = 10

    return set_trg_of_map_and_save(txt_mapping, trg_txt)


def iup_translation(txtlc: TxtLC, txtlc_2: TxtLC, translator: str, score: int = 80) -> G3Result:
    """Update or insert txtlc pair"""
    txt_mapping = find_or_ins_txtlc_with_txtlc_2(txtlc.txt, txtlc.lc, txtlc_2.lc, translator)
    if txt_mapping.txtlc_trg and txt_mapping.txtlc_trg.txt == txtlc_2.txt \
            and txt_mapping.score == score:
        return G3Result(0, txt_mapping)
    txt_mapping.score = score
    txt_mapping.translator = translator

    return set_trg_of_map_and_save(txt_mapping, txtlc_2.txt)


def set_trg_of_map_and_save(txt_mapping: TxtLCMapping, txt) -> G3Result:
    txtlc_find = fiby_txt_lc(txt, txt_mapping.lc_2)
    if not txtlc_find:
        txtlc_find = db.ins_txtlc(TxtLC(txt, txt_mapping.lc_2)).result
    txt_mapping.txtlc_trg = txtlc_find
    g3r: G3Result = db.ins_upd_txt_mapping(txt_mapping)
    return g3r


def translate_google(text: str, lc, lc_2) -> str:
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
    result = translate_client.translate(text, source_language=lc, target_language=lc_2)
    # noinspection PyTypeChecker
    return result["translatedText"]


def conv_onym_str_li(src_txt: str, trg_txt: str) -> (list, list, list, list):
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
            ant_split_li = split_li[0].split(' ! ')
            syn_li.append(ant_split_li[0].strip())
            for ant in ant_split_li:
                ant_li.append(ant.strip())
        else:
            for idx, item in enumerate(split_li):
                ant_split_li = item.strip().split(' ! ')
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


def onyms_strs_from_txt_maps(txt_map: TxtLCMapping) -> (str, str):
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


def i_reply_str_from_txt_map_li(idx_src_syn_last: int, lc: str, lc_2: str, txt_map_li: list[TxtLCMapping],
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
        else:
            reply_str = ''
        reply_str += f'{src_str}\n'
        if verbosity == 'v':
            reply_str += f'\n{bold(lc_2)}\n'
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


def hdl_cmd_reply_trans(upd: Update, src_msg: Message, user_id: int, text: str, lc: str,
                        lc_2: str,
                        reply_string_builder: Callable = i_reply_str_from_txt_map_li_v,
                        is_send_reply=True) -> list[TxtLCMapping]:
    """ Save translation of the source message which is either the replied to message
     or your last message (not counting commands).
     If a text is provided in 2 lines, the first line will be the lc text.
     The second line will be the lc_2 text. Any source message will be ignored.
     If no text is provided, the source message will be translated by the bot instead """
    # Preparing the variables
    if lc:
        lc = lc.upper()
    if lc_2:
        lc_2 = lc_2.upper()

    if not lc or not lc_2:
        tg_reply.reply(upd, 'Call /lc_pair XX-XX \nExamples:\n/lc_pair DE-EN\n/lc_pair RU-DE\n/lc_pair VI-EN')
        return []

    src_txt, trg_txt = '', ''
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
    # ohne trg: do translations, put in list of txtLCMapping
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
            txt_map: TxtLCMapping = find_or_ins_translation(src, lc, lc_2).result
            txt_map_li.append(txt_map)
        else:
            trg = trg_li[idx]
            g3r = iup_translation(TxtLC(src, lc), TxtLC(trg, lc_2), str(user_id))
            txt_map_li.append(g3r.result)

    idx_src_syn_last = len(src_syn_li) - 1
    reply_str = reply_string_builder(idx_src_syn_last, lc, lc_2, txt_map_li)
    ins_onyms_from_str_li(lc, src_syn_li, str(user_id), 'syn')
    ins_onyms_from_str_li(lc, src_ant_li, str(user_id), 'ant')
    if is_send_reply:
        # upd.effective_message.reply_html(reply_str, reply_to_message_id=reply_msg_id)
        upd.effective_message.reply_html(reply_str, reply_to_message_id=None)
    return txt_map_li


def translate_all_since(reply_to_msg: Message, lc: str, lc_2: str) \
        -> (list[TxtLCMapping], list[dict]):
    chat_id = reply_to_msg.chat.id
    user_id = reply_to_msg.from_user.id
    from_msg_id = reply_to_msg.message_id
    msg_dct_li = tg_db.sel_msg_rng_by_chat_user(from_msg_id, chat_id, user_id).result
    txt_map_li: list[TxtLCMapping] = []
    for msg_dct in msg_dct_li:
        translation: TxtLCMapping = find_or_ins_translation(msg_dct['text'], lc, lc_2).result
        txt_map_li.append(translation)
    return msg_dct_li, txt_map_li


def li_all_onym(txtlc: TxtLC) -> tuple[list[TxtLCOnym]]:
    return db.li_onym_by_txtlc(txtlc).result


def ins_onyms_from_str_li(lc: str, str_li: list[str], creator: str, onym_ty='syn') -> None:
    if len(str_li) < 2:
        return
    txtlc_src = db.fiby_txt_lc(TxtLC(str_li[0], lc)).result
    for onym in str_li[1:]:
        txtlc_trg = db.fiby_txt_lc(TxtLC(onym, lc)).result
        g3r = db.ins_onym(TxtLCOnym(txtlc_src, txtlc_trg, creator, onym_ty))
        if g3r.retco == 0:
            id_ = g3r.result.id_
            logger.debug(f'Inserted Onym Mapping, ID:{id_}')


def ins_seq_if_new(src_str: str, lc: str, lc2: str, txt_map_li: list[TxtLCMapping],
                   chat_id: int, user_id: int):
    # src_str = src_str.lower()
    txt_map: TxtLCMapping = find_or_ins_translation(src_str, lc, lc2).result
    txt_seq = TxtSeq(txt_map.txtlc_src)
    txt_seq.convert_to_item_li(txt_map_li)
    txt_seq = db.find_seq(txt_seq)
    if not txt_seq.id_:
        txt_seq = db.ins_seq(txt_seq).result
    db.iup_setting(
        chat_user_setting(chat_id, user_id,
                          elements.ELE_TYP_txt_seq_id, str(txt_seq.id_))
    )


def find_curr_txt_seq(chat_id: int, user_id: int) -> TxtSeq:
    txt_seq_id = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_txt_seq_id)).result
    if not txt_seq_id:
        return
    txt_seq: TxtSeq = db.get_txt_seq(txt_seq_id).result
    return txt_seq


def execute_split(lc, lc_2, split_str, src_msg_text):
    split_li: list[str] = split_str.split(',')
    word_li = src_msg_text.split(' ')
    word_li_len = len(word_li)
    if int(split_li[len(split_li) - 1]) < word_li_len:
        # to simplify the algorithm
        split_li.append(str(word_li_len + 1))
    start_index = 0
    trans_dct = dict[int, dict[str, str]]()
    word_li_remain: list[str]
    txt_map_li: list[TxtLCMapping] = []
    for count, split_after in enumerate(split_li):
        split_after = int(split_after)
        if split_after >= word_li_len:
            split_after = word_li_len
            word_li_remain = []
        else:
            word_li_remain = word_li[split_after:word_li_len]
        words_to_join_li = word_li[start_index:split_after]
        src_str = ' '.join(words_to_join_li)
        translation: TxtLCMapping = find_or_ins_translation(
            src_str, lc, lc_2).result
        txt_map_li.append(translation)
        trg_str = translation.txtlc_trg.txt
        word_dct = dict(
            src=src_str,
            trg=trg_str
        )
        trans_dct.update({count: word_dct})
        start_index = split_after
        if len(word_li_remain) == 0:
            break
    return trans_dct, txt_map_li


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


def create_test(tst_type: str, bkey: str, txt_map_li: list[TxtLCMapping], lc: str, lc_2: str) -> TstTemplate:
    g3r = db.sel_tst_tplate_by_bk(bkey)
    if g3r.retco == 0:
        return None
    tst_template = TstTemplate(tst_type, bkey, lc, lc_2)
    tst_template.add_items_from_map(txt_map_li)
    g3r = db.ins_tst_tplate(tst_template)

    return g3r.result


def read_lc_settings_w_fback(chat_id: int, user_id: int) -> (str, str):
    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc)).result
    lc_2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc2)).result
    return lc, lc_2


def tst_new_qt(tst_tplate: TstTemplate, qt_str: str) -> TstTemplateIt:
    txtlc_qt: TxtLC = find_or_ins_translation(qt_str, tst_tplate.lc, tst_tplate.lc_2).result.txtlc_src
    tst_tplate_item: TstTemplateIt = \
        TstTemplateIt(tst_tplate, txtlc_qt, tst_tplate.nxt_num())
    return tst_tplate_item


def tst_new_ans(tst_tplate: TstTemplate, tst_tplate_it: TstTemplateIt, ans_str: str) -> (
        TstTemplateIt, TstTemplateItAns):
    txtlc_ans: TxtLC = find_or_ins_translation(ans_str, tst_tplate.lc, tst_tplate.lc_2).result.txtlc_src
    if txtlc_ans in tst_tplate_it.txtlc_ans_li:
        return None, None
    tst_tplate_it_ans = tst_tplate_it.add_answer(txtlc_ans)
    return tst_tplate_it, tst_tplate_it_ans
