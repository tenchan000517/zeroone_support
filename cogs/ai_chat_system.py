# -*- coding: utf-8 -*-
"""
AIキャラクター会話システム
複数のAIキャラクターが自発的に会話するシステム
"""

import discord
from discord.ext import commands, tasks
import asyncio
import random
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from models.ai_character import AICharacterManager, AICharacter
from lib.gemini_chat import GeminiChat
from config.config import AI_CHAT_CONFIG

class AIChatSystem(commands.Cog):
    """AIキャラクター会話システム"""
    
    def __init__(self, bot):
        self.bot = bot
        self.character_manager = AICharacterManager()
        self.gemini_chat = GeminiChat() if hasattr(GeminiChat, '__init__') else None
        self.active_conversations: Dict[int, List[str]] = {}  # チャンネルID -> 会話中キャラクターID
        self.conversation_history: Dict[int, List[Dict]] = {}  # チャンネルID -> 会話履歴
        self.last_activity: Dict[int, datetime] = {}  # チャンネルID -> 最後の活動時間
        
        # 自発的会話のタスク
        self.spontaneous_chat.start()
        # ユーザーとの会話履歴を管理
        self.user_conversation_context: Dict[int, Dict] = {}  # チャンネルID -> 会話コンテキスト
        
    def cog_unload(self):
        """Cog終了時の処理"""
        self.spontaneous_chat.cancel()
    
    @tasks.loop(hours=1)  # 1時間ごとにチェック
    async def spontaneous_chat(self):
        """自発的会話タスク"""
        try:
            if not AI_CHAT_CONFIG["enabled"]:
                return
                
            current_hour = datetime.now().hour
            current_time = datetime.now()
            
            # 設定された時刻のタイミングでのみ実行
            target_hours = AI_CHAT_CONFIG["spontaneous_chat_times"]
            if current_hour not in target_hours:
                return
                
            # 指定されたチャンネルのみで会話
            target_channel_id = int(AI_CHAT_CONFIG["target_channel_id"])
            channel = self.bot.get_channel(target_channel_id)
            
            if not channel or not channel.permissions_for(channel.guild.me).send_messages:
                logging.warning(f"AIチャット対象チャンネル {target_channel_id} が見つからないか、権限がありません")
                return
                
            # 1日に同じ時間帯での重複を防ぐ
            today = current_time.date()
            channel_activity = self.last_activity.get(channel.id)
            
            # 同じ日の同じ時間帯（±2時間）で既に会話していればスキップ
            if (channel_activity and 
                channel_activity.date() == today and 
                abs(channel_activity.hour - current_hour) <= 2):
                return
                
            # 自発的会話を開始
            await self._start_spontaneous_conversation(channel)
                        
        except Exception as e:
            logging.error(f"自発的会話エラー: {e}")
    
    async def _start_spontaneous_conversation(self, channel: discord.TextChannel):
        """自発的会話を開始"""
        try:
            # ランダムに2-3人のキャラクターを選択
            participants = self.character_manager.get_random_characters(random.randint(2, 3))
            if len(participants) < 2:
                return
                
            # 会話トピックを生成（キャラクターに応じて調整）
            base_topics = [
                "最近の技術トレンドについて",
                "好きな音楽について",
                "おすすめの本について", 
                "今日の天気について",
                "最新のニュースについて",
                "趣味について",
                "最近見た映画について",
                "起業のアイデアについて",
                "マーケティング戦略について",
                "プログラミングの面白さについて"
            ]
            
            # キング・ダイナカが参加している場合は筋トレ関連トピックを追加
            king_dynaka_topics = [
                "筋トレの素晴らしさについて",
                "プロテインの効果について",
                "モチベーション向上の秘訣について",
                "体力づくりの重要性について"
            ]
            
            topics = base_topics
            if any(p.id == "ai_king_dynaka" for p in participants):
                topics.extend(king_dynaka_topics)
                
            topic = random.choice(topics)
            
            # 会話を開始
            await self._conduct_ai_conversation(channel, participants, topic)
            
        except Exception as e:
            logging.error(f"自発的会話開始エラー: {e}")
    
    async def _conduct_ai_conversation(self, channel: discord.TextChannel, participants: List[AICharacter], topic: str):
        """AIキャラクター同士の会話を実行"""
        try:
            conversation_length = random.randint(3, 8)  # 会話の長さ
            
            for i in range(conversation_length):
                # 話者を選択（前回と同じキャラクターは避ける）
                speaker = random.choice(participants)
                
                # 会話内容を生成
                interests_text = "、".join(speaker.interests[:2])  # 興味の上位2つを含める
                
                if i == 0:
                    # 最初の発言
                    prompt = f"あなたは{speaker.name}です。{speaker.personality}な性格で、{speaker.speaking_style}話し方をします。" \
                             f"主な興味は{interests_text}です。" \
                             f"「{topic}」について他のAIキャラクターと会話を始めてください。あなたの個性と話し方を活かして、簡潔に1-2文で発言してください。"
                else:
                    # 継続的な会話
                    recent_messages = self.conversation_history.get(channel.id, [])[-3:]  # 直近3件の会話
                    context = "\n".join([f"{msg['speaker']}: {msg['content']}" for msg in recent_messages])
                    prompt = f"あなたは{speaker.name}です。{speaker.personality}な性格で、{speaker.speaking_style}話し方をします。" \
                             f"主な興味は{interests_text}です。" \
                             f"以下の会話の流れを受けて、あなたの個性を活かして自然に応答してください。簡潔に1-2文で発言してください。\n\n{context}"
                
                # AIから応答を取得（必須）
                response = None
                if self.gemini_chat:
                    try:
                        response = self.gemini_chat.get_response(f"ai_{speaker.id}", prompt)
                        # 応答の長さを制限
                        if len(response) > 200:
                            response = response[:200] + "..."
                    except Exception as e:
                        logging.error(f"Gemini AI応答エラー ({speaker.name}): {e}")
                
                # AIが利用できない場合はスキップ
                if not response:
                    logging.warning(f"AI応答を取得できませんでした ({speaker.name})")
                    continue
                
                # Webhookを使用してキャラクターとして発言
                await self._send_as_character(channel, speaker, response)
                
                # 会話履歴を保存
                if channel.id not in self.conversation_history:
                    self.conversation_history[channel.id] = []
                self.conversation_history[channel.id].append({
                    'speaker': speaker.display_name,
                    'content': response,
                    'timestamp': datetime.now()
                })
                
                # 会話の間隔を設ける
                await asyncio.sleep(random.randint(2, 5))
                
            # 最後の活動時間を更新
            self.last_activity[channel.id] = datetime.now()
            
        except Exception as e:
            logging.error(f"AI会話実行エラー: {e}")
    
    async def _send_as_character(self, channel: discord.TextChannel, character: AICharacter, message: str):
        """キャラクターとしてメッセージを送信"""
        try:
            # Webhookを作成/取得
            webhooks = await channel.webhooks()
            webhook = None
            webhook_name = f"AI_Character_{character.id}"
            
            for wh in webhooks:
                if wh.name == webhook_name:
                    webhook = wh
                    break
            
            if webhook is None:
                webhook = await channel.create_webhook(name=webhook_name)
            
            # キャラクターとして発言
            await webhook.send(
                content=message,
                username=character.display_name,
                avatar_url=character.avatar_url if character.avatar_url else None
            )
            
        except discord.Forbidden:
            # Webhook作成権限がない場合は通常のメッセージで送信
            await channel.send(f"**{character.display_name}**: {message}")
        except Exception as e:
            logging.error(f"キャラクター発言エラー: {e}")
            await channel.send(f"**{character.display_name}**: {message}")
    
    @commands.hybrid_command(name="ai_characters", description="AIキャラクター一覧を表示")
    async def show_characters(self, ctx):
        """AIキャラクター一覧を表示"""
        character_list = self.character_manager.get_character_list()
        embed = discord.Embed(
            title="🤖 AIキャラクター一覧",
            description=character_list,
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ai_chat_start", description="指定されたキャラクターで会話を開始")
    async def start_ai_chat(self, ctx, character_count: int = 2):
        """AIキャラクター会話を手動で開始"""
        if character_count < 2 or character_count > 5:
            await ctx.send("キャラクター数は2-5人の範囲で指定してください。")
            return
            
        participants = self.character_manager.get_random_characters(character_count)
        if len(participants) < 2:
            await ctx.send("利用可能なキャラクターが不足しています。")
            return
            
        await ctx.send(f"🎭 {character_count}人のAIキャラクターが会話を開始します...")
        
        # 会話トピックをランダム選択
        topics = [
            "最近の技術トレンドについて",
            "好きな音楽について", 
            "おすすめの本について",
            "今日の天気について",
            "趣味について"
        ]
        topic = random.choice(topics)
        
        await self._conduct_ai_conversation(ctx.channel, participants, topic)
    
    @commands.hybrid_command(name="ai_join_voice", description="指定されたキャラクターをボイスチャンネルに参加させる")
    async def join_voice_channel(self, ctx, character_count: int = 1):
        """AIキャラクターをボイスチャンネルに参加させる（ミュート状態）"""
        if not ctx.author.voice:
            await ctx.send("ボイスチャンネルに参加してからコマンドを実行してください。")
            return
            
        if character_count < 1 or character_count > 10:
            await ctx.send("キャラクター数は1-10人の範囲で指定してください。")
            return
            
        voice_channel = ctx.author.voice.channel
        
        try:
            # ボイスチャンネルに参加
            voice_client = await voice_channel.connect()
            
            # ミュート状態にする
            await voice_client.guild.change_voice_state(
                channel=voice_channel,
                self_mute=True,
                self_deaf=True
            )
            
            participants = self.character_manager.get_random_characters(character_count)
            char_names = [char.display_name for char in participants]
            
            await ctx.send(f"🎤 {', '.join(char_names)} がボイスチャンネル「{voice_channel.name}」にミュート状態で参加しました！")
            
        except discord.ClientException:
            await ctx.send("既にボイスチャンネルに参加しています。")
        except Exception as e:
            await ctx.send(f"ボイスチャンネル参加エラー: {e}")
    
    @commands.hybrid_command(name="ai_leave_voice", description="ボイスチャンネルから退出")
    async def leave_voice_channel(self, ctx):
        """ボイスチャンネルから退出"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("🎤 ボイスチャンネルから退出しました。")
        else:
            await ctx.send("ボイスチャンネルに参加していません。")
    
    @commands.hybrid_command(name="ai_character_info", description="特定のキャラクター情報を表示")
    async def show_character_info(self, ctx, character_name: str = None):
        """特定のキャラクター情報を表示"""
        if not character_name:
            active_chars = self.character_manager.get_active_characters()
            char_list = ", ".join([char.name for char in active_chars])
            await ctx.send(f"キャラクター名を指定してください。利用可能: {char_list}")
            return
            
        # 名前でキャラクターを検索
        character = None
        for char in self.character_manager.get_active_characters():
            if char.name == character_name or char.display_name.endswith(character_name):
                character = char
                break
        
        if not character:
            await ctx.send(f"キャラクター「{character_name}」が見つかりません。")
            return
            
        embed = discord.Embed(
            title=f"🤖 {character.display_name}",
            description=character.personality,
            color=0x00ff00
        )
        embed.add_field(name="話し方", value=character.speaking_style, inline=False)
        embed.add_field(name="興味", value="、".join(character.interests), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ai_dynaka_power", description="キング・ダイナカのパワーを発動")
    async def dynaka_power(self, ctx):
        """キング・ダイナカ専用コマンド"""
        dynaka = self.character_manager.get_character("ai_king_dynaka")
        if not dynaka:
            await ctx.send("キング・ダイナカが見つかりません...")
            return
            
        power_messages = [
            "💪 筋肉は裏切らないッス！今日も1セット追加ッス！",
            "🔥 プロテインの力でパワーアップッス！みんなも飲むッス！",
            "⚡ モチベーション MAX ッス！諦めたらそこで試合終了ッス！",
            "🏋️ 筋トレは人生の基本ッス！心も体も鍛えるッス！",
            "💯 今日という日は二度と来ないッス！全力で行くッス！"
        ]
        
        message = random.choice(power_messages)
        await self._send_as_character(ctx.channel, dynaka, message)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """ユーザーメッセージへの応答"""
        # ボット自身のメッセージは無視
        if message.author.bot:
            return
            
        # コマンドメッセージは無視
        if message.content.startswith(self.bot.command_prefix) or message.content.startswith('/'):
            return
            
        # AIチャット機能が無効の場合は応答しない
        if not AI_CHAT_CONFIG["enabled"] or not AI_CHAT_CONFIG["user_interaction_enabled"]:
            return
            
        # 指定されたチャンネル以外では応答しない
        target_channel_id = int(AI_CHAT_CONFIG["target_channel_id"])
        if message.channel.id != target_channel_id:
            return
            
        # AIキャラクターがメンションされた、またはリプライされた場合に応答
        is_mentioned = self.bot.user.mentioned_in(message)
        is_reply_to_ai = message.reference and message.reference.message_id
        
        if not (is_mentioned or is_reply_to_ai):
            return
            
        await self._handle_user_interaction(message, is_reply=is_reply_to_ai)
    
    async def _handle_user_interaction(self, message, is_reply=False):
        """ユーザーとのインタラクションを処理"""
        try:
            channel_id = message.channel.id
            user_id = message.author.id
            
            # リプライの場合は、リプライ先のキャラクターを特定
            replying_to_character = None
            if is_reply and message.reference:
                try:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    if replied_message.webhook_id:  # Webhookからのメッセージ
                        # Webhook名からキャラクターを特定
                        webhook = await replied_message.channel.webhooks()
                        for wh in webhook:
                            if wh.id == replied_message.webhook_id:
                                # Webhook名からキャラクターIDを抽出
                                if wh.name.startswith("AI_Character_"):
                                    character_id = wh.name.replace("AI_Character_", "")
                                    replying_to_character = self.character_manager.get_character(character_id)
                                break
                except Exception as e:
                    logging.error(f"リプライ先メッセージの取得エラー: {e}")
            
            # 会話コンテキストを取得/初期化
            if channel_id not in self.user_conversation_context:
                self.user_conversation_context[channel_id] = {
                    'last_interaction': datetime.now(),
                    'response_count': 0,
                    'participants': []
                }
            
            context = self.user_conversation_context[channel_id]
            
            # 最後のインタラクションから時間が経っていれば新しい会話としてリセット
            timeout_minutes = AI_CHAT_CONFIG["conversation_timeout_minutes"]
            if datetime.now() - context['last_interaction'] > timedelta(minutes=timeout_minutes):
                context['response_count'] = 0
                context['participants'] = []
            
            # 応答回数制限（設定から取得）
            # リプライの場合は制限を緩和（直接的な返答なので）
            max_responses = AI_CHAT_CONFIG["max_responses_per_conversation"]
            if not is_reply and context['response_count'] >= max_responses:
                return
            
            # 応答するキャラクターを選択
            if replying_to_character:
                # リプライの場合は該当キャラクターが応答
                responding_character = replying_to_character
                # 参加者リストに追加（まだいない場合）
                if replying_to_character not in context['participants']:
                    context['participants'].append(replying_to_character)
            else:
                # メンションの場合は既存のロジック
                if not context['participants']:
                    # 初回は1-2人のキャラクターを選択
                    context['participants'] = self.character_manager.get_random_characters(random.randint(1, 2))
                
                if not context['participants']:
                    return
                    
                # ランダム選択
                responding_character = random.choice(context['participants'])
            
            # メッセージからメンションを削除
            clean_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            # AIに応答を生成させる（必須）
            interests_text = "、".join(responding_character.interests[:2])
            
            # リプライの場合は元メッセージの内容も含める
            if is_reply and replying_to_character:
                try:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    original_content = replied_message.content
                    prompt = f"あなたは{responding_character.name}です。{responding_character.personality}な性格で、{responding_character.speaking_style}話し方をします。" \
                             f"主な興味は{interests_text}です。" \
                             f"あなたが先ほど「{original_content}」と発言したところ、" \
                             f"ユーザー「{message.author.display_name}」から「{clean_message}」とリプライされました。" \
                             f"あなたの個性を活かして、この内容に対して適切に応答してください。簡潔に1-2文で返答してください。"
                except:
                    # リプライ先が取得できない場合は通常のプロンプト
                    prompt = f"あなたは{responding_character.name}です。{responding_character.personality}な性格で、{responding_character.speaking_style}話し方をします。" \
                             f"主な興味は{interests_text}です。" \
                             f"ユーザー「{message.author.display_name}」から「{clean_message}」とリプライされました。" \
                             f"あなたの個性を活かして自然に応答してください。簡潔に1-2文で返答してください。"
            else:
                # メンションの場合は通常のプロンプト
                prompt = f"あなたは{responding_character.name}です。{responding_character.personality}な性格で、{responding_character.speaking_style}話し方をします。" \
                         f"主な興味は{interests_text}です。" \
                         f"ユーザー「{message.author.display_name}」から「{clean_message}」と言われました。" \
                         f"あなたの個性を活かして自然に応答してください。簡潔に1-2文で返答し、会話を無理に続けようとしないでください。"
            
            response = None
            if self.gemini_chat:
                try:
                    response = self.gemini_chat.get_response(f"user_{user_id}", prompt)
                    # 応答の長さを制限
                    if len(response) > 200:
                        response = response[:200] + "..."
                except Exception as e:
                    logging.error(f"Gemini AI応答エラー ({responding_character.name}): {e}")
            
            # AIが利用できない場合は応答をスキップ
            if not response:
                logging.warning(f"AI応答を取得できませんでした ({responding_character.name})")
                return
            
            # 応答を送信
            await self._send_as_character(message.channel, responding_character, response)
            
            # コンテキストを更新
            context['last_interaction'] = datetime.now()
            # リプライの場合は応答回数をカウントしない（直接的な返答なので）
            if not is_reply:
                context['response_count'] += 1
                
                # 50%の確率で会話を終了（自然な終了）
                if context['response_count'] >= 2 and random.random() < 0.5:
                    context['response_count'] = 99  # 実質的に会話終了
                
        except Exception as e:
            logging.error(f"ユーザーインタラクションエラー: {e}")
    

async def setup(bot):
    await bot.add_cog(AIChatSystem(bot))