from sqlalchemy import select, delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from trans.data import eng_TRANS
from trans.data.model_orm import Dic
from trans.data.model_orm import Txtlc
from trans.data.model_orm import Wrd
from trans.data.model_orm import WrdR
from trans.data.model_orm import WrdTxtSeq


def sel_dic(id_: int) -> Dic:
    session = Session(eng_TRANS)
    res: CursorResult = session.execute(select(Dic).where(Dic.id == id_))
    dic = res.first()
    session.close()
    return dic.Dic


def fin_dic(bkey: str = ''):
    session = Session(eng_TRANS)
    stmnt = select(Dic)
    if bkey:
        stmnt = stmnt.where(Dic.bkey == bkey)
    res: CursorResult = session.execute(stmnt)
    dic_li = res.all()
    session.close()
    return [dic.Dic for dic in dic_li]


def del_dic(dic: Dic):
    session = Session(eng_TRANS)
    stmnt = delete(Dic).where(Dic.id == dic.id)
    # noinspection PyUnusedLocal
    res: CursorResult = session.execute(stmnt)
    session.commit()
    session.close()


def ins_dic(dic: Dic):
    session = Session(eng_TRANS)
    session.add(dic)
    session.commit()
    session.close()


def sel_txtlc(id_: int) -> Txtlc:
    session = Session(eng_TRANS)
    res: CursorResult = session.execute(select(Txtlc).where(Txtlc.id == id_))
    txtlc = res.first()
    session.close()
    return txtlc.Txtlc


def fin_txtlc(bkey: str = ''):
    session = Session(eng_TRANS)
    stmnt = select(Txtlc)
    if bkey:
        stmnt = stmnt.where(Txtlc.bkey == bkey)
    res: CursorResult = session.execute(stmnt)
    txtlc_li = res.all()
    session.close()
    return [txtlc.Txtlc for txtlc in txtlc_li]


def del_txtlc(txtlc: Txtlc):
    session = Session(eng_TRANS)
    stmnt = delete(Txtlc).where(Txtlc.id == txtlc.id)
    # noinspection PyUnusedLocal
    res: CursorResult = session.execute(stmnt)
    session.commit()
    session.close()


def ins_txtlc(txtlc: Txtlc):
    session = Session(eng_TRANS)
    session.add(txtlc)
    session.commit()
    session.close()


def sel_wrd(id_: int) -> Wrd:
    session = Session(eng_TRANS)
    res: CursorResult = session.execute(select(Wrd).where(Wrd.id == id_))
    wrd = res.first()
    session.close()
    return wrd.Wrd


def fin_wrd(bkey: str = ''):
    session = Session(eng_TRANS)
    stmnt = select(Wrd)
    if bkey:
        stmnt = stmnt.where(Wrd.bkey == bkey)
    res: CursorResult = session.execute(stmnt)
    wrd_li = res.all()
    session.close()
    return [wrd.Wrd for wrd in wrd_li]


def del_wrd(wrd: Wrd):
    session = Session(eng_TRANS)
    stmnt = delete(Wrd).where(Wrd.id == wrd.id)
    # noinspection PyUnusedLocal
    res: CursorResult = session.execute(stmnt)
    session.commit()
    session.close()


def ins_wrd(wrd: Wrd):
    session = Session(eng_TRANS)
    session.add(wrd)
    session.commit()
    session.close()


def sel_wrd_r(id_: int) -> WrdR:
    session = Session(eng_TRANS)
    res: CursorResult = session.execute(select(WrdR).where(WrdR.id == id_))
    wrd_r = res.first()
    session.close()
    return wrd_r.WrdR


def fin_wrd_r(bkey: str = ''):
    session = Session(eng_TRANS)
    stmnt = select(WrdR)
    if bkey:
        stmnt = stmnt.where(WrdR.bkey == bkey)
    res: CursorResult = session.execute(stmnt)
    wrd_r_li = res.all()
    session.close()
    return [wrd_r.WrdR for wrd_r in wrd_r_li]


def del_wrd_r(wrd_r: WrdR):
    session = Session(eng_TRANS)
    stmnt = delete(WrdR).where(WrdR.id == wrd_r.id)
    # noinspection PyUnusedLocal
    res: CursorResult = session.execute(stmnt)
    session.commit()
    session.close()


def ins_wrd_r(wrd_r: WrdR):
    session = Session(eng_TRANS)
    session.add(wrd_r)
    session.commit()
    session.close()


def sel_wrd_txt_seq(id_: int) -> WrdTxtSeq:
    session = Session(eng_TRANS)
    res: CursorResult = session.execute(select(WrdTxtSeq).where(WrdTxtSeq.id == id_))
    wrd_txt_seq = res.first()
    session.close()
    return wrd_txt_seq.WrdTxtSeq


def fin_wrd_txt_seq(bkey: str = ''):
    session = Session(eng_TRANS)
    stmnt = select(WrdTxtSeq)
    if bkey:
        stmnt = stmnt.where(WrdTxtSeq.bkey == bkey)
    res: CursorResult = session.execute(stmnt)
    wrd_txt_seq_li = res.all()
    session.close()
    return [wrd_txt_seq.WrdTxtSeq for wrd_txt_seq in wrd_txt_seq_li]


def del_wrd_txt_seq(wrd_txt_seq: WrdTxtSeq):
    session = Session(eng_TRANS)
    stmnt = delete(WrdTxtSeq).where(WrdTxtSeq.id == wrd_txt_seq.id)
    # noinspection PyUnusedLocal
    res: CursorResult = session.execute(stmnt)
    session.commit()
    session.close()


def ins_wrd_txt_seq(wrd_txt_seq: WrdTxtSeq):
    session = Session(eng_TRANS)
    session.add(wrd_txt_seq)
    session.commit()
    session.close()

