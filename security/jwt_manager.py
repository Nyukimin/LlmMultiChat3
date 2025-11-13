"""JWT Token Manager for LlmMultiChat3.

このモジュールはJWT（JSON Web Token）の生成・検証を提供します。

Phase 3 Week 8-1:
- アクセストークン生成（有効期限: 1時間）
- リフレッシュトークン生成（有効期限: 30日）
- トークン検証・デコード
- トークン更新

使用例:
    >>> jwt_manager = JWTManager(secret_key="your-secret-key")
    >>> access_token = jwt_manager.create_access_token(user_id="user123")
    >>> payload = jwt_manager.verify_token(access_token)
    >>> print(payload["sub"])  # "user123"
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    TokenGenerationError
)


logger = logging.getLogger(__name__)


class JWTManager:
    """JWT トークン管理クラス.
    
    JWT（JSON Web Token）を使用した認証・認可システムの実装。
    
    トークンの種類:
    - Access Token: 短期間有効（1時間）、API呼び出しに使用
    - Refresh Token: 長期間有効（30日）、アクセストークン更新に使用
    
    Attributes:
        secret_key: JWT署名用の秘密鍵
        algorithm: 署名アルゴリズム（デフォルト: HS256）
        access_token_expires: アクセストークン有効期限（秒）
        refresh_token_expires: リフレッシュトークン有効期限（秒）
    """
    
    DEFAULT_ALGORITHM = "HS256"
    DEFAULT_ACCESS_TOKEN_EXPIRES = 3600  # 1時間
    DEFAULT_REFRESH_TOKEN_EXPIRES = 2592000  # 30日
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = DEFAULT_ALGORITHM,
        access_token_expires: Optional[int] = None,
        refresh_token_expires: Optional[int] = None
    ):
        """JWTManagerを初期化.
        
        Args:
            secret_key: JWT署名用の秘密鍵（最低32文字推奨）
            algorithm: 署名アルゴリズム（HS256, HS384, HS512など）
            access_token_expires: アクセストークン有効期限（秒）
            refresh_token_expires: リフレッシュトークン有効期限（秒）
        
        Raises:
            ValueError: secret_keyが短すぎる場合
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError(
                "Secret key must be at least 32 characters long for security"
            )
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires = (
            access_token_expires or self.DEFAULT_ACCESS_TOKEN_EXPIRES
        )
        self.refresh_token_expires = (
            refresh_token_expires or self.DEFAULT_REFRESH_TOKEN_EXPIRES
        )
        
        logger.info(
            f"JWTManager initialized with algorithm={algorithm}, "
            f"access_expires={self.access_token_expires}s, "
            f"refresh_expires={self.refresh_token_expires}s"
        )
    
    def create_access_token(
        self,
        user_id: str,
        roles: Optional[list] = None,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """アクセストークンを生成.
        
        Args:
            user_id: ユーザーID（subクレームに設定）
            roles: ユーザーロールのリスト
            expires_delta: カスタム有効期限（Noneの場合はデフォルト値）
            additional_claims: 追加のクレーム（任意）
        
        Returns:
            str: JWT文字列
        
        Raises:
            TokenGenerationError: トークン生成に失敗した場合
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token(
            ...     user_id="user123",
            ...     roles=["user", "premium"]
            ... )
        """
        try:
            now = datetime.utcnow()
            
            if expires_delta is None:
                expires_delta = timedelta(seconds=self.access_token_expires)
            
            # 標準クレーム
            payload = {
                "sub": user_id,  # Subject（ユーザーID）
                "iat": now,  # Issued At（発行時刻）
                "exp": now + expires_delta,  # Expiration Time（有効期限）
                "type": "access",  # トークンタイプ
                "jti": self._generate_jti()  # JWT ID（一意識別子）
            }
            
            # ロール追加
            if roles:
                payload["roles"] = roles
            
            # 追加クレーム
            if additional_claims:
                payload.update(additional_claims)
            
            # トークン生成
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug(f"Access token created for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise TokenGenerationError(f"Failed to create access token: {e}")
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """リフレッシュトークンを生成.
        
        Args:
            user_id: ユーザーID
            expires_delta: カスタム有効期限（Noneの場合はデフォルト値）
        
        Returns:
            str: JWT文字列
        
        Raises:
            TokenGenerationError: トークン生成に失敗した場合
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_refresh_token(user_id="user123")
        """
        try:
            now = datetime.utcnow()
            
            if expires_delta is None:
                expires_delta = timedelta(seconds=self.refresh_token_expires)
            
            payload = {
                "sub": user_id,
                "iat": now,
                "exp": now + expires_delta,
                "type": "refresh",
                "jti": self._generate_jti()
            }
            
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug(f"Refresh token created for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise TokenGenerationError(f"Failed to create refresh token: {e}")
    
    def verify_token(
        self,
        token: str,
        expected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """トークンを検証してペイロードを返す.
        
        Args:
            token: JWT文字列
            expected_type: 期待するトークンタイプ（"access" or "refresh"）
        
        Returns:
            dict: デコードされたペイロード
        
        Raises:
            TokenExpiredError: トークンの有効期限切れ
            InvalidTokenError: 無効なトークン
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token("user123")
            >>> payload = manager.verify_token(token, expected_type="access")
            >>> print(payload["sub"])  # "user123"
        """
        try:
            # トークンをデコード
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # トークンタイプ検証
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type:
                    raise InvalidTokenError(
                        f"Expected {expected_type} token, got {token_type}"
                    )
            
            logger.debug(f"Token verified for user {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: expired")
            raise TokenExpiredError("Token has expired")
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: {e}")
            raise InvalidTokenError(f"Invalid token: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise InvalidTokenError(f"Token verification error: {e}")
    
    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """トークンを検証せずにデコード（デバッグ用）.
        
        Warning:
            本番環境では使用しないこと。検証なしでデコードするため、
            トークンの真正性・有効性は保証されません。
        
        Args:
            token: JWT文字列
        
        Returns:
            dict: デコードされたペイロード
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> payload = manager.decode_token_without_verification(token)
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            raise InvalidTokenError(f"Failed to decode token: {e}")
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """トークンの有効期限を取得.
        
        Args:
            token: JWT文字列
        
        Returns:
            datetime: 有効期限（UTCタイムゾーン）
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token("user123")
            >>> expiry = manager.get_token_expiry(token)
            >>> print(expiry)
            2025-11-13 10:00:00
        """
        try:
            payload = self.decode_token_without_verification(token)
            exp_timestamp = payload.get("exp")
            
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token expiry: {e}")
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """トークンの有効期限切れチェック.
        
        Args:
            token: JWT文字列
        
        Returns:
            bool: 期限切れの場合True
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token("user123")
            >>> manager.is_token_expired(token)
            False
        """
        try:
            expiry = self.get_token_expiry(token)
            if expiry:
                return datetime.utcnow() > expiry
            return True
            
        except Exception:
            return True
    
    def get_token_user_id(self, token: str) -> Optional[str]:
        """トークンからユーザーIDを取得.
        
        Args:
            token: JWT文字列
        
        Returns:
            str: ユーザーID（subクレーム）
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token("user123")
            >>> user_id = manager.get_token_user_id(token)
            >>> print(user_id)  # "user123"
        """
        try:
            payload = self.decode_token_without_verification(token)
            return payload.get("sub")
        except Exception as e:
            logger.error(f"Failed to get user ID from token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """リフレッシュトークンから新しいアクセストークンを生成.
        
        Args:
            refresh_token: 有効なリフレッシュトークン
        
        Returns:
            str: 新しいアクセストークン
        
        Raises:
            TokenExpiredError: リフレッシュトークンの有効期限切れ
            InvalidTokenError: 無効なリフレッシュトークン
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> refresh_token = manager.create_refresh_token("user123")
            >>> new_access_token = manager.refresh_access_token(refresh_token)
        """
        # リフレッシュトークンを検証
        payload = self.verify_token(refresh_token, expected_type="refresh")
        
        user_id = payload.get("sub")
        roles = payload.get("roles")
        
        # 新しいアクセストークンを生成
        new_access_token = self.create_access_token(
            user_id=user_id,
            roles=roles
        )
        
        logger.info(f"Access token refreshed for user {user_id}")
        return new_access_token
    
    @staticmethod
    def _generate_jti() -> str:
        """JWT ID（一意識別子）を生成.
        
        Returns:
            str: UUID形式の一意識別子
        """
        from uuid import uuid4
        return str(uuid4())
    
    def get_token_info(self, token: str) -> dict:
        """トークンの詳細情報を取得（デバッグ用）.
        
        Args:
            token: JWT文字列
        
        Returns:
            dict: トークン情報
        
        Example:
            >>> manager = JWTManager(secret_key="my-secret-key")
            >>> token = manager.create_access_token("user123")
            >>> info = manager.get_token_info(token)
            >>> print(info)
            {
                'user_id': 'user123',
                'type': 'access',
                'issued_at': '2025-11-13T08:00:00',
                'expires_at': '2025-11-13T09:00:00',
                'is_expired': False,
                'remaining_seconds': 3540
            }
        """
        try:
            payload = self.decode_token_without_verification(token)
            
            issued_at = datetime.fromtimestamp(payload.get("iat", 0))
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            now = datetime.utcnow()
            
            remaining_seconds = max(0, int((expires_at - now).total_seconds()))
            
            return {
                'user_id': payload.get('sub'),
                'type': payload.get('type'),
                'roles': payload.get('roles', []),
                'issued_at': issued_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_expired': now > expires_at,
                'remaining_seconds': remaining_seconds,
                'jti': payload.get('jti')
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {
                'error': str(e),
                'valid': False
            }
