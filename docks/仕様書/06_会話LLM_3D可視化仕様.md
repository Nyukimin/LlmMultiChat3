# 会話LLM 3D可視化仕様書

**バージョン:** 3.1.0  
**最終更新:** 2025-11-19  
**親文書:** [会話LLM_仕様.md](./01_会話LLM_仕様.md)

---

## 目次

1. [概要](#1-概要)
2. [可視化パネルの仕様](#2-可視化パネルの仕様)
3. [UIコントロール](#3-uiコントロール)
4. [自動更新モード](#4-自動更新モード)
5. [使用例](#5-使用例)
6. [パフォーマンス最適化](#6-パフォーマンス最適化)
7. [UI配置](#7-ui配置)
8. [技術実装](#8-技術実装)

---

## 1. 概要

連想ネットワーク3D可視化パネルは、ユーザーが連想記憶の構造を**視覚的に理解・探索**できるインタラクティブなインターフェースです。

### 1.1 設計思想

- **視覚的理解**: 複雑なネットワーク構造を直感的に把握
- **ON/OFF切り替え**: 必要な時だけ表示（デフォルトOFF）
- **リアルタイム更新**: 会話に応じて自動更新
- **インタラクティブ**: ズーム・回転・ノードクリック可能

### 1.2 主要機能

- 3Dグラフ描画（Plotly.js + WebGL）
- ノード・エッジの色・サイズによる情報表現
- マウス操作（ドラッグ回転・ホイールズーム）
- エクスポート（PNG/HTML）
- 自動更新モード

---

## 2. 可視化パネルの仕様

### 2.1 基本クラス

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

---

## 3. UIコントロール

### 3.1 コントロールパネル

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

### 3.2 マウス操作

| 操作 | 動作 |
|------|------|
| **ドラッグ** | グラフ回転 |
| **ホイール** | ズームイン/アウト |
| **ノードクリック** | そのノードを中心に再描画 |
| **ダブルクリック** | リセット |

---

## 4. 自動更新モード

### 4.1 実装

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

### 4.2 更新トリガー

- **トピック変更時**: 話題が切り替わったら中心ノード更新
- **新概念追加時**: グラフに新ノード追加
- **関連性強化時**: エッジの太さ・色を更新

---

## 5. 使用例

### 5.1 基本的な使い方

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

### 5.2 会話フロー統合

```python
async def chat_with_visualization(user_input):
    """可視化統合チャット"""
    
    # 通常の会話処理
    response = await process_chat(user_input)
    
    # 可視化パネルがONなら更新
    if viz_panel.enabled:
        # 主要トピック抽出
        topic = extract_main_topic(user_input)
        
        # グラフ更新
        viz_panel.update_center(topic)
    
    return response
```

---

## 6. パフォーマンス最適化

### 6.1 最適化設定

| 項目 | 設定 | 理由 |
|------|------|------|
| 最大ノード数 | 50 | 描画パフォーマンス |
| 更新頻度 | 1秒/回 | CPU負荷軽減 |
| レンダリング | WebGL | 3D高速描画 |
| 遅延ロード | 有効 | 初期表示高速化 |

### 6.2 負荷軽減策

```python
class OptimizedVisualization:
    """最適化版可視化"""
    
    def __init__(self):
        self.cache = LRUCache(maxsize=100)
        self.render_queue = Queue()
        self.last_render_time = 0
        self.min_render_interval = 1.0  # 最小1秒間隔
    
    def update_center_throttled(self, concept):
        """レート制限付き更新"""
        now = time.time()
        
        if now - self.last_render_time < self.min_render_interval:
            # キューに追加（後で処理）
            self.render_queue.put(concept)
        else:
            # 即座に描画
            self._render_graph(concept)
            self.last_render_time = now
```

---

## 7. UI配置

### 7.1 レイアウト

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

### 7.2 レスポンシブデザイン

```css
/* モバイル対応 */
@media (max-width: 768px) {
  .visualization-panel {
    height: 300px;
    width: 100%;
  }
}

/* タブレット */
@media (min-width: 768px) and (max-width: 1024px) {
  .visualization-panel {
    height: 500px;
    width: 100%;
  }
}

/* デスクトップ */
@media (min-width: 1024px) {
  .visualization-panel {
    height: 700px;
    width: 100%;
  }
}
```

---

## 8. 技術実装

### 8.1 フロントエンド

```javascript
// React + Plotly.js
import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

const AssociationGraph = ({ centerConcept, depth, threshold }) => {
  const [data, setData] = useState([]);
  const [layout, setLayout] = useState({});

  useEffect(() => {
    fetchGraphData(centerConcept, depth, threshold).then(response => {
      setData(response.data);
      setLayout(response.layout);
    });
  }, [centerConcept, depth, threshold]);

  return (
    <Plot
      data={data}
      layout={layout}
      config={{ responsive: true }}
    />
  );
};
```

### 8.2 バックエンドAPI

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/visualization/graph")
async def get_graph_data(
    center: str,
    depth: int = 3,
    threshold: float = 0.3
):
    """グラフデータ取得API"""
    panel = AssociationVisualizationPanel()
    panel.center_concept = center
    panel.depth = depth
    panel.threshold = threshold
    
    fig = panel._render_graph()
    
    return {
        "data": fig.data,
        "layout": fig.layout
    }
```

### 8.3 WebSocket更新

```python
import asyncio
from fastapi import WebSocket

@app.websocket("/ws/visualization")
async def visualization_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # クライアントからの更新リクエスト待機
            message = await websocket.receive_json()
            
            # グラフデータ生成
            graph_data = get_graph_data(
                center=message["center"],
                depth=message["depth"],
                threshold=message["threshold"]
            )
            
            # クライアントへ送信
            await websocket.send_json(graph_data)
    except:
        await websocket.close()
```

---

## 関連ドキュメント

- **親文書**: [会話LLM_仕様.md](./01_会話LLM_仕様.md)
- **記憶システム**: [会話LLM_記憶システム仕様.md](./02_会話LLM_記憶システム仕様.md)
- **キャラクター**: [会話LLM_キャラクター仕様.md](./03_会話LLM_キャラクター仕様.md)
- **感情・対話**: [会話LLM_感情・対話仕様.md](./04_会話LLM_感情・対話仕様.md)
- **連想記憶**: [会話LLM_連想記憶仕様.md](./05_会話LLM_連想記憶仕様.md)

---

**文書バージョン:** 3.1.0  
**最終更新:** 2025-11-19
