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
        query_date = request.args.get("queryDate", None)
        if not query_date:
            query_date = datetime.today().strftime("%Y-%m-%d")
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录过期了,刷新主页重新登录!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        user_id = user_info["uid"]
        if user_info["is_admin"]:  # 管理员获取所有客户名称
            # cursor.execute(
            #     "SELECT custable.id,usetb.name as username,custable.name,crightstb.id as rid,custable.create_time,custable.account,custable.note,"
            #     "crightstb.remain,crightstb.interest,crightstb.crights,crightstb.custom_time "
            #     "FROM info_customer AS custable "
            #     "INNER JOIN user_info AS usetb "
            #     "ON custable.belong_user=usetb.id "
            #     "LEFT JOIN (SELECT id,customer_id,remain,interest,crights,custom_time "
            #     "FROM customer_rights "
            #     "WHERE DATE_FORMAT(custom_time,'%%Y-%%m-%%d')<=%s ORDER BY custom_time DESC limit 999999999) AS crightstb "
            #     "ON crightstb.customer_id=custable.id "
            #     "GROUP BY custable.id;",
            #     (query_date, )
            # )

            cursor.execute(
                "SELECT * FROM (SELECT custable.id,usetb.name as username,"
                "custable.name, crightstb.id as rid,custable.create_time,custable.account,custable.note,"
                "crightstb.remain,crightstb.interest,crightstb.crights,crightstb.custom_time "
                "FROM info_customer AS custable "
                "INNER JOIN user_info AS usetb "
                "ON custable.belong_user=usetb.id "
                "LEFT JOIN (SELECT id,create_time,customer_id,remain,interest,crights,custom_time "
                "FROM customer_rights WHERE DATE_FORMAT(custom_time,'%%Y-%%m-%%d')<=%s "
                "ORDER BY custom_time DESC limit 999999999) AS crightstb "
                "ON crightstb.customer_id = custable.id "
                "ORDER BY crightstb.customer_id, crightstb.custom_time DESC limit 99999999) as ftb "
                "GROUP BY ftb.id;",
                (query_date,)
            )
            message = "当前为【管理员】客户总权益为 {} 所有客户如下："
        else:
            # 查询当前用户的所有客户,并取得每个客户自己的最近的一条记录值
            # cursor.execute(
            #             #     "SELECT custable.id,usetb.name as username,custable.name, crightstb.id as rid,custable.create_time,custable.account,custable.note,"
            #             #     "crightstb.remain,crightstb.interest,crightstb.crights,crightstb.custom_time "
            #             #     "FROM info_customer AS custable "
            #             #     "INNER JOIN user_info AS usetb "
            #             #     "ON custable.belong_user=usetb.id AND usetb.id=%s "
            #             #     "LEFT JOIN (SELECT id,customer_id,remain,interest,crights,custom_time "
            #             #     "FROM customer_rights WHERE DATE_FORMAT(custom_time,'%%Y-%%m-%%d')<=%s "
            #             #     "ORDER BY custom_time DESC limit 999999999) AS crightstb "
            #             #     "ON crightstb.customer_id=custable.id "
            #             #     "GROUP BY custable.id;",
            #             #     (user_id, query_date)
            #             # )

            cursor.execute(
                "SELECT * FROM (SELECT custable.id,usetb.name as username,"
                "custable.name, crightstb.id as rid,custable.create_time,custable.account,custable.note,"
                "crightstb.remain,crightstb.interest,crightstb.crights,crightstb.custom_time "
                "FROM info_customer AS custable "
                "INNER JOIN user_info AS usetb "
                "ON custable.belong_user=usetb.id AND usetb.id=%s "
                "LEFT JOIN (SELECT id,create_time,customer_id,remain,interest,crights,custom_time "
                "FROM customer_rights WHERE DATE_FORMAT(custom_time,'%%Y-%%m-%%d')<=%s "
                "ORDER BY custom_time DESC limit 999999999) AS crightstb "
                "ON crightstb.customer_id = custable.id "
                "ORDER BY crightstb.customer_id, crightstb.custom_time DESC limit 99999999) as ftb "
                "GROUP BY ftb.id;",
                (user_id, query_date)
            )
            message = "我的客户总权益为: {}"

        all_customer = cursor.fetchall()
        db_connection.close()
        sum_rights = 0
        for customer in all_customer:
            if customer["create_time"] is not None:
                customer["create_time"] = customer['create_time'].strftime("%Y-%m-%d")
            if customer["custom_time"] is not None:
                customer["custom_time"] = customer["custom_time"].strftime("%Y-%m-%d")
            if customer["remain"] is not None:
                customer["remain"] = float(customer["remain"])
            if customer["interest"] is not None:
                customer["interest"] = float(customer["interest"])
            if customer["crights"] is not None:
                customer["crights"] = float(customer["crights"])
                sum_rights += customer["crights"]
        sum_rights = round(sum_rights, 2)
        message = message.format(sum_rights)
        return jsonify({"message": "查询成功!", "customers": all_customer, "customer_message": message})

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
    def get(self, cid):
        # 查询当前客户某一天是否有数据了
        current_date = request.args.get("currentDate", None)
        try:
            current_date = datetime.strptime(current_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception as e:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if self.is_record_exists(cursor, current_date, cid):
            db_connection.close()
            return jsonify({"message": "当前客户{}权益记录已存在\n继续添加将会覆盖记录?".format(current_date), "is_exists": True})
        else:
            db_connection.close()
            return jsonify({"message": "当前客户权益记录不存在", "is_exists": False})

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
            if not cid:
                raise ValueError("请选择客户再添加记录")
            sql_data = {
                "custom_time": datetime.strptime(custom_time, '%Y-%m-%d'),
                "customer_id": cid,
                "remain": float(remain),
                "interest": float(interest),
                "crights": float(crights),
                "note": note,
            }
            current_ctime = datetime.strptime(custom_time, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception as e:
            return jsonify({"message": "参数错误!{}".format(e)}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if self.is_record_exists(cursor, current_ctime, cid):  # 存在更新信息
            cursor.execute(
                "UPDATE customer_rights "
                "SET remain=%s,interest=%s,crights=%s,note=%s "
                "WHERE customer_id=%s;",
                (sql_data["remain"], sql_data["interest"], sql_data["crights"],sql_data["note"], cid)
            )
        else:
            cursor.execute(
                "INSERT INTO customer_rights "
                "(custom_time, customer_id, remain, interest,crights,note) "
                "VALUES (%(custom_time)s,%(customer_id)s,%(remain)s,%(interest)s,%(crights)s,%(note)s);",
                sql_data
            )
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "添加成功!"})

    def is_record_exists(self, cursor, current_date, cid):
        cursor.execute(
            "SELECT id, customer_id "
            "FROM customer_rights "
            "WHERE DATE_FORMAT(custom_time,'%%Y-%%m-%%d')=%s AND customer_id=%s;",
            (current_date, cid)
        )
        is_exists = cursor.fetchone()
        if is_exists:
            return True
        return False

    def delete(self, cid):
        # 删除客户的权益记录
        body_json = request.json
        utoken = body_json.get("utoken", None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录过期了,刷新主页重新登录后再进行操作."}), 400
        record_id = body_json.get("record_id", None)
        if not record_id:
            return jsonify({"message": "参数错误,删除失败!"}), 400
        # 进行删除记录
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(
            "DELETE FROM customer_rights WHERE customer_id=%s AND id=%s;",
            (cid, record_id)
        )
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "删除成功!"})
