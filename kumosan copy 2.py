# -*- coding:utf-8 -*-
import discord
import datetime
import os
import configparser
import logging

#import wikipedia
# import requests
#import json
#import random
#import re
#import subprocess
#import time
#import urllib.request
#from bs4 import BeautifulSoup
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

# ロギングの設定
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a',
                    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# 設定ファイルの読み出し
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
# サーバのauthトークン(str), bot管理者のユーザID(int), いくつかのメソッドで特に利用するチャンネルid(dict[str])
my_token = config_ini.get('TOKEN', 'my_token')
admin_id = config_ini.get('ADMIN_ID', 'admin_id')
channel_dict = config_ini.items('USE_CHANNELS')
channel_dict = dict(channel_dict)


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


@client.event
async def on_message(message):
    logging.info(f"Message received: {message.content} from {message.author}")
    channel = message.channel
    user_id = message.author.id
    current_date = datetime.datetime.now().date()

    if message.content.startswith("占い"):
        if user_id in last_uranai_usage and last_uranai_usage[user_id] == current_date:
            await message.channel.send("今日はもう占ったよ！また明日来てね！")
        else:
            last_uranai_usage[user_id] = current_date
            msg = uranai.uranai()  # 占いの結果を取得
            await message.channel.send(msg)
            logging.info(f"占い was triggered by {message.author}: {msg}")

    elif message.content.startswith("おみくじ"):
        msg = omikuji.omikuji()  # おみくじの結果を取得
        await message.channel.send(msg)
        logging.info(f"おみくじ was triggered by {message.author}: {msg}")

# ループ状態に入って対象のdiscordサーバを監視
@client.event
async def on_message(message):
    logging.info(f"Message received: {message.content} from {message.author}")

    # メッセージが投稿されたチャンネル情報を格納
    channel = message.channel
    
    ######## 管理者直操作モード ########
    # - admin_idユーザのみ利用できるモード
    # - back_modeチャンネルに投稿したメッセージをDJアイズに喋らせる
    # - ex)`main DJアイズだよ！`
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
    ####################################

    ######## ここからが主な機能のハンドル ########
    # 「DJアイズ」で始まるか調べる
    elif message.content.startswith("DJアイズ"):
    # 送り主がBotだった場合反応したくないので
        if client.user != message.author:
            try:
                user_name = message.author.name
                user_id = message.author.id
                text = message.content
                print(text)

                msg =  kumo_san + user_name + 'さん '
                #msg = user_name + 'さん '
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
                elif text.find('おみくじ') > -1:
                    logging.info(f"おみくじ command triggered by {message.author}")

                    msg += omikuji.omikuji()
                    logging.info(f"おみくじ result: {msg}")

                elif text.find('大丈夫') > -1 or text.find('生きてる') > -1 or text.find('元気') > -1 or text.find('死んでない') > -1:
                    msg = '大丈夫です！'
                elif text.find('好き') > -1 or text.find('愛') > -1 or text.find('すき') > -1 or text.find('かわいい') > -1 or text.find('可愛い') > -1:
                    msg = 'えへへ'
                elif text.find('嫌い') > -1 or text.find('きらい') > -1:
                    msg = 'えへへ'
                elif text.find('ぬるぽ') > -1 or text.find('NullPointerException') > -1:
                    msg = 'ガッ'
                elif text.find('月曜日が') > -1:
                    msg = '.........始マンデイ！！！！！！:crescent_moon:'
                elif text.find('木曜日') > -1 or text.find('もくもく') > -1:
                    msg = 'もくもくもくようび〜\n'+kumo_san+'\n\n(・_・)ｽｯ\n\nなにがもくもくもくようびだ\n明日もまた仕事だぞ :cloud_lightning:'
                elif text.find('悪い子では') > -1:
                    msg = '悪い子ですね！'
                elif text.find('悪い子') > -1 or text.find('不正') > -1 or text.find('じゃんけん') > -1:
                    msg = '知らない。よく覚えてない。'
                elif text.find('自己紹介') > -1:
                    msg = 'はい！はじめまして。天ちゃんに作られた陽気なbotのDJアイズと申します。趣味は素数を数えることです。皆さんのお役に立てるようにがんばりますので、どうぞよろしくお願いします！:cloud:'
                elif text.find('help') > -1 or text.find('-h') > -1:
                    msg += 'https://discordapp.com/channels/407045885281828877/407050154315874315/558382007433035786'
                #### ここからメソッドを呼び出して使うトリガー検知 ####
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
                    msg += weather.get_weather_information(text)
                elif text.find('は素数') > -1:
                    msg += primarity_test.primarity_test(text, 50)
                ######## clear in #暴風域 ########
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

                ##################################
                else:
                    msg += 'その言葉は知らなかったから調べたよ。\n' + wiki.wiki(text)
                    #メッセージが送られてきたチャンネルへメッセージを送ります
                await channel.send(msg)
                logging.info(f"Responded with: {msg} to {message.author} in channel {message.channel}")

                return msg
            except Exception as e:
                logging.error(f"Error while handling message: {e}")

                print(e)
                raise e
            
        # コンソールにもログを出力するためのハンドラーを追加
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)


client.run(my_token)
