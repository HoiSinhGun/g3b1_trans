import functools
import inspect
from collections import namedtuple
from typing import Union

import generic_hdl
from g3b1_cfg.tg_cfg import g3_cmd_by
from g3b1_data.elements import ELE_TY_lc
from g3b1_data.model import G3Command, MenuIt, Menu
from g3b1_data.settings import read_setng, cu_setng
from trans.data.enums import TyLcPair, Lc
from trans.data.model import TxtlcMp
from trans.serv.services import find_or_ins_translation

TyStep = namedtuple('TyStep', ['done', 'next', 'l_step_descr'])


def localize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        full_spec = inspect.getfullargspec(func)
        for param in full_spec.kwonlyargs:
            if full_spec.annotations[param] == TyStep:
                lc_s = read_setng(ELE_TY_lc).val
                lc_pair = TyLcPair(Lc.EN, Lc.fin(lc_s))
                if lc_s and lc_s != Lc.EN.value:
                    ty_step: TyStep = kwargs[param]
                    txtlc_mp: TxtlcMp = find_or_ins_translation(ty_step.l_step_descr, lc_pair).result
                    kwargs[param] = TyStep(ty_step.done, ty_step.next, txtlc_mp.txtlc_trg.txt)

        return func(*args, **kwargs)

    return wrapper


def step_done(*, step: TyStep):
    menu, mi_list = build_menu(step=step)
    generic_hdl.send_menu_keyboard(menu, mi_list)


@localize
def build_menu(*, step: TyStep) -> (Menu, list[MenuIt]):
    mi_list_base: list[MenuIt] = [sta_menu_but(step.next, f'{lc.flag()} {lc.value}', lc.value) for lc in Lc]
    mi_list = []
    for idx, mi in enumerate(mi_list_base):
        if (idx + 1) % 3 == 0:
            mi_list.append(MenuIt('row-' + str(idx), '\n'))
        mi_list.append(mi)
    menu = Menu('trans:sta_menu', step.l_step_descr)

    for mi in mi_list:
        mi.menu = menu

    return menu, mi_list


def sta_menu_but(cmd_str: str, lbl: str = '', arg_str: Union[str, int] = '') -> MenuIt:
    """label with leading emoji code for icon buttons """
    g3_cmd: G3Command = g3_cmd_by(f'sta_menu_{cmd_str}')
    arg_str = str(arg_str)
    if not lbl:
        lbl = g3_cmd.icon
    menu_it_id_str = cmd_str
    if arg_str:
        menu_it_id_str += ' ' + arg_str
    menu_it = MenuIt(cmd_str, lbl, None, g3_cmd, None, arg_str)
    return menu_it
