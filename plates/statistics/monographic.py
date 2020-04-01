# _*_ coding:utf-8 _*_
# Author: zizle
import json
import datetime
from flask import jsonify, request
from db import MySQLConnection
from flask.views import MethodView


"""专题研究统计视图"""


class MonographicWorkAmount(MethodView):
    def get(self):
        import pandas as pd
        try:
            query_year = int(request.args.get('year', 0))
            query_month = int(request.args.get('month', 0))  # 获取查询的月份
        except Exception:
            return jsonify("参数错误"), 400
        start_date, end_date = self.get_start_date_end_date(query_year, query_month)  # 获取开始和结束的时间
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
        query_statement = "SELECT DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') AS `date`, mogtb.author_id, usertb.name, COUNT(*) AS `count` " \
                          "FROM `monographic` as mogtb INNER JOIN `user_info` as usertb " \
                          "ON (mogtb.author_id=usertb.id) AND (DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') BETWEEN %s AND %s) GROUP BY mogtb.author_id, DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') ORDER BY DATE_FORMAT(mogtb.custom_time,'%%Y-%%m-%%d') ASC;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (start_date, end_date))
        amount_all = cursor.fetchall()
        # print('数据查询结果:',amount_all)
        # print(amount_all[0], amount_all[-1])
        if not amount_all:  # 没有数据记录
            return jsonify({})
        # 生成数据时间段的时间列表
        date_array = self.generate_date(amount_all[0]['date'], amount_all[-1]['date'])
        # 获取职员的集合数组，第一个值为日期（后续做表头使用）
        stuffs = ['日期']
        for work_count_item in amount_all:
            if work_count_item['name'] not in stuffs:
                stuffs.append(work_count_item['name'])
        # print('系统总职员:', stuffs)
        # 用于计算的二维数组
        array_to_calculate_sum = list()
        for date_item in date_array:
            date_statistics_arr = [0 for _ in range(len(stuffs))]  # 默认行的数据
            date_statistics_arr[0] = date_item  # 修改第一个值为日期
            for work_count_item in amount_all:
                if work_count_item['date'] == date_item:  # 日期一致
                    name_index = 0  # 默认索引为0的数待修改
                    for index, stuff_name in enumerate(stuffs):  # 查找出当前真正属于谁的数据
                        if work_count_item['name'] == stuff_name:  # 必有值
                            name_index = index  # 修改索引index
                    # 修改行中目标索引的数据
                    date_statistics_arr[name_index] = work_count_item['count']
            array_to_calculate_sum.append(date_statistics_arr)  # 加入准备好的容器
        # 转为pandas的DataFrame进行数据计算
        pd_data_frame = pd.DataFrame(array_to_calculate_sum, columns=stuffs)
        # 切出数据
        # print("切片数据：\n", pd_data_frame.iloc[:, 1:])
        pd_data_frame["合计"] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=1)  # 各行数据和添加至末尾列
        pd_data_frame.loc['总计'] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=0)  # 各列的数据和添加至末尾行
        # print('计算后的数据:\n', pd_data_frame)
        pd_data_frame.iloc[pd_data_frame.shape[0]-1, 0] = '总计'  # 将最后一行第一个值原NAN修改为总计
        # 数据体转为json数据
        statistics_arr = json.loads(pd_data_frame.to_json(orient='split', double_precision=0))
        return jsonify(statistics_arr)

    def generate_date(self, begin_date, end_date):
        dates = []
        dt = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
        date = begin_date[:]
        while date <= end_date:
            dates.append(date)
            dt = dt + datetime.timedelta(1)
            date = dt.strftime("%Y-%m-%d")
        return dates

    # 获取查询的开始日期和结束日期
    @staticmethod
    def get_start_date_end_date(year, month):
        today = datetime.datetime.today()
        if not year or year < 1 or year > 12:
            year = today.year
        if not month or month < 1 or month > 12:
            month = today.month
        str_month_first = "%d-%d" % (year, month)
        if month == 12:
            next_month = 1
            next_year = year + 1
            str_next_month_first = "%d-%d" % (next_year, next_month)
        else:
            month += 1
            str_next_month_first = "%d-%d" % (year, month)
        return datetime.datetime.strptime(str_month_first, "%Y-%m"), datetime.datetime.strptime(
            str_next_month_first, "%Y-%m") + datetime.timedelta(seconds=-1)
