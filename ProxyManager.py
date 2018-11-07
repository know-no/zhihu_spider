import  requests

class ProxyManager:

    def __init__(self):
        self.api = ""
        self.session = requests.session()
        self.proxies = list()

    def ask(self):
        if len(self.proxies) == 0:
            try:
                resp = self.session.get(self.api)
                # print(resp.text)
            except Exception as e:
                print(e)
            if resp  is not None:
                resp =resp.text.split('\n')[0:-1]
                # print(resp)
                for proxy in resp:
                    p = "https://" + proxy
                    self.proxies.append( {"https": p} )


    def get(self):
        if len(self.proxies) == 0:
            self.ask()

        return self.proxies.pop() if len(self.proxies) > 0 else None

if __name__ == "__main__":
    ps = ProxyManager()
    for i in range(5):
        print(ps.get())