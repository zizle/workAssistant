# _*_ coding:utf-8 _*_
# Author: zizle
import sys
import jwt
import time
from flask import request, jsonify, url_for
from flask.views import MethodView
from flask import current_app
from settings import SECRET_KEY, JSON_WEB_TOKEN_EXPIRE
from db import MySQLConnection

from utils import psd_handler


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
        db_connection.close()
        # 测试写入日志
        return jsonify(result)


# 用户视图
class RegisterView(MethodView):

    # 用户注册的接口
    def post(self):
        json_data = request.json
        # 验证数据完整性，存入数据库
        username = json_data.get('name')
        password = psd_handler.hash_user_password(json_data.get('password'))
        org_id = json_data.get('organization_id')
        if not username or not password or not org_id:
            return jsonify("请提交完整注册信息."), 400
        # 生成fixed_code
        fixed_code = psd_handler.generate_string_with_time(org_id, 6)
        if self.save_user_information(username, password, org_id, fixed_code):
            return jsonify("注册成功!"), 201
        else:
            return jsonify("注册失败"), 400

    @staticmethod
    def save_user_information(username, password, org_id, fixed_code):
        logger = current_app.logger
        try:
            # 连接数据库，写入数据
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            user_info = "('%s','%s','%s',%d)" % (username, fixed_code, password, org_id)
            save_user = "INSERT INTO user_info (name,fixed_code,password,org_id) VALUES %s;" % (user_info)
            cursor.execute(save_user)
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            logger.error("用户注册写入错误:" + str(e))
            return False
        else:
            return True


class LoginView(MethodView):

    def get(self):  # 验证token
        token = request.args.get('token', None)
        user_info = psd_handler.verify_json_web_token(token)
        if not user_info:  # 状态保持错误
            return jsonify('登录已过期.'), 400
        # 查询系统模块
        print(user_info)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        uid = user_info['uid']
        # 查询用户无需填报的模块
        no_work_statement = "SELECT module_id FROM user_ndo_module WHERE user_id=%s;"
        cursor.execute(no_work_statement, uid)
        no_work_module = cursor.fetchall()
        print(no_work_module, type(no_work_module))
        # 查询系统模块
        if user_info['is_admin']:
            modules_statement = "SELECT id,name,page_url FROM work_module WHERE is_active=1;"
        else:
            modules_statement = "SELECT id,name,page_url FROM work_module WHERE is_active=1 AND is_private=0;"
        cursor.execute(modules_statement)
        all_modules = cursor.fetchall()
        print('所有模块', all_modules, type(all_modules))
        # 剔除无需处理的模块
        response_modules = list()
        for module_item in all_modules:
            if module_item['id'] in no_work_module:
                continue
            response_modules.append(module_item)
        if user_info['is_admin']:
            response_modules += [
                {'id': 0, 'name': '人员设置', 'page_url': 'stuff-maintain.html'},
                {'id': 0, 'name': '部门统计', 'page_url': 'org-statistics.html'},
                {'id': 0, 'name': '系统设置', 'page_url': 'sys-manager.html'},
            ]
        return jsonify(response_modules), 200

    def post(self):
        json_data = request.json
        # print("上传数据：",json_data)
        name = json_data.get('name')
        password = json_data.get('password')
        # is_remember = json_data.get('is_remember', 0)
        # 查询数据库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT id,name,fixed_code,password,is_admin,org_id FROM user_info WHERE name=%s OR fixed_code=%s;"
        cursor.execute(select_statement, [name, name])
        user_obj = cursor.fetchone()
        real_password = user_obj['password']
        # 检查密码
        login_successful = psd_handler.check_user_password(password, real_password)
        if login_successful:  # 登录成功
            is_admin = int.from_bytes(user_obj['is_admin'], byteorder=sys.byteorder, signed=False)
            # 签发token
            token = self.generate_json_web_token(
                uid=user_obj['id'],
                name=user_obj['name'],
                fixed_code=user_obj['fixed_code'],
                org_id=user_obj['org_id'],
                is_admin=is_admin
            )
            status_code = 200
        else:
            token = ''
            status_code = 400
        db_connection.close()  # 关闭数据库连接
        return jsonify(token), status_code

    @staticmethod
    def generate_json_web_token(uid, name, fixed_code, org_id, is_admin):
        issued_at = time.time()
        expiration = issued_at + JSON_WEB_TOKEN_EXPIRE  # 有效期
        token_dict = {
            'iat': issued_at,
            'exp': expiration,
            'uid': uid,
            'name': name,
            'fixed_code': fixed_code,
            'org_id': org_id,
            'is_admin': is_admin
        }

        headers = {
            'alg': 'HS256',
        }
        jwt_token = jwt.encode(
            payload=token_dict,
            key=SECRET_KEY,
            algorithm='HS256',
            headers=headers
        ).decode('utf-8')
        return jwt_token
