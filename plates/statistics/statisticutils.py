# _*_ coding:utf-8 _*_
# __Author__： zizle
import json
import datetime


# 处理查询结果date_array与amount_all内的日期格式对应
def query_result_into_stuffs(date_array, amount_all):
    import pandas as pd
    stuffs = ['日期']
    # 获取职员的集合数组，第一个值为日期（表头）
    for work_count_item in amount_all:
        if work_count_item['name'] not in stuffs:
            stuffs.append(work_count_item['name'])
    array_to_calculate_sum = list()  # 用于计算的二维数组
    for date_item in date_array:
        date_statistics_arr = [0 for _ in range(len(stuffs))]  # 默认行的数据
        date_statistics_arr[0] = date_item  # 修改第一个值为日期
        for work_count_item in amount_all:
            if work_count_item['date'] == date_item:  # 日期一致
                name_index = 0  # 默认索引为0的数待修改
                for index, stuff_name in enumerate(stuffs):  # 查找出当前真正属于谁的数据
                    if work_count_item['name'] == stuff_name:  # 必有值
                        name_index = index  # 修改索引index
                date_statistics_arr[name_index] = work_count_item['count']  # 修改行中目标索引的数据
        array_to_calculate_sum.append(date_statistics_arr)  # 加入准备好的容器
    # 转为pandas的DataFrame进行数据计算
    pd_data_frame = pd.DataFrame(array_to_calculate_sum, columns=stuffs)
    pd_data_frame["合计"] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=1)  # 各行数据和添加至末尾列
    pd_data_frame.loc['总计'] = pd_data_frame.iloc[:, 1:].apply(lambda x: x.sum(), axis=0)  # 各列的数据和添加至末尾行
    pd_data_frame.iloc[pd_data_frame.shape[0] - 1, 0] = '总计'  # 将最后一行第一个值原NAN修改为总计
    return json.loads(pd_data_frame.to_json(orient='split', double_precision=0))


def generate_date_array(year, month):
    date_array = list()
    start_date, end_date = get_first_month_last_month(year, month)
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    while start_date <= end_date:
        date_array.append(start_date.strftime("%Y-%m-%d"))
        start_date += datetime.timedelta(1)
    return date_array


def generate_month_array(year):
    date_array = list()
    if not year:
        today = datetime.datetime.today()
        year = today.year
    month = 1

    while month <= 12:
        month_str = "%d-%02d" % (year, month)
        date_array.append(month_str)
        month += 1
    return date_array


# 获取查询的开始日期和结束日期
def get_first_month_last_month(year, month):
    today = datetime.datetime.today()
    if not year or year < 1970:
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
    first_month = datetime.datetime.strptime(str_month_first, "%Y-%m")
    last_month = datetime.datetime.strptime(str_next_month_first, "%Y-%m")+ datetime.timedelta(seconds=-1)
    return first_month.strftime("%Y-%m-%d"), last_month.strftime("%Y-%m-%d %H:%M:%S")


def get_year_start_year_end(year):
    if not year:
        today = datetime.datetime.today()
        year = today.year
    start_month = "%d-%d" % (year, 1)
    end_time = "%d-12-31 23:59:59" % year
    year_start = datetime.datetime.strptime(start_month, "%Y-%m")
    year_end = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    return year_start.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d %H:%M:%S")
