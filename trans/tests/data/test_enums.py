import unittest

from trans.data.enums import WrdRTy


class MyTestCase(unittest.TestCase):
    def test_fin_wrd_r_ty(self):
        self.assertEqual(WrdRTy.fin('ant'), WrdRTy.ant)


if __name__ == '__main__':
    unittest.main()
