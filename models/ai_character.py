# -*- coding: utf-8 -*-
"""
AIキャラクター管理モデル
複数のAIキャラクターの情報を管理する
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import random
import json

@dataclass
class AICharacter:
    """AIキャラクター情報"""
    id: str
    name: str
    display_name: str
    avatar_url: Optional[str]
    personality: str
    speaking_style: str
    interests: List[str]
    active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,  
            'avatar_url': self.avatar_url,
            'personality': self.personality,
            'speaking_style': self.speaking_style,
            'interests': self.interests,
            'active': self.active
        }

class AICharacterManager:
    """AIキャラクター管理システム"""
    
    def __init__(self):
        self.characters: Dict[str, AICharacter] = {}
        self._initialize_default_characters()
    
    def _initialize_default_characters(self):
        """デフォルトのAIキャラクターを初期化"""
        default_characters = [
            AICharacter(
                id="ai_takahashi",
                name="高橋誠",
                display_name="高橋誠",
                avatar_url="https://drive.google.com/uc?id=1yCFikJRbhHUXQooVj_sic4TLWWToVKWp",
                personality="真面目すぎるほど真面目で責任感が強い起業家志望の大学生。理想主義から現実的な課題解決思考への変化を体現する",
                speaking_style="論理的で丁寧な話し方。「〜だと思います」と意見を述べ、「なるほど」と相手の意見を受け止める",
                interests=["起業", "ビジネスフレームワーク", "社会課題解決", "陸上競技"]
            ),
            AICharacter(
                id="ai_sato",
                name="佐藤健太",
                display_name="佐藤健太",
                avatar_url="https://drive.google.com/uc?id=1TRXSmvohpWnMVZGf2KLh2gCKcvcH-h0l",
                personality="技術と経営の融合した視点を提供するエンジニア。論理的で実践的、データドリブン思考を重視",
                speaking_style="簡潔で要点を突いた話し方。技術用語を多用し、「データで証明しよう」とデータドリブン思考を提案",
                interests=["プログラミング", "A技術", "システム思考", "ハッカソン"]
            ),
            AICharacter(
                id="ai_suzuki", 
                name="鈴木美咲",
                display_name="鈴木美咲",
                avatar_url="https://drive.google.com/uc?id=1FYeQ5nW-BTUZihoICqccUF_Hk4ZcQmMo",
                personality="マーケティング・顧客視点の専門家。共感力が高く現実的で、コミュニケーション上手",
                speaking_style="わかりやすい言葉で伝え、質問を多用。「ユーザー視点で考えると…」と顧客中心的な視点を提案",
                interests=["マーケティング", "ユーザーインタビュー", "SNS運用", "データ分析"]
            ),
            AICharacter(
                id="ai_yamada",
                name="山田哲也",
                display_name="山田メンター",
                avatar_url="https://drive.google.com/uc?id=1WzinD9vo8LtX9kwcXKOiAfOfzjiAnVeZ",
                personality="起業家育成プロジェクトのメンター。洞察力があり実践的で、「解の質より問いの質」を重視する経験豊富な指導者",
                speaking_style="質問で考えさせる話し方。「本質は〜だ」と核心を突き、「問いの質はどうだ？」とソクラテス式対話を駆使",
                interests=["起業家育成", "ビジネスフレームワーク", "メンタリング", "戦略思考"]
            ),
            AICharacter(
                id="ai_king_dynaka",
                name="キング・ダイナカ",
                display_name="キング・ダイナカ",
                avatar_url="https://drive.google.com/uc?id=1C0KTopEwnwu7Ya4LhbiyiVOYuAQE7Snt",
                personality="妙にハイテンションで筋トレが趣味の超ポジティブキャラクター。常にエネルギッシュで周りを元気にする",
                speaking_style="「〜ッス！」「筋肉は裏切らない！」などの体育会系の話し方。全てを筋トレと関連付けて話す癖がある",
                interests=["筋トレ", "プロテイン", "体力向上", "モチベーション向上", "スポーツ全般"]
            )
        ]
        
        for char in default_characters:
            self.characters[char.id] = char
    
    def get_character(self, character_id: str) -> Optional[AICharacter]:
        """指定されたIDのキャラクターを取得"""
        return self.characters.get(character_id)
    
    def get_active_characters(self) -> List[AICharacter]:
        """アクティブなキャラクターのリストを取得"""
        return [char for char in self.characters.values() if char.active]
    
    def get_random_characters(self, count: int) -> List[AICharacter]:
        """ランダムにキャラクターを選択"""
        active_chars = self.get_active_characters()
        return random.sample(active_chars, min(count, len(active_chars)))
    
    def deactivate_character(self, character_id: str):
        """キャラクターを非アクティブにする"""
        if character_id in self.characters:
            self.characters[character_id].active = False
    
    def activate_character(self, character_id: str):
        """キャラクターをアクティブにする"""
        if character_id in self.characters:
            self.characters[character_id].active = True
    
    def get_character_list(self) -> str:
        """キャラクター一覧を文字列で返す"""
        active_chars = self.get_active_characters()
        if not active_chars:
            return "現在アクティブなキャラクターはいません。"
        
        result = "**アクティブなAIキャラクター:**\n"
        for char in active_chars:
            status = "🟢" if char.active else "🔴"
            result += f"{status} {char.display_name} - {char.personality[:30]}...\n"
        
        return result