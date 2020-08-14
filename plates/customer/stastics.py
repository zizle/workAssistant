# _*_ coding:utf-8 _*_
# @File  : stastics.py
# @Time  : 2020-08-14 10:09
# @Author: zizle


""" 对客户的权益统计 """

# 目标：统计每个人每个月的所有客户权益和

# 把权益表按时间降序排列->
# 按客户分组加limit分别得到所有客户的时间降序权益表 ->
# 按月分组取第一条得到客户的每月最新权益记录加limit的到所有人员的客户 ->
# 按人分组加limit得到每个成员的客户,并计算权益和
import json
from datetime import datetime

import pandas as pd
from flask import request, jsonify
from flask.views import MethodView

from db import MySQLConnection


def generate_month_array(year):
    date_array = list()
    if not year:
        today = datetime.today()
        year = today.year
    month = 1

    while month <= 12:
        month_str = "%d-%02d" % (year, month)
        date_array.append(month_str)
        month += 1
    return date_array


class CustomerStatistics(MethodView):
    def get(self):
        # # 非管理员不得查询数据
        # utoken = request.args.get('utoken', None)
        # user_info = verify_json_web_token(utoken)
        # if not user_info or not user_info["is_admin"]:
        #     return jsonify({'message': 'Invalidate User!'}), 400
        # query_date = request.args.get("queryDate", None)  # 固定只取每月10日的数据就无需查询日期
        start_year = request.args.get("startYear", None)
        # 验证时间
        try:
            # query_date = datetime.strptime(query_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            start_year = datetime.strptime(start_year, "%Y").strftime("%Y")
            end_year = str(int(start_year) + 1)
        except Exception as e:
            return jsonify({"message": "Invalidate query Date or Year!"})
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询所有用户信息以id为key转为字典
        cursor.execute(
            "SELECT id,name FROM user_info;"
        )
        all_user = cursor.fetchall()
        all_user_dict = {user["id"]: user["name"] for user in all_user}
        # 系统统计只取当月10日的数据
        # WHERE DATE_FORMAT(custom_time,'%%Y')>=%s AND DATE_FORMAT(custom_time,'%%d')='10'
        # 如果要取当月的最后一条记录只需改成WHERE DATE_FORMAT(custom_time,'%%Y')>=%s AND DATE_FORMAT(custom_time,'%%Y-%%mm-%%d')<=月末最后一天
        query_sql = "SELECT infoctb.belong_user,cmrights.ctime,sum(cmrights.crights) as sum_rights " \
                    "FROM info_customer AS infoctb " \
                    "LEFT JOIN " \
                    "(SELECT crighttb.ctime,crighttb.customer_id,crighttb.remain,crighttb.interest,crighttb.crights " \
                    "FROM (" \
                    "SELECT DATE_FORMAT(custom_time,'%%Y-%%m') AS ctime, customer_id,remain,interest,crights " \
                    "FROM customer_rights WHERE DATE_FORMAT(custom_time,'%%Y')>=%s AND DATE_FORMAT(custom_time,'%%Y')<%s AND DATE_FORMAT(custom_time,'%%d')='10' " \
                    "ORDER BY create_time DESC LIMIT 999999999) AS crighttb " \
                    "GROUP BY crighttb.customer_id, crighttb.ctime) AS cmrights " \
                    "ON infoctb.id=cmrights.customer_id " \
                    "GROUP BY cmrights.ctime,infoctb.belong_user;"
        cursor.execute(query_sql, (start_year, end_year))
        result = cursor.fetchall()
        stuffs = ["月份"]
        for item in result:
            if item["ctime"] is None:
                continue
            item["sum_rights"] = float(item["sum_rights"])
            item["username"] = all_user_dict.get(item["belong_user"], '')
            if item["username"] not in stuffs:
                stuffs.append(item["username"])
        # 生成月份数据
        month_arr = generate_month_array(int(start_year))
        array_to_calculate_sum = list()  # 用于计算的二维数组
        for date_item in month_arr:
            line_data_arr = [0 for _ in range(len(stuffs))]  # 默认行的数据
            line_data_arr[0] = date_item  # 修改第一个值为日期
            for result_item in result:
                if result_item['ctime'] == date_item:  # 日期一致
                    name_index = 0  # 默认索引为0的数待修改
                    for index, stuff_name in enumerate(stuffs):  # 查找出当前真正属于谁的数据
                        if result_item['username'] == stuff_name:  # 必有值
                            name_index = index  # 修改索引index
                    line_data_arr[name_index] = result_item['sum_rights']  # 修改行中目标索引的数据
            array_to_calculate_sum.append(line_data_arr)  # 加入准备好的容器
        pd_data_frame = pd.DataFrame(array_to_calculate_sum, columns=stuffs)
        pd_data_frame["合计"] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=1)  # 各行数据和添加至末尾列
        pd_data_frame.loc['总计'] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=0)  # 各列的数据和添加至末尾行
        pd_data_frame.iloc[pd_data_frame.shape[0] - 1, 0] = '总计'  # 将最后一行第一个值原NAN修改为总计
        finally_result = json.loads(pd_data_frame.to_json(orient='split'))

        return jsonify(finally_result)














