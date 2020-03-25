# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import MonographicView

"""
非常态工作任务功能模块
"""

monograohic_blp = Blueprint(name='mogp', import_name=__name__, url_prefix='/')
monograohic_blp.add_url_rule('monographic/', view_func=MonographicView.as_view(name="mogc"))



