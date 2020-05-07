# _*_ coding:utf-8 _*_
# __Author__： zizle
import codecs
import csv
import datetime
import hashlib
import os
import time

import pandas as pd
from flask import jsonify, request, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.psd_handler import verify_json_web_token
from vlibs import ABNORMAL_WORK, ORGANIZATIONS


class QueryStuffRecordView(MethodView):
    ABNORMAL = 1
    MONOGRAPHIC = 2
    INVESTMENT = 3
    INVESTRATEGY = 4
    ARTPUBLISH = 5
    SHORTMESSAGE = 6
    ONDUTYMESSAGE = 7

    def get(self):
        params = request.args
        try:
            utoken = params.get('utoken')
            workuuid = int(params.get('workuuid'))
            userid = int(params.get('userid'))
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 50))
            export_action = int(params.get('export', 0))
        except Exception as e:
            return jsonify("参数错误"), 400
        if not all([workuuid, start_date, end_date]):
            return jsonify("参数错误"), 400
        request_user = verify_json_web_token(utoken)
        if not request_user or not request_user['is_admin']:
            return jsonify("INVALID USER"), 400
        if workuuid == self.ABNORMAL:
            if export_action:
                return self.export_abnormal_work(userid, start_date, end_date)
            else:
                return self.get_abnormal_work(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.MONOGRAPHIC:
            if export_action:
                return self.export_monographic(userid, start_date, end_date)
            else:
                return self.get_monographic(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.INVESTMENT:
            if export_action:
                return self.export_investment(userid, start_date, end_date)
            else:
                return self.get_investment(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.INVESTRATEGY:
            if export_action:
                return self.export_investrategy(userid, start_date, end_date)
            else:
                return self.get_investrategy(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.ARTPUBLISH:
            if export_action:
                return self.export_article_publish(userid, start_date, end_date)
            else:
                return self.get_article_publish(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.SHORTMESSAGE:
            if export_action:
                return self.export_short_message(userid, start_date, end_date)
            else:
                return self.get_short_message(userid, start_date, end_date, current_page, page_size)
        elif workuuid == self.ONDUTYMESSAGE:
            if export_action:
                return self.export_onduty_message(userid, start_date, end_date)
            else:
                return self.get_onduty_message(userid, start_date, end_date, current_page, page_size)
        else:
            return jsonify("参数错误"), 400

    def get_abnormal_work(self, userid, start_date, end_date, current_page, page_size):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        start_id = current_page * page_size
        table_headers = ['日期', '姓名', '标题', '类型', '申请部门', '申请者', '联系电话', '瑞币', '补贴', '备注', '附件']
        header_keys = ['custom_time', 'name', 'title', 'task_type', 'applied_org', 'applicant', 'tel_number',
                       'swiss_coin', 'allowance', 'note', 'annex_url']
        if userid == 0:
            query_statement = "SELECT usertb.name, abwtb.* " \
                              "FROM `abnormal_work` AS abwtb INNER JOIN `user_info` AS usertb " \
                              "ON abwtb.author_id=usertb.id AND (abwtb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY abwtb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(abwtb.id) AS `total` " \
                                    "FROM `abnormal_work` AS abwtb INNER JOIN `user_info` AS usertb " \
                                    "ON abwtb.author_id=usertb.id AND (abwtb.custom_time BETWEEN %s AND %s);"
            cursor.execute(total_count_statement, (start_date, end_date))
            total_count = cursor.fetchone()['total']  # 计算总页数
        else:
            query_statement = "SELECT usertb.name, abwtb.* " \
                              "FROM `abnormal_work` AS abwtb INNER JOIN `user_info` AS usertb " \
                              "ON abwtb.author_id=usertb.id AND abwtb.author_id=%s AND (abwtb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY abwtb.custom_time DESC " \
                              "LIMIT %s,%s;"

            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            # 总数
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `abnormal_work` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime("%Y-%m-%d")
            record_item['task_type'] = ABNORMAL_WORK.get(record_item['task_type'], '')
            record_item['swiss_coin'] = record_item['swiss_coin'] if record_item['swiss_coin'] else ''
            record_item['allowance'] = int(record_item['allowance'])
            record_item['annex'] = record_item['annex_url'] if record_item['annex_url'] else ''
            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count

        return jsonify(response_data)

    def export_abnormal_work(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '标题', '类型', '主办方', '申请部门', '申请者', '联系电话', '瑞币', '补贴', '备注']
        query_statement = "SELECT usertb.name,usertb.org_id,abworktb.custom_time,abworktb.task_type,abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number,abworktb.swiss_coin,abworktb.allowance,abworktb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb " \
                          "ON (usertb.id=%s AND usertb.id=abworktb.author_id) AND (abworktb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY abworktb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append(ABNORMAL_WORK.get(record_item['task_type'], ''))
            row_content.append(record_item['sponsor'])
            row_content.append(record_item['applied_org'])
            row_content.append(record_item['applicant'])
            row_content.append(record_item['tel_number'])
            row_content.append(record_item['swiss_coin'] if record_item['swiss_coin'] else '')
            row_content.append(int(record_item['allowance']))
            row_content.append(record_item['note'])

            file_records.append(row_content)
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        with codecs.open(file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(table_headers)
            writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )

    def get_monographic(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '姓名', '题目', '字数', '外发情况', '等级', '得分', '备注', '附件']
        header_keys = ['custom_time', 'name', 'title', 'words', 'is_publish', 'level', 'score', 'note', 'annex_url']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if userid == 0:
            query_statement = "SELECT usertb.name, mogytb.* " \
                              "FROM `monographic` AS mogytb INNER JOIN `user_info` AS usertb " \
                              "ON mogytb.author_id=usertb.id AND (mogytb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY mogytb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(mogytb.id) AS `total` " \
                                    "FROM `monographic` AS mogytb INNER JOIN `user_info` AS usertb " \
                                    "ON mogytb.author_id=usertb.id AND (mogytb.custom_time BETWEEN %s AND %s);"
            cursor.execute(total_count_statement, (start_date, end_date))
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT usertb.name, mogytb.* " \
                              "FROM `monographic` AS mogytb INNER JOIN `user_info` AS usertb " \
                              "ON mogytb.author_id=usertb.id AND mogytb.author_id=%s AND (mogytb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY mogytb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `monographic` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            total_count = cursor.fetchone()['total']

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime("%Y-%m-%d")
            record_item['words'] = int(record_item['words'])
            record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def export_monographic(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '题目', '字数', '外发情况', '等级', '得分', '备注']
        query_statement = "SELECT usertb.name,usertb.org_id,mgpctb.custom_time,mgpctb.title,mgpctb.words,mgpctb.is_publish,mgpctb.level,mgpctb.score,mgpctb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `monographic` AS mgpctb " \
                          "ON (usertb.id=%s AND usertb.id=mgpctb.author_id) AND (mgpctb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY mgpctb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append("是" if record_item['is_publish'] else "否")
            row_content.append(record_item['level'])
            row_content.append(record_item['score'])
            row_content.append(record_item['note'])

            file_records.append(row_content)
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        with codecs.open(file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(table_headers)
            writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )

    def get_investment(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '姓名', '标题', '品种', '方向', '实建日期', '实建均价', '实建手数', '实出均价', '止损均价', '有效期', '评级', '结果','备注','附件']
        header_keys = ['custom_time', 'name', 'title', 'variety', 'direction', 'build_time', 'build_price',
                       'build_hands', 'out_price','cutloss_price', 'expire_time', 'level', 'profit','note', 'annex_url']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        if userid == 0:
            query_statement = "SELECT usertb.name, invstb.* " \
                              "FROM `investment` AS invstb INNER JOIN `user_info` AS usertb " \
                              "ON invstb.author_id=usertb.id AND (invstb.custom_time BETWEEN %s AND %s ) " \
                              "ORDER BY invstb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(invstb.id) AS `total`,SUM(invstb.profit) AS `sumprofit` " \
                                    "FROM `investment` AS invstb INNER JOIN `user_info` AS usertb " \
                                    "ON invstb.author_id=usertb.id AND (invstb.custom_time BETWEEN %s AND %s );"
            cursor.execute(total_count_statement, (start_date, end_date))
            fetch_one = cursor.fetchone()
            if fetch_one:
                total_count = fetch_one['total']
                sum_porfit = fetch_one['sumprofit']
            else:
                total_count = sum_porfit = 0
        else:
            query_statement = "SELECT usertb.name, invstb.* " \
                              "FROM `investment` AS invstb INNER JOIN `user_info` AS usertb " \
                              "ON invstb.author_id=usertb.id AND invstb.author_id=%s AND (invstb.custom_time BETWEEN %s AND %s ) " \
                              "ORDER BY invstb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total`, SUM(`profit`) AS `sumprofit` FROM `investment` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            fetch_one = cursor.fetchone()
            # print(fetch_one)
            if fetch_one:
                total_count = fetch_one['total']
                sum_porfit = fetch_one['sumprofit']
            else:
                total_count = sum_porfit = 0

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime("%Y-%m-%d")
            record_item['build_time'] = record_item['build_time'].strftime('%Y-%m-%d %H:%M')
            record_item['expire_time'] = record_item['expire_time'].strftime('%Y-%m-%d %H:%M')
            record_item['variety'] = variety_dict.get(record_item['variety_id'], '') + str(record_item['contract'])
            # record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
            record_item['build_price'] = int(record_item['build_price'])
            record_item['out_price'] = int(record_item['out_price'])
            record_item['cutloss_price'] = int(record_item['cutloss_price'])
            record_item['profit'] = float(record_item['profit'])

            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        response_data['sum_profit'] = float(sum_porfit) if sum_porfit else 0
        return jsonify(response_data)

    def export_investment(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '标题', '品种', '合约', '方向', '实建日期', '实建均价', '实建手数', '实出均价', '止损均价', '有效期',
                         '外发', '结果']
        query_statement = "SELECT usertb.name,usertb.org_id,invstb.custom_time,invstb.title,invstb.variety_id,invstb.contract,invstb.direction,invstb.build_time," \
                          "invstb.build_price,invstb.build_hands,invstb.out_price,invstb.cutloss_price,invstb.expire_time,invstb.is_publish,invstb.profit " \
                          "FROM `user_info` AS usertb INNER JOIN `investment` AS invstb " \
                          "ON (usertb.id=%s AND usertb.id=invstb.author_id) AND (invstb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY invstb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append(variety_dict.get(record_item['variety_id'], '未知'))
            row_content.append(record_item['contract'])
            row_content.append(record_item['direction'])
            row_content.append(record_item['build_time'].strftime("%Y-%m-%d %H:%M"))
            row_content.append(record_item['build_price'])
            row_content.append(record_item['build_hands'])
            row_content.append(record_item['out_price'])
            row_content.append(record_item['cutloss_price'])
            row_content.append(record_item['expire_time'].strftime("%Y-%m-%d %H:%M"))
            row_content.append("是" if record_item['is_publish'] else "否")
            row_content.append(record_item['profit'])

            file_records.append(row_content)
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        with codecs.open(file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(table_headers)
            writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )

    def get_investrategy(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '姓名','策略内容', '品种', '方向', '手数', '策略开仓', '策略平仓', '结果','备注']
        header_keys = ['custom_time', 'name','content', 'variety', 'direction', 'hands', 'open_position', 'close_position','profit','note']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        if userid == 0:
            query_statement = "SELECT usertb.name, sgytb.* " \
                              "FROM `investrategy` AS sgytb INNER JOIN `user_info` AS usertb " \
                              "ON sgytb.author_id=usertb.id AND (sgytb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY sgytb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(sgytb.id) AS `total`,SUM(sgytb.profit) AS `sumprofit` " \
                                    "FROM `investrategy` AS sgytb INNER JOIN `user_info` AS usertb " \
                                    "ON sgytb.author_id=usertb.id AND (sgytb.custom_time BETWEEN %s AND %s);"
            cursor.execute(total_count_statement, (start_date, end_date))
            fetch_one = cursor.fetchone()
            if fetch_one:
                total_count = fetch_one['total']
                sum_porfit = fetch_one['sumprofit']
            else:
                total_count = sum_porfit = 0
        else:
            query_statement = "SELECT usertb.name, sgytb.* " \
                              "FROM `investrategy` AS sgytb INNER JOIN `user_info` AS usertb " \
                              "ON sgytb.author_id=usertb.id AND sgytb.author_id=%s AND (sgytb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY sgytb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total`, SUM(`profit`) AS `sumprofit` " \
                                    "FROM `investrategy` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            fetch_one = cursor.fetchone()
            if fetch_one:
                total_count = fetch_one['total']
                sum_porfit = fetch_one['sumprofit']
            else:
                total_count = sum_porfit = 0

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime("%Y-%m-%d")
            record_item['variety'] = variety_dict.get(record_item['variety_id'], '') + str(record_item['contract'])
            record_item['profit'] = float(record_item['profit'])
            record_item['open_position'] = float(record_item['open_position'])
            record_item['close_position'] = float(record_item['close_position'])
            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        response_data['sum_profit'] = float(sum_porfit) if sum_porfit else 0
        return jsonify(response_data)

    def export_investrategy(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '策略内容', '品种', '合约', '方向', '手数', '策略开仓', '策略平仓', '结果']
        query_statement = "SELECT usertb.name,usertb.org_id,invsgytb.custom_time,invsgytb.content,invsgytb.variety_id,invsgytb.contract,invsgytb.direction,invsgytb.hands," \
                          "invsgytb.open_position,invsgytb.close_position,invsgytb.profit " \
                          "FROM `user_info` AS usertb INNER JOIN `investrategy` AS invsgytb " \
                          "ON (usertb.id=%s AND usertb.id=invsgytb.author_id) AND (invsgytb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY invsgytb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['content'])
            row_content.append(variety_dict.get(record_item['variety_id'], '未知'))
            row_content.append(record_item['contract'])
            row_content.append(record_item['direction'])
            row_content.append(record_item['hands'])
            row_content.append(float(record_item['open_position']))
            row_content.append(float(record_item['close_position']))
            row_content.append(float(record_item['profit']))

            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = table_headers
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.xlsx'.format(md5_str))
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name="投顾策略记录"
        )
        # with codecs.open(file_path, 'w', 'utf_8_sig') as f:
        #     writer = csv.writer(f, dialect='excel')
        #     writer.writerow(table_headers)
        #     writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )

    def get_article_publish(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '姓名','题目', '发表/采访媒体', '稿件形式', '字数', '审核人', '收入奖励', '合作人', '备注','附件']
        header_keys = ['custom_time', 'name','title', 'media_name', 'rough_type', 'words', 'checker', 'allowance', 'partner','note','annex_url']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if userid == 0:
            query_statement = "SELECT usertb.name, arptb.* " \
                              "FROM `article_publish` AS arptb INNER JOIN `user_info` AS usertb " \
                              "ON arptb.author_id=usertb.id AND (arptb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY arptb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(arptb.id) AS `total` " \
                                    "FROM `article_publish` AS arptb INNER JOIN `user_info` AS usertb " \
                                    "ON arptb.author_id=usertb.id AND (arptb.custom_time BETWEEN %s AND %s);"
            cursor.execute(total_count_statement, (start_date, end_date))
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT usertb.name, arptb.* " \
                              "FROM `article_publish` AS arptb INNER JOIN `user_info` AS usertb " \
                              "ON arptb.author_id=usertb.id AND arptb.author_id=%s AND (arptb.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY arptb.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid,start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `article_publish` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid,start_date, end_date))
            total_count = cursor.fetchone()['total']

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')

            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def export_article_publish(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '题目', '发表/采访媒体', '稿件形式', '字数', '审核人', '收入奖励', '合作人', '备注']
        query_statement = "SELECT usertb.name,usertb.org_id,atltb.custom_time,atltb.title,atltb.media_name,atltb.rough_type,atltb.words,atltb.checker," \
                          "atltb.allowance,atltb.partner,atltb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `article_publish` AS atltb " \
                          "ON (usertb.id=%s AND usertb.id=atltb.author_id) AND (atltb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY atltb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # # 准备品种信息
        # query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        # cursor.execute(query_variety)
        # variety_all = cursor.fetchall()
        # variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append(record_item['media_name'])
            row_content.append(record_item['rough_type'])
            row_content.append(record_item['words'])
            row_content.append(record_item['checker'])
            row_content.append(record_item['allowance'])
            row_content.append(record_item['partner'])
            row_content.append(record_item['note'])

            file_records.append(row_content)
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        with codecs.open(file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(table_headers)
            writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )

    def get_short_message(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期','姓名', '信息内容', '类别', '影响品种', '备注']
        header_keys = ['custom_time','name', 'content', 'msg_type', 'effect_variety', 'note']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if userid == 0:
            query_statement = "SELECT usertb.name,sotmsg.* " \
                              "FROM `short_message` AS sotmsg INNER JOIN `user_info` AS usertb " \
                              "ON sotmsg.author_id=usertb.id AND (sotmsg.custom_time BETWEEN %s AND %s ) " \
                              "ORDER BY sotmsg.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(sotmsg.id) AS `total` " \
                                    "FROM `short_message` AS sotmsg INNER JOIN `user_info` AS usertb " \
                                    "ON sotmsg.author_id=usertb.id AND (sotmsg.custom_time BETWEEN %s AND %s );"
            cursor.execute(total_count_statement, (start_date, end_date))
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT usertb.name,sotmsg.* " \
                              "FROM `short_message` AS sotmsg INNER JOIN `user_info` AS usertb " \
                              "ON sotmsg.author_id=usertb.id AND sotmsg.author_id=%s AND (sotmsg.custom_time BETWEEN %s AND %s ) " \
                              "ORDER BY sotmsg.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `short_message` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            total_count = cursor.fetchone()['total']

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            records.append(record_item)
        response_data['records'] = query_result
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def export_short_message(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '信息内容', '类别', '影响品种', '备注']
        query_statement = "SELECT usertb.name,usertb.org_id,smsgtb.custom_time,smsgtb.content,smsgtb.msg_type,smsgtb.effect_variety,smsgtb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `short_message` AS smsgtb " \
                          "ON (usertb.id=%s AND usertb.id=smsgtb.author_id) AND (smsgtb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY smsgtb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['content'])
            row_content.append(record_item['msg_type'])
            row_content.append(record_item['effect_variety'])
            row_content.append(record_item['note'])

            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = table_headers
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.xlsx'.format(md5_str))
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name="短信通记录"
        )
        # file_folder, md5_str = self.generate_file_path(userid)
        # file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        # with codecs.open(file_path, 'w', 'utf_8_sig') as f:
        #     writer = csv.writer(f, dialect='excel')
        #     writer.writerow(table_headers)
        #     writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )

    def get_onduty_message(self, userid, start_date, end_date, current_page, page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '姓名','信息内容']
        header_keys = ['custom_time', 'name','content']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if userid == 0:
            query_statement = "SELECT usertb.name, odmsg.* " \
                              "FROM `onduty_message` AS odmsg INNER JOIN `user_info` AS usertb " \
                              "WHERE odmsg.author_id=usertb.id AND (odmsg.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY odmsg.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(odmsg.id) AS `total` " \
                                    "FROM `onduty_message` AS odmsg INNER JOIN `user_info` AS usertb " \
                                    "WHERE odmsg.author_id=usertb.id AND (odmsg.custom_time BETWEEN %s AND %s);"
            cursor.execute(total_count_statement,(start_date, end_date))
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT usertb.name, odmsg.* " \
                              "FROM `onduty_message` AS odmsg INNER JOIN `user_info` AS usertb " \
                              "WHERE odmsg.author_id=usertb.id AND odmsg.author_id=%s AND (odmsg.custom_time BETWEEN %s AND %s) " \
                              "ORDER BY odmsg.custom_time DESC " \
                              "LIMIT %s,%s;"
            cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
            query_result = cursor.fetchall()
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `onduty_message` " \
                                    "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
            cursor.execute(total_count_statement, (userid, start_date, end_date))
            total_count = cursor.fetchone()['total']

        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            records.append(record_item)
        response_data['records'] = query_result
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def export_onduty_message(self, userid, start_date, end_date):
        table_headers = ['日期', '部门小组', '姓名', '信息内容', '备注']
        query_statement = "SELECT usertb.name,usertb.org_id,ondmsgtb.custom_time,ondmsgtb.content,ondmsgtb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `onduty_message` AS ondmsgtb " \
                          "ON (usertb.id=%s AND usertb.id=ondmsgtb.author_id) AND (ondmsgtb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY ondmsgtb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        file_records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['content'])
            row_content.append(record_item['note'])

            file_records.append(row_content)
        file_folder, md5_str = self.generate_file_path(userid)
        file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))
        with codecs.open(file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(table_headers)
            writer.writerows(file_records)
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )

    def generate_file_path(self, userid):
        # 生成承载数据的文件
        t = "%.4f" % time.time()
        md5_hash = hashlib.md5()
        md5_hash.update(t.encode('utf-8'))
        md5_hash.update(str(userid).encode('utf-8'))
        md5_str = md5_hash.hexdigest()
        file_folder = os.path.join(BASE_DIR, 'fileStore/exports/')
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        return file_folder, md5_str
