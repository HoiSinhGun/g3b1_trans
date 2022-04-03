from typing import Union

from g3b1_cfg.tg_cfg import g3_cmd_by
from model import G3Command, MenuIt


def menu_but(menu_key: str, cmd_str: str, lbl: str = '', arg_str: Union[str, int] = '') -> MenuIt:
    """label with leading emoji code for icon buttons """
    g3_cmd: G3Command = g3_cmd_by(f'{menu_key}_{cmd_str}')
    arg_str = str(arg_str)
    if not lbl:
        lbl = g3_cmd.icon
    menu_it_id_str = cmd_str
    if arg_str:
        menu_it_id_str += ' ' + arg_str
    menu_it = MenuIt(cmd_str, lbl, None, g3_cmd, None, arg_str)
    return menu_it
