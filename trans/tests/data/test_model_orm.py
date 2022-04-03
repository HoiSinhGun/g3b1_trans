from unittest import TestCase

from trans.data.enums import Lc
from trans.data.model_orm import Dic
from gen import db_gen


class Test(TestCase):
    def test_txtlc(self):
        self.fail()

    def test_dic(self):
        bkey = 'test'
        dic_li = db_gen.fin_dic(bkey)
        if dic_li:
            db_gen.del_dic(dic_li[0])
        db_gen.ins_dic(Dic(bkey=bkey, lc=Lc.VI, lc2=Lc.EN))
        dic_li = db_gen.fin_dic(bkey)
        self.assertTrue(len(dic_li) == 1)
        dic = db_gen.sel_dic(dic_li[0].id)
        self.assertEqual(dic.bkey, bkey)

    def test_wrd(self):
        self.fail()

    def test_wrd_r(self):
        self.fail()

    def test_wrd_txt_seq(self):
        self.fail()
