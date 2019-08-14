import requests
from requests.exceptions import HTTPError
import urllib.parse as urlparse
import base64
import time
from PIL import Image


class StateError(HTTPError):
    pass


class AuthError(HTTPError):

    def __init__(self, resp):
        super().__init__(resp)
        self.response = resp


class WeRead(object):
    SIGNATURE_URL = "https://i.weread.qq.com/wxticket"
    QRCONNECT_URL = "https://open.weixin.qq.com/connect/sdk/qrconnect"
    LONG_QRCONNECT_URL = "https://long.open.weixin.qq.com/connect/l/qrconnect"
    TOKEN_URL = "https://i.weread.qq.com/login"
    REFRESH_TOKEN_URL = "https://i.weread.qq.com/login"
    REVIEWID_URL = "https://i.weread.qq.com/mp/read"
    ARTICLE_URL = "https://i.weread.qq.com/book/articles"

    weopen_headers = {
        "Host": "open.weixin.qq.com",
        "Connection": "Keep-Alive",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE(java 1.4)"
    }

    weread_headers = {
        "osver": "6.0.1",
        "appver": "3.4.0.10135763",
        "basever": "3.4.0.10135763",
        "beta": "0",
        "channelId": "248",
        "User-Agent": "WeRead/3.4.0 WRBrand/Android Dalvik/2.1.0",
        "Host": "i.weread.qq.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    wemp_headers = {
        "Host": "mp.weixin.qq.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.12.1"
    }

    def __init__(self):
        self.nonceStr = "weread"
        self.appid = "wxab9b71ad2b90ff34"
        self.deviceId = "3337192264877969242486422277"
        self.mailDeviceId = "3577139267462447713926746244"
        self.scope = "snsapi_userinfo,snsapi_timeline,snsapi_friend"
        self.__sign = {"signature": "", "timestamp": 0, "expires_in": 0}
        self.__uuid = ""
        self.qrcode_path = "image's filename"
        self.wx_code = "exchange for token"
        self.token = {}
        self.articles = {}

    def get_signature(self):
        params = {"nonceStr": self.nonceStr}
        resp = requests.get(self.SIGNATURE_URL, params, headers=self.weread_headers)
        self.__sign["signature"] = resp.json()["signature"]
        self.__sign["timestamp"] = resp.json()["timeStamp"]
        self.__sign["expires_in"] = resp.json()["expires_in"]

    def get_uuid_and_qrcode(self):
        params = {
            "appid": self.appid,
            "noncestr": self.nonceStr,
            "timestamp": self.__sign["timestamp"],
            "scope": self.scope,
            "signature": self.__sign["signature"]
        }
        resp = requests.get(self.QRCONNECT_URL, params, headers=self.weopen_headers)
        self.__uuid = resp.json()["uuid"]
        self.qrcode_path = self.parse_qrcode(resp.json()["qrcode"]["qrcodebase64"])

    def get_wxcode(self):
        params = {
            "f": "json",
            "uuid": self.__uuid,
        }
        resp = requests.get(self.LONG_QRCONNECT_URL, params, headers=self.weopen_headers)
        print(resp.json())
        if not resp.json()["wx_code"]:
            time.sleep(0.5)
            params["last"] = 404
            resp = requests.get(self.LONG_QRCONNECT_URL, params, headers=self.weopen_headers)
            print(resp.json())
            if not resp.json()["wx_code"]:
                time.sleep(0.5)
                params["last"] = 404
                # supposed to success here
                resp = requests.get(self.LONG_QRCONNECT_URL, params, headers=self.weopen_headers)
                print(resp.json())
        self.wx_code = resp.json()["wx_code"]

    def get_token(self):
        data = {
            "code": self.wx_code,
            "deviceId": self.deviceId,
            "mailDeviceId": self.mailDeviceId,
            "random": 937,
            "signature": self.__sign["signature"],
            "timestamp": self.__sign["timestamp"],
            "trackId": ""
        }
        resp = requests.post(self.TOKEN_URL, json=data, headers=self.weread_headers)
        self.token = resp.json()

    def refresh_token(self, ref="/pay/memberCardSummary"):
        data = {
            "deviceId": self.deviceId,
            "inBackground": 0,
            "kickType": 1,
            "random": 46,
            "refCgi": ref,
            "refreshToken": self.token["refreshToken"],
            "signature": self.__sign["signature"],  # 只需要重新请求签名
            "timestamp": self.__sign["timestamp"],
            "trackId": "",
            "wxToken": 0
        }

        resp = requests.post(self.REFRESH_TOKEN_URL, json=data, headers=self.weread_headers)
        self.token["accessToken"] = resp.json()["accessToken"]
        self.token["skey"] = resp.json()["skey"]

    def get_articles(self, share_url):
        headers_add = {
            "accessToken": self.token["accessToken"],
            "vid": "1731234"
        }
        headers = self.weread_headers.copy()
        headers.update(headers_add)
        params = {
            "bookId": self.get_book_id(share_url),
            "count": 10,
            "createTime": 1565011808,
            "synckey": int(time.time()),
            "maxIdx": 1562945115,
            "topshelf": 0
        }
        resp = requests.get(self.ARTICLE_URL, params, headers=headers)
        self.articles = resp.json()
        return self.articles

    def get_book_id(self, share_url):
        if not self.is_article_available(share_url):
            return
        review_id = self.get_review_id(share_url)
        book_id = '_'.join(review_id.split('_')[:-1])
        return book_id

    def get_review_id(self, share_url) -> str:
        headers_add = {
            "accessToken": self.token["accessToken"],
            "vid": "1731234"
        }
        headers = self.weread_headers.copy()
        headers.update(headers_add)
        data = {"account": "", "isDelete": 0, "reviewId": "", "thumbUrl": "", "title": "",
                "url": share_url
                }
        resp = requests.post(self.REVIEWID_URL, json=data, headers=headers)
        return resp.json()["reviewId"]

    def is_article_available(self, share_url):
        resp = requests.get(share_url, headers=self.wemp_headers)
        if resp.cookies.get("wxtokenkey", None) is not None:
            if resp.cookies.get("LogicRet") != "0":
                return True
        return False

    def parse_qrcode(self, qrcode_base64):
        b = base64.standard_b64decode(qrcode_base64)
        filename = "qrcode_{0}.jpg".format(int(time.time()))
        with open(filename, "wb") as fw:
            fw.write(b)
        return filename

    def parse_url_host(self, url):
        return urlparse.urlparse(url)[1]


# todo: update properties about user authentication as class-property
# todo: use one instance to process one mp and keep infos of it
# todo: consider initializing instance from database as well as committing itself to database

if __name__ == "__main__":
    # w = WeRead()
    # w.get_signature()
    # time.sleep(0.2)
    # w.get_uuid_and_qrcode()
    # input("Press to continue")
    # w.get_wxcode()
    # time.sleep(0.5)
    # w.get_token()
    # print(w.token)
    w = WeRead()
    w.get_book_id("https://mp.weixin.qq.com/s/glP9GhITiResIC86FmAWEQ")
