"""ChatService - Phase 1-3統合チャットサービス.

FastAPI（非同期）とLangGraph（同期）を橋渡しする統合レイヤー。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from main import MultiLLMChat

logger = logging.getLogger(__name__)


class ChatService:
    """Phase 1-3統合チャットサービス.

    機能:
    - 非同期会話実行（Phase 3 FastAPI → Phase 1 LangGraph）
    - ユーザー別セッション管理
    - ストリーミング応答対応
    - マルチユーザー対応（セッションID変換）
    """

    def __init__(self):
        """ChatService初期化."""
        # Phase 1コアインスタンス（プロセスごと1つ）
        self.multi_llm_chat = MultiLLMChat()
        logger.info("MultiLLMChat initialized")

        # ユーザーセッションマップ: {user_id: {session_id: Phase1SessionID}}
        self.user_sessions: Dict[str, Dict[str, str]] = {}
        logger.info("ChatService initialized")

    async def chat(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        character: Optional[str] = None,
    ) -> Dict[str, Any]:
        """非同期会話実行.

        Args:
            user_id: ユーザーID（JWT認証から取得）
            session_id: セッションID（クライアント指定）
            user_input: ユーザー入力テキスト
            character: 指定キャラクター（optional）

        Returns:
            Dict[str, Any]: 会話レスポンス
            {
                'session_id': セッションID,
                'response': AI応答テキスト,
                'character': 応答キャラクター,
                'timestamp': タイムスタンプ,
                'metadata': {
                    'model': モデル名,
                    'tokens': トークン数,
                    'processing_time_ms': 処理時間（ミリ秒）
                }
            }

        Raises:
            Exception: LangGraph実行エラー
        """
        try:
            start_time = datetime.now()

            # ユーザー専用セッションID取得
            phase1_session_id = self._get_phase1_session_id(user_id, session_id)
            logger.info(
                f"Chat request: user={user_id}, session={session_id}, phase1_session={phase1_session_id}"
            )

            # Phase 1同期処理を非同期実行（asyncio.to_thread）
            result = await asyncio.to_thread(
                self.multi_llm_chat.chat,
                user_input=user_input,
                session_id=phase1_session_id,
                character=character,
            )

            # 処理時間計算
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # レスポンス整形（Phase 3形式）
            response = {
                "session_id": session_id,  # クライアント指定のセッションIDを返却
                "response": result["response"],
                "character": result.get("speaker", character or "lumina"),  # speakerまたは指定キャラクター
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "model": result.get("metadata", {}).get("model", "unknown"),
                    "tokens": result.get("metadata", {}).get("tokens", 0),
                    "processing_time_ms": int(processing_time),
                },
            }

            logger.info(
                f"Chat success: user={user_id}, character={response['character']}, time={processing_time:.2f}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}", exc_info=True)
            raise

    async def stream_chat(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        character: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """非同期ストリーミング会話.

        Args:
            user_id: ユーザーID
            session_id: セッションID
            user_input: ユーザー入力テキスト
            character: 指定キャラクター（optional）

        Yields:
            str: 応答テキストの文字列（1文字ずつ）

        Notes:
            現在は疑似ストリーミング（通常会話結果を分割）
            TODO: LangGraphストリーミングサポート実装後に真のストリーミング対応
        """
        try:
            logger.info(f"Stream chat request: user={user_id}, session={session_id}")

            # 通常会話実行
            result = await self.chat(user_id, session_id, user_input, character)
            response_text = result["response"]

            # 文字ごとにストリーミング（疑似ストリーミング）
            for i, char in enumerate(response_text):
                yield char
                # ストリーミング効果（10ms間隔）
                if i % 5 == 0:  # 5文字ごとにsleep（パフォーマンス最適化）
                    await asyncio.sleep(0.01)

            logger.info(
                f"Stream chat completed: user={user_id}, chars={len(response_text)}"
            )

        except Exception as e:
            logger.error(f"Stream chat error for user {user_id}: {e}", exc_info=True)
            raise

    async def get_conversation_history(
        self, user_id: str, session_id: str, limit: int = 50
    ) -> Dict[str, Any]:
        """会話履歴取得.

        Args:
            user_id: ユーザーID
            session_id: セッションID
            limit: 取得件数上限

        Returns:
            Dict[str, Any]: 会話履歴
            {
                'session_id': セッションID,
                'history': [
                    {'role': 'user', 'content': '...', 'timestamp': '...'},
                    {'role': 'assistant', 'content': '...', 'timestamp': '...'},
                    ...
                ],
                'total_turns': 総ターン数
            }
        """
        try:
            phase1_session_id = self._get_phase1_session_id(user_id, session_id)

            # Phase 1記憶マネージャーから履歴取得
            context = await asyncio.to_thread(
                self.multi_llm_chat.memory.get_conversation_context,
                session_id=phase1_session_id,
            )

            # 履歴整形
            history = context.get("history", [])[-limit:]  # 最新limit件

            return {
                "session_id": session_id,
                "history": history,
                "total_turns": len(context.get("history", [])),
            }

        except Exception as e:
            logger.error(f"Get history error for user {user_id}: {e}", exc_info=True)
            raise

    async def list_sessions(self, user_id: str) -> Dict[str, Any]:
        """ユーザーのセッション一覧取得.

        Args:
            user_id: ユーザーID

        Returns:
            Dict[str, Any]: セッション一覧
            {
                'user_id': ユーザーID,
                'sessions': [
                    {'session_id': '...', 'turn_count': 10, 'last_activity': '...'},
                    ...
                ],
                'total_sessions': 総セッション数
            }
        """
        try:
            user_session_map = self.user_sessions.get(user_id, {})
            sessions = []

            for session_id, phase1_session_id in user_session_map.items():
                # 各セッションの情報取得
                context = await asyncio.to_thread(
                    self.multi_llm_chat.memory.get_conversation_context,
                    session_id=phase1_session_id,
                )

                sessions.append(
                    {
                        "session_id": session_id,
                        "turn_count": len(context.get("history", [])),
                        "last_activity": context.get("last_activity", "N/A"),
                    }
                )

            return {
                "user_id": user_id,
                "sessions": sessions,
                "total_sessions": len(sessions),
            }

        except Exception as e:
            logger.error(f"List sessions error for user {user_id}: {e}", exc_info=True)
            raise

    async def clear_session(self, user_id: str, session_id: str) -> bool:
        """セッションクリア.

        Args:
            user_id: ユーザーID
            session_id: セッションID

        Returns:
            bool: クリア成功（True）
        """
        try:
            phase1_session_id = self._get_phase1_session_id(user_id, session_id)

            # Phase 1記憶マネージャーでセッションクリア
            await asyncio.to_thread(
                self.multi_llm_chat.memory.clear_session,
                session_id=phase1_session_id,
            )

            # ユーザーセッションマップから削除
            if (
                user_id in self.user_sessions
                and session_id in self.user_sessions[user_id]
            ):
                del self.user_sessions[user_id][session_id]

            logger.info(f"Session cleared: user={user_id}, session={session_id}")
            return True

        except Exception as e:
            logger.error(f"Clear session error for user {user_id}: {e}", exc_info=True)
            raise

    def _get_phase1_session_id(self, user_id: str, session_id: str) -> str:
        """ユーザー専用Phase 1セッションID取得.

        セッションID変換ルール:
        Phase 3 セッションID: "session-abc123"（ユーザーが指定）
        ↓
        Phase 1 セッションID: "user_{user_id}_session-abc123"（内部変換）

        Args:
            user_id: ユーザーID
            session_id: セッションID（クライアント指定）

        Returns:
            str: Phase 1用セッションID
        """
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}

        if session_id not in self.user_sessions[user_id]:
            # Phase 1用セッションID生成
            phase1_session_id = f"user_{user_id}_{session_id}"
            self.user_sessions[user_id][session_id] = phase1_session_id
            logger.info(f"New Phase 1 session created: {phase1_session_id}")

        return self.user_sessions[user_id][session_id]


# グローバルインスタンス（FastAPIアプリケーション起動時使用）
chat_service = ChatService()
