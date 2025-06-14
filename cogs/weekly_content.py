# -*- coding:utf-8 -*-
import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import aiohttp
from config.config import ADMIN_ID
from utils.weekly_settings_manager import WeeklySettingsManager
from utils.event_manager import EventManager
from utils.news_manager import NewsManager

class WeeklyContentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_manager = WeeklySettingsManager()
        self.event_manager = EventManager()
        self.news_manager = NewsManager()
        # 送信済み記録（重複防止用）
        self.sent_today = set()
        
    async def cog_load(self):
        """Cogが読み込まれた時に実行"""
        if self.bot.is_ready():
            self.start_scheduler()
    
    def start_scheduler(self):
        """週間スケジューラーを開始"""
        if not self.weekly_scheduler.is_running():
            self.weekly_scheduler.start()
    
    def cog_unload(self):
        """Cogがアンロードされる時にタスクを停止"""
        self.weekly_scheduler.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """ボット起動時にスケジューラーを開始"""
        await asyncio.sleep(5)  # ボット完全起動を待つ
        self.start_scheduler()
        print("Weekly content scheduler started")
    
    # 週間スケジューラー（10分ごとにチェック）
    @tasks.loop(minutes=10)
    async def weekly_scheduler(self):
        """週間コンテンツ配信スケジューラー"""
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        current_date = now.strftime("%Y-%m-%d")
        current_weekday = now.weekday()
        
        # 日付が変わったら送信記録をリセット
        if hasattr(self, 'last_check_date'):
            if self.last_check_date != current_date:
                self.sent_today = set()
        self.last_check_date = current_date
        
        # 各ギルドの設定をチェック
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            
            # すでに送信済みの場合はスキップ
            if guild_id in self.sent_today:
                continue
            
            # 今日のコンテンツ情報を取得
            content_info = self.settings_manager.get_today_content_info(guild_id, current_weekday)
            
            # 無効化されている場合はスキップ
            if not content_info['enabled']:
                continue
            
            # 時刻チェック（設定時刻から10分以内）
            target_hour = content_info['hour']
            target_minute = content_info['minute']
            
            if (now.hour == target_hour and 
                abs(now.minute - target_minute) <= 10):
                
                # コンテンツを送信
                await self.send_daily_content(guild, content_info['content_type'])
                self.sent_today.add(guild_id)
    
    async def send_daily_content(self, guild, content_type):
        """日次コンテンツを送信"""
        settings = self.settings_manager.get_guild_settings(str(guild.id))
        
        try:
            if content_type == "quotes":
                embed = await self.create_quotes_embed()
            elif content_type == "trends":
                embed = await self.create_trends_embed()
            elif content_type == "tips":
                embed = await self.create_tips_embed()
            elif content_type == "tech":
                embed = await self.create_tech_embed()
            elif content_type == "challenge":
                embed = await self.create_challenge_embed()
            elif content_type == "events":
                regions = self.settings_manager.get_regions_list(str(guild.id))
                embed = await self.create_events_embed(regions)
            elif content_type == "mindset":
                embed = await self.create_mindset_embed()
            else:
                return  # 未知のコンテンツタイプ
            
            await self.send_to_guild(guild, settings, embed)
            
        except Exception as e:
            print(f"Error sending daily content to {guild.name}: {e}")
    
    async def create_quotes_embed(self):
        """起業家格言のEmbed作成"""
        quotes = [
            {
                "quote": "イノベーションは、リーダーとフォロワーを区別するものだ。",
                "author": "スティーブ・ジョブズ",
                "context": "Apple創業者"
            },
            {
                "quote": "失敗は選択肢の一つではない。",
                "author": "イーロン・マスク", 
                "context": "Tesla・SpaceX CEO"
            },
            {
                "quote": "最も重要なことは、質問し続けることをやめないことだ。",
                "author": "アルベルト・アインシュタイン",
                "context": "理論物理学者"
            },
            {
                "quote": "顧客が求めているものを与えるのではない。彼らが欲しがるであろうものを与えるのだ。",
                "author": "スティーブ・ジョブズ",
                "context": "Apple創業者"
            },
            {
                "quote": "起業家にとって最も危険なのは、計画通りに進むことだ。",
                "author": "エリック・リース",
                "context": "リーンスタートアップ提唱者"
            }
        ]
        
        quote_data = random.choice(quotes)
        
        embed = discord.Embed(
            title="💎 今日の起業家格言",
            description=f'"{quote_data["quote"]}"',
            color=discord.Color.gold()
        )
        embed.add_field(
            name="📝 発言者",
            value=f"**{quote_data['author']}** ({quote_data['context']})",
            inline=False
        )
        embed.add_field(
            name="🚀 今日のアクション",
            value="この言葉を胸に、今日も新しいことにチャレンジしましょう！",
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 🌟 成長は毎日の積み重ね")
        
        return embed
    
    async def create_trends_embed(self):
        """ビジネストレンドのEmbed作成"""
        trends = [
            {
                "category": "🤖 AI・テクノロジー",
                "trend": "生成AI市場が急拡大中",
                "detail": "ChatGPTをはじめとした生成AIツールが企業の業務効率化を大幅に向上させています。",
                "action": "自社業務でのAI活用可能性を検討してみましょう。"
            },
            {
                "category": "💚 サステナビリティ",
                "trend": "ESG投資の重要性が増加",
                "detail": "環境・社会・ガバナンスを重視した企業への投資が世界的なトレンドとなっています。",
                "action": "自社のサステナビリティ取り組みを見直してみましょう。"
            },
            {
                "category": "🏠 リモートワーク",
                "trend": "ハイブリッドワークが定着",
                "detail": "完全リモートから、オフィスとリモートを組み合わせた働き方にシフトしています。",
                "action": "効率的なハイブリッドワーク環境を整備しましょう。"
            }
        ]
        
        trend_data = random.choice(trends)
        
        embed = discord.Embed(
            title="📊 ビジネストレンド速報",
            color=discord.Color.purple()
        )
        embed.add_field(
            name=f"{trend_data['category']}",
            value=f"**{trend_data['trend']}**",
            inline=False
        )
        embed.add_field(
            name="📰 トレンド詳細",
            value=trend_data['detail'],
            inline=False
        )
        embed.add_field(
            name="💡 アクションポイント",
            value=trend_data['action'],
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 📈 トレンドを先取りして競争優位を築こう")
        
        return embed
    
    async def create_tips_embed(self):
        """スキルアップTipsのEmbed作成"""
        tips = [
            {
                "category": "💻 プログラミング",
                "tip": "毎日30分でもコードを書く習慣をつけよう",
                "detail": "小さなプロジェクトでも継続することで、確実にスキルが身につきます"
            },
            {
                "category": "📈 マーケティング",
                "tip": "顧客の声を直接聞く機会を作ろう",
                "detail": "アンケートやインタビューで、真のニーズを把握できます"
            },
            {
                "category": "🤝 コミュニケーション",
                "tip": "相手の話を最後まで聞く習慣をつけよう",
                "detail": "傾聴スキルは、信頼関係構築の基盤となります"
            }
        ]
        
        tip_data = random.choice(tips)
        
        embed = discord.Embed(
            title="🛠️ 今日のスキルアップTips",
            color=discord.Color.blue()
        )
        embed.add_field(
            name=f"{tip_data['category']}",
            value=f"**{tip_data['tip']}**",
            inline=False
        )
        embed.add_field(
            name="💡 詳細解説",
            value=tip_data['detail'],
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 📈 スキルアップで差をつけよう")
        
        return embed
    
    async def create_tech_embed(self):
        """テック・イノベーションのEmbed作成（リアルタイムニュース）"""
        try:
            # リアルタイムニュース取得を試行
            articles = await self.news_manager.get_tech_news(max_articles=5)
            embed_data = self.news_manager.format_news_for_embed(articles)
            
            embed = discord.Embed(
                title=embed_data["title"],
                description=embed_data["description"],
                color=embed_data["color"]
            )
            
            for field in embed_data["fields"]:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            
            embed.set_footer(text="ZERO to ONE 🚀 テクノロジーで未来を創ろう")
            
        except Exception as e:
            print(f"Error creating tech news embed: {e}")
            # フォールバック用の従来のEmbed
            embed = discord.Embed(
                title="🌐 テック・イノベーション情報",
                description="最新テクノロジー動向をお届けします",
                color=discord.Color.teal()
            )
            embed.add_field(
                name="📰 今日のトピック",
                value="**AI・DX技術の進化が加速**\n生成AI技術の企業導入が急拡大中。業務効率化と新サービス創出の両面で活用が進んでいます。",
                inline=False
            )
            embed.add_field(
                name="💡 ビジネスへの活用",
                value="• 業務自動化による効率化\n• 新しい顧客体験の創出\n• データ活用による意思決定支援",
                inline=False
            )
            embed.set_footer(text="ZERO to ONE 🚀 テクノロジーで未来を創ろう")
        
        return embed
    
    async def create_challenge_embed(self):
        """今日のチャレンジのEmbed作成"""
        challenges = [
            {
                "title": "競合分析チャレンジ",
                "task": "気になる競合他社を1社選んで、強みと弱みを分析してみよう",
                "time": "30分",
                "benefit": "市場理解と戦略立案スキルが向上します"
            },
            {
                "title": "アイデア発想チャレンジ",
                "task": "日常の不便を3つ見つけて、解決アイデアを考えてみよう",
                "time": "20分",
                "benefit": "問題発見力と創造性が磨かれます"
            },
            {
                "title": "ネットワーキングチャレンジ",
                "task": "新しい人と1人、意味のある会話をしてみよう",
                "time": "随時",
                "benefit": "人脈形成とコミュニケーション力が向上します"
            }
        ]
        
        challenge_data = random.choice(challenges)
        
        embed = discord.Embed(
            title="🎯 今日のビジネスチャレンジ",
            color=discord.Color.orange()
        )
        embed.add_field(
            name=f"📋 {challenge_data['title']}",
            value=challenge_data['task'],
            inline=False
        )
        embed.add_field(
            name="⏰ 目安時間",
            value=challenge_data['time'],
            inline=True
        )
        embed.add_field(
            name="💪 期待効果",
            value=challenge_data['benefit'],
            inline=True
        )
        embed.set_footer(text="ZERO to ONE 🎯 毎日の挑戦で成長しよう")
        
        return embed
    
    async def create_events_embed(self, regions):
        """地域イベントのEmbed作成"""
        try:
            events = await self.event_manager.get_career_events(regions, days_ahead=7)
            embed_data = self.event_manager.format_events_for_embed(events, regions)
            
            embed = discord.Embed(
                title=embed_data["title"],
                description=embed_data["description"],
                color=embed_data["color"]
            )
            
            for field in embed_data["fields"]:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            
            embed.set_footer(text="ZERO to ONE 🎪 イベント参加でチャンスを掴もう")
            
        except Exception as e:
            print(f"Error creating events embed: {e}")
            # フォールバック用の簡単なEmbed
            embed = discord.Embed(
                title="🎪 今週の地域イベント情報",
                description=f"**対象地域:** {', '.join(regions)}\n\nイベント情報の取得に失敗しました。",
                color=0x9B59B6
            )
        
        return embed
    
    async def create_mindset_embed(self):
        """成功マインドセットのEmbed作成"""
        mindsets = [
            {
                "title": "成長マインドセット",
                "concept": "失敗は学習の機会である",
                "detail": "困難や失敗を避けるのではなく、それらを成長のチャンスとして捉える姿勢が重要です。",
                "action": "今週の挑戦や失敗から、何を学べるかを振り返ってみましょう。"
            },
            {
                "title": "継続の力",
                "concept": "小さな積み重ねが大きな変化を生む",
                "detail": "毎日の小さな努力が、長期的に見ると驚くほど大きな成果をもたらします。",
                "action": "今日できる小さな一歩を決めて、実行してみましょう。"
            },
            {
                "title": "ポジティブシンキング",
                "concept": "可能性にフォーカスする",
                "detail": "問題や制約に注目するのではなく、解決策や機会に意識を向けることが成功への鍵です。",
                "action": "今抱えている課題を、新しい機会として捉え直してみましょう。"
            }
        ]
        
        mindset_data = random.choice(mindsets)
        
        embed = discord.Embed(
            title="🚀 成功マインドセット",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"💡 {mindset_data['title']}",
            value=f"**{mindset_data['concept']}**",
            inline=False
        )
        embed.add_field(
            name="🧠 解説",
            value=mindset_data['detail'],
            inline=False
        )
        embed.add_field(
            name="✨ 今週のアクション",
            value=mindset_data['action'],
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 🌟 マインドセットが成功を決める")
        
        return embed
    
    async def send_to_guild(self, guild, settings, embed):
        """個別ギルドに送信"""
        try:
            target_channel = self.settings_manager.get_target_channel(guild, settings)
            if target_channel:
                mention_text = self.settings_manager.get_mention_text(guild, settings)
                if mention_text:
                    await target_channel.send(mention_text, embed=embed)
                else:
                    await target_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # 送信権限がない場合はスキップ
        except Exception as e:
            print(f"Error sending to guild {guild.name}: {e}")
    
    # テスト用コマンド
    @discord.app_commands.command(name='weekly_test', description='週間コンテンツのテスト（管理者専用）')
    @discord.app_commands.describe(content_type='テストするコンテンツタイプ')
    async def test_weekly_content(self, interaction: discord.Interaction, content_type: str):
        """週間コンテンツのテスト"""
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        # 先にinteractionに応答してタイムアウトを防ぐ
        await interaction.response.send_message("コンテンツを生成中...", ephemeral=True)
        
        content_type = content_type.lower()
        
        try:
            if content_type in ['quotes', '格言']:
                embed = await self.create_quotes_embed()
            elif content_type in ['trends', 'トレンド']:
                embed = await self.create_trends_embed()
            elif content_type in ['tips', 'スキル']:
                embed = await self.create_tips_embed()
            elif content_type in ['tech', 'テック']:
                embed = await self.create_tech_embed()
            elif content_type in ['challenge', 'チャレンジ']:
                embed = await self.create_challenge_embed()
            elif content_type in ['events', 'イベント']:
                regions = self.settings_manager.get_regions_list(str(interaction.guild.id))
                embed = await self.create_events_embed(regions)
            elif content_type in ['mindset', 'マインド']:
                embed = await self.create_mindset_embed()
            else:
                await interaction.edit_original_response(
                    content="利用可能なタイプ: quotes, trends, tips, tech, challenge, events, mindset"
                )
                return
            
            settings = self.settings_manager.get_guild_settings(str(interaction.guild.id))
            await self.send_to_guild(interaction.guild, settings, embed)
            await interaction.edit_original_response(content=f"{content_type}コンテンツを送信しました")
            
        except Exception as e:
            print(f"Error in weekly_test: {e}")
            await interaction.edit_original_response(content=f"エラーが発生しました: {str(e)}")
    
    # 設定用コマンド
    @discord.app_commands.command(name='weekly_config', description='週間コンテンツ設定')
    @discord.app_commands.describe(
        action='実行するアクション',
        channel='送信先チャンネル',
        mention='メンション対象',
        regions='地域設定（カンマ区切り）',
        weekday='曜日（monday-sunday）',
        content_type='コンテンツタイプ',
        enabled='有効/無効',
        hour='時刻（時）',
        minute='時刻（分）'
    )
    async def weekly_config(self, interaction: discord.Interaction,
                           action: str,
                           channel: discord.TextChannel = None,
                           mention: str = None,
                           regions: str = None,
                           weekday: str = None,
                           content_type: str = None,
                           enabled: bool = None,
                           hour: int = None,
                           minute: int = None):
        """週間コンテンツ設定コマンド"""
        
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        
        if action.lower() == "show":
            # 現在の設定を表示
            settings = self.settings_manager.get_guild_settings(guild_id)
            
            embed = discord.Embed(
                title="🔧 週間コンテンツ設定",
                color=discord.Color.blue()
            )
            
            # チャンネル設定
            if settings.channel_id:
                channel_obj = interaction.guild.get_channel(int(settings.channel_id))
                channel_name = channel_obj.name if channel_obj else "不明なチャンネル"
                embed.add_field(
                    name="📢 送信先チャンネル",
                    value=f"#{channel_name}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📢 送信先チャンネル",
                    value="自動選択",
                    inline=False
                )
            
            # メンション設定
            if settings.mention_target:
                if settings.mention_target == "@everyone":
                    mention_text = "@everyone"
                elif settings.mention_target == "@here":
                    mention_text = "@here"
                else:
                    role = interaction.guild.get_role(int(settings.mention_target))
                    mention_text = f"@{role.name}" if role else "不明なロール"
                embed.add_field(
                    name="📣 メンション",
                    value=mention_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📣 メンション",
                    value="なし",
                    inline=False
                )
            
            # 地域設定
            regions_list = self.settings_manager.get_regions_list(guild_id)
            embed.add_field(
                name="🌍 対象地域",
                value=", ".join(regions_list),
                inline=False
            )
            
            # スケジュール設定
            schedule_info = self.settings_manager.format_schedule_info(settings)
            embed.add_field(
                name="📅 週間スケジュール",
                value=schedule_info,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        elif action.lower() == "channel":
            if not channel:
                await interaction.response.send_message("チャンネルを指定してください", ephemeral=True)
                return
            
            success = self.settings_manager.update_channel_settings(guild_id, channel_id=str(channel.id))
            if success:
                await interaction.response.send_message(f"送信先チャンネルを {channel.mention} に設定しました", ephemeral=True)
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        elif action.lower() == "mention":
            if not mention:
                await interaction.response.send_message("メンション対象を指定してください", ephemeral=True)
                return
            
            mention_target = None
            if mention.lower() in ["everyone", "@everyone"]:
                mention_target = "@everyone"
            elif mention.lower() in ["here", "@here"]:
                mention_target = "@here"
            elif mention.lower() in ["none", "なし"]:
                mention_target = None
            else:
                role = discord.utils.get(interaction.guild.roles, name=mention)
                if role:
                    mention_target = str(role.id)
                else:
                    await interaction.response.send_message("指定されたロールが見つかりません", ephemeral=True)
                    return
            
            success = self.settings_manager.update_channel_settings(guild_id, mention_target=mention_target)
            if success:
                await interaction.response.send_message("メンション設定を更新しました", ephemeral=True)
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        elif action.lower() == "regions":
            if not regions:
                await interaction.response.send_message("地域をカンマ区切りで指定してください（例：愛知県,東京都）", ephemeral=True)
                return
            
            regions_list = [region.strip() for region in regions.split(",")]
            success = self.settings_manager.update_regions(guild_id, regions_list)
            if success:
                await interaction.response.send_message(f"対象地域を {', '.join(regions_list)} に設定しました", ephemeral=True)
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        elif action.lower() == "schedule":
            if not weekday:
                await interaction.response.send_message("曜日を指定してください（monday-sunday）", ephemeral=True)
                return
            
            weekday_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            
            if weekday.lower() not in weekday_map:
                await interaction.response.send_message("曜日は monday-sunday で指定してください", ephemeral=True)
                return
            
            weekday_num = weekday_map[weekday.lower()]
            
            # 時刻の妥当性チェック
            if hour is not None and minute is not None:
                if not self.settings_manager.validate_time(hour, minute):
                    await interaction.response.send_message("時刻は0-23時、0-59分で指定してください", ephemeral=True)
                    return
            
            success = self.settings_manager.update_weekday_schedule(
                guild_id, weekday_num, enabled=enabled, content_type=content_type, hour=hour, minute=minute
            )
            
            if success:
                await interaction.response.send_message(f"{weekday}の設定を更新しました", ephemeral=True)
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        else:
            await interaction.response.send_message(
                "利用可能なアクション: show, channel, mention, regions, schedule",
                ephemeral=True
            )
    
    @discord.app_commands.command(name='help_admin', description='管理者向けヘルプ')
    async def help_admin(self, interaction: discord.Interaction):
        """管理者向けヘルプコマンド"""
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔧 DJアイズ 管理者ガイド",
            description="週間コンテンツ配信システムの設定方法",
            color=discord.Color.blue()
        )
        
        # 基本設定
        embed.add_field(
            name="📌 基本設定",
            value=(
                "`/weekly_config show` - 現在の設定確認\n"
                "`/weekly_config channel #チャンネル名` - 送信先設定\n" 
                "`/weekly_config mention @ロール名` - メンション設定\n"
                "`/weekly_config regions 愛知県,東京都` - 地域設定"
            ),
            inline=False
        )
        
        # スケジュール設定
        embed.add_field(
            name="📅 スケジュール設定",
            value=(
                "`/weekly_config schedule weekday:monday content_type:quotes hour:7 minute:0 enabled:True`\n"
                "**曜日**: monday-sunday\n"
                "**コンテンツ**: quotes, trends, tips, tech, challenge, events, mindset"
            ),
            inline=False
        )
        
        # テスト機能
        embed.add_field(
            name="🧪 テスト配信",
            value=(
                "`/weekly_test quotes` - 起業家格言テスト\n"
                "`/weekly_test events` - イベント情報テスト\n"
                "`/weekly_test tech` - テックニュース（リアルタイム）"
            ),
            inline=False
        )
        
        # デフォルト配信スケジュール
        embed.add_field(
            name="📋 デフォルトスケジュール",
            value=(
                "月: 起業家格言 (7:00)\n"
                "火: ビジネストレンド (7:00)\n"
                "水: スキルアップTips (7:00)\n"
                "木: テック・イノベーション (7:00)\n"
                "金: 今日のチャレンジ (7:00)\n"
                "土: 地域イベント情報 (7:00)\n"
                "日: 成功マインドセット (7:00)"
            ),
            inline=False
        )
        
        embed.set_footer(text="10分毎にチェック・配信時刻から10分以内に送信")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WeeklyContentCog(bot))