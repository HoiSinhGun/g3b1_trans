from g3b1_serv.tg_reply import bold
from trans.data.model import TstTemplateIt, TstTemplate


def tst_template_lbl(tst_template: TstTemplate) -> str:
    lbl = f'{bold("Test")}: {bold(tst_template.bkey)}'
    return lbl


def tst_template_it_lbl(tst_template_it: TstTemplateIt) -> str:
    lbl = bold(f'Item number: {tst_template_it.itnum}\n')
    if tst_template_it.descr:
        lbl += tst_template_it.descr + '\n'
    lbl += bold(tst_template_it.txtlc_qt.txt)
    return lbl
