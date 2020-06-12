# _*_ coding:utf-8 _*_
# Author: zizle
import logging
import os

SECRET_KEY = "c7jgb1k2xzfq*3odq5my-vts^+cv+p7suw+(_5#va%f0=tt5mp"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASES = {
    'mysql2': {
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'assistant_worker',
        'PASSWORD': 'rdyj0327wa',
        'NAME': 'work_assistant'
    },
    'mysql': {
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': 'mysql',
        'NAME': 'work_assistant'
    },
    'redis': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DBINDEX': 0,
        'PASSWORD': ''
    },
    'sqlite': {
        'NAME': 'test.db'
    }
}
# DEBUG,INFO,WARNING,ERROR,CRITICAL

LOGGER_LEVEL = logging.DEBUG
# jwt的有效时间
JSON_WEB_TOKEN_EXPIRE = 1728000

EMAIL = 'rdyjwork@163.com'
EMAILPSD = 'DXLBPVLQTEQKOYEI'
