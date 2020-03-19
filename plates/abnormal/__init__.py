# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import testView

"""
非常态工作任务功能模块
"""

abnormal_blp = Blueprint(name='abnormal', import_name=__name__, url_prefix='/abnormal/')
abnormal_blp.add_url_rule('', view_func=testView.as_view(name=""))


# @abnormal_blp.before_app_first_request
# def before_first_request():
#     print('第一个请求的事前处理钩子')
#
#
# @abnormal_blp.before_request
# def before_request():
#     print('请求的事前处理钩子')
#
#
# @abnormal_blp.after_request
# def after_request(response):
#     print(response)
#     print('请求后处理钩子')
#     return response


