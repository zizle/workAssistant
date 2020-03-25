# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import BasicModuleView, RetrieveModuleView,NoNormalWorkTaskTypeView,VarietyView

"""
系统基本数据支持
"""


basic_blp = Blueprint(name='basic', import_name=__name__, url_prefix='')
basic_blp.add_url_rule('module/', view_func=BasicModuleView.as_view(name="module"))
basic_blp.add_url_rule('module/<int:module_id>/', view_func=RetrieveModuleView.as_view(name='mdymd'))
basic_blp.add_url_rule('nonormal-work/task-type/', view_func=NoNormalWorkTaskTypeView.as_view(name='nottp'))
basic_blp.add_url_rule('variety/', view_func=VarietyView.as_view(name='variety'))