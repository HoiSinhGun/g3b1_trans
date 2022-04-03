from unittest import TestCase

from g3b1_cfg.tg_cfg import G3Ctx
from test_utils import MockChat, MockUpdate, MockUser
from trans.data import md_TRANS, eng_TRANS, BOT_BKEY_TRANS
from trans.data.db import fin_txtlc_file
from trans.data.enums import Lc
from trans.data.model import TxtlcFile


class TestStory(TestCase):
    def test_fin(self):
        G3Ctx.md = md_TRANS
        G3Ctx.eng = eng_TRANS
        G3Ctx.g3_m_str = BOT_BKEY_TRANS
        chat_id = 1749165037
        mock_chat = MockChat(chat_id)
        user_id = 1749165037
        G3Ctx.upd = MockUpdate(mock_chat, MockUser(user_id))

    txtlc_file_li: list[TxtlcFile] = fin_txtlc_file(Lc.VI).result
    for txtlc_file in txtlc_file_li:
        print(txtlc_file.txtlc.txt)

