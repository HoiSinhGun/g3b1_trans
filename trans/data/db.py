import logging
from collections import namedtuple
from dataclasses import asdict
from typing import Any

from sqlalchemy import Table, select, desc, update, delete, and_, or_, asc, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import LegacyCursorResult, Result, Row
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select, ColumnCollection, Update

import g3b1_data.db
import integrity
import trans.data
import utilities
from entities import ENT_TY_txtlc, ENT_TY_txt_seq_it, ENT_TY_txt_seq, ENT_TY_tst_tplate, ENT_TY_tst_tplate_it, \
    ENT_TY_tst_tplate_it_ans
from g3b1_data import settings
from g3b1_data.elements import ELE_TY_chat_id, ELE_TY_tst_tplate_it_id, ELE_TY_tst_tplate_id, Element
from g3b1_data.model import G3Result
from g3b1_log.g3b1_log import cfg_logger
from trans.data import model, MetaData_TRANS, Engine_TRANS, sqlalchemy
from trans.data.model import Txtlc, TxtlcMp, TxtlcOnym, TxtSeq, TxtSeqIt, TstTplate, TstTplateIt, \
    TstTplateItAns, Lc, TstRun, TstRunAct, TstRunActSus
from trans.data.sqlalchemy import pop_only_dc_fields, replace_lcs

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def ins_user_setting_default(user_id: int) -> G3Result:
    setng_dct = model.user_settings(user_id)
    return iup_setting(setng_dct)


def iup_setting(setng_dct: dict[str, ...]) -> G3Result:
    with trans.data.Engine_TRANS.connect() as con:
        settings.iup_setting(con, trans.data.MetaData_TRANS, setng_dct)
        return G3Result()


def read_setting(setng_dct: dict[str, ...], is_fback=False) -> G3Result:
    if is_fback and 'chat_id' in setng_dct.keys():
        read_setting_w_fback(setng_dct)
    with trans.data.Engine_TRANS.connect() as con:
        g3r = settings.read_setting(con, trans.data.MetaData_TRANS, setng_dct)
        return g3r


def read_setting_w_fback(setng_dct: dict[str, ...]) -> G3Result:
    with trans.data.Engine_TRANS.connect() as con:
        g3r = settings.read_setting(con, trans.data.MetaData_TRANS, setng_dct)
        if g3r.retco == 0 or 'chat_id' not in setng_dct.keys() or \
                'user_id' not in setng_dct.keys():
            return g3r
        setng_dct_ = setng_dct
        setng_dct_.pop(ELE_TY_chat_id.id_)
        g3r = settings.read_setting(con, trans.data.MetaData_TRANS, setng_dct_)
        return g3r


def ins_txtlc(txtlc: Txtlc) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc']
        insert_stmnt: insert = insert(tbl).values(
            txt=txtlc.txt, lc=txtlc.lc.value
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        txtlc.id_ = rs.lastrowid
    return G3Result(0, txtlc)


def fiby_txt_lc(txtlc: Txtlc, con: MockConnection = None) -> G3Result[Txtlc]:
    def wrapped(con_: MockConnection, txtlc_: Txtlc, logger_: logging.Logger) -> G3Result:
        tbl: Table = MetaData_TRANS.tables['txtlc']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        if txtlc.id_:
            sql_stmnt = sql_stmnt.where(
                cols.id == txtlc_.id_
            )
        else:
            sql_stmnt = sql_stmnt.where(
                cols.txt == txtlc_.txt, cols.lc == txtlc_.lc.value
            )
        logger.debug(sql_stmnt)
        rs: Result = con_.execute(sql_stmnt)
        res_li: list = rs.fetchall()
        if not res_li or len(res_li) < 1:
            return G3Result(4)
        if len(res_li) > 1:
            logger_.error(f'more than one entry found for {txtlc_}')
        first: Row = res_li[0]
        txtlc_ = sqlalchemy.from_row_any(ENT_TY_txtlc, first)
        return G3Result(0, txtlc_)

    if con:
        return wrapped(con, txtlc, logger)
    with Engine_TRANS.connect() as con:
        return wrapped(con, txtlc, logger)


def ins_onym(txt_onym: TxtlcOnym) -> G3Result:
    """	'id'	INTEGER NOT NULL,
        'lc'	text NOT NULL,
        'src__txtlc_id'	INTEGER NOT NULL,
        'trg__txtlc_id'	INTEGER NOT NULL,
        'onym_ty'	text NOT NULL DEFAULT synonym,
        'creator'	TEXT NOT NULL,
    """
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_onym']
        insert_stmnt: insert = insert(tbl).values(
            lc=txt_onym.txtlc_src.lc.value,
            src__txtlc_id=txt_onym.txtlc_src.id_,
            trg__txtlc_id=txt_onym.txtlc_trg.id_,
            onym_ty=txt_onym.onym_ty,
            creator=txt_onym.creator
        ).on_conflict_do_nothing()
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        txt_onym.id_ = rs.lastrowid
    return G3Result(0, txt_onym)


def del_onym(id_: int) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_onym']
        stmnt: delete = delete(tbl).where(tbl.columns.id == id_)
        con.execute(stmnt)
    return G3Result(0)


def li_onym_by_txtlc(txtlc: Txtlc, src_and_trg: bool = True) -> \
        G3Result[tuple[list[TxtlcOnym]]]:
    def convert_results(g3_res: list[namedtuple]) -> list[TxtlcOnym]:
        res_li: list[TxtlcOnym] = []
        for i in g3_res:
            # noinspection PyTypeChecker,PyArgumentList
            txtlc_src = fiby_txt_lc(Txtlc('', None, i['src__txtlc_id'])).result
            # noinspection PyTypeChecker,PyArgumentList
            txtlc_trg = fiby_txt_lc(Txtlc('', None, i['trg__txtlc_id'])).result
            # noinspection PyArgumentList
            txt_lc_onym = TxtlcOnym(txtlc_src, txtlc_trg, i['creator'], i['onym_ty'], i['id'])
            res_li.append(txt_lc_onym)
        return res_li

    with Engine_TRANS.connect() as con:
        txt_lc = fiby_txt_lc(txtlc, con).result
        g3_res_syn = li_onym_by_txtlc_ty(txt_lc, 'syn', src_and_trg, con)
        g3_res_ant = li_onym_by_txtlc_ty(txt_lc, 'ant', src_and_trg, con)
        syn_li: list[TxtlcOnym] = []
        ant_li: list[TxtlcOnym] = []
        if g3_res_syn.retco == 0:
            syn_li.extend(convert_results(g3_res_syn.result))
        if g3_res_ant.retco == 0:
            ant_li.extend(convert_results(g3_res_ant.result))
        return G3Result(0, (syn_li, ant_li))


def li_onym_by_txtlc_ty(txtlc: Txtlc, onym_ty: str = 'syn', src_and_trg: bool = True,
                        con: MockConnection = None) -> G3Result[list[namedtuple]]:
    """	'id'	INTEGER NOT NULL,
            'lc'	text NOT NULL,
            'src__txtlc_id'	INTEGER NOT NULL,
            'trg__txtlc_id'	INTEGER NOT NULL,
            'onym_ty'	text NOT NULL DEFAULT synonym,
            'creator'	TEXT NOT NULL,
        """

    def wrapped(con_: MockConnection) -> G3Result[list[namedtuple]]:
        tbl: Table = MetaData_TRANS.tables['txtlc_onym']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        where_clause = cols.src__txtlc_id == txtlc.id_
        if src_and_trg:
            where_clause = or_(where_clause, cols.trg__txtlc_id == txtlc.id_)

        sql_stmnt = sql_stmnt.where(
            and_(where_clause, cols.onym_ty == onym_ty, cols.lc == txtlc.lc.value)
        )
        logger.debug(sql_stmnt)
        rs: LegacyCursorResult = con_.execute(sql_stmnt)
        res_li: list[namedtuple] = rs.fetchall()
        if not res_li or len(res_li) < 1:
            return G3Result(4)
        return G3Result(0, res_li)

    if con:
        return wrapped(con)
    with Engine_TRANS.connect() as con:
        return wrapped(con)


def fi_txt_mapping(txtlc: Txtlc, lc2: Lc, translator=None) -> G3Result[TxtlcMp]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_mp']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        if translator:
            sql_stmnt = sql_stmnt.where(
                cols.src__txtlc_id == txtlc.id_, cols.lc2 == lc2.value, cols.translator == translator
            )
        else:
            sql_stmnt = sql_stmnt.where(
                cols.src__txtlc_id == txtlc.id_, cols.lc2 == lc2.value
            ).order_by(desc(cols.score))
        rs: Result = con.execute(sql_stmnt)
        result = rs.first()
        if not result:
            return G3Result(4)
        # noinspection PyTypeChecker
        txtlc_trg = fiby_txt_lc(Txtlc('', None, result['trg__txtlc_id'])).result
        return G3Result(0, TxtlcMp(
            txtlc_src=txtlc, txtlc_trg=txtlc_trg,
            lc2=lc2.value, translator=result[2],
            score=result['score'])
                        )


def upd_txt_mapping(txt_mapping: TxtlcMp) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_mp']
        c = tbl.columns
        stmnt = (update(tbl).
                 where(c['src__txtlc_id'] == txt_mapping.txtlc_src.id_,
                       c['lc2'] == txt_mapping.lc2.value,
                       c['translator'] == txt_mapping.translator).
                 values(dict(trg__txtlc_id=txt_mapping.txtlc_trg.id_,
                             score=txt_mapping.score))
                 )
        rs = con.execute(stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
    return G3Result(0, txt_mapping)


def iup_txt_mapping(txt_mapping: TxtlcMp) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        values = dict(
            src__txtlc_id=txt_mapping.txtlc_src.id_,
            lc2=txt_mapping.lc2.value,
            translator=txt_mapping.translator,
            trg__txtlc_id=txt_mapping.txtlc_trg.id_,
            score=txt_mapping.score
        )
        tbl: Table = MetaData_TRANS.tables['txtlc_mp']
        insert_stmnt: insert = insert(tbl).values(
            values
        ).on_conflict_do_update(
            index_elements=['src__txtlc_id', 'lc2', 'translator'],
            set_=values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)

        return G3Result(0, txt_mapping)


def txtlc_txt_cp(txt: str, lc: Lc, limit: int = 10) -> list[Txtlc]:
    txtlc_li: list[Txtlc] = []
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc']
        # noinspection PyTypeChecker
        c: ColumnCollection = tbl.columns
        sql_stmnt: Select = select(tbl, text('length(txt) AS len_txt'))
        sql_stmnt = sql_stmnt.where(
            (c.txt.like(f'%{txt}%')) & (c.lc == lc.value)
            & text('length(txt) < 100')
        ).order_by(asc(text('len_txt'))).limit(limit)
        rs: Result = con.execute(sql_stmnt)
        logger.debug(sql_stmnt)
        result = rs.fetchall()
        if result:
            for row in result:
                txtlc = sqlalchemy.from_row_any(ENT_TY_txtlc, row)
                txtlc_li.append(txtlc)
        return txtlc_li


def sel_txt_seq(txt_seq_id: int) -> G3Result[TxtSeq]:
    txt_seq: TxtSeq
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables[ENT_TY_txt_seq.tbl_name]
        tbl_it: Table = MetaData_TRANS.tables[ENT_TY_txt_seq_it.tbl_name]
        stmnt = select(tbl).where(tbl.columns['id'] == txt_seq_id)
        rs = con.execute(stmnt)
        row = rs.first()
        if not row:
            return G3Result(4)
        repl_dct = sqlalchemy.orm(con, tbl, row)
        txt_seq: TxtSeq = sqlalchemy.from_row_txt_seq(row, repl_dct)
        # now the items
        stmt = select(tbl_it).where(tbl_it.columns['txt_seq_id'] == txt_seq_id). \
            order_by(asc(tbl_it.columns['itnum']))
        rs = con.execute(stmt)
        rows = rs.fetchall()
        for it_row in rows:
            repl_dct: dict[str, Any] = {'txt_seq_id': txt_seq}
            repl_dct = sqlalchemy.orm(con, tbl_it, it_row, repl_dct)
            txt_seq_it: TxtSeqIt = sqlalchemy.from_row_txt_seq_it(it_row, repl_dct)
            txt_seq.it_li.append(txt_seq_it)
    return G3Result(0, txt_seq)


def sel_txt_seq_by_uq(txt_seq: TxtSeq) -> TxtSeq:
    """By unique txtlc / sec_str"""
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txt_seq']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        sql_stmnt = sql_stmnt.where(
            cols.src__txtlc_id == txt_seq.txtlc_src.id_,
            cols.seq_str == txt_seq.seq_str
        )
        rs: Result = con.execute(sql_stmnt)
        result = rs.first()
        if result:
            txt_seq.id_ = result['id']
        return txt_seq


def ins_seq(txt_seq: TxtSeq) -> G3Result[TxtSeq]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables[ENT_TY_txt_seq.tbl_name]
        tbl_i: Table = MetaData_TRANS.tables[ENT_TY_txt_seq_it.tbl_name]

        values = dict(
            src__txtlc_id=txt_seq.txtlc_src.id_,
            lc=txt_seq.lc.value,
            seq_str=txt_seq.seq_str
        )
        insert_stmnt: insert = insert(tbl).values(
            values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        rowid = rs.lastrowid
        txt_seq_id = 0
        if rowid:
            rs = con.execute(f"SELECT ROWID, * FROM {tbl.name} WHERE ROWID=:rowid", rowid=rowid)
            txt_seq_id = int(rs.first()['id'])
        txt_seq.id_ = txt_seq_id
        for i in txt_seq.it_li:
            values = dict(
                txt_seq_id=txt_seq.id_,
                trg__txtlc_id=i.txtlc_trg.id_,
                itnum=i.itnum
            )
            insert_stmnt: insert = insert(tbl_i).values(
                values
            )
            # noinspection PyUnusedLocal
            rs = con.execute(insert_stmnt)
        return G3Result(0, txt_seq)


def sel_tst_tplate(tst_tplate_id: int) -> G3Result[TstTplate]:
    tst_tplate: TstTplate
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_tplate']
        stmnt = select(tbl).where(tbl.columns['id'] == int(tst_tplate_id))
        rs = con.execute(stmnt)
        logger.debug(stmnt)
        row = rs.first()
        if not row:
            return G3Result(4)

        tst_tplate = sqlalchemy.from_row_tst_tplate(row)
        tbl_it: Table = MetaData_TRANS.tables['tst_tplate_it']
        stmnt = select(tbl_it).where(tbl_it.columns['tst_tplate_id'] == tst_tplate_id). \
            order_by(asc(tbl_it.columns['itnum']))
        rs = con.execute(stmnt)
        rows_it = rs.fetchall()

        for row_it in rows_it:
            repl_dct: dict[str, Any] = {'tst_tplate_id': tst_tplate}
            repl_dct = sqlalchemy.orm(con, tbl_it, row_it, repl_dct)
            tst_tplate_it: TstTplateIt = sqlalchemy.from_row_tst_tplate_it(row_it, repl_dct)
            tst_tplate.it_li.append(tst_tplate_it)

            # Now the answers
            tbl_it_ans: Table = MetaData_TRANS.tables['tst_tplate_it_ans']
            stmnt = select(tbl_it_ans).where(tbl_it_ans.columns['tst_tplate_it_id'] == tst_tplate_it.id_). \
                order_by(asc(tbl_it_ans.columns['ans_num']))
            rs = con.execute(stmnt)
            rows_it_it = rs.fetchall()
            for row_it_it in rows_it_it:
                repl_dct: dict[str, Any] = {'tst_tplate_it_id': tst_tplate_it}
                repl_dct = sqlalchemy.orm(con, tbl_it_ans, row_it_it, repl_dct)
                tst_tplate_it_ans: TstTplateItAns = \
                    sqlalchemy.from_row_tst_tplate_it_ans(row_it_it, repl_dct)
                tst_tplate_it.ans_li.append(tst_tplate_it_ans)

        return G3Result(0, tst_tplate)


def sel_tst_tplate__bk(bkey: str) -> G3Result[TstTplate]:
    tst_tplate: TstTplate
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_tplate']
        stmnt = select(tbl).where(tbl.columns['bkey'] == bkey)
        rs = con.execute(stmnt)
        row: Row = rs.first()
        if not row:
            return G3Result(4)
        tst_tplate = sqlalchemy.from_row_tst_tplate(row)
        return sel_tst_tplate(tst_tplate.id_)


def sel_tst_tplate_by_item_id(item_id: int) -> G3Result[TstTplate]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_i: Table = MetaData_TRANS.tables['tst_tplate_it']
        stmnt = select(tbl_i.columns.tst_tplate_id).where(tbl_i.columns['id'] == item_id)
        rs: LegacyCursorResult = con.execute(stmnt)
        tst_tplate_id = int(rs.first()[0])
        g3r = sel_tst_tplate(tst_tplate_id)
        if g3r.retco == 0:
            return g3r
        else:
            return G3Result(4)


def ins_tst_tplate_item(tst_tplate: TstTplate, i: TstTplateIt) -> \
        G3Result[tuple[TstTplate, TstTplateIt]]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_i: Table = MetaData_TRANS.tables['tst_tplate_it']
        txt_seq_id = i.txt_seq.id_ if i.txt_seq else None
        txtlc_id = i.txtlc_qt.id_ if i.txtlc_qt else None
        values = dict(
            tst_tplate_id=tst_tplate.id_,
            txt_seq_id=txt_seq_id,
            quest__txtlc_id=txtlc_id,
            itnum=i.itnum
        )
        insert_stmnt: insert = insert(tbl_i).values(
            values
        )
        rs = con.execute(insert_stmnt)
        i.id_ = g3b1_data.db.fetch_id(con, rs, tbl_i.name)
        if i.id_ is None:
            return G3Result(4)
        tst_tplate.repl_or_app_item(i)
        return G3Result(0, (tst_tplate, i))


def ins_tst_tplate(tst_template: TstTplate) -> G3Result[TstTplate]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_tplate']
        tbl_i: Table = MetaData_TRANS.tables['tst_tplate_it']
        val_dct = asdict(tst_template)
        values = replace_lcs(pop_only_dc_fields(val_dct, tbl))
        insert_stmnt: insert = insert(tbl).values(
            values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        rowid = rs.lastrowid
        tst_tplate_id = 0
        if rowid:
            rs = con.execute(f"SELECT ROWID, * FROM {tbl.name} WHERE ROWID=:rowid", rowid=rowid)
            tst_tplate_id = int(rs.first()['id'])
        tst_template.id_ = tst_tplate_id
        for i in tst_template.it_li:
            txt_seq_id = i.txt_seq.id_ if i.txt_seq else None
            txtlc_id = i.txtlc_qt.id_ if i.txtlc_qt else None
            values = dict(
                tst_tplate_id=tst_template.id_,
                txt_seq_id=txt_seq_id,
                quest__txtlc_id=txtlc_id,
                itnum=i.itnum
            )
            insert_stmnt: insert = insert(tbl_i).values(
                values
            )
            con.execute(insert_stmnt)
        return G3Result(0, tst_template)


def iup_tst_tplate_it_ans(it: TstTplateIt, ans: TstTplateItAns) -> \
        G3Result[tuple[TstTplateIt, TstTplateItAns]]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_a: Table = MetaData_TRANS.tables['tst_tplate_it_ans']
        seq_it_id: int = ans.txt_seq_it.id_ if ans.txt_seq_it else None
        txtlc_id: int = ans.txtlc.id_ if ans.txtlc else None
        values = dict(
            tst_tplate_it_id=it.id_,
            txt_seq_it_id=seq_it_id,
            txtlc_id=txtlc_id,
            ans_num=ans.ans_num
        )
        insert_stmnt: insert = insert(tbl_a).values(
            values
        ).on_conflict_do_update(
            index_elements=['tst_tplate_it_id', 'ans_num'],
            set_=values
        )
        rs = con.execute(insert_stmnt)
        ans.id_ = g3b1_data.db.fetch_id(con, rs, tbl_a.name)
        if ans.id_ is None:
            return G3Result(4)
        return G3Result(0, (it, ans))


def upd_tst_template_lc_pair(tst_tplate_id: int, lc_tup: tuple[Lc, Lc]) -> \
        G3Result[None]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_tplate']
        c = tbl.columns
        stmnt = (update(tbl).
                 where(c['id'] == tst_tplate_id).
                 values(dict(lc=lc_tup[0].value,
                             lc2=lc_tup[1].value)
                        )
                 )
        rs = con.execute(stmnt)

        if rs.rowcount != 1:
            return G3Result(4)
    return G3Result(0, None)


def tst_tplate_refs(tst_tplate: TstTplate, con_: MockConnection = None) -> list[dict[str, ...]]:
    def core_tst_tplate_refs(con: MockConnection) -> list[dict[str, ...]]:
        tbl: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate.tbl_name]
        tbl_it: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate_it.tbl_name]
        # tbl_it_ans: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate_it_ans.tbl_name]
        # ans_id_li = [it_ans.id_ for it in tst_tplate.it_li for it_ans in it.ans_li ]
        all_refs: list[dict[str, ...]] = []
        it_id_li = [it.id_ for it in tst_tplate.it_li]
        for id_ in it_id_li:
            ref_li = settings.sel_cu_setng_ref_li(con, MetaData_TRANS, ELE_TY_tst_tplate_it_id, id_)
            all_refs.extend(ref_li)
        ref_li = settings.sel_cu_setng_ref_li(con, MetaData_TRANS, ELE_TY_tst_tplate_id, tst_tplate.id_)
        all_refs.extend(ref_li)
        return all_refs

    if con_:
        return core_tst_tplate_refs(con_)
    else:
        with Engine_TRANS.connect() as con_:
            return core_tst_tplate_refs(con_)


def tst_tplate_del(tst_tplate: TstTplate) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate.tbl_name]
        tbl_it: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate_it.tbl_name]
        tbl_it_ans: Table = MetaData_TRANS.tables[ENT_TY_tst_tplate_it_ans.tbl_name]

        # References from settings table
        tbl_li: list[Table] = integrity.ref_cascade(tst_tplate)
        tbl_ref_li = [i for i in tbl_li if i not in [tbl, tbl_it, tbl_it_ans]]
        if tbl_ref_li:
            return G3Result(4)

        # ans_id_li = [it_ans.id_ for it in tst_tplate.it_li for it_ans in it.ans_li]
        # if ans_id_li:
        #     stmnt: delete = delete(tbl_it_ans).where(tbl_it_ans.columns.id.in_(ans_id_li))
        #     con.execute(stmnt)
        #
        # it_id_li = [it.id_ for it in tst_tplate.it_li]
        # if it_id_li:
        #     stmnt: delete = delete(tbl_it).where(tbl_it.columns.id.in_(it_id_li))
        #     con.execute(stmnt)

        stmnt: delete = delete(tbl).where(tbl.columns.id.in_([tst_tplate.id_]))
        con.execute(stmnt)

    return G3Result(0, None)


def ins_tst_run(tst_run: TstRun) -> G3Result[TstRun]:
    """Ins tst_run"""
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_run']
        values = {
            'tst_tplate_id': tst_run.tst_tplate.id_,
            'tg_chat_id': tst_run.chat_id,
            'tg_user_id': tst_run.user_id
        }
        insert_stmnt: insert = insert(tbl).values(
            values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        rowid = rs.lastrowid
        id_ = 0
        if rowid:
            rs = con.execute(f"SELECT ROWID, * FROM {tbl.name} WHERE ROWID=:rowid", rowid=rowid)
            id_ = int(rs.first()['id'])
        tst_run.id_ = id_
    return G3Result(0, tst_run)


def ins_tst_run_act(tst_run: TstRun, con_: MockConnection = None) -> G3Result[TstRun]:
    """Ins 1 ...act and n ...act_sus"""
    if not (tst_run_act := tst_run.act_last()):
        return G3Result(4)

    def wrapped(con: MockConnection) -> G3Result[TstRun]:
        tbl: Table = MetaData_TRANS.tables['tst_run_act']
        val_dct = {'act_ty': tst_run_act.act_ty.value, 'txt': tst_run_act.txt, 'tst_run_id': tst_run.id_}
        if tst_run_act.tst_tplate_it_ans:
            val_dct['tst_tplate_it_ans_id'] = tst_run_act.tst_tplate_it_ans.id_
        insert_stmnt: insert = insert(tbl).values(
            val_dct
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        rowid = rs.lastrowid
        id_ = 0
        if rowid:
            rs = con.execute(f"SELECT ROWID, * FROM {tbl.name} WHERE ROWID=:rowid", rowid=rowid)
            id_ = int(rs.first()['id'])
        tst_run_act.id_ = id_

        tbl_it: Table = MetaData_TRANS.tables['tst_run_act_sus']
        for it_row in tst_run_act.it_li:
            it_val_dct = {'tst_run_act_id': tst_run_act.id_,
                          'tst_tplate_it_ans_id': tst_run_act.tst_tplate_it_ans.id_,
                          'sus_bkey': it_row.sus.value}
            stmnt: insert = insert(tbl_it).values(
                it_val_dct
            )
            rs = con.execute(stmnt)
            if rs.rowcount != 1:
                return G3Result(4)
            rowid = rs.lastrowid
            id_ = 0
            if rowid:
                rs = con.execute(f"SELECT ROWID, * FROM {tbl_it.name} WHERE ROWID=:rowid", rowid=rowid)
                id_ = int(rs.first()['id'])
            it_row.id_ = id_

        return G3Result(0, tst_run)

    if con_:
        return wrapped(con_)
    else:
        with Engine_TRANS.connect() as con_:
            return wrapped(con_)


def upd_tst_run__end(tst_run: TstRun) -> G3Result[TstRun]:
    """Set end_tst and ins 1 ...act and n ...act_sus"""
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_run']
        tst_run.end_tst = utilities.tst_for_sql()
        values = {'end_tst': tst_run.end_tst}
        c = tbl.columns
        stmnt: Update = (update(tbl).
                         where(c.id == tst_run.id_).
                         values(values)
                        )
        rs = con.execute(stmnt)
        if rs.rowcount != 1:
            return G3Result(4)

        return ins_tst_run_act(tst_run, con)


def sel_tst_run(id_: int) -> G3Result[TstRun]:
    """Sel tst_run"""
    ent: TstRun
    ent_ty = TstRun.ent_ty()
    tbl_name = ent_ty.tbl_name
    element = Element.by_ent_ty(ent_ty)
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables[tbl_name]
        stmnt = select(tbl).where(tbl.columns['id'] == id_)
        rs = con.execute(stmnt)
        logger.debug(stmnt)
        row = rs.first()
        if not row:
            return G3Result(4)
        repl_dct: dict[str, Any] = {}
        repl_dct = sqlalchemy.orm(con, tbl, row, repl_dct)
        ent = sqlalchemy.from_row_tst_run(row, repl_dct)

        # items
        # 1st level
        tbl_it: Table = MetaData_TRANS.tables['tst_run_act']
        stmnt = select(tbl_it).where(tbl_it.columns[element.id_] == ent.id_). \
            order_by(asc(tbl_it.columns['act_tst']))
        rs = con.execute(stmnt)
        rows_it = rs.fetchall()
        # orm
        for row_it in rows_it:
            repl_dct: dict[str, Any] = {element.id_: ent}
            repl_dct = sqlalchemy.orm(con, tbl_it, row_it, repl_dct)
            ent_it: TstRunAct = sqlalchemy.from_row_tst_run_act(row_it, repl_dct)
            ent.it_li.append(ent_it)

            # items
            # 2nd level
            ent_it_ty = ent_it.ent_ty()
            element_it = Element.by_ent_ty(ent_it_ty)
            tbl_it_it: Table = MetaData_TRANS.tables['tst_run_act_sus']
            stmnt = select(tbl_it_it).where(tbl_it_it.columns[element_it.id_] == ent_it.id_)
            rs = con.execute(stmnt)
            rows_it_it = rs.fetchall()
            # orm
            for row_it_it in rows_it_it:
                repl_dct: dict[str, Any] = {element_it.id_: ent_it}
                repl_dct = sqlalchemy.orm(con, tbl_it_it, row_it_it, repl_dct)
                ent_it_it: TstRunActSus = \
                    sqlalchemy.from_row_tst_run_act_sus(row_it_it, repl_dct)
                ent_it.it_li.append(ent_it_it)
        return G3Result(0, ent)

