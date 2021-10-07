import logging

from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)

# Better move them to data package?
SUB_MOD_LI = ['tst']
