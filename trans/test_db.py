import unittest
from _ast import FunctionDef

from sqlalchemy import ForeignKey, Column, Integer
from telegram.ext import Dispatcher

import generic_hdl
import integrity
import test_utils
import tg_hdl
import utilities
from entities import ENT_TY_li, G3_M_TRANS
from model import G3Command, g3_m_dct
from trans.data.db import *

is_print = True


# noinspection PyDecorator
@staticmethod
def do_print(*args):
    if is_print:
        print(args)


unittest.TestCase.print = do_print


class TstTplateRefs(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        utilities.logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        self.dispatcher: Dispatcher = test_utils.setup(tg_hdl.__file__)

    def test_tst_tplate_refs(self):
        tst_tplate = sel_tst_tplate(49).result
        tplate_ref_li = tst_tplate_refs(tst_tplate)
        self.assertGreater(len(tplate_ref_li), 1)
        for tplate_ref in tplate_ref_li:
            # noinspection PyUnresolvedReferences
            self.print(tplate_ref.items())

    def test_ref_tbl(self):
        tbl_fk_li_dct: dict[Table, list[ForeignKey]] = {}
        for tbl in [MetaData_TRANS.tables[i.tbl_name] for i in ENT_TY_li if i.g3_m_str == G3_M_TRANS]:
            tbl_fk_li_dct[tbl] = list[ForeignKey]()
        for ent_ty in [i for i in ENT_TY_li if i.g3_m_str == G3_M_TRANS]:
            # noinspection PyUnresolvedReferences
            self.print(ent_ty.id_)
            for k, v in ent_ty.ref_tbl_dct(MetaData_TRANS).items():
                if k in tbl_fk_li_dct.keys():
                    for col_id in v:
                        column = Column(name='id', type_=Integer)
                        column.table = MetaData_TRANS.tables[ent_ty.tbl_name]
                        tbl_fk_li_dct[k].append(ForeignKey(column))
                # noinspection PyUnresolvedReferences
                self.print(f'{k.name.ljust(25)} = {", ".join(v)}')
            # noinspection PyUnresolvedReferences
            self.print('\n')
        for tbl in tbl_fk_li_dct.keys():
            for col_id, col in tbl.columns.items():
                fk: ForeignKey
                for fk in [i for i in col.foreign_keys if i.column.table in tbl_fk_li_dct.keys()]:
                    found = False
                    for fk_check in tbl_fk_li_dct[tbl]:
                        if fk.column.table == fk_check.column.table:
                            found = True
                    self.assertTrue(found, msg=str(f'{fk} not found in reverse engineered FK list of table {tbl.name}'))

    def test_txtlc_refs(self):
        txtlc = fiby_txt_lc(Txtlc.from_id(4641)).result
        ref_li = integrity.ref(txtlc)
        # noinspection PyUnresolvedReferences
        self.print('\n'.join([tbl.name for tbl in ref_li]))

    # noinspection PyMethodMayBeStatic
    def test_tplate_it_refs(self):
        tst_tplate = sel_tst_tplate_by_item_id(209).result
        ref_li = integrity.ref_cascade(tst_tplate)
        print('\n'.join([tbl.name for tbl in ref_li]))

    def test_(self):
        ts: test_utils.TestSuite = test_utils.TestSuite(
            self.dispatcher, []
        )
        func_def: FunctionDef = utilities.read_function(generic_hdl.__file__,
                                                        generic_hdl.cmd_ent_ty_33_li.__name__)

        g3_cmd: G3Command = G3Command(g3_m_dct['trans'], generic_hdl.cmd_ent_ty_33_li,
                                      func_def.args.args)

        tstca_hdl = test_utils.TestCaseHdl(g3_cmd, {'ent_ty': ENT_TY_tst_tplate})
        callback = test_utils.MsgCallback()
        ts.tc_exec(tstca_hdl, callback)
        for i in callback.msg_li:
            print(i)
            print(len(i))
        pass


class Txt13(unittest.TestCase):

    def test_txtlc_txt_cp(self):
        txtlc_li = txtlc_txt_cp('gặp', Lc.VI)
        for i in txtlc_li:
            # noinspection PyUnresolvedReferences
            self.print(i)
        self.assertGreater(len(txtlc_li), 1)


if __name__ == '__main__':
    unittest.main()
