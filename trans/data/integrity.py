import logging

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Row

import integrity
from entities import *
from g3b1_log.log import cfg_logger
from trans.data import ELE_TY_txt_seq_id, ELE_TY_txt_seq_it_id, ELE_TY_txtlc_mp_id, ELE_TY_vocry_id, ENT_TY_vocry, \
    ENT_TY_vocry_it, ENT_TY_learned, ENT_TY_vocry_mp_it, ENT_TY_txtlc_file
from trans.data import ENT_TY_txtlc, ENT_TY_txtlc_mp, ENT_TY_txt_seq, ENT_TY_tst_tplate, ENT_TY_tst_run, \
    ENT_TY_tst_run_act, \
    ENT_TY_tst_run_act_sus, ENT_TY_story, ENT_TY_story_it, ENT_TY_txt_seq_aud
from trans.data.enums import ActTy, Sus
from trans.data.model import TstTplate, TstTplateIt, Txtlc, TstTplateItAns, Lc, TxtSeq, TxtSeqIt, TstRun, TstRunAct, \
    TstRunActSus, TxtlcMp, Vocry, VocryIt, Learned, VocryMpIt, TxtSeqAud, Story, StoryIt, TxtlcFile

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def from_row_tst_tplate(row: Row) -> TstTplate:
    return TstTplate(row['tst_type'], row['bkey'], row['tg_user_id'],
                     Lc.fin(row['lc']), Lc.fin(row['lc2']),
                     row['descr'], row['id'])


def from_row_tst_tplate_it(row: Row, repl_dct=None) -> TstTplateIt:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateIt(repl_dct['tst_tplate_id'], repl_dct[ELE_TY_txt_seq_id.col_name],
                       repl_dct['quest__txtlc_id'], row['itnum'],
                       row['descr'], row['id'])


def from_row_tst_tplate_it_ans(row: Row, repl_dct=None) -> TstTplateItAns:
    if repl_dct is None:
        repl_dct = {}

    return TstTplateItAns(repl_dct['tst_tplate_it_id'], repl_dct[ELE_TY_txt_seq_it_id.col_name], repl_dct['txtlc_id'],
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
                     ActTy.fin(row['act_ty']), row['act_tst'], row['txt'],
                     row['id'])


def from_row_tst_run_act_sus(row: Row, repl_dct=None) -> TstRunActSus:
    if repl_dct is None:
        repl_dct = {}

    return TstRunActSus(repl_dct['tst_run_act_id'],
                        Sus.fin(row['sus_bkey']),
                        repl_dct['tst_tplate_it_ans_id'],
                        row['id'])


def from_row_txt_seq(row: Row, repl_dct=None) -> TxtSeq:
    if row is None:
        # noinspection PyTypeChecker
        return None

    if repl_dct is None:
        repl_dct = {}

    return TxtSeq(row['chat_id'], row['txt'], Lc.fin(row['lc']), Lc.fin(row['lc2']),
                  repl_dct.get(ELE_TY_txtlc_mp_id.col_name, row[ELE_TY_txtlc_mp_id.col_name]), row['id'])


def from_row_txt_seq_it(row: Row, repl_dct=None) -> TxtSeqIt:
    if repl_dct is None:
        repl_dct = {}

    return TxtSeqIt(repl_dct.get(ELE_TY_txt_seq_id.col_name, row[ELE_TY_txt_seq_id.col_name]),
                    repl_dct.get(ELE_TY_txtlc_mp_id.col_name, row[ELE_TY_txtlc_mp_id.col_name]),
                    row['rowno'], row['id'])


def from_row_vocry(row: Row) -> Vocry:
    if row is None:
        # noinspection PyTypeChecker
        return None

    return Vocry(row=row)


def from_row_vocry_it(row: Row, repl_dct=None) -> VocryIt:
    if repl_dct is None:
        repl_dct = {}

    return VocryIt(repl_dct.get(ELE_TY_vocry_id.col_name, row[ELE_TY_vocry_id.col_name]),
                   repl_dct.get(ELE_TY_txt_seq_id.col_name, row[ELE_TY_txt_seq_id.col_name]),
                   row['rowno'], row['id'])


def from_row_story(row: Row) -> Story:
    if row is None:
        # noinspection PyTypeChecker
        return None

    return Story(row=row)


def from_row_story_it(row: Row, repl_dct=None) -> StoryIt:
    if repl_dct is None:
        repl_dct = {}

    return StoryIt(row=row, repl_dct=repl_dct)


def from_row_vocry_mp_it(row: Row, repl_dct=None) -> VocryMpIt:
    if repl_dct is None:
        repl_dct = {}

    return VocryMpIt(repl_dct.get(ELE_TY_vocry_id.col_name, row[ELE_TY_vocry_id.col_name]),
                     repl_dct.get(ELE_TY_txtlc_mp_id.col_name, row[ELE_TY_txtlc_mp_id.col_name]),
                     row['id'])


def from_row_learned(row: Row, repl_dct=None) -> Learned:
    if repl_dct is None:
        repl_dct = {}

    return Learned(row['user_id'],
                   repl_dct.get('txtlc_id', row['txtlc_id']),
                   row['ins_tst'], row['id'])


def from_row_txtlc(row: Row) -> Txtlc:
    return Txtlc(row['txt'], Lc.fin(row['lc']), s_review=row['s_review'], id_=row['id'])


def from_row_txtlc_file(row:Row, repl_dct: dict[str, Any] = None) -> TxtlcFile:
    if repl_dct is None:
        repl_dct = {}

    return TxtlcFile(row=row, repl_dct=repl_dct)



def from_row_txtlc_mp(row: Row, repl_dct: dict[str, Any]) -> TxtlcMp:
    return TxtlcMp(repl_dct.get('src__txtlc_id', row['src__txtlc_id']),
                   repl_dct.get('trg__txtlc_id', row['trg__txtlc_id']),
                   Lc.fin(row['lc2']), row['translator'], row['score'], row['id'])


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


def orm(con: Connection, tbl: Table, row: Row, repl_dct=None) -> dict[str, Any]:
    return integrity.orm(con, tbl, row, from_row_any, repl_dct)


def from_row_any(ent_ty: EntTy[ET], row: Row, repl_dct: dict) -> ET:
    if ent_ty == ENT_TY_txtlc:
        return from_row_txtlc(row)
    elif ent_ty == ENT_TY_txtlc_file:
        return from_row_txtlc_file(row, repl_dct)
    elif ent_ty == ENT_TY_txtlc_mp:
        return from_row_txtlc_mp(row, repl_dct)
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
    elif ent_ty == ENT_TY_vocry:
        return from_row_vocry(row)
    elif ent_ty == ENT_TY_vocry_it:
        return from_row_vocry_it(row, repl_dct)
    elif ent_ty == ENT_TY_vocry_mp_it:
        return from_row_vocry_mp_it(row, repl_dct)
    elif ent_ty == ENT_TY_learned:
        return from_row_learned(row, repl_dct)
    elif ent_ty == ENT_TY_story:
        return Story(row=row, repl_dct=repl_dct)
    elif ent_ty == ENT_TY_story_it:
        return StoryIt(row=row, repl_dct=repl_dct)
    elif ent_ty == ENT_TY_txt_seq_aud:
        return TxtSeqAud(row=row, repl_dct=repl_dct)

    return row['id']
