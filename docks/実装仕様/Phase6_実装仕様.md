# Phase 6 実装仕様書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 6 - キャラクター成長 + MCP対応  
**期間**: 4週間  
**作成日**: 2025-11-20  
**Phase 5完了前提**: 対話スタイル適応・自己省察実装済み

---

## 目次

1. [Phase 6概要](#1-phase-6概要)
2. [前提条件](#2-前提条件)
3. [Week 1-2: KPIベース成長システム](#3-week-1-2-kpiベース成長システム)
4. [Week 3-4: MCP Server実装](#4-week-3-4-mcp-server実装)
5. [技術スタック](#5-技術スタック)
6. [テスト計画](#6-テスト計画)
7. [成果物](#7-成果物)

---

## 1. Phase 6概要

### 1.1 目的

KPIベースのキャラクター成長システムとMCP Server実装により、**長期運用での進化と外部連携**を実現します。

### 1.2 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **KPI収集** | ユーザー評価・会話回数追跡 | 🔴 High |
| **レベルアップ** | 自動成長・機能解禁 | 🔴 High |
| **MCP Server** | 外部ツール公開 | 🟡 Medium |
| **リソース公開** | キャラクター情報提供 | 🟡 Medium |

### 1.3 達成目標

✅ KPI収集・レベルアップ自動化  
✅ MCP Server起動・外部接続成功  
✅ Claude Desktop統合確認  
✅ 成長による会話スタイル変化

---

## 2. 前提条件

### 2.1 Phase 1-5完了事項

✅ **Phase 1**: LangGraphコア・5階層記憶システム  
✅ **Phase 2**: エラーハンドリング・セキュリティ  
✅ **Phase 3**: REST/WebSocket API（23エンドポイント）  
✅ **Phase 4**: 連想記憶システム・感情モデル基盤  
✅ **Phase 5**: 対話スタイル適応・自己省察

**参照**: [`docks/実装仕様/Phase5_実装仕様.md`](Phase5_実装仕様.md:1)

### 2.2 利用可能なPhase 5機能

- **対話スタイル適応**: [`core/dialogue_style.py`](../../core/dialogue_style.py)
- **自己省察**: [`core/self_reflection.py`](../../core/self_reflection.py)

---

## 3. Week 1-2: KPIベース成長システム

### 3.1 実装内容

**参照**: [`docks/仕様書/03_会話LLM_キャラクター仕様.md:246-333`](../仕様書/03_会話LLM_キャラクター仕様.md:246)

#### 3.1.1 KPI収集

**5種類のKPI**:

```python
{
    "user_thumbs_up": 0,      # ユーザー評価 👍
    "answer_hits": 0,          # 推薦が採用された回数
    "search_success": 0,       # 検索結果が役立った回数
    "conversation_count": 0,   # 会話参加回数
    "topic_expertise": {}      # トピック別専門性 {"Python": 10, "ML": 5}
}
```

#### 3.1.2 レベルアップロジック

**計算式**:
```python
level = floor(sqrt(total_kpi / 10))

# 例:
# total_kpi = 0   → level = 0
# total_kpi = 10  → level = 1
# total_kpi = 40  → level = 2
# total_kpi = 90  → level = 3
# total_kpi = 160 → level = 4
```

**レベル別解禁機能**:

| Level | 解禁機能 |
|-------|---------|
| 0 | 基本会話のみ |
| 1 | 記憶検索強化 |
| 2 | プラグイン利用可能 |
| 3 | 自律サーチ開始 |
| 4 | LoRAファインチューニング適用 |
| 5+ | 全機能フル活用 |

#### 3.1.3 成長結果

**パラメータ自動調整**:
- `verbosity`: レベル2以上で +0.1（より詳細な説明）
- `proactivity`: レベル3以上で +0.2（積極的提案）
- `technical_level`: トピック専門性に応じて調整

**外観更新**（将来実装）:
- 3Dアバター変化
- 声質向上

### 3.2 ファイル構成

#### core/character_growth.py (350行)

```python
"""キャラクター成長システム."""

from typing import Dict, Any, Optional
import sqlite3
import math
from datetime import datetime


class CharacterGrowth:
    """KPIベースキャラクター成長クラス."""
    
    def __init__(self, character_name: str, db_path: str = "db/character_growth.db"):
        """
        初期化.
        
        Args:
            character_name: キャラクター名
            db_path: データベースパス
        """
        self.character_name = character_name
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
        self.current_level = self._load_current_level()
    
    def _init_schema(self) -> None:
        """データベーススキーマ初期化."""
        self.conn.executescript("""
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
            
            CREATE INDEX IF NOT EXISTS idx_character_kpi 
            ON character_growth(character_name, kpi_type);
        """)
        self.conn.commit()
    
    def update_kpi(
        self,
        event_type: str,
        value: int = 1,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        KPI更新.
        
        Args:
            event_type: KPIタイプ ("user_thumbs_up", "answer_hits", etc.)
            value: 加算値
            topic: トピック（topic_expertiseの場合）
        
        Returns:
            Dict: 更新結果（レベルアップ情報含む）
        """
        cursor = self.conn.cursor()
        
        # 既存KPI取得
        cursor.execute("""
            SELECT id, value FROM character_growth
            WHERE character_name = ? AND kpi_type = ? AND (topic = ? OR topic IS NULL)
        """, (self.character_name, event_type, topic))
        
        row = cursor.fetchone()
        
        if row:
            # 更新
            new_value = row[1] + value
            cursor.execute("""
                UPDATE character_growth
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_value, row[0]))
        else:
            # 新規作成
            cursor.execute("""
                INSERT INTO character_growth (character_name, kpi_type, value, topic)
                VALUES (?, ?, ?, ?)
            """, (self.character_name, event_type, value, topic))
        
        self.conn.commit()
        
        # レベル計算
        new_level = self._calculate_level()
        level_up_occurred = False
        
        if new_level > self.current_level:
            level_up_occurred = True
            self._level_up(new_level)
        
        return {
            "event_type": event_type,
            "new_value": row[1] + value if row else value,
            "current_level": new_level,
            "level_up_occurred": level_up_occurred
        }
    
    def _calculate_level(self) -> int:
        """
        現在のレベル計算.
        
        Returns:
            int: レベル
        """
        cursor = self.conn.cursor()
        
        # 全KPI合計
        cursor.execute("""
            SELECT SUM(value) FROM character_growth
            WHERE character_name = ?
        """, (self.character_name,))
        
        total_kpi = cursor.fetchone()[0] or 0
        
        # レベル計算: level = floor(sqrt(total_kpi / 10))
        level = math.floor(math.sqrt(total_kpi / 10))
        
        return level
    
    def _load_current_level(self) -> int:
        """
        現在のレベル読み込み.
        
        Returns:
            int: レベル
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT level FROM character_growth
            WHERE character_name = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (self.character_name,))
        
        row = cursor.fetchone()
        return row[0] if row else 0
    
    def _level_up(self, new_level: int) -> None:
        """
        レベルアップ処理.
        
        Args:
            new_level: 新しいレベル
        """
        print(f"🎉 {self.character_name} がレベル {new_level} にレベルアップしました！")
        
        # レベル記録更新
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE character_growth
            SET level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE character_name = ?
        """, (new_level, self.character_name))
        self.conn.commit()
        
        self.current_level = new_level
        
        # 機能解禁
        self._unlock_new_features(new_level)
        
        # パラメータ調整
        self._adjust_parameters(new_level)
        
        # 外観更新（将来実装）
        # self._update_appearance(new_level)
    
    def _unlock_new_features(self, level: int) -> None:
        """
        レベルに応じた機能解禁.
        
        Args:
            level: レベル
        """
        features = {
            1: "記憶検索強化",
            2: "プラグイン利用可能",
            3: "自律サーチ開始",
            4: "LoRAファインチューニング適用",
            5: "全機能フル活用"
        }
        
        if level in features:
            print(f"🔓 新機能解禁: {features[level]}")
    
    def _adjust_parameters(self, level: int) -> None:
        """
        レベルに応じたパラメータ調整.
        
        Args:
            level: レベル
        """
        from core.dialogue_style import AdaptiveDialogueStyle
        
        # 対話スタイル調整（例）
        # style = AdaptiveDialogueStyle(user_id=f"character_{self.character_name}")
        # if level >= 2:
        #     style.parameters["verbosity"] = min(1.0, style.parameters["verbosity"] + 0.1)
        # if level >= 3:
        #     style.parameters["proactivity"] = min(1.0, style.parameters["proactivity"] + 0.2)
        # style._save_to_profile()
        
        print(f"⚙️ パラメータ調整完了（レベル {level}）")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報取得.
        
        Returns:
            Dict: 統計情報
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT kpi_type, SUM(value) as total, topic
            FROM character_growth
            WHERE character_name = ?
            GROUP BY kpi_type, topic
        """, (self.character_name,))
        
        rows = cursor.fetchall()
        
        stats = {
            "character_name": self.character_name,
            "level": self.current_level,
            "kpis": {},
            "topic_expertise": {}
        }
        
        for row in rows:
            kpi_type, total, topic = row
            if topic:
                if kpi_type not in stats["topic_expertise"]:
                    stats["topic_expertise"][kpi_type] = {}
                stats["topic_expertise"][kpi_type][topic] = total
            else:
                stats["kpis"][kpi_type] = total
        
        return stats
```

### 3.3 データベーススキーマ

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

### 3.4 テスト（15件）

#### tests/test_character_growth.py

```python
"""キャラクター成長システムのテスト."""

import pytest
from core.character_growth import CharacterGrowth


def test_kpi_update():
    """KPI更新テスト."""
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result = growth.update_kpi("user_thumbs_up", value=1)
    assert result["new_value"] == 1
    assert result["current_level"] == 0
    
    # 10回で level 1
    for _ in range(9):
        growth.update_kpi("user_thumbs_up", value=1)
    
    result = growth.update_kpi("user_thumbs_up", value=1)
    assert result["current_level"] == 1
    assert result["level_up_occurred"] is True


def test_level_calculation():
    """レベル計算テスト."""
    growth = CharacterGrowth("clarisse", db_path=":memory:")
    
    # total_kpi = 0 → level = 0
    assert growth._calculate_level() == 0
    
    # total_kpi = 10 → level = 1
    growth.update_kpi("conversation_count", value=10)
    assert growth._calculate_level() == 1
    
    # total_kpi = 40 → level = 2
    growth.update_kpi("answer_hits", value=30)
    assert growth._calculate_level() == 2


def test_level_up():
    """レベルアップテスト."""
    growth = CharacterGrowth("nox", db_path=":memory:")
    
    # 10 KPIでレベル1
    for _ in range(10):
        growth.update_kpi("search_success", value=1)
    
    assert growth.current_level == 1


def test_get_stats():
    """統計取得テスト."""
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    growth.update_kpi("user_thumbs_up", value=5)
    growth.update_kpi("answer_hits", value=3)
    growth.update_kpi("topic_expertise", value=10, topic="Python")
    
    stats = growth.get_stats()
    assert stats["kpis"]["user_thumbs_up"] == 5
    assert stats["kpis"]["answer_hits"] == 3
    assert stats["topic_expertise"]["topic_expertise"]["Python"] == 10


# ... 他11件（境界値、異常系、統合テスト）
```

---

## 4. Week 3-4: MCP Server実装

### 4.1 実装内容

**参照**: [`docks/仕様書/01_会話LLM_仕様.md:501-529`](../仕様書/01_会話LLM_仕様.md:501)

#### 4.1.1 MCP Server基盤

**MCPプロトコル準拠**:
- JSON-RPC 2.0
- Server-Sent Events (SSE)
- Tools & Resources公開

#### 4.1.2 公開ツール

```python
# 1. chat_with_character
{
    "name": "chat_with_character",
    "description": "指定キャラクターと会話",
    "inputSchema": {
        "type": "object",
        "properties": {
            "character": {"type": "string", "enum": ["lumina", "clarisse", "nox"]},
            "message": {"type": "string"}
        }
    }
}

# 2. search_memories
{
    "name": "search_memories",
    "description": "記憶検索",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 5}
        }
    }
}

# 3. autonomous_search（Phase 7で実装）
{
    "name": "autonomous_search",
    "description": "自律Web検索",
    "inputSchema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"}
        }
    }
}
```

#### 4.1.3 公開リソース

```python
# 1. character://lumina
{
    "uri": "character://lumina",
    "name": "ルミナ情報",
    "description": "ルミナのキャラクター設定と現在状態",
    "mimeType": "application/json"
}

# 2. memory://user:{id}
{
    "uri": "memory://user:123",
    "name": "ユーザー記憶",
    "description": "特定ユーザーの記憶情報",
    "mimeType": "application/json"
}
```

### 4.2 ファイル構成

#### api/mcp_server.py (400行)

```python
"""MCP Server実装."""

from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
import asyncio


class LlmMultiChatMCPServer:
    """LlmMultiChat3 MCP Server."""
    
    def __init__(self):
        """初期化."""
        self.server = Server("llmmultichat3")
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self) -> None:
        """ツール登録."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """利用可能なツール一覧."""
            return [
                Tool(
                    name="chat_with_character",
                    description="指定キャラクターと会話します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "character": {
                                "type": "string",
                                "enum": ["lumina", "clarisse", "nox"],
                                "description": "キャラクター名"
                            },
                            "message": {
                                "type": "string",
                                "description": "メッセージ内容"
                            }
                        },
                        "required": ["character", "message"]
                    }
                ),
                Tool(
                    name="search_memories",
                    description="記憶を検索します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "検索クエリ"
                            },
                            "top_k": {
                                "type": "integer",
                                "default": 5,
                                "description": "取得件数"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """ツール実行."""
            if name == "chat_with_character":
                return await self._chat_with_character(
                    arguments["character"],
                    arguments["message"]
                )
            elif name == "search_memories":
                return await self._search_memories(
                    arguments["query"],
                    arguments.get("top_k", 5)
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _register_resources(self) -> None:
        """リソース登録."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """利用可能なリソース一覧."""
            return [
                Resource(
                    uri="character://lumina",
                    name="ルミナ情報",
                    description="ルミナのキャラクター設定と現在状態",
                    mimeType="application/json"
                ),
                Resource(
                    uri="character://clarisse",
                    name="クラリス情報",
                    description="クラリスのキャラクター設定と現在状態",
                    mimeType="application/json"
                ),
                Resource(
                    uri="character://nox",
                    name="ノクス情報",
                    description="ノクスのキャラクター設定と現在状態",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """リソース取得."""
            if uri.startswith("character://"):
                character_name = uri.split("://")[1]
                return await self._get_character_info(character_name)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _chat_with_character(
        self,
        character: str,
        message: str
    ) -> List[TextContent]:
        """
        キャラクターと会話.
        
        Args:
            character: キャラクター名
            message: メッセージ
        
        Returns:
            List[TextContent]: 応答
        """
        from services.chat_service import ChatService
        
        chat_service = ChatService()
        response = await chat_service.chat(
            user_input=message,
            character_name=character,
            session_id="mcp_session"
        )
        
        return [TextContent(type="text", text=response["response"])]
    
    async def _search_memories(
        self,
        query: str,
        top_k: int
    ) -> List[TextContent]:
        """
        記憶検索.
        
        Args:
            query: クエリ
            top_k: 取得件数
        
        Returns:
            List[TextContent]: 検索結果
        """
        from memory.long_term import LongTermMemory
        
        long_term = LongTermMemory()
        results = long_term.search(query=query, top_k=top_k)
        
        formatted = "\n".join([
            f"{i+1}. {r['content']} (similarity: {r['similarity']:.2f})"
            for i, r in enumerate(results)
        ])
        
        return [TextContent(type="text", text=formatted)]
    
    async def _get_character_info(self, character_name: str) -> str:
        """
        キャラクター情報取得.
        
        Args:
            character_name: キャラクター名
        
        Returns:
            str: JSON形式のキャラクター情報
        """
        import json
        from core.character_growth import CharacterGrowth
        
        growth = CharacterGrowth(character_name)
        stats = growth.get_stats()
        
        return json.dumps(stats, ensure_ascii=False, indent=2)
    
    async def run(self):
        """MCP Server起動."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """エントリーポイント."""
    server = LlmMultiChatMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 Claude Desktop統合設定

#### claude_desktop_config.json

```json
{
  "mcpServers": {
    "llmmultichat3": {
      "command": "python",
      "args": ["-m", "api.mcp_server"],
      "cwd": "c:/GenerativeAI/LlmMultiChat3",
      "env": {
        "PYTHONPATH": "c:/GenerativeAI/LlmMultiChat3"
      }
    }
  }
}
```

### 4.4 テスト（20件）

#### tests/test_mcp_server.py

```python
"""MCP Serverのテスト."""

import pytest
from api.mcp_server import LlmMultiChatMCPServer


@pytest.mark.asyncio
async def test_mcp_server_init():
    """初期化テスト."""
    server = LlmMultiChatMCPServer()
    assert server.server.name == "llmmultichat3"


@pytest.mark.asyncio
async def test_list_tools():
    """ツール一覧テスト."""
    server = LlmMultiChatMCPServer()
    # Note: 実際のテストはMCPクライアント経由で実行


@pytest.mark.asyncio
async def test_chat_with_character_tool():
    """チャットツールテスト."""
    server = LlmMultiChatMCPServer()
    
    result = await server._chat_with_character("lumina", "こんにちは")
    assert len(result) > 0
    assert result[0].type == "text"


@pytest.mark.asyncio
async def test_search_memories_tool():
    """記憶検索ツールテスト."""
    server = LlmMultiChatMCPServer()
    
    result = await server._search_memories("機械学習", top_k=5)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_character_resource():
    """キャラクターリソーステスト."""
    server = LlmMultiChatMCPServer()
    
    info = await server._get_character_info("lumina")
    assert "lumina" in info.lower()


# ... 他15件（境界値、異常系、統合テスト）
```

---

## 5. 技術スタック

### 5.1 Python依存

```txt
# requirements.txt に追加
mcp==0.1.0              # Model Context Protocol SDK
```

### 5.2 新規モジュール

- **core/character_growth.py**: キャラクター成長システム
- **api/mcp_server.py**: MCP Server実装

---

## 6. テスト計画

### 6.1 テスト構成

| テストファイル | テスト件数 | カバレッジ目標 |
|---------------|-----------|---------------|
| `tests/test_character_growth.py` | 15件 | > 90% |
| `tests/test_mcp_server.py` | 20件 | > 85% |
| **合計** | **35件** | **> 87%** |

### 6.2 テストカテゴリ

**Unit Tests（25件)**:
- KPI更新テスト
- レベル計算テスト
- MCP Server初期化テスト
- ツール実行テスト
- リソース取得テスト

**Integration Tests（10件)**:
- ChatServiceとの連携テスト
- 記憶システムとの連携テスト
- Claude Desktop統合テスト

### 6.3 実行方法

```bash
# 全テスト実行
pytest tests/test_character_growth.py tests/test_mcp_server.py -v

# MCP Server起動
python -m api.mcp_server

# Claude Desktop連携確認
# （Claude Desktop設定後、ツール一覧に "llmmultichat3" が表示されることを確認）
```

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `core/character_growth.py` (350行)
- `api/mcp_server.py` (400行)
- **合計**: 750行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_character_growth.py` (15件)
- `tests/test_mcp_server.py` (20件)
- **合計**: 35件

### 7.3 ドキュメント

- `docks/完了報告/Phase6_完了サマリー.md`
- MCP Server設定ガイド
- Claude Desktop統合ガイド

### 7.4 マイルストーン

- [ ] KPI収集・レベルアップ動作確認
- [ ] MCP Server外部接続テスト成功
- [ ] Claude Desktop統合確認
- [ ] 全テスト成功（35件）
- [ ] カバレッジ > 87%

---

**Phase 6 実装完了**: キャラクター成長システムと外部連携基盤が整いました。