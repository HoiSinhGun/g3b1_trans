import logging
from collections import namedtuple
from dataclasses import asdict

from sqlalchemy import Table, select, desc, update, delete, and_, or_, asc
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import LegacyCursorResult, Result, Row
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select

import g3b1_data.db
import trans.data
from g3b1_data import settings
from g3b1_data.elements import ELE_TYP_chat_id
from g3b1_data.model import G3Result
from g3b1_log.g3b1_log import cfg_logger
from trans.data import model, MetaData_TRANS, Engine_TRANS, sqlalchemy
from trans.data.model import TxtLC, TxtLCMapping, TxtLCOnym, TxtSeq, TxtSeqItem, TstTemplate, TstTemplateIt, \
    TstTemplateItAns

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
        setng_dct_.pop(ELE_TYP_chat_id['id'])
        g3r = settings.read_setting(con, trans.data.MetaData_TRANS, setng_dct_)
        return g3r


def ins_txtlc(txtlc: TxtLC) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc']
        insert_stmnt: insert = insert(tbl).values(
            txt=txtlc.txt, lc=txtlc.lc
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        txtlc.id_ = rs.lastrowid
    return G3Result(0, txtlc)


def fiby_txt_lc(txtlc: TxtLC, con: MockConnection = None) -> G3Result[TxtLC]:
    def wrapped(con_: MockConnection, txtlc_: TxtLC, logger_: logging.Logger) -> G3Result:
        tbl: Table = MetaData_TRANS.tables['txtlc']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        if txtlc.id_:
            sql_stmnt = sql_stmnt.where(
                cols.id == txtlc_.id_
            )
        else:
            sql_stmnt = sql_stmnt.where(
                cols.txt == txtlc_.txt, cols.lc == txtlc_.lc
            )
        logger.debug(sql_stmnt)
        rs: LegacyCursorResult = con_.execute(sql_stmnt)
        res_li: list = rs.fetchall()
        if not res_li or len(res_li) < 1:
            return G3Result(4)
        if len(res_li) > 1:
            logger_.error(f'more than one entry found for {txtlc_}')
        first: tuple = res_li[0]
        txtlc_ = TxtLC(first[1], first[2], first[0])
        return G3Result(0, txtlc_)

    if con:
        return wrapped(con, txtlc, logger)
    with Engine_TRANS.connect() as con:
        return wrapped(con, txtlc, logger)


def ins_onym(txt_onym: TxtLCOnym) -> G3Result:
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
            lc=txt_onym.txtlc_src.lc,
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


def li_onym_by_txtlc(txtlc: TxtLC, src_and_trg: bool = True) -> \
        G3Result[tuple[list[TxtLCOnym]]]:
    def convert_results(g3_res: list[namedtuple]) -> list[TxtLCOnym]:
        res_li: list[TxtLCOnym] = []
        for i in g3_res:
            txtlc_src = fiby_txt_lc(TxtLC('', '', i['src__txtlc_id'])).result
            txtlc_trg = fiby_txt_lc(TxtLC('', '', i['trg__txtlc_id'])).result
            txt_lc_onym = TxtLCOnym(txtlc_src, txtlc_trg, i['creator'], i['onym_ty'], i['id'])
            res_li.append(txt_lc_onym)
        return res_li

    with Engine_TRANS.connect() as con:
        txt_lc = fiby_txt_lc(txtlc, con).result
        g3_res_syn = li_onym_by_txtlc_ty(txt_lc, 'syn', src_and_trg, con)
        g3_res_ant = li_onym_by_txtlc_ty(txt_lc, 'ant', src_and_trg, con)
        syn_li: list[TxtLCOnym] = []
        ant_li: list[TxtLCOnym] = []
        if g3_res_syn.retco == 0:
            syn_li.extend(convert_results(g3_res_syn.result))
        if g3_res_ant.retco == 0:
            ant_li.extend(convert_results(g3_res_ant.result))
        return G3Result(0, (syn_li, ant_li))


def li_onym_by_txtlc_ty(txtlc: TxtLC, onym_ty: str = 'syn', src_and_trg: bool = True,
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
            and_(where_clause, cols.onym_ty == onym_ty, cols.lc == txtlc.lc)
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


def fi_txt_mapping(txtlc: TxtLC, lc_2: str, translator=None) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_lc2']
        cols = tbl.columns
        sql_stmnt: Select = select(tbl)
        if translator:
            sql_stmnt = sql_stmnt.where(
                cols.src__txtlc_id == txtlc.id_, cols.lc_2 == lc_2, cols.translator == translator
            )
        else:
            sql_stmnt = sql_stmnt.where(
                cols.src__txtlc_id == txtlc.id_, cols.lc_2 == lc_2
            ).order_by(desc(cols.score))
        rs: Result = con.execute(sql_stmnt)
        result = rs.first()
        if not result:
            return G3Result(4)
        txtlc_trg = fiby_txt_lc(TxtLC('', '', result['trg__txtlc_id'])).result
        return G3Result(0, TxtLCMapping(
            txtlc_src=txtlc, txtlc_trg=txtlc_trg,
            lc_2=lc_2, translator=result[2],
            score=result['score'])
                        )


def upd_txt_mapping(txt_mapping: TxtLCMapping) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txtlc_lc2']
        c = tbl.columns
        stmnt = (update(tbl).
                 where(c['src__txtlc_id'] == txt_mapping.txtlc_src.id_,
                       c['lc_2'] == txt_mapping.lc_2,
                       c['translator'] == txt_mapping.translator).
                 values(dict(trg__txtlc_id=txt_mapping.txtlc_trg.id_,
                             score=txt_mapping.score))
                 )
        rs = con.execute(stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
    return G3Result(0, txt_mapping)


def ins_upd_txt_mapping(txt_mapping: TxtLCMapping) -> G3Result:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        values = dict(
            src__txtlc_id=txt_mapping.txtlc_src.id_,
            lc_2=txt_mapping.lc_2.upper(),
            translator=txt_mapping.translator,
            trg__txtlc_id=txt_mapping.txtlc_trg.id_,
            score=txt_mapping.score
        )
        tbl: Table = MetaData_TRANS.tables['txtlc_lc2']
        insert_stmnt: insert = insert(tbl).values(
            values
        ).on_conflict_do_update(
            index_elements=['src__txtlc_id', 'lc_2', 'translator'],
            set_=values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)

        return G3Result(0, txt_mapping)


def find_seq(txt_seq: TxtSeq) -> TxtSeq:
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
        tbl: Table = MetaData_TRANS.tables['txt_seq']
        tbl_i: Table = MetaData_TRANS.tables['txt_seq_item']

        values = dict(
            src__txtlc_id=txt_seq.txtlc_src.id_,
            lc=txt_seq.lc.upper(),
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
        for i in txt_seq.item_li:
            values = dict(
                txt_seq_id=txt_seq.id_,
                trg__txtlc_id=i.txtlc_trg.id_,
                itnum=i.itnum
            )
            insert_stmnt: insert = insert(tbl_i).values(
                values
            )
            rs = con.execute(insert_stmnt)
        return G3Result(0, txt_seq)


def get_txt_seq(txt_seq_id: int) -> G3Result[TxtSeq]:
    txt_seq: TxtSeq
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['txt_seq']
        tbl_i: Table = MetaData_TRANS.tables['txt_seq_item']
        stmnt = select(tbl).where(tbl.columns['id'] == txt_seq_id)
        rs = con.execute(stmnt)
        row = rs.first()
        if not row:
            return G3Result(4)
        txtlc_src = fiby_txt_lc(TxtLC('', '', row['src__txtlc_id']), con).result
        txt_seq = TxtSeq(txtlc_src)
        txt_seq.id_ = row['id']
        txt_seq.lc = row['lc']
        txt_seq.seq_str = row['seq_str']
        txt_seq.item_li = []
        stmt = select(tbl_i).where(tbl_i.columns['txt_seq_id'] == txt_seq_id). \
            order_by(asc(tbl_i.columns['itnum']))
        rs = con.execute(stmt)
        rows = rs.fetchall()
        for row in rows:
            txtlc_trg = fiby_txt_lc(TxtLC('', '', row['trg__txtlc_id']), con).result
            txt_seq.item_li.append(TxtSeqItem(txtlc_trg, row['itnum']))
    return G3Result(0, txt_seq)


def sel_tst_tplate_by_bk(bkey: str) -> G3Result[TstTemplate]:
    tst_tplate: TstTemplate
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_template']
        stmnt = select(tbl).where(tbl.columns['bkey'] == bkey)
        rs = con.execute(stmnt)
        row: Row = rs.first()
        if not row:
            return G3Result(4)
        tst_tplate = sqlalchemy.tst_template_from_row(row)
        return sel_tst_tplate_by_id(tst_tplate.id_)


def sel_tst_tplate_by_item_id(item_id: int) -> G3Result[TstTemplate]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_i: Table = MetaData_TRANS.tables['tst_template_it']
        stmnt = select(tbl_i.columns.tst_template_id).where(tbl_i.columns['id'] == item_id)
        rs: LegacyCursorResult = con.execute(stmnt)
        tst_tplate_id = int(rs.first()[0])
        g3r = sel_tst_tplate_by_id(tst_tplate_id)
        if g3r.retco == 0:
            return g3r
        else:
            return G3Result(4)


def sel_tst_tplate_by_id(tst_tplate_id: int) -> G3Result[TstTemplate]:
    tst_tplate: TstTemplate
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_template']
        stmnt = select(tbl).where(tbl.columns['id'] == int(tst_tplate_id))
        rs = con.execute(stmnt)
        logger.debug(stmnt)
        row = rs.first()
        if not row:
            return G3Result(4)
        tst_tplate = sqlalchemy.tst_template_from_row(row)
        tbl_it: Table = MetaData_TRANS.tables['tst_template_it']
        stmnt = select(tbl_it).where(tbl_it.columns['tst_template_id'] == tst_tplate_id).\
            order_by(asc(tbl_it.columns['itnum']))
        rs = con.execute(stmnt)
        rows = rs.fetchall()
        for row in rows:
            quest_txtlc = fiby_txt_lc(TxtLC('', '', row['quest__txtlc_id'])).result
            answer_txtlc = fiby_txt_lc(TxtLC('', '', row['answer__txtlc_id'])).result
            item = TstTemplateIt(tst_tplate, quest_txtlc, row['itnum'], answer_txtlc, row['id'])
            tst_tplate.item_li.append(item)
        return G3Result(0, tst_tplate)


def ins_tst_tplate_item(tst_tplate: TstTemplate, i: TstTemplateIt) -> \
        G3Result[tuple[TstTemplate, TstTemplateIt]]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_i: Table = MetaData_TRANS.tables['tst_template_it']
        values = dict(
            tst_template_id=tst_tplate.id_,
            quest__txtlc_id=i.txtlc_qt.id_,
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


def ins_tst_tplate(tst_template: TstTemplate) -> G3Result[TstTemplate]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl: Table = MetaData_TRANS.tables['tst_template']
        tbl_i: Table = MetaData_TRANS.tables['tst_template_it']
        values = asdict(tst_template)
        insert_stmnt: insert = insert(tbl).values(
            values
        )
        rs = con.execute(insert_stmnt)
        if rs.rowcount != 1:
            return G3Result(4)
        rowid = rs.lastrowid
        tst_template_id = 0
        if rowid:
            rs = con.execute(f"SELECT ROWID, * FROM {tbl.name} WHERE ROWID=:rowid", rowid=rowid)
            tst_template_id = int(rs.first()['id'])
        tst_template.id_ = tst_template_id
        for i in tst_template.item_li:
            values = dict(
                tst_template_id=tst_template.id_,
                quest__txtlc_id=i.txtlc_qt.id_,
                itnum=i.itnum
            )
            insert_stmnt: insert = insert(tbl_i).values(
                values
            )
            con.execute(insert_stmnt)
        return G3Result(0, tst_template)


def iup_tst_tplate_item_ans(it: TstTemplateIt, ans: TstTemplateItAns) -> \
        G3Result[tuple[TstTemplateIt, TstTemplateItAns]]:
    con: MockConnection
    with Engine_TRANS.connect() as con:
        tbl_a: Table = MetaData_TRANS.tables['tst_template_it_ans']
        values = dict(
            tst_template_it_id=it.id_,
            txtlc_id=ans.txtlc.id_,
            ans_num=ans.ans_num
        )
        insert_stmnt: insert = insert(tbl_a).values(
            values
        ).on_conflict_do_update(
            index_elements=['tst_template_it_id', 'ans_num'],
            set_=values
        )
        rs = con.execute(insert_stmnt)
        ans.id_ = g3b1_data.db.fetch_id(con, rs, tbl_a.name)
        if ans.id_ is None:
            return G3Result(4)
        return G3Result(0, (it, ans))
