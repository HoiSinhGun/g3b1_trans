import logging

from g3b1_serv import utilities
from g3b1_log.g3b1_log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)
g3_m_str_trans: str = utilities.module_by_file_str(__file__)
COLUMNS_TRANS = dict[str: utilities.TgColumn]

# Better move them to data package?
LC_li = ['EN', 'VI', 'DE', 'RU']
SUB_MOD_LI = ['tst']
