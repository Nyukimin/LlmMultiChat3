# MemoryService の「API経由の記憶」詳細解説

## MemoryManager B（Phase 3新規）が存在する理由

### Phase 3の要求仕様

**Phase 3 Week 8-10で実装されたもの:**
- FastAPI REST API（23エンドポイント）
- WebSocket リアルタイム通信
- マルチユーザー対応
- JWT認証・RBAC（ロールベース認証）

**Phase 3で追加された7つの記憶管理APIエンドポイント:**

1. **POST /api/v1/memory/search** - 記憶検索
2. **POST /api/v1/memory/store** - 記憶保存
3. **DELETE /api/v1/memory/delete/{memory_id}** - 記憶削除
4. **GET /api/v1/memory/stats** - 統計情報取得
5. **GET /api/v1/memory/sessions/{session_id}** - セッション別記憶取得
6. **POST /api/v1/memory/flush** - 記憶フラッシュ
7. **GET /api/v1/memory/health** - ヘルスチェック

## 具体的なユースケース

### ユースケース1: Webフロントエンドからの記憶検索

**シナリオ:**
ユーザーがブラウザから「以前AIについて話した内容を見たい」とリクエスト

**処理フロー:**

```
[Reactフロントエンド]
    |
    | HTTP POST /api/v1/memory/search
    | {
    |   "query": "AI",
    |   "memory_types": ["short_term", "long_term"],
    |   "limit": 10
    | }
    ↓
[FastAPI Server]
    |
    | JWT認証チェック
    | ユーザーID取得: user_123
    ↓
[api/routes/memory.py:124-155]
    |
    | async def search_memory(...)
    ↓
[services/memory_service.py:49-102]
    |
    | MemoryService.search(
    |   user_id="user_123",
    |   query="AI",
    |   layers=["short_term", "long_term"],
    |   limit=10
    | )
    ↓
[MemoryManager B]
    |
    | search_memory() 実行
    | - 短期記憶から検索
    | - 長期記憶（VectorDB）から検索
    | - スコアリング・ソート
    ↓
レスポンス返却:
{
  "query": "AI",
  "results": [
    {
      "memory_id": "mem-456",
      "content": "AIは機械学習を含む...",
      "relevance_score": 0.95
    }
  ]
}
```

### ユースケース2: 記憶統計ダッシュボード

**シナリオ:**
ユーザーが自分の会話記憶統計を見たい

**処理フロー:**

```
[Reactフロントエンド]
    |
    | HTTP GET /api/v1/memory/stats
    ↓
[FastAPI Server]
    |
    | JWT認証: user_123
    ↓
[services/memory_service.py:104-150]
    |
    | MemoryService.get_stats(user_id="user_123")
    ↓
[MemoryManager B]
    |
    | get_memory_stats() 実行
    ↓
レスポンス:
{
  "total_memories": 150,
  "by_layer": {
    "short_term": 20,
    "mid_term": 50,
    "long_term": 80
  },
  "total_sessions": 10,
  "character_stats": {...}
}
```

## Phase 1とPhase 3の違い

### Phase 1（MemoryManager A）

**使用シーン:**
- ローカル実行（`python main.py`）
- 単一ユーザー
- コマンドライン対話

**記憶へのアクセス:**
```python
# main.py - Phase 1
chat_system = MultiLLMChat()
result = chat_system.chat("こんにちは")
# ↓ 内部でMemoryManager Aに保存
```

**特徴:**
- 直接メソッド呼び出し
- 同期処理
- ユーザー認証なし
- API不要

### Phase 3（MemoryManager B）

**使用シーン:**
- Webアプリケーション
- マルチユーザー（100人同時接続）
- ブラウザ・モバイルアプリから利用

**記憶へのアクセス:**
```javascript
// Reactフロントエンド
const response = await fetch('http://localhost:8000/api/v1/memory/search', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer eyJhbGc...',  // JWTトークン
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "AI",
    memory_types: ["long_term"],
    limit: 10
  })
});

const data = await response.json();
console.log(data.results);  // 検索結果
```

**特徴:**
- HTTP/WebSocket経由
- 非同期処理
- JWT認証必須
- ユーザー別データ分離

## なぜMemoryServiceが必要なのか

### 1. マルチユーザー対応

**Phase 1（単一ユーザー）:**
```python
memory_manager = MemorySystemManager()
memory_manager.add_conversation_turn("lumina", "こんにちは")
# ↑ ユーザーIDなし、全員共通の記憶
```

**Phase 3（マルチユーザー）:**
```python
# services/memory_service.py
async def get_stats(self, user_id: str):
    # ユーザーごとに独立した統計
    stats = await asyncio.to_thread(
        self.memory_manager.get_memory_stats,
        session_id=user_id  # ← ユーザー分離
    )
```

### 2. 非同期処理

**FastAPIは非同期フレームワーク:**
```python
# api/routes/memory.py
@router.post("/search")
async def search_memory(...):
    # ↑ async必須（FastAPIの要求）
    
    # Phase 1の同期処理を非同期実行
    results = await asyncio.to_thread(
        self.memory_manager.search_memory,
        query=query
    )
```

**なぜasyncio.to_thread()が必要か:**
- Phase 1のMemoryManagerは同期処理
- FastAPIは非同期処理要求
- `asyncio.to_thread()`で同期→非同期変換

### 3. セキュリティ・認証

**Phase 3のAPI呼び出し:**
```python
@router.post("/search")
async def search_memory(
    current_user: User = Depends(get_current_user)  # ← JWT認証
):
    # current_user.user_id でユーザー識別
    results = await memory_service.search(
        user_id=current_user.user_id,  # ← 認証されたユーザーのみアクセス
        query=query
    )
```

**Phase 1には認証機能なし:**
```python
# main.py - 認証なし
chat_system.chat("こんにちは")
```

## MemoryService（B）の具体的な役割

### 役割1: Phase 1とPhase 3の橋渡し

```python
# services/memory_service.py:49-102
class MemoryService:
    async def search(self, user_id, query, layers, limit):
        # ↓ Phase 1の同期処理を非同期実行
        results = await asyncio.to_thread(
            self.memory_manager.search_memory,  # ← Phase 1メソッド
            query=query,
            layers=layers,
            limit=limit
        )
        return results  # ← Phase 3形式で返却
```

### 役割2: API形式のレスポンス整形

**Phase 1の戻り値（内部形式）:**
```python
[
    {'id': 'mem-1', 'text': '...', 'score': 0.9},
    ...
]
```

**Phase 3のレスポンス（API形式）:**
```json
{
  "query": "AI",
  "results": [
    {
      "memory_id": "mem-1",
      "content": "...",
      "relevance_score": 0.9,
      "timestamp": "2025-11-17T..."
    }
  ],
  "total_count": 1
}
```

### 役割3: ユーザー別データ分離

```python
# 同時アクセスの例
user_123 = await memory_service.get_stats(user_id="user_123")
user_456 = await memory_service.get_stats(user_id="user_456")

# ↓ それぞれ独立した統計
user_123['total_memories']  # 150件
user_456['total_memories']  # 80件
```

## まとめ

**「API経由の記憶」の意味:**

1. **HTTPリクエストで記憶にアクセス**
   - POST /api/v1/memory/search
   - GET /api/v1/memory/stats
   - 等の7エンドポイント

2. **WebブラウザやモバイルアプリからのHTTP通信**
   - JavaScript fetch()
   - axios.post()
   - etc.

3. **JWT認証でユーザー識別**
   - トークンでユーザーID取得
   - ユーザー別データ分離

**MemoryManager B（Phase 3）が存在する理由:**

1. **Phase 3のAPI機能のため**
   - 7つの記憶管理エンドポイント
   - マルチユーザー対応
   - 非同期処理

2. **Phase 1との互換性維持のため**
   - Phase 1は同期処理
   - Phase 3は非同期処理
   - `asyncio.to_thread()`で橋渡し

3. **統合作業の過渡期**
   - 本来は1つで十分
   - 段階的統合のため一時的に2つ存在

---
作成日: 2025-11-17
