import logging

from telegram import Message

import tg_db
from data.model import TxtSeq, VocryIt, VocryMpIt, Story
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_ui.model import TgUIC
from log import cfg_logger
from serv.internal import i_vocry_mp_it_build_li
from serv.services import write_to_setng, vocry_01, utc_txt_seq, google_link
from settings import ent_by_setng
from tg_db import ins_ent_ty
from trans.data import ELE_TY_vocry_id, ENT_TY_vocry, ELE_TY_txtlc_id, ENT_TY_txtlc
from trans.data.db import sel_vocry, sel_txtlc
from trans.data.model import Vocry, Txtlc
from trans.serv.services import read_setng_lc_pair, find_or_ins_translation, all_links
from trans.serv.services_vocry_menu import vocry_tst_next
from utilities import now_for_sql

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def vocry_tst():
    vocry: Vocry = ent_by_setng(G3Ctx.cu_tup(), ELE_TY_vocry_id, sel_vocry, ENT_TY_vocry).result
    if not vocry:
        TgUIC.uic.err_setng_miss(ELE_TY_vocry_id)
        return
    if not vocry.txtlc_d():
        TgUIC.uic.error(f'No vocabulary found in {vocry.bkey}')
        return
    lc_pair = read_setng_lc_pair()
    txtlc: Txtlc = ent_by_setng(G3Ctx.cu_tup(), ELE_TY_txtlc_id, sel_txtlc, ENT_TY_txtlc).result
    if txtlc:
        txtlc_mp = find_or_ins_translation(txtlc.txt, lc_pair).result
        TgUIC.uic.send(f'{txtlc_mp.txtlc_src.txt}\n{txtlc_mp.txtlc_trg.txt}')
    txtlc_d: dict = vocry_tst_next(vocry)
    if not txtlc_d:
        TgUIC.uic.error('Vocabulary list is empty!')
        return
    # TgUIC.uic.send(google_link(txtlc_d))
    # TgUIC.uic.send(vdict_link(txtlc_d))
    txtlc_s: str = txtlc_d['txtlc'].txt
    TgUIC.uic.send(google_link(txtlc_s))
    if len(txtlc_s.split(' ')) < 3:
        TgUIC.uic.send(all_links(txtlc_d['text'].replace('\n', '')))
    bot_message: Message = TgUIC.uic.send(txtlc_s)
    if not bot_message or not isinstance(bot_message, Message):
        return
    tg_db.synchronize_from_message(bot_message, G3Ctx.g3_m_str, False)


def story_vocry(story: Story) -> Vocry:
    txt_seq = story.it_li[0].p_txt_seq
    vocry: Vocry = ent_by_setng(G3Ctx.cu_tup(), ELE_TY_vocry_id, sel_vocry, ENT_TY_vocry).result
    if not vocry:
        vocry = Vocry(G3Ctx.chat_id(), now_for_sql(), txt_seq.lc, txt_seq.lc2)
        vocry = vocry_01(vocry)
        write_to_setng(vocry)
    for story_it in story.it_li:
        logger.debug(f'Proceesing story_it {story_it.id}\n{story_it.p_txt_seq.txtlc_mp.txtlc_src.txt}')
        txt_seq = story_it.p_txt_seq
        vocry_it: VocryIt = VocryIt(vocry, txt_seq, 0)
        vocry.it_li.append(vocry_it)
        ins_ent_ty(vocry_it)
    vocry = sel_vocry(vocry.id).result
    vocry_mp_it_li: list[VocryMpIt] = vocry.build_mp_li()
    for vocry_mp_it in vocry_mp_it_li:
        ins_ent_ty(vocry_mp_it)
    write_to_setng(Txtlc())
    return vocry


def utc_vocry(text):
    txt_seq: TxtSeq = utc_txt_seq(text)
    vocry: Vocry = ent_by_setng(G3Ctx.cu_tup(), ELE_TY_vocry_id, sel_vocry, ENT_TY_vocry).result
    if not vocry:
        vocry = Vocry(G3Ctx.chat_id(), now_for_sql(), txt_seq.lc, txt_seq.lc2)
        vocry = vocry_01(vocry)
        write_to_setng(vocry)
    vocry_it: VocryIt = VocryIt(vocry, txt_seq, 0)
    vocry_it = ins_ent_ty(vocry_it).result
    vocry_mp_it_li: list[VocryMpIt] = i_vocry_mp_it_build_li(txt_seq, vocry)
    for vocry_mp_it in vocry_mp_it_li:
        ins_ent_ty(vocry_mp_it)
    return vocry, vocry_it
