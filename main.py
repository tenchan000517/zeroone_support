# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
import datetime
import os
import logging
import asyncio
import random
import aiohttp
from urllib.parse import quote
from dotenv import load_dotenv

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
from lib.gemini_chat import GeminiChat
from models.database import init_db

# 環境変数をロード
load_dotenv()

# ロギングの設定
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a', format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

# Intentsの設定
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

# このbotのアカウント情報を格納、CommandsBotを使用
client = commands.Bot(command_prefix='DJアイズ ', intents=intents)

# Gemini AIインスタンス
gemini_chat = None

# データベース初期化
init_db()

################# Don't touch. ################
kumo_san = ''
################# Don't touch. ################

# ユーザーが占いを使った日を記録する辞書
last_uranai_usage = {}

@client.event
async def on_ready():
    global gemini_chat
    print('Logged in as')
    print('Name: ' + client.user.name)
    print('ID:   ' + str(client.user.id))
    print('--------\n')
    
    # Gemini AI初期化
    try:
        gemini_chat = GeminiChat()
        print('Gemini AI initialized successfully')
    except Exception as e:
        print(f'Failed to initialize Gemini AI: {e}')
        gemini_chat = None
    
    # Cogsをロード
    for cog in ['cogs.points', 'cogs.role_panel', 'cogs.rumble', 'cogs.welcome', 'cogs.weekly_content', 'cogs.help_system', 'cogs.channel_intro', 'cogs.metrics_collector', 'cogs.announcement_detector', 'cogs.rss_monitor']:
        try:
            await client.load_extension(cog)
            print(f'Loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')
    
    # スラッシュコマンドを同期（改善版）
    try:
        # グローバルコマンド同期
        synced = await client.tree.sync()
        print(f'Successfully synced {len(synced)} global slash commands')
        
        # 同期されたコマンド一覧を表示
        for cmd in synced:
            print(f'  - /{cmd.name}: {cmd.description}')
            
        # 特定のギルドでのコマンドを確認
        for guild in client.guilds:
            try:
                guild_commands = await client.tree.fetch_commands(guild=guild)
                print(f'Guild {guild.name}: {len(guild_commands)} commands available')
            except Exception as guild_e:
                print(f'Could not fetch commands for guild {guild.name}: {guild_e}')
                
    except Exception as e:
        print(f'Failed to sync slash commands: {e}')
        print('Attempting manual sync for each guild...')
        
        # フォールバック: 各ギルドで個別同期
        for guild in client.guilds:
            try:
                guild_synced = await client.tree.sync(guild=guild)
                print(f'Synced {len(guild_synced)} commands for guild {guild.name}')
            except Exception as guild_e:
                print(f'Failed to sync for guild {guild.name}: {guild_e}')

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

    # コマンド処理を先に実行
    await client.process_commands(message)

    # 天気予報システム（独立したコマンド）
    if '天気' in message.content and not message.content.startswith('DJアイズ'):
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
        return  # 天気予報処理後は他の処理をスキップ

    # 統一占いシステム: ZERO to ONE星座占い
    fortune_triggers = ['今日の運勢', '運勢教えて', '運勢チェック', '占って', '星に聞いて']
    if any(trigger in message.content for trigger in fortune_triggers) and not message.content.startswith('DJアイズ'):
        if user_id in last_uranai_usage and last_uranai_usage[user_id] == current_date:
            await message.channel.send("🚀 今日はもう占いました！\n✨ 明日のビジネス運もお楽しみに ✨")
        else:
            last_uranai_usage[user_id] = current_date
            user_name = message.author.display_name
            msg = uranai.dj_eyes_fortune(user_name)
            await message.channel.send(msg)
            logging.info(f"ZERO to ONE占い was triggered by {message.author}")
        return  # 占い処理後は他の処理をスキップ

    # スタートアップおみくじシステム
    elif any(trigger in message.content for trigger in ['おみくじ', 'インキュベーター']) and not message.content.startswith('DJアイズ'):
        msg = omikuji.dj_omikuji()
        await message.channel.send(msg)
        logging.info(f"スタートアップおみくじ was triggered by {message.author}")
        return  # おみくじ処理後は他の処理をスキップ

    elif '犯罪係数' in message.content and not message.content.startswith('DJアイズ'):
        msg = dominator.dominator(message.content)
        await message.channel.send(msg)
        logging.info(f"犯罪係数 was triggered by {message.author}: {msg}")
        return  # 犯罪係数処理後は他の処理をスキップ

    # 管理者専用バックモード
    print(f"DEBUG: message.channel.id = {message.channel.id}")
    print(f"DEBUG: BACK_MODE_CHANNEL = {BACK_MODE_CHANNEL}")
    print(f"DEBUG: message.author.id = {message.author.id}")
    print(f"DEBUG: ADMIN_ID = {ADMIN_ID}")
    
    if message.channel == client.get_channel(int(BACK_MODE_CHANNEL)) and str(message.author.id) == ADMIN_ID:
        print("DEBUG: バックモード条件に一致しました")
        try:
            text = message.content
            print(f"DEBUG: 受信メッセージ = '{text}'")
            selector = int(BOT_SALON_CHANNEL)
            print(f"DEBUG: デフォルトselector = {selector}")
            # メッセージ形式: "チャンネル名 送信したいテキスト"
            space_index = text.find(' ')
            if space_index == -1:
                # スペースがない場合は全体をテキストとして扱う
                search_channel = ""
                search_text = text
            else:
                search_channel = text[:space_index]
                search_text = text[space_index + 1:]
            print(f"DEBUG: search_channel = '{search_channel}'")
            print(f"DEBUG: search_text = '{search_text}'")
            if search_channel == 'bot' or search_channel == 'bot_salon':
                selector = int(BOT_SALON_CHANNEL)
            elif search_channel == 'main' or search_channel == 'main_chat':
                selector = int(MAIN_CHAT_CHANNEL)
            elif search_channel == 'storm':
                selector = int(STORM_CHANNEL)
            elif search_channel == 'grave' or search_channel == 'hakaba':
                selector = int(GRAVE_CHANNEL)
            elif search_channel == 'dev':
                selector = int(DEV_CHANNEL)
            elif search_channel == 'pokemon':
                selector = int(POKEMON_CHANNEL)
            else:
                selector = int(BOT_SALON_CHANNEL)
            print(selector)
            msg = kumo_san + search_text
            await client.get_channel(selector).send(msg)
            logging.info(f"Admin command executed: {msg} in channel {selector}")
            return msg
        except Exception as e:
            logging.error(f"Error in admin command: {e}")
            print(e)
            raise e 

    # メンション or DJアイズへの呼びかけ処理
    elif (client.user in message.mentions) or (message.content.startswith("DJアイズ") and not message.content.startswith("DJアイズ ")):
        if client.user != message.author:
            try:
                user_name = message.author.display_name
                user_id = message.author.id
                text = message.content
                print(text)

                # メンションの場合は@を削除
                if client.user in message.mentions:
                    text = text.replace(f'<@{client.user.id}>', '').strip()
                
                # コマンドシステムを優先（ポイント確認、ロールパネル作成など）
                command_keywords = ['ポイント確認', 'デイリーボーナス', 'ランキング', 'ポイント付与', 'ポイント削除', 'ポイント設定', 
                                  'ロールパネル作成']
                if any(keyword in text for keyword in command_keywords):
                    # コマンドシステムに処理を任せるため、何もしない
                    return
                
                # 特定のキーワードは既存機能を使用（トークン節約）
                if text.find('慰めて') > -1 or text.find('なぐさめて') > -1 or text.find('アドバイス') > -1 or text.find('助言') > -1:
                    msg = meigen.meigen()
                elif text.find('グー') > -1 or text.find('チョキ') > -1 or text.find('パー') > -1 or text.find('ぐー') > -1 or text.find('ちょき') > -1 or text.find('ぱー') > -1:
                    msg = keisuke_honda.keisuke_honda(text, user_id)
                elif text.find('なろう') > -1: 
                    msg = narou.narou_search(text)
                elif text.find('犯罪係数') > -1 or text.find('ドミネータ') > -1 or text.find('サイコパス') > -1 or text.find('色相') > -1 or text.find('シビュラ') > -1:
                    msg = kumo_san + dominator.dominator(text)
                elif text.find('modokicraft') > -1:
                    msg = kumo_san + user_name + 'さん ' + modokicraft.send_signal_to_modokicraft(text)
                elif text.find('wp') > -1:
                    msg = kumo_san + waruiko_point.waruiko_point(text, user_id)
                elif text.find('マインスイーパ') > -1 or text.find('まいんすいーぱ') > -1:
                    msg = kumo_san + user_name + 'さん 出題！\n' + minesweeper.minesweeper(text)
                elif text.find('級') > -1 or text.find('遊ぼ') > -1 or text.find('遊んで') > -1 or text.find('あそぼ') > -1 or text.find('あそんで') > -1:
                    msg = kumo_san + user_name + 'さん マインスイーパーしましょう！\n' + minesweeper.minesweeper(text)
                # 星座占いは統一システムに移行済み（重複除去）
                elif text.find('d') > -1:
                    msg = kumo_san + user_name + 'さん のダイス結果です\n' + dice.nDn(text)
                elif text.find('って何') > -1 or text.find('ってなに') > -1:
                    msg = kumo_san + user_name + 'さん ' + wiki.wikipedia_search(text)
                elif text.find('は素数') > -1:
                    msg = kumo_san + user_name + 'さん ' + primarity_test.primarity_test(text, 50)
                elif text.find('おそうじ') > -1 or text.find('お掃除') > -1:
                    history = ""
                    if channel == client.get_channel(int(STORM_CHANNEL)):
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
                        msg = kumo_san + user_name + 'さん 塵一つ残しません！ :cloud_tornado: '
                        logging.info("Cleaning command executed in storm channel")
                    else:
                        msg = kumo_san + user_name + 'さん このコマンドは #暴風域 でしか使えないよ！'
                        logging.info("Cleaning command attempted outside storm channel")
                # メッセージがある場合はGemini AI、空の場合は定型文
                elif text.replace('DJアイズ', '').strip():
                    # Gemini AIで応答
                    if gemini_chat:
                        try:
                            ai_response = gemini_chat.get_response(str(user_id), text.replace('DJアイズ', '').strip())
                            msg = ai_response
                        except:
                            msg = kumo_san + user_name + 'さん その言葉は知らなかったから調べたよ。\n' + wiki.wiki(text)
                    else:
                        msg = kumo_san + user_name + 'さん その言葉は知らなかったから調べたよ。\n' + wiki.wiki(text)
                else:
                    # 空のメンション・呼びかけには定型文で応答
                    msg = 'はい！ご用でしょうか！'
                    logging.info(f"Basic call response triggered by {message.author}")
                
                await channel.send(msg)
                logging.info(f"Responded with: {msg} to {message.author} in channel {message.channel}")
                return msg
            except Exception as e:
                logging.error(f"Error while handling message: {e}")
                print(e)
                raise e

if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)