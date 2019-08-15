import requests
import base64
import time


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
    __sign = {"signature": "", "timestamp": 0, "expires_in": 0}
    __uuid = ""
    qrcode_path = "image's filename"
    wx_code = "exchange for token"
    token = {'vid': 1731234, 'accessToken': '', 'refreshToken': '', 'skey': '', 'openId': '',
             'user': {'name': '', 'avatar': ''}, 'firstLogin': 0, 'userAgreement': 1}

    @classmethod
    def get_signature(cls):
        params = {"nonceStr": cls.nonceStr}
        resp = requests.get(cls.SIGNATURE_URL, params, headers=cls.weread_headers)
        cls.__sign["signature"] = resp.json()["signature"]
        cls.__sign["timestamp"] = resp.json()["timeStamp"]
        cls.__sign["expires_in"] = resp.json()["expires_in"]

    @classmethod
    def get_uuid_and_qrcode(cls):
        params = {
            "appid": cls.appid,
            "noncestr": cls.nonceStr,
            "timestamp": cls.__sign["timestamp"],
            "scope": cls.scope,
            "signature": cls.__sign["signature"]
        }
        resp = requests.get(cls.QRCONNECT_URL, params, headers=cls.weopen_headers)
        cls.__uuid = resp.json()["uuid"]
        cls.qrcode_path = cls.parse_qrcode(resp.json()["qrcode"]["qrcodebase64"])
    
    @staticmethod
    def parse_qrcode(qrcode_base64):
        b = base64.standard_b64decode(qrcode_base64)
        filename = "qrcode_{0}.jpg".format(int(time.time()))
        with open(filename, "wb") as fw:
            fw.write(b)
        return filename
    
    @classmethod
    def get_wxcode(cls):
        params = {
            "f": "json",
            "uuid": cls.__uuid,
        }
        resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
        print(resp.json())
        if not resp.json()["wx_code"]:
            time.sleep(0.5)
            params["last"] = 404
            resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
            print(resp.json())
            if not resp.json()["wx_code"]:
                time.sleep(0.5)
                params["last"] = 404
                # supposed to success here
                resp = requests.get(cls.LONG_QRCONNECT_URL, params, headers=cls.weopen_headers)
                print(resp.json())
        cls.wx_code = resp.json()["wx_code"]
    
    @classmethod
    def get_token(cls):
        data = {
            "code": cls.wx_code,
            "deviceId": cls.deviceId,
            "mailDeviceId": cls.mailDeviceId,
            "random": 937,
            "signature": cls.__sign["signature"],
            "timestamp": cls.__sign["timestamp"],
            "trackId": ""
        }
        resp = requests.post(cls.TOKEN_URL, json=data, headers=cls.weread_headers)
        cls.token = resp.json()

    @classmethod
    def refresh_token(cls, ref="/pay/memberCardSummary"):
        data = {
            "deviceId": cls.deviceId,
            "inBackground": 0,
            "kickType": 1,
            "random": 46,
            "refCgi": ref,
            "refreshToken": cls.token["refreshToken"],
            "signature": cls.__sign["signature"],  # 只需要重新请求签名
            "timestamp": cls.__sign["timestamp"],
            "trackId": "",
            "wxToken": 0
        }

        resp = requests.post(cls.REFRESH_TOKEN_URL, json=data, headers=cls.weread_headers)
        cls.token["accessToken"] = resp.json()["accessToken"]
        cls.token["skey"] = resp.json()["skey"]

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

# todo: make a decorator for checking and updating signature
# todo: make a decorator for update accessToken
