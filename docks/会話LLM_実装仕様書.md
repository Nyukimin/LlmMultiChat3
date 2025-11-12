
```markdown
# 会話LLM_IMPLEMENTATION.md
## ― 人間らしい対話を実現するマルチLLM会話システム 実装仕様書 ―
（LangGraph / Ollama / Serper API / Neo4j）

**バージョン 3.0.0** - 感情・記憶・成長を持つAI対話パートナー

---

## 1. 実装目的

本仕様書は「会話LLM_仕様.md（v3.0）」で定義された
**人間らしい対話を実現するマルチLLM会話システム**の
**実装構成・モジュール仕様・設定項目・新機能の実装方法**を記述する。

### v3.0の主な追加実装

1. **感情モデル** - Plutchikの8基本感情
2. **連想記憶** - Neo4jグラフDBによる概念ネットワーク
3. **自己省察** - メタ認知システム
4. **適応的対話** - ユーザーに最適化
5. **記憶の重要度判定** - 感情・新規性ベース
6. **対話の一貫性チェック** - 矛盾検出
7. **ペルソナ一貫性** - キャラクター維持
8. **自然なタイミング** - 人間らしい待ち時間

---

## 2. プロジェクト構成（v3.0拡張版）

```
Llm_Multi_Chat/
├── main.py                       # メインアプリケーション
├── config.py                     # 設定・環境変数管理（拡張性考慮）
├── conversation_state.py         # 会話状態・履歴管理
├── llm_nodes.py                  # 各キャラLLMノード処理
├── utils.py                      # ログ・エクスポート・検証
├── check_system.py               # システム診断
├── requirements.txt              # 依存関係
├── env_example.txt               # 環境変数例
│
├── core/                         # v3.0 コアシステム
│   ├── emotional_state.py        # 感情モデル
│   ├── associative_memory.py     # 連想記憶
│   ├── self_reflection.py        # 自己省察
│   ├── dialogue_coherence.py     # 対話一貫性
│   ├── persona_consistency.py    # ペルソナ維持
│   ├── adaptive_style.py         # 適応的対話スタイル
│   ├── memory_salience.py        # 記憶重要度判定
│   ├── topic_tracker.py          # トピック追跡
│   ├── natural_pacing.py         # 自然なタイミング
│   └── plugin_manager.py         # プラグインマネージャ（Phase 3）
│
├── personas/                     # 各キャラの設定YAML
├── adapters/                     # LoRA / Adapter格納
├── kb/                           # 知識ベースETLスクリプト
├── memory/                       # 記憶管理
│   ├── short_term.py             # 短期記憶
│   ├── mid_term.py               # 中期記憶（Redis/DuckDB）
│   ├── long_term.py              # 長期記憶（VectorDB/SQL）
│   ├── knowledge_base.py         # 知識ベース
│   └── association_visualization.py  # 3D可視化（v3.0）
│
├── security/                     # セキュリティ層（Phase 2）
│   ├── auth.py                   # 認証・認可
│   ├── encryption.py             # データ暗号化
│   └── audit_log.py              # 監査ログ
│
├── api/                          # REST/WebSocket API（Phase 3）
│   ├── routes.py                 # エンドポイント定義
│   ├── middleware.py             # 認証・レート制限
│   └── websocket.py              # リアルタイム通信
│
├── plugins/                      # プラグインエコシステム（Phase 3）
│   ├── base.py                   # プラグイン基底クラス
│   ├── weather.py                # 天気プラグイン例
│   └── translate.py              # 翻訳プラグイン例
│
├── tests/                        # テストスイート（Phase 2）
│   ├── unit/                     # ユニットテスト
│   ├── integration/              # 統合テスト
│   └── performance/              # パフォーマンステスト
│
├── static/                       # 静的ファイル（HTML/CSS/JS）
│   ├── css/                      # スタイルシート
│   ├── js/                       # JavaScript
│   └── templates/                # HTMLテンプレート
│
└── README.md


---

## 2.1 拡張性を考慮した初手設計パターン

**技術スタック: Python + HTML + CSS**

### 2.1.1 プラグイン型アーキテクチャ

**Phase 1から実装**

```python
# core/plugin_manager.py
class PluginInterface:
    """プラグイン基底クラス（初手から定義）"""
    
    def on_message(self, message: str, context: dict) -> Optional[dict]:
        """メッセージ受信時のフック"""
        pass
    
    def on_response(self, response: str, context: dict) -> str:
        """応答生成後のフック"""
        return response
    
    def on_memory_store(self, memory: dict) -> dict:
        """記憶保存前のフック"""
        return memory

class PluginManager:
    """プラグインマネージャ（Phase 1から組み込み）"""
    
    def __init__(self):
        self.plugins: List[PluginInterface] = []
    
    def register(self, plugin: PluginInterface):
        """プラグイン登録（動的ロード対応）"""
        self.plugins.append(plugin)
    
    def trigger(self, hook: str, *args, **kwargs):
        """全プラグインのフックを実行"""
        for plugin in self.plugins:
            method = getattr(plugin, hook, None)
            if method:
                result = method(*args, **kwargs)
                if result is not None:
                    return result
```

**Phase 3で追加実装:**
```python
# plugins/weather.py（Phase 3で追加）
class WeatherPlugin(PluginInterface):
    def on_message(self, message, context):
        if "天気" in message:
            return {"action": "weather_api", "location": "Tokyo"}
```

---

### 2.1.2 設定ベース拡張（config.py）

**Phase 1から実装**

```python
# config.py
class Config:
    """環境変数+YAML設定の統合管理（拡張性考慮）"""
    
    def __init__(self):
        # Phase 1: 基本設定
        self.load_env()
        self.load_yaml()
        
        # Phase 2以降の拡張ポイント（初手から定義）
        self.security = SecurityConfig()  # Phase 2で実装
        self.api = APIConfig()             # Phase 3で実装
        self.plugins = []                  # Phase 3で実装
    
    def load_yaml(self, path="config.yaml"):
        """YAML設定の動的読み込み"""
        with open(path) as f:
            config = yaml.safe_load(f)
            self._merge_config(config)

class SecurityConfig:
    """Phase 2で実装するが、Phase 1から構造定義"""
    def __init__(self):
        self.encryption_enabled = False  # Phase 1: OFF
        self.auth_enabled = False        # Phase 2: ON
        self.jwt_secret = None           # Phase 2で設定
```

**config.yaml（Phase 1から拡張可能）**
```yaml
# Phase 1設定
ollama:
  host: "http://localhost:11434"
  models:
    fast: "llama3-jp-8b"

# Phase 2で追加（初手から定義可能）
security:
  encryption: false  # Phase 2でtrue
  auth: false        # Phase 2でtrue

# Phase 3で追加
api:
  enabled: false     # Phase 3でtrue
  rate_limit: 100
```

---

### 2.1.3 モジュール分離設計

**Phase 1から実装**

```python
# memory/base.py（Phase 1から抽象化）
class MemoryBackend(ABC):
    """記憶バックエンドの抽象基底クラス"""
    
    @abstractmethod
    def store(self, key: str, value: Any):
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Any:
        pass

# memory/short_term.py（Phase 1実装）
class ShortTermMemory(MemoryBackend):
    def __init__(self):
        self.storage = {}  # RAM
    
    def store(self, key, value):
        self.storage[key] = value

# memory/mid_term.py（Phase 1実装）
class MidTermMemory(MemoryBackend):
    def __init__(self):
        self.redis = redis.Redis()  # Phase 1から実装
    
    def store(self, key, value):
        self.redis.setex(key, 86400, value)
```

**Phase 2で追加（インターフェース変更不要）:**
```python
# memory/encrypted_backend.py（Phase 2で追加）
class EncryptedMemory(MemoryBackend):
    def __init__(self, backend: MemoryBackend):
        self.backend = backend
        self.cipher = AES256()
    
    def store(self, key, value):
        encrypted = self.cipher.encrypt(value)
        self.backend.store(key, encrypted)
```

---

### 2.1.4 エラーハンドリング基盤（Phase 1から）

```python
# utils/error_handler.py
class ErrorHandler:
    """Phase 1から拡張可能なエラーハンドリング"""
    
    def __init__(self):
        self.fallback_strategies = {}
    
    def register_fallback(self, error_type: Type[Exception], strategy: Callable):
        """Phase 3でカスタム戦略追加"""
        self.fallback_strategies[error_type] = strategy
    
    def handle(self, error: Exception) -> Any:
        """エラー種別に応じた処理"""
        strategy = self.fallback_strategies.get(type(error))
        if strategy:
            return strategy(error)
        else:
            # Phase 1: デフォルト処理
            logger.error(f"Unhandled error: {error}")
            return None

# Phase 1から登録
error_handler = ErrorHandler()
error_handler.register_fallback(TimeoutError, lambda e: "少し待ってください")
```

---

### 2.1.5 データベース抽象化レイヤー

**Phase 1から実装**

```python
# core/db_adapter.py
class DatabaseAdapter(ABC):
    """Phase 1から拡張可能なDB抽象化"""
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def execute(self, query: str, params: tuple):
        pass

# Phase 1実装
class SQLiteAdapter(DatabaseAdapter):
    def connect(self):
        self.conn = sqlite3.connect("app.db")
    
    def execute(self, query, params):
        return self.conn.execute(query, params)

# Phase 3で追加（インターフェース変更不要）
class PostgreSQLAdapter(DatabaseAdapter):
    def connect(self):
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
```

---

### 2.1.6 WebUI構造（HTML + CSS + JS）

**Phase 1から拡張可能**

```html
<!-- static/templates/index.html（Phase 1） -->
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <div id="chat-container">
        <!-- Phase 1: 基本チャット -->
        <div id="messages"></div>
        <input id="input" type="text">
    </div>
    
    <!-- Phase 3: 3D可視化（初手からdiv確保） -->
    <div id="visualization-panel" style="display:none;">
        <!-- Phase 3で実装 -->
    </div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>
```

```css
/* static/css/main.css（Phase 1から拡張可能） */
:root {
    /* Phase 1: 基本カラー */
    --primary-color: #4A90E2;
    
    /* Phase 4: テーマ切り替え用（初手から定義） */
    --dark-bg: #1E1E1E;
    --light-bg: #FFFFFF;
}

/* Phase 1実装 */
#chat-container {
    width: 100%;
    max-width: 800px;
}

/* Phase 3で有効化 */
#visualization-panel {
    width: 400px;
    height: 400px;
}
```

---

### 2.1.7 テスト基盤（Phase 1から）

```python
# tests/conftest.py（Phase 1から定義）
import pytest

@pytest.fixture
def mock_llm():
    """Phase 1から使用するモックLLM"""
    class MockLLM:
        def generate(self, prompt):
            return "テスト応答"
    return MockLLM()

@pytest.fixture
def test_config():
    """Phase 1から拡張可能なテスト設定"""
    return {
        "phase_1": {"ollama_enabled": True},
        "phase_2": {"encryption": False},  # Phase 2で有効化
        "phase_3": {"api_enabled": False}  # Phase 3で有効化
    }
```

---

### 2.1.8 フェーズ別実装チェックリスト

| Phase | 初手から実装 | Phase Xで有効化 |
|-------|-------------|----------------|
| **Phase 1** | プラグインI/F定義 | - |
| | エラーハンドリング基盤 | - |
| | DB抽象化レイヤー | - |
| | 設定ファイル構造 | - |
| | WebUI基本構造 | - |
| **Phase 2** | SecurityConfig定義 | 暗号化・認証実装 |
| | TestSuite構造 | 全テスト実装 |
| **Phase 3** | APIConfig定義 | REST/WS実装 |
| | PluginManager実装 | プラグイン追加 |

---

**拡張の原則:**

1. **Phase 1**: インターフェース・抽象クラス・設定構造を定義
2. **Phase 2+**: 実装追加（既存コード変更最小限）
3. **互換性維持**: 古いコードが動き続ける設計

```

---

## 3. 設定ファイル構造（`config.py`）

```python
class Config:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")
        
        self.models = {
            "fast": "7shi/llm-jp-3-ezo-humanities:3.7b-instruct-q8_0",
            "medium": "amoral-gemma3:latest",
            "search": "dsasai/llama3-elyza-jp-8b:latest"
        }

        self.max_turns = 6
        self.enable_search = True
````

**主な機能**

* モデル設定の一元管理
* APIキーとOllama接続先の定義
* 設定整合性チェック（`validate_config()`）

---

## 4. 会話状態管理（`conversation_state.py`）

```python
class ConversationState:
    def __init__(self):
        self.history = []
        self.current_turn = 0
        self.max_turns = 6
        self.start_time = datetime.now()

    def add_turn(self, speaker: str, message: str):
        self.history.append({"speaker": speaker, "msg": message})
        self.current_turn += 1

    def summarize(self):
        # 履歴を要約して中期メモリへ転送
        return summarize_conversation(self.history)
```

**機能**

* 会話履歴の保持
* ターン数の追跡と自動リセット
* 要約生成・中期メモリ転送（flush）

---

## 5. LLMノード実装（`llm_nodes.py`）

### 5.1 ルミナ

```python
def conversation_lumina(state: ConversationState):
    prompt = f"""
    あなたは親しみやすく洞察力のあるAI「ルミナ」です。
    次のメッセージに自然で温かみのある返答をしてください。
    メッセージ: {state.history[-1]['msg']}
    返答:
    """
    return ollama.chat(model=config.models["fast"], messages=[{"role":"user","content":prompt}])
```

### 5.2 クラリス

```python
def conversation_claris(state: ConversationState):
    prompt = f"""
    あなたは理論的で穏やかなAI「クラリス」です。
    以下の内容を丁寧に整理し、背景や構造を解説してください。
    メッセージ: {state.history[-1]['msg']}
    """
    return ollama.chat(model=config.models["medium"], messages=[{"role":"user","content":prompt}])
```

### 5.3 ノクス（検索機能付き）

```python
def conversation_nox(state: ConversationState):
    msg = state.history[-1]["msg"]
    search_keywords = ["調べて", "最新情報", "ニュース", "検索"]
    if any(k in msg for k in search_keywords):
        result = serper_search(msg)
        context = result["summary"]
    else:
        context = ""
    prompt = f"""
    あなたはクールで情報整理に優れたAI「ノクス」です。
    以下の発話と検索結果を要約し、正確な情報を提供してください。
    発話: {msg}
    検索結果: {context}
    """
    return ollama.chat(model=config.models["search"], messages=[{"role":"user","content":prompt}])
```

---

## 6. LangGraph構成（`main.py`）

```python
class MultiLLMChat:
    def __init__(self):
        self.state = ConversationState()
        self.nodes = {
            "lumina": conversation_lumina,
            "claris": conversation_claris,
            "nox": conversation_nox
        }
        self.graph = self._build_graph()
        self.compiled = self.graph.compile()

    def _build_graph(self):
        g = StateGraph()
        g.add_node("lumina", self.nodes["lumina"])
        g.add_node("claris", self.nodes["claris"])
        g.add_node("nox", self.nodes["nox"])
        g.add_edge("lumina", "claris")
        g.add_edge("claris", "nox")
        g.add_edge("nox", "lumina")
        return g

    def run(self):
        self.compiled.invoke(self.state)
```

---

## 7. ユーティリティ群（`utils.py`）

### 7.1 ログ管理

```python
class Logger:
    def log_conversation(self, msg, llm, turn):
        self.logger.info(f"[Turn {turn}] [{llm}] {msg}")
```

### 7.2 システム検証

```python
class SystemChecker:
    @staticmethod
    def check_ollama_connection():
        return requests.get(f"{config.ollama_host}/api/version").status_code == 200
```

### 7.3 エクスポート機能

```python
class ConversationExporter:
    @staticmethod
    def export_to_json(data, filename=None):
        with open(filename or f"chat_{ts()}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 8. システムチェック（`check_system.py`）

```python
def main():
    print("=== System Check ===")
    print("Ollama:", SystemChecker.check_ollama_connection())
    print("Models:", SystemChecker.check_models_availability(config.models))
    print("API Key:", bool(config.serper_api_key))
```

実行：

```bash
python check_system.py
```

---

## 9. セットアップ手順

### 1. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 2. モデル準備

```bash
ollama pull 7shi/llm-jp-3-ezo-humanities:3.7b-instruct-q8_0
ollama pull amoral-gemma3:latest
ollama pull dsasai/llama3-elyza-jp-8b:latest
```

### 3. APIキー設定

```bash
set SERPER_API_KEY=your_key_here   # Windows
export SERPER_API_KEY=your_key_here # Linux/Mac
```

### 4. 実行

```bash
python main.py
```

---

## 10. 検索ユーティリティ（`serper_search`）

```python
def serper_search(query: str) -> dict:
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": config.serper_api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": 3}
    resp = requests.post(url, headers=headers, json=payload).json()
    summary = " / ".join([r["title"] for r in resp.get("organic", [])[:3]])
    return {"summary": summary, "source": resp.get("organic", [])[0]["link"]}
```

---

## 11. KPI更新・成長ロジック

```python
def update_kpi(character: str, event: str):
    db = sqlite3.connect("meta.db")
    cur = db.cursor()
    cur.execute(
        "INSERT INTO kpi_log (char,event,ts) VALUES (?,?,?)",
        (character, event, datetime.now())
    )
    db.commit()
```

KPI累積 → レベル計算：

```python
level = floor(sqrt(total_kpi / 10))
```

---

## 12. 開発・運用ポイント

| カテゴリ   | 推奨設定                       |
| ------ | -------------------------- |
| GPUメモリ | 12GB以上（LoRA利用時16GB推奨）      |
| 並列処理   | asyncio + LangGraph並列ノード   |
| 永続化    | Redis自動flush + DuckDB 週次圧縮 |
| 監視     | logs/*.log + KPIメトリクス      |
| バックアップ | MinIO同期／RDB snapshot       |

---

## 13. トラブルシューティング

| 問題          | 対応策                   |
| ----------- | --------------------- |
| Ollama接続不可  | `ollama serve` を実行    |
| モデル未登録      | `ollama pull <model>` |
| APIキー無効     | Serperキーを再取得          |
| 検索結果空       | クエリフィルタを再設定           |
| LangGraph例外 | ノード間型不一致を確認           |

---

## 14. 今後の拡張予定

* WebUI（Streamlit / FastAPI）統合
* 会話履歴の永続検索機能
* DuckDB＋VectorDB統合ビューア
* マルチユーザーセッション対応
* KPI→LoRA自動再学習

---

---

## 15. v3.0新機能の実装詳細

### 15.1 感情モデルの実装

**ファイル:** `core/emotional_state.py`

```python
class EmotionalState:
    """各キャラクターの感情状態管理"""
    
    def __init__(self, character_name):
        self.character = character_name
        self.emotions = {
            "joy": 0.5, "trust": 0.5, "fear": 0.0, "surprise": 0.0,
            "sadness": 0.0, "disgust": 0.0, "anger": 0.0, "anticipation": 0.5
        }
        self.mood_history = []
    
    def update_from_conversation(self, user_input, context):
        user_emotion = analyze_sentiment(user_input)
        if user_emotion["valence"] < 0:
            self.emotions["sadness"] += 0.2
            self.emotions["trust"] += 0.1
        else:
            self.emotions["joy"] += 0.2
        self._decay_emotions()
```

### 15.2 連想記憶の実装

**ファイル:** `core/associative_memory.py`

**依存関係:**
```bash
pip install neo4j py2neo
```

**Neo4j接続設定:**
```python
from neo4j import GraphDatabase

class AssociativeMemory:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
```

### 15.3 自己省察の実装

**ファイル:** `core/self_reflection.py`

```python
class SelfReflection:
    def reflect_on_conversation(self, conversation_history):
        reflection_prompt = f"""
        以下の会話を振り返り、改善点を分析してください:
        {format_conversation(conversation_history)}
        """
        reflection = llm.generate(reflection_prompt)
        self._store_reflection(reflection)
        return reflection
```
### 15.4 連想ネットワーク3D可視化の実装

**ファイル:** `core/memory/association_visualization.py`

#### 15.4.1 概要

連想記憶の構造を視覚的に理解・探索できるインタラクティブな3D可視化パネル。

**主な機能:**
- ON/OFF切り替え可能（デフォルトOFF）
- リアルタイム更新
- インタラクティブ操作（ズーム・回転・ノードクリック）
- エクスポート（PNG/HTML）

#### 15.4.2 実装クラス

```python
import plotly.graph_objects as go
import networkx as nx
from typing import Optional, Dict, List

class AssociationVisualizationPanel:
    """
    連想ネットワーク3D可視化パネル
    
    ワード間の距離を視覚化し、近い概念をよく思い出す仕組みを実装。
    スター型構造で中心概念から関連概念を放射状に配置。
    """
    
    def __init__(self, association_memory):
        self.association = association_memory
        self.is_visible = False  # デフォルトOFF
        self.fig = None
        self.auto_update = False
        self.center_concept = None
        self.depth = 3
        self.threshold = 0.3
        self.max_nodes = 50  # パフォーマンス考慮
        
    def toggle(self) -> bool:
        """パネルのON/OFF切り替え"""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self._initialize_visualization()
        else:
            self._cleanup()
        return self.is_visible
        
    def update_center(self, concept: str, max_depth: int = 3):
        """
        中心概念を変更してグラフを更新
        
        Args:
            concept: 中心となる概念
            max_depth: 探索深度（1-5ホップ）
        """
        if not self.is_visible:
            return
            
        self.center_concept = concept
        self.depth = max_depth
        
        # 連想ネットワークから関連概念を取得
        related = self.association.explore_associations(
            concept, max_depth=max_depth
        )
        
        # 3Dグラフを描画（Plotly + NetworkX）
        self.fig = self._create_3d_graph(concept, related)
        
    def _create_3d_graph(self, center: str, associations: List[Dict]) -> go.Figure:
        """
        3Dグラフ描画（Force-Directed Layout）
        
        距離の計算:
        - 距離 = 1.0 - エッジ重み
        - 近い概念（重み高）= 距離小 = ノード大きい
        """
        # NetworkXグラフ構築
        G = nx.Graph()
        G.add_node(center, distance=0)
        
        for assoc in associations[:self.max_nodes]:
            G.add_node(assoc['concept'], distance=assoc['distance'])
            G.add_edge(
                center if assoc['distance'] == 1 else assoc['parent'],
                assoc['concept'],
                weight=assoc['strength']
            )
        
        # 3D配置計算（Force-Directed Layout）
        pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)
        
        # エッジ描画データ
        edge_traces = self._create_edge_traces(G, pos)
        
        # ノード描画データ
        node_trace = self._create_node_trace(G, pos, center)
        
        # レイアウト設定
        layout = go.Layout(
            title=f"連想ネットワーク: {center}",
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
        
        fig = go.Figure(data=edge_traces + [node_trace], layout=layout)
        return fig
    
    def _create_edge_traces(self, G, pos) -> List[go.Scatter3d]:
        """エッジ描画データ作成（強度で色・太さ変更）"""
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
                    width=strength * 5,
                    color=self._get_edge_color(strength)
                ),
                hoverinfo='text',
                hovertext=f"強度: {strength:.2f}",
                showlegend=False
            )
            edge_traces.append(edge_trace)
        return edge_traces
    
    def _create_node_trace(self, G, pos, center) -> go.Scatter3d:
        """ノード描画データ作成（距離で色・サイズ変更）"""
        node_x, node_y, node_z = [], [], []
        node_text, node_colors, node_sizes = [], [], []
        
        for node in G.nodes(data=True):
            x, y, z = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            distance = node[1].get('distance', 999)
            node_text.append(node[0])
            node_colors.append(self._get_node_color(distance))
            node_sizes.append(self._get_node_size(distance))
        
        return go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_text,
            textposition="top center",
            textfont=dict(size=10),
            hoverinfo='text',
            hovertext=[
                f"{node[0]}<br>距離: {node[1].get('distance', 'N/A')}"
                for node in G.nodes(data=True)
            ]
        )
    
    def _get_edge_color(self, strength: float) -> str:
        """エッジ色（強度ベース）"""
        if strength > 0.7:
            return 'rgba(255, 0, 0, 0.8)'  # 強い: 赤
        elif strength > 0.4:
            return 'rgba(255, 165, 0, 0.6)'  # 中: オレンジ
        else:
            return 'rgba(128, 128, 128, 0.3)'  # 弱い: グレー
    
    def _get_node_color(self, distance: int) -> str:
        """ノード色（距離ベース）"""
        if distance == 0:
            return '#FF0000'  # 中心: 赤
        elif distance == 1:
            return '#FFA500'  # 1ホップ: オレンジ
        elif distance == 2:
            return '#FFFF00'  # 2ホップ: 黄
        else:
            return '#00FF00'  # 3ホップ: 緑
    
    def _get_node_size(self, distance: int) -> int:
        """ノードサイズ（距離ベース：近いほど大きい）"""
        return max(20 - distance * 5, 5)
    
    def export(self, filepath: str, format: str = "png"):
        """
        グラフをエクスポート
        
        Args:
            filepath: 保存先パス
            format: 'png' または 'html'
        """
        if not self.fig:
            return
            
        if format == "png":
            self.fig.write_image(filepath, width=1920, height=1080)
        elif format == "html":
            self.fig.write_html(filepath)
```

#### 15.4.3 使用例

```python
# 初期化
viz = AssociationVisualizationPanel(association_memory)

# ON/OFF切り替え
viz.toggle()  # True (表示)

# 会話中の自動更新
# ユーザー: 「インセプションについて話して」
viz.update_center("インセプション", max_depth=3)
# → 「夢」「記憶」「ノーラン」「時間」が近くに表示される

# エクスポート
viz.export("association_graph.png", format="png")
viz.export("association_graph.html", format="html")
```

#### 15.4.4 パフォーマンス仕様

- **最大ノード数:** 50（パフォーマンス考慮）
- **更新頻度:** 1秒/回
- **描画エンジン:** Plotly WebGL（高速描画）
- **CPU負荷:** 最小限

#### 15.4.5 技術的ポイント

1. **距離の計算**
   - 距離 = 1.0 - エッジ重み
   - 近い概念（重み高）= 距離小 = ノード大きい

2. **力学モデル**
   - NetworkXの`spring_layout`でノード配置
   - 関連性の強い概念ほど近くに配置
   - 視覚的に「よく思い出す」を表現

3. **スター型構造**
   - 中心概念を原点に、関連概念を放射状に配置
   - 深度1: 直接関連（最も近い）
   - 深度2-3: 間接関連（やや遠い）

4. **WebGL描画**
   - Plotlyの`plotly.graph_objects.Scatter3d`で高速描画

---


---

## 16. 依存関係の更新（v3.0）

**requirements.txt**

```txt
# コア
langchain>=0.1.0
langgraph>=0.0.20
ollama>=0.1.0

# 記憶層
redis>=5.0.0
duckdb>=0.9.0
psycopg2-binary>=2.9.0
pinecone-client>=2.2.0
# または qdrant-client>=1.7.0

# 連想記憶
neo4j>=5.14.0
py2neo>=2021.2.3

# 感情分析
transformers>=4.30.0
torch>=2.0.0

# 3D可視化
plotly>=5.17.0
networkx>=3.1
kaleido>=0.2.1  # PNG/PDFエクスポート用

# ユーティリティ
numpy>=1.24.0
pandas>=2.0.0
pyyaml>=6.0
requests>=2.31.0

# Web検索
google-serper>=0.1.0

# 音声・画像（オプション）
openai-whisper>=20230314
pillow>=10.0.0

# ETL
apache-airflow>=2.7.0

# 監視
prometheus-client>=0.17.0
```

---

## 17. データベースセットアップ（v3.0）

### 17.1 Neo4j（連想記憶）

```bash
# Docker経由
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### 17.2 PostgreSQL（メタデータ）

```bash
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=llm_multi_chat \
  postgres:15
```

### 17.3 Redis（中期記憶）

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

---

## 18. 開発・運用ポイント（v3.0更新）

| カテゴリ | 推奨設定 | 備考 |
|---------|---------|------|
| GPUメモリ | 16GB以上 | 感情分析モデル含む |
| CPU | 8コア以上 | Neo4j推奨 |
| RAM | 32GB以上 | グラフDB + ベクトルDB |
| 並列処理 | asyncio + LangGraph | 複数キャラ同時応答 |
| 永続化 | Redis + DuckDB + Neo4j | 階層記憶 |
| 監視 | Prometheus + Grafana | KPI + 感情状態 |
| バックアップ | MinIO + RDB Snapshot | 週次推奨 |

---

## 19. v3.0アップグレードガイド

### 既存システムからv3.0へ

1. **依存関係の追加インストール**
```bash
pip install neo4j py2neo transformers torch
```

2. **Neo4jのセットアップ**
```bash
docker-compose up -d neo4j
```

3. **新機能モジュールの追加**
```bash
mkdir -p core memory
# core/以下に新機能実装
```

4. **既存データの移行**
```python
python migrate_to_v3.py
```

---

**実装完了日:** 2024-12
**v3.0更新日:** 2025-11-11
**バージョン:** 3.0.0（人間らしい対話システム完全版）
**ライセンス:** MIT
**開発:** LUMINA SYSTEM DEVELOPMENT TEAM

**v3.0の主な追加実装:**
- ✨ 感情モデル（8基本感情）
- 🧠 連想記憶（Neo4j Graph DB）
- 🪞 自己省察システム
- 🎭 適応的対話スタイル
- 🔗 対話一貫性チェック
- ⏱️ 自然なタイミング制御
- 🌈 記憶重要度判定
- 🔄 トピック追跡
- 📊 連想ネットワーク3D可視化パネル


---

## 16. v3.1新機能の実装詳細（API・MCP・自律サーチ）

### 16.1 REST/WebSocket API実装

**ファイル:** `api/routes.py`, `api/middleware.py`, `api/websocket.py`

**優先度:** 高（Phase 1拡張）  
**工数:** 2週間

#### 16.1.1 依存関係追加

```bash
# requirements.txt に追加
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
websockets==12.0
redis==5.0.1
```

#### 16.1.2 FastAPIアプリケーション基本構造

**ファイル:** `api/main.py`

```python
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import jwt
from datetime import datetime, timedelta
import redis

app = FastAPI(title="会話LLM API", version="3.1.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis接続（レート制限用）
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
```

#### 16.1.3 認証実装

**ファイル:** `api/auth.py`

```python
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"  # 環境変数から取得推奨
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### 16.1.4 レート制限実装

**ファイル:** `api/rate_limit.py`

```python
from fastapi import HTTPException
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def check_rate_limit(user_id: str, role: str = "free"):
    """
    レート制限チェック
    - Free: 100リクエスト/分
    - Pro: 1000リクエスト/分
    """
    limit = 100 if role == "free" else 1000
    key = f"rate_limit:{user_id}"
    
    current = redis_client.get(key)
    if current is None:
        redis_client.setex(key, 60, 1)
    else:
        count = int(current)
        if count >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        redis_client.incr(key)
```

#### 16.1.5 WebSocket実装

**ファイル:** `api/websocket.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/api/v1/stream")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    
    try:
        # 認証
        auth_data = await websocket.receive_json()
        if auth_data.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "Authentication required"})
            await websocket.close()
            return
        
        user_id = verify_token_ws(auth_data["token"])
        await manager.connect(websocket, user_id)
        await websocket.send_json({"type": "auth_success", "user_id": user_id})
        
        # 会話ループ
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # ストリーミング応答
                async for chunk in stream_conversation(
                    user_id=user_id,
                    message=data["content"],
                    thread_id=data.get("thread_id")
                ):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk["text"],
                        "character": chunk["character"]
                    })
                
                await websocket.send_json({
                    "type": "done",
                    "message_id": chunk["message_id"],
                    "thread_id": chunk["thread_id"]
                })
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
```

#### 16.1.6 実装チェックリスト

- [ ] FastAPI基本構造実装
- [ ] Pydanticモデル定義（`api/models.py`）
- [ ] JWT認証実装
- [ ] レート制限（Redis）
- [ ] WebSocketストリーミング
- [ ] CORS設定
- [ ] エラーハンドリング
- [ ] OpenAPI仕様書自動生成
- [ ] Postmanコレクション作成

---

### 16.2 MCP (Model Context Protocol) 対応実装

**ファイル:** `mcp/server.py`, `mcp/client.py`

**優先度:** 中（Phase 1拡張）  
**工数:** 1週間

#### 16.2.1 依存関係追加

```bash
# requirements.txt に追加
mcp==0.9.0
```

#### 16.2.2 MCP Server実装

**ファイル:** `mcp/server.py`

```python
from mcp.server import Server
from mcp.types import TextContent, Tool, Resource
from typing import Any, Sequence

class LlmMultiChatMCPServer(Server):
    """会話LLMシステムをMCP Serverとして公開"""
    
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
            from conversation_state import execute_conversation
            
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
            from memory.long_term import search_vector_db
            
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
            from memory.knowledge_base import query_knowledge_base
            
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
            from core.autonomous_search import perform_autonomous_search
            
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
        
        @self.resource("character://nox")
        async def get_nox_info() -> TextContent:
            """ノクスのプロフィール"""
            return TextContent(
                type="text",
                text="ノクス: クールな情報ハンター。検証・要約特化。"
            )
        
        @self.resource("memory://recent")
        async def get_recent_memories() -> TextContent:
            """最近の記憶"""
            from memory.long_term import get_recent_memories
            
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

#### 16.2.3 MCP Server起動方法

```bash
# stdio方式でMCP Server起動
python mcp/server.py

# Claude Desktop連携設定（~/.config/Claude/claude_desktop_config.json）
{
  "mcpServers": {
    "llm-multi-chat": {
      "command": "python",
      "args": ["c:/GenerativeAI/LlmMultiChat3/mcp/server.py"]
    }
  }
}
```

#### 16.2.4 実装チェックリスト

- [ ] MCP Server基本実装
- [ ] 4つのツール実装（chat/search/kb/autonomous_search）
- [ ] 4つのリソース実装（character×3 + memory）
- [ ] stdio通信実装
- [ ] Claude Desktop連携テスト
- [ ] MCPドキュメント作成

---

### 16.3 自律的外部サーチ・情報収集エージェント実装

**ファイル:** `core/autonomous_search.py`, `core/knowledge_updater.py`

**優先度:** 高（Phase 1拡張）  
**工数:** 2週間

#### 16.3.1 依存関係追加

```bash
# requirements.txt に追加
langchain==0.1.0
langchain-community==0.0.13
apscheduler==3.10.4
wikipedia==1.4.0
```

#### 16.3.2 自律サーチエージェント実装

**ファイル:** `core/autonomous_search.py`

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import asyncio

class AutonomousSearchAgent:
    """自律的外部サーチ・情報収集エージェント"""
    
    def __init__(self):
        self.serper = GoogleSerperAPIWrapper()
        self.wikipedia = WikipediaAPIWrapper()
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
                func=self.wikipedia.run,
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
        
        from llm_nodes import get_llm
        return create_react_agent(
            llm=get_llm("gpt-4"),
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
        from memory.knowledge_base import query_all_knowledge_bases
        
        results = await query_all_knowledge_bases(query, top_k=5)
        if results:
            return "\n\n".join([r["content"] for r in results])
        return "知識ベースに関連情報なし"
    
    async def _save_to_kb(self, category: str, content: str) -> str:
        """知識ベース保存"""
        from memory.knowledge_base import upsert_to_knowledge_base
        from datetime import datetime
        
        await upsert_to_knowledge_base(
            kb_name=f"kb:{category}",
            content=content,
            metadata={"source": "autonomous_search", "timestamp": datetime.utcnow()}
        )
        return f"知識ベース kb:{category} に保存完了"
    
    def _classify_category(self, query: str) -> str:
        """カテゴリ分類（簡易版）"""
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
```

#### 16.3.3 定期更新スケジューラ実装

**ファイル:** `core/knowledge_updater.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.autonomous_search import AutonomousSearchAgent
import asyncio

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

#### 16.3.4 LangGraphへの統合

**ファイル:** `main.py` に追加

```python
from core.autonomous_search import AutonomousSearchAgent

# LangGraphノードに追加
def autonomous_search_node(state: ConversationState):
    """自律サーチノード"""
    query = state.history[-1]["msg"]
    
    # 既存知識ベース確認
    kb_results = query_all_knowledge_bases(query, top_k=3)
    
    if kb_results and kb_results[0]["score"] > 0.8:
        # 既存知識で十分
        state.search_results = kb_results[0]["content"]
    else:
        # 外部検索必要
        agent = AutonomousSearchAgent()
        result = asyncio.run(agent.search_and_collect(
            query=query,
            max_depth=3,
            save_to_kb=True
        ))
        state.search_results = result["result"]
    
    return state

# グラフに組み込み
graph.add_node("autonomous_search", autonomous_search_node)
graph.add_conditional_edges(
    "check_kb",
    lambda s: "autonomous_search" if s["need_search"] else "respond"
)
```

#### 16.3.5 実装チェックリスト

- [ ] ReActエージェント実装
- [ ] 4つのツール実装（web/kb/wikipedia/save）
- [ ] カテゴリ自動分類
- [ ] 定期実行スケジューラ
- [ ] LangGraph統合
- [ ] 重複排除・品質フィルタ
- [ ] エラーハンドリング

---

### 16.4 v3.1実装サマリー

| 機能 | ファイル | 工数 | ステータス |
|------|---------|------|-----------|
| **REST/WebSocket API** | `api/*.py` | 2週 | Phase 1拡張 |
| **MCP対応** | `mcp/*.py` | 1週 | Phase 1拡張 |
| **自律サーチ** | `core/autonomous_*.py` | 2週 | Phase 1拡張 |

**合計工数**: 5週間（Phase 1: 4ヶ月→5ヶ月に延長）

**v3.1の主な追加実装:**
- 🌐 REST/WebSocket API（FastAPI）
- 🔌 MCP対応（Claude Desktop連携）
- 🤖 自律的外部サーチ・情報収集エージェント

```
