# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
import asyncio
import random
import datetime
from typing import Dict, List, Optional

class RumbleGame:
    def __init__(self):
        self.players: Dict[discord.Member, str] = {}  # player: team (red/blue)
        self.ready_players: List[discord.Member] = []
        self.in_progress = False
        self.channel: Optional[discord.TextChannel] = None
        self.time_limit: int = 60
        self.start_time: datetime.datetime = datetime.datetime.now()
    
    def add_player(self, player: discord.Member) -> bool:
        if player in self.players or self.in_progress:
            return False
        
        # チーム振り分け（バランスを考慮）
        red_count = sum(1 for team in self.players.values() if team == 'red')
        blue_count = sum(1 for team in self.players.values() if team == 'blue')
        
        team = 'red' if red_count <= blue_count else 'blue'
        self.players[player] = team
        return True
    
    def remove_player(self, player: discord.Member) -> bool:
        if player in self.players and not self.in_progress:
            del self.players[player]
            if player in self.ready_players:
                self.ready_players.remove(player)
            return True
        return False
    
    def toggle_ready(self, player: discord.Member) -> bool:
        if player not in self.players or self.in_progress:
            return False
        
        if player in self.ready_players:
            self.ready_players.remove(player)
        else:
            self.ready_players.append(player)
        return True
    
    def can_start(self) -> bool:
        if self.in_progress:
            return False
        
        # 最低2人、全員ready
        return (len(self.players) >= 2 and 
                len(self.ready_players) == len(self.players))
    
    def get_teams(self) -> tuple[List[discord.Member], List[discord.Member]]:
        red_team = [p for p, t in self.players.items() if t == 'red']
        blue_team = [p for p, t in self.players.items() if t == 'blue']
        return red_team, blue_team

class RumbleView(discord.ui.View):
    def __init__(self, game: RumbleGame, admin_id: str):
        super().__init__(timeout=300)  # 5分でタイムアウト
        self.game = game
        self.admin_id = admin_id
    
    @discord.ui.button(label="参加", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.add_player(interaction.user):
            team_name = "赤" if self.game.players[interaction.user] == 'red' else "青"
            await interaction.response.send_message(
                f"{interaction.user.mention} がランブルに参加しました！（チーム: {team_name}）",
                ephemeral=True
            )
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message(
                "すでに参加しているか、ゲームが進行中です",
                ephemeral=True
            )
    
    @discord.ui.button(label="退出", style=discord.ButtonStyle.danger, emoji="🚪")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.remove_player(interaction.user):
            await interaction.response.send_message(
                f"{interaction.user.mention} がランブルから退出しました",
                ephemeral=True
            )
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message(
                "参加していないか、ゲームが進行中です",
                ephemeral=True
            )
    
    async def update_embed(self, interaction: discord.Interaction):
        red_team, blue_team = self.game.get_teams()
        
        embed = discord.Embed(
            title="⚔️ ランブルマッチ募集中！",
            description="参加ボタンを押して参加し、準備ができたら準備完了ボタンを押してください",
            color=discord.Color.orange()
        )
        
        # 赤チーム
        red_names = []
        for player in red_team:
            ready = "✅" if player in self.game.ready_players else "⏳"
            red_names.append(f"{ready} {player.display_name}")
        embed.add_field(
            name=f"🔴 赤チーム ({len(red_team)}人)",
            value="\n".join(red_names) if red_names else "募集中...",
            inline=True
        )
        
        # 青チーム
        blue_names = []
        for player in blue_team:
            ready = "✅" if player in self.game.ready_players else "⏳"
            blue_names.append(f"{ready} {player.display_name}")
        embed.add_field(
            name=f"🔵 青チーム ({len(blue_team)}人)",
            value="\n".join(blue_names) if blue_names else "募集中...",
            inline=True
        )
        
        # ステータス
        if self.game.can_start():
            embed.add_field(
                name="ステータス",
                value="✅ 開始可能！",
                inline=False
            )
        else:
            conditions = []
            if len(self.game.ready_players) < len(self.game.players):
                conditions.append("全員が準備完了する")
            if len(self.game.players) < 2:
                conditions.append("最低2人必要")
            
            embed.add_field(
                name="開始条件",
                value="\n".join(f"❌ {c}" for c in conditions),
                inline=False
            )
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    async def update_embed_from_admin(self):
        """管理者操作によるEmbed更新"""
        if hasattr(self, 'last_interaction') and self.last_interaction:
            await self.update_embed(self.last_interaction)
    
    async def start_game_from_admin(self):
        """管理者操作によるゲーム開始"""
        if hasattr(self, 'last_interaction') and self.last_interaction:
            await self.start_game(self.last_interaction)
    
    async def start_game(self, interaction: discord.Interaction):
        self.game.in_progress = True
        
        # ボタンを無効化
        for item in self.children:
            item.disabled = True
        
        await interaction.edit_original_response(view=self)
        
        red_team, blue_team = self.game.get_teams()
        
        # チャレンジ開始エンベッド
        embed = discord.Embed(
            title="🎯 ZERO to ONE チャレンジ開始！",
            description="キャリア成長バトルが始まります！各ラウンドで様々な挑戦が待っています！",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔥 チャレンジャーズ",
            value="\n".join(p.display_name for p in red_team),
            inline=True
        )
        embed.add_field(
            name="💼 ビジネスチーム",
            value="\n".join(p.display_name for p in blue_team),
            inline=True
        )
        
        await interaction.channel.send(embed=embed)
        
        # ラウンド制バトル実行
        await self.run_career_rounds(interaction.channel, red_team, blue_team)
    
    async def run_career_rounds(self, channel, red_team, blue_team):
        """キャリア成長ラウンド制バトル"""
        
        # チームスコア初期化
        red_score = 0
        blue_score = 0
        
        career_challenges = [
            {
                "title": "📊 ビジネス企画力チャレンジ",
                "scenarios": [
                    "新サービスのアイデアを5分で考案！", 
                    "競合分析をサクッと実施！",
                    "マーケティング戦略を立案！",
                    "投資家向けピッチ資料を作成！",
                    "市場調査結果から新商品を企画！",
                    "ユーザーペルソナを設定してサービス改善！",
                    "収益モデルを構築して事業計画を立案！",
                    "ブランディング戦略で差別化を図る！",
                    "データ分析から次の施策を決定！",
                    "SNSマーケティングで認知度アップ！",
                    "スタートアップのビジネスモデルを構築！",
                    "サブスクリプション型サービスを企画！",
                    "BtoBサービスの営業戦略を考案！",
                    "海外展開のロードマップを作成！",
                    "DX推進プロジェクトを立案！",
                    "新規事業の採算性を計算！",
                    "クラウドファンディングの企画を作成！",
                    "フリーミアムモデルの戦略を構築！",
                    "アフィリエイトマーケティング戦略を考案！",
                    "インフルエンサーマーケティングを企画！",
                    "オムニチャネル戦略を設計！",
                    "カスタマージャーニーマップを作成！",
                    "価格戦略とポジショニングを決定！",
                    "プロダクトマーケットフィットを検証！",
                    "リーンスタートアップ手法で事業検証！"
                ]
            },
            {
                "title": "🤝 コミュニケーション力チャレンジ", 
                "scenarios": [
                    "クライアントとの交渉を成功させろ！",
                    "チームの士気を上げるスピーチ！",
                    "困っている同僚をサポート！",
                    "厳しいクレーム対応を円満解決！",
                    "上司を説得して新企画を承認してもらう！",
                    "チーム内の対立を仲裁して解決！",
                    "プレゼンで投資家の心を掴む！",
                    "多様な価値観のメンバーをまとめる！",
                    "リモートワークチームの結束を高める！",
                    "顧客の真のニーズを聞き出す！",
                    "部下のモチベーション低下を解決！",
                    "異文化チームでの意思疎通を円滑化！",
                    "ステークホルダーとの利害調整！",
                    "緊急事態での冷静な情報伝達！",
                    "パワハラ問題を適切に対処！",
                    "世代間ギャップを埋めるコミュニケーション！",
                    "オンライン会議での効果的なファシリテート！",
                    "炎上した企画を関係者に説明！",
                    "海外クライアントとの文化の壁を越える！",
                    "メディア対応でブランドイメージを守る！",
                    "労働組合との交渉を成功させる！",
                    "転職を考える優秀な部下を引き留める！",
                    "新卒採用の面接で人材を見極める！",
                    "退職する社員との円満な引き継ぎ！",
                    "取引先との長期パートナーシップを構築！"
                ]
            },
            {
                "title": "💡 問題解決力チャレンジ",
                "scenarios": [
                    "システムトラブルを迅速に解決！",
                    "予算不足の課題をクリア！", 
                    "納期遅れをリカバリー！",
                    "売上急降下の原因を特定して改善！",
                    "人手不足を効率化で乗り切る！",
                    "競合他社の追い上げに対抗策を考案！",
                    "品質問題を根本から解決！",
                    "コスト削減しながら品質維持！",
                    "新型ウイルス対応で事業継続！",
                    "炎上案件を鎮静化させる！",
                    "データ漏洩事故の緊急対応！",
                    "工場の生産ライン停止を復旧！",
                    "サプライチェーン断絶への対策！",
                    "キーパーソンの突然の退職をカバー！",
                    "法規制変更への緊急対応！",
                    "自然災害でのBCP発動！",
                    "ハッキング被害からの復旧！",
                    "在庫過多による資金繰り悪化を解決！",
                    "特許侵害問題への対処！",
                    "労働基準法違反の改善！",
                    "環境問題への企業対応！",
                    "AI導入による業務効率化！",
                    "レガシーシステムの刷新計画！",
                    "リモートワーク環境の最適化！",
                    "セキュリティホールの緊急パッチ対応！"
                ]
            },
            {
                "title": "🚀 リーダーシップチャレンジ",
                "scenarios": [
                    "新プロジェクトを成功に導け！",
                    "チームの方向性を決定！",
                    "困難な決断を下す時！",
                    "組織改革を推進してチームを変革！",
                    "失敗から立ち直るチームを鼓舞！",
                    "多国籍チームの文化の違いを乗り越える！",
                    "限られた時間で最大の成果を出す！",
                    "新人メンバーを一人前に育成！",
                    "ベテラン社員のモチベーションを復活！",
                    "会社の危機を乗り越える決断！",
                    "大規模リストラの実行と組織再建！",
                    "M&A後の企業統合をリード！",
                    "新市場参入の陣頭指揮！",
                    "デジタルトランスフォーメーションを主導！",
                    "企業文化改革プロジェクトを牽引！",
                    "グローバル展開戦略の実行！",
                    "イノベーション創出のための組織作り！",
                    "危機的な業績を黒字転換！",
                    "次世代リーダーの育成システム構築！",
                    "ダイバーシティ推進の組織変革！",
                    "サステナビリティ経営への転換！",
                    "アジャイル組織への変革！",
                    "データドリブン経営の導入！",
                    "カスタマーファーストの組織作り！",
                    "スタートアップ買収後の統合管理！"
                ]
            }
        ]
        
        round_num = 1
        all_players_scores = {}  # プレイヤーごとの累計得点を記録
        
        for challenge in career_challenges:
            await asyncio.sleep(20)  # 20秒間隔
            
            # ラウンド開始アナウンス
            scenario = random.choice(challenge["scenarios"])
            
            round_start_embed = discord.Embed(
                title=f"📋 Round {round_num}: {challenge['title']}",
                description=f"**チャレンジ:** {scenario}",
                color=discord.Color.orange()
            )
            await channel.send(embed=round_start_embed)
            
            # 各プレイヤーの個別パフォーマンスを計算
            red_results = self.calculate_individual_performance(red_team, challenge["title"])
            blue_results = self.calculate_individual_performance(blue_team, challenge["title"])
            
            # チームごとの合計得点を計算
            red_round_score = sum(result["points"] for result in red_results)
            blue_round_score = sum(result["points"] for result in blue_results)
            
            # 個人累計得点を記録
            for result in red_results + blue_results:
                player_id = str(result["player"].id)
                if player_id not in all_players_scores:
                    all_players_scores[player_id] = {"player": result["player"], "total_points": 0}
                all_players_scores[player_id]["total_points"] += result["points"]
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 先攻チーム（チャレンジャーズ）の結果
            red_details = self.format_team_results(red_results, red_round_score)
            red_embed = discord.Embed(
                title=f"🔥 チャレンジャーズ (合計: {red_round_score}pt)",
                description=red_details,
                color=discord.Color.red()
            )
            await channel.send(embed=red_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 後攻チーム（ビジネスチーム）の結果
            blue_details = self.format_team_results(blue_results, blue_round_score)
            blue_embed = discord.Embed(
                title=f"💼 ビジネスチーム (合計: {blue_round_score}pt)",
                description=blue_details,
                color=discord.Color.blue()
            )
            await channel.send(embed=blue_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # ラウンド勝者決定と現在のスコア
            if red_round_score > blue_round_score:
                red_score += 1
                team_name = "🔥 チャレンジャーズ"
                result_msg = f"合計 {red_round_score}pt で勝利！"
            elif blue_round_score > red_round_score:
                blue_score += 1
                team_name = "💼 ビジネスチーム"
                result_msg = f"合計 {blue_round_score}pt で勝利！"
            else:
                team_name = "引き分け"
                result_msg = f"両チーム {red_round_score}pt で同点！"
            
            result_embed = discord.Embed(
                title="🏆 ラウンド結果",
                color=discord.Color.gold()
            )
            result_embed.add_field(
                name="勝者",
                value=f"{team_name}\n✨ {result_msg}",
                inline=False
            )
            result_embed.add_field(
                name="📈 現在のスコア",
                value=f"🔥 チャレンジャーズ: {red_score}点\n💼 ビジネスチーム: {blue_score}点",
                inline=False
            )
            
            await channel.send(embed=result_embed)
            round_num += 1
        
        # 最終結果発表
        await asyncio.sleep(2)
        
        if red_score > blue_score:
            final_winners = red_team
            final_losers = blue_team
            winner_name = "🔥 チャレンジャーズ"
            winner_message = "新しい発想と柔軟性で勝利！"
        elif blue_score > red_score:
            final_winners = blue_team
            final_losers = red_team
            winner_name = "💼 ビジネスチーム"
            winner_message = "経験と戦略で勝利！"
        else:
            # 引き分けの場合
            final_embed = discord.Embed(
                title="🤝 ZERO to ONE チャレンジ結果",
                description="**素晴らしい！引き分けです！**\n両チームとも成長の証！",
                color=discord.Color.gold()
            )
            final_embed.add_field(
                name="🎉 結果",
                value="お互いの強みを認め合える素晴らしいバトルでした！\n全員がキャリア成長の階段を一歩上がりました！",
                inline=False
            )
            await channel.send(embed=final_embed)
            return
        
        # 勝者発表（メンション付きで盛り上げ）
        final_embed = discord.Embed(
            title="🎉 ZERO to ONE チャレンジ結果",
            description=f"**{winner_name} の勝利！**\n{winner_message}",
            color=discord.Color.gold()
        )
        
        # メンション付きで勝者チーム表示
        winner_mentions = " ".join(p.mention for p in final_winners)
        loser_mentions = " ".join(p.mention for p in final_losers)
        
        final_embed.add_field(
            name="🏆 優勝チーム",
            value=winner_mentions,
            inline=False
        )
        
        final_embed.add_field(
            name="📊 最終スコア",
            value=f"🔥 チャレンジャーズ: {red_score}点\n💼 ビジネスチーム: {blue_score}点",
            inline=False
        )
        
        final_embed.add_field(
            name="💝 成長ポイント",
            value="全参加者がキャリアスキルを磨きました！\n次回もぜひ挑戦してくださいね！",
            inline=False
        )
        
        # 勝者への特別メッセージ
        celebration_msg = f"🎊 おめでとうございます！ {winner_mentions}\n素晴らしいチームワークでした！"
        
        await channel.send(embed=final_embed)
        await channel.send(celebration_msg)
        
        # MVP表彰
        await asyncio.sleep(3)
        await self.announce_mvp(channel, all_players_scores)
    
    def calculate_individual_performance(self, team, challenge_title):
        """各プレイヤーの個別パフォーマンスと得点を計算"""
        results = []
        
        # チャレンジ別のパフォーマンスパターン（大幅に拡張）
        performance_patterns = {
            "📊 ビジネス企画力チャレンジ": {
                "excellent": [
                    {"action": "💡 革新的なアイデアを提案", "points": 3},
                    {"action": "📈 市場分析で新トレンドを発見", "points": 3},
                    {"action": "🚀 実現可能性の高い戦略を構築", "points": 3},
                    {"action": "💰 収益モデルの完璧な設計", "points": 3},
                    {"action": "🎯 ターゲット市場を的確に特定", "points": 3},
                    {"action": "📊 データドリブンな企画を立案", "points": 3},
                    {"action": "🌟 独創的なマーケティング戦略", "points": 3},
                    {"action": "🔥 競合優位性を明確に打ち出し", "points": 3},
                    {"action": "💎 ユニークバリュープロポジションを創出", "points": 3},
                    {"action": "🎪 エンターテイメント性抜群の企画", "points": 3},
                    {"action": "🧠 論理的思考で課題を解決", "points": 3},
                    {"action": "✨ 斬新なビジネスモデルを考案", "points": 3},
                    {"action": "🏆 投資家が食いつく企画書を作成", "points": 3},
                    {"action": "🎨 クリエイティブな発想で差別化", "points": 3},
                    {"action": "⚡ スピード重視の実行計画を策定", "points": 3}
                ],
                "good": [
                    {"action": "📋 詳細なリサーチを実施", "points": 2},
                    {"action": "🔍 競合の弱点を特定", "points": 2},
                    {"action": "📊 データを整理して提示", "points": 2},
                    {"action": "💼 実務的な企画を提案", "points": 2},
                    {"action": "📈 成長戦略を明確に描く", "points": 2},
                    {"action": "🎯 マイルストーンを設定", "points": 2},
                    {"action": "💡 改善案を複数提示", "points": 2},
                    {"action": "🔄 PDCAサイクルを組み込み", "points": 2},
                    {"action": "📝 詳細な仕様書を作成", "points": 2},
                    {"action": "🤝 ステークホルダーを意識した企画", "points": 2},
                    {"action": "💻 デジタル活用の提案", "points": 2},
                    {"action": "🌐 グローバル展開を視野に入れる", "points": 2},
                    {"action": "🔧 技術的実現性を検証", "points": 2},
                    {"action": "📱 モバイルファーストの設計", "points": 2},
                    {"action": "💚 サステナビリティを考慮", "points": 2}
                ],
                "average": [
                    {"action": "💭 アイデアを出すも平凡", "points": 1},
                    {"action": "📝 基本的な調査を実施", "points": 1},
                    {"action": "📋 一般的な企画書を作成", "points": 1},
                    {"action": "🤔 既存事例を参考に提案", "points": 1},
                    {"action": "📊 基本的なデータ分析", "points": 1},
                    {"action": "💼 無難なビジネスプランを策定", "points": 1},
                    {"action": "🎯 ターゲットをざっくり設定", "points": 1},
                    {"action": "📈 標準的な成長計画を立案", "points": 1},
                    {"action": "🔍 表面的な競合分析", "points": 1},
                    {"action": "💡 そこそこのアイデアを提示", "points": 1},
                    {"action": "📝 最低限の要件を満たす企画", "points": 1},
                    {"action": "🎨 デザインに少しこだわり", "points": 1},
                    {"action": "💻 基本的なIT活用を提案", "points": 1},
                    {"action": "📱 モバイル対応を考慮", "points": 1},
                    {"action": "🤝 チームワークを重視した企画", "points": 1}
                ],
                "poor": [
                    {"action": "😅 企画が現実的でなく減点", "points": -1},
                    {"action": "💔 アイデアが既存サービスと酷似", "points": -1},
                    {"action": "⏰ 時間内に企画をまとめられず", "points": -1},
                    {"action": "📉 市場規模を見誤り大幅減点", "points": -1},
                    {"action": "💸 コスト計算が甘く赤字確定", "points": -1},
                    {"action": "🤯 複雑すぎて誰も理解できず", "points": -1},
                    {"action": "🙈 競合調査を怠り後手に回る", "points": -1},
                    {"action": "😰 プレゼンで緊張し支離滅裂", "points": -1},
                    {"action": "💀 法的リスクを見落とし危険", "points": -1},
                    {"action": "🌀 方向性がブレまくり迷走", "points": -1},
                    {"action": "😴 ありきたりで誰も興味を示さず", "points": -1},
                    {"action": "💥 技術的に不可能な提案で炎上", "points": -1},
                    {"action": "🎭 見栄えだけで中身が空っぽ", "points": -1},
                    {"action": "📱 ユーザビリティを完全無視", "points": -1},
                    {"action": "🔥 批判を浴びて企画が頓挫", "points": -1}
                ]
            },
            "🤝 コミュニケーション力チャレンジ": {
                "excellent": [
                    {"action": "🗣️ 説得力抜群のプレゼンで満点", "points": 3},
                    {"action": "🤝 相手の心を完全に掴む", "points": 3},
                    {"action": "😊 チーム全体の士気を大幅向上", "points": 3},
                    {"action": "🎯 的確な質問で本質を引き出す", "points": 3},
                    {"action": "💬 絶妙なタイミングでフォロー", "points": 3},
                    {"action": "🌟 カリスマ性で皆を魅了", "points": 3},
                    {"action": "🎭 ストーリーテリングで感動を呼ぶ", "points": 3},
                    {"action": "🔥 熱意が伝わり全員がやる気に", "points": 3},
                    {"action": "🧠 論理的説明で完全に納得させる", "points": 3},
                    {"action": "💎 的確な比喩で複雑な内容を分かりやすく", "points": 3},
                    {"action": "🎪 エンターテイメント性で場を盛り上げ", "points": 3},
                    {"action": "💡 建設的な提案で議論をリード", "points": 3},
                    {"action": "🤗 相手の立場に立った共感力を発揮", "points": 3},
                    {"action": "⚡ 瞬時に空気を読んで適切な対応", "points": 3},
                    {"action": "🏆 全員が納得する Win-Win の解決策", "points": 3}
                ],
                "good": [
                    {"action": "📢 積極的に意見を発信", "points": 2},
                    {"action": "👂 相手の話をしっかり傾聴", "points": 2},
                    {"action": "💬 適切なタイミングでフォロー", "points": 2},
                    {"action": "🎯 要点を整理して分かりやすく説明", "points": 2},
                    {"action": "🤝 円滑な人間関係を構築", "points": 2},
                    {"action": "😊 ポジティブな雰囲気作りに貢献", "points": 2},
                    {"action": "📝 議事録で重要ポイントを整理", "points": 2},
                    {"action": "🔄 フィードバックを適切に実施", "points": 2},
                    {"action": "💡 建設的な意見交換を促進", "points": 2},
                    {"action": "🎨 視覚的な資料で理解を促進", "points": 2},
                    {"action": "⏰ 時間管理を意識した進行", "points": 2},
                    {"action": "🌐 多様な視点を取り入れる", "points": 2},
                    {"action": "💼 プロフェッショナルな対応", "points": 2},
                    {"action": "🎤 自信を持って発言", "points": 2},
                    {"action": "🤔 相手の立場を考慮した提案", "points": 2}
                ],
                "average": [
                    {"action": "🎤 発表はできたが印象薄", "points": 1},
                    {"action": "💡 提案したが説得力不足", "points": 1},
                    {"action": "📋 必要最低限の報告を実施", "points": 1},
                    {"action": "🤷 当たり障りのない意見を述べる", "points": 1},
                    {"action": "👥 グループ討論で普通に参加", "points": 1},
                    {"action": "📞 電話対応を無難にこなす", "points": 1},
                    {"action": "💬 簡単な質疑応答に対応", "points": 1},
                    {"action": "📊 データを読み上げるだけ", "points": 1},
                    {"action": "🎯 指示された内容を伝達", "points": 1},
                    {"action": "😐 表情は変えずに淡々と対応", "points": 1},
                    {"action": "📝 メモを取りながら聞く", "points": 1},
                    {"action": "⏰ 時間通りに会議を進行", "points": 1},
                    {"action": "🤝 挨拶や基本的なマナーは守る", "points": 1},
                    {"action": "💻 オンライン会議に普通に参加", "points": 1},
                    {"action": "📞 取り次ぎを正確に行う", "points": 1}
                ],
                "poor": [
                    {"action": "😰 緊張で言葉が出ず", "points": -1},
                    {"action": "💔 相手を不快にさせてしまう", "points": -1},
                    {"action": "🤐 最後まで発言できず", "points": -1},
                    {"action": "😡 感情的になって議論が紛糾", "points": -1},
                    {"action": "🙄 相手の話を聞かず一方的に主張", "points": -1},
                    {"action": "📱 会議中にスマホをいじって顰蹙", "points": -1},
                    {"action": "💤 居眠りして重要な情報を聞き逃し", "points": -1},
                    {"action": "🤔 質問の意図を理解できず的外れな回答", "points": -1},
                    {"action": "🗣️ 声が小さすぎて誰にも聞こえず", "points": -1},
                    {"action": "💥 不適切な発言で場が凍りつく", "points": -1},
                    {"action": "🌀 話がまとまらず相手を困惑させる", "points": -1},
                    {"action": "😅 笑ってごまかそうとして逆効果", "points": -1},
                    {"action": "📞 電話を途中で切ってしまい大問題", "points": -1},
                    {"action": "🎭 嘘をついてバレて信頼失墜", "points": -1},
                    {"action": "💀 機密情報を漏らして大炎上", "points": -1}
                ]
            },
            "💡 問題解決力チャレンジ": {
                "excellent": [
                    {"action": "🔧 根本原因を即座に特定", "points": 3},
                    {"action": "⚡ 迅速かつ的確な解決策", "points": 3},
                    {"action": "🧩 複雑な問題を見事に整理", "points": 3},
                    {"action": "💡 創造的なアプローチで突破口を開く", "points": 3},
                    {"action": "🎯 問題の本質を一発で見抜く", "points": 3},
                    {"action": "🚀 スピード解決で他を圧倒", "points": 3},
                    {"action": "🔍 データ分析で隠れた要因を発見", "points": 3},
                    {"action": "💎 エレガントな解決策で感動を呼ぶ", "points": 3},
                    {"action": "🧠 論理的思考で確実に解決", "points": 3},
                    {"action": "⚙️ システム的視点で包括的解決", "points": 3},
                    {"action": "🎪 斬新な発想で常識を覆す", "points": 3},
                    {"action": "🔥 情熱的な取り組みで奇跡を起こす", "points": 3},
                    {"action": "🏆 過去の経験を活かした完璧な対応", "points": 3},
                    {"action": "💰 コスト効率を考慮した最適解", "points": 3},
                    {"action": "🌟 チーム全体のポテンシャルを引き出す", "points": 3}
                ],
                "good": [
                    {"action": "🔍 問題の詳細を正確に調査", "points": 2},
                    {"action": "📝 解決手順を明確に整理", "points": 2},
                    {"action": "🛠️ 実用的な改善案を提示", "points": 2},
                    {"action": "📊 データに基づいた分析を実施", "points": 2},
                    {"action": "🎯 優先順位をつけて段階的に解決", "points": 2},
                    {"action": "💡 複数の選択肢を検討", "points": 2},
                    {"action": "🤝 チームと連携して問題解決", "points": 2},
                    {"action": "⏰ 期限内に確実に解決", "points": 2},
                    {"action": "📈 改善効果を測定可能な形で提示", "points": 2},
                    {"action": "🔄 PDCAサイクルで継続改善", "points": 2},
                    {"action": "💻 ITツールを活用した効率化", "points": 2},
                    {"action": "📚 過去事例を参考に適切な対応", "points": 2},
                    {"action": "🎨 ユーザー視点での解決策を提示", "points": 2},
                    {"action": "💼 ビジネス影響を考慮した判断", "points": 2},
                    {"action": "🌐 グローバルな視点で問題を捉える", "points": 2}
                ],
                "average": [
                    {"action": "🤔 問題は把握したが解決策が曖昧", "points": 1},
                    {"action": "📈 部分的な改善を提案", "points": 1},
                    {"action": "📋 マニュアル通りの対応を実施", "points": 1},
                    {"action": "🔍 表面的な調査で原因を推測", "points": 1},
                    {"action": "💭 一般的な解決策を提示", "points": 1},
                    {"action": "⏰ 時間をかけてゆっくり解決", "points": 1},
                    {"action": "📞 専門家に相談して対応", "points": 1},
                    {"action": "📝 報告書をまとめて状況を整理", "points": 1},
                    {"action": "🎯 明確な範囲で限定的な解決", "points": 1},
                    {"action": "💻 既存システムの範囲内で対応", "points": 1},
                    {"action": "🤝 上司の指示に従って実行", "points": 1},
                    {"action": "📊 基本的なデータ収集を実施", "points": 1},
                    {"action": "🔧 応急処置で一時的に解決", "points": 1},
                    {"action": "📚 参考書を調べて知識を補強", "points": 1},
                    {"action": "🎨 見た目だけの改善を実施", "points": 1}
                ],
                "poor": [
                    {"action": "😵 問題の本質を見誤り迷走", "points": -1},
                    {"action": "💸 コストばかりかかる解決策", "points": -1},
                    {"action": "⏰ 制限時間内に解決できず", "points": -1},
                    {"action": "💥 解決策が裏目に出て状況悪化", "points": -1},
                    {"action": "🙈 問題を見て見ぬふりして放置", "points": -1},
                    {"action": "🤯 パニックになって冷静な判断失う", "points": -1},
                    {"action": "📱 ググって出てきた情報をそのまま実行", "points": -1},
                    {"action": "😅 他人に責任転嫁して逃げる", "points": -1},
                    {"action": "💀 致命的なミスで取り返しのつかない事態", "points": -1},
                    {"action": "🌀 右往左往して時間だけが過ぎる", "points": -1},
                    {"action": "🎭 問題ないふりをして隠蔽工作", "points": -1},
                    {"action": "💔 チームの足を引っ張る解決策", "points": -1},
                    {"action": "🔥 炎上させて問題を拡大", "points": -1},
                    {"action": "😴 面倒くさがって適当に対応", "points": -1},
                    {"action": "💸 予算を大幅にオーバーして大問題", "points": -1}
                ]
            },
            "🚀 リーダーシップチャレンジ": {
                "excellent": [
                    {"action": "👑 的確な判断でチームを完全統率", "points": 3},
                    {"action": "🎯 明確なビジョンで皆を鼓舞", "points": 3},
                    {"action": "🏆 困難な決断で見事に成功へ導く", "points": 3},
                    {"action": "🔥 情熱的なリーダーシップで士気最高潮", "points": 3},
                    {"action": "💡 革新的なアイデアでチームを変革", "points": 3},
                    {"action": "🌟 カリスマ性で全員を魅了", "points": 3},
                    {"action": "⚡ 迅速な意思決定で危機を救う", "points": 3},
                    {"action": "🎪 エンターテイメント性でチームを楽しませる", "points": 3},
                    {"action": "💎 一人ひとりの強みを最大限活用", "points": 3},
                    {"action": "🧠 戦略的思考で長期的成功を設計", "points": 3},
                    {"action": "🤝 多様性を活かしたチーム作り", "points": 3},
                    {"action": "🚀 イノベーションを促進する環境構築", "points": 3},
                    {"action": "💰 利益と社会貢献を両立させる方針", "points": 3},
                    {"action": "🎯 数値目標を掲げて確実に達成", "points": 3},
                    {"action": "🌈 ポジティブな企業文化を創造", "points": 3}
                ],
                "good": [
                    {"action": "🤝 チームワークを重視した采配", "points": 2},
                    {"action": "📊 状況を的確に把握し指示", "points": 2},
                    {"action": "💬 メンバーを上手くサポート", "points": 2},
                    {"action": "🎯 明確な目標設定でチームを導く", "points": 2},
                    {"action": "📈 成果を出すための戦略を立案", "points": 2},
                    {"action": "💡 建設的なフィードバックを提供", "points": 2},
                    {"action": "⏰ 効率的な時間管理で生産性向上", "points": 2},
                    {"action": "🔄 継続的改善の文化を醸成", "points": 2},
                    {"action": "👥 適材適所の人員配置を実施", "points": 2},
                    {"action": "📚 部下の成長を積極的にサポート", "points": 2},
                    {"action": "🌐 外部との連携を効果的に活用", "points": 2},
                    {"action": "💼 責任感を持って役割を全う", "points": 2},
                    {"action": "🎨 クリエイティブな発想を促進", "points": 2},
                    {"action": "🔧 問題解決に積極的に取り組む", "points": 2},
                    {"action": "😊 ポジティブな雰囲気作りに貢献", "points": 2}
                ],
                "average": [
                    {"action": "🎨 新しい視点は出したが指導力不足", "points": 1},
                    {"action": "📈 方向性は良いが実行力が弱い", "points": 1},
                    {"action": "📋 指示された通りにチームを管理", "points": 1},
                    {"action": "💼 事務的な業務を淡々とこなす", "points": 1},
                    {"action": "📊 報告書を作成して状況を共有", "points": 1},
                    {"action": "🤷 平均的な成果でまとまりのあるチーム", "points": 1},
                    {"action": "⏰ 定時通りに会議を進行", "points": 1},
                    {"action": "📞 必要な連絡を適切に実施", "points": 1},
                    {"action": "💬 基本的なコミュニケーションを維持", "points": 1},
                    {"action": "📝 議事録や記録を正確に作成", "points": 1},
                    {"action": "👥 メンバーとの関係を良好に保つ", "points": 1},
                    {"action": "🎯 与えられた目標を着実に追求", "points": 1},
                    {"action": "📚 マニュアルに従った管理を実施", "points": 1},
                    {"action": "🔄 ルーティンワークを確実に遂行", "points": 1},
                    {"action": "😐 感情を表に出さず冷静に対応", "points": 1}
                ],
                "poor": [
                    {"action": "😰 重要な場面で決断できず", "points": -1},
                    {"action": "💔 チームの意見をまとめられず", "points": -1},
                    {"action": "🌀 方針がコロコロ変わり混乱を招く", "points": -1},
                    {"action": "😡 感情的になってチームの雰囲気悪化", "points": -1},
                    {"action": "🙈 責任逃れをして部下に押し付け", "points": -1},
                    {"action": "💤 やる気がなく部下のモチベーション低下", "points": -1},
                    {"action": "📱 会議中にスマホで部下から不信感", "points": -1},
                    {"action": "🎭 嘘をついてチームの信頼失墜", "points": -1},
                    {"action": "💥 パワハラで大問題に発展", "points": -1},
                    {"action": "🔥 炎上案件を作り出して責任問題", "points": -1},
                    {"action": "💸 予算管理を怠り大幅赤字", "points": -1},
                    {"action": "😵 プレッシャーに負けて判断ミス連発", "points": -1},
                    {"action": "🚨 重要な情報を共有せず大トラブル", "points": -1},
                    {"action": "👹 独裁的な態度で部下が次々離職", "points": -1},
                    {"action": "💀 致命的な判断ミスで会社に大損害", "points": -1}
                ]
            }
        }
        
        patterns = performance_patterns.get(challenge_title, {
            "excellent": [{"action": "🌟 素晴らしい活躍", "points": 3}],
            "good": [{"action": "💪 良い働き", "points": 2}],
            "average": [{"action": "😊 普通の貢献", "points": 1}],
            "poor": [{"action": "😅 うまくいかず", "points": -1}]
        })
        
        # このラウンドで使用済みのアクションを追跡
        used_actions = set()
        
        for player in team:
            # ランダムでパフォーマンスレベルを決定（重み付き）
            performance_level = random.choices(
                ["excellent", "good", "average", "poor"],
                weights=[15, 40, 35, 10]  # excellent: 15%, good: 40%, average: 35%, poor: 10%
            )[0]
            
            # 使用済みでないアクションを選択
            available_actions = [p for p in patterns[performance_level] if p["action"] not in used_actions]
            
            # 利用可能なアクションがない場合は全体から選択
            if not available_actions:
                available_actions = patterns[performance_level]
            
            performance = random.choice(available_actions)
            used_actions.add(performance["action"])
            
            # 得点にランダム要素を追加（同一レベルでも差をつける）
            base_points = performance["points"]
            if performance_level == "excellent":
                bonus = random.choice([0, 0, 0, 1])  # 25%の確率で+1
            elif performance_level == "good":
                bonus = random.choice([-1, 0, 0, 0, 0, 1])  # 微細な調整
            elif performance_level == "average":
                bonus = random.choice([-1, 0, 0, 0, 1])  # 微細な調整
            else:  # poor
                bonus = random.choice([-1, 0, 0, 0])  # 25%の確率で-1
            
            final_points = max(-2, min(4, base_points + bonus))  # -2から4の範囲でクリップ
            
            results.append({
                "player": player,
                "action": performance["action"],
                "points": final_points,
                "level": performance_level
            })
        
        return results
    
    def format_team_results(self, results, total_score):
        """チーム結果を整形"""
        formatted = []
        
        for result in results:
            emoji = {
                "excellent": "🌟",
                "good": "✨", 
                "average": "💪",
                "poor": "😅"
            }.get(result["level"], "💫")
            
            points_text = f"(+{result['points']}pt)" if result['points'] >= 0 else f"({result['points']}pt)"
            formatted.append(f"{emoji} {result['player'].display_name}: {result['action']} {points_text}")
        
        return "\n".join(formatted)
    
    async def announce_mvp(self, channel, all_players_scores):
        """MVP表彰を行う"""
        if not all_players_scores:
            return
        
        # 累計得点でソート
        sorted_players = sorted(
            all_players_scores.values(), 
            key=lambda x: x["total_points"], 
            reverse=True
        )
        
        # 最高得点を取得
        max_points = sorted_players[0]["total_points"]
        
        # 同点の場合は複数MVP
        mvp_players = [p for p in sorted_players if p["total_points"] == max_points]
        
        if len(mvp_players) == 1:
            # 単独MVP
            mvp = mvp_players[0]
            mvp_embed = discord.Embed(
                title="🏅 MVP (Most Valuable Player) 🏅",
                description=f"**最優秀選手賞**\n最も活躍したプレイヤーを表彰します！",
                color=discord.Color.gold()
            )
            
            mvp_embed.add_field(
                name="🌟 MVP受賞者",
                value=f"{mvp['player'].mention}\n**累計得点: {mvp['total_points']}pt**",
                inline=False
            )
            
            mvp_embed.add_field(
                name="🎉 受賞理由",
                value="全4ラウンドを通じて最も安定した高いパフォーマンスを発揮！\n素晴らしいスキルと判断力でチームに貢献しました！",
                inline=False
            )
            
            special_msg = f"🎊✨ {mvp['player'].mention} さん、MVP受賞おめでとうございます！✨🎊\nあなたの活躍は皆の目標です！"
            
        else:
            # 複数MVP（同点）
            mvp_mentions = " ".join(p["player"].mention for p in mvp_players)
            
            mvp_embed = discord.Embed(
                title="🏅 MVP (Most Valuable Player) 🏅",
                description=f"**最優秀選手賞（同点受賞）**\n素晴らしい接戦でした！",
                color=discord.Color.gold()
            )
            
            mvp_embed.add_field(
                name="🌟 MVP受賞者",
                value=f"{mvp_mentions}\n**累計得点: {max_points}pt**",
                inline=False
            )
            
            mvp_embed.add_field(
                name="🎉 受賞理由",
                value="同点という素晴らしい競争！\n全員が最高のパフォーマンスを発揮しました！",
                inline=False
            )
            
            special_msg = f"🎊✨ {mvp_mentions}\n同点MVP受賞おめでとうございます！✨🎊\n互いを高め合う素晴らしい戦いでした！"
        
        # その他の順位も表示
        ranking_text = ""
        for i, player_data in enumerate(sorted_players[:5], 1):  # TOP5まで表示
            if i == 1:
                if len(mvp_players) == 1:
                    continue  # 単独MVPは既に表示済み
                else:
                    ranking_text += f"🥇 1位: {player_data['player'].display_name} ({player_data['total_points']}pt)\n"
            elif i == 2:
                ranking_text += f"🥈 2位: {player_data['player'].display_name} ({player_data['total_points']}pt)\n"
            elif i == 3:
                ranking_text += f"🥉 3位: {player_data['player'].display_name} ({player_data['total_points']}pt)\n"
            else:
                ranking_text += f"🏆 {i}位: {player_data['player'].display_name} ({player_data['total_points']}pt)\n"
        
        if ranking_text:
            mvp_embed.add_field(
                name="📊 個人成績ランキング",
                value=ranking_text,
                inline=False
            )
        
        await channel.send(embed=mvp_embed)
        await channel.send(special_msg)
        
        # ゲーム終了処理（重要！）
        rumble_cog = self.get_cog_instance(channel)
        if rumble_cog:
            guild_id = None
            for gid, active_game in list(rumble_cog.active_games.items()):
                if hasattr(active_game, 'players') and active_game.players == self.game.players:
                    guild_id = gid
                    break
            
            if guild_id:
                del rumble_cog.active_games[guild_id]
                print(f"ランブルゲーム終了: Guild ID {guild_id}")
    
    def get_cog_instance(self, channel):
        """RumbleCogインスタンスを取得"""
        for guild in channel.client.guilds:
            if guild == channel.guild:
                return channel.client.get_cog('RumbleCog')
        return None


class AdminRumbleView(RumbleView):
    def __init__(self, game: RumbleGame, main_view: RumbleView):
        super().__init__(game, main_view.admin_id)
        self.main_view = main_view
    
    @discord.ui.button(label="準備完了", style=discord.ButtonStyle.success, emoji="✅")
    async def ready_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 参加者全員を準備完了にする
        for player in self.game.players.keys():
            if player not in self.game.ready_players:
                self.game.ready_players.append(player)
        
        await interaction.response.send_message(
            "全員を準備完了状態にしました",
            ephemeral=True
        )
        
        # メインの埋め込みを更新
        await self.main_view.update_embed_from_admin()
        
        # 全員準備完了したら自動開始
        if self.game.can_start():
            await self.main_view.start_game_from_admin()
    
    @discord.ui.button(label="テストユーザー追加", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def add_dummy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ダミーユーザーを作成
        class DummyUser:
            def __init__(self, user_id, name):
                self.id = user_id
                self.display_name = name
                self.mention = f"@{name}"
        
        dummy_names = ["テストユーザー1", "テストユーザー2", "テストユーザー3", "テストユーザー4"]
        added_count = 0
        
        for i, name in enumerate(dummy_names):
            dummy_user = DummyUser(f"dummy_{i}", name)
            # IDで重複チェック
            if not any(p.id == dummy_user.id for p in self.game.players.keys()):
                if self.game.add_player(dummy_user):
                    self.game.ready_players.append(dummy_user)  # ダミーは自動準備完了
                    added_count += 1
        
        if added_count > 0:
            await interaction.response.send_message(
                f"テストユーザー {added_count}人を追加しました",
                ephemeral=True
            )
            
            # メインの埋め込みを更新
            await self.main_view.update_embed_from_admin()
            
            # 自動開始チェック
            if self.game.can_start():
                await self.main_view.start_game_from_admin()
        else:
            await interaction.response.send_message(
                "すでに十分なテストユーザーが参加しています",
                ephemeral=True
            )

    async def update_embed(self, interaction: discord.Interaction):
        red_team, blue_team = self.game.get_teams()
        
        embed = discord.Embed(
            title="⚔️ ランブルマッチ募集中！",
            description="参加ボタンを押して参加し、準備ができたら準備完了ボタンを押してください",
            color=discord.Color.orange()
        )
        
        # 赤チーム
        red_names = []
        for player in red_team:
            ready = "✅" if player in self.game.ready_players else "⏳"
            red_names.append(f"{ready} {player.display_name}")
        embed.add_field(
            name=f"🔴 赤チーム ({len(red_team)}人)",
            value="\n".join(red_names) if red_names else "募集中...",
            inline=True
        )
        
        # 青チーム
        blue_names = []
        for player in blue_team:
            ready = "✅" if player in self.game.ready_players else "⏳"
            blue_names.append(f"{ready} {player.display_name}")
        embed.add_field(
            name=f"🔵 青チーム ({len(blue_team)}人)",
            value="\n".join(blue_names) if blue_names else "募集中...",
            inline=True
        )
        
        # ステータス
        if self.game.can_start():
            embed.add_field(
                name="ステータス",
                value="✅ 開始可能！",
                inline=False
            )
        else:
            conditions = []
            if len(self.game.ready_players) < len(self.game.players):
                conditions.append("全員が準備完了する")
            if len(self.game.players) < 2:
                conditions.append("最低2人必要")
            
            embed.add_field(
                name="開始条件",
                value="\n".join(f"❌ {c}" for c in conditions),
                inline=False
            )
    
    async def update_embed_from_admin(self):
        """管理者操作によるEmbed更新"""
        if hasattr(self, 'last_interaction') and self.last_interaction:
            await self.update_embed(self.last_interaction)
    
    async def start_game_from_admin(self):
        """管理者操作によるゲーム開始"""
        if hasattr(self, 'last_interaction') and self.last_interaction:
            await self.start_game(self.last_interaction)
        
    
    async def start_game(self, interaction: discord.Interaction):
        self.game.in_progress = True
        
        # ボタンを無効化
        for item in self.children:
            item.disabled = True
        
        await interaction.edit_original_response(view=self)
        
        red_team, blue_team = self.game.get_teams()
        
        # チャレンジ開始エンベッド
        embed = discord.Embed(
            title="🎯 ZERO to ONE チャレンジ開始！",
            description="キャリア成長バトルが始まります！各ラウンドで様々な挑戦が待っています！",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔥 チャレンジャーズ",
            value="\n".join(p.display_name for p in red_team),
            inline=True
        )
        embed.add_field(
            name="💼 ビジネスチーム",
            value="\n".join(p.display_name for p in blue_team),
            inline=True
        )
        
        await interaction.channel.send(embed=embed)
        
        # ラウンド制バトル実行
        await self.run_career_rounds(interaction.channel, red_team, blue_team)
    
    async def run_career_rounds(self, channel, red_team, blue_team):
        """キャリア成長ラウンド制バトル"""
        
        # チームスコア初期化
        red_score = 0
        blue_score = 0
        
        career_challenges = [
            {
                "title": "📊 ビジネス企画力チャレンジ",
                "scenarios": [
                    "新サービスのアイデアを5分で考案！", 
                    "競合分析をサクッと実施！",
                    "マーケティング戦略を立案！",
                    "投資家向けピッチ資料を作成！",
                    "市場調査結果から新商品を企画！",
                    "ユーザーペルソナを設定してサービス改善！",
                    "収益モデルを構築して事業計画を立案！",
                    "ブランディング戦略で差別化を図る！",
                    "データ分析から次の施策を決定！",
                    "SNSマーケティングで認知度アップ！",
                    "スタートアップのビジネスモデルを構築！",
                    "サブスクリプション型サービスを企画！",
                    "BtoBサービスの営業戦略を考案！",
                    "海外展開のロードマップを作成！",
                    "DX推進プロジェクトを立案！",
                    "新規事業の採算性を計算！",
                    "クラウドファンディングの企画を作成！",
                    "フリーミアムモデルの戦略を構築！",
                    "アフィリエイトマーケティング戦略を考案！",
                    "インフルエンサーマーケティングを企画！",
                    "オムニチャネル戦略を設計！",
                    "カスタマージャーニーマップを作成！",
                    "価格戦略とポジショニングを決定！",
                    "プロダクトマーケットフィットを検証！",
                    "リーンスタートアップ手法で事業検証！"
                ]
            },
            {
                "title": "🤝 コミュニケーション力チャレンジ", 
                "scenarios": [
                    "クライアントとの交渉を成功させろ！",
                    "チームの士気を上げるスピーチ！",
                    "困っている同僚をサポート！",
                    "厳しいクレーム対応を円満解決！",
                    "上司を説得して新企画を承認してもらう！",
                    "チーム内の対立を仲裁して解決！",
                    "プレゼンで投資家の心を掴む！",
                    "多様な価値観のメンバーをまとめる！",
                    "リモートワークチームの結束を高める！",
                    "顧客の真のニーズを聞き出す！",
                    "部下のモチベーション低下を解決！",
                    "異文化チームでの意思疎通を円滑化！",
                    "ステークホルダーとの利害調整！",
                    "緊急事態での冷静な情報伝達！",
                    "パワハラ問題を適切に対処！",
                    "世代間ギャップを埋めるコミュニケーション！",
                    "オンライン会議での効果的なファシリテート！",
                    "炎上した企画を関係者に説明！",
                    "海外クライアントとの文化の壁を越える！",
                    "メディア対応でブランドイメージを守る！",
                    "労働組合との交渉を成功させる！",
                    "転職を考える優秀な部下を引き留める！",
                    "新卒採用の面接で人材を見極める！",
                    "退職する社員との円満な引き継ぎ！",
                    "取引先との長期パートナーシップを構築！"
                ]
            },
            {
                "title": "💡 問題解決力チャレンジ",
                "scenarios": [
                    "システムトラブルを迅速に解決！",
                    "予算不足の課題をクリア！", 
                    "納期遅れをリカバリー！",
                    "売上急降下の原因を特定して改善！",
                    "人手不足を効率化で乗り切る！",
                    "競合他社の追い上げに対抗策を考案！",
                    "品質問題を根本から解決！",
                    "コスト削減しながら品質維持！",
                    "新型ウイルス対応で事業継続！",
                    "炎上案件を鎮静化させる！",
                    "データ漏洩事故の緊急対応！",
                    "工場の生産ライン停止を復旧！",
                    "サプライチェーン断絶への対策！",
                    "キーパーソンの突然の退職をカバー！",
                    "法規制変更への緊急対応！",
                    "自然災害でのBCP発動！",
                    "ハッキング被害からの復旧！",
                    "在庫過多による資金繰り悪化を解決！",
                    "特許侵害問題への対処！",
                    "労働基準法違反の改善！",
                    "環境問題への企業対応！",
                    "AI導入による業務効率化！",
                    "レガシーシステムの刷新計画！",
                    "リモートワーク環境の最適化！",
                    "セキュリティホールの緊急パッチ対応！"
                ]
            },
            {
                "title": "🚀 リーダーシップチャレンジ",
                "scenarios": [
                    "新プロジェクトを成功に導け！",
                    "チームの方向性を決定！",
                    "困難な決断を下す時！",
                    "組織改革を推進してチームを変革！",
                    "失敗から立ち直るチームを鼓舞！",
                    "多国籍チームの文化の違いを乗り越える！",
                    "限られた時間で最大の成果を出す！",
                    "新人メンバーを一人前に育成！",
                    "ベテラン社員のモチベーションを復活！",
                    "会社の危機を乗り越える決断！",
                    "大規模リストラの実行と組織再建！",
                    "M&A後の企業統合をリード！",
                    "新市場参入の陣頭指揮！",
                    "デジタルトランスフォーメーションを主導！",
                    "企業文化改革プロジェクトを牽引！",
                    "グローバル展開戦略の実行！",
                    "イノベーション創出のための組織作り！",
                    "危機的な業績を黒字転換！",
                    "次世代リーダーの育成システム構築！",
                    "ダイバーシティ推進の組織変革！",
                    "サステナビリティ経営への転換！",
                    "アジャイル組織への変革！",
                    "データドリブン経営の導入！",
                    "カスタマーファーストの組織作り！",
                    "スタートアップ買収後の統合管理！"
                ]
            }
        ]
        
        round_num = 1
        all_players_scores = {}  # プレイヤーごとの累計得点を記録
        
        for challenge in career_challenges:
            await asyncio.sleep(20)  # 20秒間隔
            
            # ラウンド開始アナウンス
            scenario = random.choice(challenge["scenarios"])
            
            round_start_embed = discord.Embed(
                title=f"📋 Round {round_num}: {challenge['title']}",
                description=f"**チャレンジ:** {scenario}",
                color=discord.Color.orange()
            )
            await channel.send(embed=round_start_embed)
            
            # 各プレイヤーの個別パフォーマンスを計算
            red_results = self.calculate_individual_performance(red_team, challenge["title"])
            blue_results = self.calculate_individual_performance(blue_team, challenge["title"])
            
            # チームごとの合計得点を計算
            red_round_score = sum(result["points"] for result in red_results)
            blue_round_score = sum(result["points"] for result in blue_results)
            
            # 個人累計得点を記録
            for result in red_results + blue_results:
                player_id = str(result["player"].id)
                if player_id not in all_players_scores:
                    all_players_scores[player_id] = {"player": result["player"], "total_points": 0}
                all_players_scores[player_id]["total_points"] += result["points"]
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 先攻チーム（チャレンジャーズ）の結果
            red_details = self.format_team_results(red_results, red_round_score)
            red_embed = discord.Embed(
                title=f"🔥 チャレンジャーズ (合計: {red_round_score}pt)",
                description=red_details,
                color=discord.Color.red()
            )
            await channel.send(embed=red_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 後攻チーム（ビジネスチーム）の結果
            blue_details = self.format_team_results(blue_results, blue_round_score)
            blue_embed = discord.Embed(
                title=f"💼 ビジネスチーム (合計: {blue_round_score}pt)",
                description=blue_details,
                color=discord.Color.blue()
            )
            await channel.send(embed=blue_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # ラウンド勝者決定と現在のスコア
            if red_round_score > blue_round_score:
                red_score += 1
                team_name = "🔥 チャレンジャーズ"
                result_msg = f"合計 {red_round_score}pt で勝利！"
            elif blue_round_score > red_round_score:
                blue_score += 1
                team_name = "💼 ビジネスチーム"
                result_msg = f"合計 {blue_round_score}pt で勝利！"
            else:
                team_name = "引き分け"
                result_msg = f"両チーム {red_round_score}pt で同点！"
            
            result_embed = discord.Embed(
                title="🏆 ラウンド結果",
                color=discord.Color.gold()
            )
            result_embed.add_field(
                name="勝者",
                value=f"{team_name}\n✨ {result_msg}",
                inline=False
            )
            result_embed.add_field(
                name="📈 現在のスコア",
                value=f"🔥 チャレンジャーズ: {red_score}点\n💼 ビジネスチーム: {blue_score}点",
                inline=False
            )
            
            await channel.send(embed=result_embed)
            round_num += 1
        
        # 最終結果発表
        await asyncio.sleep(2)
        
        if red_score > blue_score:
            final_winners = red_team
            final_losers = blue_team
            winner_name = "🔥 チャレンジャーズ"
            winner_message = "新しい発想と柔軟性で勝利！"
        elif blue_score > red_score:
            final_winners = blue_team
            final_losers = red_team
            winner_name = "💼 ビジネスチーム"
            winner_message = "経験と戦略で勝利！"
        else:
            # 引き分けの場合
            final_embed = discord.Embed(
                title="🤝 ZERO to ONE チャレンジ結果",
                description="**素晴らしい！引き分けです！**\n両チームとも成長の証！",
                color=discord.Color.gold()
            )
            final_embed.add_field(
                name="🎉 結果",
                value="お互いの強みを認め合える素晴らしいバトルでした！\n全員がキャリア成長の階段を一歩上がりました！",
                inline=False
            )
            await channel.send(embed=final_embed)
            return
        
        # 勝者発表（メンション付きで盛り上げ）
        final_embed = discord.Embed(
            title="🎉 ZERO to ONE チャレンジ結果",
            description=f"**{winner_name} の勝利！**\n{winner_message}",
            color=discord.Color.gold()
        )
        
        # メンション付きで勝者チーム表示
        winner_mentions = " ".join(p.mention for p in final_winners)
        loser_mentions = " ".join(p.mention for p in final_losers)
        
        final_embed.add_field(
            name="🏆 優勝チーム",
            value=winner_mentions,
            inline=False
        )
        
        final_embed.add_field(
            name="📊 最終スコア",
            value=f"🔥 チャレンジャーズ: {red_score}点\n💼 ビジネスチーム: {blue_score}点",
            inline=False
        )
        
        final_embed.add_field(
            name="💝 成長ポイント",
            value="全参加者がキャリアスキルを磨きました！\n次回もぜひ挑戦してくださいね！",
            inline=False
        )
        
        # 勝者への特別メッセージ
        celebration_msg = f"🎊 おめでとうございます！ {winner_mentions}\n素晴らしいチームワークでした！"
        
        await channel.send(embed=final_embed)
        await channel.send(celebration_msg)
        
        # MVP表彰
        await asyncio.sleep(3)
        await self.announce_mvp(channel, all_players_scores)
    
    
    def get_cog_instance(self, channel):
        """RumbleCogインスタンスを取得"""
        for guild in channel.client.guilds:
            if guild == channel.guild:
                return channel.client.get_cog('RumbleCog')
        return None

class RumbleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games: Dict[int, RumbleGame] = {}  # guild_id: game
    
    @discord.app_commands.command(name='rumble', description='ランブルマッチの募集を開始')
    async def start_rumble(self, interaction: discord.Interaction, time_limit: int = 60):
        """ランブルマッチの募集を開始（管理者・特定ロールのみ）"""
        
        # 権限チェック
        allowed_role_ids = {1236487195741913119, 1236433752851349656}  # 運営、もう一つのロール
        user_role_ids = {role.id for role in interaction.user.roles}
        
        if not (interaction.user.guild_permissions.administrator or user_role_ids & allowed_role_ids):
            await interaction.response.send_message("❌ このコマンドは管理者または特定のロールのみ使用できます。", ephemeral=True)
            return
        ctx = interaction
        if interaction.guild.id in self.active_games:
            await interaction.response.send_message("すでにランブルが進行中です")
            return
        
        game = RumbleGame()
        game.channel = interaction.channel
        game.time_limit = time_limit
        game.start_time = datetime.datetime.now()
        self.active_games[interaction.guild.id] = game
        
        embed = discord.Embed(
            title="⚔️ ランブルマッチ募集中！",
            description=f"参加ボタンを押して参加してください\n募集時間: {time_limit}秒",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="🔴 赤チーム (0人)",
            value="募集中...",
            inline=True
        )
        embed.add_field(
            name="🔵 青チーム (0人)",
            value="募集中...",
            inline=True
        )
        embed.add_field(
            name="開始条件",
            value="❌ 最低2人必要\n❌ 全員が準備完了する",
            inline=False
        )
        
        from config.config import ADMIN_ID
        view = RumbleView(game, ADMIN_ID)
        view.last_interaction = interaction  # 後で更新用に保存
        
        await interaction.response.send_message(embed=embed, view=view)
        
        # 管理者にプライベートで管理ボタンを送信
        admin_view = AdminRumbleView(game, view)
        await interaction.followup.send(
            "🔧 **管理者専用コントロール**\nランブルの管理を行えます。",
            view=admin_view,
            ephemeral=True
        )
        
        # 非同期で時間制限処理（バックグラウンド実行）
        asyncio.create_task(self._handle_time_limit(interaction, game, time_limit))
    
    async def _handle_time_limit(self, interaction, game, time_limit):
        """時間制限処理（バックグラウンド実行）"""
        await asyncio.sleep(time_limit)
        
        # ゲームがまだ存在し、開始されていない場合
        if (interaction.guild.id in self.active_games and 
            not game.in_progress and 
            self.active_games[interaction.guild.id] == game):
            
            if len(game.players) >= 2:
                # 全員を準備完了にして開始
                for player in game.players.keys():
                    if player not in game.ready_players:
                        game.ready_players.append(player)
                
                # ゲーム開始
                await self.auto_start_game(interaction.channel, game)
            else:
                # 参加者不足で終了
                del self.active_games[interaction.guild.id]
                try:
                    await interaction.followup.send("参加者が不足のため、ランブル募集を終了しました")
                except:
                    await interaction.channel.send("参加者が不足のため、ランブル募集を終了しました")
    
    async def auto_start_game(self, channel, game):
        """時間切れ時の自動ゲーム開始"""
        game.in_progress = True
        
        red_team, blue_team = game.get_teams()
        
        # バトル開始エンベッド
        embed = discord.Embed(
            title="⚔️ 時間切れ！ランブルマッチ開始！",
            description="募集時間が終了したため、バトルが始まります！",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🔴 赤チーム",
            value="\n".join(p.display_name for p in red_team),
            inline=True
        )
        embed.add_field(
            name="🔵 青チーム",
            value="\n".join(p.display_name for p in blue_team),
            inline=True
        )
        
        await channel.send(embed=embed)
        
        # バトル実行
        await self._execute_battle(channel, game, red_team, blue_team)
    
    async def _execute_battle(self, channel, game, red_team, blue_team):
        """バトル実行とゲーム終了処理"""
        # バトルシミュレーション（より詳細な演出）
        battle_events = [
            "⚡ 激しい攻防が始まった！",
            "🔥 赤チームが攻勢に出る！",
            "🌊 青チームが反撃！",
            "💥 両チーム一歩も譲らず！",
            "⭐ 決定的な瞬間が訪れる！"
        ]
        
        for i, event in enumerate(battle_events):
            await asyncio.sleep(3)  # 3秒間隔
            battle_embed = discord.Embed(
                title="⚔️ バトル進行中...",
                description=event,
                color=discord.Color.orange()
            )
            await channel.send(embed=battle_embed)
        
        # 最終待機
        await asyncio.sleep(2)
        
        # ランダムに勝者を決定
        winner_team = random.choice(['red', 'blue'])
        winners = red_team if winner_team == 'red' else blue_team
        losers = blue_team if winner_team == 'red' else red_team
        
        # 結果発表
        result_embed = discord.Embed(
            title="🏆 バトル終了！",
            description=f"{'🔴 赤' if winner_team == 'red' else '🔵 青'}チームの勝利！",
            color=discord.Color.gold()
        )
        result_embed.add_field(
            name="🏆 勝者",
            value="\n".join(p.mention for p in winners),
            inline=True
        )
        result_embed.add_field(
            name="💀 敗者",
            value="\n".join(p.mention for p in losers),
            inline=True
        )
        
        await channel.send(embed=result_embed)
        
        # ゲーム終了処理（重要！）
        await self._cleanup_game(game)
    
    async def _cleanup_game(self, game):
        """ゲーム終了処理"""
        guild_id = None
        for gid, active_game in list(self.active_games.items()):
            if active_game == game:
                guild_id = gid
                break
        
        if guild_id:
            del self.active_games[guild_id]
            print(f"ランブルゲーム終了: Guild ID {guild_id}")

async def setup(bot):
    await bot.add_cog(RumbleCog(bot))