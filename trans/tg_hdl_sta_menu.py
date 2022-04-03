from data.enums import Lc
from elements import ELE_TY_lc, ELE_TY_lc2
from g3b1_ui.model import TgUIC
from serv.services_sta_menu import TyStep, step_done
from settings import iup_setng, cu_setng


def lc(lc: Lc):
    iup_setng(cu_setng(ELE_TY_lc, lc.value))
    TgUIC.f_send = True
    step_done(step=TyStep('lc', 'lc2', 'Choose the target language'))


def lc2(lc2: Lc):
    iup_setng(cu_setng(ELE_TY_lc2, lc2.value))
    TgUIC.f_send = True

