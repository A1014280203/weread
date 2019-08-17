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


def wait_for_scanning(filename):
    img = cv2.imread(filename)
    cv2.imshow("QR", img)
    cv2.waitKey()
    cv2.destroyAllWindows()


def authorization():
    WeRead.get_signature()
    WeRead.get_uuid_and_qrcode()
    wait_for_scanning(WeRead.qrcode_path)
    WeRead.get_wxcode()
    WeRead.get_token()
