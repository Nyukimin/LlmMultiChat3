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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # results = await memory_manager.search(
        #     query=search_request.query,
        #     memory_types=search_request.memory_types,
        #     user_id=current_user.user_id,
        #     session_id=search_request.session_id,
        #     limit=search_request.limit
        # )
        
        # モック検索結果（Phase 1統合後に削除）
        mock_results = MemorySearchResponse(
            query=search_request.query,
            results=[
                MemoryItem(
                    memory_id="mem-123",
                    memory_type="long_term",
                    content=f"モック記憶: {search_request.query}に関する情報",
                    metadata={
                        "session_id": search_request.session_id,
                        "user_id": current_user.user_id
                    },
                    relevance_score=0.95,
                    timestamp=datetime.utcnow().isoformat()
                )
            ],
            total_count=1
        )
        
        logger.info(
            f"Memory search: user={current_user.user_id}, "
            f"query={search_request.query}, count={len(mock_results.results)}"
        )
        
        return mock_results
        
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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # memory_id = await memory_manager.store(
        #     memory_type=store_request.memory_type,
        #     content=store_request.content,
        #     user_id=current_user.user_id,
        #     session_id=store_request.session_id,
        #     metadata=store_request.metadata
        # )
        
        # モック保存（Phase 1統合後に削除）
        mock_memory_id = f"mem-{datetime.utcnow().timestamp()}"
        
        logger.info(
            f"Memory stored: user={current_user.user_id}, "
            f"type={store_request.memory_type}, id={mock_memory_id}"
        )
        
        return MemoryStoreResponse(
            memory_id=mock_memory_id,
            memory_type=store_request.memory_type
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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # await memory_manager.delete(
        #     memory_id=memory_id,
        #     user_id=current_user.user_id
        # )
        
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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # stats = await memory_manager.get_stats(
        #     user_id=current_user.user_id
        # )
        
        # モック統計（Phase 1統合後に削除）
        mock_stats = MemoryStats(
            total_memories=150,
            by_type={
                "short_term": 20,
                "mid_term": 30,
                "long_term": 80,
                "associative": 10,
                "knowledge": 10
            },
            by_session={
                "session-123": 50,
                "session-456": 100
            },
            storage_size_mb=2.5,
            oldest_memory=datetime.utcnow().isoformat(),
            newest_memory=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Memory stats retrieved: user={current_user.user_id}, "
            f"total={mock_stats.total_memories}"
        )
        
        return mock_stats
        
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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # deleted_count = await memory_manager.delete_session_memories(
        #     session_id=session_id,
        #     user_id=current_user.user_id
        # )
        
        # モック削除（Phase 1統合後に削除）
        mock_deleted_count = 25
        
        logger.info(
            f"Session memories deleted: user={current_user.user_id}, "
            f"session={session_id}, count={mock_deleted_count}"
        )
        
        return {
            "status": "success",
            "message": f"Deleted {mock_deleted_count} memories from session {session_id}",
            "deleted_count": mock_deleted_count
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
        # TODO: Phase 1の記憶システムを使用
        # memory_manager = request.app.state.memory_manager
        # flush_result = await memory_manager.flush_short_to_mid()
        
        # モックフラッシュ（Phase 1統合後に削除）
        mock_result = {
            "status": "success",
            "message": "Memory flush completed",
            "flushed_memories": 50,
            "duration_ms": 1234
        }
        
        logger.info(
            f"Memory flush executed by admin: {current_user.user_id}"
        )
        
        return mock_result
        
    except Exception as e:
        logger.error(f"Memory flush error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory flush failed"
        )