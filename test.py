# coding=utf-8
# 中文
def test(i_list=None):
    """
    456461313

    :type i_list: list or None
    :param i_list: abc
    :rtype: int
    :return: 132
    """
    if i_list is None:
        i_list = []
    i_list.append(1)
    print 'test', i_list, id(i_list)
    return ''


def show(i_list):
    print i_list, id(i_list)


class A:
    def __init__(self):
        pass

    def __funcA(self):
        return 1

    def _funcB(self):
        return 2


testA = A()
print getattr(testA, '_A__funcA')()
