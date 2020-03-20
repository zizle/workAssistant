# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import RegisterView, OrganizationGroupView, LoginView

user_blp = Blueprint(name='user', import_name=__name__, url_prefix='')

# 返回业务部门小组信息
user_blp.add_url_rule('org/', view_func=OrganizationGroupView.as_view(name="org"))
# 用户注册
user_blp.add_url_rule('register/', view_func=RegisterView.as_view(name="reg"))
# 用户登录
user_blp.add_url_rule('login/', view_func=LoginView.as_view(name="login"))



# 第一个请求之前处理的事情

"""

# 查看数据库中是否有部门小组信息表、用户信息表、品种表、系统模块记录表
# 如果没有这些表，则创建表

"""

