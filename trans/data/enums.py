from enum import Enum


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
    def by_val(val: str) -> "ActTy":
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
    def by_val(val: str) -> "Sus":
        if not val:
            # noinspection PyTypeChecker
            return None
        for k, v in ActTy.__members__.items():
            if k == v:
                return v
        # noinspection PyTypeChecker
        return None