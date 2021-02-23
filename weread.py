import base64
import json
import time
import requests
import cv2


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
    appid = "appid"
    deviceId = "deviceId"
    mailDeviceId = "mailDeviceId"
    scope = "snsapi_userinfo,snsapi_timeline,snsapi_friend"
    qrcode_path = "image's filename"
    sign = {"signature": "", "timestamp": 0, "expires_in": 0}
    uuid = ""
    wx_code = "exchange for token"
    token = {"vid": "vid", "accessToken": "", "refreshToken": "", "skey": "", "openId": "",
             "user": {"name": "", "avatar": ""}, "firstLogin": 0, "userAgreement": 1, "from": "int, timestamp of token"}

    @classmethod
    def _get_signature(cls):
        """
        1. get signature from weread server
        2. signature is used to get accessToken and refresh accressToken
        """
        print(f"WeRead: _get_signature()")
        params = {"nonceStr": cls.nonceStr}
        resp = requests.get(cls.SIGNATURE_URL, params, headers=cls.weread_headers)
        cls.sign["signature"] = resp.json()["signature"]
        cls.sign["timestamp"] = resp.json()["timeStamp"]
        cls.sign["expires_in"] = resp.json()["expires_in"]

    @classmethod
    def _refresh_signature(cls):
        print(f"WeRead: _refresh_signature()")
        cls._get_signature()

    @classmethod
    def _get_uuid_and_qrcode(cls):
        """
        1. get uuid and QRCode from wechat developer platform
        2. uuid is the variable user-id, QRCode is for user authorization
        3. After authorized, method: _get_wxcode will be called to get wxcode automatically
        3. the authorization process is described at method: __pare_qrcode
        4. uuid and qrcode are both only used to get wxcode
        :return:
        """
        print(f"WeRead: _get_uuid_and_qrcode()")
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
        """
        1. convert base64 code to image in .jpg
        1. this method will be called by method: _get_uuid_and_qrcode
        2. this method will save image in the root directory of project, named unix timestamp in seconds
        3. on windows, the image will showed by cv2.imshow(), but on linux, there will be only one tip line
        4. after scanned, no matter on windows or linux,
                                    it's supposed to press Enter to execute method: _get_wxcode_ to go on
        :param qrcode_base64:
          there is no info about how the QRCode-base64 flow produce, but base64.standard_b64decode works, others don't
        :return: filename of QRCode image
        """
        b = base64.standard_b64decode(qrcode_base64)
        filename = "qrcode_{0}.jpg".format(int(time.time()))
        with open(filename, "wb") as fw:
            fw.write(b)
        return filename
    
    @classmethod
    def _get_wxcode(cls):
        """
        1. get wxcode from wechat developer platform through uuid
        2. uuid now is useless, and wxcode is the user-id on wechat platform
        3. wxcode is for getting accessToken and refreshToken
        4. from experience, it may not success by one request, but no more than three request
        :return:
        """
        print(f"WeRead: _get_wxcode()")
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
    def _get_token(cls):
        """
        1. pack many params to get accessToken and refreshToken from weread
        2. two main params here. One is code, which is from open platform,
                            and the other one is signature, which is from weread
        2. when got token, excode is useless, for it's no use to refresh token
        3. this method will add "from" key for timestamp when got token to cls.token
        :return:
        """
        print(f"WeRead: _get_token()")
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
    def _refresh_token(cls, ref="/pay/memberCardSummary"):
        """
        1. refresh token from weread
        2. this method will add "from" key for timestamp when got token to cls.token
        :param ref: like http Referer
        :return:
        """
        print(f"WeRead: _refresh_token()")
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
        # try:
        #     cls.token["skey"] = resp.json()["skey"]
        # except KeyError as e:
        #     # {'errcode': -2013, 'errmsg': '微信登录授权已过期，继续购买需跳转到微信重新登录', 'vid': 1731234, 'accessToken': 'AenOJb0n', 'alertType': 0}
        #     raise e

    @classmethod
    def authorize(cls, cmd=True):
        """
        integrate authorization flow
        work flow:
            cls._get_signature()    <- weread
            cls._get_uuid_and_qrcode()  <- weopen
            if cmd:
                cls.__wait_for_scanning_cmd()
            else:
                cls.__wait_for_scanning_gui()
            cls._get_wxcode()   <- weopen
            cls._get_token()    <- weread
        :param cmd:
        :return:
        """
        print(f"WeRead: authorize()")
        cls._get_signature()
        cls._get_uuid_and_qrcode()
        if cmd:
            cls.__wait_for_scanning_cmd()
        else:
            cls.__wait_for_scanning_gui()
        cls._get_wxcode()
        cls._get_token()

    @classmethod
    def __wait_for_scanning_gui(cls):
        img = cv2.imread(cls.qrcode_path)
        cv2.imshow("QR", img)
        cv2.waitKey()
        cv2.destroyAllWindows()

    @classmethod
    def __wait_for_scanning_cmd(cls):
        input(f"Please quickly: {cls.qrcode_path}")

    @classmethod
    def refresh_login(cls):
        """
        1. refresh auth
        2. here is not a "good" implementation, because it doesn't handle accessToken expire time
        3. no information about accessToken expire time as well as refreshToken
        :return:
        """
        print(f"WeRead: refresh_login()")
        if cls.sign["timestamp"] + cls.sign["expires_in"] > int(time.time()) - 60:
            cls._refresh_signature()
        cls._refresh_token()

    @classmethod
    def dump_auth(cls, path="./WeRead.json"):
        """
        1. dump auth info as JSON
        1. there are some extra values like uuid, wxcode
        1. cls.token is just the response body from server which contains a lot of values including refreshToken
        2. the actually useful value is sign and token, both for refreshing token
        3. as mentioned in method: _refresh_token above, we only need sign and refreshToken
        :return:
        """
        print(f"WeRead: dump_auth()")
        data = {
            "sign": cls.sign,
            "uuid": cls.uuid,
            "wx_code": cls.wx_code,
            "token": cls.token
        }
        with open(path, "w", encoding="utf-8") as fw:
            json.dump(data, fw)

    @classmethod
    def load_auth(cls, path="./WeRead.json"):
        """
        reverse to method: dump_auth
        """
        print(f"WeRead: load_auth()")
        with open(path, "r", encoding="utf-8") as fr:
            data = json.load(fr)
            cls.sign = data["sign"]
            cls.uuid = data["uuid"]
            cls.wx_code = data["wx_code"]
            cls.token = data["token"]

    def __init__(self, bid, state, share_url="", bookId="", last_update=0):
        self.articles = {}
        self.review_id = ""
        self.bid = bid
        self.state = state
        self.last_update = last_update
        self.book_id = bookId
        self.share_url = share_url
        self.success = True
        if not last_update:
            self.success = self.__is_article_available()
        print(f"{bid}-{bookId}: {share_url} init {self.success}, last update {self.last_update}")

    def update_articles(self):
        """
        ! user auth info needed
        Get 10, as count set, articles of the mp, which posted the share article.
        - accessToken will be updated every 1.5h by method:refresh_auth
        - normal http headers extended with user auth info
        :return:
        """
        print(f"{self.bid}-{self.book_id}: update_articles() ->", end=" ")
        if not self.success:
            return None
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

        if "reviews" in resp.json():
            print("reviews")
            self.articles = resp.json()
        elif "errcode" in resp.json() and resp.json()["errcode"] == -2012:
            print(resp.json()["errmsg"])
            self.refresh_login()
            self.update_articles()
        else:
            print(resp.json())

    def __is_article_available(self):
        """
        query the state(accessible, illegal and inaccessible(deleted)) of the post
        :return: False for share_url invalid
        """
        print(f"{self.bid}-{self.book_id}: __is_article_available()")
        if self.book_id:
            return True
        if self.share_url:
            resp = requests.get(self.share_url, headers=self.wemp_headers)
            if resp.cookies.get("wxtokenkey", None) is not None:
                if resp.cookies.get("LogicRet") != "0":
                    return True
        return False

    def __get_book_id(self):
        """
        Get book id from review id
        - check post state first
        :return: None for article illegal or inaccessible(deleted)
        """
        print(f"{self.bid}-{self.book_id}: __get_book_id() ->", end=" ")
        self.review_id = self.__get_review_id()
        book_id = "_".join(self.review_id.split("_")[:-1])
        self.book_id = book_id
        print(self.book_id)
        return book_id

    def __get_review_id(self) -> str:
        """
        ! user auth info needed
        :return: str
        """
        print(f"{self.bid}-{self.book_id}: __get_review_id() ->", end=" ")
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
        if "reviewId" in resp.json():
            print(resp.json()["reviewId"])
            return resp.json()["reviewId"]
        if "errcode" in resp.json() and resp.json()["errcode"] == -2012:
            print(resp.json()["errmsg"])
            self.refresh_login()
            self.__get_review_id()
        else:
            print(resp.json())

    def dump_articles(self) -> [dict, ]:
        print(f"{self.bid}-{self.book_id}: dump_articles()")
        if "reviews" not in self.articles:
            return []
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
        print(f"{self.bid}-{self.book_id}: dump_book()")
        return {"bookId": self.book_id, "share_url": self.share_url,
                "last_update": self.last_update, "bid": self.bid}
