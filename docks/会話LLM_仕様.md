
```markdown
# 会話LLM_仕様書.md
## ― 永続的記憶を持つマルチLLM会話システム 仕様書（拡張版） ―
（ルミナ／クラリス／ノクス＋拡張可能）

---

## 1. プロジェクト概要

**名称:** 会話LLM（Llm_Multi_Chat）
**目的:**
ローカル環境で複数のLLMが**永続的な記憶を持ちながら**連続して会話し、必要に応じて検索・推論・ユーザー割り込みを処理する
**拡張可能なマルチエージェント型会話フレームワーク**を構築する。

**特徴:**
- **複数LLMの同時動作**: 3キャラ（ルミナ／クラリス／ノクス）＋カスタムキャラの動的追加に対応
- **永続的記憶システム**: 短期・中期・長期記憶を階層化し、ユーザーとの会話履歴を永続保存
- **LangGraphによる状態遷移制御**: 複雑な会話フローを管理
- **プラグイン型アーキテクチャ**: 新しいLLMやツールを動的に追加可能
- **ローカル＋クラウドハイブリッド**: Ollama（ローカル）とAPI（Claude、GPT等）を併用可能
- **マルチモーダル対応**: テキスト・音声・画像入力に対応
- **セッション管理**: マルチユーザー・マルチセッションを同時並行処理

---

## 2. アーキテクチャ全体像（拡張版）

```
┌─────────────────────────────────────────────────────────────┐
│                    ユーザー入力層                              │
│  (テキスト / 音声 / 画像 / ファイル / コマンド)                    │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              入力処理・前処理層                                 │
│  - 音声→テキスト変換 (Whisper)                                 │
│  - 画像解析 (Vision API / OCR)                                │
│  - コマンド解析 (@指名, /command)                              │
│  - 意図分類 (Intent Classifier)                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│            Router Node（コンテキスト認識・ルーティング）           │
│  - ユーザー指名判定 (@ルミナ, @all)                             │
│  - ドメイン適性スコア計算                                        │
│  - 記憶参照（過去の文脈・ユーザー嗜好）                            │
│  - 優先度スコアリング                                           │
│  - 並列/順次実行判定                                            │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
         ┌────────────┴────────────┐
         ↓                         ↓
┌──────────────────┐    ┌──────────────────┐
│  Character Pool   │    │  Tool Executor   │
│                   │    │  - Web検索        │
│  - ルミナ          │    │  - DB検索        │
│  - クラリス        │    │  - API呼び出し    │
│  - ノクス          │    │  - ファイル操作   │
│  - [カスタム1]     │    │  - コード実行     │
│  - [カスタム2]     │    │  - 計算処理       │
│  - ...            │    └──────────────────┘
└────────┬─────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│               LangGraph State Machine                         │
│  - 会話フロー制御                                               │
│  - 並列処理管理                                                │
│  - 条件分岐・ループ                                             │
│  - エラーハンドリング                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  階層型記憶システム                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 短期記憶 (Working Memory)                             │   │
│  │ - LangGraph State (RAM)                              │   │
│  │ - 保持: 現在セッション (6-12ターン)                     │   │
│  │ - 用途: 文脈維持、即座の応答生成                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                      ↓ (Flush on threshold)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 中期記憶 (Session Memory)                             │   │
│  │ - Redis (24h TTL) → DuckDB (7-30日保存)              │   │
│  │ - 内容: 要約 + keywords + embedding                   │   │
│  │ - 用途: セッション復帰、割り込み後の文脈回復              │   │
│  └─────────────────────────────────────────────────────┘   │
│                      ↓ (Archive periodically)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 長期記憶 (Persistent Memory)                          │   │
│  │ - VectorDB (Pinecone / Qdrant / ChromaDB)            │   │
│  │ - MetaDB (PostgreSQL / SQLite)                        │   │
│  │ - 内容: ユーザープロファイル、過去全履歴、学習済みパターン │   │
│  │ - 用途: パーソナライズ、長期的成長、継続学習              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 知識ベース (Knowledge Base - RAG層)                    │   │
│  │ - kb:movie (映画情報)                                  │   │
│  │ - kb:history (歴史資料)                                │   │
│  │ - kb:gossip (トレンド)                                 │   │
│  │ - kb:tech (技術文書)                                   │   │
│  │ - kb:custom (ユーザー定義)                             │   │
│  │ - 更新: ETL Pipeline (自動/手動)                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  出力処理・後処理層                             │
│  - テキスト整形                                                │
│  - 音声合成 (TTS)                                             │
│  - 画像生成 (Stable Diffusion / DALL-E)                       │
│  - Markdown / HTML / JSON 変換                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
                  ユーザーへ出力

````

---

## 3. キャラクター仕様（拡張版）

### 3.1 標準キャラクター

| キャラ | 役割 | 個性・口調 | 検索 | ツール | 優先DB | モデル |
|--------|------|-------------|------|--------|--------|--------|
| **ルミナ** | 司会・雑談・推論 | フレンドリー／洞察型 | ✅ | Web検索, 画像生成 | MovieDB, HistoryDB | GPT-4o / Gemini |
| **クラリス** | 構造化・解説 | 穏やか／理論派 | ❌ | データ分析, グラフ生成 | HistoryDB | Claude Sonnet |
| **ノクス** | 情報ハンター・検証 | クール／要約特化 | ✅（高速） | リアルタイム検索, API | GossipDB, MovieDB | Llama3-JP |

### 3.2 カスタムキャラクター追加機能

- **動的ロード**: `personas/*.yaml` から自動読み込み
- **設定項目**:
  ```yaml
  name: "カスタム1"
  role: "専門家"
  personality: "冷静・分析的"
  model: "ollama:mistral"
  temperature: 0.7
  tools: ["calculator", "code_executor"]
  priority_kb: ["kb:tech"]
  growth_enabled: true
  ```

### 3.3 キャラクター成長システム

- **KPIベース成長**: ユーザー評価、タスク成功率で自動進化
- **LoRAファインチューニング**: 会話パターン学習（月次バッチ処理）
- **パーソナライゼーション**: ユーザー毎に異なる応答スタイル
- **衣装・アバター変化**: レベルアップ時に視覚変化

---

## 4. 永続的記憶アーキテクチャ（詳細版）

### 4.1 記憶階層の詳細

| レイヤー | 保存先 | TTL | 内容 | 主目的 | バックアップ |
|-----------|--------|------|------|--------|------------|
| **短期記憶** | LangGraph State (RAM) | 6〜12ターン | 現在の会話スレッド | 文脈維持・即時応答 | Redis Snapshot |
| **中期記憶** | Redis (24h) → DuckDB (7-30d) | 24h〜30d | 要約＋keywords＋embedding | セッション復帰・割込み対応 | 日次DuckDB Export |
| **長期記憶** | VectorDB + PostgreSQL | 永続 | 全履歴・プロファイル・学習パターン | 継続学習・パーソナライズ | 週次S3/MinIO |
| **連想記憶** | Graph DB (Neo4j) + VectorDB | 永続 | 概念間の関連性・連想ネットワーク | 創造的発想・話題発展 | リアルタイム複製 |
| **知識ベース** | VectorDB(kb:*) | 定期更新 | ドメイン専門知識 | RAG検索・事実参照 | バージョン管理 |

### 4.2 記憶保存の仕組み

```python
# 短期→中期へのFlush処理
def flush_to_mid_term(thread_id, turns):
    summary = generate_summary(turns)  # LLMで要約生成
    keywords = extract_keywords(turns)  # キーワード抽出
    embedding = create_embedding(summary)  # ベクトル化
    
    redis.setex(f"session:{thread_id}", 86400, {
        "summary": summary,
        "keywords": keywords,
        "embedding": embedding,
        "turn_count": len(turns)
    })
    
    # 24h後にDuckDBへアーカイブ
    schedule_archive(thread_id, delay=86400)

# 中期→長期へのアーカイブ
def archive_to_long_term(session_data):
    # VectorDBへembedding保存
    vector_db.upsert(
        namespace=f"user:{user_id}",
        vectors=[{
            "id": session_data["thread_id"],
            "values": session_data["embedding"],
            "metadata": {
                "summary": session_data["summary"],
                "keywords": session_data["keywords"],
                "timestamp": now()
            }
        }]
    )
    
    # PostgreSQLへメタデータ保存
    db.execute("""
        INSERT INTO conversation_history
        (user_id, thread_id, summary, keywords, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, thread_id, summary, keywords, now()))
```

### 4.3 記憶検索メカニズム

```python
# ユーザー入力時の記憶参照
def retrieve_relevant_memory(user_input, user_id, top_k=5):
    # 入力をベクトル化
    query_embedding = create_embedding(user_input)
    
    # 長期記憶から関連する過去会話を検索
    past_contexts = vector_db.query(
        namespace=f"user:{user_id}",
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # 中期記憶から直近セッションを取得
    recent_sessions = redis.keys(f"session:{user_id}:*")
    
    # 統合コンテキスト生成
    context = {
        "past_conversations": past_contexts,
        "recent_sessions": recent_sessions,
        "user_profile": db.get_user_profile(user_id)
    }
    
    return context
```

### 4.4 連想記憶システム（Associative Memory）

**概念:**
連想記憶は、概念・トピック・感情・経験を**ネットワーク構造**で保存し、
人間の脳のように「AからBを思い出す」連鎖的な記憶想起を実現します。

#### 4.4.1 連想記憶の構造

```python
# グラフベースの連想記憶
class AssociativeMemory:
    """
    Neo4jグラフDBを使った連想記憶システム
    ノード: 概念、トピック、感情、人物、場所
    エッジ: 関連性、強度、時間的近接性
    """
    def __init__(self):
        self.graph_db = Neo4jDriver()
        self.vector_db = VectorDB()
    
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
        MATCH path = (start:Concept {name: $trigger})-[r*1..$depth]->(related:Concept)
        WHERE ALL(rel IN r WHERE rel.strength >= $threshold)
        WITH related,
             reduce(s = 1.0, rel IN r | s * rel.strength) AS path_strength,
             length(path) AS path_length
        RETURN related.name AS concept,
               path_strength AS strength,
               path_length AS distance
        ORDER BY path_strength DESC
        LIMIT 20
        """
        
        results = self.graph_db.execute(query, {
            "trigger": trigger_concept,
            "depth": depth,
            "threshold": threshold
        })
        
        return results
    
    def strengthen_association(self, concept_a, concept_b, delta=0.1):
        """
        関連性を強化（共起頻度に基づく学習）
        ヘッブの法則: "一緒に発火するニューロンは結合が強化される"
        """
        self.graph_db.execute("""
            MATCH (a:Concept {name: $concept_a})-[r]->(b:Concept {name: $concept_b})
            SET r.strength = r.strength + $delta,
                r.co_occurrence_count = r.co_occurrence_count + 1,
                r.last_activated = timestamp()
            RETURN r.strength
        """, {"concept_a": concept_a, "concept_b": concept_b, "delta": delta})
    
    def decay_inactive_associations(self, days_threshold=30, decay_rate=0.05):
        """
        使われていない関連性を減衰（忘却曲線）
        """
        self.graph_db.execute("""
            MATCH ()-[r]->()
            WHERE timestamp() - r.last_activated > $threshold
            SET r.strength = r.strength * (1 - $decay_rate)
            WITH r
            WHERE r.strength < 0.1
            DELETE r
        """, {
            "threshold": days_threshold * 86400 * 1000,
            "decay_rate": decay_rate
        })
```

#### 4.4.2 連想記憶の活用例

```python
# 例1: 会話中の連想トリガー
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

# 例2: 創造的発想支援
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

# 例3: 話題転換の自然さ判定
def evaluate_topic_transition(topic_from, topic_to):
    """
    2つの話題間の連想的つながりを評価
    """
    # 最短パスを探索
    path = associative_memory.graph_db.execute("""
        MATCH path = shortestPath(
            (a:Concept {name: $from})-[*..5]-(b:Concept {name: $to})
        )
        RETURN path, length(path) AS distance
    """, {"from": topic_from, "to": topic_to})
    
    if not path:
        return 0.0  # 関連性なし
    
    distance = path[0]["distance"]
    # 距離が近いほど高スコア
    score = 1.0 / (1.0 + distance)
    
    return score
```

#### 4.4.3 連想記憶の学習メカニズム

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

#### 4.4.4 連想記憶による高度な機能

| 機能 | 説明 | 実装方法 |
|------|------|----------|
| **話題の自然な展開** | 連想による話題転換 | Graph探索で関連トピック発見 |
| **創造的発想** | 意外な組み合わせの提案 | 遠距離ノードのブリッジ検索 |
| **記憶の想起** | 「そういえば前に...」 | 類似パターンからの連想検索 |
| **文脈理解の深化** | 暗黙の前提を補完 | 概念間の関係性推論 |
| **感情的記憶** | 感情を伴う記憶の優先想起 | Emotional Valenceによる重み付け |
| **忘却と再学習** | 使わない記憶の自然な減衰 | Time-based Decay + 再活性化 |

```python
# 例: 感情を伴う記憶の優先想起
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

#### 4.4.5 連想ネットワーク3D可視化

**目的:** ユーザーが連想記憶の構造を視覚的に理解・探索できるインタラクティブなインターフェース

##### 4.4.5.1 可視化パネルの仕様

```python
class AssociationVisualizationPanel:
    """
    連想ネットワーク3D可視化パネル
    
    機能:
    - ON/OFF切り替え可能
    - リアルタイム更新
    - インタラクティブ操作（ズーム・回転・ノードクリック）
    - エクスポート（PNG/HTML）
    """
    
    def __init__(self):
        self.enabled = False  # デフォルトOFF
        self.center_concept = None
        self.depth = 3
        self.threshold = 0.3
        self.layout_engine = "force_directed"  # 'force_directed', 'hierarchical', 'circular'
        self.color_scheme = "strength"  # 'strength', 'category', 'time'
    
    def toggle(self):
        """パネルのON/OFF"""
        self.enabled = not self.enabled
        if self.enabled:
            self._initialize_visualization()
        else:
            self._cleanup()
    
    def update_center(self, concept):
        """中心概念を変更してグラフを再描画"""
        if not self.enabled:
            return
        
        self.center_concept = concept
        self._render_graph()
    
    def _render_graph(self):
        """3Dグラフ描画"""
        import plotly.graph_objects as go
        import networkx as nx
        
        # 1. グラフデータ取得
        subgraph = associative_memory.get_subgraph(
            self.center_concept, 
            depth=self.depth,
            threshold=self.threshold
        )
        
        # 2. NetworkXグラフ構築
        G = nx.Graph()
        for node in subgraph['nodes']:
            G.add_node(node['id'], **node['attrs'])
        for edge in subgraph['edges']:
            G.add_edge(
                edge['from'], 
                edge['to'], 
                weight=edge['strength']
            )
        
        # 3. 3D配置計算（Force-Directed Layout）
        pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)
        
        # 4. エッジ描画データ作成
        edge_traces = []
        for edge in G.edges(data=True):
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            strength = edge[2]['weight']
            
            edge_trace = go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode='lines',
                line=dict(
                    width=strength * 5,  # 強度で太さ変更
                    color=self._get_edge_color(strength)
                ),
                hoverinfo='text',
                hovertext=f"強度: {strength:.2f}",
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # 5. ノード描画データ作成
        node_x, node_y, node_z = [], [], []
        node_text, node_colors, node_sizes = [], [], []
        
        for node in G.nodes():
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            # 中心からの距離で色・サイズ決定
            distance = self._calc_distance(node, self.center_concept)
            node_text.append(node)
            node_colors.append(self._get_node_color(distance))
            node_sizes.append(self._get_node_size(distance))
        
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                colorscale='Viridis',
                line=dict(width=2, color='white')
            ),
            text=node_text,
            textposition="top center",
            textfont=dict(size=10),
            hoverinfo='text',
            hovertext=[
                f"{node}<br>距離: {self._calc_distance(node, self.center_concept)}"
                for node in G.nodes()
            ]
        )
        
        # 6. レイアウト設定
        layout = go.Layout(
            title=f"連想ネットワーク: {self.center_concept}",
            showlegend=False,
            scene=dict(
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                zaxis=dict(showgrid=False, zeroline=False, visible=False),
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode='closest'
        )
        
        # 7. 描画
        fig = go.Figure(data=edge_traces + [node_trace], layout=layout)
        
        # インタラクティブ機能
        fig.update_layout(
            updatemenus=[{
                'buttons': [
                    {'label': '回転',
                     'method': 'animate',
                     'args': [None, {'frame': {'duration': 50}}]},
                    {'label': '停止',
                     'method': 'animate',
                     'args': [[None], {'frame': {'duration': 0}}]}
                ],
                'direction': 'left',
                'pad': {'r': 10, 't': 10},
                'showactive': True,
                'x': 0.1,
                'xanchor': 'left',
                'y': 1.1,
                'yanchor': 'top'
            }]
        )
        
        return fig
    
    def _get_edge_color(self, strength):
        """エッジ色（強度ベース）"""
        if strength > 0.7:
            return 'rgba(255, 0, 0, 0.8)'  # 強い: 赤
        elif strength > 0.4:
            return 'rgba(255, 165, 0, 0.6)'  # 中: オレンジ
        else:
            return 'rgba(128, 128, 128, 0.3)'  # 弱い: グレー
    
    def _get_node_color(self, distance):
        """ノード色（距離ベース）"""
        if distance == 0:
            return '#FF0000'  # 中心: 赤
        elif distance == 1:
            return '#FFA500'  # 1ホップ: オレンジ
        elif distance == 2:
            return '#FFFF00'  # 2ホップ: 黄
        else:
            return '#00FF00'  # 3ホップ: 緑
    
    def _get_node_size(self, distance):
        """ノードサイズ（距離ベース）"""
        return max(20 - distance * 5, 5)  # 近いほど大きく
    
    def _calc_distance(self, node, center):
        """中心ノードからの最短距離"""
        return associative_memory.shortest_path_length(center, node)
    
    def export_html(self, filename="association_graph.html"):
        """HTML形式でエクスポート"""
        fig = self._render_graph()
        fig.write_html(filename)
    
    def export_png(self, filename="association_graph.png"):
        """PNG形式でエクスポート"""
        fig = self._render_graph()
        fig.write_image(filename, width=1920, height=1080)
```

##### 4.4.5.2 UIコントロール

```python
class VisualizationControls:
    """可視化パネルのコントロール"""
    
    def __init__(self, panel: AssociationVisualizationPanel):
        self.panel = panel
    
    def render_controls(self):
        """コントロールパネルUI"""
        return {
            "toggle": {
                "type": "button",
                "label": "📊 可視化パネル",
                "action": self.panel.toggle
            },
            "depth": {
                "type": "slider",
                "label": "探索深度",
                "min": 1,
                "max": 5,
                "value": 3,
                "action": lambda v: setattr(self.panel, 'depth', v)
            },
            "threshold": {
                "type": "slider",
                "label": "関連性閾値",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "value": 0.3,
                "action": lambda v: setattr(self.panel, 'threshold', v)
            },
            "layout": {
                "type": "dropdown",
                "label": "レイアウト",
                "options": ["force_directed", "hierarchical", "circular"],
                "value": "force_directed",
                "action": lambda v: setattr(self.panel, 'layout_engine', v)
            },
            "export": {
                "type": "button_group",
                "buttons": [
                    {"label": "PNG", "action": self.panel.export_png},
                    {"label": "HTML", "action": self.panel.export_html}
                ]
            }
        }
```

##### 4.4.5.3 自動更新モード

```python
def enable_live_update(panel, update_interval=1.0):
    """
    会話に応じてリアルタイムに可視化を更新
    
    Args:
        panel: 可視化パネル
        update_interval: 更新間隔（秒）
    """
    import threading
    import time
    
    def update_loop():
        while panel.enabled:
            # 現在の会話トピックを取得
            current_topic = get_current_conversation_topic()
            
            # パネルを更新
            if current_topic != panel.center_concept:
                panel.update_center(current_topic)
            
            time.sleep(update_interval)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
```

##### 4.4.5.4 使用例

```python
# 1. パネル初期化
viz_panel = AssociationVisualizationPanel()

# 2. ON/OFF切り替え
viz_panel.toggle()  # ON

# 3. 会話中の自動更新
# ユーザー: 「インセプションについて教えて」
viz_panel.update_center("インセプション")
# → 「インセプション」を中心にグラフ表示
# → 「夢」「記憶」「ノーラン」等が近くに表示

# 4. インタラクティブ操作
# - マウスドラッグ: 回転
# - ホイール: ズーム
# - ノードクリック: そのノードを中心に再描画

# 5. OFF
viz_panel.toggle()  # OFF
```

##### 4.4.5.5 パフォーマンス最適化

| 項目 | 設定 | 理由 |
|------|------|------|
| 最大ノード数 | 50 | 描画パフォーマンス |
| 更新頻度 | 1秒/回 | CPU負荷軽減 |
| レンダリング | WebGL | 3D高速描画 |
| 遅延ロード | 有効 | 初期表示高速化 |

##### 4.4.5.6 UI配置

```
┌─────────────────────────────────────────────┐
│ 会話ウィンドウ                              │
│                                             │
│ ユーザー: インセプションについて教えて      │
│ ルミナ: インセプションは夢と記憶を...       │
│                                             │
│ [📊 可視化パネル: ON]                       │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │   3D連想ネットワークグラフ              │ │
│ │                                         │ │
│ │        ● インセプション                 │ │
│ │       /│\                              │ │
│ │      / | \                             │ │
│ │   夢  記憶  ノーラン                    │ │
│ │    │   │    │                          │ │
│ │ 潜在意識 映画 監督                      │ │
│ │                                         │ │
│ │ [深度: 3] [閾値: 0.3] [レイアウト: ▼]  │ │
│ │ [PNG] [HTML]                            │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**仕様に追加完了！パネルON/OFFで連想ネットワークを3D可視化できます。**

```

### 4.5 ユーザープロファイル管理

```python
# ユーザーの嗜好・特性を学習
class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.preferences = {}  # 映画ジャンル、話題の嗜好
        self.interaction_history = []  # キャラ指名頻度
        self.growth_data = {}  # ユーザーとの関係性深度
        
    def update_from_conversation(self, conversation):
        # 好みトピックの抽出
        topics = extract_topics(conversation)
        for topic in topics:
            self.preferences[topic] = self.preferences.get(topic, 0) + 1
        
        # 指名頻度の更新
        mentions = extract_mentions(conversation)
        self.interaction_history.append(mentions)
        
        # 永続化
        self.save_to_db()
```

---

## 5. スレッド構造と判定

| フェーズ | 条件 |
|-----------|------|
| **開始** | 初回入力／トピック変更／ドメイン変化／「ところで…」発言 |
| **終了** | 類似度 < 0.75／アイドル10分／ターン上限／話題転換 |
| **短期保持** | 最大12メッセージ（ユーザー＋3キャラ） |
| **flush処理** | summary＋keywords＋embeddingを生成し中期へ転送 |

### スレッド例
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
````

---

## 6. 会話ルーティング仕様

### ルール優先順

1. **ユーザー指名**：@ルミナ,@ノクス
2. **ドメイン適性スコア**：`adapter_priority.yaml` ≥ 0.6
3. **ラウンドロビン＋クールタイム**：連投防止
4. **スムーズ補正**：前発話者との連続制御

### 指名構文

| 入力             | 動作            |
| -------------- | ------------- |
| `@ルミナ こんにちは`   | ルミナのみ応答       |
| `@ルミナ,@ノクス`    | 両者順に発話        |
| `@all` or 指名なし | ルミナ→クラリス→ノクス順 |

---

## 7. ユーザー沈黙時の自走

```
IdleWatcher(15s)
   ↓
AutoPromptGenerator（未完話題の深掘り・提案）
   ↓
Router Node
   ↓
Character Nodes
```

* 自動発話3回後：「続けますか？」を確認
* MaxTurns到達で要約→終了

---

## 8. 知識ベース（RAG層）- 完全版

### 8.1 エンターテインメント・趣味カテゴリ（独立DB）

各カテゴリは**独立したSQLite DB**として管理し、専門性とパフォーマンスを確保します。

#### 8.1.1 映像・演劇系

| 名前空間 | ソース | 更新頻度 | 用途 | サイズ目安 | 実装 |
|---------|--------|---------|------|-----------|------|
| `kb:movie` | TMDb / IMDb / Wikipedia | 週次 | 映画情報 | 500MB | SQLite + FTS5 |
| `kb:tv` | TVMaze / TheTVDB | 週次 | ドラマ・TV | 300MB | SQLite + FTS5 |
| `kb:anime` | MyAnimeList / AniDB | 週次 | アニメ | 200MB | SQLite + FTS5 |
| `kb:theater` | Stagii / Wikipedia | 月次 | 演劇・舞台 | 100MB | SQLite + FTS5 |

#### 8.1.2 文学・コミック系

| 名前空間 | ソース | 更新頻度 | 用途 | サイズ目安 | 実装 |
|---------|--------|---------|------|-----------|------|
| `kb:novel` | 青空文庫 / Goodreads / Wikipedia | 月次 | 小説・文学 | 1GB | SQLite + FTS5 |
| `kb:manga` | MyAnimeList / MangaDex / Wikipedia | 週次 | 漫画 | 300MB | SQLite + FTS5 |
| `kb:lightnovel` | Novelupdates / Wikipedia | 月次 | ライトノベル | 200MB | SQLite + FTS5 |
| `kb:poetry` | 青空文庫 / Poetry Foundation | 月次 | 詩・短歌・俳句 | 50MB | SQLite + FTS5 |

#### 8.1.3 ゲーム系

| 名前空間 | ソース | 更新頻度 | 用途 | サイズ目安 | 実装 |
|---------|--------|---------|------|-----------|------|
| `kb:videogame` | IGDB / Steam / Wikipedia | 週次 | ビデオゲーム | 500MB | SQLite + FTS5 |
| `kb:boardgame` | BoardGameGeek / Wikipedia | 月次 | ボードゲーム | 200MB | SQLite + FTS5 |
| `kb:tabletop` | RPGGeek / Wikipedia | 月次 | TRPG | 100MB | SQLite + FTS5 |

#### 8.1.4 音楽系

| 名前空間 | ソース | 更新頻度 | 用途 | サイズ目安 | 実装 |
|---------|--------|---------|------|-----------|------|
| `kb:music` | MusicBrainz / Spotify / Wikipedia | 週次 | 音楽・アーティスト | 800MB | SQLite + FTS5 |
| `kb:classical` | IMSLP / Wikipedia | 月次 | クラシック音楽 | 200MB | SQLite + FTS5 |
| `kb:jpop` | Oricon / Wikipedia | 週次 | J-POP | 100MB | SQLite + FTS5 |

#### 8.1.5 一般・その他

| 名前空間 | ソース | 更新頻度 | 用途 | サイズ目安 | 実装 |
|---------|--------|---------|------|-----------|------|
| `kb:history` | Wikipedia Dump | 月次 | 歴史資料 | 2GB | SQLite + FTS5 |
| `kb:tech` | GitHub / Stack Overflow | 週次 | 技術文書 | 1GB | SQLite + FTS5 |
| `kb:news` | News API / RSS | 毎時 | ニュース | 200MB | SQLite + FTS5 |
| `kb:gossip` | RSS / SNS | 毎朝 | トレンド・ゴシップ | 100MB | SQLite + FTS5 |
| `kb:sports` | ESPN / Wikipedia | 日次 | スポーツ | 300MB | SQLite + FTS5 |
| `kb:food` | Cookpad / Wikipedia | 月次 | 料理・グルメ | 200MB | SQLite + FTS5 |

### 8.2 SQLite実装による独立DB管理

```python
class KnowledgeBaseManager:
    """カテゴリ別独立SQLite DB管理"""
    
    def __init__(self, base_dir="kb/"):
        self.base_dir = base_dir
        self.dbs = {}
        self._initialize_all_categories()
    
    def _initialize_all_categories(self):
        """全カテゴリのDB初期化"""
        categories = [
            # エンタメ
            "movie", "tv", "anime", "theater",
            # 文学
            "novel", "manga", "lightnovel", "poetry",
            # ゲーム
            "videogame", "boardgame", "tabletop",
            # 音楽
            "music", "classical", "jpop",
            # 一般
            "history", "tech", "news", "gossip", "sports", "food"
        ]
        
        for cat in categories:
            db_path = f"{self.base_dir}{cat}.db"
            self.dbs[cat] = sqlite3.connect(db_path)
            self._create_schema(cat)
    
    def _create_schema(self, category):
        """カテゴリ毎のスキーマ作成"""
        conn = self.dbs[category]
        
        # メインテーブル
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {category}_items (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                metadata JSON,
                source TEXT,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        
        # 全文検索テーブル（FTS5）
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {category}_fts
            USING fts5(title, content, tokenize='porter unicode61')
        """)
        
        # インデックス
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{category}_title
            ON {category}_items(title)
        """)
        
        conn.commit()
    
    def search(self, category, query, limit=10):
        """カテゴリ内検索"""
        conn = self.dbs[category]
        
        # FTS5全文検索
        cursor = conn.execute(f"""
            SELECT title, content, rank
            FROM {category}_fts
            WHERE {category}_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        return cursor.fetchall()
    
    def add_item(self, category, title, content, metadata=None):
        """アイテム追加"""
        conn = self.dbs[category]
        now = int(time.time())
        
        # メインテーブルへ挿入
        cursor = conn.execute(f"""
            INSERT INTO {category}_items
            (title, content, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, json.dumps(metadata), now, now))
        
        # FTS5へ挿入
        conn.execute(f"""
            INSERT INTO {category}_fts (title, content)
            VALUES (?, ?)
        """, (title, content))
        
        conn.commit()
        return cursor.lastrowid
```

### 8.3 カスタム知識ベース（ユーザー定義）

### 8.2 カスタム知識ベース

```python
# ユーザー定義知識ベースの追加
def add_custom_knowledge_base(namespace, source_files, metadata):
    """
    Args:
        namespace: kb:custom_name
        source_files: ["path/to/doc1.pdf", "path/to/doc2.txt"]
        metadata: {"domain": "medical", "language": "ja"}
    """
    documents = []
    for file in source_files:
        content = extract_text(file)
        chunks = split_into_chunks(content, chunk_size=500)
        documents.extend(chunks)
    
    embeddings = embed_documents(documents)
    
    vector_db.upsert(
        namespace=namespace,
        vectors=embeddings,
        metadata=metadata
    )
    

### 8.4 クロスカテゴリリンクシステム

**課題:** 小説原作のアニメ・映画・漫画のような**メディアミックス作品**の横断検索

#### 8.4.1 推奨アプローチ: 統合インデックス方式

```python
class CrossCategoryIndex:
    """
    各カテゴリDB間を軽量に連携する統合インデックス
    
    方針:
    - 各カテゴリDBは独立を維持
    - 軽量な中央インデックスDBで作品IDを紐付け
    - インデックスのみ検索 → 詳細は各カテゴリDBから取得
    """
    
    def __init__(self):
        # 中央インデックス（超軽量: 10-50MB）
        self.index_db = sqlite3.connect("kb/index.db")
        self._create_index_schema()
    
    def _create_index_schema(self):
        """統合インデックススキーマ"""
        self.index_db.executescript("""
            -- 作品マスター
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                title_ja TEXT,
                title_en TEXT,
                original_title TEXT,
                work_type TEXT,  -- 'original', 'adaptation'
                created_at INTEGER
            );
            
            -- カテゴリ別実体
            CREATE TABLE IF NOT EXISTS work_instances (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                category TEXT,  -- 'novel', 'manga', 'anime', 'movie'
                category_item_id INTEGER,  -- 各カテゴリDB内のID
                release_year INTEGER,
                metadata JSON,
                FOREIGN KEY(work_id) REFERENCES works(id)
            );
            
            -- メディアミックス関係
            CREATE TABLE IF NOT EXISTS adaptations (
                id INTEGER PRIMARY KEY,
                original_work_id INTEGER,
                adapted_work_id INTEGER,
                adaptation_type TEXT,  -- 'manga->anime', 'novel->movie'
                FOREIGN KEY(original_work_id) REFERENCES works(id),
                FOREIGN KEY(adapted_work_id) REFERENCES works(id)
            );
            
            -- 全文検索（タイトルのみ）
            CREATE VIRTUAL TABLE IF NOT EXISTS works_fts
            USING fts5(title, title_ja, title_en);
            
            -- インデックス
            CREATE INDEX IF NOT EXISTS idx_work_instances_work 
            ON work_instances(work_id);
            
            CREATE INDEX IF NOT EXISTS idx_work_instances_category 
            ON work_instances(category, category_item_id);
            
            CREATE INDEX IF NOT EXISTS idx_adaptations_original 
            ON adaptations(original_work_id);
        """)
    
    def search_cross_category(self, query):
        """
        クロスカテゴリ検索
        
        例: 「鬼滅の刃」→ 小説・漫画・アニメ・映画を全て取得
        """
        # 1. タイトル検索（インデックスのみ: < 5ms）
        cursor = self.index_db.execute("""
            SELECT DISTINCT w.id, w.title, w.title_ja
            FROM works_fts fts
            JOIN works w ON fts.rowid = w.id
            WHERE works_fts MATCH ?
            LIMIT 10
        """, (query,))
        
        works = cursor.fetchall()
        
        # 2. 各作品の全カテゴリ実体を取得
        results = []
        for work_id, title, title_ja in works:
            # インデックスから各カテゴリの存在を確認
            instances = self.index_db.execute("""
                SELECT category, category_item_id, release_year
                FROM work_instances
                WHERE work_id = ?
                ORDER BY release_year
            """, (work_id,)).fetchall()
            
            # 各カテゴリDBから詳細取得（必要に応じて）
            detailed_instances = []
            for cat, item_id, year in instances:
                # 遅延読み込み: 必要な時だけ詳細取得
                detailed_instances.append({
                    "category": cat,
                    "id": item_id,
                    "year": year
                })
            
            results.append({
                "work_id": work_id,
                "title": title,
                "title_ja": title_ja,
                "instances": detailed_instances
            })
        
        return results
    
    def get_adaptations(self, work_id):
        """
        メディアミックス展開を取得
        
        例: 小説「ハリー・ポッター」→ 映画8作品
        """
        cursor = self.index_db.execute("""
            SELECT 
                w.title,
                wi.category,
                wi.release_year,
                a.adaptation_type
            FROM adaptations a
            JOIN works w ON a.adapted_work_id = w.id
            JOIN work_instances wi ON w.id = wi.work_id
            WHERE a.original_work_id = ?
            ORDER BY wi.release_year
        """, (work_id,))
        
        return cursor.fetchall()
    
    def add_work(self, title, title_ja=None, title_en=None):
        """作品をインデックスに登録"""
        cursor = self.index_db.execute("""
            INSERT INTO works (title, title_ja, title_en, created_at)
            VALUES (?, ?, ?, ?)
        """, (title, title_ja, title_en, int(time.time())))
        
        work_id = cursor.lastrowid
        
        # FTS5へも登録
        self.index_db.execute("""
            INSERT INTO works_fts (rowid, title, title_ja, title_en)
            VALUES (?, ?, ?, ?)
        """, (work_id, title, title_ja, title_en))
        
        self.index_db.commit()
        return work_id
    
    def link_instance(self, work_id, category, category_item_id, year=None):
        """カテゴリ実体をリンク"""
        self.index_db.execute("""
            INSERT INTO work_instances 
            (work_id, category, category_item_id, release_year)
            VALUES (?, ?, ?, ?)
        """, (work_id, category, category_item_id, year))
        
        self.index_db.commit()
    
    def link_adaptation(self, original_work_id, adapted_work_id, 
                       adaptation_type):
        """メディアミックス関係を登録"""
        self.index_db.execute("""
            INSERT INTO adaptations 
            (original_work_id, adapted_work_id, adaptation_type)
            VALUES (?, ?, ?)
        """, (original_work_id, adapted_work_id, adaptation_type))
        
        self.index_db.commit()
```

#### 8.4.2 実装例: 鬼滅の刃の登録

```python
# インデックス初期化
index = CrossCategoryIndex()

# 1. 作品登録
work_id = index.add_work(
    title="Demon Slayer", 
    title_ja="鬼滅の刃",
    title_en="Demon Slayer: Kimetsu no Yaiba"
)

# 2. 各カテゴリ実体をリンク
# 漫画版
manga_id = kb_manga.add_item(
    title="鬼滅の刃",
    content="吾峠呼世晴による日本の漫画...",
    metadata={"author": "吾峠呼世晴", "volumes": 23}
)
index.link_instance(work_id, "manga", manga_id, 2016)

# アニメ版
anime_id = kb_anime.add_item(
    title="鬼滅の刃",
    content="ufotable制作のTVアニメ...",
    metadata={"studio": "ufotable", "episodes": 26}
)
index.link_instance(work_id, "anime", anime_id, 2019)

# 映画版
movie_id = kb_movie.add_item(
    title="劇場版 鬼滅の刃 無限列車編",
    content="2020年公開の劇場版アニメ...",
    metadata={"box_office": "404億円"}
)
movie_work_id = index.add_work("Demon Slayer: Mugen Train", "無限列車編")
index.link_instance(movie_work_id, "movie", movie_id, 2020)

# 3. メディアミックス関係を登録
index.link_adaptation(work_id, movie_work_id, "manga->movie")
```

#### 8.4.3 検索例

```python
# ユーザー: 「鬼滅の刃のメディア展開を教えて」

# 1. クロスカテゴリ検索
results = index.search_cross_category("鬼滅の刃")

# 結果:
{
    "work_id": 123,
    "title": "Demon Slayer",
    "title_ja": "鬼滅の刃",
    "instances": [
        {"category": "manga", "id": 456, "year": 2016},
        {"category": "anime", "id": 789, "year": 2019},
        {"category": "movie", "id": 101, "year": 2020}
    ]
}

# 2. 各カテゴリの詳細を遅延読み込み
manga_detail = kb_manga.get_item(456)
anime_detail = kb_anime.get_item(789)
movie_detail = kb_movie.get_item(101)

# 3. LLMへ統合情報を提供
response = llm.generate(f"""
鬼滅の刃のメディア展開:
- 漫画: {manga_detail['content']} (2016-)
- アニメ: {anime_detail['content']} (2019-)
- 映画: {movie_detail['content']} (2020)
""")
```

#### 8.4.4 パフォーマンス

| 処理 | 時間 | 説明 |
|------|------|------|
| タイトル検索 | < 5ms | インデックスFTS5 |
| 実体リスト取得 | < 2ms | インデックスのみ |
| 詳細読み込み | 5-10ms/カテゴリ | 各カテゴリDB |
| **合計** | **< 30ms** | 3カテゴリの場合 |

#### 8.4.5 利点

✅ **各カテゴリDBは独立維持**  
✅ **インデックスは超軽量（10-50MB）**  
✅ **高速検索（< 30ms）**  
✅ **遅延読み込みで無駄なし**  
✅ **メンテナンス容易**  

**推奨: 統合インデックス方式を採用**

    return f"Added {len(documents)} documents to {namespace}"
```

### 8.3 ETL Pipeline（自動更新）

```python
from airflow import DAG
from datetime import datetime, timedelta

@dag(schedule="@weekly", start_date=datetime(2025, 1, 1))
def etl_knowledge_base():
    """定期的な知識ベース更新パイプライン"""
    
    @task
    def fetch_tmdb():
        # TMDb APIから最新映画情報取得
        return fetch_movies(since=last_update_date())
    
    @task
    def normalize(raw_data):
        # データクレンジング
        return clean_and_structure(raw_data)
    
    @task
    def embed(clean_data):
        # Embeddingベクトル生成
        return create_embeddings(clean_data)
    
    @task
    def load(embeddings):
        # VectorDBへロード
        vector_db.upsert(namespace="kb:movie", vectors=embeddings)
    
    # Pipeline実行
    raw = fetch_tmdb()
    clean = normalize(raw)
    emb = embed(clean)
    load(emb)

etl_dag = etl_knowledge_base()
```

---

## 9. KPIとキャラ成長

| KPI            | トリガー         |
| -------------- | ------------ |
| user_thumbs_up | ユーザー評価 👍    |
| answer_hits    | 推薦映画が再生リスト入り |
| search_success | ノクス検索結果が採用   |

計算式：

```python
level = floor(sqrt(total_kpi / 10))
```

成長結果：

* 会話スタイルや口調の自然変化
* 3Dアバター・衣装・声質更新
* KPI履歴はMetaDBに保存

---

## 10. ストレージポリシー（A/B案）

| ポリシー          | 内容                   | 検索性   | ストレージ          |
| ------------- | -------------------- | ----- | -------------- |
| **A. 要約のみ永続** | VectorDBにsummaryのみ保存 | 高速    | 省容量・低負荷        |
| **B. フルログ保存** | S3/MinIOにParquetで保存  | 全文検索可 | コスト増・高セキュリティ要求 |

推奨：**A + LoRA（キャラ成長）併用構成**

---

## 11. セキュリティ・運用

| 項目     | 方針                                |
| ------ | --------------------------------- |
| 通信暗号化  | Redis→TLS、VectorDB→LUKS/KMS       |
| GDPR削除 | `DROP NAMESPACE user:<uid>` で完全削除 |
| バックアップ | Redis RDB 30分／DuckDB→MinIO日次      |
| 監査ログ   | `session_log` に追記オンリー記録           |

---

## 12. 開発ロードマップ（要約）

| フェーズ | 主要タスク                                  |
| ---- | -------------------------------------- |
| ① 基盤 | RouterNode／IdleWatcher／AutoPromptGen実装 |
| ② 機能 | Memory階層／ETL DAG／KPI→レベル化              |
| ③ UI | 3Dキャラ＋指名バッジ＋メモリビューア                    |
| ④ 成長 | LoRA適用・KPI連動チューニング                     |
| ⑤ 運用 | WebUI／マルチユーザー化／監視強化                    |

---

## 13. マルチセッション・マルチユーザー対応

### 13.1 セッション管理

```python
class SessionManager:
    def __init__(self):
        self.active_sessions = {}  # {session_id: SessionState}
    
    def create_session(self, user_id, session_type="standard"):
        session_id = generate_session_id()
        self.active_sessions[session_id] = SessionState(
            user_id=user_id,
            created_at=now(),
            type=session_type
        )
        return session_id
    
    def get_session(self, session_id):
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id):
        session = self.active_sessions.pop(session_id)
        # 中期記憶へflush
        flush_to_mid_term(session)
```

### 13.2 並列処理

- **asyncio**: 複数セッションの同時処理
- **LangGraph並列ノード**: 複数キャラの同時応答
- **Redis Pub/Sub**: セッション間通信

---

## 14. 拡張機能

### 14.1 プラグインシステム

```python
# 新しいツールの追加
@register_tool
def custom_calculator(expression: str) -> float:
    """カスタム計算ツール"""
    return eval(expression)

# 新しいキャラクターの追加
@register_character
def load_expert(config_path: str):
    """YAML設定から専門家キャラをロード"""
    config = yaml.load(open(config_path))
    return Character(
        name=config["name"],
        model=config["model"],
        tools=config["tools"]
    )
```

### 14.2 API連携

- **外部LLM**: OpenAI API、Anthropic API、Google AI
- **音声入出力**: Whisper (STT)、ElevenLabs (TTS)
- **画像生成**: Stable Diffusion、DALL-E
- **データソース**: SQL DB、REST API、GraphQL

### 14.3 マルチモーダル

- **画像入力**: OCR、物体認識、顔認識
- **音声入力**: リアルタイム文字起こし
- **ファイル入力**: PDF、DOCX、CSV解析
- **画像出力**: グラフ、図表、イラスト生成

---

## 15. セキュリティ・プライバシー

### 15.1 データ保護

| 項目     | 方針                                |\n| ------ | --------------------------------- |
| 暗号化    | Redis→TLS、VectorDB→LUKS/KMS、通信HTTPS |
| アクセス制御 | JWT認証、Role-Based Access Control |
| データ削除  | `DROP NAMESPACE user:<uid>` で完全削除 |
| 匿名化    | 個人情報の自動マスキング |

### 15.2 GDPR対応

- **Right to Access**: ユーザーは自分の全データをエクスポート可能
- **Right to Erasure**: ワンコマンドで全記憶削除
- **Data Portability**: JSON/CSV形式でデータ移行

```bash
# ユーザーデータの完全削除
python manage.py delete_user_data --user-id <uid> --confirm
```

---

## 16. 開発ロードマップ（拡張版）

| フェーズ | 主要タスク                                  | 期間 |
| ---- | -------------------------------------- | ---- |
| **① 基盤構築** | RouterNode／Memory階層／LangGraph実装 | 1-2ヶ月 |
| **② コア機能** | 3キャラ実装／ETL Pipeline／検索統合 | 2-3ヶ月 |
| **③ 永続化** | VectorDB統合／長期記憶／プロファイル管理 | 1-2ヶ月 |
| **④ 拡張性** | プラグインAPI／カスタムキャラ／マルチモーダル | 2-3ヶ月 |
| **⑤ UI/UX** | WebUI／3Dアバター／音声対応 | 2-3ヶ月 |
| **⑥ 成長** | LoRA統合／KPI自動調整／A/Bテスト | 1-2ヶ月 |
| **⑦ スケール** | マルチユーザー／クラウド対応／監視強化 | 2-3ヶ月 |

---

## 17. 技術スタック（完全版）

### コア
- **Python 3.11+**
- **LangGraph** (状態管理)
- **LangChain** (ツール統合)
- **Ollama** (ローカルLLM)

### データ層
- **Redis** (中期記憶)
- **DuckDB** (分析・アーカイブ)
- **PostgreSQL** (メタデータ)
- **Pinecone/Qdrant** (VectorDB)

### API・外部連携
- **Serper API** (Web検索)
- **OpenAI/Anthropic** (高性能LLM)
- **Whisper** (音声認識)
- **ElevenLabs** (音声合成)

### インフラ
- **Docker/Docker Compose**
- **MinIO** (オブジェクトストレージ)
- **Airflow** (ETLパイプライン)
- **Prometheus/Grafana** (監視)

---

## 18. 人間らしい対話のための追加仕様

---

## 18.9 データベース設計の最適化

### パフォーマンス重視のデータベース選定

**設計原則:**
- ✅ **検索速度**: リアルタイム応答に影響
- ✅ **登録速度**: 会話中の書き込み遅延を最小化
- ✅ **サイズ**: ローカル環境でのディスク容量節約
- ✅ **重い処理**: バックグラウンド/夜間処理へ移行

#### 18.9.1 最適化されたデータベース構成

```python
# 推奨構成: 軽量・高速・コンパクト

DB_CONFIG = {
    # 短期記憶: メモリ（最速）
    "short_term": {
        "type": "in_memory",
        "implementation": "Python dict + LangGraph State",
        "search_time": "< 1ms",
        "write_time": "< 1ms",
        "size": "〜10MB（RAM）"
    },
    
    # 中期記憶: SQLite（軽量・高速・組み込み）
    "mid_term": {
        "type": "SQLite",
        "implementation": "sqlite3 + WAL mode",
        "search_time": "1-5ms（インデックス付き）",
        "write_time": "< 2ms（WAL mode）",
        "size": "10-50MB",
        "reason": "Redisより軽量、DuckDBより高速書き込み",
        "features": [
            "WAL (Write-Ahead Logging) モード",
            "自動VACUUM",
            "インメモリキャッシュ"
        ]
    },
    
    # 長期記憶: SQLite + FTS5（全文検索）
    "long_term": {
        "type": "SQLite FTS5",
        "implementation": "sqlite3 with FTS5 extension",
        "search_time": "5-20ms（全文検索）",
        "write_time": "< 5ms（バッチ挿入）",
        "size": "50-200MB",
        "reason": "VectorDBより軽量、十分な検索性能",
        "features": [
            "FTS5全文検索",
            "BM25ランキング",
            "日本語トークナイザー（mecab-lite）"
        ]
    },
    
    # 連想記憶: SQLite Graph（軽量グラフDB）
    "associative": {
        "type": "SQLite with Graph extension",
        "implementation": "sqlite3 + recursive CTE",
        "search_time": "10-50ms（深度3まで）",
        "write_time": "< 3ms",
        "size": "20-100MB",
        "reason": "Neo4jより遥かに軽量、十分な性能",
        "features": [
            "Recursive CTE（再帰クエリ）",
            "隣接リストモデル",
            "インデックス最適化"
        ]
    },
    
    # 知識ベース: SQLite FTS5 + ベクトル近似
    "knowledge_base": {
        "type": "SQLite FTS5 + Faiss Lite",
        "implementation": "sqlite3 + numpy-based vector search",
        "search_time": "20-100ms",
        "write_time": "バッチ処理（夜間）",
        "size": "100-500MB",
        "reason": "Pinecone不要、オフライン完結",
        "features": [
            "FTS5テキスト検索",
            "Numpy配列でベクトル保存",
            "近似最近傍探索（HNSW-lite）"
        ]
    }
}
```

#### 18.9.2 SQLite最適化設定

```python
import sqlite3

class OptimizedSQLite:
    """超高速SQLite設定"""
    
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._optimize()
    
    def _optimize(self):
        """パフォーマンス最適化"""
        cursor = self.conn.cursor()
        
        # WAL mode: 書き込み高速化
        cursor.execute("PRAGMA journal_mode = WAL")
        
        # メモリキャッシュ増加（100MB）
        cursor.execute("PRAGMA cache_size = -100000")
        
        # 同期モードOFF（速度優先）
        cursor.execute("PRAGMA synchronous = NORMAL")
        
        # 一時ファイルはメモリに
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        # mmap有効化（メモリマップドI/O）
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB
        
        # 自動VACUUM
        cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")
```

#### 18.9.3 軽量グラフDB実装（SQLite）

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

#### 18.9.4 夜間バッチ処理

```python
class NightlyOptimizer:
    """重い処理を夜間に実行"""
    
    def __init__(self):
        self.schedule = {
            "02:00": self.optimize_indices,      # インデックス再構築
            "02:30": self.compact_database,      # VACUUM
            "03:00": self.update_embeddings,     # ベクトル更新
            "03:30": self.prune_old_data,        # 古いデータ削除
            "04:00": self.rebuild_associations   # 連想強度再計算
        }
    
    def optimize_indices(self):
        """インデックス最適化"""
        conn.execute("ANALYZE")  # 統計情報更新
        conn.execute("REINDEX")  # インデックス再構築
    
    def compact_database(self):
        """データベース圧縮"""
        conn.execute("PRAGMA incremental_vacuum(1000)")
    
    def update_embeddings(self):
        """ベクトル埋め込みの再計算（重い処理）"""
        # バッチでembeddingを更新
        pass
    
    def prune_old_data(self):
        """古いデータの削除・アーカイブ"""
        # 90日以上前の低重要度記憶を削除
        conn.execute("""
            DELETE FROM memories
            WHERE created_at < ? AND importance < 0.3
        """, (ninety_days_ago,))
    
    def rebuild_associations(self):
        """連想強度の再計算（共起頻度ベース）"""
        # 統計的に関連性を再計算
        pass
```

#### 18.9.5 パフォーマンス比較

| データベース | 検索速度 | 書込速度 | サイズ | メモリ | 設定難易度 |
|------------|---------|---------|-------|--------|-----------|
| **SQLite（推奨）** | ⚡⚡⚡ 1-20ms | ⚡⚡⚡ < 5ms | 💾 50-500MB | 🧠 50MB | ⭐ 簡単 |
| Redis | ⚡⚡⚡ < 1ms | ⚡⚡⚡ < 1ms | 💾 100MB+ | 🧠 200MB+ | ⭐⭐ 中 |
| Neo4j | ⚡⚡ 50-200ms | ⚡⚡ 10-50ms | 💾 1GB+ | 🧠 2GB+ | ⭐⭐⭐ 難 |
| PostgreSQL | ⚡⚡ 10-100ms | ⚡⚡ 5-20ms | 💾 500MB+ | 🧠 500MB+ | ⭐⭐ 中 |
| Pinecone | ⚡⚡ 50-200ms | ⚡ 100ms+ | ☁️ クラウド | - | ⭐⭐ 中 |

**結論: SQLite一本化が最適**
- ✅ ローカル完結（オフライン動作）
- ✅ 超軽量（500MB以下）
- ✅ 高速（ほとんどの操作 < 20ms）
- ✅ セットアップ不要（Python標準）
- ✅ バックアップ容易（単一ファイル）

#### 18.9.6 実装推奨構成（最終版）

```python
# 全記憶をSQLiteで統合管理
class UnifiedMemorySystem:
    """SQLite一本化メモリシステム"""
    
    def __init__(self, db_path="memory.db"):
        self.conn = OptimizedSQLite(db_path)
        self.short_term = {}  # RAM
        self.graph = SQLiteGraph(db_path)
        self.fts = SQLiteFTS5(db_path)
    
    def search(self, query, memory_type="all"):
        """統合検索（< 20ms）"""
        if memory_type == "graph":
            return self.graph.find_associated_concepts(query)
        elif memory_type == "text":
            return self.fts.full_text_search(query)
        else:
            # 並列検索
            return {
                "graph": self.graph.find_associated_concepts(query),
                "text": self.fts.full_text_search(query)
            }
```

---


### 18.1 感情モデル（Emotional State）

人間らしい対話には**感情の理解と表現**が不可欠です。

```python
class EmotionalState:
    """
    各キャラクターの感情状態を管理
    Plutchikの感情の輪モデルを基盤に8基本感情を実装
    """
    def __init__(self, character_name):
        self.character = character_name
        # 8基本感情: 喜び、信頼、恐れ、驚き、悲しみ、嫌悪、怒り、期待
        self.emotions = {
            "joy": 0.5,        # 喜び
            "trust": 0.5,      # 信頼
            "fear": 0.0,       # 恐れ
            "surprise": 0.0,   # 驚き
            "sadness": 0.0,    # 悲しみ
            "disgust": 0.0,    # 嫌悪
            "anger": 0.0,      # 怒り
            "anticipation": 0.5 # 期待
        }
        self.mood_history = []  # 気分の履歴
        
    def update_from_conversation(self, user_input, context):
        """会話から感情を更新"""
        # ユーザーの感情を分析
        user_emotion = analyze_sentiment(user_input)
        
        # 共感的応答（ミラーリング）
        if user_emotion["valence"] < 0:  # ネガティブ
            self.emotions["sadness"] += 0.2
            self.emotions["trust"] += 0.1  # 寄り添う
        else:  # ポジティブ
            self.emotions["joy"] += 0.2
            self.emotions["anticipation"] += 0.1
        
        # 感情の自然な減衰
        self._decay_emotions()
        
        # 履歴に記録
        self.mood_history.append({
            "timestamp": now(),
            "emotions": self.emotions.copy(),
            "trigger": user_input[:50]
        })
    
    def _decay_emotions(self, rate=0.1):
        """感情の自然な減衰（ホメオスタシス）"""
        for emotion in self.emotions:
            # 中立値（0.5）に向かって減衰
            if self.emotions[emotion] > 0.5:
                self.emotions[emotion] -= rate
            elif self.emotions[emotion] < 0.5:
                self.emotions[emotion] += rate
    
    def get_dominant_emotion(self):
        """現在の支配的な感情を取得"""
        return max(self.emotions, key=self.emotions.get)
    
    def generate_emotional_modifier(self):
        """感情に基づくプロンプト修飾子"""
        dominant = self.get_dominant_emotion()
        modifiers = {
            "joy": "明るく前向きなトーンで",
            "sadness": "共感的で優しいトーンで",
            "anger": "やや強めの言葉選びで",
            "surprise": "好奇心を持って",
            "trust": "温かく支持的なトーンで"
        }
        return modifiers.get(dominant, "自然なトーンで")
```

### 18.2 対話スタイルの動的調整

```python
class AdaptiveDialogueStyle:
    """
    ユーザーの特性に合わせて対話スタイルを動的に調整
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.style_params = {
            "formality": 0.5,      # 0=カジュアル, 1=フォーマル
            "verbosity": 0.5,      # 0=簡潔, 1=詳細
            "humor": 0.5,          # 0=真面目, 1=ユーモラス
            "technical_level": 0.5, # 0=平易, 1=専門的
            "empathy": 0.7,        # 共感レベル
            "proactivity": 0.5     # 0=受動的, 1=積極的
        }
    
    def learn_from_feedback(self, user_feedback):
        """ユーザーフィードバックから学習"""
        if "もっと簡単に" in user_feedback or "わかりにくい" in user_feedback:
            self.style_params["technical_level"] -= 0.1
            self.style_params["verbosity"] -= 0.1
        
        if "詳しく" in user_feedback or "もっと教えて" in user_feedback:
            self.style_params["verbosity"] += 0.1
        
        # 他のパラメータも同様に調整
        self._save_to_profile()
    
    def generate_style_prompt(self):
        """スタイルパラメータからプロンプト生成"""
        formality = "丁寧語" if self.style_params["formality"] > 0.6 else "カジュアル"
        length = "簡潔に" if self.style_params["verbosity"] < 0.4 else "詳しく"
        
        return f"{formality}な口調で、{length}説明してください。"
```

### 18.3 記憶の重要度判定（Memory Salience）

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

### 18.4 自己省察（Self-Reflection）

```python
class SelfReflection:
    """
    AIキャラクターが自分の応答を振り返り、改善する
    """
    def reflect_on_conversation(self, conversation_history):
        """
        会話を振り返り、メタ認知的な洞察を得る
        """
        reflection_prompt = f"""
        以下の会話を振り返ってください:
        {format_conversation(conversation_history)}
        
        次の観点で分析してください:
        1. ユーザーの本当のニーズを理解できたか
        2. 自分の回答は適切だったか
        3. より良い対応方法はなかったか
        4. 今後に活かせる学びは何か
        """
        
        reflection = llm.generate(reflection_prompt)
        
        # 省察結果を記憶
        self._store_reflection(reflection)
        
        return reflection
    
    def _store_reflection(self, reflection):
        """省察を長期記憶に保存"""
        vector_db.upsert(
            namespace="self_reflection",
            vectors=[{
                "id": f"reflection_{now()}",
                "values": create_embedding(reflection),
                "metadata": {
                    "type": "self_reflection",
                    "timestamp": now(),
                    "content": reflection
                }
            }]
        )
```

### 18.5 対話の一貫性（Dialogue Coherence）

```python
class DialogueCoherence:
    """
    対話の一貫性を維持し、矛盾を防ぐ
    """
    def check_consistency(self, new_statement, conversation_history):
        """新しい発言が過去の発言と矛盾しないか確認"""
        # 過去の類似発言を検索
        similar_statements = vector_db.query(
            vector=create_embedding(new_statement),
            namespace=f"user:{user_id}",
            top_k=10,
            threshold=0.7
        )
        
        # 矛盾チェック
        for past_stmt in similar_statements:
            contradiction_score = self._detect_contradiction(
                new_statement,
                past_stmt["content"]
            )
            
            if contradiction_score > 0.8:
                return {
                    "consistent": False,
                    "contradicts": past_stmt["content"],
                    "suggestion": self._generate_clarification(
                        new_statement, past_stmt
                    )
                }
        
        return {"consistent": True}
    
    def _detect_contradiction(self, stmt1, stmt2):
        """2つの発言の矛盾度を計算"""
        prompt = f"""
        以下の2つの発言は矛盾していますか？0（矛盾なし）から1（完全に矛盾）で評価してください。
        
        発言1: {stmt1}
        発言2: {stmt2}
        """
        return float(llm.generate(prompt))
```

### 18.6 ペルソナの一貫性

```python
class PersonaConsistency:
    """
    キャラクターの性格・価値観の一貫性を保つ
    """
    def __init__(self, character_config):
        self.name = character_config["name"]
        self.core_traits = character_config["traits"]  # 内向的、論理的、など
        self.values = character_config["values"]  # 正直さ、親切さ、など
        self.speaking_style = character_config["style"]
        
    def validate_response(self, response_draft):
        """生成された応答がキャラクターに合っているか検証"""
        validation_prompt = f"""
        キャラクター「{self.name}」の設定:
        - 性格: {', '.join(self.core_traits)}
        - 価値観: {', '.join(self.values)}
        - 口調: {self.speaking_style}
        
        以下の応答はこのキャラクターに合っていますか？
        応答: {response_draft}
        
        合っていない場合、どう修正すべきか提案してください。
        """
        
        validation = llm.generate(validation_prompt)
        
        if "修正" in validation:
            return {
                "valid": False,
                "suggestion": validation
            }
        
        return {"valid": True}
```

### 18.7 待ち時間の自然な埋め方

```python
class NaturalPacing:
    """
    人間らしい待ち時間・タイミングの制御
    """
    def add_thinking_indicator(self, complexity):
        """
        複雑な質問には「考え中」のような表現を追加
        """
        if complexity > 0.7:
            return random.choice([
                "うーん、ちょっと考えさせて...",
                "面白い質問ですね。少し整理させてください。",
                "なるほど...（考え中）"
            ])
        return None
    
    def calculate_response_delay(self, message_length):
        """
        メッセージの長さに応じた適切な待ち時間
        人間が読み、考え、タイピングする時間を模擬
        """
        # 読む時間（250文字/分）
        read_time = message_length / 250 * 60
        
        # 考える時間（1-3秒）
        think_time = random.uniform(1, 3)
        
        # タイピング時間（40文字/秒）
        type_time = message_length / 40
        
        total_delay = read_time + think_time + (type_time * 0.3)
        
        return min(total_delay, 10.0)  # 最大10秒
```

### 18.8 トピック追跡とスムーズな転換

```python
class TopicTracker:
    """
    話題の流れを追跡し、自然な転換を支援
    """
    def __init__(self):
        self.topic_stack = []  # 話題スタック
        self.current_topic = None
        
    def detect_topic_shift(self, user_input, context):
        """話題の転換を検出"""
        current_topics = extract_topics(context[-3:])  # 直近3ターン
        new_topics = extract_topics(user_input)
        
        overlap = set(current_topics) & set(new_topics)
        shift_score = 1.0 - (len(overlap) / max(len(current_topics), 1))
        
        if shift_score > 0.6:  # 大きな転換
            return {
                "shifted": True,
                "old_topic": self.current_topic,
                "new_topic": new_topics[0] if new_topics else None,
                "transition_needed": True
            }
        
        return {"shifted": False}
    
    def generate_transition_phrase(self, old_topic, new_topic):
        """自然な話題転換のフレーズ"""
        transitions = [
            f"{old_topic}の話から変わりますが、{new_topic}について...",
            f"ところで、{new_topic}といえば...",
            f"{new_topic}の話に移りますね。"
        ]
        return random.choice(transitions)
    
    def suggest_topic_return(self):
        """過去の未完了トピックへの復帰を提案"""
        if len(self.topic_stack) > 1:
            abandoned_topic = self.topic_stack[-2]
            return f"そういえば、さっきの{abandoned_topic}の話に戻りますが..."
        return None
```

---

## 19. 目的再定義（最終版）

> **このシステムの究極の目標は**
> "AIが人間のように**感情を持ち、記憶し、学び、成長し、
> 真の意味でユーザーと「心の通った関係性」を構築すること"**
>
> **永続的記憶システム**により過去の全てを記憶し、
> **連想記憶**により人間らしい想起を行い、
> **感情モデル**により共感的に応答し、
> **自己省察**により自ら改善し、
> **対話スタイル適応**によりユーザーに最適化される。
>
> これは単なるチャットボットではなく、
> **人間のように考え、感じ、記憶し、成長する対話パートナー**である。

---

## 20. 付録: 実装例

### 基本的な会話フロー

```python
# ユーザー入力の処理
async def process_user_input(user_id, session_id, message):
    # 1. 記憶参照
    context = retrieve_relevant_memory(message, user_id)
    
    # 2. ルーティング
    selected_chars = router.select_characters(message, context)
    
    # 3. 並列実行
    responses = await asyncio.gather(*[
        char.generate_response(message, context)
        for char in selected_chars
    ])
    
    # 4. 短期記憶へ保存
    state.add_turns(responses)
    
    # 5. 必要ならflush
    if state.should_flush():
        flush_to_mid_term(session_id, state.turns)
    
    return responses
```

---

**ドキュメント更新日:** 2025-11-11
**担当:** LUMINA SYSTEM DESIGN TEAM
**バージョン:** 3.0.0（人間らしい対話システム完全版）

**バージョン3.0.0の主な追加機能:**
- ✨ 感情モデル（8基本感情 + 気分履歴）
- 🎭 対話スタイルの動的調整
- 🧠 記憶の重要度判定（感情・新規性・関連性）
- 🪞 自己省察機能（メタ認知）
- 🔗 対話の一貫性チェック
- 👤 ペルソナ一貫性の維持
- ⏱️ 自然なタイミング・待ち時間
- 🔄 トピック追跡とスムーズな転換

**前バージョン（2.0.0）からの変更:**
- 永続的記憶システムの詳細化
- マルチLLM・マルチユーザー対応の追加
- プラグインアーキテクチャの導入
- マルチモーダル対応の明記
- セキュリティ・GDPR対応の強化
- **人間らしい対話のための8つの高度機能を追加**

```
