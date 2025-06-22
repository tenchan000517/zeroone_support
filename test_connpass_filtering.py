#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.connpass_manager import ConnpassManager

async def test_connpass_filtering():
    """connpassフィルタリング機能のテスト"""
    print("=== Connpass フィルタリング機能テスト ===")
    
    manager = ConnpassManager()
    
    print("\n1. 設定確認:")
    print(f"   フィルタキーワード: {manager.filter_keywords}")
    print(f"   オンライン判定パターン: {manager.online_place_patterns}")
    
    print("\n2. オンライン講座取得テスト:")
    try:
        events = await manager.get_online_courses(days_ahead=7)
        
        print(f"\n   取得結果: {len(events)}件")
        
        if events:
            print("\n3. 取得したイベント詳細:")
            for i, event in enumerate(events[:3], 1):
                title = event.get('title', 'N/A')
                place = event.get('place', 'N/A')
                address = event.get('address', 'N/A')
                catch = event.get('catch', 'N/A')
                url = event.get('url', 'N/A')
                
                print(f"\n   [{i}] {title}")
                print(f"       場所: {place}")
                print(f"       住所: {address}")
                print(f"       概要: {catch[:50]}...")
                print(f"       URL: {url}")
        else:
            print("\n   ⚠️ フィルタリング後のイベントが0件でした")
            
    except Exception as e:
        print(f"\n   ❌ エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_connpass_filtering())