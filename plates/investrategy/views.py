# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
from flask import jsonify,request,current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from vlibs import VARIETY_LIB


class InvestrategyView(MethodView):
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
        inner_join_statement = "SELECT usertb.name,orgtb.name as org_name,invstb.custom_time,invstb.content,invstb.variety_id,invstb.contract,invstb.direction,invstb.hands,invstb.open_position," \
                               "invstb.close_position,invstb.profit " \
                               "FROM `user_info` AS usertb INNER JOIN `investrategy` AS invstb ON " \
                               "usertb.id=%d AND usertb.id=invstb.author_id INNER JOIN `organization_group` AS orgtb ON orgtb.id=usertb.org_id " \
                               "limit %d,%d;" % (user_id, start_id, page_size)
        cursor.execute(inner_join_statement)
        result_records = cursor.fetchall()
        print("内连接查投顾策略自方案结果", result_records)

        # 查询总条数
        count_statement = "SELECT COUNT(*) as total FROM `user_info` AS usertb INNER JOIN `investrategy`AS invstb ON usertb.id=%s AND usertb.id=invstb.author_id;"
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
            record_item['variety'] = VARIETY_LIB.get(int(record_item['variety_id']), '未知') + str(record_item['contract'])
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
        content = body_data.get('content', False)
        variety = body_data.get('variety', False)
        direction = body_data.get('direction', False)
        if not content or not variety or not direction:
            return jsonify("参数错误,NOT FOUND CONTENT,VARIETY,DIRECTION."), 400

        # 组织信息
        custom_time = body_data.get('custom_time')
        custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d') if custom_time else datetime.datetime.now()

        author_id = user_obj['id']
        contract = body_data.get('contract', '')
        hands = body_data.get('hands', 0)
        open_position = body_data.get('open_position', 0)
        close_position = body_data.get('close_position', 0)
        profit = body_data.get('profit')
        note = body_data.get('work_note', '')

        # 存入数据库
        save_invest_statement = "INSERT INTO `investrategy`" \
                              "(`custom_time`,`author_id`,`content`,`variety_id`,`contract`,`direction`,`hands`," \
                              "`open_position`,`close_position`,`profit`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型
            variety_id = int(variety)
            hands = int(hands)
            open_position = int(open_position)
            close_position = int(close_position)
            cursor.execute(save_invest_statement,
                           (custom_time, author_id, content, variety_id, contract, direction,hands,
                            open_position, close_position, profit)
                           )
            db_connection.commit()
            db_connection.close()
        except Exception as e:
            current_app.logger.error("写入投顾策略记录错误:" + str(e))
            return jsonify("参数错误!无法保存。"), 400
        else:
            return jsonify("保存成功!"), 201