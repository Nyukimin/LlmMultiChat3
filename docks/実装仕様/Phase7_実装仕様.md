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
6. [テスト計画](#6-テスト計画)
7. [成果物](#7-成果物)

---

## 1. Phase 7概要

### 1.1 目的

連想ネットワークの3D可視化と自律情報収集により、**視覚的理解と知識の自動拡張**を実現します。

### 1.2 主要機能

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

### 3.3 テスト（10件）

#### tests/test_visualization.py

```python
"""3D可視化モジュールのテスト."""

import pytest
from visualization.association_3d import AssociationVisualizationPanel
from memory.associative import AssociativeMemory


def test_panel_init():
    """初期化テスト."""
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    assert panel.is_enabled is False
    assert panel.current_center is None


def test_toggle():
    """ON/OFF切り替えテスト."""
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    assert panel.toggle() is True
    assert panel.is_enabled is True
    
    assert panel.toggle() is False
    assert panel.is_enabled is False


def test_update_center():
    """中心概念更新テスト."""
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    panel.update_center("機械学習")
    assert panel.current_center == "機械学習"


def test_render_graph():
    """グラフ描画テスト."""
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    # 概念追加
    memory.add_concept("機械学習", embedding=[0.1]*128, metadata={})
    memory.add_concept("Python", embedding=[0.2]*128, metadata={})
    memory.link_concepts("機械学習", "Python", "related", strength=0.8)
    
    panel.current_center = "機械学習"
    fig = panel._render_graph()
    
    assert fig is not None


# ... 他6件（境界値、異常系、統合テスト）
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

### 4.3 テスト（15件）

#### tests/test_autonomous_search.py

```python
"""自律サーチエージェントのテスト."""

import pytest
from agents.autonomous_search import AutonomousSearchAgent


def test_should_search():
    """検索判定テスト."""
    agent = AutonomousSearchAgent()
    
    # KB結果なし → 検索実行
    assert agent.should_search("質問", []) is True
    
    # 信頼度低い → 検索実行
    assert agent.should_search("質問", [{"similarity": 0.5}]) is True
    
    # 信頼度高い → 検索不要
    assert agent.should_search("質問", [{"similarity": 0.9}]) is False


@pytest.mark.skipif(not pytest.config.getoption("--run-slow"), reason="Slow test")
def test_web_search():
    """Web検索テスト（Serper API必要）."""
    agent = AutonomousSearchAgent(serper_api_key="test_key")
    # Note: 実際のAPIキーでテスト


def test_wikipedia_search():
    """Wikipedia検索テスト."""
    agent = AutonomousSearchAgent()
    
    result = agent.wikipedia_search("Python")
    assert result is not None
    assert "title" in result
    assert "summary" in result


# ... 他12件（境界値、異常系、統合テスト）
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

## 6. テスト計画

### 6.1 テスト構成

| テストファイル | テスト件数 | カバレッジ目標 |
|---------------|-----------|---------------|
| `tests/test_visualization.py` | 10件 | > 80% |
| `tests/test_autonomous_search.py` | 15件 | > 85% |
| **合計** | **25件** | **> 83%** |

### 6.2 テストカテゴリ

**Unit Tests（15件）**:
- パネル初期化テスト
- グラフ描画テスト
- 検索判定テスト
- Wikipedia検索テスト

**Integration Tests（10件）**:
- 連想記憶との連携テスト
- KB保存テスト
- スケジューラ統合テスト

### 6.3 実行方法

```bash
# 全テスト実行
pytest tests/test_visualization.py tests/test_autonomous_search.py -v

# スケジューラ起動
python -m scheduler.update_scheduler

# 3D可視化確認
python -c "from visualization.association_3d import AssociationVisualizationPanel; panel.export_html('test.html')"
```

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
- `tests/test_visualization.py` (10件)
- `tests/test_autonomous_search.py` (15件)
- **合計**: 25件

### 7.3 ドキュメント

- `docks/完了報告/Phase7_完了サマリー.md`
- 3D可視化操作ガイド
- 自律サーチ設定ガイド

### 7.4 マイルストーン

- [ ] 3D可視化パネル動作確認
- [ ] 自律サーチ定期実行テスト成功
- [ ] KB自動更新確認
- [ ] 全テスト成功（25件）
- [ ] カバレッジ > 83%

---

**Phase 7 実装完了**: 視覚的理解と知識拡張の基盤が整いました。