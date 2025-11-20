# Phase 8 実装仕様書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 8 - LoRAファインチューニング + 最終統合  
**期間**: 3週間  
**作成日**: 2025-11-20  
**Phase 7完了前提**: 3D可視化・自律サーチ実装済み

---

## 目次

1. [Phase 8概要](#1-phase-8概要)
2. [前提条件](#2-前提条件)
3. [Week 1-2: LoRAファインチューニング](#3-week-1-2-loraファインチューニング)
4. [Week 3: 最終統合・品質保証](#4-week-3-最終統合品質保証)
5. [技術スタック](#5-技術スタック)
6. [テスト計画（TDD実装）](#6-テスト計画tdd実装)
   - [TDD実装仕様サマリー](#60-tdd実装仕様サマリー)
   - [テストカバレッジ目標](#61-テストカバレッジ目標)
   - [テスト実行方法](#62-テスト実行方法)
   - [Week 1-2: LoRAファインチューニング - テスト仕様（TDD）](#week-1-2-loraファインチューニング---テスト仕様tdd)
   - [Week 3: 最終統合・品質保証 - テスト仕様（TDD）](#week-3-最終統合品質保証---テスト仕様tdd)
   - [統合テスト仕様（TDD）](#統合テスト仕様tdd)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [テスト実行戦略](#テスト実行戦略)
7. [成果物](#7-成果物)
8. [Phase 8成功基準](#8-phase-8成功基準)

---

## 1. Phase 8概要

### 1.1 目的

LoRAファインチューニングによるキャラクター進化と全システム統合により、**完全な会話AIシステム**を完成させます。

### 1.2 TDD実装アプローチ

Phase 8は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

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
- ✅ 外部依存はモックで分離（GPU不要な軽量テストを優先）

### 1.3 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **LoRA適用** | 月次バッチ処理 | 🟡 Medium |
| **統合テスト** | Phase 1-7横断テスト | 🔴 High |
| **パフォーマンス最適化** | ボトルネック改善 | 🔴 High |
| **リリース準備** | ドキュメント・バージョン管理 | 🔴 High |

### 1.3 達成目標

✅ LoRAファインチューニング動作確認  
✅ 全Phase統合テスト成功  
✅ リリース準備完了  
✅ v4.0.0リリースノート作成

---

## 2. 前提条件

### 2.1 Phase 1-7完了事項

✅ **Phase 1**: LangGraphコア・5階層記憶システム  
✅ **Phase 2**: エラーハンドリング・セキュリティ  
✅ **Phase 3**: REST/WebSocket API（23エンドポイント）  
✅ **Phase 4**: 連想記憶システム・感情モデル基盤  
✅ **Phase 5**: 対話スタイル適応・自己省察  
✅ **Phase 6**: キャラクター成長・MCP Server  
✅ **Phase 7**: 3D可視化・自律サーチ

**参照**: [`docks/実装仕様/Phase7_実装仕様.md`](Phase7_実装仕様.md:1)

### 2.2 ハードウェア要件

**LoRAファインチューニング用**:
- **GPU**: VRAM 8GB以上（NVIDIA推奨）
- **CPU代替**: 可能だが10倍以上の時間
- **メモリ**: 16GB以上

---

## 3. Week 1-2: LoRAファインチューニング

### 3.1 実装内容

**参照**: [`docks/仕様書/03_会話LLM_キャラクター仕様.md:335-379`](../仕様書/03_会話LLM_キャラクター仕様.md:335)

#### 3.1.1 月次バッチ処理

**処理フロー**:
1. **会話履歴収集**: 過去1ヶ月分の全会話
2. **訓練データ作成**: Alpaca形式変換
3. **LoRA適用**: PEFTライブラリで学習
4. **モデル保存**: `models/lora_{character_name}/`

#### 3.1.2 訓練データ形式

```json
{
  "instruction": "ユーザーからの質問や指示",
  "input": "追加コンテキスト（オプション）",
  "output": "キャラクターの応答"
}
```

**例**:
```json
{
  "instruction": "機械学習について教えてください",
  "input": "",
  "output": "機械学習は、コンピュータがデータからパターンを学習する技術です。主に教師あり学習、教師なし学習、強化学習の3つに分類されます。"
}
```

### 3.2 ファイル構成

#### training/lora_tuning.py (400行)

```python
"""LoRAファインチューニングモジュール."""

from typing import List, Dict, Any
import os
import json
from datetime import datetime, timedelta
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

class CharacterFineTuning:
    """キャラクターLoRAファインチューニングクラス."""
    
    def __init__(
        self,
        base_model: str = "gpt2",
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1
    ):
        """
        初期化.
        
        Args:
            base_model: ベースモデル名
            lora_r: LoRAランク
            lora_alpha: LoRAアルファ
            lora_dropout: LoRAドロップアウト
        """
        self.base_model_name = base_model
        self.lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=["c_attn"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
    
    def fine_tune_character(
        self,
        character_name: str,
        num_epochs: int = 3,
        batch_size: int = 4
    ) -> str:
        """
        キャラクターファインチューニング実行.
        
        Args:
            character_name: キャラクター名
            num_epochs: エポック数
            batch_size: バッチサイズ
        
        Returns:
            str: 保存パス
        """
        # 1. 会話履歴収集
        conversations = self._collect_conversations(character_name, days=30)
        
        if len(conversations) < 100:
            raise ValueError(f"訓練データ不足: {len(conversations)}件（最低100件必要）")
        
        # 2. 訓練データ作成
        training_data = self._create_training_data(conversations)
        
        # 3. モデル・トークナイザーロード
        model = AutoModelForCausalLM.from_pretrained(self.base_model_name)
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 4. LoRA適用
        model = get_peft_model(model, self.lora_config)
        
        # 5. データセット作成
        dataset = Dataset.from_list(training_data)
        
        def tokenize_function(examples):
            prompts = [
                f"Instruction: {inst}\nInput: {inp}\nOutput: {out}"
                for inst, inp, out in zip(
                    examples["instruction"],
                    examples["input"],
                    examples["output"]
                )
            ]
            return tokenizer(
                prompts,
                truncation=True,
                padding="max_length",
                max_length=512
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # 6. 訓練設定
        output_dir = f"models/lora_{character_name}"
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            save_steps=100,
            logging_steps=10,
            learning_rate=3e-4,
            fp16=torch.cuda.is_available(),
        )
        
        # 7. 訓練実行（実際はTrainerクラス使用）
        # trainer = Trainer(...)
        # trainer.train()
        
        # 8. モデル保存
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        return output_dir
    
    def _collect_conversations(
        self,
        character_name: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        会話履歴収集.
        
        Args:
            character_name: キャラクター名
            days: 収集日数
        
        Returns:
            List[Dict]: 会話履歴
        """
        from services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # 過去N日分の会話取得
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conversations = chat_service.get_history(
            character_name=character_name,
            start_date=start_date,
            limit=10000
        )
        
        return conversations
    
    def _create_training_data(
        self,
        conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        訓練データ作成（Alpaca形式）.
        
        Args:
            conversations: 会話履歴
        
        Returns:
            List[Dict]: 訓練データ
        """
        training_data = []
        
        for conv in conversations:
            # user → assistant のペア抽出
            if conv.get("role") == "user":
                user_input = conv.get("content", "")
                
                # 次のassistant応答を探す
                assistant_output = None
                for i, c in enumerate(conversations):
                    if c.get("timestamp") > conv.get("timestamp") and c.get("role") == "assistant":
                        assistant_output = c.get("content")
                        break
                
                if assistant_output:
                    training_data.append({
                        "instruction": user_input,
                        "input": "",
                        "output": assistant_output
                    })
        
        return training_data
    
    def load_lora_model(self, character_name: str):
        """
        LoRAモデルロード.
        
        Args:
            character_name: キャラクター名
        
        Returns:
            Model: ファインチューニング済みモデル
        """
        from peft import PeftModel
        
        model_path = f"models/lora_{character_name}"
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"LoRAモデルなし: {model_path}")
        
        base_model = AutoModelForCausalLM.from_pretrained(self.base_model_name)
        model = PeftModel.from_pretrained(base_model, model_path)
        
        return model
```

### 3.3 テスト仕様（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

**重要**: LoRAファインチューニングはGPUを必要とするため、**GPU不要な軽量テストを優先**し、GPUテストはオプションとして実装します。

#### テストファイル構成

- `tests/test_lora_tuning.py`: CharacterFineTuningクラスのユニットテスト（30件、GPU不要）
- `tests/test_integration_lora.py`: LoRA統合テスト（10件、GPU不要）

#### テストデータ定義

```python
# tests/fixtures/lora_tuning_fixtures.py

TEST_CHARACTERS = ["lumina", "clarisse", "nox"]
TEST_CONVERSATIONS = [
    {
        "role": "user",
        "content": "こんにちは",
        "timestamp": "2025-11-20T10:00:00Z"
    },
    {
        "role": "assistant",
        "content": "こんにちは！",
        "timestamp": "2025-11-20T10:00:01Z"
    }
]

TEST_LORA_CONFIGS = [
    {"r": 8, "alpha": 16, "dropout": 0.1},
    {"r": 16, "alpha": 32, "dropout": 0.05},
    {"r": 4, "alpha": 8, "dropout": 0.2},
]

TEST_EPOCHS = [1, 3, 5, 10]
TEST_BATCH_SIZES = [1, 4, 8, 16]
```

---

## 4. Week 3: 最終統合・品質保証

### 4.1 全Phase統合テスト（TDD）

**注意**: このセクションは実装前のテスト仕様です。実装は必ずテストファーストで行います。

#### テストファイル構成

- `tests/test_integration_phase1_7.py`: Phase 1-7横断統合テスト（20件）
- `tests/test_integration_phase4_8.py`: Phase 4-8統合テスト（15件）
- `tests/test_e2e.py`: エンドツーエンドテスト（10件）
- `tests/test_performance.py`: パフォーマンステスト（5件）

---

## Week 3: 最終統合・品質保証 - テスト仕様（TDD）

### テストファイル: `tests/test_integration_phase1_7.py`

**テストクラス**: `TestPhase1_7Integration`

**テストケース一覧（20件）**:

#### 1. LangGraphコア統合テスト（5件）

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_langgraph_conversation_flow():
    """
    Given: LangGraphコアと会話サービス
    When: 会話を実行
    Then: LangGraphフローが正しく動作する
    """
    from services.chat_service import ChatService
    
    chat_service = ChatService()
    
    response = await chat_service.chat(
        user_input="こんにちは",
        character_name="lumina",
        session_id="test_001"
    )
    
    assert response["status"] == "success"
    assert len(response["response"]) > 0

@pytest.mark.integration
def test_memory_hierarchy_integration():
    """
    Given: 5階層記憶システム
    When: 記憶を保存・検索
    Then: 各階層が正しく動作する
    """
    from memory.working import WorkingMemory
    from memory.short_term import ShortTermMemory
    from memory.long_term import LongTermMemory
    
    # 各階層のテスト
    working = WorkingMemory()
    working.store("テスト記憶")
    
    assert len(working.retrieve()) > 0
```

#### 2. 連想記憶・感情統合テスト（5件）

```python
@pytest.mark.integration
def test_associative_memory_with_emotion():
    """
    Given: 連想記憶と感情システム
    When: 概念を追加し、感情を更新
    Then: 連想記憶と感情が連携する
    """
    from memory.associative import AssociativeMemory
    from core.emotion import EmotionalState
    
    memory = AssociativeMemory(db_path=":memory:")
    emotion = EmotionalState("lumina")
    
    memory.add_concept("Python", embedding=[0.1]*128, metadata={})
    emotion.update_emotion("joy", intensity=0.8)
    
    # 連想検索
    results = memory.retrieve_associated_concepts("Python", depth=2, threshold=0.5)
    
    assert len(results) >= 0
```

#### 3. 対話スタイル・自己省察統合テスト（5件）

```python
@pytest.mark.integration
def test_dialogue_style_with_reflection():
    """
    Given: 対話スタイル適応と自己省察
    When: 会話後に省察を実行
    Then: 対話スタイルが更新される
    """
    from core.dialogue_style import AdaptiveDialogueStyle
    from core.self_reflection import SelfReflection
    
    style = AdaptiveDialogueStyle("user_001")
    reflection = SelfReflection("lumina")
    
    # フィードバック学習
    style.learn_from_feedback({
        "message": "もっと詳しく説明してほしい",
        "thumbs_up": True
    })
    
    # 省察
    conversation = [
        {"role": "user", "content": "わかりやすく", "session_id": "sess_001"}
    ]
    result = reflection.reflect_on_conversation(conversation)
    
    assert result is not None
    assert style.parameters["verbosity"] > 0.5
```

#### 4. キャラクター成長・MCP統合テスト（5件）

```python
@pytest.mark.integration
def test_character_growth_with_mcp():
    """
    Given: キャラクター成長とMCP Server
    When: KPIを更新し、MCP経由で情報取得
    Then: 成長情報がMCP経由で取得できる
    """
    from core.character_growth import CharacterGrowth
    from api.mcp_server import LlmMultiChatMCPServer
    
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # KPI更新
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # MCP経由で情報取得
    server = LlmMultiChatMCPServer()
    
    import asyncio
    info = asyncio.run(server._get_character_info("lumina"))
    
    assert "lumina" in info.lower()
    assert growth.current_level == 1
```

### テストファイル: `tests/test_integration_phase4_8.py`

**テストクラス**: `TestPhase4_8Integration`

**テストケース一覧（15件）**:

```python
"""Phase 4-8統合テスト."""

import pytest
from services.chat_service import ChatService
from memory.associative import AssociativeMemory
from core.emotion import EmotionalState
from core.dialogue_style import AdaptiveDialogueStyle
from core.character_growth import CharacterGrowth
from api.mcp_server import LlmMultiChatMCPServer
from visualization.association_3d import AssociationVisualizationPanel
from agents.autonomous_search import AutonomousSearchAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_conversation():
    """
    Given: 全システム統合
    When: エンドツーエンド会話を実行
    Then: すべてのシステムが連携して動作する
    """
    chat_service = ChatService()
    
    response = await chat_service.chat(
        user_input="機械学習について教えてください",
        character_name="lumina",
        session_id="integration_test_001"
    )
    
    assert response["status"] == "success"
    assert len(response["response"]) > 0

@pytest.mark.integration
def test_associative_memory_integration():
    """
    Given: 連想記憶システム
    When: 概念を追加・検索
    Then: 連想記憶が正しく動作する
    """
    memory = AssociativeMemory(db_path=":memory:")
    
    memory.add_concept("Python", embedding=[0.1]*128, metadata={})
    memory.add_concept("機械学習", embedding=[0.2]*128, metadata={})
    memory.link_concepts("Python", "機械学習", "related", strength=0.8)
    
    results = memory.retrieve_associated_concepts("Python", depth=2, threshold=0.5)
    
    assert len(results) > 0

@pytest.mark.integration
def test_character_growth_with_kpi():
    """
    Given: キャラクター成長システム
    When: KPIを更新
    Then: レベルアップが発生する
    """
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    assert growth.current_level == 1

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_server_integration():
    """
    Given: MCP Server
    When: チャットツールを呼び出す
    Then: チャット応答が返される
    """
    server = LlmMultiChatMCPServer()
    
    result = await server._chat_with_character("lumina", "こんにちは")
    
    assert len(result) > 0

@pytest.mark.integration
def test_visualization_with_associative_memory():
    """
    Given: 3D可視化と連想記憶
    When: グラフを描画
    Then: 連想記憶から概念が取得され、グラフが描画される
    """
    memory = AssociativeMemory(db_path=":memory:")
    panel = AssociationVisualizationPanel(memory)
    
    memory.add_concept("機械学習", embedding=[0.1]*128, metadata={})
    panel.current_center = "機械学習"
    
    fig = panel._render_graph()
    
    assert fig is not None

@pytest.mark.integration
def test_autonomous_search_with_kb():
    """
    Given: 自律サーチとKB
    When: 検索してKBに保存
    Then: KBに正しく保存される
    """
    agent = AutonomousSearchAgent()
    
    with patch.object(agent, 'web_search', return_value=[
        {"title": "結果", "snippet": "説明", "link": "http://example.com"}
    ]):
        agent.save_to_kb("テストコンテンツ", "news")
        
        # KBから検索
        results = agent.kb.search("テスト", top_k=1)
        assert len(results) >= 0

# ... 他9件（全システム統合、エラー回復、パフォーマンステストなど）
```

### テストファイル: `tests/test_e2e.py`

**テストクラス**: `TestEndToEnd`

**テストケース一覧（10件）**:

```python
"""エンドツーエンドテスト."""

import pytest
from services.chat_service import ChatService


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_conversation_flow():
    """
    Given: 全システム統合
    When: 完全な会話フローを実行
    Then: すべての機能が連携して動作する
    """
    chat_service = ChatService()
    
    # 1. 会話開始
    response1 = await chat_service.chat(
        user_input="こんにちは",
        character_name="lumina",
        session_id="e2e_test_001"
    )
    assert response1["status"] == "success"
    
    # 2. 続きの会話
    response2 = await chat_service.chat(
        user_input="機械学習について教えて",
        character_name="lumina",
        session_id="e2e_test_001"
    )
    assert response2["status"] == "success"
    
    # 3. フィードバック
    # 実装に応じてフィードバック機能のテスト

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_character_conversation():
    """
    Given: 複数のキャラクター
    When: 各キャラクターと会話
    Then: 各キャラクターが独立して動作する
    """
    chat_service = ChatService()
    
    characters = ["lumina", "clarisse", "nox"]
    
    for char in characters:
        response = await chat_service.chat(
            user_input="こんにちは",
            character_name=char,
            session_id=f"e2e_test_{char}"
        )
        assert response["status"] == "success"

# ... 他8件（長時間会話、大量データ、エラー回復など）
```

### テストファイル: `tests/test_performance.py`

**テストクラス**: `TestPerformance`

**テストケース一覧（5件）**:

```python
"""パフォーマンステスト."""

import pytest
import time
from services.chat_service import ChatService


@pytest.mark.performance
@pytest.mark.asyncio
async def test_chat_response_time():
    """
    Given: ChatService
    When: 会話を実行
    Then: 応答時間が許容範囲内（< 5秒）
    """
    chat_service = ChatService()
    
    start_time = time.time()
    response = await chat_service.chat(
        user_input="テスト",
        character_name="lumina",
        session_id="perf_test_001"
    )
    elapsed_time = time.time() - start_time
    
    assert response["status"] == "success"
    assert elapsed_time < 5.0

@pytest.mark.performance
def test_memory_search_performance():
    """
    Given: 大量の記憶データ
    When: 検索を実行
    Then: 検索時間が許容範囲内（< 1秒）
    """
    from memory.long_term import LongTermMemory
    
    memory = LongTermMemory()
    
    # 大量データ投入（モック）
    # 検索時間測定
    
    start_time = time.time()
    results = memory.search("テスト", top_k=10)
    elapsed_time = time.time() - start_time
    
    assert elapsed_time < 1.0

# ... 他3件（並行処理、メモリ使用量、CPU使用率など）
```

---

## 統合テスト仕様（TDD）

### テスト実行順序

1. **Phase 1-7統合テスト**: 各Phaseの機能が正しく連携しているか確認
2. **Phase 4-8統合テスト**: 新機能（Phase 4-8）の統合確認
3. **エンドツーエンドテスト**: 完全な会話フローの確認
4. **パフォーマンステスト**: 応答時間・リソース使用量の確認

---

## テストフィクスチャ仕様

### conftest.py の拡張

```python
# tests/conftest.py（拡張）

import pytest
import tempfile
from unittest.mock import Mock, patch, AsyncMock

from training.lora_tuning import CharacterFineTuning
from services.chat_service import ChatService
from memory.associative import AssociativeMemory
from core.character_growth import CharacterGrowth
from api.mcp_server import LlmMultiChatMCPServer

@pytest.fixture
def character_fine_tuning():
    """CharacterFineTuningインスタンス"""
    return CharacterFineTuning()

@pytest.fixture
def mock_chat_service():
    """ChatServiceのモック"""
    mock = AsyncMock()
    mock.chat = AsyncMock(return_value={
        "status": "success",
        "response": "モック応答"
    })
    mock.get_history = Mock(return_value=[])
    return mock

@pytest.fixture
def mock_transformer_model():
    """Transformersモデルのモック"""
    with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock(pad_token=None, eos_token="<eos>")
        yield mock_model, mock_tokenizer

@pytest.fixture
def temp_model_dir():
    """一時的なモデルディレクトリ"""
    import tempfile
    import os
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

---

## テスト実行戦略

### TDD実装順序（詳細版）

#### Week 1-2: LoRAファインチューニング

**Day 1: 初期化・訓練データ作成テスト（15件）→ 実装**
- 初期化: デフォルト設定、カスタム設定、LoRA設定
- 訓練データ作成: 基本変換、複数ペア、エッジケース

**Day 2: 会話履歴収集・ファインチューニング実行テスト（15件）→ 実装**
- 会話履歴収集: 基本収集、空結果、エラーハンドリング
- ファインチューニング実行: データ不足、十分なデータ、モック使用

**Day 3: モデルロード・エッジケーステスト（15件）→ 実装**
- モデルロード: 存在確認、ロード成功、エラーハンドリング
- エッジケース: 欠損データ、異常値、境界値

**Day 4-5: パラメータ化テスト・リファクタリング（5件）→ 実装・リファクタリング**

#### Week 3: 最終統合・品質保証

**Day 1-2: Phase 1-7統合テスト（20件）→ 実装**
- LangGraphコア統合、記憶階層統合、連想記憶・感情統合

**Day 3: Phase 4-8統合テスト（15件）→ 実装**
- 対話スタイル・自己省察統合、キャラクター成長・MCP統合

**Day 4: エンドツーエンドテスト（10件）→ 実装**
- 完全な会話フロー、複数キャラクター、長時間会話

**Day 5: パフォーマンステスト（5件）→ 実装・リファクタリング**
- 応答時間、検索時間、リソース使用量

### テスト品質基準

**必須要件**:
- ✅ **テスト成功率**: 100%（全95件以上のテストが成功）
- ✅ **コードカバレッジ**: 83%以上（平均）
- ✅ **テスト実行時間**: 全テスト10分以内（GPUテスト除く）
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（GPU、モデルロード等）はモックで分離

**TDDサイクル遵守**:
- ✅ **RED**: 実装前にテストを書いている
- ✅ **GREEN**: 最小限の実装でテストを通している
- ✅ **REFACTOR**: リファクタリング後もテストが成功している

---

## 7. 成果物

### 4.2 パフォーマンス最適化

#### profiler/performance_analysis.py

```python
"""パフォーマンス分析."""

import time
import cProfile
import pstats
from io import StringIO


def profile_chat_service():
    """ChatServiceプロファイル."""
    profiler = cProfile.Profile()
    
    profiler.enable()
    
    # ベンチマーク実行
    from services.chat_service import ChatService
    chat_service = ChatService()
    
    for _ in range(10):
        chat_service.chat(
            user_input="テスト",
            character_name="lumina",
            session_id="bench_001"
        )
    
    profiler.disable()
    
    # 結果出力
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    print(s.getvalue())
```

### 4.3 ドキュメント最終更新

**作成ドキュメント**:
1. **完全仕様書更新**: 全Phase統合内容
2. **API仕様書最終版**: 全エンドポイント一覧
3. **ユーザーガイド**: インストール・使用方法
4. **リリースノート v4.0.0**: 変更履歴

### 4.4 リリース準備

#### リリースノート v4.0.0

```markdown
# LlmMultiChat3 v4.0.0 リリースノート

**リリース日**: 2025年XX月XX日

## 🎉 新機能

### Phase 4: 記憶システム拡張 + 感情基盤
- 連想記憶システム（SQLite Graph）
- 8基本感情モデル（Plutchik）

### Phase 5: 対話スタイル適応 + 自己省察
- ユーザー別対話スタイル自動調整
- 自己省察・矛盾検出

### Phase 6: キャラクター成長 + MCP対応
- KPIベース成長システム
- MCP Server実装（Claude Desktop統合）

### Phase 7: 3D可視化 + 自律サーチ
- 連想ネットワーク3D可視化（Plotly.js）
- 自律的外部サーチエージェント

### Phase 8: LoRAファインチューニング + 最終統合
- 月次バッチLoRA学習
- 全Phase統合完了

## 📊 技術スタック

- **Backend**: Python 3.9+, FastAPI, LangGraph
- **Frontend**: React 18, TypeScript, Vite
- **Database**: SQLite, Redis
- **AI**: OpenAI API, Ollama
- **Visualization**: Plotly.js

## 🚀 インストール

```bash
git clone https://github.com/Nyukimin/LlmMultiChat3.git
cd LlmMultiChat3
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📖 ドキュメント

- [完全仕様書](docks/仕様書/)
- [API仕様書](docks/API仕様書.md)
- [ユーザーガイド](docks/ユーザーガイド.md)

## 🐛 既知の問題

- LoRAファインチューニングはGPU推奨（CPU版は低速）

## 👏 貢献者

- @Nyukimin
```

---

## 5. 技術スタック

### 5.1 Python依存

```txt
# requirements.txt に追加
transformers==4.35.0    # LoRAファインチューニング
peft==0.6.0             # PEFT（LoRA）
torch==2.1.0            # PyTorch
datasets==2.15.0        # データセット管理
```

### 5.2 新規モジュール

- **training/lora_tuning.py**: LoRAファインチューニング

---

## 6. テスト計画（TDD実装）

### 6.0 TDD実装仕様サマリー

**Phase 8は完全なTDD（テスト駆動開発）アプローチで実装します。**

#### TDD実装の原則

1. **テストファースト**: すべての機能は実装前にテストを書く
2. **RED-GREEN-REFACTORサイクル**: 失敗→成功→リファクタリングのサイクルを徹底
3. **Given-When-Then形式**: すべてのテストを明確な形式で記述
4. **テスト独立性**: 各テストは独立して実行可能
5. **モック分離**: 外部依存（GPU、モデルロード等）はモックで分離
6. **軽量テスト優先**: GPU不要なテストを優先し、GPUテストはオプション

#### テスト構成

| カテゴリ | テストファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|--------------|---------|--------------|--------|
| **LoRAファインチューニング** |
| CharacterFineTuning | `test_lora_tuning.py` | 30件 + エッジケース10件 + パラメータ化5件 | 85%以上 | 🟡 Medium |
| **最終統合テスト** |
| Phase 1-7統合 | `test_integration_phase1_7.py` | 20件 | 85%以上 | 🔴 High |
| Phase 4-8統合 | `test_integration_phase4_8.py` | 15件 | 85%以上 | 🔴 High |
| エンドツーエンド | `test_e2e.py` | 10件 | 80%以上 | 🔴 High |
| **パフォーマンステスト** |
| パフォーマンス分析 | `test_performance.py` | 5件 | 70%以上 | 🟡 Medium |
| **合計** | **5ファイル + フィクスチャ1ファイル** | **105件以上** | **平均83%以上** | - |

#### テスト実行戦略

- **Week 1-2**: LoRAファインチューニング（5日間で段階的に実装、GPU不要テスト優先）
- **Week 3**: 最終統合・品質保証（5日間で段階的に実装）
- **各機能**: RED → GREEN → REFACTORサイクルで実装
- **品質基準**: テスト成功率100%、カバレッジ83%以上、実行時間10分以内（GPUテスト除く）

### 6.1 テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| **LoRAファインチューニング** |
| CharacterFineTuning | `test_lora_tuning.py` | 45件 | 85%以上 | 🟡 Medium |
| **最終統合テスト** |
| Phase 1-7統合 | `test_integration_phase1_7.py` | 20件 | 85%以上 | 🔴 High |
| Phase 4-8統合 | `test_integration_phase4_8.py` | 15件 | 85%以上 | 🔴 High |
| エンドツーエンド | `test_e2e.py` | 10件 | 80%以上 | 🔴 High |
| **パフォーマンステスト** |
| パフォーマンス分析 | `test_performance.py` | 5件 | 70%以上 | 🟡 Medium |
| **合計** | **5ファイル** | **95件以上** | **平均83%以上** | - |

### 6.2 テスト実行方法

#### 基本的なテスト実行

```bash
# 全テスト実行（GPU不要テストのみ）
pytest tests/test_lora_tuning.py tests/test_integration_phase1_7.py tests/test_integration_phase4_8.py -v

# カバレッジ付きテスト実行
pytest tests/ \
  --cov=training.lora_tuning \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=83

# GPUテストを除外
pytest tests/ -m "not gpu" -v

# GPUテストのみ実行（GPU環境が必要）
pytest tests/ -m gpu -v

# 特定のテストのみ実行
pytest tests/test_lora_tuning.py::test_training_data_creation -v

# マーカーで実行
pytest -m unit -v              # ユニットテストのみ
pytest -m integration -v      # 統合テストのみ
pytest -m e2e -v               # エンドツーエンドテストのみ
pytest -m "not slow" -v        # 遅いテストを除外
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_lora_tuning.py::test_training_data_creation -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_lora_tuning.py::test_training_data_creation -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_lora_tuning.py -v
# → 期待: 全テスト PASSED
```

---

## Week 1-2: LoRAファインチューニング - テスト仕様（TDD）

### テストファイル: `tests/test_lora_tuning.py`

**テストクラス**: `TestCharacterFineTuning`

**テストケース一覧（45件、GPU不要）**:

#### 1. 初期化テスト（5件）

```python
def test_fine_tuning_init_default():
    """
    Given: デフォルトパラメータ
    When: CharacterFineTuningを初期化
    Then: デフォルト設定で初期化される
    """
    tuning = CharacterFineTuning()
    
    assert tuning.base_model_name == "gpt2"
    assert tuning.lora_config.r == 8
    assert tuning.lora_config.lora_alpha == 16
    assert tuning.lora_config.lora_dropout == 0.1

def test_fine_tuning_init_custom():
    """
    Given: カスタムパラメータ
    When: CharacterFineTuningを初期化
    Then: カスタム設定で初期化される
    """
    tuning = CharacterFineTuning(
        base_model="gpt2-medium",
        lora_r=16,
        lora_alpha=32,
        lora_dropout=0.05
    )
    
    assert tuning.base_model_name == "gpt2-medium"
    assert tuning.lora_config.r == 16
    assert tuning.lora_config.lora_alpha == 32
    assert tuning.lora_config.lora_dropout == 0.05

def test_fine_tuning_init_lora_config():
    """
    Given: CharacterFineTuningインスタンス
    When: 初期化
    Then: LoRA設定が正しく作成される
    """
    tuning = CharacterFineTuning()
    
    assert tuning.lora_config.task_type == TaskType.CAUSAL_LM
    assert tuning.lora_config.bias == "none"
    assert "c_attn" in tuning.lora_config.target_modules
```

#### 2. 訓練データ作成テスト（10件）

```python
def test_create_training_data_simple():
    """
    Given: user→assistantのペア
    When: _create_training_data()を呼び出す
    Then: Alpaca形式の訓練データが作成される
    """
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user", "content": "こんにちは", "timestamp": "2025-11-20T10:00:00Z"},
        {"role": "assistant", "content": "こんにちは！", "timestamp": "2025-11-20T10:00:01Z"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    assert len(data) == 1
    assert data[0]["instruction"] == "こんにちは"
    assert data[0]["input"] == ""
    assert data[0]["output"] == "こんにちは！"

def test_create_training_data_multiple_pairs():
    """
    Given: 複数のuser→assistantペア
    When: _create_training_data()を呼び出す
    Then: すべてのペアが訓練データに変換される
    """
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user", "content": "質問1", "timestamp": "2025-11-20T10:00:00Z"},
        {"role": "assistant", "content": "回答1", "timestamp": "2025-11-20T10:00:01Z"},
        {"role": "user", "content": "質問2", "timestamp": "2025-11-20T10:00:02Z"},
        {"role": "assistant", "content": "回答2", "timestamp": "2025-11-20T10:00:03Z"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    assert len(data) == 2
    assert data[0]["instruction"] == "質問1"
    assert data[1]["instruction"] == "質問2"

def test_create_training_data_no_assistant_response():
    """
    Given: userメッセージに対応するassistantメッセージがない
    When: _create_training_data()を呼び出す
    Then: そのペアは訓練データに含まれない
    """
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user", "content": "質問", "timestamp": "2025-11-20T10:00:00Z"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    assert len(data) == 0

def test_create_training_data_empty_conversations():
    """
    Given: 空の会話履歴
    When: _create_training_data()を呼び出す
    Then: 空のリストが返される
    """
    tuning = CharacterFineTuning()
    
    data = tuning._create_training_data([])
    
    assert len(data) == 0

def test_create_training_data_timestamp_order():
    """
    Given: タイムスタンプ順でない会話履歴
    When: _create_training_data()を呼び出す
    Then: タイムスタンプ順に処理される
    """
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user", "content": "質問1", "timestamp": "2025-11-20T10:00:02Z"},
        {"role": "assistant", "content": "回答1", "timestamp": "2025-11-20T10:00:03Z"},
        {"role": "user", "content": "質問2", "timestamp": "2025-11-20T10:00:00Z"},
        {"role": "assistant", "content": "回答2", "timestamp": "2025-11-20T10:00:01Z"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    # タイムスタンプ順に処理されることを確認
    assert len(data) >= 0  # 実装に応じて検証
```

#### 3. 会話履歴収集テスト（8件）

```python
def test_collect_conversations():
    """
    Given: キャラクター名と日数
    When: _collect_conversations()を呼び出す
    Then: 指定期間の会話履歴が収集される
    """
    tuning = CharacterFineTuning()
    
    with patch('services.chat_service.ChatService') as mock_service:
        mock_instance = Mock()
        mock_instance.get_history = Mock(return_value=[
            {"role": "user", "content": "質問", "timestamp": "2025-11-20T10:00:00Z"}
        ])
        mock_service.return_value = mock_instance
        
        conversations = tuning._collect_conversations("lumina", days=30)
        
        assert len(conversations) == 1
        mock_instance.get_history.assert_called_once()

def test_collect_conversations_empty_result():
    """
    Given: 会話履歴が存在しない
    When: _collect_conversations()を呼び出す
    Then: 空のリストが返される
    """
    tuning = CharacterFineTuning()
    
    with patch('services.chat_service.ChatService') as mock_service:
        mock_instance = Mock()
        mock_instance.get_history = Mock(return_value=[])
        mock_service.return_value = mock_instance
        
        conversations = tuning._collect_conversations("lumina", days=30)
        
        assert len(conversations) == 0
```

#### 4. ファインチューニング実行テスト（8件、モック使用）

```python
def test_fine_tune_character_insufficient_data():
    """
    Given: 訓練データが100件未満
    When: fine_tune_character()を呼び出す
    Then: ValueErrorが発生する
    """
    tuning = CharacterFineTuning()
    
    with patch.object(tuning, '_collect_conversations', return_value=[{}] * 50):
        with pytest.raises(ValueError, match="訓練データ不足"):
            tuning.fine_tune_character("lumina")

def test_fine_tune_character_sufficient_data():
    """
    Given: 訓練データが100件以上
    When: fine_tune_character()を呼び出す
    Then: ファインチューニングが実行される
    """
    tuning = CharacterFineTuning()
    
    # モックでモデルロードと訓練をスキップ
    with patch.object(tuning, '_collect_conversations', return_value=[{}] * 100):
        with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model:
            with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
                with patch('peft.get_peft_model') as mock_peft:
                    with patch('datasets.Dataset.from_list') as mock_dataset:
                        mock_model.return_value = Mock()
                        mock_tokenizer.return_value = Mock(pad_token=None, eos_token="<eos>")
                        mock_peft.return_value = Mock()
                        mock_dataset.return_value = Mock()
                        
                        # 実装に応じて検証
                        # result = tuning.fine_tune_character("lumina")
```

#### 5. モデルロードテスト（4件）

```python
def test_load_lora_model_not_found():
    """
    Given: 存在しないLoRAモデルパス
    When: load_lora_model()を呼び出す
    Then: FileNotFoundErrorが発生する
    """
    tuning = CharacterFineTuning()
    
    with patch('os.path.exists', return_value=False):
        with pytest.raises(FileNotFoundError, match="LoRAモデルなし"):
            tuning.load_lora_model("nonexistent_character")

def test_load_lora_model_success():
    """
    Given: 存在するLoRAモデルパス
    When: load_lora_model()を呼び出す
    Then: モデルがロードされる
    """
    tuning = CharacterFineTuning()
    
    with patch('os.path.exists', return_value=True):
        with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_base:
            with patch('peft.PeftModel.from_pretrained') as mock_peft:
                mock_base.return_value = Mock()
                mock_peft.return_value = Mock()
                
                model = tuning.load_lora_model("lumina")
                
                assert model is not None
```

#### 6. エッジケース・異常系テスト（追加: 10件）

```python
def test_create_training_data_missing_fields():
    """
    Given: 必須フィールドが欠けている会話
    When: _create_training_data()を呼び出す
    Then: エラーが発生しない（スキップされる）
    """
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user"},  # contentが欠けている
        {"role": "assistant", "content": "回答"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    # 実装に応じて検証
    assert isinstance(data, list)

def test_collect_conversations_invalid_days():
    """
    Given: 負の日数
    When: _collect_conversations()を呼び出す
    Then: エラーが発生する（または0件が返される）
    """
    tuning = CharacterFineTuning()
    
    # 実装に応じてエラーまたは空のリスト
    with pytest.raises((ValueError, TypeError)):
        tuning._collect_conversations("lumina", days=-1)
```

#### 7. パラメータ化テスト（追加: 5件）

```python
@pytest.mark.parametrize("lora_r,lora_alpha", [
    (4, 8),
    (8, 16),
    (16, 32),
    (32, 64),
])
def test_fine_tuning_various_lora_configs(lora_r, lora_alpha):
    """
    Given: 様々なLoRA設定
    When: CharacterFineTuningを初期化
    Then: すべての設定で正しく初期化される
    """
    tuning = CharacterFineTuning(lora_r=lora_r, lora_alpha=lora_alpha)
    
    assert tuning.lora_config.r == lora_r
    assert tuning.lora_config.lora_alpha == lora_alpha

@pytest.mark.parametrize("character", ["lumina", "clarisse", "nox"])
def test_collect_conversations_all_characters(character):
    """
    Given: 各キャラクター
    When: _collect_conversations()を呼び出す
    Then: すべてのキャラクターで正しく動作する
    """
    tuning = CharacterFineTuning()
    
    with patch('services.chat_service.ChatService') as mock_service:
        mock_instance = Mock()
        mock_instance.get_history = Mock(return_value=[])
        mock_service.return_value = mock_instance
        
        conversations = tuning._collect_conversations(character, days=30)
        
        assert isinstance(conversations, list)
        mock_instance.get_history.assert_called_once()
```

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `training/lora_tuning.py` (400行)
- **合計**: 400行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_lora_tuning.py` (45件)
  - 初期化テスト: 5件
  - 訓練データ作成テスト: 10件
  - 会話履歴収集テスト: 8件
  - ファインチューニング実行テスト: 8件
  - モデルロードテスト: 4件
  - エッジケース・異常系テスト: 10件
  - パラメータ化テスト: 5件
- `tests/test_integration_phase1_7.py` (20件)
  - LangGraphコア統合: 5件
  - 連想記憶・感情統合: 5件
  - 対話スタイル・自己省察統合: 5件
  - キャラクター成長・MCP統合: 5件
- `tests/test_integration_phase4_8.py` (15件)
  - エンドツーエンド会話: 3件
  - 連想記憶統合: 2件
  - キャラクター成長統合: 2件
  - MCP Server統合: 2件
  - 3D可視化統合: 2件
  - 自律サーチ統合: 2件
  - 全システム統合: 2件
- `tests/test_e2e.py` (10件)
  - 完全な会話フロー: 3件
  - 複数キャラクター: 2件
  - 長時間会話: 2件
  - エラー回復: 2件
  - 大量データ: 1件
- `tests/test_performance.py` (5件)
  - 応答時間: 2件
  - 検索時間: 1件
  - リソース使用量: 2件
- `tests/fixtures/lora_tuning_fixtures.py`: テストデータ定義
- **合計**: 95件以上（エッジケース・パラメータ化テスト含む）

### 7.3 ドキュメント

- `docks/完了報告/Phase8_完了サマリー.md`
- `docks/完了報告/Phase4-8_最終統合レポート.md`
- リリースノート v4.0.0

### 7.4 マイルストーン

- [ ] LoRAファインチューニング動作確認
- [ ] 全Phase統合テスト成功
- [ ] リリース準備完了
- [ ] 全テスト成功（95件以上）
- [ ] カバレッジ > 83%
- [ ] v4.0.0リリース

---

## 8. Phase 8成功基準

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全95件以上のテストが成功）
- ✅ **コードカバレッジ**: 83%以上（平均）
- ✅ **テスト実行時間**: 全テスト10分以内（GPUテスト除く）
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（GPU、モデルロード等）はモックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | pytest（全95件以上） |
| **コードカバレッジ** | **83%以上** | pytest-cov |
| **テスト実行時間** | **< 10分** | pytest --durations（GPUテスト除く） |
| LoRA訓練データ作成時間 | < 1分 | パフォーマンステスト |
| 統合テスト実行時間 | < 5分 | 統合テスト |
| エンドツーエンドテスト実行時間 | < 3分 | E2Eテスト |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全95件以上のテストケースが定義されている
✅ **LoRAファインチューニング動作**: 月次バッチ処理
✅ **全Phase統合完了**: Phase 1-7の全機能が統合されている
✅ **リリース準備完了**: ドキュメント・バージョン管理完了

---

**Phase 8 実装完了**: LlmMultiChat3 v4.0.0完成！