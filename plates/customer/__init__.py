# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-08-13 13:29
# @Author: zizle

""" 客户开发 """
from flask import Blueprint

from .retrieve import CustomerView, CustomerCrightsView

customer_blp = Blueprint(name='customer', import_name=__name__, url_prefix='')

customer_blp.add_url_rule('customer/', view_func=CustomerView.as_view(name="customer"))  # 客户视图(创建)
customer_blp.add_url_rule('customer/<int:cid>/crights/', view_func=CustomerCrightsView.as_view(name="cright"))  # 单个客户视图
