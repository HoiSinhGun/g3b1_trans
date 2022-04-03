import unittest

from trans.serv.services_txt_menu import build_new_txt, build_word_d_li


class MyTestCase(unittest.TestCase):
    def test_build_new_txt_simple(self):
        new_txt = build_new_txt('bây giờ bot đã tốt hơn nhiều', 2, 3)
        self.assertEqual('bây giờ [bot đã] tốt hơn nhiều', new_txt)

        new_txt = build_new_txt('bây giờ bot đã tốt hơn nhiều', 0, 0)
        self.assertEqual('[bây] giờ bot đã tốt hơn nhiều', new_txt)

        new_txt = build_new_txt('bây giờ bot đã tốt hơn nhiều', 5, 6)
        self.assertEqual('bây giờ bot đã tốt [hơn nhiều]', new_txt)

        new_txt = build_new_txt('bây [giờ bot] đã tốt hơn nhiều', 4, 5)
        self.assertEqual('bây [giờ bot] đã tốt [hơn nhiều]', new_txt)

        new_txt = build_new_txt('bây [giờ bot] đã tốt [hơn nhiều]', 1, 2)
        self.assertEqual('bây [giờ bot đã] tốt [hơn nhiều]', new_txt)

    def test_build_new_txt(self):
        new_txt = build_new_txt('bây [giờ bot] đã tốt [hơn nhiều]', 3, 4)
        self.assertEqual('bây [giờ bot] đã [tốt hơn nhiều]', new_txt)

    def test_build_word_li(self):
        word_d, word_li = build_word_d_li('bây [giờ bot] đã tốt [hơn nhiều]')
        res_li = []
        for word in word_li:
            word = word_d.get(word, word)
            res_li.append(word)
        self.assertEqual(['bây', 'giờ bot', 'đã', 'tốt', 'hơn nhiều'], res_li)



if __name__ == '__main__':
    unittest.main()
