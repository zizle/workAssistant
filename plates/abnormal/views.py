# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
import hashlib
import os
import time

import pandas as pd
import xlrd
from flask import jsonify, current_app, request, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.file_handler import hash_file_name
from utils.psd_handler import verify_json_web_token
from vlibs import ABNORMAL_WORK, ORGANIZATIONS


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
        # 原生sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,abworktb.id,abworktb.custom_time,abworktb.task_type," \
                               "abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number," \
                               "abworktb.swiss_coin,abworktb.allowance,abworktb.note,abworktb.annex,abworktb.annex_url " \
                               "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                               "usertb.id=%s AND usertb.id=abworktb.author_id AND (abworktb.custom_time BETWEEN %s AND %s) " \
                               "ORDER BY abworktb.custom_time DESC " \
                               "limit %s,%s;"

        # 内联查询另一写法:where子句(INNER JOIN->','(逗号); ON->WHERE)
        # "SELECT usertb.name,abworktb.title FROM `user_info` AS usertb,`abnormal_work`AS abworktb WHERE usertb.id=%s AND usertb.id=abworktb.worker;"
        # 连表查询语句两种方式都可以去除'AS'关键字

        cursor.execute(inner_join_statement,(user_id, start_date, end_date, start_id, page_size))
        abworks = cursor.fetchall()
        # print("内连接查询结果", abworks)
        # 查询总条数
        inner_join_statement = "SELECT COUNT(abworktb.id) as total FROM `user_info` AS usertb INNER JOIN `abnormal_work`AS abworktb " \
                               "ON usertb.id=%s AND usertb.id=abworktb.author_id AND (abworktb.custom_time BETWEEN %s AND %s);"

        cursor.execute(inner_join_statement, (user_id, start_date, end_date))
        total_ = cursor.fetchone()
        total_count = total_['total']  # 计算总页数
        db_connection.close()
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
            work_item['allowance'] = int(work_item['allowance'])
            response_data['abworks'].append(work_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(abworks)
        response_data['total_count'] = total_count

        return jsonify(response_data)

    def post(self):
        body_data = request.form
        worker_id = body_data.get('worker_id', None)
        if not worker_id:
            return jsonify("参数错误，HAS NO WORKERID.")
        # 查找用户
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_user_statement = "SELECT `id`,`name`,`is_admin` FROM `user_info` WHERE `id`=%s;"
        cursor.execute(select_user_statement, worker_id)
        user_obj = cursor.fetchone()
        # 管理员不给添加信息
        if user_obj['is_admin']:
            return jsonify('请不要使用用管理员用户添加记录.')
        # 不为空的信息判断
        task_type = body_data.get('task_type', 0)
        task_type_text = ABNORMAL_WORK.get(int(task_type), 0)
        title = body_data.get('work_title', False)
        if not task_type_text or not title:
            return jsonify("参数错误,NOT FOUND TASKTYPE AND TITLE"), 400
        # 组织信息
        custom_time = datetime.datetime.strptime(body_data.get('work_date'), '%Y-%m-%d')
        worker = user_obj['id']
        sponsor = body_data.get('sponsor', '')
        applied_org = body_data.get('applicat_org', '')
        applicant = body_data.get('application_person', '')
        tel_number = body_data.get('link_number', '')
        swiss_coin = body_data.get('ruibi_count', 0)
        allowance = body_data.get('income_allowance', 0)
        note = body_data.get('work_note', '')
        partner = body_data.get('partner_name', '')
        # 读取文件
        annex_file = request.files.get('annex_file', None)
        if not annex_file:
            filename = ''
            annex_url = ''
            file_path = ''
        else:
            # 文件名hash
            filename = annex_file.filename
            hash_name = hash_file_name(filename)
            # 获取保存的位置
            file_path = os.path.join(BASE_DIR, "fileStore/abwork/" + hash_name)
            annex_url = "fileStore/abwork/" + hash_name  # 数据库路径
            annex_file.save(file_path)
        # 存入数据库
        save_work_statement = "INSERT INTO `abnormal_work`" \
                              "(`custom_time`,`author_id`,`task_type`,`title`,`sponsor`,`applied_org`," \
                              "`applicant`,`tel_number`,`swiss_coin`,`allowance`,`note`,`partner`,`annex`,`annex_url`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            swiss_coin = int(swiss_coin) if swiss_coin else 0
            allowance = float(allowance) if allowance else 0
            cursor.execute(save_work_statement,
                           (custom_time, worker, task_type, title, sponsor, applied_org,
                            applicant, tel_number, swiss_coin, allowance, note, partner, filename, annex_url)
                           )
            db_connection.commit()

        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("写入非常态工作错误:" + str(e))
            # 保存错误得删除已保存的文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify("参数错误!无法保存。"), 400
        else:
            db_connection.close()
            return jsonify("保存成功!"), 201


# 文件数据上传(含总模板下载)
class FileHandlerAbnormalWorkView(MethodView):

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
        db_connection.close()
        # 管理员不给添加信息
        if user_obj['is_admin']:
            return jsonify('请不要使用用管理员用户添加记录.')
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
        message = "表格列数据类型有误,请检查后上传."
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
                    try:
                        record_row.append(xlrd.xldate_as_datetime(row_content[0], 0))
                    except Exception as e:
                        message = "第一列【日期】请使用日期格式上传."
                        raise ValueError(e)
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
            current_app.logger.error('{}上传非常态工作错误:{}'.format(user_obj['name'], e))
            return jsonify(message), 400

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


# 导出数据到文件
class ExportAbnormalWorkView(MethodView):
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

        # 查询当前用户的非常态工作记录
        query_statement = "SELECT usertb.name,usertb.org_id,abworktb.custom_time,abworktb.task_type,abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number,abworktb.swiss_coin,abworktb.allowance,abworktb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb " \
                          "ON usertb.id=%s AND usertb.id=abworktb.author_id AND (abworktb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY abworktb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
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
            row_content.append(ABNORMAL_WORK.get(record_item['task_type'], ''))
            row_content.append(record_item['title'])
            row_content.append(record_item['sponsor'])
            row_content.append(record_item['applied_org'])
            row_content.append(record_item['applicant'])
            row_content.append(record_item['tel_number'])
            row_content.append(record_item['swiss_coin'] if record_item['swiss_coin'] else '')
            row_content.append(int(record_item['allowance']))
            row_content.append(record_item['note'])
            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = ['日期', '部门小组','姓名', '任务类型', '主题/标题', '主办方', '申请部门/受用单位', '申请者', '联系电话', '瑞币情况', '收入补贴','备注']
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name='非常态工作记录'
        )
        # 将文件返回
        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )


# 修改记录
class RetrieveAbWorkView(MethodView):
    def get(self, work_id):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT usertb.name,usertb.org_id,abworktb.custom_time,abworktb.task_type,abworktb.title," \
                           "abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number,abworktb.swiss_coin," \
                           "abworktb.allowance,abworktb.note,abworktb.annex,abworktb.annex_url " \
                           "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                           "abworktb.id=%s AND abworktb.author_id=usertb.id;"
        cursor.execute(select_statement, work_id)
        work_item = cursor.fetchone()
        work_item['custom_time'] = work_item['custom_time'].strftime('%Y-%m-%d')
        work_item['allowance'] = int(work_item['allowance'])
        work_item['org_name'] = ORGANIZATIONS.get(int(work_item['org_id']), '')
        work_item['task_type_name'] = ABNORMAL_WORK.get(int(work_item['task_type']), '')
        work_item['work_types'] = ABNORMAL_WORK
        db_connection.close()
        return jsonify(work_item)

    def put(self, work_id):
        body_data = request.form
        utoken = body_data.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['uid']
        # 不为空的信息判断
        task_type = body_data.get('task_type', 0)
        task_type_text = ABNORMAL_WORK.get(int(task_type), 0)
        title = body_data.get('title', False)
        if not task_type_text or not title:
            return jsonify("参数错误,NOT FOUND TASKTYPE AND TITLE"), 400
        # 组织信息
        custom_time = datetime.datetime.strptime(body_data.get('custom_time'), '%Y-%m-%d')
        task_type = body_data.get('task_type', 0)
        sponsor = body_data.get('sponsor', '')
        applied_org = body_data.get('applied_org', '')
        applicant = body_data.get('applicant', '')
        tel_number = body_data.get('tel_number', '')
        swiss_coin = body_data.get('swiss_coin', 0)
        allowance = body_data.get('allowance', 0)
        note = body_data.get('note', '')
        partner = body_data.get('partner_name', '')
        filename = body_data.get('annex','')
        annex_url = body_data.get('annex_url','')
        old_annex_url = annex_url  # 保存旧文件路径待删除文件
        # 读取文件
        annex_file = request.files.get('annex_file', None)
        file_path = ''
        if annex_file:
            filename = annex_file.filename
            hash_name = hash_file_name(filename)
            # 获取保存的位置
            file_path = os.path.join(BASE_DIR, "fileStore/abwork/" + hash_name)
            annex_url = "fileStore/abwork/" + hash_name  # 数据库路径
            annex_file.save(file_path)
        # 存入数据库
        update_statement = "UPDATE `abnormal_work` SET " \
                            "`custom_time`=%s,`task_type`=%s,`title`=%s,`sponsor`=%s,`applied_org`=%s," \
                            "`applicant`=%s,`tel_number`=%s,`swiss_coin`=%s,`allowance`=%s,`note`=%s,`partner`=%s," \
                            "`annex`=%s,`annex_url`=%s " \
                            "WHERE `id`=%s AND `author_id`=%s;"
        db_connection = MySQLConnection()
        try:
            swiss_coin = int(swiss_coin) if swiss_coin else 0
            allowance = float(allowance) if allowance else 0
            cursor = db_connection.get_cursor()
            cursor.execute(update_statement,
                           (custom_time, task_type, title, sponsor, applied_org,
                            applicant, tel_number, swiss_coin, allowance, note, partner,
                            filename,annex_url,
                            work_id, user_id)
                           )
            db_connection.commit()
            # 删除原来的文件
            old_file_path = os.path.join(BASE_DIR, old_annex_url)
            if annex_file and os.path.isfile(old_file_path):
                os.remove(old_file_path)
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("修改非常态工作记录错误:" + str(e))
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify("参数错误!无法修改。"), 400
        else:
            db_connection.close()
            return jsonify("修改成功!")

    def delete(self, work_id):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        db_connection = MySQLConnection()
        annex_file_path = None
        try:
            cursor = db_connection.get_cursor()
            # 查询当前记录是否有附件
            annex_query_statement = "SELECT `annex_url` FROM `abnormal_work` WHERE `id`=%d;" % work_id
            cursor.execute(annex_query_statement)
            annex_file = cursor.fetchone()
            if annex_file:
                annex_file_path = annex_file['annex_url']
            user_id = int(user_info['uid'])
            delete_statement = "DELETE FROM `abnormal_work` WHERE `id`=%d AND `author_id`=%d;" % (work_id, user_id)
            lines_changed = cursor.execute(delete_statement)
            db_connection.commit()
            if lines_changed <= 0:
                raise ValueError("删除错误,没有记录被删除>…<")
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify(str(e))
        else:
            db_connection.close()
            if annex_file_path:
                file_local_path = os.path.join(BASE_DIR, annex_file_path)
                if os.path.isfile(file_local_path):
                    os.remove(file_local_path)
            return jsonify("删除成功^.^!")
