import logging

from g3b1_log.log import cfg_logger
from model import g3m_str_by_file_str

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)
g3_m_str_trans: str = g3m_str_by_file_str(__file__)

# Better move them to data package?
SUB_MOD_LI = ['tst']
