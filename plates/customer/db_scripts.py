# _*_ coding:utf-8 _*_
# @File  : db_scripts.py
# @Time  : 2020-08-13 13:38
# @Author: zizle

""" 初始化创建数据库的脚本 """

from db import MySQLConnection

db_connection = MySQLConnection()
cursor = db_connection.get_cursor()

# 客户数据库
cursor.execute("CREATE TABLE IF NOT EXISTS `info_customer` ("
               "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
               "`create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
               "`name` VARCHAR(128) NOT NULL,"
               "`account` VARCHAR(256) NOT NULL,"
               "`belong_user` INT(11) NOT NULL,"
               "`note` VARCHAR(512) NOT NULL DEFAULT ''"
               ");")

# 客户权益表
cursor.execute("CREATE TABLE IF NOT EXISTS `customer_rights` ("
               "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
               "`create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
               "`custom_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
               "`customer_id` INT(11) NOT NULL,"
               "`remain` DECIMAL(11, 2) NOT NULL DEFAULT 0,"
               "`interest` DECIMAL(11, 2) NOT NULL DEFAULT 0,"
               "`crights` DECIMAL(11, 2) NOT NULL DEFAULT 0,"
               "`note` VARCHAR(1024) NOT NULL DEFAULT ''"
               ");")

db_connection.close()
