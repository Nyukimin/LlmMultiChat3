# Phase 3実装計画書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 3 - API・プラグインエコシステム  
**期間**: Week 8-10  
**作成日**: 2025-11-13  
**Phase 1完了**: `f003dc5`  
**Phase 2完了**: `64a541f`

---

## 目次

1. [Phase 3概要](#1-phase-3概要)
2. [前提条件（Phase 1-2完了事項）](#2-前提条件phase-1-2完了事項)
3. [Week 8: JWT認証・認可システム](#3-week-8-jwt認証認可システム)
4. [Week 9: REST/WebSocket API](#4-week-9-restwebsocket-api)
5. [Week 10: プラグインエコシステム](#5-week-10-プラグインエコシステム)
6. [技術スタック](#6-技術スタック)
7. [デプロイ計画](#7-デプロイ計画)
8. [Phase 4以降の展望](#8-phase-4以降の展望)

---

## 1. Phase 3概要

### 1.1 目的

LlmMultiChat3をローカル環境から**本格的なAPI駆動型サービス**へ進化させ、外部アプリケーションからの利用を可能にします。

### 1.2 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **JWT認証・認可** | ユーザー登録・ログイン・トークン管理 | 🔴 High |
| **REST API** | CRUD操作・会話API・記憶API | 🔴 High |
| **WebSocket API** | リアルタイム通信・ストリーミング応答 | 🟡 Medium |
| **レート制限** | API呼び出し制限・Quota管理 | 🟡 Medium |
| **プラグインシステム** | 動的機能拡張・サードパーティ統合 | 🟢 Low |

### 1.3 Phase 3達成目標

✅ JWT認証完全実装（ユーザー登録・ログイン・トークン更新）  
✅ REST API 20エンドポイント公開  
✅ WebSocketリアルタイム通信  
✅ レート制限（10-100req/min）  
✅ プラグインマネージャー実装  
✅ Swagger/OpenAPI仕様書生成  
✅ Postman/Insomnia動作確認  
✅ セキュリティペネトレーションテスト実施

---

## 2. 前提条件（Phase 1-2完了事項）

### 2.1 Phase 1完了事項

✅ LangGraphコア実装  
✅ 3キャラクター（ルミナ・クラリス・ノクス）  
✅ 5階層記憶システム  
✅ パフォーマンスプロファイリング

**参照**: [`docks/Phase1_完了サマリー.md`](Phase1_完了サマリー.md:1)

### 2.2 Phase 2完了事項

✅ 18種類のカスタム例外クラス  
✅ 構造化ログ・メトリクス収集  
✅ Redis 2層キャッシュ  
✅ 入力検証（XSS/SQLインジェクション対策）  
✅ セキュリティ評価B+  
✅ パフォーマンス10倍高速化

**参照**: [`docks/Phase2_完了サマリー.md`](Phase2_完了サマリー.md:1)

### 2.3 Phase 3で活用する既存機能

| Phase 1-2機能 | Phase 3での活用 |
|--------------|----------------|
| カスタム例外 | API エラーレスポンス |
| 入力検証 | JWT検証・APIパラメータ検証 |
| メトリクス収集 | API呼び出し統計 |
| Redis キャッシュ | セッショントークン保存 |
| 構造化ログ | API監査ログ |

---

## 3. Week 8: JWT認証・認可システム

### 3.1 実装タスク

#### Week 8-1: JWT基盤実装（3日）

**ファイル作成**:
- `security/auth.py` (400行)
- `security/jwt_manager.py` (300行)
- `security/password_hasher.py` (150行)

**実装機能**:

1. **ユーザーモデル**
   ```python
   # security/models.py
   from pydantic import BaseModel, EmailStr
   from datetime import datetime
   
   class User(BaseModel):
       user_id: str
       username: str
       email: EmailStr
       password_hash: str
       roles: List[str] = ["user"]
       created_at: datetime
       last_login: Optional[datetime] = None
       is_active: bool = True
   ```

2. **JWT生成・検証**
   ```python
   # security/jwt_manager.py
   import jwt
   from datetime import datetime, timedelta
   
   class JWTManager:
       def __init__(self, secret_key: str, algorithm: str = "HS256"):
           self.secret_key = secret_key
           self.algorithm = algorithm
       
       def create_access_token(self, user_id: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
           payload = {
               "sub": user_id,
               "exp": datetime.utcnow() + expires_delta,
               "iat": datetime.utcnow(),
               "type": "access"
           }
           return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
       
       def create_refresh_token(self, user_id: str, expires_delta: timedelta = timedelta(days=30)) -> str:
           payload = {
               "sub": user_id,
               "exp": datetime.utcnow() + expires_delta,
               "iat": datetime.utcnow(),
               "type": "refresh"
           }
           return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
       
       def verify_token(self, token: str) -> dict:
           try:
               payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
               return payload
           except jwt.ExpiredSignatureError:
               raise TokenExpiredError("Token has expired")
           except jwt.InvalidTokenError:
               raise InvalidTokenError("Invalid token")
   ```

3. **パスワードハッシュ**
   ```python
   # security/password_hasher.py
   import bcrypt
   
   class PasswordHasher:
       @staticmethod
       def hash_password(password: str) -> str:
           salt = bcrypt.gensalt()
           return bcrypt.hashpw(password.encode(), salt).decode()
       
       @staticmethod
       def verify_password(password: str, password_hash: str) -> bool:
           return bcrypt.checkpw(password.encode(), password_hash.encode())
   ```

#### Week 8-2: ユーザー管理実装（3日）

**ファイル作成**:
- `security/user_manager.py` (500行)
- `security/role_manager.py` (200行)
- `db/users.db` (SQLite)

**実装機能**:

1. **ユーザー登録**
   ```python
   # security/user_manager.py
   class UserManager:
       def register_user(self, username: str, email: str, password: str) -> User:
           # 1. 重複チェック
           if self.user_exists(email):
               raise UserAlreadyExistsError(f"User with email {email} already exists")
           
           # 2. パスワードハッシュ
           password_hash = PasswordHasher.hash_password(password)
           
           # 3. ユーザー作成
           user = User(
               user_id=str(uuid4()),
               username=username,
               email=email,
               password_hash=password_hash,
               created_at=datetime.utcnow()
           )
           
           # 4. DB保存
           self.db.insert_user(user)
           
           return user
   ```

2. **ログイン**
   ```python
   def login(self, email: str, password: str) -> dict:
       # 1. ユーザー取得
       user = self.db.get_user_by_email(email)
       if not user:
           raise InvalidCredentialsError("Invalid email or password")
       
       # 2. パスワード検証
       if not PasswordHasher.verify_password(password, user.password_hash):
           raise InvalidCredentialsError("Invalid email or password")
       
       # 3. トークン生成
       access_token = self.jwt_manager.create_access_token(user.user_id)
       refresh_token = self.jwt_manager.create_refresh_token(user.user_id)
       
       # 4. Redisにトークン保存
       self.redis.setex(f"refresh_token:{user.user_id}", 2592000, refresh_token)
       
       # 5. 最終ログイン更新
       self.db.update_last_login(user.user_id)
       
       return {
           "access_token": access_token,
           "refresh_token": refresh_token,
           "token_type": "Bearer",
           "expires_in": 3600
       }
   ```

3. **ロールベースアクセス制御（RBAC）**
   ```python
   # security/role_manager.py
   class RoleManager:
       ROLES = {
           "admin": ["read", "write", "delete", "manage_users"],
           "user": ["read", "write"],
           "guest": ["read"]
       }
       
       def has_permission(self, user: User, permission: str) -> bool:
           for role in user.roles:
               if permission in self.ROLES.get(role, []):
                   return True
           return False
   ```

#### Week 8-3: 認証ミドルウェア（2日）

**ファイル作成**:
- `api/middleware/auth_middleware.py` (250行)
- `api/middleware/rate_limiter.py` (200行)

**実装機能**:

1. **認証ミドルウェア**
   ```python
   # api/middleware/auth_middleware.py
   from fastapi import Request, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   class AuthMiddleware:
       def __init__(self, jwt_manager: JWTManager):
           self.jwt_manager = jwt_manager
           self.security = HTTPBearer()
       
       async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> dict:
           token = credentials.credentials
           try:
               payload = self.jwt_manager.verify_token(token)
               return payload
           except TokenExpiredError:
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Token has expired"
               )
           except InvalidTokenError:
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid token"
               )
   ```

2. **レート制限ミドルウェア**
   ```python
   # api/middleware/rate_limiter.py
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @limiter.limit("10/minute")
   async def rate_limit_endpoint(request: Request):
       # エンドポイント処理
       pass
   ```

#### Week 8-4: テスト・ドキュメント（2日）

**テストファイル**:
- `tests/test_auth.py` (300行)
- `tests/test_jwt.py` (200行)
- `tests/test_rbac.py` (150行)

**ドキュメント**:
- `docks/認証仕様書.md` (400行)

**テストケース**（30件）:
- ユーザー登録（正常・異常系）
- ログイン（正常・異常系）
- トークン検証（正常・期限切れ・不正）
- トークン更新
- RBAC権限チェック
- パスワードリセット

---

## 4. Week 9: REST/WebSocket API

### 4.1 実装タスク

#### Week 9-1: FastAPI基盤構築（3日）

**ファイル作成**:
- `api/main.py` (400行)
- `api/routes/auth.py` (300行)
- `api/routes/chat.py` (400行)
- `api/routes/memory.py` (300行)
- `api/routes/metrics.py` (200行)

**実装機能**:

1. **FastAPIアプリケーション**
   ```python
   # api/main.py
   from fastapi import FastAPI, Request
   from fastapi.middleware.cors import CORSMiddleware
   from api.routes import auth, chat, memory, metrics
   from api.middleware.auth_middleware import AuthMiddleware
   
   app = FastAPI(
       title="LlmMultiChat3 API",
       version="3.0.0",
       description="永続的記憶を持つマルチLLM会話システム"
   )
   
   # CORS設定
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 本番環境では制限
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"]
   )
   
   # ルート登録
   app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
   app.include_router(chat.router, prefix="/api/v1/chat", tags=["会話"])
   app.include_router(memory.router, prefix="/api/v1/memory", tags=["記憶"])
   app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["メトリクス"])
   ```

2. **認証エンドポイント**
   ```python
   # api/routes/auth.py
   from fastapi import APIRouter, Depends, HTTPException
   
   router = APIRouter()
   
   @router.post("/register")
   async def register(user_data: UserRegistration):
       try:
           user = user_manager.register_user(
               username=user_data.username,
               email=user_data.email,
               password=user_data.password
           )
           return {"status": "success", "user_id": user.user_id}
       except UserAlreadyExistsError as e:
           raise HTTPException(status_code=400, detail=str(e))
   
   @router.post("/login")
   async def login(credentials: LoginCredentials):
       try:
           tokens = user_manager.login(
               email=credentials.email,
               password=credentials.password
           )
           return tokens
       except InvalidCredentialsError as e:
           raise HTTPException(status_code=401, detail=str(e))
   
   @router.post("/refresh")
   async def refresh_token(refresh_token: str):
       try:
           new_access_token = user_manager.refresh_access_token(refresh_token)
           return {"access_token": new_access_token, "token_type": "Bearer"}
       except TokenExpiredError as e:
           raise HTTPException(status_code=401, detail=str(e))
   ```

3. **会話エンドポイント**
   ```python
   # api/routes/chat.py
   @router.post("/")
   async def chat(
       request: ChatRequest,
       current_user: dict = Depends(auth_middleware.verify_token)
   ):
       try:
           # 入力検証
           validated_input = InputValidator.validate_user_input(request.user_input)
           
           # 会話処理
           response = chat_manager.chat(
               session_id=request.session_id,
               user_input=validated_input,
               user_id=current_user["sub"]
           )
           
           # メトリクス記録
           record_llm_call(
               node_name=response["metadata"]["llm_node"],
               duration=response["metadata"]["processing_time_ms"] / 1000,
               success=True
           )
           
           return response
       except InputValidationError as e:
           raise HTTPException(status_code=400, detail=str(e))
   
   @router.get("/history")
   async def get_history(
       session_id: str,
       limit: int = 50,
       current_user: dict = Depends(auth_middleware.verify_token)
   ):
       history = chat_manager.get_history(session_id, limit)
       return {"status": "success", "history": history}
   ```

#### Week 9-2: WebSocket API実装（3日）

**ファイル作成**:
- `api/websocket.py` (500行)
- `api/streaming.py` (300行)

**実装機能**:

1. **WebSocket接続**
   ```python
   # api/websocket.py
   from fastapi import WebSocket, WebSocketDisconnect
   
   class ConnectionManager:
       def __init__(self):
           self.active_connections: Dict[str, WebSocket] = {}
       
       async def connect(self, websocket: WebSocket, user_id: str):
           await websocket.accept()
           self.active_connections[user_id] = websocket
       
       def disconnect(self, user_id: str):
           del self.active_connections[user_id]
       
       async def send_message(self, user_id: str, message: dict):
           if user_id in self.active_connections:
               await self.active_connections[user_id].send_json(message)
   
   manager = ConnectionManager()
   
   @app.websocket("/ws/chat")
   async def websocket_endpoint(websocket: WebSocket):
       await manager.connect(websocket, user_id="guest")
       try:
           while True:
               data = await websocket.receive_json()
               
               # 認証チェック
               if data["type"] == "auth":
                   token = data["token"]
                   payload = jwt_manager.verify_token(token)
                   user_id = payload["sub"]
               
               # 会話処理
               elif data["type"] == "chat":
                   response = await process_chat_streaming(data["user_input"])
                   async for chunk in response:
                       await manager.send_message(user_id, {
                           "type": "chunk",
                           "content": chunk
                       })
       except WebSocketDisconnect:
           manager.disconnect(user_id)
   ```

2. **ストリーミング応答**
   ```python
   # api/streaming.py
   async def process_chat_streaming(user_input: str):
       response_generator = llm.stream(user_input)
       async for chunk in response_generator:
           yield chunk
   ```

#### Week 9-3: OpenAPI/Swagger（2日）

**自動生成**: FastAPIが自動生成  
**URL**: `http://localhost:8000/docs`

**カスタマイズ**:
```python
# api/main.py
app = FastAPI(
    title="LlmMultiChat3 API",
    version="3.0.0",
    description=open("docks/API仕様書_Phase2.md").read(),
    openapi_tags=[
        {"name": "認証", "description": "ユーザー認証・認可"},
        {"name": "会話", "description": "LLM会話API"},
        {"name": "記憶", "description": "記憶システムAPI"},
        {"name": "メトリクス", "description": "パフォーマンスメトリクス"}
    ]
)
```

#### Week 9-4: テスト・ドキュメント（2日）

**テストファイル**:
- `tests/test_api.py` (400行)
- `tests/test_websocket.py` (300行)

**ドキュメント**:
- `docks/API仕様書_Phase3.md` (800行)

**テストケース**（40件）:
- REST APIエンドポイント（20件）
- WebSocket接続・通信（10件）
- 認証フロー（5件）
- エラーハンドリング（5件）

---

## 5. Week 10: プラグインエコシステム

### 5.1 実装タスク

#### Week 10-1: プラグインマネージャー（3日）

**ファイル作成**:
- `core/plugin_manager.py` (600行)
- `plugins/base.py` (200行)
- `plugins/weather.py` (300行)
- `plugins/translate.py` (300行)

**実装機能**:

1. **プラグイン基底クラス**
   ```python
   # plugins/base.py
   from abc import ABC, abstractmethod
   
   class PluginInterface(ABC):
       def __init__(self, config: dict):
           self.config = config
           self.enabled = True
       
       @abstractmethod
       def on_message(self, message: str, context: dict) -> Optional[dict]:
           """メッセージ受信時のフック"""
           pass
       
       @abstractmethod
       def on_response(self, response: str, context: dict) -> str:
           """応答生成後のフック"""
           pass
       
       @property
       @abstractmethod
       def plugin_info(self) -> dict:
           """プラグイン情報"""
           return {
               "name": "plugin_name",
               "version": "1.0.0",
               "description": "Plugin description",
               "author": "Author name"
           }
   ```

2. **プラグインマネージャー**
   ```python
   # core/plugin_manager.py
   class PluginManager:
       def __init__(self):
           self.plugins: Dict[str, PluginInterface] = {}
           self.hooks: Dict[str, List[Callable]] = {
               "on_message": [],
               "on_response": [],
               "on_memory_store": []
           }
       
       def register_plugin(self, plugin: PluginInterface):
           plugin_name = plugin.plugin_info["name"]
           self.plugins[plugin_name] = plugin
           
           # フック登録
           for hook_name in self.hooks.keys():
               hook_method = getattr(plugin, hook_name, None)
               if hook_method:
                   self.hooks[hook_name].append(hook_method)
       
       def unregister_plugin(self, plugin_name: str):
           if plugin_name in self.plugins:
               plugin = self.plugins[plugin_name]
               
               # フック解除
               for hook_name, hook_list in self.hooks.items():
                   hook_method = getattr(plugin, hook_name, None)
                   if hook_method in hook_list:
                       hook_list.remove(hook_method)
               
               del self.plugins[plugin_name]
       
       async def trigger_hook(self, hook_name: str, *args, **kwargs):
           """全プラグインのフックを実行"""
           results = []
           for hook_method in self.hooks.get(hook_name, []):
               result = await hook_method(*args, **kwargs)
               if result is not None:
                   results.append(result)
           return results
       
       def load_plugins_from_directory(self, directory: str):
           """ディレクトリから自動ロード"""
           for file in os.listdir(directory):
               if file.endswith(".py") and file != "base.py":
                   module_name = file[:-3]
                   module = importlib.import_module(f"plugins.{module_name}")
                   plugin_class = getattr(module, f"{module_name.capitalize()}Plugin")
                   plugin = plugin_class(config={})
                   self.register_plugin(plugin)
   ```

3. **天気プラグイン例**
   ```python
   # plugins/weather.py
   import requests
   
   class WeatherPlugin(PluginInterface):
       def __init__(self, config: dict):
           super().__init__(config)
           self.api_key = config.get("openweather_api_key")
       
       @property
       def plugin_info(self) -> dict:
           return {
               "name": "weather",
               "version": "1.0.0",
               "description": "天気情報取得プラグイン",
               "author": "LlmMultiChat3 Team"
           }
       
       def on_message(self, message: str, context: dict) -> Optional[dict]:
           if "天気" in message or "weather" in message.lower():
               location = self._extract_location(message)
               weather_data = self._fetch_weather(location)
               return {
                   "action": "weather_info",
                   "data": weather_data
               }
           return None
       
       def on_response(self, response: str, context: dict) -> str:
           return response
       
       def _extract_location(self, message: str) -> str:
           # 簡易実装（Phase 4でNLP強化）
           return "Tokyo"
       
       def _fetch_weather(self, location: str) -> dict:
           url = f"https://api.openweathermap.org/data/2.5/weather"
           params = {"q": location, "appid": self.api_key, "units": "metric"}
           response = requests.get(url, params=params)
           return response.json()
   ```

#### Week 10-2: プラグイン統合テスト（2日）

**テストファイル**:
- `tests/test_plugins.py` (300行)

**テストケース**（15件）:
- プラグイン登録・解除
- フックトリガー
- 天気プラグイン動作確認
- 翻訳プラグイン動作確認
- エラーハンドリング

#### Week 10-3: Phase 3統合テスト（2日）

**テストファイル**:
- `tests/test_phase3_integration.py` (500行)

**テストケース**（50件）:
- JWT認証フロー
- REST API全エンドポイント
- WebSocket通信
- プラグインシステム
- レート制限

#### Week 10-4: ドキュメント整備（3日）

**ドキュメント**:
- `docks/Phase3_完了サマリー.md` (500行)
- `docks/プラグイン開発ガイド.md` (600行)
- `docks/API利用ガイド.md` (400行)

---

## 6. 技術スタック

### 6.1 新規追加（Phase 3）

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| Webフレームワーク | FastAPI 0.104.0 | REST/WebSocket API |
| 認証 | PyJWT 2.8.0 | JWT生成・検証 |
| パスワード | bcrypt 4.1.0 | パスワードハッシュ |
| レート制限 | slowapi 0.1.9 | API呼び出し制限 |
| CORS | fastapi.middleware | クロスオリジン対応 |
| OpenAPI | FastAPI自動生成 | API仕様書 |

### 6.2 既存継続（Phase 1-2）

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| LLM実行 | Ollama | ローカルLLM推論 |
| 状態管理 | LangGraph 1.0.3 | 会話フロー制御 |
| データベース | DuckDB | 中期記憶アーカイブ |
| キャッシュ | Redis 7.0.1 | 2層キャッシュ |
| ログ | Python logging | 構造化ログ |

---

## 7. デプロイ計画

### 7.1 開発環境

```bash
# 依存関係追加
pip install fastapi==0.104.0 pyjwt==2.8.0 bcrypt==4.1.0 slowapi==0.1.9 uvicorn==0.24.0

# 起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.2 本番環境（Docker）

**Dockerfile更新**:
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

**docker-compose.yml更新**:
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

## 8. Phase 4以降の展望

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

## 9. Phase 3成功基準

### 9.1 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| テスト成功率 | 100% | pytest |
| セキュリティ評価 | A- 以上 | OWASP Top 10 |
| API応答時間 | < 200ms | Locust負荷テスト |
| WebSocketレイテンシ | < 50ms | Ping-Pong測定 |
| JWT検証時間 | < 5ms | プロファイリング |

### 9.2 定性目標

✅ Postman/Insomnia動作確認完了  
✅ Swagger UI完全生成  
✅ プラグイン開発ガイド整備  
✅ セキュリティペネトレーションテスト実施  
✅ Phase 3完了サマリー作成

---

**Phase 3実装計画書 v1.0**  
**作成日**: 2025-11-13  
**ステータス**: ✅ レビュー待ち