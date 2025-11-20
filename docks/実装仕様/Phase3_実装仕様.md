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
6. [テスト仕様（TDD実装）](#テスト仕様tdd実装)
   - [TDDアプローチ](#tddアプローチ)
   - [Week 8: JWT認証・認可システム - テスト仕様](#week-8-jwt認証認可システム---テスト仕様)
   - [Week 9: REST/WebSocket API - テスト仕様](#week-9-restwebsocket-api---テスト仕様)
   - [Week 10: プラグインエコシステム - テスト仕様](#week-10-プラグインエコシステム---テスト仕様)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [エラーハンドリング・エッジケース テスト仕様](#エラーハンドリングエッジケース-テスト仕様)
   - [テスト実行戦略](#テスト実行戦略)
   - [テスト品質基準](#テスト品質基準)
7. [API仕様](#api仕様)
8. [セキュリティ](#セキュリティ)

---

## 実装概要

### 🎯 Phase 3の目標

LlmMultiChat3をローカル環境から**本格的なAPI駆動型サービス**へ進化させ、外部アプリケーションからの利用を可能にします。

### 🔴 TDD実装アプローチ

Phase 3は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

1. **🔴 RED**: テストを書く（実装前、テストは失敗）
2. **🟢 GREEN**: 最小限の実装でテストを通す
3. **🔵 REFACTOR**: コードをリファクタリング（テストは常に成功）

**TDDの原則**:
- ✅ 実装前に必ずテストを書く
- ✅ 1つのテスト → 1つの実装 → リファクタリングのサイクル
- ✅ Given-When-Then形式でテストを記述
- ✅ 各テストは独立して実行可能
- ✅ 外部依存はモックで分離

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
| **テスト** | [`tests/test_*.py`](../../tests/) | 4,500 | TDDテスト（230件） |
| | `tests/test_jwt_manager.py` | 600 | JWTManagerテスト（25件） |
| | `tests/test_user_manager.py` | 500 | UserManagerテスト（20件） |
| | `tests/test_api_auth.py` | 800 | 認証APIテスト（30件） |
| | `tests/test_api_chat.py` | 700 | 会話APIテスト（25件） |
| | `tests/test_api_memory.py` | 700 | 記憶APIテスト（25件） |
| | `tests/test_websocket.py` | 400 | WebSocketテスト（15件） |
| | `tests/test_plugin_manager.py` | 900 | プラグインマネージャーテスト（30件） |
| | `tests/test_weather_plugin.py` | 500 | 天気プラグインテスト（20件） |
| | `tests/test_translate_plugin.py` | 500 | 翻訳プラグインテスト（20件） |
| | `tests/test_error_handling.py` | 300 | エラーハンドリングテスト（15件） |
| | `tests/conftest.py` | 200 | テストフィクスチャ |

**総行数**: 約10,000行（コード5,500行 + テスト4,500行）

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

## テスト仕様（TDD実装）

### TDDアプローチ

Phase 3は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

```
1. 🔴 RED: テストを書く（失敗する）
2. 🟢 GREEN: 最小限の実装でテストを通す
3. 🔵 REFACTOR: コードをリファクタリング（テストは常に成功）
```

### TDD実装の原則

1. **テストファースト**: 実装前に必ずテストを書く
2. **小さなステップ**: 1つのテスト → 1つの実装 → リファクタリング
3. **明確な意図**: Given-When-Then形式でテストを記述
4. **独立性**: 各テストは独立して実行可能
5. **モック活用**: 外部依存をモックで分離

### テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| JWT認証 | `test_jwt_manager.py` | 25 | 95%以上 | 🔴 High |
| ユーザー管理 | `test_user_manager.py` | 20 | 95%以上 | 🔴 High |
| 認証API | `test_api_auth.py` | 30 | 90%以上 | 🔴 High |
| 会話API | `test_api_chat.py` | 25 | 90%以上 | 🔴 High |
| 記憶API | `test_api_memory.py` | 25 | 90%以上 | 🔴 High |
| WebSocket | `test_websocket.py` | 15 | 85%以上 | 🟡 Medium |
| プラグインマネージャー | `test_plugin_manager.py` | 30 | 95%以上 | 🟡 Medium |
| 天気プラグイン | `test_weather_plugin.py` | 20 | 90%以上 | 🟢 Low |
| 翻訳プラグイン | `test_translate_plugin.py` | 20 | 90%以上 | 🟢 Low |
| **合計** | **9ファイル** | **230** | **平均90%以上** | - |

### テスト実行方法

#### 基本的なテスト実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付きテスト実行
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# 特定のカテゴリのみ
pytest tests/test_api*.py -v  # APIテストのみ
pytest tests/test_*plugin*.py -v  # プラグインテストのみ

# 特定のテストのみ
pytest tests/test_api_auth.py::test_user_registration_success -v

# マーカーで実行
pytest -m unit -v  # ユニットテストのみ
pytest -m integration -v  # 統合テストのみ
pytest -m "not slow" -v  # 遅いテストを除外
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_jwt_manager.py::test_create_access_token -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_jwt_manager.py::test_create_access_token -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_jwt_manager.py -v
# → 期待: 全テスト PASSED
```

---

## Week 8: JWT認証・認可システム - テスト仕様

### 8-1: JWTManager テスト仕様

#### テストファイル: `tests/test_jwt_manager.py`

**テストクラス**: `TestJWTManager`

#### テストケース一覧（25件）

**1. 初期化テスト（3件）**

```python
def test_jwt_manager_initialization():
    """
    Given: 秘密鍵とデフォルト設定
    When: JWTManagerを初期化
    Then: 正しい設定値が設定される
    """
    manager = JWTManager(secret_key="test_secret")
    assert manager.secret_key == "test_secret"
    assert manager.algorithm == "HS256"
    assert manager.access_token_expire == timedelta(minutes=30)
    assert manager.refresh_token_expire == timedelta(days=7)

def test_jwt_manager_custom_expiration():
    """
    Given: カスタム有効期限設定
    When: JWTManagerを初期化
    Then: カスタム設定値が適用される
    """
    manager = JWTManager(
        secret_key="test_secret",
        access_token_expire_minutes=60,
        refresh_token_expire_days=14
    )
    assert manager.access_token_expire == timedelta(minutes=60)
    assert manager.refresh_token_expire == timedelta(days=14)

def test_jwt_manager_custom_algorithm():
    """
    Given: カスタムアルゴリズム設定
    When: JWTManagerを初期化
    Then: カスタムアルゴリズムが適用される
    """
    manager = JWTManager(secret_key="test_secret", algorithm="HS512")
    assert manager.algorithm == "HS512"
```

**2. アクセストークン生成テスト（5件）**

```python
def test_create_access_token_success():
    """
    Given: ユーザーIDとロールリスト
    When: create_access_token()を呼び出す
    Then: 有効なJWTアクセストークンが生成される
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_access_token(
        user_id="user_123",
        roles=["user", "admin"]
    )
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # トークン検証
    payload = manager.verify_token(token)
    assert payload["sub"] == "user_123"
    assert payload["roles"] == ["user", "admin"]
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload

def test_create_access_token_with_empty_roles():
    """
    Given: 空のロールリスト
    When: create_access_token()を呼び出す
    Then: 空のロールリストでトークンが生成される
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_access_token(user_id="user_123", roles=[])
    
    payload = manager.verify_token(token)
    assert payload["roles"] == []

def test_create_access_token_expiration():
    """
    Given: アクセストークン生成
    When: トークンの有効期限を確認
    Then: 有効期限が30分後に設定されている
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_access_token(user_id="user_123", roles=["user"])
    
    payload = manager.verify_token(token)
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    assert (exp_time - iat_time).total_seconds() == 30 * 60

def test_create_access_token_different_users():
    """
    Given: 異なるユーザーID
    When: 複数のアクセストークンを生成
    Then: 各トークンに正しいユーザーIDが含まれる
    """
    manager = JWTManager(secret_key="test_secret")
    
    token1 = manager.create_access_token(user_id="user_1", roles=["user"])
    token2 = manager.create_access_token(user_id="user_2", roles=["user"])
    
    payload1 = manager.verify_token(token1)
    payload2 = manager.verify_token(token2)
    
    assert payload1["sub"] == "user_1"
    assert payload2["sub"] == "user_2"
    assert payload1["sub"] != payload2["sub"]

def test_create_access_token_invalid_user_id():
    """
    Given: 無効なユーザーID（空文字列）
    When: create_access_token()を呼び出す
    Then: ValueErrorが発生する
    """
    manager = JWTManager(secret_key="test_secret")
    
    with pytest.raises(ValueError):
        manager.create_access_token(user_id="", roles=["user"])
```

**3. リフレッシュトークン生成テスト（4件）**

```python
def test_create_refresh_token_success():
    """
    Given: ユーザーID
    When: create_refresh_token()を呼び出す
    Then: 有効なJWTリフレッシュトークンが生成される
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_refresh_token(user_id="user_123")
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    payload = manager.verify_token(token)
    assert payload["sub"] == "user_123"
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload

def test_refresh_token_expiration():
    """
    Given: リフレッシュトークン生成
    When: トークンの有効期限を確認
    Then: 有効期限が7日後に設定されている
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_refresh_token(user_id="user_123")
    
    payload = manager.verify_token(token)
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    assert (exp_time - iat_time).total_seconds() == 7 * 24 * 60 * 60

def test_refresh_token_no_roles():
    """
    Given: リフレッシュトークン生成
    When: トークンのペイロードを確認
    Then: ロール情報が含まれていない
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_refresh_token(user_id="user_123")
    
    payload = manager.verify_token(token)
    assert "roles" not in payload
```

**4. トークン検証テスト（8件）**

```python
def test_verify_token_success():
    """
    Given: 有効なJWTトークン
    When: verify_token()を呼び出す
    Then: デコードされたペイロードが返される
    """
    manager = JWTManager(secret_key="test_secret")
    token = manager.create_access_token(user_id="user_123", roles=["user"])
    
    payload = manager.verify_token(token)
    assert payload["sub"] == "user_123"
    assert payload["roles"] == ["user"]

def test_verify_token_expired():
    """
    Given: 期限切れのJWTトークン
    When: verify_token()を呼び出す
    Then: TokenExpiredErrorが発生する
    """
    manager = JWTManager(secret_key="test_secret", access_token_expire_minutes=-1)
    token = manager.create_access_token(user_id="user_123", roles=["user"])
    
    # 少し待機して期限切れにする
    import time
    time.sleep(2)
    
    with pytest.raises(TokenExpiredError):
        manager.verify_token(token)

def test_verify_token_invalid_signature():
    """
    Given: 異なる秘密鍵で署名されたトークン
    When: verify_token()を呼び出す
    Then: InvalidTokenErrorが発生する
    """
    manager1 = JWTManager(secret_key="secret1")
    manager2 = JWTManager(secret_key="secret2")
    
    token = manager1.create_access_token(user_id="user_123", roles=["user"])
    
    with pytest.raises(InvalidTokenError):
        manager2.verify_token(token)

def test_verify_token_malformed():
    """
    Given: 不正な形式のトークン
    When: verify_token()を呼び出す
    Then: InvalidTokenErrorが発生する
    """
    manager = JWTManager(secret_key="test_secret")
    
    with pytest.raises(InvalidTokenError):
        manager.verify_token("invalid.token.string")

def test_verify_token_empty_string():
    """
    Given: 空文字列のトークン
    When: verify_token()を呼び出す
    Then: InvalidTokenErrorが発生する
    """
    manager = JWTManager(secret_key="test_secret")
    
    with pytest.raises(InvalidTokenError):
        manager.verify_token("")

def test_verify_token_none():
    """
    Given: Noneのトークン
    When: verify_token()を呼び出す
    Then: InvalidTokenErrorが発生する
    """
    manager = JWTManager(secret_key="test_secret")
    
    with pytest.raises(InvalidTokenError):
        manager.verify_token(None)

def test_verify_token_access_vs_refresh():
    """
    Given: アクセストークンとリフレッシュトークン
    When: それぞれのトークンを検証
    Then: 正しいtypeが設定されている
    """
    manager = JWTManager(secret_key="test_secret")
    
    access_token = manager.create_access_token(user_id="user_123", roles=["user"])
    refresh_token = manager.create_refresh_token(user_id="user_123")
    
    access_payload = manager.verify_token(access_token)
    refresh_payload = manager.verify_token(refresh_token)
    
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
```

**5. エッジケース・統合テスト（5件）**

```python
def test_token_roundtrip():
    """
    Given: トークン生成と検証の往復
    When: トークンを生成して検証
    Then: 元の情報が正しく復元される
    """
    manager = JWTManager(secret_key="test_secret")
    
    user_id = "user_123"
    roles = ["user", "admin"]
    
    token = manager.create_access_token(user_id=user_id, roles=roles)
    payload = manager.verify_token(token)
    
    assert payload["sub"] == user_id
    assert payload["roles"] == roles

def test_multiple_tokens_independence():
    """
    Given: 複数のトークン生成
    When: 各トークンを検証
    Then: トークンは互いに独立している
    """
    manager = JWTManager(secret_key="test_secret")
    
    tokens = []
    for i in range(10):
        token = manager.create_access_token(user_id=f"user_{i}", roles=["user"])
        tokens.append(token)
    
    # 全てのトークンが異なる
    assert len(set(tokens)) == 10
    
    # 全てのトークンが検証可能
    for i, token in enumerate(tokens):
        payload = manager.verify_token(token)
        assert payload["sub"] == f"user_{i}"

@pytest.mark.parametrize("algorithm", ["HS256", "HS512"])
def test_different_algorithms(algorithm):
    """
    Given: 異なるアルゴリズム
    When: トークンを生成・検証
    Then: 正しく動作する
    """
    manager = JWTManager(secret_key="test_secret", algorithm=algorithm)
    token = manager.create_access_token(user_id="user_123", roles=["user"])
    payload = manager.verify_token(token)
    
    assert payload["sub"] == "user_123"
```

### 8-2: UserManager テスト仕様

#### テストファイル: `tests/test_user_manager.py`

**テストクラス**: `TestUserManager`

#### テストケース一覧（20件）

**1. 初期化テスト（2件）**

```python
def test_user_manager_initialization():
    """
    Given: データベースパス
    When: UserManagerを初期化
    Then: データベースが初期化される
    """
    manager = UserManager(db_path=":memory:")
    assert manager.db_path == ":memory:"
    assert manager.password_hasher is not None

def test_user_manager_default_db_path():
    """
    Given: デフォルト設定
    When: UserManagerを初期化
    Then: デフォルトパスが使用される
    """
    manager = UserManager()
    assert manager.db_path == "data/users.db"
```

**2. ユーザー作成テスト（6件）**

```python
def test_create_user_success():
    """
    Given: 有効なユーザー情報
    When: create_user()を呼び出す
    Then: ユーザーが作成される
    """
    manager = UserManager(db_path=":memory:")
    user = manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    assert user.username == "test_user"
    assert user.email == "test@example.com"
    assert user.user_id is not None
    assert user.password_hash != "SecurePass123!"  # ハッシュ化されている
    assert "user" in user.roles

def test_create_user_duplicate_email():
    """
    Given: 既存のメールアドレス
    When: create_user()を呼び出す
    Then: UserAlreadyExistsErrorが発生する
    """
    manager = UserManager(db_path=":memory:")
    manager.create_user(
        username="user1",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    with pytest.raises(UserAlreadyExistsError):
        manager.create_user(
            username="user2",
            email="test@example.com",
            password="SecurePass123!"
        )

def test_create_user_weak_password():
    """
    Given: 弱いパスワード
    When: create_user()を呼び出す
    Then: WeakPasswordErrorが発生する
    """
    manager = UserManager(db_path=":memory:")
    
    with pytest.raises(WeakPasswordError):
        manager.create_user(
            username="test_user",
            email="test@example.com",
            password="weak"  # 8文字未満
        )

def test_create_user_with_custom_roles():
    """
    Given: カスタムロール
    When: create_user()を呼び出す
    Then: カスタムロールが設定される
    """
    manager = UserManager(db_path=":memory:")
    user = manager.create_user(
        username="admin_user",
        email="admin@example.com",
        password="SecurePass123!",
        roles=["admin", "user"]
    )
    
    assert "admin" in user.roles
    assert "user" in user.roles

def test_create_user_password_hash():
    """
    Given: ユーザー作成
    When: パスワードハッシュを確認
    Then: パスワードがハッシュ化されている
    """
    manager = UserManager(db_path=":memory:")
    user = manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    assert user.password_hash != "SecurePass123!"
    assert len(user.password_hash) > 50  # bcrypt hash length

def test_create_user_timestamp():
    """
    Given: ユーザー作成
    When: 作成日時を確認
    Then: 現在時刻が設定されている
    """
    manager = UserManager(db_path=":memory:")
    before = datetime.utcnow()
    
    user = manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    after = datetime.utcnow()
    assert before <= user.created_at <= after
```

**3. 認証テスト（5件）**

```python
def test_authenticate_success():
    """
    Given: 登録済みユーザー
    When: authenticate()を正しいパスワードで呼び出す
    Then: ユーザーが返される
    """
    manager = UserManager(db_path=":memory:")
    manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    user = manager.authenticate("test@example.com", "SecurePass123!")
    assert user is not None
    assert user.email == "test@example.com"

def test_authenticate_wrong_password():
    """
    Given: 登録済みユーザー
    When: authenticate()を間違ったパスワードで呼び出す
    Then: Noneが返される
    """
    manager = UserManager(db_path=":memory:")
    manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    user = manager.authenticate("test@example.com", "WrongPassword")
    assert user is None

def test_authenticate_nonexistent_user():
    """
    Given: 存在しないユーザー
    When: authenticate()を呼び出す
    Then: Noneが返される
    """
    manager = UserManager(db_path=":memory:")
    
    user = manager.authenticate("nonexistent@example.com", "password")
    assert user is None

def test_authenticate_case_sensitive_email():
    """
    Given: 大文字小文字が異なるメールアドレス
    When: authenticate()を呼び出す
    Then: 認証が失敗する（メールは大文字小文字を区別）
    """
    manager = UserManager(db_path=":memory:")
    manager.create_user(
        username="test_user",
        email="Test@Example.com",
        password="SecurePass123!"
    )
    
    user = manager.authenticate("test@example.com", "SecurePass123!")
    assert user is None  # または実装に応じて成功
```

**4. ユーザー取得テスト（4件）**

```python
def test_get_user_by_email_success():
    """
    Given: 登録済みユーザー
    When: get_user_by_email()を呼び出す
    Then: ユーザーが返される
    """
    manager = UserManager(db_path=":memory:")
    created_user = manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    user = manager.get_user_by_email("test@example.com")
    assert user is not None
    assert user.email == created_user.email

def test_get_user_by_email_not_found():
    """
    Given: 存在しないメールアドレス
    When: get_user_by_email()を呼び出す
    Then: Noneが返される
    """
    manager = UserManager(db_path=":memory:")
    
    user = manager.get_user_by_email("nonexistent@example.com")
    assert user is None
```

**5. エッジケース・統合テスト（3件）**

```python
def test_user_lifecycle():
    """
    Given: ユーザーライフサイクル
    When: 作成→認証→取得の流れ
    Then: 全ての操作が成功する
    """
    manager = UserManager(db_path=":memory:")
    
    # 作成
    user = manager.create_user(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    # 認証
    authenticated = manager.authenticate("test@example.com", "SecurePass123!")
    assert authenticated.user_id == user.user_id
    
    # 取得
    retrieved = manager.get_user_by_email("test@example.com")
    assert retrieved.user_id == user.user_id
```

---

## Week 9: REST/WebSocket API - テスト仕様

### 9-1: 認証API テスト仕様

#### テストファイル: `tests/test_api_auth.py`

**テストクラス**: `TestAuthAPI`

#### テストケース一覧（30件）

**1. ユーザー登録API（6件）**

```python
def test_register_success(test_client, test_user_data):
    """
    Given: 有効なユーザー登録情報
    When: POST /api/v1/auth/register を呼び出す
    Then: 201 Created とトークンが返される
    """
    response = test_client.post("/api/v1/auth/register", json=test_user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user_data["email"]

def test_register_duplicate_email(test_client, test_user_data):
    """
    Given: 既存のメールアドレス
    When: POST /api/v1/auth/register を呼び出す
    Then: 400 Bad Request が返される
    """
    test_client.post("/api/v1/auth/register", json=test_user_data)
    
    response = test_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "error" in response.json()

def test_register_weak_password(test_client):
    """
    Given: 弱いパスワード
    When: POST /api/v1/auth/register を呼び出す
    Then: 422 Unprocessable Entity が返される
    """
    response = test_client.post("/api/v1/auth/register", json={
        "username": "test_user",
        "email": "test@example.com",
        "password": "weak"  # 8文字未満
    })
    assert response.status_code == 422

def test_register_invalid_email(test_client):
    """
    Given: 無効なメールアドレス
    When: POST /api/v1/auth/register を呼び出す
    Then: 422 Unprocessable Entity が返される
    """
    response = test_client.post("/api/v1/auth/register", json={
        "username": "test_user",
        "email": "invalid-email",
        "password": "SecurePass123!"
    })
    assert response.status_code == 422

def test_register_missing_fields(test_client):
    """
    Given: 必須フィールドが欠落
    When: POST /api/v1/auth/register を呼び出す
    Then: 422 Unprocessable Entity が返される
    """
    response = test_client.post("/api/v1/auth/register", json={
        "username": "test_user"
        # email, password が欠落
    })
    assert response.status_code == 422

def test_register_rate_limit(test_client, test_user_data):
    """
    Given: レート制限（5回/分）
    When: 6回連続で登録APIを呼び出す
    Then: 6回目で429 Too Many Requests が返される
    """
    for i in range(5):
        test_client.post("/api/v1/auth/register", json={
            **test_user_data,
            "email": f"test{i}@example.com"
        })
    
    response = test_client.post("/api/v1/auth/register", json={
        **test_user_data,
        "email": "test6@example.com"
    })
    assert response.status_code == 429
```

**2. ログインAPI（5件）**

```python
def test_login_success(test_client, registered_user):
    """
    Given: 登録済みユーザー
    When: POST /api/v1/auth/login を呼び出す
    Then: 200 OK とトークンが返される
    """
    response = test_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_wrong_password(test_client, registered_user):
    """
    Given: 登録済みユーザー
    When: 間違ったパスワードでログイン
    Then: 401 Unauthorized が返される
    """
    response = test_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_login_nonexistent_user(test_client):
    """
    Given: 存在しないユーザー
    When: POST /api/v1/auth/login を呼び出す
    Then: 401 Unauthorized が返される
    """
    response = test_client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password"
    })
    assert response.status_code == 401
```

**3. トークン更新API（4件）**

```python
def test_refresh_token_success(test_client, registered_user):
    """
    Given: 有効なリフレッシュトークン
    When: POST /api/v1/auth/refresh を呼び出す
    Then: 200 OK と新しいトークンが返される
    """
    login_response = test_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    refresh_token = login_response.json()["refresh_token"]
    
    response = test_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_refresh_token_expired(test_client):
    """
    Given: 期限切れのリフレッシュトークン
    When: POST /api/v1/auth/refresh を呼び出す
    Then: 401 Unauthorized が返される
    """
    # 期限切れトークンの生成（モック使用）
    # ...
```

**4. プロファイル取得API（3件）**

```python
def test_get_profile_success(test_client, auth_headers):
    """
    Given: 認証済みユーザー
    When: GET /api/v1/auth/me を呼び出す
    Then: 200 OK とユーザープロファイルが返される
    """
    response = test_client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "username" in data

def test_get_profile_unauthorized(test_client):
    """
    Given: 未認証リクエスト
    When: GET /api/v1/auth/me を呼び出す
    Then: 401 Unauthorized が返される
    """
    response = test_client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_get_profile_invalid_token(test_client):
    """
    Given: 無効なトークン
    When: GET /api/v1/auth/me を呼び出す
    Then: 401 Unauthorized が返される
    """
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

**5. パスワード変更API（4件）**

```python
def test_change_password_success(test_client, auth_headers):
    """
    Given: 認証済みユーザー
    When: POST /api/v1/auth/change-password を呼び出す
    Then: 200 OK が返される
    """
    response = test_client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "SecurePass123!",
            "new_password": "NewSecurePass123!"
        }
    )
    assert response.status_code == 200

def test_change_password_wrong_old_password(test_client, auth_headers):
    """
    Given: 間違った現在のパスワード
    When: POST /api/v1/auth/change-password を呼び出す
    Then: 400 Bad Request が返される
    """
    response = test_client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "WrongPassword",
            "new_password": "NewSecurePass123!"
        }
    )
    assert response.status_code == 400
```

**6. ユーザー削除API（3件）**

```python
def test_delete_user_admin_success(test_client, admin_headers, test_user_id):
    """
    Given: 管理者権限
    When: DELETE /api/v1/auth/users/{user_id} を呼び出す
    Then: 200 OK が返される
    """
    response = test_client.delete(
        f"/api/v1/auth/users/{test_user_id}",
        headers=admin_headers
    )
    assert response.status_code == 200

def test_delete_user_non_admin(test_client, auth_headers, test_user_id):
    """
    Given: 一般ユーザー権限
    When: DELETE /api/v1/auth/users/{user_id} を呼び出す
    Then: 403 Forbidden が返される
    """
    response = test_client.delete(
        f"/api/v1/auth/users/{test_user_id}",
        headers=auth_headers
    )
    assert response.status_code == 403
```

**7. エッジケース・統合テスト（5件）**

```python
def test_auth_flow_integration(test_client, test_user_data):
    """
    Given: 認証フロー全体
    When: 登録→ログイン→プロファイル取得→ログアウト
    Then: 全ての操作が成功する
    """
    # 登録
    register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
    assert register_response.status_code == 201
    
    # ログイン
    login_response = test_client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    
    # プロファイル取得
    token = login_response.json()["access_token"]
    profile_response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
```

### 9-2: 会話API テスト仕様

#### テストファイル: `tests/test_api_chat.py`

**テストクラス**: `TestChatAPI`

#### テストケース一覧（25件）

**1. 会話実行API（6件）**

```python
def test_chat_success(test_client, auth_headers):
    """
    Given: 認証済みユーザーと会話リクエスト
    When: POST /api/v1/chat を呼び出す
    Then: 200 OK とLLM応答が返される
    """
    response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "test_session",
            "user_input": "こんにちは",
            "character": "lumina"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert "character" in data

def test_chat_unauthorized(test_client):
    """
    Given: 未認証リクエスト
    When: POST /api/v1/chat を呼び出す
    Then: 401 Unauthorized が返される
    """
    response = test_client.post("/api/v1/chat", json={
        "session_id": "test_session",
        "user_input": "こんにちは"
    })
    assert response.status_code == 401

def test_chat_invalid_input(test_client, auth_headers):
    """
    Given: 無効な入力（空文字列）
    When: POST /api/v1/chat を呼び出す
    Then: 400 Bad Request が返される
    """
    response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "test_session",
            "user_input": "",  # 空文字列
            "character": "lumina"
        }
    )
    assert response.status_code == 400

def test_chat_invalid_character(test_client, auth_headers):
    """
    Given: 無効なキャラクター名
    When: POST /api/v1/chat を呼び出す
    Then: 400 Bad Request が返される
    """
    response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "test_session",
            "user_input": "こんにちは",
            "character": "invalid_character"
        }
    )
    assert response.status_code == 400

def test_chat_rate_limit(test_client, auth_headers):
    """
    Given: レート制限（100回/分）
    When: 101回連続で会話APIを呼び出す
    Then: 101回目で429 Too Many Requests が返される
    """
    # モックでレート制限をテスト
    # ...
```

**2. ストリーミング会話API（4件）**

```python
def test_chat_stream_success(test_client, auth_headers):
    """
    Given: 認証済みユーザー
    When: POST /api/v1/chat/stream を呼び出す
    Then: 200 OK とストリーミング応答が返される
    """
    response = test_client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={
            "session_id": "test_session",
            "user_input": "こんにちは",
            "character": "lumina"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    # ストリーミングデータの検証
```

**3. 会話履歴取得API（4件）**

```python
def test_get_history_success(test_client, auth_headers, test_session_id):
    """
    Given: 認証済みユーザーとセッションID
    When: GET /api/v1/chat/history/{session_id} を呼び出す
    Then: 200 OK と会話履歴が返される
    """
    response = test_client.get(
        f"/api/v1/chat/history/{test_session_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)

def test_get_history_not_found(test_client, auth_headers):
    """
    Given: 存在しないセッションID
    When: GET /api/v1/chat/history/{session_id} を呼び出す
    Then: 404 Not Found が返される
    """
    response = test_client.get(
        "/api/v1/chat/history/nonexistent_session",
        headers=auth_headers
    )
    assert response.status_code == 404
```

**4. セッション管理API（6件）**

```python
def test_list_sessions_success(test_client, auth_headers):
    """
    Given: 認証済みユーザー
    When: GET /api/v1/chat/sessions を呼び出す
    Then: 200 OK とセッション一覧が返される
    """
    response = test_client.get("/api/v1/chat/sessions", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)

def test_delete_session_success(test_client, auth_headers, test_session_id):
    """
    Given: 認証済みユーザーとセッションID
    When: DELETE /api/v1/chat/sessions/{session_id} を呼び出す
    Then: 200 OK が返される
    """
    response = test_client.delete(
        f"/api/v1/chat/sessions/{test_session_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
```

**5. エッジケース・統合テスト（5件）**

```python
def test_chat_flow_integration(test_client, auth_headers):
    """
    Given: 会話フロー全体
    When: 会話実行→履歴取得→セッション削除
    Then: 全ての操作が成功する
    """
    # 会話実行
    chat_response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "integration_test",
            "user_input": "こんにちは",
            "character": "lumina"
        }
    )
    assert chat_response.status_code == 200
    
    # 履歴取得
    history_response = test_client.get(
        "/api/v1/chat/history/integration_test",
        headers=auth_headers
    )
    assert history_response.status_code == 200
    
    # セッション削除
    delete_response = test_client.delete(
        "/api/v1/chat/sessions/integration_test",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
```

### 9-3: WebSocket API テスト仕様

#### テストファイル: `tests/test_websocket.py`

**テストクラス**: `TestWebSocketAPI`

#### テストケース一覧（15件）

```python
def test_websocket_connection_success(test_client, auth_token):
    """
    Given: 有効な認証トークン
    When: WebSocket接続を確立
    Then: 接続が成功する
    """
    with test_client.websocket_connect(f"/ws/chat?token={auth_token}") as websocket:
        assert websocket is not None

def test_websocket_authentication_required(test_client):
    """
    Given: トークンなし
    When: WebSocket接続を試みる
    Then: 接続が拒否される
    """
    with pytest.raises(Exception):  # WebSocket接続エラー
        test_client.websocket_connect("/ws/chat")

def test_websocket_chat_message(test_client, auth_token):
    """
    Given: WebSocket接続
    When: チャットメッセージを送信
    Then: ストリーミング応答が受信される
    """
    with test_client.websocket_connect(f"/ws/chat?token={auth_token}") as websocket:
        websocket.send_json({
            "session_id": "test_session",
            "message": "こんにちは",
            "character": "lumina"
        })
        
        # ストリーミング応答を受信
        response = websocket.receive_json()
        assert response["type"] == "chunk" or response["type"] == "complete"
```

---

## Week 10: プラグインエコシステム - テスト仕様

### 10-1: プラグインマネージャー テスト仕様

#### テストファイル: `tests/test_plugin_manager.py`

**テストクラス**: `TestPluginManager`

#### テストケース一覧（30件）

**1. プラグインロードテスト（6件）**

```python
def test_load_plugin_success(plugin_manager, mock_plugin_class):
    """
    Given: 有効なプラグインクラス
    When: load_plugin()を呼び出す
    Then: プラグインがロードされる
    """
    result = await plugin_manager.load_plugin(mock_plugin_class)
    assert result is True
    assert "mock_plugin" in plugin_manager._plugins

def test_load_plugin_invalid_class(plugin_manager):
    """
    Given: BasePluginを継承していないクラス
    When: load_plugin()を呼び出す
    Then: PluginErrorが発生する
    """
    class InvalidPlugin:
        pass
    
    with pytest.raises(PluginError):
        await plugin_manager.load_plugin(InvalidPlugin)

def test_load_plugin_duplicate(plugin_manager, mock_plugin_class):
    """
    Given: 既にロード済みのプラグイン
    When: 同じプラグインを再度ロード
    Then: PluginErrorが発生する（または上書きされる）
    """
    await plugin_manager.load_plugin(mock_plugin_class)
    
    # 実装に応じてエラーまたは上書き
    with pytest.raises(PluginError):
        await plugin_manager.load_plugin(mock_plugin_class)
```

**2. プラグイン初期化テスト（6件）**

```python
def test_initialize_all_success(plugin_manager, mock_plugin_class):
    """
    Given: ロード済みプラグイン
    When: initialize_all()を呼び出す
    Then: 全プラグインが初期化される
    """
    await plugin_manager.load_plugin(mock_plugin_class)
    results = await plugin_manager.initialize_all()
    
    assert results["mock_plugin"] is True
    assert plugin_manager._plugins["mock_plugin"].status == PluginStatus.INITIALIZED

def test_initialize_all_partial_failure(plugin_manager, failing_plugin_class):
    """
    Given: 初期化に失敗するプラグイン
    When: initialize_all()を呼び出す
    Then: 失敗したプラグインはエラー状態になる
    """
    await plugin_manager.load_plugin(failing_plugin_class)
    results = await plugin_manager.initialize_all()
    
    assert results["failing_plugin"] is False
    assert plugin_manager._plugins["failing_plugin"].status == PluginStatus.ERROR
```

**3. プラグイン実行テスト（8件）**

```python
def test_execute_plugin_success(plugin_manager, initialized_plugin):
    """
    Given: 初期化済みプラグイン
    When: execute_plugin()を呼び出す
    Then: プラグインが実行され、結果が返される
    """
    result = await plugin_manager.execute_plugin(
        "mock_plugin",
        param1="value1",
        param2="value2"
    )
    
    assert result is not None
    assert result["result"] == "success"

def test_execute_plugin_not_found(plugin_manager):
    """
    Given: 存在しないプラグイン名
    When: execute_plugin()を呼び出す
    Then: PluginErrorが発生する
    """
    with pytest.raises(PluginError):
        await plugin_manager.execute_plugin("nonexistent_plugin")

def test_execute_plugin_not_initialized(plugin_manager, mock_plugin_class):
    """
    Given: 初期化されていないプラグイン
    When: execute_plugin()を呼び出す
    Then: PluginErrorが発生する
    """
    await plugin_manager.load_plugin(mock_plugin_class)
    # 初期化しない
    
    with pytest.raises(PluginError):
        await plugin_manager.execute_plugin("mock_plugin")
```

**4. エラーハンドリングテスト（6件）**

```python
def test_plugin_execution_error(plugin_manager, error_plugin_class):
    """
    Given: 実行時にエラーを発生するプラグイン
    When: execute_plugin()を呼び出す
    Then: PluginExecutionErrorが発生する
    """
    await plugin_manager.load_plugin(error_plugin_class)
    await plugin_manager.initialize_all()
    
    with pytest.raises(PluginExecutionError):
        await plugin_manager.execute_plugin("error_plugin")
```

**5. 統合テスト（4件）**

```python
def test_plugin_lifecycle(plugin_manager, mock_plugin_class):
    """
    Given: プラグインライフサイクル
    When: ロード→初期化→実行→クリーンアップ
    Then: 全ての操作が成功する
    """
    # ロード
    await plugin_manager.load_plugin(mock_plugin_class)
    
    # 初期化
    await plugin_manager.initialize_all()
    
    # 実行
    result = await plugin_manager.execute_plugin("mock_plugin")
    assert result is not None
    
    # クリーンアップ
    await plugin_manager._plugins["mock_plugin"].cleanup()
```

### 10-2: 天気プラグイン テスト仕様

#### テストファイル: `tests/test_weather_plugin.py`

**テストクラス**: `TestWeatherPlugin`

#### テストケース一覧（20件）

```python
def test_weather_plugin_initialization_success(weather_plugin, mock_api_key):
    """
    Given: 有効なAPIキー
    When: initialize()を呼び出す
    Then: 初期化が成功する
    """
    result = await weather_plugin.initialize({"api_key": mock_api_key})
    assert result is True
    assert weather_plugin.status == PluginStatus.INITIALIZED

def test_weather_plugin_initialization_no_api_key(weather_plugin):
    """
    Given: APIキーなし
    When: initialize()を呼び出す
    Then: 初期化が失敗する
    """
    result = await weather_plugin.initialize()
    assert result is False

@patch('aiohttp.ClientSession.get')
def test_weather_plugin_execute_success(mock_get, weather_plugin, mock_weather_response):
    """
    Given: 初期化済みプラグインと都市名
    When: execute()を呼び出す
    Then: 天気情報が返される
    """
    mock_get.return_value.__aenter__.return_value.json.return_value = mock_weather_response
    mock_get.return_value.__aenter__.return_value.status = 200
    
    await weather_plugin.initialize({"api_key": "test_key"})
    result = await weather_plugin.execute(city="Tokyo")
    
    assert result["city"] == "Tokyo"
    assert "temperature" in result
    assert "description" in result

def test_weather_plugin_execute_api_error(weather_plugin):
    """
    Given: APIエラー
    When: execute()を呼び出す
    Then: PluginExecutionErrorが発生する
    """
    # モックでAPIエラーをシミュレート
    # ...
```

---

## テストフィクスチャ仕様

### conftest.py の拡張

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os

from api.main import app
from security.jwt_manager import JWTManager
from security.user_manager import UserManager
from core.plugin_manager import PluginManager

# ===== FastAPIテストクライアント =====

@pytest.fixture
def test_client():
    """FastAPIテストクライアント"""
    return TestClient(app)

# ===== JWT認証フィクスチャ =====

@pytest.fixture
def jwt_manager():
    """JWTManagerインスタンス"""
    return JWTManager(secret_key="test_secret_key_for_testing")

@pytest.fixture
def auth_token(jwt_manager):
    """テスト用認証トークン"""
    return jwt_manager.create_access_token(
        user_id="test_user_123",
        roles=["user"]
    )

@pytest.fixture
def auth_headers(auth_token):
    """認証ヘッダー"""
    return {"Authorization": f"Bearer {auth_token}"}

# ===== ユーザー管理フィクスチャ =====

@pytest.fixture
def user_manager():
    """UserManagerインスタンス（メモリDB）"""
    return UserManager(db_path=":memory:")

@pytest.fixture
def test_user_data():
    """テストユーザーデータ"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }

@pytest.fixture
def registered_user(user_manager, test_user_data):
    """登録済みユーザー"""
    return user_manager.create_user(**test_user_data)

# ===== プラグインフィクスチャ =====

@pytest.fixture
def plugin_manager():
    """PluginManagerインスタンス"""
    return PluginManager(plugin_directory=tempfile.mkdtemp())

@pytest.fixture
def mock_plugin_class():
    """モックプラグインクラス"""
    from plugins.base import BasePlugin, PluginMetadata
    
    class MockPlugin(BasePlugin):
        def _get_metadata(self):
            return PluginMetadata(
                name="mock_plugin",
                version="1.0.0",
                author="Test",
                description="Mock plugin for testing"
            )
        
        async def initialize(self, config=None):
            return True
        
        async def execute(self, **kwargs):
            return {"result": "success", "params": kwargs}
        
        async def cleanup(self):
            return True
    
    return MockPlugin

# ===== モック・スタブフィクスチャ =====

@pytest.fixture
def mock_chat_service():
    """ChatServiceのモック"""
    mock = AsyncMock()
    mock.process_chat = AsyncMock(return_value={
        "response": "モック応答",
        "character": "lumina",
        "timestamp": "2025-01-01T00:00:00"
    })
    return mock

@pytest.fixture
def mock_memory_service():
    """MemoryServiceのモック"""
    mock = AsyncMock()
    mock.search_memory = AsyncMock(return_value=[])
    mock.store_memory = AsyncMock(return_value={"memory_id": "mem_001"})
    return mock
```

---

## エラーハンドリング・エッジケース テスト仕様

### エラーハンドリングテスト（15件）

```python
# tests/test_error_handling.py

def test_invalid_json_request(test_client):
    """
    Given: 不正なJSONリクエスト
    When: APIエンドポイントを呼び出す
    Then: 400 Bad Request が返される
    """
    response = test_client.post(
        "/api/v1/auth/register",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400

def test_missing_required_fields(test_client):
    """
    Given: 必須フィールドが欠落
    When: APIエンドポイントを呼び出す
    Then: 422 Unprocessable Entity が返される
    """
    response = test_client.post(
        "/api/v1/auth/register",
        json={"username": "test"}  # email, password が欠落
    )
    assert response.status_code == 422

def test_sql_injection_attempt(test_client, auth_headers):
    """
    Given: SQLインジェクション攻撃
    When: APIエンドポイントを呼び出す
    Then: 400 Bad Request が返される（サニタイズされる）
    """
    response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "'; DROP TABLE users; --",
            "user_input": "test",
            "character": "lumina"
        }
    )
    # SQLインジェクションはサニタイズされる
    assert response.status_code in [400, 200]  # 実装に応じて

def test_xss_attempt(test_client, auth_headers):
    """
    Given: XSS攻撃
    When: APIエンドポイントを呼び出す
    Then: 400 Bad Request が返される（サニタイズされる）
    """
    response = test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "session_id": "test_session",
            "user_input": "<script>alert('XSS')</script>",
            "character": "lumina"
        }
    )
    # XSSはサニタイズされる
    assert response.status_code in [400, 200]  # 実装に応じて
```

---

## テスト実行戦略

### TDD実装順序

1. **Week 8: JWT認証・認可**
   - 1日目: JWTManagerテスト（25件）→ 実装
   - 2日目: UserManagerテスト（20件）→ 実装
   - 3日目: 認証APIテスト（30件）→ 実装
   - 4日目: 統合テスト・リファクタリング

2. **Week 9: REST/WebSocket API**
   - 1-2日目: 会話APIテスト（25件）→ 実装
   - 3日目: 記憶APIテスト（25件）→ 実装
   - 4日目: WebSocketテスト（15件）→ 実装
   - 5日目: 統合テスト・リファクタリング

3. **Week 10: プラグインエコシステム**
   - 1-2日目: プラグインマネージャーテスト（30件）→ 実装
   - 3日目: 天気プラグインテスト（20件）→ 実装
   - 4日目: 翻訳プラグインテスト（20件）→ 実装
   - 5日目: 統合テスト・リファクタリング

### テスト実行コマンド

```bash
# TDDサイクル（1つのテスト）
pytest tests/test_jwt_manager.py::test_create_access_token_success -v

# カテゴリ別テスト
pytest tests/test_jwt_manager.py -v  # JWTManager全テスト
pytest tests/test_api_auth.py -v  # 認証API全テスト

# カバレッジ測定
pytest tests/ --cov=security --cov=api --cov-report=html

# 全テスト実行
pytest tests/ -v --tb=short
```

---

## テスト品質基準

### 必須要件

- ✅ **テスト成功率**: 100%（全テストが成功）
- ✅ **コードカバレッジ**: 90%以上
- ✅ **テスト実行時間**: 全テスト5分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存はモックで分離

### 品質指標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| テスト成功率 | 100% | pytest |
| コードカバレッジ | 90%以上 | pytest-cov |
| テスト実行時間 | < 5分 | pytest --durations |
| テスト独立性 | 100% | テストの並列実行 |
| モック使用率 | 外部依存100% | コードレビュー |

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

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全230件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: 全テスト5分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存は100%モックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | pytest（全230件） |
| **コードカバレッジ** | **90%以上** | pytest-cov |
| **テスト実行時間** | **< 5分** | pytest --durations |
| セキュリティ評価 | A- 以上 | OWASP Top 10 |
| API応答時間 | < 200ms | Locust負荷テスト |
| WebSocketレイテンシ | < 50ms | Ping-Pong測定 |
| JWT検証時間 | < 5ms | プロファイリング |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全230件のテストケースが定義されている
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