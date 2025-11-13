"""
validators.py
入力検証・サニタイゼーション

ユーザー入力、コマンド、セッションIDの検証を行う。
XSS対策、SQLインジェクション対策を含む。
"""

import re
from typing import Optional, List
from exceptions import ValidationError


class InputValidator:
    """入力検証クラス"""
    
    # 定数
    MAX_MESSAGE_LENGTH = 10000
    MAX_SESSION_ID_LENGTH = 100
    ALLOWED_COMMANDS = [
        '/reset', '/export', '/history', '/memory', '/quit',
        '/help', '/list', '/stats', '/search'
    ]
    
    # 禁止パターン（SQLインジェクション対策）
    SQL_INJECTION_PATTERNS = [
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",  # OR 1=1, AND 1=1（数値比較のみ）
        r";\s*(DROP|DELETE|UPDATE|INSERT)\b",  # ; DROP TABLE
        r"--\s",  # SQLコメント（スペース付き）
        r"/\*.*\*/",  # SQLコメント
        r"\bUNION\s+SELECT\b",  # UNION SELECT
    ]
    
    # XSS対策用エスケープマップ
    XSS_ESCAPE_MAP = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;',
    }
    
    @staticmethod
    def validate_user_input(text: str, allow_empty: bool = False) -> str:
        """
        ユーザー入力検証
        
        Args:
            text: 入力文字列
            allow_empty: 空文字列を許可するか
            
        Returns:
            サニタイズされた文字列
            
        Raises:
            ValidationError: 検証失敗時
        """
        # 前後の空白を削除
        text = text.strip() if text else ""
        
        # 空文字チェック
        if not text:
            if not allow_empty:
                raise ValidationError(
                    "入力が空です",
                    field="user_input"
                )
            return ""
        
        # 長さチェック
        if len(text) > InputValidator.MAX_MESSAGE_LENGTH:
            raise ValidationError(
                f"入力が長すぎます（最大{InputValidator.MAX_MESSAGE_LENGTH}文字）",
                field="user_input"
            )
        
        # XSS対策（危険なタグ検出）
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',  # onclick, onerror等
            r'<iframe',
            r'<object',
            r'<embed',
        ]
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(
                    "潜在的なXSS攻撃を検出しました",
                    field="user_input",
                    error_code="E4010"
                )
        
        # SQLインジェクション対策
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(
                    "不正な入力パターンが検出されました",
                    field="user_input",
                    error_code="E4001"
                )
        
        return text
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """
        ユーザー入力サニタイゼーション（HTMLエスケープ）
        
        Args:
            text: 入力文字列
            
        Returns:
            エスケープ済み文字列
        """
        return InputValidator._escape_html(text)
    
    @staticmethod
    def validate_speaker_name(speaker: str) -> bool:
        """
        話者名検証
        
        Args:
            speaker: 話者名
            
        Returns:
            有効な場合True
        """
        if not speaker or len(speaker) > 50:
            return False
        
        # 危険な文字チェック
        dangerous_chars = ['<', '>', '/', '\\', '..']
        for char in dangerous_chars:
            if char in speaker:
                return False
        
        return True
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """
        SQLインジェクション検出
        
        Args:
            text: 検査対象文字列
            
        Returns:
            危険な場合True
        """
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def validate_command(command: str) -> str:
        """
        コマンド検証
        
        Args:
            command: コマンド文字列
            
        Returns:
            検証済みコマンド
            
        Raises:
            ValidationError: 検証失敗時
        """
        if not command:
            raise ValidationError(
                "コマンドが空です",
                field="command"
            )
        
        # コマンド形式チェック
        if not command.startswith('/'):
            raise ValidationError(
                "コマンドは/で始まる必要があります",
                field="command",
                error_code="E4002"
            )
        
        # コマンド名取得（最初の単語）
        cmd_name = command.split()[0]
        
        # 許可リストチェック
        if cmd_name not in InputValidator.ALLOWED_COMMANDS:
            raise ValidationError(
                f"不正なコマンド: {cmd_name}",
                field="command",
                error_code="E4002"
            )
        
        # 危険な文字チェック
        if any(char in command for char in ['<', '>', ';', '|', '&', '$', '`']):
            raise ValidationError(
                "無効なコマンド形式",
                field="command",
                error_code="E4002"
            )
        
        return command
    
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """
        セッションID検証（英数字・ハイフン・アンダースコアのみ）
        
        Args:
            session_id: セッションID
            
        Returns:
            検証済みセッションID
            
        Raises:
            ValidationError: 検証失敗時
        """
        if not session_id:
            raise ValidationError(
                "セッションIDが空です",
                field="session_id"
            )
        
        # 長さチェック（最小3文字）
        if len(session_id) < 3:
            raise ValidationError(
                "セッションIDが短すぎます（最小3文字）",
                field="session_id"
            )
        
        if len(session_id) > InputValidator.MAX_SESSION_ID_LENGTH:
            raise ValidationError(
                f"セッションIDが長すぎます（最大{InputValidator.MAX_SESSION_ID_LENGTH}文字）",
                field="session_id"
            )
        
        # 文字種チェック（英数字・ハイフン・アンダースコアのみ）
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise ValidationError(
                "セッションIDに不正な文字が含まれています（英数字・ハイフン・アンダースコアのみ許可）",
                field="session_id",
                error_code="E4003"
            )
        
        return session_id
    
    @staticmethod
    def validate_file_path(filepath: str, allowed_extensions: Optional[List[str]] = None) -> str:
        """
        ファイルパス検証（パストラバーサル対策）
        
        Args:
            filepath: ファイルパス
            allowed_extensions: 許可する拡張子リスト（例: ['.json', '.txt']）
            
        Returns:
            検証済みファイルパス
            
        Raises:
            ValidationError: 検証失敗時
        """
        if not filepath:
            raise ValidationError(
                "ファイルパスが空です",
                field="filepath"
            )
        
        # パストラバーサル対策（../ や ..\\ を含まない）
        if '..' in filepath:
            raise ValidationError(
                "不正なファイルパスです（パストラバーサル検出）",
                field="filepath",
                error_code="E4004"
            )
        
        # 絶対パス禁止（ルートディレクトリアクセス防止）
        if filepath.startswith('/') or (len(filepath) > 1 and filepath[1] == ':'):
            raise ValidationError(
                "絶対パスは許可されていません",
                field="filepath",
                error_code="E4005"
            )
        
        # 拡張子チェック
        if allowed_extensions:
            if not any(filepath.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(
                    f"許可されていない拡張子です（許可: {', '.join(allowed_extensions)}）",
                    field="filepath",
                    error_code="E4006"
                )
        
        return filepath
    
    @staticmethod
    def validate_character_name(character_name: str) -> str:
        """
        キャラクター名検証
        
        Args:
            character_name: キャラクター名
            
        Returns:
            検証済みキャラクター名
            
        Raises:
            ValidationError: 検証失敗時
        """
        ALLOWED_CHARACTERS = ['ルミナ', 'クラリス', 'ノクス', 'Router']
        
        if not character_name:
            raise ValidationError(
                "キャラクター名が空です",
                field="character_name"
            )
        
        if character_name not in ALLOWED_CHARACTERS:
            raise ValidationError(
                f"不正なキャラクター名: {character_name}",
                field="character_name",
                error_code="E4007"
            )
        
        return character_name
    
    @staticmethod
    def validate_metadata(metadata: dict, max_keys: int = 50, max_value_length: int = 1000) -> dict:
        """
        メタデータ検証
        
        Args:
            metadata: メタデータ辞書
            max_keys: 最大キー数
            max_value_length: 値の最大長
            
        Returns:
            検証済みメタデータ
            
        Raises:
            ValidationError: 検証失敗時
        """
        if not isinstance(metadata, dict):
            raise ValidationError(
                "メタデータは辞書型である必要があります",
                field="metadata"
            )
        
        # キー数チェック
        if len(metadata) > max_keys:
            raise ValidationError(
                f"メタデータのキー数が多すぎます（最大{max_keys}個）",
                field="metadata",
                error_code="E4008"
            )
        
        # 各値の長さチェック
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > max_value_length:
                raise ValidationError(
                    f"メタデータ値が長すぎます: {key}（最大{max_value_length}文字）",
                    field="metadata",
                    error_code="E4009"
                )
        
        return metadata
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """
        HTML特殊文字をエスケープ（XSS対策）
        
        Args:
            text: エスケープ対象文字列
            
        Returns:
            エスケープ済み文字列
        """
        for char, escaped in InputValidator.XSS_ESCAPE_MAP.items():
            text = text.replace(char, escaped)
        return text
    
    @staticmethod
    def sanitize_for_log(text: str, max_length: int = 200) -> str:
        """
        ログ出力用サニタイゼーション（機密情報マスク）
        
        Args:
            text: ログ出力文字列
            max_length: 最大長
            
        Returns:
            サニタイズ済み文字列
        """
        # 長さ制限
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # 機密情報パターンマスク
        text = re.sub(r'(password|pwd)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
        text = re.sub(r'(api[_-]?key)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
        text = re.sub(r'(token|bearer)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
        
        return text


class CommandParser:
    """コマンドパーサー"""
    
    @staticmethod
    def parse(command: str) -> dict:
        """
        コマンド解析
        
        Args:
            command: コマンド文字列
            
        Returns:
            解析結果辞書
        """
        # 検証
        validated = InputValidator.validate_command(command)
        
        parts = validated.split()
        cmd_name = parts[0][1:]  # '/'を除去
        args = []
        kwargs = {}
        
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                kwargs[key] = value.strip("'\"")
            else:
                args.append(part)
        
        return {
            "command": cmd_name,
            "args": args,
            "kwargs": kwargs
        }
    
    @staticmethod
    def get_command_name(command: str) -> str:
        """
        コマンド名取得
        
        Args:
            command: コマンド文字列
            
        Returns:
            コマンド名
        """
        parts = command.split()
        return parts[0][1:] if parts and parts[0].startswith('/') else ""
    
    @staticmethod
    def get_command_args(command: str) -> list:
        """
        コマンド引数取得
        
        Args:
            command: コマンド文字列
            
        Returns:
            引数リスト
        """
        parts = command.split()[1:]
        return [p for p in parts if '=' not in p]
    
    @staticmethod
    def parse_command(input_text: str) -> tuple[str, list]:
        """
        コマンド解析（後方互換性用）
        
        Args:
            input_text: 入力文字列
            
        Returns:
            (コマンド名, 引数リスト)のタプル
        """
        if not input_text.startswith('/'):
            return ('', [])
        
        parts = input_text.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return (command, args)
    
    @staticmethod
    def is_command(input_text: str) -> bool:
        """
        コマンドかどうか判定
        
        Args:
            input_text: 入力文字列
            
        Returns:
            コマンドの場合True
        """
        return input_text.startswith('/')