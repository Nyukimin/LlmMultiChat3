# 会話履歴: API・MCP・自律サーチ機能追加

**作成日**: 2025-11-12  
**対象バージョン**: 3.1.0（Phase 1拡張）  
**担当**: LUMINA SYSTEM DESIGN TEAM

---

## 📋 背景と目的

### ユーザーからのフィードバック
> "このシステムにAPIつけるの忘れてた。最終的にはMCPに転用したい。あと、外部サーチも実装して、自律で情報収集できるようにしたい"

### 現状の問題点
1. **API設計不足**: セクション20.7で基本エンドポイントのみ記載、実装詳細なし
2. **MCP未対応**: 仕様書に記載なし、外部システムとの標準化された連携不可
3. **自律性の欠如**: 知識ベースは手動/定期更新のみ、自律的な情報収集なし

---

## 🎯 追加する3つの機能

### 1️⃣ REST/WebSocket API 完全設計 🌐
### 2️⃣ MCP (Model Context Protocol) 対応 🔌
### 3️⃣ 自律的外部サーチ・情報収集エージェント 🤖

---

# 1️⃣ REST/WebSocket API 完全設計

## 1.1 概要

**目的**: 外部アプリケーションが会話LLMシステムを利用できるようにするためのRESTful API + WebSocket APIを提供。

**技術スタック**:
- **FastAPI**: Python 3.10+ 高速Webフレームワーク
- **Pydantic**: データバリデーション
- **WebSocket**: リアルタイム双方向通信
- **JWT**: 認証・認可
- **Redis**: レート制限・セッション管理

---

## 1.2 API設計

### 1.2.1 エンドポイント一覧

```python
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="会話LLM API", version="3.1.0")
security = HTTPBearer()

# ========================================
# 1. 認証エンドポイント
# ========================================

class UserRole(str, Enum):
    FREE = "free"
    PRO = "pro"
    ADMIN = "admin"

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1時間
    user_id: str
    role: UserRole

@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["認証"])
async def login(request: LoginRequest):
    """
    ユーザーログイン
    
    - **username**: ユーザー名
    - **password**: パスワード
    
    Returns:
        JWT Access Token
    """
    # TODO: DB認証実装
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # JWT生成
    token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(hours=1)
    )
    
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        role=user.role
    )

@app.post("/api/v1/auth/refresh", tags=["認証"])
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """リフレッシュトークン発行"""
    # TODO: トークンリフレッシュ実装
    pass

# ========================================
# 2. 会話エンドポイント
# ========================================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: Optional[str] = None
    character: Optional[str] = None  # "lumina", "clarisse", "nox", "all"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    stream: bool = False

class ChatResponse(BaseModel):
    message_id: str
    thread_id: str
    character: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["会話"])
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    メッセージ送信（同期）
    
    - **message**: ユーザーメッセージ
    - **thread_id**: スレッドID（継続会話の場合）
    - **character**: 指名キャラクター（省略時は自動選択）
    - **temperature**: 応答のランダム性（0.0-2.0）
    - **max_tokens**: 最大トークン数
    - **stream**: ストリーミング応答（WebSocketを推奨）
    """
    user_id = verify_token(credentials.credentials)
    
    # レート制限チェック
    check_rate_limit(user_id)
    
    # LangGraph実行
    response = await execute_conversation(
        user_id=user_id,
        message=request.message,
        thread_id=request.thread_id,
        character=request.character,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    return ChatResponse(
        message_id=response["message_id"],
        thread_id=response["thread_id"],
        character=response["character"],
        content=response["content"],
        timestamp=datetime.utcnow(),
        metadata=response.get("metadata", {})
    )

# ========================================
# 3. WebSocket（ストリーミング会話）
# ========================================

@app.websocket("/api/v1/stream")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocketストリーミング会話
    
    Protocol:
    1. Client → Server: {"type": "auth", "token": "JWT"}
    2. Server → Client: {"type": "auth_success", "user_id": "xxx"}
    3. Client → Server: {"type": "message", "content": "こんにちは"}
    4. Server → Client (streaming): {"type": "chunk", "content": "こ"}
    5. Server → Client (streaming): {"type": "chunk", "content": "ん"}
    6. Server → Client: {"type": "done", "message_id": "xxx"}
    """
    await websocket.accept()
    
    try:
        # 認証
        auth_data = await websocket.receive_json()
        if auth_data.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "Authentication required"})
            await websocket.close()
            return
        
        user_id = verify_token(auth_data["token"])
        await websocket.send_json({"type": "auth_success", "user_id": user_id})
        
        # 会話ループ
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # ストリーミング応答
                async for chunk in stream_conversation(
                    user_id=user_id,
                    message=data["content"],
                    thread_id=data.get("thread_id"),
                    character=data.get("character")
                ):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk["text"],
                        "character": chunk["character"]
                    })
                
                # 完了通知
                await websocket.send_json({
                    "type": "done",
                    "message_id": chunk["message_id"],
                    "thread_id": chunk["thread_id"]
                })
    
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()

# ========================================
# 4. 記憶エンドポイント
# ========================================

class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    MID_TERM = "mid_term"
    LONG_TERM = "long_term"
    ASSOCIATIVE = "associative"
    KNOWLEDGE_BASE = "knowledge_base"

class Memory(BaseModel):
    id: str
    type: MemoryType
    content: str
    summary: Optional[str] = None
    keywords: List[str] = []
    timestamp: datetime
    importance: float = Field(..., ge=0.0, le=1.0)

class MemorySearchRequest(BaseModel):
    query: str
    memory_types: List[MemoryType] = [MemoryType.LONG_TERM]
    limit: int = Field(10, ge=1, le=100)

class MemorySearchResponse(BaseModel):
    memories: List[Memory]
    total: int

@app.post("/api/v1/memories/search", response_model=MemorySearchResponse, tags=["記憶"])
async def search_memories(
    request: MemorySearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    記憶検索
    
    - **query**: 検索クエリ
    - **memory_types**: 検索対象の記憶タイプ
    - **limit**: 最大件数
    """
    user_id = verify_token(credentials.credentials)
    
    # VectorDB検索
    results = await search_vector_db(
        user_id=user_id,
        query=request.query,
        memory_types=request.memory_types,
        limit=request.limit
    )
    
    return MemorySearchResponse(
        memories=[Memory(**m) for m in results],
        total=len(results)
    )

@app.delete("/api/v1/memories/{memory_id}", tags=["記憶"])
async def delete_memory(
    memory_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """記憶削除（GDPR対応）"""
    user_id = verify_token(credentials.credentials)
    
    # TODO: VectorDB + PostgreSQL削除
    await delete_from_vector_db(user_id, memory_id)
    await delete_from_meta_db(user_id, memory_id)
    
    return {"status": "deleted", "memory_id": memory_id}

# ========================================
# 5. キャラクターエンドポイント
# ========================================

class Character(BaseModel):
    id: str
    name: str
    role: str
    personality: str
    model: str
    temperature: float
    tools: List[str]
    priority_kb: List[str]
    growth_enabled: bool
    level: int = 1
    kpi: Dict[str, int] = {}

class CharacterListResponse(BaseModel):
    characters: List[Character]

@app.get("/api/v1/characters", response_model=CharacterListResponse, tags=["キャラクター"])
async def list_characters(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """キャラクター一覧"""
    user_id = verify_token(credentials.credentials)
    
    # personas/*.yaml読み込み
    characters = load_all_characters()
    
    return CharacterListResponse(characters=characters)

@app.post("/api/v1/characters", response_model=Character, tags=["キャラクター"])
async def create_character(
    character: Character,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """カスタムキャラクター追加"""
    user_id = verify_token(credentials.credentials)
    
    # RBAC: Admin only
    user_role = get_user_role(user_id)
    if user_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    
    # personas/custom_{id}.yamlに保存
    save_character_config(character)
    
    return character

# ========================================
# 6. データポータビリティ
# ========================================

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"

@app.post("/api/v1/export", tags=["データポータビリティ"])
async def export_data(
    format: ExportFormat = ExportFormat.JSON,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    会話履歴エクスポート（GDPR対応）
    
    - **format**: エクスポート形式（JSON/CSV/Markdown）
    """
    user_id = verify_token(credentials.credentials)
    
    # 全記憶取得
    memories = await get_all_memories(user_id)
    conversations = await get_all_conversations(user_id)
    
    # フォーマット変換
    if format == ExportFormat.JSON:
        data = {"memories": memories, "conversations": conversations}
        return {"download_url": f"/download/{user_id}.json"}
    # TODO: CSV, Markdown対応
    
    return {"status": "export_started", "format": format}

# ========================================
# 7. ヘルスチェック・メトリクス
# ========================================

@app.get("/api/v1/health", tags=["システム"])
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "3.1.0",
        "timestamp": datetime.utcnow()
    }

@app.get("/api/v1/metrics", tags=["システム"])
async def get_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """メトリクス取得（Admin only）"""
    user_id = verify_token(credentials.credentials)
    user_role = get_user_role(user_id)
    
    if user_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    
    # TODO: Prometheusメトリクス取得
    return {
        "total_users": 100,
        "active_sessions": 25,
        "total_messages": 10000,
        "avg_response_time_ms": 1200
    }
```

---

## 1.3 エラーハンドリング

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# カスタムエラー
class RateLimitExceeded(APIError):
    def __init__(self):
        super().__init__(429, "Rate limit exceeded. Try again later.")

class InvalidToken(APIError):
    def __init__(self):
        super().__init__(401, "Invalid or expired token.")
```

---

## 1.4 レート制限

```python
import redis
from datetime import datetime, timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def check_rate_limit(user_id: str):
    """
    レート制限チェック
    
    - Free: 100リクエスト/分
    - Pro: 1000リクエスト/分
    """
    user_role = get_user_role(user_id)
    limit = 100 if user_role == UserRole.FREE else 1000
    
    key = f"rate_limit:{user_id}"
    current = redis_client.get(key)
    
    if current is None:
        redis_client.setex(key, 60, 1)
    else:
        count = int(current)
        if count >= limit:
            raise RateLimitExceeded()
        redis_client.incr(key)
```

---

## 1.5 CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

# 2️⃣ MCP (Model Context Protocol) 対応

## 2.1 MCP概要

**Model Context Protocol (MCP)**: Anthropicが提唱する、AIモデルと外部ツール・データソース間の標準化された通信プロトコル。

**利点**:
- 標準化されたインターフェース
- ツールの動的追加
- セキュアな外部連携
- Claude Desktopなど既存エコシステムとの統合

---

## 2.2 MCP Server実装

```python
# mcp_server.py
from mcp.server import Server, Tool, Resource
from mcp.types import TextContent, ImageContent
from typing import Any, Sequence

class LlmMultiChatMCPServer(Server):
    """
    会話LLMシステムをMCP Serverとして公開
    """
    
    def __init__(self):
        super().__init__(name="llm-multi-chat-server")
        self.register_tools()
        self.register_resources()
    
    def register_tools(self):
        """ツール登録"""
        
        @self.tool()
        async def chat_with_character(
            character: str,
            message: str,
            thread_id: str | None = None
        ) -> str:
            """
            特定キャラクターと会話
            
            Args:
                character: キャラクター名（lumina/clarisse/nox）
                message: メッセージ
                thread_id: スレッドID（継続会話）
            
            Returns:
                応答テキスト
            """
            response = await execute_conversation(
                user_id="mcp_user",
                message=message,
                character=character,
                thread_id=thread_id
            )
            return response["content"]
        
        @self.tool()
        async def search_memories(
            query: str,
            limit: int = 10
        ) -> list[dict[str, Any]]:
            """
            記憶検索
            
            Args:
                query: 検索クエリ
                limit: 最大件数
            
            Returns:
                記憶リスト
            """
            results = await search_vector_db(
                user_id="mcp_user",
                query=query,
                limit=limit
            )
            return results
        
        @self.tool()
        async def get_knowledge_base(
            kb_name: str,
            topic: str
        ) -> str:
            """
            知識ベース検索
            
            Args:
                kb_name: 知識ベース名（movie/history/gossip/tech）
                topic: トピック
            
            Returns:
                関連情報
            """
            results = await query_knowledge_base(kb_name, topic)
            return "\n\n".join([r["content"] for r in results])
        
        @self.tool()
        async def autonomous_search(
            query: str,
            max_results: int = 5
        ) -> str:
            """
            自律的Web検索
            
            Args:
                query: 検索クエリ
                max_results: 最大件数
            
            Returns:
                検索結果サマリー
            """
            # セクション3で詳述
            results = await perform_autonomous_search(query, max_results)
            return summarize_search_results(results)
    
    def register_resources(self):
        """リソース登録"""
        
        @self.resource("character://lumina")
        async def get_lumina_info() -> TextContent:
            """ルミナのプロフィール"""
            return TextContent(
                type="text",
                text="ルミナ: フレンドリーな司会役。洞察型で雑談・推論が得意。"
            )
        
        @self.resource("character://clarisse")
        async def get_clarisse_info() -> TextContent:
            """クラリスのプロフィール"""
            return TextContent(
                type="text",
                text="クラリス: 穏やかな理論派。構造化・解説が得意。"
            )
        
        @self.resource("memory://recent")
        async def get_recent_memories() -> TextContent:
            """最近の記憶"""
            memories = await get_recent_memories(user_id="mcp_user", limit=10)
            text = "\n".join([m["summary"] for m in memories])
            return TextContent(type="text", text=text)

# MCP Server起動
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        server = LlmMultiChatMCPServer()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    asyncio.run(main())
```

---

## 2.3 MCP Client実装（他システムから利用）

```python
# mcp_client.py
from mcp.client import Client
from mcp.client.stdio import stdio_client

async def use_llm_multi_chat_via_mcp():
    """
    外部アプリケーションから会話LLMシステムを利用
    """
    # MCP Client接続
    async with stdio_client(
        command="python",
        args=["mcp_server.py"]
    ) as (read, write):
        async with Client(read, write) as client:
            # 初期化
            await client.initialize()
            
            # ツール一覧取得
            tools = await client.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")
            
            # ルミナと会話
            result = await client.call_tool(
                "chat_with_character",
                arguments={
                    "character": "lumina",
                    "message": "おすすめの映画を教えて"
                }
            )
            print(f"Lumina: {result.content}")
            
            # 記憶検索
            memories = await client.call_tool(
                "search_memories",
                arguments={"query": "映画", "limit": 5}
            )
            print(f"Memories: {memories.content}")
            
            # リソース取得
            lumina_info = await client.read_resource("character://lumina")
            print(f"Lumina info: {lumina_info.contents[0].text}")
```

---

## 2.4 MCP統合アーキテクチャ

```
┌─────────────────────────────────────┐
│     外部アプリケーション               │
│  (Claude Desktop, VSCode, etc.)    │
└─────────────────┬───────────────────┘
                  │ MCP Protocol
                  ↓
┌─────────────────────────────────────┐
│      MCP Server (stdio)             │
│  - ツール公開                         │
│  - リソース公開                        │
│  - セキュリティ管理                    │
└─────────────────┬───────────────────┘
                  │
                  ↓
┌─────────────────────────────────────┐
│   会話LLMシステム（既存）              │
│  - LangGraph                        │
│  - 5階層記憶                         │
│  - キャラクター管理                   │
└─────────────────────────────────────┘
```

---

# 3️⃣ 自律的外部サーチ・情報収集エージェント

## 3.1 概要

**目的**: 会話LLMシステムが自律的にWeb検索・情報収集を行い、知識ベースを自動更新する。

**トリガー条件**:
1. **ユーザー質問時**: 既存知識ベースに情報がない場合
2. **定期実行**: 日次/週次で最新情報を収集
3. **手動トリガー**: 管理者による明示的な更新指示

---

## 3.2 自律サーチエージェント実装

```python
# autonomous_search_agent.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import asyncio

class AutonomousSearchAgent:
    """
    自律的外部サーチ・情報収集エージェント
    """
    
    def __init__(self):
        self.serper = GoogleSerperAPIWrapper()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """ツール定義"""
        return [
            Tool(
                name="web_search",
                func=self.serper.run,
                description="Web検索。最新情報の取得に使用。"
            ),
            Tool(
                name="knowledge_base_query",
                func=self._query_kb,
                description="既存知識ベース検索。movie/history/gossip/techから検索。"
            ),
            Tool(
                name="wikipedia_search",
                func=self._wikipedia_search,
                description="Wikipedia検索。詳細な百科事典情報の取得。"
            ),
            Tool(
                name="save_to_kb",
                func=self._save_to_kb,
                description="知識ベースへ保存。重要な情報を永続化。"
            )
        ]
    
    def _create_agent(self):
        """ReActエージェント作成"""
        prompt = PromptTemplate.from_template("""
あなたは自律的な情報収集エージェントです。
ユーザーの質問に答えるため、以下の手順で情報を収集してください：

1. まず既存の知識ベースを検索
2. 情報が不足している場合、Web検索を実行
3. 必要に応じてWikipedia検索で詳細情報を取得
4. 重要な情報は知識ベースに保存
5. 最終的な回答を生成

利用可能なツール:
{tools}

ツール名:
{tool_names}

質問: {input}

思考プロセス:
{agent_scratchpad}
        """)
        
        return create_react_agent(
            llm=get_llm("gpt-4"),  # または "claude-3-sonnet"
            tools=self.tools,
            prompt=prompt
        )
    
    async def search_and_collect(
        self,
        query: str,
        max_depth: int = 3,
        save_to_kb: bool = True
    ) -> Dict[str, Any]:
        """
        自律的検索・情報収集
        
        Args:
            query: 検索クエリ
            max_depth: 探索深度
            save_to_kb: 知識ベース自動保存
        
        Returns:
            収集した情報
        """
        # エージェント実行
        agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=max_depth
        )
        
        result = await agent_executor.ainvoke({"input": query})
        
        # 知識ベース保存
        if save_to_kb:
            await self._save_to_kb(
                category=self._classify_category(query),
                content=result["output"]
            )
        
        return {
            "query": query,
            "result": result["output"],
            "intermediate_steps": result.get("intermediate_steps", []),
            "saved_to_kb": save_to_kb
        }
    
    async def _query_kb(self, query: str) -> str:
        """知識ベース検索"""
        # VectorDB検索
        results = await query_all_knowledge_bases(query, top_k=5)
        if results:
            return "\n\n".join([r["content"] for r in results])
        return "知識ベースに関連情報なし"
    
    async def _wikipedia_search(self, query: str) -> str:
        """Wikipedia検索"""
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wikipedia.run(query)
    
    async def _save_to_kb(self, category: str, content: str) -> str:
        """知識ベース保存"""
        # VectorDBへ保存
        await upsert_to_knowledge_base(
            kb_name=f"kb:{category}",
            content=content,
            metadata={"source": "autonomous_search", "timestamp": datetime.utcnow()}
        )
        return f"知識ベース kb:{category} に保存完了"
    
    def _classify_category(self, query: str) -> str:
        """カテゴリ分類（簡易版）"""
        # TODO: LLMベースの分類
        keywords = {
            "movie": ["映画", "ドラマ", "俳優", "監督"],
            "history": ["歴史", "年表", "出来事"],
            "gossip": ["トレンド", "ニュース", "話題"],
            "tech": ["技術", "プログラミング", "AI"]
        }
        
        for category, kws in keywords.items():
            if any(kw in query for kw in kws):
                return category
        return "custom"

# ========================================
# 定期実行スケジューラ
# ========================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler

class KnowledgeBaseUpdater:
    """知識ベース定期更新"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.agent = AutonomousSearchAgent()
    
    def start(self):
        """スケジューラ起動"""
        # 毎朝6時: ニュース・トレンド更新
        self.scheduler.add_job(
            self._update_gossip,
            'cron',
            hour=6,
            minute=0
        )
        
        # 毎週日曜日: 映画情報更新
        self.scheduler.add_job(
            self._update_movies,
            'cron',
            day_of_week='sun',
            hour=3,
            minute=0
        )
        
        # 毎月1日: 技術情報更新
        self.scheduler.add_job(
            self._update_tech,
            'cron',
            day=1,
            hour=2,
            minute=0
        )
        
        self.scheduler.start()
    
    async def _update_gossip(self):
        """トレンド情報更新"""
        queries = [
            "今日の主要ニュース",
            "Twitterトレンド",
            "話題の出来事"
        ]
        for query in queries:
            await self.agent.search_and_collect(query, save_to_kb=True)
    
    async def _update_movies(self):
        """映画情報更新"""
        queries = [
            "今週公開の映画",
            "話題の映画ランキング",
            "アカデミー賞ノミネート作品"
        ]
        for query in queries:
            await self.agent.search_and_collect(query, save_to_kb=True)
    
    async def _update_tech(self):
        """技術情報更新"""
        queries = [
            "最新AI技術トレンド",
            "GitHub人気リポジトリ",
            "Stack Overflow人気質問"
        ]
        for query in queries:
            await self.agent.search_and_collect(query, save_to_kb=True)

# 起動
if __name__ == "__main__":
    updater = KnowledgeBaseUpdater()
    updater.start()
    
    # イベントループ維持
    asyncio.get_event_loop().run_forever()
```

---

## 3.3 LangGraphへの統合

```python
# langgraph_integration.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from autonomous_search_agent import AutonomousSearchAgent

class State(TypedDict):
    messages: List[str]
    user_input: str
    need_search: bool
    search_results: Optional[str]
    final_response: str

def create_autonomous_search_graph():
    """自律サーチ統合LangGraph"""
    
    search_agent = AutonomousSearchAgent()
    
    # ノード定義
    async def check_knowledge_base(state: State) -> State:
        """既存知識ベース確認"""
        query = state["user_input"]
        kb_results = await query_all_knowledge_bases(query, top_k=3)
        
        if kb_results and kb_results[0]["score"] > 0.8:
            # 既存知識で十分
            state["need_search"] = False
            state["search_results"] = kb_results[0]["content"]
        else:
            # 外部検索必要
            state["need_search"] = True
        
        return state
    
    async def autonomous_search(state: State) -> State:
        """自律的Web検索"""
        if state["need_search"]:
            result = await search_agent.search_and_collect(
                query=state["user_input"],
                max_depth=3,
                save_to_kb=True
            )
            state["search_results"] = result["result"]
        
        return state
    
    async def generate_response(state: State) -> State:
        """最終応答生成"""
        # LLMで応答生成
        prompt = f"""
ユーザー: {state["user_input"]}

参考情報:
{state["search_results"]}

上記の情報を元に、わかりやすく回答してください。
        """
        
        response = await generate_llm_response(prompt)
        state["final_response"] = response
        
        return state
    
    # グラフ構築
    graph = StateGraph(State)
    
    graph.add_node("check_kb", check_knowledge_base)
    graph.add_node("search", autonomous_search)
    graph.add_node("respond", generate_response)
    
    graph.set_entry_point("check_kb")
    
    # 条件分岐
    graph.add_conditional_edges(
        "check_kb",
        lambda s: "search" if s["need_search"] else "respond"
    )
    
    graph.add_edge("search", "respond")
    graph.add_edge("respond", END)
    
    return graph.compile()

# 使用例
async def main():
    graph = create_autonomous_search_graph()
    
    result = await graph.ainvoke({
        "user_input": "2024年のアカデミー賞受賞作品は？",
        "messages": [],
        "need_search": False,
        "search_results": None,
        "final_response": ""
    })
    
    print(result["final_response"])

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 3機能の統合アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│              外部アプリケーション                      │
│      (Web UI, Mobile App, Claude Desktop)           │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ↓ REST/WebSocket     ↓ MCP
┌───────────────────┐  ┌────────────────┐
│   FastAPI Server  │  │   MCP Server   │
│  - JWT認証        │  │  - ツール公開   │
│  - レート制限     │  │  - リソース公開 │
│  - CORS          │  └────────────────┘
└─────────┬─────────┘
          │
          ↓
┌─────────────────────────────────────────────────────┐
│              LangGraph State Machine                │
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │ Router Node                                  │   │
│  │  - ユーザー指名判定                           │   │
│  │  - 記憶参照                                   │   │
│  │  - 自律サーチトリガー判定 ⭐                  │   │
│  └─────────────────────────────────────────────┘   │
│                      ↓                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ Autonomous Search Agent ⭐                   │   │
│  │  1. 既存知識ベース検索                         │   │
│  │  2. 不足時→Web検索                            │   │
│  │  3. Wikipedia検索                            │   │
│  │  4. 知識ベース自動保存                         │   │
│  └─────────────────────────────────────────────┘   │
│                      ↓                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ Character Pool (Lumina/Clarisse/Nox)        │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│           5階層記憶システム                           │
│  ① 短期記憶                                          │
│  ② 中期記憶                                          │
│  ③ 長期記憶                                          │
│  ④ 連想記憶                                          │
│  ⑤ 知識ベース ← 自律サーチで自動更新 ⭐              │
└─────────────────────────────────────────────────────┘
```

---

## 📈 Phase計画の更新

### Phase 1（4ヶ月 → 5ヶ月に延長）

| 機能 | 優先度 | 工数 | 担当 |
|------|--------|------|------|
| **セクション21: 一般的なチャットLLM機能** | 高 | 11週 | 既存 |
| **REST/WebSocket API** ⭐ | 高 | 2週 | 新規 |
| **MCP対応** ⭐ | 中 | 1週 | 新規 |
| **自律的外部サーチ** ⭐ | 高 | 2週 | 新規 |

**合計**: 16週（4ヶ月）→ 20週（5ヶ月）

---

## 🎯 実装優先順位

### Week 1-11: 既存Phase 1機能
- レスポンス制御
- ユーザー管理・認証
- コンテンツモデレーション
- レート制限
- データポータビリティ
- プロンプトテンプレート
- WebUI基本設計

### Week 12-13: REST/WebSocket API ⭐
- FastAPI実装
- Pydanticスキーマ
- WebSocketストリーミング
- JWT認証
- レート制限（Redis）

### Week 14: MCP対応 ⭐
- MCP Server実装
- ツール・リソース公開
- Claude Desktop連携テスト

### Week 15-16: 自律的外部サーチ ⭐
- ReActエージェント実装
- 定期実行スケジューラ
- 知識ベース自動更新
- LangGraph統合

### Week 17-20: 統合テスト・ドキュメント
- E2Eテスト
- パフォーマンスチューニング
- API/MCPドキュメント作成
- デプロイ準備

---

## ✅ タスク完了チェックリスト

### REST/WebSocket API
- [ ] FastAPI基本構造実装
- [ ] Pydanticモデル定義
- [ ] JWT認証実装
- [ ] WebSocket実装
- [ ] レート制限（Redis）
- [ ] CORS設定
- [ ] エラーハンドリング
- [ ] OpenAPI仕様書生成
- [ ] Postmanコレクション作成

### MCP対応
- [ ] MCP Server実装
- [ ] ツール定義（chat/search/kb）
- [ ] リソース定義（character/memory）
- [ ] stdio通信実装
- [ ] Claude Desktop連携テスト
- [ ] MCPドキュメント作成

### 自律的外部サーチ
- [ ] ReActエージェント実装
- [ ] Web検索ツール統合（Serper）
- [ ] Wikipedia検索統合
- [ ] 知識ベース保存機能
- [ ] カテゴリ自動分類
- [ ] 定期実行スケジューラ
- [ ] LangGraph統合
- [ ] 重複排除・品質フィルタ

---

## 📝 次のステップ

1. **会話履歴を仕様書に統合**
   - [`docks/会話LLM_仕様.md`](docks/会話LLM_仕様.md)に新セクション追加
   - セクション22: REST/WebSocket API詳細設計
   - セクション23: MCP対応
   - セクション24: 自律的外部サーチ・情報収集エージェント

2. **Phase計画更新**
   - Phase 1を4ヶ月→5ヶ月に延長
   - 工数見積を更新

3. **Git操作**
   - 会話履歴コミット
   - 仕様書更新コミット
   - プッシュ

---

**作成者**: LUMINA SYSTEM DESIGN TEAM  
**作成日**: 2025-11-12  
**対象バージョン**: 3.1.0