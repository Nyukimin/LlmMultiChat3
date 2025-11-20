"""Chat Routes.

LLM会話API エンドポイント。

Phase 3 Week 9-1:
- テキスト会話
- 会話履歴取得
- セッション管理
- ストリーミング応答
- キャラクター選択

使用例:
    >>> # 会話開始
    >>> POST /api/v1/chat
    >>> {
    ...     "session_id": "session-123",
    ...     "user_input": "こんにちは",
    ...     "character": "lumina"
    ... }
    >>> 
    >>> # 会話履歴取得
    >>> GET /api/v1/chat/history/session-123?limit=50
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.middleware.auth_middleware import get_current_user
from security.models import User
from exceptions import (
    InputValidationError,
    SessionNotFoundError,
    CharacterNotFoundError,
    LLMError
)
from services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ===== リクエスト/レスポンスモデル =====

class ChatRequest(BaseModel):
    """会話リクエスト."""
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="セッションID（一意識別子）"
    )
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="ユーザー入力テキスト（1-5000文字）"
    )
    character: Optional[str] = Field(
        None,
        description="応答するキャラクター名（lumina/clarisse/nox）。未指定の場合は自動選択"
    )
    stream: bool = Field(
        False,
        description="ストリーミング応答を有効にする"
    )
    
    @validator('character')
    def validate_character(cls, v):
        """キャラクター名検証."""
        if v is not None:
            valid_characters = ["lumina", "clarisse", "nox"]
            if v.lower() not in valid_characters:
                raise ValueError(
                    f"Invalid character. Must be one of: {', '.join(valid_characters)}"
                )
            return v.lower()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "user_input": "最近のAI技術の進化について教えて",
                "character": "lumina",
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """会話レスポンス."""
    
    session_id: str
    character: str
    response: str
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="メタデータ（処理時間、使用モデル等）"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "character": "lumina",
                "response": "AI技術は近年急速に進化しています...",
                "metadata": {
                    "llm_node": "lumina_node",
                    "model": "gpt-4o",
                    "processing_time_ms": 1234,
                    "tokens_used": 156
                },
                "timestamp": "2025-11-13T23:00:00.000Z"
            }
        }


class MessageHistory(BaseModel):
    """メッセージ履歴."""
    
    role: str = Field(..., description="ロール（user/assistant/system）")
    content: str = Field(..., description="メッセージ内容")
    character: Optional[str] = Field(None, description="キャラクター名")
    timestamp: str = Field(..., description="タイムスタンプ")


class ChatHistoryResponse(BaseModel):
    """会話履歴レスポンス."""
    
    session_id: str
    messages: List[MessageHistory]
    total_count: int
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "messages": [
                    {
                        "role": "user",
                        "content": "こんにちは",
                        "character": None,
                        "timestamp": "2025-11-13T23:00:00.000Z"
                    },
                    {
                        "role": "assistant",
                        "content": "こんにちは！何かお手伝いできることはありますか?",
                        "character": "lumina",
                        "timestamp": "2025-11-13T23:00:01.000Z"
                    }
                ],
                "total_count": 2
            }
        }


class SessionInfo(BaseModel):
    """セッション情報."""
    
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    message_count: int
    characters_used: List[str]


class SessionListResponse(BaseModel):
    """セッション一覧レスポンス."""
    
    sessions: List[SessionInfo]
    total_count: int


# ===== エンドポイント =====

@router.post(
    "/",
    response_model=ChatResponse,
    summary="会話実行",
    description="ユーザー入力に対してLLMが応答します。セッションIDで会話を管理します。",
    responses={
        200: {"description": "会話成功"},
        400: {"description": "入力検証エラー"},
        401: {"description": "未認証"},
        503: {"description": "LLMサービス利用不可"}
    }
)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """会話エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        chat_request: 会話リクエスト
        current_user: 現在のユーザー
    
    Returns:
        ChatResponse: LLM応答
    
    Raises:
        HTTPException: 入力検証エラー、LLMエラー等
    """
    try:
        # Phase 1-3統合: ChatService呼び出し
        result = await chat_service.chat(
            user_id=current_user.user_id,
            session_id=chat_request.session_id,
            user_input=chat_request.user_input,
            character=chat_request.character
        )
        
        # レスポンス整形
        response = ChatResponse(
            session_id=result['session_id'],
            character=result['character'],
            response=result['response'],
            metadata=result['metadata'],
            timestamp=result['timestamp']
        )
        
        logger.info(
            f"Chat request processed: "
            f"user={current_user.user_id}, session={chat_request.session_id}, "
            f"character={response.character}"
        )
        
        return response
        
    except InputValidationError as e:
        logger.warning(f"Input validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except CharacterNotFoundError as e:
        logger.warning(f"Character not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except LLMError as e:
        logger.error(f"LLM error: {e.message}", extra={"details": e.details})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service temporarily unavailable"
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed"
        )


@router.post(
    "/stream",
    summary="ストリーミング会話",
    description="Server-Sent Events (SSE)形式でストリーミング応答を返します。",
    responses={
        200: {"description": "ストリーミング開始"},
        401: {"description": "未認証"},
        503: {"description": "LLMサービス利用不可"}
    }
)
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """ストリーミング会話エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        chat_request: 会話リクエスト
        current_user: 現在のユーザー
    
    Returns:
        StreamingResponse: SSEストリーミング
    """
    async def generate():
        """SSEストリームジェネレーター."""
        try:
            # Phase 1-3統合: ChatService ストリーミング呼び出し
            async for chunk in chat_service.stream_chat(
                user_id=current_user.user_id,
                session_id=chat_request.session_id,
                user_input=chat_request.user_input,
                character=chat_request.character
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
            logger.info(
                f"Stream chat completed: "
                f"user={current_user.user_id}, session={chat_request.session_id}"
            )
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield "data: {\"error\": \"Streaming failed\"}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="会話履歴取得",
    description="指定セッションの会話履歴を取得します。",
    responses={
        200: {"description": "履歴取得成功"},
        401: {"description": "未認証"},
        404: {"description": "セッションが存在しない"}
    }
)
async def get_history(
    request: Request,
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
) -> ChatHistoryResponse:
    """会話履歴取得エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        session_id: セッションID
        limit: 取得件数上限（デフォルト50）
        offset: オフセット（デフォルト0）
        current_user: 現在のユーザー
    
    Returns:
        ChatHistoryResponse: 会話履歴
    
    Raises:
        HTTPException: セッションが存在しない
    """
    try:
        # Phase 1-3統合: ChatService 履歴取得呼び出し
        result = await chat_service.get_conversation_history(
            user_id=current_user.user_id,
            session_id=session_id,
            limit=limit
        )
        
        # レスポンス整形
        messages = [
            MessageHistory(
                role=msg.get('role', 'user'),
                content=msg.get('content', ''),
                character=msg.get('character'),
                timestamp=msg.get('timestamp', datetime.utcnow().isoformat())
            )
            for msg in result['history']
        ]
        
        history_response = ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            total_count=result['total_turns']
        )
        
        logger.info(
            f"History retrieved: user={current_user.user_id}, "
            f"session={session_id}, count={len(messages)}"
        )
        
        return history_response
        
    except SessionNotFoundError as e:
        logger.warning(f"Session not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"History retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="History retrieval failed"
        )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="セッション一覧取得",
    description="現在のユーザーの全セッション一覧を取得します。",
    responses={
        200: {"description": "一覧取得成功"},
        401: {"description": "未認証"}
    }
)
async def list_sessions(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
) -> SessionListResponse:
    """セッション一覧取得エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        limit: 取得件数上限（デフォルト20）
        offset: オフセット（デフォルト0）
        current_user: 現在のユーザー
    
    Returns:
        SessionListResponse: セッション一覧
    """
    try:
        # Phase 1-3統合: ChatService セッション一覧取得呼び出し
        result = await chat_service.list_sessions(
            user_id=current_user.user_id
        )
        
        # レスポンス整形
        sessions = [
            SessionInfo(
                session_id=sess['session_id'],
                user_id=current_user.user_id,
                created_at=sess.get('last_activity', datetime.utcnow().isoformat()),
                last_activity=sess.get('last_activity', datetime.utcnow().isoformat()),
                message_count=sess.get('turn_count', 0),
                characters_used=sess.get('characters_used', ['lumina'])  # Phase 1-3統合: セッションデータからキャラクター取得
            )
            for sess in result['sessions'][offset:offset+limit]
        ]
        
        session_list = SessionListResponse(
            sessions=sessions,
            total_count=result['total_sessions']
        )
        
        logger.info(
            f"Sessions retrieved: user={current_user.user_id}, "
            f"count={len(sessions)}"
        )
        
        return session_list
        
    except Exception as e:
        logger.error(f"Session listing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session listing failed"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="セッション削除",
    description="指定セッションとその会話履歴を削除します。",
    responses={
        200: {"description": "削除成功"},
        401: {"description": "未認証"},
        404: {"description": "セッションが存在しない"}
    }
)
async def delete_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """セッション削除エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        session_id: セッションID
        current_user: 現在のユーザー
    
    Returns:
        dict: 削除結果
    
    Raises:
        HTTPException: セッションが存在しない
    """
    try:
        # Phase 1-3統合: ChatService セッションクリア呼び出し
        success = await chat_service.clear_session(
            user_id=current_user.user_id,
            session_id=session_id
        )
        
        if not success:
            raise SessionNotFoundError(
                message=f"Session {session_id} not found",
                session_id=session_id
            )
        
        logger.info(
            f"Session cleared: user={current_user.user_id}, session={session_id}"
        )
        
        return {
            "status": "success",
            "message": f"Session {session_id} cleared successfully"
        }
        
    except SessionNotFoundError as e:
        logger.warning(f"Session deletion failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Session deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session deletion failed"
        )