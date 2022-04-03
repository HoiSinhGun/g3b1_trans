import logging
from datetime import datetime

from telegram.ext import Dispatcher

from g3b1_serv import utilities
from g3b1_test import test_utils
from trans import trans__tg_hdl


def main():
    utilities.logger.setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    dispatcher: Dispatcher = test_utils.setup(trans__tg_hdl.__file__)

    ts: test_utils.TestSuite = test_utils.TestSuite(
        dispatcher, []
    )

    ts.tc_li.extend(
        [
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                tg_hdl.cmd_subscribe),
                {}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                tg_hdl.cmd_t),
                {'reply_to_msg': test_utils.MyMessage(-1, datetime.now(),
                                                      chat=test_utils.chat_default(),
                                                      from_user=test_utils.user_default(),
                                                      text='Hallo Welt!'),
                 'trg_text': 'Hello World!'}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                tg_hdl.cmd_lc_view),
                {}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                trans__tg_hdl.cmd_lc),
                {'lc': 'AT'}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                trans__tg_hdl.cmd_t),
                {'reply_to_msg': test_utils.MyMessage(-1, datetime.now(),
                                                      chat=test_utils.chat_default(),
                                                      from_user=test_utils.user_default(),
                                                      text='Hallo Welt!')
                 }
            )
        ]
    )
    for tc in ts.tc_li[:2]:
        ts.tc_exec(tc)


if __name__ == '__main__':
    main()
