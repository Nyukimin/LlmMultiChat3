"""
memory/short_term.py
短期記憶の実装

LangGraph Stateとして管理される即時応答用の記憶。
6-12ターン程度を保持し、会話の文脈を維持。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import OrderedDict
from .base import MemoryBackend, MemoryItem, MemoryConfig


class ShortTermMemory(MemoryBackend):
    """短期記憶の実装（RAM上で管理）"""
    
    def __init__(self, config: MemoryConfig = None):
        """
        初期化
        
        Args:
            config: メモリ設定
        """
        super().__init__()
        self.backend_type = "short_term"
        self.config = config or MemoryConfig()
        
        # OrderedDictで順序を保持
        self.storage: OrderedDict[str, MemoryItem] = OrderedDict()
        
        # 統計情報
        self.stats = {
            'total_stores': 0,
            'total_retrievals': 0,
            'total_deletions': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def store(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """
        データを保存
        
        Args:
            key: 保存キー
            value: 保存する値
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            # 既存アイテムがあれば削除
            if key in self.storage:
                del self.storage[key]
            
            # 新しいアイテムを作成
            item = MemoryItem(key, value, metadata)
            
            # 容量制限チェック
            if len(self.storage) >= self.config.short_term_max_items:
                # 最古のアイテムを削除（FIFO）
                self.storage.popitem(last=False)
            
            # 保存
            self.storage[key] = item
            self.stats['total_stores'] += 1
            
            return True
            
        except Exception as e:
            print(f"Short-term memory store error: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        データを取得
        
        Args:
            key: 取得キー
            
        Returns:
            保存されたデータ、存在しない場合None
        """
        self.stats['total_retrievals'] += 1
        
        if key in self.storage:
            item = self.storage[key]
            item.update_access()
            self.stats['cache_hits'] += 1
            
            # TTLチェック
            elapsed = (datetime.now() - item.created_at).total_seconds()
            if elapsed > self.config.short_term_ttl_seconds:
                # 期限切れ
                del self.storage[key]
                self.stats['cache_misses'] += 1
                return None
            
            return item.value
        else:
            self.stats['cache_misses'] += 1
            return None
    
    def delete(self, key: str) -> bool:
        """
        データを削除
        
        Args:
            key: 削除キー
            
        Returns:
            成功した場合True
        """
        if key in self.storage:
            del self.storage[key]
            self.stats['total_deletions'] += 1
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """
        キーが存在するか確認
        
        Args:
            key: 確認キー
            
        Returns:
            存在する場合True
        """
        return key in self.storage
    
    def clear(self) -> bool:
        """
        全データを削除
        
        Returns:
            成功した場合True
        """
        self.storage.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        cache_hit_rate = 0.0
        if self.stats['total_retrievals'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / self.stats['total_retrievals']
        
        return {
            'backend_type': self.backend_type,
            'current_items': len(self.storage),
            'max_items': self.config.short_term_max_items,
            'ttl_seconds': self.config.short_term_ttl_seconds,
            'cache_hit_rate': cache_hit_rate,
            **self.stats
        }
    
    def get_recent_items(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        最新のN件のアイテムを取得
        
        Args:
            n: 取得件数
            
        Returns:
            アイテムのリスト
        """
        items = list(self.storage.values())[-n:]
        return [item.to_dict() for item in items]
    
    def cleanup_expired(self) -> int:
        """
        期限切れアイテムを削除
        
        Returns:
            削除件数
        """
        now = datetime.now()
        expired_keys = []
        
        for key, item in self.storage.items():
            elapsed = (now - item.created_at).total_seconds()
            if elapsed > self.config.short_term_ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.storage[key]
        
        return len(expired_keys)
    
    def get_all_keys(self) -> List[str]:
        """
        全キーを取得
        
        Returns:
            キーのリスト
        """
        return list(self.storage.keys())
    
    def get_size_bytes(self) -> int:
        """
        メモリ使用量を取得（概算）
        
        Returns:
            バイト数
        """
        import sys
        total_size = 0
        for item in self.storage.values():
            total_size += sys.getsizeof(item.value)
            total_size += sys.getsizeof(item.metadata)
        return total_size


class ConversationBuffer:
    """会話バッファ（短期記憶の特殊化）"""
    
    def __init__(self, max_turns: int = 12):
        """
        初期化
        
        Args:
            max_turns: 最大ターン数
        """
        self.max_turns = max_turns
        self.buffer: List[Dict[str, Any]] = []
    
    def add_turn(self, speaker: str, message: str, metadata: Dict = None):
        """
        ターンを追加
        
        Args:
            speaker: 発話者
            message: メッセージ
            metadata: メタデータ
        """
        turn = {
            'speaker': speaker,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.buffer.append(turn)
        
        # バッファサイズ制限
        if len(self.buffer) > self.max_turns:
            self.buffer.pop(0)
    
    def get_recent_turns(self, n: int = None) -> List[Dict[str, Any]]:
        """
        最近のN件のターンを取得
        
        Args:
            n: 取得件数（Noneの場合は全て）
            
        Returns:
            ターンのリスト
        """
        if n is None:
            return self.buffer.copy()
        return self.buffer[-n:] if n > 0 else []
    
    def clear(self):
        """バッファをクリア"""
        self.buffer.clear()
    
    def get_context_string(self, max_turns: int = 6) -> str:
        """
        会話コンテキストを文字列として取得
        
        Args:
            max_turns: 最大ターン数
            
        Returns:
            フォーマットされた会話文字列
        """
        recent = self.get_recent_turns(max_turns)
        lines = []
        for turn in recent:
            speaker = turn['speaker']
            message = turn['message']
            lines.append(f"{speaker}: {message}")
        return "\n".join(lines)