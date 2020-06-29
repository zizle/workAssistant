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


class ShortMessageView(MethodView):
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
            return jsonify("参数错误:INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,smsgtb.id,smsgtb.custom_time,smsgtb.content,smsgtb.msg_type,smsgtb.effect_variety,smsgtb.note " \
                               "FROM `user_info` AS usertb INNER JOIN `short_message` AS smsgtb " \
                               "ON usertb.id=%s AND usertb.id=smsgtb.author_id AND (smsgtb.custom_time BETWEEN %s AND %s) " \
                               "ORDER BY smsgtb.custom_time DESC " \
                               "limit %s,%s;"
        cursor.execute(inner_join_statement, (user_id, start_date, end_date, start_id, page_size))
        result_records = cursor.fetchall()
        # print("内连接查短讯通结果", result_records)

        # 查询总条数
        count_statement = "SELECT COUNT(smsgtb.id) as total FROM `user_info` AS usertb INNER JOIN `short_message`AS smsgtb " \
                          "ON usertb.id=%s AND usertb.id=smsgtb.author_id AND (smsgtb.custom_time BETWEEN %s AND %s);"
        cursor.execute(count_statement, (user_id, start_date, end_date))
        # print("条目记录：", cursor.fetchone()) 打开注释下行将无法解释编译

        # 计算总页数
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['records'] = list()
        for record_item in result_records:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), "未知")
            response_data['records'].append(record_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(result_records)
        response_data['total_count'] = total_count

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
        if not content:
            return jsonify("参数错误,NOT FOUND CONTENT."), 400

        # 组织信息
        custom_time = body_data.get('custom_time')
        custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d') if custom_time else datetime.datetime.now()

        author_id = user_obj['id']
        msg_type = body_data.get('msg_type', '')
        effect_variety = body_data.get('effect_variety', '')
        note = body_data.get('work_note', '')
        # 存入数据库
        save_invest_statement = "INSERT INTO `short_message`" \
                              "(`custom_time`,`author_id`,`content`,`msg_type`,`effect_variety`,`note`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型执行语句
            cursor.execute(save_invest_statement,
                           (custom_time, author_id, content, msg_type, effect_variety, note)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入短讯通记录错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201


class FileHandlerShortMessageView(MethodView):

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
        # 文件内容
        file_contents = file.read()
        file_contents = xlrd.open_workbook(file_contents=file_contents)

        # 导入名称为“短讯通记录”的表
        table_data = file_contents.sheet_by_name('短讯通记录')

        # 检查sheet1是否导入完毕
        status = file_contents.sheet_loaded('短讯通记录')
        if not status:
            return jsonify('文件数据导入失败'), 400
        # 读取第一行数据
        first_row = table_data.row_values(0)
        # 格式判断
        if first_row != ["日期","信息内容","类别","影响品种","备注"]:
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
                    record_row.append(str(row_content[2]))
                    record_row.append(str(row_content[3]))
                    record_row.append(str(row_content[4]))
                    ready_to_save.append(record_row)
            if len(ready_to_save) == 0:
                raise ValueError('没有读取到数据.')
            new_df = pd.DataFrame(ready_to_save)
            new_df.columns = ['custom_time', 'author_id', 'content', 'msg_type','effect_variety','note']
            save_list = self.drop_duplicates(new_df, user_id)
            # print('保存的数据:', save_list)
            if len(save_list) > 0:
                message = "数据保存成功!"
                insert_statement = "INSERT INTO `short_message`" \
                                   "(`custom_time`,`author_id`,`content`,`msg_type`,`effect_variety`,`note`)" \
                                   " VALUES (%s,%s,%s,%s,%s,%s);"
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
        query_statement = "SELECT `custom_time`,`author_id`,`content`,`msg_type`,`effect_variety`,`note` " \
                          "FROM `short_message` WHERE `author_id`=%s;"
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


class RetrieveShortMessageView(MethodView):
    def get(self, rid):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT usertb.name,usertb.org_id,smsgtb.id,smsgtb.custom_time,smsgtb.content,smsgtb.msg_type,smsgtb.effect_variety,smsgtb.note " \
                           "FROM `user_info` AS usertb INNER JOIN `short_message` AS smsgtb ON " \
                           "smsgtb.id=%d AND usertb.id=smsgtb.author_id;" %rid
        cursor.execute(select_statement)
        record_item = cursor.fetchone()
        if record_item:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), "未知")
        else:
            record_item = {}
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
        if not content:
            return jsonify("参数错误,NOT FOUND CONTENT."), 400

        # 组织信息
        custom_time = record_info.get('custom_time')
        msg_type = record_info.get('msg_type', '')
        effect_variety = record_info.get('effect_variety', '')
        note = record_info.get('note', '')
        # 存入数据库
        update_sms_statement = "UPDATE `short_message` SET " \
                                "`custom_time`=%s,`content`=%s,`msg_type`=%s,`effect_variety`=%s,`note`=%s " \
                                "WHERE `id`=%s AND `author_id`=%s;" \

        try:
            # 转换类型执行语句
            user_id = int(user_id)
            custom_time = datetime.datetime.strptime(custom_time,'%Y-%m-%d') if custom_time else datetime.datetime.now()
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            cursor.execute(update_sms_statement,
                           (custom_time, content, msg_type, effect_variety, note, rid, user_id)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("修改短讯通记录错误:" + str(e))
            return jsonify("参数错误!无法修改。"), 400
        else:
            return jsonify("修改成功!")

    def delete(self, rid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        db_connection = MySQLConnection()
        try:
            user_id = int(user_info['uid'])
            delete_statement = "DELETE FROM `short_message` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (
                               rid, user_id)
            cursor = db_connection.get_cursor()
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
            return jsonify("删除成功^.^!")


class ShortMessageExportView(MethodView):
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

        query_statement = "SELECT usertb.name,usertb.org_id,smsgtb.custom_time,smsgtb.content,smsgtb.msg_type,smsgtb.effect_variety,smsgtb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `short_message` AS smsgtb ON " \
                          "usertb.id=%s AND usertb.id=smsgtb.author_id AND (smsgtb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY smsgtb.custom_time ASC;"
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
            row_content.append(record_item['content'])
            row_content.append(record_item['msg_type'])
            row_content.append(record_item['effect_variety'])
            row_content.append(record_item['note'])
            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = ['日期', '部门小组', '姓名', '信息内容', '类别', '影响品种','备注']
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name='短讯通记录'
        )

        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )

