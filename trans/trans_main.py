import logging

from telegram import Update
from telegram.ext import CallbackContext

import generic_hdl
from config.model import TransConfig
from g3b1_cfg.tg_cfg import sel_g3_m, G3Ctx
from g3b1_data import settings, tg_db
from g3b1_data.elements import ELE_TY_cmd, ELE_TY_cmd_prefix
from g3b1_data.entities import EntTy, G3_M_TRANS
from g3b1_log.log import cfg_logger
from g3b1_serv import tgdata_main, utilities
from g3b1_serv.utilities import G3Command
from g3b1_serv.utilities import is_msg_w_cmd
from serv import services_sta_menu
from serv.services_sta_menu import TyStep
from subscribe.serv import services as sub_services
from subscribe.serv.services import iup_g3_file_message
from tg_db import synchronize_user
from trans import trans__tg_hdl
from trans.data import db, md_TRANS, eng_TRANS
from trans.serv.services import translate_google, reg_user_if_new
from trans__tg_hdl import cmd_txtlc_file_01

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def hdl_start(upd: Update, ctx: CallbackContext) -> None:
    """Start menu and bot for user activation"""
    generic_hdl.init_g3_ctx(upd, ctx)

    g3_m_str = G3Ctx.g3_m_str

    settings.ins_init_setng()
    sub_services.bot_activate(g3_m_str)

    menu, mi_list = services_sta_menu.build_menu(step=TyStep('', 'lc', 'Choose your language'))

    generic_hdl.send_menu_keyboard(menu, mi_list)


def hdl_audio(upd: Update, ctx: CallbackContext) -> None:
    G3Ctx.upd = upd
    G3Ctx.ctx = ctx
    G3Ctx.g3_m_str = G3_M_TRANS
    reg_user_if_new()
    g3_file = iup_g3_file_message()
    # if not upd.effective_message.reply_to_message:
    #     return
    ctx.args = [str(g3_file.id)]
    cmd_txtlc_file_01(upd, ctx)


def hdl_message(upd: Update, ctx: CallbackContext) -> None:
    """store message to DB"""
    generic_hdl.init_g3_ctx(upd, ctx)
    g3_m_str = ctx.bot.username.split('_')[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'
    logger.debug(f'Target module: {g3_m_str}')
    # filter_r_g3cmd(utilities.)
    message = upd.effective_message
    if message.forward_from:
        settings.ins_init_setng(message.forward_from.id)
        sub_services.bot_activate(g3_m_str, user_id=message.forward_from.id)
        synchronize_user(message.forward_from)
    cmd_dct = sel_g3_m(g3_m_str).cmd_dct
    if not (text := message.text):
        text = message.caption
    if not text:
        text = ''
    if message.photo:
        text = f'{text}[IMG]\n'
    if message.video:
        text = f'{text}[VID]\n'
    matched: bool = False
    # noinspection PyTypeChecker
    g3_cmd: G3Command = None
    is_command_explicit = True
    cmd_prefix = db.read_setting(settings.chat_user_setting(
        upd.effective_chat.id, upd.effective_user.id, ELE_TY_cmd_prefix)).result
    if not is_msg_w_cmd(text):
        if text.startswith('|'):
            text = f'.txt_seq_01 {text}'
        else:
            ent_ty = EntTy.by_cmd_prefix(cmd_prefix)
            if ent_ty and ent_ty.but_cmd_def:
                text = ent_ty.get_cmd_by_but(text)
            else:
                # prefix with translates default cmd
                cmd = db.read_setting(settings.chat_setting(
                    upd.effective_chat.id, ELE_TY_cmd)).result
                if not cmd:
                    cmd = 'sta_menu_t'
                if cmd:
                    text = f'.{cmd} {text}'
        is_command_explicit = False
    if text.startswith('..') and not text.startswith('...'):
        pass
    elif text.startswith('.'):
        if text.strip() == '.':
            latest_cmd = utilities.read_latest_cmd(sel_g3_m(g3_m_str))
            text = latest_cmd.text
            is_command_explicit = False
            # pass text = utilities
        if text.startswith('...'):
            if cmd_prefix:
                text = text.replace('...', cmd_prefix, 1)
        word_li = text.split(' ')
        test_if_cmd = text[1:].strip()
        if len(word_li) > 1:
            test_if_cmd = ''
            if word_li[0] != '.':
                #  the space must occur after 2nd letter
                #  the first entry after removing the dot must be a valid cmd name
                #  or no command has been executed
                test_if_cmd = word_li[0][1:]
        if len(test_if_cmd) == 5 and test_if_cmd[2] == '2':
            test_if_cmd = 'xx2xx'
        test_if_cmd = test_if_cmd.replace('.', '_')
        if test_if_cmd == 'tr':
            test_if_cmd = 't__r'
        if test_if_cmd == 'tv':
            test_if_cmd = 't__v'
        if test_if_cmd == 'tb':
            test_if_cmd = 't__b'
        if test_if_cmd in cmd_dct.keys():
            g3_cmd = cmd_dct[test_if_cmd]
            logger.debug(f'CMD: {g3_cmd}')
            if len(word_li) > 1:
                ctx.args = word_li[1:]
            g3_cmd.handler(upd, ctx)
            matched = True
        elif test_if_cmd.endswith('33'):
            # list
            ent_str = test_if_cmd[:-3]
            ent_ty = EntTy.by_id(ent_str)
            if ent_ty:
                # Generic list command on entity of type ent_ty
                generic_hdl.cmd_ent_ty_33_li(upd, ctx, ent_ty=ent_ty)
        logger.debug(f'matched: {matched}')
    logger.debug(f"Handle message {message.message_id}")
    message.bot = ctx.bot
    if matched:
        g3_cmd_long_str = g3_cmd.long_name
        if g3_cmd_long_str in ['trans_l', 'trans_txt_13']:
            # HAAAACKKKK
            is_command_explicit = False
    else:
        g3_cmd_long_str = None
        is_command_explicit = False
    tg_db.synchronize_from_message(message, g3_cmd_long_str, is_command_explicit)


def start_bot():
    """Run the bot."""
    # str(bot_key): dict(db_row)
    TransConfig.translate_func = translate_google
    # noinspection PyUnresolvedReferences
    tgdata_main.start_bot(trans__tg_hdl.__file__, eng=eng_TRANS, md=md_TRANS,
                          hdl_for_message=hdl_message, hdl_for_audio=hdl_audio, hdl_for_start=hdl_start)


def main() -> None:
    # exec(open(tgdata_main.__file__).read())
    start_bot()
    print('Finished')


if __name__ == '__main__':
    main()
