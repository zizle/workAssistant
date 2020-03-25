# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .views import RegisterView, OrganizationGroupView, LoginView, UserView,RetrieveUserView,RetrieveUserModuleView,\
    RetrieveUMView,ParserUserTokenView

user_blp = Blueprint(name='user', import_name=__name__, url_prefix='')

# 返回业务部门小组信息
user_blp.add_url_rule('org/', view_func=OrganizationGroupView.as_view(name="org"))
# 用户注册
user_blp.add_url_rule('register/', view_func=RegisterView.as_view(name="reg"))
# 用户登录
user_blp.add_url_rule('login/', view_func=LoginView.as_view(name="login"))
user_blp.add_url_rule('users/', view_func=UserView.as_view(name='users'))
user_blp.add_url_rule('user/<int:user_id>/', view_func=RetrieveUserView.as_view(name='ruser'))
user_blp.add_url_rule('user/<int:user_id>/module/', view_func=RetrieveUserModuleView.as_view(name='userworking'))
user_blp.add_url_rule('user/<int:user_id>/module/<int:module_id>/', view_func=RetrieveUMView.as_view(name='um'))
user_blp.add_url_rule('user/parse-token/', view_func=ParserUserTokenView.as_view(name='pst'))




# 第一个请求之前处理的事情

"""

# 查看数据库中是否有部门小组信息表、用户信息表、品种表、系统模块记录表
# 如果没有这些表，则创建表

"""

