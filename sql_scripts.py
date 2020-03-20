# _*_ coding:utf-8 _*_
# Author: zizle

from db import MySQLConnection


""" 创建数据库表信息 """


def create_tables():
    # 连接mysql
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 系统模块信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `work_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(32) NOT NULL,"
                   "`page_url` VARCHAR (255) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "`is_private` BIT NOT NULL DEFAULT 0"
                   ")")

    # 创建部门信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `organization_group` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(255) NOT NULL UNIQUE"
                   ");")

    # 创建用户信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `user_info` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(255) NOT NULL UNIQUE,"
                   "`fixed_code` VARCHAR(8) NOT NULL UNIQUE,"
                   "`join_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                   "`password` VARCHAR(32) NOT NULL,"
                   "`is_admin` BIT NOT NULL DEFAULT 0,"
                   "`org_id` INTEGER DEFAULT 0"
                   ")")

    # 用户与不用提交的模块第三方表
    cursor.execute("CREATE TABLE IF NOT EXISTS `user_ndo_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INTEGER NOT NULL,"
                   "`module_id` INTEGER NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `user_id`(`user_id`,`module_id`)"
                   ")")


    # 加入部门小组信息数据
    save_org = "INSERT INTO organization_group (name) VALUES %s;" % ("('宏观金融'),('化工小组'),('农产品组'),('金属小组'),('创新部门')")
    cursor.execute(save_org)
    # 提交数据
    db_connection.commit()
    db_connection.close()  # 关闭数据库连接


if __name__ == '__main__':
    create_tables()