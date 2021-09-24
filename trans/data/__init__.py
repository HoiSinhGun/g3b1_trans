from sqlalchemy import MetaData, create_engine

from entities import ENT_TY_tst_run

BOT_BKEY_TRANS = "trans"

DB_FILE_TRANS = rf'C:\Users\IFLRGU\Documents\dev\g3b1_{BOT_BKEY_TRANS}.db'
md_TRANS = MetaData()
eng_TRANS = create_engine(f"sqlite:///{DB_FILE_TRANS}")
md_TRANS.reflect(bind=eng_TRANS)

TST_TY_VOCABULARY = dict(id=1, bkey='vocabulary', descr="Vocabulary test - including both: "
                                                        "single words and whole sentences")
TST_TY_BLANKS = dict(id=2, bkey='blanks', descr='Text sections with blanks. '
                                                'Student fills in words from the word list into the blanks')

TST_TY_LI = [TST_TY_VOCABULARY, TST_TY_BLANKS]

ENT_TY_tst_run.cmd_prefix = '.tst.run.'
ENT_TY_tst_run.but_cmd_def = 'qansw'
ENT_TY_tst_run.but_cmd_li = [
    [('<<', 'qprev'), ('😶', 'qinfo'), ('🤔', 'qhint'), ('>>', 'qnext')],
    [('❗', 'tinfo'), ('❓', 'thint'), ('🔐', 'tfnsh')]
]
ENT_TY_tst_run.keyboard_descr = 'Type the answer or choose an option!'
