"""Rate Limiting Middleware for FastAPI.

このモジュールはAPI呼び出しのレート制限を提供します。

Phase 3 Week 8-3:
- レート制限（回数/期間）
- IPアドレスベース制限
- ユーザーベース制限
- Redisバックエンド（オプション）

使用例:
    >>> from api.middleware.rate_limiter import limiter, rate_limit
    >>> 
    >>> @router.get("/api")
    >>> @limiter.limit("10/minute")
    >>> async def api_endpoint(request: Request):
    ...     return {"message": "success"}
    >>> 
    >>> @router.post("/expensive")
    >>> @limiter.limit("5/hour")
    >>> async def expensive_operation(request: Request):
    ...     return {"status": "processing"}
"""

from typing import Optional, Callable
from fastapi import Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


def get_user_identifier(request: Request) -> str:
    """リクエストからユーザー識別子を取得.
    
    優先順位:
    1. 認証済みユーザーID（JWTトークンから）
    2. IPアドレス
    
    Args:
        request: FastAPI Requestオブジェクト
    
    Returns:
        str: ユーザー識別子
    """
    # JWTトークンからユーザーIDを取得（認証済みの場合）
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # IPアドレスを使用
    return f"ip:{get_remote_address(request)}"


class RateLimitConfig:
    """レート制限設定.
    
    Attributes:
        default_limits: デフォルトのレート制限（例: ["100/hour", "10/minute"]）
        enabled: レート制限の有効/無効
        storage_uri: Redisストレージ URI（オプション）
    """
    
    def __init__(
        self,
        default_limits: Optional[list] = None,
        enabled: bool = True,
        storage_uri: Optional[str] = None
    ):
        """RateLimitConfigを初期化.
        
        Args:
            default_limits: デフォルトのレート制限リスト
            enabled: レート制限の有効/無効
            storage_uri: Redisストレージ URI（例: "redis://localhost:6379"）
        """
        self.default_limits = default_limits or ["100/hour", "10/minute"]
        self.enabled = enabled
        self.storage_uri = storage_uri
        
        logger.info(
            f"RateLimitConfig initialized: enabled={enabled}, "
            f"limits={self.default_limits}"
        )


# グローバルレート制限インスタンス
_limiter: Optional[Limiter] = None
_rate_limit_config: Optional[RateLimitConfig] = None


def init_rate_limiter(
    config: Optional[RateLimitConfig] = None,
    key_func: Optional[Callable] = None
) -> Limiter:
    """レート制限を初期化.
    
    Args:
        config: レート制限設定（Noneの場合はデフォルト設定）
        key_func: キー生成関数（Noneの場合はget_user_identifier）
    
    Returns:
        Limiter: Slowapi Limiterインスタンス
    
    Example:
        >>> # api/main.py
        >>> from api.middleware.rate_limiter import init_rate_limiter, RateLimitConfig
        >>> 
        >>> config = RateLimitConfig(
        ...     default_limits=["100/hour", "10/minute"],
        ...     storage_uri="redis://localhost:6379"
        ... )
        >>> limiter = init_rate_limiter(config)
    """
    global _limiter, _rate_limit_config
    
    _rate_limit_config = config or RateLimitConfig()
    
    # キー生成関数（デフォルト: ユーザー識別子）
    key_function = key_func or get_user_identifier
    
    # Limiterインスタンス作成
    _limiter = Limiter(
        key_func=key_function,
        default_limits=_rate_limit_config.default_limits if _rate_limit_config.enabled else [],
        storage_uri=_rate_limit_config.storage_uri,
        enabled=_rate_limit_config.enabled
    )
    
    logger.info("Rate limiter initialized")
    return _limiter


def get_rate_limiter() -> Limiter:
    """グローバルレート制限インスタンスを取得.
    
    Returns:
        Limiter: Limiterインスタンス
    
    Raises:
        RuntimeError: 初期化されていない場合
    """
    if _limiter is None:
        raise RuntimeError(
            "Rate limiter not initialized. "
            "Call init_rate_limiter() first."
        )
    return _limiter


class QuotaManager:
    """ユーザーAPIクォータ管理.
    
    ユーザーごとの日次API呼び出し上限を管理します。
    
    Attributes:
        redis_client: Redisクライアント（オプション）
        in_memory_quotas: インメモリクォータストレージ（Redis未使用時）
    """
    
    def __init__(self, redis_client=None):
        """QuotaManagerを初期化.
        
        Args:
            redis_client: Redisクライアント（オプション）
        """
        self.redis_client = redis_client
        self.in_memory_quotas = defaultdict(lambda: {"used": 0, "reset_at": None})
        
        logger.info(f"QuotaManager initialized (Redis: {redis_client is not None})")
    
    def check_quota(self, user_id: str, quota_limit: int) -> bool:
        """ユーザーのクォータをチェック.
        
        Args:
            user_id: ユーザーID
            quota_limit: 日次上限
        
        Returns:
            bool: クォータ内の場合True
        
        Example:
            >>> quota_manager = QuotaManager()
            >>> if quota_manager.check_quota("user123", 1000):
            ...     # API処理
            ...     quota_manager.increment_quota("user123")
        """
        if self.redis_client:
            return self._check_quota_redis(user_id, quota_limit)
        else:
            return self._check_quota_memory(user_id, quota_limit)
    
    def increment_quota(self, user_id: str) -> int:
        """ユーザーのクォータをインクリメント.
        
        Args:
            user_id: ユーザーID
        
        Returns:
            int: 現在の使用量
        """
        if self.redis_client:
            return self._increment_quota_redis(user_id)
        else:
            return self._increment_quota_memory(user_id)
    
    def get_quota_info(self, user_id: str, quota_limit: int) -> dict:
        """ユーザーのクォータ情報を取得.
        
        Args:
            user_id: ユーザーID
            quota_limit: 日次上限
        
        Returns:
            dict: クォータ情報（used, limit, remaining, reset_at）
        """
        if self.redis_client:
            used = self._get_quota_redis(user_id)
        else:
            used = self.in_memory_quotas[user_id]["used"]
        
        remaining = max(0, quota_limit - used)
        reset_at = self._get_reset_time()
        
        return {
            "used": used,
            "limit": quota_limit,
            "remaining": remaining,
            "reset_at": reset_at.isoformat()
        }
    
    def _check_quota_redis(self, user_id: str, quota_limit: int) -> bool:
        """Redis使用時のクォータチェック."""
        try:
            key = f"quota:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            used = int(self.redis_client.get(key) or 0)
            return used < quota_limit
        except Exception as e:
            logger.error(f"Redis quota check failed: {e}")
            return True  # Redis障害時は許可
    
    def _check_quota_memory(self, user_id: str, quota_limit: int) -> bool:
        """インメモリ使用時のクォータチェック."""
        quota_data = self.in_memory_quotas[user_id]
        
        # リセット時刻を過ぎている場合はリセット
        now = datetime.utcnow()
        if quota_data["reset_at"] is None or now >= quota_data["reset_at"]:
            quota_data["used"] = 0
            quota_data["reset_at"] = self._get_reset_time()
        
        return quota_data["used"] < quota_limit
    
    def _increment_quota_redis(self, user_id: str) -> int:
        """Redis使用時のクォータインクリメント."""
        try:
            key = f"quota:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            used = self.redis_client.incr(key)
            
            # 有効期限を設定（翌日0時UTC）
            if used == 1:
                reset_time = self._get_reset_time()
                ttl = int((reset_time - datetime.utcnow()).total_seconds())
                self.redis_client.expire(key, ttl)
            
            return used
        except Exception as e:
            logger.error(f"Redis quota increment failed: {e}")
            return 0
    
    def _increment_quota_memory(self, user_id: str) -> int:
        """インメモリ使用時のクォータインクリメント."""
        quota_data = self.in_memory_quotas[user_id]
        quota_data["used"] += 1
        return quota_data["used"]
    
    def _get_quota_redis(self, user_id: str) -> int:
        """Redis使用時のクォータ取得."""
        try:
            key = f"quota:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            return int(self.redis_client.get(key) or 0)
        except Exception as e:
            logger.error(f"Redis quota get failed: {e}")
            return 0
    
    def _get_reset_time(self) -> datetime:
        """クォータリセット時刻を取得（翌日0時UTC）."""
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)


# グローバルクォータマネージャー
_quota_manager: Optional[QuotaManager] = None


def init_quota_manager(redis_client=None) -> QuotaManager:
    """クォータマネージャーを初期化.
    
    Args:
        redis_client: Redisクライアント（オプション）
    
    Returns:
        QuotaManager: クォータマネージャーインスタンス
    """
    global _quota_manager
    _quota_manager = QuotaManager(redis_client)
    logger.info("Global QuotaManager initialized")
    return _quota_manager


def get_quota_manager() -> QuotaManager:
    """グローバルクォータマネージャーを取得.
    
    Returns:
        QuotaManager: クォータマネージャーインスタンス
    
    Raises:
        RuntimeError: 初期化されていない場合
    """
    if _quota_manager is None:
        raise RuntimeError(
            "QuotaManager not initialized. "
            "Call init_quota_manager() first."
        )
    return _quota_manager


async def check_user_quota(request: Request):
    """ユーザークォータをチェックする依存性.
    
    Raises:
        HTTPException: クォータ超過
    
    Example:
        >>> @router.post("/api/chat")
        >>> async def chat(
        ...     request: Request,
        ...     _: None = Depends(check_user_quota)
        ... ):
        ...     # クォータ内の場合のみ実行
        ...     pass
    """
    # ユーザー情報を取得（認証済みの場合）
    if not hasattr(request.state, "user"):
        # 未認証ユーザーはスキップ
        return
    
    user = request.state.user
    quota_manager = get_quota_manager()
    
    # クォータチェック
    if not quota_manager.check_quota(user.user_id, user.quota_limit):
        quota_info = quota_manager.get_quota_info(user.user_id, user.quota_limit)
        
        logger.warning(
            f"User {user.user_id} exceeded quota: "
            f"{quota_info['used']}/{quota_info['limit']}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Quota exceeded",
                "quota_info": quota_info
            },
            headers={
                "X-RateLimit-Limit": str(quota_info["limit"]),
                "X-RateLimit-Remaining": str(quota_info["remaining"]),
                "X-RateLimit-Reset": quota_info["reset_at"]
            }
        )
    
    # クォータをインクリメント
    quota_manager.increment_quota(user.user_id)


# レート制限エラーハンドラー
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """カスタムレート制限エラーハンドラー.
    
    Args:
        request: FastAPI Request
        exc: RateLimitExceeded例外
    
    Returns:
        Response: JSONエラーレスポンス
    """
    logger.warning(
        f"Rate limit exceeded for {get_user_identifier(request)}: {exc.detail}"
    )
    
    return Response(
        content=f'{{"error": "Rate limit exceeded", "detail": "{exc.detail}"}}',
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={
            "Content-Type": "application/json",
            "Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"
        }
    )
