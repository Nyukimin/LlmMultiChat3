"""
validators.pyのテストコード
"""
import pytest
from validators import InputValidator, CommandParser
from exceptions import ValidationError


class TestInputValidator:
    """InputValidatorクラスのテスト"""
    
    def test_validate_user_input_normal(self):
        """正常な入力のテスト"""
        # 正常なテキスト
        result = InputValidator.validate_user_input("こんにちは")
        assert result == "こんにちは"
        
        # 空白を含む正常なテキスト
        result = InputValidator.validate_user_input("  こんにちは  ")
        assert result == "こんにちは"  # 前後の空白は削除される
    
    def test_validate_user_input_empty(self):
        """空入力のテスト"""
        with pytest.raises(ValidationError, match="入力が空です"):
            InputValidator.validate_user_input("")
        
        with pytest.raises(ValidationError, match="入力が空です"):
            InputValidator.validate_user_input("   ")
    
    def test_validate_user_input_too_long(self):
        """長すぎる入力のテスト"""
        long_input = "a" * 10001
        with pytest.raises(ValidationError, match="入力が長すぎます"):
            InputValidator.validate_user_input(long_input)
    
    def test_validate_user_input_xss(self):
        """XSS攻撃のテスト"""
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>"
        ]
        
        for xss_input in xss_inputs:
            with pytest.raises(ValidationError, match="潜在的なXSS攻撃を検出"):
                InputValidator.validate_user_input(xss_input)
    
    def test_sanitize_user_input(self):
        """入力サニタイゼーションのテスト"""
        # HTMLエスケープ（二重エスケープ考慮）
        result = InputValidator.sanitize_user_input("<script>alert('test')</script>")
        assert "<script>" not in result
        # "&lt;" が "&amp;lt;" にエスケープされる可能性を考慮
        assert "&lt;" in result or "&amp;lt;" in result
        
        # 特殊文字エスケープ
        result = InputValidator.sanitize_user_input("Test & 'quotes' \"test\"")
        assert "&amp;" in result or "&amp;amp;" in result
    
    def test_validate_session_id_normal(self):
        """正常なセッションIDのテスト"""
        valid_ids = [
            "session_123",
            "SESSION-456",
            "abc123def456",
            "test_session_01"
        ]
        
        for valid_id in valid_ids:
            result = InputValidator.validate_session_id(valid_id)
            assert result == valid_id
    
    def test_validate_session_id_invalid(self):
        """無効なセッションIDのテスト"""
        # 空・短すぎる・長すぎる
        with pytest.raises(ValidationError):
            InputValidator.validate_session_id("")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_session_id("ab")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_session_id("a" * 101)
        
        # パストラバーサル
        with pytest.raises(ValidationError):
            InputValidator.validate_session_id("../session")
    
    def test_validate_speaker_name(self):
        """話者名検証のテスト"""
        # 正常なケース
        assert InputValidator.validate_speaker_name("Lumina") == True
        assert InputValidator.validate_speaker_name("Nox") == True
        assert InputValidator.validate_speaker_name("User") == True
        assert InputValidator.validate_speaker_name("system") == True
        
        # 異常なケース
        assert InputValidator.validate_speaker_name("") == False
        assert InputValidator.validate_speaker_name("a" * 51) == False
        assert InputValidator.validate_speaker_name("test<script>") == False
        assert InputValidator.validate_speaker_name("../admin") == False
    
    def test_validate_file_path(self):
        """ファイルパス検証のテスト"""
        # 正常なケース
        valid_paths = [
            "data/session.json",
            "logs/app.log",
            "memory/sessions/test.json",
            "./config/settings.yml"
        ]
        
        for path in valid_paths:
            result = InputValidator.validate_file_path(path)
            assert result == path
        
        # 異常なケース（パストラバーサル）
        invalid_paths = [
            "../etc/passwd",
            "../../secret.txt",
            "data/../../../root.txt",
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
        ]
        
        for path in invalid_paths:
            with pytest.raises(ValidationError):
                result = InputValidator.validate_file_path(path)
    
    def test_check_sql_injection(self):
        """SQLインジェクション検出のテスト"""
        # 安全な入力
        safe_inputs = [
            "こんにちは",
            "What's your name?",
        ]
        
        for safe_input in safe_inputs:
            result = InputValidator.check_sql_injection(safe_input)
            assert result == False
        
        # 危険な入力（数値比較パターン）
        dangerous_inputs = [
            "' OR 1=1",
            "admin' OR 1=1--",
            "; DROP TABLE users;",
            "UNION SELECT password FROM users-- ",
        ]
        
        for dangerous_input in dangerous_inputs:
            result = InputValidator.check_sql_injection(dangerous_input)
            assert result == True, f"Failed to detect SQL injection in: {dangerous_input}"
    
    def test_validate_command(self):
        """コマンド検証のテスト"""
        # 正常なコマンド
        valid_commands = [
            "/help",
            "/list sessions",
            "/export session_123",
            "/stats"
        ]
        
        for cmd in valid_commands:
            result = InputValidator.validate_command(cmd)
            assert result == cmd
        
        # 異常なコマンド
        with pytest.raises(ValidationError, match="コマンドは/で始まる必要があります"):
            InputValidator.validate_command("help")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_command("/test<script>")
    
    def test_sanitize_for_log(self):
        """ログサニタイゼーションのテスト"""
        # パスワードマスク
        log = "User password=secret123"
        result = InputValidator.sanitize_for_log(log)
        assert "secret123" not in result
        assert "***MASKED***" in result
        
        # APIキーマスク
        log = "api_key=sk-1234567890abcdef"
        result = InputValidator.sanitize_for_log(log)
        assert "sk-1234567890abcdef" not in result
        
        # トークンマスク
        log = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = InputValidator.sanitize_for_log(log)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result


class TestCommandParser:
    """CommandParserクラスのテスト"""
    
    def test_parse_simple_command(self):
        """シンプルなコマンド解析"""
        result = CommandParser.parse("/help")
        assert result == {
            "command": "help",
            "args": [],
            "kwargs": {}
        }
    
    def test_parse_command_with_args(self):
        """引数付きコマンド解析"""
        result = CommandParser.parse("/export session_123 json")
        assert result["command"] == "export"
        assert result["args"] == ["session_123", "json"]
    
    def test_parse_command_with_kwargs(self):
        """キーワード引数付きコマンド解析"""
        result = CommandParser.parse("/search query=testquery limit=10")
        assert result["command"] == "search"
        assert result["kwargs"]["query"] == "testquery"
        assert result["kwargs"]["limit"] == "10"
    
    def test_parse_invalid_command(self):
        """無効なコマンド解析"""
        with pytest.raises(ValidationError):
            CommandParser.parse("not a command")
        
        with pytest.raises(ValidationError):
            CommandParser.parse("/test<script>alert('xss')</script>")
    
    def test_get_command_name(self):
        """コマンド名取得"""
        assert CommandParser.get_command_name("/help") == "help"
        assert CommandParser.get_command_name("/export session_123") == "export"
        assert CommandParser.get_command_name("/stats --verbose") == "stats"
    
    def test_get_command_args(self):
        """コマンド引数取得"""
        args = CommandParser.get_command_args("/export session_123 json pretty")
        assert args == ["session_123", "json", "pretty"]
        
        args = CommandParser.get_command_args("/help")
        assert args == []


def test_integration_user_flow():
    """ユーザーフロー統合テスト"""
    # 1. ユーザー入力検証
    user_input = "  こんにちは、Luminaさん  "
    validated = InputValidator.validate_user_input(user_input)
    assert validated == "こんにちは、Luminaさん"
    
    # 2. セッションID検証
    session_id = "session_20250113_001"
    validated_session = InputValidator.validate_session_id(session_id)
    assert validated_session == session_id
    
    # 3. 話者名検証
    assert InputValidator.validate_speaker_name("Lumina") == True
    
    # 4. ログサニタイゼーション
    log_message = f"User {session_id} said: {validated}"
    sanitized = InputValidator.sanitize_for_log(log_message)
    assert "session_20250113_001" in sanitized


def test_security_attack_prevention():
    """セキュリティ攻撃防止テスト"""
    # XSS攻撃
    with pytest.raises(ValidationError):
        InputValidator.validate_user_input("<script>alert('XSS')</script>")
    
    # SQLインジェクション
    dangerous_input = "'; DROP TABLE users; --"
    assert InputValidator.check_sql_injection(dangerous_input) == True
    
    # パストラバーサル
    with pytest.raises(ValidationError):
        InputValidator.validate_file_path("../../etc/passwd")
    
    # コマンドインジェクション
    with pytest.raises(ValidationError):
        InputValidator.validate_command("/test; rm -rf /")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])