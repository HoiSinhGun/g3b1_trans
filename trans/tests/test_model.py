from unittest import TestCase

from py_meta import ent_as_dict_sql
from trans.data.enums import Lc
from trans.data.model import Learned, Txtlc, TxtSeq


class TestLearned(TestCase):
    def test_build_new_txt_simple(self):
        learned = Learned(-1, Txtlc('test', Lc.VI))
        print(learned)
        print(f'learned.ent_ty is callable: {callable(learned.ent_ty)}')
        print(ent_as_dict_sql(learned))
        print(str(Lc.VI))
        txt_seq = TxtSeq(5, 'test', Lc.VI, Lc.EN)
        print(f"txt_seq hasattr id_: {hasattr(txt_seq, 'id_')}")
        print(f"txt_seq hasattr ent_ty: {hasattr(txt_seq, 'ent_ty')}")
        print(f'txt_seq.ent_ty is callable: {callable(txt_seq.ent_ty)}')


