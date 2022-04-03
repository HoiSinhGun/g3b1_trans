from unittest import TestCase

from entities import EntId
from g3b1_cfg.tg_cfg import G3Ctx
from test_utils import MockChat, MockUpdate, MockUser
from tg_db import sel_ent_ty_li, ins_ent_ty, del_ent_ty
from trans.data import ENT_TY_txt_seq, md_TRANS, eng_TRANS, BOT_BKEY_TRANS, ENT_TY_story
from trans.data.db import ins_story, sel_story, fin_story, sel_txt_seq
from trans.data.enums import Lc
from trans.data.model import Story, StoryIt, TxtSeq


class TestStory(TestCase):
    def test_ins(self):
        G3Ctx.md = md_TRANS
        G3Ctx.eng = eng_TRANS
        G3Ctx.g3_m_str = BOT_BKEY_TRANS
        chat_id = 1749165037
        mock_chat = MockChat(chat_id)
        user_id = 1749165037
        G3Ctx.upd = MockUpdate(mock_chat, MockUser(user_id))

        story_found = fin_story(chat_id, 'test')
        # if doesnt work... I dont know why....if story_found and story_found.id:
        # noinspection PyBroadException
        try:
            story_sel: Story = sel_story(story_found.id).result
            del_ent_ty(EntId(ENT_TY_story, story_sel.id))
            print(f'Removed story with id: {id}', story_sel.id)
        except Exception as e:
            if story_found:
                print(f'story {story_found.id} not deleted')
            else:
                print(f'story found {story_found}')

        story = Story(chat_id, user_id, 'test', Lc.VI)
        txt_seq_row_li = sel_ent_ty_li(ENT_TY_txt_seq)
        txt_seq_id: int = txt_seq_row_li[0]['id']
        txt_seq: TxtSeq = sel_txt_seq(txt_seq_id).result
        story_it = StoryIt(story, 0, txt_seq, 0)
        story.it_li.append(story_it)
        g_result = ins_story(story)
        story = g_result.result
        print(story)
        print(story.it_li[0])

        txt_seq_id: int = txt_seq_row_li[1]['id']
        txt_seq: TxtSeq = sel_txt_seq(txt_seq_id).result
        story_it = StoryIt(story, 0, txt_seq, 0)
        story_it_ins = ins_ent_ty(story_it).result
        print(story_it_ins)

    def test_story_lesson_seg_fl(self):
        story = Story(666, 555, 'E24', Lc.VI)
        story_it = story.append(StoryIt(story, None, 1, 3))
        print('\n'.join(story_it.vers_seg_fl_li()))

