"""
Discord Bot - 告知自動検出・応援機能
実例ベースの判定ロジックで告知を検出してロールメンションで拡散する
"""

import discord
from discord.ext import commands
import re
import logging
from typing import Optional, List
import asyncio
from datetime import datetime, timedelta

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnnouncementDetector(commands.Cog):
    """告知自動検出・応援クラス"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # チャンネル・ロール設定
        self.ANNOUNCEMENT_CHANNEL_ID = 1330790111259922513  # 告知元チャンネル
        self.EVERYONE_ROLE_ID = 1382167308180394145        # みんなの告知ロール
        self.STAFF_ROLE_ID = 1236487195741913119           # 運営ロール
        
        # ユーザーの投稿履歴（メモリ上で管理）
        self.user_post_history = {}  # {user_id: [timestamp, ...]}
        
        logger.info("📢 AnnouncementDetector初期化完了")
    
    def update_user_history(self, user_id: int):
        """ユーザーの投稿履歴を更新"""
        now = datetime.now()
        if user_id not in self.user_post_history:
            self.user_post_history[user_id] = []
        
        # 1時間以内の投稿のみ保持
        self.user_post_history[user_id] = [
            timestamp for timestamp in self.user_post_history[user_id]
            if now - timestamp < timedelta(hours=1)
        ]
        
        # 新しい投稿を追加
        self.user_post_history[user_id].append(now)
    
    def has_recent_posts(self, user_id: int) -> bool:
        """1時間以内に投稿があるかチェック"""
        if user_id not in self.user_post_history:
            return False
        
        now = datetime.now()
        recent_posts = [
            timestamp for timestamp in self.user_post_history[user_id]
            if now - timestamp < timedelta(hours=1)
        ]
        
        return len(recent_posts) > 1  # 現在の投稿を除いて1つ以上あれば
    
    def check_structure(self, content: str) -> dict:
        """1次判定: 構造的特徴をチェック"""
        result = {
            'length_ok': len(content) >= 200,
            'line_breaks': content.count('\n') >= 5,
            'has_url': bool(re.search(r'https?://', content)),
            'has_bullet_points': bool(re.search(r'[・○●•]\s', content))
        }
        
        result['structure_score'] = sum(result.values())
        logger.info(f"📊 構造判定: {result}")
        return result
    
    def check_content(self, content: str) -> dict:
        """2次判定: 内容分析"""
        content_lower = content.lower()
        
        # 未来日時パターン
        future_date = bool(re.search(r'[0-9]{1,2}月[0-9]{1,2}日|[0-9]{1,2}/[0-9]{1,2}|[0-9]{1,2}:[0-9]{2}', content))
        
        # 行動促進キーワード
        action_keywords = ['参加', '申し込み', '募集', 'エントリー', '応募', '受付', '予約', '登録']
        has_action = any(keyword in content for keyword in action_keywords)
        
        # 告知性キーワード
        announcement_keywords = ['イベント', '開催', '決定', 'セミナー', '勉強会', '交流会', 'リリース', '発表', '公開']
        has_announcement_word = any(keyword in content for keyword in announcement_keywords)
        
        # 初投稿性
        greeting_keywords = ['初めまして', 'はじめまして', '初投稿']
        is_first_post = any(keyword in content for keyword in greeting_keywords)
        
        # 組織・企業情報
        org_keywords = ['団体', '組織', '委員会', '会社', '企業', '株式会社', '有限会社']
        has_org_info = any(keyword in content for keyword in org_keywords)
        
        result = {
            'future_date': future_date,
            'has_action': has_action,
            'has_announcement_word': has_announcement_word,
            'is_first_post': is_first_post,
            'has_org_info': has_org_info
        }
        
        result['content_score'] = sum(result.values())
        logger.info(f"📝 内容判定: {result}")
        return result
    
    def check_exclusions(self, message: discord.Message) -> dict:
        """3次判定: 除外条件をチェック"""
        content = message.content
        
        # 既存メンション確認
        target_roles = {self.EVERYONE_ROLE_ID, self.STAFF_ROLE_ID}
        mentioned_role_ids = {role.id for role in message.role_mentions}
        has_existing_mention = bool(target_roles & mentioned_role_ids)
        
        # 返信・リプライ形式
        is_reply = message.reference is not None
        
        # 質問形式（短文で？で終わる）
        is_short_question = len(content) < 100 and content.strip().endswith('？')
        
        # 直近投稿チェック
        has_recent = self.has_recent_posts(message.author.id)
        
        result = {
            'has_existing_mention': has_existing_mention,
            'is_reply': is_reply,
            'is_short_question': is_short_question,
            'has_recent_posts': has_recent
        }
        
        result['should_exclude'] = any([
            has_existing_mention,
            is_reply,
            is_short_question,
            has_recent
        ])
        
        logger.info(f"🚫 除外判定: {result}")
        return result
    
    def is_announcement(self, message: discord.Message) -> bool:
        """総合的な告知判定"""
        content = message.content
        
        # 1次判定: 構造
        structure = self.check_structure(content)
        if structure['structure_score'] < 2:  # 最低2つの構造的特徴が必要
            return False
        
        # 2次判定: 内容
        content_analysis = self.check_content(content)
        if content_analysis['content_score'] < 2:  # 最低2つの内容的特徴が必要
            return False
        
        # 3次判定: 除外条件
        exclusions = self.check_exclusions(message)
        if exclusions['should_exclude']:
            return False
        
        # 総合スコア
        total_score = structure['structure_score'] + content_analysis['content_score']
        logger.info(f"🎯 総合判定スコア: {total_score} - 告知と判定")
        
        return True
    
    def should_mention_staff(self, content: str) -> bool:
        """運営メンションが必要かどうかを判定"""
        content_lower = content.lower()
        
        # 重要度の高いキーワード
        high_priority_keywords = [
            '後援', '協賛', 'スポンサー', '提携', 'パートナー',
            '愛知県', '県', '市', '行政', '自治体',
            '新聞', 'メディア', '取材', 'プレス',
            '大規模', '200名', '100名', '特別', '初'
        ]
        
        staff_keyword_count = sum(1 for keyword in high_priority_keywords 
                                if keyword in content)
        
        # 外部の重要組織が関わっている
        important_orgs = ['県', '市', '新聞', '通信社', '放送']
        has_important_org = any(org in content for org in important_orgs)
        
        return staff_keyword_count >= 2 or has_important_org
    
    async def generate_feedback(self, content: str, author_name: str) -> str:
        """告知に対するフィードバックメッセージを生成"""
        # イベント種別を推定
        content_lower = content.lower()
        
        event_type = "イベント"
        if '勉強会' in content:
            event_type = "勉強会"
        elif 'セミナー' in content:
            event_type = "セミナー"
        elif '交流会' in content:
            event_type = "交流会"
        elif 'リリース' in content or '公開' in content:
            event_type = "リリース"
        elif '団体' in content or '組織' in content:
            event_type = "団体イベント"
        
        # 日時情報の抽出
        date_match = re.search(r'([0-9]{1,2}月[0-9]{1,2}日|[0-9]{1,2}/[0-9]{1,2})', content)
        date_info = f"📅 {date_match.group(1)}" if date_match else ""
        
        # 基本フィードバック
        feedback_lines = [
            f"📢 {author_name}さんからの{event_type}告知です！"
        ]
        
        if date_info:
            feedback_lines.append(date_info)
        
        # 特徴的な要素を抽出
        if 'LINE' in content and 'https://' in content:
            feedback_lines.append("🔗 詳細・申し込みはLINEから！")
        elif 'https://' in content:
            feedback_lines.append("🔗 詳細リンクあり")
        
        if '無料' in content:
            feedback_lines.append("💰 参加無料")
        
        if '抽選' in content or '豪華' in content:
            feedback_lines.append("🎁 豪華特典あり")
        
        # 応援メッセージ
        feedback_lines.extend([
            "",
            "✨ 素晴らしい機会ですね！興味のある方はぜひチェックしてみてください！",
            "🚀 みんなで応援しましょう！"
        ])
        
        return "\n".join(feedback_lines)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """メッセージ受信時の告知検出処理"""
        # BOTメッセージは除外
        if message.author.bot:
            return
            
        # 対象チャンネルかチェック
        if message.channel.id != self.ANNOUNCEMENT_CHANNEL_ID:
            return
        
        # ユーザーの投稿履歴を更新
        self.update_user_history(message.author.id)
        
        # 告知判定
        if not self.is_announcement(message):
            return
        
        logger.info(f"🎯 告知検出成功: {message.author.display_name}")
        
        try:
            # フィードバック生成
            feedback = await self.generate_feedback(message.content, message.author.display_name)
            
            # メンション準備
            everyone_role = message.guild.get_role(self.EVERYONE_ROLE_ID)
            mentions = []
            
            if everyone_role:
                mentions.append(everyone_role.mention)
            
            # 運営メンション判定
            if self.should_mention_staff(message.content):
                staff_role = message.guild.get_role(self.STAFF_ROLE_ID)
                if staff_role:
                    mentions.append(staff_role.mention)
                    feedback += "\n🏢 運営チームにもお知らせ！ぜひ応援しましょう！"
            
            # メッセージ送信（少し遅延を入れる）
            await asyncio.sleep(2)  # 2秒後に送信
            
            mention_text = " ".join(mentions)
            full_message = f"{mention_text}\n\n{feedback}"
            
            await message.channel.send(full_message)
            
            logger.info(f"✅ 告知応援メッセージ送信完了")
            
        except Exception as e:
            logger.error(f"❌ 告知処理エラー: {e}")
    
    @discord.app_commands.command(name="announcement_test", description="告知検出テスト")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(text="テスト対象のテキスト")
    async def test_announcement_detection(self, interaction: discord.Interaction, text: str):
        """告知検出機能のテスト"""
        await interaction.response.defer()
        
        # テスト用の仮メッセージオブジェクト作成
        class MockMessage:
            def __init__(self, content, author_id):
                self.content = content
                self.author = type('Author', (), {'id': author_id, 'display_name': 'テストユーザー'})()
                self.reference = None
                self.role_mentions = []
        
        mock_message = MockMessage(text, interaction.user.id)
        
        # 各段階の判定を実行
        structure = self.check_structure(text)
        content_analysis = self.check_content(text)
        exclusions = self.check_exclusions(mock_message)
        
        is_announcement = (
            structure['structure_score'] >= 2 and 
            content_analysis['content_score'] >= 2 and 
            not exclusions['should_exclude']
        )
        
        should_mention_staff = self.should_mention_staff(text)
        
        # 結果表示
        embed = discord.Embed(
            title="🧪 告知検出テスト結果",
            color=discord.Color.green() if is_announcement else discord.Color.orange()
        )
        
        embed.add_field(
            name="📝 入力テキスト", 
            value=text[:200] + "..." if len(text) > 200 else text, 
            inline=False
        )
        
        embed.add_field(
            name="🏗️ 構造判定", 
            value=f"スコア: {structure['structure_score']}/4\n文字数: {'✅' if structure['length_ok'] else '❌'} 改行: {'✅' if structure['line_breaks'] else '❌'} URL: {'✅' if structure['has_url'] else '❌'} 箇条書き: {'✅' if structure['has_bullet_points'] else '❌'}", 
            inline=True
        )
        
        embed.add_field(
            name="📄 内容判定", 
            value=f"スコア: {content_analysis['content_score']}/5\n日時: {'✅' if content_analysis['future_date'] else '❌'} 行動促進: {'✅' if content_analysis['has_action'] else '❌'} 告知語: {'✅' if content_analysis['has_announcement_word'] else '❌'}", 
            inline=True
        )
        
        embed.add_field(
            name="🚫 除外判定", 
            value=f"除外: {'⚠️ あり' if exclusions['should_exclude'] else '✅ なし'}", 
            inline=True
        )
        
        embed.add_field(
            name="🎯 最終判定", 
            value=f"**{'✅ 告知として認識' if is_announcement else '❌ 通常メッセージ'}**", 
            inline=False
        )
        
        if is_announcement:
            embed.add_field(
                name="🏢 運営メンション", 
                value="✅ あり" if should_mention_staff else "❌ なし", 
                inline=True
            )
            
            feedback = await self.generate_feedback(text, "テストユーザー")
            embed.add_field(
                name="📢 生成メッセージ", 
                value=feedback[:500] + "..." if len(feedback) > 500 else feedback, 
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @discord.app_commands.command(name="announcement_config", description="告知検出設定確認")
    @discord.app_commands.default_permissions(administrator=True)
    async def show_config(self, interaction: discord.Interaction):
        """告知検出設定の確認"""
        embed = discord.Embed(
            title="⚙️ 告知検出設定",
            color=discord.Color.blue()
        )
        
        # チャンネル情報
        announcement_channel = self.bot.get_channel(self.ANNOUNCEMENT_CHANNEL_ID)
        embed.add_field(
            name="📺 監視チャンネル",
            value=f"<#{self.ANNOUNCEMENT_CHANNEL_ID}>" if announcement_channel else "チャンネルが見つかりません",
            inline=False
        )
        
        # ロール情報
        guild = interaction.guild
        everyone_role = guild.get_role(self.EVERYONE_ROLE_ID) if guild else None
        staff_role = guild.get_role(self.STAFF_ROLE_ID) if guild else None
        
        embed.add_field(
            name="👥 メンション対象ロール",
            value=f"みんなの告知: <@&{self.EVERYONE_ROLE_ID}>\n運営: <@&{self.STAFF_ROLE_ID}>",
            inline=False
        )
        
        # 判定条件
        embed.add_field(
            name="📋 判定条件",
            value="**1次: 構造**\n• 200文字以上 + 5行以上\n• URL + 箇条書き\n\n**2次: 内容**\n• 日時 + 行動促進語\n• 告知性キーワード\n\n**3次: 除外**\n• 既存メンション/返信\n• 直近投稿チェック",
            inline=False
        )
        
        # 履歴情報
        active_users = len([uid for uid, history in self.user_post_history.items() if history])
        embed.add_field(
            name="📊 監視状況",
            value=f"アクティブユーザー: {active_users}人\n投稿履歴: 1時間保持",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Cogのセットアップ"""
    await bot.add_cog(AnnouncementDetector(bot))