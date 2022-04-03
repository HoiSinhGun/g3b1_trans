import unittest

from trans.data.enums import Lc
from trans.data.model_orm import Dic
from gen.db_gen import ins_dic


class MyTestCase(unittest.TestCase):
    def test_something(self):
        dic = Dic(bkey='test_dic_3', lc=Lc.VI, lc2=Lc.EN)
        ins_dic(dic)
        self.assertIsNotNone(dic.id)  # add assertion here


if __name__ == '__main__':
    unittest.main()
