import time
from weread import WeRead
from model import Post, Book
import cv2


# 授权完成
# ——开始
# 实例化
# 爬取
# 存储
# 释放内存
# 等待
# ——回到开始


def authorization():
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
    books = Book().query_all_json()
    mps = list()
    for book in books:
        mp = WeRead(**book)
        mps.append(mp)
    return mps


def wait_for(sec: float):
    time.sleep(sec)


def update_by_mp(mps: [WeRead, ]):
    p = Post()
    for mp in mps:
        mp.update_articles()
        p.add(mp.dump_articles())
        p.commit()
        wait_for(60*5)
    p.close_session()


def work_on(check_points: [int, ], mps):
    while True:
        if time.localtime().tm_hour in check_points:
            update_by_mp(mps)
        time.sleep(60*60)


if __name__ == "__main__":
    authorization()
    mps = get_mps()
    work_on([22, 11], mps)

# todo: update mps by bid
# todo: unbound model and db control
