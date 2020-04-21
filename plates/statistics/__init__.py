# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint

from .abnormal_work import StuffAbnormalWorkAmount
from .contribute_article import DistributeArticleAmount
from .investment import InvestmentAmount
from .investrategy import InvestrategyAmount
from .monographic import MonographicWorkAmount
from .ondutymsg import OnDutyMessageAmount
from .query_stuff import QueryStuffRecordView
from .shormessage import ShortMessageAmount

statistics_blp = Blueprint(name='statistics', import_name=__name__, url_prefix='/')
statistics_blp.add_url_rule('statistics/abwork/', view_func=StuffAbnormalWorkAmount.as_view(name="abwm"))
statistics_blp.add_url_rule('statistics/monographic/', view_func=MonographicWorkAmount.as_view(name="moghic"))
statistics_blp.add_url_rule('statistics/investment/', view_func=InvestmentAmount.as_view(name="investmentcount"))
statistics_blp.add_url_rule('statistics/investrategy/', view_func=InvestrategyAmount.as_view(name="investrategycount"))
statistics_blp.add_url_rule('statistics/distribute-article/', view_func=DistributeArticleAmount.as_view(name="disartcount"))
statistics_blp.add_url_rule('statistics/shortmessage/', view_func=ShortMessageAmount.as_view(name="srtmsgcount"))
statistics_blp.add_url_rule('statistics/ondutymsg/', view_func=OnDutyMessageAmount.as_view(name="ondmsgcount"))

statistics_blp.add_url_rule('statistics/query-stuff/', view_func=QueryStuffRecordView.as_view(name="querystuff"))
statistics_blp.add_url_rule('statistics/query-export/', vaiew_func=ExportStuffRecordView.as_view(name="exportstuff"))

