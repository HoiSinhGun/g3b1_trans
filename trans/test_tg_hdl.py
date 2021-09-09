import logging
from unittest import TestCase

from telegram.ext import Dispatcher

import trans
from g3b1_serv import utilities
from g3b1_test import test_utils
from g3b1_test.test_utils import MsgCallback
from trans import tg_hdl
from trans.data import TST_TY_BLANKS


class Test(TestCase):

    def setUp(self) -> None:
        super().setUp()
        utilities.logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        self.dispatcher: Dispatcher = test_utils.setup(tg_hdl.__file__)

    def test_cmd_cmd_default(self):
        ts: test_utils.TestSuite = test_utils.TestSuite(
            self.dispatcher, []
        )

        tstca_hdl = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_cmd_default), {})
        callback = MsgCallback()
        ts.tc_exec(tstca_hdl, callback)

        for msg_str in callback.msg_li:
            print(msg_str)

    def test_tst_ed(self):
        ts: test_utils.TestSuite = test_utils.TestSuite(
            self.dispatcher, []
        )

        callback = MsgCallback()
        tstca_hdl_10 = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_02), {})
        ts.tc_exec(tstca_hdl_10, callback)

        tst_bkey = utilities.now_for_sql()
        tstca_hdl_20 = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_01),
                                              {'bkey': tst_bkey,
                                               'tst_type': TST_TY_BLANKS['bkey']})
        ts.tc_exec(tstca_hdl_20, callback)

        tstca_hdl_30 = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_qt),
                                              {'qt_str': 'Alle meine Entchen ... auf dem See'})
        ts.tc_exec(tstca_hdl_30, callback)

        tstca_hdl_40 = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_ans),
                                              {})
        ts.tc_exec(tstca_hdl_40, callback)

        # noinspection SpellCheckingInspection
        tstca_hdl_50 = test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_ans),
                                              {'ans_str': 'schwimmen'})
        ts.tc_exec(tstca_hdl_50, callback)

        ts.tc_exec(test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_take),
                                          {'bkey': tst_bkey}),
                   callback)

        ts.tc_exec(test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_qt),
                                          {}),
                   callback)

        # noinspection SpellCheckingInspection
        ts.tc_exec(test_utils.TestCaseHdl(utilities.g3_cmd_by_func(tg_hdl.cmd_tst_tplate_ans),
                                          {'ans_str': 'schwimmen'}),
                   callback)

        for msg_str in callback.msg_li:
            print(msg_str)
