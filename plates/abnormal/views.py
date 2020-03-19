# _*_ coding:utf-8 _*_
# Author: zizle
from flask import jsonify
from flask.views import MethodView

# 视图


# 蓝图的测试视图
class testView(MethodView):
    def get(self):
        print("进入视图函数")
        return jsonify("这是非常态工作任务的GET测试视图"), 400
