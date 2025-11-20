# 会話LLM 感情・対話仕様書

**バージョン:** 3.1.0  
**最終更新:** 2025-11-19  
**親文書:** [会話LLM_仕様.md](./01_会話LLM_仕様.md)

---

## 目次

1. [概要](#1-概要)
2. [感情モデル](#2-感情モデル)
3. [対話スタイルの動的調整](#3-対話スタイルの動的調整)
4. [自己省察](#4-自己省察)
5. [対話の一貫性](#5-対話の一貫性)
6. [待ち時間の自然な埋め方](#6-待ち時間の自然な埋め方)
7. [トピック追跡とスムーズな転換](#7-トピック追跡とスムーズな転換)

---

## 1. 概要

人間らしい対話には**感情の理解と表現**、**対話スタイルの適応**、**自己省察能力**が不可欠です。このドキュメントでは、会話LLMシステムにおける感情モデルと対話品質管理の仕様を定義します。

### 1.1 設計思想

- **共感性**: ユーザーの感情を理解し、適切に応答
- **適応性**: ユーザーの特性に合わせて対話スタイルを調整
- **一貫性**: 矛盾のない対話を維持
- **自然性**: 人間らしいタイミング・間の取り方

---

## 2. 感情モデル

### 2.1 Plutchikの8基本感情

会話LLMシステムは**Plutchikの感情の輪モデル**を基盤に8基本感情を実装します。

```python
class EmotionalState:
    """
    各キャラクターの感情状態を管理
    Plutchikの感情の輪モデルを基盤に8基本感情を実装
    """
    def __init__(self, character_name):
        self.character = character_name
        # 8基本感情: 喜び、信頼、恐れ、驚き、悲しみ、嫌悪、怒り、期待
        self.emotions = {
            "joy": 0.5,        # 喜び
            "trust": 0.5,      # 信頼
            "fear": 0.0,       # 恐れ
            "surprise": 0.0,   # 驚き
            "sadness": 0.0,    # 悲しみ
            "disgust": 0.0,    # 嫌悪
            "anger": 0.0,      # 怒り
            "anticipation": 0.5 # 期待
        }
        self.mood_history = []  # 気分の履歴
        
    def update_from_conversation(self, user_input, context):
        """会話から感情を更新"""
        # ユーザーの感情を分析
        user_emotion = analyze_sentiment(user_input)
        
        # 共感的応答(ミラーリング)
        if user_emotion["valence"] < 0:  # ネガティブ
            self.emotions["sadness"] += 0.2
            self.emotions["trust"] += 0.1  # 寄り添う
        else:  # ポジティブ
            self.emotions["joy"] += 0.2
            self.emotions["anticipation"] += 0.1
        
        # 感情の自然な減衰
        self._decay_emotions()
        
        # 履歴に記録
        self.mood_history.append({
            "timestamp": now(),
            "emotions": self.emotions.copy(),
            "trigger": user_input[:50]
        })
    
    def _decay_emotions(self, rate=0.1):
        """感情の自然な減衰(ホメオスタシス)"""
        for emotion in self.emotions:
            # 中立値(0.5)に向かって減衰
            if self.emotions[emotion] > 0.5:
                self.emotions[emotion] -= rate
            elif self.emotions[emotion] < 0.5:
                self.emotions[emotion] += rate
    
    def get_dominant_emotion(self):
        """現在の支配的な感情を取得"""
        return max(self.emotions, key=self.emotions.get)
    
    def generate_emotional_modifier(self):
        """感情に基づくプロンプト修飾子"""
        dominant = self.get_dominant_emotion()
        modifiers = {
            "joy": "明るく前向きなトーンで",
            "sadness": "共感的で優しいトーンで",
            "anger": "やや強めの言葉選びで",
            "surprise": "好奇心を持って",
            "trust": "温かく支持的なトーンで"
        }
        return modifiers.get(dominant, "自然なトーンで")
```

### 2.2 感情状態の遷移

```
[中立状態 0.5]
     ↓
ユーザー入力分析
     ↓
┌─────────────┐
│ ポジティブ?│
└─────────────┘
  ↓Yes    ↓No
Joy↑    Sadness↑
Trust↑  
     ↓
自然な減衰(中立へ)
```

### 2.3 感情履歴の活用

```python
def analyze_mood_trend(self):
    """気分の推移を分析"""
    if len(self.mood_history) < 5:
        return "neutral"
    
    recent_moods = self.mood_history[-5:]
    avg_valence = sum(
        m["emotions"]["joy"] - m["emotions"]["sadness"]
        for m in recent_moods
    ) / len(recent_moods)
    
    if avg_valence > 0.2:
        return "positive_trend"
    elif avg_valence < -0.2:
        return "negative_trend"
    else:
        return "stable"
```

---

## 3. 対話スタイルの動的調整

### 3.1 スタイルパラメータ

```python
class AdaptiveDialogueStyle:
    """
    ユーザーの特性に合わせて対話スタイルを動的に調整
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.style_params = {
            "formality": 0.5,      # 0=カジュアル, 1=フォーマル
            "verbosity": 0.5,      # 0=簡潔, 1=詳細
            "humor": 0.5,          # 0=真面目, 1=ユーモラス
            "technical_level": 0.5, # 0=平易, 1=専門的
            "empathy": 0.7,        # 共感レベル
            "proactivity": 0.5     # 0=受動的, 1=積極的
        }
    
    def learn_from_feedback(self, user_feedback):
        """ユーザーフィードバックから学習"""
        if "もっと簡単に" in user_feedback or "わかりにくい" in user_feedback:
            self.style_params["technical_level"] -= 0.1
            self.style_params["verbosity"] -= 0.1
        
        if "詳しく" in user_feedback or "もっと教えて" in user_feedback:
            self.style_params["verbosity"] += 0.1
        
        if "カジュアルに" in user_feedback:
            self.style_params["formality"] -= 0.1
        
        if "もっと丁寧に" in user_feedback:
            self.style_params["formality"] += 0.1
        
        # パラメータを0-1範囲に制限
        for key in self.style_params:
            self.style_params[key] = max(0.0, min(1.0, self.style_params[key]))
        
        # 永続化
        self._save_to_profile()
    
    def generate_style_prompt(self):
        """スタイルパラメータからプロンプト生成"""
        formality = "丁寧語" if self.style_params["formality"] > 0.6 else "カジュアル"
        length = "簡潔に" if self.style_params["verbosity"] < 0.4 else "詳しく"
        technical = "専門的な用語を使って" if self.style_params["technical_level"] > 0.6 else "わかりやすく"
        
        return f"{formality}な口調で、{length}{technical}説明してください。"
    
    def _save_to_profile(self):
        """ユーザープロファイルに保存"""
        db.execute("""
            UPDATE user_profiles
            SET dialogue_style = ?
            WHERE user_id = ?
        """, (json.dumps(self.style_params), self.user_id))
```

### 3.2 適応学習フロー

```
ユーザー発言
     ↓
応答生成
     ↓
ユーザー反応分析
     ↓
┌──────────────┐
│ 満足度判定   │
└──────────────┘
  ↓低        ↓高
パラメータ調整  維持
  ↓
永続化
```

---

## 4. 自己省察

### 4.1 省察メカニズム

```python
class SelfReflection:
    """
    AIキャラクターが自分の応答を振り返り、改善する
    """
    def reflect_on_conversation(self, conversation_history):
        """
        会話を振り返り、メタ認知的な洞察を得る
        """
        reflection_prompt = f"""
        以下の会話を振り返ってください:
        {format_conversation(conversation_history)}
        
        次の観点で分析してください:
        1. ユーザーの本当のニーズを理解できたか
        2. 自分の回答は適切だったか
        3. より良い対応方法はなかったか
        4. 今後に活かせる学びは何か
        """
        
        reflection = llm.generate(reflection_prompt)
        
        # 省察結果を記憶
        self._store_reflection(reflection)
        
        return reflection
    
    def _store_reflection(self, reflection):
        """省察を長期記憶に保存"""
        vector_db.upsert(
            namespace="self_reflection",
            vectors=[{
                "id": f"reflection_{now()}",
                "values": create_embedding(reflection),
                "metadata": {
                    "type": "self_reflection",
                    "timestamp": now(),
                    "content": reflection
                }
            }]
        )
    
    def retrieve_past_lessons(self, current_situation):
        """過去の学びを検索"""
        query_embedding = create_embedding(current_situation)
        
        past_reflections = vector_db.query(
            namespace="self_reflection",
            vector=query_embedding,
            top_k=3
        )
        
        return [r["metadata"]["content"] for r in past_reflections]
```

### 4.2 省察トリガー

- **定期実行**: 10ターン毎
- **低評価時**: ユーザー👎
- **複雑な対話終了時**: 長時間セッション終了後

---

## 5. 対話の一貫性

### 5.1 矛盾検出

```python
class DialogueCoherence:
    """
    対話の一貫性を維持し、矛盾を防ぐ
    """
    def check_consistency(self, new_statement, conversation_history):
        """新しい発言が過去の発言と矛盾しないか確認"""
        # 過去の類似発言を検索
        similar_statements = vector_db.query(
            vector=create_embedding(new_statement),
            namespace=f"user:{user_id}",
            top_k=10,
            threshold=0.7
        )
        
        # 矛盾チェック
        for past_stmt in similar_statements:
            contradiction_score = self._detect_contradiction(
                new_statement,
                past_stmt["content"]
            )
            
            if contradiction_score > 0.8:
                return {
                    "consistent": False,
                    "contradicts": past_stmt["content"],
                    "suggestion": self._generate_clarification(
                        new_statement, past_stmt
                    )
                }
        
        return {"consistent": True}
    
    def _detect_contradiction(self, stmt1, stmt2):
        """2つの発言の矛盾度を計算"""
        prompt = f"""
        以下の2つの発言は矛盾していますか?0(矛盾なし)から1(完全に矛盾)で評価してください。
        
        発言1: {stmt1}
        発言2: {stmt2}
        
        数値のみ回答してください。
        """
        return float(llm.generate(prompt))
    
    def _generate_clarification(self, new_stmt, past_stmt):
        """矛盾を解消する修正案生成"""
        prompt = f"""
        以下の2つの発言は矛盾しています。
        
        新しい発言: {new_stmt}
        過去の発言: {past_stmt["content"]}
        
        矛盾を解消する修正案を提示してください。
        """
        return llm.generate(prompt)
```

### 5.2 一貫性チェックフロー

```
応答生成
     ↓
一貫性チェック
     ↓
┌──────────────┐
│ 矛盾あり?   │
└──────────────┘
  ↓Yes    ↓No
修正案生成  承認
  ↓
再生成
```

---

## 6. 待ち時間の自然な埋め方

### 6.1 タイミング制御

```python
class NaturalPacing:
    """
    人間らしい待ち時間・タイミングの制御
    """
    def add_thinking_indicator(self, complexity):
        """
        複雑な質問には「考え中」のような表現を追加
        """
        if complexity > 0.7:
            return random.choice([
                "うーん、ちょっと考えさせて...",
                "面白い質問ですね。少し整理させてください。",
                "なるほど...(考え中)"
            ])
        return None
    
    def calculate_response_delay(self, message_length):
        """
        メッセージの長さに応じた適切な待ち時間
        人間が読み、考え、タイピングする時間を模擬
        """
        # 読む時間(250文字/分)
        read_time = message_length / 250 * 60
        
        # 考える時間(1-3秒)
        think_time = random.uniform(1, 3)
        
        # タイピング時間(40文字/秒)
        type_time = message_length / 40
        
        total_delay = read_time + think_time + (type_time * 0.3)
        
        return min(total_delay, 10.0)  # 最大10秒
    
    async def stream_with_natural_pace(self, response_text):
        """自然なペースでストリーミング"""
        words = response_text.split()
        
        for i, word in enumerate(words):
            # 単語毎に送信
            yield word + " "
            
            # 句読点の後に自然な間
            if word.endswith(("。", "!", "?")):
                await asyncio.sleep(random.uniform(0.3, 0.6))
            elif word.endswith(("、", "、")):
                await asyncio.sleep(random.uniform(0.1, 0.3))
            else:
                await asyncio.sleep(random.uniform(0.05, 0.15))
```

### 6.2 複雑度判定

```python
def calculate_complexity(user_input):
    """質問の複雑度を計算"""
    score = 0.0
    
    # 長さ
    score += min(len(user_input) / 500, 0.3)
    
    # 疑問文の数
    questions = user_input.count("?") + user_input.count("?")
    score += min(questions * 0.2, 0.3)
    
    # 専門用語の数
    technical_terms = count_technical_terms(user_input)
    score += min(technical_terms * 0.1, 0.4)
    
    return min(score, 1.0)
```

---

## 7. トピック追跡とスムーズな転換

### 7.1 トピック追跡

```python
class TopicTracker:
    """
    話題の流れを追跡し、自然な転換を支援
    """
    def __init__(self):
        self.topic_stack = []  # 話題スタック
        self.current_topic = None
        
    def detect_topic_shift(self, user_input, context):
        """話題の転換を検出"""
        current_topics = extract_topics(context[-3:])  # 直近3ターン
        new_topics = extract_topics(user_input)
        
        overlap = set(current_topics) & set(new_topics)
        shift_score = 1.0 - (len(overlap) / max(len(current_topics), 1))
        
        if shift_score > 0.6:  # 大きな転換
            return {
                "shifted": True,
                "old_topic": self.current_topic,
                "new_topic": new_topics[0] if new_topics else None,
                "transition_needed": True
            }
        
        return {"shifted": False}
    
    def generate_transition_phrase(self, old_topic, new_topic):
        """自然な話題転換のフレーズ"""
        transitions = [
            f"{old_topic}の話から変わりますが、{new_topic}について...",
            f"ところで、{new_topic}といえば...",
            f"{new_topic}の話に移りますね。"
        ]
        return random.choice(transitions)
    
    def suggest_topic_return(self):
        """過去の未完了トピックへの復帰を提案"""
        if len(self.topic_stack) > 1:
            abandoned_topic = self.topic_stack[-2]
            return f"そういえば、さっきの{abandoned_topic}の話に戻りますが..."
        return None
```

### 7.2 トピック抽出

```python
def extract_topics(text_list):
    """テキストからトピックを抽出"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    # TF-IDFでキーワード抽出
    vectorizer = TfidfVectorizer(max_features=5)
    tfidf_matrix = vectorizer.fit_transform(text_list)
    
    keywords = vectorizer.get_feature_names_out()
    return list(keywords)
```

### 7.3 スムーズな転換フロー

```
ユーザー入力
     ↓
話題検出
     ↓
┌──────────────┐
│ 転換あり?   │
└──────────────┘
  ↓Yes    ↓No
転換フレーズ  通常応答
  ↓
新トピックスタックに追加
  ↓
応答生成
```

---

## 関連ドキュメント

- **親文書**: [会話LLM_仕様.md](./01_会話LLM_仕様.md)
- **記憶システム**: [会話LLM_記憶システム仕様.md](./02_会話LLM_記憶システム仕様.md)
- **キャラクター**: [会話LLM_キャラクター仕様.md](./03_会話LLM_キャラクター仕様.md)
- **連想記憶**: [会話LLM_連想記憶仕様.md](./05_会話LLM_連想記憶仕様.md)
- **3D可視化**: [会話LLM_3D可視化仕様.md](./06_会話LLM_3D可視化仕様.md)

---

**文書バージョン:** 3.1.0  
**最終更新:** 2025-11-19
