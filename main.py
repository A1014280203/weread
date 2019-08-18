import os
import time

import cv2

from model import Post, Book, DBC
from weread import WeRead


# 授权完成
# ——开始
# 实例化
# 爬取
# 存储
# 释放内存
# 等待
# ——回到开始


def authorization():
    if os.path.exists("./WeRead.json"):
        WeRead.load()
    else:
        WeRead.get_signature()
        WeRead.get_uuid_and_qrcode()
        wait_for_scanning(WeRead.qrcode_path)
        WeRead.get_wxcode()
        WeRead.get_token()
        WeRead.save()


def wait_for_scanning(filename):
    img = cv2.imread(filename)
    cv2.imshow("QR", img)
    cv2.waitKey()
    cv2.destroyAllWindows()


def get_mps():
    books = DBC().query_all_pretty(Book)
    mps = list()
    for book in books:
        mp = WeRead(**book)
        mps.append(mp)
    return mps


def wait_for(minutes: float):
    time.sleep(minutes*60)


def update_by_mp(mps: [WeRead, ]):
    dbc = DBC()
    for mp in mps:
        mp.update_articles()
        [dbc.add(Post(**a)) for a in mp.dump_articles()]
        dbc.commit()
        wait_for(5)
    dbc.close_session()


def work_on(check_points: [int, ], mps):
    while True:
        if time.localtime().tm_hour in check_points:
            update_by_mp(mps)
        wait_for(60*10)


def update_slightly():
    """
    Fetch WeRead from database, update it and then discard it one after another.
    In this way, lower memory will cost, of course, memory operations may be more frequent
    """
    pass


# todo: find a better way to func: wait_for_scanning

if __name__ == "__main__":
    authorization()
    mps = get_mps()
    work_on([22, 11], mps)
