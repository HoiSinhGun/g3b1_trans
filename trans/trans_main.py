import logging

from telegram import Update
from telegram.ext import CallbackContext

import generic_hdl
from config.model import TransConfig
from entities import EntTy
from g3b1_cfg.tg_cfg import sel_g3_m
from g3b1_data import settings, tg_db
from g3b1_data.elements import ELE_TY_cmd, ELE_TY_cmd_prefix
from g3b1_log.log import cfg_logger
from g3b1_serv import tgdata_main, utilities
from g3b1_serv.utilities import G3Command
from g3b1_serv.utilities import is_msg_w_cmd
from serv.services import translate_google
from trans import tg_hdl
from trans.data import db, md_TRANS, eng_TRANS

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def hdl_message(upd: Update, ctx: CallbackContext) -> None:
    """store message to DB"""
    generic_hdl.init_g3_ctx(upd, ctx)
    g3_m_str = ctx.bot.username.split('_')[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'
    logger.debug(f'Target module: {g3_m_str}')
    # filter_r_g3cmd(utilities.)
    message = upd.effective_message
    cmd_dct = sel_g3_m(g3_m_str).cmd_dct
    text = message.text
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
                if cmd:
                    text = f'.{cmd} {text}'
        is_command_explicit = False
    if text.startswith('..') and not text.startswith('...'):
        pass
    elif text.startswith('.'):
        if text.strip() == '.':
            latest_cmd = utilities.read_latest_cmd(upd, sel_g3_m(g3_m_str))
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
    else:
        g3_cmd_long_str = None
        is_command_explicit = False
    tg_db.synchronize_from_message(message, g3_cmd_long_str, is_command_explicit)


def start_bot():
    """Run the bot."""
    # str(bot_key): dict(db_row)
    TransConfig.translate_func = translate_google
    tgdata_main.start_bot(tg_hdl.__file__, eng=eng_TRANS,md=md_TRANS,hdl_for_message=hdl_message)


def main() -> None:
    # exec(open(tgdata_main.__file__).read())
    start_bot()
    print('Finished')


if __name__ == '__main__':
    main()
