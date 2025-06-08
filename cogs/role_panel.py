# -*- coding:utf-8 -*-
import discord
from discord.ext import commands
from config.config import ADMIN_ID

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        self.role = role
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role.id}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            if self.role in user.roles:
                await user.remove_roles(self.role)
                await interaction.response.send_message(
                    f"❌ **{self.role.name}** ロールを削除しました", 
                    ephemeral=True
                )
            else:
                await user.add_roles(self.role)
                await interaction.response.send_message(
                    f"✅ **{self.role.name}** ロールを付与しました", 
                    ephemeral=True
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"⚠️ **{self.role.name}** ロールの付与権限がありません", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ エラーが発生しました: {str(e)}", 
                ephemeral=True
            )

class RolePanel(discord.ui.View):
    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=None)
        for role in roles[:25]:  # Discord UIは最大25個のボタン
            self.add_item(RoleButton(role))

class RolePanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # オートコンプリート機能（一時的にコメントアウト）
    # async def role_autocomplete(self, interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    #     """ロール名のオートコンプリート"""
    #     # @everyoneとボットロールを除外
    #     roles = [role for role in interaction.guild.roles 
    #             if role.name != "@everyone" and not role.managed]
    #     
    #     # 位置順でソート（高い位置から）
    #     roles.sort(key=lambda r: r.position, reverse=True)
    #     
    #     # Discordの制限に合わせて最初の25個を返す
    #     choices = []
    #     for role in roles[:25]:
    #         choices.append(
    #             discord.app_commands.Choice(
    #                 name=f"{role.name} (位置: {role.position})",
    #                 value=role.name
    #             )
    #         )
    #     
    #     return choices
    
    def find_role_fuzzy(self, guild: discord.Guild, role_name: str) -> discord.Role:
        """あいまいロール検索（@メンション対応・部分一致・大文字小文字無視）"""
        role_name = role_name.strip()
        
        # @メンション形式の処理
        if role_name.startswith('<@&') and role_name.endswith('>'):
            # <@&123456789> 形式からIDを抽出
            try:
                role_id = int(role_name[3:-1])
                role_by_id = guild.get_role(role_id)
                if role_by_id:
                    return role_by_id
            except ValueError:
                pass
        
        role_name_lower = role_name.lower()
        
        # 1. 完全一致
        exact_match = discord.utils.get(guild.roles, name=role_name)
        if exact_match:
            return exact_match
        
        # 2. 大文字小文字無視で完全一致
        case_insensitive = discord.utils.find(
            lambda r: r.name.lower() == role_name_lower, guild.roles
        )
        if case_insensitive:
            return case_insensitive
        
        # 3. 部分一致（ロール名に検索ワードが含まれる）
        partial_match = discord.utils.find(
            lambda r: role_name_lower in r.name.lower(), guild.roles
        )
        return partial_match
    
    @discord.app_commands.command(name='rolelist', description='サーバー内のロール一覧を表示')
    async def list_roles(self, interaction: discord.Interaction):
        """サーバー内のロール一覧を表示"""
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        # @everyoneとボットロールを除外
        roles = [role for role in interaction.guild.roles 
                if role.name != "@everyone" and not role.managed]
        
        if not roles:
            await interaction.response.send_message("使用可能なロールがありません", ephemeral=True)
            return
        
        # ロールを位置順でソート（高い位置から）
        roles.sort(key=lambda r: r.position, reverse=True)
        
        embed = discord.Embed(
            title="📝 サーバー内ロール一覧",
            description="ロールパネル作成時に使用できるロール名一覧です",
            color=discord.Color.green()
        )
        
        # ロールをページ別に分割（20個ずつ）
        role_chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]
        
        for i, chunk in enumerate(role_chunks):
            role_list = "\n".join([f"• `{role.name}`" for role in chunk])
            
            if i == 0:
                embed.add_field(
                    name=f"🏆 ロール一覧 ({len(roles)}個)",
                    value=role_list,
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"続き ({i*20+1}-{min((i+1)*20, len(roles))})",
                    value=role_list,
                    inline=False
                )
        
        embed.add_field(
            name="📝 使用例",
            value="`/rolepanel ロール1 ロール2 ロール3`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.app_commands.command(name='rolepanel', description='ロール付与パネルを作成')
    @discord.app_commands.describe(roles='ロール名をスペース区切りで指定 (例: Member VIP Moderator)')
    async def create_role_panel(self, interaction: discord.Interaction, roles: str):
        """ロール付与パネルを作成（改善版）"""
        if str(interaction.user.id) != ADMIN_ID:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます", ephemeral=True)
            return
        
        role_names = roles.split()
        if not role_names:
            await interaction.response.send_message(
                "📝 ロール名を指定してください\n\n"
                "📝 **使用例:**\n"
                "`/rolepanel ロール1 ロール2 ロール3`\n\n"
                "🔍 **ロール一覧を確認:**\n"
                "`/rolelist`", 
                ephemeral=True
            )
            return
        
        # あいまい検索でロールを取得（重複除去）
        role_list = []
        not_found = []
        processed_role_ids = set()  # 重複チェック用
        
        for role_name in role_names:
            role = self.find_role_fuzzy(interaction.guild, role_name)
            if role:
                # 重複チェック
                if role.id not in processed_role_ids:
                    role_list.append(role)
                    processed_role_ids.add(role.id)
                # 重複の場合はスキップ（エラーにしない）
            else:
                not_found.append(role_name)
        
        # ロールが見つからなかった場合のエラー処理
        if not role_list:
            await interaction.response.send_message(
                f"❌ **ロールが見つかりませんでした**\n\n"
                f"🔍 **未発見:** {', '.join(not_found)}\n\n"
                f"📝 **ヒント:**\n"
                f"• `/rolelist` で正確なロール名を確認してください\n"
                f"• @ロール でメンション形式でも指定できます", 
                ephemeral=True
            )
            return
        
        # ユーザーに分かりやすいパネル作成
        embed = discord.Embed(
            title="🔔 通知ロール選択パネル",
            description="以下のボタンをクリックして、受け取りたい通知ロールを選択してください。",
            color=discord.Color.blue()
        )
        
        # 利用可能なロール一覧を表示
        role_descriptions = []
        for role in role_list:
            # ロール名に基づいた説明を生成
            if '通知' in role.name or 'notification' in role.name.lower():
                desc = "🔔 通知を受け取ります"
            elif 'イベント' in role.name or 'event' in role.name.lower():
                desc = "🎉 イベント情報を受け取ります"
            elif '更新' in role.name or 'update' in role.name.lower():
                desc = "🔄 更新情報を受け取ります"
            elif 'ニュース' in role.name or 'news' in role.name.lower():
                desc = "📰 ニュースを受け取ります"
            elif '重要' in role.name or 'important' in role.name.lower():
                desc = "⚠️ 重要なお知らせを受け取ります"
            else:
                desc = "📨 関連する情報を受け取ります"
            
            role_descriptions.append(f"• **{role.name}** - {desc}")
        
        if len(role_descriptions) <= 10:  # 10個以下なら詳細表示
            embed.add_field(
                name="📋 利用可能なロール",
                value="\n".join(role_descriptions),
                inline=False
            )
        else:  # 多すぎる場合は簡略表示
            embed.add_field(
                name="📋 利用可能なロール",
                value=f"{len(role_list)}種類の通知ロールがあります。ボタンをクリックして選択してください。",
                inline=False
            )
        
        embed.add_field(
            name="🔄 使い方",
            value="• ロールを**追加**したい場合：該当ボタンをクリック\n"
                  "• ロールを**削除**したい場合：もう一度同じボタンをクリック\n"
                  "• 複数のロールを同時に持つことも可能です",
            inline=False
        )
        
        embed.set_footer(text="ボタンをクリックすると、個人的な確認メッセージが表示されます。")
        
        # 管理者向けの簡潔な情報
        admin_msg = f"✅ **パネル作成完了** - {len(role_list)}個のロール"
        if not_found:
            admin_msg += f" (未発見: {len(not_found)}個)"
        
        view = RolePanel(role_list)
        
        # ユーザー向けの分かりやすいパネルを送信
        await interaction.response.send_message(embed=embed, view=view)
        
        # 管理者向けの簡潔な確認をephemeralで送信
        await interaction.followup.send(admin_msg, ephemeral=True)
    
    # オートコンプリートを再度有効化する場合は以下のコメントを外してください
    # @create_role_panel.autocomplete('roles')
    # async def role_autocomplete(self, interaction: discord.Interaction, current: str):
    #     """ロール名のオートコンプリート"""
    #     roles = [role for role in interaction.guild.roles 
    #             if role.name != "@everyone" and not role.managed]
    #     roles.sort(key=lambda r: r.position, reverse=True)
    #     
    #     if current:
    #         roles = [r for r in roles if current.lower() in r.name.lower()]
    #     
    #     return [
    #         discord.app_commands.Choice(name=role.name, value=role.name)
    #         for role in roles[:25]
    #     ]

async def setup(bot):
    await bot.add_cog(RolePanelCog(bot))