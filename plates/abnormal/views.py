# _*_ coding:utf-8 _*_
# Author: zizle
import os
import xlrd
import datetime
from flask import jsonify, current_app, request, Response
from flask.views import MethodView
from db import MySQLConnection
from vlibs import ABNORMAL_WORK, ORGANIZATIONS
from utils.psd_handler import verify_json_web_token
from settings import BASE_DIR


# 数据提交与查询
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
        # 原生sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,abworktb.custom_time,abworktb.task_type,abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number,abworktb.swiss_coin,abworktb.allowance,abworktb.note " \
                               "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                               "usertb.id=%d AND usertb.id=abworktb.author_id ORDER BY abworktb.custom_time DESC " \
                               "limit %d,%d;" % (user_id, start_id, page_size)

        # 内联查询另一写法:where子句(INNER JOIN->','(逗号); ON->WHERE)
        # "SELECT usertb.name,abworktb.title FROM `user_info` AS usertb,`abnormal_work`AS abworktb WHERE usertb.id=%s AND usertb.id=abworktb.worker;"
        # 连表查询语句两种方式都可以去除'AS'关键字

        cursor.execute(inner_join_statement)
        abworks = cursor.fetchall()
        print("内连接查询结果", abworks)

        # 查询总条数
        inner_join_statement = "SELECT COUNT(*) as total FROM `user_info` AS usertb INNER JOIN `abnormal_work`AS abworktb ON usertb.id=%s AND usertb.id=abworktb.author_id;"
        cursor.execute(inner_join_statement, user_id)
        # print("条目记录：", cursor.fetchone()) 打开注释，下行将无法解释编译
        total_count = cursor.fetchone()['total']  # 计算总页数
        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['abworks'] = list()
        for work_item in abworks:
            work_item['custom_time'] = work_item['custom_time'].strftime('%Y-%m-%d')
            work_item['task_type'] = ABNORMAL_WORK.get(work_item['task_type'], '')
            work_item['org_name'] = ORGANIZATIONS.get(int(work_item['org_id']), '未知')
            work_item['swiss_coin'] = work_item['swiss_coin'] if work_item['swiss_coin'] else ''
            work_item['allowance'] = work_item['allowance'] if work_item['allowance'] else ''
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
        custom_time = datetime.datetime.strptime(body_data.get('work_date'), '%Y-%m-%d')
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
                              "(`custom_time`,`author_id`,`task_type`,`title`,`sponsor`,`applied_org`," \
                              "`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note`,`partner`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            swiss_coin = int(swiss_coin) if swiss_coin else 0
            allowance = int(allowance) if allowance else 0
            cursor.execute(save_work_statement,
                           (custom_time, worker, task_type, title, sponsor, applied_org,
                            applicant, tel_number, swiss_coin, allowance, note, partner)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入非常态工作错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201


# 文件数据上传(含总模板下载)
class FileHandlerAbnormalWorkView(MethodView):

    def post(self):
        # 获取当前用户的信息
        user_id = request.form.get('uid')
        file = request.files.get('file', None)
        if not file or not user_id:
            return jsonify('参数错误,NOT FILE OR UID'), 400
        # 准备任务类型字典
        task_type_dict = {value: key for key, value in ABNORMAL_WORK.items()}
        # 文件内容
        file_contents = file.read()

        file_contents = xlrd.open_workbook(file_contents=file_contents)
        # table_data = file_contents.sheets()[0]
        # 导入名称为“非常态工作”的表
        table_data = file_contents.sheet_by_name('非常态工作')

        # 检查sheet1是否导入完毕
        status = file_contents.sheet_loaded('非常态工作')
        if not status:
            return jsonify('文件数据导入失败'), 400
        # 读取第一行数据
        first_row = table_data.row_values(0)
        # 格式判断
        if first_row != [
            "日期", "任务类型(报告演讲,内外培训,材料撰写,协同开发,课件,客户服务,调研组织,参与外部活动,其它)",
            "主题/标题", "主办方", "申请部门或受用单位","申请者或受用人", "联系电话", "瑞币情况", "收入补贴", "备注"
        ]:
            return jsonify("表格格式有误,请修正."), 400
        nrows = table_data.nrows
        # ncols = table_data.ncols
        # print("行数：", nrows, "列数：", ncols)
        # 获取数据
        ready_to_save = list()  # 准备保存的数据集
        start_data_in = False
        # 组织数据写入数据库
        try:
            for row in range(nrows):
                row_content = table_data.row_values(row)
                # 找到需要开始上传的数据
                if str(row_content[0]).strip() == 'start':
                    start_data_in = True
                    continue  # 继续下一行
                if str(row_content[0]).strip() == 'end':
                    start_data_in = False
                    continue
                if start_data_in:
                    record_row = list()  # 每行记录
                    # 转换数据类型
                    record_row.append(xlrd.xldate_as_datetime(row_content[0], 0))
                    record_row.append(user_id)
                    # 处理任务类型
                    task_type_id = task_type_dict.get(str(row_content[1].strip()), '')
                    record_row.append(int(task_type_id))
                    record_row.append(str(row_content[2]))
                    record_row.append(str(row_content[3]))
                    record_row.append(str(row_content[4]))
                    record_row.append(str(row_content[5]))
                    record_row.append(str(row_content[6]))
                    record_row.append(int(row_content[7]) if row_content[7] else 0)
                    record_row.append(int(row_content[8]) if row_content[8] else 0)
                    record_row.append(str(row_content[9]))
                    ready_to_save.append(record_row)
        except Exception as e:
            return jsonify("表格列数据类型有误,请检查后上传.")

        insert_statement = "INSERT INTO `abnormal_work`" \
                           "(`custom_time`,`author_id`,`task_type`,`title`,`sponsor`,`applied_org`," \
                           "`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note`)" \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        # print('准备保存：', ready_to_save)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.executemany(insert_statement, ready_to_save)
        # print("获取{}行数据".format(len(ready_to_save)))
        db_connection.commit()
        db_connection.close()

        return jsonify("数据保存成功!")
