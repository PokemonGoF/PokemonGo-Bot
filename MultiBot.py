# encoding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility
import json, traceback
import multiprocessing
import os, sys, random, time, platform, re, urllib2
import shutil
import threading
from time import gmtime, strftime, sleep
from threading import *
import requests

import urllib3

urllib3.disable_warnings()

Null = ""
proxyCur = 0
hashkeyCur = 0
accountNum = 0
try:
    os.mkdir('configs/temp')
except:
    pass
AccountLock = Semaphore(value=1)
screen_lock = Semaphore(value=1)
MultiBotConfig = json.loads(open('configs/MultiBotConfig.json').read())


def Lprint(content):
    content = "{0} {1}".format(strftime("%Y-%m-%d %H:%M:%S"), content)
    screen_lock.acquire()
    print(content)
    screen_lock.release()


def stop():
    Lprint('Interrupted stopping')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)


class Manager:
    def __init__(self):
        # Accounts = []
        # self.Accounts = Accounts
        self.hashkeyCur = 0
        self.proxyCur = 0
        # Loading accounts
        try:
            with open('configs/' + MultiBotConfig[u'AccountsFile']) as accountsFile:
                self.Accounts = accountsFile.read().splitlines()
            if MultiBotConfig[u'AccountRunOrder']:
                Accounts = random.sample(self.Accounts, len(self.Accounts))
        except IOError:
            Lprint('configs/{} does not exist'.format(MultiBotConfig[u'AccountsFile']))

        # Loading proxies
        try:
            with open('configs/' + MultiBotConfig[u'ProxyFile']) as proxyFile:
                self.proxyAll = proxyFile.read().splitlines()
        except IOError:
            print('configs/{} does not exist'.format(MultiBotConfig[u'ProxyFile']))

        # Loading hashkeys

        try:
            with open('configs/' + MultiBotConfig[u'HashKeyFile']) as hashkeyFile:
                self.hashkeyAll = hashkeyFile.read().splitlines()
            self.hashkeyNum = len(self.hashkeyAll)
        except IOError:
            Lprint('configs/{} does not exist'.format(MultiBotConfig[u'HashKeyFile']))

    # get a account to run
    def GetAccount(self):
        AccountLock.acquire()
        AccountTemp = self.Accounts[0]
        del self.Accounts[0]
        AccountLock.release()
        return AccountTemp

    # back to the pool
    def SetAccount(self, Account):
        AccountLock.acquire()
        self.Accounts.append(Account)
        AccountLock.release()
        return True

    # check hashkey if valid and use it
    @property
    def GetHashKey(self):
        while True:
            try:
                hashkey = self.hashkeyAll[0]
                del self.hashkeyAll[0]
                headers = {'X-AuthToken': hashkey}
                r = requests.post('http://pokehash.buddyauth.com/api/v133_1/hash', data='', headers=headers)
                if str(r.headers).find("X-MaxRequestCount") != -1:
                    Lprint("{} is valid".format(hashkey[:-10]))
                    self.hashkeyAll.append(hashkey)
                    return hashkey
                elif r.text.find("Could not verify your authentication details") != -1:
                    Lprint("key not valid")
                elif r.status_code == 401:
                    self.hashkeyAll.append(hashkey)
                    Lprint("temp banned waiting 3 min")
                    time.sleep(180)
            except KeyboardInterrupt:
                stop()
            except IndexError:
                Lprint("no valid hashkey! exit in 10s")
                sleep(10)
                stop()
            except Exception:
                pass

    def getProxy(self):
        # global proxyCur
        # global proxy
        while True:
            try:
                proxy = self.proxyAll[0]
                del self.proxyAll[0]
                proxies = {"http": "http://{0}".format(proxy), "https": "https://" + proxy}
                headers = {'user-agent': 'Niantic App'}
                if requests.get('https://pgorelease.nianticlabs.com/plfe/', headers=headers,
                                proxies=proxies).status_code == 200:
                    headers = {'user-agent': 'pokemongo/1 CFNetwork/758.5.3 Darwin/15.6.0'}
                    if requests.get('https://sso.pokemon.com/', headers=headers, proxies=proxies).status_code == 200:
                        self.proxyAll.append(proxy)
                        return str(proxy)
                    else:
                        Lprint("Proxy {} is Banned or offline".format(proxy))
                else:
                    Lprint("Proxy {} is Banned or offline".format(proxy))
            except IndexError:
                Lprint("no valid Proxy found exit in 10s")
                sleep(10)
                stop()
            except Exception:
                pass


def MakeConf(CurThread, username, password):
    killswitch_url = 'https://raw.githubusercontent.com/PokemonGoF/PokemonGo-Bot/dev/killswitch.json'

    try:
        jsonData = json.loads(open('configs/' + MultiBotConfig[u'AuthJsonFile']).read())
        jsonData[u'username'] = username
        jsonData[u'password'] = password
        jsonData[u'hashkey'] = Manager.GetHashKey

        with open('configs/temp/auth-' + str(CurThread) + '.json', 'w') as s:
            s.write(json.dumps(jsonData))
            s.close()

        jsonData = json.loads(open('configs/' + MultiBotConfig[u'ConfigJsonFile']).read())

        # Thanks to MerlionRock for the killswitch
        if jsonData.get('killswitch'):
            response = urllib2.urlopen(killswitch_url)
            killswitch_data = json.load(response)
            response.close()

            if killswitch_data['killswitch']:
                print "\033[91mKill Switch Activated By: \033[0m" + format(killswitch_data['activated_by'])
                print "\033[91mMessage: \033[0m\n" + format(killswitch_data['message']) + "\n\n\n"
                stop()

        if MultiBotConfig.get(u'CompleteTutorialNickName'):
            for i in range(len(jsonData[u'tasks'])):
                try:
                    if jsonData[u'tasks'][i][u'config'][u'nickname']:
                        jsonData[u'tasks'][i][u'config'][u'nickname'] = username.replace('_', '')
                        break
                except KeyboardInterrupt:
                    stop()
                except:
                    pass
        if MultiBotConfig.get(u'WebSocket')[u'start_embedded_server']:
            for i in range(len(jsonData[u'tasks'])):
                try:
                    if jsonData[u'websocket'][u'server_url']:
                        jsonData[u'websocket'][u'server_url'] = MultiBotConfig[u'WebSocket'][u'IP'] + ':' + str(
                            MultiBotConfig[u'WebSocket'][u'Port'] + CurThread)
                        break
                except KeyboardInterrupt:
                    stop()
                except:
                    jsonData.items().append(
                        "{u'websocket':,{u'server_url': u'" + MultiBotConfig[u'WebSocket'][u'IP'] + ":" + str(
                            MultiBotConfig[u'WebSocket'][u'Port'] + CurThread) + "u'start_embedded_server': True}")
        elif not MultiBotConfig[u'WebSocket'][u'start_embedded_server']:
            try:
                del jsonData[u'websocket']
            except KeyboardInterrupt:
                stop()
            except:
                pass
        if MultiBotConfig.get('TelegramTask'):
            try:
                for i in range(len(jsonData[u'tasks'])):
                    if jsonData[u'tasks'][1][u'type'] == u'TelegramTask':
                        jsonData[u'tasks'][i][u'config'][u'enabled'] = True
                        break
            except KeyboardInterrupt:
                stop()
            except:
                pass

        if not MultiBotConfig.get('TelegramTask'):
            try:
                for i in range(len(jsonData[u'tasks'])):
                    if jsonData[u'tasks'][1][u'type'] == u'TelegramTask':
                        jsonData[u'tasks'][i][u'config'][u'enabled'] = False
                        break
            except KeyboardInterrupt:
                stop()
            except:
                pass

        with open('configs/temp/config-' + str(CurThread) + '.json', 'w') as s:
            s.write(json.dumps(jsonData))
            s.close()

    except IOError:
        Lprint('config file error')
        time.sleep(30)
    except KeyboardInterrupt:
        stop()


class ThreadClass(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.paused = True  # start out paused
        self.state = threading.Condition()
        self.Manager = Manager

    def run(self):
        time.sleep(.1)
        self.resume()  # unpause self
        while True:
            with self.state:
                if self.paused:
                    self.state.wait()  # block until notified
            self.CurThread = int(self.getName().replace('Thread-', '')) - 1

            self.Account = Manager.GetAccount()
            username, password = self.Account.split(':')
            Lprint('Thread-{0} using account {1}'.format(self.CurThread, username))
            try:
                MakeConf(self.CurThread, username, password)
                StartCmd = "python pokecli.py -af configs/temp/auth-{0}.json -cf configs/temp/config-{0}.json --walker_limit_output {1}".format(
                    self.CurThread, MultiBotConfig[u'walker_limit_output'])
                if MultiBotConfig[u'UseProxy']:
                    proxy2 = Manager.getProxy()
                    if platform.system() == "Linux":
                        # os.system('export HTTP_PROXY="http://' + proxy + '"; export HTTPS_PROXY="https://' + proxy + '"; ' + StartCmd)
                        pass
                    if platform.system() == "Windows":
                        pass
                        # os.system('set HTTP_PROXY="http://' + proxy + '" & set HTTPS_PROXY="https://' + proxy + '" & ' + StartCmd)
                else:
                    pass
                    # os.system(StartCmd)
            except Exception as e:
                Lprint((traceback()))
                time.sleep(60)
            except KeyboardInterrupt:
                stop()
            finally:
                self.Manager.SetAccount(self.Account)

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
    global Manager
    Manager = Manager()
    try:
        for i in range(MultiBotConfig[u'Threads']):
            t = ThreadClass()
            time.sleep(0.1)
            t.start()
            time.sleep(10)
    except KeyboardInterrupt:
        Lprint("stopping all Threads")
        for i in range(MultiBotConfig[u'Threads']):
            t.stop()
        stop()


if __name__ == "__main__":
    start()
