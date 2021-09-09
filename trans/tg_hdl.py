"""Trans commands """
from builtins import int
from typing import Optional

from telegram import Update
from telegram.ext import CallbackContext

import trans
import trans.data
from data.model import TstTplate
from g3b1_serv import utilities, tgdata_main
from serv.services import hdl_cmd_languages, i_cmd_lc, i_cmd_lc2, i_cmd_lc_view, hdl_cmd_setng_cmd_prefix
from subscribe.data import db as subscribe_db
from subscribe.serv import services as subscribe_services
from subscribe.serv.services import for_user
from trans.serv import internal
from trans.serv.internal import *

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


@tgdata_main.tg_handler()
def cmd_li_user(upd: Update, chat_id: int) -> None:
    """List the users id/uname for the bot"""
    subscribe_services.tbl_chat_user_send(upd, chat_id, trans.data.Engine_TRANS, i_user_dct_append_lc_pair)


@tgdata_main.tg_handler()
def cmd_subscribe(upd: Update, chat_id: int, user_id: int, subst_user_id: int = None):
    """ Subscribe for chat/user and basic setup for the user.
    """
    if subst_user_id:
        user_id = subst_user_id
    subscribe_db.bot_activate(chat_id, user_id, trans.data.BOT_BKEY_TRANS)
    # db.ins_user_setting_default(user_id)
    tg_reply.cmd_success(upd)


@tgdata_main.tg_handler()
def cmd_cmd_default(upd: Update, chat_id: int, cmd_set: str):
    """Set the default cmd for messages without leading command.
    Eg /cmd_default t, use without arguments to view the current setting"""
    if cmd_set and cmd_set not in g3_m_dct[trans.g3_m_str_trans].cmd_dct.keys() \
            and cmd_set != 'None':
        upd.effective_message.reply_html(f'The command {cmd_set} does not exist!')
        cmd_set = ''

    if cmd_set:
        db.iup_setting(settings.chat_setting(chat_id, ELE_TY_cmd, cmd_set))

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TY_cmd)).result
    setng_dct: dict[str, str] = {str(ELE_TY_cmd.id_): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@tgdata_main.tg_handler()
def cmd_setng_send_onyms(upd: Update, chat_id: int, user_id: int):
    """Switches on or off sending synonyms and antonyms to user private chat."""

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TY_send_onyms)).result
    if setting:
        setting = 0
    else:
        setting = 1
    db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TY_send_onyms, str(setting)))

    setng_dct: dict[str, str] = {str(ELE_TY_send_onyms.id_): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@tgdata_main.tg_handler()
def cmd_setng_cmd_prefix(upd: Update, cmd_prefix: str):
    """Set the cmd prefix which replaces triple dot"""
    hdl_cmd_setng_cmd_prefix(upd, cmd_prefix)


@tgdata_main.tg_handler()
def cmd_languages(upd: Update):
    """Display supported languages"""
    hdl_cmd_languages(upd)


@tgdata_main.tg_handler()
def cmd_lc(upd: Update, chat_id, user_id, lc: str, fallback: str):
    """Set source language code for this chat.
    Use /lc %lc x to set the source language code as fallback for all chats."""
    i_cmd_lc(upd, chat_id, user_id, lc, True, fallback)


@tgdata_main.tg_handler()
def cmd_lc2(upd: Update, chat_id, user_id, lc2: str, fallback: str):
    """Set target language code for this chat.
    Use /lc2 %lc x to set the target language code as fallback for all chats."""
    i_cmd_lc2(upd, chat_id, user_id, lc2, True, fallback)


@tgdata_main.tg_handler()
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


@tgdata_main.tg_handler()
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


@tgdata_main.tg_handler()
def cmd_lc_view(upd: Update, chat_id, user_id, for_uname: str):
    """Display lc settings"""
    i_cmd_lc_view(upd, chat_id, user_id, for_uname)


@tgdata_main.tg_handler()
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


@tgdata_main.tg_handler()
def cmd_t(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the last message or the replied to message to text.
    If text is empty, the bot will translate itself.
    """
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li)


@tgdata_main.tg_handler()
def cmd_t__v(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_v)


@tgdata_main.tg_handler()
def cmd_t__b(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_vb)


@tgdata_main.tg_handler()
def cmd_t__u(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_srcus)


@tgdata_main.tg_handler()
def cmd_t__r(upd: Update, src_msg: Message, chat_id: int, user_id: int, trg_text: str):
    """ Translate the source message and then back again to the original lc.
    """
    lc, lc2 = services.setng_read_lc_pair(chat_id, user_id)
    txt_map_li = services.hdl_cmd_reply_trans(upd, src_msg, user_id, trg_text, (lc, lc2), is_send_reply=False)
    if len(txt_map_li) < 1:
        tg_reply.cmd_err(upd)
    for txt_map in txt_map_li:
        # noinspection PyTypeChecker
        services.hdl_cmd_reply_trans(upd, None, user_id, txt_map.txtlc_trg.txt, (lc2, lc),
                                     services.i_reply_str_from_txt_map_li_v)


@tgdata_main.tg_handler()
def cmd_repl__ta(upd: Update, src_msg: Message, chat_id: int, user_id: int):
    """ The bot translates the last message or the replied to message. In the result toi/ban will be
    replaced by anh/em
    """
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, '', lc_pair,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_repl_ta)


@tgdata_main.tg_handler()
def cmd_txt_seq_01(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Creates a sequence of the text by splitting at the operator |
        The texts will be translated by the bot.
    """
    src_str = text if text else src_msg.text
    split_str = internal.i_extract_split_string(src_str)
    src_str = src_str.replace('| ', ' ').replace('  ', ' ')

    lc_pair = services.setng_read_lc_pair(chat_id, user_id)

    i_execute_split_and_send(chat_id, lc_pair, split_str, src_str, upd, user_id)


@tgdata_main.tg_handler()
def cmd_txt_seq_03(upd: Update, chat_id: int, user_id: int):
    txt_seq: TxtSeq = services.find_curr_txt_seq(chat_id, user_id)
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    # if lc2 currently different, the txt_seq_it will be changed
    i_execute_split_and_send(chat_id, lc_pair, txt_seq.seq_str,
                             txt_seq.txtlc_src.txt, upd, user_id)


@tgdata_main.tg_handler()
def cmd_s(upd: Update, src_msg: Message,
          chat_id: int, user_id: int,
          split_str: str = None):
    """ Split command. E.g. /s 3,5,7 -> split after the 3rd, 5th and 7th word
    """
    src_msg_text = src_msg.text
    if not split_str:
        split_str = '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
    lc_pair = services.setng_read_lc_pair(chat_id, user_id)

    i_execute_split_and_send(chat_id, lc_pair, split_str, src_msg_text, upd, user_id)


@tgdata_main.tg_handler()
def cmd_ss(upd: Update, chat_id: int, user_id: int, op: str):
    if not op:
        tg_reply.cmd_p_req(upd, op, 1)
        return
    txt_seq: TxtSeq = services.find_curr_txt_seq(chat_id, user_id)
    src_msg_text = txt_seq.txtlc_src.txt
    split_str = services.split_on_split(txt_seq.seq_str, op).result
    lc = txt_seq.lc
    lc2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TY_lc2)).result

    i_execute_split_and_send(chat_id, (lc, lc2), split_str, src_msg_text, upd, user_id)


@tgdata_main.tg_handler()
def cmd_txt_13(upd: Update, chat_id: int, user_id: int, txt: str):
    """Find %txt% in the dictionary of the users current source language (check with .lc.view)"""
    if not txt:
        tg_reply.cmd_p_req(upd, 'txt')

    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
    txt_map_li = services.txtlc_cp_txt(lc_pair, txt)

    reply_str = ''
    for txt_map in txt_map_li:
        reply_str += f'{txt_map.txtlc_src.txt}\n{italic(txt_map.txtlc_trg.txt)}\n\n'

    tg_reply.reply(upd, reply_str)


@tgdata_main.tg_handler()
def cmd_msg_latest(upd: Update, reply_to_user_id: int, chat_id: int, user_id: int):
    """Display the latest message of the replied to user or the current user_id"""
    for_user_id = user_id
    if reply_to_user_id:
        for_user_id = reply_to_user_id
    msg = utilities.read_latest_message(chat_id, for_user_id)
    tg_reply.print_msg(upd, msg)


@tgdata_main.tg_handler()
def cmd_tst_tplate_help(upd: Update, chat_id: int, user_id: int):
    """Showing information about what you can do based on your settings."""
    reply_str = ''
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_mode))
    if g3r.retco != 0:
        i_set_tst_mode_and_notify(upd, chat_id, user_id, 1)
    tst_mode: int = int(db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_mode)).result)
    tst_tplate = internal.i_tst_tplate_by_setng(chat_id, user_id)
    tst_tplate_it: TstTplateIt
    if tst_tplate:
        reply_str += f'{tst_tplate.label()}\n\n'
    if tst_mode == 1:
        # if not tst_template then need to pick one first with tst_take
        # else proceed with tst_qt
        tst_tplate, tst_tplate_it = internal.i_tst_tplate_it_by_setng(chat_id, user_id)
        if not tst_tplate or not tst_tplate_it:
            reply_str += f'Call /tst_take %bkey% to take an existing test\n'
        if tst_tplate_it:
            reply_str += f'Current task/question:\n{tst_tplate_it.text()}'
            reply_str += f'Answer the task by calling /tst_ans %ans_str%'
    elif tst_mode == 2:
        # if not tst_template then need to pick one first eg by creating one
        # tst_gen_v / tst_new
        # then qt, ans
        if not tst_tplate:
            reply_str += f'Call /tst_new %bkey% to create a new test\n'
        else:
            tst_tplate, tst_tplate_it = internal.i_tst_tplate_it_by_setng(chat_id, user_id)
            if not tst_tplate_it:
                reply_str += f'Add a new question with /tst_tplate_qt %qt_str%'
            else:
                reply_str += f'{tst_tplate_it.label()}'
                if tst_tplate_it.has_answer():
                    for ans in tst_tplate_it.ans_li:
                        reply_str += ans.label()
                    reply_str += '\n\nAdd more answers with /tst_tplate_ans %ans_str%'
                    reply_str += '\n\nAdd a new question with /tst_tplate_qt %qt_str%'
                else:
                    reply_str += '\n\nAdd answers with /tst_tplate_ans %ans_str%'
    tg_reply.reply(upd, reply_str)


@tgdata_main.tg_handler()
def cmd_tst_tplate_exe(upd: Update, chat_id: int, user_id: int):
    """Switch to Execution mode to take the tests"""
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 1)


@tgdata_main.tg_handler()
def cmd_tst_take(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Take the test with the given bkey."""
    if not bkey:
        tg_reply.cmd_p_req(upd, 'bkey')
        return
    g3r = db.sel_tst_tplate__bk(bkey)
    if g3r.retco != 0:
        tg_reply.cmd_err(upd)
        return
    tst_template = g3r.result
    tst_template_it = tst_template.item_first()
    if not tst_template_it:
        tg_reply.reply(upd, f'{bold(bkey)} has not test items!')
        tg_reply.cmd_err(upd)
        return
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 1, True)
    g3r = internal.i_iup_setng_tst_tplate_w_it(chat_id, user_id, tst_template_it)
    if g3r != 0:
        tg_reply.reply(upd, f'Storing tst_template setting failed!')
    else:
        tg_reply.cmd_success(upd)
    tg_reply.reply(upd, f'Call tst_qt to read the first question. Separate alternative answers row breaks!')


@tgdata_main.tg_handler()
def cmd_tst_tplate_types(upd: Update):
    """Display the types of tests"""
    i_tst_types(upd)


@tgdata_main.tg_handler()
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

    lc_pair = services.setng_read_lc_pair(chat_id, user_id)
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


@tgdata_main.tg_handler()
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
    if g3r.result != 0:
        tg_reply.cmd_err_key_exists(upd, ENT_TY_tst_tplate, bkey)
    tst_tplate: TstTplate = g3r.result
    tst_tplate_it: TstTplateIt
    if len(tst_tplate.items_wo_ans()) > 0:
        tst_tplate_it = tst_tplate.items_wo_ans()[0]
    else:
        tst_tplate_it = tst_tplate.item_first()
    internal.i_iup_setng_tst_tplate_w_it(chat_id, user_id, tst_tplate_it, tst_tplate)
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 2)
    cmd_tst_tplate_help(upd, ctx)


@tgdata_main.tg_handler()
def cmd_tst_tplate_02_lc(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, lc_str_pair: str):
    lc_pair = internal.i_parse_lc_pair(upd, lc_str_pair)
    if not lc_pair:
        return

    tst_tplate = internal.i_tst_tplate_by_setng(chat_id, user_id)
    if not tst_tplate:
        tg_reply.cmd_err_setng_miss(upd, ELE_TY_tst_tplate_id)

    db.upd_tst_template_lc_pair(tst_tplate.id_, lc_pair)
    ctx.args = []
    cmd_tst_tplate_03(upd, ctx)


@tgdata_main.tg_handler()
def cmd_tst_tplate_03(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Print information about the test having %bkey%"""
    if not bkey:
        tst_tplate = internal.i_tst_tplate_by_setng(chat_id, user_id)
    else:
        g3r = db.sel_tst_tplate__bk(bkey)
        if g3r.result != 0:
            tg_reply.cmd_err(upd)
        tst_tplate = g3r.result

    reply_str = tst_tplate.label() + '\n\n'
    for i in tst_tplate.it_li:
        # noinspection PyTypeChecker
        txtlc_mapping: TxtlcMp = None
        txtlc = i.txt_seq.txtlc_src if i.txt_seq else i.txtlc_qt
        if txtlc:
            txtlc_mapping = services.find_or_ins_translation(txtlc.txt, tst_tplate.lc_pair()).result
        reply_str += i.label(txtlc_mapping) + '\n'
        for ans in i.ans_li:
            # noinspection PyTypeChecker
            txtlc_mapping = None
            txtlc_ans = ans.txt_seq_it.txtlc_trg if ans.txt_seq_it else ans.txtlc
            if txtlc_ans:
                txtlc_mapping = services.find_or_ins_translation(txtlc_ans.txt, tst_tplate.lc_pair()).result
            reply_str += ans.label(txtlc_mapping)
        reply_str += '\n\n'

    tg_reply.reply(upd, reply_str)


@tgdata_main.tg_handler()
def cmd_tst_tplate_del(upd: Update, bkey: str):
    """Delete tplate by bkey"""
    tst_tplate = i_sel_tst_tplate_bk(bkey)
    if not tst_tplate:
        return
    g3r = db.tst_tplate_del(tst_tplate)
    utilities.hdl_retco(upd, logger, g3r.retco)


@tgdata_main.tg_handler()
def cmd_tst_tplate_qt(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, qt_str: str):
    """Depending on setting tst_mode:
     tst_mode_execute: Ask the student the question
     tst_mode_edit: Create a question based on the text passed to the command
     """

    tst_template = internal.i_tst_tplate_by_setng(chat_id, user_id)

    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_mode))
    if g3r.retco != 0:
        tg_reply.cmd_err_setng_miss(upd, ELE_TY_tst_mode)
        return

    tst_mode = g3r.result
    if tst_mode == 1:
        tst_template, tst_tplate_item = internal.i_tst_tplate_it_by_setng(chat_id, user_id)
        if not tst_template or not tst_tplate_item:
            tg_reply.reply(upd, f'Please execute first /tst_take %bkey% to take a test.')
            return
        internal.i_tst_qt_mode_exe(upd, tst_template, tst_tplate_item)
    elif tst_mode == 2:
        internal.i_tst_qt_mode_edit(upd, chat_id, user_id, tst_template, qt_str)
        cmd_tst_tplate_help(upd, ctx)


@tgdata_main.tg_handler()
def cmd_tst_tplate_ans(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, ans_str: str):
    """Depending on setting tst_mode:
     tst_mode_execute: Answer the question of the current item
     tst_mode_edit: Add an answer to the question of the current item
     """
    ans_str = ans_str.strip()

    tst_tplate_it: TstTplateIt
    tst_tplate, tst_tplate_it = internal.i_tst_tplate_it_by_setng(chat_id, user_id)

    if not tst_tplate_it:
        upd.effective_message.reply_html(f'Current item not set. It will be set when you request'
                                         f' or add the next question'
                                         f'with /tst_qt')
        return

    if not ans_str:
        tg_reply.cmd_p_req(upd, 'ans_str')
        upd.effective_message.reply_html(f'Question of current item {tst_tplate_it.itnum}:\n\n'
                                         f'{code(tst_tplate_it.text())}')
        return

    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_mode))
    if g3r.retco != 0:
        tg_reply.cmd_err_setng_miss(upd, ELE_TY_tst_mode)
        return

    tst_mode = g3r.result
    if tst_mode == 1:
        tst_tplate_it_next = internal.i_tst_ans_mode_exe(upd, tst_tplate, tst_tplate_it, ans_str)

        ele_val: str
        if tst_tplate_it_next:
            ele_val = str(tst_tplate_it_next.id_)
        else:
            ele_val = 'None'
        db.iup_setting(chat_user_setting(chat_id, user_id, ELE_TY_tst_tplate_it_id, ele_val))
    elif tst_mode == 2:
        internal.i_tst_ans_mode_edit(upd, tst_tplate, tst_tplate_it, ans_str)
        cmd_tst_tplate_help(upd, ctx)


@tgdata_main.tg_handler()
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
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 1, True)

    for_user_id = reply_to_msg.from_user.id
    lc_tup = services.read_lc_settings_w_fback(chat_id, for_user_id)
    msg_dct_li, txt_map_li = services.translate_all_since(reply_to_msg, *lc_tup)
    tst_template = services.create_test(trans.data.TST_TY_VOCABULARY['bkey'], bkey,
                                        user_id, txt_map_li, *lc_tup)
    g3r = internal.i_iup_setng_tst_template(chat_id, upd.effective_user.id, tst_template)
    if g3r != 0:
        tg_reply.reply(upd, f'Storing tst_template setng failed')
    tg_reply.cmd_success(upd)


@tgdata_main.tg_handler()
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
    lc_pair = services.setng_read_lc_pair(chat_id, for_user_id)
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
@tgdata_main.tg_handler()
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
    tbl_def = utilities.TableDef(col_li=col_li)
    tbl = utilities.dc_dic_to_table(hint_dct, tbl_def)
    reply_str: str = utilities.table_print(tbl)
    upd.effective_message.reply_html(
        f'<code>{reply_str}</code>'
    )


@tgdata_main.tg_handler()
def cmd_tst_run_01(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Run a test as student"""
    tst_tplate: Optional[TstTplate] = i_sel_tst_tplate_bk(bkey)
    if not tst_tplate:
        return
    hdl_cmd_setng_cmd_prefix(upd, '.tst.run.')

    pass
