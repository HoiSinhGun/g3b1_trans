import logging
from typing import Any

from sqlalchemy import Table, select, Column, ForeignKey
from sqlalchemy.engine import Row, CursorResult
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select

import integrity
from entities import *
from g3b1_log.g3b1_log import cfg_logger
from trans.data.model import TstTplate, TstTplateIt, Txtlc, TstTplateItAns, Lc, TxtSeq, TxtSeqIt

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def tst_tplate_from_row(row: Row) -> TstTplate:
    return TstTplate(row['tst_type'], row['bkey'], row['tg_user_id'],
                     Lc.find_lc(row['lc']), Lc.find_lc(row['lc2']),
                     row['descr'], row['id'])


def tst_tplate_it_from_row(row: Row, repl_dct=None) -> TstTplateIt:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateIt(repl_dct['tst_tplate_id'], repl_dct['txt_seq_id'],
                       repl_dct['quest__txtlc_id'], row['itnum'],
                       row['descr'], row['id'])


def tst_tplate_it_ans_from_row(row: Row, repl_dct=None) -> TstTplateItAns:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateItAns(repl_dct['tst_tplate_it_id'], repl_dct['txt_seq_it_id'], repl_dct['txtlc_id'],
                          row['ans_num'], row['id'])


def from_row_txt_seq(row: Row, repl_dct=None) -> TxtSeq:
    if repl_dct is None:
        repl_dct = {}

    return TxtSeq(repl_dct['src__txtlc_id'],
                  row['id'], row['seq_str'])


def from_row_txt_seq_it(row: Row, repl_dct=None) -> TxtSeqIt:
    if repl_dct is None:
        repl_dct = {}

    return TxtSeqIt(repl_dct['txt_seq_id'], repl_dct['trg__txtlc_id'],
                    row['itnum'], row['id'])


def from_row_txtlc(row: Row) -> Txtlc:
    return Txtlc(row['txt'], Lc.find_lc(row['lc']), row['id'])


def pop_only_dc_fields(val_dct: dict[str, ...], tbl: Table) -> dict[str, ...]:
    return {k: v for (k, v) in val_dct.items() if k in tbl.columns.keys()}


def replace_lcs(val_dct: dict[str, ...]) -> dict[str, ...]:
    new_dct: dict = {}

    for k, v in val_dct.items():
        if v and (k == 'lc' or k == 'lc2'):
            new_dct[k] = v.value
        else:
            new_dct[k] = v

    return new_dct


def orm(con: MockConnection, tbl: Table, row: Row, repl_dct=None) -> dict[str, Any]:
    return integrity.orm(con, tbl, row, from_row_any, repl_dct)


def from_row_any(ent_ty: Entity, row: Row) -> Any:
    if ent_ty == ENT_TY_txtlc:
        return from_row_txtlc(row)
    elif ent_ty == ENT_TY_txt_seq:
        return from_row_txt_seq(row)

    return row['id']
