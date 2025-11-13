"""Security Models for LlmMultiChat3.

このモジュールはユーザー認証・認可に関するデータモデルを定義します。

Phase 3 Week 8-1:
- Userモデル: ユーザー基本情報
- UserRegistrationモデル: 新規登録リクエスト
- LoginCredentialsモデル: ログインリクエスト
- TokenResponseモデル: トークンレスポンス
- UserProfileモデル: ユーザープロファイル
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
import re


class User(BaseModel):
    """ユーザーモデル.
    
    Attributes:
        user_id: 一意のユーザー識別子（UUID）
        username: ユーザー名（3-30文字、英数字とアンダースコア）
        email: メールアドレス（EmailStr型で自動検証）
        password_hash: bcryptでハッシュ化されたパスワード
        roles: ロールリスト（デフォルト: ["user"]）
        created_at: アカウント作成日時
        last_login: 最終ログイン日時（Optional）
        is_active: アカウント有効フラグ
        is_verified: メール認証済みフラグ
        quota_limit: API呼び出し上限（回/日）
        quota_used: 本日のAPI呼び出し数
    """
    
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password_hash: str
    roles: List[str] = Field(default=["user"])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    is_verified: bool = False
    quota_limit: int = 1000  # 1日あたりのAPI呼び出し上限
    quota_used: int = 0
    
    @validator('username')
    def validate_username(cls, v):
        """ユーザー名検証: 英数字とアンダースコアのみ許可."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v
    
    @validator('roles')
    def validate_roles(cls, v):
        """ロール検証: 有効なロールのみ許可."""
        valid_roles = {'admin', 'user', 'guest', 'premium'}
        for role in v:
            if role not in valid_roles:
                raise ValueError(f'Invalid role: {role}. Valid roles: {valid_roles}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "lumina_user",
                "email": "lumina@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqTlCj3nPm",
                "roles": ["user"],
                "created_at": "2025-11-13T08:00:00Z",
                "last_login": "2025-11-13T09:30:00Z",
                "is_active": True,
                "is_verified": True,
                "quota_limit": 1000,
                "quota_used": 42
            }
        }


class UserRegistration(BaseModel):
    """新規ユーザー登録リクエスト.
    
    Attributes:
        username: ユーザー名（3-30文字）
        email: メールアドレス
        password: パスワード（8-64文字、大小英字・数字・記号含む）
        confirm_password: パスワード確認
    """
    
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        """ユーザー名検証."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """パスワード強度検証.
        
        要件:
        - 8文字以上
        - 大文字・小文字・数字・記号をそれぞれ1文字以上含む
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """パスワード一致確認."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "new_user",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            }
        }


class LoginCredentials(BaseModel):
    """ログインリクエスト.
    
    Attributes:
        email: メールアドレス
        password: パスワード（プレーンテキスト、検証後ハッシュ化）
    """
    
    email: EmailStr
    password: str = Field(..., min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class TokenResponse(BaseModel):
    """トークンレスポンス.
    
    Attributes:
        access_token: アクセストークン（有効期限: 1時間）
        refresh_token: リフレッシュトークン（有効期限: 30日）
        token_type: トークンタイプ（Bearer）
        expires_in: アクセストークン有効期限（秒）
    """
    
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1時間
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class RefreshTokenRequest(BaseModel):
    """リフレッシュトークンリクエスト.
    
    Attributes:
        refresh_token: リフレッシュトークン
    """
    
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class UserProfile(BaseModel):
    """ユーザープロファイル（パスワードハッシュを含まない）.
    
    Attributes:
        user_id: ユーザーID
        username: ユーザー名
        email: メールアドレス
        roles: ロールリスト
        created_at: アカウント作成日時
        last_login: 最終ログイン日時
        is_active: アカウント有効フラグ
        is_verified: メール認証済みフラグ
        quota_limit: API呼び出し上限
        quota_used: 本日のAPI呼び出し数
        quota_remaining: 残りAPI呼び出し数
    """
    
    user_id: str
    username: str
    email: EmailStr
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_verified: bool
    quota_limit: int
    quota_used: int
    
    @property
    def quota_remaining(self) -> int:
        """残りAPI呼び出し数を計算."""
        return max(0, self.quota_limit - self.quota_used)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "lumina_user",
                "email": "lumina@example.com",
                "roles": ["user", "premium"],
                "created_at": "2025-11-13T08:00:00Z",
                "last_login": "2025-11-13T09:30:00Z",
                "is_active": True,
                "is_verified": True,
                "quota_limit": 5000,
                "quota_used": 123
            }
        }


class PasswordResetRequest(BaseModel):
    """パスワードリセットリクエスト.
    
    Attributes:
        email: メールアドレス
    """
    
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordReset(BaseModel):
    """パスワードリセット実行.
    
    Attributes:
        reset_token: パスワードリセットトークン
        new_password: 新しいパスワード
        confirm_password: パスワード確認
    """
    
    reset_token: str
    new_password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        """パスワード強度検証（UserRegistrationと同じ）."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """パスワード一致確認."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!"
            }
        }
