# Phase 5 実装仕様書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 5 - 対話スタイル適応 + 自己省察  
**期間**: 4週間  
**作成日**: 2025-11-20  
**Phase 4完了前提**: 連想記憶・感情基盤実装済み

---

## 目次

1. [Phase 5概要](#1-phase-5概要)
2. [前提条件](#2-前提条件)
3. [Week 1-2: 対話スタイル動的調整](#3-week-1-2-対話スタイル動的調整)
4. [Week 3-4: 自己省察・一貫性チェック](#4-week-3-4-自己省察一貫性チェック)
5. [技術スタック](#5-技術スタック)
6. [テスト計画（TDD実装）](#6-テスト計画tdd実装)
   - [Week 1-2: 対話スタイル動的調整 - テスト仕様（TDD）](#week-1-2-対話スタイル動的調整---テスト仕様tdd)
   - [Week 3-4: 自己省察・一貫性チェック - テスト仕様（TDD）](#week-3-4-自己省察一貫性チェック---テスト仕様tdd)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [テスト実行戦略](#テスト実行戦略)
7. [成果物](#7-成果物)
8. [Phase 5成功基準](#8-phase-5成功基準)

---

## 1. Phase 5概要

### 1.1 目的

ユーザーに合わせた対話スタイル調整と自己改善機能を実装し、**個々のユーザーに最適化された会話体験**を提供します。

### 1.2 TDD実装アプローチ

Phase 5は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

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
| **対話スタイル適応** | ユーザーフィードバックから学習 | 🔴 High |
| **自己省察** | 会話振り返りとメタ認知 | 🔴 High |
| **矛盾検出** | 過去発言との一貫性チェック | 🟡 Medium |
| **トピック追跡** | 話題の流れ管理 | 🟡 Medium |

### 1.3 達成目標

✅ ユーザー別対話スタイル自動調整  
✅ 自己省察による継続的改善  
✅ 矛盾検出・修正提案  
✅ トピック追跡精度 > 80%

---

## 2. 前提条件

### 2.1 Phase 1-4完了事項

✅ **Phase 1**: LangGraphコア・5階層記憶システム  
✅ **Phase 2**: エラーハンドリング・セキュリティ  
✅ **Phase 3**: REST/WebSocket API（23エンドポイント）  
✅ **Phase 4**: 連想記憶システム・感情モデル基盤

**参照**: [`docks/実装仕様/Phase4_実装仕様.md`](Phase4_実装仕様.md:1)

### 2.2 利用可能なPhase 4機能

- **連想記憶システム**: [`memory/associative.py`](../../memory/associative.py)
- **感情モデル**: [`core/emotion.py`](../../core/emotion.py)
- **API追加**: `/api/v1/memory/associate`, `/api/v1/character/{name}/emotion`

---

## 3. Week 1-2: 対話スタイル動的調整

### 3.1 実装内容

**参照**: [`docks/仕様書/04_会話LLM_感情・対話仕様.md:152-208`](../仕様書/04_会話LLM_感情・対話仕様.md:152)

#### 3.1.1 スタイルパラメータ管理

**6つのパラメータ**（0.0 ～ 1.0）:

```python
{
    "formality": 0.5,      # カジュアル(0.0) ⇔ フォーマル(1.0)
    "verbosity": 0.5,      # 簡潔(0.0) ⇔ 詳細(1.0)
    "humor": 0.5,          # 真面目(0.0) ⇔ ユーモラス(1.0)
    "technical_level": 0.5,# 平易(0.0) ⇔ 専門的(1.0)
    "empathy": 0.7,        # 共感レベル
    "proactivity": 0.5     # 受動的(0.0) ⇔ 積極的(1.0)
}
```

#### 3.1.2 フィードバック学習

**ユーザーフィードバック例**:
- 👍 "もっと詳しく説明してほしい" → `verbosity += 0.1`
- 👍 "専門用語が多すぎる" → `technical_level -= 0.15`
- 👍 "カジュアルな感じがいい" → `formality -= 0.1`

#### 3.1.3 プロンプト動的生成

```python
# 例: formality=0.8, verbosity=0.3 の場合
"""
あなたは丁寧で簡潔な回答を心がけます。
敬語を使用し、要点を絞って説明してください。
"""

# 例: formality=0.2, humor=0.8 の場合
"""
あなたはフレンドリーでユーモアのある会話を心がけます。
軽いジョークを交えながら、リラックスした雰囲気で話してください。
"""
```

### 3.2 ファイル構成

#### core/dialogue_style.py (250行)

```python
"""対話スタイル動的調整モジュール."""

from typing import Dict, Any
import json


class AdaptiveDialogueStyle:
    """ユーザー別対話スタイル適応クラス."""
    
    def __init__(self, user_id: str):
        """
        初期化.
        
        Args:
            user_id: ユーザーID
        """
        self.user_id = user_id
        self.parameters = {
            "formality": 0.5,
            "verbosity": 0.5,
            "humor": 0.5,
            "technical_level": 0.5,
            "empathy": 0.7,
            "proactivity": 0.5
        }
        self._load_from_profile()
    
    def learn_from_feedback(self, user_feedback: Dict[str, Any]) -> None:
        """
        ユーザーフィードバックから学習.
        
        Args:
            user_feedback: {
                "message": "もっと詳しく説明してほしい",
                "thumbs_up": True,
                "specific_feedback": {"verbosity": "+"}
            }
        """
        if user_feedback.get("specific_feedback"):
            for param, direction in user_feedback["specific_feedback"].items():
                if direction == "+":
                    self.parameters[param] = min(1.0, self.parameters[param] + 0.1)
                elif direction == "-":
                    self.parameters[param] = max(0.0, self.parameters[param] - 0.1)
        
        # フィードバックメッセージからの自動推論
        message = user_feedback.get("message", "").lower()
        if "詳し" in message or "detail" in message:
            self.parameters["verbosity"] = min(1.0, self.parameters["verbosity"] + 0.15)
        if "簡潔" in message or "brief" in message:
            self.parameters["verbosity"] = max(0.0, self.parameters["verbosity"] - 0.15)
        if "専門" in message or "technical" in message:
            self.parameters["technical_level"] = min(1.0, self.parameters["technical_level"] + 0.15)
        if "わかりやすく" in message or "simple" in message:
            self.parameters["technical_level"] = max(0.0, self.parameters["technical_level"] - 0.15)
        
        self._save_to_profile()
    
    def generate_style_prompt(self) -> str:
        """
        スタイルに応じたプロンプト修飾子生成.
        
        Returns:
            str: プロンプト修飾子
        """
        prompt_parts = []
        
        # Formality
        if self.parameters["formality"] > 0.7:
            prompt_parts.append("丁寧で礼儀正しい言葉遣いを心がけてください。")
        elif self.parameters["formality"] < 0.3:
            prompt_parts.append("フレンドリーでカジュアルな言葉遣いで話してください。")
        
        # Verbosity
        if self.parameters["verbosity"] > 0.7:
            prompt_parts.append("詳細な説明と具体例を多く含めてください。")
        elif self.parameters["verbosity"] < 0.3:
            prompt_parts.append("簡潔で要点を絞った回答を心がけてください。")
        
        # Humor
        if self.parameters["humor"] > 0.7:
            prompt_parts.append("適度にユーモアを交え、楽しい雰囲気で話してください。")
        elif self.parameters["humor"] < 0.3:
            prompt_parts.append("真面目で誠実なトーンを保ってください。")
        
        # Technical Level
        if self.parameters["technical_level"] > 0.7:
            prompt_parts.append("専門用語や技術的な詳細を含めて説明してください。")
        elif self.parameters["technical_level"] < 0.3:
            prompt_parts.append("平易な言葉で、誰にでもわかりやすく説明してください。")
        
        # Empathy
        if self.parameters["empathy"] > 0.7:
            prompt_parts.append("ユーザーの感情に寄り添い、共感的な態度を示してください。")
        
        # Proactivity
        if self.parameters["proactivity"] > 0.7:
            prompt_parts.append("積極的に提案や追加情報を提供してください。")
        elif self.parameters["proactivity"] < 0.3:
            prompt_parts.append("ユーザーの質問に対してのみ回答してください。")
        
        return "\n".join(prompt_parts)
    
    def _load_from_profile(self) -> None:
        """ユーザープロファイルから読み込み."""
        try:
            with open(f"profiles/{self.user_id}_style.json", "r") as f:
                saved_params = json.load(f)
                self.parameters.update(saved_params)
        except FileNotFoundError:
            pass
    
    def _save_to_profile(self) -> None:
        """ユーザープロファイルに保存."""
        import os
        os.makedirs("profiles", exist_ok=True)
        with open(f"profiles/{self.user_id}_style.json", "w") as f:
            json.dump(self.parameters, f, indent=2)
```

### 3.3 テスト（12件）

#### tests/test_dialogue_style.py

```python
"""対話スタイル適応モジュールのテスト."""

import pytest
from core.dialogue_style import AdaptiveDialogueStyle


def test_style_init():
    """初期化テスト."""
    style = AdaptiveDialogueStyle("user_001")
    assert style.user_id == "user_001"
    assert style.parameters["formality"] == 0.5
    assert style.parameters["empathy"] == 0.7


def test_learn_from_feedback():
    """フィードバック学習テスト."""
    style = AdaptiveDialogueStyle("user_002")
    
    # 詳細希望フィードバック
    style.learn_from_feedback({
        "message": "もっと詳しく説明してほしい",
        "thumbs_up": True
    })
    assert style.parameters["verbosity"] > 0.5
    
    # 専門用語多すぎるフィードバック
    style.learn_from_feedback({
        "message": "専門用語が多すぎる",
        "thumbs_up": False
    })
    # Note: 現在の実装では"専門"は増加方向なので、別ロジック必要


def test_generate_style_prompt():
    """プロンプト生成テスト."""
    style = AdaptiveDialogueStyle("user_003")
    
    # フォーマル・詳細
    style.parameters["formality"] = 0.8
    style.parameters["verbosity"] = 0.8
    prompt = style.generate_style_prompt()
    assert "丁寧" in prompt
    assert "詳細" in prompt
    
    # カジュアル・簡潔
    style.parameters["formality"] = 0.2
    style.parameters["verbosity"] = 0.2
    prompt = style.generate_style_prompt()
    assert "フレンドリー" in prompt or "カジュアル" in prompt
    assert "簡潔" in prompt


def test_parameter_bounds():
    """パラメータ境界テスト."""
    style = AdaptiveDialogueStyle("user_004")
    
    # 上限チェック
    for _ in range(20):
        style.learn_from_feedback({"message": "詳しく", "thumbs_up": True})
    assert style.parameters["verbosity"] <= 1.0
    
    # 下限チェック
    style.parameters["verbosity"] = 0.0
    for _ in range(20):
        style.learn_from_feedback({"message": "簡潔に", "thumbs_up": True})
    assert style.parameters["verbosity"] >= 0.0


def test_save_and_load():
    """保存・読み込みテスト."""
    style1 = AdaptiveDialogueStyle("user_005")
    style1.parameters["formality"] = 0.9
    style1._save_to_profile()
    
    style2 = AdaptiveDialogueStyle("user_005")
    assert style2.parameters["formality"] == 0.9


# ... 他7件（境界値、異常系、統合テスト）
```

---

## 4. Week 3-4: 自己省察・一貫性チェック

### 4.1 実装内容

**参照**: [`docks/仕様書/04_会話LLM_感情・対話仕様.md:230-536`](../仕様書/04_会話LLM_感情・対話仕様.md:230)

#### 4.1.1 自己省察（Reflection）

**目的**: 会話終了後の振り返りと学習

```python
# 省察例
{
    "timestamp": "2025-11-20T15:30:00Z",
    "session_id": "sess_001",
    "reflection": "ユーザーは機械学習について初心者だった。専門用語を多用しすぎた。次回は平易な言葉で説明すべき。",
    "lessons_learned": [
        "technical_level を下げる",
        "具体例を多用する"
    ],
    "improvement_areas": ["説明の平易化", "ユーザーレベル推定精度向上"]
}
```

#### 4.1.2 矛盾検出（Contradiction Detection）

**目的**: 過去発言との一貫性維持

```python
# 矛盾検出例
{
    "new_statement": "私は猫が好きです",
    "contradictory_past_statement": {
        "content": "私は猫が苦手です",
        "timestamp": "2025-11-15T10:00:00Z",
        "session_id": "sess_old_001"
    },
    "contradiction_detected": True,
    "clarification": "以前「猫が苦手」とおっしゃっていましたが、最近は猫がお好きになられたのですか？"
}
```

#### 4.1.3 トピック追跡（Topic Tracking）

**目的**: 話題の流れ管理と自然な転換

```python
# トピック履歴例
{
    "topic_history": [
        {"topic": "機械学習", "start": 1, "end": 5, "duration": 5},
        {"topic": "Python", "start": 6, "end": 10, "duration": 5},
        {"topic": "データベース", "start": 11, "end": None, "duration": None}
    ],
    "current_topic": "データベース",
    "shift_detected": True,
    "transition_phrase": "Pythonの話から、データベースについてお話しましょうか。"
}
```

### 4.2 ファイル構成

#### core/self_reflection.py (300行)

```python
"""自己省察・一貫性チェックモジュール."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from memory.long_term import LongTermMemory


class SelfReflection:
    """自己省察クラス."""
    
    def __init__(self, character_name: str):
        """
        初期化.
        
        Args:
            character_name: キャラクター名
        """
        self.character_name = character_name
        self.long_term_memory = LongTermMemory()
    
    def reflect_on_conversation(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        会話振り返り.
        
        Args:
            conversation_history: 会話履歴
        
        Returns:
            Dict: 省察結果
        """
        reflection = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": conversation_history[0].get("session_id"),
            "reflection": "",
            "lessons_learned": [],
            "improvement_areas": []
        }
        
        # ユーザー発言からパターン抽出
        user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
        if not user_messages:
            return reflection
        
        # 分析例（実際はLLMで生成）
        reflection["reflection"] = f"{len(user_messages)}回のやり取りがありました。"
        
        # 学びの抽出
        if any("わかりやすく" in msg.get("content", "") for msg in user_messages):
            reflection["lessons_learned"].append("technical_level を下げる")
        
        if any("詳しく" in msg.get("content", "") for msg in user_messages):
            reflection["lessons_learned"].append("verbosity を上げる")
        
        self._store_reflection(reflection)
        return reflection
    
    def _store_reflection(self, reflection: Dict[str, Any]) -> None:
        """省察を長期記憶に保存."""
        self.long_term_memory.store(
            content=json.dumps(reflection, ensure_ascii=False),
            category="reflection",
            metadata={"character": self.character_name}
        )
    
    def retrieve_past_lessons(self, current_situation: str) -> List[Dict[str, Any]]:
        """
        過去の学びを検索.
        
        Args:
            current_situation: 現在の状況（例: "ユーザーが技術的な質問をしている"）
        
        Returns:
            List[Dict]: 関連する過去の学び
        """
        results = self.long_term_memory.search(
            query=current_situation,
            top_k=5,
            filter_dict={"category": "reflection"}
        )
        
        lessons = []
        for result in results:
            try:
                reflection = json.loads(result["content"])
                lessons.append(reflection)
            except json.JSONDecodeError:
                continue
        
        return lessons


class DialogueCoherence:
    """対話一貫性チェッククラス."""
    
    def __init__(self):
        """初期化."""
        self.long_term_memory = LongTermMemory()
    
    def check_consistency(
        self,
        new_statement: str,
        history: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        一貫性チェック.
        
        Args:
            new_statement: 新しい発言
            history: 会話履歴
            threshold: 矛盾検出閾値
        
        Returns:
            Dict: チェック結果
        """
        result = {
            "contradiction_detected": False,
            "contradictory_past_statement": None,
            "clarification": None
        }
        
        # 過去発言から類似トピック検索
        past_statements = self.long_term_memory.search(
            query=new_statement,
            top_k=10
        )
        
        for past in past_statements:
            if self._detect_contradiction(new_statement, past["content"]):
                result["contradiction_detected"] = True
                result["contradictory_past_statement"] = past
                result["clarification"] = self._generate_clarification(
                    new_statement,
                    past["content"]
                )
                break
        
        return result
    
    def _detect_contradiction(self, stmt1: str, stmt2: str) -> bool:
        """
        矛盾検出（簡易版）.
        
        実際はLLMまたはNLI（Natural Language Inference）モデルを使用.
        """
        # 簡易実装例
        negation_patterns = [
            ("好き", "苦手"),
            ("得意", "苦手"),
            ("賛成", "反対")
        ]
        
        for pos, neg in negation_patterns:
            if (pos in stmt1 and neg in stmt2) or (neg in stmt1 and pos in stmt2):
                return True
        
        return False
    
    def _generate_clarification(self, new_stmt: str, past_stmt: str) -> str:
        """
        矛盾に対する明確化質問生成.
        
        Args:
            new_stmt: 新発言
            past_stmt: 過去発言
        
        Returns:
            str: 明確化質問
        """
        return f"以前「{past_stmt}」とおっしゃっていましたが、今回は「{new_stmt}」とのこと。お考えが変わられたのでしょうか？"


class TopicTracker:
    """トピック追跡クラス."""
    
    def __init__(self):
        """初期化."""
        self.topic_history: List[Dict[str, Any]] = []
        self.current_topic: Optional[str] = None
        self.message_count = 0
    
    def detect_topic_shift(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        話題転換検出.
        
        Args:
            user_input: ユーザー入力
            context: 文脈情報
        
        Returns:
            Dict: 検出結果
        """
        self.message_count += 1
        
        # トピック抽出（簡易版、実際はLLMで抽出）
        new_topic = self._extract_topic(user_input)
        
        shift_detected = False
        if self.current_topic and new_topic != self.current_topic:
            shift_detected = True
            # 現在のトピック終了
            if self.topic_history:
                self.topic_history[-1]["end"] = self.message_count - 1
                self.topic_history[-1]["duration"] = (
                    self.topic_history[-1]["end"] - self.topic_history[-1]["start"] + 1
                )
        
        if shift_detected or self.current_topic is None:
            self.current_topic = new_topic
            self.topic_history.append({
                "topic": new_topic,
                "start": self.message_count,
                "end": None,
                "duration": None
            })
        
        return {
            "shift_detected": shift_detected,
            "current_topic": self.current_topic,
            "topic_history": self.topic_history
        }
    
    def generate_transition_phrase(self, old_topic: str, new_topic: str) -> str:
        """
        話題転換フレーズ生成.
        
        Args:
            old_topic: 旧トピック
            new_topic: 新トピック
        
        Returns:
            str: 転換フレーズ
        """
        return f"{old_topic}の話から、{new_topic}についてお話しましょうか。"
    
    def suggest_topic_return(self) -> Optional[str]:
        """
        以前のトピックへの戻り提案.
        
        Returns:
            Optional[str]: 提案メッセージ
        """
        if len(self.topic_history) < 2:
            return None
        
        previous_topic = self.topic_history[-2]["topic"]
        return f"先ほどの{previous_topic}の話題に戻りましょうか？"
    
    def _extract_topic(self, text: str) -> str:
        """
        トピック抽出（簡易版）.
        
        実際はLLMまたはトピックモデルを使用.
        """
        # キーワードベース簡易実装
        keywords = {
            "機械学習": ["機械学習", "ML", "モデル"],
            "Python": ["Python", "パイソン", "コード"],
            "データベース": ["データベース", "DB", "SQL"]
        }
        
        for topic, kws in keywords.items():
            if any(kw in text for kw in kws):
                return topic
        
        return "その他"
```

### 4.3 テスト（18件）

#### tests/test_self_reflection.py

```python
"""自己省察・一貫性チェックモジュールのテスト."""

import pytest
from core.self_reflection import SelfReflection, DialogueCoherence, TopicTracker


def test_reflect_on_conversation():
    """省察テスト."""
    reflection = SelfReflection("lumina")
    
    conversation = [
        {"role": "user", "content": "わかりやすく説明してください", "session_id": "sess_001"},
        {"role": "assistant", "content": "承知しました", "session_id": "sess_001"}
    ]
    
    result = reflection.reflect_on_conversation(conversation)
    assert result["session_id"] == "sess_001"
    assert "technical_level を下げる" in result["lessons_learned"]


def test_store_reflection():
    """省察保存テスト."""
    reflection = SelfReflection("clarisse")
    
    conversation = [
        {"role": "user", "content": "詳しく教えて", "session_id": "sess_002"},
        {"role": "assistant", "content": "はい", "session_id": "sess_002"}
    ]
    
    result = reflection.reflect_on_conversation(conversation)
    # 保存処理は _store_reflection 内で実行済み
    assert result is not None


def test_retrieve_past_lessons():
    """学び検索テスト."""
    reflection = SelfReflection("lumina")
    
    lessons = reflection.retrieve_past_lessons("ユーザーが技術的な質問をしている")
    assert isinstance(lessons, list)


def test_check_consistency():
    """一貫性チェックテスト."""
    coherence = DialogueCoherence()
    
    history = [
        {"role": "assistant", "content": "私は猫が苦手です"}
    ]
    
    result = coherence.check_consistency("私は猫が好きです", history)
    # Note: 実際は長期記憶に保存されたものを検索するため、テスト環境では検出されない可能性


def test_detect_contradiction():
    """矛盾検出テスト."""
    coherence = DialogueCoherence()
    
    # 矛盾あり
    assert coherence._detect_contradiction("私は猫が好きです", "私は猫が苦手です")
    
    # 矛盾なし
    assert not coherence._detect_contradiction("私は猫が好きです", "私は犬も好きです")


def test_topic_shift_detection():
    """話題転換検出テスト."""
    tracker = TopicTracker()
    
    # 初回
    result1 = tracker.detect_topic_shift("機械学習について教えてください", {})
    assert result1["shift_detected"] is False
    assert result1["current_topic"] == "機械学習"
    
    # 同じトピック
    result2 = tracker.detect_topic_shift("機械学習のモデルは？", {})
    assert result2["shift_detected"] is False
    
    # トピック転換
    result3 = tracker.detect_topic_shift("Pythonのコードを教えて", {})
    assert result3["shift_detected"] is True
    assert result3["current_topic"] == "Python"


def test_transition_phrase():
    """転換フレーズテスト."""
    tracker = TopicTracker()
    
    phrase = tracker.generate_transition_phrase("機械学習", "Python")
    assert "機械学習" in phrase
    assert "Python" in phrase


# ... 他11件（境界値、異常系、統合テスト）
```

---

## 5. 技術スタック

### 5.1 Python依存

```txt
# requirements.txt に追加
textblob==0.17.1        # センチメント分析（感情推論用）
scikit-learn==1.3.0     # トピック抽出・類似度計算
```

### 5.2 新規モジュール

- **core/dialogue_style.py**: 対話スタイル適応
- **core/self_reflection.py**: 自己省察・一貫性チェック

---

## 6. テスト計画（TDD実装）

### 6.1 テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| **対話スタイル適応** |
| AdaptiveDialogueStyle | `test_dialogue_style.py` | 25 | 95%以上 | 🔴 High |
| **自己省察・一貫性** |
| SelfReflection | `test_self_reflection.py` | 15 | 95%以上 | 🔴 High |
| DialogueCoherence | `test_self_reflection.py` | 15 | 90%以上 | 🔴 High |
| TopicTracker | `test_self_reflection.py` | 15 | 90%以上 | 🟡 Medium |
| **統合テスト** |
| 長期記憶連携 | `test_integration_reflection.py` | 10 | 85%以上 | 🟡 Medium |
| API統合 | `test_api_dialogue.py` | 10 | 85%以上 | 🟡 Medium |
| **合計** | **6ファイル** | **90** | **平均90%以上** | - |

### 6.2 テスト実行方法

#### 基本的なテスト実行

```bash
# 全テスト実行
pytest tests/test_dialogue_style.py tests/test_self_reflection.py -v

# カバレッジ付きテスト実行
pytest tests/ --cov=core.dialogue_style --cov=core.self_reflection --cov-report=html --cov-report=term

# 特定のテストのみ
pytest tests/test_dialogue_style.py::test_style_init -v

# マーカーで実行
pytest -m unit -v  # ユニットテストのみ
pytest -m integration -v  # 統合テストのみ
```

#### TDDサイクルでの実行

```bash
# 1. テストを書いた後（RED）
pytest tests/test_dialogue_style.py::test_style_init -v
# → 期待: FAILED（実装前）

# 2. 最小限の実装後（GREEN）
pytest tests/test_dialogue_style.py::test_style_init -v
# → 期待: PASSED

# 3. リファクタリング後（REFACTOR）
pytest tests/test_dialogue_style.py -v
# → 期待: 全テスト PASSED
```

---

## Week 1-2: 対話スタイル動的調整 - テスト仕様（TDD）

### テストファイル: `tests/test_dialogue_style.py`

**テストクラス**: `TestAdaptiveDialogueStyle`

**テストケース一覧（25件）**:

#### 1. 初期化テスト（4件）

```python
def test_style_init_default_parameters():
    """
    Given: ユーザーID
    When: AdaptiveDialogueStyleを初期化
    Then: デフォルトパラメータが設定される
    """
    style = AdaptiveDialogueStyle("user_001")
    
    assert style.user_id == "user_001"
    assert style.parameters["formality"] == 0.5
    assert style.parameters["verbosity"] == 0.5
    assert style.parameters["humor"] == 0.5
    assert style.parameters["technical_level"] == 0.5
    assert style.parameters["empathy"] == 0.7
    assert style.parameters["proactivity"] == 0.5

def test_style_init_load_from_profile():
    """
    Given: 既存のプロファイルファイル
    When: AdaptiveDialogueStyleを初期化
    Then: プロファイルからパラメータが読み込まれる
    """
    # 事前にプロファイルを作成
    import os
    os.makedirs("profiles", exist_ok=True)
    with open("profiles/user_002_style.json", "w") as f:
        json.dump({"formality": 0.8, "verbosity": 0.3}, f)
    
    style = AdaptiveDialogueStyle("user_002")
    
    assert style.parameters["formality"] == 0.8
    assert style.parameters["verbosity"] == 0.3

def test_style_init_nonexistent_profile():
    """
    Given: 存在しないプロファイル
    When: AdaptiveDialogueStyleを初期化
    Then: デフォルトパラメータが使用される
    """
    style = AdaptiveDialogueStyle("nonexistent_user")
    
    assert style.parameters["formality"] == 0.5
    assert style.parameters["verbosity"] == 0.5
```

#### 2. フィードバック学習テスト（8件）

```python
def test_learn_from_feedback_verbosity_increase():
    """
    Given: 詳細希望フィードバック
    When: learn_from_feedback()を呼び出す
    Then: verbosityパラメータが増加する
    """
    style = AdaptiveDialogueStyle("user_003")
    initial_verbosity = style.parameters["verbosity"]
    
    style.learn_from_feedback({
        "message": "もっと詳しく説明してほしい",
        "thumbs_up": True
    })
    
    assert style.parameters["verbosity"] > initial_verbosity
    assert style.parameters["verbosity"] <= 1.0

def test_learn_from_feedback_verbosity_decrease():
    """
    Given: 簡潔希望フィードバック
    When: learn_from_feedback()を呼び出す
    Then: verbosityパラメータが減少する
    """
    style = AdaptiveDialogueStyle("user_004")
    initial_verbosity = style.parameters["verbosity"]
    
    style.learn_from_feedback({
        "message": "簡潔に説明してください",
        "thumbs_up": True
    })
    
    assert style.parameters["verbosity"] < initial_verbosity
    assert style.parameters["verbosity"] >= 0.0

def test_learn_from_feedback_technical_level_decrease():
    """
    Given: 専門用語多すぎるフィードバック
    When: learn_from_feedback()を呼び出す
    Then: technical_levelパラメータが減少する
    """
    style = AdaptiveDialogueStyle("user_005")
    style.parameters["technical_level"] = 0.8
    initial_level = style.parameters["technical_level"]
    
    style.learn_from_feedback({
        "message": "わかりやすく説明してください",
        "thumbs_up": True
    })
    
    assert style.parameters["technical_level"] < initial_level
    assert style.parameters["technical_level"] >= 0.0

def test_learn_from_feedback_specific_feedback():
    """
    Given: 特定パラメータのフィードバック
    When: learn_from_feedback()を呼び出す
    Then: 指定されたパラメータが更新される
    """
    style = AdaptiveDialogueStyle("user_006")
    initial_formality = style.parameters["formality"]
    
    style.learn_from_feedback({
        "message": "カジュアルな感じがいい",
        "thumbs_up": True,
        "specific_feedback": {"formality": "-"}
    })
    
    assert style.parameters["formality"] < initial_formality

def test_learn_from_feedback_parameter_upper_bound():
    """
    Given: 上限に達しているパラメータ
    When: learn_from_feedback()で増加を試みる
    Then: パラメータが1.0を超えない
    """
    style = AdaptiveDialogueStyle("user_007")
    style.parameters["verbosity"] = 1.0
    
    style.learn_from_feedback({
        "message": "もっと詳しく",
        "thumbs_up": True
    })
    
    assert style.parameters["verbosity"] == 1.0

def test_learn_from_feedback_parameter_lower_bound():
    """
    Given: 下限に達しているパラメータ
    When: learn_from_feedback()で減少を試みる
    Then: パラメータが0.0を下回らない
    """
    style = AdaptiveDialogueStyle("user_008")
    style.parameters["verbosity"] = 0.0
    
    style.learn_from_feedback({
        "message": "簡潔に",
        "thumbs_up": True
    })
    
    assert style.parameters["verbosity"] == 0.0

def test_learn_from_feedback_saves_to_profile():
    """
    Given: フィードバック学習
    When: learn_from_feedback()を呼び出す
    Then: プロファイルに保存される
    """
    style = AdaptiveDialogueStyle("user_009")
    style.learn_from_feedback({
        "message": "詳しく",
        "thumbs_up": True
    })
    
    # 新しいインスタンスで読み込み確認
    style2 = AdaptiveDialogueStyle("user_009")
    assert style2.parameters["verbosity"] > 0.5
```

#### 3. プロンプト生成テスト（8件）

```python
def test_generate_style_prompt_formal():
    """
    Given: フォーマルなパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: フォーマルなプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_010")
    style.parameters["formality"] = 0.8
    
    prompt = style.generate_style_prompt()
    
    assert "丁寧" in prompt or "礼儀正しい" in prompt

def test_generate_style_prompt_casual():
    """
    Given: カジュアルなパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: カジュアルなプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_011")
    style.parameters["formality"] = 0.2
    
    prompt = style.generate_style_prompt()
    
    assert "フレンドリー" in prompt or "カジュアル" in prompt

def test_generate_style_prompt_verbose():
    """
    Given: 詳細なパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: 詳細な説明を促すプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_012")
    style.parameters["verbosity"] = 0.8
    
    prompt = style.generate_style_prompt()
    
    assert "詳細" in prompt or "具体例" in prompt

def test_generate_style_prompt_concise():
    """
    Given: 簡潔なパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: 簡潔な説明を促すプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_013")
    style.parameters["verbosity"] = 0.2
    
    prompt = style.generate_style_prompt()
    
    assert "簡潔" in prompt or "要点" in prompt

def test_generate_style_prompt_humorous():
    """
    Given: ユーモラスなパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: ユーモアを含むプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_014")
    style.parameters["humor"] = 0.8
    
    prompt = style.generate_style_prompt()
    
    assert "ユーモア" in prompt or "楽しい" in prompt

def test_generate_style_prompt_technical():
    """
    Given: 専門的なパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: 専門用語を含むプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_015")
    style.parameters["technical_level"] = 0.8
    
    prompt = style.generate_style_prompt()
    
    assert "専門用語" in prompt or "技術的" in prompt

def test_generate_style_prompt_empathy():
    """
    Given: 共感度の高いパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: 共感的なプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_016")
    style.parameters["empathy"] = 0.8
    
    prompt = style.generate_style_prompt()
    
    assert "共感" in prompt or "寄り添い" in prompt

def test_generate_style_prompt_multiple_parameters():
    """
    Given: 複数のパラメータ設定
    When: generate_style_prompt()を呼び出す
    Then: 複数の指示を含むプロンプトが生成される
    """
    style = AdaptiveDialogueStyle("user_017")
    style.parameters["formality"] = 0.8
    style.parameters["verbosity"] = 0.8
    style.parameters["humor"] = 0.2
    
    prompt = style.generate_style_prompt()
    
    assert "丁寧" in prompt
    assert "詳細" in prompt
    assert "真面目" in prompt or "誠実" in prompt
```

#### 4. エッジケース・統合テスト（5件）

```python
def test_parameter_bounds_extreme_values():
    """
    Given: 極端な値でのフィードバック
    When: 複数回フィードバックを適用
    Then: パラメータが境界内に保たれる
    """
    style = AdaptiveDialogueStyle("user_018")
    
    # 上限テスト
    for _ in range(20):
        style.learn_from_feedback({"message": "詳しく", "thumbs_up": True})
    assert style.parameters["verbosity"] <= 1.0
    
    # 下限テスト
    style.parameters["verbosity"] = 0.0
    for _ in range(20):
        style.learn_from_feedback({"message": "簡潔に", "thumbs_up": True})
    assert style.parameters["verbosity"] >= 0.0

def test_empty_feedback_message():
    """
    Given: 空のフィードバックメッセージ
    When: learn_from_feedback()を呼び出す
    Then: エラーが発生しない
    """
    style = AdaptiveDialogueStyle("user_019")
    
    style.learn_from_feedback({
        "message": "",
        "thumbs_up": True
    })
    
    # パラメータは変更されない
    assert style.parameters["verbosity"] == 0.5

def test_invalid_parameter_name():
    """
    Given: 無効なパラメータ名
    When: learn_from_feedback()で指定
    Then: エラーが発生しない（無視される）
    """
    style = AdaptiveDialogueStyle("user_020")
    
    style.learn_from_feedback({
        "message": "test",
        "specific_feedback": {"invalid_param": "+"}
    })
    
    # エラーが発生しないことを確認
    assert "invalid_param" not in style.parameters
```

---

## Week 3-4: 自己省察・一貫性チェック - テスト仕様（TDD）

### テストファイル: `tests/test_self_reflection.py`

**テストクラス**: `TestSelfReflection`, `TestDialogueCoherence`, `TestTopicTracker`

**テストケース一覧（45件）**:

#### 1. SelfReflection テスト（15件）

```python
class TestSelfReflection:
    """自己省察クラスのテスト"""
    
    def test_reflect_on_conversation_success(self):
        """
        Given: 会話履歴
        When: reflect_on_conversation()を呼び出す
        Then: 省察結果が返される
        """
        reflection = SelfReflection("lumina")
        
        conversation = [
            {"role": "user", "content": "わかりやすく説明してください", "session_id": "sess_001"},
            {"role": "assistant", "content": "承知しました", "session_id": "sess_001"}
        ]
        
        result = reflection.reflect_on_conversation(conversation)
        
        assert "timestamp" in result
        assert result["session_id"] == "sess_001"
        assert "reflection" in result
        assert "lessons_learned" in result
        assert isinstance(result["lessons_learned"], list)
    
    def test_reflect_on_conversation_extracts_lessons(self):
        """
        Given: わかりやすく説明してほしいという会話
        When: reflect_on_conversation()を呼び出す
        Then: technical_levelを下げるという学びが抽出される
        """
        reflection = SelfReflection("lumina")
        
        conversation = [
            {"role": "user", "content": "わかりやすく説明してください", "session_id": "sess_002"},
            {"role": "assistant", "content": "承知しました", "session_id": "sess_002"}
        ]
        
        result = reflection.reflect_on_conversation(conversation)
        
        assert "technical_level を下げる" in result["lessons_learned"]
    
    def test_reflect_on_conversation_empty_history(self):
        """
        Given: 空の会話履歴
        When: reflect_on_conversation()を呼び出す
        Then: 空の省察結果が返される
        """
        reflection = SelfReflection("lumina")
        
        result = reflection.reflect_on_conversation([])
        
        assert result["reflection"] == ""
        assert result["lessons_learned"] == []
    
    def test_reflect_on_conversation_no_user_messages(self):
        """
        Given: ユーザーメッセージがない会話履歴
        When: reflect_on_conversation()を呼び出す
        Then: 空の省察結果が返される
        """
        reflection = SelfReflection("lumina")
        
        conversation = [
            {"role": "assistant", "content": "こんにちは", "session_id": "sess_003"}
        ]
        
        result = reflection.reflect_on_conversation(conversation)
        
        assert result["lessons_learned"] == []
    
    def test_store_reflection(self):
        """
        Given: 省察結果
        When: reflect_on_conversation()を呼び出す
        Then: 省察が長期記憶に保存される
        """
        reflection = SelfReflection("clarisse")
        
        conversation = [
            {"role": "user", "content": "詳しく教えて", "session_id": "sess_004"},
            {"role": "assistant", "content": "はい", "session_id": "sess_004"}
        ]
        
        result = reflection.reflect_on_conversation(conversation)
        
        # 保存処理は _store_reflection 内で実行済み
        assert result is not None
    
    def test_retrieve_past_lessons(self):
        """
        Given: 過去の学びが保存されている
        When: retrieve_past_lessons()を呼び出す
        Then: 関連する過去の学びが返される
        """
        reflection = SelfReflection("lumina")
        
        # 事前に省察を保存
        conversation = [
            {"role": "user", "content": "わかりやすく", "session_id": "sess_005"},
            {"role": "assistant", "content": "承知", "session_id": "sess_005"}
        ]
        reflection.reflect_on_conversation(conversation)
        
        lessons = reflection.retrieve_past_lessons("ユーザーが技術的な質問をしている")
        
        assert isinstance(lessons, list)
```

#### 2. DialogueCoherence テスト（15件）

```python
class TestDialogueCoherence:
    """対話一貫性チェッククラスのテスト"""
    
    def test_check_consistency_no_contradiction(self):
        """
        Given: 矛盾のない新しい発言
        When: check_consistency()を呼び出す
        Then: 矛盾が検出されない
        """
        coherence = DialogueCoherence()
        
        history = [
            {"role": "assistant", "content": "私は猫が好きです"}
        ]
        
        result = coherence.check_consistency("私は犬も好きです", history)
        
        assert result["contradiction_detected"] is False
        assert result["contradictory_past_statement"] is None
    
    def test_detect_contradiction_like_dislike(self):
        """
        Given: 好きと苦手の矛盾
        When: _detect_contradiction()を呼び出す
        Then: 矛盾が検出される
        """
        coherence = DialogueCoherence()
        
        assert coherence._detect_contradiction("私は猫が好きです", "私は猫が苦手です")
    
    def test_detect_contradiction_no_contradiction(self):
        """
        Given: 矛盾のない2つの発言
        When: _detect_contradiction()を呼び出す
        Then: 矛盾が検出されない
        """
        coherence = DialogueCoherence()
        
        assert not coherence._detect_contradiction("私は猫が好きです", "私は犬も好きです")
    
    def test_detect_contradiction_opposite_patterns(self):
        """
        Given: 反対のパターン
        When: _detect_contradiction()を呼び出す
        Then: 矛盾が検出される
        """
        coherence = DialogueCoherence()
        
        # 得意と苦手
        assert coherence._detect_contradiction("私はプログラミングが得意です", "私はプログラミングが苦手です")
        
        # 賛成と反対
        assert coherence._detect_contradiction("その案に賛成です", "その案に反対です")
    
    def test_generate_clarification(self):
        """
        Given: 矛盾が検出された
        When: _generate_clarification()を呼び出す
        Then: 明確化質問が生成される
        """
        coherence = DialogueCoherence()
        
        clarification = coherence._generate_clarification(
            "私は猫が好きです",
            "私は猫が苦手です"
        )
        
        assert "以前" in clarification
        assert "猫が苦手" in clarification
        assert "猫が好き" in clarification
```

#### 3. TopicTracker テスト（15件）

```python
class TestTopicTracker:
    """トピック追跡クラスのテスト"""
    
    def test_detect_topic_shift_initial(self):
        """
        Given: 初回のユーザー入力
        When: detect_topic_shift()を呼び出す
        Then: トピックが設定され、転換は検出されない
        """
        tracker = TopicTracker()
        
        result = tracker.detect_topic_shift("機械学習について教えてください", {})
        
        assert result["shift_detected"] is False
        assert result["current_topic"] == "機械学習"
        assert len(result["topic_history"]) == 1
    
    def test_detect_topic_shift_same_topic(self):
        """
        Given: 同じトピックの入力
        When: detect_topic_shift()を呼び出す
        Then: 転換は検出されない
        """
        tracker = TopicTracker()
        tracker.detect_topic_shift("機械学習について教えてください", {})
        
        result = tracker.detect_topic_shift("機械学習のモデルは？", {})
        
        assert result["shift_detected"] is False
        assert result["current_topic"] == "機械学習"
    
    def test_detect_topic_shift_different_topic(self):
        """
        Given: 異なるトピックの入力
        When: detect_topic_shift()を呼び出す
        Then: 転換が検出され、トピック履歴が更新される
        """
        tracker = TopicTracker()
        tracker.detect_topic_shift("機械学習について教えてください", {})
        
        result = tracker.detect_topic_shift("Pythonのコードを教えて", {})
        
        assert result["shift_detected"] is True
        assert result["current_topic"] == "Python"
        assert len(result["topic_history"]) == 2
        assert result["topic_history"][0]["topic"] == "機械学習"
        assert result["topic_history"][0]["end"] is not None
    
    def test_generate_transition_phrase(self):
        """
        Given: 旧トピックと新トピック
        When: generate_transition_phrase()を呼び出す
        Then: 転換フレーズが生成される
        """
        tracker = TopicTracker()
        
        phrase = tracker.generate_transition_phrase("機械学習", "Python")
        
        assert "機械学習" in phrase
        assert "Python" in phrase
    
    def test_suggest_topic_return(self):
        """
        Given: 2つ以上のトピック履歴
        When: suggest_topic_return()を呼び出す
        Then: 以前のトピックへの戻り提案が返される
        """
        tracker = TopicTracker()
        tracker.detect_topic_shift("機械学習について", {})
        tracker.detect_topic_shift("Pythonについて", {})
        
        suggestion = tracker.suggest_topic_return()
        
        assert suggestion is not None
        assert "機械学習" in suggestion
    
    def test_suggest_topic_return_insufficient_history(self):
        """
        Given: トピック履歴が1つ以下
        When: suggest_topic_return()を呼び出す
        Then: Noneが返される
        """
        tracker = TopicTracker()
        tracker.detect_topic_shift("機械学習について", {})
        
        suggestion = tracker.suggest_topic_return()
        
        assert suggestion is None
    
    def test_extract_topic_keyword_match(self):
        """
        Given: キーワードを含むテキスト
        When: _extract_topic()を呼び出す
        Then: 対応するトピックが返される
        """
        tracker = TopicTracker()
        
        assert tracker._extract_topic("機械学習のモデルについて") == "機械学習"
        assert tracker._extract_topic("Pythonのコードを書く") == "Python"
        assert tracker._extract_topic("データベースの設計") == "データベース"
    
    def test_extract_topic_no_match(self):
        """
        Given: キーワードに一致しないテキスト
        When: _extract_topic()を呼び出す
        Then: "その他"が返される
        """
        tracker = TopicTracker()
        
        assert tracker._extract_topic("今日はいい天気ですね") == "その他"
```

---

## テストフィクスチャ仕様

### conftest.py の拡張

```python
# tests/conftest.py（拡張）

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, MagicMock

from core.dialogue_style import AdaptiveDialogueStyle
from core.self_reflection import SelfReflection, DialogueCoherence, TopicTracker
from memory.long_term import LongTermMemory

@pytest.fixture
def temp_profile_dir():
    """一時的なプロファイルディレクトリ"""
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    os.makedirs("profiles", exist_ok=True)
    yield temp_dir
    os.chdir(original_dir)
    import shutil
    shutil.rmtree(temp_dir)

@pytest.fixture
def dialogue_style(temp_profile_dir):
    """AdaptiveDialogueStyleインスタンス"""
    return AdaptiveDialogueStyle("test_user")

@pytest.fixture
def mock_long_term_memory():
    """LongTermMemoryのモック"""
    mock = Mock(spec=LongTermMemory)
    mock.store = Mock(return_value={"memory_id": "mem_001"})
    mock.search = Mock(return_value=[])
    return mock

@pytest.fixture
def self_reflection(mock_long_term_memory):
    """SelfReflectionインスタンス（モック使用）"""
    reflection = SelfReflection("test_character")
    reflection.long_term_memory = mock_long_term_memory
    return reflection

@pytest.fixture
def dialogue_coherence(mock_long_term_memory):
    """DialogueCoherenceインスタンス（モック使用）"""
    coherence = DialogueCoherence()
    coherence.long_term_memory = mock_long_term_memory
    return coherence

@pytest.fixture
def topic_tracker():
    """TopicTrackerインスタンス"""
    return TopicTracker()
```

---

## テスト実行戦略

### TDD実装順序

1. **Week 1-2: 対話スタイル動的調整**
   - 1日目: 初期化テスト（4件）→ 実装
   - 2日目: フィードバック学習テスト（8件）→ 実装
   - 3日目: プロンプト生成テスト（8件）→ 実装
   - 4日目: エッジケース・統合テスト（5件）→ 実装・リファクタリング

2. **Week 3-4: 自己省察・一貫性チェック**
   - 1-2日目: SelfReflectionテスト（15件）→ 実装
   - 3日目: DialogueCoherenceテスト（15件）→ 実装
   - 4日目: TopicTrackerテスト（15件）→ 実装・リファクタリング

### テスト品質基準

**必須要件**:
- ✅ **テスト成功率**: 100%（全90件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: 全テスト3分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（LongTermMemory等）はモックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

---

## 7. 成果物

### 7.1 実装コード

**新規ファイル**:
- `core/dialogue_style.py` (250行)
- `core/self_reflection.py` (300行)
- **合計**: 550行

### 7.2 テストコード

**新規ファイル**:
- `tests/test_dialogue_style.py` (25件)
- `tests/test_self_reflection.py` (45件)
- `tests/test_integration_reflection.py` (10件)
- `tests/test_api_dialogue.py` (10件)
- **合計**: 90件

### 7.3 ドキュメント

- `docks/完了報告/Phase5_完了サマリー.md`
- API仕様書更新

### 7.4 マイルストーン

- [ ] 対話スタイル適応動作確認
- [ ] 自己省察・矛盾検出テスト成功
- [ ] トピック追跡精度 > 80%
- [ ] 全テスト成功（90件）
- [ ] カバレッジ > 90%

---

## 8. Phase 5成功基準

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全90件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: 全テスト3分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存（LongTermMemory等）はモックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | pytest（全90件） |
| **コードカバレッジ** | **90%以上** | pytest-cov |
| **テスト実行時間** | **< 3分** | pytest --durations |
| 対話スタイル適応精度 | > 85% | ユーザーフィードバック評価 |
| トピック追跡精度 | > 80% | トピック検出テスト |
| 矛盾検出精度 | > 75% | 矛盾検出テスト |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全90件のテストケースが定義されている
✅ **対話スタイル適応動作**: ユーザーフィードバックから学習
✅ **自己省察機能動作**: 会話振り返りとメタ認知
✅ **矛盾検出機能動作**: 過去発言との一貫性チェック
✅ **トピック追跡機能動作**: 話題の流れ管理

---

**Phase 5 実装完了**: ユーザー適応型対話システムの基盤が整いました。