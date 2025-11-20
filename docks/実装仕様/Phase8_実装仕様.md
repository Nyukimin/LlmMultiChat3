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
6. [テスト計画](#6-テスト計画)
7. [成果物](#7-成果物)

---

## 1. Phase 8概要

### 1.1 目的

LoRAファインチューニングによるキャラクター進化と全システム統合により、**完全な会話AIシステム**を完成させます。

### 1.2 主要機能

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

### 3.3 テスト（8件 - GPU不要な軽量テスト）

#### tests/test_lora_tuning.py

```python
"""LoRAファインチューニングのテスト（軽量版）."""

import pytest
from training.lora_tuning import CharacterFineTuning


def test_training_data_creation():
    """訓練データ作成テスト."""
    tuning = CharacterFineTuning()
    
    conversations = [
        {"role": "user", "content": "こんにちは", "timestamp": "2025-11-20T10:00:00Z"},
        {"role": "assistant", "content": "こんにちは！", "timestamp": "2025-11-20T10:00:01Z"}
    ]
    
    data = tuning._create_training_data(conversations)
    
    assert len(data) == 1
    assert data[0]["instruction"] == "こんにちは"
    assert data[0]["output"] == "こんにちは！"


def test_lora_config():
    """LoRA設定テスト."""
    tuning = CharacterFineTuning(lora_r=8, lora_alpha=16)
    
    assert tuning.lora_config.r == 8
    assert tuning.lora_config.lora_alpha == 16


@pytest.mark.skipif(not pytest.config.getoption("--run-gpu"), reason="GPU test")
def test_model_save_load():
    """モデル保存・ロードテスト（GPU必要）."""
    # GPUテスト環境でのみ実行
    pass


# ... 他5件（軽量テストのみ）
```

---

## 4. Week 3: 最終統合・品質保証

### 4.1 全Phase統合テスト

#### tests/test_integration_phase4_8.py

```python
"""Phase 4-8統合テスト."""

import pytest
from services.chat_service import ChatService
from memory.associative import AssociativeMemory
from core.emotion import EmotionalState
from core.dialogue_style import AdaptiveDialogueStyle
from core.character_growth import CharacterGrowth
from api.mcp_server import LlmMultiChatMCPServer


@pytest.mark.asyncio
async def test_end_to_end_conversation():
    """エンドツーエンド会話テスト."""
    chat_service = ChatService()
    
    # 会話実行
    response = await chat_service.chat(
        user_input="機械学習について教えてください",
        character_name="lumina",
        session_id="integration_test_001"
    )
    
    assert response["status"] == "success"
    assert len(response["response"]) > 0


def test_associative_memory_integration():
    """連想記憶統合テスト."""
    memory = AssociativeMemory(db_path=":memory:")
    
    # 概念追加
    memory.add_concept("Python", embedding=[0.1]*128, metadata={})
    memory.add_concept("機械学習", embedding=[0.2]*128, metadata={})
    memory.link_concepts("Python", "機械学習", "related", strength=0.8)
    
    # 連想検索
    results = memory.retrieve_associated_concepts("Python", depth=2, threshold=0.5)
    
    assert len(results) > 0


def test_character_growth_with_kpi():
    """キャラクター成長KPI統合テスト."""
    growth = CharacterGrowth("lumina", db_path=":memory:")
    
    # KPI更新
    for _ in range(10):
        growth.update_kpi("user_thumbs_up", value=1)
    
    # レベル確認
    assert growth.current_level == 1


@pytest.mark.asyncio
async def test_mcp_server_integration():
    """MCP Server統合テスト."""
    server = LlmMultiChatMCPServer()
    
    result = await server._chat_with_character("lumina", "こんにちは")
    
    assert len(result) > 0


# ... 他統合テスト
```

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

## 6. テスト計画

### 6.1 テスト構成

| テストファイル | テスト件数 | カバレッジ目標 |
|---------------|-----------|---------------|
| `tests/test_lora_tuning.py` | 8件 | > 70% |
| `tests/test_integration_phase4_8.py` | 10件 | > 80% |
| **合計** | **18件** | **> 75%** |

### 6.2 実行方法

```bash
# 軽量テスト実行
pytest tests/test_lora_tuning.py -v

# 統合テスト実行
pytest tests/test_integration_phase4_8.py -v

# LoRAファインチューニング実行（GPU推奨）
python -m training.lora_tuning --character lumina --epochs 3
```

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `training/lora_tuning.py` (400行)
- **合計**: 400行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_lora_tuning.py` (8件)
- `tests/test_integration_phase4_8.py` (10件)
- **合計**: 18件

### 7.3 ドキュメント

- `docks/完了報告/Phase8_完了サマリー.md`
- `docks/完了報告/Phase4-8_最終統合レポート.md`
- リリースノート v4.0.0

### 7.4 マイルストーン

- [ ] LoRAファインチューニング動作確認
- [ ] 全Phase統合テスト成功
- [ ] リリース準備完了
- [ ] 全テスト成功（18件）
- [ ] v4.0.0リリース

---

**Phase 8 実装完了**: LlmMultiChat3 v4.0.0完成！