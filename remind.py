import argparse
import pytz
import re
import requests
from datetime import datetime


# send_keys = {
#     "zhangqizhe": 'SCT93347TMIJdNWyZgmrMWGK7kIZvA5nb',
#     "chenning": 'SCT266074TMuRnhHWwe8oNd6BSEFNeA6cd',
# }

# time_zones = {
#     "zhangqizhe": 'Asia/Shanghai',
#     "chenning": 'Europe/Paris',
# }


def sc_send(sendkey, title, desp='', options={}):

    if sendkey.startswith('sctp'):
        match = re.match(r'sctp(\d+)t', sendkey)
        if match:
            num = match.group(1)
            url = f'https://{num}.push.ft07.com/send/{sendkey}.send'
        else:
            raise ValueError('Invalid sendkey format for sctp')
    else:
        url = f'https://sctapi.ftqq.com/{sendkey}.send'
    
    params = {
        'title': title,
        'desp': desp,
        **options
    }
    headers = {
        'Content-Type': 'application/json;charset=utf-8'
    }
    response = requests.post(url, json=params, headers=headers)
    result = response.json()
    return result


def get_title(time_zone):
    timezone = pytz.timezone(time_zone)
    date = datetime.now(timezone)
    return f"💉 吃药提醒 ({date.strftime('%m/%d')})"


def get_desp(time_zone):
    desp = ""
    
    timezone = pytz.timezone(time_zone)
    date = datetime.now(timezone)
    
    desp += f"🕒 现在是{date.year}年{date.month}月{date.day}日{date.hour}时{date.minute}分\n\n"
    desp += f"🐇感冒了，不要忘记吃💊哦！"
    return desp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-key", type=str)
    parser.add_argument("--time-zone", type=str)
    args = parser.parse_args()
    
    ret = sc_send(args.send_key, get_title(args.time_zone), get_desp(args.time_zone))
    print(ret['data']['error'])