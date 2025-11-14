"""Memory Routes.

5階層記憶システムAPI エンドポイント。

Phase 3 Week 9-1:
- 記憶検索
- 記憶保存
- 記憶削除
- 統計情報取得

使用例:
    >>> # 記憶検索
    >>> POST /api/v1/memory/search
    >>> {
    ...     "query": "AIについて",
    ...     "memory_types": ["short_term", "long_term"],
    ...     "limit": 10
    ... }
    >>> 
    >>> # 記憶統計
    >>> GET /api/v1/memory/stats
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.middleware.auth_middleware import get_current_user, require_permission
from security.models import User
from exceptions import (
    MemoryNotFoundError,
    MemoryStorageError,
    InvalidMemoryTypeError
)
from services import memory_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ===== リクエスト/レスポンスモデル =====

class MemorySearchRequest(BaseModel):
    """記憶検索リクエスト."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="検索クエリ"
    )
    memory_types: List[str] = Field(
        default=["short_term", "mid_term", "long_term"],
        description="検索対象記憶タイプ"
    )
    session_id: Optional[str] = Field(
        None,
        description="セッションID（指定時はそのセッションの記憶のみ検索）"
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="取得件数上限（1-100）"
    )
    
    @validator('memory_types')
    def validate_memory_types(cls, v):
        """記憶タイプ検証."""
        valid_types = ["short_term", "mid_term", "long_term", "associative", "knowledge"]
        for memory_type in v:
            if memory_type not in valid_types:
                raise ValueError(
                    f"Invalid memory type: {memory_type}. "
                    f"Must be one of: {', '.join(valid_types)}"
                )
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "AIについて学んだこと",
                "memory_types": ["short_term", "long_term"],
                "session_id": "session-123",
                "limit": 10
            }
        }


class MemoryItem(BaseModel):
    """記憶アイテム."""
    
    memory_id: str
    memory_type: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float
    timestamp: str


class MemorySearchResponse(BaseModel):
    """記憶検索レスポンス."""
    
    query: str
    results: List[MemoryItem]
    total_count: int
    
    class Config:
        schema_extra = {
            "example": {
                "query": "AIについて学んだこと",
                "results": [
                    {
                        "memory_id": "mem-123",
                        "memory_type": "long_term",
                        "content": "AIは機械学習、深層学習などの技術を含む...",
                        "metadata": {
                            "session_id": "session-123",
                            "character": "lumina"
                        },
                        "relevance_score": 0.95,
                        "timestamp": "2025-11-13T23:00:00.000Z"
                    }
                ],
                "total_count": 1
            }
        }


class MemoryStoreRequest(BaseModel):
    """記憶保存リクエスト."""
    
    memory_type: str = Field(
        ...,
        description="記憶タイプ（short_term/mid_term/long_term/associative/knowledge）"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="記憶内容"
    )
    session_id: Optional[str] = Field(
        None,
        description="セッションID"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="メタデータ"
    )
    
    @validator('memory_type')
    def validate_memory_type(cls, v):
        """記憶タイプ検証."""
        valid_types = ["short_term", "mid_term", "long_term", "associative", "knowledge"]
        if v not in valid_types:
            raise ValueError(
                f"Invalid memory type: {v}. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "memory_type": "long_term",
                "content": "ユーザーはAI技術に興味があり、特に機械学習分野を学びたい",
                "session_id": "session-123",
                "metadata": {
                    "character": "lumina",
                    "importance": "high"
                }
            }
        }


class MemoryStoreResponse(BaseModel):
    """記憶保存レスポンス."""
    
    status: str = "success"
    message: str = "Memory stored successfully"
    memory_id: str
    memory_type: str


class MemoryStats(BaseModel):
    """記憶統計."""
    
    total_memories: int
    by_type: Dict[str, int]
    by_session: Dict[str, int]
    storage_size_mb: float
    oldest_memory: Optional[str] = None
    newest_memory: Optional[str] = None


# ===== エンドポイント =====

@router.post(
    "/search",
    response_model=MemorySearchResponse,
    summary="記憶検索",
    description="5階層記憶システムから関連する記憶を検索します。ベクトル類似検索を使用。",
    responses={
        200: {"description": "検索成功"},
        401: {"description": "未認証"},
        400: {"description": "検証エラー"}
    }
)
@limiter.limit("60/minute")
async def search_memory(
    request: Request,
    search_request: MemorySearchRequest,
    current_user: User = Depends(get_current_user)
) -> MemorySearchResponse:
    """記憶検索エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        search_request: 検索リクエスト
        current_user: 現在のユーザー
    
    Returns:
        MemorySearchResponse: 検索結果
    
    Raises:
        HTTPException: 検証エラー等
    """
    try:
        # Phase 1-3統合: MemoryService 検索呼び出し
        results = await memory_service.search(
            user_id=current_user.user_id,
            query=search_request.query,
            layers=search_request.memory_types,
            limit=search_request.limit
        )
        
        # レスポンス整形
        memory_items = [
            MemoryItem(
                memory_id=result.get('memory_id', 'unknown'),
                memory_type=result.get('layer', 'short_term'),
                content=result.get('content', ''),
                metadata=result.get('metadata', {}),
                relevance_score=result.get('relevance_score', 0.0),
                timestamp=result.get('timestamp', datetime.utcnow().isoformat())
            )
            for result in results
        ]
        
        search_response = MemorySearchResponse(
            query=search_request.query,
            results=memory_items,
            total_count=len(memory_items)
        )
        
        logger.info(
            f"Memory search: user={current_user.user_id}, "
            f"query={search_request.query}, count={len(memory_items)}"
        )
        
        return search_response
        
    except InvalidMemoryTypeError as e:
        logger.warning(f"Invalid memory type: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Memory search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory search failed"
        )


@router.post(
    "/",
    response_model=MemoryStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="記憶保存",
    description="新しい記憶を指定した記憶タイプに保存します。",
    responses={
        201: {"description": "保存成功"},
        401: {"description": "未認証"},
        400: {"description": "検証エラー"}
    }
)
@limiter.limit("30/minute")
async def store_memory(
    request: Request,
    store_request: MemoryStoreRequest,
    current_user: User = Depends(get_current_user)
) -> MemoryStoreResponse:
    """記憶保存エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        store_request: 保存リクエスト
        current_user: 現在のユーザー
    
    Returns:
        MemoryStoreResponse: 保存結果
    
    Raises:
        HTTPException: 保存エラー
    """
    try:
        # Phase 1-3統合: MemoryService 保存呼び出し
        result = await memory_service.store(
            user_id=current_user.user_id,
            session_id=store_request.session_id or f"session-{current_user.user_id}",
            content=store_request.content,
            layer=store_request.memory_type,
            metadata=store_request.metadata
        )
        
        logger.info(
            f"Memory stored: user={current_user.user_id}, "
            f"type={store_request.memory_type}, id={result.get('memory_id')}"
        )
        
        return MemoryStoreResponse(
            memory_id=result.get('memory_id', 'unknown'),
            memory_type=result.get('layer', store_request.memory_type)
        )
        
    except MemoryStorageError as e:
        logger.error(f"Memory storage error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Memory store error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory storage failed"
        )


@router.delete(
    "/{memory_id}",
    summary="記憶削除",
    description="指定したIDの記憶を削除します。",
    responses={
        200: {"description": "削除成功"},
        401: {"description": "未認証"},
        404: {"description": "記憶が存在しない"}
    }
)
async def delete_memory(
    request: Request,
    memory_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """記憶削除エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        memory_id: 記憶ID
        current_user: 現在のユーザー
    
    Returns:
        dict: 削除結果
    
    Raises:
        HTTPException: 記憶が存在しない
    """
    try:
        # Phase 1-3統合: MemoryService 削除呼び出し
        success = await memory_service.delete(
            user_id=current_user.user_id,
            memory_id=memory_id
        )
        
        if not success:
            raise MemoryNotFoundError(
                message=f"Memory {memory_id} not found",
                memory_id=memory_id
            )
        
        logger.info(
            f"Memory deleted: user={current_user.user_id}, memory_id={memory_id}"
        )
        
        return {
            "status": "success",
            "message": f"Memory {memory_id} deleted successfully"
        }
        
    except MemoryNotFoundError as e:
        logger.warning(f"Memory not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Memory deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory deletion failed"
        )


@router.get(
    "/stats",
    response_model=MemoryStats,
    summary="記憶統計取得",
    description="現在のユーザーの記憶統計情報を取得します。",
    responses={
        200: {"description": "統計取得成功"},
        401: {"description": "未認証"}
    }
)
async def get_memory_stats(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> MemoryStats:
    """記憶統計取得エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        current_user: 現在のユーザー
    
    Returns:
        MemoryStats: 統計情報
    """
    try:
        # Phase 1-3統合: MemoryService 統計取得呼び出し
        stats_result = await memory_service.get_stats(
            user_id=current_user.user_id
        )
        
        # レスポンス整形
        stats = MemoryStats(
            total_memories=stats_result.get('total_memories', 0),
            by_type=stats_result.get('by_layer', {}),
            by_session=stats_result.get('by_session', {}),
            storage_size_mb=stats_result.get('storage_size_mb', 0.0),
            oldest_memory=stats_result.get('oldest_memory'),
            newest_memory=stats_result.get('newest_memory')
        )
        
        logger.info(
            f"Memory stats retrieved: user={current_user.user_id}, "
            f"total={stats.total_memories}"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Memory stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory stats retrieval failed"
        )


@router.delete(
    "/sessions/{session_id}/all",
    summary="セッション記憶一括削除",
    description="指定セッションの全記憶を削除します。",
    responses={
        200: {"description": "削除成功"},
        401: {"description": "未認証"}
    }
)
async def delete_session_memories(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """セッション記憶一括削除エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        session_id: セッションID
        current_user: 現在のユーザー
    
    Returns:
        dict: 削除結果
    """
    try:
        # Phase 1-3統合: MemoryService セッション記憶取得→削除
        session_memories = await memory_service.get_session_memories(
            user_id=current_user.user_id,
            session_id=session_id,
            limit=1000  # 全記憶取得
        )
        
        deleted_count = 0
        for memory in session_memories.get('memories', []):
            memory_id = memory.get('memory_id')
            if memory_id:
                await memory_service.delete(
                    user_id=current_user.user_id,
                    memory_id=memory_id
                )
                deleted_count += 1
        
        logger.info(
            f"Session memories deleted: user={current_user.user_id}, "
            f"session={session_id}, count={deleted_count}"
        )
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} memories from session {session_id}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Session memories deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session memories deletion failed"
        )


@router.post(
    "/admin/flush",
    summary="記憶フラッシュ（管理者のみ）",
    description="短期記憶→中期記憶への手動フラッシュを実行します。管理者権限が必要です。",
    responses={
        200: {"description": "フラッシュ成功"},
        403: {"description": "権限不足"}
    }
)
async def flush_memory(
    request: Request,
    current_user: User = Depends(require_permission("manage_memory"))
) -> Dict[str, Any]:
    """記憶フラッシュエンドポイント（管理者専用）.
    
    Args:
        request: リクエストオブジェクト
        current_user: 現在のユーザー（管理者権限チェック済み）
    
    Returns:
        dict: フラッシュ結果
    """
    try:
        # Phase 1-3統合: MemoryService フラッシュ呼び出し
        flush_result = await memory_service.flush(
            user_id=current_user.user_id,
            confirm=True
        )
        
        logger.warning(
            f"Memory flush executed by admin: user={current_user.user_id}, "
            f"flushed={flush_result.get('flushed_memories', 0)}"
        )
        
        return {
            "status": "success",
            "message": "Memory flush completed",
            "flushed_memories": flush_result.get('flushed_memories', 0),
            "flushed_sessions": flush_result.get('flushed_sessions', 0)
        }
        
    except Exception as e:
        logger.error(f"Memory flush error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory flush failed"
        )