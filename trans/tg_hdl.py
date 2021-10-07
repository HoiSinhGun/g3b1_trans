"""Trans commands """
import re
from builtins import int

from telegram import Update, Message
from telegram.ext import CallbackContext

import generic_hdl
import tg_hdl_txt_menu
import trans
import trans.data
from data.enums import LcPair
from data.model import TxtSeq, Txtlc
from entities import G3_M_TRANS
from g3b1_cfg.tg_cfg import sel_g3_m, G3Ctx, g3_cmd_by
from g3b1_log.log import *
from g3b1_serv import utilities
from g3b1_ui.model import TgUIC
from g3b1_ui.ui_mdl import IdxRngSel
from generic_hdl import send_ent_ty_keyboard
from model import Menu
from serv.services import hdl_cmd_languages, i_cmd_lc, i_cmd_lc2, i_cmd_lc_view, hdl_cmd_setng_cmd_prefix, \
    txt_seq_03, i_tst_qt_mode_edit, cmd_string, tst_tplate_it_ans_01, txt_seq_01, \
    write_to_setng, init_4_kb
from serv.services_txt_menu import txt_menu
from sql_utils import dc_dic_2_tbl, tbl_2_str
from subscribe.data import db as subscribe_db
from subscribe.data.db import eng_SUB, md_SUB
from subscribe.serv import services as subscribe_services
from subscribe.serv.services import for_user
from trans.data import ELE_TY_txt_seq_id, ELE_TY_tst_run_id
from trans.data import ENT_TY_txt_seq, ENT_TY_tst_tplate, ENT_TY_tst_run
from trans.data import eng_TRANS, md_TRANS
from trans.serv import internal
from trans.serv import services
from trans.serv.internal import *

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


@generic_hdl.tg_handler()
def cmd_go2():
    send_ent_ty_keyboard(ENT_TY_tst_run)


@generic_hdl.tg_handler()
def cmd_li_user(upd: Update, chat_id: int) -> None:
    """List the users id/uname for the bot"""
    subscribe_services.tbl_chat_user_send(upd, chat_id, eng_TRANS, md_TRANS, i_user_dct_append_lc_pair)


@generic_hdl.tg_handler()
def cmd_su_exit() -> None:
    """Exit SU (switch user)"""
    setng = settings.cu_setng(ELE_TY_su__user_id)
    setng['user_id'] = G3Ctx.user_id()
    settings.iup_setting(eng_SUB, md_SUB, setng)


@generic_hdl.tg_handler()
def cmd_su(req__user_id: id) -> None:
    """SU (switch user)"""
    setng = settings.cu_setng(ELE_TY_su__user_id, req__user_id)
    setng['user_id'] = G3Ctx.user_id()
    settings.iup_setting(eng_SUB, md_SUB, setng)


@generic_hdl.tg_handler()
def cmd_out_chat(trg_chat_id: str) -> None:
    """Set chat for output"""
    setng = settings.cu_setng(ELE_TY_out__chat_id, trg_chat_id)
    setng['user_id'] = G3Ctx.user_id()
    settings.iup_setting(eng_SUB, md_SUB, setng)
    TgUIC.uic.cmd_sccs()


@generic_hdl.tg_handler()
def cmd_subscribe(upd: Update, chat_id: int, user_id: int, subst_user_id: int = None):
    """ Subscribe for chat/user and basic setup for the user.
    """
    if subst_user_id:
        user_id = subst_user_id
    subscribe_db.ins_bcu(chat_id, user_id, trans.data.BOT_BKEY_TRANS)
    # db.ins_user_setting_default(user_id)
    tg_reply.cmd_success(upd)


@generic_hdl.tg_handler()
def cmd_cmd_default(upd: Update, chat_id: int, cmd_set: str):
    """Set the default cmd for messages without leading command.
    Eg /cmd_default t, use without arguments to view the current setting"""
    if cmd_set and cmd_set not in sel_g3_m(G3_M_TRANS).cmd_dct.keys() \
            and cmd_set != 'None':
        upd.effective_message.reply_html(f'The command {cmd_set} does not exist!')
        cmd_set = ''

    if cmd_set:
        db.iup_setting(settings.chat_setting(chat_id, ELE_TY_cmd, cmd_set))

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TY_cmd)).result
    setng_dct: dict[str, str] = {str(ELE_TY_cmd.id_): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@generic_hdl.tg_handler()
def cmd_setng_send_onyms(upd: Update, chat_id: int, user_id: int):
    """Switches on or off sending synonyms and antonyms to user private chat."""

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TY_send_onyms)).result
    if setting:
        setting = 0
    else:
        setting = 1
    db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TY_send_onyms, str(setting)))

    setng_dct: dict[str, str] = {str(ELE_TY_send_onyms.id): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@generic_hdl.tg_handler()
def cmd_setng_cmd_prefix(upd: Update, cmd_prefix: str):
    """Set the cmd prefix which replaces triple dot"""
    hdl_cmd_setng_cmd_prefix(upd, cmd_prefix)


@generic_hdl.tg_handler()
def cmd_languages(upd: Update):
    """Display supported languages"""
    hdl_cmd_languages(upd)


@generic_hdl.tg_handler()
def cmd_lc(upd: Update, chat_id, user_id, lc: str, fallback: str):
    """Set source language code for this chat.
    Use /lc %lc x to set the source language code as fallback for all chats."""
    i_cmd_lc(upd, chat_id, user_id, lc, True, fallback)


@generic_hdl.tg_handler()
def cmd_lc2(upd: Update, chat_id, user_id, lc2: str, fallback: str):
    """Set target language code for this chat.
    Use /lc2 %lc x to set the target language code as fallback for all chats."""
    i_cmd_lc2(upd, chat_id, user_id, lc2, True, fallback)


@generic_hdl.tg_handler()
def cmd_lc_pair(upd: Update, chat_id, user_id, lc_pair: str, for_uname: str = None):
    """Example: /lc_pair DE-EN"""
    if not lc_pair:
        tg_reply.cmd_p_req(upd, 'lc_pair')
        return
    lc_pair = lc_pair.strip()
    if len(lc_pair) != 5 or len(lc_pair.split('-')) != 2:
        tg_reply.cmd_err(upd)
        return
    for_user_id = for_user(for_uname, user_id)
    if not for_user_id:
        tg_reply.cmd_err(upd)
        return

    i_cmd_lc(upd, chat_id, for_user_id, lc_pair[:2].upper(), False)
    i_cmd_lc2(upd, chat_id, for_user_id, lc_pair[3:5].upper(), False)
    i_cmd_lc_view(upd, chat_id, user_id, for_uname)


@generic_hdl.tg_handler()
def cmd_lc_swap(upd: Update, chat_id: int, user_id: int, for_uname: str = None):
    """Swap the lc source - target"""
    for_user_id = for_user(for_uname, user_id)
    if not for_user_id:
        tg_reply.cmd_err(upd)
        return

    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TY_lc)).result
    lc2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TY_lc2)).result

    i_cmd_lc(upd, chat_id, for_user_id, lc2, False)
    i_cmd_lc2(upd, chat_id, for_user_id, lc, False)
    i_cmd_lc_view(upd, chat_id, for_user_id, for_uname)


@generic_hdl.tg_handler()
def cmd_lc_view(upd: Update, chat_id, user_id, for_uname: str):
    """Display lc settings"""
    i_cmd_lc_view(upd, chat_id, user_id, for_uname)


@generic_hdl.tg_handler()
def cmd_menu(upd: Update, ctx: CallbackContext, mi_str: str) -> None:
    mi_str_split = mi_str.split(' ', 1)
    setng_bkey: str = mi_str_split[0].split(':')[0]
    cmd_sfx: str = mi_str_split[0].split(':')[1]
    cmd_str = mi_str_split[0].replace(':', '_')

    g3_cmd = g3_cmd_by(cmd_str)
    if len(mi_str_split) == 2:
        ctx.args = mi_str_split[1].split(' ')
    f_send = TgUIC.uic.f_send
    TgUIC.f_send = False
    g3_cmd.handler(upd, ctx)
    TgUIC.f_send = f_send


@generic_hdl.tg_handler()
def cmd_txt_menu_rnd(lc_str: str):
    rnd_txt = tg_hdl_txt_menu.rnd(lc_str)
    txt_menu(rnd_txt)


@generic_hdl.tg_handler()
def cmd_txt_menu_reset(cur__txt: str):
    """⏮ """
    txt = tg_hdl_txt_menu.reset(cur__txt)
    txt_menu(txt, TgUIC.get_send_str_li())


@generic_hdl.tg_handler()
def cmd_txt_menu_rview_ok(cur__txtlc: Txtlc, cur__lc2: Lc):
    """👍 """
    TgUIC.f_send = True
    tg_hdl_txt_menu.rview('2', cur__txtlc, cur__lc2)
    # call next command
    g3_ctx_dct = G3Ctx.as_dict()
    G3Ctx.ctx.args = [cur__txtlc.lc.value]
    cmd_txt_menu_rnd(G3Ctx.upd, G3Ctx.ctx)
    G3Ctx.from_dict(g3_ctx_dct)


@generic_hdl.tg_handler()
def cmd_txt_menu_rview_no(cur__txtlc: Txtlc, cur__lc2: Lc):
    """👎 """
    TgUIC.f_send = True
    tg_hdl_txt_menu.rview('1', cur__txtlc, cur__lc2)
    # call next command
    g3_ctx_dct = G3Ctx.as_dict()
    G3Ctx.ctx.args = [cur__txtlc.lc.value]
    cmd_txt_menu_rnd(G3Ctx.upd, G3Ctx.ctx)
    G3Ctx.from_dict(g3_ctx_dct)


@generic_hdl.tg_handler()
def cmd_txt_menu_tlt(cur__txtlc: Txtlc, cur__lc2: Lc, cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    """❓ """
    tg_hdl_txt_menu.tlt(cur__txtlc, cur__lc2)
    txt_menu(cur__txt, TgUIC.get_send_str_li(), cur__sel_idx_rng)


@generic_hdl.tg_handler()
def cmd_txt_menu_it_tgl(req__idx_str: str, cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    sel_idx_rng = tg_hdl_txt_menu.it_tgl(req__idx_str, cur__txt, cur__sel_idx_rng)
    txt_menu(cur__txt, TgUIC.get_send_str_li(), sel_idx_rng)


@generic_hdl.tg_handler()
def cmd_txt_menu_it_13(cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    """🔗 """
    tg_hdl_txt_menu.it_13(cur__txt, cur__sel_idx_rng)
    txt_menu(cur__txt, TgUIC.get_send_str_li(), cur__sel_idx_rng)


@generic_hdl.tg_handler()
def cmd_txt_menu_it_tlt(cur__txt: str, cur__sel_idx_rng: IdxRngSel, cur__lc_pair: LcPair):
    """ℹ """
    tg_hdl_txt_menu.it_tlt(cur__txt, cur__sel_idx_rng, cur__lc_pair)
    txt_menu(cur__txt, TgUIC.get_send_str_li(), cur__sel_idx_rng)


@generic_hdl.tg_handler()
def cmd_txt_menu_it_ccat(cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    """➕ """
    new_txt = tg_hdl_txt_menu.it_ccat(cur__txt, cur__sel_idx_rng)
    txt_menu(new_txt, TgUIC.get_send_str_li(), cur__sel_idx_rng)


@generic_hdl.tg_handler()
def cmd_txt_13(txt: str):
    """Find %txt% in the dictionary of the users current source language (check with .lc.view)"""
    if not txt:
        TgUIC.uic.err_p_miss(ELE_TY_txt)
        return

    services.txt_13(txt)


@generic_hdl.tg_handler()
def cmd_xx2xx(upd: Update, chat_id: int, user_id: int, text: str):
    cmd_split = upd.effective_message.text.split(' ', 1)[0].split('2')
    lc_str = cmd_split[0][1:].upper()
    lc2_str = cmd_split[1].upper()
    if lc_str == 'XX' or lc_str == 'X':
        lc_str = db.read_setting_w_fback(
            settings.chat_user_setting(chat_id, user_id, ELE_TY_lc)).result
    if lc2_str == 'XX' or lc2_str == 'X':
        lc2_str = db.read_setting_w_fback(
            settings.chat_user_setting(chat_id, user_id, ELE_TY_lc2)).result
    if not (lc := lc_check(upd, lc_str)):
        return
    if not (lc2 := lc_check(upd, lc2_str)):
        return
    # noinspection PyTypeChecker
    services.hdl_cmd_reply_trans(upd, None, user_id, text, (lc, lc2))


@generic_hdl.tg_handler()
def cmd_t(upd: Update, src_msg: Message, user_id: int, text: str):
    """ Translate the last message or the replied to message to text.
    If text is empty, the bot will translate itself.
    """
    lc_pair = services.read_setng_lc_pair()
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li)


@generic_hdl.tg_handler()
def cmd_t__v(upd: Update, src_msg: Message, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.read_setng_lc_pair()
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_v)


@generic_hdl.tg_handler()
def cmd_t__b(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.read_setng_lc_pair()
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_vb)


@generic_hdl.tg_handler()
def cmd_t__u(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.read_setng_lc_pair()
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_srcus)


@generic_hdl.tg_handler()
def cmd_t__r(upd: Update, src_msg: Message, user_id: int, trg_text: str):
    """ Translate the source message and then back again to the original lc.
    """
    lc, lc2 = services.read_setng_lc_pair()
    txt_map_li = services.hdl_cmd_reply_trans(upd, src_msg, user_id, trg_text, (lc, lc2), is_send_reply=False)
    if len(txt_map_li) < 1:
        tg_reply.cmd_err(upd)
    for txt_map in txt_map_li:
        # noinspection PyTypeChecker
        services.hdl_cmd_reply_trans(upd, None, user_id, txt_map.txtlc_trg.txt, (lc2, lc),
                                     services.i_reply_str_from_txt_map_li_v)


@generic_hdl.tg_handler()
def cmd_repl__ta(upd: Update, src_msg: Message, user_id: int):
    """ The bot translates the last message or the replied to message. In the result toi/ban will be
    replaced by anh/em
    """
    lc_pair = services.read_setng_lc_pair()
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, '', lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_repl_ta)


@generic_hdl.tg_handler()
def cmd_text_divide(req__idx_str: str, cur__txt: str):
    split: list[str] = cur__txt.split(' ')
    txt_new: str = ''
    for idx, word in enumerate(split):
        if txt_new:
            txt_new += ' '
        if idx == int(req__idx_str):
            if word.endswith('|'):
                txt_new += word.replace('|', '')
            else:
                txt_new += word + '|'
        else:
            txt_new += word
    G3Ctx.ctx.args = [txt_new]
    cmd_text_new(G3Ctx.upd, G3Ctx.ctx)


@generic_hdl.tg_handler()
def cmd_text_new(req__txt: str):
    setng = settings.cu_setng(ELE_TY_txt, req__txt)
    settings.iup_setting(eng_TRANS, md_TRANS, setng)

    # mi_list: list[MenuIt] = txt_to_menu_it(req__txt, g3_cmd_by('text_divide'))

    menu = Menu('txt_new', req__txt)
    # send_menu_keyboard(menu, mi_list)


@generic_hdl.tg_handler()
def cmd_txt_seq_01(upd: Update, src_msg: Message, text: str):
    """ Creates a sequence of the text by splitting at the operator |
        The texts will be translated by the bot.
    """
    src_str = text if text else src_msg.text
    txt = TxtSeq.smart_format(src_str)
    lc_pair = services.read_setng_lc_pair()

    txt_seq: TxtSeq = txt_seq_01(lc_pair, txt)
    write_to_setng(txt_seq)
    txt_seq_03(upd, txt_seq)


@generic_hdl.tg_handler()
def cmd_txt_seq_02(upd: Update, txt_seq_id: int):
    """Set current txt_seq by id"""
    if not txt_seq_id:
        tg_reply.cmd_p_req(upd, ELE_TY_txt_seq_id.id)
        return
    txt_seq: TxtSeq = db.sel_txt_seq(txt_seq_id).result
    if not txt_seq:
        tg_reply.cmd_err_key_not_found(upd, ENT_TY_txt_seq.descr, str(txt_seq_id))
        return
    g3r = services.write_to_setng(txt_seq)
    if g3r.retco == 0:
        tg_reply.send_settings(upd, g3r.result)


@generic_hdl.tg_handler()
def cmd_txt_seq_03(upd: Update):
    if not (txt_seq := services.txt_seq_by_setng()):
        tg_reply.cmd_err(upd)
        return

    txt_seq_03(upd, txt_seq)


# @generic_hdl.tg_handler()
# def cmd_ss(upd: Update, chat_id: int, user_id: int, op: str):
#     if not op:
#         tg_reply.cmd_p_req(upd, op, 1)
#         return
#     if not (txt_seq := services.txt_seq_by_setng(upd)):
#         tg_reply.cmd_err(upd)
#         return
#     src_msg_text = txt_seq.txtlc_src.txt
#     split_ops = services.split_on_split(txt_seq.seq_str, op).result
#     lc = txt_seq.lc
#     lc2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc2)).result
#
#     i_execute_split_and_send(upd, (lc, lc2), split_ops, src_msg_text)


@generic_hdl.tg_handler()
def cmd_msg_latest(upd: Update):
    """Display the latest message of the replied to user or the current user_id"""
    msg = utilities.read_latest_message()
    tg_reply.print_msg(upd, msg)


@generic_hdl.tg_handler()
def cmd_tst_tplate_types(upd: Update):
    """Display the types of tests"""
    i_tst_types(upd)


@generic_hdl.tg_handler()
def cmd_tst_tplate_help(upd: Update):
    """Showing information about what you can do based on your settings."""
    reply_str = ''
    tst_tplate = services.tst_tplate_by_setng()
    tst_tplate_it: TstTplateIt
    if tst_tplate:
        reply_str += f'{tst_tplate.label()}\n\n'

    # if not tst_template then need to pick one first eg by creating one
    # tst_gen_v / tst_new
    # then qt, ans
    cmd_01 = cmd_string('.tst.tplate.01')
    if not tst_tplate:
        reply_str += f'Call {cmd_01} %type% %bkey% to create a new test\n'
        tg_reply.reply(upd, reply_str)
        return
    tst_tplate, tst_tplate_it = services.tst_tplate_it_by_setng()

    cmd_qt_str = cmd_string('.tst.tplate.qt')
    cmd_qt_del_str = cmd_string('.tst.tplate.qt.del')
    cmd_ans_str = cmd_string('.tst.tplate.ans')
    add_new_qt_str = f'Add a new question with either command:\n' \
                     f'{code(cmd_qt_str + " %qt_str%")}\n' \
                     f'{code(cmd_qt_str + " ." + ENT_TY_txt_seq.id + ".")}'
    if not tst_tplate_it:
        reply_str += add_new_qt_str
        tg_reply.reply(upd, reply_str)
        return
    reply_str += f'{tst_tplate_it.build_descr()}'
    if tst_tplate_it.has_answer():
        for ans in tst_tplate_it.ans_li:
            reply_str += ans.label()
        reply_str += f'\n\nAdd more answers with {code(cmd_ans_str + " %ans_str%")}'
        reply_str += f'\n\n{add_new_qt_str}'
    else:
        reply_str += f'\n\nAdd answers with {code(cmd_ans_str + " %ans_str%")}'
    reply_str += f'\n\nRemove current question with {code(cmd_qt_del_str)}'

    # keyboard = [
    #     [
    #         InlineKeyboardButton("Option 1", callback_data='1'),
    #         InlineKeyboardButton("Option 2", callback_data='2'),
    #     ],
    #     [InlineKeyboardButton("Option 3", callback_data='3')],
    # ]
    #
    # reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(keyboard)

    tg_reply.reply(upd, reply_str)


@generic_hdl.tg_handler()
def cmd_tst_tplate_upl(req__text: str, cur__tst_tplate: TstTplate):
    str_it_li: list[str] = req__text.replace('$$$\n\n', '\n\n$$$').replace('$$$\n', '\n$$$').split('$$$')
    txt_seq_li: list[tuple[TxtSeq, list[str]]] = []
    for str_it in str_it_li:
        # ans_count = str_it.count('[')
        # noinspection RegExpRedundantEscape
        p = re.compile('\[(.*?)\]')
        ans_str_li: list[str] = p.findall(str_it)
        seq_str = '||' + str_it.replace('[', '|').replace(']', '|')
        for ans_str in ans_str_li:
            if ans_str.find('///') == -1:
                continue
            seq_str = seq_str.replace(ans_str, ans_str.split('///')[0].strip())
        seq_str = TxtSeq.smart_format(seq_str, False)
        lc_pair = services.read_setng_lc_pair()
        txt_seq: TxtSeq = txt_seq_01(lc_pair, seq_str)
        txt_seq_li.append((txt_seq, ans_str_li))

    for txt_seq, ans_str_li in txt_seq_li:
        write_to_setng(txt_seq)
        tst_tplate_it = i_tst_qt_mode_edit(cur__tst_tplate, f'.{ENT_TY_txt_seq.id}.')
        for ans_str in ans_str_li:
            it = txt_seq.it_by_txt(ans_str)
            tst_tplate_it_ans_01(cur__tst_tplate, tst_tplate_it, str(it.rowno))
    TgUIC.uic.cmd_sccs()


@generic_hdl.tg_handler()
def cmd_tst_tplate_01(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, tst_type: str, bkey: str):
    """Insert a new tst_template of the given type with the given bkey."""
    if not tst_type:
        tg_reply.cmd_p_req(upd, 'tst_type')
        i_tst_types(upd)
        return

    if not bkey:
        bkey = utilities.now_for_sql()

    g3r = db.sel_tst_tplate__bk(bkey)
    if g3r.retco == 0:
        tg_reply.cmd_err_key_exists(upd, ENT_TY_tst_tplate.descr, bkey)
        return

    lc_pair = services.read_setng_lc_pair()
    tst_template = services.create_test(tst_type, bkey, user_id, [], lc_pair)
    if tst_template:
        g3r = internal.i_iup_setng_tst_template(chat_id, upd.effective_user.id, tst_template)
        if g3r.retco == 0:
            tg_reply.cmd_success(upd)
            cmd_tst_tplate_help(upd, ctx)
        else:
            tg_reply.reply(upd, f'Storing tst template setting failed')
    else:
        tg_reply.cmd_err(upd)


@generic_hdl.tg_handler()
def cmd_tst_tplate_02(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, bkey: str):
    """Select Test Template by %bkey% for edit.

    Switch to Edit mode to create new tests.

    Args:
        upd(Update): chat-user-message data
        ctx(CallbackContext): callback context
        chat_id(int): id of chat (from upd)
        user_id(int): id of user (from upd)
        bkey(str): TstTplate's bkey
    """
    if not bkey:
        tg_reply.cmd_p_req(upd, 'bkey')
        return

    g3r = db.sel_tst_tplate__bk(bkey)
    if g3r.retco != 0:
        tg_reply.cmd_err_key_exists(upd, ENT_TY_tst_tplate.descr, bkey)
    tst_tplate: TstTplate = g3r.result
    tst_tplate_it: TstTplateIt
    if len(tst_tplate.items_wo_ans()) > 0:
        tst_tplate_it = tst_tplate.items_wo_ans()[0]
    else:
        tst_tplate_it = tst_tplate.item_first()
    internal.i_iup_setng_tst_tplate_w_it(chat_id, user_id, tst_tplate_it, tst_tplate)
    cmd_tst_tplate_help(upd, ctx)


@generic_hdl.tg_handler()
def cmd_tst_tplate_02_lc(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, lc_str_pair: str):
    lc_pair = internal.i_parse_lc_pair(upd, lc_str_pair)
    if not lc_pair:
        return

    tst_tplate = internal.i_tst_tplate_by_setng(chat_id, user_id)
    if not tst_tplate:
        TgUIC.uic.err_setng_miss(ELE_TY_tst_tplate_id)

    db.upd_tst_template_lc_pair(tst_tplate.id_, lc_pair)
    ctx.args = []
    cmd_tst_tplate_03(upd, ctx)


@generic_hdl.tg_handler()
def cmd_tst_tplate_03(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Print information about the test having %bkey%"""
    if not bkey:
        tst_tplate = internal.i_tst_tplate_by_setng(chat_id, user_id)
    else:
        g3r = db.sel_tst_tplate__bk(bkey)
        if g3r.retco != 0:
            tg_reply.cmd_err(upd)
            return
        tst_tplate = g3r.result

    send_li = services.tst_tplate_info(tst_tplate, f_trans=True)

    tg_reply.li_send(upd, send_li)


@generic_hdl.tg_handler()
def cmd_tst_tplate_del(upd: Update, bkey: str):
    """Delete tplate by bkey"""
    if not (tst_tplate := i_sel_tst_tplate_bk(upd, bkey)):
        return
    g3r = db.tst_tplate_del(tst_tplate)
    tg_reply.hdl_retco(upd, logger, g3r)


@generic_hdl.tg_handler()
def cmd_tst_tplate_qt(upd: Update, ctx: CallbackContext, qt_str: str):
    """Create a question based on the text passed to the command
     """

    tst_template = services.tst_tplate_by_setng()

    i_tst_qt_mode_edit(tst_template, qt_str)
    cmd_tst_tplate_help(upd, ctx)


@generic_hdl.tg_handler()
def cmd_tst_tplate_qt_del(upd: Update, ctx: CallbackContext):
    """Delete the current question
     """
    tst_tplate, tst_tplate_it = services.tst_tplate_it_by_setng()
    if tst_tplate_it:
        db.tst_tplate_it_del(tst_tplate_it)
    else:
        tg_reply.reply(upd, 'No question selected!')
    cmd_tst_tplate_help(upd, ctx)


@generic_hdl.tg_handler()
def cmd_tst_tplate_ans(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, ans_str: str):
    """Depending on setting tst_mode:
     tst_mode_execute: Answer the question of the current item
     tst_mode_edit: Add an answer to the question of the current item
     """
    ans_str = ans_str.strip()

    tst_tplate_it: TstTplateIt
    tst_tplate, tst_tplate_it = internal.i_tst_tplate_it_by_setng(chat_id, user_id)

    if not tst_tplate_it:
        cmd_tst_tplate_help(upd, ctx)
        return

    if not ans_str:
        tg_reply.cmd_p_req(upd, 'ans_str')
        cmd_tst_tplate_help(upd, ctx)
        return

    tst_tplate_it_ans_01(tst_tplate, tst_tplate_it, ans_str)

    cmd_tst_tplate_help(upd, ctx)


@generic_hdl.tg_handler()
def cmd_tst_gen_v(upd: Update, reply_to_msg: Message, chat_id: int, user_id, bkey: str):
    """ Generate vocabulary test
    Merge the messages from the same user starting at the replied to message.
    And generates a vocabulary test by convert those messages into items of the test
    Requires tst_mode = EDIT /tsted, the mode will be set automatically"""
    if not reply_to_msg:
        tg_reply.err_req_reply_to_msg(upd)
        return
    if not bkey:
        tg_reply.cmd_p_req(upd, 'bkey')
        return

    for_user_id = reply_to_msg.from_user.id
    lc_tup = services.read_lc_settings_w_fback(chat_id, for_user_id)
    msg_dct_li, txt_map_li = services.translate_all_since(reply_to_msg, *lc_tup)
    tst_template = services.create_test(trans.data.TST_TY_VOCABULARY['bkey'], bkey,
                                        user_id, txt_map_li, *lc_tup)
    g3r = internal.i_iup_setng_tst_template(chat_id, upd.effective_user.id, tst_template)
    if g3r != 0:
        tg_reply.reply(upd, f'Storing tst_template setng failed')
    tg_reply.cmd_success(upd)


@generic_hdl.tg_handler()
def cmd_merge(upd: Update, reply_to_msg: Message, chat_id: int, opt_str: str):
    """ Merge the messages from the same user starting at the replied to message"""
    if not reply_to_msg:
        tg_reply.err_req_reply_to_msg(upd)
        return
    if not opt_str:
        opt_str = ''
    inc_date = False
    if opt_str.find('-d') > -1:
        inc_date = True
    for_user_id = reply_to_msg.from_user.id
    lc_pair = services.read_setng_lc_pair()
    lc = lc_pair[0].value
    lc2 = lc_pair[1].value
    msg_dct_li, txt_map_li = services.translate_all_since(reply_to_msg, lc_pair)
    src_str = ''
    trg_str = ''
    for idx, msg_dct in enumerate(msg_dct_li):
        txt_map = txt_map_li[idx]
        tst = ''
        if inc_date:
            tst = f'[{bold(msg_dct["date"])}] '
        src_str += f'{tst}{txt_map.txtlc_src.txt}\n'
        trg_str += f'{tst}{txt_map.txtlc_trg.txt}\n'
        if len(src_str) + len(trg_str) > 3357:
            reply_str = f'<b>{lc}</b>\n{src_str}\n\n<b>{lc2}</b>\n{trg_str}'
            upd.effective_message.reply_html(reply_str, reply_to_message_id=None)
            src_str = ''
            trg_str = ''
    reply_str = f'<b>{lc}</b>\n{src_str}\n\n<b>{lc2}</b>\n{trg_str}'
    upd.effective_message.reply_html(reply_str, reply_to_message_id=None)


# noinspection SpellCheckingInspection
@generic_hdl.tg_handler()
def cmd_telex(upd: Update):
    """Show telex hints"""
    col_li: list[TgColumn] = [
        TgColumn('c1', -1, 'Ton', 23),
        TgColumn('c2', -1, 'Eingabe', 17),
        TgColumn('c3', -1, 'Beispiel', 20)
    ]
    hint_dct = {
        1: {'c1': 'konstant             ', 'c2': 'nichts (oder z)', 'c3': 'ngang   -> ngang'},
        2: {'c1': 'fallend              ', 'c2': 'f              ', 'c3': 'huyeenf -> huyen'},
        3: {'c1': 'steigend             ', 'c2': 's              ', 'c3': 'sawcs   -> sac'},
        4: {'c1': 'unterbrochen steigend', 'c2': 'r              ', 'c3': 'hoir    -> hoi'},
        5: {'c1': 'hoch steigend        ', 'c2': 'x              ', 'c3': 'ngax    -> nga'},
        6: {'c1': 'tief fallend         ', 'c2': 'j              ', 'c3': 'nawngj  -> nang'}
    }
    tbl_def = TableDef(col_li=col_li)
    tbl = dc_dic_2_tbl(hint_dct, tbl_def)
    reply_str: str = tbl_2_str(tbl)
    upd.effective_message.reply_html(
        f'<code>{reply_str}</code>'
    )


@generic_hdl.tg_handler()
def cmd_tst_run_01(bkey: str):
    """Run a test as student"""
    if not (tst_tplate := i_sel_tst_tplate_bk(G3Ctx.upd, bkey)):
        return
    hdl_cmd_setng_cmd_prefix(G3Ctx.upd, ENT_TY_tst_run.cmd_prefix)
    tst_run: TstRun = services.tst_run_01(tst_tplate)
    info_str: str = services.tst_run_qinfo(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_02():
    """Run the cur__tst_run as student"""
    tst_run: TstRun = services.tst_run_by_setng()
    if not tst_run:
        return TgUIC.uic.err_setng_miss(ELE_TY_tst_run_id)
    hdl_cmd_setng_cmd_prefix(G3Ctx.upd, ENT_TY_tst_run.cmd_prefix, False)
    info_str: str = services.tst_run_qinfo(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_help(upd: Update):
    """Show help"""
    tst_run: TstRun = services.tst_run_by_setng()
    services.tst_run_help(upd, tst_run)
    send_ent_ty_keyboard(init_4_kb())


@generic_hdl.tg_handler()
def cmd_tst_run_qnext(upd: Update):
    """Show next test question"""
    tst_run: TstRun = services.tst_run_by_setng()
    info_str = services.tst_run_qnext(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_qprev():
    """Show previous test question"""
    tst_run: TstRun = services.tst_run_by_setng()
    info_str = services.tst_run_qprev(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_qinfo():
    """Show test question info"""
    tst_run: TstRun = services.tst_run_by_setng()
    info_str = services.tst_run_qinfo(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_qhint(upd: Update):
    """Show test question hint"""
    tst_run: TstRun = services.tst_run_by_setng()
    info_str = services.tst_run_qhint(tst_run)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_qansw(upd: Update, text: str):
    """Answer the current question"""
    tst_run: TstRun = services.tst_run_by_setng()
    if not tst_run:
        return TgUIC.uic.err_setng_miss(ELE_TY_tst_run_id)

    info_str: str = services.tst_run_qansw(tst_run, text)
    services.tst_run_menu(tst_run, info_str)


@generic_hdl.tg_handler()
def cmd_tst_run_tinfo(upd: Update):
    """Show current test info"""
    tst_run: TstRun = services.tst_run_by_setng()
    services.tst_run_tinfo(tst_run)
    send_ent_ty_keyboard(init_4_kb())


@generic_hdl.tg_handler()
def cmd_tst_run_thint(upd: Update):
    """Show current test hint"""
    tst_run: TstRun = services.tst_run_by_setng()
    services.tst_run_thint(upd, tst_run)
    send_ent_ty_keyboard(init_4_kb())


@generic_hdl.tg_handler()
def cmd_tst_run_tfnsh(upd: Update):
    """Finish current test"""
    tst_run: TstRun = services.tst_run_by_setng()
    services.tst_run_tfnsh(upd, tst_run)
