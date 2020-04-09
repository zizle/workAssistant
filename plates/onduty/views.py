# _*_ coding:utf-8 _*_
# __Author__： zizle
import xlrd
import datetime
from flask import jsonify,request,current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from vlibs import ORGANIZATIONS


class OnDutyView(MethodView):
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
        inner_join_statement = "SELECT usertb.name,usertb.org_id,ondmsgtb.custom_time,ondmsgtb.content,ondmsgtb.note " \
                               "FROM `user_info` AS usertb INNER JOIN `onduty_message` AS ondmsgtb ON " \
                               "usertb.id=%d AND usertb.id=ondmsgtb.author_id " \
                               "limit %d,%d;" % (user_id, start_id, page_size)
        cursor.execute(inner_join_statement)
        result_records = cursor.fetchall()
        # print("内连接查询专题研究结果", result_records)

        # 查询总条数
        count_statement = "SELECT COUNT(*) as total FROM `user_info` AS usertb INNER JOIN `onduty_message`AS ondmsgtb ON usertb.id=%s AND usertb.id=ondmsgtb.author_id;"
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
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
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
            return jsonify("参数错误,NOT FOUND CONTENT"), 400
        # 组织信息
        custom_time = body_data.get('custom_time')
        custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d') if custom_time else datetime.datetime.now()
        author_id = user_obj['id']
        note = body_data.get('note', '')
        # 存入数据库
        save_work_statement = "INSERT INTO `onduty_message`" \
                              "(`custom_time`,`author_id`,`content`,`note`)" \
                              "VALUES (%s,%s,%s,%s);"
        try:
            cursor.execute(save_work_statement,
                           (custom_time, author_id, content, note)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入值班记录错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201


# 文件数据上传
class FileHandlerOnDutyMsgView(MethodView):

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
        # table_data = file_contents.sheets()[0]
        # 导入名称为“值班信息”的表
        table_data = file_contents.sheet_by_name('值班信息')
        # 检查sheet1是否导入完毕
        status = file_contents.sheet_loaded('值班信息')
        if not status:
            return jsonify('文件数据导入失败'), 400
        # 读取第一行数据
        first_row = table_data.row_values(0)
        # 格式判断
        if first_row != [
            "日期", "信息内容", "备注"
        ]:
            return jsonify("表格格式有误,请修正."), 400
        nrows = table_data.nrows
        # ncols = table_data.ncols
        # print("行数：", nrows, "列数：", ncols)
        # 获取数据
        ready_to_save = list()  # 准备保存的数据集
        start_data_in = False
        # 组织数据写入数据库
        message = "表格列数据类型有误,请检查后上传."
        try:
            for row in range(nrows):
                row_content = table_data.row_values(row)
                # 找到需要开始上传的数据
                if str(row_content[0]).strip() == 'start':
                    start_data_in = True
                    continue  # 继续下一行
                if str(row_content[0]).strip() == 'end':
                    start_data_in = False
                    continue
                if start_data_in:
                    record_row = list()  # 每行记录
                    # 转换数据类型
                    try:
                        record_row.append(xlrd.xldate_as_datetime(row_content[0], 0))
                    except Exception as e:
                        message = "第一列【日期】请使用日期格式上传."
                        raise ValueError(e)
                    record_row.append(user_id)
                    record_row.append(str(row_content[1]))
                    record_row.append(str(row_content[2]))
                    ready_to_save.append(record_row)
            insert_statement = "INSERT INTO `onduty_message`" \
                               "(`custom_time`,`author_id`,`content`,`note`)" \
                               "VALUES (%s,%s,%s,%s);"
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            cursor.executemany(insert_statement, ready_to_save)
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            return jsonify(message), 400
        else:
            return jsonify("数据保存成功!")