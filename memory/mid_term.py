"""
memory/mid_term.py
中期記憶の実装

24時間〜30日のセッション復帰用記憶。
DuckDBを使用してローカルに永続化。
Redis キャッシュ層を追加（Phase 2）。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from .base import MemoryBackend, MemoryItem, MemoryConfig
from .redis_cache import get_redis_cache, RedisCache


class MidTermMemory(MemoryBackend):
    """中期記憶の実装（DuckDBバックエンド）"""
    
    def __init__(
        self,
        config: MemoryConfig = None,
        db_path: str = "data/mid_term.db",
        redis_enabled: bool = True,
        redis_host: str = 'localhost',
        redis_port: int = 6379
    ):
        """
        初期化
        
        Args:
            config: メモリ設定
            db_path: データベースパス
            redis_enabled: Redisキャッシュを有効化
            redis_host: Redisホスト
            redis_port: Redisポート
        """
        super().__init__()
        self.backend_type = "mid_term"
        self.config = config or MemoryConfig()
        self.db_path = Path(db_path)
        
        # データディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Redisキャッシュ初期化
        self.redis_cache: Optional[RedisCache] = None
        if redis_enabled:
            self.redis_cache = get_redis_cache(host=redis_host, port=redis_port)
        
        # DuckDB接続（Phase 1では簡易実装）
        self.storage: Dict[str, MemoryItem] = {}
        self._load_from_file()
        
        # 統計情報
        self.stats = {
            'total_stores': 0,
            'total_retrievals': 0,
            'total_deletions': 0,
            'db_size_bytes': 0,
            'redis_hits': 0,
            'redis_misses': 0,
        }
    
    def _load_from_file(self):
        """ファイルからデータを読み込み"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, item_data in data.items():
                        self.storage[key] = MemoryItem.from_dict(item_data)
            except Exception as e:
                print(f"Mid-term memory load error: {e}")
    
    def _save_to_file(self):
        """ファイルにデータを保存"""
        try:
            data = {}
            for key, item in self.storage.items():
                data[key] = item.to_dict()
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Mid-term memory save error: {e}")
    
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
            # 新しいアイテムを作成
            item = MemoryItem(key, value, metadata)
            
            # 容量制限チェック
            if len(self.storage) >= self.config.mid_term_max_items:
                # 最古のアイテムを削除（LRU）
                oldest_key = min(
                    self.storage.keys(),
                    key=lambda k: self.storage[k].accessed_at
                )
                del self.storage[oldest_key]
                # Redisからも削除
                if self.redis_cache and self.redis_cache.is_available():
                    self.redis_cache.delete(f"mid_term:{oldest_key}")
            
            # 保存
            self.storage[key] = item
            self.stats['total_stores'] += 1
            
            # Redisキャッシュに保存（TTL: 24時間）
            if self.redis_cache and self.redis_cache.is_available():
                cache_key = f"mid_term:{key}"
                self.redis_cache.set(
                    cache_key,
                    item.to_dict(),
                    expire_seconds=86400  # 24時間
                )
            
            # ファイルに永続化
            self._save_to_file()
            
            return True
            
        except Exception as e:
            print(f"Mid-term memory store error: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        データを取得（Redisキャッシュ優先）
        
        Args:
            key: 取得キー
            
        Returns:
            保存されたデータ、存在しない場合None
        """
        self.stats['total_retrievals'] += 1
        
        # 1. Redisキャッシュから取得試行
        if self.redis_cache and self.redis_cache.is_available():
            cache_key = f"mid_term:{key}"
            cached_data = self.redis_cache.get(cache_key, as_json=True)
            
            if cached_data:
                self.stats['redis_hits'] += 1
                # MemoryItemオブジェクトに復元
                item = MemoryItem.from_dict(cached_data)
                item.update_access()
                return item.value
            else:
                self.stats['redis_misses'] += 1
        
        # 2. JSONファイルから取得
        if key in self.storage:
            item = self.storage[key]
            item.update_access()
            
            # TTLチェック
            elapsed = (datetime.now() - item.created_at).total_seconds()
            if elapsed > self.config.mid_term_ttl_seconds:
                # 期限切れ
                del self.storage[key]
                self._save_to_file()
                # Redisからも削除
                if self.redis_cache and self.redis_cache.is_available():
                    self.redis_cache.delete(f"mid_term:{key}")
                return None
            
            # Redisキャッシュに再登録
            if self.redis_cache and self.redis_cache.is_available():
                cache_key = f"mid_term:{key}"
                self.redis_cache.set(cache_key, item.to_dict(), expire_seconds=86400)
            
            return item.value
        
        return None
    
    def delete(self, key: str) -> bool:
        """
        データを削除
        
        Args:
            key: 削除キー
            
        Returns:
            成功した場合True
        """
        # Redisから削除
        if self.redis_cache and self.redis_cache.is_available():
            self.redis_cache.delete(f"mid_term:{key}")
        
        # JSONファイルから削除
        if key in self.storage:
            del self.storage[key]
            self.stats['total_deletions'] += 1
            self._save_to_file()
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
        self._save_to_file()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        return {
            'backend_type': self.backend_type,
            'current_items': len(self.storage),
            'max_items': self.config.mid_term_max_items,
            'ttl_seconds': self.config.mid_term_ttl_seconds,
            'db_size_bytes': db_size,
            **self.stats
        }
    
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
            if elapsed > self.config.mid_term_ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.storage[key]
        
        if expired_keys:
            self._save_to_file()
        
        return len(expired_keys)
    
    def get_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        セッション情報を取得
        
        Args:
            limit: 取得件数
            
        Returns:
            セッション情報のリスト
        """
        sessions = []
        for key, item in self.storage.items():
            if key.startswith('session:'):
                sessions.append({
                    'session_id': key.replace('session:', ''),
                    'created_at': item.created_at.isoformat(),
                    'accessed_at': item.accessed_at.isoformat(),
                    'access_count': item.access_count
                })
        
        # アクセス日時でソート
        sessions.sort(key=lambda x: x['accessed_at'], reverse=True)
        return sessions[:limit]
    
    def store_session_summary(self, session_id: str, summary: Dict[str, Any]) -> bool:
        """
        セッションサマリーを保存
        
        Args:
            session_id: セッションID
            summary: サマリー情報
            
        Returns:
            成功した場合True
        """
        key = f"session:{session_id}"
        metadata = {
            'type': 'session_summary',
            'session_id': session_id
        }
        return self.store(key, summary, metadata)
    
    def retrieve_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションサマリーを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            サマリー情報、存在しない場合None
        """
        key = f"session:{session_id}"
        return self.retrieve(key)


class SessionManager:
    """セッション管理クラス"""
    
    def __init__(self, mid_term_memory: MidTermMemory):
        """
        初期化
        
        Args:
            mid_term_memory: 中期記憶インスタンス
        """
        self.memory = mid_term_memory
    
    def save_session(self, session_id: str, conversation_history: List[Dict],
                    metadata: Dict = None) -> bool:
        """
        セッションを保存
        
        Args:
            session_id: セッションID
            conversation_history: 会話履歴
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        summary = {
            'session_id': session_id,
            'total_turns': len(conversation_history),
            'start_time': conversation_history[0]['timestamp'] if conversation_history else '',
            'end_time': conversation_history[-1]['timestamp'] if conversation_history else '',
            'speakers': self._count_speakers(conversation_history),
            'metadata': metadata or {}
        }
        
        return self.memory.store_session_summary(session_id, summary)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションを読み込み
        
        Args:
            session_id: セッションID
            
        Returns:
            セッション情報、存在しない場合None
        """
        return self.memory.retrieve_session_summary(session_id)
    
    def list_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近のセッション一覧を取得
        
        Args:
            limit: 取得件数
            
        Returns:
            セッション情報のリスト
        """
        return self.memory.get_sessions(limit)
    
    def _count_speakers(self, history: List[Dict]) -> Dict[str, int]:
        """
        発話者ごとの発言数をカウント
        
        Args:
            history: 会話履歴
            
        Returns:
            発話者ごとのカウント
        """
        speakers = {}
        for turn in history:
            speaker = turn.get('speaker', 'Unknown')
            speakers[speaker] = speakers.get(speaker, 0) + 1
        return speakers