# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
import hashlib
import os
import time

import pandas as pd
from flask import jsonify, request, current_app, send_from_directory
from flask.views import MethodView

from db import MySQLConnection
from settings import BASE_DIR
from utils.file_handler import hash_file_name
from utils.psd_handler import verify_json_web_token
from vlibs import ORGANIZATIONS


# 提交与查询
class InvestmentView(MethodView):
    def get(self):
        params = request.args
        # 解析用户信息
        token = params.get('utoken')
        user_info = verify_json_web_token(token)
        if not user_info:
            return jsonify("您的登录已过期,请重新登录查看.")
        user_id = user_info['uid']
        try:
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('pagesize', 30))
        except Exception:
            return jsonify("参数错误:DATE FORMAT ERROR & INT TYPE REQUIRED!")
        start_id = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # sql内联查询
        inner_join_statement = "SELECT usertb.name,usertb.org_id,invstb.id,invstb.custom_time,invstb.title,varietytb.name as variety,invstb.contract,invstb.direction,invstb.build_time,invstb.build_price," \
                               "invstb.build_hands,invstb.out_price,invstb.cutloss_price,invstb.expire_time,invstb.is_publish,invstb.profit,invstb.annex_url,invstb.note,invstb.level " \
                               "FROM `user_info` AS usertb INNER JOIN `investment` AS invstb INNER JOIN `variety` as varietytb ON " \
                               "(usertb.id=%s AND usertb.id=invstb.author_id) AND invstb.variety_id=varietytb.id AND (invstb.custom_time BETWEEN %s AND %s) " \
                               "ORDER BY invstb.custom_time DESC " \
                               "limit %s,%s;"
        cursor.execute(inner_join_statement,(user_id, start_date, end_date,start_id, page_size))
        result_records = cursor.fetchall()
        # print("内连接查询投资自方案结果", result_records)

        # 查询总条数
        count_statement = "SELECT COUNT(invstb.id) AS total, SUM(invstb.profit) AS `sumprofit` " \
                          "FROM `user_info` AS usertb INNER JOIN `investment`AS invstb ON " \
                          "usertb.id=%s AND usertb.id=invstb.author_id AND (invstb.custom_time BETWEEN %s AND %s);"
        cursor.execute(count_statement, (user_id, start_date, end_date))
        # print("条目记录：", cursor.fetchone()) 打开注释下行将无法解释编译
        fetch_one = cursor.fetchone()
        # print(fetch_one)
        db_connection.close()
        if fetch_one:
            total_count = fetch_one['total']
            sum_porfit = fetch_one['sumprofit']
        else:
            total_count = sum_porfit = 0

        total_page = int((total_count + page_size - 1) / page_size)

        # print('total_page',total_page)
        # 组织数据返回
        response_data = dict()
        response_data['records'] = list()
        for record_item in result_records:
            record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
            record_item['build_time'] = record_item['build_time'].strftime('%Y-%m-%d %H:%M')
            record_item['expire_time'] = record_item['expire_time'].strftime('%Y-%m-%d %H:%M')
            record_item['variety'] = (record_item['variety'] if record_item['variety'] else '') + str(record_item['contract'])
            record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
            record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
            record_item['build_price'] = int(record_item['build_price'])
            record_item['out_price'] = int(record_item['out_price'])
            record_item['cutloss_price'] = int(record_item['cutloss_price'])
            record_item['profit'] = int(record_item['profit'])
            response_data['records'].append(record_item)
        response_data['current_page'] = current_page + 1  # 查询前给减1处理了，加回来
        response_data['total_page'] = total_page
        response_data['current_count'] = len(result_records)
        response_data['total_count'] = total_count
        response_data['sum_profit'] = float(sum_porfit) if sum_porfit else 0

        return jsonify(response_data)

    def post(self):
        body_data = request.form
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
        title = body_data.get('title', False)
        variety = body_data.get('variety', False)
        direction = body_data.get('direction', False)
        if not title or not variety or not direction:
            return jsonify("参数错误,NOT FOUND TITLE,VARIETY,DIRECTION."), 400
        # 组织信息
        write_time = body_data.get('write_time')
        author_id = user_obj['id']
        contract = body_data.get('contract','')
        build_time = body_data.get('build_date_time')
        build_price = body_data.get('build_price')
        build_hands = body_data.get('build_hands')
        out_price = body_data.get('out_price')
        cutloss_price = body_data.get('cutloss_price')
        expire_time = body_data.get('expire_time')
        is_publish = 1 if body_data.get('is_publish', False) else 0
        profit = body_data.get('profit')
        level = body_data.get('level', '')
        note = body_data.get('note', '')
        # 读取文件
        annex_file = request.files.get('annex_file', None)
        if not annex_file:
            filename = ''
            annex_url = ''
            file_path = ''
        else:
            # 文件名hash
            filename = annex_file.filename
            hash_name = hash_file_name(filename)
            # 获取保存的位置
            file_path = os.path.join(BASE_DIR, "fileStore/investment/" + hash_name)
            annex_url = "fileStore/investment/" + hash_name  # 数据库路径
            annex_file.save(file_path)
        # 存入数据库
        save_invest_statement = "INSERT INTO `investment`" \
                              "(`custom_time`,`author_id`,`title`,`variety_id`,`contract`,`direction`,`build_time`," \
                              "`build_price`,`build_hands`,`out_price`,`cutloss_price`,`expire_time`,`is_publish`,`profit`,`annex`,`annex_url`,`note`,`level`)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        try:
            # 转换类型
            custom_time = datetime.datetime.strptime(write_time, '%Y-%m-%d') if write_time else datetime.datetime.now()
            build_time = datetime.datetime.strptime(build_time,'%Y-%m-%dT%H:%M') if build_time else datetime.datetime.now()
            expire_time = datetime.datetime.strptime(expire_time,'%Y-%m-%dT%H:%M') if expire_time else datetime.datetime.now()
            variety_id = int(variety)
            build_price = float(build_price) if build_price else 0
            build_hands = int(build_hands) if build_hands else 0
            out_price = float(out_price) if out_price else 0
            cutloss_price = float(cutloss_price) if cutloss_price else 0
            profit = float(profit) if profit else 0
            cursor.execute(save_invest_statement,
                           (custom_time, author_id, title, variety_id,contract, direction, build_time,
                            build_price, build_hands, out_price, cutloss_price, expire_time, is_publish, profit, filename,annex_url,note, level)
                           )
            db_connection.commit()

        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("写入投在方案记录错误:" + str(e))
            # 保存错误得删除已保存的文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify("参数错误!无法保存。"), 400
        else:
            db_connection.close()
            return jsonify("保存成功!"), 201


class RetrieveInvestmentView(MethodView):
    def get(self, rid):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT usertb.name,usertb.org_id,invstb.custom_time,invstb.variety_id,invstb.title,invstb.contract,invstb.direction,invstb.build_time,invstb.build_price, " \
                           "invstb.build_hands,invstb.out_price,invstb.cutloss_price,invstb.expire_time,invstb.is_publish,invstb.profit,invstb.annex,invstb.annex_url,invstb.note,invstb.level " \
                           "FROM `user_info` AS usertb INNER JOIN `investment` AS invstb ON " \
                           "invstb.id=%s AND invstb.author_id=usertb.id;"
        cursor.execute(select_statement, rid)
        record_item = cursor.fetchone()

        record_item['custom_time'] = record_item['custom_time'].strftime('%Y-%m-%d')
        record_item['build_time'] = record_item['build_time'].strftime('%Y-%m-%dT%H:%M:%S')
        record_item['expire_time'] = record_item['expire_time'].strftime('%Y-%m-%dT%H:%M:%S')
        record_item['is_publish'] = "是" if record_item['is_publish'] else "否"
        record_item['org_name'] = ORGANIZATIONS.get(int(record_item['org_id']), '未知')
        record_item['build_price'] = float(record_item['build_price'])
        record_item['out_price'] = float(record_item['out_price'])
        record_item['cutloss_price'] = float(record_item['cutloss_price'])
        record_item['profit'] = float(record_item['profit'])
        db_connection.close()
        return jsonify(record_item)

    def put(self, rid):
        body_data = request.form
        utoken = body_data.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['uid']
        # 不为空的信息判断
        title = body_data.get('title', False)
        variety_id = body_data.get('variety_id', False)
        direction = body_data.get('direction', False)
        if not title or not variety_id or not direction:
            return jsonify("参数错误,NOT FOUND TITLE,VARIETY,DIRECTION."), 400
        # 组织信息
        write_time = body_data.get('custom_time')
        contract = body_data.get('contract', '')
        build_time = body_data.get('build_time')
        build_price = body_data.get('build_price')
        build_hands = body_data.get('build_hands')
        out_price = body_data.get('out_price')
        cutloss_price = body_data.get('cutloss_price')
        expire_time = body_data.get('expire_time')
        is_publish = 1 if body_data.get('is_publish', False) else 0
        profit = body_data.get('profit')
        note = body_data.get('note', '')
        level = body_data.get('level', '')
        filename=body_data.get('annex', '')
        annex_url = body_data.get('annex_url', '')
        old_annex_url = annex_url
        annex_file = request.files.get('annex_file', None)
        file_path = ''
        if annex_file:
            filename = annex_file.filename
            hash_name = hash_file_name(filename)
            file_path = os.path.join(BASE_DIR, "fileStore/investment/" + hash_name)
            annex_url = "fileStore/investment/" + hash_name  # 数据库路径
            annex_file.save(file_path)

        # 存入数据库
        update_statement = "UPDATE `investment` SET " \
                            "`custom_time`=%s,`title`=%s,`variety_id`=%s,`contract`=%s,`direction`=%s,`build_time`=%s," \
                            "`build_price`=%s,`build_hands`=%s,`out_price`=%s,`cutloss_price`=%s,`expire_time`=%s," \
                            "`is_publish`=%s,`profit`=%s,`annex`=%s,`annex_url`=%s,`note`=%s,`level`=%s " \
                            "WHERE `id`=%s AND `author_id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            # 转换类型
            variety_id = int(variety_id)
            build_price = float(build_price) if build_price else 0
            build_hands = int(build_hands) if build_hands else 0
            out_price = float(out_price) if out_price else 0
            cutloss_price = float(cutloss_price) if cutloss_price else 0
            profit = float(profit) if profit else 0
            expire_time_format = build_time_format = '%Y-%m-%dT%H:%M:%S'
            if len(build_time) < 19:
                build_time_format = '%Y-%m-%dT%H:%M'
            if len(expire_time) < 19:
                expire_time_format = '%Y-%m-%dT%H:%M'
            custom_time = datetime.datetime.strptime(write_time, '%Y-%m-%d') if write_time else datetime.datetime.now()
            build_time = datetime.datetime.strptime(build_time,build_time_format) if build_time else datetime.datetime.now()
            expire_time = datetime.datetime.strptime(expire_time,expire_time_format) if expire_time else datetime.datetime.now()
            cursor.execute(update_statement,
                           (custom_time, title, variety_id, contract, direction, build_time,
                            build_price, build_hands, out_price, cutloss_price, expire_time, is_publish, profit,filename, annex_url,note,level,
                            rid, user_id)
                           )
            db_connection.commit()
            old_file_path = os.path.join(BASE_DIR, old_annex_url)
            if annex_file and os.path.isfile(old_file_path):
                os.remove(old_file_path)
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("更新投资方案记录错误:" + str(e))
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify("参数错误!无法更新。"), 400
        else:
            db_connection.close()
            return jsonify("更新成功!"), 201

    def delete(self, rid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        db_connection = MySQLConnection()
        annex_file_path = None
        try:
            cursor = db_connection.get_cursor()
            annex_query_statement = "SELECT `annex_url` FROM `investment` WHERE `id`=%d;" % rid
            cursor.execute(annex_query_statement)
            annex_file = cursor.fetchone()
            if annex_file:
                annex_file_path = annex_file['annex_url']
            user_id = int(user_info['uid'])
            delete_statement = "DELETE FROM `investment` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (
                               rid, user_id)
            lines_changed = cursor.execute(delete_statement)
            db_connection.commit()
            if lines_changed <= 0:
                raise ValueError("删除错误,没有记录被删除>…<")
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify(str(e))
        else:
            db_connection.close()
            if annex_file_path:
                file_local_path = os.path.join(BASE_DIR, annex_file_path)
                if os.path.isfile(file_local_path):
                    os.remove(file_local_path)
            return jsonify("删除成功^.^!")


class InvestmentExportView(MethodView):
    def get(self):
        params = request.args
        utoken = params.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify("登录已过期!刷新网页重新登录."), 400
        try:
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            end_date = (end_date + datetime.timedelta(seconds=-1)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return jsonify("参数错误:DATE FORMAT ERROR!")

        query_statement = "SELECT usertb.name,usertb.org_id,invstb.custom_time,invstb.title,invstb.variety_id,invstb.contract,invstb.direction,invstb.build_time,invstb.build_price," \
                          "invstb.build_hands,invstb.out_price,invstb.cutloss_price,invstb.expire_time,invstb.is_publish,invstb.profit,invstb.note " \
                          "FROM `user_info` AS usertb INNER JOIN `investment` AS invstb ON " \
                          "usertb.id=%s AND usertb.id=invstb.author_id AND (invstb.custom_time BETWEEN %s AND %s) " \
                          "ORDER BY invstb.custom_time ASC;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询品种
        query_variety = "SELECT `id`,`name` FROM `variety` WHERE `parent_id` IS NOT NULL;"
        cursor.execute(query_variety)
        variety_all = cursor.fetchall()
        variety_dict = {variety_item["id"]: variety_item['name'] for variety_item in variety_all}
        cursor.execute(query_statement, (user_info['uid'], start_date, end_date))
        records_all = cursor.fetchall()
        db_connection.close()
        # 生成承载数据的文件
        t = "%.4f" % time.time()
        md5_hash = hashlib.md5()
        md5_hash.update(t.encode('utf-8'))
        md5_hash.update(user_info['name'].encode('utf-8'))
        md5_str = md5_hash.hexdigest()
        file_folder = os.path.join(BASE_DIR, 'fileStore/exports/')
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        file_path = os.path.join(file_folder, '{}.xlsx'.format(md5_str))

        file_records = list()
        for record_item in records_all:
            row_content = list()
            row_content.append(record_item['custom_time'].strftime("%Y-%m-%d"))
            row_content.append(ORGANIZATIONS.get(record_item['org_id'], '未知'))
            row_content.append(record_item['name'])
            row_content.append(record_item['title'])
            row_content.append(variety_dict.get(record_item['variety_id'],''))
            row_content.append(record_item['contract'])
            row_content.append(record_item['direction'])
            row_content.append(record_item['build_time'].strftime("%Y-%m-%d %H:%M"))
            row_content.append(float(record_item['build_price']))
            row_content.append(record_item['build_hands'])
            row_content.append(float(record_item['out_price']))
            row_content.append(float(record_item['cutloss_price']))
            row_content.append(record_item['expire_time'].strftime("%Y-%m-%d %H:%M"))
            row_content.append("是" if record_item['is_publish'] else "否")
            row_content.append(float(record_item['profit']))
            row_content.append(record_item['note'])
            file_records.append(row_content)

        export_df = pd.DataFrame(file_records)
        export_df.columns = ['日期', '部门小组', '姓名', '标题', '品种', '合约','方向', '实建日期','实建均价','实建手数','实出均价','止损均价',
                             '有效期','外发情况','方案结果','备注']
        export_df.to_excel(
            excel_writer=file_path,
            index=False,
            sheet_name='投资方案记录'
        )

        return send_from_directory(directory=file_folder, filename='{}.xlsx'.format(md5_str),
                                   as_attachment=True, attachment_filename='{}.xlsx'.format(md5_str)
                                   )
