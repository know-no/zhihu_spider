from AccountManager import AccountManager
from DataPraser import DataPraser
from redisManager import RedisExecutor
from redisManager import  RedisManager
from ProxyManager import  ProxyManager
import re

import requests
# todo
# 应该加入多个下载线程或者进程，目前就先实现单线程的

# todo
# 代理

class DownloadThread:
    def __init__(self,account_manager,redis_executor = None,proxy_manager =None):
        self.redis_executor = redis_executor
        self.account_manager = account_manager
        self.proxy_manager = proxy_manager
        self.session = self.account_manager.get_session()
        self.proxy = self.proxy_manager.get() if proxy_manager is not None else None

        self.init_api_ee = 'https://www.zhihu.com/api/v4/members/{0}' \
                       '/followees?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed' \
                       '%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&limit={1}&offset={2}'

        self.init_api_er = "https://www.zhihu.com/api/v4/members/{0}/followers?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={1}&limit={2}"

        self.activities_page = "https://www.zhihu.com/people/{0}/activities"


    def run(self):
        #　todo 阻塞
        do = True
        count_session = 0
        count_proxy = 0
        while(do):
            token = self.redis_executor.get_token().decode('utf-8')
            # token = "tiancaixinxin"
            # token = "excited-vczh"
            count_session %= 5
            if(count_session == 0):
                self.session = self.account_manager.exchange_session(self.session)

            if token is not None:
                print("*"*10 + "Working on {0}".format(token) + "*"*10)

            else:
                print("No token left")
                exit(0)

            url_token = self.activities_page.format(token)
            print(url_token)
            api_ee = self.init_api_ee.format(token,20,0)
            api_er = self.init_api_er.format(token,0,20)

            user_info = dict()
            followees = list()
            followers = list()
            end_ee = False
            end_er = False

            while(True):
                try:
                    print("get info with proxy:{0}".format(self.proxy))
                    user_resp = self.session.get(url_token,proxies = self.proxy)
                # print(user_resp.text)
                    if user_resp.ok:
                        print('获取个人信息完成')
                        break
                except requests.exceptions.RequestException as rer:
                    print(rer)
                    print("change proxy......")
                    self.proxy = self.proxy_manager.get()
                    print("new proxy = {0}".format(self.proxy))

            info =(DataPraser.parse_user_info(user_resp.content,token))
            user_info.update(info)

            while  end_ee is False:
                while(True):
                    try:
                        print("get followee with proxy:{0}".format(self.proxy))
                        js = self.session.get(api_ee, proxies = self.proxy)
                        js = js.json()
                        followee_temp = DataPraser.parse_user_followees(js['data'])
                        for i in followee_temp:
                            followees.append(i)
                        print('获取本页被关注者完成')
                        break
                    except Exception as e:
                        print("1")
                        # todo 异常处理
                        print(e)
                        print("change proxy......")
                        self.proxy = self.proxy_manager.get()
                        print("new proxy = {0}".format(self.proxy))

                paging = js['paging']
                end_ee = paging['is_end']
                if end_ee is False:
                    limit = re.search('limit=(\d*)', paging['next']).groups()[0]
                    offset = re.search('offset=(\d*)', paging['next']).groups()[0]
                    api_ee = self.init_api_ee.format(token,limit,offset)
                    print('下一页被关注者')
                else:
                    end_ee = True
                    del js

            while  end_er is False:
                while(True):
                    try:
                        print("get follower with proxy:{0}".format(self.proxy))
                        js = self.session.get(api_er,proxies = self.proxy)
                        js = js.json()
                        follower_temp = DataPraser.parse_user_followers(js['data'])
                        for i in follower_temp:
                            followers.append(i)
                        print('获取本页关注者完成')
                        break
                    except Exception as e:
                        print("2")
                        print(e)
                        # todo 处理异常
                        print("change proxy......")
                        self.proxy = self.proxy_manager.get()
                        print("new proxy = {0}".format(self.proxy))

                paging = js['paging']
                end_er = paging['is_end']
                if end_er is False:
                    # print(paging['next'])
                    limit = re.search('limit=(\d*)', paging['next']).groups()[0]
                    offset = re.search('offset=(\d*)', paging['next']).groups()[0]
                    api_er = self.init_api_er.format(token, offset,limit)
                    print('下一页关注者')
                else:
                    end_er = True
                    print('')
                    del js

            user_info['token'] = token
            user_info.update({"followee":followees})
            user_info.update({"follower":followers})

            self.redis_executor.save_user(user_info)
            print()

if __name__=="__main__":
    a = AccountManager()
    r = RedisManager()
    p = ProxyManager()
    con = r.get_con()
    dl = DownloadThread(a,redis_executor=con,proxy_manager=p)
    dl.run()


# class DownloadDaemon(Thread):
#     def __init__(self,redis_manager,session_manager):
#         super.__init__(self)
#         self.session_manager = session_manager
#         self.downloadPool = set()
#         self.redis_manager = redis_manager
#     #添加线程进入线程池，并且启动
#     def start_download_thread(self,num = 5):
#         for i in range(num):
#             dw = DownloadThread(self.redis_manager.get_con(),self.session_manager.get_session())
#             self.downloadPool.add(dw)
#             dw.start()
#     #守护进程在运行，定时检测
#     def run(self):
#         self.start_download_thread()
#         while(True):
#             Thread.sleep(30)
#             for i in self.downloadPool:
#                 if i.isAlive() is False:
#                     self.redis_manager.return_con(i)
#                     self.start_download_thread(1)
