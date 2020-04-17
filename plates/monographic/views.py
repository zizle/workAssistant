# _*_ coding:utf-8 _*_
# Author: zizle
import codecs
import csv
import datetime
import hashlib
import os
import time

from flask import jsonify, request, current_app, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.file_handler import hash_file_name
from utils.psd_handler import verify_json_web_token
from vlibs import ORGANIZATIONS


class MonographicView(MethodView):
    def get(self):
        params = request.args
        # 解析用户信息
        token = params.get('utoken')
        user_info = verify_json_web_token(token)
        if not user_info:
            return jsonify("您的登录已过期,请重新登录查看.")
        user_id = user_info['uid']
        # print(user_id)
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 30))
        except Exception:
            return jsonify("参数错误:INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,mgpctb.id,mgpctb.custom_time,mgpctb.title,mgpctb.words,mgpctb.is_publish,mgpctb.level,mgpctb.score,mgpctb.note " \
                               "FROM `user_info` AS usertb INNER JOIN `monographic` AS mgpctb ON " \
                               "usertb.id=%d AND usertb.id=mgpctb.author_id ORDER BY mgpctb.custom_time DESC " \
                               "limit %d,%d;" % (user_id, start_id, page_size)
        cursor.execute(inner_join_statement)
        result_records = cursor.fetchall()
        # print("内连接查询专题研究结果", result_records)

        # 查询总条数
        count_statement = "SELECT COUNT(*) as total FROM `user_info` AS usertb INNER JOIN `monographic`AS mgpctb ON usertb.id=%s AND usertb.id=mgpctb.author_id;"
        cursor.execute(count_statement, user_id)
        # print("条目记录：", cursor.fetchone()) 打开注释下行将无法解释编译

        # 计算总页数
        total_count = cursor.fetchone()['total']
        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['records'] = list()
        for record_item in result_records:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']),'未知')
            record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
            response_data['records'].append(record_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(result_records)
        return jsonify(response_data)

    def post(self):
        body_data = request.form
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
        title = body_data.get('title', False)
        if not title:
            return jsonify("参数错误,NOT FOUND TITLE"), 400
        # 组织信息
        upload_time = body_data.get('upload_time')
        upload_time = datetime.datetime.strptime(upload_time, '%Y-%m-%d') if upload_time else datetime.datetime.now()
        author_id = user_obj['id']
        words = body_data.get('words', 0)
        is_publish = body_data.get('is_publish', False)
        level = body_data.get('level', 'D')
        score = body_data.get('score', 0)
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
            file_path = os.path.join(BASE_DIR, "fileStore/monographic/" + hash_name)
            annex_url = "fileStore/monographic/" + hash_name  # 数据库路径
            annex_file.save(file_path)
        # 存入数据库
        save_work_statement = "INSERT INTO `monographic`" \
                              "(`custom_time`,`author_id`,`title`,`words`,`is_publish`,`level`," \
                              "`score`,`note`,`partner`,`annex`,`annex_url`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型
            words = int(words) if words else 0
            score = int(score) if score else 0
            is_publish = 1 if is_publish else 0
            cursor.execute(save_work_statement,
                           (upload_time, author_id,title, words,is_publish,level,score,note,partner,filename,annex_url)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入专题研究记录错误:" + str(e))
            # 保存错误得删除已保存的文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201
        

# 导出数据到文件
class MonographicExportView(MethodView):
    def get(self):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify("登录已过期!刷新网页重新登录."), 400
        # 查询当前用户的专题研究记录
        query_statement = "SELECT usertb.name,usertb.org_id,mgpctb.custom_time,mgpctb.title,mgpctb.words,mgpctb.is_publish,mgpctb.level,mgpctb.score,mgpctb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `monographic` AS mgpctb ON " \
                          "usertb.id=%s AND usertb.id=mgpctb.author_id ORDER BY mgpctb.custom_time ASC;"

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, user_info['uid'])
        records_all = cursor.fetchall()
        # 生成承载数据的文件
        t = "%.4f" % time.time()
        md5_hash = hashlib.md5()
        md5_hash.update(t.encode('utf-8'))
        md5_hash.update(user_info['name'].encode('utf-8'))
        md5_str = md5_hash.hexdigest()
        file_folder = os.path.join(BASE_DIR, 'fileStore/exports/')
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        csv_file_path = os.path.join(file_folder, '{}.csv'.format(md5_str))

        file_records = list()
        for record_item in records_all:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append(record_item['words'])
            row_content.append("是" if record_item['is_publish'] else "否")
            row_content.append(record_item['level'])
            row_content.append(record_item['score'])
            row_content.append(record_item['note'])
            file_records.append(row_content)
        with codecs.open(csv_file_path, 'w', 'utf_8_sig') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(['日期', '部门小组','姓名', '专题题目','字数', '外发情况', '等级', '得分','备注'])
            writer.writerows(file_records)
        # 将文件返回
        return send_from_directory(directory=file_folder, filename='{}.csv'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.csv'.format(md5_str)
                                   )
    

# 具体记录详情(修改记录)
class RetrieveMonographicView(MethodView):
    def get(self, rid):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT usertb.name,usertb.org_id,mgpctb.custom_time,mgpctb.title,mgpctb.words,mgpctb.is_publish,mgpctb.level,mgpctb.score,mgpctb.partner,mgpctb.note " \
                           "FROM `user_info` AS usertb INNER JOIN `monographic` AS mgpctb ON " \
                           "mgpctb.id=%s AND mgpctb.author_id=usertb.id;"
        cursor.execute(select_statement, rid)
        record_item = cursor.fetchone()
        record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
        record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
        record_item['is_publish'] = 1 if record_item['is_publish'] else 0
        record_item['level_types'] = ["A", "B", "C"]
        return jsonify(record_item)

    def put(self, rid):
        body_json = request.json
        record_info = body_json.get('record_data')
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['uid']
        # 不为空的信息判断
        title = record_info.get('title', False)
        if not title:
            return jsonify("参数错误,NOT FOUND TITLE"), 400
        # 组织信息
        custom_time = record_info.get('custom_time')
        words = record_info.get('words', 0)
        is_publish = record_info.get('is_publish', False)
        level = record_info.get('level', 'D')
        score = record_info.get('score', 0)
        note = record_info.get('note', '')
        partner = record_info.get('partner_name', '')
        save_work_statement = "UPDATE `monographic` SET" \
                              "`custom_time`=%s,`title`=%s,`words`=%s,`is_publish`=%s,`level`=%s," \
                              "`score`=%s,`note`=%s,`partner`=%s" \
                              "WHERE `id`=%s AND `author_id`=%s;"
        try:
            # 转换类型
            custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d')
            words = int(words) if words else 0
            score = int(score) if score else 0
            is_publish = 1 if is_publish else 0
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            cursor.execute(save_work_statement,
                           (custom_time, title, words, is_publish, level, score, note, partner, rid, user_id)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("修改专题研究记录错误:" + str(e))
            # # 保存错误得删除已保存的文件
            # if file_path and os.path.exists(file_path):
            #     os.remove(file_path)
            return jsonify("参数错误!无法保存。")
        else:
            return jsonify("修改成功!")

    def delete(self, rid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        db_connection = MySQLConnection()
        annex_file_path = None
        try:
            cursor = db_connection.get_cursor()
            annex_query_statement = "SELECT `annex_url` FROM `monographic` WHERE `id`=%d;" %rid
            cursor.execute(annex_query_statement)
            annex_file = cursor.fetchone()
            if annex_file:
                annex_file_path = annex_file['annex_url']
            user_id = int(user_info['uid'])
            delete_statement = "DELETE FROM `monographic` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(), `create_time`) < 3;" % (rid, user_id)

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
            if annex_file_path:
                file_local_path = os.path.join(BASE_DIR, annex_file_path)
                if os.path.isfile(file_local_path):
                    os.remove(file_local_path)
            return jsonify("删除成功^.^!")


