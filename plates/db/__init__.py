# _*_ coding:utf-8 _*_
# Author: zizle

""" 数据库交互 """

# _*_ coding:utf-8 _*_
# Author: zizle

from pymysql import connect
from pymysql.cursors import DictCursor
import settings


class MySQLConnection(object):
    def __init__(self):
        db_params = settings.DATABASES.get('mysql')
        self._db = connect(
            host=db_params['HOST'],
            user=db_params['USER'],
            password=db_params['PASSWORD'],
            database=db_params['NAME'],
            port=db_params['PORT'],
        )
        self.cursor = self._db.cursor(DictCursor)  # 传入字典形式的cursor返回的是字典

    # 获取游标
    def get_cursor(self):
        return self.cursor

    # 关闭游标,断开连接
    def close(self):
        self.cursor.close()
        self._db.close()

    # 开启事务
    def begin(self):
        self._db.begin()

    # 事务回滚
    def rollback(self):
        self._db.rollback()

    # 提交事务
    def commit(self):
        self._db.commit()
