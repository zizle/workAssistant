# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
import hashlib
import os
import time

import pandas as pd
import xlrd
from flask import jsonify, request, current_app, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.psd_handler import verify_json_web_token
from vlibs import ORGANIZATIONS


class InvestrategyView(MethodView):
    def get(self):
        params = request.args
        # 解析用户信息
        token = params.get('utoken')
        user_info = verify_json_web_token(token)
        if not user_info:
            return jsonify("您的登录已过期,请重新登录查看.")
        user_id = user_info['uid']

        try:
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 30))
        except Exception:
            return jsonify("参数错误:DATE FORMAT ERROR & INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,invsgytb.id,invsgytb.custom_time,invsgytb.content,invsgytb.variety_id, varietytb.name AS variety, invsgytb.contract,invsgytb.direction,invsgytb.hands,invsgytb.open_position," \
                               "invsgytb.close_position,invsgytb.profit " \
                               "FROM `user_info` AS usertb INNER JOIN `investrategy` AS invsgytb INNER JOIN `variety` as varietytb ON " \
                               "(usertb.id=%s AND usertb.id=invsgytb.author_id) AND invsgytb.variety_id=varietytb.id AND (invsgytb.custom_time BETWEEN %s AND %s) " \
                               "ORDER BY invsgytb.custom_time DESC " \
                               "limit %s,%s;"
        cursor.execute(inner_join_statement, (user_id, start_date, end_date, start_id, page_size))
        result_records = cursor.fetchall()
        # print("内连接查投顾策略自方案结果", result_records)
        # 查询总条数
        count_statement = "SELECT COUNT(invsgytb.id) as total, SUM(invsgytb.profit) AS `sumprofit` " \
                          "FROM `user_info` AS usertb INNER JOIN `investrategy`AS invsgytb " \
                          "ON usertb.id=%s AND usertb.id=invsgytb.author_id AND (invsgytb.custom_time BETWEEN %s AND %s);"
        cursor.execute(count_statement, (user_id, start_date, end_date))

        fetch_one = cursor.fetchone()
        # print(fetch_one)
        db_connection.close()
        if fetch_one:
            total_count = fetch_one['total']
            sum_porfit = fetch_one['sumprofit']
        else:
            total_count = sum_porfit = 0

        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['records'] = list()
        for record_item in result_records:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            record_item['variety'] = (record_item['variety'] if record_item['variety'] else '') + str(record_item['contract'])
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
            record_item['open_position'] = float(record_item['open_position'])
            record_item['close_position'] = float(record_item['close_position'])
            record_item['profit'] = float(record_item['profit'])
            response_data['records'].append(record_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(result_records)
        response_data['total_count'] = total_count
        response_data['sum_profit'] = float(sum_porfit)

        return jsonify(response_data)

    def post(self):
        body_data = request.json
        author_id = body_data.get('author_id', None)
        if not author_id:
            return jsonify("参数错误，HAS NO AUTHORID.")
        # 查找用户
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_user_statement = "SELECT `id`,`name`,`is_admin` FROM `user_info` WHERE `id`=%s AND `is_active`=1;"
        cursor.execute(select_user_statement, author_id)
        user_obj = cursor.fetchone()
        if not user_obj:
            return jsonify("系统没有查到您的信息,无法操作."), 400
        if user_obj['is_admin']:
            return jsonify('请不要使用用管理员用户添加记录.')
        # 不为空的信息判断
        content = body_data.get('content', False)
        variety = body_data.get('variety', False)
        direction = body_data.get('direction', False)
        if not content or not variety or not direction:
            return jsonify("参数错误,NOT FOUND CONTENT,VARIETY,DIRECTION."), 400

        # 组织信息
        custom_time = body_data.get('custom_time')
        custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d') if custom_time else datetime.datetime.now()

        author_id = user_obj['id']
        contract = body_data.get('contract', '')
        hands = body_data.get('hands', 0)
        open_position = body_data.get('open_position', 0)
        close_position = body_data.get('close_position', 0)
        profit = body_data.get('profit')
        note = body_data.get('work_note', '')
        # 存入数据库
        save_invest_statement = "INSERT INTO `investrategy`" \
                              "(`custom_time`,`author_id`,`content`,`variety_id`,`contract`,`direction`,`hands`," \
                              "`open_position`,`close_position`,`profit`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型
            variety_id = int(variety)
            hands = int(hands) if hands else 0
            open_position = int(open_position) if open_position else 0
            close_position = int(close_position) if close_position else 0
            profit = float(profit) if profit else 0
            cursor.execute(save_invest_statement,
                           (custom_time, author_id, content, variety_id, contract, direction,hands,
                            open_position, close_position, profit)
                           )
            db_connection.commit()

        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("写入投顾策略记录错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            db_connection.close()
            return jsonify("保存成功!"), 201


class FileHandlerInvestrategyView(MethodView):

    def post(self):
        # 获取当前用户的信息
        user_id = request.form.get('uid')
        file = request.files.get('file', None)
        if not file or not user_id:
            return jsonify('参数错误,NOT FILE OR UID'), 400
        # 查找用户
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_user_statement = "SELECT `id`,`name`,`is_admin` FROM `user_info` WHERE `id`=%s;"
        cursor.execute(select_user_statement, user_id)
        user_obj = cursor.fetchone()

        # 管理员不给添加信息
        if user_obj['is_admin']:
            return jsonify('请不要使用用管理员用户添加记录.')
        # 准备品种信息
        # variety_dict = {value: key for key, value in VARIETY_LIB.items()}
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["name"]:variety_item['id'] for variety_item in variety_all}
        db_connection.close()
        # 文件内容
        file_contents = file.read()
        file_contents = xlrd.open_workbook(file_contents=file_contents)

        # 导入名称为“投顾策略记录”的表
        table_data = file_contents.sheet_by_name('投顾策略记录')

        # 检查sheet1是否导入完毕
        status = file_contents.sheet_loaded('投顾策略记录')
        if not status:
            return jsonify('文件数据导入失败'), 400
        # 读取第一行数据
        first_row = table_data.row_values(0)
        # 格式判断
        if first_row != ["日期", "策略内容", "品种", "合约", "方向(多头,空头,套利)","10万为限对应手数",
                         "策略开仓","策略平仓","策略结果(+/-/0)"]:
            return jsonify("表格格式有误,请修正."), 400
        # 读取数据并写入数据库
        nrows = table_data.nrows
        # ncols = table_data.ncols
        ready_to_save = list()
        start_row_in = False
        message = "表格列数据类型有误,请检查后上传."
        try:
            for row in range(nrows):
                row_content = table_data.row_values(row)
                if str(row_content[0]).strip() == "start":
                    start_row_in = True
                    continue
                if str(row_content[0]).strip() == "end":
                    start_row_in = False
                    continue
                if start_row_in:
                    record_row = list()
                    try:
                        record_row.append(xlrd.xldate_as_datetime(row_content[0], 0))
                    except Exception as e:
                        message = "第一列【日期】请使用日期格式上传."
                        raise ValueError(message)
                    record_row.append(user_id)
                    record_row.append(str(row_content[1]))
                    try:
                        record_row.append(int(variety_dict.get(str(row_content[2]))))  # 品种
                    except Exception as e:
                        message = "系统中没有【" + str(row_content[2]) + "】品种信息."
                        raise ValueError(message)
                    try:
                        contract = int(row_content[3])
                    except Exception:
                        contract = row_content[3]
                    record_row.append(str(contract))
                    record_row.append(str(row_content[4]))
                    record_row.append(int(row_content[5]) if row_content[5] else 0)
                    record_row.append(float(row_content[6]) if row_content[6] else 0)
                    record_row.append(float(row_content[7]) if row_content[7] else 0)
                    record_row.append(float(row_content[8]) if row_content[8] else 0)
                    ready_to_save.append(record_row)
            if len(ready_to_save) == 0:
                raise ValueError('没有读取到数据.')
            new_df = pd.DataFrame(ready_to_save)
            new_df.columns = ['custom_time', 'author_id', 'content', 'variety_id','contract','direction','hands','open_position','close_position','profit']
            save_list = self.drop_duplicates(new_df, user_id)
            if len(save_list) > 0:
                message = "数据保存成功!"
                insert_statement = "INSERT INTO `investrategy`" \
                                   "(`custom_time`,`author_id`,`content`,`variety_id`,`contract`,`direction`,`hands`," \
                                   "`open_position`,`close_position`,`profit`)" \
                                   "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                db_connection = MySQLConnection()
                cursor = db_connection.get_cursor()
                cursor.executemany(insert_statement, ready_to_save)
                db_connection.commit()
                db_connection.close()
            else:
                message = "数据上传成功,没有发现新数据!"
        except Exception as e:
            return jsonify(str(e)), 400
        else:
            return jsonify(message)

    @staticmethod
    def drop_duplicates(new_df, user_id):
        # 查询旧的数据
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `custom_time`,`author_id`,`content`,`variety_id`,`contract`,`direction`,`hands`, " \
                          "`open_position`,`close_position`,`profit` " \
                          "FROM `investrategy` WHERE `author_id`=%s;"
        cursor.execute(query_statement, user_id)
        old_df = pd.DataFrame(cursor.fetchall())
        db_connection.close()
        old_df['custom_time'] = pd.to_datetime(old_df['custom_time'], format='%Y-%m-%d')
        new_df['custom_time'] = pd.to_datetime(new_df['custom_time'], format='%Y-%m-%d')
        concat_df = pd.concat([old_df, new_df, old_df])
        save_df = concat_df.drop_duplicates(subset=['custom_time', 'content'], keep=False, inplace=False)
        if save_df.empty:
            return []
        else:
            save_df = save_df.copy()
            save_df['custom_time'] = save_df['custom_time'].apply(lambda x: x.strftime('%Y-%m-%d'))
            return save_df.values.tolist()


class RetrieveInvestrategyView(MethodView):
    def get(self, rid):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT usertb.name,usertb.org_id,invsgytb.id,invsgytb.custom_time,invsgytb.content,invsgytb.variety_id,invsgytb.contract,invsgytb.direction,invsgytb.hands,invsgytb.open_position," \
                           "invsgytb.close_position,invsgytb.profit " \
                           "FROM `user_info` AS usertb INNER JOIN `investrategy` AS invsgytb ON " \
                           "invsgytb.id=%s AND usertb.id=invsgytb.author_id;"
        cursor.execute(select_statement, rid)
        record_item = cursor.fetchone()
        record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
        record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
        record_item['open_position'] = float(record_item['open_position'])
        record_item['close_position'] = float(record_item['close_position'])
        record_item['profit'] = int(record_item['profit'])
        db_connection.close()
        return jsonify(record_item)

    def put(self, rid):
        body_json = request.json
        record_info = body_json.get('record_data')
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['uid']
        # 不为空的信息判断
        content = record_info.get('content', False)
        variety_id = record_info.get('variety_id', False)
        direction = record_info.get('direction', False)
        if not content or not variety_id or not direction:
            return jsonify("参数错误,NOT FOUND CONTENT,VARIETY,DIRECTION."), 400

        # 组织信息
        custom_time = record_info.get('custom_time')
        contract = record_info.get('contract', '')
        hands = record_info.get('hands', 0)
        open_position = record_info.get('open_position', 0)
        close_position = record_info.get('close_position', 0)
        profit = record_info.get('profit')
        # 存入数据库
        save_invest_statement = "UPDATE `investrategy` SET " \
                                "`custom_time`=%s,`content`=%s,`variety_id`=%s,`contract`=%s,`direction`=%s,`hands`=%s," \
                                "`open_position`=%s,`close_position`=%s,`profit`=%s " \
                                "WHERE `id`=%s AND `author_id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            # 转换类型
            custom_time = datetime.datetime.strptime(custom_time,'%Y-%m-%d') if custom_time else datetime.datetime.now()
            variety_id = int(variety_id)
            hands = int(hands) if hands else 0
            open_position = float(open_position) if open_position else 0
            close_position = float(close_position) if close_position else 0
            profit = float(profit) if profit else 0
            cursor.execute(save_invest_statement,
                           (custom_time, content, variety_id, contract, direction, hands,
                            open_position, close_position, profit, rid, user_id)
                           )
            db_connection.commit()

        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("更新投顾策略记录错误:" + str(e))
            return jsonify("参数错误!无法修改。"), 400
        else:
            db_connection.close()
            return jsonify("修改成功!"), 201

    def delete(self, rid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        db_connection = MySQLConnection()
        try:
            user_id = int(user_info['uid'])
            delete_statement = "DELETE FROM `investrategy` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(), `create_time`) < 3;" % (rid, user_id)
            cursor = db_connection.get_cursor()
            lines_changed = cursor.execute(delete_statement)
            db_connection.commit()
            if lines_changed <= 0:
                raise ValueError("较早的记录.已经无法删除了>…<")
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify(str(e))
        else:
            db_connection.close()
            return jsonify("删除成功^.^!")


class InvestrategyExportView(MethodView):
    def get(self):
        params = request.args
        utoken = params.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify("登录已过期!刷新网页重新登录."), 400
        try:
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return jsonify("参数错误:DATE FORMAT ERROR!")
        query_statement = "SELECT usertb.name,usertb.org_id,invsgytb.custom_time,invsgytb.content,invsgytb.variety_id,invsgytb.contract,invsgytb.direction,invsgytb.hands," \
                          "invsgytb.open_position,invsgytb.close_position,invsgytb.profit,invsgytb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `investrategy` AS invsgytb ON " \
                          "usertb.id=%s AND usertb.id=invsgytb.author_id AND (invsgytb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY invsgytb.custom_time ASC;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询品种
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (user_info['uid'], start_date, end_date))
        records_all = cursor.fetchall()
        db_connection.close()
        # 生成承载数据的文件
        t = "%.4f" % time.time()
        md5_hash = hashlib.md5()
        md5_hash.update(t.encode('utf-8'))
        md5_hash.update(user_info['name'].encode('utf-8'))
        md5_str = md5_hash.hexdigest()
        file_folder = os.path.join(BASE_DIR, 'fileStore/exports/')
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        file_path = os.path.join(file_folder, '{}.xlsx'.format(md5_str))

        file_records = list()
        for record_item in records_all:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['content'])
            row_content.append(variety_dict.get(record_item['variety_id'], ''))
            row_content.append(record_item['contract'])
            row_content.append(record_item['direction'])
            row_content.append(record_item['hands'])
            row_content.append(float(record_item['open_position']))
            row_content.append(float(record_item['close_position']))
            row_content.append(float(record_item['profit']))
            row_content.append(record_item['note'])
            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = ['日期', '部门小组', '姓名', '策略内容', '品种', '合约', '方向', '手数', '策略开仓', '策略平仓', '策略结果','备注']
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name='投顾策略记录'
        )

        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )
