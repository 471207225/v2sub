#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import urllib
import time

import json
import subprocess

import requests

from shadowsocks import Shadowsocks
from confMaker import ConfMaker
import util


class Switcher:
    mode = 'changeNode'
    v2rayConfigLocal = '/usr/local/etc/v2ray/config.json'
    testFileUrl = "http://cachefly.cachefly.net/10mb.test"

    def __init__(self):
        self.subLink = ""
        self.serverListLink = []

        # 鉴权
        # if os.geteuid() != 0:
        #     print("您需要切换到 Root 身份才可以使用本脚本。尝试在命令前加上 sudo?\n")
        #     exit()

    def loadSubLink(self):

        # 本脚本的配置文件，目前的作用是仅存储用户输入的订阅地址，这样用户再次启动脚本时，就无需再输入订阅地址。
        # 预设的存储的路径为存储到用户的 HOME 内。
        subFilePath = os.path.expandvars('$HOME') + '/.v2sub.conf'
        # 获取订阅地址
        if not os.path.exists(subFilePath):
            open(subFilePath, 'w+')
        subFile = open(subFilePath, 'r')
        self.subLink = subFile.read().strip()
        subFile.close()

        if not self.subLink:
            print('您还没有输入订阅地址')
            print('订阅地址文件', subFilePath)
        else:
            print('订阅地址：' + self.subLink)

        print('如果您的订阅地址有误，请删除或编辑 ' + subFilePath)
        print("\n开始从订阅地址中读取服务器节点… 如等待时间过久，请检查网络。\n")

    def readSubInfo(self):

        # 获取订阅信息
        urldata = requests.get(self.subLink).text
        self.serverListLink = util.decode(urldata).splitlines(False)
        for i in range(len(self.serverListLink)):
            if self.serverListLink[i].startswith('ss://'):
                # ss node
                base64Str = self.serverListLink[i].replace('ss://', '')
                base64Str = urllib.parse.unquote(base64Str)
                origin = util.decode(base64Str[0: base64Str.index('#')])
                remark = base64Str[base64Str.index('#') + 1:]
                security = origin[0: origin.index(':')]
                password = origin[origin.index(':') + 1: origin.index('@')]
                ipandport = origin[origin.index('@') + 1:]
                ip = ipandport[0: ipandport.index(':')]
                port = int(ipandport[ipandport.index(':') + 1:])
                print('【' + str(i) + '】' + remark)
                ssNode = Shadowsocks(ip, port, remark, security, password)
                self.serverListLink[i] = ssNode
            else:
                # vmess
                base64Str = self.serverListLink[i].replace('vmess://', '')
                jsonstr = util.decode(base64Str)
                serverNode = json.loads(jsonstr)
                print('【' + str(i) + '】' + serverNode['ps'])
                node = {
                    'ip': serverNode['add'],
                    'port': int(serverNode['port']),
                    'remark': serverNode['ps'],
                    'security': 'auto',
                    'uuid': serverNode['id'],
                    'alterId': int(serverNode['aid']),
                    'network': serverNode['net'],
                }
                self.serverListLink[i] = node

    def changeNode(self):

        maker = ConfMaker(self.serverListLink)
        v2rayConf, serverNameMap = maker.formatConfig()
        json.dump(v2rayConf, open(self.v2rayConfigLocal, 'w'), indent=2)

        print(v2rayConf, serverNameMap)
        json.dump(serverNameMap, open('./servers.json', 'w'), indent=2)

        print("\n重启 v2ray 服务……\n")
        subprocess.call('systemctl restart v2ray.service', shell=True)
        print('地址切换完成')
        print('代理端口协议：tcp')
        print('代理地址: 127.0.0.1')
        ports = {it['port']: serverNameMap[it['tag']]['name'] for it in v2rayConf['inbounds']}
        print('代理端口号：', ports)

    def testSpeed(self):

        # copy config.json
        print("\n当前模式为测速模式\n")
        print("\n正在备份现有配置文件 %s\n" % self.v2rayConfigLocal)
        subprocess.call('cp ' + self.v2rayConfigLocal + ' ' + self.v2rayConfigLocal + '.bak', shell=True)
        for i in range(len(self.serverListLink)):
            json.dump(self.serverListLink[i].formatConfig(), open(self.v2rayConfigLocal, 'w'), indent=2)
            subprocess.call('systemctl restart v2ray.service', shell=True)
            try:
                time.sleep(5)
                output = subprocess.check_output(
                    'curl -o /dev/null -s -w %{speed_download} -x socks5://127.0.0.1:7890 ' + self.testFileUrl,
                    shell=True)
            except KeyboardInterrupt:
                break
            except BaseException:
                output = b'0.000'

            print('【%d】%s : %d kb/s' % (i, self.serverListLink[i].remark, float(output) / 1000))

        print("\n正在恢复现有配置文件 %s\n" % self.v2rayConfigLocal)
        subprocess.call('mv ' + self.v2rayConfigLocal + '.bak ' + self.v2rayConfigLocal, shell=True)
        subprocess.call('systemctl restart v2ray.service', shell=True)


if __name__ == '__main__':
    sw = Switcher()
    sw.loadSubLink()
    sw.readSubInfo()
    sw.changeNode()
