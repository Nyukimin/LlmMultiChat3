"""Memory API Tests.

Phase 3 Week 9: 記憶APIのテスト。

テストケース (15件):
- 記憶検索(正常系・異常系)
- 記憶保存
- 記憶削除
- 記憶統計
- セッション記憶一括削除
- 管理者専用機能
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
        "username": "memory_user",
        "email": "memory@example.com",
        "password": "MemoryPass123!"
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


# ===== 記憶検索テスト =====

def test_search_memory_success(auth_headers):
    """記憶検索成功."""
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "AIについて学んだこと",
        "memory_types": ["short_term", "long_term"],
        "limit": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "AIについて学んだこと"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "total_count" in data


def test_search_memory_all_types(auth_headers):
    """全記憶タイプで検索."""
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "テストクエリ",
        "memory_types": ["short_term", "mid_term", "long_term", "associative", "knowledge"],
        "limit": 20
    })
    
    assert response.status_code == 200


def test_search_memory_with_session(auth_headers):
    """セッション指定で検索."""
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "セッション内検索",
        "memory_types": ["short_term"],
        "session_id": "test-session-123",
        "limit": 10
    })
    
    assert response.status_code == 200


def test_search_memory_invalid_type(auth_headers):
    """無効な記憶タイプ."""
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "テスト",
        "memory_types": ["invalid_type"],
        "limit": 10
    })
    
    # バリデーションエラー
    assert response.status_code == 422


def test_search_memory_empty_query(auth_headers):
    """空のクエリ."""
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "",
        "memory_types": ["long_term"],
        "limit": 10
    })
    
    # バリデーションエラー(min_length=1)
    assert response.status_code == 422


def test_search_memory_limit_validation(auth_headers):
    """limit境界値テスト."""
    # limit=0(無効)
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "テスト",
        "memory_types": ["long_term"],
        "limit": 0
    })
    assert response.status_code == 422
    
    # limit=101(上限超過)
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "テスト",
        "memory_types": ["long_term"],
        "limit": 101
    })
    assert response.status_code == 422


def test_search_memory_unauthorized():
    """未認証での検索失敗."""
    response = client.post("/api/v1/memory/search", json={
        "query": "テスト",
        "memory_types": ["long_term"],
        "limit": 10
    })
    
    assert response.status_code == 403


# ===== 記憶保存テスト =====

def test_store_memory_success(auth_headers):
    """記憶保存成功."""
    response = client.post("/api/v1/memory", headers=auth_headers, json={
        "memory_type": "long_term",
        "content": "ユーザーはAI技術に興味があり、特に機械学習分野を学びたい",
        "session_id": "store-session-1",
        "metadata": {
            "character": "lumina",
            "importance": "high"
        }
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "memory_id" in data
    assert data["memory_type"] == "long_term"


def test_store_memory_all_types(auth_headers):
    """全記憶タイプで保存."""
    memory_types = ["short_term", "mid_term", "long_term", "associative", "knowledge"]
    
    for memory_type in memory_types:
        response = client.post("/api/v1/memory", headers=auth_headers, json={
            "memory_type": memory_type,
            "content": f"{memory_type}のテストコンテンツ"
        })
        
        assert response.status_code == 201


def test_store_memory_invalid_type(auth_headers):
    """無効な記憶タイプで保存."""
    response = client.post("/api/v1/memory", headers=auth_headers, json={
        "memory_type": "invalid_type",
        "content": "テストコンテンツ"
    })
    
    # バリデーションエラー
    assert response.status_code == 422


def test_store_memory_empty_content(auth_headers):
    """空のコンテンツ."""
    response = client.post("/api/v1/memory", headers=auth_headers, json={
        "memory_type": "long_term",
        "content": ""
    })
    
    # バリデーションエラー(min_length=1)
    assert response.status_code == 422


def test_store_memory_long_content(auth_headers):
    """長いコンテンツ(10000文字超)."""
    long_content = "a" * 11000
    
    response = client.post("/api/v1/memory", headers=auth_headers, json={
        "memory_type": "long_term",
        "content": long_content
    })
    
    # バリデーションエラー(max_length=10000)
    assert response.status_code == 422


# ===== 記憶削除テスト =====

def test_delete_memory_success(auth_headers):
    """記憶削除成功."""
    # まず記憶保存
    store_response = client.post("/api/v1/memory", headers=auth_headers, json={
        "memory_type": "short_term",
        "content": "削除予定の記憶"
    })
    memory_id = store_response.json()["memory_id"]
    
    # 記憶削除
    response = client.delete(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_delete_memory_nonexistent(auth_headers):
    """存在しない記憶の削除."""
    response = client.delete(
        "/api/v1/memory/nonexistent-memory-id",
        headers=auth_headers
    )
    
    # 存在しない記憶
    assert response.status_code in [404, 500]


# ===== 記憶統計テスト =====

def test_get_memory_stats_success(auth_headers):
    """記憶統計取得成功."""
    response = client.get("/api/v1/memory/stats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_memories" in data
    assert "by_type" in data
    assert "by_session" in data
    assert "storage_size_mb" in data


def test_get_memory_stats_unauthorized():
    """未認証での統計取得失敗."""
    response = client.get("/api/v1/memory/stats")
    
    assert response.status_code == 403


# ===== セッション記憶一括削除テスト =====

def test_delete_session_memories_success(auth_headers):
    """セッション記憶一括削除成功."""
    session_id = "bulk-delete-session-1"
    
    # セッションに記憶保存
    for i in range(3):
        client.post("/api/v1/memory", headers=auth_headers, json={
            "memory_type": "short_term",
            "content": f"セッション記憶{i}",
            "session_id": session_id
        })
    
    # 一括削除
    response = client.delete(
        f"/api/v1/memory/sessions/{session_id}/all",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "deleted_count" in data


def test_delete_session_memories_nonexistent(auth_headers):
    """存在しないセッションの記憶削除."""
    response = client.delete(
        "/api/v1/memory/sessions/nonexistent-session/all",
        headers=auth_headers
    )
    
    # 存在しないセッションでもエラーにならない可能性
    assert response.status_code in [200, 404]


# ===== 管理者専用機能テスト =====

def test_flush_memory_admin():
    """記憶フラッシュ(管理者専用)."""
    # TODO: 管理者トークン取得(Week 8のRBAC実装後)
    # admin_token = get_admin_token()
    # response = client.post(
    #     "/api/v1/memory/admin/flush",
    #     headers={"Authorization": f"Bearer {admin_token}"}
    # )
    # assert response.status_code == 200
    # data = response.json()
    # assert data["status"] == "success"
    # assert "flushed_memories" in data
    pass


def test_flush_memory_forbidden_non_admin(auth_headers):
    """非管理者によるフラッシュ失敗."""
    response = client.post(
        "/api/v1/memory/admin/flush",
        headers=auth_headers
    )
    
    # 権限不足
    assert response.status_code in [403, 500]


# ===== レート制限テスト =====

def test_search_memory_rate_limit(auth_headers):
    """記憶検索レート制限(60/min)."""
    # 60回検索試行
    for i in range(60):
        client.post("/api/v1/memory/search", headers=auth_headers, json={
            "query": f"レート制限テスト{i}",
            "memory_types": ["long_term"],
            "limit": 5
        })
    
    # 61回目は制限
    response = client.post("/api/v1/memory/search", headers=auth_headers, json={
        "query": "レート制限テスト61",
        "memory_types": ["long_term"],
        "limit": 5
    })
    
    # レート制限エラー
    assert response.status_code == 429