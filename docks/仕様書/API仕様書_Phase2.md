# LlmMultiChat3 API仕様書（Phase 2版）

**バージョン**: 2.0  
**対象フェーズ**: Phase 2（セキュリティ・品質向上完了版）  
**最終更新**: 2025-11-13

---

## 目次

1. [API概要](#1-api概要)
2. [認証・認可](#2-認証認可)
3. [エンドポイント一覧](#3-エンドポイント一覧)
4. [入力検証仕様](#4-入力検証仕様)
5. [エラーレスポンス形式](#5-エラーレスポンス形式)
6. [メトリクスAPI](#6-メトリクスapi)
7. [レート制限](#7-レート制限)
8. [セキュリティヘッダー](#8-セキュリティヘッダー)

---

## 1. API概要

### 1.1 基本情報

- **ベースURL**: `http://localhost:8000` (開発環境)
- **プロトコル**: HTTP/1.1
- **データ形式**: JSON (UTF-8)
- **認証方式**: JWT Bearer Token（Phase 3で実装予定）
- **API バージョニング**: URL Prefix (`/api/v1/`)

### 1.2 Phase 2での変更点

| 項目 | Phase 1 | Phase 2 |
|-----|---------|---------|
| 入力検証 | なし | XSS/SQLインジェクション/パストラバーサル対策 |
| エラーハンドリング | 汎用エラー | カスタム例外18種類 |
| ログ | 標準出力 | 構造化ログ（JSON形式） |
| メトリクス | なし | メトリクス収集API追加 |
| リトライ | なし | 最大3回リトライ（指数バックオフ） |
| キャッシュ | なし | Redis 2層キャッシュ |

---

## 2. 認証・認可

### 2.1 現在の状態（Phase 2）

**認証: なし**  
Phase 2では認証機能は未実装。ローカル環境でのみ動作。

### 2.2 Phase 3での実装予定

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

**レスポンス**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 3. エンドポイント一覧

### 3.1 会話API

#### 3.1.1 会話開始

```http
POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "session_12345",
  "user_input": "こんにちは",
  "context": {
    "user_id": "user_001",
    "timestamp": "2025-11-13T17:00:00Z"
  }
}
```

**リクエストパラメータ**:

| パラメータ | 型 | 必須 | 検証ルール | 説明 |
|-----------|---|------|-----------|------|
| `session_id` | string | ✅ | 3-100文字、英数字・ハイフン・アンダースコア | セッションID |
| `user_input` | string | ✅ | 1-10000文字、XSS対策済み | ユーザー入力 |
| `context` | object | ❌ | - | 追加コンテキスト |

**レスポンス（成功）**:
```json
{
  "status": "success",
  "session_id": "session_12345",
  "response": "こんにちは！何かお手伝いできることはありますか？",
  "metadata": {
    "llm_node": "lumina",
    "processing_time_ms": 234,
    "cached": false,
    "retry_count": 0
  },
  "timestamp": "2025-11-13T17:00:01Z"
}
```

**レスポンス（エラー）**:
```json
{
  "status": "error",
  "error_type": "InputValidationError",
  "error_code": "E2001",
  "error_message": "Potential XSS attack detected",
  "field": "user_input",
  "timestamp": "2025-11-13T17:00:01Z"
}
```

#### 3.1.2 会話履歴取得

```http
GET /api/v1/chat/history?session_id=session_12345&limit=50
```

**クエリパラメータ**:

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|------|-----------|------|
| `session_id` | string | ✅ | - | セッションID |
| `limit` | integer | ❌ | 50 | 取得件数（最大100） |
| `offset` | integer | ❌ | 0 | オフセット |

**レスポンス**:
```json
{
  "status": "success",
  "session_id": "session_12345",
  "history": [
    {
      "turn": 1,
      "speaker": "user",
      "message": "こんにちは",
      "timestamp": "2025-11-13T17:00:00Z"
    },
    {
      "turn": 2,
      "speaker": "lumina",
      "message": "こんにちは！何かお手伝いできることはありますか？",
      "timestamp": "2025-11-13T17:00:01Z"
    }
  ],
  "total_count": 2,
  "has_more": false
}
```

### 3.2 記憶API

#### 3.2.1 記憶保存

```http
POST /api/v1/memory/store
Content-Type: application/json

{
  "session_id": "session_12345",
  "memory_type": "mid_term",
  "key": "user_preference",
  "value": {
    "theme": "dark",
    "language": "ja"
  },
  "ttl_hours": 24
}
```

**リクエストパラメータ**:

| パラメータ | 型 | 必須 | 検証ルール | 説明 |
|-----------|---|------|-----------|------|
| `session_id` | string | ✅ | セッションID検証 | セッションID |
| `memory_type` | string | ✅ | `short_term`, `mid_term`, `long_term` | 記憶タイプ |
| `key` | string | ✅ | 1-256文字 | キー |
| `value` | any | ✅ | JSON形式 | 値 |
| `ttl_hours` | integer | ❌ | 1-720（30日） | TTL（時間） |

**レスポンス**:
```json
{
  "status": "success",
  "memory_type": "mid_term",
  "key": "user_preference",
  "cached_in_redis": true,
  "expires_at": "2025-11-14T17:00:00Z"
}
```

#### 3.2.2 記憶取得

```http
GET /api/v1/memory/retrieve?session_id=session_12345&memory_type=mid_term&key=user_preference
```

**レスポンス**:
```json
{
  "status": "success",
  "memory_type": "mid_term",
  "key": "user_preference",
  "value": {
    "theme": "dark",
    "language": "ja"
  },
  "cached": true,
  "cache_hit_from": "redis"
}
```

### 3.3 メトリクスAPI

#### 3.3.1 メトリクスサマリー取得

```http
GET /api/v1/metrics/summary
```

**レスポンス**:
```json
{
  "status": "success",
  "metrics": {
    "llm_calls": {
      "total": 1234,
      "avg_duration_ms": 245.3,
      "max_duration_ms": 890,
      "min_duration_ms": 120,
      "success_rate": 0.987
    },
    "cache": {
      "hit_rate": 0.92,
      "redis_hits": 850,
      "redis_misses": 74,
      "json_fallback_count": 12
    },
    "errors": {
      "total": 16,
      "by_type": {
        "LLMCallError": 8,
        "InputValidationError": 5,
        "CacheError": 3
      }
    },
    "retry": {
      "total_retries": 24,
      "avg_retries_per_call": 0.019
    }
  },
  "timestamp": "2025-11-13T17:00:00Z"
}
```

#### 3.3.2 メトリクスエクスポート

```http
GET /api/v1/metrics/export?format=json
```

**クエリパラメータ**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `format` | string | `json` | `json`, `csv`, `prometheus` |
| `start_date` | string (ISO8601) | 7日前 | 開始日時 |
| `end_date` | string (ISO8601) | 現在 | 終了日時 |

**レスポンス（JSON）**:
```json
{
  "status": "success",
  "format": "json",
  "period": {
    "start": "2025-11-06T00:00:00Z",
    "end": "2025-11-13T17:00:00Z"
  },
  "data": {
    "llm_calls": [
      {
        "timestamp": "2025-11-13T16:00:00Z",
        "duration_ms": 234,
        "node": "lumina",
        "success": true
      }
    ]
  }
}
```

**レスポンス（Prometheus）**:
```prometheus
# HELP llm_call_duration_seconds LLM call duration
# TYPE llm_call_duration_seconds histogram
llm_call_duration_seconds_bucket{node="lumina",le="0.1"} 120
llm_call_duration_seconds_bucket{node="lumina",le="0.5"} 850
llm_call_duration_seconds_sum{node="lumina"} 302.4
llm_call_duration_seconds_count{node="lumina"} 1234

# HELP cache_hit_rate Cache hit rate
# TYPE cache_hit_rate gauge
cache_hit_rate{backend="redis"} 0.92
```

### 3.4 ダッシュボードAPI

#### 3.4.1 ダッシュボード生成

```http
POST /api/v1/dashboard/generate
Content-Type: application/json

{
  "filename": "dashboard_20251113.html",
  "include_sections": ["metrics", "errors", "cache"]
}
```

**レスポンス**:
```json
{
  "status": "success",
  "filename": "dashboard_20251113.html",
  "url": "/static/dashboard_20251113.html",
  "generated_at": "2025-11-13T17:00:00Z"
}
```

---

## 4. 入力検証仕様

### 4.1 検証ルール

#### 4.1.1 ユーザー入力検証（`user_input`）

**検証項目**:

| 項目 | 検証内容 | エラーコード |
|-----|---------|-------------|
| 長さ | 1-10000文字 | E2001 |
| XSS検出 | `<script>`, `javascript:`, `on*=`等 | E2002 |
| SQLインジェクション | `'; DROP TABLE`, `UNION SELECT`等 | E2003 |
| パストラバーサル | `../`, `..\\`等 | E2004 |

**Python実装**:
```python
from validators import InputValidator

try:
    validated_input = InputValidator.validate_user_input(user_input)
except InputValidationError as e:
    return {
        "status": "error",
        "error_code": e.error_code,
        "error_message": str(e)
    }
```

#### 4.1.2 セッションID検証

**検証ルール**:
- 長さ: 3-100文字
- 文字種: 英数字、ハイフン（`-`）、アンダースコア（`_`）のみ
- パターン: `^[a-zA-Z0-9_-]{3,100}$`

**例**:
```python
import re

def validate_session_id(session_id: str) -> bool:
    pattern = r'^[a-zA-Z0-9_-]{3,100}$'
    return bool(re.match(pattern, session_id))
```

#### 4.1.3 話者名検証

**検証ルール**:
- 長さ: 1-50文字
- 禁止文字: `<`, `>`, `/`, `\`, `..`

**Python実装**:
```python
from validators import InputValidator

try:
    is_valid = InputValidator.validate_speaker_name(speaker)
except ValidationError as e:
    return {"status": "error", "error_message": str(e)}
```

**実装コード** ([`validators.py:117`](validators.py:117)):
```python
@staticmethod
def validate_speaker_name(speaker: str) -> bool:
    """話者名検証"""
    if not speaker or len(speaker) > 50:
        return False
    
    dangerous_chars = ['<', '>', '/', '\', '..']
    for char in dangerous_chars:
        if char in speaker:
            return False
    
    return True
```

#### 4.1.4 ファイルパス検証（パストラバーサル対策）

**検証項目**:

| 項目 | 検証内容 | エラーコード |
|-----|---------|-------------|
| パストラバーサル | `../`, `..\` 禁止 | E4004 |
| 絶対パス | `/`始まり、`C:`等禁止 | E4005 |
| 拡張子 | 許可リストチェック | E4006 |

**Python実装** ([`validators.py:247`](validators.py:247)):
```python
from validators import InputValidator

try:
    validated_path = InputValidator.validate_file_path(
        filepath,
        allowed_extensions=['.json', '.txt', '.md']
    )
except ValidationError as e:
    return {"status": "error", "error_code": e.error_code}
```

**実装詳細**:
```python
@staticmethod
def validate_file_path(filepath: str, allowed_extensions: Optional[List[str]] = None) -> str:
    """ファイルパス検証（パストラバーサル対策）"""
    if not filepath:
        raise ValidationError("ファイルパスが空です", field="filepath")
    
    # パストラバーサル対策（../ や ..\ を含まない）
    if '..' in filepath:
        raise ValidationError(
            "不正なファイルパスです（パストラバーサル検出）",
            field="filepath",
            error_code="E4004"
        )
    
    # 絶対パス禁止（ルートディレクトリアクセス防止）
    if filepath.startswith('/') or (len(filepath) > 1 and filepath[1] == ':'):
        raise ValidationError(
            "絶対パスは許可されていません",
            field="filepath",
            error_code="E4005"
        )
    
    # 拡張子チェック
    if allowed_extensions:
        if not any(filepath.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                f"許可されていない拡張子です（許可: {', '.join(allowed_extensions)}）",
                field="filepath",
                error_code="E4006"
            )
    
    return filepath
```

#### 4.1.5 キャラクター名検証

**許可リスト**:
```python
ALLOWED_CHARACTERS = ['ルミナ', 'クラリス', 'ノクス', 'Router']
```

**実装** ([`validators.py:295`](validators.py:295)):
```python
@staticmethod
def validate_character_name(character_name: str) -> str:
    """キャラクター名検証"""
    if not character_name:
        raise ValidationError(
            "キャラクター名が空です",
            field="character_name"
        )
    
    if character_name not in ALLOWED_CHARACTERS:
        raise ValidationError(
            f"不正なキャラクター名: {character_name}",
            field="character_name",
            error_code="E4007"
        )
    
    return character_name
```

#### 4.1.6 メタデータ検証

**検証ルール**:
- 型: dict型のみ許可
- キー数: 最大50個
- 値の長さ: 文字列の場合最大1000文字

**実装** ([`validators.py:326`](validators.py:326)):
```python
@staticmethod
def validate_metadata(metadata: dict, max_keys: int = 50, max_value_length: int = 1000) -> dict:
    """メタデータ検証"""
    if not isinstance(metadata, dict):
        raise ValidationError(
            "メタデータは辞書型である必要があります",
            field="metadata"
        )
    
    # キー数チェック
    if len(metadata) > max_keys:
        raise ValidationError(
            f"メタデータのキー数が多すぎます（最大{max_keys}個）",
            field="metadata",
            error_code="E4008"
        )
    
    # 各値の長さチェック
    for key, value in metadata.items():
        if isinstance(value, str) and len(value) > max_value_length:
            raise ValidationError(
                f"メタデータ値が長すぎます: {key}（最大{max_value_length}文字）",
                field="metadata",
                error_code="E4009"
            )
    
    return metadata
```

#### 4.1.7 コマンド検証

**検証ルール**:
- 長さ: 3-100文字
- 文字種: 英数字、ハイフン（`-`）、アンダースコア（`_`）のみ
- パターン: `^[a-zA-Z0-9_-]{3,100}$`

**例**:
```python
import re

def validate_session_id(session_id: str) -> bool:
    pattern = r'^[a-zA-Z0-9_-]{3,100}$'
    return bool(re.match(pattern, session_id))
```

#### 4.1.7 コマンド検証

**許可リスト**:
```python
ALLOWED_COMMANDS = [
    "ls", "pwd", "echo", "cat", "grep",
    "find", "wc", "head", "tail"
]
```

**検証**:
```python
from validators import InputValidator

try:
    InputValidator.validate_command(command)
except ValidationError as e:
    return {"status": "error", "error_message": str(e)}
```

### 4.2 サニタイゼーション

#### 4.2.1 ログ出力サニタイゼーション

**実装** ([`validators.py:382`](validators.py:382)):
```python
@staticmethod
def sanitize_for_log(text: str, max_length: int = 200) -> str:
    """ログ出力用サニタイゼーション（機密情報マスク）"""
    # 長さ制限
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # 機密情報パターンマスク
    text = re.sub(r'(password|pwd)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
    text = re.sub(r'(api[_-]?key)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
    text = re.sub(r'(token|bearer)["\s:=]+([^\s]+)', r'\1=***MASKED***', text, flags=re.IGNORECASE)
    
    return text
```

**マスク対象**:
- パスワード: `password=***`
- APIキー: `api_key=***`
- トークン: `token=***`

**実装**:
```python
from validators import InputValidator

sanitized_log = InputValidator.sanitize_for_log(raw_message)
logger.info(sanitized_log)
```

**例**:
```python
# 入力
raw_message = "User login: password=MySecret123, api_key=sk-abc123"

# 出力
sanitized_log = "User login: password=***, api_key=***"
```

---

## 5. エラーレスポンス形式

### 5.1 エラーレスポンス構造

```json
{
  "status": "error",
  "error_type": "InputValidationError",
  "error_code": "E2002",
  "error_message": "Potential XSS attack detected",
  "field": "user_input",
  "details": {
    "pattern_matched": "<script>",
    "position": 45
  },
  "timestamp": "2025-11-13T17:00:00Z",
  "request_id": "req_abc123"
}
```

### 5.2 エラーコード一覧

#### 5.2.1 検証エラー（E2xxx）

| コード | エラータイプ | 説明 |
|-------|------------|------|
| E2001 | InputValidationError | 入力長さエラー |
| E2002 | InputValidationError | XSS検出 |
| E2003 | InputValidationError | SQLインジェクション検出 |
| E2004 | InputValidationError | パストラバーサル検出 |
| E2005 | SessionValidationError | セッションID不正 |
| E2006 | ValidationError | コマンド不許可 |

#### 5.2.2 記憶エラー（E3xxx）

| コード | エラータイプ | 説明 |
|-------|------------|------|
| E3001 | ShortTermMemoryError | 短期記憶エラー |
| E3002 | MidTermMemoryError | 中期記憶エラー |
| E3003 | LongTermMemoryError | 長期記憶エラー |
| E3004 | CacheError | キャッシュエラー |

#### 5.2.3 LLMエラー（E4xxx）

| コード | エラータイプ | 説明 |
|-------|------------|------|
| E4001 | LLMCallError | LLM呼び出しエラー |
| E4002 | LLMTimeoutError | LLMタイムアウト |
| E4003 | LLMNodeError | LLMノードエラー |
| E4004 | ValidationError | パストラバーサル検出（ファイルパス） |
| E4005 | ValidationError | 絶対パス禁止（ファイルパス） |
| E4006 | ValidationError | 許可されていない拡張子 |
| E4007 | ValidationError | 不正なキャラクター名 |
| E4008 | ValidationError | メタデータキー数超過 |
| E4009 | ValidationError | メタデータ値長さ超過 |

#### 5.2.4 設定エラー（E5xxx）

| コード | エラータイプ | 説明 |
|-------|------------|------|
| E5001 | ConfigError | 設定エラー |
| E5002 | MissingConfigError | 設定欠落 |

### 5.3 HTTPステータスコード

| ステータス | 用途 |
|-----------|------|
| 200 OK | 成功 |
| 400 Bad Request | 入力検証エラー |
| 401 Unauthorized | 認証エラー（Phase 3） |
| 403 Forbidden | 認可エラー（Phase 3） |
| 404 Not Found | リソース未検出 |
| 429 Too Many Requests | レート制限超過（Phase 3） |
| 500 Internal Server Error | サーバーエラー |
| 503 Service Unavailable | サービス一時停止 |

---

## 6. メトリクスAPI

### 6.1 メトリクス種類

#### 6.1.1 LLM呼び出しメトリクス

```python
from metrics import record_llm_call

record_llm_call(
    node_name="lumina",
    duration=0.234,
    success=True,
    retry_count=0
)
```

**収集データ**:
- 呼び出し回数
- 平均処理時間
- 最大処理時間
- 最小処理時間
- 成功率
- リトライ回数

#### 6.1.2 キャッシュメトリクス

```python
from metrics import record_cache_hit, record_cache_miss

record_cache_hit(backend="redis")
record_cache_miss(backend="redis")
```

**収集データ**:
- ヒット率
- Redisヒット数
- Redisミス数
- JSONフォールバック数

#### 6.1.3 記憶操作メトリクス

**実装** ([`metrics.py:108`](metrics.py:108)):
```python
from metrics import MetricsCollector

collector = MetricsCollector()
collector.record_memory_operation(
    operation_type="read",
    duration_ms=12.5,
    success=True
)
```

**収集データ**:
- 総操作数
- 読み込み回数
- 書き込み回数
- エラー数
- 操作別平均時間

**operation_type**: `read`, `write`, `update`, `delete`

#### 6.1.4 LLMフォールバックメトリクス

**実装** ([`metrics.py:93`](metrics.py:93)):
```python
from metrics import MetricsCollector

collector = MetricsCollector()
collector.record_llm_fallback(character="ルミナ")
```

**収集データ**:
- フォールバック総数
- キャラクター別フォールバック数
- タイムスタンプ付き詳細ログ

#### 6.1.5 パフォーマンスレポート

**実装** ([`metrics.py:287`](metrics.py:287)):
```python
from metrics import MetricsCollector

collector = MetricsCollector()
report = collector.get_performance_report()
print(report)
```

**レポート内容**:
- セッション情報（開始・終了時刻、実行時間）
- LLM統計（呼び出し数、平均/中央値/最小/最大時間、エラー数、リトライ数）
- 記憶システム統計（総操作数、読み書き回数、エラー数）
- 会話統計（総ターン数、ユーザー入力数、システム応答数、セッション数）
- キャラクター別応答数
- エラー統計（総エラー数、種別集計）

#### 6.1.6 エラーメトリクス

#### 6.1.6 エラーメトリクス

```python
from metrics import record_error

record_error(
    error_type="InputValidationError",
    error_code="E2002",
    message="XSS detected"
)
```

**収集データ**:
- エラー総数
- エラータイプ別集計
- エラーコード別集計

### 6.2 メトリクス取得API

#### 6.2.1 リアルタイムメトリクス

```http
GET /api/v1/metrics/realtime
```

**レスポンス**:
```json
{
  "status": "success",
  "metrics": {
    "llm_calls_per_minute": 45,
    "cache_hit_rate": 0.92,
    "active_sessions": 12,
    "avg_response_time_ms": 234
  },
  "timestamp": "2025-11-13T17:00:00Z"
}
```

#### 6.2.2 時系列メトリクス

```http
GET /api/v1/metrics/timeseries?metric=llm_call_duration&interval=1h&period=24h
```

**レスポンス**:
```json
{
  "status": "success",
  "metric": "llm_call_duration",
  "interval": "1h",
  "period": "24h",
  "data": [
    {
      "timestamp": "2025-11-13T16:00:00Z",
      "value": 234,
      "count": 150
    },
    {
      "timestamp": "2025-11-13T15:00:00Z",
      "value": 245,
      "count": 142
    }
  ]
}
```

---

## 7. レート制限

### 7.1 Phase 3実装予定

**制限ルール**:
- 会話API: 10リクエスト/分
- メトリクスAPI: 60リクエスト/分
- 記憶API: 100リクエスト/分

**レスポンスヘッダー**:
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699891200
```

**超過時のレスポンス**:
```json
{
  "status": "error",
  "error_type": "RateLimitExceeded",
  "error_code": "E6001",
  "error_message": "Rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30,
  "timestamp": "2025-11-13T17:00:00Z"
}
```

---

## 8. セキュリティヘッダー

### 8.1 Phase 3実装予定

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## 9. WebSocket API（Phase 3実装済み）

### 9.1 接続管理

**実装** ([`api/websocket.py:47`](api/websocket.py:47)):

```python
class ConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """WebSocket接続を受け入れ"""
        await websocket.accept()
        connection_id = user_id or f"guest-{id(websocket)}"
        self.active_connections[connection_id] = websocket
        return connection_id
    
    def disconnect(self, connection_id: str):
        """WebSocket接続を切断"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
```

### 9.2 メッセージ型定義

**サポートメッセージ型**:

| メッセージ型 | 方向 | 説明 |
|-------------|------|------|
| `auth` | Client → Server | 認証リクエスト |
| `auth_response` | Server → Client | 認証結果 |
| `chat` | Client → Server | 会話リクエスト |
| `response` | Server → Client | 会話応答 |
| `typing` | Server → Client | タイピング状態通知 |
| `error` | Server → Client | エラー通知 |
| `disconnect` | Client → Server | 切断通知 |

### 9.3 接続フロー

**1. WebSocket接続**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat");

ws.onopen = () => {
  ws.send(JSON.stringify({
    "type": "auth",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }));
};
```

### 9.4 認証（実装済み）

**認証メッセージ** ([`api/websocket.py:211`](api/websocket.py:211)):
```javascript
ws.send(JSON.stringify({
  type: "auth",
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}));
```

**認証成功レスポンス**:
```json
{
  "type": "auth_response",
  "status": "success",
  "user_id": "user_001"
}
```

**認証失敗レスポンス**:
```json
{
  "type": "auth_response",
  "status": "error",
  "message": "Invalid or expired token"
}
```

### 9.5 会話メッセージ送信

```javascript
ws.send(JSON.stringify({
  "type": "chat",
  "session_id": "session_12345",
  "user_input": "こんにちは"
}));
```

### 9.6 メッセージ受信

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // {
  //   "type": "response",
  //   "response": "こんにちは！何かお手伝いできることはありますか？",
  //   "metadata": {...}
  // }
};
```

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0 | 2025-10-01 | 初版（Phase 1） |
| 2.0 | 2025-11-13 | Phase 2対応（入力検証、エラーハンドリング、メトリクスAPI追加） |

---

## 11. サポート

**プロジェクトURL**: https://github.com/your-org/LlmMultiChat3  
**ドキュメント**: `docks/`ディレクトリ  
**Issue報告**: GitHub Issues

---

**作成日**: 2025-11-13  
**バージョン**: 2.0  
**ステータス**: ✅ Phase 2対応完了