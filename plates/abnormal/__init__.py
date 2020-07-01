# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint

from .examine import ExamineWorkRecord
from .views import AbnormalWorkView, FileHandlerAbnormalWorkView, ExportAbnormalWorkView, RetrieveAbWorkView

"""
非常态工作任务功能模块
"""

abnormal_blp = Blueprint(name='abnormal', import_name=__name__, url_prefix='/')
abnormal_blp.add_url_rule('abnormal-work/', view_func=AbnormalWorkView.as_view(name="push"))
abnormal_blp.add_url_rule('abnormal-work/<int:work_id>/', view_func=RetrieveAbWorkView.as_view(name="putabw"))
# abnormal_blp.add_url_rule('abnormal-work/file/', view_func=FileHandlerAbnormalWorkView.as_view(name="pushf"))
abnormal_blp.add_url_rule('abnormal-work/export/', view_func=ExportAbnormalWorkView.as_view(name="exportf"))

abnormal_blp.add_url_rule('abnormal-work/examine/', view_func=ExamineWorkRecord.as_view(name="abwexamine"))  # 审核非常态工作









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


