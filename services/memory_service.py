"""MemoryService - Phase 1-3統合記憶サービス.

Phase 1記憶マネージャーをFastAPI（非同期）で利用可能にする統合レイヤー。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from memory_manager import MemorySystemManager

logger = logging.getLogger(__name__)


class MemoryService:
    """Phase 1-3統合記憶サービス.

    機能:
    - 記憶検索（非同期）
    - 記憶統計取得
    - 記憶保存・削除
    - ユーザー別記憶管理
    """

    def __init__(self, memory_manager: Optional[MemorySystemManager] = None):
        """MemoryService初期化.

        Args:
            memory_manager: Phase 1記憶マネージャー（Noneなら新規作成）
        """
        if memory_manager is None:
            # テスト用: MemoryManagerを新規作成
            self.memory_manager = MemorySystemManager()
            self.memory_manager.initialize_characters()
            logger.info("MemoryService initialized with new MemoryManager")
        else:
            self.memory_manager = memory_manager
            logger.info("MemoryService initialized with provided MemoryManager")

    def set_memory_manager(self, memory_manager: MemorySystemManager):
        """記憶マネージャー設定.

        Args:
            memory_manager: Phase 1記憶マネージャー
        """
        self.memory_manager = memory_manager
        logger.info("MemoryManager set in MemoryService")

    async def search(
        self,
        user_id: str,
        query: str,
        layers: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """記憶検索（非同期）.

        Args:
            user_id: ユーザーID
            query: 検索クエリ
            layers: 検索対象レイヤー（省略時: 短期・中期・長期）
            limit: 取得件数上限

        Returns:
            List[Dict[str, Any]]: 検索結果
            [
                {
                    'memory_id': 記憶ID,
                    'content': 記憶内容,
                    'layer': レイヤー名,
                    'timestamp': タイムスタンプ,
                    'relevance_score': 関連度スコア
                },
                ...
            ]
        """
        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.info(f"Memory search: user={user_id}, query={query[:50]}...")

            # デフォルトレイヤー設定
            if layers is None:
                layers = ["short_term", "mid_term", "long_term"]

            # Phase 1記憶検索を非同期実行
            results = await asyncio.to_thread(
                self.memory_manager.search_memory,
                query=query,
                layers=layers,
                limit=limit,
            )

            logger.info(
                f"Memory search completed: user={user_id}, results={len(results)}"
            )
            return results

        except Exception as e:
            logger.error(f"Memory search error for user {user_id}: {e}", exc_info=True)
            raise

    async def get_stats(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """記憶統計取得（非同期）.

        Args:
            user_id: ユーザーID
            session_id: セッションID（省略時: 全セッション統計）

        Returns:
            Dict[str, Any]: 記憶統計
            {
                'total_memories': 総記憶数,
                'by_layer': {
                    'short_term': 短期記憶数,
                    'mid_term': 中期記憶数,
                    'long_term': 長期記憶数,
                    'knowledge_base': 知識ベース数
                },
                'total_sessions': 総セッション数,
                'total_turns': 総ターン数,
                'character_stats': {
                    'lumina': {...},
                    'clarissa': {...},
                    'nox': {...}
                }
            }
        """
        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.info(f"Memory stats request: user={user_id}, session={session_id}")

            # Phase 1記憶統計を非同期実行
            stats = await asyncio.to_thread(
                self.memory_manager.get_memory_stats, session_id=session_id
            )

            logger.info(
                f"Memory stats retrieved: user={user_id}, total={stats.get('total_memories', 0)}"
            )
            return stats

        except Exception as e:
            logger.error(f"Memory stats error for user {user_id}: {e}", exc_info=True)
            raise

    async def store(
        self,
        user_id: str,
        session_id: str,
        content: str,
        layer: str = "short_term",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """記憶保存（非同期）.

        Args:
            user_id: ユーザーID
            session_id: セッションID
            content: 記憶内容
            layer: 保存先レイヤー（'short_term', 'mid_term', 'long_term'）
            metadata: メタデータ（optional）

        Returns:
            Dict[str, Any]: 保存結果
            {
                'memory_id': 記憶ID,
                'layer': レイヤー名,
                'timestamp': タイムスタンプ
            }
        """
        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.info(
                f"Memory store: user={user_id}, session={session_id}, layer={layer}"
            )

            # Phase 1記憶保存を非同期実行
            result = await asyncio.to_thread(
                self.memory_manager.store_memory,
                session_id=session_id,
                content=content,
                layer=layer,
                metadata=metadata or {},
            )

            logger.info(
                f"Memory stored: user={user_id}, memory_id={result.get('memory_id')}"
            )
            return result

        except Exception as e:
            logger.error(f"Memory store error for user {user_id}: {e}", exc_info=True)
            raise

    async def delete(self, user_id: str, memory_id: str) -> bool:
        """記憶削除（非同期）.

        Args:
            user_id: ユーザーID
            memory_id: 記憶ID

        Returns:
            bool: 削除成功（True）
        """
        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.info(f"Memory delete: user={user_id}, memory_id={memory_id}")

            # Phase 1記憶削除を非同期実行
            success = await asyncio.to_thread(
                self.memory_manager.delete_memory, memory_id=memory_id
            )

            logger.info(
                f"Memory deleted: user={user_id}, memory_id={memory_id}, success={success}"
            )
            return success

        except Exception as e:
            logger.error(f"Memory delete error for user {user_id}: {e}", exc_info=True)
            raise

    async def get_session_memories(
        self, user_id: str, session_id: str, limit: int = 50
    ) -> Dict[str, Any]:
        """セッション記憶取得（非同期）.

        Args:
            user_id: ユーザーID
            session_id: セッションID
            limit: 取得件数上限

        Returns:
            Dict[str, Any]: セッション記憶
            {
                'session_id': セッションID,
                'memories': [
                    {'memory_id': '...', 'content': '...', 'timestamp': '...'},
                    ...
                ],
                'total_memories': 総記憶数
            }
        """
        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.info(
                f"Session memories request: user={user_id}, session={session_id}"
            )

            # Phase 1セッション記憶取得を非同期実行
            memories = await asyncio.to_thread(
                self.memory_manager.get_session_memories,
                session_id=session_id,
                limit=limit,
            )

            return {
                "session_id": session_id,
                "memories": memories,
                "total_memories": len(memories),
            }

        except Exception as e:
            logger.error(
                f"Session memories error for user {user_id}: {e}", exc_info=True
            )
            raise

    async def flush(self, user_id: str, confirm: bool = False) -> Dict[str, Any]:
        """記憶フラッシュ（非同期、admin専用）.

        Args:
            user_id: ユーザーID
            confirm: 確認フラグ（True必須）

        Returns:
            Dict[str, Any]: フラッシュ結果
            {
                'flushed_memories': フラッシュ済み記憶数,
                'flushed_sessions': フラッシュ済みセッション数
            }

        Raises:
            ValueError: confirm=Falseの場合
        """
        if not confirm:
            raise ValueError("Memory flush requires confirmation (confirm=True)")

        if not self.memory_manager:
            raise RuntimeError("MemoryManager not initialized")

        try:
            logger.warning(f"Memory flush requested by user={user_id}")

            # Phase 1記憶フラッシュを非同期実行
            result = await asyncio.to_thread(self.memory_manager.flush_all)

            logger.warning(
                f"Memory flushed: memories={result.get('flushed_memories', 0)}"
            )
            return result

        except Exception as e:
            logger.error(f"Memory flush error for user {user_id}: {e}", exc_info=True)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック（非同期）.

        Returns:
            Dict[str, Any]: ヘルスチェック結果
            {
                'status': 'healthy' | 'unhealthy',
                'memory_manager': 'initialized' | 'not_initialized',
                'layers': {
                    'short_term': 'ok',
                    'mid_term': 'ok',
                    'long_term': 'ok',
                    'knowledge_base': 'ok'
                }
            }
        """
        try:
            if not self.memory_manager:
                return {
                    "status": "unhealthy",
                    "memory_manager": "not_initialized",
                    "layers": {},
                }

            # 記憶マネージャーヘルスチェック
            health = await asyncio.to_thread(self.memory_manager.health_check)

            return {
                "status": "healthy" if all(health.values()) else "unhealthy",
                "memory_manager": "initialized",
                "layers": health,
            }

        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "memory_manager": "error",
                "layers": {},
                "error": str(e),
            }


# グローバルインスタンス（FastAPIアプリケーション起動時使用）
memory_service = MemoryService()
