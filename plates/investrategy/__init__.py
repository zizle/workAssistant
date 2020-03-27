# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import InvestrategyView,FileHandlerInvestrategyView

"""
投顾策略功能模块
"""

investrategy_blp = Blueprint(name='ivstgy', import_name=__name__, url_prefix='/')
investrategy_blp.add_url_rule('investrategy/', view_func=InvestrategyView.as_view(name="ivstgy"))
investrategy_blp.add_url_rule('investrategy/file/', view_func=FileHandlerInvestrategyView.as_view(name="ivstgyf"))



