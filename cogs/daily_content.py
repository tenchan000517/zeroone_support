# -*- coding:utf-8 -*-
import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
from config.config import ADMIN_ID
from utils.daily_settings_manager import DailySettingsManager

class DailyContentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_manager = DailySettingsManager()
        # 送信済み記録（重複防止用）
        self.sent_today = {
            "quotes": set(),
            "tips": set(), 
            "challenge": set(),
            "trends": set()
        }
        
    async def cog_load(self):
        """Cogが読み込まれた時に実行"""
        if self.bot.is_ready():
            self.start_scheduler()
    
    def start_scheduler(self):
        """統一スケジューラーを開始"""
        if not self.daily_scheduler.is_running():
            self.daily_scheduler.start()
    
    def cog_unload(self):
        """Cogがアンロードされる時にタスクを停止"""
        self.daily_scheduler.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """ボット起動時にスケジューラーを開始"""
        await asyncio.sleep(5)  # ボット完全起動を待つ
        self.start_scheduler()
        print("Daily content scheduler started")
    
    # 統一スケジューラー（10分ごとにチェック）
    @tasks.loop(minutes=10)
    async def daily_scheduler(self):
        """全コンテンツタイプを統合管理するスケジューラー"""
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        current_time = f"{now.hour:02d}:{now.minute:02d}"
        current_date = now.strftime("%Y-%m-%d")
        current_weekday = now.weekday()
        
        # 日付が変わったら送信記録をリセット
        if hasattr(self, 'last_check_date'):
            if self.last_check_date != current_date:
                self.sent_today = {
                    "quotes": set(),
                    "tips": set(),
                    "challenge": set(),
                    "trends": set()
                }
        self.last_check_date = current_date
        
        # 各ギルドの設定をチェック
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            settings = self.settings_manager.get_guild_settings(guild_id)
            
            # 起業家格言チェック
            if (settings.quotes_enabled and 
                now.hour == settings.quotes_hour and 
                now.minute == settings.quotes_minute and
                guild_id not in self.sent_today["quotes"]):
                await self.send_quotes_content(guild, settings)
                self.sent_today["quotes"].add(guild_id)
            
            # スキルアップTipsチェック
            if (settings.tips_enabled and
                now.hour == settings.tips_hour and
                now.minute == settings.tips_minute and
                guild_id not in self.sent_today["tips"]):
                await self.send_tips_content(guild, settings)
                self.sent_today["tips"].add(guild_id)
            
            # 今日のチャレンジチェック
            if (settings.challenge_enabled and
                now.hour == settings.challenge_hour and
                now.minute == settings.challenge_minute and
                guild_id not in self.sent_today["challenge"]):
                await self.send_challenge_content(guild, settings)
                self.sent_today["challenge"].add(guild_id)
            
            # ビジネストレンドチェック
            if (settings.trends_enabled and
                now.hour == settings.trends_hour and
                now.minute == settings.trends_minute and
                guild_id not in self.sent_today["trends"]):
                # 曜日チェック
                trend_days = [int(d.strip()) for d in settings.trends_days.split(',')]
                if current_weekday in trend_days:
                    await self.send_trends_content(guild, settings)
                    self.sent_today["trends"].add(guild_id)
    
    async def send_quotes_content(self, guild, settings):
        """起業家格言コンテンツを送信"""
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
            },
            {
                "quote": "大きな危険を冒さなければ、何も得られない。",
                "author": "ジェフ・ベゾス",
                "context": "Amazon創業者"
            },
            {
                "quote": "今日できることを明日に延ばすな。",
                "author": "ベンジャミン・フランクリン",
                "context": "政治家・発明家"
            },
            {
                "quote": "成功の秘訣は、始めることだ。",
                "author": "マーク・トウェイン",
                "context": "作家"
            },
            {
                "quote": "完璧を目指すよりまず終わらせろ。",
                "author": "シェリル・サンドバーグ",
                "context": "Meta COO"
            },
            {
                "quote": "アイデアは実行されなければ何の価値もない。",
                "author": "スコット・ベルスキー",
                "context": "Adobe Chief Product Officer"
            },
            {
                "quote": "夢を見ることができれば、それは実現できる。",
                "author": "ウォルト・ディズニー",
                "context": "ディズニー創業者"
            },
            {
                "quote": "他人の意見に振り回されてはいけない。自分の内なる声を聞け。",
                "author": "スティーブ・ジョブズ",
                "context": "Apple創業者"
            },
            {
                "quote": "今日という日は、残りの人生の最初の日だ。",
                "author": "アビー・ホフマン",
                "context": "社会活動家"
            },
            {
                "quote": "失敗することを恐れるな。恐れるべきは高い目標を持たないことだ。",
                "author": "マイケル・ジョーダン",
                "context": "バスケットボール選手・起業家"
            },
            {
                "quote": "ビジネスで成功する方法は、顧客に価値を提供することだ。",
                "author": "ビル・ゲイツ",
                "context": "Microsoft創業者"
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
        
        await self.send_to_guild(guild, settings, embed)
    
    async def send_tips_content(self, guild, settings):
        """スキルアップTipsコンテンツを送信"""
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
                "category": "💰 財務管理",
                "tip": "毎月の収支を必ず記録しよう",
                "detail": "お金の流れを把握することが、ビジネス成功の第一歩です"
            },
            {
                "category": "🤝 コミュニケーション",
                "tip": "相手の話を最後まで聞く習慣をつけよう",
                "detail": "傾聴スキルは、信頼関係構築の基盤となります"
            },
            {
                "category": "🎯 プロジェクト管理",
                "tip": "タスクを小さく分割して進捗を可視化しよう",
                "detail": "大きな目標も、小さなステップに分ければ達成しやすくなります"
            },
            {
                "category": "📊 データ分析",
                "tip": "数字を見る習慣をつけて、客観的判断力を鍛えよう",
                "detail": "感覚ではなく、データに基づいた意思決定が重要です"
            },
            {
                "category": "🚀 営業スキル",
                "tip": "相手のメリットを最初に話そう",
                "detail": "自分の売りたいものではなく、相手が得られる価値を伝えましょう"
            },
            {
                "category": "💡 アイデア発想",
                "tip": "毎日5分でもブレインストーミングの時間を作ろう",
                "detail": "意図的にアイデアを出す時間を作ることで、創造力が鍛えられます"
            },
            {
                "category": "⏰ 時間管理",
                "tip": "重要かつ緊急でないタスクに時間を割こう",
                "detail": "緊急事態に追われず、計画的に行動できるようになります"
            },
            {
                "category": "🌐 ネットワーキング",
                "tip": "与えることから始めよう",
                "detail": "相手に価値を提供することで、自然と良い関係が築けます"
            },
            {
                "category": "📚 学習方法",
                "tip": "学んだことを誰かに説明してみよう",
                "detail": "アウトプットすることで、理解度が格段に向上します"
            },
            {
                "category": "🎨 デザイン思考",
                "tip": "ユーザーの立場に立って考える習慣をつけよう",
                "detail": "自分目線ではなく、使う人の視点で物事を考えましょう"
            },
            {
                "category": "💻 デジタルスキル",
                "tip": "新しいツールを月に1つは試してみよう",
                "detail": "効率化ツールを知ることで、生産性が大幅に向上します"
            },
            {
                "category": "🧠 論理的思考",
                "tip": "「なぜ？」を5回繰り返す習慣をつけよう",
                "detail": "根本原因を見つけることで、本質的な解決策が見えてきます"
            },
            {
                "category": "🎯 目標設定",
                "tip": "SMARTな目標設定を心がけよう",
                "detail": "具体的、測定可能、達成可能、関連性、期限を明確にしましょう"
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
        embed.add_field(
            name="✨ 実践チャレンジ",
            value="今日から早速試してみましょう！小さな変化が大きな成長につながります。",
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 📈 スキルアップで差をつけよう")
        
        await self.send_to_guild(guild, settings, embed)
    
    async def send_challenge_content(self, guild, settings):
        """今日のチャレンジコンテンツを送信"""
        challenges = [
            {
                "title": "競合分析チャレンジ",
                "task": "気になる競合他社を1社選んで、強みと弱みを分析してみよう",
                "time": "30分",
                "benefit": "市場理解と戦略立案スキルが向上します"
            },
            {
                "title": "ユーザーインタビューチャレンジ",
                "task": "身近な人に「困っていること」を1つ聞いてみよう",
                "time": "15分",
                "benefit": "ニーズ発見とコミュニケーション力が鍛えられます"
            },
            {
                "title": "アイデア発想チャレンジ",
                "task": "日常の不便を3つ見つけて、解決アイデアを考えてみよう",
                "time": "20分",
                "benefit": "問題発見力と創造性が磨かれます"
            },
            {
                "title": "コスト削減チャレンジ",
                "task": "今月の支出を見直して、削減できる項目を見つけよう",
                "time": "25分",
                "benefit": "財務管理スキルと効率性が身につきます"
            },
            {
                "title": "ネットワーキングチャレンジ",
                "task": "新しい人と1人、意味のある会話をしてみよう",
                "time": "随時",
                "benefit": "人脈形成とコミュニケーション力が向上します"
            },
            {
                "title": "学習チャレンジ",
                "task": "興味のある分野の記事を1本読んで要約してみよう",
                "time": "30分",
                "benefit": "知識吸収力と要約スキルが向上します"
            },
            {
                "title": "効率化チャレンジ",
                "task": "今日の作業で時間がかかったことを1つ、改善案を考えよう",
                "time": "15分",
                "benefit": "生産性向上と改善思考が身につきます"
            },
            {
                "title": "マーケット調査チャレンジ",
                "task": "気になる商品の価格を3店舗で比較してみよう",
                "time": "20分",
                "benefit": "市場感覚と分析力が養われます"
            },
            {
                "title": "プレゼンチャレンジ",
                "task": "好きなものを1分で誰かに説明してみよう",
                "time": "10分",
                "benefit": "プレゼンテーション力と要約力が向上します"
            },
            {
                "title": "データ分析チャレンジ",
                "task": "今週の活動を数値で振り返ってみよう",
                "time": "20分",
                "benefit": "数値分析力と客観視スキルが身につきます"
            },
            {
                "title": "ブランディングチャレンジ",
                "task": "自分の強みを3つ、短い言葉で表現してみよう",
                "time": "15分",
                "benefit": "自己分析力とブランディング思考が向上します"
            },
            {
                "title": "顧客視点チャレンジ",
                "task": "よく使うサービスの改善点を1つ考えてみよう",
                "time": "15分",
                "benefit": "ユーザー視点と改善思考が身につきます"
            },
            {
                "title": "計画立案チャレンジ",
                "task": "来週の目標を3つ設定して、行動計画を立てよう",
                "time": "25分",
                "benefit": "計画性と目標設定スキルが向上します"
            },
            {
                "title": "リスク分析チャレンジ",
                "task": "新しく始めたいことのリスクを3つ考えて対策を立てよう",
                "time": "20分",
                "benefit": "リスク管理と戦略思考が身につきます"
            },
            {
                "title": "イノベーションチャレンジ",
                "task": "古い方法でやっていることを1つ、新しいやり方で試してみよう",
                "time": "随時",
                "benefit": "革新思考と変化適応力が向上します"
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
        embed.add_field(
            name="🚀 行動のコツ",
            value="完璧を求めず、まずは始めることが大切！小さな一歩が大きな変化を生みます。",
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 🎯 毎日の挑戦で成長しよう")
        
        await self.send_to_guild(guild, settings, embed)
    
    async def send_trends_content(self, guild, settings):
        """ビジネストレンドコンテンツを送信"""
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
            },
            {
                "category": "🛒 Eコマース",
                "trend": "ライブコマースが急成長",
                "detail": "リアルタイム配信での商品販売が、特にZ世代に人気を集めています。",
                "action": "SNSを活用した新しい販売手法を検討してみましょう。"
            },
            {
                "category": "🏥 ヘルステック",
                "trend": "デジタルヘルスサービスが拡大",
                "detail": "オンライン診療やウェアラブルデバイスによる健康管理が一般化しています。",
                "action": "従業員の健康管理にテクノロジーを活用しましょう。"
            },
            {
                "category": "💰 フィンテック",
                "trend": "デジタル決済がさらに普及",
                "detail": "QRコード決済やBNPL(後払い)サービスが消費者行動を変えています。",
                "action": "顧客の決済体験を見直してみましょう。"
            },
            {
                "category": "🎓 エドテック",
                "trend": "オンライン学習プラットフォームが成長",
                "detail": "スキルアップやリスキリングの需要増加でオンライン教育市場が拡大中です。",
                "action": "従業員のスキル開発にオンライン学習を取り入れましょう。"
            },
            {
                "category": "🚗 モビリティ",
                "trend": "MaaS(Mobility as a Service)が注目",
                "detail": "移動を一つのサービスとして提供する概念が都市部で実用化されています。",
                "action": "事業でのモビリティサービス活用を検討しましょう。"
            },
            {
                "category": "🏭 製造業",
                "trend": "スマートファクトリーが主流に",
                "detail": "IoTとAIを活用した自動化・最適化が製造業の競争力を左右しています。",
                "action": "生産プロセスのデジタル化を進めましょう。"
            },
            {
                "category": "🌐 Web3",
                "trend": "ブロックチェーン技術の実用化が進展",
                "detail": "NFTやDeFi以外にも、供給チェーン管理などでの活用が広がっています。",
                "action": "ブロックチェーンの事業活用可能性を調査しましょう。"
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
        embed.add_field(
            name="🔍 さらに学ぶには",
            value="関連するニュースサイトや業界レポートをチェックして、より深い理解を得ましょう。",
            inline=False
        )
        embed.set_footer(text="ZERO to ONE 📈 トレンドを先取りして競争優位を築こう")
        
        await self.send_to_guild(guild, settings, embed)
    
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
    @discord.app_commands.command(name='daily_test', description='定期発信機能のテスト（管理者専用）')
    @discord.app_commands.describe(content_type='テストする内容タイプ')
    @discord.app_commands.default_permissions(administrator=True)
    async def test_daily_content(self, interaction: discord.Interaction, content_type: str):
        """定期発信機能のテスト"""
        
        guild = interaction.guild
        settings = self.settings_manager.get_guild_settings(str(guild.id))
        content_type = content_type.lower()
        
        if content_type in ['quote', '格言', '名言']:
            await self.send_quotes_content(guild, settings)
            await interaction.response.send_message("起業家格言を送信しました", ephemeral=True)
        elif content_type in ['tip', 'tips', 'スキル']:
            await self.send_tips_content(guild, settings)
            await interaction.response.send_message("スキルアップTipsを送信しました", ephemeral=True)
        elif content_type in ['challenge', 'チャレンジ']:
            await self.send_challenge_content(guild, settings)
            await interaction.response.send_message("今日のチャレンジを送信しました", ephemeral=True)
        elif content_type in ['trend', 'トレンド', 'ニュース']:
            await self.send_trends_content(guild, settings)
            await interaction.response.send_message("ビジネストレンド速報を送信しました", ephemeral=True)
        else:
            await interaction.response.send_message(
                "利用可能なタイプ: quote(格言), tip(スキル), challenge(チャレンジ), trend(トレンド)",
                ephemeral=True
            )
    
    # 設定用スラッシュコマンド
    @discord.app_commands.command(name='daily_config', description='定期発信機能の設定')
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(
        action='実行するアクション',
        channel='送信先チャンネル',
        mention='メンション対象',
        content_type='設定するコンテンツタイプ',
        enabled='有効/無効',
        hour='時刻（時）',
        minute='時刻（分）',
        days='曜日（トレンド用、例：1,4 = 火金）'
    )
    async def daily_config(self, interaction: discord.Interaction, 
                          action: str,
                          channel: discord.TextChannel = None,
                          mention: str = None,
                          content_type: str = None,
                          enabled: bool = None,
                          hour: int = None,
                          minute: int = None,
                          days: str = None):
        """定期発信機能の設定コマンド"""
        
        
        guild_id = str(interaction.guild.id)
        
        if action.lower() == "show":
            # 現在の設定を表示
            settings = self.settings_manager.get_guild_settings(guild_id)
            
            embed = discord.Embed(
                title="🔧 定期発信設定",
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
                    value="自動選択（システム > general > 最初のチャンネル）",
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
            
            # スケジュール設定
            schedule_info = self.settings_manager.format_schedule_info(settings)
            embed.add_field(
                name="⏰ スケジュール",
                value=schedule_info,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        elif action.lower() == "channel":
            # チャンネル設定
            if not channel:
                await interaction.response.send_message("チャンネルを指定してください", ephemeral=True)
                return
            
            success = self.settings_manager.update_channel_settings(
                guild_id, 
                channel_id=str(channel.id)
            )
            
            if success:
                await interaction.response.send_message(
                    f"送信先チャンネルを {channel.mention} に設定しました",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        elif action.lower() == "mention":
            # メンション設定
            if not mention:
                await interaction.response.send_message("メンション対象を指定してください", ephemeral=True)
                return
            
            mention_target = None
            if mention.lower() in ["everyone", "@everyone"]:
                mention_target = "@everyone"
            elif mention.lower() in ["here", "@here"]:
                mention_target = "@here"
            elif mention.lower() in ["none", "なし", "無し"]:
                mention_target = None
            else:
                # ロール名またはIDとして処理
                role = None
                if mention.startswith('<@&') and mention.endswith('>'):
                    # メンション形式
                    try:
                        role_id = int(mention[3:-1])
                        role = interaction.guild.get_role(role_id)
                    except ValueError:
                        pass
                else:
                    # ロール名検索
                    role = discord.utils.get(interaction.guild.roles, name=mention)
                
                if role:
                    mention_target = str(role.id)
                else:
                    await interaction.response.send_message("指定されたロールが見つかりません", ephemeral=True)
                    return
            
            success = self.settings_manager.update_channel_settings(
                guild_id,
                mention_target=mention_target
            )
            
            if success:
                if mention_target:
                    await interaction.response.send_message(
                        f"メンション設定を {mention} に設定しました",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message("メンションを無効にしました", ephemeral=True)
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        elif action.lower() == "schedule":
            # スケジュール設定
            if not content_type:
                await interaction.response.send_message(
                    "コンテンツタイプを指定してください (quotes/tips/challenge/trends)",
                    ephemeral=True
                )
                return
            
            valid_types = ["quotes", "tips", "challenge", "trends"]
            if content_type.lower() not in valid_types:
                await interaction.response.send_message(
                    f"有効なコンテンツタイプ: {', '.join(valid_types)}",
                    ephemeral=True
                )
                return
            
            # 時刻の妥当性チェック
            if hour is not None and minute is not None:
                if not self.settings_manager.validate_time(hour, minute):
                    await interaction.response.send_message("時刻は0-23時、0-59分で指定してください", ephemeral=True)
                    return
            
            # 曜日の妥当性チェック（トレンド用）
            if content_type.lower() == "trends" and days:
                if not self.settings_manager.validate_weekdays(days):
                    await interaction.response.send_message(
                        "曜日は0-6（月-日）で指定してください（例：1,4）",
                        ephemeral=True
                    )
                    return
            
            success = self.settings_manager.update_content_schedule(
                guild_id,
                content_type.lower(),
                enabled=enabled,
                hour=hour,
                minute=minute,
                days=days
            )
            
            if success:
                await interaction.response.send_message(
                    f"{content_type} のスケジュール設定を更新しました",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message("設定の更新に失敗しました", ephemeral=True)
                
        else:
            await interaction.response.send_message(
                "利用可能なアクション: show（設定表示）, channel（チャンネル設定）, mention（メンション設定）, schedule（スケジュール設定）",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(DailyContentCog(bot))