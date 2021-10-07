# noinspection PyDefaultArgument
from typing import Union

from g3b1_cfg.tg_cfg import g3_cmd_by
from g3b1_ui.ui_mdl import IdxRngSel
from generic_hdl import send_menu_keyboard
from model import G3Command, MenuIt, Menu


# noinspection PyDefaultArgument
def txt_menu(txt: str, send_str_li: list[str] = [], sel_idx_rng: IdxRngSel = None):
    sel_idx_li: list[int] = []
    if sel_idx_rng:
        sel_idx_li = sel_idx_rng.idx_li
    msg_str = '\n'.join(send_str_li)
    if msg_str:
        msg_str += '\n\n'
    menu = Menu('trans:txt_menu', msg_str + txt.replace('|', ''))
    mi_list: list[MenuIt] = [
        txt_menu_but('rview_no'),
        txt_menu_but('tlt'),
        txt_menu_but('rview_ok'),
        MenuIt('777', '\n')
    ]
    mi_list.extend(txt_to_menu_it(txt, 'it_tgl', sel_idx_li))
    mi_list.extend([
        MenuIt('111', '\n'),
        txt_menu_but('it_ccat'),
        txt_menu_but('it_tlt'),
        txt_menu_but('it_13'),
        txt_menu_but('reset')
        # MenuIt(f'txt_menu_settings', '⚙️', None, g3_cmd_by('txt_menu_settings'), None)
    ])
    for mi in mi_list:
        mi.menu = menu
    send_menu_keyboard(menu, mi_list)


def txt_menu_but(cmd_str: str, lbl: str = '', arg_str: Union[str, int] = '') -> MenuIt:
    g3_cmd: G3Command = g3_cmd_by(f'txt_menu_{cmd_str}')
    arg_str = str(arg_str)
    if not lbl:
        lbl = g3_cmd.icon
    menu_it_id_str = cmd_str
    if arg_str:
        menu_it_id_str += ' ' + arg_str
    menu_it = MenuIt(cmd_str, lbl, None, g3_cmd, None, arg_str)
    return menu_it


# noinspection PyDefaultArgument
def txt_to_menu_it(txt: str, cmd_str: str, sel_idx_li: list[int] = []) -> list[MenuIt]:
    split: list[str] = txt.strip().split(' ')
    row_len = 0
    mi_list: list[MenuIt] = []
    seq_str = ''
    f_start = False
    f_end = False
    for idx, item in enumerate(split):
        word = item.replace('|', '')
        if f_start:
            if seq_str:
                seq_str += ' '
            seq_str += word
            if item.find('|') > -1:
                f_start = False
                f_end = True
            else:
                continue
        else:
            seq_str = word

        row_len += len(seq_str)

        if idx in sel_idx_li:
            lbl = f'✔️ {seq_str}'
        else:
            lbl = seq_str

        mi_list.append(
            txt_menu_but(cmd_str, lbl, idx)
        )
        if row_len > 13:
            row_len = 0
            mi_list.append(MenuIt('row-' + str(idx), '\n'))

        seq_str = ''

        if item.find('|') > -1:
            if f_end:
                f_end = False
            else:
                f_start = True

    return mi_list
