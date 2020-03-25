# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import InvestmentView

"""
投资方案撰写功能模块
"""

investment_blp = Blueprint(name='ivst', import_name=__name__, url_prefix='/')
investment_blp.add_url_rule('investment/', view_func=InvestmentView.as_view(name="ivst"))


