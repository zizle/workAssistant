# _*_ coding:utf-8 _*_
# Author: zizle


from flask import Flask
from plates.abnormal import abnormal_blp
from plates.users import user_blp
from plates.basic import basic_blp
from flask_cors import CORS
from utils.log_handler import config_logger_handler

app = Flask(__name__)

CORS(app, supports_credemtials=True)  # 支持跨域
app.config['JSON_AS_ASCII'] = False  # json返回数据支持中文

app.logger.addHandler(config_logger_handler())  # 配置日志

# 主页
@app.route('/')
def index():
    return "hello work Assistant!"

# 用户板块
app.register_blueprint(user_blp)
# 非常态工作板块
app.register_blueprint(abnormal_blp)
# 系统基础信息支持板块
app.register_blueprint(basic_blp)


if __name__ == '__main__':
    print(app.url_map)
    app.run()
