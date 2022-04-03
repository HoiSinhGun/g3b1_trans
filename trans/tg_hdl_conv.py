from collections import namedtuple

from anytree import Node

from data.enums import TyLcPair, Lc
# from data.model import ConvRole, ConvIt, Conv
from g3b1_cfg.tg_cfg import G3Ctx
from utilities import now_for_sql


class ConvMgr:
    TyConv = namedtuple('TyConv', ['chat_id', 'bkey', 'lc_pair', 'title', 'roles', 'step'])

    ins_d: dict[int, "ConvMgr"] = {}

    def __init__(self):
        self.chat_id = G3Ctx.chat_id()
        self.lc_pair = TyLcPair(Lc.VI, Lc.EN)
        self.bkey = now_for_sql()
        self.descr = f'Conversation in {self.lc_pair.lc.value}'
        # self.role_li = [ConvRole('a', ['a']), ConvRole('b', ['b'])]
        # self.conv: Conv = Conv(self.chat_id, self.bkey, self.descr, self.lc_pair, self.role_li)
        self.step: Node = self.conv.it_node

    @classmethod
    def start(cls) -> "ConvMgr":
        """ Start a conversation for the given chat_id"""
        conv_mgr = cls()
        cls.ins_d[conv_mgr.chat_id] = conv_mgr
        return conv_mgr

    def set_bkey(self, bkey: str):
        """ Set a bkey for the conversation"""
        self.conv.bkey = bkey

    def set_lc_pair(self, lc_pair: TyLcPair):
        """ Set the language pair"""
        self.conv.lc_pair = lc_pair

    def set_descr(self, descr: str):
        """ Set a description for the conversation"""
        self.conv.descr = descr

    # def set_role_li(self, role_li: list[ConvRole]):
    #     """Specify key, description, replacement options for the 2 roles when playing the conversation"""
    #     self.conv.role_li = role_li

    def play(self):
        """Play the conversation with role replacement map"""
        self.step = self.conv.it_node

    # def step_add(self, conv_it: ConvIt):
    #     """ Add conversation step = text/reply/question/answer"""
    #     self.step = Node(conv_it.bkey, parent=self.step, bkey=conv_it.bkey, txt=conv_it.txt)

    def step_choose(self, bkey: str) -> Node:
        """ Choose a conversation step"""
        return self.step_goto(bkey)

    def step_goto(self, bkey: str):
        """ Move conversation step pointer to the given step """
        for it in self.conv.it_node.descendants:
            if it.name == bkey:
                self.step = it
                return it
        raise KeyError(f'bkey:{bkey}')

