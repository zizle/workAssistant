# _*_ coding:utf-8 _*_
# Author: zizle


from flask import Flask
from plates.abnormal import abnormal_blp
from plates.users import user_blp
from plates.basic import basic_blp
from plates.monographic import monograohic_blp
from plates.investment import investment_blp
from plates.investrategy import investrategy_blp
from plates.article_publish import article_publish_blp
from plates.short_message import shortmsg_blp
from flask_cors import CORS
from utils.log_handler import config_logger_handler

app = Flask(__name__)

CORS(app, supports_credemtials=True)  # 支持跨域
app.config['JSON_AS_ASCII'] = False  # json返回数据支持中文

app.logger.addHandler(config_logger_handler())  # 配置日志

# 主页
@app.route('/')
def index():
    return "HELLO WORK ASSISTANT!"

app.register_blueprint(user_blp)
app.register_blueprint(abnormal_blp)
app.register_blueprint(basic_blp)
app.register_blueprint(monograohic_blp)
app.register_blueprint(investment_blp)
app.register_blueprint(investrategy_blp)
app.register_blueprint(article_publish_blp)
app.register_blueprint(shortmsg_blp)

if __name__ == '__main__':
    print(app.url_map)
    app.run()
