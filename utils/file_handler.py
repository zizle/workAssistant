# _*_ coding:utf-8 _*_
# __Author__： zizle
import time
from hashlib import md5


def hash_file_name(filename):
    filename_list = filename.rsplit('.', 1)
    t = "%.4f" % time.time()
    md5_hash = md5()
    md5_hash.update(t.encode('utf-8'))
    md5_hash.update(filename_list[0].encode('utf-8'))
    return md5_hash.hexdigest() + '.' + filename_list[1]
