# _*_ coding:utf-8 _*_
# Author: zizle
import jwt
import time
import random
from hashlib import md5
from settings import SECRET_KEY

# hash密码
def hash_user_password(password):
    hasher = md5()
    hasher.update(password.encode('utf-8'))
    hasher.update(SECRET_KEY.encode('utf-8'))
    print('输入密码hash后：', hasher.hexdigest())
    return hasher.hexdigest()


# 检查密码
def check_user_password(password, real_password):
    print("用户输入密码：", password)
    print('数据库密码：', real_password)
    if hash_user_password(password) == real_password:
        return True
    else:
        return False


def generate_string_with_time(org_id, len):
    """
    # 以时间戳hash生成固定位数的字符串
    :param org_id: 前缀整数
    :param len: 生成的长度
    :return: 结果
    """
    result_str = "%02d" % org_id
    t = "%.4f" % time.time()
    md5_hash = md5()
    md5_hash.update(t.encode('utf-8'))
    md5_str = md5_hash.hexdigest()
    for i in range(len):
        result_str += random.choice(md5_str)
    return result_str


def verify_json_web_token(token):
    if not token:
        return {}
    try:
        data = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=['HS256']
        )
    except Exception as e:
        print(e)
        return {}
    else:
        return data

# 管理员用户验证
def user_is_admin(token):
    if not token:
        return False
    user_info = verify_json_web_token(token)
    if user_info.get('is_admin'):
        return True
    else:
        return False


if __name__ == '__main__':
    print(generate_string_with_time(2, 6))