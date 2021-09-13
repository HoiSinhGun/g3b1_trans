import logging
from typing import Any

from sqlalchemy.engine import Row
from sqlalchemy.engine.mock import MockConnection

import integrity
from entities import *
from g3b1_log.g3b1_log import cfg_logger
from trans.data.enums import ActTy, Sus
from trans.data.model import TstTplate, TstTplateIt, Txtlc, TstTplateItAns, Lc, TxtSeq, TxtSeqIt, TstRun, TstRunAct, \
    TstRunActSus

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def from_row_tst_tplate(row: Row) -> TstTplate:
    return TstTplate(row['tst_type'], row['bkey'], row['tg_user_id'],
                     Lc.find_lc(row['lc']), Lc.find_lc(row['lc2']),
                     row['descr'], row['id'])


def from_row_tst_tplate_it(row: Row, repl_dct=None) -> TstTplateIt:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateIt(repl_dct['tst_tplate_id'], repl_dct['txt_seq_id'],
                       repl_dct['quest__txtlc_id'], row['itnum'],
                       row['descr'], row['id'])


def from_row_tst_tplate_it_ans(row: Row, repl_dct=None) -> TstTplateItAns:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateItAns(repl_dct['tst_tplate_it_id'], repl_dct['txt_seq_it_id'], repl_dct['txtlc_id'],
                          row['ans_num'], row['id'])


def from_row_tst_run(row: Row, repl_dct=None) -> TstRun:
    if repl_dct is None:
        repl_dct = {}

    return TstRun(repl_dct['tst_tplate_id'],
                  row['tg_chat_id'], row['tg_user_id'],
                  row['sta_tst'], row['end_tst'], row['id'])


def from_row_tst_run_act(row: Row, repl_dct=None) -> TstRunAct:
    if repl_dct is None:
        repl_dct = {}

    return TstRunAct(repl_dct['tst_run_id'], repl_dct['tst_tplate_it_ans_id'],
                     ActTy.by_val(row['act_ty']), row['act_tst'], row['txt'],
                     row['id'])


def from_row_tst_run_act_sus(row: Row, repl_dct=None) -> TstRunActSus:
    if repl_dct is None:
        repl_dct = {}

    return TstRunActSus(repl_dct['tst_run_act_id'],
                        Sus.by_val(row['sus_bkey']),
                        repl_dct['tst_tplate_it_ans_id'],
                        row['id'])


def from_row_txt_seq(row: Row, repl_dct=None) -> TxtSeq:
    if repl_dct is None:
        repl_dct = {}

    return TxtSeq(repl_dct['src__txtlc_id'],
                  row['id'], row['seq_str'])


def from_row_txt_seq_it(row: Row, repl_dct=None) -> TxtSeqIt:
    if repl_dct is None:
        repl_dct = {}

    # noinspection PyArgumentList
    return TxtSeqIt(repl_dct['txt_seq_id'], repl_dct['trg__txtlc_id'],
                    row['itnum'], row['id'])


def from_row_txtlc(row: Row) -> Txtlc:
    # noinspection PyArgumentList
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


def from_row_any(ent_ty: EntTy, row: Row) -> Any:
    if ent_ty == ENT_TY_txtlc:
        return from_row_txtlc(row)
    elif ent_ty == ENT_TY_txt_seq:
        return from_row_txt_seq(row)
    elif ent_ty == ENT_TY_tst_tplate:
        return from_row_tst_tplate(row)
    elif ent_ty == ENT_TY_tst_run:
        return from_row_tst_run(row)
    elif ent_ty == ENT_TY_tst_run_act:
        return from_row_tst_run_act(row)
    elif ent_ty == ENT_TY_tst_run_act_sus:
        return from_row_tst_run_act_sus(row)

    return row['id']
