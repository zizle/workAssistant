# _*_ coding:utf-8 _*_
# Author: zizle
# Flask要求app得是一个包
# 文档中有这么一句话："你的应用可能是一个你符号链接到site-packages文件夹的单个.py文件。
# 请注意这不会正常工作，除非把这个文件放进pythonpath包含的文件夹中，或是把应用转换成一个包。
# 这个问题同样适用于非安装的包，模块文件名用于定位资源，而符号链接会获取错误的文件名。"
from flask import Flask,redirect
from plates.abnormal import abnormal_blp
from plates.users import user_blp
from plates.basic import basic_blp
from plates.monographic import monograohic_blp
from plates.investment import investment_blp
from plates.investrategy import investrategy_blp
from plates.article_publish import article_publish_blp
from plates.short_message import shortmsg_blp
from plates.statistics import statistics_blp
from flask_cors import CORS
from utils.log_handler import config_logger_handler

app = Flask(__name__)

CORS(app, supports_credemtials=True)  # 支持跨域
app.config['JSON_AS_ASCII'] = False  # json返回数据支持中文

app.logger.addHandler(config_logger_handler())  # 配置日志

# 主页
@app.route('/')
def index():
    return redirect("/static/index.html")  # 重定向

app.register_blueprint(user_blp)
app.register_blueprint(abnormal_blp)
app.register_blueprint(basic_blp)
app.register_blueprint(monograohic_blp)
app.register_blueprint(investment_blp)
app.register_blueprint(investrategy_blp)
app.register_blueprint(article_publish_blp)
app.register_blueprint(shortmsg_blp)
app.register_blueprint(statistics_blp)

if __name__ == '__main__':
    app.run()

