"""Authentication Middleware for FastAPI.

このモジュールはFastAPI用の認証ミドルウェアを提供します。

Phase 3 Week 8-3:
- JWT認証ミドルウェア
- 依存性注入（Depends）
- ユーザー情報取得
- 権限チェック

使用例:
    >>> from api.middleware.auth_middleware import get_current_user, require_permission
    >>> 
    >>> @router.get("/protected")
    >>> async def protected_route(
    ...     current_user: User = Depends(get_current_user)
    ... ):
    ...     return {"user_id": current_user.user_id}
    >>> 
    >>> @router.delete("/admin/users/{user_id}")
    >>> async def delete_user(
    ...     user_id: str,
    ...     current_user: User = Depends(require_permission("manage_users"))
    ... ):
    ...     # 管理者のみアクセス可能
    ...     pass
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from security.jwt_manager import JWTManager
from security.user_manager import UserManager
from security.role_manager import RoleManager
from security.models import User, UserProfile
from exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError,
    InsufficientPermissionsError
)


logger = logging.getLogger(__name__)


# HTTPBearer認証スキーム
security = HTTPBearer()


class AuthMiddleware:
    """認証ミドルウェアクラス.
    
    FastAPIの依存性注入を使用してJWT認証を実装します。
    
    Attributes:
        jwt_manager: JWT管理インスタンス
        user_manager: ユーザー管理インスタンス
        role_manager: ロール管理インスタンス
    """
    
    def __init__(
        self,
        jwt_manager: JWTManager,
        user_manager: UserManager,
        role_manager: Optional[RoleManager] = None
    ):
        """AuthMiddlewareを初期化.
        
        Args:
            jwt_manager: JWT管理インスタンス
            user_manager: ユーザー管理インスタンス
            role_manager: ロール管理インスタンス（Noneの場合は新規作成）
        """
        self.jwt_manager = jwt_manager
        self.user_manager = user_manager
        self.role_manager = role_manager or RoleManager()
        
        logger.info("AuthMiddleware initialized")
    
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """トークンを検証してペイロードを返す.
        
        Args:
            credentials: HTTP Bearer認証クレデンシャル
        
        Returns:
            dict: デコードされたペイロード（user_id, roles等）
        
        Raises:
            HTTPException: トークン検証失敗
        
        Example:
            >>> @router.get("/protected")
            >>> async def protected(
            ...     payload: dict = Depends(auth_middleware.verify_token)
            ... ):
            ...     return {"user_id": payload["sub"]}
        """
        token = credentials.credentials
        
        try:
            payload = self.jwt_manager.verify_token(
                token,
                expected_type="access"
            )
            
            logger.debug(f"Token verified for user {payload.get('sub')}")
            return payload
            
        except TokenExpiredError as e:
            logger.warning(f"Token expired: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def get_current_user(
        self,
        payload: dict = Depends(verify_token)
    ) -> User:
        """現在のユーザーを取得.
        
        Args:
            payload: 検証済みのJWTペイロード
        
        Returns:
            User: ユーザーオブジェクト
        
        Raises:
            HTTPException: ユーザーが存在しない場合
        
        Example:
            >>> @router.get("/me")
            >>> async def get_me(
            ...     current_user: User = Depends(auth_middleware.get_current_user)
            ... ):
            ...     return {"username": current_user.username}
        """
        user_id = payload.get("sub")
        
        try:
            user = self.user_manager.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            logger.debug(f"Retrieved user: {user.user_id}")
            return user
            
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user information"
            )
    
    async def get_current_user_profile(
        self,
        current_user: User = Depends(get_current_user)
    ) -> UserProfile:
        """現在のユーザープロファイルを取得（パスワードハッシュ除外）.
        
        Args:
            current_user: 現在のユーザー
        
        Returns:
            UserProfile: ユーザープロファイル
        
        Example:
            >>> @router.get("/profile")
            >>> async def get_profile(
            ...     profile: UserProfile = Depends(auth_middleware.get_current_user_profile)
            ... ):
            ...     return profile
        """
        return UserProfile(
            user_id=current_user.user_id,
            username=current_user.username,
            email=current_user.email,
            roles=current_user.roles,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            quota_limit=current_user.quota_limit,
            quota_used=current_user.quota_used
        )
    
    def require_permission(self, permission: str) -> Callable:
        """特定の権限を要求する依存性を作成.
        
        Args:
            permission: 必要な権限名
        
        Returns:
            Callable: FastAPI依存性関数
        
        Raises:
            HTTPException: 権限不足
        
        Example:
            >>> @router.delete("/admin/users/{user_id}")
            >>> async def delete_user(
            ...     user_id: str,
            ...     current_user: User = Depends(
            ...         auth_middleware.require_permission("manage_users")
            ...     )
            ... ):
            ...     # 管理者のみアクセス可能
            ...     pass
        """
        async def permission_checker(
            current_user: User = Depends(self.get_current_user)
        ) -> User:
            try:
                self.role_manager.require_permission(
                    current_user,
                    permission,
                    raise_error=True
                )
                return current_user
                
            except InsufficientPermissionsError as e:
                logger.warning(
                    f"User {current_user.user_id} lacks permission: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission} required"
                )
        
        return permission_checker
    
    def require_any_permission(self, permissions: list) -> Callable:
        """いずれかの権限を要求する依存性を作成.
        
        Args:
            permissions: 必要な権限名のリスト
        
        Returns:
            Callable: FastAPI依存性関数
        
        Example:
            >>> @router.get("/data")
            >>> async def get_data(
            ...     current_user: User = Depends(
            ...         auth_middleware.require_any_permission(["read", "write"])
            ...     )
            ... ):
            ...     pass
        """
        async def permission_checker(
            current_user: User = Depends(self.get_current_user)
        ) -> User:
            if not self.role_manager.has_any_permission(current_user, permissions):
                logger.warning(
                    f"User {current_user.user_id} lacks any of permissions: {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: one of {permissions} required"
                )
            
            return current_user
        
        return permission_checker
    
    def require_role(self, role: str) -> Callable:
        """特定のロールを要求する依存性を作成.
        
        Args:
            role: 必要なロール名
        
        Returns:
            Callable: FastAPI依存性関数
        
        Example:
            >>> @router.get("/admin/dashboard")
            >>> async def admin_dashboard(
            ...     current_user: User = Depends(
            ...         auth_middleware.require_role("admin")
            ...     )
            ... ):
            ...     pass
        """
        async def role_checker(
            current_user: User = Depends(self.get_current_user)
        ) -> User:
            if role not in current_user.roles:
                logger.warning(
                    f"User {current_user.user_id} lacks role: {role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )
            
            return current_user
        
        return role_checker


# グローバルインスタンス（FastAPIアプリケーションで初期化）
_auth_middleware: Optional[AuthMiddleware] = None


def init_auth_middleware(
    jwt_manager: JWTManager,
    user_manager: UserManager,
    role_manager: Optional[RoleManager] = None
):
    """認証ミドルウェアを初期化.
    
    Args:
        jwt_manager: JWT管理インスタンス
        user_manager: ユーザー管理インスタンス
        role_manager: ロール管理インスタンス（オプション）
    
    Example:
        >>> # api/main.py
        >>> from api.middleware.auth_middleware import init_auth_middleware
        >>> 
        >>> init_auth_middleware(
        ...     jwt_manager=jwt_manager,
        ...     user_manager=user_manager
        ... )
    """
    global _auth_middleware
    _auth_middleware = AuthMiddleware(
        jwt_manager=jwt_manager,
        user_manager=user_manager,
        role_manager=role_manager
    )
    logger.info("Global AuthMiddleware initialized")


def get_auth_middleware() -> AuthMiddleware:
    """グローバル認証ミドルウェアインスタンスを取得.
    
    Returns:
        AuthMiddleware: 認証ミドルウェアインスタンス
    
    Raises:
        RuntimeError: 初期化されていない場合
    """
    if _auth_middleware is None:
        raise RuntimeError(
            "AuthMiddleware not initialized. "
            "Call init_auth_middleware() first."
        )
    return _auth_middleware


# 便利な依存性関数（グローバルインスタンス使用）

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """現在のユーザーを取得（グローバルインスタンス使用）.
    
    Example:
        >>> @router.get("/me")
        >>> async def get_me(
        ...     current_user: User = Depends(get_current_user)
        ... ):
        ...     return {"username": current_user.username}
    """
    auth_middleware = get_auth_middleware()
    payload = await auth_middleware.verify_token(credentials)
    return await auth_middleware.get_current_user(payload)


async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """現在のユーザープロファイルを取得.
    
    Example:
        >>> @router.get("/profile")
        >>> async def get_profile(
        ...     profile: UserProfile = Depends(get_current_user_profile)
        ... ):
        ...     return profile
    """
    auth_middleware = get_auth_middleware()
    return await auth_middleware.get_current_user_profile(current_user)


def require_permission(permission: str) -> Callable:
    """特定の権限を要求.
    
    Example:
        >>> @router.delete("/admin/users/{user_id}")
        >>> async def delete_user(
        ...     user_id: str,
        ...     current_user: User = Depends(require_permission("manage_users"))
        ... ):
        ...     pass
    """
    auth_middleware = get_auth_middleware()
    return auth_middleware.require_permission(permission)


def require_role(role: str) -> Callable:
    """特定のロールを要求.
    
    Example:
        >>> @router.get("/admin/dashboard")
        >>> async def admin_dashboard(
        ...     current_user: User = Depends(require_role("admin"))
        ... ):
        ...     pass
    """
    auth_middleware = get_auth_middleware()
    return auth_middleware.require_role(role)
