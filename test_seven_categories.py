#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
7カテゴリ表示テスト
修正されたEnhanced Trends Managerが7カテゴリ全てを表示できるかテスト
"""

import asyncio
from utils.enhanced_trends_manager import EnhancedTrendsManager

async def test_seven_categories():
    """7カテゴリ表示テスト"""
    print("🧪 7カテゴリ表示テスト開始")
    print("=" * 60)
    
    required_categories = [
        'プログラミング', 'ウェブ開発', '生成AI', 
        'データサイエンス・AI開発', 'キャリア', 'ビジネス', '勉強・自己啓発'
    ]
    
    async with EnhancedTrendsManager() as manager:
        print("📊 Enhanced Trends Manager トレンドデータ取得中...")
        
        # トレンドデータ取得
        trends = await manager.get_enhanced_trends(max_trends=100)
        print(f"✅ 総取得データ数: {len(trends)}件")
        
        # カテゴリ別統計
        print("\n📋 カテゴリ別データ数:")
        category_stats = {}
        for trend in trends:
            category = trend.get('category', '未分類')
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(trend)
        
        for category in required_categories:
            count = len(category_stats.get(category, []))
            status = "✅" if count >= 2 else "❌"
            print(f"  {status} {category}: {count}件")
        
        # その他のカテゴリ
        other_categories = set(category_stats.keys()) - set(required_categories)
        if other_categories:
            print("\n📎 その他のカテゴリ:")
            for category in other_categories:
                count = len(category_stats[category])
                print(f"  📄 {category}: {count}件")
        
        # Discord Embed形式テスト
        print("\n🎮 Discord Embed形式テスト")
        print("-" * 40)
        
        discord_data = manager.format_trends_for_discord(trends)
        
        print(f"📋 タイトル: {discord_data.get('title', 'N/A')}")
        print(f"📝 説明: {discord_data.get('description', 'N/A')}")
        print(f"🎨 色: #{discord_data.get('color', 0):06x}")
        
        fields = discord_data.get('fields', [])
        print(f"📂 フィールド数: {len(fields)}個")
        
        # 各フィールドの詳細
        print("\n📄 フィールド詳細:")
        category_fields = 0
        for i, field in enumerate(fields, 1):
            field_name = field.get('name', '')
            field_value = field.get('value', '')
            field_length = len(field_value)
            
            # データ統計フィールドをスキップしてカテゴリフィールドをカウント
            if field_name.startswith('📂'):
                category_fields += 1
                category_name = field_name.replace('📂 ', '')
                status = "✅" if category_name in required_categories else "📎"
                print(f"  {status} {field_name} ({field_length}文字)")
                
                # フィールド内容の一部を表示
                lines = field_value.split('\n')
                first_line = lines[0] if lines else "内容なし"
                if len(first_line) > 60:
                    first_line = first_line[:57] + "..."
                print(f"     内容: {first_line}")
            else:
                print(f"  📊 {field_name} ({field_length}文字)")
        
        # 結果評価
        print("\n" + "=" * 60)
        print("🎯 テスト結果")
        print("-" * 30)
        
        success = True
        
        # 1. 7カテゴリ全てにデータがあるか
        missing_categories = []
        for category in required_categories:
            if category not in category_stats or len(category_stats[category]) < 2:
                missing_categories.append(category)
        
        if missing_categories:
            print(f"❌ 不足カテゴリ: {', '.join(missing_categories)}")
            success = False
        else:
            print("✅ 7カテゴリ全てに2件以上のデータあり")
        
        # 2. Discord Embedに7カテゴリ全て表示されるか
        if category_fields >= 7:
            print(f"✅ Discord Embedに{category_fields}カテゴリ表示")
        else:
            print(f"❌ Discord Embedに{category_fields}カテゴリのみ表示（期待値: 7）")
            success = False
        
        # 3. 重複記事の確認
        unique_titles = set()
        duplicates = []
        for trend in trends:
            title = trend.get('title', '')
            if title in unique_titles:
                duplicates.append(title)
            else:
                unique_titles.add(title)
        
        if duplicates:
            print(f"⚠️ 重複記事: {len(duplicates)}件")
            for dup in duplicates[:3]:  # 最初の3件のみ表示
                print(f"   - {dup}")
        else:
            print("✅ 重複記事なし")
        
        # 最終判定
        print("\n" + "=" * 60)
        if success:
            print("🎉 テスト成功！7カテゴリ全て表示されています")
            print("✅ 水曜日配信の準備完了")
        else:
            print("❌ テスト失敗。修正が必要です")
            
        return success

if __name__ == "__main__":
    result = asyncio.run(test_seven_categories())
    exit(0 if result else 1)