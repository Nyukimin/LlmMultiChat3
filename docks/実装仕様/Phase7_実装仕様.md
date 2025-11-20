# Phase 7 実装仕様書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 7 - 3D可視化 + 自律サーチ  
**期間**: 4週間  
**作成日**: 2025-11-20  
**Phase 6完了前提**: キャラクター成長・MCP Server実装済み

---

## 目次

1. [Phase 7概要](#1-phase-7概要)
2. [前提条件](#2-前提条件)
3. [Week 1-2: 3D可視化パネル](#3-week-1-2-3d可視化パネル)
4. [Week 3-4: 自律的外部サーチエージェント](#4-week-3-4-自律的外部サーチエージェント)
5. [技術スタック](#5-技術スタック)
6. [テスト計画（TDD実装）](#6-テスト計画tdd実装)
   - [TDD実装仕様サマリー](#60-tdd実装仕様サマリー)
   - [テストカバレッジ目標](#61-テストカバレッジ目標)
   - [テスト実行方法](#62-テスト実行方法)
   - [Week 1-2: 3D可視化パネル - テスト仕様（TDD）](#week-1-2-3d可視化パネル---テスト仕様tdd)
   - [Week 3-4: 自律的外部サーチエージェント - テスト仕様（TDD）](#week-3-4-自律的外部サーチエージェント---テスト仕様tdd)
   - [統合テスト仕様（TDD）](#統合テスト仕様tdd)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [テスト実行戦略](#テスト実行戦略)
7. [成果物](#7-成果物)
8. [Phase 7成功基準](#8-phase-7成功基準)

---

## 1. Phase 7概要

### 1.1 目的

連想ネットワークの3D可視化と自律情報収集により、**視覚的理解と知識の自動拡張**を実現します。

### 1.2 TDD実装アプローチ

Phase 7は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

```
1. 🔴 RED: テストを書く（失敗する）
2. 🟢 GREEN: 最小限の実装でテストを通す
3. 🔵 REFACTOR: コードをリファクタリング（テストは常に成功）
```

**TDDの原則**:
- ✅ 実装前に必ずテストを書く
- ✅ 1つのテスト → 1つの実装 → リファクタリングのサイクル
- ✅ Given-When-Then形式でテストを記述
- ✅ 各テストは独立して実行可能
- ✅ 外部依存はモックで分離

### 1.3 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **3D可視化** | 連想記憶ネットワークの可視化 | 🟡 Medium |
| **インタラクティブ操作** | ドラッグ・ズーム・クリック | 🟡 Medium |
| **自律サーチ** | 自動Web検索・KB保存 | 🔴 High |
| **定期更新** | スケジュール実行 | 🔴 High |

### 1.3 達成目標

✅ 3D可視化パネル動作確認  
✅ 自律サーチ定期実行テスト成功  
✅ KB自動更新確認  
✅ Plotly.js統合完了

---

## 2. 前提条件

### 2.1 Phase 1-6完了事項

✅ **Phase 1**: LangGraphコア・5階層記憶システム  
✅ **Phase 2**: エラーハンドリング・セキュリティ  
✅ **Phase 3**: REST/WebSocket API（23エンドポイント）  
✅ **Phase 4**: 連想記憶システム・感情モデル基盤  
✅ **Phase 5**: 対話スタイル適応・自己省察  
✅ **Phase 6**: キャラクター成長・MCP Server

**参照**: [`docks/実装仕様/Phase6_実装仕様.md`](Phase6_実装仕様.md:1)

### 2.2 利用可能なPhase 4機能

- **連想記憶システム**: [`memory/associative.py`](../../memory/associative.py)
- **SQLite Graph**: 再帰CTE連想検索

---

## 3. Week 1-2: 3D可視化パネル

### 3.1 実装内容

**参照**: [`docks/仕様書/06_会話LLM_3D可視化仕様.md`](../仕様書/06_会話LLM_3D可視化仕様.md)

#### 3.1.1 Plotly.js 3Dグラフ

**主要機能**:
1. **ノード描画**: 概念を球体で表現
2. **エッジ描画**: 関連性を線で表現
3. **Force-Directed Layout**: 物理シミュレーション配置
4. **色・サイズによる情報表現**:
   - ノード色: 距離（青→緑→黄→赤）
   - ノードサイズ: 活性化回数
   - エッジ色: 関連性強度（薄灰→濃灰）

#### 3.1.2 インタラクティブ操作

- **ドラッグ回転**: マウスドラッグで3D空間回転
- **ホイールズーム**: マウスホイールでズーム
- **ノードクリック**: クリックで詳細表示

#### 3.1.3 ON/OFF切り替え

- **デフォルトOFF**: パフォーマンス考慮
- **リアルタイム更新**: 会話中に自動更新（ON時）

### 3.2 ファイル構成

#### visualization/association_3d.py (500行)

```python
"""連想記憶3D可視化モジュール."""

from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from memory.associative import AssociativeMemory


class AssociationVisualizationPanel:
    """連想記憶3D可視化パネル."""
    
    def __init__(self, associative_memory: AssociativeMemory):
        """
        初期化.
        
        Args:
            associative_memory: 連想記憶システムインスタンス
        """
        self.associative_memory = associative_memory
        self.is_enabled = False
        self.current_center = None
        self.max_nodes = 50  # パフォーマンス制限
    
    def toggle(self) -> bool:
        """
        ON/OFF切り替え.
        
        Returns:
            bool: 新しい状態（True=ON, False=OFF）
        """
        self.is_enabled = not self.is_enabled
        return self.is_enabled
    
    def update_center(self, concept: str) -> None:
        """
        中心概念更新.
        
        Args:
            concept: 中心となる概念
        """
        self.current_center = concept
        if self.is_enabled:
            self._render_graph()
    
    def _render_graph(self) -> go.Figure:
        """
        3Dグラフ描画.
        
        Returns:
            go.Figure: Plotly Figure
        """
        if not self.current_center:
            return go.Figure()
        
        # 連想概念取得
        associated = self.associative_memory.retrieve_associated_concepts(
            trigger=self.current_center,
            depth=3,
            threshold=0.3
        )
        
        # 最大ノード数制限
        if len(associated) > self.max_nodes:
            associated = associated[:self.max_nodes]
        
        # ノード座標計算（Force-Directed Layout簡易版）
        node_positions = self._calculate_positions(associated)
        
        # エッジ取得
        edges = self._get_edges(associated)
        
        # ノードトレース作成
        node_trace = self._create_node_trace(associated, node_positions)
        
        # エッジトレース作成
        edge_traces = self._create_edge_traces(edges, node_positions)
        
        # Figure作成
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title=f"連想ネットワーク - 中心: {self.current_center}",
            showlegend=False,
            hovermode='closest',
            scene=dict(
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                zaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
            margin=dict(l=0, r=0, b=0, t=40),
        )
        
        return fig
    
    def _calculate_positions(
        self,
        concepts: List[Dict[str, Any]]
    ) -> Dict[str, tuple]:
        """
        ノード座標計算（Force-Directed Layout簡易版）.
        
        Args:
            concepts: 概念リスト
        
        Returns:
            Dict[str, tuple]: {概念名: (x, y, z)}
        """
        import random
        import math
        
        positions = {}
        
        # 中心を原点に配置
        positions[self.current_center] = (0.0, 0.0, 0.0)
        
        # 他の概念を距離に応じて配置
        for concept in concepts:
            if concept['name'] == self.current_center:
                continue
            
            depth = concept.get('depth', 1)
            
            # 球面座標でランダム配置
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            radius = depth * 2.0  # 距離に応じた半径
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            positions[concept['name']] = (x, y, z)
        
        return positions
    
    def _get_edges(
        self,
        concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        エッジ取得.
        
        Args:
            concepts: 概念リスト
        
        Returns:
            List[Dict]: エッジリスト
        """
        edges = []
        
        # 各概念間のエッジを取得（実際はDBから取得）
        concept_names = [c['name'] for c in concepts]
        
        # 簡易実装: 隣接概念とのみ接続
        for i, concept in enumerate(concepts):
            if i == 0:
                continue
            edges.append({
                'from': self.current_center if concept.get('depth', 1) == 1 else concepts[i-1]['name'],
                'to': concept['name'],
                'strength': concept.get('strength', 0.5)
            })
        
        return edges
    
    def _create_node_trace(
        self,
        concepts: List[Dict[str, Any]],
        positions: Dict[str, tuple]
    ) -> go.Scatter3d:
        """
        ノードトレース作成.
        
        Args:
            concepts: 概念リスト
            positions: 座標辞書
        
        Returns:
            go.Scatter3d: ノードトレース
        """
        node_x, node_y, node_z = [], [], []
        node_text, node_color, node_size = [], [], []
        
        for concept in concepts:
            name = concept['name']
            if name not in positions:
                continue
            
            x, y, z = positions[name]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            node_text.append(name)
            node_color.append(self._get_node_color(concept.get('depth', 0)))
            node_size.append(10 + concept.get('activation_count', 0))
        
        return go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            marker=dict(
                size=node_size,
                color=node_color,
                colorscale='Viridis',
                line=dict(color='white', width=0.5)
            ),
            hoverinfo='text'
        )
    
    def _create_edge_traces(
        self,
        edges: List[Dict[str, Any]],
        positions: Dict[str, tuple]
    ) -> List[go.Scatter3d]:
        """
        エッジトレース作成.
        
        Args:
            edges: エッジリスト
            positions: 座標辞書
        
        Returns:
            List[go.Scatter3d]: エッジトレースリスト
        """
        edge_traces = []
        
        for edge in edges:
            from_name = edge['from']
            to_name = edge['to']
            
            if from_name not in positions or to_name not in positions:
                continue
            
            x0, y0, z0 = positions[from_name]
            x1, y1, z1 = positions[to_name]
            
            edge_trace = go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode='lines',
                line=dict(
                    color=self._get_edge_color(edge['strength']),
                    width=2
                ),
                hoverinfo='none'
            )
            
            edge_traces.append(edge_trace)
        
        return edge_traces
    
    def _get_edge_color(self, strength: float) -> str:
        """
        エッジ色取得.
        
        Args:
            strength: 関連性強度 (0.0-1.0)
        
        Returns:
            str: 色コード
        """
        # 薄灰 → 濃灰
        gray_value = int(200 - strength * 100)
        return f'rgb({gray_value}, {gray_value}, {gray_value})'
    
    def _get_node_color(self, distance: int) -> int:
        """
        ノード色取得（距離ベース）.
        
        Args:
            distance: 中心からの距離
        
        Returns:
            int: 色値（0-3）
        """
        # 0=青, 1=緑, 2=黄, 3=赤
        return min(distance, 3)
    
    def export_html(self, filename: str) -> None:
        """
        HTML出力.
        
        Args:
            filename: 出力ファイル名
        """
        fig = self._render_graph()
        fig.write_html(filename)
    
    def export_png(self, filename: str) -> None:
        """
        PNG出力.
        
        Args:
            filename: 出力ファイル名
        """
        fig = self._render_graph()
        fig.write_image(filename)


class VisualizationControls:
    """可視化コントロールUI."""
    
    def render_controls(self) -> str:
        """
        コントロールHTML生成.
        
        Returns:
            str: HTML文字列
        """
        return """
        <div id="viz-controls">
            <button onclick="toggleVisualization()">可視化 ON/OFF</button>
            <input type="text" id="center-concept" placeholder="中心概念">
            <button onclick="updateCenter()">更新</button>
        </div>
        """
```

### 3.3 テスト仕様（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

#### テストファイル構成

- `tests/test_visualization.py`: AssociationVisualizationPanelクラスのユニットテスト（30件）
- `tests/test_integration_visualization.py`: 連想記憶連携の統合テスト（10件）

#### テストデータ定義

```python
# tests/fixtures/visualization_fixtures.py

TEST_CONCEPTS = [
    "機械学習",
    "Python",
    "データベース",
    "Web開発",
    "自然言語処理"
]

TEST_CONCEPT_PAIRS = [
    ("機械学習", "Python", 0.8),
    ("Python", "データベース", 0.6),
    ("Web開発", "Python", 0.7),
]

TEST_DEPTHS = [1, 2, 3]
TEST_THRESHOLDS = [0.1, 0.3, 0.5, 0.7, 0.9]
TEST_MAX_NODES = [10, 50, 100, 1000]
```

---

## 4. Week 3-4: 自律的外部サーチエージェント

### 4.1 実装内容

**参照**: [`docks/仕様書/01_会話LLM_仕様.md:531-561`](../仕様書/01_会話LLM_仕様.md:531)

#### 4.1.1 トリガー条件判定

**3つのトリガー**:
1. **ユーザー質問時**: KB検索で回答なし
2. **定期実行**: スケジュール設定
3. **手動トリガー**: ユーザー明示的指示

#### 4.1.2 検索ツール統合

```python
# 1. Serper API（Google検索）
{
    "url": "https://google.serper.dev/search",
    "headers": {"X-API-KEY": "YOUR_SERPER_API_KEY"},
    "params": {"q": "最新AI技術", "gl": "jp", "hl": "ja"}
}

# 2. Wikipedia検索
{
    "library": "wikipedia",
    "lang": "ja",
    "query": "機械学習"
}
```

#### 4.1.3 定期更新スケジューラ

| 頻度 | 時刻 | トピック |
|------|------|---------|
| 毎日 | 06:00 | ニュース・トレンド |
| 毎週日曜 | 10:00 | 映画情報 |
| 毎月1日 | 00:00 | 技術情報 |

### 4.2 ファイル構成

#### agents/autonomous_search.py (350行)

```python
"""自律的外部サーチエージェント."""

from typing import Dict, List, Any, Optional
import requests
import wikipedia
from memory.knowledge_base import KnowledgeBase


class AutonomousSearchAgent:
    """自律サーチエージェント."""
    
    def __init__(self, serper_api_key: Optional[str] = None):
        """
        初期化.
        
        Args:
            serper_api_key: Serper API KEY
        """
        self.serper_api_key = serper_api_key
        self.kb = KnowledgeBase()
        wikipedia.set_lang("ja")
    
    def should_search(
        self,
        user_question: str,
        kb_results: List[Dict[str, Any]]
    ) -> bool:
        """
        検索必要性判定.
        
        Args:
            user_question: ユーザー質問
            kb_results: KB検索結果
        
        Returns:
            bool: True=検索実行
        """
        # KB結果なし または 信頼度低い
        if not kb_results:
            return True
        
        if kb_results[0].get('similarity', 0.0) < 0.6:
            return True
        
        return False
    
    def web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Web検索（Serper API）.
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
        
        Returns:
            List[Dict]: 検索結果
        """
        if not self.serper_api_key:
            return []
        
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "gl": "jp",
            "hl": "ja",
            "num": max_results
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("organic", [])[:max_results]:
                results.append({
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "link": item.get("link")
                })
            
            return results
        
        except requests.RequestException as e:
            print(f"Web検索エラー: {e}")
            return []
    
    def wikipedia_search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Wikipedia検索.
        
        Args:
            query: 検索クエリ
        
        Returns:
            Optional[Dict]: Wikipedia記事
        """
        try:
            page = wikipedia.page(query, auto_suggest=True)
            
            return {
                "title": page.title,
                "summary": wikipedia.summary(query, sentences=3),
                "content": page.content,
                "url": page.url
            }
        
        except wikipedia.exceptions.PageError:
            print(f"Wikipedia記事なし: {query}")
            return None
        
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"曖昧性解消必要: {e.options[:3]}")
            # 最初の候補で再試行
            if e.options:
                return self.wikipedia_search(e.options[0])
            return None
    
    def save_to_kb(
        self,
        content: str,
        category: str,
        source: str = "autonomous_search"
    ) -> None:
        """
        KB保存.
        
        Args:
            content: コンテンツ
            category: カテゴリ
            source: ソース
        """
        self.kb.store(
            content=content,
            category=category,
            metadata={"source": source}
        )
```

#### scheduler/update_scheduler.py (200行)

```python
"""定期更新スケジューラ."""

from typing import Callable
import schedule
import time
from agents.autonomous_search import AutonomousSearchAgent


class UpdateScheduler:
    """定期更新スケジューラ."""
    
    def __init__(self, search_agent: AutonomousSearchAgent):
        """
        初期化.
        
        Args:
            search_agent: サーチエージェント
        """
        self.search_agent = search_agent
    
    def schedule_daily_news(self) -> None:
        """毎朝6時: ニュース・トレンド."""
        schedule.every().day.at("06:00").do(self._fetch_news)
    
    def schedule_weekly_movies(self) -> None:
        """毎週日曜10時: 映画情報."""
        schedule.every().sunday.at("10:00").do(self._fetch_movies)
    
    def schedule_monthly_tech(self) -> None:
        """毎月1日0時: 技術情報."""
        schedule.every().month.at("00:00").do(self._fetch_tech)
    
    def _fetch_news(self) -> None:
        """ニュース取得."""
        results = self.search_agent.web_search("最新ニュース", max_results=5)
        
        for result in results:
            self.search_agent.save_to_kb(
                content=f"{result['title']}: {result['snippet']}",
                category="news"
            )
    
    def _fetch_movies(self) -> None:
        """映画情報取得."""
        results = self.search_agent.web_search("今週公開映画", max_results=3)
        
        for result in results:
            self.search_agent.save_to_kb(
                content=f"{result['title']}: {result['snippet']}",
                category="movies"
            )
    
    def _fetch_tech(self) -> None:
        """技術情報取得."""
        topics = ["Python最新情報", "機械学習トレンド", "Web開発技術"]
        
        for topic in topics:
            wiki = self.search_agent.wikipedia_search(topic)
            if wiki:
                self.search_agent.save_to_kb(
                    content=wiki['summary'],
                    category="tech"
                )
    
    def run(self) -> None:
        """スケジューラ実行."""
        while True:
            schedule.run_pending()
            time.sleep(60)
```

### 4.3 テスト仕様（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

#### テストファイル構成

- `tests/test_autonomous_search.py`: AutonomousSearchAgentクラスのユニットテスト（30件）
- `tests/test_scheduler.py`: UpdateSchedulerクラスのユニットテスト（15件）
- `tests/test_integration_search.py`: KB連携・スケジューラ統合テスト（10件）

#### テストデータ定義

```python
# tests/fixtures/autonomous_search_fixtures.py

TEST_QUERIES = [
    "機械学習",
    "Python",
    "最新ニュース",
    "",  # 空クエリ（エッジケース）
    "a" * 1000,  # 長いクエリ（エッジケース）
]

TEST_KB_RESULTS = [
    [],  # 空の結果
    [{"similarity": 0.5}],  # 低信頼度
    [{"similarity": 0.6}],  # 境界値
    [{"similarity": 0.9}],  # 高信頼度
]

TEST_MAX_RESULTS = [1, 5, 10, 0, -1, 1000]  # 正常値とエッジケース

TEST_CATEGORIES = ["news", "movies", "tech", "general"]
TEST_SOURCES = ["autonomous_search", "manual", "scheduled"]
```

---

## 5. 技術スタック

### 5.1 Python依存

```txt
# requirements.txt に追加
plotly==5.17.0          # 3D可視化
kaleido==0.2.1          # 画像出力
wikipedia==1.4.0        # Wikipedia検索
requests==2.31.0        # HTTP通信
schedule==1.2.0         # スケジューラ
```

### 5.2 新規モジュール

- **visualization/association_3d.py**: 3D可視化パネル
- **agents/autonomous_search.py**: 自律サーチエージェント
- **scheduler/update_scheduler.py**: 定期更新スケジューラ

---

## 6. テスト計画（TDD実装）

### 6.0 TDD実装仕様サマリー

**Phase 7は完全なTDD（テスト駆動開発）アプローチで実装します。**

#### TDD実装の原則

1. **テストファースト**: すべての機能は実装前にテストを書く
2. **RED-GREEN-REFACTORサイクル**: 失敗→成功→リファクタリングのサイクルを徹底
3. **Given-When-Then形式**: すべてのテストを明確な形式で記述
4. **テスト独立性**: 各テストは独立して実行可能
5. **モック分離**: 外部依存（API、Wikipedia等）はモックで分離

#### テスト構成

| カテゴリ | テストファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|--------------|---------|--------------|--------|
| **3D可視化パネル** |
| AssociationVisualizationPanel | `test_visualization.py` | 30件 + エッジケース10件 + パラメータ化5件 | 90%以上 | 🟡 Medium |
| **自律サーチエージェント** |
| AutonomousSearchAgent | `test_autonomous_search.py` | 30件 + エッジケース10件 + パラメータ化5件 | 90%以上 | 🔴 High |
| UpdateScheduler | `test_scheduler.py` | 15件 + エッジケース5件 | 85%以上 | 🔴 High |
| **統合テスト** |
| 連想記憶連携 | `test_integration_visualization.py` | 10件 | 85%以上 | 🟡 Medium |
| KB連携・スケジューラ | `test_integration_search.py` | 10件 | 85%以上 | 🟡 Medium |
| **合計** | **5ファイル + フィクスチャ2ファイル** | **120件以上** | **平均88%以上** | - |

#### テスト実行戦略

- **Week 1-2**: 3D可視化パネル（6日間で段階的に実装）
- **Week 3-4**: 自律サーチエージェント（6日間で段階的に実装）
- **各機能**: RED → GREEN → REFACTORサイクルで実装
- **品質基準**: テスト成功率100%、カバレッジ88%以上、実行時間5分以内

### 6.1 テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| **3D可視化パネル** |
| AssociationVisualizationPanel | `test_visualization.py` | 45件 | 90%以上 | 🟡 Medium |
| **自律サーチエージェント** |
| AutonomousSearchAgent | `test_autonomous_search.py` | 45件 | 90%以上 | 🔴 High |
| UpdateScheduler | `test_scheduler.py` | 20件 | 85%以上 | 🔴 High |
| **統合テスト** |
| 連想記憶連携 | `test_integration_visualization.py` | 10件 | 85%以上 | 🟡 Medium |
| KB連携・スケジューラ | `test_integration_search.py` | 10件 | 85%以上 | 🟡 Medium |
| **合計** | **5ファイル** | **130件以上** | **平均88%以上** | - |

### 6.2 テスト実行方法

#### 基本的なテスト実行

```bash
# 全テスト実行
pytest tests/test_visualization.py tests/test_autonomous_search.py tests/test_scheduler.py -v

# カバレッジ付きテスト実行
pytest tests/ \
  --cov=visualization.association_3d \
  --cov=agents.autonomous_search \
  --cov=scheduler.update_scheduler \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=88

# 特定のテストのみ
pytest tests/test_visualization.py::test_panel_init -v

# マーカーで実行
pytest -m unit -v              # ユニットテストのみ
pytest -m integration -v      # 統合テストのみ
pytest -m slow -v             # 遅いテストのみ（API呼び出しなど）
pytest -m "not slow" -v       # 遅いテストを除外
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_visualization.py::test_panel_init -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_visualization.py::test_panel_init -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_visualization.py -v
# → 期待: 全テスト PASSED
```

---

## Week 1-2: 3D可視化パネル - テスト仕様（TDD）

### テストファイル: `tests/test_visualization.py`

**テストクラス**: `TestAssociationVisualizationPanel`, `TestVisualizationControls`

**テストケース一覧（45件）**:

#### 1. 初期化テスト（5件）

```python
def test_panel_init_default_state():
    """
    Given: AssociativeMemoryインスタンス
    When: AssociationVisualizationPanelを初期化
    Then: デフォルト状態で初期化される（is_enabled=False, current_center=None）
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    assert panel.is_enabled is False
    assert panel.current_center is None
    assert panel.max_nodes == 50
    assert panel.associative_memory is memory

def test_panel_init_with_custom_max_nodes():
    """
    Given: カスタムmax_nodes値
    When: AssociationVisualizationPanelを初期化
    Then: max_nodesが設定される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.max_nodes = 100
    
    assert panel.max_nodes == 100

def test_panel_init_with_none_memory():
    """
    Given: NoneのAssociativeMemory
    When: AssociationVisualizationPanelを初期化
    Then: エラーが発生する
    """
    with pytest.raises((TypeError, ValueError)):
        AssociationVisualizationPanel(None)
```

#### 2. ON/OFF切り替えテスト（5件）

```python
def test_toggle_from_off_to_on():
    """
    Given: パネルがOFF状態
    When: toggle()を呼び出す
    Then: ON状態になり、Trueが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    result = panel.toggle()
    
    assert result is True
    assert panel.is_enabled is True

def test_toggle_from_on_to_off():
    """
    Given: パネルがON状態
    When: toggle()を呼び出す
    Then: OFF状態になり、Falseが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.is_enabled = True
    
    result = panel.toggle()
    
    assert result is False
    assert panel.is_enabled is False

def test_toggle_multiple_times():
    """
    Given: パネル
    When: toggle()を複数回呼び出す
    Then: 状態が交互に切り替わる
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    assert panel.toggle() is True
    assert panel.toggle() is False
    assert panel.toggle() is True
    assert panel.toggle() is False
```

#### 3. 中心概念更新テスト（5件）

```python
def test_update_center_sets_center():
    """
    Given: 概念名
    When: update_center()を呼び出す
    Then: current_centerが設定される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    panel.update_center("機械学習")
    
    assert panel.current_center == "機械学習"

def test_update_center_triggers_render_when_enabled():
    """
    Given: パネルがON状態
    When: update_center()を呼び出す
    Then: グラフが描画される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.is_enabled = True
    
    # モックで_render_graphが呼ばれたことを確認
    with patch.object(panel, '_render_graph') as mock_render:
        panel.update_center("機械学習")
        mock_render.assert_called_once()

def test_update_center_empty_concept():
    """
    Given: 空の概念名
    When: update_center()を呼び出す
    Then: current_centerが空文字列に設定される（またはエラー）
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    panel.update_center("")
    
    assert panel.current_center == ""
```

#### 4. グラフ描画テスト（10件）

```python
def test_render_graph_with_no_center():
    """
    Given: current_centerがNone
    When: _render_graph()を呼び出す
    Then: 空のFigureが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    fig = panel._render_graph()
    
    assert fig is not None
    assert len(fig.data) == 0

def test_render_graph_with_concepts():
    """
    Given: 概念が存在する
    When: _render_graph()を呼び出す
    Then: ノードとエッジを含むFigureが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    # 概念追加
    memory.add_concept("機械学習", embedding=[0.1]*128, metadata={})
    memory.add_concept("Python", embedding=[0.2]*128, metadata={})
    memory.link_concepts("機械学習", "Python", "related", strength=0.8)
    
    panel.current_center = "機械学習"
    fig = panel._render_graph()
    
    assert fig is not None
    assert len(fig.data) > 0

def test_render_graph_max_nodes_limit():
    """
    Given: max_nodesを超える概念数
    When: _render_graph()を呼び出す
    Then: max_nodes数までに制限される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.max_nodes = 5
    
    # 10個の概念を追加
    for i in range(10):
        memory.add_concept(f"概念{i}", embedding=[0.1]*128, metadata={})
    
    panel.current_center = "概念0"
    
    with patch.object(memory, 'retrieve_associated_concepts') as mock_retrieve:
        mock_retrieve.return_value = [{"name": f"概念{i}"} for i in range(10)]
        fig = panel._render_graph()
        
        # max_nodesまでに制限されていることを確認
        # 実際の実装に応じて検証
```

#### 5. 座標計算テスト（5件）

```python
def test_calculate_positions_center_at_origin():
    """
    Given: 中心概念
    When: _calculate_positions()を呼び出す
    Then: 中心が原点(0,0,0)に配置される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    concepts = [{"name": "機械学習"}]
    positions = panel._calculate_positions(concepts)
    
    assert positions["機械学習"] == (0.0, 0.0, 0.0)

def test_calculate_positions_depth_based_radius():
    """
    Given: 異なるdepthの概念
    When: _calculate_positions()を呼び出す
    Then: depthに応じた半径で配置される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    concepts = [
        {"name": "機械学習", "depth": 0},
        {"name": "Python", "depth": 1},
        {"name": "データベース", "depth": 2}
    ]
    positions = panel._calculate_positions(concepts)
    
    # depth=1の概念は半径2.0、depth=2の概念は半径4.0の範囲内
    # 実際の座標値はランダムなので、範囲チェック
    assert "Python" in positions
    assert "データベース" in positions
```

#### 6. ノード・エッジ作成テスト（8件）

```python
def test_create_node_trace_with_concepts():
    """
    Given: 概念リストと座標
    When: _create_node_trace()を呼び出す
    Then: Scatter3dトレースが作成される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    concepts = [
        {"name": "機械学習", "depth": 0, "activation_count": 5}
    ]
    positions = {"機械学習": (0.0, 0.0, 0.0)}
    
    trace = panel._create_node_trace(concepts, positions)
    
    assert isinstance(trace, go.Scatter3d)
    assert len(trace.x) == 1

def test_create_edge_traces_with_edges():
    """
    Given: エッジリストと座標
    When: _create_edge_traces()を呼び出す
    Then: エッジトレースリストが作成される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    edges = [
        {"from": "機械学習", "to": "Python", "strength": 0.8}
    ]
    positions = {
        "機械学習": (0.0, 0.0, 0.0),
        "Python": (1.0, 1.0, 1.0)
    }
    
    traces = panel._create_edge_traces(edges, positions)
    
    assert len(traces) == 1
    assert isinstance(traces[0], go.Scatter3d)
```

#### 7. 色・サイズ計算テスト（5件）

```python
def test_get_node_color_by_distance():
    """
    Given: 異なる距離
    When: _get_node_color()を呼び出す
    Then: 距離に応じた色値が返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    assert panel._get_node_color(0) == 0  # 青
    assert panel._get_node_color(1) == 1  # 緑
    assert panel._get_node_color(2) == 2  # 黄
    assert panel._get_node_color(3) == 3  # 赤
    assert panel._get_node_color(10) == 3  # 上限

def test_get_edge_color_by_strength():
    """
    Given: 異なる強度
    When: _get_edge_color()を呼び出す
    Then: 強度に応じた色コードが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    color1 = panel._get_edge_color(0.0)  # 薄灰
    color2 = panel._get_edge_color(1.0)  # 濃灰
    
    assert color1 != color2
    assert "rgb" in color1
```

#### 8. エクスポートテスト（2件）

```python
def test_export_html():
    """
    Given: グラフが描画可能
    When: export_html()を呼び出す
    Then: HTMLファイルが作成される
    """
    import tempfile
    import os
    
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
        filename = tmp.name
    
    try:
        panel.export_html(filename)
        assert os.path.exists(filename)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def test_export_png():
    """
    Given: グラフが描画可能
    When: export_png()を呼び出す
    Then: PNGファイルが作成される
    """
    import tempfile
    import os
    
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        filename = tmp.name
    
    try:
        panel.export_png(filename)
        assert os.path.exists(filename)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
```

#### 9. エッジケース・異常系テスト（追加: 10件）

```python
def test_render_graph_with_empty_concepts():
    """
    Given: 空の概念リスト
    When: _render_graph()を呼び出す
    Then: 空のFigureが返される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    with patch.object(memory, 'retrieve_associated_concepts', return_value=[]):
        fig = panel._render_graph()
        assert fig is not None

def test_calculate_positions_with_duplicate_concepts():
    """
    Given: 重複する概念名
    When: _calculate_positions()を呼び出す
    Then: エラーが発生しない（または重複が処理される）
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.current_center = "機械学習"
    
    concepts = [
        {"name": "機械学習"},
        {"name": "機械学習"}  # 重複
    ]
    
    positions = panel._calculate_positions(concepts)
    # 重複処理の実装に応じて検証
```

#### 10. パラメータ化テスト（追加: 5件）

```python
@pytest.mark.parametrize("concept", ["機械学習", "Python", "データベース"])
def test_update_center_various_concepts(concept):
    """
    Given: 様々な概念名
    When: update_center()を呼び出す
    Then: すべての概念名が正しく設定される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    panel.update_center(concept)
    
    assert panel.current_center == concept

@pytest.mark.parametrize("max_nodes", [10, 50, 100, 1000])
def test_render_graph_various_max_nodes(max_nodes):
    """
    Given: 様々なmax_nodes値
    When: _render_graph()を呼び出す
    Then: max_nodes数までに制限される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    panel.max_nodes = max_nodes
    panel.current_center = "機械学習"
    
    # 実装に応じて検証
```

---

## Week 3-4: 自律的外部サーチエージェント - テスト仕様（TDD）

### テストファイル: `tests/test_autonomous_search.py`

**テストクラス**: `TestAutonomousSearchAgent`

**テストケース一覧（45件）**:

#### 1. 初期化テスト（3件）

```python
def test_agent_init_without_api_key():
    """
    Given: APIキーなし
    When: AutonomousSearchAgentを初期化
    Then: serper_api_keyがNoneで初期化される
    """
    agent = AutonomousSearchAgent()
    
    assert agent.serper_api_key is None
    assert agent.kb is not None

def test_agent_init_with_api_key():
    """
    Given: APIキー
    When: AutonomousSearchAgentを初期化
    Then: serper_api_keyが設定される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    assert agent.serper_api_key == "test_key"

def test_agent_init_wikipedia_lang_set():
    """
    Given: AutonomousSearchAgent
    When: 初期化
    Then: Wikipediaの言語が日本語に設定される
    """
    agent = AutonomousSearchAgent()
    
    import wikipedia
    assert wikipedia.language == "ja"
```

#### 2. 検索判定テスト（8件）

```python
def test_should_search_no_kb_results():
    """
    Given: KB検索結果が空
    When: should_search()を呼び出す
    Then: Trueが返される（検索実行）
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("質問", [])
    
    assert result is True

def test_should_search_low_similarity():
    """
    Given: 信頼度が0.6未満
    When: should_search()を呼び出す
    Then: Trueが返される（検索実行）
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("質問", [{"similarity": 0.5}])
    
    assert result is True

def test_should_search_threshold_boundary():
    """
    Given: 信頼度が0.6（境界値）
    When: should_search()を呼び出す
    Then: Falseが返される（検索不要）
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("質問", [{"similarity": 0.6}])
    
    assert result is False

def test_should_search_high_similarity():
    """
    Given: 信頼度が0.6以上
    When: should_search()を呼び出す
    Then: Falseが返される（検索不要）
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("質問", [{"similarity": 0.9}])
    
    assert result is False

def test_should_search_empty_question():
    """
    Given: 空の質問
    When: should_search()を呼び出す
    Then: エラーが発生しない
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("", [])
    
    assert isinstance(result, bool)
```

#### 3. Web検索テスト（10件）

```python
def test_web_search_without_api_key():
    """
    Given: APIキーなし
    When: web_search()を呼び出す
    Then: 空のリストが返される
    """
    agent = AutonomousSearchAgent()
    
    results = agent.web_search("test query")
    
    assert results == []

@pytest.mark.asyncio
async def test_web_search_success():
    """
    Given: 有効なAPIキーとクエリ
    When: web_search()を呼び出す
    Then: 検索結果が返される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "organic": [
                {"title": "結果1", "snippet": "説明1", "link": "http://example.com/1"},
                {"title": "結果2", "snippet": "説明2", "link": "http://example.com/2"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        results = agent.web_search("test query", max_results=5)
        
        assert len(results) == 2
        assert results[0]["title"] == "結果1"

def test_web_search_max_results_limit():
    """
    Given: max_resultsパラメータ
    When: web_search()を呼び出す
    Then: 指定された件数までに制限される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "organic": [{"title": f"結果{i}"} for i in range(10)]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        results = agent.web_search("test", max_results=3)
        
        assert len(results) == 3

def test_web_search_request_exception():
    """
    Given: リクエストエラー
    When: web_search()を呼び出す
    Then: 空のリストが返される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    with patch('requests.post', side_effect=requests.RequestException("Error")):
        results = agent.web_search("test query")
        
        assert results == []
```

#### 4. Wikipedia検索テスト（10件）

```python
def test_wikipedia_search_success():
    """
    Given: 有効なクエリ
    When: wikipedia_search()を呼び出す
    Then: Wikipedia記事が返される
    """
    agent = AutonomousSearchAgent()
    
    with patch('wikipedia.page') as mock_page:
        mock_page_instance = Mock()
        mock_page_instance.title = "Python"
        mock_page_instance.url = "https://ja.wikipedia.org/wiki/Python"
        mock_page.return_value = mock_page_instance
        
        with patch('wikipedia.summary', return_value="Pythonはプログラミング言語です"):
            result = agent.wikipedia_search("Python")
            
            assert result is not None
            assert result["title"] == "Python"
            assert "summary" in result

def test_wikipedia_search_page_error():
    """
    Given: 存在しないページ
    When: wikipedia_search()を呼び出す
    Then: Noneが返される
    """
    agent = AutonomousSearchAgent()
    
    with patch('wikipedia.page', side_effect=wikipedia.exceptions.PageError("Page not found")):
        result = agent.wikipedia_search("存在しないページ")
        
        assert result is None

def test_wikipedia_search_disambiguation():
    """
    Given: 曖昧性解消が必要なクエリ
    When: wikipedia_search()を呼び出す
    Then: 最初の候補で再試行される
    """
    agent = AutonomousSearchAgent()
    
    with patch('wikipedia.page') as mock_page:
        # 最初の呼び出しでDisambiguationError
        mock_page.side_effect = [
            wikipedia.exceptions.DisambiguationError("曖昧", ["Python (言語)", "Python (蛇)"]),
            Mock(title="Python (言語)", url="https://ja.wikipedia.org/wiki/Python_(言語)")
        ]
        
        with patch('wikipedia.summary', return_value="Pythonはプログラミング言語です"):
            result = agent.wikipedia_search("Python")
            
            assert result is not None
            assert mock_page.call_count == 2
```

#### 5. KB保存テスト（5件）

```python
def test_save_to_kb():
    """
    Given: コンテンツとカテゴリ
    When: save_to_kb()を呼び出す
    Then: KBに保存される
    """
    agent = AutonomousSearchAgent()
    
    with patch.object(agent.kb, 'store') as mock_store:
        agent.save_to_kb("コンテンツ", "news")
        
        mock_store.assert_called_once_with(
            content="コンテンツ",
            category="news",
            metadata={"source": "autonomous_search"}
        )

def test_save_to_kb_custom_source():
    """
    Given: カスタムソース
    When: save_to_kb()を呼び出す
    Then: ソースが設定される
    """
    agent = AutonomousSearchAgent()
    
    with patch.object(agent.kb, 'store') as mock_store:
        agent.save_to_kb("コンテンツ", "news", source="manual")
        
        mock_store.assert_called_once_with(
            content="コンテンツ",
            category="news",
            metadata={"source": "manual"}
        )
```

#### 6. エッジケース・異常系テスト（追加: 10件）

```python
def test_web_search_timeout():
    """
    Given: タイムアウトエラー
    When: web_search()を呼び出す
    Then: 空のリストが返される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    with patch('requests.post', side_effect=requests.Timeout("Timeout")):
        results = agent.web_search("test")
        
        assert results == []

def test_wikipedia_search_empty_query():
    """
    Given: 空のクエリ
    When: wikipedia_search()を呼び出す
    Then: エラーが発生する（またはNoneが返される）
    """
    agent = AutonomousSearchAgent()
    
    result = agent.wikipedia_search("")
    
    # 実装に応じてエラーまたはNone
    assert result is None or isinstance(result, dict)
```

#### 7. パラメータ化テスト（追加: 5件）

```python
@pytest.mark.parametrize("similarity,expected", [
    (0.0, True),
    (0.5, True),
    (0.6, False),
    (0.9, False),
])
def test_should_search_parametrized(similarity, expected):
    """
    Given: 様々な信頼度
    When: should_search()を呼び出す
    Then: 期待される結果が返される
    """
    agent = AutonomousSearchAgent()
    
    result = agent.should_search("質問", [{"similarity": similarity}])
    
    assert result == expected

@pytest.mark.parametrize("max_results", [1, 5, 10, 20])
def test_web_search_various_max_results(max_results):
    """
    Given: 様々なmax_results値
    When: web_search()を呼び出す
    Then: 指定された件数までに制限される
    """
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "organic": [{"title": f"結果{i}"} for i in range(20)]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        results = agent.web_search("test", max_results=max_results)
        
        assert len(results) == max_results
```

### テストファイル: `tests/test_scheduler.py`

**テストクラス**: `TestUpdateScheduler`

**テストケース一覧（20件）**:

#### 1. 初期化テスト（2件）

```python
def test_scheduler_init():
    """
    Given: AutonomousSearchAgentインスタンス
    When: UpdateSchedulerを初期化
    Then: search_agentが設定される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    assert scheduler.search_agent is agent
```

#### 2. スケジュール設定テスト（6件）

```python
def test_schedule_daily_news():
    """
    Given: UpdateScheduler
    When: schedule_daily_news()を呼び出す
    Then: 毎朝6時のスケジュールが設定される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch('schedule.every') as mock_every:
        mock_day = Mock()
        mock_day.day = Mock()
        mock_day.day.at = Mock(return_value=mock_day)
        mock_every.return_value = mock_day
        
        scheduler.schedule_daily_news()
        
        mock_day.day.at.assert_called_with("06:00")

def test_schedule_weekly_movies():
    """
    Given: UpdateScheduler
    When: schedule_weekly_movies()を呼び出す
    Then: 毎週日曜10時のスケジュールが設定される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch('schedule.every') as mock_every:
        mock_sunday = Mock()
        mock_sunday.sunday = Mock()
        mock_sunday.sunday.at = Mock(return_value=mock_sunday)
        mock_every.return_value = mock_sunday
        
        scheduler.schedule_weekly_movies()
        
        mock_sunday.sunday.at.assert_called_with("10:00")
```

#### 3. フェッチ関数テスト（6件）

```python
def test_fetch_news():
    """
    Given: UpdateScheduler
    When: _fetch_news()を呼び出す
    Then: ニュースが検索され、KBに保存される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch.object(agent, 'web_search', return_value=[
        {"title": "ニュース1", "snippet": "説明1"}
    ]) as mock_search:
        with patch.object(agent, 'save_to_kb') as mock_save:
            scheduler._fetch_news()
            
            mock_search.assert_called_once_with("最新ニュース", max_results=5)
            mock_save.assert_called()

def test_fetch_movies():
    """
    Given: UpdateScheduler
    When: _fetch_movies()を呼び出す
    Then: 映画情報が検索され、KBに保存される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch.object(agent, 'web_search', return_value=[
        {"title": "映画1", "snippet": "説明1"}
    ]) as mock_search:
        with patch.object(agent, 'save_to_kb') as mock_save:
            scheduler._fetch_movies()
            
            mock_search.assert_called_once_with("今週公開映画", max_results=3)
            mock_save.assert_called()
```

#### 4. スケジューラ実行テスト（4件）

```python
def test_run_executes_pending():
    """
    Given: UpdateScheduler
    When: run()を呼び出す
    Then: 保留中のジョブが実行される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch('schedule.run_pending') as mock_run:
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            try:
                scheduler.run()
            except KeyboardInterrupt:
                pass
            
            mock_run.assert_called()
```

#### 5. エッジケース・異常系テスト（追加: 5件）

```python
def test_fetch_news_empty_results():
    """
    Given: 検索結果が空
    When: _fetch_news()を呼び出す
    Then: KB保存が呼ばれない
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    with patch.object(agent, 'web_search', return_value=[]):
        with patch.object(agent, 'save_to_kb') as mock_save:
            scheduler._fetch_news()
            
            mock_save.assert_not_called()
```

---

## 統合テスト仕様（TDD）

### テストファイル: `tests/test_integration_visualization.py`

**テストケース一覧（10件）**:

```python
"""3D可視化の統合テスト."""

import pytest
from visualization.association_3d import AssociationVisualizationPanel
from memory.associative import AssociativeMemory


@pytest.mark.integration
def test_visualization_with_associative_memory():
    """
    Given: 連想記憶に概念が存在
    When: 可視化パネルでグラフを描画
    Then: 連想記憶から概念が取得され、グラフが描画される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    # 概念追加
    memory.add_concept("機械学習", embedding=[0.1]*128, metadata={})
    memory.add_concept("Python", embedding=[0.2]*128, metadata={})
    memory.link_concepts("機械学習", "Python", "related", strength=0.8)
    
    panel.current_center = "機械学習"
    panel.is_enabled = True
    fig = panel._render_graph()
    
    assert fig is not None
    assert len(fig.data) > 0

# ... 他9件（リアルタイム更新、大量データ、パフォーマンステストなど）
```

### テストファイル: `tests/test_integration_search.py`

**テストケース一覧（10件）**:

```python
"""自律サーチの統合テスト."""

import pytest
from agents.autonomous_search import AutonomousSearchAgent
from memory.knowledge_base import KnowledgeBase
from scheduler.update_scheduler import UpdateScheduler


@pytest.mark.integration
def test_search_and_save_to_kb():
    """
    Given: 検索エージェントとKB
    When: 検索してKBに保存
    Then: KBに正しく保存される
    """
    agent = AutonomousSearchAgent()
    
    with patch.object(agent, 'web_search', return_value=[
        {"title": "結果", "snippet": "説明", "link": "http://example.com"}
    ]):
        agent.save_to_kb("テストコンテンツ", "news")
        
        # KBから検索して確認
        results = agent.kb.search("テスト", top_k=1)
        assert len(results) > 0

@pytest.mark.integration
def test_scheduler_integration():
    """
    Given: スケジューラと検索エージェント
    When: スケジュールを設定して実行
    Then: 検索とKB保存が実行される
    """
    agent = AutonomousSearchAgent()
    scheduler = UpdateScheduler(agent)
    
    scheduler.schedule_daily_news()
    
    # スケジュールが設定されたことを確認
    # 実際の実行は時間がかかるため、スケジュール設定のみ確認

# ... 他8件（定期実行、エラー回復、パフォーマンステストなど）
```

---

## テストフィクスチャ仕様

### conftest.py の拡張

```python
# tests/conftest.py（拡張）

import pytest
import tempfile
from unittest.mock import Mock, patch

from visualization.association_3d import AssociationVisualizationPanel
from memory.associative import AssociativeMemory
from agents.autonomous_search import AutonomousSearchAgent
from scheduler.update_scheduler import UpdateScheduler

@pytest.fixture
def associative_memory():
    """AssociativeMemoryインスタンス"""
    return AssociativeMemory(db_path=":memory:")

@pytest.fixture
def visualization_panel(associative_memory):
    """AssociationVisualizationPanelインスタンス"""
    return AssociationVisualizationPanel(associative_memory)

@pytest.fixture
def search_agent():
    """AutonomousSearchAgentインスタンス"""
    return AutonomousSearchAgent()

@pytest.fixture
def scheduler(search_agent):
    """UpdateSchedulerインスタンス"""
    return UpdateScheduler(search_agent)

@pytest.fixture
def mock_requests():
    """requests.postのモック"""
    with patch('requests.post') as mock:
        yield mock

@pytest.fixture
def mock_wikipedia():
    """wikipediaのモック"""
    with patch('wikipedia.page') as mock_page, \
         patch('wikipedia.summary') as mock_summary:
        yield mock_page, mock_summary
```

---

## テスト実行戦略

### TDD実装順序（詳細版）

#### Week 1-2: 3D可視化パネル

**Day 1: 初期化・ON/OFF切り替えテスト（10件）→ 実装**
- 初期化: デフォルト状態、カスタム設定、エラーハンドリング
- ON/OFF切り替え: 状態変更、複数回切り替え

**Day 2: 中心概念更新・グラフ描画テスト（15件）→ 実装**
- 中心概念更新: 設定、描画トリガー、エッジケース
- グラフ描画: 基本描画、空データ、max_nodes制限

**Day 3: 座標計算・ノード・エッジ作成テスト（13件）→ 実装**
- 座標計算: 中心配置、depthベース配置
- ノード・エッジ作成: トレース作成、色・サイズ計算

**Day 4: エクスポート・エッジケーステスト（12件）→ 実装**
- エクスポート: HTML、PNG出力
- エッジケース: 空データ、重複、異常値

**Day 5-6: 統合テスト（10件）→ 実装・リファクタリング**
- 連想記憶連携、リアルタイム更新、パフォーマンス

#### Week 3-4: 自律サーチエージェント

**Day 1-2: 検索判定・Web検索テスト（18件）→ 実装**
- 検索判定: KB結果なし、低信頼度、境界値
- Web検索: APIキーなし、成功、エラーハンドリング

**Day 3: Wikipedia検索・KB保存テスト（15件）→ 実装**
- Wikipedia検索: 成功、PageError、DisambiguationError
- KB保存: 基本保存、カスタムソース

**Day 4: スケジューラテスト（20件）→ 実装**
- スケジュール設定: 毎日、毎週、毎月
- フェッチ関数: ニュース、映画、技術情報
- スケジューラ実行: 保留ジョブ実行

**Day 5-6: 統合テスト（10件）→ 実装・リファクタリング**
- KB連携、スケジューラ統合、エラー回復

### テスト品質基準

**必須要件**:
- ✅ **テスト成功率**: 100%（全130件以上のテストが成功）
- ✅ **コードカバレッジ**: 88%以上（平均）
- ✅ **テスト実行時間**: 全テスト5分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（API、Wikipedia等）はモックで分離

**TDDサイクル遵守**:
- ✅ **RED**: 実装前にテストを書いている
- ✅ **GREEN**: 最小限の実装でテストを通している
- ✅ **REFACTOR**: リファクタリング後もテストが成功している

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `visualization/association_3d.py` (500行)
- `agents/autonomous_search.py` (350行)
- `scheduler/update_scheduler.py` (200行)
- **合計**: 1,050行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_visualization.py` (45件)
  - 初期化テスト: 5件
  - ON/OFF切り替えテスト: 5件
  - 中心概念更新テスト: 5件
  - グラフ描画テスト: 10件
  - 座標計算テスト: 5件
  - ノード・エッジ作成テスト: 8件
  - 色・サイズ計算テスト: 5件
  - エクスポートテスト: 2件
  - エッジケース・異常系テスト: 10件
  - パラメータ化テスト: 5件
- `tests/test_autonomous_search.py` (45件)
  - 初期化テスト: 3件
  - 検索判定テスト: 8件
  - Web検索テスト: 10件
  - Wikipedia検索テスト: 10件
  - KB保存テスト: 5件
  - エッジケース・異常系テスト: 10件
  - パラメータ化テスト: 5件
- `tests/test_scheduler.py` (20件)
  - 初期化テスト: 2件
  - スケジュール設定テスト: 6件
  - フェッチ関数テスト: 6件
  - スケジューラ実行テスト: 4件
  - エッジケース・異常系テスト: 5件
- `tests/test_integration_visualization.py` (10件)
- `tests/test_integration_search.py` (10件)
- `tests/fixtures/visualization_fixtures.py`: テストデータ定義
- `tests/fixtures/autonomous_search_fixtures.py`: テストデータ定義
- **合計**: 130件以上（エッジケース・パラメータ化テスト含む）

### 7.3 ドキュメント

- `docks/完了報告/Phase7_完了サマリー.md`
- 3D可視化操作ガイド
- 自律サーチ設定ガイド

### 7.4 マイルストーン

- [ ] 3D可視化パネル動作確認
- [ ] 自律サーチ定期実行テスト成功
- [ ] KB自動更新確認
- [ ] 全テスト成功（130件以上）
- [ ] カバレッジ > 88%

---

## 8. Phase 7成功基準

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全130件以上のテストが成功）
- ✅ **コードカバレッジ**: 88%以上（平均）
- ✅ **テスト実行時間**: 全テスト5分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（API、Wikipedia等）はモックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | pytest（全130件以上） |
| **コードカバレッジ** | **88%以上** | pytest-cov |
| **テスト実行時間** | **< 5分** | pytest --durations |
| 3D可視化レンダリング時間 | < 1秒 | パフォーマンステスト |
| Web検索応答時間 | < 2秒 | API呼び出しテスト |
| Wikipedia検索応答時間 | < 3秒 | API呼び出しテスト |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全130件以上のテストケースが定義されている
✅ **3D可視化動作**: 連想記憶ネットワークの可視化
✅ **自律サーチ動作**: 自動Web検索・KB保存
✅ **スケジューラ動作**: 定期更新実行

---

**Phase 7 実装完了**: 視覚的理解と知識拡張の基盤が整いました。