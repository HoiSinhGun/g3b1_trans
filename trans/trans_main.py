import logging

from telegram import Update
from telegram.ext import CallbackContext

from g3b1_data import settings, tg_db
from g3b1_data.elements import ELE_TYP_cmd
from g3b1_log.g3b1_log import cfg_logger
from g3b1_serv import tgdata_main, utilities
from g3b1_serv.utilities import G3Command, g3_m_dct
from g3b1_serv.utilities import is_msg_w_cmd
from trans import COLUMNS_TRANS
from trans import tg_hdl
from trans.data import db

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def hdl_message(upd: Update, ctx: CallbackContext) -> None:
    """store message to DB"""
    g3_m_str = ctx.bot.username.split('_')[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'
    logger.debug(f'Target module: {g3_m_str}')
    # filter_r_g3cmd(utilities.)
    message = upd.effective_message
    cmd_dct = utilities.cmd_dct_by(g3_m_str)
    text = message.text
    matched: bool = False
    # noinspection PyTypeChecker
    g3_cmd: G3Command = None
    is_command_explicit = True
    if not is_msg_w_cmd(text):
        # prefix with translates default cmd
        cmd = db.read_setting(settings.chat_setting(
            upd.effective_chat.id, ELE_TYP_cmd)).result
        if cmd:
            text = f'.{cmd} {text}'
        is_command_explicit = False
    if text.startswith('...'):
        pass
    elif text.startswith('..'):
        pass
    elif text.startswith('.'):
        if text.strip() == '.':
            latest_cmd = utilities.read_latest_cmd(upd, g3_m_dct[g3_m_str])
            text = latest_cmd.text
            is_command_explicit = False
            # pass text = utilities
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
            if len(word_li) > 1:
                ctx.args = word_li[1:]
            g3_cmd.handler(upd, ctx)
            matched = True
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
    tgdata_main.start_bot(tg_hdl.__file__, COLUMNS_TRANS, hdl_for_message=hdl_message)


def main() -> None:
    exec(open(tgdata_main.__file__).read())
    start_bot()
    print('Finished')


if __name__ == '__main__':
    main()


def test():
    print('end')


import atexit

atexit.register(test)
