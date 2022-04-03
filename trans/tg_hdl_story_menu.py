import codecs
import logging
import os
from typing import Optional

from telegram import Message

import tg_db
from constants import env_g3b1_dir
from data.enums import LcPair, Lc
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_ui.model import TgUIC
from generic_hdl import send_menu_keyboard
from log import cfg_logger
from serv.services_story_menu import it_paging_val, story_of, build_menu, story_it_by_setng
from serv.services_vocry_menu import txtlc_li_for_d
from settings import read_setng
from str_utils import bold
from tg_db import ins_ent_ty, upd_ent_ty
from trans.data import ELE_TY_story_it_id
from trans.data.db import ins_story, sel_story, sel_txt_seq
from trans.data.model import Story, TxtSeq, StoryIt, TxtlcMp, Vocry, VocryIt, VocryMpIt
from trans.serv.services import write_to_setng, find_or_ins_translation, utc_txt_seq, read_setng_lc_pair, \
    write_to_c_setng, all_links, babla_link
from ui.msg import send_txtlc_audio, send_lesson_audio
from utilities import now_for_sql

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def story_01(bkey: str, txt_seq: TxtSeq) -> Story:
    story: Story = Story(G3Ctx.chat_id(), G3Ctx.for_user_id(), bkey, txt_seq.lc)
    story_it = StoryIt(story, None, txt_seq)
    story.it_li.append(story_it)
    story_id = ins_story(story).result.id
    story = sel_story(story_id).result
    write_to_c_setng(story)
    # noinspection PyTypeChecker
    # write_to_setng(StoryIt(None, None, None, None))
    write_to_c_setng(story.it_li[0])
    return story


def story_02(story_id: int) -> Story:
    story: Story = sel_story(story_id).result
    if story:
        write_to_c_setng(story)
        if story.it_li:
            write_to_c_setng(story.it_li[0])
        else:
            # noinspection PyTypeChecker
            write_to_c_setng(StoryIt(None, None, None, None))
    else:
        TgUIC.uic.error(f'story id: {story_id} not found')
    return story


def story_03(story: Story, f_all_it: bool = False):
    send_s: str = str(story)
    if not story.it_li:
        TgUIC.uic.send(send_s)
        return
    if f_all_it:
        send_s = f'{send_s}\n' + '\n'.join([it.str_compact(33) for it in story.it_li])
        TgUIC.uic.send(send_s)
        return
    story_it = story.it_li[0]
    if len(story) > 1:
        if story_it := story_it_by_setng():
            story_it = story.it_by_id(story_it.id)
        else:
            story_it = story.it_li[0]
            write_to_setng(story_it)
    send_s = f'{send_s}\n{bold("Item")}: {story_it.rowno} (id: {story_it.id})'
    TgUIC.uic.send(send_s)
    if story_it.txtlc_mp:
        TgUIC.uic.send(bold(story_it.txtlc_mp.txtlc_src.txt))
        # send_s = f'{send_s}\n\n{bold(story_it.txtlc_mp.txtlc_src.txt)}'
    if story_it:
        bot_message: Message = TgUIC.uic.send(story_it.p_txt_seq.txtlc_mp.txtlc_src.txt)
        if not bot_message or not isinstance(bot_message, Message):
            return
        tg_db.synchronize_from_message(bot_message, G3Ctx.g3_m_str, False, sub_module='story', menu_id='trans:story')


def story_it_01(story: Story, txt_seq: TxtSeq) -> StoryIt:
    story_it = StoryIt(story, None, txt_seq)
    story_it: StoryIt = ins_ent_ty(story_it).result
    write_to_c_setng(story_it)
    return story_it


def story_it_02_header(story_it: StoryIt, header_s: str, lc_pair: LcPair) -> StoryIt:
    txtlc_mp: TxtlcMp = find_or_ins_translation(header_s, lc_pair).result
    story_it.txtlc_mp = txtlc_mp
    story_it = upd_ent_ty(story_it, ['txtlc_mp_id'])
    return story_it


def story_it_2n(add: int) -> Optional[StoryIt]:
    story_it = it_paging_val()
    if not story_it:
        TgUIC.uic.no_data()
        return
    story: Story = story_it.story
    idx = story.it_li.index(story_it)
    logger.debug(f'getting story_it at idx: {idx}')
    idx = idx + add
    if idx < 0:
        idx = len(story.it_li) - 1
    elif idx >= len(story.it_li):
        idx = 0
    logger.debug(f'getting story_it at idx: {idx}')
    new_story_it = story.it_li[idx]
    write_to_c_setng(new_story_it)
    menu, menu_it_li = build_menu(new_story_it)
    bot_message: Message = send_menu_keyboard(menu, menu_it_li)
    if not bot_message or not isinstance(bot_message, Message):
        return
    tg_db.synchronize_from_message(bot_message, G3Ctx.g3_m_str, False, sub_module='story', menu_id='trans:story')
    if new_story_it.story.is_lesson():
        send_lesson_audio(new_story_it, False)
    return new_story_it


def story_25(user_id: int, story_bkey: str) -> Optional[Story]:
    story: Story = story_of(user_id, story_bkey)
    if story is None:
        TgUIC.uic.no_data()
        return
    story = sel_story(story.id).result
    return story


def story_menu(user_id: int, story_bkey: str) -> Optional[Message]:
    story: Story = story_of(user_id, story_bkey)
    if story.id:
        story = sel_story(story.id).result
    else:
        TgUIC.uic.error(f'Story {story_bkey} of user {user_id} not found!')
        return
    write_to_c_setng(story)
    if story.it_li:
        write_to_c_setng(story.it_li[0])
    else:
        # noinspection PyTypeChecker
        write_to_c_setng(StoryIt(None, None, None, None))
    if not (story_it_id := read_setng(ELE_TY_story_it_id, True).val, True):
        if not story.it_li:
            TgUIC.uic.error(f'Story (story_id:{story.id}) {story.bkey} has no items!')
            return
        story_it_id = story.it_li[0]
    story_it = story.it_by_id(story_it_id)
    menu, menu_it_li = build_menu(story_it)
    bot_message: Message = send_menu_keyboard(menu, menu_it_li, force_new_msg=True)
    if not bot_message or not isinstance(bot_message, Message):
        return
    tg_db.synchronize_from_message(bot_message, G3Ctx.g3_m_str, False, sub_module='story', menu_id='trans:story')
    if story_it.story.is_lesson():
        send_lesson_audio(story_it, False)
    return bot_message


def story_it_voc(story_it: StoryIt) -> str:
    txt_seq = sel_txt_seq(story_it.p_txt_seq.id_).result
    story_it.p_txt_seq = txt_seq
    vocry = Vocry(G3Ctx.chat_id(), now_for_sql(), txt_seq.lc, txt_seq.lc2)
    vocry_it: VocryIt = VocryIt(vocry, txt_seq, 0)
    vocry.it_li.append(vocry_it)
    txtlc_li: list[dict] = txtlc_li_for_d(vocry.txtlc_d())
    send_str_1: str = ''
    send_str_2: str = ''
    for txtlc_d in txtlc_li:
        txtlc_s = txtlc_d['txtlc'].txt
        if send_str_1:
            send_str_1 = send_str_1 + '\n'
            send_str_2 = send_str_2 + '\n'
        send_str_1 = send_str_1 + babla_link(txtlc_s)
        # send_str_2 = send_str_2 + f'[{txtlc_s}]'
        send_str_2 = send_str_2 + txtlc_s
    # TgUIC.uic.send(send_str_1)
    # TgUIC.uic.send(send_str_2)
    return send_str_2


def story_it_aud(story_it: StoryIt, incl_proj=False):
    txt_seq = sel_txt_seq(story_it.p_txt_seq.id_).result
    story_it.p_txt_seq = txt_seq
    if story_it.story.is_lesson():
        send_lesson_audio(story_it, incl_proj)
    if story_it.txtlc_mp:
        txtlc = story_it.txtlc_mp.txtlc_src
        if not send_txtlc_audio(txtlc, txtlc.txt):
            TgUIC.uic.info(f'No audio for header txtlc (txtlc_id:{txtlc.id_})')
    txtlc = txt_seq.txtlc_mp.txtlc_src
    # noinspection PyUnusedLocal
    if not (g3_file := send_txtlc_audio(txtlc, txtlc.txt)):
        TgUIC.uic.info(f'No audio for txtlc (txtlc_id:{txtlc.id_})')


def story_from_lesson(bkey: str) -> Story:
    lyrics_fl_s: str = os.path.join(env_g3b1_dir, 'vn', bkey, 'lyrics_vi.data')
    story: Story = Story(G3Ctx.chat_id(), G3Ctx.for_user_id(), bkey, Lc.VI)
    with codecs.open(lyrics_fl_s, encoding='UTF-8') as file:
        while line := file.readline().strip():
            seg_li: list[str] = line.split(':')
            if seg_li[1] in ['*', '...']:
                continue
            if len(seg_li) <3:
                logger.error(f'seg_li must have 3 items: {seg_li}')
            txt_seq = utc_txt_seq(f'{seg_li[2]}', seg_li[2].find('|') == -1)
            story_it = StoryIt(story, None, txt_seq, int(seg_li[0]), seg_li[1])
            story.append(story_it)
    story_id = ins_story(story).result.id
    story = sel_story(story_id).result
    write_to_c_setng(story)
    write_to_c_setng(story.it_li[0])
    return story


def story_from_txt_li(txt_li: list[str], bkey: str = '', f_utc=True) -> Story:
    lc_pair = read_setng_lc_pair()
    if not bkey:
        bkey = now_for_sql()
    story: Story = Story(G3Ctx.chat_id(), G3Ctx.for_user_id(), bkey, lc_pair[0])

    head_s: str = ''
    cont_s: str = ''
    for txt in [it.replace('\r\n', '').replace('\n', '') for it in txt_li]:
        if txt.startswith('h:'):
            head_s = txt[2:]
        else:
            cont_s = txt
        if cont_s:
            txt_seq = utc_txt_seq(cont_s, f_utc)
            # noinspection PyTypeChecker
            txtlc_mp = None
            if head_s:
                txtlc_mp: TxtlcMp = find_or_ins_translation(head_s, lc_pair).result
            story.append(StoryIt(story, txtlc_mp, txt_seq))
            head_s = ''
            cont_s = ''
    story_id = ins_story(story).result.id
    story = sel_story(story_id).result
    write_to_c_setng(story)
    write_to_c_setng(story.it_li[0])
    return story
