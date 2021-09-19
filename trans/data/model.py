from builtins import enumerate
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.engine import Row

from elements import EleVal, ELE_TY_bkey, ELE_TY_tst_type, ELE_TY_user_id, ELE_TY_lc, ELE_TY_lc2
from entities import EntTy, ENT_TY_tst_tplate, ENT_TY_txt_seq_it, ENT_TY_txt_seq, ENT_TY_tst_tplate_it, \
    ENT_TY_tst_tplate_it_ans, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym, ENT_TY_txtlc, ENT_TY_tst_run, \
    ENT_TY_tst_run_act_sus, ENT_TY_tst_run_act
from g3b1_serv.tg_reply import bold, italic
from trans.data.enums import Lc, ActTy, Sus


def user_settings(user_id: int, lc: str = None, lc2: str = None) -> dict[str, str]:
    user_set_dct = dict(user_id=str(user_id))
    if lc:
        user_set_dct['lc'] = lc
    if lc2:
        user_set_dct['lc2'] = lc2
    return user_set_dct


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
    id_: int = field(repr=False, compare=False, default=0)

    # Here we go: get entity type. I wrote that code before in Java
    # In some product called Innbound. Owned by some Swiss company.
    # Later on bought by some other company who forgot to look at what they actually bought.
    # Their bosses incapable of selling the software.
    # They wanted me also to sell the software.
    # And I wondered why the heck am I an employee?
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

    def label(self, txtlc_mapping: TxtlcMp = None):
        label = f'AnsNr: {bold(str(self.ans_num))}: '
        if self.txtlc_src():
            label += self.txtlc_src().txt
            if txtlc_mapping:
                label += f' ({italic(txtlc_mapping.txtlc_trg.txt)})'
            label += '\n'
        return label


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

    def text(self) -> str:
        if self.txt_seq:
            return self.txt_seq.txtlc_mp.txtlc_src.txt
        elif self.txtlc_qt:
            return self.txtlc_qt.txt
        else:
            return ''

    def label(self, txtlc_mapping: TxtlcMp = None):
        label = f'Item number: {bold(str(self.itnum))}\n'
        if self.txt_seq:
            label += f'TxtSeq ID: {bold(str(self.txt_seq.id_))}\n'
        if self.descr:
            label += bold(self.descr) + '\n'
        it_txt = self.text().replace(' ,', ',').replace(' .', '.')
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
        self.lc = EleVal(ELE_TY_lc, tst_tplate.lc, tst_tplate.lc.value)
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
    def smart_format(cls, src_str: str) -> str:
        txt = src_str
        if src_str.startswith('||'):
            # Example input: "||Hello world, how |  are| you today ! Is |everything|  OK?"
            # output: "||Hello world|,|how|are|you today|!|Is|everything|OK|?|
            txt = txt.replace('  ', ' ')
            txt = txt.replace('| ', '|').replace(' |', '|')
            for sc in cls.sc_li():
                txt = txt.replace(f'{sc} ', sc).replace(f' {sc}', sc).replace(sc, f'|{sc}|')
        txt = txt.strip('|')
        return txt

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
