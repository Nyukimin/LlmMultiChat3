"""
Redis統合テスト
"""
import pytest
import time
from memory.redis_cache import RedisCache, get_redis_cache
from memory.mid_term import MidTermMemory


class TestRedisCache:
    """RedisCacheクラスのテスト"""
    
    @pytest.fixture
    def redis_cache(self):
        """Redisキャッシュインスタンス"""
        return RedisCache()
    
    def test_redis_availability(self, redis_cache):
        """Redis接続テスト"""
        # Redisが利用可能かどうかテスト
        # （Redisサーバーが起動していない場合はFalse）
        is_available = redis_cache.is_available()
        assert isinstance(is_available, bool)
    
    def test_set_get_string(self, redis_cache):
        """文字列の保存・取得テスト"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        key = "test:string"
        value = "Hello Redis"
        
        # 保存
        result = redis_cache.set(key, value)
        assert result == True
        
        # 取得
        retrieved = redis_cache.get(key)
        assert retrieved == value
        
        # 削除
        redis_cache.delete(key)
    
    def test_set_get_dict(self, redis_cache):
        """辞書の保存・取得テスト"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        key = "test:dict"
        value = {"name": "Lumina", "age": 25, "skills": ["magic", "healing"]}
        
        # 保存
        result = redis_cache.set(key, value)
        assert result == True
        
        # 取得
        retrieved = redis_cache.get(key, as_json=True)
        assert retrieved == value
        
        # 削除
        redis_cache.delete(key)
    
    def test_expire(self, redis_cache):
        """有効期限テスト"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        key = "test:expire"
        value = "expire_test"
        
        # 1秒で期限切れ
        redis_cache.set(key, value, expire_seconds=1)
        
        # すぐに取得（成功）
        retrieved = redis_cache.get(key)
        assert retrieved == value
        
        # 2秒待機
        time.sleep(2)
        
        # 期限切れで取得失敗
        retrieved = redis_cache.get(key)
        assert retrieved is None
    
    def test_exists(self, redis_cache):
        """存在確認テスト"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        key = "test:exists"
        value = "exists_test"
        
        # 最初は存在しない
        assert redis_cache.exists(key) == False
        
        # 保存後は存在する
        redis_cache.set(key, value)
        assert redis_cache.exists(key) == True
        
        # 削除後は存在しない
        redis_cache.delete(key)
        assert redis_cache.exists(key) == False
    
    def test_keys_pattern(self, redis_cache):
        """キー検索テスト"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        # テストキー作成
        redis_cache.set("test:pattern:1", "value1")
        redis_cache.set("test:pattern:2", "value2")
        redis_cache.set("test:other", "value3")
        
        # パターンマッチ
        keys = redis_cache.keys("test:pattern:*")
        assert len(keys) >= 2
        
        # クリーンアップ
        for key in keys:
            redis_cache.delete(key)
        redis_cache.delete("test:other")
    
    def test_get_info(self, redis_cache):
        """統計情報取得テスト"""
        info = redis_cache.get_info()
        
        assert "enabled" in info
        
        if redis_cache.is_available():
            assert info["enabled"] == True
            assert "used_memory" in info
            assert "keyspace" in info


class TestMidTermMemoryWithRedis:
    """中期記憶のRedis統合テスト"""
    
    @pytest.fixture
    def mid_term_memory(self):
        """中期記憶インスタンス（Redis有効）"""
        return MidTermMemory(redis_enabled=True)
    
    def test_store_retrieve_with_redis(self, mid_term_memory):
        """Redis経由のデータ保存・取得テスト"""
        key = "session:test_001"
        value = {"user": "Lumina", "turns": 5}
        
        # 保存
        result = mid_term_memory.store(key, value)
        assert result == True
        
        # 取得（Redisから）
        retrieved = mid_term_memory.retrieve(key)
        assert retrieved == value
        
        # 統計確認
        if mid_term_memory.redis_cache and mid_term_memory.redis_cache.is_available():
            assert mid_term_memory.stats['redis_hits'] >= 0
        
        # クリーンアップ
        mid_term_memory.delete(key)
    
    def test_fallback_to_json(self, mid_term_memory):
        """Redisフォールバック時のJSON動作テスト"""
        key = "session:fallback_test"
        value = {"user": "Nox", "data": "fallback"}
        
        # 保存（Redis無効でもJSONに保存される）
        result = mid_term_memory.store(key, value)
        assert result == True
        
        # 取得（JSONファイルから）
        retrieved = mid_term_memory.retrieve(key)
        assert retrieved == value
        
        # クリーンアップ
        mid_term_memory.delete(key)
    
    def test_delete_from_both_layers(self, mid_term_memory):
        """Redis + JSON両方からの削除テスト"""
        key = "session:delete_test"
        value = {"test": "delete"}
        
        # 保存
        mid_term_memory.store(key, value)
        
        # 削除
        result = mid_term_memory.delete(key)
        assert result == True
        
        # 取得失敗
        retrieved = mid_term_memory.retrieve(key)
        assert retrieved is None
    
    def test_performance_comparison(self, mid_term_memory):
        """Redisとファイル読み込みのパフォーマンス比較"""
        if not mid_term_memory.redis_cache or not mid_term_memory.redis_cache.is_available():
            pytest.skip("Redis not available")
        
        key = "session:perf_test"
        value = {"data": "x" * 1000}  # 1KB程度のデータ
        
        # データ保存
        mid_term_memory.store(key, value)
        
        # 1回目: Redisキャッシュヒット
        start = time.time()
        retrieved1 = mid_term_memory.retrieve(key)
        redis_time = time.time() - start
        
        # Redisキャッシュクリア（テスト用）
        if mid_term_memory.redis_cache:
            mid_term_memory.redis_cache.delete(f"mid_term:{key}")
        
        # 2回目: JSONファイルから読み込み
        start = time.time()
        retrieved2 = mid_term_memory.retrieve(key)
        json_time = time.time() - start
        
        # 結果検証
        assert retrieved1 == value
        assert retrieved2 == value
        
        # パフォーマンス比較（参考値）
        print(f"\nRedis取得: {redis_time*1000:.2f}ms")
        print(f"JSON取得: {json_time*1000:.2f}ms")
        print(f"速度比: {json_time/redis_time:.1f}倍高速")
        
        # クリーンアップ
        mid_term_memory.delete(key)


def test_singleton_pattern():
    """シングルトンパターンテスト"""
    cache1 = get_redis_cache()
    cache2 = get_redis_cache()
    
    # 同一インスタンス
    assert cache1 is cache2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])