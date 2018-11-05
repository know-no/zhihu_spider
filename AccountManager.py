import os
import requests
import time
import json
import base64
import hmac
from PIL import Image
from hashlib import  sha1
from http import cookiejar

class AccountManager:
    def __init__(self):
        self.accounts = set()
        self.sessions = set()
        self.cookies_files = set()
        self.prepared = False

    def read_account_file(self):
        with open("accounts") as f:
            lines = f.readlines()
        for line in lines:
            clean_line = line.strip().split(" ")
            account = (clean_line[0],clean_line[1])
            self.accounts.add(account)
        # todo
        # 读取目录下的cookies文件，格式　zhanghao.cookies ,./cookies/"+self.username+'.cookies
        # done
        dirs = os.walk("./cookies")
        for root ,dir , file in dirs:
            for f in file:
                self.cookies_files.add(os.path.join(root,f))
        # print(self.cookies_files)

    def prepare(self):
        self.read_account_file()
        if len(self.cookies_files) > 0:
            for c in self.cookies_files:
                one = LoginOne(cookie=c).login()
                if one is not None:
                    self.sessions.add(one)
            for i in self.sessions:
                print(i.headers)
            self.prepared = True
            return
        for account in self.accounts:
            one = LoginOne(account[0],account[1]).login()
            if one is not None:
                self.sessions.add(one)
                one.cookies.save()
        self.prepared =True

    def get_session(self):
        if not self.prepared:
            self.prepare()
        if len(self.sessions) > 0:
            return self.sessions.pop()
        else:
            return  None




class LoginOne:
    def __init__(self,username = None, password = None,cookie = None):
        self.username = username
        self.password = password
        self.cookie = cookie
        self.success = False
        self.headers = {
    'Connection': 'keep-alive',
    'Referer': 'https://www.zhihu.com/signup?next=%2F',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36'
    }
        self.zhihu = "https://www.zhihu.com"
        self.login_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        self.code = b"d1b964811afb40118a12068ff74a12f4"
        self.grantType = "password"
        self.clientId = "c3cef7c66a1843f8b3a9e6a1e3160e20"
        self.source = "com.zhihu.web"
        self.en = "https://www.zhihu.com/api/v3/oauth/captcha?lang=en"
        self.session = requests.session()
        self.session.headers = self.headers.copy()
        if(self.cookie is  None):
            self.session.cookies = cookiejar.LWPCookieJar("./cookies/"+self.username+'.cookies')
        else:
            self.session.cookies = cookiejar.LWPCookieJar(self.cookie)

    def get_start_cookie(self):
        resp1 = self.session.get(self.zhihu)
        _xrsf = resp1.cookies.get("_xsrf")
        d_c0 = resp1.cookies.get("d_c0")
        x_udid = d_c0.split("|")[0].strip("\"")
        self.session.headers.update({
            "x-xsrftoken": _xrsf,
            "x-udid": x_udid,
            "x-zse-83": '3_1.1',
            "x-requested-with": "fetch"
        })

    def get_identify_str(self):
        resp_old = self.session.get(self.en)
        ticket = ""
        print(resp_old.text)
        if(resp_old.text[16:-1] == "false"):
            return ticket
        # it needs to be verified by login with email
        print("Needs captcha")
        resp_new = self.session.put(self.en)

        captcha = json.loads(resp_new.text)['img_base64']
        with open("captcha.jpg",'wb') as img:
            img.write(base64.b64decode(captcha))
        img = Image.open("captcha.jpg")
        img.show()
        time.sleep(5)
        img.close()
        ticket = input("Input:")
        self.session.post(self.en,data = {"input_text":ticket})
        return ticket

    def get_signature(self,timestamp):
        hm = hmac.new(self.code,None,sha1)
        hm.update(str.encode(self.grantType))
        hm.update(str.encode(self.clientId))
        hm.update(str.encode(self.source))
        hm.update(str.encode(timestamp))

        return str(hm.hexdigest())


    def login(self):
        if self.cookie is not None:
            self.session.cookies.load(ignore_discard = True)
            self.session.headers.update({"referer": self.zhihu})
            return self.session
        self.get_start_cookie()
        ticket = self.get_identify_str()
        t = time.time() * 1000
        timestamp = str(t).split('.')[0]
        # print(timestamp)
        data = {
            "client_id": self.clientId,
            "grant_type": self.grantType,
            "source": self.source,
            "timestamp": timestamp,
            "username": self.username,
            "password": self.password,
            "captcha": ticket,
            "signature": self.get_signature(timestamp)
        }
        resp = self.session.post(self.login_url,data)
        self.success = resp.ok
        if(self.success):
            self.session.headers.update({"referer":self.zhihu})
            return self.session
        else:
            return None

if __name__ == "__main__":
     manager = AccountManager()
     manager.read_account_file()
     manager.prepare()