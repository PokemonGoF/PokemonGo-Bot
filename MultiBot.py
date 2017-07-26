#encoding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility
import gzip
import json
import multiprocessing
import os
import platform
import re
import shutil
import sys
import threading
import time
from threading import *
import requests

Null = ""
proxyCur = 0
hashkeyCur = 0
accountNum = 0
try:
    os.rmdir('configs/temp')
except:
    pass
try:
    os.mkdir('configs/temp')    
except:
    pass 
AccountLock = Semaphore(value=1)
MultiBotConfig = json.loads(open('configs/MultiBotConfig.json').read())

def getProxy():
    try:
        while True:
            try:
                with open('configs/' + MultiBotConfig[u'ProxyFile']) as proxyFile:
                    proxyAll = proxyFile.readlines()
                proxyNum = sum(1 for line in open('configs/' + MultiBotConfig[u'ProxyFile']))
                global proxyCur
                global proxy
                proxy = proxyAll[proxyCur].replace('\n', '').replace('\r', '')
                proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
                proxyCur += 1
                if proxyCur >= proxyNum:
                    proxyCur = 0
                headers = {'user-agent': 'Niantic App'}
                if requests.get('https://pgorelease.nianticlabs.com/plfe/', headers=headers, proxies=proxies).status_code == 200:
                    headers = {'user-agent': 'pokemongo/1 CFNetwork/758.5.3 Darwin/15.6.0'}
                    if requests.get('https://sso.pokemon.com/', headers=headers, proxies=proxies).status_code == 200:
                        return proxy
                    else:
                        print ("Proxy is Banned")
                else:
                    print ("Proxy is Banned")

            except Exception as e:
                print (e)
                pass
    except IOError:
        print 'configs/{} does not exist'.format(MultiBotConfig[u'ProxyFile'])

try:
    Accounts = []
    with open('configs/' + MultiBotConfig[u'AccountsFile']) as f:
        for line in f:
            line = line.replace('\n', '').replace('\r', '').replace(',', '.')
            Accounts.append(line)
except IOError:
    print 'configs/{} does not exist'.format(MultiBotConfig[u'AccountsFile'])

def getHashKey():
    try:
        with open('configs/' + MultiBotConfig[u'HashKeyFile']) as hashkeyFile:
            hashkeyAll = hashkeyFile.readlines()
        hashkeyNum = sum(1 for line in open('configs/' + MultiBotConfig[u'HashKeyFile']))-1
        global hashkeyCur
        global hashkey
        if hashkeyCur is hashkeyNum:
            hashkeyCur = 0
        hashkeyCur += 1
        return hashkeyAll[hashkeyCur].replace('\n', '').replace('\r', '')
    except IOError:
        print 'configs/{} does not exist'.format(MultiBotConfig[u'HashKeyFile'])

def AccountManager(Account=None):
    AccountLock.acquire()
    global Accounts
    if Account is None:
        AccountTemp = Accounts[0]
        del Accounts[0]        
        AccountLock.release()
        return AccountTemp
    else:
        Accounts.append(Account)
        AccountLock.release()

def MakeConf(CurThread, username, password):
    try:
        jsonData = json.loads(open('configs/' + MultiBotConfig[u'AuthJsonFile']).read())
        jsonData[u'username'] = username
        jsonData[u'password'] = password
        jsonData[u'hashkey'] = getHashKey()

        with open('configs/temp/auth-' + str(CurThread) + '.json', 'w') as s:
            s.write(json.dumps(jsonData))
            s.close()

        jsonData = json.loads(open('configs/' + MultiBotConfig[u'ConfigJsonFile']).read())
        if MultiBotConfig[u'CompleteTutorialNickName']:
            for i in range(len(jsonData[u'tasks'])):
                try:
                    if jsonData[u'tasks'][i][u'config'][u'nickname']:
                        jsonData[u'tasks'][i][u'config'][u'nickname'] = username.replace('_', '')
                except:
                    pass
        try:
            if jsonData[u'websocket'][u'start_embedded_server']:
                jsonData[u'websocket'][u'server_url'] = MultiBotConfig[u'WebSocket'][u'IP'] + ':' + str(MultiBotConfig[u'WebSocket'][u'Port'] + CurThread)
        except:
            print 'error websocket'

        with open('configs/temp/config-' + str(CurThread) + '.json', 'w') as s:
            s.write(json.dumps(jsonData))
            s.close()

    except IOError:
        print 'config file error'
        time.sleep(30)

class ThreadClass(threading.Thread):
      def run(self):
        self.CurThread = int(self.getName().replace('Thread-', '')) -1
        while True:
            self.Account = AccountManager()
            self.username, self.password = self.Account.split(':')
            print 'Thread-{0} using account {1}'.format(self.CurThread, self.username)
            try:
                MakeConf(self.CurThread, self.username, self.password)
                if MultiBotConfig[u'UseProxy']:
                    self.proxy = getProxy()
                    if platform.system() == "Linux":
                        self.os.system('export HTTP_PROXY="http://' + proxy + '"; export HTTPS_PROXY="https://' + proxy + '"')
                    if platform.system() == "Windows":
                        self.os.system('')
                os.system(
                    "python pokecli.py -af configs/temp/auth-{0}.json -cf configs/temp/config-{0}.json --walker_limit_output {1}".format(
                        self.CurThread, MultiBotConfig[u'walker_limit_output']))
            except Exception as e:
                import traceback
                print("Generic Exception: " + traceback.format_exc())
            finally:
                AccountManager(self.Account)
                time.sleep (60)
def start():
    for i in range(MultiBotConfig[u'Threads']):
        t = ThreadClass()
        time.sleep (0.1)
        t.start()
        time.sleep (10)

if __name__ == "__main__":
    start()
