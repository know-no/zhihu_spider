from redis import  StrictRedis
from redis import  ConnectionPool
import queue
from  threading import Lock

class RedisManager():
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 6379
        self.db = 0
        self.connectionPool = None
        self.pool = queue.Queue()
        self.lock = Lock()
        self.num = 0

    def init(self):
        #this may not have to try
        try:
            self.connectionPool = ConnectionPool(self.host, self.port, self.db)
        except Exception as  e:
            print(e)
        self.generate_con()

    def generate_con(self,num = 5):
        self.lock.acquire()
        for i in range(num):
            con = StrictRedis(connection_pool=self.connectionPool)
            con = RedisExecutor(con)
            self.num += 1
            self.pool.put(con)
        self.lock.release()



    def get_con(self):
        tmp = None
        if self.num <=0 :
            self.generate_con()

        self.lock.acquire()
        self.num -= 1
        tmp = self.pool.get()
        self.lock.release()

        return tmp

    def return_con(self,ex):
        self.lock.acquire()
        self.num +=1
        self.pool.put(ex)
        self.lock.release()


class RedisExecutor:
    def __init__(self,strict_redis):
        self.strict_redis = strict_redis

    def save_user(self,user):

        #假如token 在 to_do中 ，丢出
        #将token 加入 already_done 中
        #将token 作为name，user作为值存储

        self.strict_redis.srem('to_do', user['token'])
        self.strict_redis.sadd('already_done',user['token'])
        self.strict_redis.setnx(user['token'],user)
        for i in user['followee']:
            if(self.strict_redis.sismember('already_done',i['token']) is not True):
                self.strict_redis.sadd('to_do',i['token'])
        # for i think that followers are worthless
        # for i in user['follower']:
        #     if (self.strict_redis.sismember('already_done', i['token']) is not True):
        #         self.strict_redis.sadd('to_do',i['token'])


    def get_token(self):
        return self.strict_redis.spop('to_do')


