# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
import asyncio
import random
import datetime
from typing import Dict, List, Optional
from .rumble_data import CAREER_CHALLENGES, PERFORMANCE_PATTERNS

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
        # 表示メンバー管理用
        self.displayed_members = {"red": set(), "blue": set()}
        self.round_count = 0
    
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
        await RumbleView.run_career_rounds(interaction.channel, red_team, blue_team)
    
    @staticmethod
    async def run_career_rounds(channel, red_team, blue_team):
        """キャリア成長ラウンド制バトル"""
        
        # チームスコア初期化
        red_score = 0
        blue_score = 0
        
        career_challenges = CAREER_CHALLENGES
        
        round_num = 1
        all_players_scores = {}  # プレイヤーごとの累計得点を記録
        displayed_members = {"red": set(), "blue": set()}  # 表示履歴管理
        
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
            red_results = RumbleView.calculate_individual_performance(red_team, challenge["title"])
            blue_results = RumbleView.calculate_individual_performance(blue_team, challenge["title"])
            
            # チームごとの実績スコア(Avarage)を計算（平均点）
            red_total_points = sum(result["points"] for result in red_results)
            blue_total_points = sum(result["points"] for result in blue_results)
            red_round_score = round(red_total_points / len(red_team), 1) if red_team else 0
            blue_round_score = round(blue_total_points / len(blue_team), 1) if blue_team else 0
            
            # 個人累計得点を記録
            for result in red_results + blue_results:
                player_id = str(result["player"].id)
                if player_id not in all_players_scores:
                    all_players_scores[player_id] = {"player": result["player"], "total_points": 0}
                    print(f"DEBUG: New player added - {result['player'].display_name} (ID: {player_id})")
                all_players_scores[player_id]["total_points"] += result["points"]
                print(f"DEBUG: {result['player'].display_name} scored {result['points']}pt, total: {all_players_scores[player_id]['total_points']}pt")
            
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 表示するメンバーを選出
            red_display = RumbleView.select_display_members(red_team, "red", red_results, displayed_members)
            blue_display = RumbleView.select_display_members(blue_team, "blue", blue_results, displayed_members)
            
            # 先攻チーム（チャレンジャーズ）の結果
            red_details = RumbleView.format_team_results(red_display, red_total_points)
            team_info = f"(全{len(red_team)}人中{len(red_display)}人表示)" if len(red_team) > 10 else ""
            red_embed = discord.Embed(
                title=f"🔥 チャレンジャーズ {team_info} (チーム実績スコア: {red_round_score})",
                description=red_details,
                color=discord.Color.red()
            )
            await channel.send(embed=red_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # 後攻チーム（ビジネスチーム）の結果
            blue_details = RumbleView.format_team_results(blue_display, blue_total_points)
            team_info = f"(全{len(blue_team)}人中{len(blue_display)}人表示)" if len(blue_team) > 10 else ""
            blue_embed = discord.Embed(
                title=f"💼 ビジネスチーム {team_info} (チーム実績スコア: {blue_round_score})",
                description=blue_details,
                color=discord.Color.blue()
            )
            await channel.send(embed=blue_embed)
            
            await asyncio.sleep(2)  # 少し間を置く
            
            # ラウンド勝者決定と現在のスコア
            if red_round_score > blue_round_score:
                red_score += 1
                team_name = "🔥 チャレンジャーズ"
                result_msg = f"チーム実績スコア(Avarage) {red_round_score} で勝利！"
            elif blue_round_score > red_round_score:
                blue_score += 1
                team_name = "💼 ビジネスチーム"
                result_msg = f"チーム実績スコア(Avarage) {blue_round_score} で勝利！"
            else:
                team_name = "引き分け"
                result_msg = f"両チーム実績スコア(Avarage) {red_round_score} で同点！"
            
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
                value=f"🔥 チャレンジャーズ: {red_score}WIN\n💼 ビジネスチーム: {blue_score}WIN",
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
            value=f"🔥 チャレンジャーズ: {red_score}WIN\n💼 ビジネスチーム: {blue_score}WIN",
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
        await RumbleView.announce_mvp(channel, all_players_scores)
        
        # ゲーム終了処理は静的メソッドでは実行できないため、コメントアウト
        # rumble_cog = self.get_cog_instance(channel)
        # if rumble_cog:
        #     guild_id = None
        #     for gid, active_game in list(rumble_cog.active_games.items()):
        #         if hasattr(active_game, 'players') and active_game.players == self.game.players:
        #             guild_id = gid
        #             break
        #     
        #     if guild_id:
        #         del rumble_cog.active_games[guild_id]
        #         print(f"ランブルゲーム終了: Guild ID {guild_id}")
    
    @staticmethod
    def select_display_members(team, team_color, results, displayed_members):
        """表示するメンバーを選出（最大10人、全員が1回は表示されるように）"""
        if len(team) <= 10:
            return results  # 10人以下なら全員表示
        
        # 未表示のメンバーを優先
        undisplayed = [r for r in results if r["player"] not in displayed_members[team_color]]
        displayed = [r for r in results if r["player"] in displayed_members[team_color]]
        
        # 未表示が10人以上いる場合は、そこからランダム選出
        if len(undisplayed) >= 10:
            selected = random.sample(undisplayed, 10)
        else:
            # 未表示を全部 + 既表示からランダム補完
            need_more = 10 - len(undisplayed)
            if need_more > 0 and displayed:
                additional = random.sample(displayed, min(need_more, len(displayed)))
                selected = undisplayed + additional
            else:
                selected = undisplayed
        
        # 表示履歴を更新
        for result in selected:
            displayed_members[team_color].add(result["player"])
        
        return selected

    @staticmethod
    def calculate_individual_performance(team, challenge_title):
        """各プレイヤーの個別パフォーマンスと得点を計算"""
        results = []
        
        # チャレンジ別のパフォーマンスパターン（大幅に拡張）
        performance_patterns = PERFORMANCE_PATTERNS
        
        # 各プレイヤーの結果を計算
        for player in team:
            # チャレンジに対応するパフォーマンスパターンを取得
            if challenge_title in performance_patterns:
                patterns = performance_patterns[challenge_title]
            else:
                # デフォルトパターン
                patterns = performance_patterns["📊 ビジネス企画力チャレンジ"]
            
            # ランダムでパフォーマンスレベルを決定（重み付き）
            # excellent: 10%, good: 40%, average: 40%, poor: 10%
            rand = random.random()
            if rand < 0.1:
                performance_level = "excellent"
            elif rand < 0.5:
                performance_level = "good"
            elif rand < 0.9:
                performance_level = "average"
            else:
                performance_level = "poor"
            
            # 該当レベルからランダムにパフォーマンスを選択
            performance = random.choice(patterns[performance_level])
            
            # 基本得点
            base_points = performance["points"]
            
            # プレイヤー固有のボーナス（ランダム要素を追加）
            # -1から+1のランダムボーナス
            bonus = random.randint(-1, 1)
            
            # 最終得点を計算（-2から4の範囲でクリップ）
            final_points = max(-2, min(4, base_points + bonus))  # -2から4の範囲でクリップ
            
            results.append({
                "player": player,
                "action": performance["action"],
                "points": final_points,
                "level": performance_level
            })
        
        return results
    
    @staticmethod
    def format_team_results(results, total_score):
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
    
    @staticmethod
    async def announce_mvp(channel, all_players_scores):
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
                value="全6ラウンドを通じて最も安定した高いパフォーマンスを発揮！\n素晴らしいスキルと判断力でチームに貢献しました！",
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
    
    def get_cog_instance(self, channel):
        """RumbleCogインスタンスを取得"""
        # Botインスタンスを取得してRumbleCogを返す
        bot = channel.guild._state._get_client()
        return bot.get_cog('RumbleCog')


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
        await self.main_view.update_embed(interaction)
        
        # 全員準備完了したら自動開始
        if self.game.can_start():
            await self.main_view.start_game(interaction)
    
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
            await self.main_view.update_embed(interaction)
            
            # 自動開始チェック
            if self.game.can_start():
                await self.main_view.start_game(interaction)
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
        await RumbleView.run_career_rounds(interaction.channel, red_team, blue_team)
    
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
            title="⚔️ レディ！！ランブルマッチ開始！",
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
        
        # キャリア成長ラウンド制バトル実行
        await RumbleView.run_career_rounds(channel, red_team, blue_team)
        
        # ゲーム終了処理
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