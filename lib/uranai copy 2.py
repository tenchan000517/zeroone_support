import requests
import datetime
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)

# Uranai function
def uranai(text):
    response_string = ''
    seiza = -1  # インデックスの初期値を有効な範囲外に設定
    date = datetime.datetime.today().strftime("%Y/%m/%d")
    index_st = text.find(' ')+1
    index_ed = text.find('座')+1
    search_text = text[index_st:index_ed].strip()  # 前後の空白を削除
    logging.info(f"Search text for Uranai: {search_text}")
    
    seiza_list = ("牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座")
    seiza_list2 = ("おひつじ座", "おうし座", "ふたご座", "かに座", "しし座", "おとめ座", "てんびん座", "さそり座", "いて座", "やぎ座", "みずがめ座", "うお座")
   
    if search_text in seiza_list:
        seiza = seiza_list.index(search_text)
    elif search_text in seiza_list2:
        seiza = seiza_list2.index(search_text)

    if seiza == -1:
        logging.warning("Star sign not found in the list: {search_text}")
        return "君の星が…見えない… :cloud:"

    logging.info(f"Making API request for {date} horoscope for {search_text}")
    try:
        res = requests.get(url=f'http://api.jugemkey.jp/api/horoscope/free/{date}')
        if res.status_code == 200:
            logging.info("API request successful.")
            txt = res.json()["horoscope"][date][seiza]
            logging.info(f"API response for {search_text}: {txt}")
            
            job = emoji(int(txt["job"]), "job")
            money = emoji(int(txt["money"]), "money")
            love = emoji(int(txt["love"]), "love")
            total = emoji(int(txt["total"]), "total")
            response_string = f"今日の**{txt['sign']}**の運勢は。。。**{txt['rank']}位**！\n{txt['content']}\nラッキーアイテムは**{txt['item']}**で、ラッキーカラーは**{txt['color']}**。\n仕事運：{job}\n金運：{money}\n恋愛運：{love}\nトータルは...{total}です！良い一日を！"
            logging.info("Uranai response constructed successfully.")
        else:
            logging.error(f"API request failed with status code: {res.status_code}")
            return "星座の運勢を取得できませんでした。"
    except Exception as e:
        logging.error(f"Exception during API request: {e}")
        return "星座の運勢を取得できませんでした。"
    
    return response_string

def emoji(number, category):
    res = ''
    for i in range(number):
        if category == 'job':
            res += ':briefcase: '
        elif category == 'money':
            res += ':moneybag: '
        elif category == 'love':
            res += ':heart: '
        elif category == 'total':
            res += ':star: '
    return res
