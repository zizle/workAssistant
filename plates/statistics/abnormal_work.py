# _*_ coding:utf-8 _*_
# Author: zizle
from flask import jsonify, request
from flask.views import MethodView

from db import MySQLConnection
from plates.statistics import statisticutils

"""非常态工作统计视图"""


class StuffAbnormalWorkAmount(MethodView):
    def get(self):
        try:
            query_year = int(request.args.get('year', 0))
            query_month = int(request.args.get('month', 0))  # 获取查询的月份
        except Exception:
            return jsonify("参数错误"), 400
        if not query_month:
            start_date, end_date = statisticutils.get_year_start_year_end(query_year)
            query_statement = "SELECT DATE_FORMAT(abwtb.custom_time,'%%Y-%%m') AS `date`, abwtb.author_id, usertb.name, COUNT(*) AS `count` " \
                              "FROM `abnormal_work` as abwtb INNER JOIN `user_info` as usertb " \
                              "ON abwtb.is_examined=1 AND (abwtb.author_id=usertb.id) AND (DATE_FORMAT(abwtb.custom_time,'%%Y-%%m-%%d') BETWEEN %s AND %s) " \
                              "GROUP BY abwtb.author_id, DATE_FORMAT(abwtb.custom_time,'%%Y-%%m') " \
                              "ORDER BY DATE_FORMAT(abwtb.custom_time,'%%Y-%%m') ASC;"
            target_date_array = statisticutils.generate_month_array(query_year)
        else:
            start_date, end_date = statisticutils.get_first_month_last_month(query_year, query_month)
            query_statement = "SELECT DATE_FORMAT(abwtb.custom_time,'%%Y-%%m-%%d') AS `date`, abwtb.author_id, usertb.name, COUNT(*) AS `count` " \
                              "FROM `abnormal_work` as abwtb INNER JOIN `user_info` as usertb " \
                              "ON abwtb.is_examined=1 AND (abwtb.author_id=usertb.id) AND (DATE_FORMAT(abwtb.custom_time,'%%Y-%%m-%%d') BETWEEN %s AND %s) " \
                              "GROUP BY abwtb.author_id, DATE_FORMAT(abwtb.custom_time,'%%Y-%%m-%%d') " \
                              "ORDER BY DATE_FORMAT(abwtb.custom_time,'%%Y-%%m-%%d') ASC;"
            target_date_array = statisticutils.generate_date_array(query_year, query_month)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (start_date, end_date))
        amount_all = cursor.fetchall()
        db_connection.close()
        if not amount_all:  # 没有数据记录
            return jsonify({})
        statistics_arr = statisticutils.query_result_into_stuffs(target_date_array, amount_all)
        return jsonify(statistics_arr)
