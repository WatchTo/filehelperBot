import requests
import re
import time
import qrcode_terminal
from urllib.parse import quote
import json
import random
import sys
from multiprocessing import Pool


class Bot:
    def __init__(self):
        self.debug = not False
        self.message_handler = None

        self.headers = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="98", "Microsoft Edge";v="98"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "mmweb_appid": "wx_webfilehelper",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.50",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "sec-gpc": "1",
        }
        self.skey = 0
        self.wxsid = 0
        self.wxuin = 0
        self.pass_ticket = 0
        self.sync_key = 0
        self.sync_key_str = 0
        self.sess = requests.Session()
        self.index_url = "https://filehelper.weixin.qq.com"
        self.uuid_url = f"https://login.wx.qq.com/jslogin?appid=wx_webfilehelper&redirect_uri=https://filehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage&fun=new&lang=zh_CN&_=%s"
        self.login_url = "https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=1&r=301908451&_=%s&appid=wx_webfilehelper"
        self.qrcode_url = "https://login.weixin.qq.com/l/%s"
        self.init_url = "https://filehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=297000710&lang=zh_CN&pass_ticket=%s"
        self.sync_url = "https://filehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/synccheck?r=1644678531725&skey=%s&sid=%s&uin=%s&deviceid=832414456672544&synckey=%s&mmweb_appid=wx_webfilehelper"
        self.mcheck_url = "https://filehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=%s&skey=%s&lang=zh_CN&pass_ticket=%s"
        # for cookies init
        try:
            ret = self.sess.get(self.index_url, verify=self.debug)
        except Exception as e:
            print(e)
            sys.exit(-1)
        # login
        ret = 0
        try:
            print("正在登录...")
            ret = self.login()
        except Exception as e:
            print(e)
            sys.exit(-1)

    def login(self):
        # 获取uuid，生成二维码
        ret = self.sess.get(self.uuid_url, verify=self.debug)
        uuid = re.findall('window.QRLogin.uuid = "(\S+)";', ret.text)[0]
        qrcode_terminal.draw(self.qrcode_url % uuid)

        start_time = time.time()
        # 等待扫描二维码
        while True:
            ret = self.sess.get(
                self.login_url % (uuid, str(int(time.time()))), verify=self.debug
            )
            # 没有成功登录就继续检查
            if "window.code=200" not in ret.text:
                if time.time() - start_time > 10:
                    sys.exit(-1)
                time.sleep(1)
                continue
            print("登录成功")
            # 成功登录，获取一些信息
            redirect_uri = re.findall('window.redirect_uri="(.*?)";', ret.text)[0]
            redirect_uri = redirect_uri.replace("?", "?fun=new&version=v2&")  # 重要
            ret = self.sess.get(redirect_uri, verify=self.debug)
            self.skey, self.wxsid, self.wxuin, self.pass_ticket = re.findall(
                "<skey>(\S+)</skey><wxsid>(\S+)</wxsid><wxuin>(\S+)</wxuin><pass_ticket>(\S+)</pass_ticket>",
                ret.text,
            )[0]
            break
        # wxinit, 获取synckey
        data = (
            '{"BaseRequest":{"Uin":%s,"Sid":"%s","Skey":"%s","DeviceID":"251195370922993"}}'
            % (self.wxuin, self.wxsid, self.skey)
        )
        url = self.init_url % quote(self.pass_ticket)
        req = requests.Request("POST", url, data=data, headers=self.headers)
        ret = self.sess.send(req.prepare(), verify=self.debug)
        if ret.json()["BaseResponse"]["Ret"] != 0:
            print(ret.text())
            return 0
        self.sync_key = ret.json()["SyncKey"]
        self.sync_key_str = "|".join(
            [f'{item["Key"]}_{item["Val"]}' for item in self.sync_key["List"]]
        )
        return 1

    def register_message_handler(self, handler):
        self.message_handler = handler

    def receive_message(self):
        while True:
            try:
                ret = self.sess.get(
                    self.sync_url
                    % (self.skey, self.wxsid, self.wxuin, self.sync_key_str),
                    verify=self.debug,
                )
            except requests.exceptions.ConnectionError:
                continue
            if 'retcode:"1101"' in ret.text:
                print("登录失效")
                break
            if 'selector:"0"' in ret.text:
                time.sleep(2)
                continue
            # 接下来处理有新消息的情况
            data = {
                "BaseRequest": {
                    "Uin": self.wxuin,
                    "Sid": f"{self.wxsid}",
                    "Skey": f"{self.skey}",
                    "DeviceID": "839030748762113",
                },
                "SyncKey": self.sync_key,
                "rr": random.randint(111111111, 999999999),
            }
            req = requests.Request(
                "POST",
                self.mcheck_url % (self.wxsid, self.skey, quote(self.pass_ticket)),
                data=json.dumps(data),
                headers=self.headers,
            )
            try:
                ret = self.sess.send(req.prepare(), verify=self.debug)
            except requests.exceptions.ConnectionError:
                continue
            if ret.json()["BaseResponse"]["Ret"] != 0:
                print(ret.text)
                break
            msg_count = ret.json()["AddMsgCount"]
            msg_list = ret.json()["AddMsgList"]
            self.sync_key = ret.json()["SyncCheckKey"]
            self.sync_key_str = "|".join(
                [f'{item["Key"]}_{item["Val"]}' for item in self.sync_key["List"]]
            )
            if self.message_handler:
                self.message_handler(msg_list)
            time.sleep(2)

    def run(self):
        p = Pool(1)
        p.apply_async(self.receive_message)
        p.close()
        try:
            p.join()
        except KeyboardInterrupt:
            p.terminate()
            p.join()

# 消息处理函数，可以自定义
def test(message_list: list):
    for msg in message_list:
        print(msg)

if __name__ == "__main__":
    bot = Bot()
    # 注册消息处理函数
    bot.register_message_handler(test)
    bot.run()
