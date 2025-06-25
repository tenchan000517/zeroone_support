#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
はてなブックマークAPI動作確認テスト
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET

async def test_hatena_apis():
    """はてなブックマークAPIの動作を詳細テスト"""
    
    async with aiohttp.ClientSession() as session:
        print("🔍 はてなブックマークAPI動作確認テスト")
        print("=" * 50)
        
        # 1. カテゴリ別フィードテスト
        categories = {
            "life": "暮らし",
            "knowledge": "学び", 
            "it": "テクノロジー",
            "economics": "政治と経済"
        }
        
        for cat_id, cat_name in categories.items():
            print(f"\n📂 {cat_name}カテゴリ ({cat_id}) テスト")
            print("-" * 30)
            
            url = f"https://b.hatena.ne.jp/hotentry/{cat_id}.rss"
            print(f"URL: {url}")
            
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"ステータス: {response.status}")
                    if response.status == 200:
                        content = await response.text()
                        print(f"レスポンス長: {len(content)}文字")
                        
                        # XML解析
                        try:
                            root = ET.fromstring(content)
                            print(f"ルート要素: {root.tag}")
                            
                            # 全体構造確認
                            for child in root:
                                print(f"  子要素: {child.tag}")
                                if child.tag == 'channel':
                                    for channel_child in child:
                                        print(f"    チャンネル子要素: {channel_child.tag}")
                            
                            # 複数の方法でitem要素を探す
                            items1 = root.findall('.//item')
                            items2 = root.findall('channel/item')
                            items3 = root.findall('*/item')
                            
                            print(f"記事数 (.//item): {len(items1)}件")
                            print(f"記事数 (channel/item): {len(items2)}件") 
                            print(f"記事数 (*/item): {len(items3)}件")
                            
                            items = items1 or items2 or items3
                            
                            # レスポンス内容の一部を表示
                            print(f"レスポンス先頭500文字:")
                            print(content[:500])
                            print("...")
                            print(f"レスポンス末尾500文字:")
                            print(content[-500:])
                            
                            # 最初の記事を詳細表示
                            if items:
                                first_item = items[0]
                                title = first_item.find('title')
                                link = first_item.find('link')
                                print(f"タイトル例: {title.text if title is not None else 'なし'}")
                                print(f"URL例: {link.text if link is not None else 'なし'}")
                                
                                # はてな特有要素チェック
                                namespace = {'hatena': 'http://www.hatena.ne.jp/info/xmlns#'}
                                bookmark_count = first_item.find('hatena:bookmarkcount', namespace)
                                if bookmark_count is not None:
                                    print(f"ブックマーク数: {bookmark_count.text}")
                                else:
                                    print("ブックマーク数: 見つからず")
                        except ET.ParseError as e:
                            print(f"XML解析エラー: {e}")
                            print(f"レスポンス先頭100文字: {content[:100]}")
                    else:
                        print(f"HTTPエラー: {response.status}")
                        
            except Exception as e:
                print(f"取得エラー: {e}")
            
            await asyncio.sleep(1)  # レート制限対策
        
        # 2. キーワード検索テスト
        print(f"\n🔍 キーワード検索テスト")
        print("-" * 30)
        
        keywords = ["転職", "勉強法", "キャリア"]
        
        for keyword in keywords:
            print(f"\nキーワード: {keyword}")
            
            # 検索URL作成
            url = f"https://b.hatena.ne.jp/search/text?q={keyword}&users=5&sort=recent&safe=on&mode=rss"
            print(f"URL: {url}")
            
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"ステータス: {response.status}")
                    if response.status == 200:
                        content = await response.text()
                        print(f"レスポンス長: {len(content)}文字")
                        
                        try:
                            root = ET.fromstring(content)
                            items = root.findall('.//item')
                            print(f"検索結果: {len(items)}件")
                            
                            if items:
                                first_item = items[0]
                                title = first_item.find('title')
                                print(f"タイトル例: {title.text if title is not None else 'なし'}")
                        except ET.ParseError as e:
                            print(f"XML解析エラー: {e}")
                            print(f"レスポンス先頭200文字: {content[:200]}")
                    else:
                        print(f"HTTPエラー: {response.status}")
                        
            except Exception as e:
                print(f"取得エラー: {e}")
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_hatena_apis())