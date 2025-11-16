"""User Manager for LlmMultiChat3.

このモジュールはユーザー登録・ログイン・管理機能を提供します。

Phase 3 Week 8-2:
- ユーザー登録（重複チェック・パスワードハッシュ化）
- ログイン（認証・トークン発行）
- トークン更新
- ユーザー情報取得・更新
- パスワードリセット

使用例:
    >>> user_manager = UserManager(
    ...     jwt_manager=jwt_manager,
    ...     password_hasher=password_hasher,
    ...     db_path="db/users.db"
    ... )
    >>> user = user_manager.register_user(
    ...     username="john_doe",
    ...     email="john@example.com",
    ...     password="SecurePass123!"
    ... )
    >>> tokens = user_manager.login("john@example.com", "SecurePass123!")
"""

import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path
import json

from security.models import (
    User,
    UserProfile
)
from security.jwt_manager import JWTManager
from security.password_hasher import PasswordHasher
from security.role_manager import RoleManager
from exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    InvalidTokenError,
    DatabaseError
)


logger = logging.getLogger(__name__)


class UserManager:
    """ユーザー管理クラス.
    
    SQLiteデータベースを使用してユーザー情報を永続化します。
    
    Attributes:
        jwt_manager: JWT管理インスタンス
        password_hasher: パスワードハッシャーインスタンス
        role_manager: ロール管理インスタンス
        db_path: SQLiteデータベースファイルパス
        redis_client: Redisキャッシュクライアント（オプション）
    """
    
    def __init__(
        self,
        jwt_manager: JWTManager,
        password_hasher: Optional[PasswordHasher] = None,
        role_manager: Optional[RoleManager] = None,
        db_path: str = "db/users.db",
        redis_client: Optional[Any] = None
    ):
        """UserManagerを初期化.
        
        Args:
            jwt_manager: JWT管理インスタンス
            password_hasher: パスワードハッシャー（Noneの場合は新規作成）
            role_manager: ロール管理インスタンス（Noneの場合は新規作成）
            db_path: SQLiteデータベースファイルパス
            redis_client: Redisキャッシュクライアント（オプション）
        """
        self.jwt_manager = jwt_manager
        self.password_hasher = password_hasher or PasswordHasher()
        self.role_manager = role_manager or RoleManager()
        self.db_path = db_path
        self.redis_client = redis_client
        
        # データベース初期化
        self._init_database()
        
        logger.info(f"UserManager initialized with database: {db_path}")
    
    def _init_database(self):
        """SQLiteデータベースを初期化.
        
        usersテーブルを作成（既存の場合はスキップ）。
        """
        # ディレクトリ作成
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # usersテーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_verified INTEGER NOT NULL DEFAULT 0,
                    quota_limit INTEGER NOT NULL DEFAULT 1000,
                    quota_used INTEGER NOT NULL DEFAULT 0,
                    quota_reset_at TEXT
                )
            """)
            
            # インデックス作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email
                ON users(email)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username
                ON users(username)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得.
        
        Returns:
            sqlite3.Connection: データベース接続
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None
    ) -> User:
        """新規ユーザーを登録.
        
        Args:
            username: ユーザー名
            email: メールアドレス
            password: パスワード（プレーンテキスト）
            roles: ロールリスト（デフォルト: ["user"]）
        
        Returns:
            User: 登録されたユーザーオブジェクト
        
        Raises:
            UserAlreadyExistsError: ユーザーが既に存在する場合
            DatabaseError: データベースエラー
        
        Example:
            >>> user = user_manager.register_user(
            ...     username="john_doe",
            ...     email="john@example.com",
            ...     password="SecurePass123!"
            ... )
        """
        # 1. 重複チェック
        if self.user_exists(email=email):
            raise UserAlreadyExistsError(
                f"User with email {email} already exists"
            )
        
        if self.user_exists(username=username):
            raise UserAlreadyExistsError(
                f"User with username {username} already exists"
            )
        
        # 2. パスワードハッシュ化
        password_hash = self.password_hasher.hash_password(password)
        
        # 3. ユーザーオブジェクト作成
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles or ["user"]
        )
        
        # 4. データベース保存
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, email, password_hash, roles,
                    created_at, last_login, is_active, is_verified,
                    quota_limit, quota_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.username,
                user.email,
                user.password_hash,
                json.dumps(user.roles),
                user.created_at.isoformat(),
                user.last_login.isoformat() if user.last_login else None,
                1 if user.is_active else 0,
                1 if user.is_verified else 0,
                user.quota_limit,
                user.quota_used
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User registered: {user.user_id} ({user.email})")
            return user
            
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            raise DatabaseError(f"Failed to register user: {e}")
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """ユーザーログイン.
        
        Args:
            email: メールアドレス
            password: パスワード（プレーンテキスト）
        
        Returns:
            dict: トークン情報（access_token, refresh_token等）
        
        Raises:
            InvalidCredentialsError: 認証失敗
            UserNotFoundError: ユーザーが存在しない
        
        Example:
            >>> tokens = user_manager.login(
            ...     email="john@example.com",
            ...     password="SecurePass123!"
            ... )
            >>> print(tokens["access_token"])
        """
        # 1. ユーザー取得
        user = self.get_user_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # 2. アカウント有効性チェック
        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive")
        
        # 3. パスワード検証
        if not self.password_hasher.verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {email}")
            raise InvalidCredentialsError("Invalid email or password")
        
        # 4. トークン生成
        access_token = self.jwt_manager.create_access_token(
            user_id=user.user_id,
            roles=user.roles
        )
        
        refresh_token = self.jwt_manager.create_refresh_token(
            user_id=user.user_id
        )
        
        # 5. Redisにリフレッシュトークンを保存（有効な場合）
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"refresh_token:{user.user_id}",
                    2592000,  # 30日
                    refresh_token
                )
            except Exception as e:
                logger.warning(f"Failed to cache refresh token: {e}")
        
        # 6. 最終ログイン日時を更新
        self._update_last_login(user.user_id)
        
        logger.info(f"User logged in: {user.user_id} ({user.email})")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600  # 1時間
        }
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """リフレッシュトークンから新しいアクセストークンを生成.
        
        Args:
            refresh_token: リフレッシュトークン
        
        Returns:
            str: 新しいアクセストークン
        
        Raises:
            TokenExpiredError: リフレッシュトークンの有効期限切れ
            InvalidTokenError: 無効なリフレッシュトークン
        
        Example:
            >>> new_token = user_manager.refresh_access_token(refresh_token)
        """
        # リフレッシュトークンを検証
        payload = self.jwt_manager.verify_token(
            refresh_token,
            expected_type="refresh"
        )
        
        user_id = payload.get("sub")
        
        # Redisでトークンを検証（有効な場合）
        if self.redis_client:
            try:
                cached_token = self.redis_client.get(f"refresh_token:{user_id}")
                if cached_token and cached_token.decode() != refresh_token:
                    raise InvalidTokenError("Refresh token has been revoked")
            except Exception as e:
                logger.warning(f"Failed to verify refresh token in Redis: {e}")
        
        # ユーザー情報を取得
        user = self.get_user_by_id(user_id)
        if not user:
            raise InvalidTokenError("User not found")
        
        # 新しいアクセストークンを生成
        new_access_token = self.jwt_manager.create_access_token(
            user_id=user.user_id,
            roles=user.roles
        )
        
        logger.info(f"Access token refreshed for user: {user_id}")
        return new_access_token
    
    def logout(self, user_id: str):
        """ユーザーログアウト（リフレッシュトークンを無効化）.
        
        Args:
            user_id: ユーザーID
        
        Example:
            >>> user_manager.logout("user123")
        """
        if self.redis_client:
            try:
                self.redis_client.delete(f"refresh_token:{user_id}")
                logger.info(f"User logged out: {user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete refresh token: {e}")
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザーを取得.
        
        Args:
            user_id: ユーザーID
        
        Returns:
            User: ユーザーオブジェクト（存在しない場合None）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_user(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            raise DatabaseError(f"Failed to get user: {e}")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """メールアドレスでユーザーを取得.
        
        Args:
            email: メールアドレス
        
        Returns:
            User: ユーザーオブジェクト（存在しない場合None）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_user(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            raise DatabaseError(f"Failed to get user: {e}")
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得.
        
        Args:
            username: ユーザー名
        
        Returns:
            User: ユーザーオブジェクト（存在しない場合None）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_user(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            raise DatabaseError(f"Failed to get user: {e}")
    
    def user_exists(self, email: Optional[str] = None, username: Optional[str] = None) -> bool:
        """ユーザーの存在確認.
        
        Args:
            email: メールアドレス（オプション）
            username: ユーザー名（オプション）
        
        Returns:
            bool: ユーザーが存在する場合True
        """
        if email:
            return self.get_user_by_email(email) is not None
        
        if username:
            return self.get_user_by_username(username) is not None
        
        return False
    
    def update_user(self, user_id: str, **kwargs) -> User:
        """ユーザー情報を更新.
        
        Args:
            user_id: ユーザーID
            **kwargs: 更新するフィールド（username, email, roles等）
        
        Returns:
            User: 更新されたユーザーオブジェクト
        
        Raises:
            UserNotFoundError: ユーザーが存在しない
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # 更新可能なフィールド
        allowed_fields = {
            "username", "email", "roles", "is_active",
            "is_verified", "quota_limit"
        }
        
        update_fields = []
        update_values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == "roles":
                    value = json.dumps(value)
                elif field in ["is_active", "is_verified"]:
                    value = 1 if value else 0
                
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_fields:
            logger.warning(f"No valid fields to update for user {user_id}")
            return user
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
            update_values.append(user_id)
            
            cursor.execute(query, update_values)
            conn.commit()
            conn.close()
            
            logger.info(f"User updated: {user_id}")
            
            # 更新後のユーザー情報を取得
            return self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise DatabaseError(f"Failed to update user: {e}")
    
    def delete_user(self, user_id: str):
        """ユーザーを削除.
        
        Args:
            user_id: ユーザーID
        
        Raises:
            UserNotFoundError: ユーザーが存在しない
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            
            # Redisからリフレッシュトークンを削除
            if self.redis_client:
                self.redis_client.delete(f"refresh_token:{user_id}")
            
            logger.info(f"User deleted: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise DatabaseError(f"Failed to delete user: {e}")
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """ユーザープロファイルを取得（パスワードハッシュを除く）.
        
        Args:
            user_id: ユーザーID
        
        Returns:
            UserProfile: ユーザープロファイル
        
        Raises:
            UserNotFoundError: ユーザーが存在しない
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
            is_verified=user.is_verified,
            quota_limit=user.quota_limit,
            quota_used=user.quota_used
        )
    
    def _update_last_login(self, user_id: str):
        """最終ログイン日時を更新.
        
        Args:
            user_id: ユーザーID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE user_id = ?",
                (datetime.utcnow().isoformat(), user_id)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"Failed to update last login: {e}")
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """SQLiteの行をUserオブジェクトに変換.
        
        Args:
            row: SQLiteの行
        
        Returns:
            User: ユーザーオブジェクト
        """
        return User(
            user_id=row["user_id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            roles=json.loads(row["roles"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
            is_active=bool(row["is_active"]),
            is_verified=bool(row["is_verified"]),
            quota_limit=row["quota_limit"],
            quota_used=row["quota_used"]
        )
