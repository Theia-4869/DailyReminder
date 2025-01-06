import argparse
import pytz
import re
import requests
from datetime import datetime
from gnews import GNews



weekday_dict = {
    0: '一',
    1: '二',
    2: '三',
    3: '四',
    4: '五',
    5: '六',
    6: '日',
}

weekday_desp = {
    0: "新的一周开始啦",
    1: "今天是努力工作的一天",
    2: "周中是否会因为工作而产生一些小情绪呢",
    3: "再坚持一下就到周末啦",
    4: "明天就是周末啦",
    5: "今天是周末，不用上班",
    6: "今天可以继续休息",
}


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


def get_news():
    google_news = GNews(
        language='zh-Hans',
        country='CN',
        max_results=10,
        period='1d',
        exclude_websites=['news.cnhubei.com', 'www.ce.cn', 'm.36kr.com', 'www.guancha.cn']
    )
    
    news = []
    for topic in ['WORLD', 'BUSINESS', 'TECHNOLOGY']:
        topic_news = google_news.get_news_by_topic(topic=topic)
        if topic == 'WORLD':
            news += [new['title'].split(' - ')[0] for new in topic_news[:4]]
        else:
            news += [new['title'].split(' - ')[0] for new in topic_news[:3]]
    return news


def get_rates(alpha_vantage_key):
    rates = {"currency": {}, "crypto": {}, "future": {}, "stock": {}}
    
    # currency
    url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey={}"
    for currency in ['CNY/EUR', 'EUR/USD', 'EUR/GBP', 'CNY/USD', 'CNY/GBP', 'CNY/TWD', 'CNY/JPY', 'CNY/KRW', 'CNY/HKD']:
        content = requests.get(url.format(currency.split('/')[1], currency.split('/')[0], alpha_vantage_key))
        rate = content.json()['Realtime Currency Exchange Rate']['5. Exchange Rate']
        rates["currency"][currency] = float(rate) * 100.
    
    # crypto
    url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency=USD&apikey={}"
    for crypto in ['BTC', 'ETH']:
        content = requests.get(url.format(crypto, alpha_vantage_key))
        rate = content.json()['Realtime Currency Exchange Rate']['5. Exchange Rate']
        rates["crypto"][crypto] = float(rate)
    
    # future
    url = "https://tools.mgtv100.com/external/v1/pear/goldPrice"
    content = requests.get(url).json()['data']
    content ={future['dir']: future for future in content}
    rates["future"]["USD/XAU"] = float(content['usdgold']['midprice'])
    rates["future"]["USD/XPT"] = float(content['usdplatinum']['midprice'])
    rates["future"]["USD/XAG"] = float(content['usdsilver']['midprice'])
    
    # stock
    url = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}"
    for stock in ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOG', 'META']:
        content = requests.get(url.format(stock, alpha_vantage_key))
        rate = content.json()['Global Quote']['05. price']
        rates["stock"][stock] = float(rate)
    
    return rates


def get_title(date):
    return f"🌞 早安晨报 ({date.strftime('%m/%d')})"


def get_desp(date, weather_key, alpha_vantage_key, weather_location):
    desp = ""
    
    desp += f"🕒 现在是{date.year}年{date.month}月{date.day}日，{weather_location}时间早上{date.hour}时{date.minute}分，星期{weekday_dict[date.weekday()]}，"
    desp += f"{weekday_desp[date.weekday()]}，开启元气满满的一天吧！\n\n"
    
    # 天气
    cityid = requests.get(r'https://geoapi.qweather.com/v2/city/lookup?location={0}'.format(
        weather_location), headers={'X-QW-Api-Key': weather_key}).json()['location'][0]['id']
    weather_now = requests.get(r'https://devapi.qweather.com/v7/weather/now?location={0}&lang=zh'.format(
        cityid), headers={'X-QW-Api-Key': weather_key}).json()['now']
    weather_24h = requests.get(r'https://devapi.qweather.com/v7/weather/24h?location={0}&lang=zh'.format(
        cityid), headers={'X-QW-Api-Key': weather_key}).json()['hourly']
    weather_ind = requests.get(r'https://devapi.qweather.com/v7/indices/1d?type=0&location={0}&lang=zh'.format(
        cityid), headers={'X-QW-Api-Key': weather_key}).json()['daily']
    weather_7d = requests.get(r'https://devapi.qweather.com/v7/weather/7d?location={0}&lang=zh'.format(
        cityid), headers={'X-QW-Api-Key': weather_key}).json()['daily']
    weather_today = weather_7d[0]
    
    if '雨' in weather_today['textDay'] or '雪' in weather_today['textDay']:
        weather_today['textDay'] += "有"
    if '雨' in weather_today['textNight'] or '雪' in weather_today['textNight']:
        weather_today['textNight'] += "有"
    
    desp += f"⛅️ 当前天气：{weather_now['text']}，实时气温：{weather_now['temp']}°C，体感温度：{weather_now['feelsLike']}°C，风力情况：{weather_now['windDir']}{weather_now['windScale']}级。\n\n"
    desp += f"🌡️ 今日气温：{weather_today['tempMin']}°C~{weather_today['tempMax']}°C，白天{weather_today['textDay']}，{weather_today['windDirDay']}{weather_today['windScaleDay']}级，夜晚{weather_today['textNight']}，{weather_today['windDirNight']}{weather_today['windScaleNight']}级。\n\n"
    
    rain = [False, 0, 0]
    for weather_hourly in weather_24h:
        hour = int(re.search(r'T(\d{2})', weather_hourly['fxTime']).group(1))
        if hour == 0:
            break
        pop = int(weather_hourly['pop'])
        if pop > 50:
            rain[0] = True
            rain[1] = hour
            if pop > rain[2]:
                rain[2] = pop
    if rain[0]:
        desp += f"☔️ 今天可能会下雨，出门记得带伞哦！预计{rain[1]-date.hour}小时后降雨，降水概率为{rain[2]}%。\n\n"
    
    weather_ind = {daily['type']: daily for daily in weather_ind}
    desp += f"👕 天气指数："
    if len(cityid) == 9:
        desp += "\n\n"
        desp += f"穿衣指数：{weather_ind['3']['category']}({weather_ind['3']['level']})，{weather_ind['3']['text']}\n\n"
        desp += f"紫外线指数：{weather_ind['5']['category']}({weather_ind['5']['level']})，{weather_ind['5']['text']}\n\n"
        desp += f"运动指数：{weather_ind['1']['category']}({weather_ind['1']['level']})，{weather_ind['1']['text']}\n\n"
        desp += f"过敏指数：{weather_ind['7']['category']}({weather_ind['7']['level']})，{weather_ind['7']['text']}\n\n"
    else:
        desp += f"穿衣指数-{weather_ind['3']['category']}({weather_ind['3']['level']})，紫外线指数-{weather_ind['5']['category']}({weather_ind['5']['level']})，运动指数-{weather_ind['1']['category']}({weather_ind['1']['level']})。\n\n"
        
    desp += f"📅 未来6日天气预报：\n\n"
    for i, weather_7d in enumerate(weather_7d):
        if i == 0:
            continue
        desp += f"{weather_7d['fxDate'][5:]}(星期{weekday_dict[(date.weekday()+i)%7]})：气温{weather_7d['tempMin']}~{weather_7d['tempMax']}°C，白天{weather_7d['textDay']}，夜晚{weather_7d['textNight']}\n\n"
    
    # 新闻
    desp += f"📰 热点新闻：\n\n"
    news = get_news()
    for i, new in enumerate(news):
        desp += f"{i+1}. {new}\n\n"
    
    # 金融
    desp += f"💵 金融数据：\n\n"
    rates = get_rates(alpha_vantage_key)
    desp += f"CNY/EUR: {rates['currency']['CNY/EUR']:6.2f}, EUR/USD: {rates['currency']['EUR/USD']:6.2f}, EUR/GBP: {rates['currency']['EUR/GBP']:6.2f}\n\n"
    desp += f"CNY/USD: {rates['currency']['CNY/USD']:6.2f}, CNY/GBP: {rates['currency']['CNY/GBP']:6.2f}, CNY/TWD: {rates['currency']['CNY/TWD']:6.2f}\n\n"
    desp += f"CNY/JPY: {rates['currency']['CNY/JPY']:6.2f}, CNY/KRW: {rates['currency']['CNY/KRW']:6.2f}, CNY/HKD: {rates['currency']['CNY/HKD']:6.2f}\n\n"
    desp += f"USD/BTC: {rates['crypto']['BTC']:.2f}, USD/ETH: {rates['crypto']['ETH']:.2f}\n\n"
    desp += f"USD/XAU: {rates['future']['USD/XAU']:.1f}, USD/XPT: {rates['future']['USD/XPT']:.2f}, USD/XAG: {rates['future']['USD/XAG']:.2f}\n\n"
    desp += f"TSLA: {rates['stock']['TSLA']:.2f}, NVDA: {rates['stock']['NVDA']:.2f}, AAPL: {rates['stock']['AAPL']:.2f}\n\n"
    desp += f"MSFT: {rates['stock']['MSFT']:.2f}, GOOG: {rates['stock']['GOOG']:.2f}, META: {rates['stock']['META']:.2f}\n\n"
    
    phrase = requests.get(r'https://whyta.cn/api/tx/one?key=96f163cda80b').json()
    if phrase['code'] == 200:
        desp += f"📖 每日一句：{phrase['result']['word']}\n\n"
    
    return desp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-key", type=str)
    parser.add_argument("--weather-key", type=str)
    parser.add_argument("--alpha-vantage-key", type=str)
    parser.add_argument("--time-zone", type=str)
    parser.add_argument("--weather-location", type=str)
    args = parser.parse_args()
    
    timezone = pytz.timezone(args.time_zone)
    date = datetime.now(timezone)
    
    ret = sc_send(args.send_key, get_title(date), get_desp(date, args.weather_key, args.alpha_vantage_key, args.weather_location))
    print(ret['data']['error'])