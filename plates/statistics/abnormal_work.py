# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
from flask import current_app, jsonify
from db import MySQLConnection
from flask.views import MethodView


"""非常态工作统计视图"""


class StuffAbnormalWorkAmount(MethodView):
    def get(self):
        # 查询统计每个人每天工作数量
        #query_statement = "SELECT DATE_FORMAT(`custom_time`,'%Y-%m-%d') AS `date`, `author_id`, COUNT(*) AS `count` FROM `abnormal_work` GROUP BY DATE_FORMAT(`custom_time`,'%Y-%m-%d'),`author_id`;"
        query_statement = "SELECT DATE_FORMAT(abwtb.custom_time,'%Y-%m-%d') AS `date`, abwtb.author_id, usertb.name, COUNT(*) AS `count` FROM `abnormal_work` as abwtb INNER JOIN `user_info` as usertb ON abwtb.author_id=usertb.id GROUP BY abwtb.author_id, DATE_FORMAT(abwtb.custom_time,'%Y-%m-%d') ORDER BY DATE_FORMAT(abwtb.custom_time,'%Y-%m-%d') DESC;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement)
        amount_all = cursor.fetchall()
        print(amount_all[0], amount_all[-1])
        # 生成数据时间段的时间列表
        date_array = self.generate_date(amount_all[-1]['date'], amount_all[0]['date'])
        print(date_array)
        # 重新整理数据[{"author_id": 1, "name": "xxx", "statistics": [{"date": "xxx-xx-xx", "count": x}]},]
        resp_data_with_ids = dict()
        for work_count_item in amount_all:
            if work_count_item['author_id'] not in resp_data_with_ids.keys():
                resp_data_with_ids[work_count_item['author_id']] = author_data_dict = dict()
                author_data_dict['statistics'] = list()
                author_data_dict['author_id'] = work_count_item['author_id']
                author_data_dict['name'] = work_count_item['name']
            author_data_dict = resp_data_with_ids.get(work_count_item['author_id'])
            author_data_dict['statistics'].append({'date': work_count_item['date'], 'count': work_count_item['count']})

        print(resp_data_with_ids)
        # 生成当前年份的所有时间


        return jsonify(resp_data_with_ids)

    def generate_date(self, begin_date, end_date):
        dates = []
        dt = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
        date = begin_date[:]
        while date <= end_date:
            dates.append(date)
            dt = dt + datetime.timedelta(1)
            date = dt.strftime("%Y-%m-%d")
        return dates



