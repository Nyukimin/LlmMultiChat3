"""Chat API Tests.

Phase 3 Week 9: 会話APIのテスト。

テストケース (15件):
- 会話実行（正常系・異常系）
- ストリーミング会話
- 会話履歴取得
- セッション管理
- キャラクター選択
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app


# テストクライアント
client = TestClient(app)


# ===== フィクスチャ =====

@pytest.fixture
def test_user():
    """テストユーザー登録・ログイン."""
    # ユーザー登録
    user_data = {
        "username": "chat_user",
        "email": "chat@example.com",
        "password": "ChatPass123!"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # ログイン
    login_response = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    return {
        "user_data": user_data,
        "token": login_response.json()["access_token"]
    }


@pytest.fixture
def auth_headers(test_user):
    """認証ヘッダー."""
    return {"Authorization": f"Bearer {test_user['token']}"}


# ===== 会話実行テスト =====

def test_chat_success(auth_headers):
    """会話実行成功."""
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "test-session-1",
        "user_input": "こんにちは",
        "character": "lumina"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-1"
    assert data["character"] == "lumina"
    assert "response" in data
    assert "metadata" in data
    assert "timestamp" in data


def test_chat_auto_character_selection(auth_headers):
    """キャラクター自動選択."""
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "test-session-2",
        "user_input": "最新のAI技術について教えて"
        # characterを指定しない
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "character" in data


def test_chat_invalid_character(auth_headers):
    """無効なキャラクター指定."""
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "test-session-3",
        "user_input": "Hello",
        "character": "invalid_character"
    })
    
    # バリデーションエラー
    assert response.status_code == 422


def test_chat_empty_input(auth_headers):
    """空の入力."""
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "test-session-4",
        "user_input": "",
        "character": "lumina"
    })
    
    # バリデーションエラー（min_length=1）
    assert response.status_code == 422


def test_chat_long_input(auth_headers):
    """長い入力（5000文字超）."""
    long_input = "a" * 6000
    
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "test-session-5",
        "user_input": long_input,
        "character": "lumina"
    })
    
    # バリデーションエラー（max_length=5000）
    assert response.status_code == 422


def test_chat_unauthorized():
    """未認証での会話実行失敗."""
    response = client.post("/api/v1/chat", json={
        "session_id": "test-session-6",
        "user_input": "Hello",
        "character": "lumina"
    })
    
    assert response.status_code == 403


# ===== ストリーミング会話テスト =====

def test_chat_stream_success(auth_headers):
    """ストリーミング会話成功."""
    response = client.post("/api/v1/chat/stream", headers=auth_headers, json={
        "session_id": "stream-session-1",
        "user_input": "ストリーミング応答をテスト",
        "character": "lumina"
    })
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # SSEデータ検証
    content = response.text
    assert "data:" in content


def test_chat_stream_unauthorized():
    """未認証でのストリーミング会話失敗."""
    response = client.post("/api/v1/chat/stream", json={
        "session_id": "stream-session-2",
        "user_input": "Hello"
    })
    
    assert response.status_code == 403


# ===== 会話履歴取得テスト =====

def test_get_history_success(auth_headers):
    """会話履歴取得成功."""
    session_id = "history-session-1"
    
    # まず会話実行
    client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": session_id,
        "user_input": "テストメッセージ1",
        "character": "lumina"
    })
    
    # 履歴取得
    response = client.get(
        f"/api/v1/chat/history/{session_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "messages" in data
    assert isinstance(data["messages"], list)
    assert "total_count" in data


def test_get_history_with_limit(auth_headers):
    """会話履歴取得（limit指定）."""
    session_id = "history-session-2"
    
    response = client.get(
        f"/api/v1/chat/history/{session_id}?limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) <= 10


def test_get_history_with_offset(auth_headers):
    """会話履歴取得（offset指定）."""
    session_id = "history-session-3"
    
    response = client.get(
        f"/api/v1/chat/history/{session_id}?offset=5&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200


def test_get_history_nonexistent_session(auth_headers):
    """存在しないセッションの履歴取得."""
    response = client.get(
        "/api/v1/chat/history/nonexistent-session",
        headers=auth_headers
    )
    
    # セッションが存在しない場合でも空の履歴を返す可能性
    assert response.status_code in [200, 404]


# ===== セッション管理テスト =====

def test_list_sessions_success(auth_headers):
    """セッション一覧取得成功."""
    # セッション作成
    for i in range(3):
        client.post("/api/v1/chat", headers=auth_headers, json={
            "session_id": f"list-session-{i}",
            "user_input": f"テストメッセージ{i}",
            "character": "lumina"
        })
    
    # 一覧取得
    response = client.get("/api/v1/chat/sessions", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert "total_count" in data


def test_list_sessions_with_pagination(auth_headers):
    """セッション一覧取得（ページネーション）."""
    response = client.get(
        "/api/v1/chat/sessions?limit=5&offset=0",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) <= 5


def test_delete_session_success(auth_headers):
    """セッション削除成功."""
    session_id = "delete-session-1"
    
    # セッション作成
    client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": session_id,
        "user_input": "削除予定",
        "character": "lumina"
    })
    
    # セッション削除
    response = client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_delete_session_nonexistent(auth_headers):
    """存在しないセッションの削除."""
    response = client.delete(
        "/api/v1/chat/sessions/nonexistent-session",
        headers=auth_headers
    )
    
    # 存在しないセッションでもエラーにならない可能性
    assert response.status_code in [200, 404]


# ===== レート制限テスト =====

def test_chat_rate_limit(auth_headers):
    """会話実行レート制限（30/min）."""
    # 30回会話試行
    for i in range(30):
        client.post("/api/v1/chat", headers=auth_headers, json={
            "session_id": f"rate-session-{i}",
            "user_input": f"レート制限テスト{i}",
            "character": "lumina"
        })
    
    # 31回目は制限
    response = client.post("/api/v1/chat", headers=auth_headers, json={
        "session_id": "rate-session-31",
        "user_input": "レート制限テスト31",
        "character": "lumina"
    })
    
    # レート制限エラー
    assert response.status_code == 429