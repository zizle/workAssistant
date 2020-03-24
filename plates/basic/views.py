# _*_ coding:utf-8 _*_
# Author: zizle
from flask import request,jsonify, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token, user_is_admin
from db import MySQLConnection
from vlibs import ABNORMAL_WORK



# 系统基本模块数据
class BasicModuleView(MethodView):

    def get(self):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        all_statement = "SELECT id,name,is_active,is_private FROM work_module WHERE parent_id is NULL ORDER BY `sort`;"
        cursor.execute(all_statement)
        all_modules = cursor.fetchall()
        response_data = list()
        for module_item in all_modules:
            # 查询模块的子集
            sub_modules_statement = "SELECT id,name,page_url,is_active,is_private FROM work_module WHERE parent_id=%d;" % module_item['id']
            cursor.execute(sub_modules_statement)
            module_item['subs'] = cursor.fetchall()
            response_data.append(module_item)
        db_connection.close()
        print('basic.views-27:模块页查询功能模块：',response_data)
        return jsonify(response_data)

    def post(self):
        json_data = request.json
        token = json_data.get('utoken', None)
        if not user_is_admin(token):
            return jsonify("登录已过期或没有权限进行这个操作."), 400
        # 验证上传的数据
        module_name = json_data.get('module_name', None)
        module_page_url = json_data.get('page_url', None)
        module_parent_id = json_data.get('parent_id', None)
        if not module_name:
            return jsonify("请填写名称!"), 400
        if module_parent_id and not module_page_url:
            return jsonify("子级模块需填写页面路径！"), 400
        module_page_url += ".html"  # 加上后缀
        # 写入数据库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            if not module_parent_id:
                save_statement = "INSERT INTO `work_module` (`name`,`page_url`,`parent_id`) VALUES (%s,'',NULL);"
                cursor.execute(save_statement, module_name)
                new_id = db_connection.insert_id()

            else:
                save_statement = "INSERT INTO `work_module` (`name`,`page_url`,`parent_id`) VALUES (%s,%s,%s);"
                cursor.execute(save_statement, (module_name,module_page_url,module_parent_id))
                new_id = db_connection.insert_id()
            # 修改sort值
            update_sort_statement = "UPDATE `work_module` SET `sort`=%s WHERE `id`=%s;"
            cursor.execute(update_sort_statement,(new_id,new_id))
            db_connection.commit()
        except Exception as e:
            logger = current_app.logger
            logger.error("新增系统模块错误:" + str(e))
            db_connection.close()
            return jsonify("系统发生了个错误。"), 400
        else:
            return self.get()  # 查询所有



class RetrieveModuleView(MethodView):
    def put(self, module_id):
        body_json = request.json
        operation = body_json.get('operation', None)
        if operation not in ['is_private', 'is_active']:
            return jsonify("参数错误."), 400
        token = body_json.get('utoken', None)
        if not user_is_admin(token):
            return jsonify("登录已过期或没有权限进行这个操作."), 400
        is_checked = 1 if body_json.get('is_checked') else 0
        try:
            # 查询模块
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            update_statement = "UPDATE work_module SET %s=%d WHERE id=%d;" % (operation, is_checked, module_id)
            cursor.execute(update_statement)
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            logger = current_app.logger
            logger.error("修改模块状态" + str(operation) + "错误:" + str(e))
            return jsonify("修改失败"), 400
        return jsonify("修改成功.")


class NoNormalWorkTaskTypeView(MethodView):
    def get(self):
        return ABNORMAL_WORK