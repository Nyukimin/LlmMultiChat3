"""
memory/base.py
記憶バックエンドの抽象基底クラス

全ての記憶システムが実装すべきインターフェースを定義。
Phase 2以降での拡張を考慮した設計。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class MemoryBackend(ABC):
    """記憶バックエンドの抽象基底クラス"""
    
    def __init__(self):
        """初期化"""
        self.backend_type = "base"
        self.created_at = datetime.now()
    
    @abstractmethod
    def store(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """
        データを保存
        
        Args:
            key: 保存キー
            value: 保存する値
            metadata: メタデータ（オプション）
            
        Returns:
            成功した場合True
        """
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """
        データを取得
        
        Args:
            key: 取得キー
            
        Returns:
            保存されたデータ、存在しない場合None
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        データを削除
        
        Args:
            key: 削除キー
            
        Returns:
            成功した場合True
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        キーが存在するか確認
        
        Args:
            key: 確認キー
            
        Returns:
            存在する場合True
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        全データを削除
        
        Returns:
            成功した場合True
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        pass


class MemoryItem:
    """記憶アイテムの基本構造"""
    
    def __init__(self, key: str, value: Any, metadata: Dict = None):
        """
        初期化
        
        Args:
            key: アイテムキー
            value: アイテム値
            metadata: メタデータ
        """
        self.key = key
        self.value = value
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()
        self.access_count = 0
    
    def update_access(self):
        """アクセス情報を更新"""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'key': self.key,
            'value': self.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'accessed_at': self.accessed_at.isoformat(),
            'access_count': self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """辞書から復元"""
        item = cls(
            key=data['key'],
            value=data['value'],
            metadata=data.get('metadata', {})
        )
        item.created_at = datetime.fromisoformat(data['created_at'])
        item.accessed_at = datetime.fromisoformat(data['accessed_at'])
        item.access_count = data.get('access_count', 0)
        return item


class MemoryConfig:
    """記憶システムの設定クラス"""
    
    def __init__(self):
        """デフォルト設定で初期化"""
        # 短期記憶設定
        self.short_term_max_items = 100
        self.short_term_ttl_seconds = 3600  # 1時間
        
        # 中期記憶設定
        self.mid_term_max_items = 1000
        self.mid_term_ttl_seconds = 86400 * 30  # 30日
        self.mid_term_backend = "duckdb"  # "redis" or "duckdb"
        
        # 長期記憶設定
        self.long_term_backend = "vectordb"  # "vectordb" or "sql"
        self.long_term_embedding_model = "all-MiniLM-L6-v2"
        
        # 知識ベース設定
        self.kb_update_interval = 86400 * 7  # 週次
        self.kb_namespaces = ["movie", "history", "gossip", "tech", "news"]
        
        # 共通設定
        self.enable_compression = True
        self.enable_encryption = False  # Phase 2で実装
        self.max_memory_mb = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'short_term': {
                'max_items': self.short_term_max_items,
                'ttl_seconds': self.short_term_ttl_seconds
            },
            'mid_term': {
                'max_items': self.mid_term_max_items,
                'ttl_seconds': self.mid_term_ttl_seconds,
                'backend': self.mid_term_backend
            },
            'long_term': {
                'backend': self.long_term_backend,
                'embedding_model': self.long_term_embedding_model
            },
            'knowledge_base': {
                'update_interval': self.kb_update_interval,
                'namespaces': self.kb_namespaces
            },
            'common': {
                'enable_compression': self.enable_compression,
                'enable_encryption': self.enable_encryption,
                'max_memory_mb': self.max_memory_mb
            }
        }