import logging
import os.path
from builtins import enumerate
from collections import namedtuple
from dataclasses import dataclass, field
from random import shuffle
from typing import Any, Optional, Union

from sqlalchemy.engine import Row
from underthesea import sent_tokenize

from constants import env_g3b1_dir
from decorator import auto_str
from elements import EleVal, ELE_TY_bkey, ELE_TY_tst_type, ELE_TY_user_id, ELE_TY_lc, ELE_TY_lc2
from g3b1_serv.str_utils import italic, bold, uncapitalize
from log import cfg_logger
from py_meta import by_row_initializer
from trans.data import EntTy, ENT_TY_tst_tplate, ENT_TY_txt_seq_it, ENT_TY_txt_seq, ENT_TY_tst_tplate_it, \
    ENT_TY_tst_tplate_it_ans, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym, ENT_TY_txtlc, ENT_TY_tst_run, \
    ENT_TY_tst_run_act_sus, ENT_TY_tst_run_act, ELE_TY_txtlc_id, ELE_TY_txtlc_mp_id, ELE_TY_txt_seq_it_id, \
    ELE_TY_tst_run_act_id, ELE_TY_tst_tplate_id, ELE_TY_tst_run_id, ELE_TY_txt_seq_id, ELE_TY_tst_run_act_sus_id, \
    ELE_TY_tst_tplate_it_ans_id, ELE_TY_tst_tplate_it_id, ENT_TY_txtlc_file, ELE_TY_txtlc_file_id, ELE_TY_txt_menu, \
    ELE_TY_txt_seq_it_num, ENT_TY_story_it, ENT_TY_story, ELE_TY_story_it_id, ELE_TY_story_id, ENT_TY_learned, \
    ELE_TY_learned_id, ENT_TY_vocry_it, ENT_TY_vocry, ENT_TY_vocry_mp_it, ELE_TY_vocry_id, ELE_TY_vocry_it_id, \
    ELE_TY_vocry_mp_it_id, ENT_TY_txt_seq_aud, ELE_TY_txt_seq_aud_id, ELE_TY_story_show_text
from trans.data.enums import Lc, ActTy, Sus

ENT_TY_trans_li = [ENT_TY_tst_tplate, ENT_TY_tst_tplate_it, ENT_TY_tst_tplate_it_ans,
                   ENT_TY_tst_run, ENT_TY_tst_run_act, ENT_TY_tst_run_act_sus,
                   ENT_TY_txt_seq, ENT_TY_txt_seq_it,
                   ENT_TY_txtlc, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym, ENT_TY_txtlc_file,
                   ENT_TY_story, ENT_TY_story_it,
                   ENT_TY_vocry, ENT_TY_vocry_it, ENT_TY_vocry_mp_it]

ELE_TY_trans_li = [ELE_TY_txt_menu,
                   ELE_TY_txtlc_id, ELE_TY_txtlc_mp_id, ELE_TY_txtlc_file_id,
                   ELE_TY_txt_seq_id, ELE_TY_txt_seq_it_id, ELE_TY_txt_seq_it_num,
                   ELE_TY_tst_run_id, ELE_TY_tst_run_act_id, ELE_TY_tst_run_act_sus_id,
                   ELE_TY_tst_tplate_id, ELE_TY_tst_tplate_it_id, ELE_TY_tst_tplate_it_ans_id,
                   ELE_TY_story_id, ELE_TY_story_it_id, ELE_TY_story_show_text,
                   ELE_TY_vocry_id, ELE_TY_vocry_it_id, ELE_TY_vocry_mp_it_id]

ENT_TY_tst_run.cmd_prefix = '.tst.run.'
ENT_TY_tst_run.but_cmd_def = 'qansw'
ENT_TY_tst_run.but_cmd_li = [
    [('<<', 'qprev'), ('😶', 'qinfo'), ('🤔', 'qhint'), ('>>', 'qnext')],
    [('❗', 'tinfo'), ('❓', 'thint'), ('🔐', 'tfnsh')]
]
ENT_TY_tst_run.keyboard_descr = 'Type the answer or choose an option!'
MenuKeyboard = namedtuple('MenuKeyboard', ['menu', 'reply_markup'])

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


class TransSqlDictFactory(dict):
    """Trying to understand dict_factory can result in severe mental pain.
    For now 2021-08-24 2:05pm I have to give up to not risk permanent brain damage"""

    def __new__(cls, *args: Any, **kwargs: Any):
        kv_li: list[tuple[str, Any]] = args[0]
        new_kv_li: list[tuple[str, Any]] = [tuple[str, Any]]
        for tup in kv_li:
            if isinstance(tup[1], Lc):
                new_kv_li.append((tup[0], tup[1].value))
            else:
                new_kv_li.append(tup)
        return super().__new__(cls, new_kv_li, **kwargs)


@dataclass
class Txtlc:
    txt: str = ''
    lc: Lc = None
    s_review: str = ''
    id_: int = field(repr=False, compare=False, default=0)

    # Here we go again (EBTAM forever): get entity type.
    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_txtlc

    @staticmethod
    def from_id(id_: int):
        # noinspection PyTypeChecker,PyArgumentList
        return Txtlc(id_=id_)

    def __post_init__(self):
        pass

    def __repr__(self) -> str:
        return self.txt


class TxtlcFile:
    var_name = 'txtlc_file'
    ent_ty = ENT_TY_txtlc_file
    ele_ty = ELE_TY_txtlc_file_id

    @by_row_initializer
    def __init__(self, txtlc_id: Union[Txtlc, int], file_id: int, user_id: int,
                 ins_tst: str = None, id_: int = 0) -> None:
        super().__init__()
        self.txtlc: Txtlc = txtlc_id
        self.file_id = file_id
        self.user_id = user_id
        self.ins_tst = ins_tst
        self.id = id_
        delattr(self, 'id_')
        delattr(self, 'txtlc_id')

    def get_path(self) -> str:
        fl_s = os.path.join(env_g3b1_dir, 'g3b1_trans', 'txtlc_file', f'{self.id}.mp3')
        return fl_s


@dataclass
class TxtlcOnym:
    txtlc_src: Txtlc
    txtlc_trg: Txtlc
    creator: str
    onym_ty: str = 'syn'
    id_: int = None
    lc: Lc = field(init=False)

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_txtlc_onym

    def __post_init__(self):
        self.lc = self.txtlc_src.lc

    def other_pair_ele(self, txtlc: Txtlc) -> Txtlc:
        if txtlc.id_ == self.txtlc_src.id_:
            return self.txtlc_trg
        if txtlc.id_ == self.txtlc_trg.id_:
            return self.txtlc_src


@dataclass
class TxtlcMp:
    txtlc_src: Txtlc
    txtlc_trg: Txtlc
    lc2: Lc
    translator: str = None
    score: int = 10
    id_: int = None

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_txtlc_mp

    @staticmethod
    def lc_pair(txtlc_mp: "TxtlcMp") -> (Lc, Lc):
        return txtlc_mp.txtlc_src.lc, txtlc_mp.txtlc_trg.lc

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id_)


@dataclass
class TstTplateItAns:
    tst_tplate_it: "TstTplateIt"
    txt_seq_it: "TxtSeqIt"
    txtlc: Txtlc
    ans_num: int
    id_: int = None

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_tplate_it_ans

    # noinspection PyMethodMayBeStatic
    def cascade(self) -> list:
        return []

    def txtlc_src(self) -> Txtlc:
        if self.txt_seq_it:
            return self.txt_seq_it.txtlc_mp.txtlc_src
        else:
            return self.txtlc

    def txtlc_src_alt(self) -> Txtlc:
        if self.txtlc:
            return self.txtlc
        return self.txt_seq_it.txtlc_mp.txtlc_src

    def label(self, txtlc_mapping: TxtlcMp = None):
        label = f'AnsNr: {bold(str(self.ans_num))}: '
        if self.txtlc_src():
            label += self.txtlc_src().txt
            if txtlc_mapping:
                label += f' ({italic(txtlc_mapping.txtlc_trg.txt)})'
            label += '\n'
        return label

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id_)


@dataclass
class TstTplateIt:
    tst_tplate: "TstTplate" = None
    txt_seq: "TxtSeq" = None
    txtlc_qt: Txtlc = None
    itnum: int = 0
    descr: str = None
    ans_li: list[TstTplateItAns] = field(init=False)
    id_: int = None

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_tplate_it

    def __post_init__(self) -> None:
        self.ans_li = []

    def cascade(self) -> list:
        return self.ans_li

    def has_answer(self) -> bool:
        return len(self.ans_li) > 0

    def build_text(self, tst_run: "TstRun" = None) -> str:
        if self.txt_seq:
            if tst_run:
                ans_txt_seq_it_dct: dict[TxtSeqIt, TstTplateItAns] = {ans.txt_seq_it: ans for ans in self.ans_li}
                text_str = ''
                for it in self.txt_seq.it_li:
                    if it in ans_txt_seq_it_dct.keys():
                        ans: TstTplateItAns = ans_txt_seq_it_dct[it]
                        if tst_run.ans_sccs(ans):
                            it_str = f'({ans.ans_num}) {italic(it.txtlc_mp.txtlc_src.txt)}'
                        else:
                            it_str = f'({ans.ans_num}).....'
                        if tst_run.ans_current().ans_num == ans.ans_num:
                            it_str = bold(it_str)
                    else:
                        it_str = it.txtlc_mp.txtlc_src.txt
                    text_str += it_str + ' '
                return TxtSeq.smart_format(text_str)
            return self.txt_seq.txtlc_mp.txtlc_src.txt
        elif self.txtlc_qt:
            return self.txtlc_qt.txt
        else:
            return ''

    def build_descr(self, txtlc_mapping: TxtlcMp = None, tst_run: "TstRun" = None):
        label = f'Item number: {bold(str(self.itnum))}\n'
        if self.txt_seq:
            label += f'TxtSeq ID: {bold(str(self.txt_seq.id_))}\n'
        if self.descr:
            label += bold(self.descr) + '\n'
        it_txt = self.build_text(tst_run).replace(' ,', ',').replace(' .', '.')
        if it_txt:
            label += it_txt + '\n'
            if txtlc_mapping:
                label += italic(txtlc_mapping.txtlc_trg.txt) + '\n'
        return label

    def nxt_num(self) -> int:
        nxt_num: int = 1
        for i in self.ans_li:
            if i.ans_num >= nxt_num:
                nxt_num = i.ans_num + 1
        return nxt_num

    def add_answer(self, txt_seq_it: "TxtSeqIt" = None, txtlc_ans: Txtlc = None) -> TstTplateItAns:
        # noinspection PyArgumentList
        it_ans = TstTplateItAns(self, txt_seq_it, txtlc_ans, self.tst_tplate.nxt_ans_num())
        self.ans_li.append(it_ans)
        return it_ans

    def txt_seq_it(self, txt_seq_it_id: int) -> Optional["TxtSeqIt"]:
        if not self.txt_seq:
            return
        return [it for it in self.txt_seq.it_li if it.id_ == txt_seq_it_id][0]


@dataclass
class TstTplate:
    tst_type: str
    bkey: str
    user_id: int
    lc: Lc
    lc2: Lc
    descr: str = None
    id_: int = None
    it_li: list[TstTplateIt] = field(init=False)

    def __post_init__(self) -> None:
        self.it_li = []

    # noinspection PyArgumentList
    @staticmethod
    def from_row(row: Row) -> "TstTplate":
        return TstTplate(row['tst_type'], row['bkey'], row['tg_user_id'],
                         Lc.fin(row['lc']), Lc.fin(row['lc2']),
                         row['descr'], row['id'])

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_tplate

    def cascade(self) -> list:
        return self.it_li

    def label(self):
        a_str = f'{self.id_}/{self.tst_type}/{self.bkey}'
        lbl_str = f'Id/Type/Bkey: {bold(a_str)}\nQuestions: {len(self.it_li)}\n{self.lc.value} -> {self.lc2.value}'
        if self.descr:
            lbl_str += italic(self.descr) + '\n'
        return lbl_str

    def items_wo_ans(self) -> list[TstTplateIt]:
        it_wo_ans_li: list[TstTplateIt] = []
        for item in self.it_li:
            if not item.has_answer():
                it_wo_ans_li.append(item)
        return it_wo_ans_li

    def add_items_from_map(self, txt_map_li: list[TxtlcMp]):
        id_li: list[int] = []
        for idx, txt_map in enumerate(txt_map_li):
            src_id_ = txt_map.txtlc_src.id_
            if src_id_ in id_li:
                continue
            id_li.append(src_id_)
            # noinspection PyTypeChecker,PyArgumentList
            item = TstTplateIt(self, None, txt_map.txtlc_src, idx + 1)
            # noinspection PyTypeChecker
            item.add_answer(None, txt_map.txtlc_trg)
            self.it_li.append(item)

    def all_ans_li(self) -> list[TstTplateItAns]:
        all_ans_li: list[TstTplateItAns] = [ans for it in self.it_li for ans in it.ans_li]
        return all_ans_li

    def nxt_ans_num(self) -> int:
        nxt_ans_num: int = 1
        for it in self.it_li:
            nxt_ans_num_by_it = it.nxt_num()
            if nxt_ans_num_by_it >= nxt_ans_num:
                nxt_ans_num = nxt_ans_num_by_it
        return nxt_ans_num

    def nxt_num(self) -> int:
        nxt_num: int = 1
        for item in self.it_li:
            if item.itnum >= nxt_num:
                nxt_num = item.itnum + 1
        return nxt_num

    def repl_or_app_item(self, i: TstTplateIt):
        idx_replace = -1
        for idx, item in enumerate(self.it_li):
            if item.itnum == i.itnum:
                idx_replace = idx
                break
        if idx_replace > -1:
            self.it_li[idx_replace] = i
        else:
            self.it_li.append(i)

    def item_by_id(self, item_id) -> TstTplateIt:
        for i in self.it_li:
            if i.id_ == item_id:
                return i

    def item_first(self) -> TstTplateIt:
        if len(self.it_li) == 0:
            # noinspection PyTypeChecker
            return None
        else:
            return self.it_li[0]

    def item_next(self, current_itnum: int) -> TstTplateIt:
        for i in self.it_li:
            if i.itnum > current_itnum:
                return i
        # noinspection PyTypeChecker
        return None

    def lc_pair(self) -> tuple[Lc, Lc]:
        return self.lc, self.lc2

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id_)


# noinspection PyPep8Naming
class TstTplate_:
    tst_tplate: TstTplate
    tst_type: EleVal = EleVal(ELE_TY_tst_type)
    bkey: EleVal = EleVal(ELE_TY_bkey)
    user_id: EleVal = EleVal(ELE_TY_user_id)
    lc: EleVal = EleVal(ELE_TY_lc)
    lc2: EleVal = EleVal(ELE_TY_lc2)

    @staticmethod
    def from_row(row: Row) -> "TstTplate_":
        tst_tplate = TstTplate.from_row(row)
        return TstTplate_(tst_tplate)

    @staticmethod
    def col_order_li() -> list[str]:
        return ['tst_type', 'bkey', 'user_id', 'lc', 'lc2']

    def __init__(self, tst_tplate: TstTplate) -> None:
        super().__init__()
        self.tst_tplate = tst_tplate
        self.tst_type = EleVal(ELE_TY_tst_type, tst_tplate.tst_type)
        self.bkey = EleVal(ELE_TY_bkey, tst_tplate.bkey)
        self.user_id = EleVal(ELE_TY_user_id, tst_tplate.user_id)
        # noinspection PyArgumentList
        self.lc = EleVal(ELE_TY_lc, tst_tplate.lc, tst_tplate.lc.value)
        # noinspection PyArgumentList
        self.lc2 = EleVal(ELE_TY_lc2, tst_tplate.lc2, tst_tplate.lc2.value)


@dataclass
class TstRun:
    tst_tplate: TstTplate
    chat_id: int
    user_id: int
    sta_tst: str = None
    end_tst: str = None
    id_: int = None
    it_li: list["TstRunAct"] = field(init=False)

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_run

    def __post_init__(self) -> None:
        self.it_li = []

    def propagate_tst_tplate(self, tst_tplate: TstTplate) -> None:
        self.tst_tplate = tst_tplate
        all_ans_li: list[TstTplateItAns] = tst_tplate.all_ans_li()
        for i in self.it_li:
            i.propagate_ans(all_ans_li)

    def ans_sccs_li(self) -> list[TstTplateItAns]:
        ans_sccs_li = [it.tst_tplate_it_ans for it in self.it_li if it.is_ans_sccs()]
        return ans_sccs_li

    def ans_open_li(self) -> list[TstTplateItAns]:
        ans_li = self.tst_tplate.all_ans_li()
        ans_sccs_li = self.ans_sccs_li()
        for ans in ans_sccs_li:
            ans_li.remove(ans)
        return ans_li

    def act_add(self, act_ty: ActTy):
        # noinspection PyArgumentList,PyTypeChecker
        self.it_li.append(TstRunAct(self, None, act_ty))

    def act_last(self) -> Optional["TstRunAct"]:
        li_len = len(self.it_li)
        if li_len == 0:
            return
        return self.it_li[li_len - 1]

    def ans_act_add(self, tst_tplate_it_ans: TstTplateItAns, act_ty: ActTy):
        # noinspection PyArgumentList
        self.it_li.append(TstRunAct(self, tst_tplate_it_ans, act_ty))

    def ans_act_sus_add(self, tst_tplate_it_ans: TstTplateItAns, act_ty: ActTy, sus: Sus):
        # noinspection PyArgumentList
        tst_run_act = TstRunAct(self, tst_tplate_it_ans, act_ty)
        tst_run_act.ans_sus_add(sus)
        self.it_li.append(tst_run_act)

    def ans_first(self) -> Optional[TstTplateItAns]:
        all_ans_li = self.tst_tplate.all_ans_li()
        if not all_ans_li:
            return
        return all_ans_li[0]

    def ans_current(self) -> Optional[TstTplateItAns]:
        for i in reversed(self.it_li):
            if i.tst_tplate_it_ans:
                return i.tst_tplate_it_ans
        return self.ans_first()

    def ans_next(self) -> Optional[TstTplateItAns]:
        if not (tst_tplate_it_ans := self.ans_current()):
            return

        all_ans_li = self.tst_tplate.all_ans_li()
        next_idx = all_ans_li.index(tst_tplate_it_ans) + 1
        if next_idx == len(all_ans_li):
            return all_ans_li[0]

        return all_ans_li[next_idx]

    def ans_prev(self) -> Optional[TstTplateItAns]:
        if not (tst_tplate_it_ans := self.ans_current()):
            return

        all_ans_li = self.tst_tplate.all_ans_li()
        prev_idx = all_ans_li.index(tst_tplate_it_ans) - 1
        if prev_idx == -1:
            return all_ans_li[len(all_ans_li) - 1]

        return all_ans_li[prev_idx]

    def ans_sccs(self, ans: TstTplateItAns) -> bool:
        act_sus_li = [act_sus
                      for act in self.it_li if act.tst_tplate_it_ans == ans
                      for act_sus in act.it_li if act_sus.sus == Sus.sccs]
        if act_sus_li:
            return True
        else:
            return False


@dataclass
class TstRunAct:
    tst_run: TstRun
    tst_tplate_it_ans: TstTplateItAns
    act_ty: ActTy
    act_tst: str = None
    txt: str = None
    id_: int = None
    it_li: list["TstRunActSus"] = field(init=False)

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_run_act

    def __post_init__(self) -> None:
        self.it_li = []

    def is_ans_sccs(self) -> bool:
        if not self.tst_tplate_it_ans:
            return False
        sccs_li = [it for it in self.it_li if it.sus == Sus.sccs]
        if sccs_li:
            return True
        else:
            return False

    def propagate_ans(self, tst_tplate_it_ans_li: list[TstTplateItAns]):
        if not self.tst_tplate_it_ans:
            return
        if isinstance(self.tst_tplate_it_ans, int):
            ans_id: int = self.tst_tplate_it_ans
        else:
            ans_id: int = self.tst_tplate_it_ans.id_
        self.tst_tplate_it_ans = [ans for ans in tst_tplate_it_ans_li if ans.id_ == ans_id][0]
        for i in self.it_li:
            i.tst_tplate_it_ans = self.tst_tplate_it_ans

    def ans_sus_add(self, sus: Sus) -> "TstRunActSus":
        tst_run_act_sus = TstRunActSus(self, sus)
        self.it_li.append(tst_run_act_sus)
        return tst_run_act_sus


@dataclass
class TstRunActSus:
    tst_run_act: TstRunAct
    sus: Sus
    tst_tplate_it_ans: TstTplateItAns = None
    id_: int = None

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_tst_run_act_sus

    def __post_init__(self) -> None:
        if not self.tst_tplate_it_ans:
            self.tst_tplate_it_ans = self.tst_run_act.tst_tplate_it_ans


@dataclass
class TxtSeqIt:
    txt_seq: "TxtSeq"
    txtlc_mp: TxtlcMp
    rowno: int
    id_: int = None

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_txt_seq_it

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id_)


@dataclass
class TxtSeq:
    chat_id: int
    txt: str
    lc: Lc
    lc2: Lc
    txtlc_mp: TxtlcMp = None
    id_: int = None
    it_li: list[TxtSeqIt] = field(init=False)

    @staticmethod
    def ent_ty() -> EntTy:
        return ENT_TY_txt_seq

    @staticmethod
    def sc_li() -> list[str]:
        return ['.', ',', '!', ';', ':', '?']

    @classmethod
    def smart_format(cls, src_str: str, f_sc=True) -> str:
        txt = src_str
        if src_str.startswith('|||'):
            # split sentences with nlp which currently already automatically done in the code block after...
            token_li: list[str] = sent_tokenize(txt[3:])
            txt = '||' + '|'.join(token_li)
        if src_str.startswith('||'):
            # Example input: "||Hello world, how |  are| you today ! Is |everything|  OK?"
            # output: "||Hello world|,|how|are|you today|!|Is|everything|OK|?|
            txt = txt.replace('  ', ' ')
            txt = txt.replace('| ', '|').replace(' |', '|')
            if f_sc:
                for sc in cls.sc_li():
                    txt = txt.replace(f'{sc} ', sc).replace(f' {sc}', sc).replace(sc, f'|{sc}|')
            txt = '||' + txt[2:].replace('||', '|')
        txt = txt.strip('|')
        return txt

    @classmethod
    def output_format(cls, text_str: str) -> str:
        for sc in cls.sc_li():
            text_str = text_str.replace(f' {sc}', sc)
        return text_str.strip()

    @classmethod
    def new(cls, chat_id: int, txt: str, lc_pair: tuple[Lc, Lc]) -> "TxtSeq":
        return cls(chat_id, txt, lc_pair[0], lc_pair[1])

    def __post_init__(self) -> None:
        self.it_li = []

    def it(self, itnum: int) -> TxtSeqIt:
        for item in self.it_li:
            if itnum == item.rowno:
                return item

    def convert_to_it_li(self, txt_map_li: list[TxtlcMp]):
        self.it_li: list[TxtSeqIt] = \
            [TxtSeqIt(self, txt_map, idx + 1) for idx, txt_map in enumerate(txt_map_li)]

    def it_by_txt(self, ans_str: str) -> TxtSeqIt:
        for item in self.it_li:
            if item.txtlc_mp.txtlc_src.txt == ans_str:
                return item


@auto_str
class Vocry:
    var_name = 'vocry'
    ent_ty = ENT_TY_vocry
    ele_ty = ELE_TY_vocry_id

    @by_row_initializer
    def __init__(self, chat_id, bkey: str, lc: Union[Lc, str], lc2: Union[Lc, str], id_: int = 0) -> None:
        super().__init__()
        self.chat_id = chat_id
        self.bkey = bkey
        self.lc: Lc = Lc.fin(str(lc))
        self.lc2: Lc = Lc.fin(str(lc2))
        self.id = id_
        self.it_li: list["VocryIt"] = []
        self.mp_it_li: list["VocryMpIt"] = []
        delattr(self, 'id_')

    def txtlc_d(self) -> dict:
        res_d: dict = {}
        for it in [i for i in self.it_li if i.p_txt_seq]:
            it_li = it.p_txt_seq.it_li
            for idx, txt_seq_it in enumerate(it_li):
                txtlc: Txtlc = txt_seq_it.txtlc_mp.txtlc_src
                if txtlc.id_ in res_d.keys():
                    continue
                text_li: list[str] = []
                if idx > 0:
                    text_li.append(it_li[idx - 1].txtlc_mp.txtlc_src.txt)
                text_li.append(txtlc.txt)
                if idx + 1 < len(it_li):
                    text_li.append(it_li[idx + 1].txtlc_mp.txtlc_src.txt)
                res_d[txtlc.id_] = {'txtlc': txtlc, 'text': ' '.join(text_li)}
        return res_d

    def build_mp_li(self) -> list["VocryMpIt"]:
        txt_seq_it_li: list[TxtSeqIt] = []
        for vocry_it in self.it_li:
            txt_seq_it_li.extend(vocry_it.p_txt_seq.it_li)
        txtlc_mp_set = set([txt_seq_it.txtlc_mp for txt_seq_it in txt_seq_it_li])
        it_li: list[VocryMpIt] = [VocryMpIt(self, txtlc_mp) for txtlc_mp in txtlc_mp_set]
        shuffle(it_li)
        self.mp_it_li = it_li
        return self.mp_it_li

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id)


@auto_str
class VocryIt:
    var_name = 'vocry_it'
    ent_ty = ENT_TY_vocry_it
    ele_ty = ELE_TY_vocry_it_id

    @by_row_initializer
    def __init__(self, vocry_id: Union[Vocry, int], p_txt_seq_id: Union[TxtSeq, int], rowno: int, id_: int = 0) -> None:
        super().__init__()
        self.vocry = vocry_id
        self.p_txt_seq: TxtSeq = p_txt_seq_id
        if not rowno:
            self.rowno = len(self.vocry.it_li) + 1
        else:
            self.rowno = rowno
        self.id = id_
        delattr(self, 'id_')
        delattr(self, 'vocry_id')
        delattr(self, 'p_txt_seq_id')


@auto_str
class VocryMpIt:
    var_name = 'vocry_mp_it'
    ent_ty = ENT_TY_vocry_mp_it
    ele_ty = ELE_TY_vocry_mp_it_id

    @by_row_initializer
    def __init__(self, vocry_id: Union[Vocry, int], txtlc_mp_id: Union[TxtlcMp, int], id_: int = 0) -> None:
        super().__init__()
        self.vocry = vocry_id
        self.txtlc_mp: TxtlcMp = txtlc_mp_id
        self.id = id_
        delattr(self, 'id_')
        delattr(self, 'vocry_id')
        delattr(self, 'txtlc_mp_id')


@auto_str
class Learned:
    var_name = 'learned'
    ent_ty = ENT_TY_learned
    ele_ty = ELE_TY_learned_id

    @by_row_initializer
    def __init__(self, user_id: int, txtlc_id: Union[Txtlc, int], f_learned=False, ins_tst: str = None,
                 id_: int = 0) -> None:
        super().__init__()
        self.user_id = user_id
        self.txtlc = txtlc_id
        self.ins_tst = ins_tst
        self.f_learned = f_learned
        self.id = id_
        delattr(self, 'id_')
        delattr(self, 'txtlc_id')
        delattr(self, 'f_learned')


class Story:
    var_name = 'story'
    ent_ty = ENT_TY_story
    ele_ty = ELE_TY_story_id

    @by_row_initializer
    def __init__(self, chat_id: int, user_id: int, bkey: str, lc: Lc, id_: int = 0) -> None:
        super().__init__()
        # noinspection PyTypeChecker
        self.id: int = id_
        self.chat_id = chat_id
        self.user_id = user_id
        self.bkey = bkey
        self.lc = lc
        self.it_li: list[StoryIt] = []
        delattr(self, 'id_')

    def __len__(self) -> int:
        return len(self.it_li)

    def is_lesson(self) -> bool:
        fl_base_cfg_s: str = os.path.join(self.base_dir(), 'base.cfg')
        path_exists = os.path.exists(fl_base_cfg_s)
        return path_exists

    def base_aud_seg_fl(self, seg: int) -> Optional[str]:
        if not self.is_lesson():
            return
        seg_s = str(seg).rjust(3, '0')
        base_aud_seg_fl = os.path.join(self.base_dir(), 'split', f'{seg_s}.mp3')
        if not os.path.exists(base_aud_seg_fl):
            logger.error(f'404: {base_aud_seg_fl}')
        return base_aud_seg_fl

    def base_dir(self) -> Optional[str]:
        return os.path.join(env_g3b1_dir, 'vn', self.bkey)

    def append(self, story_it: "StoryIt") -> "StoryIt":
        self.it_li.append(story_it)
        return story_it

    def it_by_xxx(self, val: int) -> "StoryIt":
        if story_it := self.it_by_rowno(val):
            return story_it
        else:
            return self.it_by_id(val)

    def it_by_rowno(self, rowno: int) -> "StoryIt":
        for it in self.it_li:
            if it.rowno == rowno:
                return it

    def it_by_id(self, id_: int) -> "StoryIt":
        for it in self.it_li:
            if it.id == id_:
                return it

    def __str__(self):
        return '%s (%s: %s)' % (
            self.bkey,
            uncapitalize(type(self).__name__) + '_id',
            self.id)


@auto_str
class StoryIt:
    var_name = 'story_it'
    ent_ty = ENT_TY_story_it
    ele_ty = ELE_TY_story_it_id

    @by_row_initializer
    def __init__(self, story_id: Union[Story, int], txtlc_mp_id: [TxtlcMp, int], p_txt_seq_id: Union[TxtSeq, int],
                 rowno=0, role='',
                 id_: int = 0) -> None:
        super().__init__()
        self.story: Story = story_id
        if txtlc_mp_id:
            self.txtlc_mp: TxtlcMp = txtlc_mp_id
        else:
            # noinspection PyTypeChecker
            self.txtlc_mp: TxtlcMp = None
        self.rowno = rowno
        if not rowno:
            if not story_id:
                self.rowno = 0
            elif isinstance(story_id, int):
                self.rowno = 0
            else:
                self.rowno = len(self.story) + 1
        self.p_txt_seq: TxtSeq = p_txt_seq_id
        self.id = id_
        self.role = role
        delattr(self, 'id_')
        delattr(self, 'story_id')
        delattr(self, 'txtlc_mp_id')
        delattr(self, 'p_txt_seq_id')

    def base_seg_fl(self) -> Optional[str]:
        return self.story.base_aud_seg_fl(self.rowno)

    def vers_seg_fl_li(self) -> list[str]:
        # files expected in {g3b1_dir}/vn/{story.bkey}/proj/***/vers/***/seg_subst
        res_li = []
        base_seg_fl = os.path.split(self.base_seg_fl())[1]
        for root, dirs, files in os.walk(os.path.join(self.story.base_dir(), 'proj')):
            if base_seg_fl in files:
                res_li.append(os.path.join(root, base_seg_fl))
        return res_li

    def str_compact(self, width=33) -> str:
        res_s = f'{self.p_txt_seq.txt[0:width - 3].ljust(width, ".")}'
        if self.txtlc_mp:
            res_s = f'Hd: {self.txtlc_mp.txtlc_src.txt} - {res_s}'
        res_s = f'(No:{self.rowno}) {res_s}'
        return res_s


@auto_str
class TxtSeqAud:
    var_name = 'txt_seq_aud'
    ent_ty = ENT_TY_txt_seq_aud
    ele_ty = ELE_TY_txt_seq_aud_id

    @by_row_initializer
    def __init__(self, user_id: int, p_txt_seq_id: Union[TxtSeq, int], ins_tst: str = None,
                 id_: int = 0) -> None:
        super().__init__()
        self.user_id = user_id
        self.p_txt_seq: TxtSeq = p_txt_seq_id
        self.ins_tst = ins_tst
        self.id = id_
        delattr(self, 'id_')
        delattr(self, 'p_txt_seq_id')
