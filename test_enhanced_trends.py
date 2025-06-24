#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Trends Manager テストスクリプト
データ取得テストと結果確認
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.enhanced_trends_manager import EnhancedTrendsManager

async def test_enhanced_trends():
    """Enhanced Trends Manager のテスト実行"""
    print("🚀 Enhanced Trends Manager テスト開始")
    print("=" * 60)
    
    try:
        async with EnhancedTrendsManager() as manager:
            print("✅ EnhancedTrendsManager 初期化成功")
            
            # 1. 基本的なトレンド取得テスト
            print("\n📊 基本トレンド取得テスト（最大20件）")
            trends = await manager.get_enhanced_trends(max_trends=20)
            
            print(f"📈 取得データ数: {len(trends)}件")
            
            if trends:
                print("\n🔍 サンプルデータ:")
                for i, trend in enumerate(trends[:3]):  # 最初の3件を表示
                    print(f"\n【{i+1}件目】")
                    print(f"  📝 タイトル: {trend.get('title', 'N/A')}")
                    print(f"  📂 カテゴリ: {trend.get('category', 'N/A')}")
                    print(f"  🌟 品質スコア: {trend.get('quality_score', 'N/A')}")
                    print(f"  👍 いいね数: {trend.get('likes', 'N/A')}")
                    print(f"  🔗 URL: {trend.get('url', 'N/A')}")
                    print(f"  📰 ソース: {trend.get('source', 'N/A')}")
                    print(f"  📄 説明: {trend.get('description', 'N/A')[:100]}...")
            
            # 2. カテゴリ別統計
            print("\n📊 カテゴリ別統計:")
            category_stats = {}
            for trend in trends:
                category = trend.get('category', 'その他')
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'sources': set()}
                category_stats[category]['count'] += 1
                category_stats[category]['sources'].add(trend.get('source', 'N/A'))
            
            for category, stats in category_stats.items():
                print(f"  {category}: {stats['count']}件 (ソース: {len(stats['sources'])}種類)")
            
            # 3. Discord用フォーマットテスト
            print("\n🤖 Discord用フォーマットテスト")
            discord_embed = manager.format_trends_for_discord(trends)
            
            print(f"📋 Embedタイトル: {discord_embed.get('title', 'N/A')}")
            print(f"📝 Embed説明: {discord_embed.get('description', 'N/A')[:100]}...")
            print(f"🏷️ Fieldの数: {len(discord_embed.get('fields', []))}")
            
            # 4. 特定カテゴリでのテスト
            print("\n🎯 特定カテゴリ取得テスト（ビジネス、プログラミング）")
            category_trends = await manager.get_enhanced_trends(
                max_trends=10,
                categories=['ビジネス', 'プログラミング']
            )
            
            print(f"📈 指定カテゴリ取得数: {len(category_trends)}件")
            if category_trends:
                for trend in category_trends[:2]:  # 最初の2件を表示
                    print(f"  📝 {trend.get('title', 'N/A')} ({trend.get('category', 'N/A')})")
            
            print("\n" + "=" * 60)
            print("✅ テスト完了！")
            print(f"📊 総取得データ数: {len(trends)}件")
            print(f"🏷️ 検出カテゴリ数: {len(category_stats)}種類")
            print(f"🔗 Discord Embed準備完了: {len(discord_embed.get('fields', []))}フィールド")
            
            return trends, discord_embed
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    trends, embed = asyncio.run(test_enhanced_trends())
    
    if trends:
        print(f"\n🎉 テスト成功！{len(trends)}件のトレンドデータを取得しました。")
    else:
        print("\n❌ テスト失敗。データ取得に問題があります。")