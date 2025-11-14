"""Authentication Routes.

ユーザー認証・認可エンドポイント。

Phase 3 Week 9-1:
- ユーザー登録
- ログイン
- トークン更新
- パスワード変更
- ユーザープロファイル取得

使用例:
    >>> # ユーザー登録
    >>> POST /api/v1/auth/register
    >>> {
    ...     "username": "test_user",
    ...     "email": "test@example.com",
    ...     "password": "SecurePass123!"
    ... }
    >>> 
    >>> # ログイン
    >>> POST /api/v1/auth/login
    >>> {
    ...     "email": "test@example.com",
    ...     "password": "SecurePass123!"
    ... }
"""

from typing import Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.middleware.auth_middleware import (
    get_current_user,
    get_current_user_profile,
    require_permission
)
from security.models import User, UserProfile
from security.user_manager import UserManager
from exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError,
    WeakPasswordError
)


logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ===== リクエスト/レスポンスモデル =====

class UserRegistration(BaseModel):
    """ユーザー登録リクエスト."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="ユーザー名（3-50文字）"
    )
    email: EmailStr = Field(
        ...,
        description="メールアドレス"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="パスワード（8-100文字、英数字記号含む）"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        """パスワード強度検証."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "test_user",
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        }


class UserRegistrationResponse(BaseModel):
    """ユーザー登録レスポンス."""
    
    status: str = "success"
    message: str = "User registered successfully"
    user_id: str
    username: str
    email: str


class LoginCredentials(BaseModel):
    """ログインリクエスト."""
    
    email: EmailStr = Field(
        ...,
        description="メールアドレス"
    )
    password: str = Field(
        ...,
        description="パスワード"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        }


class LoginResponse(BaseModel):
    """ログインレスポンス."""
    
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserProfile


class RefreshTokenRequest(BaseModel):
    """トークン更新リクエスト."""
    
    refresh_token: str = Field(
        ...,
        description="リフレッシュトークン"
    )


class RefreshTokenResponse(BaseModel):
    """トークン更新レスポンス."""
    
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト."""
    
    current_password: str = Field(
        ...,
        description="現在のパスワード"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="新しいパスワード（8-100文字）"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """パスワード強度検証."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordChangeResponse(BaseModel):
    """パスワード変更レスポンス."""
    
    status: str = "success"
    message: str = "Password changed successfully"


# ===== エンドポイント =====

@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
    description="新しいユーザーアカウントを作成します。",
    responses={
        201: {"description": "ユーザー登録成功"},
        400: {"description": "バリデーションエラー（ユーザー既存等）"},
        429: {"description": "レート制限超過"}
    }
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegistration,
    user_manager: UserManager = Depends(lambda: request.app.state.user_manager)
) -> UserRegistrationResponse:
    """ユーザー登録エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        user_data: ユーザー登録データ
        user_manager: ユーザーマネージャー（依存性注入）
    
    Returns:
        UserRegistrationResponse: 登録結果
    
    Raises:
        HTTPException: ユーザー既存、バリデーションエラー等
    """
    try:
        user = user_manager.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info(f"User registered: {user.user_id} ({user.email})")
        
        return UserRegistrationResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email
        )
        
    except UserAlreadyExistsError as e:
        logger.warning(f"Registration failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except WeakPasswordError as e:
        logger.warning(f"Weak password: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="ログイン",
    description="メールアドレスとパスワードでログインし、アクセストークンとリフレッシュトークンを取得します。",
    responses={
        200: {"description": "ログイン成功"},
        401: {"description": "認証失敗"},
        429: {"description": "レート制限超過"}
    }
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: LoginCredentials,
    user_manager: UserManager = Depends(lambda: request.app.state.user_manager)
) -> LoginResponse:
    """ログインエンドポイント.
    
    Args:
        request: リクエストオブジェクト
        credentials: ログイン認証情報
        user_manager: ユーザーマネージャー
    
    Returns:
        LoginResponse: トークン情報
    
    Raises:
        HTTPException: 認証失敗
    """
    try:
        result = user_manager.login(
            email=credentials.email,
            password=credentials.password
        )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=result["user"]
        )
        
    except InvalidCredentialsError as e:
        logger.warning(f"Login failed: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="トークン更新",
    description="リフレッシュトークンを使用して新しいアクセストークンを取得します。",
    responses={
        200: {"description": "トークン更新成功"},
        401: {"description": "トークン無効"},
        429: {"description": "レート制限超過"}
    }
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    user_manager: UserManager = Depends(lambda: request.app.state.user_manager)
) -> RefreshTokenResponse:
    """トークン更新エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        token_request: リフレッシュトークンリクエスト
        user_manager: ユーザーマネージャー
    
    Returns:
        RefreshTokenResponse: 新しいアクセストークン
    
    Raises:
        HTTPException: トークン無効・期限切れ
    """
    try:
        new_access_token = user_manager.refresh_access_token(
            refresh_token=token_request.refresh_token
        )
        
        logger.debug("Access token refreshed")
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=request.app.state.config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except (TokenExpiredError, InvalidTokenError) as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="プロファイル取得",
    description="現在ログイン中のユーザープロファイルを取得します。",
    responses={
        200: {"description": "プロファイル取得成功"},
        401: {"description": "未認証"}
    }
)
async def get_profile(
    current_user_profile: UserProfile = Depends(get_current_user_profile)
) -> UserProfile:
    """ユーザープロファイル取得エンドポイント.
    
    Args:
        current_user_profile: 現在のユーザープロファイル（依存性注入）
    
    Returns:
        UserProfile: ユーザープロファイル
    """
    return current_user_profile


@router.post(
    "/change-password",
    response_model=PasswordChangeResponse,
    summary="パスワード変更",
    description="現在のパスワードを検証し、新しいパスワードに変更します。",
    responses={
        200: {"description": "パスワード変更成功"},
        401: {"description": "認証失敗"},
        400: {"description": "バリデーションエラー"}
    }
)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(lambda: request.app.state.user_manager)
) -> PasswordChangeResponse:
    """パスワード変更エンドポイント.
    
    Args:
        request: リクエストオブジェクト
        password_data: パスワード変更データ
        current_user: 現在のユーザー
        user_manager: ユーザーマネージャー
    
    Returns:
        PasswordChangeResponse: 変更結果
    
    Raises:
        HTTPException: 認証失敗、バリデーションエラー
    """
    try:
        user_manager.change_password(
            user_id=current_user.user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        logger.info(f"Password changed for user: {current_user.user_id}")
        
        return PasswordChangeResponse()
        
    except InvalidCredentialsError as e:
        logger.warning(f"Password change failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    except WeakPasswordError as e:
        logger.warning(f"Weak password: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.delete(
    "/users/{user_id}",
    summary="ユーザー削除（管理者のみ）",
    description="指定したユーザーアカウントを削除します。管理者権限が必要です。",
    responses={
        200: {"description": "削除成功"},
        403: {"description": "権限不足"},
        404: {"description": "ユーザーが存在しない"}
    }
)
async def delete_user(
    request: Request,
    user_id: str,
    current_user: User = Depends(require_permission("manage_users")),
    user_manager: UserManager = Depends(lambda: request.app.state.user_manager)
) -> Dict[str, str]:
    """ユーザー削除エンドポイント（管理者専用）.
    
    Args:
        request: リクエストオブジェクト
        user_id: 削除対象ユーザーID
        current_user: 現在のユーザー（管理者権限チェック済み）
        user_manager: ユーザーマネージャー
    
    Returns:
        dict: 削除結果
    
    Raises:
        HTTPException: ユーザーが存在しない
    """
    try:
        user_manager.delete_user(user_id)
        
        logger.info(f"User deleted: {user_id} (by {current_user.user_id})")
        
        return {
            "status": "success",
            "message": f"User {user_id} deleted successfully"
        }
        
    except UserNotFoundError as e:
        logger.warning(f"User deletion failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"User deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )