from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint, orm
from sqlalchemy.orm import declarative_base, relationship

from trans.data.enums import Lc, WrdRTy
from trans.data.model import TxtSeq

Base = declarative_base()


class Txtlc(Base):
    __tablename__ = 'txtlc'

    id = Column(Integer, primary_key=True)
    text = Column(String(999), nullable=False)
    lc = Column(String(2), nullable=False)
    s_review = Column(String(10), nullable=False, default=0)


class Dic(Base):
    __tablename__ = 'dic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bkey = Column(String(30), unique=True, nullable=False)
    lc = Column(Enum(Lc), nullable=False)
    lc2 = Column(Enum(Lc), nullable=False)

    wrd_li: list = relationship('Wrd', cascade="all,delete", back_populates='dic')

    def __repr__(self):
        return f"{Dic.__tablename__}(id={self.id!r}, bkey={self.bkey!r})"


class Wrd(Base):
    __tablename__ = 'wrd'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dic_id = Column(Integer, ForeignKey('dic.id'), nullable=False)
    txtlc_id = Column(Integer, ForeignKey('txtlc.id'), nullable=False)

    dic = relationship('Dic', back_populates='wrd_li')
    txtlc = relationship('Txtlc')

    UniqueConstraint('dic_id', 'txtlc_id', name='wrd_uc_1')


class WrdR(Base):
    __tablename__ = 'wrd_r'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wrd_id = Column(Integer, ForeignKey('wrd.id'), nullable=False)
    wrd2_id = Column(Integer, ForeignKey('wrd.id'), nullable=False)
    ty = Column(Enum(WrdRTy), nullable=False)
    hier = Column(String, nullable=False, default='0101')
    wrd = relationship('Wrd', foreign_keys=[wrd_id])
    wrd2 = relationship('Wrd', foreign_keys=[wrd2_id])

    UniqueConstraint('wrd_id', 'wrd2_id', 'ty', name='wrd_r_uc_1')


class WrdTxtSeq(Base):
    __tablename__ = 'wrd_txt_seq'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wrd_id = Column(Integer, ForeignKey('wrd.id'), nullable=False)
    txt_seq_id = Column(Integer, ForeignKey('wrd.id'), nullable=False)
    hier = Column(String, nullable=False, default='0101')

    UniqueConstraint('wrd_id', 'txt_seq_id', name='wrd_txt_seq_uc_1')

    def __init__(self, txt_seq: TxtSeq) -> None:
        super().__init__()
        self.txt_seq: TxtSeq = txt_seq
        self.txt_seq_id = self.txt_seq.id_

    @orm.reconstructor
    def init_on_load(self):
        self.txt_seq = TxtSeq(0, '', Lc.VI, Lc.EN, id_=self.txt_seq_id)
