from typing import Optional

from telegram import Update

import elements
import settings
from g3b1_data.elements import *
from g3b1_data.model import G3Result
from g3b1_data.settings import chat_user_setting
from g3b1_serv import tg_reply
from generic_mdl import TableDef, TgColumn
from tg_reply import italic, code, bold
from trans.data import db, TST_TY_LI
from trans.data.db import iup_setting
from trans.data.model import TstTplate, TstTplateIt, Lc, TstTplateItAns, TxtlcMp, TstRun


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
    if not (lc := Lc.fin(lc_str)):
        upd.effective_message.reply_html(f'Language code {lc_str} unknown')
        # noinspection PyTypeChecker
        return None
    return lc


def i_iup_setng_tst_template(chat_id: int, user_id: int, tst_template: TstTplate) -> G3Result:
    return iup_setting(
        chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_id, str(tst_template.id_))
    )


def i_tst_types(upd: Update):
    reply_str = ''
    for i in TST_TY_LI:
        reply_str += f'{str(i["id"]).rjust(4)} = {i["bkey"].ljust(40)}\n{i["descr"].ljust(40)}\n\n'
    upd.effective_message.reply_html(code(reply_str))


def i_send_txtlc_mp(upd: Update, txtlc_mp: TxtlcMp, pre_str=''):
    send_str = f'{pre_str}\n' \
               f'{bold(txtlc_mp.txtlc_src.lc.value)}\n' \
               f'{txtlc_mp.txtlc_src.txt}\n\n' \
               f'{bold(txtlc_mp.txtlc_trg.lc.value)}\n' \
               f'{italic(txtlc_mp.txtlc_trg.txt)}'
    tg_reply.send(upd, send_str)


def i_send_txtlc_mp_li(upd: Update, txtlc_mp_li: list[TxtlcMp], pre_str=''):
    lc, lc2 = TxtlcMp.lc_pair(txtlc_mp_li[0])
    tbl_def = TableDef(
        [TgColumn('src', -1, lc.value, 30), TgColumn('trg', -1, lc2.value, 30)])
    row_li = [dict(src=i.txtlc_src.txt, trg=i.txtlc_trg.txt) for i in txtlc_mp_li]
    tg_reply.send_table(upd, tbl_def, row_li, pre_str)


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


def i_tst_run_q_ans_info(tst_run: TstRun, ans: TstTplateItAns) -> str:
    info_str = ans.tst_tplate_it.build_descr(tst_run=tst_run) + '\n\n'
    info_str += f'Answer for number: {bold(str(ans.ans_num))}'
    return info_str
