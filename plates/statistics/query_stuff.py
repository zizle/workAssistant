# _*_ coding:utf-8 _*_
# __Author__： zizle
import datetime
import hashlib
import os
import time

from flask import jsonify, request, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.psd_handler import verify_json_web_token
from vlibs import ABNORMAL_WORK


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
        export_action = 0
        try:
            utoken = params.get('utoken')
            workuuid = int(params.get('workuuid'))
            userid = int(params.get('userid'))
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date,'%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 50))
            export_action = int(params.get('export', 0))
        except Exception as e:
            return jsonify("参数错误"), 400
        if not all([workuuid, userid, start_date, end_date]):
            return jsonify("参数错误"), 400
        request_user = verify_json_web_token(utoken)
        if not request_user or not request_user['is_admin']:
            return jsonify("INVALID USER"), 400

        if workuuid == self.ABNORMAL:
            return self.get_abnormal_work(userid,start_date,end_date, current_page,page_size)
        elif workuuid == self.MONOGRAPHIC:
            return self.get_monographic(userid,start_date,end_date,current_page,page_size)
        elif workuuid == self.INVESTMENT:
            return self.get_investment(userid,start_date,end_date,current_page,page_size)
        elif workuuid == self.INVESTRATEGY:
            return self.get_investrategory(userid,start_date,end_date,current_page,page_size)
        elif workuuid == self.ARTPUBLISH:
            return self.get_article_publish(userid,start_date,end_date,current_page,page_size)
        elif workuuid == self.SHORTMESSAGE:
            return self.get_short_message(userid,start_date,end_date,current_page,page_size)
        elif workuuid == self.ONDUTYMESSAGE:
            return self.get_onduty_message(userid,start_date,end_date,current_page,page_size)
        else:
            return jsonify("参数错误"), 400

    def get_abnormal_work(self,userid,start_date,end_date,current_page,page_size):
        start_id = current_page * page_size
        table_headers = ['日期','标题','类型','申请部门','申请者','联系电话','瑞币','补贴','备注']
        header_keys = ['custom_time','title','task_type','applied_org','applicant','tel_number','swiss_coin','allowance','note']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`task_type`,`title`,`applied_org`,`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note` " \
                          "`annex`,`annex_url` " \
                          "FROM `abnormal_work` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `abnormal_work` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement,(userid,start_date,end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['task_type'] = ABNORMAL_WORK.get(record_item['task_type'], '')
            record_item['swiss_coin'] = record_item['swiss_coin'] if record_item['swiss_coin'] else ''
            record_item['allowance'] = int(record_item['allowance'])
            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count

        return jsonify(response_data)

    def export_abnormal_word(self, userid, username, start_date,end_date):
        table_headers = ['日期','部门小组','姓名','标题', '类型', '申请部门', '申请者', '联系电话', '瑞币', '补贴', '备注']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`task_type`,`title`,`applied_org`,`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note` " \
                          "`annex`,`annex_url` " \
                          "FROM `abnormal_work` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date))
        query_result = cursor.fetchall()
        db_connection.close()
        records = list()
        for record_item in query_result:
            row_content = list()
            row_content.append()
            record_item['task_type'] = ABNORMAL_WORK.get(record_item['task_type'], '')
            record_item['swiss_coin'] = record_item['swiss_coin'] if record_item['swiss_coin'] else ''
            record_item['allowance'] = int(record_item['allowance'])
            row_content.append()
            records.append(row_content)

        file_folder,file_path = self.generate_file_path(username)


        return send_from_directory(directory=file_folder, filename=file_path,
                                   as_attachment=True, attachment_filename='statistics_abnormalwork.csv'
                                   )


    def get_monographic(self,userid,start_date,end_date,current_page,page_size):
        start_id = current_page * page_size
        table_headers = ['日期', '题目', '字数', '外发情况', '等级', '得分', '备注']
        header_keys = ['custom_time', 'title', 'words', 'is_publish', 'level', 'score', 'note']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`title`,`words`,`is_publish`,`level`,`score`,`note` " \
                          "FROM `monographic` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `monographic` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
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

    def get_investment(self,userid,start_date,end_date,current_page,page_size):
        print('投资方案')
        start_id = current_page * page_size
        table_headers = ['日期','标题','品种','方向','实建日期','实建均价','实建手数','实出均价','止损均价','有效期','外发','结果']
        header_keys = ['custom_time', 'title','variety', 'direction', 'build_time', 'build_price', 'build_hands', 'out_price',
                       'cutloss_price','expire_time','is_publish','profit']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`title`,`variety_id`,`contract`,`direction`,`build_time`,`build_price`,`build_hands` " \
                          "`out_price`,`cutloss_price`,`expire_time`,`is_publish`,`profit`,`note` " \
                          "FROM `investment` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `investment` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:

            record_item['build_time'] = record_item['build_time'].strftime('%Y-%m-%d %H:%M')
            record_item['expire_time'] = record_item['expire_time'].strftime('%Y-%m-%d %H:%M')
            record_item['variety'] = variety_dict.get(record_item['variety_id'],'') + str(record_item['contract'])
            record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
            record_item['build_price'] = int(record_item['build_price'])
            record_item['out_price'] = int(record_item['out_price'])
            record_item['cutloss_price'] = int(record_item['cutloss_price'])
            record_item['profit'] = int(record_item['profit'])

            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def get_investrategory(self,userid,start_date,end_date,current_page,page_size):
        print("投顾策略")
        start_id = current_page * page_size
        table_headers = ['日期','策略内容','品种','方向','手数','策略开仓',	'策略平仓','结果']
        header_keys = ['custom_time', 'content', 'variety','direction', 'hands', 'open_position', 'close_position','profit']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`content`,`variety_id`,`contract`,`direction`,`hands`,`open_position`,`close_position`,`profit` " \
                          "FROM `investrategy` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        # 准备品种信息
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `investrategy` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        records = list()
        for record_item in query_result:
            record_item['variety'] = variety_dict.get(record_item['variety_id'],'') + str(record_item['contract'])
            record_item['profit'] = int(record_item['profit'])

            records.append(record_item)
        response_data['records'] = records
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def get_article_publish(self,userid,start_date,end_date,current_page,page_size):
        start_id = current_page * page_size
        table_headers = ['日期','题目','发表/采访媒体','稿件形式','字数','审核人','收入奖励','合作人','备注']
        header_keys = ['custom_time', 'title', 'media_name', 'rough_type', 'words', 'checker', 'allowance','partner','note']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`title`,`media_name`,`rough_type`,`words`,`checker`,`allowance`,`partner`,`note` " \
                          "FROM `article_publish` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `article_publish` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        # records = list()
        # for record_item in query_result:
        #
        #     records.append(record_item)
        response_data['records'] = query_result
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def get_short_message(self,userid,start_date,end_date,current_page,page_size):
        start_id = current_page * page_size
        table_headers = ['日期','信息内容','类别','影响品种','备注']
        header_keys = ['custom_time', 'content', 'msg_type', 'effect_variety', 'note']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`content`,`msg_type`,`effect_variety`,`note` " \
                          "FROM `short_message` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `short_message` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        # records = list()
        # for record_item in query_result:
        #
        #     records.append(record_item)
        response_data['records'] = query_result
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)

    def get_onduty_message(self,userid,start_date,end_date,current_page,page_size):
        start_id = current_page * page_size
        table_headers = ['日期','信息内容']
        header_keys = ['custom_time', 'content']
        query_statement = "SELECT DATE_FORMAT(`custom_time`,'%%Y-%%m-%%d') AS `custom_time`, " \
                          "`content`,`note` " \
                          "FROM `onduty_message` WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, (userid, start_date, end_date, start_id, page_size))
        query_result = cursor.fetchall()
        # 总数
        total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `onduty_message` " \
                                "WHERE `author_id`=%s AND `custom_time` BETWEEN %s AND %s;"
        cursor.execute(total_count_statement, (userid, start_date, end_date))
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)
        db_connection.close()
        response_data = dict()
        # records = list()
        # for record_item in query_result:
        #
        #     records.append(record_item)
        response_data['records'] = query_result
        response_data['table_headers'] = table_headers
        response_data['header_keys'] = header_keys
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['total_count'] = total_count
        return jsonify(response_data)


    def generate_file_path(self,userid):
        # 生成承载数据的文件
        t = "%.4f" % time.time()
        md5_hash = hashlib.md5()
        md5_hash.update(t.encode('utf-8'))
        md5_hash.update(str(userid).encode('utf-8'))
        md5_str = md5_hash.hexdigest()
        file_folder = os.path.join(BASE_DIR, 'fileStore/exports/')
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        return (file_folder, os.path.join(file_folder, '{}.csv'.format(md5_str)))
