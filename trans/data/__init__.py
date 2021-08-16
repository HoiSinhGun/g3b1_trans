from sqlalchemy import MetaData, create_engine

BOT_BKEY_TRANS = "trans"

DB_FILE_TRANS = rf'C:\Users\IFLRGU\Documents\dev\g3b1_{BOT_BKEY_TRANS}.db'
MetaData_TRANS = MetaData()
Engine_TRANS = create_engine(f"sqlite:///{DB_FILE_TRANS}")
MetaData_TRANS.reflect(bind=Engine_TRANS)

TST_TY_VOCABULARY = dict(id=1, bkey='vocabulary', descr="Vocabulary test - including both: "
                                                        "single words and whole sentences")
TST_TY_BLANKS = dict(id=2, bkey='blanks', descr='Text sections with blanks. '
                                                'Student fills in words from the word list into the blanks')

TST_TY_LI = [TST_TY_VOCABULARY, TST_TY_BLANKS]
