from functools import cache
from random import shuffle

from sqlalchemy.engine import Row

from trans.data.db import sel_txtlc
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_ui.model import TgUIC
from settings import iup_setng, cu_setng, ent_by_setng
from tg_db import sel_ent_ty_li
from trans.data import ENT_TY_learned, ELE_TY_txtlc_id, ENT_TY_txtlc
from trans.data.model import Vocry, Txtlc, TxtSeq


# def build_menu(*, txtl_mp:TxtlcMp) -> (Menu, list[MenuIt]):
#     mi_list_base: list[MenuIt] = [sta_menu_but(step.next, f'{lc.flag()} {lc.value}', lc.value) for lc in Lc]
#     mi_list = []
#     for idx, mi in enumerate(mi_list_base):
#         if (idx + 1) % 3 == 0:
#             mi_list.append(MenuIt('row-' + str(idx), '\n'))
#         mi_list.append(mi)
#     menu = Menu('trans:sta_menu', step.l_step_descr)
#
#     for mi in mi_list:
#         mi.menu = menu
#
#     return menu, mi_list
#
#
def txtlc_li_for_d(txt_d: dict[int, dict]) -> list[dict]:
    learned_row_li: list[Row] = sel_ent_ty_li(ENT_TY_learned)
    txtlc_id_li = [row['txtlc_id'] for row in learned_row_li if row['txtlc_id']]
    txtlc_d_li: list[dict] = [v for k, v in txt_d.items() if
                              k not in txtlc_id_li and v['txtlc'].txt.find(
                                  '\n') == -1 and v['txtlc'].txt.strip() not in TxtSeq.sc_li()]
    # TgUIC.uic.send(f'{len(txtlc_d_li)}/{len(txt_d)}')
    shuffle(txtlc_d_li)
    return txtlc_d_li


@cache
def txtlc_li_for(vocry: Vocry) -> list[dict]:
    txt_d: dict[int, dict] = vocry.txtlc_d()
    return txtlc_li_for_d(txt_d)


def vocry_tst_next(vocry: Vocry) -> dict:
    txtlc_li = txtlc_li_for(vocry)
    if not txtlc_li:
        return {}

    txtlc: Txtlc = ent_by_setng(G3Ctx.cu_tup(), ELE_TY_txtlc_id, sel_txtlc, ENT_TY_txtlc).result
    idx = 0
    if txtlc:
        for count, txtlc_d in enumerate(txtlc_li):
            if txtlc_d['txtlc'].id_ == txtlc.id_:
                idx = count

    idx = idx + 1
    if idx == len(txtlc_li):
        idx = 0
    txtlc = txtlc_li[idx]['txtlc']
    iup_setng(cu_setng(ELE_TY_txtlc_id, str(txtlc.id_)))
    return txtlc_li[idx]
