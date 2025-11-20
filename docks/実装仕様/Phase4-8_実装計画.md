# Phase 4-8 実装計画書（MVP優先方式）

**プロジェクト名**: 会話LLM（LlmMultiChat3）  
**バージョン**: 3.1.0  
**作成日**: 2025-11-20  
**計画期間**: 22週間（約5.5ヶ月）  
**方針**: MVP優先 - 少しずつ確実に実装

---

## 📊 エグゼクティブサマリー

### 目的
Phase 1-3で実装済みの基盤（LangGraphコア・記憶・API）に対し、仕様書で定義された高度な機能を段階的に追加し、**人間らしい対話を持つAIパートナー**を実現する。

### 実装規模
- **総行数**: 約3,250行（Phase 4-8）
- **総期間**: 22週間
- **テスト**: 約133件
- **Phase数**: 5 Phases

### Phase別概要

| Phase | 期間 | 主要機能 | 実装規模 | テスト |
|-------|------|---------|---------|--------|
| **Phase 4** | 4週間 | 連想記憶・感情基盤 | 700行 | 35件 |
| **Phase 5** | 4週間 | 対話適応・自己省察 | 550行 | 30件 |
| **Phase 6** | 4週間 | キャラ成長・MCP | 750行 | 35件 |
| **Phase 7** | 4週間 | 3D可視化・自律サーチ | 850行 | 25件 |
| **Phase 8** | 3週間 | LoRA・最終統合 | 400行 | 8件 |

---

## 🎯 Phase 4: 記憶システム拡張 + 感情基盤

**期間**: 4週間  
**目標**: 連想記憶と感情モデルの基礎実装

### 4.1 連想記憶システム（Week 1-2）

#### 実装内容
**参照**: [`docks/仕様書/05_会話LLM_連想記憶仕様.md`](docks/仕様書/05_会話LLM_連想記憶仕様.md)

**主要機能**:
1. **SQLite Graph実装** ([`05_会話LLM_連想記憶仕様.md:52-181`](docks/仕様書/05_会話LLM_連想記憶仕様.md:52))
   - ノード管理（概念・トピック・感情）
   - エッジ管理（関連性・強度）
   - 再帰CTE連想検索

2. **学習メカニズム** ([`05_会話LLM_連想記憶仕様.md:323-364`](docks/仕様書/05_会話LLM_連想記憶仕様.md:323))
   - ヘッブの法則（共起強化）
   - 時間的近接性学習
   - 感情的関連学習

3. **忘却曲線** ([`05_会話LLM_連想記憶仕様.md:164-180`](docks/仕様書/05_会話LLM_連想記憶仕様.md:164))
   - 未使用記憶の減衰
   - 弱い関連性の自動削除

#### ファイル構成
```python
memory/associative.py          # 400行
├── AssociativeMemory クラス
│   ├── add_concept(concept, embedding, metadata)
│   ├── link_concepts(concept_a, concept_b, relationship_type, strength)
│   ├── retrieve_associated_concepts(trigger, depth, threshold)
│   ├── strengthen_association(concept_a, concept_b, delta)
│   └── decay_inactive_associations(days_threshold, decay_rate)
│
└── SQLiteGraph クラス
    ├── create_node(label, properties)
    ├── create_relationship(from_node, to_node, rel_type, properties)
    └── find_associated_concepts(start_concept, depth, threshold)
```

#### データベーススキーマ
```sql
-- memory/associative_schema.sql

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    type TEXT,
    metadata JSON,
    created_at INTEGER,
    activation_count INTEGER DEFAULT 0,
    emotional_valence REAL DEFAULT 0.0
);

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

CREATE INDEX idx_nodes_name ON nodes(name);
CREATE INDEX idx_edges_from ON edges(from_id);
CREATE INDEX idx_edges_to ON edges(to_id);
CREATE INDEX idx_edges_strength ON edges(strength);
```

#### テスト（20件）
```python
tests/test_associative_memory.py

def test_add_concept()                    # 概念追加
def test_link_concepts()                  # 関連付け
def test_retrieve_associated_concepts()   # 連想検索
def test_strengthen_association()         # 関連性強化
def test_decay_inactive_associations()    # 忘却処理
def test_hebbian_learning()               # ヘッブ学習
def test_graph_traversal()                # グラフ探索
def test_shortest_path()                  # 最短パス
def test_emotional_memory()               # 感情記憶
def test_concept_clustering()             # クラスタリング
# ... 他10件
```

#### API追加
```python
# api/routes/memory.py に追加

@router.post("/api/v1/memory/associate")
async def create_association(
    concept_a: str,
    concept_b: str,
    strength: float = 1.0
):
    """2つの概念を関連付け"""
    ...

@router.get("/api/v1/memory/associations/{concept}")
async def get_associations(
    concept: str,
    depth: int = 3,
    threshold: float = 0.3
):
    """連想検索"""
    ...
```

---

### 4.2 感情モデル基盤（Week 3-4）

#### 実装内容
**参照**: [`docks/仕様書/04_会話LLM_感情・対話仕様.md`](docks/仕様書/04_会話LLM_感情・対話仕様.md)

**主要機能**:
1. **8基本感情管理** ([`04_会話LLM_感情・対話仕様.md:34-108`](docks/仕様書/04_会話LLM_感情・対話仕様.md:34))
   - Plutchikの感情の輪モデル
   - 喜び、信頼、恐れ、驚き、悲しみ、嫌悪、怒り、期待

2. **感情の自然な減衰**
   - ホメオスタシス（中立値0.5へ）
   - 時間経過による自動減衰

3. **ユーザー感情分析**
   - sentiment analysis統合
   - 共感的応答（ミラーリング）

4. **感情履歴記録**
   - タイムスタンプ付き履歴
   - トレンド分析

#### ファイル構成
```python
core/emotion.py                # 300行
├── EmotionalState クラス
│   ├── __init__(character_name)
│   ├── update_from_conversation(user_input, context)
│   ├── _decay_emotions(rate)
│   ├── get_dominant_emotion()
│   ├── generate_emotional_modifier()
│   └── analyze_mood_trend()
│
└── analyze_sentiment(text)    # 外部関数
```

#### テスト（15件）
```python
tests/test_emotion.py

def test_emotional_state_init()           # 初期化
def test_update_from_conversation()       # 感情更新
def test_decay_emotions()                 # 減衰
def test_get_dominant_emotion()           # 支配的感情
def test_generate_emotional_modifier()    # プロンプト修飾子
def test_mood_history()                   # 履歴記録
def test_analyze_mood_trend()             # トレンド分析
def test_sentiment_analysis()             # センチメント分析
# ... 他7件
```

#### API追加
```python
# api/routes/chat.py に追加

@router.get("/api/v1/character/{name}/emotion")
async def get_character_emotion(name: str):
    """キャラクターの感情状態取得"""
    emotion_state = character_manager.get_emotion(name)
    return {
        "character": name,
        "emotions": emotion_state.emotions,
        "dominant": emotion_state.get_dominant_emotion(),
        "mood_trend": emotion_state.analyze_mood_trend()
    }
```

---

### Phase 4 成果物

**実装コード**:
- `memory/associative.py` (400行)
- `core/emotion.py` (300行)
- **合計**: 700行

**テスト**:
- `tests/test_associative_memory.py` (20件)
- `tests/test_emotion.py` (15件)
- **合計**: 35件

**ドキュメント**:
- `docks/完了報告/Phase4_完了サマリー.md`
- API仕様書更新

**マイルストーン**:
- [ ] 連想記憶の基本動作確認
- [ ] 感情モデルの統合テスト成功
- [ ] パフォーマンス < 30ms（連想検索）

---

## 🎭 Phase 5: 対話スタイル適応 + 自己省察

**期間**: 4週間  
**目標**: ユーザーに合わせた対話スタイル調整と自己改善機能

### 5.1 対話スタイル動的調整（Week 1-2）

#### 実装内容
**参照**: [`docks/仕様書/04_会話LLM_感情・対話仕様.md:152-208`](docks/仕様書/04_会話LLM_感情・対話仕様.md:152)

**主要機能**:
1. **スタイルパラメータ管理**
   - formality: カジュアル ⇔ フォーマル
   - verbosity: 簡潔 ⇔ 詳細
   - humor: 真面目 ⇔ ユーモラス
   - technical_level: 平易 ⇔ 専門的
   - empathy: 共感レベル
   - proactivity: 受動的 ⇔ 積極的

2. **フィードバック学習**
   - ユーザーフィードバック解析
   - パラメータ自動調整
   - 永続化

3. **プロンプト動的生成**
   - スタイルに応じたプロンプト生成

#### ファイル構成
```python
core/dialogue_style.py         # 250行
├── AdaptiveDialogueStyle クラス
│   ├── __init__(user_id)
│   ├── learn_from_feedback(user_feedback)
│   ├── generate_style_prompt()
│   └── _save_to_profile()
```

#### テスト（12件）
```python
tests/test_dialogue_style.py

def test_style_init()                     # 初期化
def test_learn_from_feedback()            # フィードバック学習
def test_generate_style_prompt()          # プロンプト生成
def test_parameter_bounds()               # パラメータ範囲
# ... 他8件
```

---

### 5.2 自己省察・一貫性チェック（Week 3-4）

#### 実装内容
**参照**: [`docks/仕様書/04_会話LLM_感情・対話仕様.md:230-536`](docks/仕様書/04_会話LLM_感情・対話仕様.md:230)

**主要機能**:
1. **自己省察** ([`04_会話LLM_感情・対話仕様.md:230-287`](docks/仕様書/04_会話LLM_感情・対話仕様.md:230))
   - 会話の振り返り
   - 過去の学び検索
   - メタ認知

2. **矛盾検出** ([`04_会話LLM_感情・対話仕様.md:298-357`](docks/仕様書/04_会話LLM_感情・対話仕様.md:298))
   - 過去発言との矛盾チェック
   - 修正案生成

3. **トピック追跡** ([`04_会話LLM_感情・対話仕様.md:456-536`](docks/仕様書/04_会話LLM_感情・対話仕様.md:456))
   - 話題の流れ追跡
   - 自然な転換支援

#### ファイル構成
```python
core/self_reflection.py        # 300行
├── SelfReflection クラス
│   ├── reflect_on_conversation(conversation_history)
│   ├── _store_reflection(reflection)
│   └── retrieve_past_lessons(current_situation)
│
├── DialogueCoherence クラス
│   ├── check_consistency(new_statement, history)
│   ├── _detect_contradiction(stmt1, stmt2)
│   └── _generate_clarification(new_stmt, past_stmt)
│
└── TopicTracker クラス
    ├── detect_topic_shift(user_input, context)
    ├── generate_transition_phrase(old_topic, new_topic)
    └── suggest_topic_return()
```

#### テスト（18件）
```python
tests/test_self_reflection.py

def test_reflect_on_conversation()        # 省察
def test_store_reflection()               # 省察保存
def test_retrieve_past_lessons()          # 学び検索
def test_check_consistency()              # 一貫性チェック
def test_detect_contradiction()           # 矛盾検出
def test_topic_shift_detection()          # 話題転換検出
def test_transition_phrase()              # 転換フレーズ
# ... 他11件
```

---

### Phase 5 成果物

**実装コード**:
- `core/dialogue_style.py` (250行)
- `core/self_reflection.py` (300行)
- **合計**: 550行

**テスト**:
- `tests/test_dialogue_style.py` (12件)
- `tests/test_self_reflection.py` (18件)
- **合計**: 30件

**ドキュメント**:
- `docks/完了報告/Phase5_完了サマリー.md`

**マイルストーン**:
- [ ] 対話スタイル適応動作確認
- [ ] 自己省察・矛盾検出テスト成功
- [ ] トピック追跡精度 > 80%

---

## 🌱 Phase 6: キャラクター成長 + MCP対応

**期間**: 4週間  
**目標**: KPIベース成長システムとMCP Server実装

### 6.1 KPIベース成長システム（Week 1-2）

#### 実装内容
**参照**: [`docks/仕様書/03_会話LLM_キャラクター仕様.md:246-333`](docks/仕様書/03_会話LLM_キャラクター仕様.md:246)

**主要機能**:
1. **KPI収集**
   - user_thumbs_up: ユーザー評価 👍
   - answer_hits: 推薦が採用
   - search_success: 検索結果が役立った
   - conversation_count: 会話参加回数
   - topic_expertise: トピック別専門性

2. **レベルアップロジック**
   - `level = floor(sqrt(total_kpi / 10))`
   - 新機能解禁
   - パラメータ自動調整

3. **成長結果**
   - 会話スタイル変化
   - 3Dアバター更新
   - 声質向上

#### ファイル構成
```python
core/character_growth.py       # 350行
├── CharacterGrowth クラス
│   ├── __init__(character_name)
│   ├── update_kpi(event_type, value, topic)
│   ├── _calculate_level()
│   ├── _level_up(new_level)
│   ├── _unlock_new_features()
│   ├── _update_appearance()
│   └── _adjust_parameters()
```

#### データベース拡張
```sql
-- db/character_growth_schema.sql

CREATE TABLE IF NOT EXISTS character_growth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_name TEXT NOT NULL,
    kpi_type TEXT NOT NULL,
    value INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    topic TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_character_kpi ON character_growth(character_name, kpi_type);
```

#### テスト（15件）
```python
tests/test_character_growth.py

def test_kpi_update()                     # KPI更新
def test_level_calculation()              # レベル計算
def test_level_up()                       # レベルアップ
def test_unlock_features()                # 機能解禁
def test_parameter_adjustment()           # パラメータ調整
# ... 他10件
```

---

### 6.2 MCP Server実装（Week 3-4）

#### 実装内容
**参照**: [`docks/仕様書/01_会話LLM_仕様.md:501-529`](docks/仕様書/01_会話LLM_仕様.md:501)

**主要機能**:
1. **MCP Server基盤**
   - ツール公開機構
   - リソース公開機構

2. **公開ツール**
   - `chat_with_character`: キャラクター指名会話
   - `search_memories`: 記憶検索
   - `autonomous_search`: 自律Web検索

3. **公開リソース**
   - `character://lumina`: キャラクター情報
   - `memory://user:{id}`: ユーザー記憶

#### ファイル構成
```python
api/mcp_server.py              # 400行
├── LlmMultiChatMCPServer クラス
│   ├── @tool デコレータ
│   │   ├── chat_with_character(character, message)
│   │   ├── search_memories(query)
│   │   └── autonomous_search(topic)
│   │
│   └── @resource デコレータ
│       ├── get_lumina_info()
│       ├── get_clarisse_info()
│       └── get_user_memories(user_id)
```

#### テスト（20件）
```python
tests/test_mcp_server.py

def test_mcp_server_init()                # 初期化
def test_chat_with_character_tool()       # ツール動作
def test_search_memories_tool()           # ツール動作
def test_character_resource()             # リソース取得
def test_memory_resource()                # リソース取得
# ... 他15件
```

---

### Phase 6 成果物

**実装コード**:
- `core/character_growth.py` (350行)
- `api/mcp_server.py` (400行)
- **合計**: 750行

**テスト**:
- `tests/test_character_growth.py` (15件)
- `tests/test_mcp_server.py` (20件)
- **合計**: 35件

**ドキュメント**:
- `docks/完了報告/Phase6_完了サマリー.md`
- MCP Server設定ガイド

**マイルストーン**:
- [ ] KPI収集・レベルアップ動作確認
- [ ] MCP Server外部接続テスト成功
- [ ] Claude Desktop統合確認

---

## 📊 Phase 7: 3D可視化 + 自律サーチ

**期間**: 4週間  
**目標**: 連想ネットワーク可視化と自律情報収集

### 7.1 3D可視化パネル（Week 1-2）

#### 実装内容
**参照**: [`docks/仕様書/06_会話LLM_3D可視化仕様.md`](docks/仕様書/06_会話LLM_3D可視化仕様.md)

**主要機能**:
1. **Plotly.js 3Dグラフ** ([`06_会話LLM_3D可視化仕様.md:42-243`](docks/仕様書/06_会話LLM_3D可視化仕様.md:42))
   - ノード・エッジ描画
   - Force-Directed Layout
   - 色・サイズによる情報表現

2. **インタラクティブ操作**
   - ドラッグ回転
   - ホイールズーム
   - ノードクリック

3. **ON/OFF切り替え**
   - デフォルトOFF
   - リアルタイム更新

#### ファイル構成
```python
visualization/association_3d.py  # 500行
├── AssociationVisualizationPanel クラス
│   ├── __init__()
│   ├── toggle()
│   ├── update_center(concept)
│   ├── _render_graph()
│   ├── _get_edge_color(strength)
│   ├── _get_node_color(distance)
│   ├── export_html(filename)
│   └── export_png(filename)
│
└── VisualizationControls クラス
    └── render_controls()
```

#### テスト（10件）
```python
tests/test_visualization.py

def test_panel_init()                     # 初期化
def test_toggle()                         # ON/OFF
def test_update_center()                  # 中心変更
def test_render_graph()                   # グラフ描画
def test_export_html()                    # HTML出力
# ... 他5件
```

---

### 7.2 自律的外部サーチエージェント（Week 3-4）

#### 実装内容
**参照**: [`docks/仕様書/01_会話LLM_仕様.md:531-561`](docks/仕様書/01_会話LLM_仕様.md:531)

**主要機能**:
1. **トリガー条件判定**
   - ユーザー質問時（既存知識なし）
   - 定期実行（日次/週次）
   - 手動トリガー

2. **検索ツール統合**
   - Serper API（Web検索）
   - Wikipedia検索
   - KB保存

3. **定期更新スケジューラ**
   - 毎朝6時: ニュース・トレンド
   - 毎週日曜: 映画情報
   - 毎月1日: 技術情報

#### ファイル構成
```python
agents/autonomous_search.py    # 350行
├── AutonomousSearchAgent クラス
│   ├── __init__()
│   ├── should_search(user_question, kb_results)
│   ├── web_search(query)
│   ├── wikipedia_search(query)
│   └── save_to_kb(content, category)
│
scheduler/update_scheduler.py  # 200行
└── UpdateScheduler クラス
    ├── schedule_daily_news()
    ├── schedule_weekly_movies()
    └── schedule_monthly_tech()
```

#### テスト（15件）
```python
tests/test_autonomous_search.py

def test_should_search()                  # 検索判定
def test_web_search()                     # Web検索
def test_wikipedia_search()               # Wikipedia検索
def test_save_to_kb()                     # KB保存
def test_daily_scheduler()                # 日次スケジュール
# ... 他10件
```

---

### Phase 7 成果物

**実装コード**:
- `visualization/association_3d.py` (500行)
- `agents/autonomous_search.py` (350行)
- **合計**: 850行

**テスト**:
- `tests/test_visualization.py` (10件)
- `tests/test_autonomous_search.py` (15件)
- **合計**: 25件

**ドキュメント**:
- `docks/完了報告/Phase7_完了サマリー.md`
- 3D可視化操作ガイド

**マイルストーン**:
- [ ] 3D可視化パネル動作確認
- [ ] 自律サーチ定期実行テスト成功
- [ ] KB自動更新確認

---

## 🎓 Phase 8: LoRAファインチューニング + 最終統合

**期間**: 3週間  
**目標**: キャラクター成長の最終形態と全システム統合

### 8.1 LoRAファインチューニング（Week 1-2）

#### 実装内容
**参照**: [`docks/仕様書/03_会話LLM_キャラクター仕様.md:335-379`](docks/仕様書/03_会話LLM_キャラクター仕様.md:335)

**主要機能**:
1. **月次バッチ処理**
   - 過去1ヶ月の会話履歴収集
   - 訓練データ作成
   - LoRA適用

2. **モデル保存・ロード**
   - `models/lora_{character_name}/`
   - 動的ロード機構

#### ファイル構成
```python
training/lora_tuning.py        # 400行
├── CharacterFineTuning クラス
│   ├── @monthly_task
│   ├── fine_tune_character(character_name)
│   ├── _create_training_data(conversations)
│   └── _load_lora_model(character_name)
```

#### 要件
- **GPU必須**: VRAM 8GB+
- **ライブラリ**: transformers, peft
- **実行頻度**: 月次バッチ

#### テスト（8件 - 軽量テストのみ）
```python
tests/test_lora_tuning.py

def test_training_data_creation()         # データ作成
def test_lora_config()                    # 設定
def test_model_save_load()                # 保存・ロード
# ... 他5件（GPU不要な軽量テスト）
```

---

### 8.2 最終統合・品質保証（Week 3）

#### タスク
1. **全Phase統合テスト**
   - Phase 4-7の統合動作確認
   - エンドツーエンドテスト

2. **パフォーマンス最適化**
   - ボトルネック特定
   - 非同期処理最適化

3. **ドキュメント最終更新**
   - 完全仕様書更新
   - API仕様書最終版
   - ユーザーガイド作成

4. **リリース準備**
   - バージョンタグ作成
   - リリースノート作成

#### 成果物
- 統合テストレポート
- パフォーマンスレポート
- リリースノート v4.0.0

---

### Phase 8 成果物

**実装コード**:
- `training/lora_tuning.py` (400行)
- **合計**: 400行

**テスト**:
- `tests/test_lora_tuning.py` (8件)
- **統合テスト**: 全Phase横断
- **合計**: 8件 + 統合テスト

**ドキュメント**:
- `docks/完了報告/Phase8_完了サマリー.md`
- `docks/完了報告/Phase4-8_最終統合レポート.md`
- リリースノート v4.0.0

**マイルストーン**:
- [ ] LoRAファインチューニング動作確認
- [ ] 全Phase統合テスト成功
- [ ] リリース準備完了

---

## 📅 総合スケジュール

### タイムライン

```
Week 1-3:   Phase 1-3統合完了（現在進行中）
Week 4-7:   Phase 4（連想記憶・感情基盤）
Week 8-11:  Phase 5（対話適応・自己省察）
Week 12-15: Phase 6（キャラ成長・MCP）
Week 16-19: Phase 7（3D可視化・自律サーチ）
Week 20-22: Phase 8（LoRA・最終統合）
```

### マイルストーン

| Week | マイルストーン | 成果物 |
|------|--------------|--------|
| Week 3 | Phase 1-3統合完了 | 統合完了サマリー |
| Week 7 | Phase 4完了 | 連想記憶・感情モデル |
| Week 11 | Phase 5完了 | 対話適応・自己省察 |
| Week 15 | Phase 6完了 | キャラ成長・MCP Server |
| Week 19 | Phase 7完了 | 3D可視化・自律サーチ |
| Week 22 | Phase 8完了 | LoRA・最終統合 |

---

## 🎯 優先度・リスク管理

### 優先度

| Phase | 優先度 | 理由 |
|-------|--------|------|
| Phase 4 | **高** | 連想記憶・感情は対話の核心機能 |
| Phase 5 | **高** | ユーザー体験向上に直結 |
| Phase 6 | **中** | 成長システムは長期運用で効果 |
| Phase 7 | **低** | 可視化は付加価値、自律サーチは補助 |
| Phase 8 | **低** | LoRAはGPU必要、オプション機能 |

### リスク

| リスク | 影響 | 対策 |
|--------|------|------|
| GPU不足（Phase 8） | 高 | CPU版LoRA実装、クラウドGPU利用 |
| パフォーマンス低下 | 中 | 非同期処理、キャッシュ強化 |
| API制限（自律サーチ） | 中 | レート制限遵守、フォールバック |
| 3D描画負荷 | 低 | 最大ノード数50制限、遅延ロード |

---

## 📊 実装規模まとめ

### コード規模

| Phase | Python | TypeScript | 合計 |
|-------|--------|------------|------|
| Phase 4 | 700 | - | 700 |
| Phase 5 | 550 | - | 550 |
| Phase 6 | 750 | - | 750 |
| Phase 7 | 650 | 200 | 850 |
| Phase 8 | 400 | - | 400 |
| **合計** | **3,050** | **200** | **3,250** |

### テスト規模

| Phase | テスト件数 |
|-------|-----------|
| Phase 4 | 35件 |
| Phase 5 | 30件 |
| Phase 6 | 35件 |
| Phase 7 | 25件 |
| Phase 8 | 8件 |
| **合計** | **133件** |

---

## ✅ 承認チェックリスト

- [ ] スケジュール（22週間）は妥当か？
- [ ] 優先度付けは適切か？
- [ ] 各Phaseの成果物は明確か？
- [ ] リスク対策は十分か？
- [ ] テスト計画は適切か？

---

**計画書バージョン**: 1.0.0  
**作成日**: 2025-11-20  
**承認**: 未承認  
**次回更新**: Phase 4開始時

---

**この計画でよろしいでしょうか？調整が必要な箇所があれば教えてください。**