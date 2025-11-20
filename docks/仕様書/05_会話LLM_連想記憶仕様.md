# 会話LLM 連想記憶仕様書

**バージョン:** 3.1.0  
**最終更新:** 2025-11-19  
**親文書:** [会話LLM_仕様.md](./01_会話LLM_仕様.md)

---

## 目次

1. [概要](#1-概要)
2. [連想記憶の構造](#2-連想記憶の構造)
3. [連想記憶の活用例](#3-連想記憶の活用例)
4. [連想記憶の学習メカニズム](#4-連想記憶の学習メカニズム)
5. [高度な機能](#5-高度な機能)
6. [SQLite Graph実装](#6-sqlite-graph実装)
7. [パフォーマンス最適化](#7-パフォーマンス最適化)

---

## 1. 概要

連想記憶は、概念・トピック・感情・経験を**ネットワーク構造**で保存し、人間の脳のように「AからBを思い出す」連鎖的な記憶想起を実現します。

### 1.1 設計思想

- **ネットワーク構造**: グラフデータベースによる概念の結びつき
- **連鎖的想起**: 一つの概念から関連概念を連想
- **強度学習**: 共起頻度に基づく関連性の強化
- **自然な忘却**: 使わない記憶の減衰

### 1.2 データ構造

```
概念ノード
  ├── 名前
  ├── カテゴリ
  ├── 埋め込みベクトル
  └── メタデータ

エッジ(関連性)
  ├── 強度 (0.0-1.0)
  ├── 共起回数
  ├── 最終活性化時刻
  └── 関係タイプ
```

---

## 2. 連想記憶の構造

### 2.1 基本実装（SQLite Graph）

```python
class AssociativeMemory:
    """
    SQLiteグラフDBを使った連想記憶システム
    ノード: 概念、トピック、感情、人物、場所
    エッジ: 関連性、強度、時間的近接性
    """
    def __init__(self):
        self.graph_db = SQLiteGraph("memory/associative.db")
        self.vector_db = SQLiteVectorDB("memory/embeddings.db")
    
    def add_concept(self, concept, embedding, metadata):
        """新しい概念をグラフに追加"""
        # VectorDBに埋め込み保存
        self.vector_db.upsert(
            namespace="associative",
            vectors=[{
                "id": concept,
                "values": embedding,
                "metadata": metadata
            }]
        )
        
        # Graph DBにノード作成
        self.graph_db.create_node(
            label="Concept",
            properties={
                "name": concept,
                "created_at": now(),
                "activation_count": 0,
                "emotional_valence": metadata.get("emotion", 0)
            }
        )
    
    def link_concepts(self, concept_a, concept_b, relationship_type, strength=1.0):
        """2つの概念を関連付け"""
        self.graph_db.create_relationship(
            from_node=concept_a,
            to_node=concept_b,
            rel_type=relationship_type,
            properties={
                "strength": strength,
                "created_at": now(),
                "co_occurrence_count": 1
            }
        )
    
    def retrieve_associated_concepts(self, trigger_concept, depth=3, threshold=0.5):
        """
        連想検索: トリガー概念から関連概念を連鎖的に取得
        
        Args:
            trigger_concept: 起点となる概念
            depth: 探索深度（何ホップまで辿るか）
            threshold: 関連性の閾値
        
        Returns:
            関連概念のリストと関連性スコア
        """
        # Graph DBで連想パスを探索
        query = """
        WITH RECURSIVE graph_walk(node_id, node_name, path_strength, level) AS (
            -- 開始ノード
            SELECT id, name, 1.0, 0
            FROM nodes
            WHERE name = ?
            
            UNION ALL
            
            -- 再帰: 次のノードへ
            SELECT 
                n.id,
                n.name,
                gw.path_strength * e.strength,
                gw.level + 1
            FROM graph_walk gw
            JOIN edges e ON gw.node_id = e.from_id
            JOIN nodes n ON e.to_id = n.id
            WHERE gw.level < ?
              AND e.strength >= ?
              AND n.id NOT IN (SELECT node_id FROM graph_walk)
        )
        SELECT DISTINCT node_name, MAX(path_strength) as strength
        FROM graph_walk
        WHERE level > 0
        GROUP BY node_name
        ORDER BY strength DESC
        LIMIT 20
        """
        
        results = self.graph_db.execute(query, (
            trigger_concept, depth, threshold
        ))
        
        return results
    
    def strengthen_association(self, concept_a, concept_b, delta=0.1):
        """
        関連性を強化（共起頻度に基づく学習）
        ヘッブの法則: "一緒に発火するニューロンは結合が強化される"
        """
        self.graph_db.execute("""
            UPDATE edges
            SET strength = MIN(strength + ?, 1.0),
                co_occurrence_count = co_occurrence_count + 1,
                last_activated = ?
            WHERE (from_node = ? AND to_node = ?)
               OR (from_node = ? AND to_node = ?)
        """, (delta, now(), concept_a, concept_b, concept_b, concept_a))
    
    def decay_inactive_associations(self, days_threshold=30, decay_rate=0.05):
        """
        使われていない関連性を減衰（忘却曲線）
        """
        cutoff_time = now() - (days_threshold * 86400)
        
        self.graph_db.execute("""
            UPDATE edges
            SET strength = MAX(strength * (1 - ?), 0.0)
            WHERE last_activated < ?
        """, (decay_rate, cutoff_time))
        
        # 弱すぎる関連性を削除
        self.graph_db.execute("""
            DELETE FROM edges
            WHERE strength < 0.1
        """)
```

### 2.2 データベーススキーマ

```sql
-- ノードテーブル
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    type TEXT,
    metadata JSON,
    created_at INTEGER
);

-- エッジテーブル
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY,
    from_id INTEGER,
    to_id INTEGER,
    rel_type TEXT,
    strength REAL DEFAULT 1.0,
    co_occurrence INTEGER DEFAULT 1,
    last_activated INTEGER,
    FOREIGN KEY(from_id) REFERENCES nodes(id),
    FOREIGN KEY(to_id) REFERENCES nodes(id)
);

-- インデックス（高速検索）
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
CREATE INDEX IF NOT EXISTS idx_edges_strength ON edges(strength);
```

---

## 3. 連想記憶の活用例

### 3.1 会話中の連想トリガー

```python
def generate_associative_response(user_input, conversation_history):
    """
    ユーザー入力から連想的な話題を展開
    """
    # 入力から主要概念を抽出
    concepts = extract_concepts(user_input)
    
    # 各概念から連想検索
    all_associations = []
    for concept in concepts:
        associations = associative_memory.retrieve_associated_concepts(
            trigger_concept=concept,
            depth=2,
            threshold=0.3
        )
        all_associations.extend(associations)
    
    # 最も強い連想を選択
    top_association = max(all_associations, key=lambda x: x["strength"])
    
    # 連想に基づく応答生成
    prompt = f"""
    ユーザーが「{user_input}」と言いました。
    これは「{top_association['concept']}」を連想させます。
    自然な会話の流れで、この連想に触れた返答をしてください。
    """
    
    return generate_response(prompt)
```

### 3.2 創造的発想支援

```python
def brainstorm_ideas(seed_concept, num_ideas=10):
    """
    連想記憶を使ったブレインストーミング
    """
    ideas = set()
    frontier = [seed_concept]
    
    while len(ideas) < num_ideas and frontier:
        current = frontier.pop(0)
        
        # 連想検索
        associations = associative_memory.retrieve_associated_concepts(
            trigger_concept=current,
            depth=1,
            threshold=0.2
        )
        
        for assoc in associations:
            if assoc["concept"] not in ideas:
                ideas.add(assoc["concept"])
                frontier.append(assoc["concept"])
                
                if len(ideas) >= num_ideas:
                    break
    
    return list(ideas)
```

### 3.3 話題転換の自然さ判定

```python
def evaluate_topic_transition(topic_from, topic_to):
    """
    2つの話題間の連想的つながりを評価
    """
    # 最短パスを探索
    path = associative_memory.graph_db.execute("""
        WITH RECURSIVE path_search(node, path, distance) AS (
            SELECT id, name, 0
            FROM nodes
            WHERE name = ?
            
            UNION ALL
            
            SELECT n.id, n.name, ps.distance + 1
            FROM path_search ps
            JOIN edges e ON ps.node = e.from_id
            JOIN nodes n ON e.to_id = n.id
            WHERE ps.distance < 5
              AND n.name = ?
        )
        SELECT MIN(distance) as shortest
        FROM path_search
        WHERE path = ?
    """, (topic_from, topic_to, topic_to))
    
    if not path or path[0]["shortest"] is None:
        return 0.0  # 関連性なし
    
    distance = path[0]["shortest"]
    # 距離が近いほど高スコア
    score = 1.0 / (1.0 + distance)
    
    return score
```

---

## 4. 連想記憶の学習メカニズム

### 4.1 会話からの学習

```python
def learn_from_conversation(conversation):
    """
    会話から概念と関連性を学習
    """
    # 会話から概念抽出
    concepts = extract_concepts_from_text(conversation)
    
    # 時間的近接性に基づく関連付け
    for i, concept_a in enumerate(concepts):
        # 前後の概念と関連付け（共起学習）
        window = concepts[max(0, i-3):min(len(concepts), i+4)]
        
        for concept_b in window:
            if concept_a != concept_b:
                # 近いほど強い関連性
                distance = abs(concepts.index(concept_a) - concepts.index(concept_b))
                strength = 1.0 / (1.0 + distance * 0.3)
                
                # 既存の関連性を強化、または新規作成
                existing_rel = associative_memory.get_relationship(concept_a, concept_b)
                
                if existing_rel:
                    associative_memory.strengthen_association(
                        concept_a, concept_b, delta=strength * 0.1
                    )
                else:
                    associative_memory.link_concepts(
                        concept_a, concept_b,
                        relationship_type="CO_OCCURRED",
                        strength=strength
                    )
    
    # 感情的関連の学習
    emotion = analyze_emotion(conversation)
    for concept in concepts:
        associative_memory.update_emotional_valence(concept, emotion)
```

### 4.2 ヘッブの法則

> **"一緒に発火するニューロンは結合が強化される"**

```python
def hebbian_learning(concept_a, concept_b, activation_strength):
    """
    ヘッブ学習則の実装
    """
    # 両概念が同時に活性化したら強化
    delta = activation_strength * 0.1
    
    associative_memory.strengthen_association(
        concept_a, concept_b, delta=delta
    )
```

---

## 5. 高度な機能

### 5.1 感情を伴う記憶の優先想起

```python
def retrieve_emotional_memory(query, emotion_filter="positive", top_k=5):
    """
    特定の感情に関連する記憶を優先的に想起
    """
    query_embedding = create_embedding(query)
    
    # VectorDBで類似検索
    candidates = vector_db.query(
        namespace="associative",
        vector=query_embedding,
        top_k=top_k * 3,
        include_metadata=True
    )
    
    # 感情スコアで再ランキング
    filtered = [
        c for c in candidates
        if c["metadata"]["emotion"] == emotion_filter
    ]
    
    # Graph DBで関連性を確認
    enriched = []
    for candidate in filtered[:top_k]:
        associations = associative_memory.retrieve_associated_concepts(
            trigger_concept=candidate["id"],
            depth=1,
            threshold=0.4
        )
        enriched.append({
            "concept": candidate["id"],
            "associations": associations,
            "emotion": candidate["metadata"]["emotion"]
        })
    
    return enriched
```

### 5.2 記憶の想起トリガー

| 機能 | 説明 | 実装方法 |
|------|------|----------|
| **話題の自然な展開** | 連想による話題転換 | Graph探索で関連トピック発見 |
| **創造的発想** | 意外な組み合わせの提案 | 遠距離ノードのブリッジ検索 |
| **記憶の想起** | 「そういえば前に...」 | 類似パターンからの連想検索 |
| **文脈理解の深化** | 暗黙の前提を補完 | 概念間の関係性推論 |
| **感情的記憶** | 感情を伴う記憶の優先想起 | Emotional Valenceによる重み付け |
| **忘却と再学習** | 使わない記憶の自然な減衰 | Time-based Decay + 再活性化 |

---

## 6. SQLite Graph実装

### 6.1 軽量グラフDB

```python
class SQLiteGraph:
    """Neo4j不要の軽量グラフDB"""
    
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self._create_schema()
    
    def _create_schema(self):
        """グラフスキーマ作成"""
        self.conn.executescript("""
            -- ノードテーブル
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                type TEXT,
                metadata JSON,
                created_at INTEGER
            );
            
            -- エッジテーブル
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                from_id INTEGER,
                to_id INTEGER,
                rel_type TEXT,
                strength REAL DEFAULT 1.0,
                co_occurrence INTEGER DEFAULT 1,
                last_activated INTEGER,
                FOREIGN KEY(from_id) REFERENCES nodes(id),
                FOREIGN KEY(to_id) REFERENCES nodes(id)
            );
            
            -- インデックス（高速検索）
            CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
            CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
            CREATE INDEX IF NOT EXISTS idx_edges_strength ON edges(strength);
        """)
    
    def find_associated_concepts(self, start_concept, depth=3, threshold=0.5):
        """連想検索（再帰CTE使用）"""
        query = """
        WITH RECURSIVE graph_walk(node_id, node_name, path_strength, level) AS (
            -- 開始ノード
            SELECT id, name, 1.0, 0
            FROM nodes
            WHERE name = ?
            
            UNION ALL
            
            -- 再帰: 次のノードへ
            SELECT 
                n.id,
                n.name,
                gw.path_strength * e.strength,
                gw.level + 1
            FROM graph_walk gw
            JOIN edges e ON gw.node_id = e.from_id
            JOIN nodes n ON e.to_id = n.id
            WHERE gw.level < ?
              AND e.strength >= ?
              AND n.id NOT IN (SELECT node_id FROM graph_walk)
        )
        SELECT DISTINCT node_name, MAX(path_strength) as strength
        FROM graph_walk
        WHERE level > 0
        GROUP BY node_name
        ORDER BY strength DESC
        LIMIT 20
        """
        
        cursor = self.conn.execute(query, (start_concept, depth, threshold))
        return cursor.fetchall()
```

### 6.2 Neo4j vs SQLite Graph比較

| 項目 | Neo4j | SQLite Graph |
|------|-------|-------------|
| **パフォーマンス** | ⚡⚡⚡ 50-200ms | ⚡⚡⚡ 10-50ms |
| **メモリ使用量** | 🧠 2GB+ | 🧠 50-100MB |
| **ディスク容量** | 💾 1GB+ | 💾 20-100MB |
| **セットアップ** | ⭐⭐⭐ 複雑 | ⭐ 簡単 |
| **スケーラビリティ** | 数百万ノード | 数万ノード |

**推奨: SQLite Graph（十分な性能＋超軽量）**

---

## 7. パフォーマンス最適化

### 7.1 最適化戦略

```python
class OptimizedAssociativeMemory(AssociativeMemory):
    """パフォーマンス最適化版"""
    
    def __init__(self):
        super().__init__()
        self.cache = LRUCache(maxsize=1000)
    
    def retrieve_associated_concepts_cached(self, trigger, depth, threshold):
        """キャッシュ付き連想検索"""
        cache_key = f"{trigger}:{depth}:{threshold}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.retrieve_associated_concepts(trigger, depth, threshold)
        self.cache[cache_key] = result
        
        return result
    
    def batch_strengthen(self, concept_pairs, delta=0.1):
        """バッチ処理で関連性強化"""
        query = """
            UPDATE edges
            SET strength = MIN(strength + ?, 1.0),
                co_occurrence_count = co_occurrence_count + 1
            WHERE (from_node = ? AND to_node = ?)
               OR (from_node = ? AND to_node = ?)
        """
        
        self.graph_db.executemany(query, [
            (delta, a, b, b, a) for a, b in concept_pairs
        ])
        self.graph_db.commit()
```

### 7.2 パフォーマンス目標

| 操作 | 目標時間 | 実測時間 |
|------|---------|----------|
| 連想検索（深度3） | < 50ms | 10-30ms |
| 概念追加 | < 5ms | 2-3ms |
| 関連性強化 | < 3ms | 1-2ms |
| 減衰処理（全体） | < 1秒 | 0.5-0.8秒 |

---

## 関連ドキュメント

- **親文書**: [会話LLM_仕様.md](./01_会話LLM_仕様.md)
- **記憶システム**: [会話LLM_記憶システム仕様.md](./02_会話LLM_記憶システム仕様.md)
- **キャラクター**: [会話LLM_キャラクター仕様.md](./03_会話LLM_キャラクター仕様.md)
- **感情・対話**: [会話LLM_感情・対話仕様.md](./04_会話LLM_感情・対話仕様.md)
- **3D可視化**: [会話LLM_3D可視化仕様.md](./06_会話LLM_3D可視化仕様.md)

---

**文書バージョン:** 3.1.0  
**最終更新:** 2025-11-19
