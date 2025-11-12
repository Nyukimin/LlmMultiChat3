"""
llm_nodes.py
各キャラクターLLMノード処理

各キャラクターの応答生成ノードを実装。
ルミナ（司会・雑談）、クラリス（解説・理論）、ノクス（検証・要約・検索）の3キャラ。
"""

import ollama
from typing import Dict, Any, Optional
from datetime import datetime
from config import Config
import requests
import json


class LLMNode:
    """LLMノードの基底クラス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.character_name = "Base"
        self.model_key = "fast"
    
    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """応答生成（サブクラスでオーバーライド）"""
        raise NotImplementedError
    
    def _call_ollama(self, prompt: str, model_key: str = None) -> str:
        """Ollama APIを呼び出し"""
        model = self.config.models.get(model_key or self.model_key)
        try:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return f"[エラー] {self.character_name}の応答生成に失敗しました: {str(e)}"
    
    def _format_history(self, history: list, max_turns: int = 6) -> str:
        """会話履歴をフォーマット"""
        recent = history[-max_turns:] if len(history) > max_turns else history
        formatted = []
        for turn in recent:
            speaker = turn.get('speaker', 'User')
            msg = turn.get('msg', '')
            formatted.append(f"{speaker}: {msg}")
        return "\n".join(formatted)


class LuminaNode(LLMNode):
    """ルミナノード（司会・雑談）"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.character_name = "ルミナ"
        self.model_key = "fast"
    
    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ルミナの応答生成"""
        history = state.get('history', [])
        current_input = state.get('user_input', '')
        
        # 会話履歴のフォーマット
        history_text = self._format_history(history)
        
        # プロンプト構築
        prompt = f"""あなたは親しみやすく洞察力のあるAI「ルミナ」です。
あなたの役割は司会進行と雑談です。

性格・口調:
- フレンドリーで明るい
- ユーザーの感情に寄り添う
- 話題を広げるのが得意
- 自然な会話の流れを作る

これまでの会話:
{history_text}

ユーザーの入力: {current_input}

上記を踏まえて、自然で温かみのある返答をしてください。
返答のみを出力してください。"""

        # 応答生成
        response = self._call_ollama(prompt)
        
        # 状態更新
        new_state = state.copy()
        new_state['history'].append({
            'speaker': self.character_name,
            'msg': response,
            'timestamp': datetime.now().isoformat()
        })
        new_state['last_speaker'] = self.character_name
        
        return new_state


class ClarisNode(LLMNode):
    """クラリスノード（解説・理論）"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.character_name = "クラリス"
        self.model_key = "medium"
    
    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """クラリスの応答生成"""
        history = state.get('history', [])
        current_input = state.get('user_input', '')
        
        # 会話履歴のフォーマット
        history_text = self._format_history(history)
        
        # プロンプト構築
        prompt = f"""あなたは理論的で穏やかなAI「クラリス」です。
あなたの役割は解説と理論的な整理です。

性格・口調:
- 穏やかで丁寧
- 論理的・構造的に説明
- 背景や理由を重視
- 分かりやすく整理するのが得意

これまでの会話:
{history_text}

ユーザーの入力: {current_input}

上記の内容を丁寧に整理し、背景や構造を含めて解説してください。
返答のみを出力してください。"""

        # 応答生成
        response = self._call_ollama(prompt)
        
        # 状態更新
        new_state = state.copy()
        new_state['history'].append({
            'speaker': self.character_name,
            'msg': response,
            'timestamp': datetime.now().isoformat()
        })
        new_state['last_speaker'] = self.character_name
        
        return new_state


class NoxNode(LLMNode):
    """ノクスノード（検証・要約・検索）"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.character_name = "ノクス"
        self.model_key = "search"
    
    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ノクスの応答生成"""
        history = state.get('history', [])
        current_input = state.get('user_input', '')
        
        # 検索が必要かチェック
        search_keywords = ["調べて", "検索", "最新", "ニュース", "情報"]
        needs_search = any(keyword in current_input for keyword in search_keywords)
        
        search_result = ""
        if needs_search and self.config.enable_search:
            search_result = self._perform_search(current_input)
        
        # 会話履歴のフォーマット
        history_text = self._format_history(history)
        
        # プロンプト構築
        prompt = f"""あなたはクールで情報整理に優れたAI「ノクス」です。
あなたの役割は検証と要約です。

性格・口調:
- クールで簡潔
- 疑問を持ちながら検証
- 情報の正確性を重視
- 要点を的確にまとめる

これまでの会話:
{history_text}

ユーザーの入力: {current_input}

{f"検索結果:\n{search_result}\n" if search_result else ""}
上記を踏まえて、正確で簡潔な返答をしてください。
返答のみを出力してください。"""

        # 応答生成
        response = self._call_ollama(prompt)
        
        # 状態更新
        new_state = state.copy()
        new_state['history'].append({
            'speaker': self.character_name,
            'msg': response,
            'timestamp': datetime.now().isoformat(),
            'search_used': needs_search
        })
        new_state['last_speaker'] = self.character_name
        
        return new_state
    
    def _perform_search(self, query: str) -> str:
        """Serper APIで検索実行"""
        if not self.config.serper_api_key:
            return "[検索APIキーが設定されていません]"
        
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.config.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {"q": query, "num": 3}
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("organic", [])[:3]
            
            if not results:
                return "[検索結果が見つかりませんでした]"
            
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                formatted.append(f"{i}. {title}\n   {snippet}")
            
            return "\n\n".join(formatted)
            
        except Exception as e:
            return f"[検索エラー: {str(e)}]"


class RouterNode:
    """ルーターノード（どのキャラに応答させるか判定）"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def route(self, state: Dict[str, Any]) -> str:
        """次に応答するキャラを決定"""
        user_input = state.get('user_input', '').lower()
        last_speaker = state.get('last_speaker', '')
        
        # 明示的な指名チェック
        if 'ルミナ' in user_input or 'るみな' in user_input:
            return 'lumina'
        elif 'クラリス' in user_input or 'くらりす' in user_input:
            return 'claris'
        elif 'ノクス' in user_input or 'のくす' in user_input:
            return 'nox'
        
        # キーワードベースのルーティング
        if any(k in user_input for k in ['調べて', '検索', '最新', 'ニュース']):
            return 'nox'
        elif any(k in user_input for k in ['説明', '解説', '詳しく', '理由']):
            return 'claris'
        else:
            return 'lumina'
    
    def decide_next(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """次のノードを決定して状態に設定"""
        next_character = self.route(state)
        new_state = state.copy()
        new_state['next_character'] = next_character
        return new_state