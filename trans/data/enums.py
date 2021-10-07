from enum import Enum

from elements import EleVal


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
        return Lc.fin(lc_pair[0]), Lc.fin(lc_pair[1])

    @staticmethod
    def fin(lc_str: str) -> "Lc":
        if not lc_str:
            # noinspection PyTypeChecker
            return None
        for k, lc in Lc.__members__.items():
            if k == lc_str:
                return lc
        # noinspection PyTypeChecker
        return None

    @classmethod
    def from_ele_val(cls, ele_val: EleVal) -> EleVal:
        ele_val.val_mp = cls.fin(ele_val.val)
        return ele_val


class LcPair:

    def __init__(self, lc: Lc, lc2: Lc) -> None:
        super().__init__()
        self.lc = lc
        self.lc2 = lc2

    @classmethod
    def from_tup(cls, lc_pair: tuple[Lc, Lc]):
        return cls(lc_pair[0], lc_pair[1])

    @classmethod
    def from_ele_val(cls, ele_val: EleVal) -> EleVal:
        lc_tup: tuple[str, ...] = ele_val.val
        lc_pair = cls(Lc.fin(lc_tup[0]), Lc.fin(lc_tup[1]))
        ele_val.val_mp = lc_pair
        return ele_val


class ActTy(Enum):
    help = 'help'
    qnext = 'qnext'
    qprev = 'qprev'
    qinfo = 'qinfo'
    qhint = 'qhint'
    qansw = 'qansw'
    tinfo = 'tinfo'
    thint = 'thint'
    tfnsh = 'tfnsh'

    @staticmethod
    def fin(val: str) -> "ActTy":
        if not val:
            # noinspection PyTypeChecker
            return None
        for k, v in ActTy.__members__.items():
            if k == v:
                return v
        # noinspection PyTypeChecker
        return None


class Sus(Enum):
    sccs = 'sccs'
    fail = 'fail'

    @staticmethod
    def fin(val: str) -> "Sus":
        if not val:
            # noinspection PyTypeChecker
            return None
        for k, v in Sus.__members__.items():
            if val == k:
                return v
        # noinspection PyTypeChecker
        return None
