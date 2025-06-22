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
            # 全キャラクター参加システム - 全5キャラクターを取得
            participants = self.character_manager.get_active_characters()
            
            # キング・ダイナカが必ず含まれることを確認
            king_dynaka = self.character_manager.get_character("ai_king_dynaka")
            if king_dynaka and king_dynaka not in participants:
                participants.append(king_dynaka)
                
            if len(participants) < 2:
                return
                
            # 直前の会話履歴からトピックを動的生成
            topic = await self._generate_contextual_topic(channel, participants)
            
            # 会話を開始
            await self._conduct_ai_conversation(channel, participants, topic)
            
        except Exception as e:
            logging.error(f"自発的会話開始エラー: {e}")
    
    async def _generate_contextual_topic(self, channel: discord.TextChannel, participants: List[AICharacter]) -> str:
        """直前の会話履歴を分析して関連性のあるトピックを生成"""
        try:
            # チャンネルの直近メッセージを取得（AI会話以外のユーザーメッセージ）
            recent_user_messages = []
            async for message in channel.history(limit=20):
                # ボット以外のメッセージで、コマンドでないものを収集
                if (not message.author.bot and 
                    not message.content.startswith('/') and 
                    not message.content.startswith('!') and
                    len(message.content) > 10):
                    recent_user_messages.append(message.content[:200])  # 最大200文字
                    if len(recent_user_messages) >= 5:
                        break
            
            # デフォルトトピック（フォールバック用）
            default_topics = [
                "最近の技術トレンドについて",
                "好きな音楽について", 
                "おすすめの本について",
                "今日の天気について",
                "趣味について",
                "最近見た映画について",
                "起業のアイデアについて",
                "マーケティング戦略について",
                "プログラミングの面白さについて"
            ]
            
            # キング・ダイナカ専用トピック
            king_dynaka_topics = [
                "筋トレの素晴らしさについて",
                "プロテインの効果について", 
                "モチベーション向上の秘訣について",
                "体力づくりの重要性について"
            ]
            
            # キング・ダイナカが参加している場合はトピックを追加
            if any(p.id == "ai_king_dynaka" for p in participants):
                default_topics.extend(king_dynaka_topics)
            
            # 直近メッセージがある場合はAIで関連トピックを生成
            if recent_user_messages and self.gemini_chat:
                try:
                    context_text = "\n".join(recent_user_messages[:3])  # 最新3件を使用
                    
                    # キャラクターの興味を考慮したプロンプト
                    participant_interests = []
                    for p in participants:
                        participant_interests.extend(p.interests[:2])  # 各キャラの興味トップ2
                    interests_text = "、".join(set(participant_interests))
                    
                    prompt = f"以下の最近の会話内容を参考に、カフェで友達同士が自然に話すような新しい話題を1つ提案してください。\n\n" \
                             f"最近の会話:\n{context_text}\n\n" \
                             f"参加者の興味分野: {interests_text}\n\n" \
                             f"条件:\n" \
                             f"- 直前の会話を蒸し返さず、雰囲気や関連性を意識した新しい話題\n" \
                             f"- 「〜について」の形で15文字以内\n" \
                             f"- カジュアルで友達同士らしい話題\n" \
                             f"- 説明は不要、話題のみ回答"
                    
                    ai_topic = self.gemini_chat.get_response(f"topic_gen_{channel.id}", prompt)
                    
                    # AI生成トピックが適切な場合は使用
                    if ai_topic and len(ai_topic.strip()) > 0 and len(ai_topic.strip()) <= 30:
                        topic = ai_topic.strip()
                        if not topic.endswith("について"):
                            topic += "について"
                        logging.info(f"AI生成トピック使用: {topic}")
                        return topic
                        
                except Exception as e:
                    logging.warning(f"AI トピック生成エラー: {e}")
            
            # AIでの生成に失敗した場合はランダム選択
            selected_topic = random.choice(default_topics)
            logging.info(f"デフォルトトピック使用: {selected_topic}")
            return selected_topic
            
        except Exception as e:
            logging.error(f"トピック生成エラー: {e}")
            return "最近の話題について"  # 最終フォールバック
    
    async def _conduct_ai_conversation(self, channel: discord.TextChannel, participants: List[AICharacter], topic: str):
        """AIキャラクター同士の会話を実行"""
        try:
            max_turns = random.randint(10, 18)  # 10-18回のやり取りでランダム（より長い会話を保証）
            
            for i in range(max_turns):
                # 改善されたキャラクター選択ロジック
                participated_chars = set(
                    msg.get('speaker') for msg in self.conversation_history.get(channel.id, [])
                )
                
                # 未参加キャラクターを優先的に選択
                unparticipated_chars = [p for p in participants if p.display_name not in participated_chars]
                
                if unparticipated_chars and i >= 1:  # 2回目以降で未参加者優先
                    # キング・ダイナカが未参加なら最優先
                    king_dynaka = next((p for p in unparticipated_chars if p.id == "ai_king_dynaka"), None)
                    if king_dynaka:
                        speaker = king_dynaka
                        logging.info(f"キング・ダイナカを優先選択: {i+1}回目")
                    else:
                        speaker = unparticipated_chars[0]  # 他の未参加者を選択
                        logging.info(f"未参加者を優先選択: {speaker.display_name}, {i+1}回目")
                else:
                    # 全員参加済みまたは1回目の場合は順番制
                    speaker = participants[i % len(participants)]
                    logging.info(f"順番制選択: {speaker.display_name}, {i+1}回目")
                
                # 会話内容を生成
                interests_text = "、".join(speaker.interests[:2])  # 興味の上位2つを含める
                
                if i == 0:
                    # 最初の発言：より詳細なコンテキストでキャラクターの個性を強調
                    participants_names = ', '.join([p.name for p in participants])
                    other_participants = [p for p in participants if p.id != speaker.id][:2]
                    other_interests = []
                    for p in other_participants:
                        other_interests.extend(p.interests[:1])
                    other_interests_text = "、".join(other_interests) if other_interests else "様々な話題"
                    
                    prompt = f"【設定】あなたは{speaker.name}です。カフェで{participants_names}の{len(participants)}人でリラックスして会話中。\n" \
                             f"【あなたの性格】{speaker.personality}\n" \
                             f"【話し方の特徴】{speaker.speaking_style}\n" \
                             f"【あなたの興味】{interests_text}\n" \
                             f"【他の参加者の興味】{other_interests_text}\n" \
                             f"【話題】「{topic}」について、あなたの個性と興味を活かして自然に話題を振ってください。\n" \
                             f"【条件】20-50文字で、あなたらしい口調で話しかけてください。質問形式でも意見でもOK。"
                else:
                    # 継続的な会話：より豊富なコンテキストで個性を発揮
                    recent_messages = self.conversation_history.get(channel.id, [])[-3:]  # 直近3件の会話
                    if recent_messages:
                        context_messages = [f"{msg['speaker']}: {msg['content']}" for msg in recent_messages]
                        full_context = "\n".join(context_messages)
                        participants_names = ', '.join([p.name for p in participants])
                        
                        # キング・ダイナカの特別な反応パターン
                        if speaker.id == "ai_king_dynaka":
                            prompt = f"【設定】あなたはキング・ダイナカです。超ポジティブで筋トレ愛好家のキャラクター。\n" \
                                     f"【性格】{speaker.personality}\n" \
                                     f"【話し方】{speaker.speaking_style}\n" \
                                     f"【会話履歴】\n{full_context}\n" \
                                     f"【指示】この会話に筋トレやモチベーション要素を絡めて参加してください。" \
                                     f"「〜ッス！」口調で、前向きでエネルギッシュに応答。30-60文字程度。"
                        else:
                            prompt = f"【設定】あなたは{speaker.name}です。カフェで{participants_names}と会話中。\n" \
                                     f"【性格】{speaker.personality}\n" \
                                     f"【話し方の特徴】{speaker.speaking_style}\n" \
                                     f"【興味分野】{interests_text}\n" \
                                     f"【会話履歴】\n{full_context}\n" \
                                     f"【指示】会話の流れを読んで、あなたの専門性や興味を活かした発言をしてください。" \
                                     f"他の参加者に質問したり、意見を述べたり、自然に会話してください。25-55文字程度。"
                    else:
                        participants_names = ', '.join([p.name for p in participants])
                        prompt = f"【設定】あなたは{speaker.name}です。{participants_names}とカフェで会話中。\n" \
                                 f"【性格】{speaker.personality}\n" \
                                 f"【話し方】{speaker.speaking_style}\n" \
                                 f"【話題】「{topic}」についてあなたらしくコメントしてください。20-50文字程度。"
                
                # AIから応答を取得（必須）
                response = None
                if self.gemini_chat:
                    try:
                        response = self.gemini_chat.get_response(f"ai_{speaker.id}_{i}", prompt)
                        # 応答を短く制限（60文字以内）
                        if len(response) > 60:
                            response = response[:55] + "..."
                    except Exception as e:
                        logging.error(f"Gemini AI応答エラー ({speaker.name}): {e}")
                
                # AIが利用できない場合はスキップ
                if not response or len(response.strip()) < 3:
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
                
                # 改善された会話終了判定（3回目以降）
                if i >= 2:
                    # 明確な終了意図のキーワードのみ検出（終了意図が明確なもののみ）
                    strong_ending_keywords = [
                        "また今度", "じゃあ", "それじゃ", "バイバイ", "お疲れ様", 
                        "お疲れさま", "さよなら", "失礼します", "また明日", "また来週"
                    ]
                    # 終了意図が明確なキーワードのみで判定
                    should_end = any(response.endswith(keyword) or f"{keyword}。" in response or f"{keyword}！" in response 
                                   for keyword in strong_ending_keywords)
                    
                    # 会話の流れを考慮した終了判定
                    conversation_depth = len(self.conversation_history.get(channel.id, []))
                    
                    # 段階的な終了確率（より長い会話を保証）
                    if i == 2:  # 3回目
                        end_probability = 0.05  # 5%（大幅減）
                    elif i == 3:  # 4回目
                        end_probability = 0.10  # 10%
                    elif i == 4:  # 5回目
                        end_probability = 0.15  # 15%
                    elif i == 5:  # 6回目
                        end_probability = 0.25  # 25%
                    elif i == 6:  # 7回目
                        end_probability = 0.35  # 35%
                    elif i >= 7:  # 8回目以降
                        end_probability = 0.50  # 50%
                    else:
                        end_probability = 0.02  # 2%
                    
                    # 全キャラクターの参加状況をチェック
                    participated_characters = set(
                        msg.get('speaker') for msg in self.conversation_history.get(channel.id, [])
                    )
                    total_participants = len(participants)
                    participated_count = len(participated_characters)
                    
                    # 全キャラクターが参加するまでは終了を大幅に抑制
                    if participated_count < total_participants:
                        end_probability *= 0.1  # 90%減
                        logging.info(f"キャラクター参加状況: {participated_count}/{total_participants} - 終了確率抑制")
                    elif participated_count < total_participants and i < 6:
                        end_probability *= 0.3  # 70%減
                    
                    # 終了判定のログ出力を追加
                    random_value = random.random()
                    logging.info(f"終了判定: i={i+1}, should_end={should_end}, probability={end_probability:.2f}, random={random_value:.2f}")
                    
                    if should_end or random_value < end_probability:
                        end_reason = "keyword" if should_end else "probability"
                        logging.info(f"AI会話が終了（{i+1}回, 理由: {end_reason}）")
                        break
                
                # 会話の間隔を設ける（ランダム）
                await asyncio.sleep(random.randint(3, 6))
                
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
    
    @commands.hybrid_command(name="ai_test", description="AIキャラクター機能をテスト")
    async def test_ai_system(self, ctx):
        """AIキャラクター機能の包括的テスト"""
        embed = discord.Embed(
            title="🧪 AIキャラクターシステム テストメニュー",
            description="以下のテストを実行できます",
            color=0x00ff00
        )
        embed.add_field(
            name="📝 基本テスト",
            value="`/ai_test_basic` - キャラクター読み込みとリスト表示\n"
                  "`/ai_test_webhook` - Webhook機能のテスト\n"
                  "`/ai_test_ai` - AI応答機能のテスト",
            inline=False
        )
        embed.add_field(
            name="🎭 会話テスト",
            value="`/ai_test_conversation` - AI同士の会話テスト（コンテキスト考慮）\n"
                  "`/ai_test_user_interaction` - ユーザーとの会話テスト\n"
                  "`/ai_test_reply` - リプライ機能のテスト\n"
                  "`/ai_test_context` - 会話コンテキスト分析",
            inline=False
        )
        embed.add_field(
            name="⚙️ システムテスト",
            value="`/ai_test_config` - 設定値の確認\n"
                  "`/ai_test_all` - 全機能の一括テスト",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ai_test_basic", description="基本機能のテスト")
    async def test_basic(self, ctx):
        """基本機能のテスト"""
        results = []
        
        # キャラクターマネージャーのテスト
        try:
            characters = self.character_manager.get_active_characters()
            results.append(f"✅ キャラクター読み込み: {len(characters)}人")
            
            if characters:
                char_names = [char.display_name for char in characters[:3]]
                results.append(f"📋 利用可能キャラクター: {', '.join(char_names)}...")
            else:
                results.append("❌ キャラクターが見つかりません")
                
        except Exception as e:
            results.append(f"❌ キャラクター読み込みエラー: {e}")
        
        # Gemini Chat の初期化テスト
        if self.gemini_chat:
            results.append("✅ GeminiChat: 初期化済み")
        else:
            results.append("❌ GeminiChat: 初期化失敗")
        
        # 設定値確認
        try:
            enabled = AI_CHAT_CONFIG.get("enabled", False)
            channel_id = AI_CHAT_CONFIG.get("target_channel_id", "未設定")
            results.append(f"⚙️ システム有効: {enabled}")
            results.append(f"🎯 対象チャンネル: {channel_id}")
        except Exception as e:
            results.append(f"❌ 設定読み込みエラー: {e}")
        
        embed = discord.Embed(
            title="🧪 基本機能テスト結果",
            description="\n".join(results),
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ai_test_webhook", description="Webhook機能のテスト")
    async def test_webhook(self, ctx):
        """Webhook機能のテスト"""
        try:
            # テスト用キャラクターを取得
            characters = self.character_manager.get_active_characters()
            if not characters:
                await ctx.send("❌ テスト可能なキャラクターがありません")
                return
                
            test_character = characters[0]
            test_message = f"🧪 Webhookテスト - {test_character.display_name} のテスト発言です"
            
            await ctx.send("🔄 Webhook機能をテスト中...")
            await self._send_as_character(ctx.channel, test_character, test_message)
            
            await ctx.send("✅ Webhookテスト完了！上記のメッセージがキャラクターから送信されました")
            
        except Exception as e:
            await ctx.send(f"❌ Webhookテストエラー: {e}")
    
    @commands.hybrid_command(name="ai_test_ai", description="AI応答機能のテスト")
    async def test_ai_response(self, ctx):
        """AI応答機能のテスト"""
        if not self.gemini_chat:
            await ctx.send("❌ GeminiChatが初期化されていません")
            return
            
        try:
            characters = self.character_manager.get_active_characters()
            if not characters:
                await ctx.send("❌ テスト可能なキャラクターがありません")
                return
                
            test_character = characters[0]
            test_prompt = f"あなたは{test_character.name}です。「テスト中です」と言ってください。"
            
            await ctx.send("🔄 AI応答機能をテスト中...")
            
            response = self.gemini_chat.get_response(f"test_{ctx.author.id}", test_prompt)
            if response:
                await self._send_as_character(ctx.channel, test_character, f"🧪 {response}")
                await ctx.send("✅ AI応答テスト完了！")
            else:
                await ctx.send("❌ AI応答が取得できませんでした")
                
        except Exception as e:
            await ctx.send(f"❌ AI応答テストエラー: {e}")
    
    @commands.hybrid_command(name="ai_test_conversation", description="AI同士の会話テスト")
    async def test_conversation(self, ctx):
        """AI同士の会話テスト"""
        try:
            # 全キャラクター参加システム - 全5キャラクターを取得
            participants = self.character_manager.get_active_characters()
            
            # キング・ダイナカが必ず含まれることを確認
            king_dynaka = self.character_manager.get_character("ai_king_dynaka")
            if king_dynaka and king_dynaka not in participants:
                participants.append(king_dynaka)
                
            if len(participants) < 2:
                await ctx.send("❌ 会話テストに必要なキャラクターが不足しています（2人必要）")
                return
                
            participant_names = [p.display_name for p in participants]
            await ctx.send(f"🧪 AI会話テスト開始: {', '.join(participant_names)}")
            
            # チャンネルの直近メッセージを取得してコンテキストを作成
            recent_messages = []
            async for message in ctx.channel.history(limit=5):
                if not message.author.bot and len(message.content) > 10:
                    recent_messages.append(message.content[:100])
                    break
            
            # コンテキストに基づいたトピック生成（本番ロジックと同じ）
            if recent_messages:
                context_topic = f"最近の話題『{recent_messages[0]}』に関連して"
            else:
                context_topic = "テクノロジーの未来について"
            
            # 🧪 本番の改善されたロジックを直接呼び出し
            await self._conduct_ai_conversation(ctx.channel, participants, context_topic)
            await ctx.send("✅ AI会話テスト完了！")
            
        except Exception as e:
            await ctx.send(f"❌ AI会話テストエラー: {e}")
    
    @commands.hybrid_command(name="ai_test_user_interaction", description="ユーザー会話機能のテスト")
    async def test_user_interaction(self, ctx):
        """ユーザー会話機能のテスト"""
        try:
            characters = self.character_manager.get_active_characters()
            if not characters:
                await ctx.send("❌ テスト可能なキャラクターがありません")
                return
                
            test_character = random.choice(characters)
            
            # テスト用のメッセージを作成
            test_message = "こんにちは！調子はどうですか？"
            
            await ctx.send(f"🧪 ユーザー会話テスト: {test_character.display_name} との会話をシミュレート")
            await ctx.send(f"💬 テスト入力: 「{test_message}」")
            
            # AI応答を生成
            if self.gemini_chat:
                interests_text = "、".join(test_character.interests[:2])
                prompt = f"あなたは{test_character.name}です。{test_character.personality}な性格で、{test_character.speaking_style}話し方をします。" \
                         f"主な興味は{interests_text}です。" \
                         f"ユーザーから「{test_message}」と言われました。あなたの個性を活かして応答してください。"
                
                response = self.gemini_chat.get_response(f"test_user_{ctx.author.id}", prompt)
                if response:
                    await self._send_as_character(ctx.channel, test_character, f"🧪 {response}")
                    await ctx.send("✅ ユーザー会話テスト完了！")
                else:
                    await ctx.send("❌ AI応答が取得できませんでした")
            else:
                await ctx.send("❌ GeminiChatが利用できません")
                
        except Exception as e:
            await ctx.send(f"❌ ユーザー会話テストエラー: {e}")
    
    @commands.hybrid_command(name="ai_test_config", description="設定値の確認")
    async def test_config(self, ctx):
        """設定値の確認"""
        try:
            embed = discord.Embed(
                title="⚙️ AI Chat システム設定",
                color=0x00ff00
            )
            
            embed.add_field(
                name="基本設定",
                value=f"システム有効: {AI_CHAT_CONFIG.get('enabled', False)}\n"
                      f"ユーザー応答有効: {AI_CHAT_CONFIG.get('user_interaction_enabled', False)}\n"
                      f"対象チャンネル: {AI_CHAT_CONFIG.get('target_channel_id', '未設定')}",
                inline=False
            )
            
            embed.add_field(
                name="会話設定",
                value=f"最大応答回数: {AI_CHAT_CONFIG.get('max_responses_per_conversation', 3)}\n"
                      f"会話タイムアウト: {AI_CHAT_CONFIG.get('conversation_timeout_minutes', 30)}分\n"
                      f"自発的会話時刻: {AI_CHAT_CONFIG.get('spontaneous_chat_times', [])}",
                inline=False
            )
            
            # 現在の状態
            active_conversations = len(self.active_conversations)
            conversation_history_count = sum(len(history) for history in self.conversation_history.values())
            
            embed.add_field(
                name="現在の状態",
                value=f"アクティブ会話: {active_conversations}\n"
                      f"会話履歴総数: {conversation_history_count}\n"
                      f"キャラクター数: {len(self.character_manager.get_active_characters())}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 設定確認エラー: {e}")
    
    @commands.hybrid_command(name="ai_test_all", description="全機能の一括テスト")
    async def test_all(self, ctx):
        """全機能の一括テスト"""
        await ctx.send("🧪 全機能テストを開始します...")
        
        # 基本機能テスト
        await ctx.send("1️⃣ 基本機能テスト中...")
        try:
            characters = self.character_manager.get_active_characters()
            gemini_status = "✅" if self.gemini_chat else "❌"
            await ctx.send(f"基本機能: キャラクター{len(characters)}人, Gemini{gemini_status}")
        except Exception as e:
            await ctx.send(f"❌ 基本機能テストエラー: {e}")
        
        # Webhookテスト
        await ctx.send("2️⃣ Webhookテスト中...")
        try:
            if characters:
                test_char = characters[0]
                await self._send_as_character(ctx.channel, test_char, "🧪 一括テスト - Webhook確認")
                await ctx.send("✅ Webhook機能正常")
        except Exception as e:
            await ctx.send(f"❌ Webhookテストエラー: {e}")
        
        # AI応答テスト
        await ctx.send("3️⃣ AI応答テスト中...")
        try:
            if self.gemini_chat and characters:
                test_char = characters[0]
                response = self.gemini_chat.get_response(f"test_all_{ctx.author.id}", 
                    f"あなたは{test_char.name}です。「一括テスト完了」と言ってください。")
                if response:
                    await self._send_as_character(ctx.channel, test_char, f"🧪 {response}")
                    await ctx.send("✅ AI応答機能正常")
                else:
                    await ctx.send("❌ AI応答取得失敗")
        except Exception as e:
            await ctx.send(f"❌ AI応答テストエラー: {e}")
        
        await ctx.send("🎉 全機能テスト完了！個別の詳細テストは各コマンドで実行してください。")
    
    @commands.hybrid_command(name="ai_test_reply", description="リプライ機能のテスト")
    async def test_reply(self, ctx):
        """リプライ機能のテスト"""
        try:
            characters = self.character_manager.get_active_characters()
            if not characters:
                await ctx.send("❌ テスト可能なキャラクターがありません")
                return
                
            test_character = random.choice(characters)
            
            # まずキャラクターに発言させる
            original_message = "🧪 これはリプライテスト用の発言です。何か質問してみてください！"
            await self._send_as_character(ctx.channel, test_character, original_message)
            
            await ctx.send(f"📝 {test_character.display_name} が発言しました。\n"
                          f"💡 **リプライテスト方法:**\n"
                          f"1. 上の {test_character.display_name} のメッセージを右クリック\n"
                          f"2. 「返信」を選択\n"
                          f"3. 何かメッセージを送信\n"
                          f"4. {test_character.display_name} が応答するかテスト")
            
        except Exception as e:
            await ctx.send(f"❌ リプライテストエラー: {e}")
    
    @commands.hybrid_command(name="ai_test_context", description="会話コンテキストのテスト")
    async def test_context(self, ctx):
        """会話コンテキストのテスト"""
        try:
            # チャンネルの直近メッセージを分析
            recent_messages = []
            message_count = 0
            
            await ctx.send("🔍 チャンネルの直近メッセージを分析中...")
            
            async for message in ctx.channel.history(limit=20):
                if not message.author.bot and len(message.content) > 5:
                    recent_messages.append({
                        'author': message.author.display_name,
                        'content': message.content[:150],
                        'timestamp': message.created_at.strftime('%H:%M')
                    })
                    message_count += 1
                    if message_count >= 5:
                        break
            
            embed = discord.Embed(
                title="📊 会話コンテキスト分析結果",
                color=0x00ff00
            )
            
            if recent_messages:
                context_text = "\n".join([
                    f"[{msg['timestamp']}] {msg['author']}: {msg['content'][:100]}..."
                    for msg in recent_messages[:3]
                ])
                embed.add_field(
                    name="直近の会話",
                    value=f"```\n{context_text}\n```",
                    inline=False
                )
                
                # AIによる会話トピック分析
                if self.gemini_chat:
                    analysis_prompt = f"以下の会話から主要なトピックを1つ特定し、簡潔に要約してください：\n{context_text}"
                    topic_analysis = self.gemini_chat.get_response(f"analysis_{ctx.author.id}", analysis_prompt)
                    if topic_analysis:
                        embed.add_field(
                            name="🤖 AI分析結果",
                            value=topic_analysis[:200],
                            inline=False
                        )
            else:
                embed.add_field(
                    name="状況",
                    value="分析可能な直近メッセージが見つかりませんでした",
                    inline=False
                )
            
            # 現在のチャンネルでの会話履歴状況
            if ctx.channel.id in self.conversation_history:
                history_count = len(self.conversation_history[ctx.channel.id])
                embed.add_field(
                    name="AI会話履歴",
                    value=f"このチャンネルでのAI会話: {history_count}件",
                    inline=True
                )
            
            if ctx.channel.id in self.user_conversation_context:
                user_context = self.user_conversation_context[ctx.channel.id]
                embed.add_field(
                    name="ユーザー会話状況",
                    value=f"応答回数: {user_context.get('response_count', 0)}\n"
                          f"参加キャラクター: {len(user_context.get('participants', []))}人",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ コンテキストテストエラー: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """ユーザーメッセージへの応答"""
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
        
        # AIキャラクターへのリプライなら、設定に関係なく応答
        if replying_to_ai_character:
            await self._handle_user_interaction(message, is_reply=True)
            return
            
        # 通常のメンション処理（設定チャンネルのみ）
        if not AI_CHAT_CONFIG["enabled"] or not AI_CHAT_CONFIG["user_interaction_enabled"]:
            return
            
        target_channel_id = int(AI_CHAT_CONFIG["target_channel_id"])
        if message.channel.id != target_channel_id:
            return
            
        # メンションされた場合に応答
        is_mentioned = self.bot.user.mentioned_in(message)
        if not is_mentioned:
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