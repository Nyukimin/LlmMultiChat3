"""FastAPI Main Application.

LlmMultiChat3のREST/WebSocket APIメインアプリケーション。

Phase 3 Week 9-1:
- FastAPI基盤構築
- CORS設定
- ルーティング登録
- OpenAPI/Swagger設定
- 起動時初期化

使用例:
    >>> # 開発環境起動
    >>> uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
    >>> 
    >>> # 本番環境起動
    >>> gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import Config
from security.jwt_manager import JWTManager
from security.user_manager import UserManager
from security.role_manager import RoleManager
from api.middleware.auth_middleware import init_auth_middleware
from exceptions import (
    LLMMultiChatException,
    InputValidationError,
    RateLimitError,
    DatabaseError,
    LLMError
)

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# レート制限設定
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理.
    
    起動時と終了時の処理を定義します。
    
    Args:
        app: FastAPIアプリケーション
    
    Yields:
        None
    """
    # 起動時処理
    logger.info("Starting LlmMultiChat3 API...")
    
    # 設定読み込み
    config = Config()
    logger.info(f"Environment: {config.ENVIRONMENT}")
    
    # JWT/認証マネージャー初期化
    jwt_manager = JWTManager(
        secret_key=config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
        access_token_expire_minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    user_manager = UserManager(
        db_path=config.USER_DB_PATH,
        jwt_manager=jwt_manager
    )
    
    role_manager = RoleManager()
    
    # 認証ミドルウェア初期化
    init_auth_middleware(
        jwt_manager=jwt_manager,
        user_manager=user_manager,
        role_manager=role_manager
    )
    
    logger.info("Authentication middleware initialized")
    
    # グローバル状態にマネージャーを保存
    app.state.jwt_manager = jwt_manager
    app.state.user_manager = user_manager
    app.state.role_manager = role_manager
    app.state.config = config
    
    logger.info("LlmMultiChat3 API started successfully")
    
    yield
    
    # 終了時処理
    logger.info("Shutting down LlmMultiChat3 API...")
    
    # DB接続クローズ等のクリーンアップ
    if hasattr(user_manager, 'close'):
        user_manager.close()
    
    logger.info("LlmMultiChat3 API shut down successfully")


# FastAPIアプリケーション作成
app = FastAPI(
    title="LlmMultiChat3 API",
    version="3.0.0",
    description=(
        "**永続的記憶を持つマルチLLM会話システム**\n\n"
        "## 主要機能\n"
        "- 🔐 JWT認証・認可（ロールベースアクセス制御）\n"
        "- 💬 リアルタイム会話API（REST/WebSocket）\n"
        "- 🧠 5階層記憶システム（短期・中期・長期・連想・知識）\n"
        "- 🎭 3キャラクター（ルミナ・クラリス・ノクス）\n"
        "- 🔌 プラグインエコシステム\n"
        "- 📊 パフォーマンスメトリクス\n\n"
        "## 認証\n"
        "ほとんどのエンドポイントはJWT Bearer認証が必要です。\n"
        "1. `/api/v1/auth/register` でユーザー登録\n"
        "2. `/api/v1/auth/login` でアクセストークン取得\n"
        "3. リクエストヘッダーに `Authorization: Bearer <token>` を含める\n\n"
        "## レート制限\n"
        "- 認証済み: 100 req/min\n"
        "- 未認証: 10 req/min\n"
    ),
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    contact={
        "name": "LlmMultiChat3 Team",
        "url": "https://github.com/Nyukimin/LlmMultiChat3",
        "email": "support@llmmultichat3.example.com"
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ミドルウェア設定

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のドメインに制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)

# Gzip圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# レート制限
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# カスタム例外ハンドラー

@app.exception_handler(LLMMultiChatException)
async def llm_multichat_exception_handler(
    request: Request,
    exc: LLMMultiChatException
) -> JSONResponse:
    """LLMMultiChatカスタム例外ハンドラー.
    
    Args:
        request: リクエストオブジェクト
        exc: 例外インスタンス
    
    Returns:
        JSONResponse: エラーレスポンス
    """
    logger.warning(
        f"LLMMultiChatException: {exc.__class__.__name__} - {exc.message}",
        extra={"details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(InputValidationError)
async def input_validation_exception_handler(
    request: Request,
    exc: InputValidationError
) -> JSONResponse:
    """入力検証エラーハンドラー."""
    logger.warning(f"InputValidationError: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "type": "InputValidationError",
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(
    request: Request,
    exc: RateLimitError
) -> JSONResponse:
    """レート制限エラーハンドラー."""
    logger.warning(f"RateLimitError: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "type": "RateLimitError",
                "message": exc.message,
                "retry_after": exc.details.get("retry_after", 60)
            }
        },
        headers={"Retry-After": str(exc.details.get("retry_after", 60))}
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request: Request,
    exc: DatabaseError
) -> JSONResponse:
    """データベースエラーハンドラー."""
    logger.error(f"DatabaseError: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "type": "DatabaseError",
                "message": "Database service temporarily unavailable"
            }
        }
    )


@app.exception_handler(LLMError)
async def llm_exception_handler(
    request: Request,
    exc: LLMError
) -> JSONResponse:
    """LLMエラーハンドラー."""
    logger.error(f"LLMError: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "type": "LLMError",
                "message": "LLM service temporarily unavailable"
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """グローバル例外ハンドラー."""
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__} - {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred"
            }
        }
    )


# ルート登録
from api.routes import auth, chat, memory
from api.websocket import websocket_endpoint

app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["会話"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["記憶"])
# app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["メトリクス"])  # TODO: Phase 2統合時

# WebSocketエンドポイント
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket会話エンドポイント.
    
    Args:
        websocket: WebSocketインスタンス
    """
    await websocket_endpoint(
        websocket,
        jwt_manager=app.state.jwt_manager,
        user_manager=app.state.user_manager
    )


# ヘルスチェックエンドポイント

@app.get("/", tags=["ヘルスチェック"])
async def root() -> Dict[str, Any]:
    """ルートエンドポイント.
    
    Returns:
        dict: API情報
    """
    return {
        "name": "LlmMultiChat3 API",
        "version": "3.0.0",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health", tags=["ヘルスチェック"])
@limiter.limit("10/minute")
async def health_check(request: Request) -> Dict[str, Any]:
    """ヘルスチェックエンドポイント.
    
    Args:
        request: リクエストオブジェクト（レート制限用）
    
    Returns:
        dict: ヘルスステータス
    """
    return {
        "status": "healthy",
        "version": "3.0.0",
        "environment": app.state.config.ENVIRONMENT
    }


@app.get("/ping", tags=["ヘルスチェック"])
async def ping() -> Dict[str, str]:
    """Pingエンドポイント（レート制限なし）.
    
    Returns:
        dict: Pong応答
    """
    return {"message": "pong"}


# OpenAPIカスタマイズ

def custom_openapi():
    """OpenAPIスキーマをカスタマイズ."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="LlmMultiChat3 API",
        version="3.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # セキュリティスキーム追加
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer認証。`/api/v1/auth/login`で取得したアクセストークンを使用"
        }
    }
    
    # デフォルトセキュリティ設定
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # タグ説明追加
    openapi_schema["tags"] = [
        {
            "name": "ヘルスチェック",
            "description": "APIヘルスステータス確認"
        },
        {
            "name": "認証",
            "description": "ユーザー認証・認可（登録・ログイン・トークン管理）"
        },
        {
            "name": "会話",
            "description": "LLM会話API（テキスト/ストリーミング/WebSocket）"
        },
        {
            "name": "記憶",
            "description": "5階層記憶システムAPI（検索・保存・削除）"
        },
        {
            "name": "メトリクス",
            "description": "パフォーマンスメトリクス・統計情報"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# メイン実行

if __name__ == "__main__":
    import uvicorn
    
    # 環境変数から設定読み込み
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server at {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )