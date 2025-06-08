# -*- coding:utf-8 -*-
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiChat:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat_sessions = {}
    
    def get_response(self, user_id: str, message: str) -> str:
        """ユーザーごとのチャットセッションを管理してレスポンスを生成"""
        try:
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
            return f"Geminiとの通信でエラーが発生しました: {str(e)}"
    
    def reset_session(self, user_id: str):
        """特定ユーザーのチャットセッションをリセット"""
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]