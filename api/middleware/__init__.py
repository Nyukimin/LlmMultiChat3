"""API Middleware Module for LlmMultiChat3.

このモジュールはFastAPI用のミドルウェアを提供します。

Phase 3 Week 8-3:
- 認証ミドルウェア（JWT検証）
- レート制限ミドルウェア
- クォータ管理

Exported Functions:
- init_auth_middleware: 認証ミドルウェア初期化
- get_current_user: 現在のユーザー取得
- require_permission: 権限チェック
- init_rate_limiter: レート制限初期化
- init_quota_manager: クォータマネージャー初期化

使用例:
    >>> from api.middleware import (
    ...     init_auth_middleware,
    ...     get_current_user,
    ...     require_permission
    ... )
    >>> 
    >>> # 初期化
    >>> init_auth_middleware(jwt_manager, user_manager)
    >>> 
    >>> # エンドポイント
    >>> @router.get("/me")
    >>> async def get_me(
    ...     current_user: User = Depends(get_current_user)
    ... ):
    ...     return {"username": current_user.username}
"""

from api.middleware.auth_middleware import (
    AuthMiddleware,
    init_auth_middleware,
    get_auth_middleware,
    get_current_user,
    get_current_user_profile,
    require_permission,
    require_role
)

from api.middleware.rate_limiter import (
    RateLimitConfig,
    QuotaManager,
    init_rate_limiter,
    get_rate_limiter,
    init_quota_manager,
    get_quota_manager,
    check_user_quota,
    custom_rate_limit_handler
)

__all__ = [
    # 認証ミドルウェア
    "AuthMiddleware",
    "init_auth_middleware",
    "get_auth_middleware",
    "get_current_user",
    "get_current_user_profile",
    "require_permission",
    "require_role",
    
    # レート制限
    "RateLimitConfig",
    "QuotaManager",
    "init_rate_limiter",
    "get_rate_limiter",
    "init_quota_manager",
    "get_quota_manager",
    "check_user_quota",
    "custom_rate_limit_handler"
]

__version__ = "3.0.0"
