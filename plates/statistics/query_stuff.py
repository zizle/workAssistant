# _*_ coding:utf-8 _*_
# __Author__： zizle
import datetime

from flask import jsonify, request
from flask.views import MethodView

from db import MySQLConnection
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
            return self.get_monographic(userid,start_date,end_date)
        elif workuuid == self.INVESTMENT:
            return self.get_investment(userid,start_date,end_date)
        elif workuuid == self.INVESTRATEGY:
            return self.get_investrategory(userid,start_date,end_date)
        elif workuuid == self.ARTPUBLISH:
            return self.get_article_publish(userid,start_date,end_date)
        elif workuuid == self.SHORTMESSAGE:
            return self.get_short_message(userid,start_date,end_date)
        elif workuuid == self.ONDUTYMESSAGE:
            return self.get_onduty_message(userid,start_date,end_date)
        else:
            return jsonify("参数错误"), 400

    def get_abnormal_work(self,userid,start_date,end_date,current_page,page_size):
        print('非常态工作')
        start_id = current_page * page_size
        table_headers = ['日期','类型','标题','申请部门','申请者','联系电话','瑞币','补贴','备注']
        header_keys = ['custom_time','task_type','title','applied_org','applicant','tel_number','swiss_coin','allowance','note']
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


    def get_monographic(self,userid,start_date,end_date):
        print('专题研究')
        return jsonify("ok")

    def get_investment(self,userid,start_date,end_date):
        print('投资方案')
        return jsonify("ok")

    def get_investrategory(self,userid,start_date,end_date):
        print("投顾策略")
        return jsonify('ok')

    def get_article_publish(self,userid,start_date,end_date):
        print('文章发表记录')
        return jsonify('ok')

    def get_short_message(self,userid,start_date,end_date):
        print('短讯通')
        return jsonify('ok')

    def get_onduty_message(self,userid,start_date,end_date):
        print("值班信息")
        return jsonify('ok')



