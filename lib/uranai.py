import requests
import datetime
import random

# Uranai
def uranai(user_name):
    response_string = ''
    date = datetime.datetime.today().strftime("%Y/%m/%d")

    try:
        res = requests.get(url='http://api.jugemkey.jp/api/horoscope/free/'+ date)
        seiza = random.randint(0, 11)  # 0から11までの乱数を生成し、星座をランダムに選択
        txt = res.json()["horoscope"][date][seiza]
        job = emoji(int(txt["job"]), "job")
        money = emoji(int(txt["money"]), "money")
        love = emoji(int(txt["love"]), "love")
        total = emoji(int(txt["total"]), "total")

        # ランキングをパーセンテージに変換
        rank = int(txt["rank"])
        percentage = (12 - (rank - 1)) * 100 // 12

        # 完全ランダムで下一桁を足す
        random_digit = random.randint(0, 9)
        final_percentage = min(percentage + random_digit, 100)

        response_string = f"今日の**{user_name}**の運勢は...**{final_percentage}％**！\n" + txt["content"] + "\nラッキーアイテムは**" + txt["item"] + "**で、ラッキーカラーは**" + txt["color"] + "**。\n仕事運："+job+"\n金　運：" + money + "\n恋愛運：" + love + "\nトータルは..." + total + "です！良い一日を！"
    except Exception as e:
        print(e)
        response_string = "今日の占いはお休みです :zzz:"

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