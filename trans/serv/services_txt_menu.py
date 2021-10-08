# noinspection PyDefaultArgument
import re
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
    menu = Menu('trans:txt_menu', msg_str + txt.replace('[', '').replace(']', ''))
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


def build_new_txt(txt: str, idx_start: int, idx_end: int) -> str:
    ccat_str_dct, word_li = build_word_li(txt)
    new_txt = ''
    for idx, word in enumerate(word_li):
        if new_txt:
            new_txt += ' '
        if idx == idx_start:
            new_txt += '['
        new_txt += word
        if idx == idx_end:
            new_txt += ']'
    for k, v in ccat_str_dct.items():
        if new_txt.startswith(k) or new_txt.endswith(k):
            # This check first to avoid index error with the next check (find_k)
            new_txt = new_txt.replace(k, f'[{v}]')
            continue
        find_k = new_txt.find(k)
        if new_txt[find_k - 1] == '[' or new_txt[find_k + len(k)] == ']':
            new_txt = new_txt.replace(k, v)
            continue
        new_txt = new_txt.replace(k, f'[{v}]')
    return new_txt


def build_word_li(txt: str) -> (dict[str, str], list[str]):
    # noinspection RegExpRedundantEscape
    p = re.compile('\[(.*?)\]')
    ccat_str_li: list[str] = p.findall(txt)
    ccat_str_dct: dict[str, str] = {}
    for idx, ccat_str in enumerate(ccat_str_li):
        ccat_str_dct[f'%{idx}%'] = ccat_str
    for k, v in ccat_str_dct.items():
        txt = txt.replace(f'[{v}]', k)
    word_li = txt.split(' ')
    return ccat_str_dct, word_li


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


def txt_to_menu_it(txt: str, cmd_str: str, sel_idx_li: list[int]) -> list[MenuIt]:
    ccat_str_dct, word_li = build_word_li(txt)
    row_len = 0
    mi_list: list[MenuIt] = []
    for idx, word in enumerate(word_li):
        word = ccat_str_dct.get(word, word)

        row_len += len(word)

        if idx in sel_idx_li:
            lbl = f'✔️ {word}'
        else:
            lbl = word

        mi_list.append(
            txt_menu_but(cmd_str, lbl, idx)
        )
        if row_len > 13:
            row_len = 0
            mi_list.append(MenuIt('row-' + str(idx), '\n'))

    return mi_list


def xtr_seq_it_li(txt: str, cur__sel_idx_rng: IdxRngSel) -> list[str]:
    if cur__sel_idx_rng.is_empty():
        return []
    ccat_str_dct, word_li = build_word_li(txt)
    res_word_li: list[str] = []
    for idx in cur__sel_idx_rng.idx_li:
        word = word_li[idx]
        word = ccat_str_dct.get(word, word)
        res_word_li.append(word)
    return res_word_li
