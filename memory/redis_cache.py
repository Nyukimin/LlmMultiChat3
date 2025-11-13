"""
Redis キャッシュモジュール
中期記憶のキャッシュ層として使用
"""

import redis
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from exceptions import MidTermMemoryError
from utils import Logger


class RedisCache:
    """Redisキャッシュマネージャー"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        max_connections: int = 10,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5
    ):
        """
        初期化
        
        Args:
            host: Redisホスト
            port: Redisポート
            db: データベース番号
            password: 認証パスワード
            decode_responses: レスポンスを文字列としてデコード
            max_connections: 最大接続数
            socket_timeout: ソケットタイムアウト（秒）
            socket_connect_timeout: 接続タイムアウト（秒）
        """
        self.logger = Logger()
        self.enabled = False
        self.redis_client: Optional[redis.Redis] = None
        
        try:
            # Redis接続プールの作成
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
            )
            
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # 接続テスト
            self.redis_client.ping()
            self.enabled = True
            
            self.logger.log_info("Redis接続成功", context="RedisCache")
            
        except redis.ConnectionError as e:
            self.logger.log_warning(
                f"Redis接続失敗（JSONフォールバック使用）: {e}",
                context="RedisCache"
            )
            self.enabled = False
        except Exception as e:
            self.logger.log_error(e, context="RedisCache.__init__")
            self.enabled = False
    
    def is_available(self) -> bool:
        """
        Redis接続が利用可能か確認
        
        Returns:
            利用可能な場合True
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        キーバリューを設定
        
        Args:
            key: キー
            value: 値（辞書・リストの場合JSON変換）
            expire_seconds: 有効期限（秒）
            
        Returns:
            成功した場合True
        """
        if not self.is_available():
            return False
        
        try:
            # 辞書・リストの場合はJSON変換
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire_seconds:
                self.redis_client.setex(key, expire_seconds, value)
            else:
                self.redis_client.set(key, value)
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.set({key})")
            return False
    
    def get(self, key: str, as_json: bool = False) -> Optional[Any]:
        """
        キーから値を取得
        
        Args:
            key: キー
            as_json: JSON文字列として取得してパース
            
        Returns:
            値（存在しない場合None）
        """
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                return None
            
            # JSON文字列の場合はパース
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
            
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.get({key})")
            return None
    
    def delete(self, key: str) -> bool:
        """
        キーを削除
        
        Args:
            key: キー
            
        Returns:
            成功した場合True
        """
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.delete({key})")
            return False
    
    def exists(self, key: str) -> bool:
        """
        キーが存在するか確認
        
        Args:
            key: キー
            
        Returns:
            存在する場合True
        """
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.exists({key})")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """
        パターンに一致するキー一覧を取得
        
        Args:
            pattern: 検索パターン（ワイルドカード可）
            
        Returns:
            キーのリスト
        """
        if not self.is_available():
            return []
        
        try:
            return [k.decode('utf-8') if isinstance(k, bytes) else k 
                    for k in self.redis_client.keys(pattern)]
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.keys({pattern})")
            return []
    
    def ttl(self, key: str) -> int:
        """
        キーの残存時間を取得（秒）
        
        Args:
            key: キー
            
        Returns:
            残存時間（秒）、存在しない場合-2、無期限の場合-1
        """
        if not self.is_available():
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.ttl({key})")
            return -2
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        キーに有効期限を設定
        
        Args:
            key: キー
            seconds: 有効期限（秒）
            
        Returns:
            成功した場合True
        """
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            self.logger.log_error(e, context=f"RedisCache.expire({key})")
            return False
    
    def flushdb(self) -> bool:
        """
        現在のデータベースをクリア
        
        Returns:
            成功した場合True
        """
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            self.logger.log_info("Redisデータベースをクリアしました", context="RedisCache")
            return True
        except Exception as e:
            self.logger.log_error(e, context="RedisCache.flushdb")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Redis統計情報を取得
        
        Returns:
            統計情報辞書
        """
        if not self.is_available():
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace": self.redis_client.dbsize(),
                "uptime_seconds": info.get('uptime_in_seconds', 0),
            }
        except Exception as e:
            self.logger.log_error(e, context="RedisCache.get_info")
            return {"enabled": False, "error": str(e)}
    
    def close(self):
        """接続をクローズ"""
        if self.redis_client:
            try:
                self.redis_client.close()
                self.logger.log_info("Redis接続をクローズしました", context="RedisCache")
            except Exception as e:
                self.logger.log_error(e, context="RedisCache.close")


# グローバルインスタンス（シングルトン）
_redis_cache_instance: Optional[RedisCache] = None


def get_redis_cache(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
) -> RedisCache:
    """
    Redisキャッシュのシングルトンインスタンスを取得
    
    Args:
        host: Redisホスト
        port: Redisポート
        db: データベース番号
        password: 認証パスワード
        
    Returns:
        RedisCache インスタンス
    """
    global _redis_cache_instance
    
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCache(
            host=host,
            port=port,
            db=db,
            password=password
        )
    
    return _redis_cache_instance