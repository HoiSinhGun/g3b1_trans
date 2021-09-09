from grpc import services

from g3b1_test import test_utils
from trans.data import db
from trans.data.model import Txtlc, Lc
from trans.serv import services
from trans.serv.services import split_on_split


def test_google():
    services.translate_google('Hello, how are you?', Lc.EN.value, 'vi')


# noinspection SpellCheckingInspection
def test_conv_onym_str_li():
    src_syn_li, src_ant_li, trg_syn_li, trg_ant_li = services.conv_onym_str_li('Test = Exam = Exercise', '')
    join = str(' = ').join(src_syn_li)
    print(join)
    src_syn_li, src_ant_li, trg_syn_li, trg_ant_li = services.conv_onym_str_li('Test = Exam = Exercise', 'abc = def')
    print_conv_onym_result((src_syn_li, src_ant_li, trg_syn_li, trg_ant_li))

    src_syn_li, src_ant_li, trg_syn_li, trg_ant_li = services.conv_onym_str_li('Test ! Exam ! Exercise', 'abc ! def  ')
    print_conv_onym_result((src_syn_li, src_ant_li, trg_syn_li, trg_ant_li))

    src_syn_li, src_ant_li, trg_syn_li, trg_ant_li = services.conv_onym_str_li(
        'strong = powerful ! weak = mighty ! timid ', 'stark = mächtig ! schwach = mächtig ! ängstlich')
    print_conv_onym_result((src_syn_li, src_ant_li, trg_syn_li, trg_ant_li))


def print_conv_onym_result(tup: tuple[list, list, list, list]):
    for idx, item in enumerate(tup):
        c = ' = '
        if idx == 1 or idx == 3:
            c = ' ! '
        print(f'{idx}: {c.join(item)}')


# noinspection PyTypeChecker,SpellCheckingInspection
def test_hdl_cmd_reply_trans():
    upd = test_utils.upd_builder()
    lc_en_de = (Lc.EN, Lc.DE)
    # noinspection PyTypeChecker
    services.hdl_cmd_reply_trans(upd, None, upd.effective_user.id,
                                 'strong = powerful ! weak = mighty ! timid',
                                 # 'stark = mächtig ! schwach = mächtig ! schüchtern'
                                 lc_en_de)
    upd = test_utils.upd_builder()
    services.hdl_cmd_reply_trans(upd, None, upd.effective_user.id,
                                 'strong = powerful ! weak = mighty ! timid\n'
                                 'stark = mächtig ! schwach = mächtig ! schüchtern',
                                 lc_en_de)
    upd = test_utils.upd_builder()
    services.hdl_cmd_reply_trans(upd, None, upd.effective_user.id,
                                 'He is a strong man!',
                                 # 'stark = mächtig ! schwach = mächtig ! schüchtern',
                                 lc_en_de)
    upd = test_utils.upd_builder()
    # noinspection PyTypeChecker
    services.hdl_cmd_reply_trans(upd, None, upd.effective_user.id,
                                 'He is a strong man!\n'
                                 'er ist ein starker kerl!',
                                 lc_en_de)


# noinspection SpellCheckingInspection
def test_ins_onyms_from_str_li():
    services.iup_translation(Txtlc('peace', Lc.EN), Txtlc('frieden', Lc.DE), 'INPUT', 80)
    services.iup_translation(Txtlc('war', Lc.EN), Txtlc('krieg', Lc.DE), 'INPUT', 80)
    services.iup_translation(Txtlc('conflict', Lc.EN), Txtlc('konflikt', Lc.DE), 'INPUT', 80)
    services.iup_translation(Txtlc('fight', Lc.EN), Txtlc('kampf', Lc.DE), 'INPUT', 80)

    ant_li = ['peace', 'war']
    services.ins_onyms_from_str_li(Lc.EN, ant_li, 'INPUT', 'ant')
    syn_li = ['war', 'conflict', 'fight']
    services.ins_onyms_from_str_li(Lc.EN, syn_li, 'INPUT', 'syn')


def test_find_onyms():
    txt_lc_src = db.fiby_txt_lc(Txtlc('war', Lc.EN)).result
    li_all_onym = services.li_all_onym(txt_lc_src)
    for i_li in li_all_onym:
        for i in i_li:
            print(i)


def test_split_on_split():
    split = split_on_split('2,5,6,8', '1-3').result
    print(split)
    split = split_on_split('2,5,6,8,10,14', '3-4,5-6').result
    print(split)
    split = split_on_split('2,5,6,8,10,14,18,22,26', '2-5,7-8').result
    print(split)


def main():
    # test_google()
    # test_ins_onyms_from_str_li()
    # test_find_onyms()
    # test_hdl_cmd_reply_trans()
    # test_conv_onym_str_li()
    test_split_on_split()


if __name__ == '__main__':
    main()
