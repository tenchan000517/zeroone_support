#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord埋め込みメッセージプレビュー
実際にDiscordに表示される内容を詳細に表示
"""

import asyncio
from utils.enhanced_trends_manager import EnhancedTrendsManager

async def show_discord_embed_preview():
    """Discord埋め込みメッセージの詳細プレビュー"""
    print("🎮 Discord埋め込みメッセージ プレビュー")
    print("=" * 70)
    
    async with EnhancedTrendsManager() as manager:
        # トレンドデータ取得
        trends = await manager.get_enhanced_trends(max_trends=100)
        
        # Discord埋め込み形式生成
        discord_data = manager.format_trends_for_discord(trends)
        
        # 埋め込みメッセージのヘッダー部分
        print("🏷️ 【DISCORD埋め込みメッセージ】")
        print("┌" + "─" * 68 + "┐")
        print(f"│ {discord_data.get('title', 'タイトルなし'):^66} │")
        print("├" + "─" * 68 + "┤")
        
        description = discord_data.get('description', '')
        if len(description) > 64:
            desc_lines = [description[i:i+64] for i in range(0, len(description), 64)]
            for desc_line in desc_lines:
                print(f"│ {desc_line:<66} │")
        else:
            print(f"│ {description:<66} │")
        
        print("└" + "─" * 68 + "┘")
        print()
        
        # 各フィールドの詳細表示
        fields = discord_data.get('fields', [])
        category_count = 0
        
        for field in fields:
            field_name = field.get('name', '')
            field_value = field.get('value', '')
            
            # カテゴリフィールドの場合
            if field_name.startswith('📂'):
                category_count += 1
                category = field_name.replace('📂 ', '')
                
                print(f"📂 【フィールド {category_count}】{category}")
                print("─" * 50)
                
                # フィールド内容を行ごとに分解
                lines = field_value.split('\n')
                current_article = {}
                article_count = 0
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('🔥 **') and line.endswith('**'):
                        # 新しい記事のタイトル
                        if current_article:
                            # 前の記事を表示
                            article_count += 1
                            print(f"  🔥 記事{article_count}: {current_article['title']}")
                            print(f"     📰 ソース: {current_article.get('source', 'N/A')}")
                            print(f"     🌟 品質: {current_article.get('quality', 'N/A')}")
                            if current_article.get('likes'):
                                print(f"     ❤️ いいね: {current_article['likes']}")
                            print()
                        
                        # 新しい記事を開始
                        title = line.replace('🔥 **', '').replace('**', '')
                        current_article = {'title': title}
                        
                    elif line.startswith('📰') and '|' in line:
                        # ソースと品質情報
                        parts = line.split('|')
                        source_part = parts[0].replace('📰 ', '').strip()
                        
                        for part in parts[1:]:
                            part = part.strip()
                            if part.startswith('品質:'):
                                current_article['quality'] = part.replace('品質: ', '')
                            elif part.startswith('❤️'):
                                current_article['likes'] = part.replace('❤️ ', '')
                        
                        current_article['source'] = source_part
                
                # 最後の記事を表示
                if current_article:
                    article_count += 1
                    print(f"  🔥 記事{article_count}: {current_article['title']}")
                    print(f"     📰 ソース: {current_article.get('source', 'N/A')}")
                    print(f"     🌟 品質: {current_article.get('quality', 'N/A')}")
                    if current_article.get('likes'):
                        print(f"     ❤️ いいね: {current_article['likes']}")
                    print()
                
                print(f"📊 文字数: {len(field_value)}文字 / 1024文字制限")
                print("=" * 50)
                print()
            
            # データ統計フィールドの場合
            elif field_name.startswith('📈'):
                print(f"📊 【データ統計】")
                print("─" * 30)
                stats_lines = field_value.split('\n')
                for stat_line in stats_lines:
                    if stat_line.strip():
                        print(f"  {stat_line}")
                print()
        
        # フッター情報
        footer = discord_data.get('footer', {})
        if footer:
            print("👣 【フッター】")
            print("─" * 20)
            print(f"  {footer.get('text', '')}")
            print()
        
        # 埋め込みの制限チェック
        print("🔍 【Discord制限チェック】")
        print("─" * 30)
        
        title_len = len(discord_data.get('title', ''))
        desc_len = len(discord_data.get('description', ''))
        field_count = len(fields)
        
        print(f"📋 タイトル: {title_len}/256文字 {'✅' if title_len <= 256 else '❌'}")
        print(f"📝 説明: {desc_len}/4096文字 {'✅' if desc_len <= 4096 else '❌'}")
        print(f"📂 フィールド数: {field_count}/25個 {'✅' if field_count <= 25 else '❌'}")
        
        # 各フィールドの文字数チェック
        max_field_len = 0
        for field in fields:
            field_len = len(field.get('value', ''))
            if field_len > max_field_len:
                max_field_len = field_len
        
        print(f"📄 最大フィールド長: {max_field_len}/1024文字 {'✅' if max_field_len <= 1024 else '❌'}")
        
        # 総文字数
        total_chars = title_len + desc_len + sum(len(f.get('value', '')) for f in fields)
        print(f"📊 総文字数: {total_chars}文字")
        
        print("\n" + "=" * 70)
        print("🎯 このような内容がDiscordの水曜日配信で表示されます！")
        print(f"📅 配信時刻: 毎週水曜日 7:00")
        print(f"🎨 色: #{discord_data.get('color', 0):06x} (青緑)")
        print(f"📂 表示カテゴリ: {category_count}個")

if __name__ == "__main__":
    asyncio.run(show_discord_embed_preview())