# -*- coding:utf-8 -*-
import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import pytz
import random
from config.config import ADMIN_ID
from models.database import SessionLocal, ChannelIntroSettings

class ChannelIntroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jst = pytz.timezone('Asia/Tokyo')
    
    async def get_gemini_talks(self) -> list:
        """Geminiから小粋なトークを取得（1個）"""
        talks = []
        try:
            from lib.gemini_chat import GeminiChat
            gemini = GeminiChat()
            
            # ランダムなトピックでトークを生成
            topics = [
                "今日は素敵な一日になりそうですね！コミュニティの皆さんに向けて、前向きな一言をお願いします",
                "ZERO to ONEコミュニティの皆さんへ、今日の活動を応援する短いメッセージをください",
                "新しい一日の始まりに、コミュニティメンバーの心を温かくする言葉をお願いします",
                "今日という日を特別にする、ちょっとした励ましの言葉をください",
                "コミュニティの絆を深める、親しみやすい挨拶をお願いします",
                "今日の活動に向けて、みんなのやる気を引き出す言葉をください",
                "ZERO to ONEの精神で、今日も頑張る皆さんへのエールをお願いします",
                "チャレンジする気持ちを大切に、今日の小さな一歩を応援する言葉をください",
                "コミュニティで新しいつながりを作る喜びについて、短い言葉でお願いします"
            ]
            
            # 1個のトークを生成
            topic = random.choice(topics)
            prompt = f"{topic}。50文字以内で、絵文字も使って親しみやすくお願いします。"
            
            response = gemini.get_response("channel_intro_system", prompt)
            
            # レスポンスを50文字に制限
            if len(response) > 50:
                response = response[:47] + "..."
            
            talks.append(f"✨ {response}")
            
        except Exception as e:
            print(f"Gemini talks error: {e}")
            
        # エラーまたは生成できなかった場合はデフォルトメッセージ（1個のみ）
        if not talks:
            default_messages = [
                "✨ 今日も素敵な一日をお過ごしください！",
                "🌟 新しい発見と出会いが待っていますよ！",
                "🚀 一歩ずつ、確実に前進していきましょう！",
                "💫 今日のあなたの活動を応援しています！",
                "🌈 素晴らしいコミュニティの一員として輝いてください！",
                "🎯 小さな挑戦から大きな成長が生まれます！",
                "💪 今日のあなたは昨日より確実に成長しています！",
                "🌱 新しいアイデアが芽吹く瞬間を楽しんで！"
            ]
            talks = [random.choice(default_messages)]  # 1個のみ
            
        return talks

    def calculate_next_scheduled_time(self, current_time: datetime.datetime, hour: int, minute: int, interval_hours: int) -> datetime.datetime:
        """指定時刻とインターバルから次回送信時刻を計算（日本時間対応）"""
        # 日本時間に変換
        if current_time.tzinfo is None:
            current_time = pytz.utc.localize(current_time)
        jst_time = current_time.astimezone(self.jst)
        
        # 本日の指定時刻（日本時間）
        today_scheduled = jst_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 今日の指定時刻がまだ来ていない場合
        if jst_time < today_scheduled:
            return today_scheduled.astimezone(pytz.utc).replace(tzinfo=None)
        
        # 既に過ぎている場合、インターバル分後の指定時刻を計算
        next_scheduled = today_scheduled
        while next_scheduled <= jst_time:
            next_scheduled += datetime.timedelta(hours=interval_hours)
        
        return next_scheduled.astimezone(pytz.utc).replace(tzinfo=None)

    def generate_channel_description(self, channel: discord.TextChannel) -> str:
        """チャンネルの説明を動的に生成"""
        
        # topicがある場合はそれを使用
        if channel.topic:
            return channel.topic
        
        # チャンネル名から汎用的な説明を生成
        channel_name = channel.name.lower()
        
        if '一般' in channel_name or 'general' in channel_name:
            return "メンバー同士の雑談や、一般的な話題を楽しむチャンネルです。どなたでも気軽に参加できます！"
        elif '雑談' in channel_name or 'chat' in channel_name or 'talk' in channel_name:
            return "自由に雑談を楽しむチャンネルです。日常の出来事や趣味の話など、気軽にお話しましょう！"
        elif '質問' in channel_name or 'question' in channel_name or 'help' in channel_name:
            return "分からないことがあれば気軽に質問してください。メンバー同士で助け合いましょう！"
        elif 'お知らせ' in channel_name or 'news' in channel_name or 'announce' in channel_name:
            return "重要なお知らせや最新情報をお届けするチャンネルです。定期的にチェックしてください！"
        elif 'イベント' in channel_name or 'event' in channel_name:
            return "イベントの告知や参加者募集を行うチャンネルです。楽しいイベントにぜひご参加ください！"
        elif 'ボット' in channel_name or 'bot' in channel_name:
            return "ボットとの交流や機能テストを行うチャンネルです。様々なコマンドを試してみてください！"
        elif 'ビジネス' in channel_name or 'business' in channel_name:
            return "ビジネスに関する情報交換や相談を行うチャンネルです。起業や副業の話題も歓迎です！"
        elif 'プログラミング' in channel_name or 'programming' in channel_name or 'code' in channel_name:
            return "プログラミングに関する質問や技術的な議論を行うチャンネルです。コード共有も歓迎！"
        elif '音楽' in channel_name or 'music' in channel_name:
            return "音楽に関する話題や楽曲紹介を行うチャンネルです。好きなアーティストや楽曲をシェアしましょう！"
        elif 'ゲーム' in channel_name or 'game' in channel_name or 'gaming' in channel_name:
            return "ゲームに関する話題や一緒にプレイする仲間を募集するチャンネルです。楽しくゲームしましょう！"
        elif '作品' in channel_name or 'showcase' in channel_name or 'portfolio' in channel_name:
            return "創作物や作品を共有するチャンネルです。イラスト、写真、音楽など様々な作品をお待ちしています！"
        elif '学習' in channel_name or 'study' in channel_name or 'learning' in channel_name:
            return "学習に関する情報交換や勉強会の告知を行うチャンネルです。一緒に成長しましょう！"
        elif '新人' in channel_name or 'welcome' in channel_name or 'newcomer' in channel_name:
            return "新しく参加されたメンバーを歓迎するチャンネルです。自己紹介や挨拶をお気軽にどうぞ！"
        elif '開発' in channel_name or 'dev' in channel_name or 'development' in channel_name:
            return "開発に関する議論やプロジェクトの相談を行うチャンネルです。技術的な交流を深めましょう！"
        elif 'ニュース' in channel_name or 'news' in channel_name:
            return "最新のニュースや話題の情報を共有するチャンネルです。世の中の動向をチェックしましょう！"
        elif 'はじめに' in channel_name or 'ルール' in channel_name:
            return "コミュニティを楽しく利用するための大切な情報が記載されています。ぜひ一度お読みください！"
        elif 'チャンネル紹介' in channel_name:
            return "各チャンネルの使い方や目的が分かります。迷った時はここをチェック！"
        elif 'ロール取得' in channel_name:
            return "通知ロールを取得して、大切なお知らせを見逃さないようにしましょう！"
        elif '自己紹介' in channel_name:
            return "あなたのことを教えてください！趣味や好きなこと、何でもOKです🎤"
        elif '人生相談' in channel_name or '相談' in channel_name:
            return "悩みや困ったことがあれば、みんなで一緒に考えましょう。気軽に相談してくださいね🫂"
        elif 'やりたい' in channel_name or '目標' in channel_name or '夢' in channel_name:
            return "あなたの夢や目標をシェアして、みんなで応援し合いましょう！🔥"
        elif '活動' in channel_name or '実績' in channel_name:
            return "これまでの活動や成果をまとめています。コミュニティの歩みをチェック！✨"
        elif 'ダミー' in channel_name:
            return "テスト用のチャンネルです。機能確認などに使用されています。"
        else:
            return f"このチャンネルで{channel.name.replace('｜', '').replace('#', '')}について話し合いましょう！"

    async def check_role_panel_in_channel(self, channel: discord.TextChannel) -> tuple[bool, list]:
        """チャンネルにロールパネルメッセージがあるかチェック（高速化版）"""
        role_panels = []
        try:
            # 最新50件のメッセージのみをチェック（高速化）
            async for message in channel.history(limit=50):
                # ロールパネルの特徴を持つメッセージを探す
                if (message.author == self.bot.user and 
                    message.embeds and 
                    any('ロール' in embed.title for embed in message.embeds if embed.title) and
                    message.components):  # ボタンがある
                    
                    # ボタンからロール情報を抽出
                    roles = []
                    for component in message.components:
                        if hasattr(component, 'children'):
                            for child in component.children:
                                if hasattr(child, 'custom_id') and child.custom_id and child.custom_id.startswith('role_'):
                                    try:
                                        role_id = child.custom_id.replace('role_', '')
                                        role = channel.guild.get_role(int(role_id))
                                        if role:
                                            roles.append(role.name)
                                    except:
                                        continue
                    
                    if roles:
                        role_panels.append({
                            'message_id': message.id,
                            'roles': roles,
                            'created_at': message.created_at
                        })
                        break  # 最初のロールパネルが見つかったら終了
            
            return len(role_panels) > 0, role_panels
        except:
            return False, []

    @discord.app_commands.command(name='channel_intro', description='サーバー内全チャンネル紹介を表示')
    @discord.app_commands.describe(
        role='表示対象となるロール（省略時は実行者のロールで判定）',
        format='出力形式（message または markdown）',
        output_channel='出力先チャンネル（省略時は現在のチャンネル）',
        private='プライベート表示するか（省略時は公開表示）',
        exclude_categories='除外カテゴリ名（カンマ区切り、例：管理,プライベート）',
        exclude_channels='除外チャンネル名（カンマ区切り、例：bot-test,admin-only）'
    )
    async def channel_intro(self, interaction: discord.Interaction, 
                           role: discord.Role = None, 
                           format: str = "message",
                           output_channel: discord.TextChannel = None,
                           private: bool = False,
                           exclude_categories: str = None,
                           exclude_channels: str = None):
        """サーバー内全チャンネル紹介を表示"""
        
        # 先にレスポンスを送信してタイムアウトを防ぐ（公開/プライベートに応じて調整）
        if private:
            await interaction.response.defer(ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=False)
        
        # 対象ロールを決定
        target_role = role or interaction.user.top_role
        
        # 除外リストを準備
        excluded_categories = set()
        excluded_channels = set()
        
        if exclude_categories:
            excluded_categories = {cat.strip().lower() for cat in exclude_categories.split(',')}
        
        if exclude_channels:
            excluded_channels = {ch.strip().lower() for ch in exclude_channels.split(',')}
        
        # そのロールが見ることができるチャンネルを取得
        accessible_channels = []
        for channel in interaction.guild.text_channels:
            # 除外チェック
            if channel.name.lower() in excluded_channels:
                continue
            
            if channel.category and channel.category.name.lower() in excluded_categories:
                continue
            
            # Welcomeチャンネルをデフォルト除外
            if 'welcome' in channel.name.lower() or 'ようこそ' in channel.name.lower():
                continue
            
            # チャンネルの表示権限をチェック
            permissions = channel.permissions_for(target_role)
            if not permissions.view_channel:
                continue
            
            # メッセージが1つでもあるかチェック
            try:
                # 最新1件のメッセージを取得してみる
                async for message in channel.history(limit=1):
                    # メッセージが1つでもあれば対象に含める
                    accessible_channels.append(channel)
                    break
            except:
                # エラーの場合はスキップ
                continue
        
        if not accessible_channels:
            await interaction.followup.send("アクセス可能なチャンネルが見つかりませんでした。", ephemeral=True)
            return
        
        # カテゴリ別にグループ化
        categorized_channels = {}
        for channel in accessible_channels:
            category_name = channel.category.name if channel.category else "その他"
            if category_name not in categorized_channels:
                categorized_channels[category_name] = []
            categorized_channels[category_name].append(channel)
        
        # ロールパネルの場所を先に確認
        role_panel_channels = []
        for channel in accessible_channels:
            has_panel, panels = await self.check_role_panel_in_channel(channel)
            if has_panel:
                role_panel_channels.append((channel, panels))
        
        if format.lower() == "markdown":
            # Markdown形式で全チャンネル紹介を生成
            intro_text = f"# 📋 {interaction.guild.name} チャンネル紹介\n\n"
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"## 📂 {category_name}\n\n"
                
                for channel in channels:
                    description = self.generate_channel_description(channel)
                    has_role_panel, role_panels = await self.check_role_panel_in_channel(channel)
                    
                    intro_text += f"### {channel.mention}\n"
                    intro_text += f"{description}\n"
                    
                    if has_role_panel:
                        intro_text += f"🔔 **ここで通知ロールを取得できます**\n"
                    
                    intro_text += "\n"
                
                intro_text += "---\n\n"
            
            # ロールパネルの場所を案内
            if role_panel_channels:
                intro_text += "## 🔔 通知ロール取得について\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"{ch.mention} で通知ロール（{', '.join(set(all_roles))}）を取得できます\n"
                intro_text += "通知ロールを取得すると、重要なお知らせを見逃すことがありません！\n\n"
            
            intro_text += "## 🌟 コミュニティガイド\n"
            intro_text += "• 💬 挨拶から始めて、気軽に会話に参加してください\n" 
            intro_text += "• 📝 各チャンネルのルールを守って楽しく利用しましょう\n"
            intro_text += "• 🔔 特定のメンバーに連絡したい時は @メンション を使いましょう\n"
            intro_text += "• ⚠️ `@everyone` や大勢が該当するメンションは控えめに使いましょう\n"
            intro_text += "• ❓ 分からないことがあれば質問チャンネルで気軽に聞いてください\n\n"
            intro_text += f"**ZERO to ONE** 🚀 みんなで作る素敵なコミュニティ"
            
        else:
            # 通常メッセージ形式で全チャンネル紹介を生成
            intro_text = f"**📋 {interaction.guild.name} チャンネル紹介**\n\n"
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"**📂 {category_name}**\n"
                
                for channel in channels:
                    description = self.generate_channel_description(channel)
                    has_role_panel, role_panels = await self.check_role_panel_in_channel(channel)
                    
                    intro_text += f"• {channel.mention}: {description}"
                    
                    if has_role_panel:
                        intro_text += f" 🔔(通知ロール取得可能)"
                    
                    intro_text += "\n"
                
                intro_text += "\n"
            
            # ロールパネルの場所を案内
            if role_panel_channels:
                intro_text += "**🔔 通知ロール取得について**\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"{ch.mention} で通知ロール（{', '.join(set(all_roles))}）を取得できます\n"
                intro_text += "通知ロールを取得すると、重要なお知らせを見逃すことがありません！\n\n"
            
            intro_text += "**🌟 コミュニティガイド**\n"
            intro_text += "💬 挨拶から始めて、気軽に会話に参加してください\n"
            intro_text += "📝 各チャンネルのルールを守って楽しく利用しましょう\n"
            intro_text += "🔔 特定のメンバーに連絡したい時は @メンション を使いましょう\n"
            intro_text += "⚠️ `@everyone` や大勢が該当するメンションは控えめに使いましょう\n\n"
            intro_text += "**ZERO to ONE** 🚀 みんなで作る素敵なコミュニティ"
        
        # 出力先を決定
        if output_channel:
            # 指定されたチャンネルに送信
            try:
                if len(intro_text) > 2000:
                    # 2000文字ずつに分割
                    chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
                    for chunk in chunks:
                        await output_channel.send(chunk)
                else:
                    await output_channel.send(intro_text)
                
                await interaction.followup.send(f"チャンネル紹介を {output_channel.mention} に送信しました。", ephemeral=True)
                
            except discord.Forbidden:
                await interaction.followup.send(f"エラー: {output_channel.mention} への送信権限がありません。", ephemeral=True)
        
        elif private:
            # 実行者のみに表示
            if len(intro_text) > 2000:
                # 2000文字ずつに分割
                chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
                for chunk in chunks:
                    await interaction.followup.send(chunk, ephemeral=True)
            else:
                await interaction.followup.send(intro_text, ephemeral=True)
        
        else:
            # 現在のチャンネルに公開送信（デフォルト）
            try:
                if len(intro_text) > 2000:
                    # 2000文字ずつに分割
                    chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await interaction.followup.send(chunk, ephemeral=False)
                        else:
                            await interaction.channel.send(chunk)
                else:
                    await interaction.followup.send(intro_text, ephemeral=False)
                
            except discord.Forbidden:
                await interaction.followup.send("エラー: このチャンネルへの送信権限がありません。", ephemeral=True)

    @discord.app_commands.command(name='channel_intro_config', description='チャンネル紹介の定期送信設定')
    @discord.app_commands.describe(
        action='設定アクション',
        channel='送信先チャンネル（デフォルト：実行チャンネル）',
        role='対象ロール（デフォルト：@everyone）',
        enabled='有効/無効',
        hour='送信時刻（時）（デフォルト：現在時刻）',
        minute='送信時刻（分）（デフォルト：現在時刻）',
        interval_days='送信間隔（日数）',
        interval_hours='送信間隔（時間数）（デフォルト：24時間）',
        send_now='初回設定時に即座に送信するか'
    )
    async def channel_intro_config(self, interaction: discord.Interaction, 
                                  action: str,
                                  channel: discord.TextChannel = None,
                                  role: discord.Role = None,
                                  enabled: bool = None,
                                  hour: int = None,
                                  minute: int = None,
                                  interval_days: int = None,
                                  interval_hours: int = None,
                                  send_now: bool = False):
        """チャンネル紹介の定期送信設定"""
        
        print(f"DEBUG: Command called - action={action}, send_now={send_now}, user={interaction.user.id}")
        
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        db = SessionLocal()
        
        try:
            print(f"DEBUG: Processing action: {action}")
            if action.lower() == "show":
                # 現在の設定を表示
                settings = db.query(ChannelIntroSettings).filter(
                    ChannelIntroSettings.guild_id == guild_id
                ).first()
                
                embed = discord.Embed(
                    title="🔧 チャンネル紹介 定期送信設定",
                    description="現在の設定状況",
                    color=discord.Color.blue()
                )
                
                if settings:
                    status = "🟢 有効" if settings.enabled else "🔴 無効"
                    channel_obj = interaction.guild.get_channel(int(settings.channel_id)) if settings.channel_id else None
                    channel_name = channel_obj.mention if channel_obj else "設定なし"
                    
                    embed.add_field(name="📊 状態", value=status, inline=True)
                    embed.add_field(name="📍 送信先", value=channel_name, inline=True)
                    embed.add_field(name="⏱️ 間隔", value=f"{settings.interval_hours}時間", inline=True)
                    
                    # 対象ロールの表示
                    if settings.target_role_id:
                        role_obj = interaction.guild.get_role(int(settings.target_role_id))
                        role_name = role_obj.name if role_obj else "不明なロール"
                    else:
                        role_name = "@everyone"
                    embed.add_field(name="👥 対象ロール", value=role_name, inline=True)
                    
                    # 時刻指定の表示
                    if settings.scheduled_hour is not None and settings.scheduled_minute is not None:
                        embed.add_field(
                            name="🕐 指定時刻", 
                            value=f"{settings.scheduled_hour:02d}:{settings.scheduled_minute:02d}", 
                            inline=True
                        )
                    
                    if settings.last_sent:
                        if settings.scheduled_hour is not None and settings.scheduled_minute is not None:
                            # 指定時刻ベースの次回送信時刻
                            next_send = self.calculate_next_scheduled_time(
                                settings.last_sent, 
                                settings.scheduled_hour, 
                                settings.scheduled_minute, 
                                settings.interval_hours
                            )
                        else:
                            # 通常のインターバルベース
                            next_send = settings.last_sent + datetime.timedelta(hours=settings.interval_hours)
                        
                        # 日本時間で表示
                        next_send_jst = pytz.utc.localize(next_send).astimezone(self.jst)
                        embed.add_field(name="📅 次回送信予定", value=next_send_jst.strftime('%Y/%m/%d %H:%M (JST)'), inline=False)
                else:
                    embed.add_field(name="📊 状態", value="🔴 未設定", inline=False)
                
                embed.add_field(
                    name="⚙️ 設定方法",
                    value="`/channel_intro_config action:set channel:#チャンネル名` で設定",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            elif action.lower() == "set":
                print(f"DEBUG: Starting set action - send_now={send_now}, channel={channel}")
                
                # 設定を更新
                settings = db.query(ChannelIntroSettings).filter(
                    ChannelIntroSettings.guild_id == guild_id
                ).first()
                
                if not settings:
                    print("DEBUG: Creating new settings")
                    settings = ChannelIntroSettings(guild_id=guild_id)
                    db.add(settings)
                else:
                    print("DEBUG: Using existing settings")
                
                print(f"DEBUG: Current settings before update - enabled={getattr(settings, 'enabled', 'NOT_SET')}, channel_id={getattr(settings, 'channel_id', 'NOT_SET')}")
                
                # パラメータの更新
                # チャンネルのデフォルト：コマンド実行チャンネル
                target_channel = channel or interaction.channel
                if target_channel:
                    print(f"DEBUG: Setting channel to {target_channel.name} (ID: {target_channel.id}) - {'specified' if channel else 'default'}")
                    settings.channel_id = str(target_channel.id)
                    settings.enabled = True
                
                # ロールのデフォルト：@everyone
                if role:
                    print(f"DEBUG: Setting target role to {role.name} (ID: {role.id})")
                    settings.target_role_id = str(role.id)
                
                if enabled is not None:
                    print(f"DEBUG: Setting enabled to {enabled}")
                    settings.enabled = enabled
                
                # 時刻のデフォルト：設定時（現在時刻・日本時間）
                if hour is not None or minute is not None:
                    # どちらか片方でも指定されている場合、もう片方にデフォルト値を設定
                    now_jst = datetime.datetime.now(self.jst)
                    hour = hour if hour is not None else now_jst.hour
                    minute = minute if minute is not None else now_jst.minute
                    
                    # 時刻指定の妥当性チェック
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        print(f"DEBUG: Setting scheduled time to {hour:02d}:{minute:02d}")
                        settings.scheduled_hour = hour
                        settings.scheduled_minute = minute
                    else:
                        await interaction.response.send_message("時刻は0-23時、0-59分で指定してください", ephemeral=True)
                        return
                
                # インターバルのデフォルト：1日（24時間）
                if interval_days:
                    print(f"DEBUG: Setting interval from days: {interval_days} days = {interval_days * 24} hours")
                    settings.interval_hours = interval_days * 24  # Convert days to hours
                elif interval_hours:
                    print(f"DEBUG: Setting interval from hours: {interval_hours} hours")
                    settings.interval_hours = interval_hours
                elif not settings.interval_hours:
                    # デフォルト値：24時間（1日）
                    print("DEBUG: Setting default interval: 24 hours")
                    settings.interval_hours = 24
                
                print(f"DEBUG: Before commit - enabled={settings.enabled}, channel_id={settings.channel_id}, send_now={send_now}")
                
                # データベースの変更をコミット
                db.commit()
                
                # 先にDiscordに応答を送信（タイムアウト防止）
                embed = discord.Embed(
                    title="✅ 設定完了",
                    description="定期送信設定を更新しました",
                    color=discord.Color.green()
                )
                
                if settings.enabled and settings.channel_id:
                    ch = interaction.guild.get_channel(int(settings.channel_id))
                    embed.add_field(
                        name="📍 送信先",
                        value=ch.mention if ch else "不明",
                        inline=True
                    )
                    embed.add_field(
                        name="⏱️ 間隔", 
                        value=f"{settings.interval_hours}時間ごと",
                        inline=True
                    )
                    embed.add_field(
                        name="📝 内容",
                        value="通知ロール取得の軽量案内",
                        inline=False
                    )
                    
                    # 時刻指定がある場合の表示
                    if settings.scheduled_hour is not None and settings.scheduled_minute is not None:
                        embed.add_field(
                            name="🕐 指定時刻",
                            value=f"{settings.scheduled_hour:02d}:{settings.scheduled_minute:02d}",
                            inline=True
                        )
                
                # 初回送信処理（応答後に実行）
                initial_send_done = False
                initial_send_error = None
                
                print(f"DEBUG: Checking initial send conditions: send_now={send_now}, enabled={settings.enabled}, channel_id={settings.channel_id}")
                
                if send_now and settings.enabled and settings.channel_id:
                    embed.add_field(
                        name="🚀 初回送信",
                        value="設定完了後にチャンネル紹介を送信します...",
                        inline=False
                    )
                
                # 先に応答を送信
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # その後で初回送信を実行
                if send_now and settings.enabled and settings.channel_id:
                    print("DEBUG: All conditions met, attempting to send initial notification")
                    try:
                        ch = interaction.guild.get_channel(int(settings.channel_id))
                        print(f"DEBUG: Got channel object: {ch}")
                        if ch:
                            print(f"DEBUG: Sending initial notification to {ch.name}")
                            await self.send_periodic_notification(ch)
                            
                            # 送信成功後、last_sentを更新
                            if settings.scheduled_hour is not None and settings.scheduled_minute is not None:
                                now = datetime.datetime.utcnow()
                                # 次回送信時刻を計算（指定時刻ベース）
                                next_scheduled = self.calculate_next_scheduled_time(now, settings.scheduled_hour, settings.scheduled_minute, settings.interval_hours)
                                settings.last_sent = next_scheduled - datetime.timedelta(hours=settings.interval_hours)
                            else:
                                # 通常のインターバルベース
                                settings.last_sent = datetime.datetime.utcnow()
                            
                            # last_sentの更新をコミット
                            db.commit()
                            initial_send_done = True
                            print("Initial notification sent successfully")
                            
                            # フォローアップで成功を通知
                            await interaction.followup.send(
                                "✅ チャンネル紹介を送信しました！", 
                                ephemeral=True
                            )
                        else:
                            initial_send_error = "指定されたチャンネルが見つかりません"
                            await interaction.followup.send(
                                f"⚠️ 初回送信エラー: {initial_send_error}", 
                                ephemeral=True
                            )
                    except Exception as e:
                        initial_send_error = str(e)
                        print(f"Initial send error: {e}")
                        import traceback
                        traceback.print_exc()
                        await interaction.followup.send(
                            f"❌ 初回送信でエラーが発生しました: {str(e)}", 
                            ephemeral=True
                        )
                
            elif action.lower() == "disable":
                # 無効化
                settings = db.query(ChannelIntroSettings).filter(
                    ChannelIntroSettings.guild_id == guild_id
                ).first()
                
                if settings:
                    settings.enabled = False
                    db.commit()
                    
                    await interaction.response.send_message(
                        "🔴 定期送信を無効にしました",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "❌ 設定が見つかりません",
                        ephemeral=True
                    )
            
            else:
                await interaction.response.send_message(
                    "**利用可能なアクション**:\n"
                    "• `show` - 現在の設定を表示\n"
                    "• `set` - 定期送信を設定\n"
                    "• `disable` - 定期送信を無効化\n\n"
                    "**デフォルト値**:\n"
                    "• チャンネル: コマンド実行チャンネル\n"
                    "• ロール: @everyone\n"
                    "• インターバル: 24時間（1日）\n"
                    "• 時刻: hour/minute指定時は現在時刻\n\n"
                    "**使用例**:\n"
                    "`/channel_intro_config action:set` (全てデフォルト)\n"
                    "`/channel_intro_config action:set send_now:True` (即座に送信)\n"
                    "`/channel_intro_config action:set role:@Member send_now:True` (Memberロール用)\n"
                    "`/channel_intro_config action:set channel:#お知らせ role:@VIP interval_hours:12`",
                    ephemeral=True
                )
        
        except Exception as e:
            print(f"ERROR: Exception in channel_intro_config: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"エラーが発生しました: {str(e)}", ephemeral=True)
            except:
                await interaction.followup.send(f"エラーが発生しました: {str(e)}", ephemeral=True)
        
        finally:
            db.close()

    # 定期送信機能
    @tasks.loop(hours=1)  # 1時間ごとにチェック
    async def daily_channel_intro(self):
        """定期的なチャンネル紹介送信（時間単位対応）"""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            
            # 設定ファイルから定期送信設定を読み込み（簡易実装）
            # 実際の運用では、設定管理システムと連携
            
            # 設定されたチャンネルでの定期送信
            db = SessionLocal()
            try:
                settings = db.query(ChannelIntroSettings).filter(
                    ChannelIntroSettings.guild_id == guild_id
                ).first()
                
                if settings and settings.enabled and settings.channel_id:
                    # 設定されたチャンネルを取得
                    channel = guild.get_channel(int(settings.channel_id))
                    if channel:
                        # 最後の送信から指定日数経過していればチャンネル紹介を送信
                        now = datetime.datetime.utcnow()
                        
                        should_send = False
                        
                        if settings.scheduled_hour is not None and settings.scheduled_minute is not None:
                            # 指定時刻ベースの送信判定
                            next_scheduled = self.calculate_next_scheduled_time(
                                settings.last_sent or now, 
                                settings.scheduled_hour, 
                                settings.scheduled_minute, 
                                settings.interval_hours
                            )
                            should_send = now >= next_scheduled
                        else:
                            # 通常のインターバルベース
                            should_send = not settings.last_sent or (now - settings.last_sent).total_seconds() >= settings.interval_hours * 3600
                        
                        if should_send:
                            await self.send_periodic_notification(channel)
                            # 送信日時を更新
                            settings.last_sent = now
                            db.commit()
            finally:
                db.close()

    async def send_periodic_notification(self, channel: discord.TextChannel):
        """軽量な定期通知（ロール取得メインの案内）"""
        try:
            guild = channel.guild
            
            # ロールパネルの場所を確認（テストチャンネル等を除外）
            role_panel_channels = []
            exclude_keywords = [
                'test', 'テスト', 'bot', 'admin', '管理', 'log', 'ログ', 
                'dev', '開発', 'debug', 'デバッグ', 'temp', '一時',
                'welcome', 'ようこそ', 'はじめに', 'ルール', 'rule'
            ]
            
            for ch in guild.text_channels:
                # 除外キーワードチェック
                if any(keyword in ch.name.lower() for keyword in exclude_keywords):
                    continue
                    
                has_panel, panels = await self.check_role_panel_in_channel(ch)
                if has_panel:
                    role_panel_channels.append((ch, panels))
            
            # ロール取得メインの軽量メッセージ
            intro_text = f"**🔔 {guild.name} 通知ロール取得のご案内**\n\n"
            
            if role_panel_channels:
                intro_text += "**📍 通知ロールはこちらで取得できます：**\n"
                for ch, panels in role_panel_channels:
                    all_roles = []
                    for panel in panels:
                        all_roles.extend(panel['roles'])
                    intro_text += f"• {ch.mention} - {', '.join(set(all_roles))}\n"
                
                intro_text += "\n**💡 通知ロールを取得すると：**\n"
                intro_text += "✅ 重要なお知らせを見逃しません\n"
                intro_text += "✅ イベント情報をいち早くキャッチ\n"
                intro_text += "✅ コミュニティの最新情報をお届け\n\n"
            
            # 簡単なチャンネル案内（アクティブなチャンネルのみ）
            intro_text += "**📋 主要チャンネル：**\n"
            
            # 対象ロールを取得（設定から、またはデフォルトで@everyone）
            target_role = guild.default_role  # デフォルト値
            
            # データベースから設定を取得してロールを決定
            try:
                from models.database import SessionLocal, ChannelIntroSettings
                db = SessionLocal()
                settings = db.query(ChannelIntroSettings).filter(
                    ChannelIntroSettings.guild_id == str(guild.id)
                ).first()
                
                if settings and settings.target_role_id:
                    role_obj = guild.get_role(int(settings.target_role_id))
                    if role_obj:
                        target_role = role_obj
                        print(f"DEBUG: Using configured role: {target_role.name}")
                    else:
                        print(f"DEBUG: Configured role not found, using @everyone")
                else:
                    print(f"DEBUG: No role configured, using @everyone")
                db.close()
            except Exception as e:
                print(f"DEBUG: Error getting role config: {e}")
                # エラーの場合はデフォルトのまま
            
            # 主要チャンネルのみを表示
            important_channels = []
            for ch in guild.text_channels:
                # ロールの表示権限をチェック
                permissions = ch.permissions_for(target_role)
                if not permissions.view_channel:
                    continue
                
                # テストチャンネルや管理チャンネル、Welcomeチャンネルを除外
                exclude_keywords = [
                    'test', 'テスト', 'bot', 'admin', '管理', 'log', 'ログ', 
                    'dev', '開発', 'debug', 'デバッグ', 'temp', '一時',
                    'welcome', 'ようこそ', 'はじめに', 'ルール', 'rule'
                ]
                if any(keyword in ch.name.lower() for keyword in exclude_keywords):
                    continue
                
                # メッセージが1つでもあるかチェック（channel_introと同じ仕組み）
                try:
                    async for message in ch.history(limit=1):
                        # メッセージが1つでもあれば対象に含める
                        important_channels.append(ch)
                        break
                except:
                    # エラーの場合はスキップ
                    continue
            
            # カテゴリ別に整理
            categorized_channels = {}
            for ch in important_channels[:8]:  # 最大8チャンネルまで
                category_name = ch.category.name if ch.category else "その他"
                if category_name not in categorized_channels:
                    categorized_channels[category_name] = []
                categorized_channels[category_name].append(ch)
            
            for category_name, channels in categorized_channels.items():
                intro_text += f"**{category_name}**\n"
                for ch in channels:
                    description = self.generate_channel_description(ch)
                    # 説明を短縮
                    if len(description) > 50:
                        description = description[:47] + "..."
                    intro_text += f"• {ch.mention} - {description}\n"
                intro_text += "\n"
            
            # Geminiからの小粋なトークを追加
            gemini_talks = await self.get_gemini_talks()
            intro_text += f"\n{gemini_talks[0]}\n\n"
            intro_text += "**ZERO to ONE** 🚀 コミュニティをお楽しみください！"
            
            # 長すぎる場合は分割送信
            if len(intro_text) > 2000:
                chunks = [intro_text[i:i+2000] for i in range(0, len(intro_text), 2000)]
                for chunk in chunks:
                    await channel.send(chunk)
            else:
                await channel.send(intro_text)
            
        except discord.Forbidden:
            # 送信権限がない場合はスキップ
            pass
        except Exception as e:
            print(f"Error sending periodic intro to {channel.name}: {e}")

    async def cog_load(self):
        """Cogロード時にタスクを開始"""
        if not self.daily_channel_intro.is_running():
            self.daily_channel_intro.start()

    def cog_unload(self):
        """Cogアンロード時にタスクを停止"""
        self.daily_channel_intro.cancel()

async def setup(bot):
    await bot.add_cog(ChannelIntroCog(bot))