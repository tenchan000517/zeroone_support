# -*- coding: utf-8 -*-
"""
AI自動会話システム（シンプル版）
3体のAIキャラクターによる構造化された会話システム
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import time

from models.ai_character import AICharacterManager, AICharacter
from lib.gemini_chat import GeminiChat
from config.config import AI_CHAT_CONFIG

class AIChatSystemSimple(commands.Cog):
    """シンプル化されたAIキャラクター会話システム"""
    
    def __init__(self, bot):
        self.bot = bot
        self.character_manager = AICharacterManager()
        self.gemini_chat = GeminiChat()
        self.last_activity: Dict[int, datetime] = {}
        self.conversation_history: Dict[int, List[Dict]] = {}
        
    def cog_unload(self):
        """Cog終了時の処理"""
        if hasattr(self, 'simplified_chat'):
            self.simplified_chat.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """ボット準備完了時にタスクを開始"""
        if not self.simplified_chat.is_running():
            self.simplified_chat.start()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージイベントリスナー - AIキャラクターへのリプライを検出"""
        # ボット自身のメッセージは無視
        if message.author.bot:
            return
            
        # コマンドメッセージは無視
        if message.content.startswith(self.bot.command_prefix) or message.content.startswith('/'):
            return
            
        # リプライの場合は、まずリプライ先がAIキャラクターかどうかを確認
        is_reply_to_ai = message.reference and message.reference.message_id
        replying_to_ai_character = None
        
        if is_reply_to_ai:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                if replied_message.webhook_id:  # Webhookからのメッセージ
                    # Webhook名からキャラクターを特定
                    webhooks = await replied_message.channel.webhooks()
                    for wh in webhooks:
                        if wh.id == replied_message.webhook_id and wh.name.startswith("AI_Character_"):
                            character_id = wh.name.replace("AI_Character_", "")
                            replying_to_ai_character = self.character_manager.get_character(character_id)
                            break
            except Exception as e:
                logging.error(f"リプライ先確認エラー: {e}")
        
        # AIキャラクターへのリプライなら応答
        if replying_to_ai_character:
            await self._handle_reply_to_character(message, replying_to_ai_character)
            return
        
        # キャラクターバイパス機能：指定チャンネルからの投稿をキャラクターバイパス
        bypass_config = AI_CHAT_CONFIG.get("character_bypass", {})
        logging.info(f"デバッグ: バイパス設定チェック - enabled={bypass_config.get('enabled')}, チャンネル比較={str(message.channel.id)} == {bypass_config.get('source_channel_id')}")
        if (bypass_config.get("enabled", False) and 
            str(message.channel.id) == str(bypass_config.get("source_channel_id", ""))):
            logging.info(f"デバッグ: キャラクターバイパス機能開始")
            await self._handle_character_bypass_message(message)
        
    @tasks.loop(hours=1)  # 1時間ごとにチェック
    async def simplified_chat(self):
        """シンプル化された自発的会話タスク"""
        try:
            if not AI_CHAT_CONFIG["enabled"]:
                return
                
            current_hour = datetime.now().hour
            current_time = datetime.now()
            
            # お昼過ぎ（13時台）のみ実行
            if current_hour != 13:
                return
                
            # 指定されたチャンネルのみで会話
            target_channel_id = int(AI_CHAT_CONFIG["target_channel_id"])
            channel = self.bot.get_channel(target_channel_id)
            
            if not channel or not channel.permissions_for(channel.guild.me).send_messages:
                logging.warning(f"AIチャット対象チャンネル {target_channel_id} が見つからないか、権限がありません")
                return
                
            # 1日1回の制限
            today = current_time.date()
            channel_activity = self.last_activity.get(channel.id)
            
            if (channel_activity and channel_activity.date() == today):
                logging.info(f"チャンネル {channel.id} で本日既に会話済みです。スキップします。")
                return
                
            # シンプル化された会話を開始
            await self._start_structured_conversation(channel)
                        
        except Exception as e:
            logging.error(f"シンプル化された自発的会話エラー: {e}")
    
    @commands.command(name='ai会話', aliases=['ai_chat', 'chat'])
    async def manual_ai_chat(self, ctx):
        """手動でAI会話を開始するコマンド"""
        try:
            await ctx.send("AI会話を開始します...")
            await self._start_structured_conversation(ctx.channel)
            
        except Exception as e:
            logging.error(f"手動AI会話エラー: {e}")
            await ctx.send("AI会話の開始に失敗しました。")
    
    async def _start_structured_conversation(self, channel: discord.TextChannel):
        """構造化された会話を開始"""
        try:
            # 3体構成：ランダム2体 + キング・ダイナカ + 山田メンター
            all_chars = self.character_manager.get_active_characters()
            available_chars = [char for char in all_chars if char.id not in ["ai_king_dynaka", "ai_yamada"]]
            
            if len(available_chars) < 2:
                return
                
            # ランダム2体を選択
            random_chars = random.sample(available_chars, 2)
            person1, person2 = random_chars[0], random_chars[1]
            
            # 固定キャラクター
            king_dynaka = self.character_manager.get_character("ai_king_dynaka")
            yamada_mentor = self.character_manager.get_character("ai_yamada")
            
            if not king_dynaka or not yamada_mentor:
                return
            
            # 身近でランダムな話題を生成
            topic = self._generate_random_topic()
            
            # 10ステップの会話フロー
            conversation_steps = [
                {"speaker": person1, "type": "topic", "message": f"最近{topic}について考えてるんだけど、みんなはどう思う？"},
                {"speaker": person2, "type": "problem", "message": "問題提起"},
                {"speaker": king_dynaka, "type": "tease", "message": "茶化し"},
                {"speaker": person1, "type": "analysis", "message": "考察"},
                {"speaker": person2, "type": "analysis2", "message": "考察2"},
                {"speaker": king_dynaka, "type": "tease2", "message": "茶化し2"},
                {"speaker": yamada_mentor, "type": "solution", "message": "解決策"},
                {"speaker": person1, "type": "response", "message": "返事"},
                {"speaker": person2, "type": "response2", "message": "返事2"},
                {"speaker": king_dynaka, "type": "final_tease", "message": "返事茶化し"}
            ]
            
            # 会話実行
            conversation_context = f"話題: {topic}"
            
            for i, step in enumerate(conversation_steps):
                try:
                    # 各ステップ間に適切な間隔をあける
                    if i > 0:
                        await asyncio.sleep(5)  # 5秒間隔
                    
                    message = await self._generate_step_message(
                        step["speaker"], 
                        step["type"], 
                        topic, 
                        conversation_context,
                        i + 1
                    )
                    
                    if message:
                        # Webhookでキャラクターとして投稿
                        await self._send_character_message(channel, step["speaker"], message)
                        
                        # 会話コンテキストを更新
                        conversation_context += f"\n{step['speaker'].name}: {message}"
                        
                except Exception as e:
                    logging.error(f"会話ステップ {i+1} でエラー: {e}")
                    continue
            
            # 最後の活動時間を更新
            self.last_activity[channel.id] = datetime.now()
            
        except Exception as e:
            logging.error(f"構造化された会話エラー: {e}")
    
    def _generate_random_topic(self) -> str:
        """身近でランダムな話題を生成"""
        topics = [
            "コンビニの新しいスイーツ",
            "朝の通勤ラッシュの混雑",
            "今日の気温の変化",
            "週末の楽しい過ごし方",
            "最近話題のドラマ",
            "最新のヒット曲",
            "美味しいレストラン",
            "便利なスマホアプリ",
            "始めてみたい新しい趣味",
            "効果的な健康法",
            "効率的な時間の使い方",
            "居心地の良いカフェ",
            "面白かった本",
            "おすすめのストレス解消法",
            "季節の楽しみ方",
            "身につけたい良い習慣",
            "友人関係の悩み",
            "快適な家時間",
            "最近気づいたこと",
            "これからの目標"
        ]
        return random.choice(topics)
    
    async def _generate_step_message(self, character: AICharacter, step_type: str, topic: str, context: str, step_number: int) -> str:
        """各ステップのメッセージを生成"""
        try:
            # ステップタイプごとのプロンプト
            step_prompts = {
                "topic": f"「{topic}」について具体的な例を交えて自然に話題を振ってください。商品名や場所など具体的な名前を含めてください。{character.name}らしい独自の視点で発言してください。",
                "problem": f"「{topic}」について具体的な問題や課題を提起してください。{character.name}の専門分野や興味から見た独自の課題を指摘してください。",
                "tease": f"前の発言を受けて、{character.name}らしく軽く茶化してください。筋トレや体力に関連付けて独自の例えで話してください。",
                "analysis": f"「{topic}」について、{character.name}らしい視点で考察してください。他の人とは異なる{character.name}独自の分析をしてください。",
                "analysis2": f"「{topic}」について、{character.name}らしい別の角度から考察してください。前の人とは全く違う{character.name}独自の視点で話してください。",
                "tease2": f"これまでの議論を受けて、{character.name}らしく茶化してください。筋トレ用語を使って独自の例えで楽しく反応してください。",
                "solution": f"「{topic}」について、{character.name}らしい実践的で多角的な解決策を提案してください。メンターとしての経験を活かした独自のアドバイスをしてください。",
                "response": f"山田メンターの解決策を受けて、{character.name}らしく返事してください。{character.name}の専門分野から見た独自の感想や追加の視点を述べてください。",
                "response2": f"これまでの議論を受けて、{character.name}らしく返事してください。前の人とは違う{character.name}独自の感想や今後の抱負を述べてください。",
                "final_tease": f"{character.name}らしく楽しく締めくくってください。筋トレの例えを使って前向きにまとめてください。"
            }
            
            prompt = step_prompts.get(step_type, f"「{topic}」について{character.name}らしく発言してください。")
            
            response = await self.gemini_chat.get_ai_character_response(
                character.name,
                character.personality,
                character.speaking_style,
                prompt,
                context
            )
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"メッセージ生成エラー ({character.name}, {step_type}): {e}")
            return None
    
    async def _send_character_message(self, channel: discord.TextChannel, character: AICharacter, message: str):
        """キャラクターとしてメッセージを送信"""
        try:
            # キャラクター固有のWebhookを使用してリプライ検出を可能にする
            webhooks = await channel.webhooks()
            webhook = None
            webhook_name = f"AI_Character_{character.id}"
            
            for wh in webhooks:
                if wh.name == webhook_name:
                    webhook = wh
                    break
            
            if not webhook:
                webhook = await channel.create_webhook(name=webhook_name)
            
            await webhook.send(
                content=message,
                username=character.display_name,
                avatar_url=character.avatar_url
            )
            
        except Exception as e:
            logging.error(f"キャラクターメッセージ送信エラー ({character.name}): {e}")
            # Webhookが失敗した場合は通常のメッセージとして送信
            await channel.send(f"**{character.display_name}**: {message}")
    
    async def _handle_reply_to_character(self, message: discord.Message, character: AICharacter):
        """AIキャラクターへのリプライを処理"""
        try:
            # リプライされたメッセージの内容を取得
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            original_content = replied_message.content if replied_message else ""
            
            # AI応答を生成
            prompt = f"あなたは{character.name}です。{character.personality}な性格で、{character.speaking_style}話し方をします。" \
                    f"ユーザーが「{original_content}」というあなたのメッセージに対して「{message.content}」と返信しました。" \
                    f"あなたの性格とキャラクターらしく、適切に返答してください。"
            
            response = await self.gemini_chat.generate_response(
                character.name,
                character.personality,
                character.speaking_style,
                prompt,
                []  # リプライの場合は会話履歴は使わない
            )
            
            if response:
                await self._send_character_message(message.channel, character, response.strip())
                logging.info(f"AIキャラクター {character.name} がリプライに応答: {message.author.display_name}")
            
        except Exception as e:
            logging.error(f"リプライ処理エラー ({character.name}): {e}")
    
    async def _handle_character_bypass_message(self, message: discord.Message):
        """キャラクターバイパスメッセージを処理"""
        try:
            bypass_config = AI_CHAT_CONFIG.get("character_bypass", {})
            
            # メッセージを行で分割（1行目：指示、2行目以降：実際のメッセージ）
            lines = message.content.strip().split('\n')
            
            # デフォルト値
            character_id = bypass_config.get("default_character_id", "ai_king_dynaka")
            target_channel_id = bypass_config.get("default_target_channel_id")
            bypass_message = ""  # 初期値は空に
            character_name = ""  # 初期値を設定
            channel_name = ""    # 初期値を設定
            
            # 1行目を指示として解析
            logging.info(f"デバッグ: 全体メッセージ行数 = {len(lines)}")
            logging.info(f"デバッグ: 各行 = {lines}")
            
            if len(lines) >= 1:
                instruction_line = lines[0].strip()
                instruction_parts = instruction_line.split(' ', 1)
                
                logging.info(f"デバッグ: 指示行 = '{instruction_line}'")
                logging.info(f"デバッグ: 指示部分 = {instruction_parts}")
                
                if len(instruction_parts) >= 2:
                    character_name = instruction_parts[0]
                    channel_name = instruction_parts[1]
                    
                    # 2行目以降を実際のメッセージとして使用（1行目は指示なので除外）
                    if len(lines) > 1:
                        bypass_message = '\n'.join(lines[1:]).strip()
                        logging.info(f"デバッグ: 送信予定メッセージ = '{bypass_message}'")
                        logging.info(f"デバッグ: メッセージ長さ = {len(bypass_message)}")
                    else:
                        await message.reply(f"❌ 送信するメッセージが入力されていません。\n使用方法:\n```\nキャラクター名 チャンネル名\n送信したいメッセージ\n```")
                        return
                else:
                    # 指示形式でない場合はデフォルト動作（全体をメッセージとして使用）
                    bypass_message = message.content.strip()
                    logging.info(f"デバッグ: デフォルト動作、全体メッセージ = '{bypass_message}'")
                    # デフォルト設定をそのまま使用（character_id, target_channel_idは既に設定済み）
                
                # キャラクター名が指定されている場合のみ、キャラクター検索を実行
                if character_name:
                    # キャラクター名からIDを取得（完全一致 → 部分一致の順）
                    all_characters = self.character_manager.get_active_characters()
                    for char in all_characters:
                        # 完全一致を優先
                        if char.name.lower() == character_name.lower() or char.display_name.lower() == character_name.lower():
                            character_id = char.id
                            break
                        # 部分一致もチェック
                        elif (character_name.lower() in char.name.lower() or 
                              character_name.lower() in char.display_name.lower() or
                              char.name.lower() in character_name.lower() or
                              char.display_name.lower() in character_name.lower()):
                            character_id = char.id
                            break
                    
                
                # チャンネル名が指定されている場合のみ、チャンネル検索を実行
                if channel_name:
                    # チャンネル名からIDを取得（完全一致 → 部分一致の順）
                    guild = message.guild
                    if guild:
                        for channel in guild.text_channels:
                            # 完全一致を優先
                            if channel.name.lower() == channel_name.lower():
                                target_channel_id = str(channel.id)
                                break
                            # 部分一致もチェック
                            elif (channel_name.lower() in channel.name.lower() or 
                                  channel.name.lower() in channel_name.lower()):
                                target_channel_id = str(channel.id)
                                break
            
            # キャラクターとチャンネルを取得
            character = self.character_manager.get_character(character_id)
            target_channel = self.bot.get_channel(int(target_channel_id)) if target_channel_id else None
            
            logging.info(f"デバッグ: 選択されたキャラクターID = '{character_id}'")
            logging.info(f"デバッグ: キャラクター = {character.name if character else 'None'}")
            logging.info(f"デバッグ: 送信先チャンネルID = '{target_channel_id}'")
            logging.info(f"デバッグ: 送信先チャンネル = {target_channel.name if target_channel else 'None'}")
            
            if not character:
                await message.reply(f"❌ キャラクター '{character_id}' が見つかりません")
                return
            
            if not target_channel:
                await message.reply(f"❌ 送信先チャンネルが見つかりません")
                return
            
            if not bypass_message.strip():
                await message.reply(f"❌ 送信するメッセージが空です")
                return
            
            # メッセージをキャラクターとして送信
            logging.info(f"デバッグ: Webhook送信開始")
            await self._send_character_message(target_channel, character, bypass_message)
            
            # 確認メッセージ
            await message.add_reaction("✅")
            logging.info(f"キャラクターバイパス: {character.name} が {target_channel.name} に送信")
            
        except Exception as e:
            logging.error(f"キャラクターバイパス処理エラー: {e}")
            await message.reply(f"❌ エラーが発生しました: {str(e)}")
    
    @app_commands.command(name="send_as", description="指定したAIキャラクターとしてメッセージを送信")
    @app_commands.describe(
        character="送信するキャラクター名",
        channel="送信先チャンネル名",
        message="送信するメッセージ内容"
    )
    async def send_as_character(
        self, 
        interaction: discord.Interaction,
        character: str,
        channel: str,
        message: str
    ):
        """指定したAIキャラクターとしてメッセージを送信するコマンド"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # キャラクター検索
            all_characters = self.character_manager.get_active_characters()
            character_obj = None
            
            for char in all_characters:
                if (char.name.lower() == character.lower() or 
                    char.display_name.lower() == character.lower() or
                    character.lower() in char.name.lower() or 
                    character.lower() in char.display_name.lower()):
                    character_obj = char
                    break
            
            if not character_obj:
                await interaction.followup.send(
                    f"❌ キャラクター '{character}' が見つかりません。\n"
                    f"利用可能: {', '.join([char.name for char in all_characters])}",
                    ephemeral=True
                )
                return
            
            # チャンネル検索
            guild = interaction.guild
            target_channel = None
            
            for ch in guild.text_channels:
                if (ch.name.lower() == channel.lower() or 
                    channel.lower() in ch.name.lower()):
                    target_channel = ch
                    break
            
            if not target_channel:
                await interaction.followup.send(
                    f"❌ チャンネル '{channel}' が見つかりません",
                    ephemeral=True
                )
                return
            
            # メッセージ送信
            await self._send_character_message(target_channel, character_obj, message)
            
            await interaction.followup.send(
                f"✅ {character_obj.name} として {target_channel.mention} にメッセージを送信しました",
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"send_as_characterコマンドエラー: {e}")
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIChatSystemSimple(bot))