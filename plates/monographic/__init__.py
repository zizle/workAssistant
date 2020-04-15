# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint

from .views import MonographicView, MonographicExportView, RetrieveMonographicView

"""
专题研究功能模块
"""

monograohic_blp = Blueprint(name='mogp', import_name=__name__, url_prefix='/')
monograohic_blp.add_url_rule('monographic/', view_func=MonographicView.as_view(name="mogc"))
monograohic_blp.add_url_rule('monographic/<int:rid>/', view_func=RetrieveMonographicView.as_view(name="retrievemogc"))
monograohic_blp.add_url_rule('monographic/export/', view_func=MonographicExportView.as_view(name="mogcexport"))



