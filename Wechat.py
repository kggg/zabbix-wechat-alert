#!/usr/bin/env python
#coding: utf-8
import time
import sys,requests
import json, os

"""
获取微信access token, 以便验证发送信息
token保留在文件中不会每次去微信后台索取，防止过多索取记录而被微信封锁
"""
class AccessToken(object):
    def __init__(self):
        self.corpid = 'xxxxxxxxxxxxxxx'         ###   company id of wechat
        self.corpsecret = 'xxxxxxxxxxxxxxxxxxxxxxxo'   ## for your company app secret
        self.token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (self.corpid, self.corpsecret)
        self.cachefile = '/etc/zabbix/alertscripts/cache.log'

    def gettoken(self):
        headers = {'content-type': 'application/json',
           'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}
        content = requests.get(self.token_url, headers=headers)
        return content.text

    def readtoken(self):
        store = open(self.cachefile, 'r')
        con = store.read()
        store.close()
        res = json.loads(con)
        return res['access_token']

    def storetoken(self, content):
        store = open(self.cachefile, 'w')
        store.write(content)
        store.close()

    def varifyexpire(self):
        nowtime = time.time()
        mtime = os.stat(self.cachefile).st_mtime
        res = nowtime - mtime
        if res >= 7200 :
            return False
        else:
            return True


"""
发送信息
"""
class WechatMsg(object):
    def __init__(self, token, user, title, msg):
        self.token = token
        self.message = title+"\n"+msg
        self.msg_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' % self.token
        self.content = {
                               "touser" : user,
                               "toparty": "3",
                               "agentid": "1000002",
                               "msgtype": "text",
                               "text": {"content" : self.message}
                        }
    def sendmsg(self, content=None):
        pdata = ""
        if content == None:
            pdata = json.dumps(self.content)
        else:
            pdata = content
        r = requests.post(self.msg_url, data=pdata)
        return r.text


"""
日志记录方便调试
"""
class Logger(object):
    def __init__(self):
        self.logfile = '/etc/zabbix/alertscripts/log/weixin.log'

    def baselog(self, string=None):
        nowtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        msglog = nowtime + "  " + string
        self.writetofile(msglog)

    def msglog(self, string=None):
        nowtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        res = json.loads(string)
        errcode = res['errcode']
        if errcode == 0 :
            msglog = nowtime + "  " + "msg ok\n"
            self.writetofile(msglog)
        else:
            msglog = nowtime + "  "+ res['errmsg']+"\n"
            self.writetofile(msglog)

    def writetofile(self, string=None):
        file = open(self.logfile, 'a')
        file.write(string)
        file.close()

if __name__ == '__main__':
    user = str(sys.argv[1])
    title =  str(sys.argv[2])
    msg =  str(sys.argv[3])
    log = Logger()
    log.baselog("Start to sendmsg\n")
    t = AccessToken()

    valid = t.varifyexpire()
    if valid == False :
        text = t.gettoken()
        t.storetoken(text)
        log.baselog("got token from weixin backends\n") 
    token = t.readtoken()
    s = WechatMsg(token, user, title, msg)
    res = s.sendmsg()
    log.msglog(res)
