#!/usr/bin/env python
#_*_coding:utf-8_*_

import urllib
import urllib.request
import urllib.parse
from urllib.error import *
import os
import time
import sys
import re
import http.cookiejar
import xml.etree.ElementTree as ET
import random
import json
import threading
import gzip


IMAGE_PATH = os.path.abspath(os.path.split(__file__)[0]) + '\\weixin.jpg'
RR_TIME = 1477468749


class SyncKey(object):
    def __init__(self, syncKeyDicInit):
        if type(syncKeyDicInit) is dict:
            self.syncKeyDict = syncKeyDicInit.copy()
        else:
            self.syncKeyDict = dict()
            
    def extractSyncKey(self):
        syncKeyString = ''
        syncKeyList = self.syncKeyDict.get('List')
        if syncKeyList:
            for index, syncKey in enumerate(syncKeyList):
                if index:
                    syncKeyString += ('|%s_%s')%(syncKey['Key'], syncKey['Val'])
                else:
                    syncKeyString += ('%s_%s')%(syncKey['Key'], syncKey['Val'])

        return syncKeyString 
        
    def getDict(self):
        return self.syncKeyDict
        
    def __str__(self):
        return self.syncKeyDict.__str__()
        
          
        
        
class WebWechat(object):
    urls = {
        'jslogin':'https://login.wx.qq.com/jslogin',
        'qrcode':'https://login.weixin.qq.com/qrcode/',
        'login':'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login',
        'webwxinit':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit',
        'webwxstatusnotify':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatusnotify',
        'webwxgetcontact':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact',
        'synccheck':'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck',
        'webwxsync':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync',
        'webwxsendmsg':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg',
    }
    
    def __init__(self, *args, imagePath=IMAGE_PATH):
        self.cookie = http.cookiejar.CookieJar() 
        processor = urllib.request.HTTPCookieProcessor(self.cookie)
        opener = urllib.request.build_opener(processor, *args)
        urllib.request.install_opener(opener)
        
        self.pgv_pvi = str(self.pgv())
        self.pgv_si = 's' + str(self.pgv())
        self.uuid = None
        self.redirect_uri = None
        self.imagePath = imagePath
        self.skey = None
        self.sid = None
        self.uin = None
        self.pass_ticket = None
        self.username = None
        self.syncKey = None
        self.serial = None
        self.recvMsgFlag = True
        self.threadID = None
    
    
    def pgv(self):
        return int(int(2147483647 * (random.random() or 0.5))*+int(time.time()*1000)%1E10)
    
    
    def sendRequest(self, url, headers, params=None, method='GET', data=None, setCookie=False):
        if not url:
            return None
            
        if params:
            fulurl = url + '?' + urllib.parse.urlencode(params)
        else:
            fulurl = url
        
        if method == 'GET' or not data:
            request = urllib.request.Request(url=fulurl, headers=headers, method='GET')
        else:
            request = urllib.request.Request(url=fulurl, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        
        if self.cookie:
            self.cookie.add_cookie_header(request)
        try:
            response = urllib.request.urlopen(request)
        except HTTPError as e:
            print(e)
            raise e
        except URLError as e:
            print(e)
            raise e
            
        if setCookie:
            self.cookie.extract_cookies(response, request)
            
        data = response.read()
        return data
        
       
    def parseString(self, regx, string):
        pm = re.search(regx, string)
        if pm:
            return pm.groups()
        else:
            return None
    
        
    def getDeviceID(self):
        deviceID = 'e' + str(random.randint(100000000000000, 999999999999999))
        return deviceID
        
        
    def getR(self):
        r = (RR_TIME-int(time.time()))*1000
        return r
        
        
    def getMsecTime(self):
        return int(time.time()*1000)    
        
        
    def getSerial(self):
        if not self.serial:
            self.serial = int((time.time()-8)*1000)
        else:
            self.serial += 1
        return self.serial
        
        
    def getUrl(self, key):
        return self.__class__.urls.get(key, None)
    
        
    def allocInitCookie(self, name, value):
        cookie = http.cookiejar.Cookie(0, name, value,
                                         None, False,
                                         '.qq.com', True, True,
                                         '/', True,
                                         False,
                                         None,
                                         False,
                                         None,
                                         None,
                                         {},
                                         False)
                                             
        return cookie
    
    
    def setInitCookie(self):
        cookie_pvi = self.allocInitCookie('pgv_pvi', self.pgv_pvi)
        cookie_si = self.allocInitCookie('pgv_si', self.pgv_si)
        cookie_mm_lang = self.allocInitCookie('mm_lang', 'zh_CN')    
        cookie_notify = self.allocInitCookie('MM_WX_NOTIFY_STATE', '1')
        cookie_sound = self.allocInitCookie('MM_WX_SOUND_STATE', '1')
        
        self.cookie.set_cookie(cookie_pvi)
        self.cookie.set_cookie(cookie_si)
        self.cookie.set_cookie(cookie_mm_lang)
        self.cookie.set_cookie(cookie_notify)
        self.cookie.set_cookie(cookie_sound)
    
    
    def printCookie(self):
        print('Cookie:')
        print('version %s'%self.cookie.version)
        print('name %s'%self.cookie.name)
        print('value %s'%self.cookie.value)
        print('port %s port_specified %s'%(self.cookie.port, self.cookie.port_specified))
        print('domain %s domain_specified %s domain_initial_dot %s'%(self.cookie.domain, self.cookie.domain_specified, self.cookie.domain_initial_dot))
        print('path %s path_specified %s'%(self.cookie.path, self.cookie.path_specified))
        print('secure %s'%self.cookie.secure)
        print('expires %s'%self.cookie.expires)
        print('discard %s'%self.cookie.discard)
        print('comment %s'%self.cookie.comment)
        print('comment_url %s'%self.cookie.comment_url)
        print('_rest %s'%self.cookie._rest)
        print('rfc2109 %s'%self.cookie.rfc2109)
        
    
    def printContent(self, msgList):
        for msg in msgList:
            if msg['MsgType'] == 1:
                print(msg['Content'])
        
    
    def getUUID(self):    
        headers = {
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'ccept-Language':'zh-CN,zh;q=0.8',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Host':'login.wx.qq.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
            'Upgrade-Insecure-Requests':'1',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        url = self.getUrl('jslogin')
        params = {
            'appid':'wx782c26e4c19acffb',
            'redirect_uri':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun':'new',
            'lang':'zh_CN',
            '_':int(time.time())
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='GET')
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.\S+ = "(\S*)";'
        result = self.parseString(regx, data.decode())
        if result:
            code = result[0]
            uuid = result[1]
            if code == '200':
                self.uuid = uuid
                
        
    def getQRCode(self, openQRFile=False):
        headers = {
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'ccept-Language':'zh-CN,zh;q=0.8',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Host':'login.wx.qq.com',
            'Referer':'https://wx.qq.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
        }
        url = self.getUrl('qrcode') + self.uuid

        data = self.sendRequest(url=url, headers=headers, method='GET') 
        try: 
            file = open(self.imagePath, 'wb')
            file.write(data)
            file.close()
        except IOError as e:
            print(e)
            raise e
        time.sleep(1)
        if openQRFile:
            os.system('call %s'%self.imagePath)  
            
            
    def checkLogin(self):
        headers = { 
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Host':'login.wx.qq.com',
            'Referer':'https://wx.qq.com/?&lang=zh_CN',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
        }
        url = self.getUrl('login')
        params = {
            'loginicon':'true',
            'uuid':self.uuid,
            'tip':'1',
            '_':int(time.time())
        }
            
        data = self.sendRequest(url=url, headers=headers, params=params, method='GET', data=None)
        regx = r'window.code=(\d+);'
        result = self.parseString(regx, data.decode())
        if result:
            code = result[0]
            if code == '200':
                regx = r'window.redirect_uri="(\S+)";'
                result = self.parseString(regx, data.decode())
                if result:
                    self.redirect_uri = result[0]
          
        
    def getSkey(self):
        headers = { 
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Host':'wx.qq.com',
            'Referer':'https://wx.qq.com/?&lang=zh_CN',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
        }
        params = {
            'fun':'new',
            'version':'v2',
            'lang':'zh_CN',
        }
        url = self.redirect_uri + '&' + urllib.parse.urlencode(params)
        
        data = self.sendRequest(url=url, headers=headers, method='GET', setCookie=True) 
        if len(data) > 0:
            root = ET.fromstring(data.decode())
            self.skey = root.find('skey').text
            self.sid = root.find('wxsid').text
            self.uin = root.find('wxuin').text
            self.pass_ticket = root.find('pass_ticket').text
        
    
    def webWxInit(self):
        headers = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/json;charset=UTF-8',
            'Host':'wx.qq.com',
            'Origin':'https://wx.qq.com',
            'Referer':'https://wx.qq.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('webwxinit')
        postData = {
            'BaseRequest':{
                'DeviceID':self.getDeviceID(),
                'Sid':self.sid,
                'Skey':self.skey,
                'Uin':self.uin,
            }, 
        }
        params = {
            'r':self.getR(),
            'lang':'zh_CN',
            'pass_ticket':self.pass_ticket,
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='POST', data=postData)
        extractData = gzip.decompress(data).decode('utf-8')
        actualData = json.loads(extractData)
        self.username = actualData['User']['UserName']
        self.syncKey = SyncKey(actualData['SyncKey'])
    
    
    def statusNotify(self):
        headers = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Content-Type':'application/json;charset=UTF-8',
            'Host':'wx.qq.com',
            'Origin':'https://wx.qq.com',
            'Referer':'https://wx.qq.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('webwxstatusnotify')
        postData = {
            'BaseRequest':{
                'DeviceID':self.getDeviceID(),
                'Sid':self.sid,
                'Skey':self.skey,
                'Uin':self.uin,
            },
            'ClientMsgId':self.getMsecTime(), 
            'Code':3,
            'FromUserName':self.username,
            'ToUserName':self.username,
        }
        params = {
            'pass_ticket':self.pass_ticket,
        }
    
        data = self.sendRequest(url=url, headers=headers, params=params, method='POST', data=postData)
        
    
    def getContact(self):
        headers = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Host':'wx.qq.com',
            'Referer':'https://wx.qq.com/?&lang=zh_CN',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('webwxgetcontact')
        params = {
            'lang':'zh_CN',
            'pass_ticket':self.pass_ticket,
            'r':self.getMsecTime(),
            'seq':0,
            'skey':self.skey,
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='GET')
         
         
    def syncCheck(self):
        headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Host':'webpush.wx.qq.com',
            'Referer':'https://wx.qq.com/?&lang=zh_CN',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('synccheck')
        params = {
            'r':self.getMsecTime(),
            'skey':self.skey,
            'sid':self.sid,
            'uin':self.uin,
            'deviceid':self.getDeviceID(),
            'synckey':self.syncKey.extractSyncKey(),
            '_':self.getSerial(),
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='GET')    
        if data:
            regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
            result = self.parseString(regx, data.decode())
            if result:
                retcode = result[0]
                selector = result[1]
                return retcode, selector
        return None, None
        
    
    def webWxSync(self):
        headers = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Content-Type':'application/json;charset=UTF-8',
            'Host':'wx.qq.com',
            'Origin':'https://wx.qq.com',
            'Referer':'https://wx.qq.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('webwxsync')
        postData = {
            'BaseRequest':{
                'DeviceID':self.getDeviceID(),
                'Sid':self.sid,
                'Skey':self.skey,
                'Uin':self.uin,
            },
            'SyncKey':self.syncKey.getDict(),
            'rr':self.getR(),
        }
        params = {
            'sid':self.sid,
            'skey':self.skey,
            'lang':'zh_CN',
            'pass_ticket':self.pass_ticket,
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='POST', data=postData, setCookie=True)
        if data:
            extractData = gzip.decompress(data).decode('utf-8')
            actualData = json.loads(extractData)
            self.syncKey = SyncKey(actualData['SyncKey'])
            
            self.printContent(actualData['AddMsgList'])
            
            
    def webWxSendMsg(self, msgContent, toUser):
        headers = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Content-Type':'application/json;charset=UTF-8',
            'Host':'wx.qq.com',
            'Origin':'https://wx.qq.com',
            'Referer':'https://wx.qq.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2723.3 Safari/537.36',
        }
        url = self.getUrl('webwxsendmsg')
        clientMsgId = str(int(time.time()*1000)) + str(random.random())[:5].replace('.', '')
        postData = {
            'BaseRequest':{
                'DeviceID':self.getDeviceID(),
                'Sid':self.sid,
                'Skey':self.skey,
                'Uin':self.uin,
            },
            'Msg':{
                'ClientMsgId':clientMsgId,
                'Content':msgContent,
                'FromUserName':self.username,
                'LocalID':clientMsgId,
                'ToUserName':toUser,
                'Type':1,
            },
            'Scene':0,
        }
        params = {
            'pass_ticket':self.pass_ticket,
        }
        
        data = self.sendRequest(url=url, headers=headers, params=params, method='POST', data=postData)
        #actualData = json.loads(data.decode('utf-8'))
        #msgID = actualData['MsgID']
            
    
    def wxLogin(self):
        self.getUUID()
        if self.uuid:
            self.getQRCode(True)
            time.sleep(5)
            
            while not self.redirect_uri:
                self.checkLogin()
                time.sleep(1)
        
            self.setInitCookie()
            self.getSkey()
           
            
    def wxInit(self):
        if self.skey:
            self.webWxInit()
            if self.username:
                self.statusNotify()
                self.getContact()
     

    def wxRecvMsg(self):
        while self.recvMsgFlag:
            retcode, selector = self.syncCheck()
            if retcode == '0':
                if selector != '0':
                    self.webWxSync()
                else:
                    time.sleep(27)
            else:
                break
                
                
    def wxStartRecvMsg(self):
        self.threadID = threading.Thread(target=self.wxRecvMsg)
        self.threadID.start()
        self.threadID.join()
            

def test():
    proxyServer = 'http://127.0.0.1:8080'
    httpProxy = urllib.request.ProxyHandler({'http':proxyServer})
    httpsProxy = urllib.request.ProxyHandler({'https':proxyServer})
    #wxObj = WebWechat(httpProxy, httpsProxy)
    wxObj = WebWechat()
    wxObj.wxLogin()
    wxObj.wxInit()
    wxObj.webWxSendMsg('Hello World!', wxObj.username)
    wxObj.wxStartRecvMsg()
    
        
if __name__ == '__main__':
    test()
        
