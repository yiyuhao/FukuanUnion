# -*- coding: utf-8 -*-
#       File: generate_area_info.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import os
import logging

import requests
import MySQLdb
from requests.exceptions import ConnectionError
from _mysql_exceptions import IntegrityError


logger = logging.getLogger(__name__)
KEY = 'GPSBZ-VJPW2-2TSUH-COVZS-CIYM6-ZOB2R'

BASE_URL = 'https://apis.map.qq.com/ws/district/v1/'

CONF = {
    '11': {'00': "北京市"},
    '31': {'00': "上海市"},
    '51': {'01': "成都市"},
}

ADCODE_FMT = '<012d'

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36')
}


def get_item_list_by_adcode(adcode):
    """
    根据城市/城市下的行政区的adcode获取所有子级行政区信息
    :param adcode: 城市/行政区域 adcode
    :return: [{id:xxx, fullname:xxx}...]
    """
    CHILDREN_URL = f'{BASE_URL}getchildren'
    params = {
        'key': KEY,
        'id': adcode,
    }
    try:
        resp = requests.get(url=CHILDREN_URL, params=params, headers=HEADERS)
    except ConnectionError as e:
        logger.info(f"获取adcode: {adcode} 的子级行政区的网络链接失败")
        return []

    if resp.status_code not in (200, 201):
        logger.info(f"获取adcode: {adcode} 的子级行政区出错,"
                    f"状态码: {resp.status_code}")
        return []

    resp_json = resp.json()
    if resp_json['status'] != 0:  # 请求成功, status为0
        logger.info(f"获取adcode: {adcode} 的子级行政区出错,"
                    f"返回值: {resp.status_code}")
        return []

    return resp_json['result'][0]


def query_ids_dic(conn, table_name, data_dic):
    """ 查询插入数据的id """
    cursor = conn.cursor()
    base_sql = 'SELECT id from {} WHERE name = '.format(table_name)
    ids_dict = {}
    for key in data_dic:
        sql = base_sql + "'{}';".format(key)
        cursor.execute(sql)
        results = cursor.fetchall()
        ids_dict[key] = results[0][0] if results else None
    return ids_dict


def insert_data(conn, table_name, data_dic, sql, values, write_db):
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, values)
        full_sql = cursor._executed.decode('utf8')
        if write_db:
            conn.commit()
        else:
            file_path = '{}/insert_sql.txt'.format(os.path.dirname(__file__))
            with open(file_path, 'a+', encoding='utf-8') as f:
                f.write(full_sql + '\n\n')
        ids_dict = query_ids_dic(conn, table_name, data_dic)
    except IntegrityError as e:
        print("插入数据出错： ", e)
        ids_dict = query_ids_dic(conn, table_name, data_dic)
    except Exception as e:
        print("发生错误了", e)
        return False

    return ids_dict


def insert_common_city(conn, table_name, data_dic, write_db):
    sql = 'INSERT INTO {} (name) VALUES (%s)'.format(table_name)
    values = []
    for city in data_dic:
        values.append((city,))

    return insert_data(conn, table_name, data_dic, sql, values, write_db)


def insert_common_area_parent_none(conn, table_name, data_dic, city_id,
                                   write_db, parent_id=None):
    sql = 'INSERT INTO {} (name, city_id, parent_id, adcode) ' \
          'VALUES (%s, %s, %s, %s)'.format(table_name)
    values = []
    for area in data_dic:
        values.append((area, city_id, parent_id, data_dic[area][1]))

    return insert_data(conn, table_name, data_dic, sql, values, write_db)


def insert_common_area_parent_true(conn, table_name, cur_area, data_dic,
                                   city_id, write_db, parent_id=None):
    sql = 'INSERT INTO {} (name, city_id, parent_id, adcode) ' \
          'VALUES (%s, %s, %s, %s)'.format(table_name)
    values = []
    for area in data_dic[cur_area]:
        values.append((area[0], city_id, parent_id, area[1]))

    return insert_data(conn, table_name, data_dic, sql, values, write_db)


def check_insert_to_mysql(func):
    """ 检查是否写入mysql """
    def inner(write_db=False, password='', conn=None):
        if write_db:
            conn = MySQLdb.connect(
                "127.0.0.1", "root", password, "payunion", charset='utf8')
            func(write_db=write_db, conn=conn)
            conn.close()
        else:
            func()
    return inner


@check_insert_to_mysql
def main(write_db=False, conn=None):
    for pk in CONF:
        for ck in CONF[pk]:   # 目前这里只有一个城市, 可以添加多个
            area_dic = {CONF[pk][ck]: {}}
            block_dic = {}

            adcode = f'{pk}{ck}00'
            areas_list = get_item_list_by_adcode(adcode)
            for item in areas_list:
                area = item['fullname']
                item_list = [item['id'], format(int(item['id']), ADCODE_FMT)]
                area_dic[CONF[pk][ck]][area] = item_list

                block_dic[area] = []
                block_list = get_item_list_by_adcode(item['id'])
                for sub_item in block_list:
                    tmp_list = [sub_item['fullname'],
                                format(int(sub_item['id']), ADCODE_FMT)]
                    block_dic[area].append(tmp_list)

            if not write_db:
                print(area_dic)
                print(block_dic)

            if conn:
                # 插入城市
                city_ids_dic = insert_common_city(conn, 'common_city', area_dic,
                                                  write_db=write_db)

                # 插入政区
                for city in city_ids_dic:
                    area_ids_dic = insert_common_area_parent_none(
                        conn, 'common_area', area_dic[city], city_ids_dic[city],
                        write_db)

                    for area in block_dic:
                        # 插入街道
                        block_ids_dic = insert_common_area_parent_true(
                            conn, 'common_area', area, block_dic,
                            city_ids_dic[city], write_db, area_ids_dic[area])


if __name__ == '__main__':
    main(write_db=True)
