#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import copy

v2rayBaseConf = {
    "log": {
        "access": "/var/log/v2ray/access.log",
        "error": "/var/log/v2ray/error.log",
        "logLevel": "none"
    },
    "inbounds": [

    ],
    "outbounds": [
        {
            "settings": {},
            "protocol": "freedom",
            "tag": "direct"
        },
        {
            "settings": {},
            "protocol": "blackhole",
            "tag": "blocked"
        }
    ],
    "routing": {
        "strategy": "rules",
        "settings": {
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "ip": [
                        "geoip:cn",
                        "geoip:private"
                    ],
                    "outboundTag": "direct"
                },
                {
                    "type": "field",
                    "inboundTag": ["in"],
                    "outboundTag": "out"
                }
            ]
        }
    }
}


class ConfMaker:

    def __init__(self, servers):
        self.servers = servers
        for i, server in enumerate(servers):
            server['inPort'] = 7810 + i

    def formatConfig(self):
        v2rayConf = copy.copy(v2rayBaseConf)

        serverNameMap = {}
        for i, server in enumerate(self.servers):
            inTag = "server_in_" + str(i)
            outTag = "server_out_" + str(i)

            inBound = self.makeInBound(inTag, port=server['inPort'])
            outBound = self.makeOutBound(outTag, server['ip'], server['port'], server['uuid'], server['alterId'])
            rule = self.makeRule(inTag, outTag)

            v2rayConf['inbounds'].append(inBound)
            v2rayConf['outbounds'].append(outBound)
            v2rayConf['routing']['settings']['rules'].append(rule)

            serverNameMap[inTag] = {"out": outTag, 'name': server['remark'], 'port': server['inPort']}

        return v2rayConf, serverNameMap

    def makeRule(self, inTag, outTag):
        return {
            "type": "field",
            "inboundTag": [inTag],
            "outboundTag": outTag
        }

    def makeInBound(self, tag, port):
        return {
            "port": int(port),
            "protocol": "http",
            "settings": {
                "accounts": [],
            },
            "tag": tag
        }

    def makeOutBound(self, tag, ip, port, uuid, alterId):
        return {
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": ip,
                    "port": int(port),
                    "users": [
                        {
                            "id": uuid,
                            "alterId": alterId
                        }
                    ]
                }]
            },
            "streamSettings": {
                "network": "tcp"
            },
            "tag": tag
        }
