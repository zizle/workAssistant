# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
from flask import jsonify,request,current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token


class MonographicView(MethodView):
    def get(self):
        params = request.args
        # 解析用户信息
        token = params.get('utoken')
        user_info = verify_json_web_token(token)
        if not user_info:
            return jsonify("您的登录已过期,请重新登录查看.")
        user_id = user_info['uid']
        print(user_id)
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 30))
        except Exception:
            return jsonify("参数错误:INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # sql内联查询
        inner_join_statement = "SELECT usertb.name,mgpctb.upload_time,mgpctb.title,mgpctb.words,mgpctb.is_publish,mgpctb.level,mgpctb.score,mgpctb.note,orgtb.name as org_name " \
                               "FROM `user_info` AS usertb INNER JOIN `monographic` AS mgpctb ON " \
                               "usertb.id=%d AND usertb.id=mgpctb.author_id INNER JOIN `organization_group` AS orgtb ON orgtb.id=usertb.org_id " \
                               "limit %d,%d;" % (user_id, start_id, page_size)
        cursor.execute(inner_join_statement)
        result_records = cursor.fetchall()
        print("内连接查询专题研究结果", result_records)

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
            record_item['upload_time'] = record_item['upload_time'].strftime('%Y-%m-%d')
            response_data['records'].append(record_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(result_records)

        return jsonify(response_data)


    def post(self):
        body_data = request.json
        author_id = body_data.get('author_id', None)
        if not author_id:
            return jsonify("参数错误，HAS NO AUTHORID.")
        # 查找用户
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_user_statement = "SELECT `id`,`name` FROM `user_info` WHERE `id`=%s AND `is_active`=1;"
        cursor.execute(select_user_statement, author_id)
        user_obj = cursor.fetchone()
        if not user_obj:
            return jsonify("系统没有查到您的信息,无法操作."), 400
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
        # 存入数据库
        save_work_statement = "INSERT INTO `monographic`" \
                              "(`upload_time`,`author_id`,`title`,`words`,`is_publish`,`level`," \
                              "`score`,`note`,`partner`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型
            words = int(words) if words else 0
            score = int(score) if score else 0

            cursor.execute(save_work_statement,
                           (upload_time, author_id,title, words,is_publish,level,score,note,partner)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入专题研究记录错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201


