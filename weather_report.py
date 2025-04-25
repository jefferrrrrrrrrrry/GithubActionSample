# 安装依赖 pip3 install requests html5lib bs4 schedule
import os
import requests
import json
from bs4 import BeautifulSoup
from typing import List, Dict

class UserConfig:
    def __init__(self, app_id: str, app_secret: str, open_id: str, template_id: str, city: str):
        self.app_id = app_id.strip()
        self.app_secret = app_secret.strip()
        self.open_id = open_id.strip()
        self.template_id = template_id.strip()
        self.city = city.strip()

def get_user_configs() -> List[UserConfig]:
    """
    从环境变量获取所有用户配置
    环境变量格式：APP_ID="id1,id2,id3" APP_SECRET="secret1,secret2,secret3" 等
    """
    app_ids = os.environ.get("APP_ID", "").strip().split(',')
    app_secrets = os.environ.get("APP_SECRET", "").strip().split(',')
    open_ids = os.environ.get("OPEN_ID", "").strip().split(',')
    template_ids = os.environ.get("TEMPLATE_ID", "").strip().split(',')
    cities = os.environ.get("CITY", "北京").strip().split(',')  # 默认城市为北京
    
    # 确保至少有一组完整的配置
    if not (app_ids[0] and app_secrets[0] and open_ids[0] and template_ids[0]):
        raise ValueError("至少需要配置一个用户的完整信息")
    
    # 确保所有数组长度一致
    max_length = max(len(app_ids), len(app_secrets), len(open_ids), len(template_ids))
    
    # 如果某个配置项的数量少于最大数量，使用最后一个值进行填充
    app_ids.extend([app_ids[-1]] * (max_length - len(app_ids)))
    app_secrets.extend([app_secrets[-1]] * (max_length - len(app_secrets)))
    open_ids.extend([open_ids[-1]] * (max_length - len(open_ids)))
    template_ids.extend([template_ids[-1]] * (max_length - len(template_ids)))
    cities.extend([cities[-1]] * (max_length - len(cities)))
    
    configs = []
    for i in range(max_length):
        configs.append(UserConfig(
            app_id=app_ids[i],
            app_secret=app_secrets[i],
            open_id=open_ids[i],
            template_id=template_ids[i],
            city=cities[i]
        ))
    
    return configs

def get_weather(my_city):
    urls = ["http://www.weather.com.cn/textFC/hb.shtml",
            "http://www.weather.com.cn/textFC/db.shtml",
            "http://www.weather.com.cn/textFC/hd.shtml",
            "http://www.weather.com.cn/textFC/hz.shtml",
            "http://www.weather.com.cn/textFC/hn.shtml",
            "http://www.weather.com.cn/textFC/xb.shtml",
            "http://www.weather.com.cn/textFC/xn.shtml"
            ]
    for url in urls:
        resp = requests.get(url)
        text = resp.content.decode("utf-8")
        soup = BeautifulSoup(text, 'html5lib')
        div_conMidtab = soup.find("div", class_="conMidtab")
        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")[2:]
            for index, tr in enumerate(trs):
                tds = tr.find_all("td")
                # 这里倒着数，因为每个省会的td结构跟其他不一样
                city_td = tds[-8]
                this_city = list(city_td.stripped_strings)[0]
                if this_city == my_city:

                    high_temp_td = tds[-5]
                    low_temp_td = tds[-2]
                    weather_type_day_td = tds[-7]
                    weather_type_night_td = tds[-4]
                    wind_td_day = tds[-6]
                    wind_td_day_night = tds[-3]

                    high_temp = list(high_temp_td.stripped_strings)[0]
                    low_temp = list(low_temp_td.stripped_strings)[0]
                    weather_typ_day = list(weather_type_day_td.stripped_strings)[0]
                    weather_type_night = list(weather_type_night_td.stripped_strings)[0]

                    wind_day = list(wind_td_day.stripped_strings)[0] + list(wind_td_day.stripped_strings)[1]
                    wind_night = list(wind_td_day_night.stripped_strings)[0] + list(wind_td_day_night.stripped_strings)[1]

                    # 如果没有白天的数据就使用夜间的
                    temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                    weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                    wind = f"{wind_day}" if wind_day != "--" else f"{wind_night}"
                    return this_city, temp, weather_typ, wind


def get_access_token(app_id, app_secret):
    # 获取access token的url
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(app_id, app_secret)
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token


def get_daily_love():
    # 每日一句情话
    url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
    r = requests.get(url)
    all_dict = json.loads(r.text)
    sentence = all_dict['returnObj'][0]
    daily_love = sentence
    return daily_love


def send_weather(access_token, user_config, weather):
    # touser 就是 openID
    # template_id 就是模板ID
    # url 就是点击模板跳转的url
    # data就按这种格式写，time和text就是之前{{time.DATA}}中的那个time，value就是你要替换DATA的值

    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    body = {
        "touser": user_config.open_id,
        "template_id": user_config.template_id,
        "url": "https://weixin.qq.com",
        "data": {
            "date": {
                "value": today_str
            },
            "region": {
                "value": weather[0]
            },
            "weather": {
                "value": weather[2]
            },
            "temp": {
                "value": weather[1]
            },
            "wind_dir": {
                "value": weather[3]
            },
            "today_note": {
                "value": get_daily_love()
            }
        }
    }
    url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
    print(requests.post(url, json.dumps(body)).text)


def weather_report(user_config):
    # 1.获取access_token
    access_token = get_access_token(user_config.app_id, user_config.app_secret)
    # 2. 获取天气
    weather = get_weather(user_config.city)
    print(f"天气信息： {weather}")
    # 3. 发送消息
    send_weather(access_token, user_config, weather)


if __name__ == '__main__':
    user_configs = get_user_configs()
    for user_config in user_configs:
        weather_report(user_config)
