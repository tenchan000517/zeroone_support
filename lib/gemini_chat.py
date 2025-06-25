# -*- coding:utf-8 -*-
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import time
from typing import Dict, Any

load_dotenv()

class GeminiChat:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.chat_sessions = {}
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2秒間隔でリクエスト制限
    
    async def get_response(self, user_id: str, message: str) -> str:
        """ユーザーごとのチャットセッションを管理してレスポンスを生成"""
        try:
            # APIスロットリング
            await self._throttle_request()
            # ユーザーごとのチャットセッションを取得または作成
            if user_id not in self.chat_sessions:
                # システムプロンプトを設定
                system_prompt = """あなたは「DJアイズ」という名前のDiscordボットです。
フレンドリーで親しみやすい性格で、ユーザーと楽しく会話してください。
長い説明や定型文は避け、自然な会話を心がけてください。
箇条書きは使わず、短く簡潔に返答してください。"""
                
                self.chat_sessions[user_id] = self.model.start_chat(
                    history=[
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["了解しました！DJアイズとして楽しく会話しますね！"]}
                    ]
                )
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(message)
            
            # セッション履歴が長くなりすぎたらリセット
            if len(chat.history) > 20:
                system_prompt = """あなたは「DJアイズ」という名前のDiscordボットです。
フレンドリーで親しみやすい性格で、ユーザーと楽しく会話してください。
長い説明や定型文は避け、自然な会話を心がけてください。
箇条書きは使わず、短く簡潔に返答してください。"""
                
                self.chat_sessions[user_id] = self.model.start_chat(
                    history=[
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["了解しました！DJアイズとして楽しく会話しますね！"]}
                    ]
                )
            
            return response.text
        except Exception as e:
            # 429エラーの場合は特別な処理
            if "429" in str(e) or "quota" in str(e).lower():
                return "現在APIの使用制限に達しています。しばらく待ってから再度お試しください。"
            return f"Geminiとの通信でエラーが発生しました: {str(e)}"
    
    def reset_session(self, user_id: str):
        """特定ユーザーのチャットセッションをリセット"""
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]
    
    async def _throttle_request(self):
        """APIリクエストのスロットリング"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_ai_character_response(self, character_name: str, character_personality: str, 
                                       speaking_style: str, message: str, conversation_context: str = "") -> str:
        """AIキャラクター専用のレスポンス生成"""
        try:
            # APIスロットリング
            await self._throttle_request()
            
            # キャラクター専用のプロンプト
            system_prompt = f"""あなたは「{character_name}」というキャラクターです。

性格・特徴: {character_personality}
話し方: {speaking_style}

会話の流れ: {conversation_context}

指示:
- 必ず{character_name}として一貫性を保って返答してください
- 話し方の特徴を忠実に再現してください
- 自然で短めの返答（1-2文程度）を心がけてください
- 他のキャラクターの話を受けて、自分らしく反応してください
- 返答にキャラクター名やコロン（：）を含めないでください
- 返答は発言内容のみにしてください
- 商品名や具体例を出す時は、実在の商品名を使ってください
- 〇〇や△△のようなプレースホルダーは絶対に使わないでください
- 括弧で囲まれた指示文（例：（会話全体を振り返って））は発言に含めないでください
- 他のキャラクターと全く同じ内容を言わないでください。必ず独自の視点で発言してください"""
            
            response = self.model.generate_content(
                f"{system_prompt}\n\n{message}"
            )
            
            return response.text
            
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                return f"({character_name}は一時的に応答できません)"
            return f"({character_name}): エラーが発生しました"