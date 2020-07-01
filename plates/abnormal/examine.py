# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-01
# ------------------------

from flask import request, jsonify
from flask.views import MethodView

from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from vlibs import ABNORMAL_WORK, ORGANIZATIONS


class ExamineWorkRecord(MethodView):
    def get(self):
        query_params = request.args
        try:
            examine_status = int(query_params.get('status', 0))
            current_page = int(query_params.get('page', 1)) - 1
            page_size = int(query_params.get('page_size', 35))
        except Exception:
            return jsonify({"message": "参数错误", "records": []}), 400
        # 通过参数查询数据
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if examine_status == 0:
            inner_join_statement = "SELECT usertb.name,usertb.org_id,abworktb.id,abworktb.custom_time,abworktb.task_type," \
                                   "abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number," \
                                   "abworktb.swiss_coin,abworktb.allowance,abworktb.note,abworktb.annex,abworktb.annex_url,abworktb.is_examined " \
                                   "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                                   "usertb.id=abworktb.author_id " \
                                   "ORDER BY abworktb.custom_time DESC " \
                                   "limit %s,%s;"
            cursor.execute(inner_join_statement, (start_id, page_size))
            # 查询总条数
            total_count_statement = "SELECT COUNT(abworktb.id) as total FROM `user_info` AS usertb INNER JOIN `abnormal_work`AS abworktb " \
                                    "ON usertb.id=abworktb.author_id;"
            abworks = cursor.fetchall()
            cursor.execute(total_count_statement)
            total_ = cursor.fetchone()
        else:
            examine_status = 0 if examine_status == 1 else 1
            # 原生sql内联查询
            inner_join_statement = "SELECT usertb.name,usertb.org_id,abworktb.id,abworktb.custom_time,abworktb.task_type," \
                                   "abworktb.title,abworktb.sponsor,abworktb.applied_org,abworktb.applicant,abworktb.tel_number," \
                                   "abworktb.swiss_coin,abworktb.allowance,abworktb.note,abworktb.annex,abworktb.annex_url,abworktb.is_examined " \
                                   "FROM `user_info` AS usertb INNER JOIN `abnormal_work` AS abworktb ON " \
                                   "usertb.id=abworktb.author_id AND abworktb.is_examined=%s " \
                                   "ORDER BY abworktb.custom_time DESC " \
                                   "limit %s,%s;"
            cursor.execute(inner_join_statement, (examine_status, start_id, page_size))
            # 查询总条数
            total_count_statement = "SELECT COUNT(abworktb.id) as total FROM `user_info` AS usertb INNER JOIN `abnormal_work`AS abworktb " \
                                    "ON usertb.id=abworktb.author_id AND abworktb.is_examined=%s;"

            abworks = cursor.fetchall()
            cursor.execute(total_count_statement, (examine_status,))
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
        response_data['message'] = "查询成功!"
        return jsonify(response_data)

    def post(self):
        work_id = request.args.get('workid', 0)
        user_token = request.args.get('utoken', '')
        examined = request.args.get('checked', 0)
        try:
            work_id = int(work_id)
            examined = int(examined)
            if examined not in [0, 1]:
                raise ValueError("参数错误")
            user_info = verify_json_web_token(user_token)
            if not user_info:
                raise ValueError('登录过期')
            if not int(user_info['is_admin']):
                raise ValueError('无权限操作...')
        except Exception as e:
            return jsonify({"message": str(e)}), 400
        # 对这个id的记录进行更新
        update_statement = "UPDATE `abnormal_work` SET `is_examined`=%s WHERE id=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(update_statement, (examined, work_id))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "修改成功!"})