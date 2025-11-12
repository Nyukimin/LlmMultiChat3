"""
conversation_state.py
会話状態・履歴管理
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ConversationState:
    """会話状態管理クラス"""
    
    # 会話履歴
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 現在のターン数
    current_turn: int = 0
    
    # 最大ターン数
    max_turns: int = 12
    
    # セッション開始時刻
    start_time: datetime = field(default_factory=datetime.now)
    
    # ユーザーID
    user_id: str = "default"
    
    # スレッドID（セッション識別）
    thread_id: Optional[str] = None
    
    # 現在のキャラクター
    current_character: Optional[str] = None
    
    # 検索結果（ノクス用）
    search_results: Optional[str] = None
    
    # 感情状態（各キャラクター）
    emotions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(
        self,
        speaker: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        ターン追加
        
        Args:
            speaker: 発話者（user/lumina/clarisse/nox）
            message: メッセージ内容
            metadata: 追加メタデータ
        """
        turn = {
            "speaker": speaker,
            "msg": message,
            "timestamp": datetime.now().isoformat(),
            "turn": self.current_turn,
            "metadata": metadata or {}
        }
        
        self.history.append(turn)
        self.current_turn += 1
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """最後のメッセージ取得"""
        if self.history:
            return self.history[-1]
        return None
    
    def get_context(self, last_n: int = 5) -> str:
        """
        最近のN ターンの文脈取得
        
        Args:
            last_n: 取得するターン数
        
        Returns:
            整形された会話文脈
        """
        recent = self.history[-last_n:]
        return "\n".join([
            f"{turn['speaker']}: {turn['msg']}"
            for turn in recent
        ])
    
    def should_flush(self) -> bool:
        """
        短期記憶のflush判定
        
        Returns:
            flushすべきかどうか
        """
        # ターン数超過
        if self.current_turn >= self.max_turns:
            return True
        
        # 時間超過（30分）
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        if duration >= 30:
            return True
        
        return False
    
    def summarize(self) -> str:
        """
        会話履歴を要約
        
        Returns:
            要約テキスト
        """
        # TODO: LLMを使った要約生成
        # 現状は簡易的な処理
        if not self.history:
            return "No conversation yet."
        
        speakers = set(turn["speaker"] for turn in self.history)
        turn_count = len(self.history)
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        
        summary = f"Conversation summary:\n"
        summary += f"- Participants: {', '.join(speakers)}\n"
        summary += f"- Turns: {turn_count}\n"
        summary += f"- Duration: {duration:.1f} minutes\n"
        
        # 最初と最後のメッセージ
        if self.history:
            summary += f"- First message: {self.history[0]['msg'][:50]}...\n"
            summary += f"- Last message: {self.history[-1]['msg'][:50]}..."
        
        return summary
    
    def reset(self):
        """会話状態をリセット"""
        self.history = []
        self.current_turn = 0
        self.start_time = datetime.now()
        self.search_results = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（シリアライズ用）"""
        return {
            "history": self.history,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "start_time": self.start_time.isoformat(),
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "current_character": self.current_character,
            "search_results": self.search_results,
            "emotions": self.emotions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """辞書形式から復元（デシリアライズ用）"""
        state = cls()
        state.history = data.get("history", [])
        state.current_turn = data.get("current_turn", 0)
        state.max_turns = data.get("max_turns", 12)
        state.start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
        state.user_id = data.get("user_id", "default")
        state.thread_id = data.get("thread_id")
        state.current_character = data.get("current_character")
        state.search_results = data.get("search_results")
        state.emotions = data.get("emotions", {})
        state.metadata = data.get("metadata", {})
        return state