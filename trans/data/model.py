from builtins import enumerate
from dataclasses import dataclass, field

from g3b1_serv.tg_reply import bold

TEST_TYPE_VOCABULARY = 'vocabulary'
TEST_TYPES_LI = [TEST_TYPE_VOCABULARY]


def user_settings(user_id: int, lc: str = None, lc_2: str = None) -> dict[str, str]:
    user_set_dct = dict(user_id=str(user_id))
    if lc:
        user_set_dct['lc'] = lc
    if lc_2:
        user_set_dct['lc_2'] = lc_2
    return user_set_dct


@dataclass()
class TxtLC:
    txt: str
    lc: str
    id_: int = field(repr=False, compare=False, default=0)

    @staticmethod
    def from_id(id_: int):
        return TxtLC('', '', id_)

    def __post_init__(self):
        # self.txt = self.txt.lower()
        self.lc = self.lc.upper()


@dataclass()
class TxtLCOnym:
    txtlc_src: TxtLC
    txtlc_trg: TxtLC
    creator: str
    onym_ty: str = 'syn'
    id_: int = None
    lc: str = field(init=False)

    def __post_init__(self):
        self.lc = self.txtlc_src.lc

    def other_pair_ele(self, txtlc: TxtLC) -> TxtLC:
        if txtlc.id_ == self.txtlc_src.id_:
            return self.txtlc_trg
        if txtlc.id_ == self.txtlc_trg.id_:
            return self.txtlc_src


@dataclass()
class TxtLCMapping:
    txtlc_src: TxtLC
    txtlc_trg: TxtLC
    lc_2: str
    translator: str = None
    score: int = 10


@dataclass()
class TstTemplateItAns:
    txtlc: TxtLC
    ans_num: int
    id_: int = None

    @staticmethod
    def ans_from_sql_dct(row_dct: dict):
        return TstTemplateItAns(TxtLC('', '', row_dct['txtlc_id']), row_dct['ans_num'], id_=row_dct['id_'])


@dataclass()
class TstTemplateIt:
    tst_template: "TstTemplate"
    txtlc_qt: TxtLC
    itnum: int
    descr: str = None
    txtlc_ans_li: list[TstTemplateItAns] = field(init=False)
    id_: int = None

    def __post_init__(self) -> None:
        self.txtlc_ans_li = []

    def has_answer(self) -> bool:
        return len(self.txtlc_ans_li) > 0

    def label(self):
        tst_item_lbl = bold(f'Item number: {self.itnum}\n')
        if self.descr:
            tst_item_lbl += self.descr + '\n'
        tst_item_lbl += bold(self.txtlc_qt.txt) + '\n'
        return tst_item_lbl

    def nxt_num(self) -> int:
        nxt_num: int = 1
        for i in self.txtlc_ans_li:
            if i.ans_num >= nxt_num:
                nxt_num = i.ans_num + 1
        return nxt_num

    def add_answer(self, txtlc_ans: TxtLC) -> TstTemplateItAns:
        it_ans = TstTemplateItAns(txtlc_ans, self.nxt_num())
        self.txtlc_ans_li.append(it_ans)
        return it_ans


@dataclass()
class TstTemplate:
    tst_type: str
    bkey: str
    lc: str
    lc_2: str
    descr: str = None
    id_: int = None
    item_li: list[TstTemplateIt] = field(init=False)

    def __post_init__(self) -> None:
        self.item_li = []

    def items_wo_ans(self) -> list[TstTemplateIt]:
        it_wo_ans_li: list[TstTemplateIt] = []
        for item in self.item_li:
            if not item.has_answer():
                it_wo_ans_li.append(item)
        return it_wo_ans_li

    def add_items_from_map(self, txt_map_li: list[TxtLCMapping]):
        id_li: list[int] = []
        for idx, txt_map in enumerate(txt_map_li):
            src_id_ = txt_map.txtlc_src.id_
            if src_id_ in id_li:
                continue
            id_li.append(src_id_)
            item = TstTemplateIt(self, txt_map.txtlc_src, idx + 1)
            item.add_answer(txt_map.txtlc_trg)
            self.item_li.append(item)

    def nxt_num(self) -> int:
        nxt_num: int = 1
        for item in self.item_li:
            if item.itnum >= nxt_num:
                nxt_num = item.itnum + 1
        return nxt_num

    def repl_or_app_item(self, i: TstTemplateIt):
        idx_replace = -1
        for idx, item in enumerate(self.item_li):
            if item.itnum == i.itnum:
                idx_replace = idx
                break
        if idx_replace > -1:
            self.item_li[idx_replace] = i
        else:
            self.item_li.append(i)

    def item_by_id(self, item_id) -> TstTemplateIt:
        for i in self.item_li:
            if i.id_ == item_id:
                return i

    def item_first(self) -> TstTemplateIt:
        if len(self.item_li) == 0:
            return None
        else:
            return self.item_li[0]

    def item_next(self, current_itnum: int) -> TstTemplateIt:
        for i in self.item_li:
            if i.itnum > current_itnum:
                return i
        return None


@dataclass()
class TxtSeqItem:
    txtlc_trg: TxtLC
    itnum: int
    id_: int = field(init=False)


@dataclass()
class TxtSeq:
    txtlc_src: TxtLC
    lc: str = field(init=False)
    id_: int = None
    item_li: list[TxtSeqItem] = field(init=False)
    seq_str: str = ''

    def __post_init__(self) -> None:
        self.lc = self.txtlc_src.lc

    def convert_to_item_li(self, txt_map_li: list[TxtLCMapping]):
        self.item_li = []
        self.seq_str = ''
        count = 0
        li_li = len(txt_map_li) - 1
        for idx, txt_map in enumerate(txt_map_li):
            src_len = len(txt_map.txtlc_src.txt.split(' '))
            count += src_len
            self.seq_str += str(count)
            if idx < li_li:
                self.seq_str += ','
            self.item_li.append(TxtSeqItem(txt_map.txtlc_src, idx))
