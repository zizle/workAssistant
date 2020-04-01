# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .abnormal_work import StuffAbnormalWorkAmount
from .monographic import MonographicWorkAmount
from .investment import InvestmentAmount
from .investrategy import InvestrategyAmount
from .contribute_article import DistributeArticleAmount
from .shormessage import ShortMessageAmount

"""
非常态工作任务功能模块
"""

statistics_blp = Blueprint(name='statistics', import_name=__name__, url_prefix='/')
statistics_blp.add_url_rule('statistics/abwork/', view_func=StuffAbnormalWorkAmount.as_view(name="abw"))
statistics_blp.add_url_rule('statistics/monographic/', view_func=MonographicWorkAmount.as_view(name="moghic"))
statistics_blp.add_url_rule('statistics/investment/', view_func=InvestmentAmount.as_view(name="investmentcount"))
statistics_blp.add_url_rule('statistics/investrategy/', view_func=InvestrategyAmount.as_view(name="investrategycount"))
statistics_blp.add_url_rule('statistics/distribute-article/', view_func=DistributeArticleAmount.as_view(name="disartcount"))
statistics_blp.add_url_rule('statistics/shortmessage/', view_func=ShortMessageAmount.as_view(name="srtmsgcount"))

