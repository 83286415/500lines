import os

from dbdb.interface import DBDB


__all__ = ['DBDB', 'connect']  # 表示在import dbdb时，只会import DBDB类和connect方法


def connect(dbname):
    try:
        f = open(dbname, 'r+b')
    except IOError:
        fd = os.open(dbname, os.O_RDWR | os.O_CREAT)
        # O_RDWR只读打开 O_CREAT创建并打开 http://www.runoob.com/python/os-open.html
        f = os.fdopen(fd, 'r+b')  # # http://www.runoob.com/python/os-fdopen.html
    return DBDB(f)
