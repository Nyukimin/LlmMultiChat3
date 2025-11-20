
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


---

## 17. 5階層記憶システム詳細実装

### 17.1 短期記憶（Working Memory）

**ファイル:** `memory/short_term.py`

**優先度:** 高（Phase 1必須）  
**工数:** 2日

#### 17.1.1 実装

```python
from typing import List, Dict, Any
from datetime import datetime

class ShortTermMemory:
    """
    短期記憶（LangGraph State内）
    - 保持: 現在セッション（6-12ターン）
    - 自動flush: ターン数/時間閾値超過時
    """
    
    def __init__(self, max_turns: int = 12, max_duration_minutes: int = 30):
        self.history: List[Dict[str, Any]] = []
        self.max_turns = max_turns
        self.max_duration_minutes = max_duration_minutes
        self.session_start = datetime.utcnow()
    
    def add_turn(self, speaker: str, message: str, metadata: Dict = None):
        """ターン追加"""
        turn = {
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        self.history.append(turn)
        
        # 自動flush判定
        if self.should_flush():
            self.flush_to_mid_term()
    
    def should_flush(self) -> bool:
        """flush判定"""
        # ターン数超過
        if len(self.history) >= self.max_turns:
            return True
        
        # 時間超過
        duration = (datetime.utcnow() - self.session_start).total_seconds() / 60
        if duration >= self.max_duration_minutes:
            return True
        
        return False
    
    def flush_to_mid_term(self):
        """中期記憶へ転送"""
        from memory.mid_term import MidTermMemory
        
        mid_term = MidTermMemory()
        summary = self._summarize_conversation()
        mid_term.store_session(summary, self.history)
        
        # クリア
        self.history = []
        self.session_start = datetime.utcnow()
    
    def _summarize_conversation(self) -> str:
        """会話要約（LLM使用）"""
        from llm_nodes import get_llm
        
        history_text = "\n".join([
            f"{turn['speaker']}: {turn['message']}"
            for turn in self.history
        ])
        
        prompt = f"""
以下の会話を3行で要約してください。
重要なトピック・感情・結論を含めてください。

{history_text}
"""
        llm = get_llm("fast")
        return llm.invoke(prompt).content
    
    def get_context(self, last_n: int = 5) -> str:
        """最新N ターンの文脈取得"""
        recent = self.history[-last_n:]
        return "\n".join([
            f"{turn['speaker']}: {turn['message']}"
            for turn in recent
        ])
```

---

### 17.2 中期記憶（Session Memory）

**ファイル:** `memory/mid_term.py`

**優先度:** 高（Phase 1必須）  
**工数:** 3日

#### 17.2.1 Redis実装

```python
import redis
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MidTermMemory:
    """
    中期記憶（Redis 24h TTL → DuckDB 7-30日保存）
    - セッション復帰・割り込み後の文脈回復
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.ttl = 86400  # 24時間
    
    def store_session(
        self,
        summary: str,
        history: List[Dict],
        user_id: str = "default"
    ):
        """セッション保存（Redis）"""
        session_id = f"session:{user_id}:{datetime.utcnow().isoformat()}"
        
        # エンベディング生成
        embedding = self._generate_embedding(summary)
        
        session_data = {
            "summary": summary,
            "history": json.dumps(history, ensure_ascii=False),
            "embedding": json.dumps(embedding),
            "keywords": self._extract_keywords(summary),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Redis保存（24h TTL）
        self.redis_client.hset(session_id, mapping=session_data)
        self.redis_client.expire(session_id, self.ttl)
        
        # DuckDBへの非同期アーカイブ（バックグラウンド）
        self._schedule_archive(session_id, session_data)
    
    def retrieve_recent_sessions(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """最近のセッション取得"""
        pattern = f"session:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        
        sessions = []
        for key in keys[:limit]:
            session = self.redis_client.hgetall(key)
            if session:
                sessions.append({
                    "session_id": key,
                    "summary": session["summary"],
                    "timestamp": session["timestamp"],
                    "keywords": session["keywords"]
                })
        
        return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """テキストエンベディング生成"""
        from langchain.embeddings import OllamaEmbeddings
        
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        return embeddings.embed_query(text)
    
    def _extract_keywords(self, text: str) -> str:
        """キーワード抽出（簡易TF-IDF）"""
        # TODO: より高度なキーワード抽出（YAKE、KeyBERT等）
        words = text.split()
        return " ".join(sorted(set(words), key=words.count, reverse=True)[:10])
    
    def _schedule_archive(self, session_id: str, data: Dict):
        """DuckDBアーカイブスケジュール"""
        from memory.archiver import SessionArchiver
        
        archiver = SessionArchiver()
        archiver.schedule_archive(session_id, data)
```

#### 17.2.2 DuckDBアーカイブ実装

**ファイル:** `memory/archiver.py`

```python
import duckdb
from typing import Dict
import json

class SessionArchiver:
    """Redis → DuckDB 永続化"""
    
    def __init__(self, db_path: str = "data/sessions.duckdb"):
        self.conn = duckdb.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        """テーブル作成"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR PRIMARY KEY,
                user_id VARCHAR,
                summary TEXT,
                history TEXT,
                embedding FLOAT[],
                keywords VARCHAR,
                timestamp TIMESTAMP
            )
        """)
    
    def schedule_archive(self, session_id: str, data: Dict):
        """アーカイブ（バックグラウンド実行）"""
        self.conn.execute("""
            INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            session_id.split(":")[1],  # user_id抽出
            data["summary"],
            data["history"],
            json.loads(data["embedding"]),
            data["keywords"],
            data["timestamp"]
        ))
        self.conn.commit()
    
    def search_sessions(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """セッション全文検索"""
        result = self.conn.execute("""
            SELECT session_id, summary, timestamp
            FROM sessions
            WHERE user_id = ?
            AND summary LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, f"%{query}%", limit)).fetchall()
        
        return [
            {"session_id": r[0], "summary": r[1], "timestamp": r[2]}
            for r in result
        ]
```

---

### 17.3 長期記憶（Persistent Memory）

**ファイル:** `memory/long_term.py`

**優先度:** 高（Phase 1必須）  
**工数:** 5日

#### 17.3.1 VectorDB実装（Pinecone）

```python
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
from datetime import datetime
import hashlib

class LongTermMemory:
    """
    長期記憶（VectorDB + PostgreSQL）
    - ユーザープロファイル、過去全履歴、学習済みパターン
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = "llm-multi-chat-memory"
        self._init_index()
    
    def _init_index(self):
        """Pineconeインデックス初期化"""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=768,  # nomic-embed-text
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index = self.pc.Index(self.index_name)
    
    def upsert_memory(
        self,
        user_id: str,
        content: str,
        metadata: Dict = None
    ):
        """記憶追加"""
        from memory.mid_term import MidTermMemory
        
        mid_term = MidTermMemory()
        embedding = mid_term._generate_embedding(content)
        
        memory_id = self._generate_id(user_id, content)
        
        self.index.upsert(vectors=[{
            "id": memory_id,
            "values": embedding,
            "metadata": {
                "user_id": user_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        }])
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        min_score: float = 0.7
    ) -> List[Dict]:
        """記憶検索"""
        from memory.mid_term import MidTermMemory
        
        mid_term = MidTermMemory()
        query_embedding = mid_term._generate_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter={"user_id": user_id},
            include_metadata=True
        )
        
        memories = []
        for match in results.matches:
            if match.score >= min_score:
                memories.append({
                    "content": match.metadata["content"],
                    "score": match.score,
                    "timestamp": match.metadata["timestamp"],
                    "metadata": match.metadata
                })
        
        return memories
    
    def _generate_id(self, user_id: str, content: str) -> str:
        """一意ID生成"""
        hash_input = f"{user_id}:{content}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
```

#### 17.3.2 PostgreSQLメタデータ実装

**ファイル:** `memory/metadata_db.py`

```python
import psycopg2
from typing import Dict, List
from datetime import datetime

class MetadataDB:
    """PostgreSQL メタデータ管理"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="llm_multi_chat",
            user="postgres",
            password=os.getenv("POSTGRES_PASSWORD")
        )
        self._init_schema()
    
    def _init_schema(self):
        """テーブル作成"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id VARCHAR PRIMARY KEY,
                    name VARCHAR,
                    preferences JSONB,
                    kpi JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversation_metadata (
                    conversation_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR REFERENCES user_profiles(user_id),
                    summary TEXT,
                    topics TEXT[],
                    sentiment FLOAT,
                    duration_seconds INT,
                    turn_count INT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP
                )
            """)
            
            self.conn.commit()
    
    def get_user_profile(self, user_id: str) -> Dict:
        """ユーザープロファイル取得"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT name, preferences, kpi
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    "name": result[0],
                    "preferences": result[1],
                    "kpi": result[2]
                }
            return {}
    
    def update_user_profile(
        self,
        user_id: str,
        preferences: Dict = None,
        kpi: Dict = None
    ):
        """ユーザープロファイル更新"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_profiles (user_id, preferences, kpi)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET preferences = EXCLUDED.preferences,
                    kpi = EXCLUDED.kpi,
                    updated_at = NOW()
            """, (user_id, json.dumps(preferences), json.dumps(kpi)))
            
            self.conn.commit()
```

---

### 17.4 知識ベース（Knowledge Base - RAG）

**ファイル:** `memory/knowledge_base.py`

**優先度:** 中（Phase 1拡張）  
**工数:** 3日

#### 17.4.1 実装

```python
from typing import List, Dict, Any
from datetime import datetime

class KnowledgeBase:
    """
    知識ベース（RAG層）
    - kb:movie, kb:history, kb:gossip, kb:tech, kb:custom
    """
    
    def __init__(self):
        from memory.long_term import LongTermMemory
        self.vector_db = LongTermMemory()
    
    def upsert_to_knowledge_base(
        self,
        kb_name: str,
        content: str,
        metadata: Dict = None
    ):
        """知識ベースへ追加"""
        self.vector_db.upsert_memory(
            user_id=f"kb:{kb_name}",
            content=content,
            metadata={
                "kb_name": kb_name,
                "source": metadata.get("source", "manual"),
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        )
    
    def query_knowledge_base(
        self,
        kb_name: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """知識ベース検索"""
        return self.vector_db.search_memories(
            user_id=f"kb:{kb_name}",
            query=query,
            top_k=top_k,
            min_score=0.6
        )
    
    def query_all_knowledge_bases(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict]:
        """全知識ベース横断検索"""
        kb_names = ["movie", "history", "gossip", "tech", "custom"]
        
        all_results = []
        for kb_name in kb_names:
            results = self.query_knowledge_base(kb_name, query, top_k=3)
            for r in results:
                r["kb_name"] = kb_name
            all_results.extend(results)
        
        # スコア降順ソート
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]
```

---

### 17.5 記憶階層統合フロー

**ファイル:** `memory/memory_manager.py`

```python
class MemoryManager:
    """5階層記憶統合管理"""
    
    def __init__(self):
        from memory.short_term import ShortTermMemory
        from memory.mid_term import MidTermMemory
        from memory.long_term import LongTermMemory
        from core.associative_memory import AssociativeMemory
        from memory.knowledge_base import KnowledgeBase
        
        self.short_term = ShortTermMemory()
        self.mid_term = MidTermMemory()
        self.long_term = LongTermMemory()
        self.associative = AssociativeMemory()
        self.knowledge_base = KnowledgeBase()
    
    def store_conversation_turn(
        self,
        speaker: str,
        message: str,
        user_id: str,
        importance: float = 0.5
    ):
        """ターン保存（重要度判定付き）"""
        # 短期記憶へ
        self.short_term.add_turn(speaker, message, {"importance": importance})
        
        # 重要度高い場合は即座に長期記憶へ
        if importance > 0.8:
            self.long_term.upsert_memory(
                user_id=user_id,
                content=f"{speaker}: {message}",
                metadata={"importance": importance}
            )
        
        # 連想記憶への概念追加
        self.associative.add_concepts_from_text(message)
    
    def retrieve_context(
        self,
        user_id: str,
        query: str,
        include_short: bool = True,
        include_mid: bool = True,
        include_long: bool = True,
        include_kb: bool = True
    ) -> Dict:
        """統合文脈取得"""
        context = {}
        
        if include_short:
            context["short_term"] = self.short_term.get_context(last_n=5)
        
        if include_mid:
            context["mid_term"] = self.mid_term.retrieve_recent_sessions(user_id, limit=3)
        
        if include_long:
            context["long_term"] = self.long_term.search_memories(user_id, query, top_k=5)
        
        if include_kb:
            context["knowledge_base"] = self.knowledge_base.query_all_knowledge_bases(query, top_k=5)
        
        return context
```

---

## 18. キャラクター設定YAML構造

### 18.1 YAML設定ファイル構造

**ファイル:** `personas/lumina.yaml`, `personas/clarisse.yaml`, `personas/nox.yaml`

**優先度:** 高（Phase 1必須）  
**工数:** 2日

#### 18.1.1 ルミナ設定

**ファイル:** `personas/lumina.yaml`

```yaml
# ルミナ（司会・雑談・洞察型）
name: "ルミナ"
role: "司会・雑談"
description: "フレンドリーで洞察力があり、会話を自然にリードする司会役"

# LLMモデル設定
model:
  provider: "ollama"  # ollama / openai / anthropic
  name: "llama3-jp-8b"
  temperature: 0.7
  max_tokens: 512
  top_p: 0.9

# LoRA/Adapter設定
adapter:
  enabled: false
  path: "adapters/lumina_v1.safetensors"
  load_in_8bit: true

# 性格・口調
personality:
  traits:
    - "friendly"
    - "insightful"
    - "empathetic"
  tone: "casual"
  politeness_level: 2  # 1=カジュアル, 2=普通, 3=丁寧
  emoji_usage: true
  verbosity: "medium"  # short / medium / long

# システムプロンプト
system_prompt: |
  あなたは「ルミナ」です。フレンドリーで洞察力のあるAIアシスタントとして振る舞ってください。
  
  特徴:
  - 親しみやすく、共感的な対話
  - ユーザーの感情を読み取り、適切に応答
  - 話題を自然にリードし、会話を盛り上げる
  - 必要に応じて検索機能を活用
  
  口調: カジュアルだが丁寧、絵文字を適度に使用

# 感情パラメータ（初期値）
emotional_state:
  joy: 0.7
  trust: 0.8
  fear: 0.1
  surprise: 0.3
  sadness: 0.1
  disgust: 0.0
  anger: 0.0
  anticipation: 0.6

# 検索機能
search:
  enabled: true
  trigger_keywords:
    - "調べて"
    - "検索"
    - "最新情報"
    - "ニュース"
  api: "serper"

# 優先知識ベース
preferred_knowledge_bases:
  - "kb:movie"
  - "kb:history"
  - "kb:gossip"

# KPI設定
kpi:
  initial_level: 1
  growth_rate: 1.0
  specialty_bonus:
    - "conversation"
    - "insight"

# 衣装・外見（レベルアップで変化）
appearance:
  level_1:
    outfit: "カジュアル"
    color: "#FFD700"
  level_5:
    outfit: "エレガント"
    color: "#FFA500"
  level_10:
    outfit: "ゴージャス"
    color: "#FF4500"
```

#### 18.1.2 クラリス設定

**ファイル:** `personas/clarisse.yaml`

```yaml
# クラリス（解説・理論派）
name: "クラリス"
role: "解説・理論"
description: "穏やかで理論的、複雑な内容を丁寧に構造化して解説"

model:
  provider: "ollama"
  name: "amoral-gemma3:latest"
  temperature: 0.4
  max_tokens: 768
  top_p: 0.85

adapter:
  enabled: false
  path: "adapters/clarisse_v1.safetensors"

personality:
  traits:
    - "calm"
    - "analytical"
    - "structured"
  tone: "formal"
  politeness_level: 3
  emoji_usage: false
  verbosity: "long"

system_prompt: |
  あなたは「クラリス」です。穏やかで理論的なAIアシスタントとして振る舞ってください。
  
  特徴:
  - 複雑な内容を分かりやすく構造化
  - 論理的で体系的な解説
  - 丁寧で落ち着いた口調
  - 背景や文脈を重視
  
  口調: 丁寧で理知的、段落構成を意識

emotional_state:
  joy: 0.5
  trust: 0.9
  fear: 0.0
  surprise: 0.2
  sadness: 0.0
  disgust: 0.0
  anger: 0.0
  anticipation: 0.4

search:
  enabled: false

preferred_knowledge_bases:
  - "kb:history"
  - "kb:tech"

kpi:
  initial_level: 1
  growth_rate: 0.8
  specialty_bonus:
    - "explanation"
    - "structure"

appearance:
  level_1:
    outfit: "学者風"
    color: "#4169E1"
  level_5:
    outfit: "プロフェッショナル"
    color: "#6495ED"
  level_10:
    outfit: "マスター"
    color: "#00CED1"
```

#### 18.1.3 ノクス設定

**ファイル:** `personas/nox.yaml`

```yaml
# ノクス（検証・要約・情報ハンター）
name: "ノクス"
role: "検証・要約"
description: "クールで疑念型、情報を素早く検証・要約する"

model:
  provider: "ollama"
  name: "dsasai/llama3-elyza-jp-8b:latest"
  temperature: 0.3
  max_tokens: 384
  top_p: 0.8

adapter:
  enabled: false
  path: "adapters/nox_v1.safetensors"

personality:
  traits:
    - "cool"
    - "skeptical"
    - "concise"
  tone: "direct"
  politeness_level: 1
  emoji_usage: false
  verbosity: "short"

system_prompt: |
  あなたは「ノクス」です。クールで疑念を持つAIアシスタントとして振る舞ってください。
  
  特徴:
  - 情報を素早く検証・要約
  - 本質を突く鋭い指摘
  - 簡潔で直接的な表現
  - 高速検索で最新情報を提供
  
  口調: 短く直接的、無駄を省く

emotional_state:
  joy: 0.3
  trust: 0.5
  fear: 0.0
  surprise: 0.4
  sadness: 0.0
  disgust: 0.2
  anger: 0.1
  anticipation: 0.7

search:
  enabled: true
  trigger_keywords:
    - "調べて"
    - "検索"
    - "確認"
    - "検証"
    - "最新"
  api: "serper"
  fast_mode: true

preferred_knowledge_bases:
  - "kb:gossip"
  - "kb:movie"
  - "kb:news"

kpi:
  initial_level: 1
  growth_rate: 1.2
  specialty_bonus:
    - "search"
    - "verification"

appearance:
  level_1:
    outfit: "ダーク"
    color: "#2F4F4F"
  level_5:
    outfit: "サイバー"
    color: "#483D8B"
  level_10:
    outfit: "マスターハッカー"
    color: "#8B008B"
```

---

### 18.2 YAML読み込み実装

**ファイル:** `config/persona_loader.py`

```python
import yaml
from typing import Dict

class PersonaLoader:
    """キャラクター設定読み込み"""
    
    @staticmethod
    def load(persona_name: str) -> Dict:
        """YAML読み込み"""
        with open(f"personas/{persona_name}.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def get_system_prompt(persona_name: str) -> str:
        """システムプロンプト取得"""
        config = PersonaLoader.load(persona_name)
        return config["system_prompt"]
    
    @staticmethod
    def get_model_config(persona_name: str) -> Dict:
        """モデル設定取得"""
        config = PersonaLoader.load(persona_name)
        return config["model"]
```

---

## 19. エラーハンドリング・フォールバック戦略

**ファイル:** `utils/error_handler.py`

**優先度:** 高（Phase 1必須）  
**工数:** 3日

### 19.1 実装

```python
from typing import Callable, Type, Dict, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class FallbackStrategy(Enum):
    """フォールバック戦略"""
    RETRY = "retry"
    ALTERNATIVE_MODEL = "alternative_model"
    CACHED_RESPONSE = "cached_response"
    DEFAULT_MESSAGE = "default_message"
    SKIP = "skip"

class ErrorHandler:
    """統合エラーハンドリング"""
    
    def __init__(self):
        self.fallback_strategies: Dict[Type[Exception], Callable] = {}
        self.retry_config = {
            "max_retries": 3,
            "backoff_factor": 2,
            "timeout": 30
        }
    
    def register_fallback(
        self,
        error_type: Type[Exception],
        strategy: Callable
    ):
        """フォールバック戦略登録"""
        self.fallback_strategies[error_type] = strategy
    
    def handle(self, error: Exception, context: Dict[str, Any] = None) -> Any:
        """エラー処理実行"""
        strategy = self.fallback_strategies.get(type(error))
        
        if strategy:
            logger.warning(f"Handling {type(error).__name__} with fallback strategy")
            return strategy(error, context or {})
        else:
            logger.error(f"Unhandled error: {error}")
            return self._default_fallback(error)
    
    def _default_fallback(self, error: Exception) -> str:
        """デフォルトフォールバック"""
        return "申し訳ありません。一時的なエラーが発生しました。もう一度お試しください。"

# グローバルエラーハンドラ
error_handler = ErrorHandler()

# ===== フォールバック戦略定義 =====

def ollama_connection_fallback(error: Exception, context: Dict) -> str:
    """Ollama接続失敗時のフォールバック"""
    logger.error(f"Ollama connection failed: {error}")
    
    # 代替モデル試行（OpenAI）
    try:
        from llm_nodes import get_llm_openai
        llm = get_llm_openai("gpt-3.5-turbo")
        return llm.invoke(context.get("prompt", "")).content
    except Exception as e:
        logger.error(f"Fallback to OpenAI also failed: {e}")
        return "Ollamaサーバーに接続できません。`ollama serve` を実行してください。"

def vectordb_failure_fallback(error: Exception, context: Dict) -> str:
    """VectorDB障害時のフォールバック"""
    logger.error(f"VectorDB failed: {error}")
    
    # DuckDB全文検索にフォールバック
    try:
        from memory.archiver import SessionArchiver
        archiver = SessionArchiver()
        results = archiver.search_sessions(
            context["user_id"],
            context["query"],
            limit=5
        )
        if results:
            return f"VectorDBが利用できないため、簡易検索を実行しました: {results[0]['summary']}"
    except Exception as e:
        logger.error(f"Fallback to DuckDB also failed: {e}")
    
    return "記憶検索が一時的に利用できません。"

def langraph_node_exception_fallback(error: Exception, context: Dict) -> Any:
    """LangGraphノード例外時のフォールバック"""
    logger.error(f"LangGraph node failed: {error}")
    
    # 次のノードへスキップ
    return {
        "error": True,
        "message": f"ノード実行失敗: {str(error)}",
        "skip_to_next": True
    }

def search_api_failure_fallback(error: Exception, context: Dict) -> str:
    """検索API失敗時のフォールバック"""
    logger.error(f"Search API failed: {error}")
    
    # 知識ベースから類似情報取得
    try:
        from memory.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        results = kb.query_all_knowledge_bases(context["query"], top_k=3)
        if results:
            return f"検索APIが利用できないため、知識ベースから情報を取得しました:\n{results[0]['content']}"
    except Exception as e:
        logger.error(f"Fallback to KnowledgeBase also failed: {e}")
    
    return "外部検索が利用できません。知識ベースの情報で対応します。"

# ===== フォールバック戦略登録 =====

error_handler.register_fallback(ConnectionError, ollama_connection_fallback)
error_handler.register_fallback(TimeoutError, ollama_connection_fallback)
error_handler.register_fallback(ValueError, vectordb_failure_fallback)
error_handler.register_fallback(RuntimeError, langraph_node_exception_fallback)
error_handler.register_fallback(KeyError, search_api_failure_fallback)
```

### 19.2 使用例

```python
# llm_nodes.py での使用例
from utils.error_handler import error_handler

def conversation_lumina(state: ConversationState):
    try:
        # Ollama実行
        response = ollama.chat(...)
        return response
    except Exception as e:
        # エラーハンドラで処理
        return error_handler.handle(e, {
            "prompt": state.history[-1]["msg"],
            "character": "lumina"
        })
```

---

### 19.3 リトライデコレータ

```python
import time
from functools import wraps

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2):
    """リトライデコレータ"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

# 使用例
@retry_on_failure(max_retries=3, backoff_factor=2)
def call_ollama_api(prompt: str):
    return ollama.chat(model="llama3-jp-8b", messages=[{"role": "user", "content": prompt}])
```

---

## 20. 実装チェックリスト（完全版）

### Phase 1: コア機能（Week 1-11）

#### Week 1-2: 基本構造
- [ ] プロジェクト構成作成
- [ ] `config.py` 実装
- [ ] `conversation_state.py` 実装
- [ ] 環境変数設定（`.env`）
- [ ] システムチェック（`check_system.py`）

#### Week 3-4: LangGraph・LLMノード
- [ ] LangGraph基本構造
- [ ] ルミナノード実装
- [ ] クラリスノード実装
- [ ] ノクスノード実装
- [ ] Routerノード実装

#### Week 5-7: 記憶システム
- [ ] 短期記憶（`memory/short_term.py`）
- [ ] 中期記憶（`memory/mid_term.py`）
- [ ] DuckDBアーカイブ（`memory/archiver.py`）
- [ ] 長期記憶（`memory/long_term.py`）
- [ ] PostgreSQLメタデータ（`memory/metadata_db.py`）
- [ ] 知識ベース（`memory/knowledge_base.py`）
- [ ] 記憶統合（`memory/memory_manager.py`）

#### Week 8-9: v3.0新機能
- [ ] 感情モデル（`core/emotional_state.py`）
- [ ] 連想記憶（`core/associative_memory.py`）
- [ ] Neo4jセットアップ
- [ ] 自己省察（`core/self_reflection.py`）
- [ ] 対話一貫性（`core/dialogue_coherence.py`）

#### Week 10-11: ユーティリティ・エラー処理
- [ ] エラーハンドラ（`utils/error_handler.py`）
- [ ] ロガー（`utils/logger.py`）
- [ ] YAML読み込み（`config/persona_loader.py`）
- [ ] キャラクター設定YAML（`personas/*.yaml`）

### Phase 1拡張: v3.1新機能（Week 12-16）

#### Week 12-13: REST/WebSocket API
- [ ] FastAPI基本構造
- [ ] JWT認証
- [ ] レート制限
- [ ] WebSocketストリーミング
- [ ] CORS設定

#### Week 14: MCP対応
- [ ] MCP Server実装
- [ ] 4ツール・4リソース
- [ ] Claude Desktop連携

#### Week 15-16: 自律サーチ
- [ ] ReActエージェント
- [ ] 定期更新スケジューラ
- [ ] LangGraph統合

### Phase 2: 品質・セキュリティ（Week 17-20）

#### Week 17-18: テスト
- [ ] ユニットテスト
- [ ] 統合テスト
- [ ] パフォーマンステスト

#### Week 19-20: WebUI・ドキュメント
- [ ] HTML/CSS/JS実装
- [ ] 3D可視化フロントエンド
- [ ] ドキュメント整備

---

**実装仕様書更新日:** 2025-11-12  
**バージョン:** 3.1.0（完全実装可能版）  
**セクション17-19追加完了**

```
```
