# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
import re
import smtplib
import time
from email.mime.text import MIMEText

import jwt
from flask import current_app
from flask import request, jsonify
from flask.views import MethodView

import settings
from db import MySQLConnection, RedisConnection
from settings import SECRET_KEY, JSON_WEB_TOKEN_EXPIRE
from utils import psd_handler
from vlibs import ORGANIZATIONS


# 部门小组信息的视图函数
class OrganizationGroupView(MethodView):
    def get(self):
        organizations = []
        for key,value in ORGANIZATIONS.items():
            o_item = dict()
            o_item['id'] = key
            o_item['name'] = value
            organizations.append(o_item)
        return jsonify(organizations)


# 用户视图
class RegisterView(MethodView):

    # 用户注册的接口
    def post(self):
        json_data = request.json
        # 验证数据完整性，存入数据库
        username = json_data.get('name')
        password = psd_handler.hash_user_password(json_data.get('password'))
        phone = json_data.get('phone', '')
        email = json_data.get('email', '')
        if not username or not password or not phone:
            return jsonify("请提交完整注册信息."), 400
        # 验证手机号和邮箱
        if not re.match(r'^1[345678][0-9]{9}$', phone):
            return jsonify('请提交正确的手机号.'), 400
        if not re.match(r'^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$', email):
            return jsonify("请提交正确的邮箱."), 400
        # 生成fixed_code
        fixed_code = psd_handler.generate_string_with_time(7)
        if self.save_user_information(username, password, 0, fixed_code, phone, email):
            return jsonify("注册成功!"), 201
        else:
            return jsonify("注册失败"), 400

    @staticmethod
    def save_user_information(username, password, org_id, fixed_code, phone, email):
        logger = current_app.logger
        try:
            # 连接数据库，写入数据
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            # user_info = "('%s','%s','%s',%d, )" % (username, fixed_code, password, org_id)
            save_user = "INSERT INTO user_info (name,fixed_code,password,phone,email,org_id) VALUES (%s,%s,%s,%s,%s,%s);"
            cursor.execute(save_user, (username, fixed_code, password, phone, email, org_id))
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
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        uid = user_info['uid']
        # 查询用户无需填报的模块
        no_work_statement = "SELECT module_id FROM user_ndo_module WHERE user_id=%s AND is_active=1;"
        cursor.execute(no_work_statement, uid)
        no_work_module = cursor.fetchall()
        no_work_module = [item['module_id'] for item in no_work_module] if no_work_module else []
        # print('no_work_module', no_work_module)
        # 查询系统模块
        if user_info['is_admin']:
            # print('管理员')
            # 查询主功能
            modules_statement = "SELECT `id`,`name` FROM `work_module` WHERE `is_active`=1 AND `parent_id` is NULL ORDER BY `sort`;"
            # 查询子集的语句
            sub_modules_statement = "SELECT `id`,`name`,`page_url` FROM `work_module` WHERE `is_active`=1 AND `parent_id`=%s ORDER BY `sort`;"
        else:
            # print('非管理员')
            # 查询主功能
            modules_statement = "SELECT `id`,`name`,`page_url` FROM `work_module` WHERE `is_active`=1 AND `is_private`=0 AND `parent_id` is NULL ORDER BY `sort`;"
            # 查询子集的语句
            sub_modules_statement = "SELECT `id`,`name`,`page_url` FROM `work_module` WHERE `is_active`=1 AND `is_private`=0 AND `parent_id`=%s ORDER BY `sort`;"
        cursor.execute(modules_statement)
        # 剔除无需处理的模块
        response_modules = list()
        for module_item in cursor.fetchall():  # 注意 cursor.fetchall()只能用一次
            if module_item['id'] in no_work_module:
                continue
            # 查询模块的子集
            cursor.execute(sub_modules_statement, module_item['id'])
            # print('子集',cursor.fetchall(),type(cursor.fetchall()))
            sub_fetchall = cursor.fetchall()
            if not sub_fetchall:  # 没有需工作的子集
                continue
            # 遍历子集
            module_item['subs'] = list()
            for sub_module_item in sub_fetchall:
                if sub_module_item['id'] in no_work_module:
                    continue
                module_item['subs'].append(sub_module_item)
            if len(module_item['subs']) > 0:
                response_modules.append(module_item)
        # print(response_modules)
        db_connection.close()
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
        select_statement = "SELECT id,name,fixed_code,password,is_admin,org_id FROM user_info WHERE (name=%s OR fixed_code=%s OR phone=%s) AND is_active=1;"
        cursor.execute(select_statement, [name, name, name])
        user_obj = cursor.fetchone()
        if not user_obj:
            return jsonify("无效用户"), 400
        real_password = user_obj['password']
        # 检查密码
        login_successful = psd_handler.check_user_password(password, real_password)
        if login_successful:  # 登录成功
            # is_admin = int.from_bytes(user_obj['is_admin'], byteorder=sys.byteorder, signed=False) 全局配置了
            # 签发token
            token = self.generate_json_web_token(
                uid=user_obj['id'],
                name=user_obj['name'],
                fixed_code=user_obj['fixed_code'],
                org_id=user_obj['org_id'],
                is_admin=user_obj['is_admin']
            )
            # 修改update_time
            modify_statement = "UPDATE user_info SET update_time=%s WHERE id=%s;"
            cursor.execute(modify_statement, (datetime.datetime.now(), user_obj['id']))
            db_connection.commit()
            status_code = 200
        else:
            token = '用户名或密码错误'
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


class UserView(MethodView):
    def get(self):
        token = request.args.get("utoken")
        if not psd_handler.user_is_admin(token):
            return jsonify("登录已过期或没有权限进行这个操作"), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询所有用户信息
        select_statement = "SELECT id,name,fixed_code,join_time,phone,email,update_time,is_active,is_admin,org_id FROM user_info;"
        cursor.execute(select_statement)
        # 重新组织用户数据
        user_data = list()
        for user_item in cursor.fetchall():
            user_dict = dict()
            user_dict['id'] = user_item['id']
            user_dict['name'] = user_item['name']
            user_dict['fixed_code'] = user_item['fixed_code']
            user_dict['join_time'] = user_item['join_time'].strftime('%Y-%m-%d %H:%M:%S')
            user_dict['update_time'] = user_item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            user_dict['is_active'] = user_item['is_active']
            user_dict['is_admin'] = user_item['is_admin']
            user_dict['organization'] = ORGANIZATIONS.get(user_item['org_id'], '未知')
            user_dict['phone'] = user_item['phone']
            user_dict['email'] = user_item['email']
            user_data.append(user_dict)
        db_connection.close()
        return jsonify(user_data)


# 单用户视图
class RetrieveUserView(MethodView):
    def post(self, user_id):
        utoken = request.json.get('utoken')
        operator_user = psd_handler.verify_json_web_token(utoken)
        if not operator_user or not operator_user['is_admin']:
            return jsonify("登录已过期或无权限操作!"), 400
        password = request.json.get('password')
        new_password = psd_handler.hash_user_password(password)
        # 设置新密码
        update_statement = "UPDATE `user_info` SET `password`=%s WHERE `id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(update_statement, (new_password, user_id))
        db_connection.commit()
        db_connection.close()
        return jsonify("重置用户密码成功!\n新密码为:123456")

    def put(self, user_id):
        utoken = request.json.get('utoken')
        is_active = 1 if request.json.get('is_checked', False) else 0
        org_id = request.json.get('org_id')
        if not psd_handler.user_is_admin(utoken):
            return jsonify("登录已过期或没有权限进行这个操作"), 400
        try:
            org_id = int(org_id)
            # 进行修改
            modify_statement = "UPDATE `user_info` SET `is_active`=%d,`org_id`=%d WHERE id=%d;" % (is_active, org_id, user_id)
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            cursor.execute(modify_statement)
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            logger = current_app.logger
            logger.error('审核用户错误:' + str(e))
            return jsonify('参数错误 require int'), 400
        else:
            return jsonify("修改成功。")


# 单个用户的工作模块信息
class RetrieveUserModuleView(MethodView):
    def get(self, user_id):
        try:
            response_data = dict()
            response_data['modules'] = list()
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            # 查询用户信息
            user_select_statement = "SELECT `id`,`name`,`fixed_code` FROM `user_info` WHERE id=%s;"
            cursor.execute(user_select_statement, user_id)
            user_info = cursor.fetchone()
            if not user_info:
                return jsonify("该人员不存在"), 400
            response_data['user_id'] = user_info['id']
            response_data['username'] = user_info['name']
            response_data['fixed_code'] = user_info['fixed_code']

            # 查询用户无需工作的模块
            nowork_statement = "SELECT `module_id`,`is_active` FROM `user_ndo_module` WHERE `user_id`=%s;"
            cursor.execute(nowork_statement, user_id)
            nowork_module_info = {no_work_item['module_id']:no_work_item['is_active'] for no_work_item in cursor.fetchall()}

            # 查询系统主模块,去除id=1与私有
            module_select_statement = "SELECT `id`,`name` FROM `work_module` WHERE `is_private`=0 AND `parent_id` is NULL;"
            cursor.execute(module_select_statement)
            # 遍历查询子模块语句
            sub_module_statement = "SELECT `id`,`name`,`page_url` FROM `work_module` WHERE `is_private`=0 AND `parent_id`=%s;"

            for module_item in cursor.fetchall():
                module_item['is_working'] = True
                cursor.execute(sub_module_statement, module_item['id'])
                # 遍历子模块，获取工作状态
                module_item['subs'] = list()
                for sub_module in cursor.fetchall():
                    if sub_module['id'] in nowork_module_info:
                        sub_module['is_working'] = not nowork_module_info.get(sub_module['id'])
                    else:
                        sub_module['is_working'] = True
                    module_item['subs'].append(sub_module)

                response_data['modules'].append(module_item)

            # print('最终结果:', response_data)
            db_connection.close()
        except Exception as e:
            logger = current_app.logger
            logger.error("分配用户需工作模块查询时错误:" + str(e))
            return jsonify("查询数据错误"), 500
        else:
            return jsonify(response_data)


class RetrieveUMView(MethodView):
    def post(self, user_id, module_id):

        token = request.json.get('utoken', None)
        is_active = True if request.json.get('is_checked', False) else False
        if not psd_handler.user_is_admin(token):
            return jsonify('登录已过期或没有权限进行这个操作'), 400
        try:
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            nowork_select_statement = "SELECT `user_id`,`module_id`,`is_active` FROM `user_ndo_module` WHERE `user_id`=%s AND `module_id`=%s;"
            cursor.execute(nowork_select_statement,(user_id,module_id))
            nowork_module = cursor.fetchone()
            # print(nowork_module)
            if not nowork_module:  # 数据库不存在记录增加一条
                add_statement = "INSERT INTO `user_ndo_module` (user_id,module_id,is_active) VALUES (%s,%s,%s);"
                cursor.execute(add_statement,(user_id, module_id, not is_active))
            else:  # 存在记录就更新
                update_statement = "UPDATE `user_ndo_module` SET `is_active`=%s WHERE `user_id`=%s AND `module_id`=%s;"
                cursor.execute(update_statement,(not is_active, user_id, module_id))
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            logger = current_app.logger
            logger.error("修改用户需要工作的模块失败:" + str(e))
            return jsonify('操作错误,500 SERVER ERROR'), 400
        else:
            return jsonify("操作成功")


class ParserUserTokenView(MethodView):
    def get(self):
        token = request.args.get('utoken')
        user_info = psd_handler.verify_json_web_token(token)
        if not user_info:  # 状态保持错误
            return jsonify('登录已过期.'), 400
        org_id = user_info.get('org_id', None)
        if org_id:
            user_info['org_name'] = ORGANIZATIONS.get(int(org_id),'未知')

        else:
            user_info['org_name'] = '无'
        return jsonify(user_info)


class UserCenterView(MethodView):
    def get(self):
        token = request.args.get('utoken')
        user_info = psd_handler.verify_json_web_token(token)
        if not user_info:  # 状态保持错误
            return jsonify('登录已过期.'), 400
        # 通过id查询用户信息
        user_id = user_info['uid']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`,`name`,`fixed_code`,`join_time`,`phone`,`email`,`org_id` " \
                          "FROM `user_info` " \
                          "WHERE `id`=%s;"
        cursor.execute(query_statement, user_id)
        user_info = cursor.fetchone()
        user_info['join_time'] = user_info['join_time'].strftime("%Y-%d-%m %H:%M:%S")
        user_info['org_name'] = ORGANIZATIONS.get(int(user_info['org_id']), '未知')
        return jsonify({'message': '查询成功!', 'userinfo': user_info})

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        password = body_json.get('password')
        user_info = psd_handler.verify_json_web_token(utoken)
        if not user_info:
            return jsonify("登录已过期，重新登录"), 400  # 重定向
        user_id = user_info['uid']
        new_password = psd_handler.hash_user_password(password)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        modify_statement = "UPDATE `user_info` SET `password`=%s WHERE `id`=%s;"
        cursor.execute(modify_statement, (new_password, user_id))
        db_connection.commit()
        db_connection.close()
        return jsonify("修改密码成功!请重新登录!")  # 重定向


class UserExistView(MethodView):
    def get(self):
        # 查询用户是否存在
        username = request.args.get('username', None)
        if not username:
            return jsonify({'message':'用户不存在','exist': False})
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id` FROM `user_info` WHERE `name`=%s;"
        cursor.execute(query_statement, username)
        exist = cursor.fetchone()
        db_connection.close()
        if not exist:
            exist = 0
        else:
            exist = 1
        return jsonify({'message': '查询成功!', 'exist': exist})


class SendEmailVerifyCodeView(MethodView):
    def get(self):
        # 向用户邮箱发送验证码
        username = request.args.get('username', None)
        if not username:
            return jsonify({'message': '用户不存在.', 'send': False})
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`,`email` FROM `user_info` WHERE `name`=%s;"
        cursor.execute(query_statement, username)
        exist = cursor.fetchone()
        db_connection.close()
        if not exist:
            return jsonify({'message': '用户不存在.', 'send': False})
        # 发送验证码
        user_email = exist['email']
        # 验证用户的邮箱格式
        if not re.match(r'^(\w+\.?)*\w+@(?:\w+\.)\w+$', user_email):
            return jsonify({'message': '预留邮箱格式错误.发送失败.', 'send': False})
        receivers = [user_email]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        # 生成验证码
        code = psd_handler.generate_string_with_time(5)
        # 将验证码保存到redis
        redis_connection = RedisConnection()
        value_key = '{}_email_code'.format(username)
        redis_connection.set_value(value_key, code, 600)  # 10分钟有效
        mail_msg = """
        <p>您正在修改《瑞达期货研究院工作管理系统》的登录密码,如不是本人操作请忽略,并请尽快进入系统修改密码.</p>
        <p>本次验证码是:</p>
        <p style='font-size:17px;color:rgb(200,20,20)'>{}<p>
        """.format(code)
        message = MIMEText(mail_msg, 'html', 'utf-8')
        message['From'] = settings.EMAIL
        message['To'] = receivers[0]
        message['Subject'] = '<瑞达期货研究院工作管理系统>修改密码邮箱验证码'
        try:
            smtpObj = smtplib.SMTP(host='smtp.163.com')
            smtpObj.login(settings.EMAIL, settings.EMAILPSD)
            smtpObj.sendmail(settings.EMAIL, receivers, message.as_string())
            send = True
        except smtplib.SMTPException as e:
            current_app.logger.error("发送邮件错误!{}".format(e))
            send = False
        return jsonify({'message': '发送成功!', 'send': send})

    def post(self):
        # 设置新密码
        body_json = request.json
        username = body_json.get('username', None)
        password = body_json.get('password', None)
        email_code = body_json.get('email_code', None)
        if not all([username, password, email_code]):
            return jsonify({'message': '参数不足.', 'ret': False})
        # 取出redis中的验证码
        redis_connection = RedisConnection()
        code = redis_connection.get_value("{}_email_code".format(username))
        # 对比验证码，设置新密码
        if code.lower() == email_code.lower():
            new_psd = psd_handler.hash_user_password(password)
            update_statement = "UPDATE `user_info` SET `password`=%s WHERE `name`=%s;"
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            cursor.execute(update_statement, (new_psd, username))
            db_connection.commit()
            db_connection.close()
            return jsonify({'message': '修改成功!', 'ret': True})
        else:
            return jsonify({'message': '验证码错误!', 'ret': False})
