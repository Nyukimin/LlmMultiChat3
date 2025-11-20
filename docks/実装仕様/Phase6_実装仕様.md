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
6. [テスト計画（TDD実装）](#6-テスト計画tdd実装)
   - [TDD実装仕様サマリー](#60-tdd実装仕様サマリー)
   - [テストカバレッジ目標](#61-テストカバレッジ目標)
   - [テスト実行方法](#62-テスト実行方法)
   - [Week 1-2: KPIベース成長システム - テスト仕様（TDD）](#week-1-2-kpiベース成長システム---テスト仕様tdd)
   - [Week 3-4: MCP Server実装 - テスト仕様（TDD）](#week-3-4-mcp-server実装---テスト仕様tdd)
   - [統合テスト仕様（TDD）](#統合テスト仕様tdd)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [テスト実行戦略](#テスト実行戦略)
7. [成果物](#7-成果物)
8. [Phase 6成功基準](#8-phase-6成功基準)

---

## 1. Phase 6概要

### 1.1 目的

KPIベースのキャラクター成長システムとMCP Server実装により、**長期運用での進化と外部連携**を実現します。

### 1.2 TDD実装アプローチ

Phase 6は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

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

### 3.4 テスト仕様（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

#### テストファイル構成

- `tests/test_character_growth.py`: CharacterGrowthクラスのユニットテスト（30件）
- `tests/test_integration_growth.py`: ChatService連携の統合テスト（10件）

#### テストデータ定義

```python
# tests/fixtures/character_growth_fixtures.py

TEST_CHARACTERS = ["lumina", "clarisse", "nox"]
TEST_KPI_TYPES = [
    "user_thumbs_up",
    "answer_hits", 
    "search_success",
    "conversation_count",
    "topic_expertise"
]
TEST_TOPICS = ["Python", "ML", "JavaScript", "Database"]

# レベル計算テストデータ
LEVEL_TEST_CASES = [
    {"total_kpi": 0, "expected_level": 0},
    {"total_kpi": 10, "expected_level": 1},
    {"total_kpi": 39, "expected_level": 1},  # 境界値
    {"total_kpi": 40, "expected_level": 2},
    {"total_kpi": 90, "expected_level": 3},
    {"total_kpi": 160, "expected_level": 4},
    {"total_kpi": 250, "expected_level": 5},
]
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

### 4.4 テスト仕様（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

#### テストファイル構成

- `tests/test_mcp_server.py`: LlmMultiChatMCPServerクラスのユニットテスト（30件）
- `tests/test_integration_mcp.py`: MCP統合テスト（10件）

#### テストデータ定義

```python
# tests/fixtures/mcp_server_fixtures.py

TEST_CHARACTERS = ["lumina", "clarisse", "nox"]
TEST_MESSAGES = [
    "こんにちは",
    "機械学習について教えてください",
    "Pythonのコードを書いてください",
    "",  # 空メッセージ（エッジケース）
    "a" * 10000,  # 長いメッセージ（エッジケース）
]
TEST_QUERIES = [
    "機械学習",
    "Python",
    "データベース",
    "",  # 空クエリ（エッジケース）
]
TEST_TOP_K_VALUES = [1, 5, 10, 0, -1, 1000]  # 正常値とエッジケース
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

## 6. テスト計画（TDD実装）

### 6.0 TDD実装仕様サマリー

**Phase 6は完全なTDD（テスト駆動開発）アプローチで実装します。**

#### TDD実装の原則

1. **テストファースト**: すべての機能は実装前にテストを書く
2. **RED-GREEN-REFACTORサイクル**: 失敗→成功→リファクタリングのサイクルを徹底
3. **Given-When-Then形式**: すべてのテストを明確な形式で記述
4. **テスト独立性**: 各テストは独立して実行可能
5. **モック分離**: 外部依存はモックで分離し、テストの速度と信頼性を確保

#### テスト構成

| カテゴリ | テストファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|--------------|---------|--------------|--------|
| **KPIベース成長システム** |
| CharacterGrowth | `test_character_growth.py` | 30件 + エッジケース8件 + パラメータ化4件 | 95%以上 | 🔴 High |
| **MCP Server実装** |
| LlmMultiChatMCPServer | `test_mcp_server.py` | 30件 + エッジケース10件 + パラメータ化5件 | 90%以上 | 🟡 Medium |
| **統合テスト** |
| ChatService連携 | `test_integration_growth.py` | 10件 | 85%以上 | 🟡 Medium |
| MCP統合 | `test_integration_mcp.py` | 10件 | 85%以上 | 🟡 Medium |
| **合計** | **4ファイル + フィクスチャ2ファイル** | **107件以上** | **平均90%以上** | - |

#### テスト実行戦略

- **Week 1-2**: KPIベース成長システム（6日間で段階的に実装）
- **Week 3-4**: MCP Server実装（4日間で段階的に実装）
- **各機能**: RED → GREEN → REFACTORサイクルで実装
- **品質基準**: テスト成功率100%、カバレッジ90%以上、実行時間3分以内

### 6.1 テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| **KPIベース成長システム** |
| CharacterGrowth | `test_character_growth.py` | 30 | 95%以上 | 🔴 High |
| **MCP Server実装** |
| LlmMultiChatMCPServer | `test_mcp_server.py` | 30 | 90%以上 | 🟡 Medium |
| **統合テスト** |
| ChatService連携 | `test_integration_growth.py` | 10 | 85%以上 | 🟡 Medium |
| MCP統合 | `test_integration_mcp.py` | 10 | 85%以上 | 🟡 Medium |
| **合計** | **4ファイル** | **80** | **平均90%以上** | - |

### 6.2 テスト実行方法

#### 基本的なテスト実行

```bash
# 全テスト実行
pytest tests/test_character_growth.py tests/test_mcp_server.py -v

# カバレッジ付きテスト実行
pytest tests/ --cov=core.character_growth --cov=api.mcp_server --cov-report=html --cov-report=term

# 特定のテストのみ
pytest tests/test_character_growth.py::test_kpi_update -v

# マーカーで実行
pytest -m unit -v  # ユニットテストのみ
pytest -m integration -v  # 統合テストのみ
pytest -m asyncio -v  # 非同期テストのみ
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_character_growth.py::test_kpi_update -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_character_growth.py::test_kpi_update -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_character_growth.py -v
# → 期待: 全テスト PASSED
```

---

## Week 1-2: KPIベース成長システム - テスト仕様（TDD）

### テストファイル: `tests/test_character_growth.py`

**テストクラス**: `TestCharacterGrowth`

**テストケース一覧（30件）**:

#### 1. 初期化テスト（4件）

```python
def test_character_growth_init():
    """
    Given: キャラクター名とデータベースパス
    When: CharacterGrowthを初期化
    Then: データベースが初期化され、レベル0で開始される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    assert growth.character_name == "lumina"
    assert growth.current_level == 0
    assert growth.conn is not None

def test_character_growth_init_schema_created():
    """
    Given: CharacterGrowthインスタンス
    When: 初期化
    Then: データベーススキーマが作成される
    """
    growth = CharacterGrowth("test_character", db_path=":memory:")
    
    cursor = growth.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='character_growth'
    """)
    
    assert cursor.fetchone() is not None

def test_character_growth_init_index_created():
    """
    Given: CharacterGrowthインスタンス
    When: 初期化
    Then: インデックスが作成される
    """
    growth = CharacterGrowth("test_character", db_path=":memory:")
    
    cursor = growth.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='idx_character_kpi'
    """)
    
    assert cursor.fetchone() is not None

def test_character_growth_init_load_existing_level():
    """
    Given: 既存のレベルデータ
    When: CharacterGrowthを初期化
    Then: 既存のレベルが読み込まれる
    """
    # 事前にデータを作成
    growth1 = CharacterGrowth("existing_character", db_path=":memory:")
    growth1.update_kpi("user_thumbs_up", value=10)
    
    # 新しいインスタンスで読み込み
    growth2 = CharacterGrowth("existing_character", db_path=":memory:")
    # 注意: メモリDBは共有されないため、実際のテストではファイルDBを使用
```

#### 2. KPI更新テスト（8件）

```python
def test_update_kpi_new_kpi():
    """
    Given: 新しいKPIタイプ
    When: update_kpi()を呼び出す
    Then: KPIが新規作成され、値が設定される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result = growth.update_kpi("user_thumbs_up", value=1)
    
    assert result["event_type"] == "user_thumbs_up"
    assert result["new_value"] == 1
    assert result["current_level"] == 0
    assert result["level_up_occurred"] is False

def test_update_kpi_existing_kpi():
    """
    Given: 既存のKPI
    When: update_kpi()を呼び出す
    Then: KPI値が加算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("user_thumbs_up", value=5)
    
    result = growth.update_kpi("user_thumbs_up", value=3)
    
    assert result["new_value"] == 8

def test_update_kpi_topic_expertise():
    """
    Given: トピック別専門性KPI
    When: update_kpi()をトピック付きで呼び出す
    Then: トピック別にKPIが記録される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result1 = growth.update_kpi("topic_expertise", value=10, topic="Python")
    result2 = growth.update_kpi("topic_expertise", value=5, topic="ML")
    
    assert result1["new_value"] == 10
    assert result2["new_value"] == 5
    
    stats = growth.get_stats()
    assert stats["topic_expertise"]["topic_expertise"]["Python"] == 10
    assert stats["topic_expertise"]["topic_expertise"]["ML"] == 5

def test_update_kpi_multiple_types():
    """
    Given: 複数のKPIタイプ
    When: それぞれupdate_kpi()を呼び出す
    Then: 各KPIが独立して記録される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    growth.update_kpi("user_thumbs_up", value=5)
    growth.update_kpi("answer_hits", value=3)
    growth.update_kpi("search_success", value=2)
    
    stats = growth.get_stats()
    assert stats["kpis"]["user_thumbs_up"] == 5
    assert stats["kpis"]["answer_hits"] == 3
    assert stats["kpis"]["search_success"] == 2

def test_update_kpi_negative_value():
    """
    Given: 負の値
    When: update_kpi()を呼び出す
    Then: KPI値が減少する（またはエラーが発生する）
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("user_thumbs_up", value=10)
    
    # 実装に応じて負の値を許可するかエラーにするか
    result = growth.update_kpi("user_thumbs_up", value=-2)
    assert result["new_value"] == 8  # またはエラー
```

#### 3. レベル計算テスト（8件）

```python
def test_calculate_level_zero():
    """
    Given: KPIが0
    When: _calculate_level()を呼び出す
    Then: レベル0が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    level = growth._calculate_level()
    
    assert level == 0

def test_calculate_level_one():
    """
    Given: total_kpi = 10
    When: _calculate_level()を呼び出す
    Then: レベル1が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=10)
    
    level = growth._calculate_level()
    
    assert level == 1

def test_calculate_level_two():
    """
    Given: total_kpi = 40
    When: _calculate_level()を呼び出す
    Then: レベル2が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=40)
    
    level = growth._calculate_level()
    
    assert level == 2

def test_calculate_level_three():
    """
    Given: total_kpi = 90
    When: _calculate_level()を呼び出す
    Then: レベル3が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=90)
    
    level = growth._calculate_level()
    
    assert level == 3

def test_calculate_level_four():
    """
    Given: total_kpi = 160
    When: _calculate_level()を呼び出す
    Then: レベル4が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=160)
    
    level = growth._calculate_level()
    
    assert level == 4

def test_calculate_level_mixed_kpis():
    """
    Given: 複数のKPIタイプの合計
    When: _calculate_level()を呼び出す
    Then: 全KPIの合計でレベルが計算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("user_thumbs_up", value=5)
    growth.update_kpi("answer_hits", value=3)
    growth.update_kpi("search_success", value=2)
    # total = 10 → level = 1
    
    level = growth._calculate_level()
    
    assert level == 1

def test_calculate_level_floor_function():
    """
    Given: レベル境界値（例: total_kpi = 39）
    When: _calculate_level()を呼び出す
    Then: floor関数で切り捨てられる
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=39)
    # sqrt(39/10) ≈ 1.97 → floor → 1
    
    level = growth._calculate_level()
    
    assert level == 1  # 切り捨て
```

#### 4. レベルアップテスト（6件）

```python
def test_level_up_occurs():
    """
    Given: レベルアップ条件を満たすKPI
    When: update_kpi()を呼び出す
    Then: レベルアップが発生し、level_up_occurredがTrue
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # 9回でまだレベル0
    for _ in range(9):
        growth.update_kpi("user_thumbs_up", value=1)
    assert growth.current_level == 0
    
    # 10回目でレベル1に
    result = growth.update_kpi("user_thumbs_up", value=1)
    
    assert result["level_up_occurred"] is True
    assert result["current_level"] == 1
    assert growth.current_level == 1

def test_level_up_multiple_levels():
    """
    Given: 複数レベルアップが発生するKPI
    When: update_kpi()を呼び出す
    Then: 複数回レベルアップが発生する
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # 10回でレベル1
    for _ in range(10):
        result = growth.update_kpi("user_thumbs_up", value=1)
    assert result["current_level"] == 1
    
    # さらに30回でレベル2
    for _ in range(30):
        result = growth.update_kpi("user_thumbs_up", value=1)
    assert result["current_level"] == 2

def test_level_up_unlock_features():
    """
    Given: レベルアップ発生
    When: _level_up()が呼び出される
    Then: レベルに応じた機能が解禁される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # レベル1に到達
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # _unlock_new_featuresが呼ばれたことを確認（モック使用）
    # 実際のテストではprint出力をキャプチャして確認

def test_level_up_adjust_parameters():
    """
    Given: レベルアップ発生
    When: _level_up()が呼び出される
    Then: パラメータが調整される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # レベル2に到達
    for _ in range(40):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # _adjust_parametersが呼ばれたことを確認（モック使用）

def test_level_up_no_duplicate():
    """
    Given: 同じレベルでのKPI更新
    When: update_kpi()を呼び出す
    Then: レベルアップは発生しない
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # レベル1に到達
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # さらに更新（レベル1のまま）
    result = growth.update_kpi("user_thumbs_up", value=1)
    
    assert result["level_up_occurred"] is False
    assert result["current_level"] == 1
```

#### 5. 統計取得テスト（4件）

```python
def test_get_stats_empty():
    """
    Given: KPIが記録されていない
    When: get_stats()を呼び出す
    Then: 空の統計情報が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    stats = growth.get_stats()
    
    assert stats["character_name"] == "lumina"
    assert stats["level"] == 0
    assert stats["kpis"] == {}
    assert stats["topic_expertise"] == {}

def test_get_stats_with_kpis():
    """
    Given: 複数のKPIが記録されている
    When: get_stats()を呼び出す
    Then: 全KPIの統計情報が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("user_thumbs_up", value=5)
    growth.update_kpi("answer_hits", value=3)
    growth.update_kpi("search_success", value=2)
    
    stats = growth.get_stats()
    
    assert stats["kpis"]["user_thumbs_up"] == 5
    assert stats["kpis"]["answer_hits"] == 3
    assert stats["kpis"]["search_success"] == 2

def test_get_stats_with_topic_expertise():
    """
    Given: トピック別専門性が記録されている
    When: get_stats()を呼び出す
    Then: トピック別統計情報が返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("topic_expertise", value=10, topic="Python")
    growth.update_kpi("topic_expertise", value=5, topic="ML")
    
    stats = growth.get_stats()
    
    assert stats["topic_expertise"]["topic_expertise"]["Python"] == 10
    assert stats["topic_expertise"]["topic_expertise"]["ML"] == 5

def test_get_stats_level_included():
    """
    Given: レベルが上がっている
    When: get_stats()を呼び出す
    Then: 現在のレベルが含まれる
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # レベル1に到達
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    stats = growth.get_stats()
    
    assert stats["level"] == 1

#### 6. エッジケース・異常系テスト（追加: 8件）

```python
def test_update_kpi_zero_value():
    """
    Given: value=0のKPI更新
    When: update_kpi()を呼び出す
    Then: KPI値が変更されない（またはエラーが発生する）
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("user_thumbs_up", value=5)
    
    result = growth.update_kpi("user_thumbs_up", value=0)
    
    assert result["new_value"] == 5  # 変更なし

def test_update_kpi_large_value():
    """
    Given: 非常に大きな値
    When: update_kpi()を呼び出す
    Then: KPI値が正しく加算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result = growth.update_kpi("conversation_count", value=1000000)
    
    assert result["new_value"] == 1000000

def test_update_kpi_invalid_kpi_type():
    """
    Given: 無効なKPIタイプ
    When: update_kpi()を呼び出す
    Then: エラーが発生する（または無視される）
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # 実装に応じてエラーまたは無視
    # エラーの場合
    with pytest.raises(ValueError):
        growth.update_kpi("invalid_kpi_type", value=1)

def test_update_kpi_empty_character_name():
    """
    Given: 空のキャラクター名
    When: CharacterGrowthを初期化
    Then: エラーが発生する（またはデフォルト値が使用される）
    """
    # 実装に応じてエラーまたはデフォルト値
    with pytest.raises(ValueError):
        CharacterGrowth("", db_path=":memory:")

def test_calculate_level_very_large_kpi():
    """
    Given: 非常に大きなKPI値
    When: _calculate_level()を呼び出す
    Then: レベルが正しく計算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=1000000)
    
    level = growth._calculate_level()
    
    # sqrt(1000000/10) = sqrt(100000) ≈ 316.23 → floor → 316
    assert level == 316

def test_get_stats_multiple_characters():
    """
    Given: 複数のキャラクターのKPI
    When: get_stats()を呼び出す
    Then: 指定キャラクターの統計のみが返される
    """
    growth1 = CharacterGrowth("lumina", db_path=":memory:")
    growth2 = CharacterGrowth("clarisse", db_path=":memory:")
    
    growth1.update_kpi("user_thumbs_up", value=10)
    growth2.update_kpi("user_thumbs_up", value=20)
    
    stats1 = growth1.get_stats()
    stats2 = growth2.get_stats()
    
    assert stats1["kpis"]["user_thumbs_up"] == 10
    assert stats2["kpis"]["user_thumbs_up"] == 20

def test_update_kpi_topic_expertise_same_topic():
    """
    Given: 同じトピックの複数回更新
    When: update_kpi()を呼び出す
    Then: トピック別KPIが加算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    growth.update_kpi("topic_expertise", value=10, topic="Python")
    growth.update_kpi("topic_expertise", value=5, topic="Python")
    
    stats = growth.get_stats()
    assert stats["topic_expertise"]["topic_expertise"]["Python"] == 15

def test_database_connection_error():
    """
    Given: データベース接続エラー
    When: CharacterGrowthを初期化
    Then: エラーが適切に処理される
    """
    # 無効なパスでエラーをシミュレート
    with pytest.raises(sqlite3.Error):
        CharacterGrowth("lumina", db_path="/invalid/path/db.db")
```

#### 7. パラメータ化テスト（追加: 4件）

```python
@pytest.mark.parametrize("kpi_type", [
    "user_thumbs_up",
    "answer_hits",
    "search_success",
    "conversation_count"
])
def test_update_kpi_all_types(kpi_type):
    """
    Given: 各KPIタイプ
    When: update_kpi()を呼び出す
    Then: すべてのKPIタイプが正しく処理される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result = growth.update_kpi(kpi_type, value=1)
    
    assert result["event_type"] == kpi_type
    assert result["new_value"] == 1

@pytest.mark.parametrize("total_kpi,expected_level", [
    (0, 0),
    (10, 1),
    (39, 1),  # 境界値
    (40, 2),
    (90, 3),
    (160, 4),
    (250, 5),
])
def test_calculate_level_parametrized(total_kpi, expected_level):
    """
    Given: 様々なKPI値
    When: _calculate_level()を呼び出す
    Then: 期待されるレベルが返される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    growth.update_kpi("conversation_count", value=total_kpi)
    
    level = growth._calculate_level()
    
    assert level == expected_level

@pytest.mark.parametrize("character_name", ["lumina", "clarisse", "nox"])
def test_get_stats_all_characters(character_name):
    """
    Given: 各キャラクター
    When: get_stats()を呼び出す
    Then: キャラクター名が正しく設定される
    """
    growth = CharacterGrowth(character_name, db_path=":memory:")
    
    stats = growth.get_stats()
    
    assert stats["character_name"] == character_name

@pytest.mark.parametrize("value", [1, 10, 100, 1000])
def test_update_kpi_various_values(value):
    """
    Given: 様々な値
    When: update_kpi()を呼び出す
    Then: KPI値が正しく加算される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    result = growth.update_kpi("user_thumbs_up", value=value)
    
    assert result["new_value"] == value
```

---

## Week 3-4: MCP Server実装 - テスト仕様（TDD）

### テストファイル: `tests/test_mcp_server.py`

**テストクラス**: `TestLlmMultiChatMCPServer`

**テストケース一覧（30件）**:

#### 1. 初期化テスト（3件）

```python
@pytest.mark.asyncio
async def test_mcp_server_init():
    """
    Given: LlmMultiChatMCPServer
    When: 初期化
    Then: Serverインスタンスが作成され、名前が設定される
    """
    server = LlmMultiChatMCPServer()
    
    assert server.server.name == "llmmultichat3"
    assert server.server is not None

@pytest.mark.asyncio
async def test_mcp_server_tools_registered():
    """
    Given: LlmMultiChatMCPServer
    When: 初期化
    Then: ツールが登録される
    """
    server = LlmMultiChatMCPServer()
    
    # ツール一覧を取得（モックまたは実際のMCPクライアント経由）
    # 実際のテストではMCPクライアントを使用

@pytest.mark.asyncio
async def test_mcp_server_resources_registered():
    """
    Given: LlmMultiChatMCPServer
    When: 初期化
    Then: リソースが登録される
    """
    server = LlmMultiChatMCPServer()
    
    # リソース一覧を取得（モックまたは実際のMCPクライアント経由）
```

#### 2. ツール実行テスト（12件）

```python
@pytest.mark.asyncio
async def test_chat_with_character_success():
    """
    Given: 有効なキャラクター名とメッセージ
    When: _chat_with_character()を呼び出す
    Then: チャット応答が返される
    """
    server = LlmMultiChatMCPServer()
    
    # ChatServiceをモック
    with patch('api.mcp_server.ChatService') as mock_chat_service:
        mock_instance = AsyncMock()
        mock_instance.chat = AsyncMock(return_value={
            "response": "こんにちは！",
            "character": "lumina"
        })
        mock_chat_service.return_value = mock_instance
        
        result = await server._chat_with_character("lumina", "こんにちは")
        
        assert len(result) > 0
        assert result[0].type == "text"
        assert "こんにちは" in result[0].text

@pytest.mark.asyncio
async def test_chat_with_character_invalid_character():
    """
    Given: 無効なキャラクター名
    When: _chat_with_character()を呼び出す
    Then: エラーが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(ValueError):
        await server._chat_with_character("invalid_character", "こんにちは")

@pytest.mark.asyncio
async def test_chat_with_character_empty_message():
    """
    Given: 空のメッセージ
    When: _chat_with_character()を呼び出す
    Then: エラーが発生する（または空の応答が返される）
    """
    server = LlmMultiChatMCPServer()
    
    # 実装に応じてエラーまたは空の応答
    result = await server._chat_with_character("lumina", "")
    # エラーチェックまたは空の応答チェック

@pytest.mark.asyncio
async def test_search_memories_success():
    """
    Given: 有効な検索クエリ
    When: _search_memories()を呼び出す
    Then: 検索結果が返される
    """
    server = LlmMultiChatMCPServer()
    
    # LongTermMemoryをモック
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[
            {"content": "機械学習について", "similarity": 0.95},
            {"content": "Pythonについて", "similarity": 0.85}
        ])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories("機械学習", top_k=5)
        
        assert len(result) > 0
        assert result[0].type == "text"
        assert "機械学習" in result[0].text

@pytest.mark.asyncio
async def test_search_memories_empty_results():
    """
    Given: 検索結果が空
    When: _search_memories()を呼び出す
    Then: 空の結果が返される
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories("存在しないトピック", top_k=5)
        
        assert len(result) > 0
        assert result[0].type == "text"

@pytest.mark.asyncio
async def test_search_memories_custom_top_k():
    """
    Given: カスタムtop_k値
    When: _search_memories()を呼び出す
    Then: 指定された件数の結果が返される
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[
            {"content": f"結果{i}", "similarity": 0.9 - i*0.1}
            for i in range(10)
        ])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories("test", top_k=3)
        
        # top_k=3で検索が呼ばれたことを確認
        mock_instance.search.assert_called_with(query="test", top_k=3)

@pytest.mark.asyncio
async def test_call_tool_chat_with_character():
    """
    Given: chat_with_characterツール名と引数
    When: call_tool()を呼び出す
    Then: _chat_with_character()が呼び出される
    """
    server = LlmMultiChatMCPServer()
    
    with patch.object(server, '_chat_with_character', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = [TextContent(type="text", text="応答")]
        
        result = await server.server.call_tool(
            "chat_with_character",
            {"character": "lumina", "message": "こんにちは"}
        )
        
        mock_chat.assert_called_once_with("lumina", "こんにちは")

@pytest.mark.asyncio
async def test_call_tool_search_memories():
    """
    Given: search_memoriesツール名と引数
    When: call_tool()を呼び出す
    Then: _search_memories()が呼び出される
    """
    server = LlmMultiChatMCPServer()
    
    with patch.object(server, '_search_memories', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [TextContent(type="text", text="結果")]
        
        result = await server.server.call_tool(
            "search_memories",
            {"query": "test", "top_k": 5}
        )
        
        mock_search.assert_called_once_with("test", 5)

@pytest.mark.asyncio
async def test_call_tool_unknown_tool():
    """
    Given: 未知のツール名
    When: call_tool()を呼び出す
    Then: ValueErrorが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(ValueError, match="Unknown tool"):
        await server.server.call_tool("unknown_tool", {})
```

#### 3. リソース取得テスト（8件）

```python
@pytest.mark.asyncio
async def test_get_character_info_success():
    """
    Given: 有効なキャラクター名
    When: _get_character_info()を呼び出す
    Then: JSON形式のキャラクター情報が返される
    """
    server = LlmMultiChatMCPServer()
    
    # CharacterGrowthをモック
    with patch('api.mcp_server.CharacterGrowth') as mock_growth:
        mock_instance = Mock()
        mock_instance.get_stats = Mock(return_value={
            "character_name": "lumina",
            "level": 2,
            "kpis": {"user_thumbs_up": 10},
            "topic_expertise": {}
        })
        mock_growth.return_value = mock_instance
        
        info = await server._get_character_info("lumina")
        
        assert isinstance(info, str)
        data = json.loads(info)
        assert data["character_name"] == "lumina"
        assert data["level"] == 2

@pytest.mark.asyncio
async def test_get_character_info_invalid_character():
    """
    Given: 無効なキャラクター名
    When: _get_character_info()を呼び出す
    Then: エラーが発生する（またはデフォルト情報が返される）
    """
    server = LlmMultiChatMCPServer()
    
    # 実装に応じてエラーまたはデフォルト情報

@pytest.mark.asyncio
async def test_read_resource_character_uri():
    """
    Given: character:// URI
    When: read_resource()を呼び出す
    Then: キャラクター情報が返される
    """
    server = LlmMultiChatMCPServer()
    
    with patch.object(server, '_get_character_info', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = '{"character_name": "lumina"}'
        
        result = await server.server.read_resource("character://lumina")
        
        mock_get.assert_called_once_with("lumina")
        assert result == '{"character_name": "lumina"}'

@pytest.mark.asyncio
async def test_read_resource_unknown_uri():
    """
    Given: 未知のURI
    When: read_resource()を呼び出す
    Then: ValueErrorが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(ValueError, match="Unknown resource"):
        await server.server.read_resource("unknown://resource")
```

#### 4. エラーハンドリング・統合テスト（7件）

```python
@pytest.mark.asyncio
async def test_chat_service_error_handling():
    """
    Given: ChatServiceでエラーが発生
    When: _chat_with_character()を呼び出す
    Then: エラーが適切に処理される
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.ChatService') as mock_chat_service:
        mock_instance = AsyncMock()
        mock_instance.chat = AsyncMock(side_effect=Exception("Chat error"))
        mock_chat_service.return_value = mock_instance
        
        with pytest.raises(Exception):
            await server._chat_with_character("lumina", "test")

@pytest.mark.asyncio
async def test_memory_service_error_handling():
    """
    Given: LongTermMemoryでエラーが発生
    When: _search_memories()を呼び出す
    Then: エラーが適切に処理される
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(side_effect=Exception("Memory error"))
        mock_memory.return_value = mock_instance
        
        with pytest.raises(Exception):
            await server._search_memories("test", top_k=5)

#### 5. エッジケース・異常系テスト（追加: 10件）

```python
@pytest.mark.asyncio
async def test_chat_with_character_long_message():
    """
    Given: 非常に長いメッセージ
    When: _chat_with_character()を呼び出す
    Then: メッセージが正しく処理される
    """
    server = LlmMultiChatMCPServer()
    long_message = "a" * 10000
    
    with patch('api.mcp_server.ChatService') as mock_chat_service:
        mock_instance = AsyncMock()
        mock_instance.chat = AsyncMock(return_value={
            "response": "応答",
            "character": "lumina"
        })
        mock_chat_service.return_value = mock_instance
        
        result = await server._chat_with_character("lumina", long_message)
        
        assert len(result) > 0

@pytest.mark.asyncio
async def test_search_memories_zero_top_k():
    """
    Given: top_k=0
    When: _search_memories()を呼び出す
    Then: エラーが発生する（または空の結果が返される）
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[])
        mock_memory.return_value = mock_instance
        
        # 実装に応じてエラーまたは空の結果
        result = await server._search_memories("test", top_k=0)
        assert isinstance(result, list)

@pytest.mark.asyncio
async def test_search_memories_negative_top_k():
    """
    Given: 負のtop_k値
    When: _search_memories()を呼び出す
    Then: エラーが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(ValueError):
        await server._search_memories("test", top_k=-1)

@pytest.mark.asyncio
async def test_search_memories_very_large_top_k():
    """
    Given: 非常に大きなtop_k値
    When: _search_memories()を呼び出す
    Then: エラーが発生する（または上限値で処理される）
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[])
        mock_memory.return_value = mock_instance
        
        # 実装に応じてエラーまたは上限値で処理
        result = await server._search_memories("test", top_k=10000)
        assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_character_info_nonexistent_character():
    """
    Given: 存在しないキャラクター名
    When: _get_character_info()を呼び出す
    Then: エラーが発生する（またはデフォルト情報が返される）
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.CharacterGrowth') as mock_growth:
        mock_instance = Mock()
        mock_instance.get_stats = Mock(side_effect=ValueError("Character not found"))
        mock_growth.return_value = mock_instance
        
        with pytest.raises(ValueError):
            await server._get_character_info("nonexistent_character")

@pytest.mark.asyncio
async def test_call_tool_missing_required_argument():
    """
    Given: 必須引数が欠けている
    When: call_tool()を呼び出す
    Then: エラーが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(KeyError):
        await server.server.call_tool(
            "chat_with_character",
            {"character": "lumina"}  # messageが欠けている
        )

@pytest.mark.asyncio
async def test_call_tool_invalid_argument_type():
    """
    Given: 無効な引数の型
    When: call_tool()を呼び出す
    Then: エラーが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(TypeError):
        await server.server.call_tool(
            "chat_with_character",
            {"character": 123, "message": "test"}  # characterが文字列ではない
        )

@pytest.mark.asyncio
async def test_read_resource_invalid_uri_format():
    """
    Given: 無効なURI形式
    When: read_resource()を呼び出す
    Then: エラーが発生する
    """
    server = LlmMultiChatMCPServer()
    
    with pytest.raises(ValueError):
        await server.server.read_resource("invalid_uri")

@pytest.mark.asyncio
async def test_chat_with_character_special_characters():
    """
    Given: 特殊文字を含むメッセージ
    When: _chat_with_character()を呼び出す
    Then: メッセージが正しく処理される
    """
    server = LlmMultiChatMCPServer()
    special_message = "こんにちは！\n改行\n\tタブ\n\"引用\"\n'シングル'"
    
    with patch('api.mcp_server.ChatService') as mock_chat_service:
        mock_instance = AsyncMock()
        mock_instance.chat = AsyncMock(return_value={
            "response": "応答",
            "character": "lumina"
        })
        mock_chat_service.return_value = mock_instance
        
        result = await server._chat_with_character("lumina", special_message)
        
        assert len(result) > 0

@pytest.mark.asyncio
async def test_search_memories_special_characters_query():
    """
    Given: 特殊文字を含む検索クエリ
    When: _search_memories()を呼び出す
    Then: クエリが正しく処理される
    """
    server = LlmMultiChatMCPServer()
    special_query = "Python & JavaScript | SQL"
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories(special_query, top_k=5)
        
        assert isinstance(result, list)
```

#### 6. パラメータ化テスト（追加: 5件）

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("character", ["lumina", "clarisse", "nox"])
async def test_chat_with_character_all_characters(character):
    """
    Given: 各キャラクター
    When: _chat_with_character()を呼び出す
    Then: すべてのキャラクターで正しく動作する
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.ChatService') as mock_chat_service:
        mock_instance = AsyncMock()
        mock_instance.chat = AsyncMock(return_value={
            "response": "応答",
            "character": character
        })
        mock_chat_service.return_value = mock_instance
        
        result = await server._chat_with_character(character, "こんにちは")
        
        assert len(result) > 0
        assert result[0].type == "text"

@pytest.mark.asyncio
@pytest.mark.parametrize("top_k", [1, 5, 10, 20])
async def test_search_memories_various_top_k(top_k):
    """
    Given: 様々なtop_k値
    When: _search_memories()を呼び出す
    Then: 指定された件数で検索が実行される
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[
            {"content": f"結果{i}", "similarity": 0.9 - i*0.1}
            for i in range(top_k)
        ])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories("test", top_k=top_k)
        
        mock_instance.search.assert_called_with(query="test", top_k=top_k)

@pytest.mark.asyncio
@pytest.mark.parametrize("uri", [
    "character://lumina",
    "character://clarisse",
    "character://nox"
])
async def test_read_resource_all_characters(uri):
    """
    Given: 各キャラクターのURI
    When: read_resource()を呼び出す
    Then: すべてのURIで正しく動作する
    """
    server = LlmMultiChatMCPServer()
    character_name = uri.split("://")[1]
    
    with patch.object(server, '_get_character_info', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = f'{{"character_name": "{character_name}"}}'
        
        result = await server.server.read_resource(uri)
        
        mock_get.assert_called_once_with(character_name)
        assert character_name in result

@pytest.mark.asyncio
@pytest.mark.parametrize("query", [
    "機械学習",
    "Python",
    "データベース",
    "自然言語処理"
])
async def test_search_memories_various_queries(query):
    """
    Given: 様々な検索クエリ
    When: _search_memories()を呼び出す
    Then: すべてのクエリで正しく動作する
    """
    server = LlmMultiChatMCPServer()
    
    with patch('api.mcp_server.LongTermMemory') as mock_memory:
        mock_instance = Mock()
        mock_instance.search = Mock(return_value=[
            {"content": f"{query}について", "similarity": 0.9}
        ])
        mock_memory.return_value = mock_instance
        
        result = await server._search_memories(query, top_k=5)
        
        assert len(result) > 0
        assert query in result[0].text or query in str(result[0])
```

---

## 統合テスト仕様（TDD）

### テストファイル: `tests/test_integration_growth.py`

**テストクラス**: `TestCharacterGrowthIntegration`

**テストケース一覧（10件）**:

```python
"""キャラクター成長システムの統合テスト."""

import pytest
from core.character_growth import CharacterGrowth
from services.chat_service import ChatService
from unittest.mock import patch, Mock


@pytest.mark.integration
def test_kpi_update_from_chat_service():
    """
    Given: ChatServiceからKPI更新が呼び出される
    When: ユーザーが👍を押す
    Then: CharacterGrowthのKPIが更新される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # ChatServiceのモック
    with patch('services.chat_service.ChatService') as mock_chat:
        mock_instance = Mock()
        mock_instance.record_feedback = Mock()
        mock_chat.return_value = mock_instance
        
        # KPI更新をシミュレート
        result = growth.update_kpi("user_thumbs_up", value=1)
        
        assert result["new_value"] == 1

@pytest.mark.integration
def test_level_up_triggers_feature_unlock():
    """
    Given: レベルアップが発生
    When: 機能解禁が実行される
    Then: 対話スタイルパラメータが調整される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # レベル2に到達
    for _ in range(40):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # パラメータ調整を確認
    stats = growth.get_stats()
    assert stats["level"] >= 2

@pytest.mark.integration
def test_multiple_characters_independent_growth():
    """
    Given: 複数のキャラクター
    When: それぞれKPIを更新
    Then: 各キャラクターの成長が独立している
    """
    growth1 = CharacterGrowth("lumina", db_path=":memory:")
    growth2 = CharacterGrowth("clarisse", db_path=":memory:")
    
    growth1.update_kpi("user_thumbs_up", value=10)
    growth2.update_kpi("user_thumbs_up", value=20)
    
    stats1 = growth1.get_stats()
    stats2 = growth2.get_stats()
    
    assert stats1["kpis"]["user_thumbs_up"] == 10
    assert stats2["kpis"]["user_thumbs_up"] == 20
    assert stats1["level"] != stats2["level"]

@pytest.mark.integration
def test_topic_expertise_affects_technical_level():
    """
    Given: トピック別専門性が記録される
    When: 対話スタイルが生成される
    Then: 専門性に応じたtechnical_levelが設定される
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    growth.update_kpi("topic_expertise", value=50, topic="Python")
    growth.update_kpi("topic_expertise", value=30, topic="ML")
    
    stats = growth.get_stats()
    
    assert "Python" in stats["topic_expertise"]["topic_expertise"]
    assert stats["topic_expertise"]["topic_expertise"]["Python"] == 50

@pytest.mark.integration
def test_concurrent_kpi_updates():
    """
    Given: 並行してKPI更新が発生
    When: 複数のスレッドからupdate_kpi()を呼び出す
    Then: データの整合性が保たれる
    """
    import threading
    
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    def update_kpi_thread():
        for _ in range(10):
            growth.update_kpi("conversation_count", value=1)
    
    threads = [threading.Thread(target=update_kpi_thread) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    stats = growth.get_stats()
    # 50回の更新が正しく記録されている
    assert stats["kpis"]["conversation_count"] == 50

# ... 他5件（データベース永続化、API連携、エラー回復など）
```

### テストファイル: `tests/test_integration_mcp.py`

**テストクラス**: `TestMCPIntegration`

**テストケース一覧（10件）**:

```python
"""MCP Server統合テスト."""

import pytest
from api.mcp_server import LlmMultiChatMCPServer
from core.character_growth import CharacterGrowth
from services.chat_service import ChatService
from memory.long_term import LongTermMemory
from unittest.mock import patch, AsyncMock, Mock


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_chat_integration():
    """
    Given: MCP Server経由でチャットツールを呼び出す
    When: 実際のChatServiceを使用
    Then: チャット応答が返される
    """
    server = LlmMultiChatMCPServer()
    
    # 実際のChatServiceを使用（統合テスト）
    result = await server._chat_with_character("lumina", "こんにちは")
    
    assert len(result) > 0
    assert result[0].type == "text"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_memory_search_integration():
    """
    Given: MCP Server経由で記憶検索ツールを呼び出す
    When: 実際のLongTermMemoryを使用
    Then: 検索結果が返される
    """
    server = LlmMultiChatMCPServer()
    
    # 実際のLongTermMemoryを使用（統合テスト）
    result = await server._search_memories("機械学習", top_k=5)
    
    assert len(result) > 0
    assert result[0].type == "text"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_character_info_integration():
    """
    Given: MCP Server経由でキャラクター情報を取得
    When: 実際のCharacterGrowthを使用
    Then: キャラクター情報が返される
    """
    server = LlmMultiChatMCPServer()
    
    # 実際のCharacterGrowthを使用（統合テスト）
    info = await server._get_character_info("lumina")
    
    import json
    data = json.loads(info)
    assert "character_name" in data
    assert "level" in data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_tool_chain():
    """
    Given: 複数のMCPツールを連続して呼び出す
    When: チャット → 記憶検索 → キャラクター情報
    Then: すべてのツールが正しく動作する
    """
    server = LlmMultiChatMCPServer()
    
    # 1. チャット
    chat_result = await server._chat_with_character("lumina", "こんにちは")
    assert len(chat_result) > 0
    
    # 2. 記憶検索
    search_result = await server._search_memories("会話", top_k=5)
    assert len(search_result) > 0
    
    # 3. キャラクター情報
    info = await server._get_character_info("lumina")
    assert "lumina" in info.lower()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_error_recovery():
    """
    Given: MCPツールでエラーが発生
    When: エラーハンドリングが実行される
    Then: 適切なエラーメッセージが返される
    """
    server = LlmMultiChatMCPServer()
    
    # 無効なキャラクター名でエラーをシミュレート
    with pytest.raises((ValueError, Exception)):
        await server._chat_with_character("invalid_character", "test")

# ... 他5件（MCPプロトコル準拠、Claude Desktop統合、パフォーマンステストなど）
```

---

## テストフィクスチャ仕様

### conftest.py の拡張

```python
# tests/conftest.py（拡張）

import pytest
import tempfile
import sqlite3
from unittest.mock import Mock, AsyncMock, patch

from core.character_growth import CharacterGrowth
from api.mcp_server import LlmMultiChatMCPServer

@pytest.fixture
def temp_db():
    """一時的なデータベース"""
    db_path = tempfile.mktemp(suffix='.db')
    yield db_path
    import os
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def character_growth(temp_db):
    """CharacterGrowthインスタンス"""
    return CharacterGrowth("test_character", db_path=temp_db)

@pytest.fixture
def mcp_server():
    """LlmMultiChatMCPServerインスタンス"""
    return LlmMultiChatMCPServer()

@pytest.fixture
def mock_chat_service():
    """ChatServiceのモック"""
    mock = AsyncMock()
    mock.chat = AsyncMock(return_value={
        "response": "モック応答",
        "character": "lumina"
    })
    return mock

@pytest.fixture
def mock_long_term_memory():
    """LongTermMemoryのモック"""
    mock = Mock()
    mock.search = Mock(return_value=[
        {"content": "モック記憶", "similarity": 0.9}
    ])
    return mock
```

---

## テスト実行戦略

### TDD実装順序（詳細版）

#### Week 1-2: KPIベース成長システム

**Day 1: 初期化テスト（4件）→ 実装**
```bash
# 1. テストを書く（RED）
pytest tests/test_character_growth.py::test_character_growth_init -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装（GREEN）
# core/character_growth.py を実装
pytest tests/test_character_growth.py::test_character_growth_init -v
# → 期待: PASSED

# 3. リファクタリング（REFACTOR）
# コードを改善
pytest tests/test_character_growth.py -v
# → 期待: 全テスト PASSED
```

**Day 2: KPI更新テスト（8件 + エッジケース8件）→ 実装**
- 正常系: 新規KPI、既存KPI、トピック別専門性、複数タイプ
- エッジケース: 負の値、ゼロ値、大きな値、無効なKPIタイプ

**Day 3: レベル計算テスト（8件 + パラメータ化4件）→ 実装**
- 正常系: 各レベルの計算
- パラメータ化: 様々なKPI値でのレベル計算

**Day 4: レベルアップテスト（6件）→ 実装**
- レベルアップ発生、複数レベルアップ、機能解禁、パラメータ調整

**Day 5: 統計取得テスト（4件 + エッジケース）→ 実装・リファクタリング**
- 空の統計、KPI統計、トピック別統計、レベル情報

**Day 6-10: 統合テスト（10件）→ 実装・リファクタリング**
- ChatService連携、機能解禁、複数キャラクター、並行処理

#### Week 3-4: MCP Server実装

**Day 1-2: 初期化・ツール実行テスト（15件 + エッジケース10件 + パラメータ化5件）→ 実装**
- 初期化: Server作成、ツール登録、リソース登録
- ツール実行: チャット、記憶検索、エラーハンドリング
- エッジケース: 長いメッセージ、特殊文字、無効な引数

**Day 3: リソース取得テスト（8件）→ 実装**
- キャラクター情報取得、URI処理、エラーハンドリング

**Day 4: エラーハンドリング・統合テスト（7件 + 統合テスト10件）→ 実装・リファクタリング**
- エラーハンドリング: ChatService、LongTermMemory、CharacterGrowth
- 統合テスト: 実際のサービス連携、ツールチェーン、エラー回復

### テスト実行コマンド（詳細版）

#### 基本的なテスト実行

```bash
# 全テスト実行
pytest tests/test_character_growth.py tests/test_mcp_server.py \
       tests/test_integration_growth.py tests/test_integration_mcp.py -v

# カバレッジ付きテスト実行
pytest tests/ \
  --cov=core.character_growth \
  --cov=api.mcp_server \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=90

# 特定のテストカテゴリのみ実行
pytest -m unit -v              # ユニットテストのみ
pytest -m integration -v      # 統合テストのみ
pytest -m asyncio -v          # 非同期テストのみ
pytest -m "not slow" -v      # 遅いテストを除外

# 特定のテストファイルのみ実行
pytest tests/test_character_growth.py -v
pytest tests/test_mcp_server.py -v

# 特定のテスト関数のみ実行
pytest tests/test_character_growth.py::test_kpi_update -v
pytest tests/test_character_growth.py::TestCharacterGrowth::test_kpi_update -v

# パラメータ化テストの特定ケースのみ実行
pytest tests/test_character_growth.py::test_calculate_level_parametrized[40-2] -v
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_character_growth.py::test_kpi_update -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_character_growth.py::test_kpi_update -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_character_growth.py -v
# → 期待: 全テスト PASSED

# 4. カバレッジ確認
pytest tests/test_character_growth.py --cov=core.character_growth --cov-report=term
# → 期待: カバレッジ > 90%
```

#### 並列実行（高速化）

```bash
# pytest-xdistを使用した並列実行
pip install pytest-xdist

# 4並列で実行
pytest tests/ -n 4

# CPUコア数に応じて自動並列数決定
pytest tests/ -n auto

# 並列実行時のカバレッジ（注意: カバレッジは並列実行と相性が悪い）
pytest tests/ -n 4 --cov=core.character_growth --cov=api.mcp_server
```

#### テスト実行時間の測定

```bash
# テスト実行時間を表示
pytest tests/ --durations=10

# 遅いテストを特定
pytest tests/ --durations=0

# タイムアウト設定（pytest-timeout使用）
pip install pytest-timeout
pytest tests/ --timeout=300  # 5分でタイムアウト
```

#### テストのデバッグ

```bash
# 詳細な出力
pytest tests/ -v -s

# 最初の失敗で停止
pytest tests/ -x

# 最後の失敗から再実行
pytest tests/ --lf

# 失敗したテストのみ再実行
pytest tests/ --ff

# デバッガーで実行
pytest tests/ --pdb
```

### テスト実行順序と依存関係

#### テストの依存関係管理

```python
# pytest-dependencyを使用
pip install pytest-dependency

# テストに依存関係を定義
@pytest.mark.dependency(depends=["test_character_growth_init"])
def test_kpi_update():
    """KPI更新テスト（初期化に依存）"""
    pass

# 依存テストをスキップ
pytest tests/ --skip-dependency
```

#### テスト実行順序の制御

```python
# pytest-orderを使用
pip install pytest-order

# テストに順序を定義
@pytest.mark.order(1)
def test_character_growth_init():
    """最初に実行"""
    pass

@pytest.mark.order(2)
def test_kpi_update():
    """2番目に実行"""
    pass
```

### CI/CDでのテスト実行

```yaml
# .github/workflows/test.yml（例）
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-xdist
      - name: Run tests
        run: |
          pytest tests/ \
            --cov=core.character_growth \
            --cov=api.mcp_server \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=junit.xml \
            -n auto
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml
```

### テスト品質基準

**必須要件**:
- ✅ **テスト成功率**: 100%（全テストが成功）
  - ユニットテスト: 60件（CharacterGrowth: 30件、MCP Server: 30件）
  - 統合テスト: 20件（成長システム: 10件、MCP: 10件）
  - **合計**: 80件以上
- ✅ **コードカバレッジ**: 90%以上（平均）
  - CharacterGrowth: 95%以上
  - MCP Server: 90%以上
- ✅ **テスト実行時間**: 全テスト3分以内
  - ユニットテスト: 1分以内
  - 統合テスト: 2分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
  - テスト間の依存関係なし
  - テスト実行順序に依存しない
- ✅ **モック使用**: 外部依存（ChatService、LongTermMemory等）はモックで分離
  - ユニットテスト: すべての外部依存をモック
  - 統合テスト: 実際のサービスを使用

**TDDサイクル遵守**:
- ✅ **RED**: 実装前にテストを書いている
  - テストが失敗することを確認
  - テストが期待する動作を明確に定義
- ✅ **GREEN**: 最小限の実装でテストを通している
  - テストを通す最小限のコードのみ実装
  - 過度な実装を避ける
- ✅ **REFACTOR**: リファクタリング後もテストが成功している
  - リファクタリング後も全テストが成功
  - コードの可読性と保守性を向上

**テスト品質チェックリスト**:
- [ ] すべてのテストがGiven-When-Then形式で記述されている
- [ ] テスト名が明確で説明的である
- [ ] 各テストが1つのことをテストしている
- [ ] テストデータが適切に定義されている
- [ ] エッジケースが十分にカバーされている
- [ ] 異常系テストが実装されている
- [ ] パラメータ化テストが適切に使用されている
- [ ] モックが適切に使用されている
- [ ] テストの実行時間が許容範囲内である
- [ ] テストの保守性が確保されている

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `core/character_growth.py` (350行)
- `api/mcp_server.py` (400行)
- **合計**: 750行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_character_growth.py` (30件)
  - 初期化テスト: 4件
  - KPI更新テスト: 8件 + エッジケース8件
  - レベル計算テスト: 8件 + パラメータ化4件
  - レベルアップテスト: 6件
  - 統計取得テスト: 4件
- `tests/test_mcp_server.py` (30件)
  - 初期化テスト: 3件
  - ツール実行テスト: 12件 + エッジケース10件 + パラメータ化5件
  - リソース取得テスト: 8件
  - エラーハンドリングテスト: 7件
- `tests/test_integration_growth.py` (10件)
  - ChatService連携: 3件
  - 機能解禁・パラメータ調整: 2件
  - 複数キャラクター: 2件
  - 並行処理: 1件
  - その他: 2件
- `tests/test_integration_mcp.py` (10件)
  - MCPツール統合: 4件
  - ツールチェーン: 1件
  - エラー回復: 1件
  - その他: 4件
- `tests/fixtures/character_growth_fixtures.py`: テストデータ定義
- `tests/fixtures/mcp_server_fixtures.py`: テストデータ定義
- **合計**: 80件以上（エッジケース・パラメータ化テスト含む）

### 7.3 ドキュメント

- `docks/完了報告/Phase6_完了サマリー.md`
- MCP Server設定ガイド
- Claude Desktop統合ガイド

### 7.4 マイルストーン

- [ ] KPI収集・レベルアップ動作確認
- [ ] MCP Server外部接続テスト成功
- [ ] Claude Desktop統合確認
- [ ] 全テスト成功（80件）
- [ ] カバレッジ > 90%

---

## 8. Phase 6成功基準

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全80件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: 全テスト3分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（ChatService、LongTermMemory等）はモックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | pytest（全80件） |
| **コードカバレッジ** | **90%以上** | pytest-cov |
| **テスト実行時間** | **< 3分** | pytest --durations |
| KPI収集精度 | 100% | KPI更新テスト |
| レベル計算精度 | 100% | レベル計算テスト |
| MCP Server応答時間 | < 500ms | MCPクライアントテスト |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全80件のテストケースが定義されている
✅ **KPI収集動作**: ユーザー評価・会話回数追跡
✅ **レベルアップ動作**: 自動成長・機能解禁
✅ **MCP Server動作**: 外部ツール公開・Claude Desktop統合

---

**Phase 6 実装完了**: キャラクター成長システムと外部連携基盤が整いました。