import argparse
import pytz
import re
import requests
from datetime import datetime



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


def get_title(date):
    return f"🍽️ 吃饭提醒 ({date.strftime('%m/%d')})"


def get_desp(date):
    desp = ""
    desp += f"🕒 现在是{date.year}年{date.month}月{date.day}日{date.hour}时{date.minute}分\n\n"
    if date.hour < 12:
        desp += f"🍳 新的一天刚刚开始，不要忘记吃早餐哦！"
    elif date.hour < 18:
        desp += f"🍛 工作再忙，也不要忘记吃午饭哦！"
    else:
        desp += f"🍝 一天的工作结束了，快去吃点好的犒劳一下自己吧！"
    return desp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-key", type=str)
    parser.add_argument("--time-zone", type=str)
    args = parser.parse_args()
    
    timezone = pytz.timezone(args.time_zone)
    date = datetime.now(timezone)
    
    ret = sc_send(args.send_key, get_title(date), get_desp(date))
    print(ret['data']['error'])