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
from time import gmtime, strftime, sleep
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
screen_lock = Semaphore(value=1)
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
                if requests.get('https://pgorelease.nianticlabs.com/plfe/', headers=headers, proxies=proxies, timeout=15).status_code == 200:
                    headers = {'user-agent': 'pokemongo/1 CFNetwork/758.5.3 Darwin/15.6.0'}
                    if requests.get('https://sso.pokemon.com/', headers=headers, proxies=proxies, timeout=15).status_code == 200:
                        return proxy
                    else:
                        Lprint ("Proxy {} is Banned or offline".format(proxy))
                else:
                    Lprint ("Proxy {} is Banned or offline".format(proxy))

            except Exception as e:
                Lprint (e)
                pass
            except KeyboardInterrupt:
                stop()                  
    except IOError:
        Lprint ('configs/{} does not exist'.format(MultiBotConfig[u'ProxyFile']))
    except KeyboardInterrupt:
        stop()

try:
    Accounts = []
    with open('configs/' + MultiBotConfig[u'AccountsFile']) as f:
        for line in f:
            line = line.replace('\n', '').replace('\r', '').replace(',', '.')
            Accounts.append(line)
except IOError:
    Lprint ('configs/{} does not exist'.format(MultiBotConfig[u'AccountsFile']))
except KeyboardInterrupt:
    stop()

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
        Lprint ('configs/{} does not exist'.format(MultiBotConfig[u'HashKeyFile']))
    except KeyboardInterrupt:
        stop()

def stop():
    Lprint ('Interrupted stopping')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)



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

def Lprint (content):
    content = "{0} {1}".format(strftime("%Y-%m-%d %H:%M:%S"), content)
    screen_lock.acquire()
    print (content)
    screen_lock.release()

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
                except KeyboardInterrupt:
                    stop()
                except:
                    pass
        if MultiBotConfig[u'WebSocket'][u'start_embedded_server']:
            try:
                if jsonData[u'websocket'][u'server_url']:
                    jsonData[u'websocket'][u'server_url'] = MultiBotConfig[u'WebSocket'][u'IP'] + ':' + str(MultiBotConfig[u'WebSocket'][u'Port'] + CurThread)
            except KeyboardInterrupt:
                stop()
            except:
                jsonData.items().append("{u'websocket':,{u'server_url': u'" + MultiBotConfig[u'WebSocket'][u'IP'] + ":" + str(MultiBotConfig[u'WebSocket'][u'Port'] + CurThread) + "u'start_embedded_server': True}")
        elif not MultiBotConfig[u'WebSocket'][u'start_embedded_server']:
            try:
                del jsonData[u'websocket']
            except KeyboardInterrupt:
                stop()
            except:
                pass
        if MultiBotConfig[u'TelegramTask']:
            try:
            	for i in range(len(jsonData[u'tasks'])):
            		if jsonData[u'tasks'][1][u'type'] == u'TelegramTask':
            			jsonData[u'tasks'][i][u'config'][u'enabled'] = True
            except KeyboardInterrupt:
                stop()
            except:
                pass
            
        if not MultiBotConfig[u'TelegramTask']:
            try:
            	for i in range(len(jsonData[u'tasks'])):
            		if jsonData[u'tasks'][1][u'type'] == u'TelegramTask':
            			jsonData[u'tasks'][i][u'config'][u'enabled'] = False
            except KeyboardInterrupt:
                stop()
            except:
                pass
                
        with open('configs/temp/config-' + str(CurThread) + '.json', 'w') as s:
            s.write(json.dumps(jsonData))
            s.close()
            
    except IOError:
        Lprint ('config file error')
        time.sleep(30)
    except KeyboardInterrupt:
        stop()


class ThreadClass(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.paused = True  # start out paused
        self.state = threading.Condition()

    def run(self):
        time.sleep(.1)
        self.resume() # unpause self
        while True:
            with self.state:
                if self.paused:
                    self.state.wait() # block until notified
            self.CurThread = int(self.getName().replace('Thread-', '')) -1
           
            self.Account = AccountManager()
            self.username, self.password = self.Account.split(':')
            Lprint ('Thread-{0} using account {1}'.format(self.CurThread, self.username))
            try:
                MakeConf(self.CurThread, self.username, self.password)
                StartCmd = "python pokecli.py -af configs/temp/auth-{0}.json -cf configs/temp/config-{0}.json --walker_limit_output {1}".format(self.CurThread, MultiBotConfig[u'walker_limit_output'])
                if MultiBotConfig[u'UseProxy']:
                    self.proxy = getProxy()
                    if platform.system() == "Linux":
                        os.system('export HTTP_PROXY="http://' + proxy + '"; export HTTPS_PROXY="https://' + proxy + '"; ' + StartCmd)
                    if platform.system() == "Windows":
                        os.system('set HTTP_PROXY="http://' + proxy + '" & set HTTPS_PROXY="https://' + proxy + '" & ' + StartCmd)
                os.system(StartCmd)
            except Exception as e:
                import traceback
                Lprint ((e))
                time.sleep (60)
            except KeyboardInterrupt:
                stop()
            finally:
                AccountManager(self.Account)

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # unblock self if waiting

    def pause(self):
        with self.state:
            self.paused = True  # make self block and wait
    def stop(self):
            self.stopped = True


def start():
    try:
        for i in range(MultiBotConfig[u'Threads']):
            t = ThreadClass()
            time.sleep (0.1)
            t.start()
            time.sleep (10)
    except KeyboardInterrupt:
        Lprint("stopping all Threads")
        for i in range(MultiBotConfig[u'Threads']):
            t.stop()
        stop()

if __name__ == "__main__":
    start()
