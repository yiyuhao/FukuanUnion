#      File: utils.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from decimal import Decimal
import re


def get_bank_name(name):
    """
    '中国招商银行成都建设路支行'  -->  '中国招商银行'
    :param name:  (str)
    :return:  (str)
    """
    match = re.match('(.+?(银行|联合社|信用社))', name)
    return match.group(1) if match else name


def get_amount(amount):
    """
    将int类型的乘了100的金额以正常形式返回
    :param amount: (int, str)
    :return: (float or int)

    >>> get_amount(30001)
    >>> 300.01

    >>> get_amount('30010')
    >>> 300.1
    """

    result = float(Decimal(amount) / 100)
    return int(result) if result.is_integer() else result


def set_amount(amount):
    """
    将金额乘100存入数据库
    >>> set_amount(300.01)
    >>> 30001

    >>> set_amount('300.1')
    >>> 30010
    :param amount: (str, int, float, Decimal)  300.01 --> 30001   '300.1' --> 30010
    :return: (int)
    """
    return int(Decimal(str(amount)) * 100)


class AreaNode:
    """Area tree node"""

    def __init__(self, id_, name, adcode, parent=None):
        """
        :param id_: (int) pk
        :param name: (str) name
        :param adcode: (str) unique adcode
        :param parent: (AreaNode)
        """

        self.id = id_
        self.name = name
        self.adcode = adcode
        self.children = []
        self.parent_id = parent
        if parent is not None:
            parent.children.append(self)

    def to_dict(self, node_dict=None, depth=3):
        if node_dict is None:
            node_dict = {}
        node_dict['name'] = self.name
        node_dict['adcode'] = self.adcode
        if self.children and depth - 1 > 0:
            node_dict['children'] = [node.to_dict(depth=depth - 1) for node in self.children]
        return node_dict
