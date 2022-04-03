from unittest import TestCase

from g3b1_cfg.tg_cfg import G3Ctx
from trans.serv.internal import i_vocry_mp_it_build_li
from test_utils import MockChat, MockUpdate, MockUser
from trans.data import ENT_TY_txt_seq, md_TRANS, eng_TRANS, BOT_BKEY_TRANS
from tg_db import sel_ent_ty_li, ins_ent_ty
from trans.data.db import ins_vocry, sel_vocry, fin_vocry, del_vocry, sel_txt_seq
from trans.data.enums import Lc
from trans.data.model import Vocry, VocryIt, TxtSeq


class TestVocry(TestCase):
    def test_ins(self):
        G3Ctx.md = md_TRANS
        G3Ctx.eng = eng_TRANS
        G3Ctx.g3_m_str = BOT_BKEY_TRANS
        chat_id = 1749165037
        mock_chat = MockChat(chat_id)
        G3Ctx.upd = MockUpdate(mock_chat, MockUser(1))

        if vocry_found := fin_vocry(chat_id, 'test'):
            vocry_sel: Vocry = sel_vocry(vocry_found.id).result
            del_vocry(vocry_sel.id)
            print(f'Removed vocry with id: {id}', vocry_sel.id)

        vocry = Vocry(chat_id, 'test', Lc.VI, Lc.EN)
        txt_seq_row_li = sel_ent_ty_li(ENT_TY_txt_seq)
        txt_seq_id: int = txt_seq_row_li[0]['id']
        txt_seq: TxtSeq = sel_txt_seq(txt_seq_id).result
        vocry_id = VocryIt(vocry, txt_seq, 0)
        i_vocry_mp_it_build_li(txt_seq, vocry)
        vocry.it_li.append(vocry_id)
        g_result = ins_vocry(vocry)
        vocry = g_result.result
        print(vocry)
        print(vocry.it_li[0])
        print(vocry.mp_it_li[0])

        txt_seq_id: int = txt_seq_row_li[1]['id']
        txt_seq: TxtSeq = sel_txt_seq(txt_seq_id).result
        vocry_it = VocryIt(vocry, txt_seq, 0)
        vocry_it_ins = ins_ent_ty(vocry_it).result
        print(vocry_it_ins)
        vocry_mp_it_li = i_vocry_mp_it_build_li(txt_seq, vocry)
        for vocry_mp_it in vocry_mp_it_li:
            ins_ent_ty(vocry_mp_it)
            print(vocry_mp_it)
