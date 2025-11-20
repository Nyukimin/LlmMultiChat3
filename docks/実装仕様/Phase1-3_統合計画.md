# Phase 1-3 統合計画書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 1-3 統合 - コア機能とAPI統合  
**作成日**: 2025-11-14  
**Phase 1完了**: `fcc08ed`  
**Phase 3完了**: `338a88c`

---

## 目次

1. [統合概要](#1-統合概要)
2. [現状分析](#2-現状分析)
3. [統合アーキテクチャ設計](#3-統合アーキテクチャ設計)
4. [モックレスポンス置換計画](#4-モックレスポンス置換計画)
5. [データフロー設計](#5-データフロー設計)
6. [実装計画](#6-実装計画)
7. [テスト計画](#7-テスト計画)
8. [パフォーマンス最適化](#8-パフォーマンス最適化)
9. [デプロイ戦略](#9-デプロイ戦略)

---

## 1. 統合概要

### 1.1 目的

Phase 1で実装した**LangGraphコア・5階層記憶システム**とPhase 3で実装した**REST/WebSocket API**を統合し、Phase 3のモックレスポンスを実際のLLM処理に置き換えます。これにより、完全に機能するエンドツーエンドのLLM会話システムを実現します。

### 1.2 統合対象

| Phase | 実装内容 | 行数 |
|-------|---------|------|
| **Phase 1** | LangGraphコア・記憶システム | 3,600行 |
| **Phase 3** | REST/WebSocket API・プラグイン | 7,558行 |
| **合計** | - | 11,158行 |

### 1.3 統合目標

✅ Phase 3 API（23エンドポイント）からPhase 1 LangGraphコア呼び出し  
✅ 5階層記憶システムとAPI記憶エンドポイント統合  
✅ WebSocketリアルタイム通信でストリーミング応答  
✅ プラグインシステムとLangGraphノード連携  
✅ エンドツーエンドテスト完備（50件）  
✅ パフォーマンス維持（API応答時間 < 200ms）

---

## 2. 現状分析

### 2.1 Phase 1 実装状況

#### LangGraphコア（main.py）

```python
# main.py: 302行
class MultiLLMChat:
    def __init__(self):
        # 記憶システム初期化
        self.memory_manager = MemoryManager()
        
        # LangGraphワークフロー構築
        self.workflow = self._build_workflow()
        
    def chat(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """会話実行（Phase 1メインエントリーポイント）."""
        # 1. 短期記憶取得
        context = self.memory_manager.get_conversation_context(session_id)
        
        # 2. LangGraph実行
        state = ConversationState(
            user_input=user_input,
            conversation_history=context['history']
        )
        result = self.workflow.invoke(state)
        
        # 3. 記憶保存
        self.memory_manager.record_turn(
            session_id=session_id,
            user_input=user_input,
            assistant_response=result['response']
        )
        
        return {
            'response': result['response'],
            'character': result['selected_character'],
            'metadata': result['metadata']
        }
```

#### 5階層記憶システム（memory/）

- **短期記憶**: [`memory/short_term.py`](../memory/short_term.py:1) (293行) - RAM/ConversationBuffer
- **中期記憶**: [`memory/mid_term.py`](../memory/mid_term.py:1) (356行) - JSON/DuckDB
- **長期記憶**: [`memory/long_term.py`](../memory/long_term.py:1) (316行) - キャラクターKPI
- **知識ベース**: [`memory/knowledge_base.py`](../memory/knowledge_base.py:1) (385行) - 簡易検索

**Phase 1の記憶システム特徴**:
- セッションベース管理（シングルユーザー想定）
- JSON永続化（ファイルベース）
- DuckDB中期記憶アーカイブ
- キャラクター別KPI追跡

### 2.2 Phase 3 実装状況

#### REST API（api/routes/chat.py）

```python
# api/routes/chat.py: 500行（モックレスポンス）
@router.post("/")
@limiter.limit("10/minute")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """会話API（現在はモックレスポンス）."""
    
    # TODO: Phase 1統合 - MultiLLMChat.chat()呼び出し
    # 現在のモックレスポンス:
    mock_response = {
        "session_id": request.session_id,
        "response": f"Hello! This is a mock response to: {request.user_input}",
        "character": request.character or "lumina",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "model": "mock-model",
            "tokens": 50,
            "processing_time_ms": 100
        }
    }
    
    return ChatResponse(**mock_response)
```

#### 記憶API（api/routes/memory.py）

```python
# api/routes/memory.py: 500行（モックレスポンス）
@router.post("/search")
async def search_memory(
    request: MemorySearchRequest,
    current_user: User = Depends(get_current_user)
) -> MemorySearchResponse:
    """記憶検索API（現在はモックレスポンス）."""
    
    # TODO: Phase 1統合 - MemoryManager.search()呼び出し
    mock_results = [
        {
            "memory_id": "mem-001",
            "content": "Mock memory content",
            "timestamp": datetime.now().isoformat(),
            "relevance_score": 0.95
        }
    ]
    
    return MemorySearchResponse(results=mock_results)
```

**Phase 3のモックレスポンス箇所**:
- `/api/v1/chat/` - 会話実行
- `/api/v1/chat/stream` - ストリーミング応答
- `/api/v1/chat/history` - 会話履歴取得
- `/api/v1/memory/search` - 記憶検索
- `/api/v1/memory/stats` - 記憶統計
- `/ws/chat` - WebSocket会話

### 2.3 統合課題

| 課題 | Phase 1 | Phase 3 | 統合方針 |
|------|---------|---------|----------|
| **セッション管理** | ファイルベース | JWT認証・マルチユーザー | Phase 3セッション → Phase 1セッションマッピング |
| **記憶永続化** | JSON | Redis想定 | Phase 1 JSON → Redis移行 |
| **非同期処理** | 同期実装 | FastAPI非同期 | Phase 1を非同期ラッパーで包む |
| **ストリーミング** | 非対応 | WebSocket/SSE対応 | LangGraphストリーミングサポート追加 |
| **マルチユーザー** | シングルユーザー | マルチユーザー | ユーザーIDベース分離 |

---

## 3. 統合アーキテクチャ設計

### 3.1 統合レイヤー構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 3: FastAPI Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  REST API   │  │ WebSocket   │  │   Plugin    │          │
│  │ Endpoints   │  │     API     │  │   Manager   │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼─────────────────┼─────────────────┼─────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│              Integration Layer (新規実装)                     │
│  ┌──────────────────────────────────────────────────┐       │
│  │         ChatService (非同期ラッパー)               │       │
│  │  - async chat()                                   │       │
│  │  - async stream_chat()                            │       │
│  │  - ユーザーセッション管理                          │       │
│  └──────────┬───────────────────────────────────────┘       │
│  ┌──────────┴───────────────────────────────────────┐       │
│  │         MemoryService (統合サービス)               │       │
│  │  - async search()                                 │       │
│  │  - async get_stats()                              │       │
│  │  - ユーザー別記憶管理                              │       │
│  └──────────┬───────────────────────────────────────┘       │
└─────────────┼───────────────────────────────────────────────┘
              │
┌─────────────┼───────────────────────────────────────────────┐
│         Phase 1: LangGraph Core Layer                         │
│  ┌──────────┴───────────────────────────────────────┐       │
│  │         MultiLLMChat (既存)                        │       │
│  │  - chat() (同期)                                  │       │
│  │  - LangGraphワークフロー実行                       │       │
│  └──────────┬───────────────────────────────────────┘       │
│  ┌──────────┴───────────────────────────────────────┐       │
│  │         MemoryManager (既存)                       │       │
│  │  - 5階層記憶システム                               │       │
│  │  - record_turn(), get_context()                   │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 新規実装レイヤー: Integration Layer

#### ChatService（統合サービス）

**目的**: Phase 3 API（非同期）とPhase 1 LangGraph（同期）を橋渡し

```python
# services/chat_service.py (新規作成)
import asyncio
from typing import Dict, Any, AsyncGenerator
import logging

from main import MultiLLMChat
from memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ChatService:
    """Phase 1-3統合チャットサービス."""
    
    def __init__(self):
        # Phase 1コアインスタンス（プロセスごと1つ）
        self.multi_llm_chat = MultiLLMChat()
        
        # ユーザーセッションマップ: {user_id: {session_id: Phase1SessionID}}
        self.user_sessions: Dict[str, Dict[str, str]] = {}
        
    async def chat(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        character: str = None
    ) -> Dict[str, Any]:
        """非同期会話実行."""
        try:
            # ユーザー専用セッションID取得
            phase1_session_id = self._get_phase1_session_id(user_id, session_id)
            
            # Phase 1同期処理を非同期実行
            result = await asyncio.to_thread(
                self.multi_llm_chat.chat,
                user_input=user_input,
                session_id=phase1_session_id
            )
            
            # レスポンス整形
            return {
                'session_id': session_id,
                'response': result['response'],
                'character': result['character'],
                'timestamp': result['metadata']['timestamp'],
                'metadata': result['metadata']
            }
            
        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}", exc_info=True)
            raise
    
    async def stream_chat(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        character: str = None
    ) -> AsyncGenerator[str, None]:
        """非同期ストリーミング会話."""
        # TODO: LangGraphストリーミングサポート実装後に対応
        # 現在は通常会話結果を分割して返す（疑似ストリーミング）
        result = await self.chat(user_id, session_id, user_input, character)
        
        # 文字ごとにストリーミング
        for char in result['response']:
            yield char
            await asyncio.sleep(0.01)  # ストリーミング効果
    
    def _get_phase1_session_id(self, user_id: str, session_id: str) -> str:
        """ユーザー専用Phase 1セッションID取得."""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        if session_id not in self.user_sessions[user_id]:
            # Phase 1用セッションID生成: user_{user_id}_{session_id}
            phase1_session_id = f"user_{user_id}_{session_id}"
            self.user_sessions[user_id][session_id] = phase1_session_id
        
        return self.user_sessions[user_id][session_id]


# グローバルインスタンス（FastAPIアプリケーション起動時作成）
chat_service = ChatService()
```

#### MemoryService（統合記憶サービス）

```python
# services/memory_service.py (新規作成)
import asyncio
from typing import Dict, Any, List
import logging

from memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class MemoryService:
    """Phase 1-3統合記憶サービス."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def search(
        self,
        user_id: str,
        query: str,
        layers: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """記憶検索（非同期）."""
        # Phase 1記憶検索を非同期実行
        results = await asyncio.to_thread(
            self.memory_manager.search_memory,
            query=query,
            layers=layers or ['short_term', 'mid_term', 'long_term'],
            limit=limit
        )
        
        return results
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """記憶統計取得（非同期）."""
        stats = await asyncio.to_thread(
            self.memory_manager.get_memory_stats
        )
        
        return stats
    
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """記憶削除（非同期）."""
        success = await asyncio.to_thread(
            self.memory_manager.delete_memory,
            memory_id=memory_id
        )
        
        return success


# グローバルインスタンス
memory_service = MemoryService(memory_manager=None)  # 初期化時にセット
```

### 3.3 ユーザーセッション管理設計

**課題**: Phase 1はシングルユーザー想定、Phase 3はマルチユーザー対応

**解決策**: ユーザーIDベースセッション分離

```python
# セッションID変換ルール
Phase 3 セッションID: "session-abc123"（ユーザーが指定）
↓
Phase 1 セッションID: "user_{user_id}_session-abc123"（内部変換）

例:
ユーザーID: "usr-001"
Phase 3 セッションID: "session-abc123"
→ Phase 1 セッションID: "user_usr-001_session-abc123"
```

**ファイル配置**:
```
memory/sessions/
├── user_usr-001_session-abc123.json
├── user_usr-001_session-xyz789.json
├── user_usr-002_session-def456.json
└── ...
```

---

## 4. モックレスポンス置換計画

### 4.1 置換対象エンドポイント

| エンドポイント | ファイル | 行数 | 置換内容 |
|--------------|---------|------|----------|
| `POST /api/v1/chat/` | [`api/routes/chat.py`](../api/routes/chat.py:1) | 150-180 | `chat_service.chat()`呼び出し |
| `POST /api/v1/chat/stream` | [`api/routes/chat.py`](../api/routes/chat.py:1) | 220-250 | `chat_service.stream_chat()`呼び出し |
| `GET /api/v1/chat/history` | [`api/routes/chat.py`](../api/routes/chat.py:1) | 280-310 | `memory_manager.get_session_history()`呼び出し |
| `POST /api/v1/memory/search` | [`api/routes/memory.py`](../api/routes/memory.py:1) | 120-150 | `memory_service.search()`呼び出し |
| `GET /api/v1/memory/stats` | [`api/routes/memory.py`](../api/routes/memory.py:1) | 180-210 | `memory_service.get_stats()`呼び出し |
| `WebSocket /ws/chat` | [`api/websocket.py`](../api/websocket.py:1) | 250-300 | `chat_service.stream_chat()`呼び出し |

### 4.2 置換実装例: POST /api/v1/chat/

#### 置換前（モックレスポンス）

```python
# api/routes/chat.py (現在)
@router.post("/")
@limiter.limit("10/minute")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """会話API（モックレスポンス）."""
    
    # モックレスポンス
    mock_response = {
        "session_id": request.session_id,
        "response": f"Hello! This is a mock response to: {request.user_input}",
        "character": request.character or "lumina",
        "timestamp": datetime.now().isoformat(),
        "metadata": {...}
    }
    
    return ChatResponse(**mock_response)
```

#### 置換後（Phase 1統合）

```python
# api/routes/chat.py (統合後)
from services.chat_service import chat_service

@router.post("/")
@limiter.limit("10/minute")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """会話API（Phase 1統合）."""
    
    try:
        # Phase 1 LangGraphコア呼び出し
        result = await chat_service.chat(
            user_id=current_user.user_id,
            session_id=request.session_id,
            user_input=request.user_input,
            character=request.character
        )
        
        return ChatResponse(**result)
        
    except InputValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=500, detail="LLM processing error")
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 4.3 置換実装例: WebSocket /ws/chat

#### 置換前（モックレスポンス）

```python
# api/websocket.py (現在)
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # モックストリーミング
    async for data in websocket.iter_json():
        if data["type"] == "chat":
            response = "Mock streaming response..."
            for char in response:
                await websocket.send_json({
                    "type": "chunk",
                    "content": char
                })
                await asyncio.sleep(0.05)
```

#### 置換後（Phase 1統合）

```python
# api/websocket.py (統合後)
from services.chat_service import chat_service

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    
    try:
        async for data in websocket.iter_json():
            if data["type"] == "auth":
                # JWT認証
                payload = jwt_manager.verify_token(data["token"])
                user_id = payload["sub"]
                await websocket.send_json({"type": "auth_ok"})
                
            elif data["type"] == "chat":
                # Phase 1ストリーミング呼び出し
                async for chunk in chat_service.stream_chat(
                    user_id=user_id,
                    session_id=data["session_id"],
                    user_input=data["user_input"],
                    character=data.get("character")
                ):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # ストリーミング完了通知
                await websocket.send_json({"type": "done"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
```

---

## 5. データフロー設計

### 5.1 会話フロー（REST API）

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/v1/chat
       │ {
       │   "session_id": "session-abc",
       │   "user_input": "こんにちは",
       │   "character": "lumina"
       │ }
       ↓
┌──────────────────────────────────────┐
│  FastAPI: api/routes/chat.py         │
│  - JWT認証（current_user取得）       │
│  - レート制限チェック                │
│  - リクエストバリデーション          │
└──────┬───────────────────────────────┘
       │ chat_service.chat()
       ↓
┌──────────────────────────────────────┐
│  Integration Layer: ChatService      │
│  - ユーザーセッションID変換          │
│    "user_{user_id}_session-abc"      │
│  - asyncio.to_thread() で同期実行    │
└──────┬───────────────────────────────┘
       │ multi_llm_chat.chat()
       ↓
┌──────────────────────────────────────┐
│  Phase 1: MultiLLMChat               │
│  ┌────────────────────────────────┐  │
│  │ 1. 短期記憶取得                │  │
│  │    memory_manager.get_context()│  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 2. LangGraphワークフロー実行   │  │
│  │    ├─ RouterNode               │  │
│  │    │   (キャラクター選択)       │  │
│  │    ├─ LuminaNode/ClarisseNode  │  │
│  │    │   (LLM推論)               │  │
│  │    └─ ResponseNode             │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 3. 記憶保存                    │  │
│  │    memory_manager.record_turn()│  │
│  │    ├─ 短期記憶（RAM）         │  │
│  │    ├─ 中期記憶（JSON/DuckDB） │  │
│  │    └─ 長期記憶（KPI更新）     │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────────────────┘
       │ return {
       │   'response': "こんにちは...",
       │   'character': 'lumina',
       │   'metadata': {...}
       │ }
       ↓
┌──────────────────────────────────────┐
│  FastAPI: api/routes/chat.py         │
│  - レスポンス整形                    │
│  - メトリクス記録                    │
└──────┬───────────────────────────────┘
       │ ChatResponse
       ↓
┌─────────────┐
│   Client    │
└─────────────┘
```

### 5.2 ストリーミングフロー（WebSocket）

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ WebSocket /ws/chat
       │ {"type": "auth", "token": "..."}
       ↓
┌──────────────────────────────────────┐
│  FastAPI: api/websocket.py           │
│  - JWT認証                           │
│  - WebSocket接続確立                 │
└──────┬───────────────────────────────┘
       │ {"type": "chat", ...}
       ↓
┌──────────────────────────────────────┐
│  Integration Layer: ChatService      │
│  - stream_chat() AsyncGenerator      │
└──────┬───────────────────────────────┘
       │ async for chunk in ...
       ↓
┌──────────────────────────────────────┐
│  Phase 1: MultiLLMChat               │
│  (疑似ストリーミング実装)            │
│  - chat()結果を文字単位で分割        │
│  - yield chunk                       │
└──────┬───────────────────────────────┘
       │ chunk: "こ" "ん" "に" ...
       ↓
┌──────────────────────────────────────┐
│  FastAPI: api/websocket.py           │
│  - WebSocket送信                     │
│    {"type": "chunk", "content": "こ"}│
└──────┬───────────────────────────────┘
       │ リアルタイム送信
       ↓
┌─────────────┐
│   Client    │
│  (UI更新)   │
└─────────────┘
```

### 5.3 記憶検索フロー

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/v1/memory/search
       │ {
       │   "query": "AI技術",
       │   "layers": ["mid_term", "long_term"],
       │   "limit": 10
       │ }
       ↓
┌──────────────────────────────────────┐
│  FastAPI: api/routes/memory.py       │
└──────┬───────────────────────────────┘
       │ memory_service.search()
       ↓
┌──────────────────────────────────────┐
│  Integration Layer: MemoryService    │
└──────┬───────────────────────────────┘
       │ memory_manager.search_memory()
       ↓
┌──────────────────────────────────────┐
│  Phase 1: MemoryManager              │
│  ┌────────────────────────────────┐  │
│  │ 1. 中期記憶検索                │  │
│  │    - DuckDB LIKE/FULL-TEXT     │  │
│  │    - sessions/*.json検索       │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 2. 長期記憶検索                │  │
│  │    - character_kpis.json検索   │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 3. 関連度スコアリング          │  │
│  │    - TF-IDF/BM25簡易実装       │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 4. 結果マージ・上位N件返却     │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────────────────┘
       │ return [
       │   {"memory_id": ..., "content": ...,
       │    "relevance_score": 0.95},
       │   ...
       │ ]
       ↓
┌─────────────┐
│   Client    │
└─────────────┘
```

---

## 6. 実装計画

### 6.1 Week 1: Integration Layer実装（5日）

#### Day 1-2: ChatService実装

**ファイル作成**:
- `services/__init__.py` (10行)
- `services/chat_service.py` (350行)

**実装内容**:
```python
# services/chat_service.py
class ChatService:
    def __init__(self): ...
    async def chat(self, user_id, session_id, user_input, character): ...
    async def stream_chat(self, user_id, session_id, user_input, character): ...
    def _get_phase1_session_id(self, user_id, session_id): ...
```

**テスト作成**:
- `tests/test_chat_service.py` (200行)

#### Day 3-4: MemoryService実装

**ファイル作成**:
- `services/memory_service.py` (300行)

**実装内容**:
```python
# services/memory_service.py
class MemoryService:
    def __init__(self, memory_manager): ...
    async def search(self, user_id, query, layers, limit): ...
    async def get_stats(self, user_id): ...
    async def delete_memory(self, user_id, memory_id): ...
```

**テスト作成**:
- `tests/test_memory_service.py` (200行)

#### Day 5: FastAPI統合・初期化

**ファイル更新**:
- `api/main.py` (50行追加)

**実装内容**:
```python
# api/main.py
from services.chat_service import chat_service
from services.memory_service import memory_service

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時処理."""
    logger.info("Initializing Phase 1-3 Integration Layer...")
    
    # Phase 1コア初期化（既に ChatService内で実施）
    # memory_service初期化
    memory_service.memory_manager = chat_service.multi_llm_chat.memory_manager
    
    # app.stateに登録
    app.state.chat_service = chat_service
    app.state.memory_service = memory_service
    
    logger.info("Integration Layer initialized successfully")
```

### 6.2 Week 2: モックレスポンス置換（7日）

#### Day 1-2: 会話エンドポイント置換

**ファイル更新**:
- `api/routes/chat.py` (150行変更)

**置換対象**:
- `POST /api/v1/chat/` (50行変更)
- `POST /api/v1/chat/stream` (50行変更)
- `GET /api/v1/chat/history` (50行変更)

#### Day 3-4: 記憶エンドポイント置換

**ファイル更新**:
- `api/routes/memory.py` (120行変更)

**置換対象**:
- `POST /api/v1/memory/search` (40行変更)
- `GET /api/v1/memory/stats` (40行変更)
- `DELETE /api/v1/memory/delete/{memory_id}` (40行変更)

#### Day 5-6: WebSocketエンドポイント置換

**ファイル更新**:
- `api/websocket.py` (100行変更)

**置換対象**:
- `WebSocket /ws/chat` (100行変更)

#### Day 7: セッション管理エンドポイント置換

**ファイル更新**:
- `api/routes/chat.py` (50行変更)

**置換対象**:
- `GET /api/v1/chat/sessions` (25行変更)
- `DELETE /api/v1/chat/sessions/{session_id}` (25行変更)

### 6.3 Week 3: 統合テスト・バグ修正（7日）

#### Day 1-3: 統合テスト実装

**ファイル作成**:
- `tests/integration/test_phase1_3_integration.py` (500行)

**テストケース**（50件）:

1. **会話フローテスト（15件）**
   - ユーザー登録→ログイン→会話実行→記憶保存
   - マルチユーザー同時会話
   - キャラクター指定会話
   - ストリーミング応答
   - エラーハンドリング

2. **記憶システムテスト（15件）**
   - 記憶検索
   - 記憶統計取得
   - セッション履歴取得
   - 記憶削除
   - ユーザー別記憶分離

3. **WebSocketテスト（10件）**
   - WebSocket接続・認証
   - ストリーミング会話
   - 接続切断処理
   - エラーハンドリング

4. **パフォーマンステスト（10件）**
   - API応答時間測定
   - 同時接続数テスト
   - メモリ使用量測定
   - スループット測定

#### Day 4-7: バグ修正・リファクタリング

**予想される課題**:
- 非同期処理のデッドロック
- セッション管理の競合
- メモリリーク
- パフォーマンス劣化

---

## 7. テスト計画

### 7.1 テストレベル

| レベル | 対象 | テスト数 | 実施時期 |
|-------|------|---------|----------|
| **ユニットテスト** | ChatService, MemoryService | 20件 | Week 1 |
| **統合テスト** | Phase 1-3統合フロー | 50件 | Week 3 |
| **APIテスト** | REST/WebSocketエンドポイント | 40件 | Week 2 |
| **E2Eテスト** | フルワークフロー | 10件 | Week 3 |
| **パフォーマンステスト** | 負荷テスト | 10件 | Week 3 |

### 7.2 統合テストシナリオ

#### シナリオ1: 基本会話フロー

```python
# tests/integration/test_phase1_3_integration.py
@pytest.mark.asyncio
async def test_basic_chat_flow():
    """基本会話フロー統合テスト."""
    
    # 1. ユーザー登録
    register_response = await client.post("/api/v1/auth/register", json={
        "username": "test_user",
        "email": "test@example.com",
        "password": "password123"
    })
    assert register_response.status_code == 200
    
    # 2. ログイン
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # 3. 会話実行（Phase 1 LangGraphコア呼び出し）
    chat_response = await client.post(
        "/api/v1/chat/",
        json={
            "session_id": "test-session-001",
            "user_input": "こんにちは、最近のAI技術について教えて",
            "character": "lumina"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    
    # Phase 1レスポンス検証
    assert "response" in data
    assert data["character"] == "lumina"
    assert "metadata" in data
    assert len(data["response"]) > 0
    
    # 4. 会話履歴取得（Phase 1記憶システムから取得）
    history_response = await client.get(
        "/api/v1/chat/history/test-session-001",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert history_response.status_code == 200
    history = history_response.json()["history"]
    assert len(history) == 2  # ユーザー入力 + アシスタント応答
    
    # 5. 記憶検索（Phase 1記憶システム検索）
    search_response = await client.post(
        "/api/v1/memory/search",
        json={
            "query": "AI技術",
            "layers": ["short_term", "mid_term"],
            "limit": 5
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert len(results) > 0
```

#### シナリオ2: WebSocketストリーミング

```python
@pytest.mark.asyncio
async def test_websocket_streaming():
    """WebSocketストリーミング統合テスト."""
    
    # 1. JWT取得
    access_token = await get_test_token()
    
    # 2. WebSocket接続
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        # 認証
        await ws.send(json.dumps({
            "type": "auth",
            "token": access_token
        }))
        auth_response = await ws.recv()
        assert json.loads(auth_response)["type"] == "auth_ok"
        
        # 会話送信（Phase 1ストリーミング）
        await ws.send(json.dumps({
            "type": "chat",
            "session_id": "ws-session-001",
            "user_input": "長文で詳しく説明して",
            "character": "clarisse"
        }))
        
        # ストリーミング受信
        chunks = []
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "chunk":
                chunks.append(data["content"])
            elif data["type"] == "done":
                break
        
        # 検証
        full_response = "".join(chunks)
        assert len(full_response) > 100  # 長文応答
        assert len(chunks) > 10  # ストリーミングチャンク数
```

### 7.3 パフォーマンステスト

#### テスト1: API応答時間

**目標**: API応答時間 < 200ms（Phase 1処理時間を除く）

```python
import time

@pytest.mark.asyncio
async def test_api_response_time():
    """API応答時間テスト."""
    
    access_token = await get_test_token()
    
    # 10回実行して平均応答時間測定
    response_times = []
    for i in range(10):
        start = time.time()
        response = await client.post(
            "/api/v1/chat/",
            json={
                "session_id": f"perf-test-{i}",
                "user_input": "短い応答でお願いします",
                "character": "nox"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        end = time.time()
        
        assert response.status_code == 200
        response_times.append((end - start) * 1000)  # ms
    
    avg_response_time = sum(response_times) / len(response_times)
    print(f"\nAverage API response time: {avg_response_time:.2f}ms")
    
    # Phase 1処理時間は除外できないが、目標値を緩和
    assert avg_response_time < 2000  # 2秒以内（Phase 1 LLM処理含む）
```

#### テスト2: 同時接続数

**目標**: 同時10接続でエラーなし

```python
import asyncio

@pytest.mark.asyncio
async def test_concurrent_connections():
    """同時接続数テスト."""
    
    access_token = await get_test_token()
    
    async def chat_request(session_id: str):
        response = await client.post(
            "/api/v1/chat/",
            json={
                "session_id": session_id,
                "user_input": "こんにちは",
                "character": "lumina"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.status_code
    
    # 10並列実行
    tasks = [chat_request(f"concurrent-{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    # 全て成功
    assert all(status == 200 for status in results)
```

---

## 8. パフォーマンス最適化

### 8.1 ボトルネック予測

| 箇所 | 予測ボトルネック | 最適化策 |
|------|-----------------|----------|
| **LangGraph実行** | LLM推論時間（1-3秒） | キャッシング、軽量モデル |
| **記憶保存** | JSON書き込み（50-100ms） | 非同期書き込み、バッチ処理 |
| **記憶検索** | DuckDB全文検索（10-50ms） | インデックス最適化 |
| **セッション管理** | ファイルI/O（5-10ms） | Redis移行 |

### 8.2 最適化実装計画

#### 最適化1: 記憶保存非同期化

**現状（Phase 1）**: 記憶保存は同期処理

```python
# memory_manager.py (現在)
def record_turn(self, session_id, user_input, assistant_response):
    # 同期的にJSON書き込み（ブロッキング）
    with open(f"memory/sessions/{session_id}.json", "w") as f:
        json.dump(session_data, f)
```

**最適化後**: 非同期書き込み

```python
# memory_manager.py (最適化後)
import aiofiles

async def record_turn_async(self, session_id, user_input, assistant_response):
    # 非同期JSON書き込み（ノンブロッキング）
    async with aiofiles.open(f"memory/sessions/{session_id}.json", "w") as f:
        await f.write(json.dumps(session_data))
```

**効果**: 記憶保存時間 50ms → 5ms（ノンブロッキング）

#### 最適化2: LLMレスポンスキャッシング

**戦略**: 同一入力に対する応答をキャッシュ（Redis）

```python
# services/chat_service.py (最適化後)
import hashlib
from redis import Redis

class ChatService:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1時間
    
    async def chat(self, user_id, session_id, user_input, character):
        # キャッシュキー生成
        cache_key = self._generate_cache_key(user_input, character)
        
        # キャッシュヒット確認
        cached_response = self.redis.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for key: {cache_key}")
            return json.loads(cached_response)
        
        # Phase 1実行
        result = await asyncio.to_thread(
            self.multi_llm_chat.chat,
            user_input=user_input,
            session_id=phase1_session_id
        )
        
        # キャッシュ保存
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
        
        return result
    
    def _generate_cache_key(self, user_input, character):
        content = f"{user_input}_{character}"
        return f"llm_cache:{hashlib.sha256(content.encode()).hexdigest()}"
```

**効果**: キャッシュヒット時 2000ms → 10ms（200倍高速化）

---

## 9. デプロイ戦略

### 9.1 デプロイ環境

**開発環境**:
```bash
# Phase 1-3統合開発環境起動
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**本番環境（Docker）**:

#### Dockerfile更新

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Phase 1コア
COPY main.py llm_nodes.py memory_manager.py ./
COPY memory/ ./memory/

# Phase 3 API
COPY api/ ./api/
COPY security/ ./security/
COPY plugins/ ./plugins/
COPY core/ ./core/

# 統合レイヤー
COPY services/ ./services/

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml更新

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
      - OLLAMA_HOST=ollama:11434
    volumes:
      - ./memory:/app/memory  # Phase 1記憶永続化
    depends_on:
      - redis
      - ollama
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

  ollama:
    image: ollama/ollama:latest
    container_name: llmmultichat3-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped
    networks:
      - llmmultichat3-network

volumes:
  ollama-data:

networks:
  llmmultichat3-network:
    driver: bridge
```

### 9.2 デプロイ手順

```bash
# 1. 環境変数設定
cp .env.example .env
vim .env  # JWT_SECRET等を設定

# 2. Docker起動
docker-compose up -d

# 3. Ollamaモデルダウンロード
docker exec -it llmmultichat3-ollama ollama pull llama2:7b

# 4. 動作確認
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI

# 5. 統合テスト実行
pytest tests/integration/test_phase1_3_integration.py -v
```

---

## 10. 統合完了基準

### 10.1 機能完了基準

✅ Integration Layer実装完了（ChatService, MemoryService）  
✅ Phase 3全エンドポイント（23件）モックレスポンス置換完了  
✅ 統合テスト50件全成功  
✅ E2Eテスト10件全成功  
✅ パフォーマンステスト目標達成  
✅ Docker本番環境デプロイ成功

### 10.2 パフォーマンス目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| API応答時間（LLM除く） | < 200ms | Locust負荷テスト |
| API応答時間（LLM含む） | < 2秒 | E2Eテスト |
| 同時接続数 | 10並列エラーなし | Locust負荷テスト |
| メモリ使用量 | < 2GB | Docker stats |
| キャッシュヒット率 | > 30% | Redis monitor |

### 10.3 品質目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| テスト成功率 | 100% | pytest |
| コードカバレッジ | > 80% | pytest-cov |
| Lint エラー | 0件 | flake8, pylint |
| 型チェックエラー | 0件 | mypy |

---

## 11. 統合後の展望

### Phase 1-3統合完了後の機能

✅ 完全なエンドツーエンドLLM会話システム  
✅ マルチユーザー対応  
✅ リアルタイムストリーミング応答  
✅ 5階層記憶システム完全動作  
✅ プラグインシステム実動作  
✅ REST/WebSocket API完全公開

### 次のステップ: Phase 4実装

Phase 1-3統合完了後、Phase 4（フロントエンド実装）へ移行。React SPAでユーザーフレンドリーなWebUIを構築し、LlmMultiChat3を完全なWebアプリケーションとして完成させます。

---

**Phase 1-3統合計画書 v1.0**  
**作成日**: 2025-11-14  
**ステータス**: ✅ レビュー待ち