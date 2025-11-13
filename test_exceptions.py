"""
test_exceptions.py
例外クラスのユニットテスト

カスタム例外クラスの動作を検証。
"""

import pytest
from exceptions import (
    LlmMultiChatError,
    MemoryError,
    ShortTermMemoryError,
    MidTermMemoryError,
    LongTermMemoryError,
    KnowledgeBaseError,
    AssociativeMemoryError,
    LLMNodeError,
    LLMInvocationError,
    LLMTimeoutError,
    ConfigurationError,
    ValidationError,
    FileOperationError,
    DatabaseError,
    DuckDBError,
    RedisError,
    Neo4jError,
    ExportError,
    ERROR_CODES
)


class TestBaseException:
    """基底例外クラスのテスト"""
    
    def test_base_exception_creation(self):
        """基底例外の作成テスト"""
        error = LlmMultiChatError("テストエラー", "E0001")
        assert error.message == "テストエラー"
        assert error.error_code == "E0001"
        assert str(error) == "[E0001] テストエラー"
    
    def test_base_exception_default_code(self):
        """デフォルトエラーコードのテスト"""
        error = LlmMultiChatError("デフォルトエラー")
        assert error.error_code == "E0000"


class TestMemoryExceptions:
    """記憶システム例外のテスト"""
    
    def test_memory_error(self):
        """記憶システムエラーのテスト"""
        error = MemoryError("記憶エラー")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E1000"
    
    def test_short_term_memory_error(self):
        """短期記憶エラーのテスト"""
        error = ShortTermMemoryError("短期記憶エラー")
        assert isinstance(error, MemoryError)
        assert error.error_code == "E1100"
    
    def test_mid_term_memory_error(self):
        """中期記憶エラーのテスト"""
        error = MidTermMemoryError("中期記憶エラー")
        assert isinstance(error, MemoryError)
        assert error.error_code == "E1200"
    
    def test_long_term_memory_error(self):
        """長期記憶エラーのテスト"""
        error = LongTermMemoryError("長期記憶エラー")
        assert isinstance(error, MemoryError)
        assert error.error_code == "E1300"
    
    def test_knowledge_base_error(self):
        """知識ベースエラーのテスト"""
        error = KnowledgeBaseError("知識ベースエラー")
        assert isinstance(error, MemoryError)
        assert error.error_code == "E1400"
    
    def test_associative_memory_error(self):
        """連想記憶エラーのテスト"""
        error = AssociativeMemoryError("連想記憶エラー")
        assert isinstance(error, MemoryError)
        assert error.error_code == "E1500"


class TestLLMNodeExceptions:
    """LLMノード例外のテスト"""
    
    def test_llm_node_error(self):
        """LLMノードエラーのテスト"""
        error = LLMNodeError("ノードエラー", node_name="ルミナ")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E2000"
        assert error.node_name == "ルミナ"
        assert "ルミナ" in str(error)
    
    def test_llm_invocation_error(self):
        """LLM呼び出しエラーのテスト"""
        error = LLMInvocationError("LLM呼び出し失敗", node_name="クラリス")
        assert isinstance(error, LLMNodeError)
        assert error.error_code == "E2100"
        assert error.node_name == "クラリス"
    
    def test_llm_timeout_error(self):
        """LLMタイムアウトエラーのテスト"""
        error = LLMTimeoutError("タイムアウト", node_name="ノクス")
        assert isinstance(error, LLMNodeError)
        assert error.error_code == "E2200"
        assert error.node_name == "ノクス"


class TestConfigurationValidationExceptions:
    """設定・検証例外のテスト"""
    
    def test_configuration_error(self):
        """設定エラーのテスト"""
        error = ConfigurationError("設定エラー")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E3000"
    
    def test_validation_error(self):
        """検証エラーのテスト"""
        error = ValidationError("検証失敗", field="user_input")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E4000"
        assert error.field == "user_input"
        assert "user_input" in str(error)
    
    def test_validation_error_no_field(self):
        """フィールド指定なし検証エラーのテスト"""
        error = ValidationError("検証失敗")
        assert error.field == ""
        assert "検証失敗" in str(error)


class TestFileOperationException:
    """ファイル操作例外のテスト"""
    
    def test_file_operation_error(self):
        """ファイル操作エラーのテスト"""
        error = FileOperationError("ファイル読み込み失敗", filepath="test.json")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E5000"
        assert error.filepath == "test.json"
        assert "test.json" in str(error)


class TestDatabaseExceptions:
    """データベース例外のテスト"""
    
    def test_database_error(self):
        """データベースエラーのテスト"""
        error = DatabaseError("DB接続失敗")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E6000"
    
    def test_duckdb_error(self):
        """DuckDBエラーのテスト"""
        error = DuckDBError("DuckDBクエリ失敗")
        assert isinstance(error, DatabaseError)
        assert error.error_code == "E6100"
    
    def test_redis_error(self):
        """Redisエラーのテスト"""
        error = RedisError("Redis接続失敗")
        assert isinstance(error, DatabaseError)
        assert error.error_code == "E6200"
    
    def test_neo4j_error(self):
        """Neo4jエラーのテスト"""
        error = Neo4jError("Neo4jクエリ失敗")
        assert isinstance(error, DatabaseError)
        assert error.error_code == "E6300"


class TestExportException:
    """エクスポート例外のテスト"""
    
    def test_export_error(self):
        """エクスポートエラーのテスト"""
        error = ExportError("エクスポート失敗")
        assert isinstance(error, LlmMultiChatError)
        assert error.error_code == "E7000"


class TestErrorCodes:
    """エラーコード一覧のテスト"""
    
    def test_error_codes_exist(self):
        """エラーコード辞書の存在確認"""
        assert isinstance(ERROR_CODES, dict)
        assert len(ERROR_CODES) > 0
    
    def test_all_error_codes_documented(self):
        """主要エラーコードが辞書に含まれるか確認"""
        expected_codes = [
            "E0000", "E1000", "E1100", "E1200", "E1300", "E1400", "E1500",
            "E2000", "E2100", "E2200", "E3000", "E4000", "E5000",
            "E6000", "E6100", "E6200", "E6300", "E7000"
        ]
        for code in expected_codes:
            assert code in ERROR_CODES, f"エラーコード {code} が辞書に存在しません"


class TestExceptionRaising:
    """例外の発生テスト"""
    
    def test_raise_and_catch_memory_error(self):
        """記憶エラーの発生とキャッチ"""
        with pytest.raises(MemoryError) as excinfo:
            raise MemoryError("テスト記憶エラー")
        assert "テスト記憶エラー" in str(excinfo.value)
    
    def test_raise_and_catch_validation_error(self):
        """検証エラーの発生とキャッチ"""
        with pytest.raises(ValidationError) as excinfo:
            raise ValidationError("不正な入力", field="email")
        assert "email" in str(excinfo.value)
    
    def test_catch_base_exception(self):
        """基底例外でのキャッチ"""
        with pytest.raises(LlmMultiChatError):
            raise ShortTermMemoryError("短期記憶エラー")


class TestExceptionChaining:
    """例外チェーンのテスト"""
    
    def test_exception_from_another(self):
        """例外チェーンの動作確認"""
        try:
            try:
                raise ValueError("元の例外")
            except ValueError as e:
                raise MemoryError("記憶エラー") from e
        except MemoryError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])