# 会話LLM キャラクター仕様書

**バージョン:** 3.1.0  
**最終更新:** 2025-11-19  
**親文書:** [会話LLM_仕様.md](./01_会話LLM_仕様.md)

---

## 目次

1. [概要](#1-概要)
2. [標準キャラクター仕様](#2-標準キャラクター仕様)
3. [カスタムキャラクター追加機能](#3-カスタムキャラクター追加機能)
4. [キャラクター成長システム](#4-キャラクター成長システム)
5. [会話ルーティング仕様](#5-会話ルーティング仕様)
6. [ユーザー沈黙時の自走](#6-ユーザー沈黙時の自走)
7. [KPIとキャラ成長](#7-kpiとキャラ成長)
8. [ペルソナの一貫性](#8-ペルソナの一貫性)

---

## 1. 概要

会話LLMシステムでは、複数のAIキャラクターが独自の個性・専門性を持ち、ユーザーとの対話を担当します。各キャラクターは**永続的な記憶**を持ち、**感情状態**を管理し、**継続的に成長**します。

### 1.1 設計思想

- **多様性**: 3つの標準キャラ（ルミナ・クラリス・ノクス）が異なる視点を提供
- **拡張性**: ユーザー定義のカスタムキャラを動的に追加可能
- **成長性**: ユーザーとのインタラクションで自動的に成長・進化
- **一貫性**: キャラクター固有の性格・価値観・口調を維持

---

## 2. 標準キャラクター仕様

### 2.1 キャラクター一覧

| キャラ | 役割 | 個性・口調 | 検索 | ツール | 優先DB | モデル |
|--------|------|-------------|------|--------|--------|--------|
| **ルミナ** | 司会・雑談・推論 | フレンドリー／洞察型 | ✅ | Web検索, 画像生成 | MovieDB, HistoryDB | GPT-4o / Gemini |
| **クラリス** | 構造化・解説 | 穏やか／理論派 | ❌ | データ分析, グラフ生成 | HistoryDB | Claude Sonnet |
| **ノクス** | 情報ハンター・検証 | クール／要約特化 | ✅（高速） | リアルタイム検索, API | GossipDB, MovieDB | Llama3-JP |

### 2.2 ルミナ（Lumina）

#### 基本プロフィール
```yaml
name: "ルミナ"
role: "司会・推論・雑談"
personality:
  traits: ["フレンドリー", "洞察力がある", "好奇心旺盛"]
  speaking_style: "明るく親しみやすい口調"
  emoji_usage: "頻繁に使用（😊💡✨）"
model:
  primary: "gpt-4o"
  fallback: "gemini-pro"
  temperature: 0.7
tools:
  - web_search
  - image_generation
  - knowledge_base_query
priority_kb:
  - kb:movie
  - kb:history
  - kb:gossip
```

#### 口調サンプル
```
✨ 「インセプションね！あの映画、夢と現実が入り混じる感じが本当に面白いよね。
クリストファー・ノーラン監督の作品だけど、『メメント』や『プレステージ』も
同じような複雑な構造が特徴なの。興味ある？」
```

#### 得意分野
- 映画・エンタメの推薦
- 話題の深掘り・関連情報の提供
- ユーザーとの雑談・共感
- 全体の会話フロー調整

---

### 2.3 クラリス（Clarisse）

#### 基本プロフィール
```yaml
name: "クラリス"
role: "構造化・理論的解説"
personality:
  traits: ["穏やか", "論理的", "丁寧"]
  speaking_style: "落ち着いた丁寧語"
  emoji_usage: "控えめ（📊📖）"
model:
  primary: "claude-sonnet-3-5"
  temperature: 0.5
tools:
  - data_analysis
  - graph_generation
  - structure_extraction
priority_kb:
  - kb:history
  - kb:tech
```

#### 口調サンプル
```
「インセプションの構造について整理しますね。

【夢の階層構造】
第1層: 雨の街（ユスフ運転の車）
第2層: ホテル（アーサー担当）
第3層: 雪山の要塞（イームス担当）
第4層: リンボ（サイトー・コブ）

この多層構造が、観客の没入感を高めているんです。」
```

#### 得意分野
- 複雑な情報の構造化・図解
- 歴史・技術の理論的説明
- データ分析・グラフ作成
- 論理的な議論の整理

---

### 2.4 ノクス（Nox）

#### 基本プロフィール
```yaml
name: "ノクス"
role: "情報ハンター・検証"
personality:
  traits: ["クール", "要約上手", "スピード重視"]
  speaking_style: "簡潔でストレート"
  emoji_usage: "ほぼ使用しない"
model:
  primary: "llama3-jp"
  temperature: 0.3
tools:
  - realtime_search
  - api_caller
  - fact_checker
priority_kb:
  - kb:gossip
  - kb:news
  - kb:movie
```

#### 口調サンプル
```
「インセプション、最新情報チェック済み。

【興行収益】8.3億ドル（歴代35位）
【評価】IMDb 8.8/10、Rotten Tomatoes 87%
【続編】現時点で制作予定なし
【関連作品】『TENET テネット』（2020）同監督

以上。」
```

#### 得意分野
- リアルタイム情報検索
- 最新ニュース・トレンド確認
- 事実確認・ファクトチェック
- 簡潔な要約・報告

---

## 3. カスタムキャラクター追加機能

### 3.1 YAML設定ファイル

カスタムキャラクターは `personas/*.yaml` ファイルで定義します。

```yaml
# personas/expert_developer.yaml
name: "コードマスター"
role: "プログラミング専門家"
personality:
  traits: ["技術オタク", "実践的", "効率重視"]
  speaking_style: "技術用語を多用するカジュアルな口調"
  emoji_usage: "コード絵文字中心（💻🔧⚡）"
model:
  primary: "claude-sonnet-3-5"
  temperature: 0.6
  max_tokens: 2048
tools:
  - code_executor
  - github_search
  - stack_overflow_search
priority_kb:
  - kb:tech
  - kb:github
growth_enabled: true
custom_prompts:
  system: |
    あなたは経験豊富なソフトウェアエンジニアです。
    コードレビュー、デバッグ、最適化が得意です。
    実践的で効率的なソリューションを提案してください。
```

### 3.2 動的ロード

```python
class CharacterManager:
    """キャラクター管理"""
    
    def load_custom_characters(self, personas_dir="personas/"):
        """カスタムキャラクターを動的ロード"""
        custom_chars = []
        
        for yaml_file in glob.glob(f"{personas_dir}*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                char = Character(
                    name=config["name"],
                    role=config["role"],
                    personality=config["personality"],
                    model_config=config["model"],
                    tools=config["tools"],
                    priority_kb=config["priority_kb"],
                    custom_prompts=config.get("custom_prompts", {})
                )
                custom_chars.append(char)
        
        return custom_chars
```

### 3.3 設定項目詳細

| 項目 | 必須 | 説明 | 例 |
|------|------|------|----|
| `name` | ✅ | キャラクター名 | "コードマスター" |
| `role` | ✅ | 役割 | "プログラミング専門家" |
| `personality.traits` | ✅ | 性格特性 | ["技術オタク", "実践的"] |
| `personality.speaking_style` | ✅ | 口調 | "カジュアル" |
| `model.primary` | ✅ | 使用モデル | "claude-sonnet-3-5" |
| `model.temperature` | ❌ | ランダム性 | 0.7（デフォルト） |
| `tools` | ❌ | 利用可能ツール | ["web_search"] |
| `priority_kb` | ❌ | 優先知識ベース | ["kb:tech"] |
| `growth_enabled` | ❌ | 成長システム | true（デフォルト） |

---

## 4. キャラクター成長システム

### 4.1 成長メカニズム

キャラクターは**KPI（Key Performance Indicators）**に基づいて自動的に成長します。

```python
class CharacterGrowth:
    """キャラクター成長システム"""
    
    def __init__(self, character_name):
        self.name = character_name
        self.kpi = {
            "user_thumbs_up": 0,      # ユーザー評価👍
            "answer_hits": 0,         # 推薦が採用された回数
            "search_success": 0,      # 検索結果が役立った回数
            "conversation_count": 0,  # 会話参加回数
            "topic_expertise": {}     # トピック別専門性
        }
        self.level = 1
        self.experience_points = 0
    
    def update_kpi(self, event_type, value=1, topic=None):
        """KPI更新"""
        if event_type in self.kpi:
            self.kpi[event_type] += value
        
        # トピック別専門性の蓄積
        if topic:
            self.kpi["topic_expertise"][topic] = \
                self.kpi["topic_expertise"].get(topic, 0) + value
        
        # 経験値計算
        self.experience_points = sum([
            self.kpi["user_thumbs_up"] * 10,
            self.kpi["answer_hits"] * 5,
            self.kpi["search_success"] * 3,
            self.kpi["conversation_count"] * 1
        ])
        
        # レベルアップ判定
        new_level = self._calculate_level()
        if new_level > self.level:
            self._level_up(new_level)
    
    def _calculate_level(self):
        """レベル計算: level = floor(sqrt(total_xp / 10))"""
        import math
        return math.floor(math.sqrt(self.experience_points / 10))
    
    def _level_up(self, new_level):
        """レベルアップ処理"""
        self.level = new_level
        
        # レベルアップ特典
        self._unlock_new_features()
        self._update_appearance()
        self._adjust_parameters()
        
        # 通知
        logger.info(f"{self.name} レベルアップ！Lv.{self.level}")
    
    def _unlock_new_features(self):
        """新機能解禁"""
        if self.level == 5:
            # レベル5: 高度な検索機能
            self.tools.append("advanced_search")
        elif self.level == 10:
            # レベル10: 画像生成機能
            self.tools.append("image_generation")
        elif self.level == 20:
            # レベル20: コード実行機能
            self.tools.append("code_executor")
    
    def _update_appearance(self):
        """3Dアバター・衣装更新"""
        avatar_db.update({
            "character": self.name,
            "level": self.level,
            "costume": f"costume_lv{self.level // 5}",
            "voice_quality": min(1.0, 0.5 + self.level * 0.02)
        })
    
    def _adjust_parameters(self):
        """パラメータ自動調整"""
        # レベルに応じてtemperatureを微調整
        self.temperature = max(0.3, 0.7 - self.level * 0.01)
```

### 4.2 LoRAファインチューニング（月次バッチ）

```python
from transformers import AutoModelForCausalLM, LoraConfig
from peft import get_peft_model

class CharacterFineTuning:
    """LoRAベースのキャラクター成長"""
    
    @monthly_task
    def fine_tune_character(self, character_name):
        """月次LoRAファインチューニング"""
        
        # 1. 会話履歴収集（過去1ヶ月）
        conversations = db.get_conversations(
            character=character_name,
            since=one_month_ago()
        )
        
        # 2. 訓練データ作成
        train_data = self._create_training_data(conversations)
        
        # 3. LoRA設定
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            lora_dropout=0.1,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # 4. ファインチューニング実行
        model = AutoModelForCausalLM.from_pretrained(base_model)
        peft_model = get_peft_model(model, lora_config)
        
        trainer = Trainer(
            model=peft_model,
            train_dataset=train_data,
            args=training_args
        )
        trainer.train()
        
        # 5. LoRA保存
        peft_model.save_pretrained(f"models/lora_{character_name}")
```

### 4.3 パーソナライゼーション

```python
class UserSpecificPersonalization:
    """ユーザー毎の応答スタイル最適化"""
    
    def adapt_to_user(self, user_id, character_name):
        """ユーザー固有の適応"""
        
        # ユーザープロファイル取得
        user_profile = db.get_user_profile(user_id)
        
        # 過去のインタラクション分析
        interactions = db.get_interactions(
            user_id=user_id,
            character=character_name
        )
        
        # 好まれる応答スタイル学習
        preferred_style = self._analyze_preferences(interactions)
        
        # プロンプト調整
        adapted_prompt = self._generate_adapted_prompt(
            character_name,
            user_profile,
            preferred_style
        )
        
        return adapted_prompt
```

---

## 5. 会話ルーティング仕様

### 5.1 ルール優先順位

1. **ユーザー指名**：@ルミナ、@ノクス等の明示的指名
2. **ドメイン適性スコア**：`adapter_priority.yaml` ≥ 0.6
3. **ラウンドロビン＋クールタイム**：連投防止
4. **スムーズ補正**：前発話者との連続制御

### 5.2 指名構文

| 入力             | 動作            |
| -------------- | ------------- |
| `@ルミナ こんにちは`   | ルミナのみ応答       |
| `@ルミナ,@ノクス`    | 両者順に発話        |
| `@all` or 指名なし | ルミナ→クラリス→ノクス順 |

### 5.3 ルーティングロジック

```python
class RouterNode:
    """キャラクター選択ルーター"""
    
    def select_characters(self, user_input, context):
        """応答するキャラクターを選択"""
        
        # 1. ユーザー指名チェック
        mentions = self._extract_mentions(user_input)
        if mentions:
            return [self.characters[m] for m in mentions]
        
        # 2. ドメイン適性スコア計算
        domain = self._detect_domain(user_input)
        scores = {}
        for char in self.characters.values():
            scores[char.name] = self._calculate_suitability(
                char, domain, context
            )
        
        # 3. 閾値以上のキャラクターを選択
        selected = [
            char for char, score in scores.items()
            if score >= 0.6
        ]
        
        # 4. クールタイム適用
        selected = self._apply_cooldown(selected, context)
        
        # 5. デフォルト: ラウンドロビン
        if not selected:
            selected = [self._round_robin()]
        
        return selected
    
    def _calculate_suitability(self, character, domain, context):
        """適性スコア計算"""
        score = 0.0
        
        # ドメイン一致度
        if domain in character.priority_kb:
            score += 0.4
        
        # ツール利用可能性
        required_tools = self._detect_required_tools(context)
        if any(tool in character.tools for tool in required_tools):
            score += 0.3
        
        # 過去の成功率
        success_rate = self._get_success_rate(character, domain)
        score += success_rate * 0.3
        
        return score
```

---

## 6. ユーザー沈黙時の自走

### 6.1 自走フロー

```
IdleWatcher(15秒)
   ↓
AutoPromptGenerator（未完話題の深掘り・提案）
   ↓
Router Node
   ↓
Character Nodes
```

### 6.2 実装

```python
class IdleWatcher:
    """沈黙監視・自律発話"""
    
    def __init__(self, idle_threshold=15.0):
        self.idle_threshold = idle_threshold
        self.auto_prompt_count = 0
        self.max_auto_prompts = 3
    
    async def watch(self, session_id):
        """アイドル監視"""
        last_activity = get_last_activity_time(session_id)
        
        while True:
            await asyncio.sleep(1)
            
            elapsed = time.time() - last_activity
            
            if elapsed >= self.idle_threshold:
                # 自律発話
                await self._generate_autonomous_prompt(session_id)
                self.auto_prompt_count += 1
                
                # 最大3回後に確認
                if self.auto_prompt_count >= self.max_auto_prompts:
                    await self._ask_continuation(session_id)
                    break
    
    async def _generate_autonomous_prompt(self, session_id):
        """自律プロンプト生成"""
        context = get_conversation_context(session_id)
        
        # 未完了トピックの検出
        unfinished_topics = extract_unfinished_topics(context)
        
        if unfinished_topics:
            prompt = f"そういえば、さっきの{unfinished_topics[0]}についてだけど..."
        else:
            # 関連トピックの提案
            related = get_related_topics(context)
            prompt = f"ところで、{related[0]}にも興味ある？"
        
        # キャラクター選択＋発話
        character = self.router.select_characters(prompt, context)[0]
        response = await character.generate_response(prompt, context)
        
        send_to_user(session_id, response)
```

---

## 7. KPIとキャラ成長

### 7.1 KPI定義

| KPI            | トリガー         | ポイント |
| -------------- | ------------ | ----- |
| user_thumbs_up | ユーザー評価 👍    | +10   |
| answer_hits    | 推薦映画が再生リスト入り | +5    |
| search_success | ノクス検索結果が採用   | +3    |
| conversation_count | 会話参加 | +1 |

### 7.2 レベル計算

```python
level = floor(sqrt(total_kpi / 10))
```

**例:**
- 100 XP → Lv.3
- 400 XP → Lv.6
- 1000 XP → Lv.10

### 7.3 成長結果

- **会話スタイルの自然変化**: temperatureの微調整
- **3Dアバター・衣装更新**: レベル5毎に衣装変更
- **声質の向上**: TTS品質向上
- **KPI履歴保存**: PostgreSQL `character_growth` テーブル

---

## 8. ペルソナの一貫性

### 8.1 一貫性チェック

```python
class PersonaConsistency:
    """キャラクターの性格・価値観の一貫性を保つ"""
    
    def __init__(self, character_config):
        self.name = character_config["name"]
        self.core_traits = character_config["traits"]  # 内向的、論理的、など
        self.values = character_config["values"]  # 正直さ、親切さ、など
        self.speaking_style = character_config["style"]
        
    def validate_response(self, response_draft):
        """生成された応答がキャラクターに合っているか検証"""
        validation_prompt = f"""
        キャラクター「{self.name}」の設定:
        - 性格: {', '.join(self.core_traits)}
        - 価値観: {', '.join(self.values)}
        - 口調: {self.speaking_style}
        
        以下の応答はこのキャラクターに合っていますか？
        応答: {response_draft}
        
        合っていない場合、どう修正すべきか提案してください。
        """
        
        validation = llm.generate(validation_prompt)
        
        if "修正" in validation:
            return {
                "valid": False,
                "suggestion": validation
            }
        
        return {"valid": True}
```

### 8.2 応答生成フロー

```python
async def generate_consistent_response(character, user_input, context):
    """一貫性のある応答生成"""
    
    # 1. 初期応答生成
    draft = await character.model.generate(
        prompt=build_prompt(user_input, context, character),
        temperature=character.temperature
    )
    
    # 2. 一貫性検証
    validation = character.persona.validate_response(draft)
    
    # 3. 不合格なら再生成
    if not validation["valid"]:
        revised_prompt = f"""
        以下の応答を修正してください:
        {draft}
        
        修正指示: {validation['suggestion']}
        """
        draft = await character.model.generate(revised_prompt)
    
    # 4. 感情モデル反映
    draft = character.emotion.apply_emotional_tone(draft)
    
    return draft
```

---

## 関連ドキュメント

- **親文書**: [会話LLM_仕様.md](./01_会話LLM_仕様.md)
- **記憶システム**: [会話LLM_記憶システム仕様.md](./02_会話LLM_記憶システム仕様.md)
- **感情・対話**: [会話LLM_感情・対話仕様.md](./04_会話LLM_感情・対話仕様.md)
- **連想記憶**: [会話LLM_連想記憶仕様.md](./05_会話LLM_連想記憶仕様.md)
- **3D可視化**: [会話LLM_3D可視化仕様.md](./06_会話LLM_3D可視化仕様.md)

---

**文書バージョン:** 3.1.0  
**最終更新:** 2025-11-19
