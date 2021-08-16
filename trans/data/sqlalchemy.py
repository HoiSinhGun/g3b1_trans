from sqlalchemy.engine import Row

from trans.data.model import TstTemplate, TstTemplateIt, TxtLC


def tst_template_from_row(row: Row) -> TstTemplate:
    return TstTemplate(row['type'], row['bkey'],
                       row['lc'], row['lc_2'],
                       row['descr'], row['id'])


def tst_template_item_from_row(tst_template: TstTemplate, row: Row) -> TstTemplateIt:
    return TstTemplateIt(tst_template, TxtLC.from_id(row['type']), row['itnum'],
                         row['descr'], row['id'])
