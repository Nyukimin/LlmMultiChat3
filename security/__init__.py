"""Security Module for LlmMultiChat3.

このモジュールはPhase 3のセキュリティ機能を提供します。

Phase 3 Week 8-1:
- JWT認証・認可
- パスワードハッシュ化
- ユーザーモデル

Exported Classes:
- JWTManager: JWT生成・検証
- PasswordHasher: パスワードハッシュ化
- User: ユーザーモデル
- UserRegistration: 新規登録リクエスト
- LoginCredentials: ログインリクエスト
- TokenResponse: トークンレスポンス
- UserProfile: ユーザープロファイル

使用例:
    >>> from security import JWTManager, PasswordHasher, User
    >>> 
    >>> # JWT管理
    >>> jwt_manager = JWTManager(secret_key="your-secret-key")
    >>> token = jwt_manager.create_access_token("user123")
    >>> 
    >>> # パスワードハッシュ
    >>> hasher = PasswordHasher()
    >>> hash_value = hasher.hash_password("SecurePass123!")
    >>> is_valid = hasher.verify_password("SecurePass123!", hash_value)
"""

from security.jwt_manager import JWTManager
from security.password_hasher import PasswordHasher
from security.models import (
    User,
    UserRegistration,
    LoginCredentials,
    TokenResponse,
    RefreshTokenRequest,
    UserProfile,
    PasswordResetRequest,
    PasswordReset
)
from security.user_manager import UserManager
from security.role_manager import RoleManager

__all__ = [
    "JWTManager",
    "PasswordHasher",
    "User",
    "UserRegistration",
    "LoginCredentials",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserProfile",
    "PasswordResetRequest",
    "PasswordReset",
    "UserManager",
    "RoleManager"
]

__version__ = "3.0.0"
