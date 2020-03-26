# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import ShortMessageView

"""
短讯通功能模块
"""

shortmsg_blp = Blueprint(name='shortmsg', import_name=__name__, url_prefix='/')
shortmsg_blp.add_url_rule('short-message/', view_func=ShortMessageView.as_view(name="shortmsg"))



