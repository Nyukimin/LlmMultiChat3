"""WebSocket API.

リアルタイム双方向通信API。

Phase 3 Week 9-2:
- WebSocket接続管理
- 認証チェック
- メッセージハンドリング
- ストリーミング応答

使用例:
    >>> # JavaScriptクライアント
    >>> const ws = new WebSocket('ws://localhost:8000/ws/chat');
    >>> 
    >>> // 認証
    >>> ws.send(JSON.stringify({
    ...     type: 'auth',
    ...     token: 'your_jwt_token'
    ... }));
    >>> 
    >>> // 会話
    >>> ws.send(JSON.stringify({
    ...     type: 'chat',
    ...     session_id: 'session-123',
    ...     user_input: 'こんにちは'
    ... }));
"""

from typing import Dict, Optional, Any
import logging
import json
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from security.jwt_manager import JWTManager
from security.user_manager import UserManager
from exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    InputValidationError,
    LLMError
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket接続管理クラス.
    
    複数のWebSocket接続を管理し、メッセージのブロードキャストや
    個別送信を行います。
    
    Attributes:
        active_connections: アクティブな接続の辞書（user_id -> WebSocket）
        connection_metadata: 接続メタデータ（user_id -> metadata）
    """
    
    def __init__(self):
        """ConnectionManagerを初期化."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ConnectionManager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None
    ) -> str:
        """WebSocket接続を受け入れ.
        
        Args:
            websocket: WebSocketインスタンス
            user_id: ユーザーID（認証前はNone）
        
        Returns:
            str: 接続ID
        """
        await websocket.accept()
        
        connection_id = user_id or f"guest-{id(websocket)}"
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "authenticated": user_id is not None
        }
        
        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(authenticated={user_id is not None})"
        )
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """WebSocket接続を切断.
        
        Args:
            connection_id: 接続ID
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """特定の接続にメッセージを送信.
        
        Args:
            connection_id: 接続ID
            message: 送信するメッセージ（JSON）
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    logger.warning(
                        f"Cannot send to disconnected WebSocket: {connection_id}"
                    )
                    self.disconnect(connection_id)
            except Exception as e:
                logger.error(
                    f"Error sending WebSocket message to {connection_id}: {e}"
                )
                self.disconnect(connection_id)
    
    async def send_text(
        self,
        connection_id: str,
        text: str
    ):
        """特定の接続にテキストメッセージを送信.
        
        Args:
            connection_id: 接続ID
            text: 送信するテキスト
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(text)
                else:
                    self.disconnect(connection_id)
            except Exception as e:
                logger.error(
                    f"Error sending WebSocket text to {connection_id}: {e}"
                )
                self.disconnect(connection_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """全接続にメッセージをブロードキャスト.
        
        Args:
            message: ブロードキャストするメッセージ（JSON）
        """
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(connection_id)
            except Exception as e:
                logger.error(
                    f"Error broadcasting to {connection_id}: {e}"
                )
                disconnected.append(connection_id)
        
        # 切断された接続をクリーンアップ
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    def get_active_count(self) -> int:
        """アクティブな接続数を取得.
        
        Returns:
            int: アクティブな接続数
        """
        return len(self.active_connections)
    
    def is_connected(self, connection_id: str) -> bool:
        """指定IDの接続が存在するか確認.
        
        Args:
            connection_id: 接続ID
        
        Returns:
            bool: 接続が存在するか
        """
        return connection_id in self.active_connections


# グローバルConnectionManagerインスタンス
manager = ConnectionManager()


class WebSocketHandler:
    """WebSocketメッセージハンドラークラス.
    
    受信したメッセージを処理し、適切なアクションを実行します。
    """
    
    def __init__(
        self,
        jwt_manager: JWTManager,
        user_manager: UserManager
    ):
        """WebSocketHandlerを初期化.
        
        Args:
            jwt_manager: JWT管理インスタンス
            user_manager: ユーザー管理インスタンス
        """
        self.jwt_manager = jwt_manager
        self.user_manager = user_manager
    
    async def handle_auth(
        self,
        connection_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """認証メッセージを処理.
        
        Args:
            connection_id: 接続ID
            data: メッセージデータ
        
        Returns:
            dict: 応答メッセージ
        """
        token = data.get("token")
        
        if not token:
            return {
                "type": "auth_response",
                "status": "error",
                "message": "Token is required"
            }
        
        try:
            payload = self.jwt_manager.verify_token(
                token,
                expected_type="access"
            )
            
            user_id = payload.get("sub")
            
            # 接続メタデータ更新
            if connection_id in manager.connection_metadata:
                manager.connection_metadata[connection_id]["user_id"] = user_id
                manager.connection_metadata[connection_id]["authenticated"] = True
            
            logger.info(f"WebSocket authenticated: {connection_id} (user={user_id})")
            
            return {
                "type": "auth_response",
                "status": "success",
                "user_id": user_id
            }
            
        except (TokenExpiredError, InvalidTokenError) as e:
            logger.warning(f"WebSocket auth failed: {e.message}")
            
            return {
                "type": "auth_response",
                "status": "error",
                "message": e.message
            }
    
    async def handle_chat(
        self,
        connection_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """会話メッセージを処理.
        
        Args:
            connection_id: 接続ID
            data: メッセージデータ
        
        Returns:
            dict: 応答メッセージ
        """
        # 認証チェック
        metadata = manager.connection_metadata.get(connection_id, {})
        if not metadata.get("authenticated"):
            return {
                "type": "error",
                "message": "Authentication required"
            }
        
        session_id = data.get("session_id")
        user_input = data.get("user_input")
        character = data.get("character")
        
        if not session_id or not user_input:
            return {
                "type": "error",
                "message": "session_id and user_input are required"
            }
        
        try:
            # TODO: Phase 1のLangGraphコアを使用
            # chat_manager = ...
            # response = await chat_manager.chat(
            #     session_id=session_id,
            #     user_id=metadata["user_id"],
            #     user_input=user_input,
            #     character=character
            # )
            
            # モック応答（Phase 1統合後に削除）
            logger.info(
                f"WebSocket chat: user={metadata['user_id']}, "
                f"session={session_id}"
            )
            
            return {
                "type": "chat_response",
                "session_id": session_id,
                "character": character or "lumina",
                "response": f"WebSocketモック応答: {user_input}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except InputValidationError as e:
            return {
                "type": "error",
                "message": e.message
            }
        
        except LLMError as e:
            logger.error(f"LLM error in WebSocket: {e.message}")
            return {
                "type": "error",
                "message": "LLM service temporarily unavailable"
            }
    
    async def handle_ping(
        self,
        connection_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pingメッセージを処理.
        
        Args:
            connection_id: 接続ID
            data: メッセージデータ
        
        Returns:
            dict: Pong応答
        """
        return {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }


async def websocket_endpoint(
    websocket: WebSocket,
    jwt_manager: JWTManager,
    user_manager: UserManager
):
    """WebSocketエンドポイント.
    
    Args:
        websocket: WebSocketインスタンス
        jwt_manager: JWT管理インスタンス
        user_manager: ユーザー管理インスタンス
    """
    connection_id = None
    
    try:
        # 接続受け入れ
        connection_id = await manager.connect(websocket)
        
        # ハンドラー初期化
        handler = WebSocketHandler(
            jwt_manager=jwt_manager,
            user_manager=user_manager
        )
        
        # メッセージループ
        while True:
            # メッセージ受信
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if not message_type:
                await manager.send_message(connection_id, {
                    "type": "error",
                    "message": "Message type is required"
                })
                continue
            
            # メッセージタイプに応じて処理
            if message_type == "auth":
                response = await handler.handle_auth(connection_id, data)
            elif message_type == "chat":
                response = await handler.handle_chat(connection_id, data)
            elif message_type == "ping":
                response = await handler.handle_ping(connection_id, data)
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
            
            # 応答送信
            await manager.send_message(connection_id, response)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {connection_id}")
    
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON from WebSocket: {connection_id}")
        await manager.send_message(connection_id, {
            "type": "error",
            "message": "Invalid JSON format"
        })
    
    except Exception as e:
        logger.error(
            f"WebSocket error for {connection_id}: {e}",
            exc_info=True
        )
    
    finally:
        # 接続クリーンアップ
        if connection_id:
            manager.disconnect(connection_id)