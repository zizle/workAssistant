# _*_ coding:utf-8 _*_
# Author: zizle

from db import MySQLConnection


""" 创建数据库表信息 """


def initial_tables_and_data():
    # 连接mysql
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 系统模块信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `work_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(32) NOT NULL,"
                   "`page_url` VARCHAR (255) DEFAULT '',"
                   "`sort` INT(11) NOT NULL DEFAULT 0,"
                   "`parent_id` INT(11) DEFAULT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "`is_private` BIT NOT NULL DEFAULT 0"
                   ")")

    # 创建部门信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `organization_group` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(255) NOT NULL UNIQUE,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
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
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "`org_id` INT(11) DEFAULT 0"
                   ")")

    # 用户与不用提交的模块第三方表
    cursor.execute("CREATE TABLE IF NOT EXISTS `user_ndo_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INT(11) NOT NULL,"
                   "`module_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `user_id`(`user_id`,`module_id`)"
                   ")")

    """添加系统默认菜单"""
    # 加入系统设置菜单组
    save_module = "INSERT INTO `work_module` (`name`,`page_url`,`parent_id`) VALUES ('系统设置','',NULL);"
    cursor.execute(save_module)
    new_mid = db_connection.insert_id()  # 返回的id
    # 修改sort
    update_sort_statement = "UPDATE `work_module` SET `sort`=%s WHERE `id`=%s;"
    cursor.execute(update_sort_statement,(new_mid, new_mid))
    # 插入系统模块管理
    insert_statement = "INSERT INTO `work_module` (`name`,`page_url`,`parent_id`) VALUES ('系统模块管理','sys-modules.html',%s);"
    cursor.execute(insert_statement,(new_mid,))
    new_mid = db_connection.insert_id() # 返回的id
    # 修改sort字段的值
    update_sort_statement = "UPDATE `work_module` SET `sort`=%s WHERE `id`=%s;"
    cursor.execute(update_sort_statement,(new_mid,new_mid))

    """添加系统默认部门小组的信息"""
    # 加入部门小组信息数据
    save_org = "INSERT INTO `organization_group` (`name`) VALUES %s;" % ("('宏观金融'),('化工小组'),('农产品组'),('金属小组'),('创新部门')")
    cursor.execute(save_org)
    """添加一个默认管理员信息"""
    # 新增一个管理员信息
    save_admin = "INSERT INTO `user_info` (`name`,`fixed_code`,`password`,`is_admin`) VALUES ('管理员','abc123','bbe7977cef5fcf80a39b801fcfdda5e0', 1);"
    cursor.execute(save_admin)

    # 提交数据
    db_connection.commit()
    db_connection.close()  # 关闭数据库连接


def create_not_normal_work_table():
    # 连接mysql
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()

    # 创建非常规工作信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `abnormal_work` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`work_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`worker` INT(11) NOT NULL,"
                   "`task_type` INT (11) NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL,"
                   "`sponsor` VARCHAR(64) DEFAULT '',"
                   "`applied_org` VARCHAR (128) DEFAULT '',"
                   "`applicant` VARCHAR (64) DEFAULT '',"
                   "`tel_number` VARCHAR (128) DEFAULT '',"
                   "`swiss_coin` INT(11) DEFAULT 0,"
                   "`allowance` INT(11) DEFAULT 0,"
                   "`note` VARCHAR(512) DEFAULT '',"
                   "`partner` VARCHAR (128) DEFAULT ''"
                   ")")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    # initial_tables_and_data()
    create_not_normal_work_table()

