"""
exceptions.py
カスタム例外クラス定義

LlmMultiChat3プロジェクト全体で使用する例外階層を定義。
各モジュールで適切な例外を発生させることで、エラーハンドリングを明確化。
"""


class LlmMultiChatError(Exception):
    """
    基底例外クラス
    
    LlmMultiChat3プロジェクト全体の例外の基底クラス。
    すべてのカスタム例外はこのクラスを継承する。
    """
    
    def __init__(self, message: str, error_code: str = "E0000"):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            error_code: エラーコード（デバッグ用）
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"


# ========================================
# 記憶システム関連例外
# ========================================

class MemoryError(LlmMultiChatError):
    """
    記憶システムエラー基底クラス
    
    5階層記憶システム全般のエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1000"):
        super().__init__(message, error_code)


class ShortTermMemoryError(MemoryError):
    """
    短期記憶エラー
    
    ConversationBuffer、キャッシュ操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1100"):
        super().__init__(message, error_code)


class MidTermMemoryError(MemoryError):
    """
    中期記憶エラー
    
    SessionManager、DuckDB、JSON操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1200"):
        super().__init__(message, error_code)


class LongTermMemoryError(MemoryError):
    """
    長期記憶エラー
    
    CharacterKPIManager、長期プロファイル操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1300"):
        super().__init__(message, error_code)


class KnowledgeBaseError(MemoryError):
    """
    知識ベースエラー
    
    KnowledgeBaseManager、検索・インデックス操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1400"):
        super().__init__(message, error_code)


class AssociativeMemoryError(MemoryError):
    """
    連想記憶エラー（Phase 2以降で使用）
    
    Neo4jグラフDB操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E1500"):
        super().__init__(message, error_code)


# ========================================
# LLMノード関連例外
# ========================================

class LLMNodeError(LlmMultiChatError):
    """
    LLMノードエラー
    
    LangGraphノード（ルミナ、クラリス、ノクス）での処理エラー。
    """
    
    def __init__(self, message: str, error_code: str = "E2000", node_name: str = ""):
        self.node_name = node_name
        super().__init__(message, error_code)
    
    def __str__(self):
        if self.node_name:
            return f"[{self.error_code}] {self.node_name}: {self.message}"
        return super().__str__()


class LLMInvocationError(LLMNodeError):
    """
    LLM呼び出しエラー
    
    Ollama等のLLM呼び出しに失敗した場合。
    """
    
    def __init__(self, message: str, error_code: str = "E2100", node_name: str = ""):
        super().__init__(message, error_code, node_name)


class LLMTimeoutError(LLMNodeError):
    """
    LLMタイムアウトエラー
    
    LLM応答がタイムアウトした場合。
    """
    
    def __init__(self, message: str, error_code: str = "E2200", node_name: str = ""):
        super().__init__(message, error_code, node_name)


# ========================================
# 設定・検証関連例外
# ========================================

class ConfigurationError(LlmMultiChatError):
    """
    設定エラー
    
    config.py、環境変数、初期化設定でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E3000"):
        super().__init__(message, error_code)


class ValidationError(LlmMultiChatError):
    """
    入力検証エラー
    
    ユーザー入力、コマンド、セッションIDの検証失敗。
    """
    
    def __init__(self, message: str, error_code: str = "E4000", field: str = ""):
        self.field = field
        super().__init__(message, error_code)
    
    def __str__(self):
        if self.field:
            return f"[{self.error_code}] {self.field}: {self.message}"
        return super().__str__()


# ========================================
# ファイルI/O関連例外
# ========================================

class FileOperationError(LlmMultiChatError):
    """
    ファイル操作エラー
    
    JSON/DuckDB/ログファイルの読み書きエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E5000", filepath: str = ""):
        self.filepath = filepath
        super().__init__(message, error_code)
    
    def __str__(self):
        if self.filepath:
            return f"[{self.error_code}] {self.filepath}: {self.message}"
        return super().__str__()


# ========================================
# データベース関連例外
# ========================================

class DatabaseError(LlmMultiChatError):
    """
    データベースエラー基底クラス
    
    DuckDB、Redis、Neo4j等のDB操作エラー。
    """
    
    def __init__(self, message: str, error_code: str = "E6000"):
        super().__init__(message, error_code)


class DuckDBError(DatabaseError):
    """
    DuckDBエラー
    
    中期記憶のDuckDB操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E6100"):
        super().__init__(message, error_code)


class RedisError(DatabaseError):
    """
    Redisエラー（Phase 2以降で使用）
    
    中期記憶キャッシュのRedis操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E6200"):
        super().__init__(message, error_code)


class Neo4jError(DatabaseError):
    """
    Neo4jエラー（Phase 2以降で使用）
    
    連想記憶のNeo4j操作でのエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E6300"):
        super().__init__(message, error_code)


# ========================================
# 認証・認可関連例外（Phase 3）
# ========================================

class AuthenticationError(LlmMultiChatError):
    """
    認証エラー基底クラス
    
    JWT、パスワード検証等の認証エラー。
    """
    
    def __init__(self, message: str, error_code: str = "E8000"):
        super().__init__(message, error_code)


class TokenExpiredError(AuthenticationError):
    """
    トークン期限切れエラー
    
    JWTアクセストークンまたはリフレッシュトークンの有効期限切れ。
    """
    
    def __init__(self, message: str, error_code: str = "E8100"):
        super().__init__(message, error_code)


class InvalidTokenError(AuthenticationError):
    """
    無効なトークンエラー
    
    JWT署名検証失敗、不正なトークンフォーマット。
    """
    
    def __init__(self, message: str, error_code: str = "E8200"):
        super().__init__(message, error_code)


class TokenGenerationError(AuthenticationError):
    """
    トークン生成エラー
    
    JWTトークン生成時のエラー。
    """
    
    def __init__(self, message: str, error_code: str = "E8300"):
        super().__init__(message, error_code)


class InvalidCredentialsError(AuthenticationError):
    """
    無効な認証情報エラー
    
    ログイン時のメールアドレス・パスワード不一致。
    """
    
    def __init__(self, message: str, error_code: str = "E8400"):
        super().__init__(message, error_code)


class UserAlreadyExistsError(AuthenticationError):
    """
    ユーザー既存エラー
    
    新規登録時のメールアドレス・ユーザー名重複。
    """
    
    def __init__(self, message: str, error_code: str = "E8500"):
        super().__init__(message, error_code)


class UserNotFoundError(AuthenticationError):
    """
    ユーザー未検出エラー
    
    指定されたユーザーIDまたはメールアドレスが存在しない。
    """
    
    def __init__(self, message: str, error_code: str = "E8600"):
        super().__init__(message, error_code)


class PasswordHashingError(AuthenticationError):
    """
    パスワードハッシュエラー
    
    bcryptハッシュ化処理の失敗。
    """
    
    def __init__(self, message: str, error_code: str = "E8700"):
        super().__init__(message, error_code)


class PasswordVerificationError(AuthenticationError):
    """
    パスワード検証エラー
    
    パスワード検証処理の失敗。
    """
    
    def __init__(self, message: str, error_code: str = "E8800"):
        super().__init__(message, error_code)


class InvalidPasswordError(AuthenticationError):
    """
    無効なパスワードエラー
    
    パスワード強度不足、フォーマット不正。
    """
    
    def __init__(self, message: str, error_code: str = "E8900"):
        super().__init__(message, error_code)


class AuthorizationError(LlmMultiChatError):
    """
    認可エラー
    
    ロールベースアクセス制御（RBAC）での権限不足。
    """
    
    def __init__(self, message: str, error_code: str = "E9000"):
        super().__init__(message, error_code)


class InsufficientPermissionsError(AuthorizationError):
    """
    権限不足エラー
    
    操作に必要な権限がない。
    """
    
    def __init__(self, message: str, error_code: str = "E9100", required_permission: str = ""):
        self.required_permission = required_permission
        super().__init__(message, error_code)
    
    def __str__(self):
        if self.required_permission:
            return f"[{self.error_code}] Required permission: {self.required_permission} - {self.message}"
        return super().__str__()


class InputValidationError(ValidationError):
    """
    入力検証エラー（Phase 3拡張）
    
    XSS、SQLインジェクション等のセキュリティ検証失敗。
    """
    
    def __init__(self, message: str, error_code: str = "E4100", field: str = ""):
        super().__init__(message, error_code, field)


# ========================================
# エクスポート・ユーティリティ関連例外
# ========================================

class ExportError(LlmMultiChatError):
    """
    エクスポートエラー
    
    会話履歴・メトリクスのエクスポート失敗。
    """
    
    def __init__(self, message: str, error_code: str = "E7000"):
        super().__init__(message, error_code)


# ========================================
# エラーコード一覧
# ========================================

ERROR_CODES = {
    # 基底・汎用エラー
    "E0000": "汎用エラー",
    
    # 記憶システムエラー (E1xxx)
    "E1000": "記憶システムエラー",
    "E1100": "短期記憶エラー",
    "E1200": "中期記憶エラー",
    "E1300": "長期記憶エラー",
    "E1400": "知識ベースエラー",
    "E1500": "連想記憶エラー",
    
    # LLMノードエラー (E2xxx)
    "E2000": "LLMノードエラー",
    "E2100": "LLM呼び出しエラー",
    "E2200": "LLMタイムアウトエラー",
    
    # 設定エラー (E3xxx)
    "E3000": "設定エラー",
    
    # 検証エラー (E4xxx)
    "E4000": "入力検証エラー",
    
    # ファイルI/Oエラー (E5xxx)
    "E5000": "ファイル操作エラー",
    
    # データベースエラー (E6xxx)
    "E6000": "データベースエラー",
    "E6100": "DuckDBエラー",
    "E6200": "Redisエラー",
    "E6300": "Neo4jエラー",
    
    # エクスポートエラー (E7xxx)
    "E7000": "エクスポートエラー",
    
    # 認証・認可エラー (E8xxx)
    "E8000": "認証エラー",
    "E8100": "トークン期限切れエラー",
    "E8200": "無効なトークンエラー",
    "E8300": "トークン生成エラー",
    "E8400": "無効な認証情報エラー",
    "E8500": "ユーザー既存エラー",
    "E8600": "ユーザー未検出エラー",
    "E8700": "パスワードハッシュエラー",
    "E8800": "パスワード検証エラー",
    "E8900": "無効なパスワードエラー",
    
    # 認可エラー (E9xxx)
    "E9000": "認可エラー",
    "E9100": "権限不足エラー"
}