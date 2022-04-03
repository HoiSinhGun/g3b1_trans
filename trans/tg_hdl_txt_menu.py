from random import randint

from underthesea import word_tokenize

from data import ELE_TY_txtlc_id, ELE_TY_txt_seq_it_num, ELE_TY_txt_seq_id, ELE_TY_txt_menu
from data.db import fi_txtlc, upd_txtlc
from data.enums import Lc, LcPair
from data.model import TxtlcMp, Txtlc, TxtSeq
from elements import ELE_TY_lc, ELE_TY_sel_idx_rng, ELE_TY_txt
from g3b1_cfg.tg_cfg import G3Ctx, g3_cmd_by
from g3b1_ui.model import TgUIC
from g3b1_ui.ui_mdl import IdxRngSel
from serv.internal import i_len_vn
from serv.services import find_or_ins_translation, txt_13, find_or_ins_txtlc
from serv.services_txt_menu import build_new_txt, xtr_seq_it_li, tokenize_txtlc, single_selected_word
from settings import read_setng, cu_setng, iup_setng
from str_utils import italic, code


def call(arg_li: list[str] = []) -> str:
    call_cmd_str = read_setng(ELE_TY_txt_menu).val
    g3_ctx_dct = G3Ctx.as_dict()
    G3Ctx.ctx.args = arg_li
    g3_cmd_by(call_cmd_str).handler(G3Ctx.upd, G3Ctx.ctx)
    G3Ctx.from_dict(g3_ctx_dct)


def fwd_prv(txt_seq: TxtSeq, cur_num: int, step: int) -> str:
    it_num = int(cur_num)
    it_idx_next = txt_seq.it_li.index(txt_seq.it(it_num)) + step
    if step > 0 and it_idx_next == len(txt_seq.it_li):
        it_idx_next = 0
    elif step < 0 and it_idx_next < 0:
        it_idx_next = len(txt_seq.it_li) - 1
    next_it = txt_seq.it_li[it_idx_next]
    next_txt = next_it.txtlc_mp.txtlc_src.txt
    if not next_txt or next_txt.strip() in TxtSeq.sc_li():
        return fwd_prv(txt_seq, next_it.rowno, step)
    iup_setng(cu_setng(ELE_TY_txt_seq_it_num, str(next_it.rowno)))
    # f_continue = 1
    call(['1'])
    return read_setng(ELE_TY_txt).val


def seq(cont_str: str, txt_seq: TxtSeq, txt_seq_it_num: str) -> str:
    if cont_str == '1' and txt_seq_it_num:
        txt_seq_it = txt_seq.it(int(txt_seq_it_num))
    else:
        txt_seq_it = txt_seq.it_li[0]
        iup_setng(cu_setng(ELE_TY_txt_seq_it_num, str(txt_seq_it.rowno)))
    text = tokenize_txtlc(txt_seq_it.txtlc_mp.txtlc_src)
    iup_setng(cu_setng(ELE_TY_txt_menu, 'txt_menu_seq'))
    iup_setng(cu_setng(ELE_TY_txtlc_id, str(txt_seq_it.txtlc_mp.txtlc_src.id_)))
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    iup_setng(cu_setng(ELE_TY_txt, text))

    return text


def default(text: str, txt_menu='txt_menu') -> str:
    lc: Lc = Lc.fin(read_setng(ELE_TY_lc).val)
    txtlc: Txtlc = find_or_ins_txtlc(text, lc)
    text = tokenize_txtlc(txtlc)
    iup_setng(cu_setng(ELE_TY_txt_menu, txt_menu))
    iup_setng(cu_setng(ELE_TY_txtlc_id, str(txtlc.id_)))
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    iup_setng(cu_setng(ELE_TY_txt, text))
    return text


def rnd(lc_str: str) -> str:
    if not lc_str:
        lc_str = read_setng(ELE_TY_lc).val
    txtlc_li = fi_txtlc(Lc.fin(lc_str))
    rand_idx = randint(0, len(txtlc_li) - 1)
    txtlc = txtlc_li[rand_idx]
    new_txt = tokenize_txtlc(txtlc)

    iup_setng(cu_setng(ELE_TY_txt_menu, 'txt_menu_rnd'))
    iup_setng(cu_setng(ELE_TY_txtlc_id, str(txtlc.id_)))
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    iup_setng(cu_setng(ELE_TY_txt, new_txt))
    return new_txt


def it_tgl(req__idx_str: str, cur__sel_idx_rng: IdxRngSel) -> IdxRngSel:
    idx: int = int(req__idx_str)
    cur__sel_idx_rng.toggle(idx)
    iup_setng(cu_setng(ELE_TY_sel_idx_rng, cur__sel_idx_rng.to_idx_rng_str()))
    return cur__sel_idx_rng


def reset(cur__txt: str) -> str:
    iup_setng(cu_setng(ELE_TY_sel_idx_rng))
    new_txt = cur__txt.replace('[', '').replace(']', '')
    iup_setng(cu_setng(ELE_TY_txt, new_txt))
    return new_txt


def it_13(cur__txt: str, cur__sel_idx_rng: IdxRngSel):
    txt = single_selected_word(cur__txt, cur__sel_idx_rng)
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


def it_ccat(cur__txt: str, cur__sel_idx_rng: IdxRngSel) -> (str, IdxRngSel):
    if cur__sel_idx_rng.is_empty():
        return cur__txt, cur__sel_idx_rng
    sel_idx_li = cur__sel_idx_rng.idx_li
    idx_start = sel_idx_li[0]
    idx_end = sel_idx_li[len(sel_idx_li) - 1]
    check = len(sel_idx_li) - (idx_end - idx_start)
    if check != 1:
        TgUIC.uic.error('To merge select adjacent words!')
        return cur__txt, cur__sel_idx_rng
    new_txt = build_new_txt(cur__txt, idx_start, idx_end)
    new_sel_idx_rng = IdxRngSel(str(idx_start))
    iup_setng(cu_setng(ELE_TY_sel_idx_rng, new_sel_idx_rng.to_idx_rng_str()))
    iup_setng(cu_setng(ELE_TY_txt, new_txt))
    return new_txt, new_sel_idx_rng


def rview(req__s_review: str, cur__txtlc: Txtlc, lc2: Lc):
    if req__s_review == 0:
        TgUIC.uic.err_cmd_fail()
        return
    upd_txtlc(cur__txtlc.id_, req__s_review)
    G3Ctx.ctx.args = [cur__txtlc.lc.value]


def tlt(cur__txtlc: Txtlc, lc2: Lc):
    txt_li = [cur__txtlc.txt]
    if cur__txtlc.txt.find('\n') > 0:
        txt_li = cur__txtlc.txt.split('\n')
    for txt in txt_li:
        txtlc_mp: TxtlcMp = find_or_ins_translation(txt, (cur__txtlc.lc, lc2)).result
        # len_diff = len(txt) - i_len_vn(txt)
        send_s = f'{txt.ljust(20)} - {txtlc_mp.txtlc_trg.txt}'
        TgUIC.uic.send(code(send_s))
    # lc = cur__txtlc.lc
    # word = cur__txtlc.txt.split(' ')[int(req__idx_str)]
    # txtlc_mp: TxtlcMp = find_or_ins_translation(word, (lc, lc2)).result
    # TgUIC.uic.send(txtlc_mp.txtlc_trg.txt)
