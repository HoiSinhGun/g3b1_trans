"""Trans commands """
import logging
from builtins import int

from telegram import Update, Message
from telegram.ext import CallbackContext

import trans
import trans.data
from g3b1_data import settings, elements
from g3b1_data.elements import *
from g3b1_data.entities import *
from g3b1_data.settings import chat_user_setting
from g3b1_log.g3b1_log import cfg_logger
from g3b1_serv import tg_reply, utilities, tgdata_main
from g3b1_serv.tg_reply import bold, code
from g3b1_serv.utilities import TgColumn, TableDef, g3_m_dct
from subscribe.data import db as subscribe_db
from subscribe.serv import services as subscribe_services
from subscribe.serv.services import for_user
from trans.data import db
from trans.ui.utilities import *
from trans.data.model import TxtSeq, TstTemplateIt
from trans.serv import services, internal
from trans.serv.internal import lc_check
from trans.serv.services import execute_split

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


@tgdata_main.tg_handler()
def cmd_li_user(upd: Update) -> None:
    """List the users id/uname for the bot"""
    subscribe_services.tbl_chat_user_send(upd, trans.data.Engine_TRANS)


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
        db.iup_setting(settings.chat_setting(chat_id, ELE_TYP_cmd, cmd_set))

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TYP_cmd)).result
    setng_dct: dict[str, str] = {str(ELE_TYP_cmd['id']): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@tgdata_main.tg_handler()
def cmd_setng_send_onyms(upd: Update, chat_id: int, user_id: int):
    """Switches on or off sending synonyms and antonyms to user private chat."""

    setting = db.read_setting(settings.chat_setting(chat_id, ELE_TYP_send_onyms)).result
    if setting:
        setting = 0
    else:
        setting = 1
    db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TYP_send_onyms, str(setting)))

    setng_dct: dict[str, str] = {str(ELE_TYP_send_onyms['id']): str(setting)}
    tg_reply.send_settings(upd, setng_dct)


@tgdata_main.tg_handler()
def cmd_languages(upd: Update):
    """Display supported languages"""
    reply_string = '\n'.join(trans.LC_li)
    reply_string = 'Supported languages: \n\n<code>' + reply_string + '</code>'
    upd.effective_message.reply_html(reply_string)


@tgdata_main.tg_handler()
def cmd_lc(upd: Update, chat_id, user_id, lc: str, fallback: str):
    """Set source language code for this chat.
    Use /lc %lc x to set the source language code as fallback for all chats."""
    i_cmd_lc(upd, chat_id, user_id, lc, True, fallback)


def i_cmd_lc(upd: Update, chat_id, user_id, lc: str, is_hdl_retco=True, fallback: str = None):
    services.reg_user_if_new(chat_id, user_id)
    if not lc:
        tg_reply.cmd_p_req(upd, 'lc')
        return
    lc = lc.upper()
    if not lc_check(upd, lc):
        cmd_languages(upd)
        return

    if fallback and fallback.lower() == 'x':
        retco = db.iup_setting(settings.user_setting(user_id, ELE_TYP_lc, lc)).retco
    else:
        retco = db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc, lc)).retco
    if is_hdl_retco:
        utilities.hdl_retco(upd, logger, retco)


@tgdata_main.tg_handler()
def cmd_lc2(upd: Update, chat_id, user_id, lc_2: str, fallback: str):
    """Set target language code for this chat.
    Use /lc2 %lc x to set the target language code as fallback for all chats."""
    i_cmd_lc2(upd, chat_id, user_id, lc_2, True, fallback)


def i_cmd_lc2(upd: Update, chat_id, user_id, lc_2: str, is_handle_retco=True, fallback: str = None):
    services.reg_user_if_new(chat_id, user_id)
    if not lc_2:
        tg_reply.cmd_p_req(upd, 'lc')
        return
    lc_2 = lc_2.upper()
    if lc_2 not in trans.LC_li:
        upd.effective_message.reply_html(f'Language code {lc_2} unknown')
        cmd_languages(upd)
    if fallback and fallback.lower() == 'x':
        retco = db.iup_setting(settings.user_setting(user_id, ELE_TYP_lc2, lc_2)).retco
    else:
        retco = db.iup_setting(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc2, lc_2)).retco
    if is_handle_retco:
        utilities.hdl_retco(upd, logger, retco)


@tgdata_main.tg_handler()
def cmd_lc_pair(upd: Update, chat_id, user_id, lc_pair: str, for_uname: str = None):
    """Example: /lc_pair DE-EN"""
    lc_pair = lc_pair.strip()
    if len(lc_pair) != 5:
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

    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc)).result
    lc_2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc2)).result

    i_cmd_lc(upd, chat_id, for_user_id, lc_2, False)
    i_cmd_lc2(upd, chat_id, for_user_id, lc, False)
    i_cmd_lc_view(upd, chat_id, for_user_id, for_uname)


@tgdata_main.tg_handler()
def cmd_lc_view(upd: Update, chat_id, user_id, for_uname: str):
    """Display lc settings"""
    i_cmd_lc_view(upd, chat_id, user_id, for_uname)


def i_cmd_lc_view(upd: Update, chat_id, user_id, for_uname: str):
    """Displays .lc -> .lc_2"""
    for_user_id = for_user(for_uname, user_id)
    if not for_user_id:
        tg_reply.cmd_err(upd)
        return
    lc = db.read_setting_w_fback(
        settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc))
    lc_2 = db.read_setting_w_fback(
        settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc2))
    reply_str = f'{lc.result} -> {lc_2.result}'
    if for_uname:
        reply_str = f'User: <b>{for_uname}</b>\n\n{reply_str}'

    upd.effective_message.reply_html(reply_str)


@tgdata_main.tg_handler()
def cmd_xx2xx(upd: Update, chat_id: int, user_id: int, text: str):
    cmd_split = upd.effective_message.text.split(' ', 1)[0].split('2')
    lc = cmd_split[0][1:].upper()
    lc2 = cmd_split[1].upper()
    if lc == 'XX' or lc == 'X':
        lc = db.read_setting_w_fback(
            settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc)).result
    if lc2 == 'XX' or lc2 == 'X':
        lc2 = db.read_setting_w_fback(
            settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc2)).result
    if not lc_check(upd, lc):
        return
    if not lc_check(upd, lc2):
        return
    services.hdl_cmd_reply_trans(upd, None, user_id, text, lc, lc2)


@tgdata_main.tg_handler()
def cmd_t(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the last message or the replied to message to text.
    If text is empty, the bot will translate itself.
    """
    lc, lc2 = services.read_lc_settings_w_fback(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc, lc2,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li)


@tgdata_main.tg_handler()
def cmd_t__v(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc, lc2 = services.read_lc_settings_w_fback(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc, lc2,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_v)


@tgdata_main.tg_handler()
def cmd_t__b(upd: Update, src_msg: Message, chat_id: int, user_id: int, text: str):
    """ Translate the replied to message to trg_text
    """
    lc, lc2 = services.read_lc_settings_w_fback(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, text, lc, lc2,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_vb)


@tgdata_main.tg_handler()
def cmd_t__r(upd: Update, src_msg: Message, chat_id: int, user_id: int, trg_text: str):
    """ Translate the source message and then back again to the original lc.
    """
    lc, lc2 = services.read_lc_settings_w_fback(chat_id, user_id)
    txt_map_li = services.hdl_cmd_reply_trans(upd, src_msg, user_id, trg_text, lc, lc2, is_send_reply=False)
    if len(txt_map_li) < 1:
        tg_reply.cmd_err(upd)
    for txt_map in txt_map_li:
        services.hdl_cmd_reply_trans(upd, None, user_id, txt_map.txtlc_trg.txt, lc2, lc,
                                     services.i_reply_str_from_txt_map_li_v)


@tgdata_main.tg_handler()
def cmd_repl__ta(upd: Update, src_msg: Message, chat_id: int, user_id: int):
    """ The bot translates the last message or the replied to message. In the result toi/ban will be
    replaced by anh/em
    """
    lc, lc2 = services.read_lc_settings_w_fback(chat_id, user_id)
    services.hdl_cmd_reply_trans(upd, src_msg, user_id, '', lc, lc2,
                                 reply_string_builder=services.i_reply_str_from_txt_map_li_repl_ta)


@tgdata_main.tg_handler()
def cmd_s(upd: Update, src_msg: Message,
          chat_id: int, user_id: int,
          split_str: str = None):
    """ Split command. E.g. /s 3,5,7 -> split after the 3rd, 5th and 7th word
    """
    src_msg_text = src_msg.text
    if not split_str:
        split_str = '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc)).result
    lc_2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc2)).result

    execute_split_and_send(chat_id, lc, lc_2, split_str, src_msg_text, upd, user_id)


@tgdata_main.tg_handler()
def cmd_ss(upd: Update, chat_id: int, user_id: int, op: str):
    if not op:
        tg_reply.cmd_p_req(upd, op, 1)
        return
    txt_seq: TxtSeq = services.find_curr_txt_seq(chat_id, user_id)
    src_msg_text = txt_seq.txtlc_src.txt
    split_str = services.split_on_split(txt_seq.seq_str, op).result
    lc = txt_seq.lc
    lc_2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, user_id, ELE_TYP_lc2)).result

    execute_split_and_send(chat_id, lc, lc_2, split_str, src_msg_text, upd, user_id)


def execute_split_and_send(chat_id, lc, lc_2, split_str, src_msg_text, upd, user_id):
    trans_dct, txt_map_li = execute_split(lc, lc_2, split_str, src_msg_text)
    services.ins_seq_if_new(src_msg_text, lc, lc_2, txt_map_li, chat_id, user_id)
    tbl_def = TableDef(
        dict(src=TgColumn('src', -1, 'src', 30), trg=TgColumn('trg', -1, 'trg', 30)))
    reply_str = f'Split positions: {tg_reply.bold(split_str)}\n\n'
    tg_reply.send_table(upd, tbl_def, trans_dct, reply_str)


@tgdata_main.tg_handler()
def cmd_msg_latest(upd: Update, reply_to_user_id: int, chat_id: int, user_id: int):
    """Display the latest message of the replied to user or the current user_id"""
    for_user_id = user_id
    if reply_to_user_id:
        for_user_id = reply_to_user_id
    msg = utilities.read_latest_message(chat_id, for_user_id)
    tg_reply.print_msg(upd, msg)


@tgdata_main.tg_handler()
def cmd_tst_help(upd: Update, chat_id: int, user_id: int):
    """Showing information about what you can do based on your settings."""
    reply_str = ''
    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_mode))
    if g3r.retco != 0:
        i_set_tst_mode_and_notify(upd, chat_id, user_id, 1)
    tst_mode: int = int(db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_mode)).result)
    tst_tplate = internal.i_tst_template_by_setng(chat_id, user_id)
    tst_tplate_item: TstTemplateIt
    if tst_tplate:
        reply_str += f'Selected test: {bold(tst_tplate.bkey)}\n\n'
    if tst_mode == 1:
        # if not tst_template then need to pick one first with tst_take
        # else proceed with tst_qt
        tst_tplate, tst_tplate_item = internal.i_tst_tplate_item_by_setng(chat_id, user_id)
        if not tst_tplate or not tst_tplate_item:
            reply_str += f'Call /tst_take %bkey% to take an existing test\n'
        if tst_tplate_item:
            reply_str += f'Current task/question:\n{tst_tplate_item.txtlc_qt.txt}'
            reply_str += f'Answer the task by calling /tst_ans %ans_txt%'
    elif tst_mode == 2:
        # if not tst_template then need to pick one first eg by creating one
        # tst_gen_v / tst_new
        # then qt, ans
        if not tst_tplate:
            reply_str += f'Call /tst_new %bkey% to create a new test\n'
        else:
            tst_tplate, tst_tplate_item = internal.i_tst_tplate_item_by_setng(chat_id, user_id)
            if not tst_tplate_item:
                reply_str += f'Add a new question with /tst_qt %qt_str%'
            else:
                reply_str += f'{tst_tplate_item.label()}'
    tg_reply.reply(upd, reply_str)


@tgdata_main.tg_handler()
def cmd_tst_info(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Print information about the test having %bkey%"""
    g3r = db.sel_tst_tplate_by_bk(bkey)
    if g3r.result != 0:
        tg_reply.cmd_err()
    tst_template = g3r.result
    lbl = tst_template_lbl(tst_template)


@tgdata_main.tg_handler()
def cmd_tst_ed(upd: Update, chat_id: int, user_id: int):
    """Switch to Edit mode to create new tests"""
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 2)


@tgdata_main.tg_handler()
def cmd_tst_exe(upd: Update, chat_id: int, user_id: int):
    """Switch to Execution mode to take the tests"""
    i_set_tst_mode_and_notify(upd, chat_id, user_id, 1)


def i_set_tst_mode_and_notify(upd: Update, chat_id: int, user_id: int, tst_mode: int, read_first=False):
    if read_first:
        g3r = db.read_setting(chat_user_setting(chat_id, user_id, elements.ELE_TYP_tst_mode))
        if g3r.retco == 0 and g3r.result == tst_mode:
            # nothing to do, tst_mode already set accordingly
            return
    setng_dct = chat_user_setting(chat_id, user_id, elements.ELE_TYP_tst_mode, str(tst_mode))
    db.iup_setting(setng_dct)
    tg_reply.send_settings(upd, setng_dct)


@tgdata_main.tg_handler()
def cmd_tst_take(upd: Update, chat_id: int, user_id: int, bkey: str):
    """Take the test with the given bkey."""
    if not bkey:
        tg_reply.cmd_p_req(upd, 'bkey')
        return
    g3r = db.sel_tst_tplate_by_bk(bkey)
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
    g3r = internal.i_iup_tst_template_it(chat_id, user_id, tst_template_it)
    if g3r != 0:
        tg_reply.reply(upd, f'Storing tst_template setting failed!')
    else:
        tg_reply.cmd_success(upd)
    tg_reply.reply(upd, f'Call tst_qt to read the first question. Separate alternative answers row breaks!')


@tgdata_main.tg_handler()
def cmd_tst_types(upd: Update):
    """Display the types of tests"""
    i_tst_types(upd)


def i_tst_types(upd: Update):
    reply_str = ''
    for i in trans.data.TST_TY_LI:
        reply_str += f'{str(i["id"]).rjust(4)} = {i["bkey"].ljust(40)}\n{i["descr"].ljust(40)}\n\n'
    upd.effective_message.reply_html(code(reply_str))


@tgdata_main.tg_handler()
def cmd_tst_new(upd: Update, ctx: CallbackContext, chat_id: int, user_id: int, tst_type: str, bkey: str):
    """Insert a new tst_template of the given type with the given bkey."""
    if not tst_type:
        tg_reply.cmd_p_req(upd, 'tst_type')
        i_tst_types(upd)
        return

    if not bkey:
        bkey = utilities.now_for_sql()

    g3r = db.sel_tst_tplate_by_bk(bkey)
    if g3r.retco == 0:
        tg_reply.cmd_err_key_exists(upd, ENT_TYP_tst_template['descr'], bkey)
        return

    lc_tup = services.read_lc_settings_w_fback(chat_id, user_id)
    tst_template = services.create_test(tst_type, bkey, [], *lc_tup)
    if tst_template:
        g3r = internal.i_iup_tst_template(chat_id, upd.effective_user.id, tst_template)
        if g3r.retco == 0:
            tg_reply.cmd_success(upd)
            cmd_tst_help(upd, ctx)
        else:
            tg_reply.reply(upd, f'Storing tst template setting failed')
    else:
        tg_reply.cmd_err(upd)


@tgdata_main.tg_handler()
def cmd_tst_qt(upd: Update, chat_id: int, user_id: int, qt_str: str):
    """Depending on setting tst_mode:
     tst_mode_execute: Ask the student the question
     tst_mode_edit: Create a question based on the text passed to the command
     """

    tst_tplate = internal.i_tst_template_by_setng(chat_id, user_id)

    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_mode))
    if g3r.retco != 0:
        tg_reply.cmd_err_setng_miss(upd, ELE_TYP_tst_mode)
        return

    tst_mode = g3r.result
    if tst_mode == 1:
        tst_tplate, tst_tplate_item = internal.i_tst_tplate_item_by_setng(chat_id, user_id)
        if not tst_tplate or not tst_tplate_item:
            tg_reply.reply(upd, f'Please execute first /tst_take %bkey% to take a test.')
            return
        internal.i_tst_qt_mode_exe(upd, tst_tplate, tst_tplate_item)
    elif tst_mode == 2:
        internal.i_tst_qt_mode_edit(upd, chat_id, user_id, tst_tplate, qt_str)


@tgdata_main.tg_handler()
def cmd_tst_ans(upd: Update, chat_id: int, user_id: int, ans_str: str):
    """Depending on setting tst_mode:
     tst_mode_execute: Answer the question of the current item
     tst_mode_edit: Add an answer to the question of the current item
     """

    tst_tplate_it: TstTemplateIt
    tst_tplate, tst_tplate_it = internal.i_tst_tplate_item_by_setng(chat_id, user_id)

    if not tst_tplate_it:
        upd.effective_message.reply_html(f'Current item not set. It will be set when you request'
                                         f' or add the next question'
                                         f'with /tst_qt')
        return

    if not ans_str:
        tg_reply.cmd_p_req(upd, 'ans_str')
        upd.effective_message.reply_html(f'Question of current item {tst_tplate_it.itnum}:\n\n'
                                         f'{code(tst_tplate_it.txtlc_qt.txt)}')
        return

    g3r = db.read_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_mode))
    if g3r.retco != 0:
        tg_reply.cmd_err_setng_miss(upd, ELE_TYP_tst_mode)
        return

    tst_mode = g3r.result
    if tst_mode == 1:
        tst_tplate_it_next = internal.i_tst_ans_mode_exe(upd, tst_tplate, tst_tplate_it, ans_str)

        ele_val: str
        if tst_tplate_it_next:
            ele_val = str(tst_tplate_it_next.id_)
        else:
            ele_val = 'None'
        db.iup_setting(chat_user_setting(chat_id, user_id, ELE_TYP_tst_template_it_id, ele_val))
    elif tst_mode == 2:
        internal.i_tst_ans_mode_edit(upd, tst_tplate, tst_tplate_it, ans_str)


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
    tst_template = services.create_test(trans.data.TST_TY_VOCABULARY['bkey'], bkey, txt_map_li, *lc_tup)
    g3r = internal.i_iup_tst_template(chat_id, upd.effective_user.id, tst_template)
    if g3r != 0:
        tg_reply.reply(upd, f'Storing tst_template setttig failed')
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
    lc = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc)).result
    lc_2 = db.read_setting_w_fback(settings.chat_user_setting(chat_id, for_user_id, ELE_TYP_lc2)).result
    msg_dct_li, txt_map_li = services.translate_all_since(reply_to_msg, lc, lc_2)
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
            reply_str = f'<b>{lc}</b>\n{src_str}\n\n<b>{lc_2}</b>\n{trg_str}'
            upd.effective_message.reply_html(reply_str, reply_to_message_id=None)
            src_str = ''
            trg_str = ''
    reply_str = f'<b>{lc}</b>\n{src_str}\n\n<b>{lc_2}</b>\n{trg_str}'
    upd.effective_message.reply_html(reply_str, reply_to_message_id=None)


@tgdata_main.tg_handler()
def cmd_telex(upd: Update):
    """Show telex hints"""
    col_dct = dict(
        c1=TgColumn('c1', -1, 'Ton', 23),
        c2=TgColumn('c2', -1, 'Eingabe', 17),
        c3=TgColumn('c3', -1, 'Beispiel', 20)
    )
    hint_dct = {
        1: {'c1': 'konstant', 'c2': 'nichts (oder z)', 'c3': 'ngang -> ngang'},
        2: {'c1': 'fallend', 'c2': 'f', 'c3': 'huyeenf -> huyen'},
        3: {'c1': 'steigend', 'c2': 's', 'c3': 'sawcs -> sac'},
        4: {'c1': 'unterbrochen steigend', 'c2': 'r', 'c3': 'hoir -> hoi'},
        5: {'c1': 'hoch steigend', 'c2': 'x', 'c3': 'ngax -> nga'},
        6: {'c1': 'tief fallend', 'c2': 'j', 'c3': 'nawngj -> nang'}
    }
    tbl_def = utilities.TableDef(cols=col_dct)
    tbl = utilities.dc_dic_to_table(hint_dct, tbl_def)
    reply_str: str = utilities.table_print(tbl)
    upd.effective_message.reply_html(
        f'<code>{reply_str}</code>'
    )
