# _*_ coding:utf-8 _*_
# Author: zizle
from flask import jsonify, request
from db import MySQLConnection
from flask.views import MethodView
from plates.statistics import statisticutils


"""专题研究统计视图"""


class MonographicWorkAmount(MethodView):
    def get(self):
        try:
            query_year = int(request.args.get('year', 0))
            query_month = int(request.args.get('month', 0))  # 获取查询的月份
        except Exception:
            return jsonify("参数错误"), 400
        if not query_month:  # 表示按年统计
            start_date, end_date = statisticutils.get_year_start_year_end(query_year)
            query_statement = "SELECT DATE_FORMAT(mogtb.custom_time,'%%Y-%%m') AS `date`, mogtb.author_id, usertb.name, COUNT(*) AS `count` " \
                              "FROM `monographic` as mogtb INNER JOIN `user_info` as usertb " \
                              "ON (mogtb.author_id=usertb.id) AND (DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') BETWEEN %s AND %s) GROUP BY mogtb.author_id, DATE_FORMAT(mogtb.custom_time,'%%Y-%%m') ORDER BY DATE_FORMAT(mogtb.custom_time,'%%Y-%%m') ASC;"
            target_date_array = statisticutils.generate_month_array(query_year)  # 生成目标数据时间段的时间列表
        else:  # 按月份统计
            start_date, end_date = statisticutils.get_first_month_last_month(query_year, query_month)  # 获取开始和结束的时间
            query_statement = "SELECT DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') AS `date`, mogtb.author_id, usertb.name, COUNT(*) AS `count` " \
                              "FROM `monographic` as mogtb INNER JOIN `user_info` as usertb " \
                              "ON (mogtb.author_id=usertb.id) AND (DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') BETWEEN %s AND %s) GROUP BY mogtb.author_id, DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') ORDER BY DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') ASC;"
            target_date_array = statisticutils.generate_date_array(query_year, query_month)  # 生成目标数据时间段的时间列表
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (start_date, end_date))
        amount_all = cursor.fetchall()
        db_connection.close()
        if not amount_all:  # 没有数据记录
            return jsonify({})
        statistics_arr = statisticutils.query_result_into_stuffs(target_date_array, amount_all)
        return jsonify(statistics_arr)
