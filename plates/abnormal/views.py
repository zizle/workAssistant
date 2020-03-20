# _*_ coding:utf-8 _*_
# Author: zizle
from flask import jsonify,current_app
from flask.views import MethodView




# 蓝图的测试视图
class testView(MethodView):
    def get(self):
        logger = current_app.logger  # 必须卸载请求内部，此时请求发起，上下文AppContext入栈才有current_app
        try:
            raise RuntimeError("RuntimeError错误")
        except Exception as e:
            logger.debug("debug:" + str(e))
        print("进入视图函数")
        # 测试写入日志
        logger.info("这是一个info日志")
        logger.error("这是一个error日志")
        logger.warning('这是一个warning日志')

        return jsonify("这是非常态工作任务的GET测试视图"), 200
