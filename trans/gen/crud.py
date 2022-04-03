import codecs
import os.path

from gen import db_gen
from str_utils import uncapitalize, underscore
from trans.data import model_orm
from trans.data.model_orm import Txtlc, Wrd, Dic, WrdR, WrdTxtSeq
from g3b1_serv import ut_os
from ut_os import write_to_fl

module_fl = db_gen.__file__
cls_li: list = [Dic, Txtlc, Wrd, WrdR, WrdTxtSeq]
base_cls_s: str = cls_li[0].__name__


def exe():
    line_li: list[str] = []

    src_line_li: list[str]
    src_import_line_li: list[str] = []
    src_def_line_li: list[str] = []
    with (codecs.open(module_fl)) as f:
        src_line_li = f.readlines()
    idx = 0
    for idx, src_line in enumerate(src_line_li):
        if not src_line:
            src_import_line_li.append(src_line)
        if src_line.startswith('def'):
            break
        if not src_line.startswith('from'):
            src_import_line_li.append(src_line)
            continue
        if src_line.strip().endswith(base_cls_s):
            continue
        src_import_line_li.append(src_line)
    src_def_line_li.extend(src_line_li[idx:])

    line_li.extend(src_import_line_li[:-2])
    for cls in cls_li:
        line_li.append(f'from trans.data.model_orm import {cls.__name__}\n')
    line_li.extend(['\n', '\n'])

    for cls in cls_li:
        if cls.__name__ == base_cls_s:
            line_li.extend(src_def_line_li)
            continue
        line_li.append('\n')
        for src_def_line in src_def_line_li:
            line_li.append(src_def_line.replace(base_cls_s, cls.__name__).replace(uncapitalize(base_cls_s),
                                                                                  underscore(cls.__name__)))
    print(''.join(line_li))
    src_db_gen = os.path.join('trans', 'gen')
    trg_db_gen = os.path.join('trans', 'data')
    trg_db_gen_fl = module_fl.replace(src_db_gen, trg_db_gen)
    write_to_fl(trg_db_gen_fl, line_li)
    # print(''.join(src_def_line_li))
