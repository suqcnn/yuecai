# -*- coding: utf-8 -*-
# @Time         : 2018/1/25 16:20
# @Author       : Huaiz
# @Email        : Apokar@163.com
# @File         : yucai_spider_update.py
# @Software     : PyCharm Community Edition
# @PROJECT_NAME : yuecai


import json
import sys
import traceback

reload(sys)
sys.setdefaultencoding('utf8')
from requests.exceptions import RequestException
import urllib3

urllib3.disable_warnings()

import re
import time
import requests
import threading
import random
import datetime
import MySQLdb

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Host': 'iris.yuecai.com',
    'Content-Type': 'application/json',
    'Origin': 'http://www.yuecai.com',
    'Content-Length': '71',
    'Referer': 'http://www.yuecai.com/purchase/?SiteID=21&start=20&page=1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}


def get_timestamp(normal_time):
    timeArray = time.strptime(str(normal_time), "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    return timestamp


def get_proxy():
    proxies = list(set(requests.get(
        "http://60.205.92.109/api.do?name=3E30E00CFEDCD468E6862270F5E728AF&status=1&type=static").text.split('\n')))
    return proxies


def get_page_number():
    payload = {"word": None, "zone": None, "page": 1, "size": 20, "sort": None, "teseData": 2}
    url = 'http://iris.yuecai.com/iris/v1/purchase/search'
    try:

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        if response.status_code == 200:
            content = json.loads(response.text)
            return content['resultData']['totalPages']
        else:
            print '获取页数出错'
            return None
    except Exception, e:
        print str(e)


def get_list_info(page):
    update_ids = []

    conn = MySQLdb.connect(host="221.226.72.226", port=13306, user="root", passwd="somao1129", db="tanke",
                           charset="utf8")
    cursor = conn.cursor()

    cursor.execute('select max(createtime) from purchase_yuecai_list')
    max_pub_time = cursor.fetchall()[0][0]

    print '获取上次跑的最新的时间  ' + str(max_pub_time)

    url = 'http://iris.yuecai.com/iris/v1/purchase/search'

    while True:
        try:
            for x in range(1, int(page) + 1):
                print '在爬第' + str(x) + '页'
                payload2 = {"word": None, "zone": None, "page": x, "size": 20, "sort": None, "teseData": 2}

                response = requests.post(url, data=json.dumps(payload2), headers=headers, timeout=30)

                info = json.loads(response.text)

                total_pages = len(info['resultData']['data'])

                for num in range(total_pages):
                    print '第' + str(num + 1) + '条'
                    id_tag = info['resultData']['data'][num]['id']
                    create_time = info['resultData']['data'][num]['pubDate']
                    type = info['resultData']['data'][num]['projectType']

                    print id_tag
                    print create_time
                    print max_pub_time

                    if get_timestamp(create_time + ':00') > get_timestamp(max_pub_time):

                        if type == '采购':

                            cursor.execute('replace into purchase_yuecai_list values ("%s","%s","%s","%s")' %
                                           (
                                               id_tag,
                                               create_time,

                                               str(datetime.datetime.now()),
                                               str(datetime.datetime.now())[:10]
                                           ))
                            update_ids.append(id_tag)
                            conn.commit()
                            print '采购类 ' + str(id_tag) + ' 发布时间: ' + str(create_time) + '  插入成功 _@_ ' + str(
                                datetime.datetime.now())

                        elif type == '竞价':
                            bidcode_t = info['resultData']['data'][num]['bidcode_t']
                            companyId = info['resultData']['data'][num]['companyId']
                            id_tag = info['resultData']['data'][num]['id']

                            url_part = str(bidcode_t) + '-' + str(companyId) + '-' + str(id_tag)
                            cursor.execute('replace into purchase_yuecai_list values ("%s","%s","%s","%s")' %
                                           (
                                               url_part,
                                               create_time,

                                               str(datetime.datetime.now()),
                                               str(datetime.datetime.now())[:10]
                                           ))
                            conn.commit()
                            update_ids.append(url_part)
                            print '竞价类 ' + str(id_tag) + ' 发布时间: ' + str(create_time) + '  插入成功 _@_ ' + str(
                                datetime.datetime.now())

                        elif type == '招标':
                            cursor.execute('replace into purchase_yuecai_list values ("%s","%s","%s","%s")' %
                                           (
                                               id_tag,
                                               create_time,

                                               str(datetime.datetime.now()),
                                               str(datetime.datetime.now())[:10]
                                           ))
                            conn.commit()
                            update_ids.append(id_tag)
                            print '招标类 ' + str(id_tag) + ' 发布时间: ' + str(create_time) + '  插入成功 _@_ ' + str(
                                datetime.datetime.now())


                    else:
                        print '检测到已爬信息  ' + str(id_tag) + ' 发布时间: ' + str(create_time) + ' _@_ ' + str(
                            datetime.datetime.now())
                        return update_ids

            break
        except Exception, e:
            if str(e).find('2006') >= 0:
                print '休息两秒 重连数据库(2006)'
                time.sleep(2)

                conn = MySQLdb.connect(host="221.226.72.226", port=13306, user="root", passwd="somao1129", db="tanke",
                                       charset="utf8")
                cursor = conn.cursor()

                continue

            elif str(e).find('2013') >= 0:
                print '休息两秒 重连数据库(2013)'
                conn = MySQLdb.connect(host="221.226.72.226", port=13306, user="root", passwd="somao1129", db="tanke",
                                       charset="utf8")
                cursor = conn.cursor()
                continue
            else:

                print traceback.format_exc()
                break


def main_update():
    page = get_page_number()
    print '有' + str(page) + '页'
    update_ids = get_list_info(page)
    # print update_ids


# if __name__ == '__main__':
#     conn = MySQLdb.connect(host="221.226.72.226", port=13306, user="root", passwd="somao1129", db="tanke",
#                            charset="utf8")
#     cursor = conn.cursor()
#
# cursor.execute('select max(createtime) from purchase_yuecai_list')
# max_pub_time = cursor.fetchall()[0][0]
#
# cursor.close()
# conn.close()
# print '获取上次跑的最新的时间  ' + str(max_pub_time)
#
#     main_update()
