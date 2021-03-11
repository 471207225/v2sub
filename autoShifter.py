import requests
import json


class Shifter:

    def readServers(self):
        return json.load(open('./servers.json', 'r'))

    def shift(self):
        servers = self.readServers()

        speeds = []
        for k, server in servers.items():
            proxies = {
                "http": "http://127.0.0.1:" + str(server['port']),
                "https": "http://127.0.0.1:" + str(server['port']),
            }

            print(server['name'])

            try:
                r = requests.get("https://codemagic.io/", proxies=proxies)
                speeds.append({**server, "speed": r.elapsed.total_seconds()})
                print(r.elapsed.total_seconds())
            except Exception as e:
                print(e.args)

        if len(speeds) > 0:
            sortedSpeeds = sorted(speeds, key=lambda x: x['speed'])
            first = sortedSpeeds[0]
            requests.get("http://backend.xxhaitun.com/output/set-proxy-port?port=" + str(first['port']))
            with open('./shift_logs.log', 'a') as f:
                f.write(
                    "set proxy %s:%s %s"
                    % (first['name'], str(first['port']), str(first['speed']))
                )


# */10 * * * *   python /root/v2ray/autoShifter.py >> /root/v2ray/cron_logs.log
if __name__ == '__main__':

    import time

    print(time.strftime("Y-m-d H:i:s", time.localtime()))

    s = Shifter()
    s.shift()
