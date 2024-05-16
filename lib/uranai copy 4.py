import requests
import datetime

# Uranai
def uranai(text):
    response_string = ''
    seiza = 100
    date = datetime.datetime.today().strftime("%Y/%m/%d")
    index_st = max(text.find('牡羊座'), text.find('牡牛座'), text.find('双子座'), text.find('蟹座'), text.find('獅子座'), text.find('乙女座'), text.find('天秤座'), text.find('蠍座'), text.find('射手座'), text.find('山羊座'), text.find('水瓶座'), text.find('魚座'))
    if index_st == -1:
        index_st = max(text.find('おひつじ座'), text.find('おうし座'), text.find('ふたご座'), text.find('かに座'), text.find('しし座'), text.find('おとめ座'), text.find('てんびん座'), text.find('さそり座'), text.find('いて座'), text.find('やぎ座'), text.find('みずがめ座'), text.find('うお座'))
    index_ed = index_st + 3
    search_text = text[index_st:index_ed]

    print(search_text)

    seiza_list = ("牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座") 
    seiza_list2 = ("おひつじ座", "おうし座", "ふたご座", "かに座", "しし座", "おとめ座", "てんびん座", "さそり座", "いて座", "やぎ座", "みずがめ座", "うお座")

    try:
        seiza = seiza_list.index(search_text)
    except:
        try:
            seiza = seiza_list2.index(search_text)  
        except Exception as e:
            response_string = "君の星座が見つからなかったよ。牡羊座、牡牛座、双子座、蟹座、獅子座、乙女座、天秤座、蠍座、射手座、山羊座、水瓶座、魚座のどれかで指定してね！ :cloud:"
            return response_string

    try:
        res = requests.get(url='http://api.jugemkey.jp/api/horoscope/free/'+ date)
        txt = res.json()["horoscope"][date][seiza]
        job = emoji(int(txt["job"]), "job") 
        money = emoji(int(txt["money"]), "money")
        love = emoji(int(txt["love"]), "love")
        total = emoji(int(txt["total"]), "total")

        response_string = "今日の\*\*" + txt["sign"] + "\*\*の運勢は。。。\*\*" + str(txt["rank"]) + "位\*\*！\\n" + txt["content"] + "\\nラッキーアイテムは\*\*" + txt["item"] + "\*\*で、ラッキーカラーは\*\*" + txt["color"] + "\*\*。\\n仕事運："+job+"\\n金　運：" + money + "\\n恋愛運：" + love + "\\nトータルは..." + total + "です！良い一日を！"
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