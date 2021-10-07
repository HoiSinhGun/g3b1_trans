from sqlalchemy import MetaData, create_engine

from elements import EleTy
from entities import EntTy, G3_M_TRANS, ENT_TY_li

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

ENT_TY_tst_tplate = EntTy(G3_M_TRANS, 'tst_tplate', 'Test Template')
ENT_TY_tst_tplate_it = EntTy(G3_M_TRANS, 'tst_tplate_it', 'Test Item')
ENT_TY_tst_tplate_it_ans = EntTy(G3_M_TRANS, 'tst_tplate_it_ans', 'Test Answer')
ENT_TY_tst_run = EntTy(G3_M_TRANS, 'tst_run', 'Tst Run', sel_ent_ty='sel_tst_run')
ENT_TY_tst_run_act = EntTy(G3_M_TRANS, 'tst_run_act', 'Tst Run Act')
ENT_TY_tst_run_act_sus = EntTy(G3_M_TRANS, 'txt_run_act_sus', 'TstRun ActSus')
ENT_TY_txt_seq = EntTy(G3_M_TRANS, 'txt_seq', 'Text Sequence', tbl_name='p_txt_seq')
ENT_TY_txt_seq_it = EntTy(G3_M_TRANS, 'txt_seq_it', 'Txt Seq Item')
ENT_TY_txtlc = EntTy(G3_M_TRANS, 'txtlc', 'Text in LC')
ENT_TY_txtlc_mp = EntTy(G3_M_TRANS, 'txtlc_mp', 'Text in LC Mapping')
ENT_TY_txtlc_onym = EntTy(G3_M_TRANS, 'txtlc_onym', 'Syn/Ant-onym')

ENT_TY_trans_li = [ENT_TY_tst_tplate, ENT_TY_tst_tplate_it, ENT_TY_tst_tplate_it_ans,
                   ENT_TY_tst_run, ENT_TY_tst_run_act, ENT_TY_tst_run_act_sus,
                   ENT_TY_txt_seq, ENT_TY_txt_seq_it,
                   ENT_TY_txtlc, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym]
ENT_TY_li.extend(ENT_TY_trans_li)

ELE_TY_txtlc_id = EleTy(id_='txtlc_id', descr='Text in LC', ent_ty=ENT_TY_txtlc)
ELE_TY_txtlc_mp_id = EleTy(id_='txtlc_mp_id', descr='Txtlc Map', ent_ty=ENT_TY_txtlc_mp)
ELE_TY_txt_seq_id = EleTy(id_='txt_seq_id', col_name='p_txt_seq_id', descr='Text Sequence', ent_ty=ENT_TY_txt_seq)
ELE_TY_txt_seq_it_id = EleTy(id_='txt_seq_it_id', descr='Txt Seq Item', ent_ty=ENT_TY_txt_seq_it)
ELE_TY_tst_run_id = EleTy(id_='tst_run_id', descr='Test Run', ent_ty=ENT_TY_tst_run)
ELE_TY_tst_run_act_id = EleTy(id_='tst_run_act_id', descr='TstRun Act', ent_ty=ENT_TY_tst_run_act)
ELE_TY_tst_run_act_sus_id = EleTy(id_='tst_run_act_sus_id', descr='TstRun ActSus', ent_ty=ENT_TY_tst_run_act_sus)
ELE_TY_tst_tplate_id = EleTy(id_='tst_tplate_id', descr='Test Template', ent_ty=ENT_TY_tst_tplate)
ELE_TY_tst_tplate_it_id = EleTy(id_='tst_tplate_it_id', descr='Tst TPlate Item', ent_ty=ENT_TY_tst_tplate_it)
ELE_TY_tst_tplate_it_ans_id = EleTy(id_='tst_tplate_it_ans_id', descr='Tst TP It Answer',
                                    ent_ty=ENT_TY_tst_tplate_it_ans)

ELE_TY_trans_li = [ELE_TY_txtlc_id, ELE_TY_txtlc_mp_id,
                   ELE_TY_txt_seq_id, ELE_TY_txt_seq_it_id,
                   ELE_TY_tst_run_id, ELE_TY_tst_run_act_id, ELE_TY_tst_run_act_sus_id,
                   ELE_TY_tst_tplate_id, ELE_TY_tst_tplate_it_id, ELE_TY_tst_tplate_it_ans_id]
