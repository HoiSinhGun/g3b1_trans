from builtins import enumerate
from enum import Enum

from sqlalchemy.engine import Row

from elements import *
from entities import Entity, ENT_TY_tst_tplate, ENT_TY_txt_seq_it, ENT_TY_txt_seq, ENT_TY_tst_tplate_it, \
    ENT_TY_tst_tplate_it_ans, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym, ENT_TY_txtlc
from g3b1_serv.tg_reply import bold, italic


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


class Lc(Enum):
    # Never change this order
    # When adding new entries, please make sure that EN stays at the bottom.
    # After all I am writing all comments in EN: isn't that honour enough?
    TR = 'TR'  # There are people who can whistle in Turkish, I hope I can visit that village before
    # some billionaire discovers it and turns it into another Disney Land for whatever reason
    RU = 'RU'  # Did you know: an influential business man is called oligarch in Russia and philanthropist in US
    DE = 'DE'
    VI = 'VI'
    VN = 'VI'
    LA = 'LA'
    IT = 'IT'
    ES = 'ES'
    FR = 'FR'
    EN = 'EN'

    @staticmethod
    def to_str_pair(lc_pair: tuple["Lc", "Lc"]) -> tuple[str, str]:
        return lc_pair[0].value, lc_pair[1].value

    @staticmethod
    def from_str_pair(lc_pair: tuple[str, str]) -> tuple["Lc", "Lc"]:
        return Lc.find_lc(lc_pair[0]), Lc.find_lc(lc_pair[1])

    @staticmethod
    def find_lc(lc_str: str) -> "Lc":
        if not lc_str:
            # noinspection PyTypeChecker
            return None
        for k, lc in Lc.__members__.items():
            if k == lc_str:
                return lc
        # noinspection PyTypeChecker
        return None


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
    def ent_ty() -> Entity:
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
    def ent_ty() -> Entity:
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

    @staticmethod
    def ent_ty() -> Entity:
        return ENT_TY_txtlc_mp


@dataclass
class TstTplateItAns:
    tst_tplate_it: "TstTplateIt"
    txt_seq_it: "TxtSeqIt"
    txtlc: Txtlc
    ans_num: int
    id_: int = None

    @staticmethod
    def ent_ty() -> Entity:
        return ENT_TY_tst_tplate_it_ans

    # noinspection PyMethodMayBeStatic
    def cascade(self) -> list:
        return []

    def txtlc_src(self) -> Txtlc:
        if self.txt_seq_it:
            return self.txt_seq_it.txtlc_trg
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
    def ent_ty() -> Entity:
        return ENT_TY_tst_tplate_it

    def __post_init__(self) -> None:
        self.ans_li = []

    def cascade(self) -> list:
        return self.ans_li

    def has_answer(self) -> bool:
        return len(self.ans_li) > 0

    def text(self) -> str:
        if self.txt_seq:
            return self.txt_seq.txtlc_src.txt
        elif self.txtlc_qt:
            return self.txtlc_qt.txt
        else:
            return ''

    def label(self, txtlc_mapping: TxtlcMp = None):
        label = f'Item number: {bold(str(self.itnum))}\n'
        if self.descr:
            label += bold(self.descr) + '\n'
        it_txt = self.text()
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

    def add_answer(self, txt_seq_it: "TxtSeqIt", txtlc_ans: Txtlc) -> TstTplateItAns:
        # noinspection PyArgumentList
        it_ans = TstTplateItAns(self, txt_seq_it, txtlc_ans, self.tst_tplate.nxt_ans_num())
        self.ans_li.append(it_ans)
        return it_ans


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
                         Lc.find_lc(row['lc']), Lc.find_lc(row['lc2']),
                         row['descr'], row['id'])

    @staticmethod
    def ent_ty() -> Entity:
        return ENT_TY_tst_tplate

    def cascade(self) -> list:
        return self.it_li

    def label(self):
        a_str = f'{self.id_}/{self.tst_type}/{self.bkey}'
        lbl_str = f'Id/Type/Bkey: {bold(a_str)}\n{self.lc.value} -> {self.lc2.value}'
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
    user_id: int
    chat_id: int
    str_tst: str = None
    end_tst: str = None
    id_: int = None
    it_li: list[TstTplateIt] = field(init=False)

    def __post_init__(self) -> None:
        self.it_li = []


@dataclass
class TstRunAct:
    tst_tplate: TstTplate
    user_id: int
    chat_id: int
    str_tst: str = None
    end_tst: str = None
    id_: int = None
    it_li: list[TstTplateIt] = field(init=False)

    def __post_init__(self) -> None:
        self.it_li = []


@dataclass
class TxtSeqIt:
    txt_seq: "TxtSeq"
    txtlc_trg: Txtlc
    itnum: int
    id_: int = None

    @staticmethod
    def ent_ty() -> Entity:
        return ENT_TY_txt_seq_it


@dataclass
class TxtSeq:
    txtlc_src: Txtlc
    lc: Lc = field(init=False)
    id_: int = None
    seq_str: str = ''
    it_li: list[TxtSeqIt] = field(init=False)

    @staticmethod
    def ent_ty() -> Entity:
        return ENT_TY_txt_seq

    def __post_init__(self) -> None:
        self.lc = self.txtlc_src.lc
        self.it_li = []

    def it(self, itnum: int) -> TxtSeqIt:
        for item in self.it_li:
            if itnum == item.itnum:
                return item

    def convert_to_it_li(self, txt_map_li: list[TxtlcMp]):
        self.it_li: list[TxtSeqIt] = []
        self.seq_str = ''
        count = 0
        li_li = len(txt_map_li) - 1
        for idx, txt_map in enumerate(txt_map_li):
            src_len = len(txt_map.txtlc_src.txt.split(' '))
            count += src_len
            self.seq_str += str(count)
            if idx < li_li:
                self.seq_str += ','
            # noinspection PyArgumentList
            self.it_li.append(TxtSeqIt(self, txt_map.txtlc_src, idx))
