# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .abnormal_work import StuffAbnormalWorkAmount

"""
非常态工作任务功能模块
"""

statistics_blp = Blueprint(name='statistics', import_name=__name__, url_prefix='/')
statistics_blp.add_url_rule('statistics/abwork/', view_func=StuffAbnormalWorkAmount.as_view(name="abw"))

