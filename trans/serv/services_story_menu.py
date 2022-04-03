import codecs
from typing import Optional

from trans.data.enums import Lc
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_ui.model import TgUIC
from model import Menu, MenuIt
from g3b1_data.settings import ent_by_setng, read_setng
from str_utils import bold
from tg_db import sel_ent_ty
from trans.data import ELE_TY_story_id, ENT_TY_story, ELE_TY_story_it_id, ENT_TY_story_it, ELE_TY_story_show_text
from trans.data import db
from trans.data.db import sel_story
from trans.data.model import StoryIt, Story
from trans.serv.services import utc_txt_str
from trans.serv.services_menu import menu_but


def story_by_setng() -> Story:
    return ent_by_setng(G3Ctx.cu_tup(), ELE_TY_story_id, sel_story, ENT_TY_story, is_chat_setng=True).result


def story_it_by_setng() -> StoryIt:
    return ent_by_setng(G3Ctx.cu_tup(), ELE_TY_story_it_id, sel_ent_ty, ENT_TY_story_it, is_chat_setng=True).result


def it_paging_val() -> Optional[StoryIt]:
    story: Story
    if not (story := story_by_setng()):
        TgUIC.uic.err_setng_miss(ELE_TY_story_id)
        return
    if not story.it_li:
        TgUIC.uic.error(f'Story id: {story.id} has no items.')
        return
    if not (story_it := story_it_by_setng()):
        story_it = story.it_li[0]
    story_it = story.it_by_rowno(story_it.rowno)
    return story_it


def story_menu_but(g3_cmd_s: str) -> MenuIt:
    return menu_but('story', g3_cmd_s)


def build_menu(story_it: StoryIt) -> (Menu, list[MenuIt]):
    mi_list_base: list[MenuIt] = [
        story_menu_but('it_prv'),
        story_menu_but('it_nxt'),
        story_menu_but('it_aud'),
        story_menu_but('it_voc')
    ]
    mi_list = []
    for idx, mi in enumerate(mi_list_base):
        if (idx + 1) % 3 == 0:
            mi_list.append(MenuIt('row-' + str(idx), '\n'))
        mi_list.append(mi)
    head_s = ''
    if story_it.txtlc_mp:
        head_s = story_it.txtlc_mp.txtlc_src.txt + '\n'
    f_show_story_text = read_setng(ELE_TY_story_show_text, True).val_mp
    text = f'{story_it.story}\n' \
           f'{story_it.rowno} (story_it_id:{story_it.id}):{bold(head_s)}\n'
    if f_show_story_text:
        text = text + f'txtlc_id={story_it.p_txt_seq.txtlc_mp.txtlc_src.id_}\n' \
                      f'{bold(story_it.role)}:::{bold(story_it.p_txt_seq.txtlc_mp.txtlc_src.txt)}'
    menu = Menu('trans:story', text)

    for mi in mi_list:
        mi.menu = menu

    return menu, mi_list


def story_of(user_id: int, bkey: str) -> Story:
    story: Story = db.fin_story_of(user_id, bkey)
    return story


def read_txt_story(fl_s: str, lc: Lc) -> list[str]:
    fl_setng_d: dict[str, str] = {}
    with codecs.open(fl_s, encoding='utf-8') as f:
        line = f.readline()
        if line.startswith(':::'):
            line_split = line.split(':::')
            for k_v in line_split:
                if k_v.find(':') == -1:
                    continue
                fl_setng_d[k_v.split(':')[0]] = k_v.split(':')[1].strip()
    txt_seq_marker = fl_setng_d.get('txt_seq_marker', '\n')

    if txt_seq_marker == '\n':
        with codecs.open(fl_s, encoding='utf-8') as f:
            line_li: list[str] = f.readlines()
    else:
        with codecs.open(fl_s, encoding='utf-8') as f:
            fl_content = f.read()
            # remove first line
            fl_content = fl_content.replace(line, '', 1)
        line_li: list[str] = fl_content.split(txt_seq_marker)
    res_li: list[str] = []
    for line_it in [it.strip() for it in line_li]:
        line_s = line_it.replace('\r\n', '\n')
        pfx_s = ''
        if line_it.startswith('h:'):
            line_s = line_it[2:]
            pfx_s = 'h:'
        res_s = utc_txt_str(line_s, lc.value == Lc.VI.value)
        res_li.append(f'{pfx_s}{res_s}\n')

    return res_li
