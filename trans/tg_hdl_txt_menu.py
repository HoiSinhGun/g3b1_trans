from random import randint

from data import ELE_TY_txtlc_id
from data.db import fi_txtlc, upd_txtlc
from data.enums import Lc, LcPair
from data.model import TxtlcMp, Txtlc
from elements import ELE_TY_lc, ELE_TY_sel_idx_rng, ELE_TY_txt
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_ui.model import TgUIC
from g3b1_ui.ui_mdl import IdxRngSel
from serv.services import xtr_seq_it_li, find_or_ins_translation, txt_13
from serv.services_txt_menu import txt_menu
from settings import read_setng, cu_setng, iup_setng
from str_utils import italic


def rnd(lc_str: str) -> str:
    if not lc_str:
        lc_str = read_setng(ELE_TY_lc).val
    txtlc_li = fi_txtlc(Lc.fin(lc_str))
    rand_idx = randint(0, len(txtlc_li) - 1)
    txtlc = txtlc_li[rand_idx]
    iup_setng(cu_setng(ELE_TY_txtlc_id, str(txtlc.id_)))
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    iup_setng(cu_setng(ELE_TY_txt, txtlc.txt))
    return txtlc.txt


def it_tgl(req__idx_str: str, cur__txt: str, cur__sel_idx_rng: IdxRngSel) -> IdxRngSel:
    idx: int = int(req__idx_str)
    cur__sel_idx_rng.toggle(idx)
    iup_setng(cu_setng(ELE_TY_sel_idx_rng, cur__sel_idx_rng.to_idx_rng_str()))
    return cur__sel_idx_rng


def reset(cur__txt: str) -> str:
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    new_txt = cur__txt.replace('|', '').strip()
    iup_setng(cu_setng(ELE_TY_txt, new_txt))
    return new_txt


def it_13(cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    seq_it_li: list[str] = xtr_seq_it_li(cur__txt, cur__sel_idx_rng)
    if len(seq_it_li) > 1:
        TgUIC.uic.error('Select exactly one entry!')
        return

    if len(seq_it_li) == 1:
        txt = seq_it_li[0]
    else:
        txt = cur__txt
    txt_13(txt)


def it_tlt(cur__txt: str, cur__sel_idx_rng: IdxRngSel, lc_pair: LcPair):
    if cur__sel_idx_rng.is_empty():
        TgUIC.uic.err_no_select()
        return
    seq_it_li: list[str] = xtr_seq_it_li(cur__txt, cur__sel_idx_rng)
    send_str = ''
    for word in seq_it_li:
        txtlc_mp: TxtlcMp = find_or_ins_translation(word.strip(), lc_pair).result
        if len(seq_it_li) == 1:
            send_str = txtlc_mp.txtlc_trg.txt
        else:
            send_str += f'{txtlc_mp.txtlc_src.txt}\n{italic(txtlc_mp.txtlc_trg.txt)}\n\n'
    if send_str:
        TgUIC.uic.send(send_str)


def it_ccat(cur__txt: str, cur__sel_idx_rng: IdxRngSel) -> str:
    if cur__sel_idx_rng.is_empty():
        return ''
    sel_idx_li = cur__sel_idx_rng.idx_li
    idx_start = sel_idx_li[0]
    idx_end = sel_idx_li[len(sel_idx_li) - 1]
    check = len(sel_idx_li) - (idx_end - idx_start)
    if check != 1:
        TgUIC.uic.error('To merge select adjacent words!')
        return ''
    word_li = cur__txt.split(' ')
    new_txt = ''
    for idx, word in enumerate(word_li):
        if idx == idx_start:
            new_txt += '|'
        if new_txt:
            new_txt += ' '
        new_txt += word
        if idx == idx_end:
            new_txt += '|'
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    iup_setng(cu_setng(ELE_TY_txt, new_txt))
    return new_txt


def rview(req__s_review: str, cur__txtlc: Txtlc, lc2: Lc):
    if req__s_review == 0:
        TgUIC.uic.err_cmd_fail()
        return
    upd_txtlc(cur__txtlc.id_, req__s_review)
    G3Ctx.ctx.args = [cur__txtlc.lc.value]


def tlt(cur__txtlc: Txtlc, lc2: Lc):
    txtlc_mp: TxtlcMp = find_or_ins_translation(cur__txtlc.txt, (cur__txtlc.lc, lc2)).result
    TgUIC.uic.send(txtlc_mp.txtlc_trg.txt)
    # lc = cur__txtlc.lc
    # word = cur__txtlc.txt.split(' ')[int(req__idx_str)]
    # txtlc_mp: TxtlcMp = find_or_ins_translation(word, (lc, lc2)).result
    # TgUIC.uic.send(txtlc_mp.txtlc_trg.txt)
