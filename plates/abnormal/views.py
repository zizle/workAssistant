# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
from flask import jsonify,current_app, request
from flask.views import MethodView
from db import MySQLConnection
from vlibs import ABNORMAL_WORK
from utils.psd_handler import verify_json_web_token

# # 蓝图的测试视图
# class testView(MethodView):
#     def get(self):
#         logger = current_app.logger  # 必须卸载请求内部，此时请求发起，上下文AppContext入栈才有current_app
#         try:
#             raise RuntimeError("RuntimeError错误")
#         except Exception as e:
#             logger.debug("debug:" + str(e))
#         print("进入视图函数")
#         # 测试写入日志
#         logger.info("这是一个info日志")
#         logger.error("这是一个error日志")
#         logger.warning('这是一个warning日志')
#
#         return jsonify("这是非常态工作任务的GET测试视图"), 200

class AbnormalWorkView(MethodView):
    def get(self):
        params = request.args
        # 解析用户信息
        token = params.get('utoken')
        user_info = verify_json_web_token(token)
        if not user_info:
            return jsonify("您的登录已过期,请重新登录查看.")
        user_id = user_info['uid']
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 30))
        except Exception:
            return jsonify("参数错误:INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        # # 单表查询当前页数据
        # select_statement = "SELECT * FROM `abnormal_work` limit %d,%d;" % (start_id,page_size)

        # 原生sql内联查询
        inner_join_statement = "SELECT usertb.name,abworktb.work_time,abworktb.task_type,abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number,abworktb.swiss_coin,abworktb.allowance,abworktb.note,orgtb.name as org_name " \
                               "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                               "usertb.id=%d AND usertb.id=abworktb.worker INNER JOIN `organization_group` AS orgtb ON orgtb.id=usertb.org_id " \
                               "limit %d,%d;"% (user_id,start_id,page_size)
        # 内联查询where子句(INNER JOIN-> ','(逗号); ON->WHERE)
        # "SELECT usertb.name,abworktb.title FROM `user_info` AS usertb,`abnormal_work`AS abworktb WHERE usertb.id=%s AND usertb.id=abworktb.worker;"
        cursor.execute(inner_join_statement)
        abworks = cursor.fetchall()
        print("内连接查询结果",abworks)

        # 查询总条数
        inner_join_statement = "SELECT COUNT(*) as total FROM `user_info` AS usertb INNER JOIN `abnormal_work`AS abworktb ON usertb.id=%s AND usertb.id=abworktb.worker;"
        cursor.execute(inner_join_statement,user_id)
        # print("条目记录：", cursor.fetchone()) 打开注释下行将无法解释编译

        # 计算总页数
        total_count = cursor.fetchone()['total']
        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['abworks'] = list()
        for work_item in abworks:
            work_item['work_time'] = work_item['work_time'].strftime('%Y-%m-%d')
            work_item['task_type'] = ABNORMAL_WORK.get(work_item['task_type'],'')
            response_data['abworks'].append(work_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(abworks)

        return jsonify(response_data)

    def post(self):
        body_data = request.json
        worker_id = body_data.get('worker_id', None)
        if not worker_id:
            return jsonify("参数错误，HAS NO WORKERID.")
        # 查找用户
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_user_statement = "SELECT `id`,`name` FROM `user_info` WHERE `id`=%s;"
        cursor.execute(select_user_statement, worker_id)
        user_obj = cursor.fetchone()
        # 不为空的信息判断
        task_type = body_data.get('task_type', 0)
        task_type_text = ABNORMAL_WORK.get(int(task_type), 0)
        title = body_data.get('work_title', False)
        if not task_type_text or not title:
            return jsonify("参数错误,NOT FOUND TASKTYPE AND TITLE"), 400
        # 组织信息
        work_time = datetime.datetime.strptime(body_data.get('work_date'), '%Y-%m-%d')
        worker = user_obj['id']
        sponsor = body_data.get('sponser', '')
        applied_org = body_data.get('applicat_org', '')
        applicant = body_data.get('application_person', '')
        tel_number = body_data.get('link_number', '')
        swiss_coin = body_data.get('ruibi_count', 0)
        allowance = body_data.get('income_allowance', 0)
        note = body_data.get('work_note', '')
        partner = body_data.get('partner_name', '')
        # 存入数据库
        save_work_statement = "INSERT INTO `abnormal_work`" \
                              "(`work_time`,`worker`,`task_type`,`title`,`sponsor`,`applied_org`," \
                              "`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note`,`partner`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            cursor.execute(save_work_statement,
                           (work_time,worker,task_type,title,sponsor,applied_org,
                            applicant,tel_number,swiss_coin,allowance,note,partner)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入非常态工作错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201
