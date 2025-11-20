# 会話LLM_記憶システム仕様.md
## ― 5階層永続的記憶アーキテクチャ ―

---

## 1. 記憶システム概要

**目的:**
人間のように**過去を記憶し、学習し、成長する**AI対話パートナーを実現するための永続的記憶システム。

**特徴:**
- **5階層記憶**: 短期・中期・長期・連想・知識ベース
- **自動階層遷移**: 重要度に応じた自動アーカイブ
- **ベクトル検索**: 意味的類似性による高速検索
- **忘却曲線**: 人間らしい自然な忘却
- **継続学習**: ユーザーとの対話から常に学習

---

## 2. 記憶階層の詳細

| レイヤー | 保存先 | TTL | 内容 | 主目的 | バックアップ |
|-----------|--------|------|------|--------|------------|
| **短期記憶** | LangGraph State (RAM) | 6〜12ターン | 現在の会話スレッド | 文脈維持・即時応答 | Redis Snapshot |
| **中期記憶** | Redis (24h) → DuckDB (7-30d) | 24h〜30d | 要約＋keywords＋embedding | セッション復帰・割込み対応 | 日次DuckDB Export |
| **長期記憶** | VectorDB + PostgreSQL | 永続 | 全履歴・プロファイル・学習パターン | 継続学習・パーソナライズ | 週次S3/MinIO |
| **連想記憶** | Graph DB (Neo4j) + VectorDB | 永続 | 概念間の関連性・連想ネットワーク | 創造的発想・話題発展 | リアルタイム複製 |
| **知識ベース** | VectorDB(kb:*) | 定期更新 | ドメイン専門知識 | RAG検索・事実参照 | バージョン管理 |

---

## 3. 短期記憶 (Working Memory)

### 3.1 基本仕様

```python
class ShortTermMemory:
    """
    短期記憶（ワーキングメモリ）
    LangGraph Stateとして実装
    """
    def __init__(self):
        self.turns = []  # 会話ターン（最大12）
        self.thread_id = None
        self.domain = None  # 話題ドメイン
        self.character_turns = {"lumina": 0, "clarisse": 0, "nox": 0}
        self.start_time = now()
        self.last_update = now()
    
    def add_turn(self, speaker, message):
        """ターン追加"""
        self.turns.append({
            "speaker": speaker,
            "message": message,
            "timestamp": now()
        })
        
        if speaker in self.character_turns:
            self.character_turns[speaker] += 1
        
        self.last_update = now()
        
        # 上限チェック
        if len(self.turns) > 12:
            self._flush_oldest()
    
    def _flush_oldest(self):
        """古いターンを中期記憶へflush"""
        flushed = self.turns.pop(0)
        flush_to_mid_term(self.thread_id, [flushed])
```

### 3.2 スレッド判定

| フェーズ | 条件 |
|-----------|------|
| **開始** | 初回入力／トピック変更／ドメイン変化／「ところで…」発言 |
| **終了** | 類似度 < 0.75／アイドル10分／ターン上限／話題転換 |
| **短期保持** | 最大12メッセージ（ユーザー＋3キャラ） |
| **flush処理** | summary＋keywords＋embeddingを生成し中期へ転送 |

### 3.3 スレッド例

```jsonc
{
  "thread_id": 42,
  "domain": "movie",
  "turns": [
    {"speaker":"user", "msg":"インセプションみたいな映画ある？"},
    {"speaker":"lumina","msg":"『メメント』や『プレステージ』が近いね"}
  ],
  "ct": {"lumina":0,"claris":1,"nox":0}
}
```

---

## 4. 中期記憶 (Session Memory)

### 4.1 保存メカニズム

```python
def flush_to_mid_term(thread_id, turns):
    """
    短期→中期へのFlush処理
    """
    # 1. LLMで要約生成
    summary = generate_summary(turns)
    
    # 2. キーワード抽出
    keywords = extract_keywords(turns)
    
    # 3. ベクトル化
    embedding = create_embedding(summary)
    
    # 4. Redisへ保存（24h TTL）
    redis.setex(f"session:{thread_id}", 86400, {
        "summary": summary,
        "keywords": keywords,
        "embedding": embedding,
        "turn_count": len(turns),
        "created_at": now()
    })
    
    # 5. 24h後にDuckDBへアーカイブをスケジュール
    schedule_archive(thread_id, delay=86400)
```

### 4.2 DuckDBアーカイブ

```python
def archive_to_duckdb(session_data):
    """
    Redis（24h）→ DuckDB（7-30日）へアーカイブ
    """
    conn = duckdb.connect('mid_term_memory.db')
    
    conn.execute("""
        INSERT INTO session_archive
        (thread_id, user_id, summary, keywords, embedding, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session_data["thread_id"],
        session_data["user_id"],
        session_data["summary"],
        json.dumps(session_data["keywords"]),
        session_data["embedding"],
        session_data["created_at"]
    ))
    
    conn.close()
```

---

## 5. 長期記憶 (Persistent Memory)

### 5.1 VectorDB保存

```python
def archive_to_long_term(session_data):
    """
    中期→長期へのアーカイブ
    """
    # 1. VectorDBへembedding保存
    vector_db.upsert(
        namespace=f"user:{user_id}",
        vectors=[{
            "id": session_data["thread_id"],
            "values": session_data["embedding"],
            "metadata": {
                "summary": session_data["summary"],
                "keywords": session_data["keywords"],
                "timestamp": now(),
                "importance": calculate_importance(session_data)
            }
        }]
    )
    
    # 2. PostgreSQLへメタデータ保存
    db.execute("""
        INSERT INTO conversation_history
        (user_id, thread_id, summary, keywords, created_at, importance)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        thread_id,
        summary,
        json.dumps(keywords),
        now(),
        importance
    ))
```

### 5.2 記憶検索

```python
def retrieve_relevant_memory(user_input, user_id, top_k=5):
    """
    ユーザー入力時の記憶参照
    """
    # 1. 入力をベクトル化
    query_embedding = create_embedding(user_input)
    
    # 2. 長期記憶から関連する過去会話を検索
    past_contexts = vector_db.query(
        namespace=f"user:{user_id}",
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # 3. 中期記憶から直近セッションを取得
    recent_sessions = redis.keys(f"session:{user_id}:*")
    
    # 4. 統合コンテキスト生成
    context = {
        "past_conversations": past_contexts,
        "recent_sessions": recent_sessions,
        "user_profile": db.get_user_profile(user_id)
    }
    
    return context
```

---

## 6. ユーザープロファイル管理

```python
class UserProfile:
    """
    ユーザーの嗜好・特性を学習
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.preferences = {}  # 映画ジャンル、話題の嗜好
        self.interaction_history = []  # キャラ指名頻度
        self.growth_data = {}  # ユーザーとの関係性深度
        
    def update_from_conversation(self, conversation):
        """会話から嗜好を学習"""
        # 好みトピックの抽出
        topics = extract_topics(conversation)
        for topic in topics:
            self.preferences[topic] = self.preferences.get(topic, 0) + 1
        
        # 指名頻度の更新
        mentions = extract_mentions(conversation)
        self.interaction_history.append(mentions)
        
        # 永続化
        self.save_to_db()
    
    def get_preference_vector(self):
        """嗜好ベクトル取得"""
        # トップ10トピックでベクトル生成
        top_topics = sorted(
            self.preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return create_embedding(
            " ".join([topic for topic, _ in top_topics])
        )
```

---

## 7. 記憶の重要度判定

```python
class MemorySalience:
    """
    人間の記憶のように、重要な出来事を優先的に記憶
    """
    def calculate_importance(self, event):
        """
        記憶の重要度を計算（0-1）
        
        要素:
        - 感情的インパクト
        - 新規性（初めての出来事か）
        - 関連性（過去の記憶との繋がり）
        - 繰り返し（何度も言及されるか）
        """
        score = 0.0
        
        # 感情的インパクト（高い感情価は記憶に残りやすい）
        emotion_intensity = abs(event.get("emotion_valence", 0))
        score += emotion_intensity * 0.4
        
        # 新規性（初めての話題は印象に残る）
        novelty = self._calculate_novelty(event)
        score += novelty * 0.3
        
        # 関連性（既存記憶との繋がりが多いほど重要）
        relatedness = self._calculate_relatedness(event)
        score += relatedness * 0.2
        
        # 繰り返し（複数回言及される情報は重要）
        recency = event.get("mention_count", 1) / 10.0
        score += min(recency, 1.0) * 0.1
        
        return min(score, 1.0)
    
    def _calculate_novelty(self, event):
        """新規性の計算"""
        # 過去の記憶と比較して類似度を計算
        similar_memories = vector_db.query(
            vector=event["embedding"],
            top_k=5,
            threshold=0.8
        )
        return 1.0 - (len(similar_memories) / 5.0)
    
    def prioritize_for_consolidation(self, short_term_memory):
        """短期記憶から長期記憶への優先順位付け"""
        scored_memories = [
            (mem, self.calculate_importance(mem))
            for mem in short_term_memory
        ]
        
        # 重要度でソート
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # 上位70%のみ長期記憶へ
        threshold_idx = int(len(scored_memories) * 0.7)
        return [mem for mem, score in scored_memories[:threshold_idx]]
```

---

## 8. ストレージポリシー

### 8.1 A/B案

| ポリシー | 内容 | 検索性 | ストレージ |
| ------------- | -------------------- | ----- | -------------- |
| **A. 要約のみ永続** | VectorDBにsummaryのみ保存 | 高速 | 省容量・低負荷 |
| **B. フルログ保存** | S3/MinIOにParquetで保存 | 全文検索可 | コスト増・高セキュリティ要求 |

**推奨:** **A + LoRA（キャラ成長）併用構成**

### 8.2 バックアップ戦略

| 対象 | 頻度 | 方法 | 保存先 |
|------|------|------|--------|
| Redis RDB | 30分 | スナップショット | ローカルディスク |
| DuckDB | 日次 | エクスポート | MinIO/S3 |
| VectorDB | 週次 | フルバックアップ | MinIO/S3 |
| PostgreSQL | 日次 | pg_dump | MinIO/S3 |

---

## 9. セキュリティ・運用

| 項目 | 方針 |
| ------ | --------------------------------- |
| 通信暗号化 | Redis→TLS、VectorDB→LUKS/KMS |
| GDPR削除 | `DROP NAMESPACE user:<uid>` で完全削除 |
| バックアップ | Redis RDB 30分／DuckDB→MinIO日次 |
| 監査ログ | `session_log` に追記オンリー記録 |

### 9.1 GDPR対応

```python
def delete_user_data(user_id, confirmation_token):
    """
    ユーザーデータ完全削除（GDPR Right to Erasure）
    """
    if not verify_deletion_token(user_id, confirmation_token):
        raise PermissionError("Invalid confirmation token")
    
    # 1. VectorDB削除
    vector_db.delete_namespace(f"user:{user_id}")
    
    # 2. PostgreSQL削除
    db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
    
    # 3. Redis削除
    redis.delete(f"session:{user_id}:*")
    
    # 4. DuckDB削除
    duckdb.execute("DELETE FROM session_archive WHERE user_id = ?", (user_id,))
    
    # 5. 監査ログ記録
    audit_log.record("user_data_deleted", user_id=user_id)
    
    return {"deleted": True, "user_id": user_id}
```

---

## 10. パフォーマンス最適化

### 10.1 キャッシング

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_profile(user_id):
    """ユーザープロファイルのキャッシング"""
    return db.get_user_profile(user_id)

@lru_cache(maxsize=500)
def get_embedding(text):
    """埋め込みベクトルのキャッシング"""
    return embedding_model.encode(text)
```

### 10.2 バッチ処理

```python
def batch_archive(sessions, batch_size=100):
    """
    バッチアーカイブ（効率化）
    """
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i:i+batch_size]
        vector_db.upsert_batch(batch)
```

---

## 11. 実装例

### 基本的な会話フロー

```python
async def process_user_input(user_id, session_id, message):
    """
    ユーザー入力の処理
    """
    # 1. 記憶参照
    context = retrieve_relevant_memory(message, user_id)
    
    # 2. 短期記憶へ追加
    state.add_turn("user", message)
    
    # 3. 応答生成（キャラクター選択は別モジュール）
    response = await generate_response(message, context)
    
    # 4. 短期記憶へ保存
    state.add_turn("assistant", response)
    
    # 5. 必要ならflush
    if state.should_flush():
        flush_to_mid_term(session_id, state.turns)
    
    return response
```

---

**ドキュメント:**
- **親文書:** [会話LLM_仕様.md](./01_会話LLM_仕様.md)
- **関連文書:**
  - [会話LLM_キャラクター仕様.md](./03_会話LLM_キャラクター仕様.md)
  - [会話LLM_連想記憶仕様.md](./05_会話LLM_連想記憶仕様.md)

**更新日:** 2025-11-19  
**バージョン:** 1.0.0  
**担当:** LUMINA MEMORY SYSTEM TEAM
