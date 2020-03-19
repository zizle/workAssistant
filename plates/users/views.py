# _*_ coding:utf-8 _*_
# Author: zizle
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection


# 部门小组信息的视图函数
class OrganizationGroupView(MethodView):
    def get(self):
        # 连接数据库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 执行查询
        query_sql = "SELECT id, name FROM organization_group;"
        cursor.execute(query_sql)
        result = cursor.fetchall()
        print(result)
        print(len(result))
        return jsonify(result)


# 用户视图
class RegisterView(MethodView):

    # 用户注册的接口
    def post(self):

        return ("注册成功")