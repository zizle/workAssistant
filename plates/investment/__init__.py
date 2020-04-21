# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint

from .views import InvestmentView, RetrieveInvestmentView, InvestmentExportView

"""
投资方案撰写功能模块
"""

investment_blp = Blueprint(name='ivst', import_name=__name__, url_prefix='/')
investment_blp.add_url_rule('investment/', view_func=InvestmentView.as_view(name="ivst"))
investment_blp.add_url_rule('investment/<int:rid>/', view_func=RetrieveInvestmentView.as_view(name="retrieveivst"))
investment_blp.add_url_rule('investment/export/', view_func=InvestmentExportView.as_view(name='ivstexport'))



