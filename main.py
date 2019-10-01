import os
import time
from model import Post, Book, DBC
from weread import WeRead
import random


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
        WeRead.load_auth()
    else:
        WeRead.authorize()
        WeRead.dump_auth()


def get_mps():
    books = DBC().query_all_pretty(Book)
    return [WeRead(**book) for book in books]


def wait_for(minutes: float):
    time.sleep(minutes*60)


def update_by_mps(mps: [WeRead, ]):
    dbc = DBC()
    WeRead.refresh_login()
    for mp in mps:
        print("main: update posts of book:", mp.bid)
        mp.update_articles()
        for a in mp.dump_articles():
            if a["title"] == a["content"]:
                a["title"] = a["title"][:35]
            dbc.add(Post(**a))
        dbc.commit()
        print("main: update book:", mp.bid)
        dbc.update(Book, "bid", mp.dump_book())
        dbc.commit()
        wait_for(random.randint(3, 10))
    WeRead.dump_auth()
    dbc.close_session()


def work_on(check_points: [int, ]):
    while True:
        print("check time", time.ctime(), flush=True)
        if time.localtime().tm_hour in check_points:
            mps = get_mps()
            random.shuffle(mps)
            update_by_mps(mps)
        print("update done", flush=True)
        wait_for(60)


if __name__ == "__main__":
    authorization()

    work_on([i for i in range(0, 24, 2)])
