from sqlalchemy import select, delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from trans.data import eng_TRANS
from trans.data.model_orm import Dic


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
    dic2 = session.refresh(dic)
    session.close()

