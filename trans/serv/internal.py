from typing import Optional

import elements
import settings
from g3b1_data.elements import *
from g3b1_data.model import G3Result
from g3b1_data.settings import chat_user_setting
from g3b1_serv.tg_reply import *
from trans.data import db, TST_TY_LI
from trans.data.db import iup_setting
from trans.data.model import TstTplate, TstTplateIt, Lc, TxtlcMp, TxtSeq
from trans.serv import services
from utilities import TableDef, TgColumn


def i_sel_tst_tplate_bk(upd: Update, bkey: str) -> Optional[TstTplate]:
    if not bkey:
        tg_reply.cmd_p_req(upd, 'bkey')
        return
    g3r = db.sel_tst_tplate__bk(bkey)
    if g3r.retco != 0:
        tg_reply.cmd_err(upd)
        return
    return g3r.result


def lc_check(upd: Update, lc_str: str) -> Lc:
    """send reply with error message and return false if lc not supported"""
    if not (lc := Lc.find_lc(lc_str)):
        upd.effective_message.reply_html(f'Language code {lc_str} unknown')
        # noinspection PyTypeChecker
        return None
    return lc


def i_tst_qt_mode_exe(upd: Update, tst_tplate: TstTplate, tst_tplate_it: TstTplateIt):
    reply_str = f'Test {tst_tplate.bkey}\n' \
                f'{italic("Separate several answers by row breaks")}\n\n' \
                f'{code(tst_tplate_it.text())}'
    upd.effective_message.reply_html(reply_str)


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

    tst_tplate_it = services.tst_new_qt(chat_id, tst_tplate, qt_str)
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


def i_extract_split_string(txt: str) -> str:
    if txt.find('| ') == -1:
        return ''
    while txt.find(' |') != -1:
        txt = txt.replace(' |', '|')
    pos = 0
    split_str = ''
    seq_li = txt.split('|')
    for seq in seq_li:
        w_li = seq.split(' ')
        if split_str:
            split_str += ','
        pos += len(w_li)
        split_str += str(pos)
    return split_str


def i_tst_ans_mode_edit(upd: Update, tst_tplate: TstTplate, tst_tplate_it: TstTplateIt, ans_str: str):
    """Add answer to the current item"""
    tst_tplate_it, tst_tplate_it_ans = services.tst_tplate_it_ans_01(tst_tplate, tst_tplate_it, ans_str)
    if not tst_tplate_it:
        tg_reply.cmd_err(upd)
        upd.effective_message.reply_html(f'Does the answer already exist for the question of the current tst_item?')
        return
    db.iup_tst_tplate_it_ans(tst_tplate_it, tst_tplate_it_ans)


def i_iup_setng_tst_template(chat_id: int, user_id: int, tst_template: TstTplate) -> G3Result:
    return iup_setting(
        chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_id, str(tst_template.id_))
    )


def i_tst_types(upd: Update):
    reply_str = ''
    for i in TST_TY_LI:
        reply_str += f'{str(i["id"]).rjust(4)} = {i["bkey"].ljust(40)}\n{i["descr"].ljust(40)}\n\n'
    upd.effective_message.reply_html(code(reply_str))


def i_execute_split_and_send(chat_id, lc_pair: tuple[Lc, Lc], split_str, src_msg_text, upd, user_id):
    row_li, txt_map_li = i_execute_split(lc_pair, split_str, src_msg_text)
    txt_seq: TxtSeq = services.ins_seq_if_new(src_msg_text, lc_pair, txt_map_li, chat_id, user_id)
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
        translation: TxtlcMp = services.find_or_ins_translation(
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


def i_iup_setng_tst_tplate_w_it(chat_id: int, user_id: int,
                                tst_tplate_it: TstTplateIt, tst_tplate: TstTplate = None) -> G3Result:
    if not tst_tplate:
        if not tst_tplate_it:
            return G3Result(4)
        elif not tst_tplate_it.tst_tplate or not tst_tplate_it.tst_tplate.id_:
            g3r = db.sel_tst_tplate_by_item_id(tst_tplate_it.id_)
            if g3r.retco != 0:
                return G3Result(4)
            tst_tplate = g3r.result
        else:
            tst_tplate = tst_tplate_it.tst_tplate
    g3r = i_iup_setng_tst_template(chat_id, user_id, tst_tplate)
    if g3r.retco != 0:
        return G3Result(4)
    if not tst_tplate_it:
        return g3r
    g3r = iup_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_it_id, str(tst_tplate_it.id_)))
    return g3r


def i_set_tst_mode_and_notify(upd: Update, chat_id: int, user_id: int, tst_mode: int, read_first=False):
    if read_first:
        g3r = db.read_setting(chat_user_setting(chat_id, user_id, elements.ELE_TY_tst_mode))
        if g3r.retco == 0 and g3r.result == tst_mode:
            # nothing to do, tst_mode already set accordingly
            return
    setng_dct = chat_user_setting(chat_id, user_id, elements.ELE_TY_tst_mode, str(tst_mode))
    db.iup_setting(setng_dct)
    tg_reply.send_settings(upd, setng_dct)


def i_tst_tplate_by_setng(chat_id: int, user_id: int) -> TstTplate:
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_id))
    if g3r.retco != 0:
        # noinspection PyTypeChecker
        return None
    tst_tplate_id = int(g3r.result)
    tst_tplate = db.sel_tst_tplate(tst_tplate_id).result
    return tst_tplate


def i_user_dct_append_lc_pair(upd: Update, user_dct: dict[int, dict[..., ...]]) -> dict[int, dict[..., ...]]:
    chat_id: int = upd.effective_chat.id
    for k, v in user_dct.items():
        lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, k, ELE_TY_lc)).result
        lc2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, k, ELE_TY_lc2)).result
        v[ELE_TY_lc] = lc
        v[ELE_TY_lc2] = lc2
    return user_dct


def i_send_lc_li(upd: Update):
    """Display supported languages"""
    lc_str_li = [i.value for i in list(Lc)]
    reply_string = '\n'.join(lc_str_li)
    reply_string = 'Supported languages: \n\n<code>' + reply_string + '</code>'
    upd.effective_message.reply_html(reply_string)


def i_parse_lc_pair(upd: Update, lc_pair: str) -> (Lc, Lc):
    if not lc_pair:
        tg_reply.cmd_p_req(upd, 'lc_pair')
    lc_pair = lc_pair.strip()

    if len(lc_pair) != 5 or len(lc_pair.split('-')) != 2 or lc_pair[2:3] != '-':
        tg_reply.cmd_err(upd)
        tg_reply.reply(upd, 'Format lc_pair: XX-XX, eg. DE-EN, TR-VI')
        return None

    lc_str = lc_pair[:2].upper()
    if not (lc := lc_check(upd, lc_str)):
        i_send_lc_li(upd)
        return None

    lc2_str = lc_pair[3:5].upper()
    if not (lc2 := lc_check(upd, lc2_str)):
        i_send_lc_li(upd)
        return None

    return lc, lc2


def i_tst_tplate_it_by_setng(chat_id: int, user_id: int) -> (TstTplate, TstTplateIt):
    tst_tplate = i_tst_tplate_by_setng(chat_id, user_id)
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_it_id))
    if g3r.retco != 0:
        # noinspection PyTypeChecker
        return tst_tplate, None
    item_id = int(g3r.result)
    tst_tplate_by_item = db.sel_tst_tplate_by_item_id(item_id).result
    if tst_tplate and tst_tplate != tst_tplate_by_item:
        # noinspection PyTypeChecker
        return tst_tplate, None
    return tst_tplate_by_item, tst_tplate_by_item.item_by_id(item_id)
