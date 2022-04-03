import os.path
from collections import Callable
from typing import Optional

from trans.data import ELE_TY_story_show_text
from entities import EntId
from g3b1_ui.model import TgUIC
from g3b1_data.settings import read_setng
from subscribe.data.model import ENT_TY_g3_file
from tg_db import sel_ent_ty
from trans.data.db import fin_txtlc_file_of
from trans.data.enums import Lc
from trans.data.model import StoryIt
from subscribe.data.model import G3File
from trans.data.model import Txtlc, TxtlcFile
from trans.serv.services import read_setng_lc_pair


def send(send_str, translate_txt: Callable, reply_markup=None):
    lc_pair = read_setng_lc_pair()
    if translate_txt and lc_pair.lc != Lc.EN:
        send_str = translate_txt(send_str, 'EN', lc_pair.lc.value)
    TgUIC.uic.send(send_str, reply_markup)


def send_txtlc_audio(txtlc: Txtlc, caption: str) -> Optional[G3File]:
    txtlc_file_li: list[TxtlcFile] = fin_txtlc_file_of(txtlc).result
    if not txtlc_file_li:
        return
    txtlc_file: TxtlcFile = txtlc_file_li[0]
    # noinspection PyTypeChecker
    g3_file: G3File = sel_ent_ty(EntId(ENT_TY_g3_file, txtlc_file.file)).result
    TgUIC.uic.send_audio(g3_file.get_path(), caption)
    return g3_file


def send_lesson_audio(story_it: StoryIt, incl_proj=False):
    f_show_story_text = read_setng(ELE_TY_story_show_text, True).val_mp
    caption_s = ''
    if f_show_story_text:
        caption_s = story_it.p_txt_seq.txtlc_mp.txtlc_src.txt
    if base_aud_seg_fl := story_it.base_seg_fl():
        TgUIC.uic.send_audio(base_aud_seg_fl, caption_s, os.path.split(base_aud_seg_fl)[1])
    if incl_proj:
        fl_li = story_it.vers_seg_fl_li()
        for fl_s in fl_li:
            title_s = fl_s.replace(story_it.story.base_dir(), '....').replace('proj', '').replace('seg_subst', '')
            TgUIC.uic.send_audio(fl_s, caption_s, title_s)
