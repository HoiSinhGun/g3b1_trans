import trans
from g3b1_data.elements import *
from g3b1_data.model import G3Result
from g3b1_data.settings import chat_user_setting
from g3b1_serv import tg_reply
from g3b1_serv.tg_reply import *
from trans.data import db
from trans.data.db import iup_setting
from trans.ui.utilities import  *
from trans.data.model import TstTemplate, TstTemplateIt
from trans.serv import services


def lc_check(upd: Update, lc: str) -> bool:
    """send reply with error message and return false if lc not supported"""
    if lc not in trans.LC_li:
        upd.effective_message.reply_html(f'Language code {lc} unknown')
        return False
    return True


def i_tst_qt_mode_exe(upd: Update, tst_tplate: TstTemplate, tst_tplate_it: TstTemplateIt):
    reply_str = f'Test {tst_tplate.bkey}\n' \
                f'{italic("Separate several answers by row breaks")}\n\n' \
                f'{code(tst_tplate_it.txtlc_qt.txt)}'
    upd.effective_message.reply_html(reply_str)


def i_tst_qt_mode_edit(upd: Update, chat_id, user_id, tst_tplate: TstTemplate, qt_str: str):
    it_wo_ans_li = tst_tplate.items_wo_ans()
    len_wo_ans = len(it_wo_ans_li)
    tst_tplate_lbl = tst_template_lbl(tst_tplate) + '\n\n'
    tst_item_lbl = ''
    tst_item: TstTemplateIt = None

    if len_wo_ans > 0:
        tst_item = it_wo_ans_li[0]
        tst_item_lbl = tst_template_it_lbl(tst_item) + '\n'

    if not qt_str:
        if len_wo_ans == 0:
            upd.effective_message.reply_html(f'{tst_tplate_lbl}'
                                             f'You can add more questions with /tst_qt %question%!')
            return
        upd.effective_message.reply_html(f'{tst_tplate_lbl}'
                                         f'{len_wo_ans} questions have no answers yet.\n'
                                         f'Provide answers with /tst_ans %answer%!\nNext missing:\n'
                                         f'{tst_item_lbl}')
        if tst_item and tst_item.id_:
            iup_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_it_id, str(tst_item.id_)))
        return

    tst_template_item = services.tst_new_qt(tst_tplate, qt_str)
    tst_tplate.item_li.append(tst_template_item)
    g3r: [(TstTemplate, TstTemplateIt)] = db.ins_tst_tplate_item(tst_tplate, tst_template_item)
    if g3r.retco != 0:
        cmd_err(upd)
        return
    tst_tplate, tst_template_item = g3r.result

    if tst_template_item and tst_template_item.id_:
        iup_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_it_id, str(tst_template_item.id_)))
    tst_item_lbl = tst_template_it_lbl(tst_item) + '\n'
    reply_str = f'Question added to test {tst_tplate_lbl}' \
                f'{tst_item_lbl}'
    upd.effective_message.reply_html(reply_str)


def i_tst_ans_mode_exe(upd: Update, tst_tplate: TstTemplate, tst_tplate_it: TstTemplateIt, ans_str: str):
    ans_str_li = ans_str.split('\n')
    if len(ans_str_li) != len(tst_tplate_it.txtlc_ans_li):
        tg_reply.reply(upd, f'Sorry bro/sis, your answer is wrong!')
        return
    for idx, ans_i in enumerate(ans_str_li):
        ans_i_comp = ans_i.strip().lower()
        ans_correct = tst_tplate_it.txtlc_ans_li[idx].txtlc.txt
        if ans_i_comp != ans_correct:
            tg_reply.reply(upd, f'Sorry bro/sis, your answer is wrong!')
            return
    tg_reply.reply(upd, 'Excellent!')
    tst_tplate_it_next = tst_tplate.item_next(tst_tplate_it.itnum)
    if tst_tplate_it_next:
        tg_reply.reply(upd, f'Please proceed to the next question with /tst_qt')
    else:
        tg_reply.reply(upd, f'Test {tst_tplate.bkey} finished!')
    return tst_tplate_it_next


def i_tst_ans_mode_edit(upd: Update, tst_tplate: TstTemplate, tst_tplate_it: TstTemplateIt, ans_str: str):
    """Add answer to the current item"""
    tst_tplate_it, tst_tplate_it_ans = services.tst_new_ans(tst_tplate, tst_tplate_it, ans_str)
    if not tst_tplate_it:
        tg_reply.cmd_err(upd)
        upd.effective_message.reply_html(f'Does the answer already exist for the question of the current tst_item?')
        return
    db.iup_tst_tplate_item_ans(tst_tplate_it, tst_tplate_it_ans)


def i_iup_tst_template(chat_id: int, user_id: int, tst_template: TstTemplate) -> G3Result:
    return iup_setting(
        chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_id, str(tst_template.id_))
    )


def i_iup_tst_template_it(chat_id: int, user_id: int, tst_template_it: TstTemplateIt) -> G3Result:
    g3r = db.sel_tst_tplate_by_item_id(tst_template_it.id_)
    if g3r.retco != 0:
        return G3Result(4)
    g3r = i_iup_tst_template(chat_id, user_id, g3r.result)
    if g3r.retco != 0:
        return G3Result(4)
    return iup_setting(
        chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_it_id, str(tst_template_it.id_))
    )


def i_tst_template_by_setng(chat_id: int, user_id: int) -> TstTemplate:
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_id))
    if g3r.retco != 0:
        # noinspection PyTypeChecker
        return None
    tst_template_id = int(g3r.result)
    tst_tplate = db.sel_tst_tplate_by_id(tst_template_id).result
    return tst_tplate


def i_tst_tplate_item_by_setng(chat_id: int, user_id: int) -> (TstTemplate, TstTemplateIt):
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_it_id))
    if g3r.retco != 0:
        return None, None
    item_id = int(g3r.result)
    tst_tplate = db.sel_tst_tplate_by_item_id(item_id).result
    return tst_tplate, tst_tplate.item_by_id(item_id)
