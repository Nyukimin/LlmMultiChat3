"""
config.py
環境変数+YAML設定の統合管理（拡張性考慮）
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import yaml

# .envファイル読み込み
load_dotenv()


class SecurityConfig:
    """Phase 2で実装するが、Phase 1から構造定義"""
    
    def __init__(self):
        self.encryption_enabled = False  # Phase 1: OFF
        self.auth_enabled = False        # Phase 2: ON
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


class APIConfig:
    """Phase 3で実装するが、Phase 1から構造定義"""
    
    def __init__(self):
        self.enabled = False     # Phase 3: ON
        self.rate_limit_free = int(os.getenv("RATE_LIMIT_FREE", "100"))
        self.rate_limit_pro = int(os.getenv("RATE_LIMIT_PRO", "1000"))
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


class DatabaseConfig:
    """データベース設定"""
    
    def __init__(self):
        # PostgreSQL
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db = os.getenv("POSTGRES_DB", "llm_multi_chat")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        
        # Redis
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # Neo4j
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        
        # DuckDB
        self.duckdb_path = os.getenv("DUCKDB_PATH", "data/sessions.duckdb")
        
        # VectorDB（Pinecone）
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")


class ModelConfig:
    """LLMモデル設定"""
    
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        self.models = {
            "fast": os.getenv("DEFAULT_MODEL_FAST", "llama3-jp-8b"),
            "medium": os.getenv("DEFAULT_MODEL_MEDIUM", "amoral-gemma3:latest"),
            "search": os.getenv("DEFAULT_MODEL_SEARCH", "dsasai/llama3-elyza-jp-8b:latest")
        }
        
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")


class SystemConfig:
    """システム設定"""
    
    def __init__(self):
        self.max_turns = int(os.getenv("MAX_TURNS", "12"))
        self.max_conversation_duration_minutes = int(
            os.getenv("MAX_CONVERSATION_DURATION_MINUTES", "30")
        )
        self.enable_search = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
        self.enable_emotion_model = os.getenv("ENABLE_EMOTION_MODEL", "true").lower() == "true"
        self.enable_associative_memory = os.getenv("ENABLE_ASSOCIATIVE_MEMORY", "true").lower() == "true"
        self.enable_self_reflection = os.getenv("ENABLE_SELF_REFLECTION", "true").lower() == "true"
        
        # Web検索API
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")
        
        # ログ設定
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")


class Config:
    """環境変数+YAML設定の統合管理（拡張性考慮）"""
    
    def __init__(self, config_path: Optional[str] = None):
        # Phase 1: 基本設定
        self.model = ModelConfig()
        self.database = DatabaseConfig()
        self.system = SystemConfig()
        
        # Phase 2以降の拡張ポイント（初手から定義）
        self.security = SecurityConfig()  # Phase 2で実装
        self.api = APIConfig()             # Phase 3で実装
        self.plugins = []                  # Phase 3で実装
        
        # YAML設定の読み込み（オプション）
        if config_path and Path(config_path).exists():
            self.load_yaml(config_path)
    
    def load_yaml(self, path: str = "config.yaml"):
        """YAML設定の動的読み込み"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
                self._merge_config(yaml_config)
        except Exception as e:
            print(f"Warning: Could not load YAML config: {e}")
    
    def _merge_config(self, yaml_config: Dict[str, Any]):
        """YAML設定をマージ"""
        # 必要に応じてYAML設定で上書き
        if "ollama" in yaml_config:
            self.model.ollama_host = yaml_config["ollama"].get("host", self.model.ollama_host)
        
        if "system" in yaml_config:
            self.system.max_turns = yaml_config["system"].get("max_turns", self.system.max_turns)
    
    def validate_config(self) -> bool:
        """設定整合性チェック"""
        errors = []
        
        # Ollama接続先チェック
        if not self.model.ollama_host:
            errors.append("OLLAMA_HOST is not set")
        
        # 検索有効時のAPIキーチェック
        if self.system.enable_search and not self.system.serper_api_key:
            errors.append("ENABLE_SEARCH is true but SERPER_API_KEY is not set")
        
        # VectorDB設定チェック
        if not self.database.pinecone_api_key:
            print("Warning: PINECONE_API_KEY is not set. VectorDB features will be disabled.")
        
        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_ollama_url(self) -> str:
        """Ollama接続URL取得"""
        return self.model.ollama_host
    
    def get_model(self, model_type: str = "fast") -> str:
        """モデル名取得"""
        return self.model.models.get(model_type, self.model.models["fast"])


# グローバル設定インスタンス
config = Config()