# -*- coding:utf-8 -*-
import discord
import datetime
import os
import logging
import asyncio
import random
import aiohttp
import requests  # requestsライブラリのインポート
import time  # timeモジュールのインポート

from urllib.parse import quote
from flask import Flask
from threading import Thread
from config.config import DISCORD_BOT_TOKEN, ADMIN_ID, MAIN_CHAT_CHANNEL, BOT_SALON_CHANNEL, BACK_MODE_CHANNEL, GRAVE_CHANNEL, STORM_CHANNEL, DEV_CHANNEL, POKEMON_CHANNEL, WEATHER_API_KEY

from lib import wiki
from lib import weather
from lib import waruiko_point
from lib import uranai
from lib import primarity_test
from lib import omikuji
from lib import narou
from lib import modokicraft
from lib import minesweeper
from lib import meigen
from lib import keisuke_honda
from lib import dominator
from lib import dice

# Flaskのインスタンスを作成
app = Flask(__name__)

# ロギングの設定
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a', format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# 環境変数から設定を読み込む
my_token = DISCORD_BOT_TOKEN
admin_id = ADMIN_ID
channel_dict = {
    'main_chat': MAIN_CHAT_CHANNEL,
    'bot_salon': BOT_SALON_CHANNEL,
    'back_mode': BACK_MODE_CHANNEL,
    'grave': GRAVE_CHANNEL,
    'storm': STORM_CHANNEL,
    'dev': DEV_CHANNEL,
    'pokemon': POKEMON_CHANNEL
}

# Intentsの設定
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

# このbotのアカウント情報を格納、Intentsも渡す
client = discord.Client(intents=intents)

################# Don't touch. ################
kumo_san = '╭◜◝ ͡ ◜◝╮ \n(   •ω•　  ) \n╰◟◞ ͜ ◟◞╯ < '
################# Don't touch. ################

# ユーザーが占いを使った日を記録する辞書
last_uranai_usage = {}

@client.event
async def on_ready():
    print('Logged in as')
    print('Name: ' + client.user.name)
    print('ID:   ' + str(client.user.id))
    print('--------\n')

async def get_weather_information(location, days=1):
    api_key = WEATHER_API_KEY
    base_url = 'http://api.weatherapi.com/v1/forecast.json'
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    response_string = ''

    location_for_geocoding = location
    if any(pref in location for pref in ("北海道", "東京都", "京都府", "大阪府")):
        pass
    elif "県" not in location:
        location_for_geocoding += "県"

    geocoding_url = f"http://api.weatherapi.com/v1/search.json?key={api_key}&q={quote(location_for_geocoding)}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(geocoding_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        lat = data[0]['lat']
                        lon = data[0]['lon']
                        weather_url = f"{base_url}?key={api_key}&q={lat},{lon}&days={days}&dt={date_str}&lang=ja"
                        async with session.get(weather_url) as weather_response:
                            if weather_response.status == 200:
                                weather_data = await weather_response.json()
                                mintemp = weather_data['forecast']['forecastday'][0]['day']['mintemp_c']
                                maxtemp = weather_data['forecast']['forecastday'][0]['day']['maxtemp_c']
                                avgtemp = weather_data['forecast']['forecastday'][0]['day']['avgtemp_c']
                                condition = weather_data['forecast']['forecastday'][0]['day']['condition']['text']

                                weather_emoji = ""
                                if "晴" in condition:
                                    weather_emoji = "☀️"
                                elif "雨" in condition:
                                    weather_emoji = "🌧️"
                                elif "雪" in condition:
                                    weather_emoji = "❄️"
                                elif "雷" in condition:
                                    weather_emoji = "⚡"
                                else:
                                    weather_emoji = "☁️"

                                response_string = f"{location}の天気予報 {weather_emoji}\n\n最低気温は{mintemp}°C\n最高気温は{maxtemp}°C\n平均気温は{avgtemp}°C\n天気 - {condition}\n\n信じるも信じないもあなた次第👆"
                                return response_string
                            else:
                                return f"天気情報の取得に失敗しました。エラーコード: {weather_response.status} :cold_sweat:"
                    else:
                        return f"{location}の場所が見つかりませんでした。 :cold_sweat:"
                else:
                    return f"ジオコーディングに失敗しました。エラーコード: {response.status} :cold_sweat:"
    except Exception as e:
        return f'天気検索でエラーです :cold_sweat:\n{e}\n'

@client.event
async def on_message(message):
    logging.info(f"Message received: {message.content} from {message.author}")
    channel = message.channel
    user_id = message.author.id
    current_date = datetime.datetime.now().date()

    if message.author == client.user:
        return

    if '天気' in message.content:
        await message.channel.send(f"{message.author.mention} どの県の天気を表示しますか？")

        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:
            reply = await client.wait_for('message', check=check, timeout=30.0)
            prefecture = reply.content
            msg = await get_weather_information(prefecture)
            await message.channel.send(msg)
        except asyncio.TimeoutError:
            prefecture = random.choice(['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'])
            msg = await get_weather_information(prefecture)
            await message.channel.send(f"{message.author.mention} 時間内に県名が送信されなかったため、ランダムに選んだ {prefecture} の天気を表示します。")

    if '占い' in message.content:
        if user_id in last_uranai_usage and last_uranai_usage[user_id] == current_date:
            await message.channel.send("今日はもう占ったよ！また明日来てね！")
        else:
            last_uranai_usage[user_id] = current_date
            user_name = message.author.display_name  # ユーザー名を取得
            msg = uranai.uranai(user_name)  # 占いの結果を取得
            await message.channel.send(msg)
            logging.info(f"占い was triggered by {message.author}: {msg}")

    elif 'おみくじ' in message.content:
        msg = omikuji.omikuji()  # おみくじの結果を取得
        await message.channel.send(msg)
        logging.info(f"おみくじ was triggered by {message.author}: {msg}")

    elif '犯罪係数' in message.content:
        msg = dominator.dominator(message.content)  # 犯罪係数の結果を取得
        await message.channel.send(msg)
        logging.info(f"犯罪係数 was triggered by {message.author}: {msg}")

    if message.channel == client.get_channel(int(channel_dict['back_mode'])) and str(message.author.id) == admin_id:
        try:
            text = message.content
            selector = int(channel_dict['bot_salon'])
            index_st = text.find(' ')+1
            index_ed = text.find(' ')
            search_channel = text[:index_ed]
            search_text = text[index_st:]
            print(search_channel)
            print(search_text)
            if search_channel == 'bot' or search_channel == 'bot_salon':
                selector = int(channel_dict['bot_salon'])
            elif search_channel == 'main' or search_channel == 'main_chat':
                selector = int(channel_dict['main_chat'])
            elif search_channel == 'storm':
                selector = int(channel_dict['storm'])
            elif search_channel == 'grave' or search_channel == 'hakaba':
                selector = int(channel_dict['grave'])
            elif search_channel == 'dev':
                selector = int(channel_dict['dev'])
            elif search_channel == 'pokemon':
                selector = int(channel_dict['pokemon'])
            else:
                selector = int(channel_dict['bot_salon'])
            print(selector)
            msg = kumo_san + search_text
            await client.get_channel(selector).send(msg)
            logging.info(f"Admin command executed: {msg} in channel {selector}")
            return msg
        except Exception as e:
            logging.error(f"Error in admin command: {e}")
            print(e)
            raise e 

    elif message.content.startswith("DJアイズ"):
        if client.user != message.author:
            try:
                user_name = message.author.name
                user_id = message.author.id
                text = message.content
                print(text)

                msg =  kumo_san + user_name + 'さん '
                if text == ('DJアイズ'):
                    msg = 'はい！ご用でしょうか！'
                    logging.info(f"DJアイズ basic call response triggered by {message.author}")

                elif text.find('おは') > -1:
                    logging.info(f"おはようございます command triggered by {message.author}")
                    msg += 'おはようございます！'
                elif text.find('こんにちは') > -1 or text.find('こんにちわ') > -1 or text.find('こんちゃ') > -1 or text.find('やあ') > -1 or text.find('おっす') > -1 or text.find('こんにち') > -1:
                    msg += 'こんにちは！'
                    logging.info(f"こんにちは command triggered by {message.author}")
                elif text.find('こんばんは') > -1 or text.find('こんばんわ') > -1 or text.find('ばんわ') > -1 or text.find('こんばん') > -1:
                    msg += 'こんばんは！'
                elif text.find('おつ') > -1 or text.find('疲') > -1 or text.find('お先') > -1 or text.find('おち') > -1 or text.find('落ち') > -1:
                    msg += 'おつかれさまです！'  
                elif text.find('おやす') > -1:
                    msg += 'おやすみなさーい！'
                elif text.find('ありがと') > -1 or text.find('thank') > -1 or text.find('thx') > -1:
                    msg += 'お役に立てたならなによりです！'
                elif text.find('慰めて') > -1 or text.find('なぐさめて') > -1 or text.find('アドバイス') > -1 or text.find('助言') > -1:
                    msg = meigen.meigen()
                elif text.find('グー') > -1 or text.find('チョキ') > -1 or text.find('パー') > -1 or text.find('ぐー') > -1 or text.find('ちょき') > -1 or text.find('ぱー') > -1:
                    msg = keisuke_honda.keisuke_honda(text, user_id)
                elif text.find('なろう') > -1: 
                    msg = narou.narou_search(text)
                elif text.find('犯罪係数') > -1 or text.find('ドミネータ') > -1 or text.find('サイコパス') > -1 or text.find('色相') > -1 or text.find('シビュラ') > -1:
                    msg = kumo_san + dominator.dominator(text)
                elif text.find('modokicraft') > -1:
                    msg += modokicraft.send_signal_to_modokicraft(text)
                elif text.find('wp') > -1:
                    msg = kumo_san + waruiko_point.waruiko_point(text, user_id)
                elif text.find('マインスイーパ') > -1 or text.find('まいんすいーぱ') > -1:
                    msg += '出題！\n' + minesweeper.minesweeper(text)
                elif text.find('級') > -1 or text.find('遊ぼ') > -1 or text.find('遊んで') > -1 or text.find('あそぼ') > -1 or text.find('あそんで') > -1:
                    msg += 'マインスイーパーしましょう！\n' + minesweeper.minesweeper(text)
                elif text.find('座') > -1:
                    msg += uranai.uranai(text)
                elif text.find('d') > -1:
                    msg += 'のダイス結果です\n' + dice.nDn(text)
                elif text.find('って何') > -1 or text.find('ってなに') > -1:
                    msg += wiki.wikipedia_search(text)
                elif text.find('天気') > -1:
                    msg += await get_weather_information(text)
                elif text.find('は素数') > -1:
                    msg += primarity_test.primarity_test(text, 50)
                elif text.find('おそうじ') > -1 or text.find('お掃除') > -1:
                    history = ""
                    if channel == client.get_channel(int(channel_dict['storm'])):
                        async for i in channel.history(oldest_first=True):
                            history += i.author.display_name+" "+i.content+"\n"
                        date = datetime.datetime.today().strftime("%Y_%m_%d")
                        path = 'removed_chat_logs/'+ date +'.txt'
                        if os.path.isfile(path) == False:
                            with open(path, mode='w') as f:
                                f.write(history)
                        else:
                            with open(path, mode='a') as f:
                                f.write(history)
                        await channel.purge()
                        msg += '塵一つ残しません！ :cloud_tornado: '
                        logging.info("Cleaning command executed in storm channel")
                    else:
                        msg += 'このコマンドは #暴風域 でしか使えないよ！'
                        logging.info("Cleaning command attempted outside storm channel")
                else:
                    msg += 'その言葉は知らなかったから調べたよ。\n' + wiki.wiki(text)
                await channel.send(msg)
                logging.info(f"Responded with: {msg} to {message.author} in channel {message.channel}")
                return msg
            except Exception as e:
                logging.error(f"Error while handling message: {e}")
                print(e)
                raise e

# Flaskのルート定義
@app.route('/')
def home():
    return "Hello, this is a placeholder for the Discord bot server."

# Discord Botを別スレッドで実行
def run_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(client.start(my_token))
    loop.run_forever()

# Keep-Aliveスクリプト
def keep_alive():
    while True:
        try:
            response = requests.get('https://uranaibot.azurewebsites.net')  # Azure App ServiceのURL
            if response.status_code == 200:
                print("Keep-alive request successful.")
            else:
                print(f"Keep-alive request failed with status code: {response.status_code}")
        except Exception as e:
            print(f"Keep-alive request encountered an error: {e}")
        time.sleep(300)  # 5分ごとにリクエストを送信

if __name__ == "__main__":
    # Flaskサーバーをメインスレッドで実行
    Thread(target=run_discord_bot).start()
    Thread(target=keep_alive).start()
    app.run(host="0.0.0.0", port=8000)
