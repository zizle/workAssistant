# _*_ coding:utf-8 _*_
# @File  : retrieve.py
# @Time  : 2020-08-13 13:32
# @Author: zizle

""" 单个客户视图 """
from datetime import datetime

from flask import request, jsonify
from flask.views import MethodView

from db import MySQLConnection
from utils.psd_handler import verify_json_web_token


class CustomerView(MethodView):
    def get(self):
        # 获取某个用户的所有客户信息
        utoken = request.args.get("user", None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录过期了,刷新主页重新登录!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        user_id = user_info["uid"]
        if user_info["is_admin"]:  # 管理员获取所有客户名称
            cursor.execute(
                "SELECT custable.id,usetb.name as username,custable.name,custable.create_time,custable.account,custable.note,"
                "crightstb.remain,crightstb.interest,crightstb.crights "
                "FROM info_customer AS custable "
                "INNER JOIN user_info AS usetb "
                "ON custable.belong_user=usetb.id "
                "LEFT JOIN (SELECT customer_id,remain,interest,crights FROM customer_rights ORDER BY id DESC limit 999999999) AS crightstb "
                "ON crightstb.customer_id=custable.id "
                "GROUP BY custable.id;"
            )
        else:
            # 查询当前用户的所有客户,并取得每个客户自己的最近的一条记录值
            cursor.execute(
                "SELECT custable.id,usetb.name as username,custable.name,custable.create_time,custable.account,custable.note,"
                "crightstb.remain,crightstb.interest,crightstb.crights "
                "FROM info_customer AS custable "
                "INNER JOIN user_info AS usetb "
                "ON custable.belong_user=usetb.id "
                "LEFT JOIN (SELECT customer_id,remain,interest,crights FROM customer_rights ORDER BY id DESC limit 999999999) AS crightstb "
                "ON crightstb.customer_id=custable.id "
                "WHERE usetb.id=%s "
                "GROUP BY custable.id;",
                (user_id, )
            )

        all_customer = cursor.fetchall()
        db_connection.close()
        for customer in all_customer:
            customer["create_time"] = customer['create_time'].strftime("%Y-%m-%d")
            if customer["remain"]:
                customer["remain"] = float(customer["remain"])
            if customer["interest"]:
                customer["interest"] = float(customer["interest"])
            if customer["crights"]:
                customer["crights"] = float(customer["crights"])
        return jsonify({"message": "查询成功!", "customers": all_customer})

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录过期了,刷新主页重新登录!"}), 400
        if user_info["is_admin"]:
            return jsonify({"message": "请不要使用管理员用户添加记录!"}), 400
        user_id = user_info["uid"]
        customer_name = body_json.get("customer_name", None)
        customer_account = body_json.get("customer_account", None)
        customer_note = body_json.get("customer_note", None)
        if not all([customer_name, customer_account]):
            return jsonify({"message": "客户名称和账号均为必填项"}), 400
        # 将客户信息入库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        new_customer = {
            "name": customer_name,
            "account": customer_account,
            "note": customer_note,
            "belong_user": user_id
        }
        cursor.execute(
            "INSERT INTO info_customer "
            "(`name`,`account`,`belong_user`,`note`) "
            "VALUES (%(name)s,%(account)s,%(belong_user)s,%(note)s);",
            new_customer
        )
        db_connection.commit()

        # 查询当前用户的所有客户
        cursor.execute(
            "SELECT `id`,`name`,`account` "
            "FROM `info_customer` "
            "WHERE `belong_user`=%s;",
            (user_id,)
        )
        all_customer = cursor.fetchall()
        db_connection.close()
        return jsonify({"message": "添加成功!", "customers": all_customer})


class CustomerCrightsView(MethodView):
    def post(self, cid):
        # 新增某客户的权益记录
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录过期了,刷新主页重新登录!"}), 400
        if user_info["is_admin"]:
            return jsonify({"message": "请不要使用管理员用户添加记录!"}), 400
        custom_time = body_json.get('custom_time', None)
        remain = body_json.get('remain', 0)
        interest = body_json.get('interest', 0)
        crights = body_json.get('crights', 0)
        note = body_json.get('note', '')
        try:
            sql_data = {
                "custom_time": datetime.strptime(custom_time, '%Y-%m-%d'),
                "customer_id": cid,
                "remain": float(remain),
                "interest": float(interest),
                "crights": float(crights),
                "note": note,
            }
        except Exception as e:
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(
            "INSERT INTO customer_rights "
            "(custom_time, customer_id, remain, interest,crights,note) "
            "VALUES (%(custom_time)s,%(customer_id)s,%(remain)s,%(interest)s,%(crights)s,%(note)s);",
            sql_data
        )
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "添加成功!"})