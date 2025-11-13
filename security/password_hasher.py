"""Password Hashing Module for LlmMultiChat3.

このモジュールはbcryptを使用したパスワードハッシュ化と検証を提供します。

Phase 3 Week 8-1:
- セキュアなパスワードハッシュ生成
- パスワード検証
- bcrypt salt自動生成（ラウンド数: 12）

使用例:
    >>> hasher = PasswordHasher()
    >>> password_hash = hasher.hash_password("SecurePass123!")
    >>> hasher.verify_password("SecurePass123!", password_hash)
    True
    >>> hasher.verify_password("WrongPass", password_hash)
    False
"""

import bcrypt
from typing import Optional
import logging
from exceptions import (
    PasswordHashingError,
    PasswordVerificationError,
    InvalidPasswordError
)


logger = logging.getLogger(__name__)


class PasswordHasher:
    """bcryptベースのパスワードハッシャー.
    
    bcryptの特徴:
    - 計算コストが高く、ブルートフォース攻撃に強い
    - 自動的にsaltを生成・管理
    - 業界標準のハッシュアルゴリズム
    
    Attributes:
        rounds: bcryptのコストファクター（デフォルト: 12）
                値が大きいほどセキュアだが計算時間が増加
                推奨値: 10-14（12が標準）
    """
    
    DEFAULT_ROUNDS = 12
    MIN_ROUNDS = 10
    MAX_ROUNDS = 16
    
    def __init__(self, rounds: Optional[int] = None):
        """PasswordHasherを初期化.
        
        Args:
            rounds: bcryptのラウンド数（デフォルト: 12）
                   10未満または16超過の場合は調整される
        """
        if rounds is None:
            self.rounds = self.DEFAULT_ROUNDS
        else:
            if rounds < self.MIN_ROUNDS:
                logger.warning(
                    f"Rounds {rounds} is too low. Using minimum: {self.MIN_ROUNDS}"
                )
                self.rounds = self.MIN_ROUNDS
            elif rounds > self.MAX_ROUNDS:
                logger.warning(
                    f"Rounds {rounds} is too high. Using maximum: {self.MAX_ROUNDS}"
                )
                self.rounds = self.MAX_ROUNDS
            else:
                self.rounds = rounds
        
        logger.info(f"PasswordHasher initialized with rounds={self.rounds}")
    
    def hash_password(self, password: str) -> str:
        """パスワードをハッシュ化.
        
        Args:
            password: プレーンテキストパスワード
        
        Returns:
            str: bcryptハッシュ文字列（例: "$2b$12$..."）
        
        Raises:
            InvalidPasswordError: パスワードが空または無効な場合
            PasswordHashingError: ハッシュ化に失敗した場合
        
        Example:
            >>> hasher = PasswordHasher()
            >>> hash_value = hasher.hash_password("MyPassword123!")
            >>> print(hash_value)
            $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqTlCj3nPm
        """
        if not password or not isinstance(password, str):
            raise InvalidPasswordError("Password must be a non-empty string")
        
        if len(password) > 72:
            # bcryptは72バイトまでしか処理しない
            logger.warning(
                f"Password exceeds 72 bytes (length: {len(password)}). "
                "Only first 72 bytes will be used."
            )
        
        try:
            # saltを生成（自動的にハッシュに含まれる）
            salt = bcrypt.gensalt(rounds=self.rounds)
            
            # パスワードをバイト列に変換してハッシュ化
            password_bytes = password.encode('utf-8')
            hash_bytes = bcrypt.hashpw(password_bytes, salt)
            
            # バイト列を文字列に変換
            hash_str = hash_bytes.decode('utf-8')
            
            logger.debug("Password hashed successfully")
            return hash_str
            
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise PasswordHashingError(f"Failed to hash password: {e}")
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """パスワードを検証.
        
        Args:
            password: プレーンテキストパスワード
            password_hash: bcryptハッシュ文字列
        
        Returns:
            bool: パスワードが一致する場合True、それ以外False
        
        Raises:
            InvalidPasswordError: パスワードまたはハッシュが無効な場合
            PasswordVerificationError: 検証処理に失敗した場合
        
        Example:
            >>> hasher = PasswordHasher()
            >>> hash_value = hasher.hash_password("MyPassword123!")
            >>> hasher.verify_password("MyPassword123!", hash_value)
            True
            >>> hasher.verify_password("WrongPassword", hash_value)
            False
        """
        if not password or not isinstance(password, str):
            raise InvalidPasswordError("Password must be a non-empty string")
        
        if not password_hash or not isinstance(password_hash, str):
            raise InvalidPasswordError("Password hash must be a non-empty string")
        
        # bcryptハッシュのフォーマット検証
        if not password_hash.startswith('$2b$') and not password_hash.startswith('$2a$'):
            raise InvalidPasswordError(
                "Invalid bcrypt hash format. Hash must start with $2b$ or $2a$"
            )
        
        try:
            # パスワードとハッシュをバイト列に変換
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            
            # 検証実行
            is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
            
            if is_valid:
                logger.debug("Password verification successful")
            else:
                logger.debug("Password verification failed: incorrect password")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            raise PasswordVerificationError(f"Failed to verify password: {e}")
    
    def needs_rehash(self, password_hash: str) -> bool:
        """ハッシュの再生成が必要かチェック.
        
        以下の場合に再ハッシュ化が推奨されます:
        - ラウンド数が現在の設定より低い
        - 古いbcryptバージョン（$2a$）を使用している
        
        Args:
            password_hash: bcryptハッシュ文字列
        
        Returns:
            bool: 再ハッシュ化が必要な場合True
        
        Example:
            >>> hasher = PasswordHasher(rounds=12)
            >>> old_hash = "$2a$10$..."  # 古いバージョン、低いラウンド数
            >>> hasher.needs_rehash(old_hash)
            True
        """
        if not password_hash or not isinstance(password_hash, str):
            return True
        
        try:
            # ハッシュからラウンド数を抽出（例: "$2b$12$..." -> 12）
            parts = password_hash.split('$')
            if len(parts) < 4:
                return True
            
            hash_version = parts[1]  # 例: "2b" または "2a"
            hash_rounds = int(parts[2])
            
            # 古いバージョンまたは低いラウンド数の場合は再ハッシュ化推奨
            if hash_version == '2a':
                logger.info("Old bcrypt version detected ($2a$), rehash recommended")
                return True
            
            if hash_rounds < self.rounds:
                logger.info(
                    f"Hash rounds ({hash_rounds}) lower than current ({self.rounds}), "
                    "rehash recommended"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check rehash requirement: {e}")
            return True
    
    @staticmethod
    def get_hash_info(password_hash: str) -> dict:
        """ハッシュの情報を取得.
        
        Args:
            password_hash: bcryptハッシュ文字列
        
        Returns:
            dict: ハッシュ情報（version, rounds, salt, hash）
        
        Example:
            >>> info = PasswordHasher.get_hash_info("$2b$12$LQv3c1yq...")
            >>> print(info)
            {'version': '2b', 'rounds': 12, 'salt': 'LQv3c1yq...', 'hash': '...'}
        """
        try:
            parts = password_hash.split('$')
            if len(parts) < 4:
                return {
                    'version': None,
                    'rounds': None,
                    'salt': None,
                    'hash': None,
                    'valid': False
                }
            
            # bcryptハッシュフォーマット: $2b$12$<22文字salt><31文字hash>
            version = parts[1]
            rounds = int(parts[2])
            salt_and_hash = parts[3] if len(parts) > 3 else ""
            
            salt = salt_and_hash[:22] if len(salt_and_hash) >= 22 else salt_and_hash
            hash_part = salt_and_hash[22:] if len(salt_and_hash) > 22 else ""
            
            return {
                'version': version,
                'rounds': rounds,
                'salt': salt,
                'hash': hash_part,
                'valid': True
            }
            
        except Exception as e:
            logger.error(f"Failed to parse hash info: {e}")
            return {
                'version': None,
                'rounds': None,
                'salt': None,
                'hash': None,
                'valid': False,
                'error': str(e)
            }
