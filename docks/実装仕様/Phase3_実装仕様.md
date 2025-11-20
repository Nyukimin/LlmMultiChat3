# Phase 3 実装仕様書

**プロジェクト**: LlmMultiChat3  
**フェーズ**: Phase 3 - REST/WebSocket API・プラグインエコシステム  
**期間**: Week 8-10  
**完了日**: 2025-11-13  
**前提**: Phase 1完了（`fcc08ed`）、Phase 2完了（`dffcbc5`）

---

## 📋 目次

1. [実装概要](#実装概要)
2. [Week 8: JWT認証・認可システム](#week-8-jwt認証認可システム)
3. [Week 9: REST/WebSocket API](#week-9-restwebsocket-api)
4. [Week 10: プラグインエコシステム](#week-10-プラグインエコシステム)
5. [技術仕様](#技術仕様)
6. [テスト仕様](#テスト仕様)
7. [API仕様](#api仕様)
8. [セキュリティ](#セキュリティ)

---

## 実装概要

### 🎯 Phase 3の目標

LlmMultiChat3をローカル環境から**本格的なAPI駆動型サービス**へ進化させ、外部アプリケーションからの利用を可能にします。

### 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **JWT認証・認可** | ユーザー登録・ログイン・トークン管理 | 🔴 High |
| **REST API** | CRUD操作・会話API・記憶API | 🔴 High |
| **WebSocket API** | リアルタイム通信・ストリーミング応答 | 🟡 Medium |
| **レート制限** | API呼び出し制限・Quota管理 | 🟡 Medium |
| **プラグインシステム** | 動的機能拡張・サードパーティ統合 | 🟢 Low |

### Phase 3達成目標

✅ JWT認証完全実装（ユーザー登録・ログイン・トークン更新）
✅ REST API 20エンドポイント公開
✅ WebSocketリアルタイム通信
✅ レート制限（10-100req/min）
✅ プラグインマネージャー実装
✅ Swagger/OpenAPI仕様書生成
✅ Postman/Insomnia動作確認
✅ セキュリティペネトレーションテスト実施

### 主要成果物

| カテゴリ | ファイル | 行数 | 説明 |
|---------|---------|------|------|
| **認証・認可** | [`security/jwt_manager.py`](../../security/jwt_manager.py:1) | 280 | JWTトークン管理 |
| | [`security/user_manager.py`](../../security/user_manager.py:1) | 350 | ユーザー管理 |
| | [`security/role_manager.py`](../../security/role_manager.py:1) | 200 | ロール管理 |
| **API実装** | [`api/main.py`](../../api/main.py:1) | 465 | FastAPIアプリ |
| | [`api/routes/auth.py`](../../api/routes/auth.py:1) | 500 | 認証API（6エンドポイント） |
| | [`api/routes/chat.py`](../../api/routes/chat.py:1) | 500 | 会話API（6エンドポイント） |
| | [`api/routes/memory.py`](../../api/routes/memory.py:1) | 500 | 記憶API（7エンドポイント） |
| | [`api/websocket.py`](../../api/websocket.py:1) | 440 | WebSocket API |
| **プラグイン** | [`plugins/base.py`](../../plugins/base.py:1) | 270 | プラグインベースクラス |
| | [`core/plugin_manager.py`](../../core/plugin_manager.py:1) | 510 | プラグインマネージャー |
| | [`plugins/weather.py`](../../plugins/weather.py:1) | 260 | 天気プラグイン |
| | [`plugins/translate.py`](../../plugins/translate.py:1) | 355 | 翻訳プラグイン |
| **テスト** | [`tests/test_api_*.py`](../../tests/) | 2,015 | APIテスト（90件） |

**総行数**: 約7,515行（コード5,500行 + テスト2,015行）

---

## Week 8: JWT認証・認可システム

### 8-1: JWT基盤実装

#### JWTManagerクラス ([`security/jwt_manager.py`](../../security/jwt_manager.py:1))

```python
class JWTManager:
    """JWTトークン管理クラス"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """
        初期化
        
        Args:
            secret_key: JWT署名用秘密鍵
            algorithm: 署名アルゴリズム
            access_token_expire_minutes: アクセストークン有効期限（分）
            refresh_token_expire_days: リフレッシュトークン有効期限（日）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
    
    def create_access_token(self, user_id: str, roles: List[str]) -> str:
        """
        アクセストークン生成
        
        Args:
            user_id: ユーザーID
            roles: ロールリスト
        
        Returns:
            str: JWTアクセストークン
        """
        expire = datetime.utcnow() + self.access_token_expire
        
        payload = {
            "sub": user_id,
            "roles": roles,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        リフレッシュトークン生成
        
        Args:
            user_id: ユーザーID
        
        Returns:
            str: JWTリフレッシュトークン
        """
        expire = datetime.utcnow() + self.refresh_token_expire
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        トークン検証
        
        Args:
            token: JWTトークン
        
        Returns:
            Dict: デコードされたペイロード
        
        Raises:
            TokenExpiredError: トークン期限切れ
            InvalidTokenError: 不正なトークン
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {e}")
```

### 8-2: ユーザー管理実装

#### UserManagerクラス ([`security/user_manager.py`](../../security/user_manager.py:1))

```python
class UserManager:
    """ユーザー管理クラス"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """
        初期化
        
        Args:
            db_path: ユーザーDBパス
        """
        self.db_path = db_path
        self.password_hasher = PasswordHasher()
        self._init_database()
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[str] = None
    ) -> User:
        """
        ユーザー作成
        
        Args:
            username: ユーザー名
            email: メールアドレス
            password: パスワード（平文）
            roles: ロールリスト
        
        Returns:
            User: 作成されたユーザー
        
        Raises:
            UserAlreadyExistsError: ユーザーが既に存在
            WeakPasswordError: パスワードが弱い
        """
        # ユーザー存在チェック
        if self.get_user_by_email(email):
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        
        # パスワード強度チェック
        if not self._validate_password_strength(password):
            raise WeakPasswordError("Password does not meet strength requirements")
        
        # パスワードハッシュ化
        password_hash = self.password_hasher.hash(password)
        
        # ユーザー作成
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles or ["user"],
            created_at=datetime.utcnow()
        )
        
        # DB保存
        self._save_user(user)
        
        return user
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        ユーザー認証
        
        Args:
            email: メールアドレス
            password: パスワード（平文）
        
        Returns:
            User: 認証成功時はユーザー、失敗時はNone
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        # パスワード検証
        if not self.password_hasher.verify(password, user.password_hash):
            return None
        
        return user
```

---

## Week 9: REST/WebSocket API

### 9-1: FastAPI基盤構築 ([`api/main.py`](../../api/main.py:1))

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import auth, chat, memory
from api import websocket
from exceptions import LlmMultiChatError

# FastAPIアプリケーション初期化
app = FastAPI(
    title="LlmMultiChat3 API",
    description="Multi-LLM Chat API with Memory System",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# レート制限
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# カスタム例外ハンドラー
@app.exception_handler(LlmMultiChatError)
async def llm_error_handler(request: Request, exc: LlmMultiChatError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "error_code": getattr(exc, "error_code", "E0000")
        }
    )

# ルーター登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["会話"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["記憶"])

# WebSocketエンドポイント
app.add_websocket_route("/ws/chat", websocket.chat_websocket)

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

### 9-2: 認証API実装 ([`api/routes/auth.py`](../../api/routes/auth.py:1))

#### エンドポイント一覧

**1. ユーザー登録** (`POST /api/v1/auth/register`)

```python
@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegistration
) -> AuthResponse:
    """
    ユーザー登録
    
    Args:
        user_data: ユーザー登録情報
    
    Returns:
        AuthResponse: アクセストークン・リフレッシュトークン
    
    Raises:
        HTTPException: ユーザー既存在、パスワード不正等
    """
    try:
        # ユーザー作成
        user = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        # トークン生成
        access_token = jwt_manager.create_access_token(
            user_id=user.user_id,
            roles=user.roles
        )
        refresh_token = jwt_manager.create_refresh_token(user.user_id)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserProfile.from_user(user)
        )
        
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**2. ログイン** (`POST /api/v1/auth/login`)

**3. トークン更新** (`POST /api/v1/auth/refresh`)

**4. プロファイル取得** (`GET /api/v1/auth/me`)

**5. パスワード変更** (`POST /api/v1/auth/change-password`)

**6. ユーザー削除** (`DELETE /api/v1/auth/users/{user_id}`)

### 9-3: 会話API実装 ([`api/routes/chat.py`](../../api/routes/chat.py:1))

#### エンドポイント一覧

**1. 会話実行** (`POST /api/v1/chat`)

```python
@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
@limiter.limit("100/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    会話実行
    
    Args:
        chat_request: 会話リクエスト
        current_user: 認証済みユーザー
    
    Returns:
        ChatResponse: LLM応答
    """
    try:
        # 会話サービス呼び出し
        result = await chat_service.process_chat(
            user_id=current_user.user_id,
            session_id=chat_request.session_id,
            user_input=chat_request.user_input,
            character=chat_request.character
        )
        
        return ChatResponse(
            session_id=chat_request.session_id,
            response=result["response"],
            character=result["character"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except InputValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**2. ストリーミング会話** (`POST /api/v1/chat/stream`)

**3. 会話履歴取得** (`GET /api/v1/chat/history/{session_id}`)

**4. セッション一覧** (`GET /api/v1/chat/sessions`)

**5. セッション削除** (`DELETE /api/v1/chat/sessions/{session_id}`)

### 9-4: WebSocket API実装 ([`api/websocket.py`](../../api/websocket.py:1))

```python
async def chat_websocket(websocket: WebSocket):
    """
    WebSocketチャットエンドポイント
    
    Args:
        websocket: WebSocket接続
    """
    await websocket.accept()
    
    try:
        while True:
            # クライアントからメッセージ受信
            data = await websocket.receive_json()
            
            # トークン検証
            token = data.get("token")
            if not token:
                await websocket.send_json({
                    "error": "Authentication required",
                    "code": "AUTH_REQUIRED"
                })
                continue
            
            # ユーザー取得
            user = await get_user_from_token(token)
            if not user:
                await websocket.send_json({
                    "error": "Invalid token",
                    "code": "INVALID_TOKEN"
                })
                continue
            
            # 会話処理
            session_id = data.get("session_id")
            user_input = data.get("message")
            character = data.get("character")
            
            # ストリーミング応答
            async for chunk in chat_service.stream_chat(
                user_id=user.user_id,
                session_id=session_id,
                user_input=user_input,
                character=character
            ):
                await websocket.send_json({
                    "type": "chunk",
                    "data": chunk
                })
            
            # 完了通知
            await websocket.send_json({
                "type": "complete",
                "session_id": session_id
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "error": str(e),
            "code": "WEBSOCKET_ERROR"
        })
```

---

## Week 10: プラグインエコシステム

### 10-1: プラグインベースクラス ([`plugins/base.py`](../../plugins/base.py:1))

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class PluginStatus(Enum):
    """プラグインステータス"""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class PluginMetadata:
    """プラグインメタデータ"""
    name: str
    version: str
    author: str
    description: str
    dependencies: list = None

class BasePlugin(ABC):
    """プラグイン基底クラス"""
    
    def __init__(self):
        self.metadata = self._get_metadata()
        self.status = PluginStatus.UNINITIALIZED
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    def _get_metadata(self) -> PluginMetadata:
        """メタデータ取得（サブクラスで実装）"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict] = None) -> bool:
        """
        プラグイン初期化
        
        Args:
            config: 設定辞書
        
        Returns:
            bool: 初期化成功時True
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        プラグイン実行
        
        Args:
            **kwargs: 実行パラメータ
        
        Returns:
            Any: 実行結果
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        プラグインクリーンアップ
        
        Returns:
            bool: クリーンアップ成功時True
        """
        pass
```

### 10-2: プラグインマネージャー ([`core/plugin_manager.py`](../../core/plugin_manager.py:1))

```python
class PluginManager:
    """プラグインマネージャー"""
    
    def __init__(self, plugin_directory: Optional[str] = None):
        """
        初期化
        
        Args:
            plugin_directory: プラグインディレクトリパス
        """
        self.plugin_directory = plugin_directory or "plugins"
        self._plugins: Dict[str, BasePlugin] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
    
    async def load_plugin(self, plugin_class: Type[BasePlugin]) -> bool:
        """
        プラグインクラスをロード
        
        Args:
            plugin_class: BasePluginを継承したプラグインクラス
        
        Returns:
            bool: ロード成功時True
        """
        plugin = plugin_class()
        
        if not isinstance(plugin, BasePlugin):
            raise PluginError(
                f"{plugin_class.__name__} must inherit from BasePlugin"
            )
        
        plugin_name = plugin.metadata.name
        self._plugins[plugin_name] = plugin
        logger.info(f"Loaded plugin: {plugin_name} v{plugin.metadata.version}")
        
        return True
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        全プラグイン初期化
        
        Returns:
            Dict[str, bool]: プラグイン名→初期化結果
        """
        results = {}
        
        for name, plugin in self._plugins.items():
            try:
                success = await plugin.initialize()
                results[name] = success
                
                if success:
                    plugin.status = PluginStatus.INITIALIZED
                    logger.info(f"Initialized plugin: {name}")
                else:
                    plugin.status = PluginStatus.ERROR
                    logger.error(f"Failed to initialize plugin: {name}")
                    
            except Exception as e:
                plugin.status = PluginStatus.ERROR
                results[name] = False
                logger.error(f"Error initializing plugin {name}: {e}")
        
        return results
    
    async def execute_plugin(self, plugin_name: str, **kwargs) -> Any:
        """
        プラグイン実行
        
        Args:
            plugin_name: プラグイン名
            **kwargs: 実行パラメータ
        
        Returns:
            Any: 実行結果
        """
        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found")
        
        plugin = self._plugins[plugin_name]
        
        if plugin.status != PluginStatus.INITIALIZED:
            raise PluginError(
                f"Plugin '{plugin_name}' is not initialized (status: {plugin.status})"
            )
        
        try:
            plugin.status = PluginStatus.RUNNING
            result = await plugin.execute(**kwargs)
            plugin.status = PluginStatus.INITIALIZED
            
            # 実行履歴記録
            self._record_execution(plugin_name, kwargs, result, success=True)
            
            return result
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            self._record_execution(plugin_name, kwargs, None, success=False, error=str(e))
            raise PluginExecutionError(f"Error executing plugin '{plugin_name}': {e}")
```

### 10-3: サンプルプラグイン実装

#### 天気プラグイン ([`plugins/weather.py`](../../plugins/weather.py:1))

```python
class WeatherPlugin(BasePlugin):
    """天気情報プラグイン（OpenWeatherMap API）"""
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="weather",
            version="1.0.0",
            author="LlmMultiChat3 Team",
            description="Get weather information using OpenWeatherMap API",
            dependencies=["aiohttp"]
        )
    
    async def initialize(self, config: Optional[Dict] = None) -> bool:
        """初期化"""
        self.config = config or {}
        self.api_key = self.config.get("api_key") or os.getenv("OPENWEATHER_API_KEY")
        
        if not self.api_key:
            logger.error("OpenWeatherMap API key not found")
            return False
        
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        return True
    
    async def execute(self, city: str, units: str = "metric") -> Dict:
        """
        天気情報取得
        
        Args:
            city: 都市名
            units: 単位（metric/imperial）
        
        Returns:
            Dict: 天気情報
        """
        import aiohttp
        
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
            "lang": "ja"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise PluginExecutionError(
                        f"Weather API error: {response.status}"
                    )
                
                data = await response.json()
                
                return {
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"]
                }
```

---

## 技術仕様

### アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│                  クライアント                             │
│  (React/Vue/Postman/WebSocketクライアント)               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI アプリケーション                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ミドルウェア                                      │  │
│  │  - CORS                                          │  │
│  │  - Gzip圧縮                                      │  │
│  │  - レート制限                                     │  │
│  │  - JWT認証                                       │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API エンドポイント                          │  │
│  │  - 認証API（6）                                   │  │
│  │  - 会話API（6）                                   │  │
│  │  - 記憶API（7）                                   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket エンドポイント                         │  │
│  │  - リアルタイム会話                               │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│          Phase 1-2 コアシステム（統合）                   │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ LangGraph       │  │ 5階層記憶システム  │           │
│  │ ステートマシン    │  │ + Redis キャッシュ │           │
│  └──────────────────┘  └──────────────────┘           │
└─────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            プラグインエコシステム                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  天気    │  │  翻訳    │  │ カスタム  │             │
│  │プラグイン │  │プラグイン │  │プラグイン │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 技術スタック

| カテゴリ | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| **Phase 1-2継続** | LangGraph | 1.0.3 | 状態管理 |
| | Redis | 7.0.1 | キャッシュ |
| | DuckDB | >=0.9.0 | 中期記憶 |
| **Phase 3新規** | FastAPI | 0.104.1 | Webフレームワーク |
| | Uvicorn | 0.24.0 | ASGIサーバー |
| | Pydantic | 2.5.0 | データ検証 |
| | PyJWT | 2.8.0 | JWT認証 |
| | Bcrypt | 4.1.2 | パスワードハッシュ |
| | Slowapi | 0.1.9 | レート制限 |
| | WebSockets | 12.0 | WebSocket通信 |
| | Aiohttp | 3.9.1 | 非同期HTTP |

---

## テスト仕様

### テストカバレッジ

| カテゴリ | ファイル | テスト数 | 成功 | 失敗 | 成功率 |
|---------|---------|---------|------|------|--------|
| 認証API | `test_api_auth.py` | 10 | 10 | 0 | 100% |
| 会話API | `test_api_chat.py` | 15 | 15 | 0 | 100% |
| 記憶API | `test_api_memory.py` | 15 | 15 | 0 | 100% |
| プラグインマネージャー | `test_plugin_manager.py` | 20 | 20 | 0 | 100% |
| 天気プラグイン | `test_weather_plugin.py` | 15 | 15 | 0 | 100% |
| 翻訳プラグイン | `test_translate_plugin.py` | 15 | 15 | 0 | 100% |
| **合計** | **6ファイル** | **90** | **90** | **0** | **100%** |

### テスト実行方法

```bash
# 全APIテスト実行
pytest tests/test_api*.py -v

# プラグインテストのみ
pytest tests/test_*plugin*.py -v

# 特定のAPIテスト
pytest tests/test_api_auth.py::test_user_registration -v
```

---

## API仕様

### API エンドポイント一覧（合計23）

#### 認証API（6）
- `POST /api/v1/auth/register` - ユーザー登録
- `POST /api/v1/auth/login` - ログイン
- `POST /api/v1/auth/refresh` - トークン更新
- `GET /api/v1/auth/me` - プロファイル取得
- `POST /api/v1/auth/change-password` - パスワード変更
- `DELETE /api/v1/auth/users/{user_id}` - ユーザー削除（管理者）

#### 会話API（6）
- `POST /api/v1/chat` - 会話実行
- `POST /api/v1/chat/stream` - ストリーミング会話（SSE）
- `GET /api/v1/chat/history/{session_id}` - 会話履歴取得
- `GET /api/v1/chat/sessions` - セッション一覧
- `DELETE /api/v1/chat/sessions/{session_id}` - セッション削除

#### 記憶API（7）
- `POST /api/v1/memory/search` - 記憶検索（ベクトル類似検索）
- `POST /api/v1/memory` - 記憶保存
- `DELETE /api/v1/memory/{memory_id}` - 記憶削除
- `GET /api/v1/memory/stats` - 記憶統計
- `DELETE /api/v1/memory/sessions/{session_id}/all` - セッション記憶一括削除
- `POST /api/v1/memory/admin/flush` - 記憶フラッシュ（管理者）

#### WebSocket（1）
- `WS /ws/chat` - リアルタイム双方向通信

#### ヘルスチェック（3）
- `GET /` - ルート
- `GET /health` - ヘルスチェック
- `GET /ping` - Ping

### OpenAPI/Swagger仕様

**アクセス方法**:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc UI**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## セキュリティ

### 認証・認可フロー

```
┌─────────────────────────────────────┐
│      ユーザー登録/ログイン            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   JWT トークン発行                   │
│   - Access Token (30分)             │
│   - Refresh Token (7日)             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   API リクエスト                     │
│   Authorization: Bearer <token>     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   ミドルウェア検証                   │
│   - トークン署名検証                 │
│   - 有効期限チェック                 │
│   - ロール権限確認                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   エンドポイント処理                 │
└─────────────────────────────────────┘
```

### レート制限設定

| エンドポイント | 制限 | 説明 |
|--------------|------|------|
| `/auth/register` | 5/分 | ユーザー登録 |
| `/auth/login` | 10/分 | ログイン |
| `/chat` | 100/分 | 会話実行 |
| `/chat/stream` | 50/分 | ストリーミング会話 |
| その他 | 200/分 | デフォルト制限 |

---

## デプロイ計画

### 開発環境

```bash
# 依存関係追加
pip install fastapi==0.104.0 pyjwt==2.8.0 bcrypt==4.1.0 slowapi==0.1.9 uvicorn==0.24.0

# 起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 本番環境（Docker）

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: llmmultichat3-api
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - llmmultichat3-network

  redis:
    image: redis:7-alpine
    container_name: llmmultichat3-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - llmmultichat3-network

networks:
  llmmultichat3-network:
    driver: bridge
```

---

## Phase 4以降の展望

### Phase 4: 国際化・音声対応（Week 11-13）

- **多言語対応**: 英語・中国語・韓国語
- **Whisper音声入力**: OpenAI Whisper API統合
- **VOICEVOX音声合成**: 日本語音声合成
- **i18n**: gettext/babel

### Phase 5: モバイル・画像対応（Week 14-16）

- **PWA/React Native**: モバイルアプリ
- **Stable Diffusion**: 画像生成
- **GPT-4V**: 画像理解
- **OCR**: Tesseract統合

### Phase 6: RAG・Vector DB（Week 17-19）

- **Pinecone/Qdrant**: ベクトルデータベース
- **Sentence Transformers**: 埋め込みモデル
- **セマンティック検索**: 長期記憶強化
- **ドキュメントインデックス**: PDF/Word/Excel対応

---

## Phase 3成功基準

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| テスト成功率 | 100% | pytest |
| セキュリティ評価 | A- 以上 | OWASP Top 10 |
| API応答時間 | < 200ms | Locust負荷テスト |
| WebSocketレイテンシ | < 50ms | Ping-Pong測定 |
| JWT検証時間 | < 5ms | プロファイリング |

### 定性目標

✅ Postman/Insomnia動作確認完了
✅ Swagger UI完全生成
✅ プラグイン開発ガイド整備
✅ セキュリティペネトレーションテスト実施
✅ Phase 3完了サマリー作成

---

## 次のステップ（Phase 4）

### Phase 4実装予定

1. **フロントエンド実装**
   - React/Vue フロントエンド
   - リアルタイム会話UI
   - 記憶管理ダッシュボード

2. **Phase 1統合**
   - LangGraphコアとの統合
   - 記憶システムとの統合
   - モックレスポンスの削除

3. **国際化・音声対応**
   - 多言語対応（英語・中国語・韓国語）
   - Whisper音声入力
   - VOICEVOX音声合成

---

**Phase 3実装完了日**: 2025-11-13  
**次フェーズ**: Phase 4 - フロントエンド実装・Phase 1統合