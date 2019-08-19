import base64
import json
import time

import requests


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

    nonceStr = "weread"
    appid = "wxab9b71ad2b90ff34"
    deviceId = "3337192264877969242486422277"
    mailDeviceId = "3577139267462447713926746244"
    scope = "snsapi_userinfo,snsapi_timeline,snsapi_friend"
    qrcode_path = "image's filename"
    sign = {"signature": "", "timestamp": 0, "expires_in": 0}
    uuid = ""
    wx_code = "exchange for token"
    token = {"vid": 1731234, "accessToken": "", "refreshToken": "", "skey": "", "openId": "",
             "user": {"name": "", "avatar": ""}, "firstLogin": 0, "userAgreement": 1, "from": "int, timestamp of token"}

    @classmethod
    def get_signature(cls):
        params = {"nonceStr": cls.nonceStr}
        resp = requests.get(cls.SIGNATURE_URL, params, headers=cls.weread_headers)
        cls.sign["signature"] = resp.json()["signature"]
        cls.sign["timestamp"] = resp.json()["timeStamp"]
        cls.sign["expires_in"] = resp.json()["expires_in"]

    @classmethod
    def get_uuid_and_qrcode(cls):
        params = {
            "appid": cls.appid,
            "noncestr": cls.nonceStr,
            "timestamp": cls.sign["timestamp"],
            "scope": cls.scope,
            "signature": cls.sign["signature"]
        }
        resp = requests.get(cls.QRCONNECT_URL, params, headers=cls.weopen_headers)
        cls.uuid = resp.json()["uuid"]
        cls.qrcode_path = cls.__parse_qrcode(resp.json()["qrcode"]["qrcodebase64"])
    
    @staticmethod
    def __parse_qrcode(qrcode_base64):
        b = base64.standard_b64decode(qrcode_base64)
        filename = "qrcode_{0}.jpg".format(int(time.time()))
        with open(filename, "wb") as fw:
            fw.write(b)
        return filename
    
    @classmethod
    def get_wxcode(cls):
        params = {
            "f": "json",
            "uuid": cls.uuid,
        }
        resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
        if not resp.json()["wx_code"]:
            time.sleep(0.5)
            params["last"] = 404
            resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
            if not resp.json()["wx_code"]:
                time.sleep(0.5)
                params["last"] = 404
                # supposed to success here
                resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
        cls.wx_code = resp.json()["wx_code"]
    
    @classmethod
    def get_token(cls):
        data = {
            "code": cls.wx_code,
            "deviceId": cls.deviceId,
            "mailDeviceId": cls.mailDeviceId,
            "random": 937,
            "signature": cls.sign["signature"],
            "timestamp": cls.sign["timestamp"],
            "trackId": ""
        }
        resp = requests.post(cls.TOKEN_URL, json=data, headers=cls.weread_headers)
        cls.token = resp.json()
        cls.token["from"] = int(time.time())

    @classmethod
    def __refresh_token(cls, ref="/pay/memberCardSummary"):
        data = {
            "deviceId": cls.deviceId,
            "inBackground": 0,
            "kickType": 1,
            "random": 46,
            "refCgi": ref,
            "refreshToken": cls.token["refreshToken"],
            "signature": cls.sign["signature"],
            "timestamp": cls.sign["timestamp"],
            "trackId": "",
            "wxToken": 0
        }

        resp = requests.post(cls.REFRESH_TOKEN_URL, json=data, headers=cls.weread_headers)
        cls.token["accessToken"] = resp.json()["accessToken"]
        cls.token["from"] = int(time.time())
        cls.token["skey"] = resp.json()["skey"]

    @classmethod
    def save(cls, path="./WeRead.json"):
        data = {
            "sign": cls.sign,
            "uuid": cls.uuid,
            "wx_code": cls.wx_code,
            "token": cls.token
        }
        with open(path, "w", encoding="utf-8") as fw:
            json.dump(data, fw)

    @classmethod
    def load(cls, path="./WeRead.json"):
        with open(path, "r", encoding="utf-8") as fr:
            data = json.load(fr)
            cls.sign = data["sign"]
            cls.uuid = data["uuid"]
            cls.wx_code = data["wx_code"]
            cls.token = data["token"]

    def __init__(self, bid, state, share_url="", bookId="", last_update=0):
        self.articles = {}
        self.bid = bid
        self.state = state
        self.last_update = last_update
        self.book_id = bookId
        self.share_url = share_url
        self.success = self.__is_article_available()

    @property
    def review_id(self):
        """
        Not support setting operation, just for a peek
        :return: str
        """
        if self.book_id:
            return self.book_id + "_" + self.share_url.split("_")[-1]

    def set_share_url(self, share_url):
        self.share_url = share_url
        self.success = self.__is_article_available()

    def update_articles(self):
        """
        Supposed to call this method rather than get_articles, if don't need return articles meantime.
        If post pointed by share url is invalid, method:get_articles won't fetch the articles with None returned.
        """
        self.get_articles()

    def get_articles(self):
        """
        ! user auth info needed
        Get 10, as count set, articles of the mp, which posted the share article.
        - accessToken will be updated every 1.5h by method:refresh_auth
        - normal http headers extended with user auth info
        :return:
        """
        if not self.success:
            return None
        self.__refresh_auth()
        headers_add = {
            "accessToken": self.token["accessToken"],
            "vid": "1731234"
        }
        headers = self.weread_headers.copy()
        headers.update(headers_add)
        params = {
            "bookId": self.book_id or self.__get_book_id(),
            "count": 10,
            "createTime": 1565011808,
            "synckey": int(time.time()),
            "maxIdx": 1562945115,
            "topshelf": 0
        }
        resp = requests.get(self.ARTICLE_URL, params, headers=headers)
        self.articles = resp.json()
        return self.articles

    def __is_article_available(self):
        """
        query the state(accessible, illegal and inaccessible(deleted)) of the post
        :return: False for share_url invalid
        """
        if self.book_id:
            return True
        if self.share_url:
            resp = requests.get(self.share_url, headers=self.wemp_headers)
            if resp.cookies.get("wxtokenkey", None) is not None:
                if resp.cookies.get("LogicRet") != "0":
                    return True
        return False

    def __refresh_auth(self):
        """
        check accessToken first
        :return:
        """
        if self.token["from"] + self.sign["expires_in"] > int(time.time()) - 60:
            if self.sign["timestamp"] + self.sign["expires_in"] > int(time.time()) - 60:
                self.get_signature()
            self.__refresh_token()

    def __get_book_id(self):
        """
        Get book id from review id
        - check post state first
        :return: None for article illegal or inaccessible(deleted)
        """
        review_id = self.__get_review_id()
        book_id = "_".join(review_id.split("_")[:-1])
        self.book_id = book_id
        return book_id

    def __get_review_id(self) -> str:
        """
        ! user auth info needed
        :return: str
        """
        self.__refresh_auth()
        headers_add = {
            "accessToken": self.token["accessToken"],
            "vid": "1731234"
        }
        headers = self.weread_headers.copy()
        headers.update(headers_add)
        data = {"account": "", "isDelete": 0, "reviewId": "", "thumbUrl": "", "title": "",
                "url": self.share_url
                }
        resp = requests.post(self.REVIEWID_URL, json=data, headers=headers)
        return resp.json()["reviewId"]

    def dump_articles(self) -> [dict, ]:
        reviews = self.articles["reviews"]
        _posts = list()
        for r in reviews:
            _p = dict()
            if r["review"]["createTime"] <= self.last_update:
                break
            _p["createTime"] = r["review"]["createTime"]
            _p["bookId"] = r["review"]["belongBookId"]
            _p["originalId"] = r["review"]["mpInfo"]["originalId"]
            _p["doc_url"] = r["review"]["mpInfo"]["doc_url"]
            _p["title"] = r["review"]["mpInfo"]["title"]
            _p["content"] = r["review"]["mpInfo"]["content"]
            _p["avatar"] = r["review"]["mpInfo"]["avatar"]
            _p["mp_name"] = r["review"]["mpInfo"]["mp_name"]
            _posts.append(_p)
        self.last_update = reviews[0]["review"]["createTime"]
        return _posts

    def dump_book(self) -> dict:
        return {"bookId": self.book_id, "share_url": self.share_url, "last_update": self.last_update}
