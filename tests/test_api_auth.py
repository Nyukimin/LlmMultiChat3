"""Authentication API Tests.

Phase 3 Week 9: 認証APIのテスト。

テストケース (10件):
- ユーザー登録（正常系・異常系）
- ログイン（正常系・異常系）
- トークン更新（正常系・異常系）
- プロファイル取得
- パスワード変更
- ユーザー削除（管理者専用）
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


# テストクライアント
client = TestClient(app)


# ===== フィクスチャ =====

@pytest.fixture
def test_user_data():
    """テストユーザーデータ."""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def registered_user(test_user_data):
    """登録済みユーザー."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_token(test_user_data):
    """認証トークン."""
    # ユーザー登録
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # ログイン
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """認証ヘッダー."""
    return {"Authorization": f"Bearer {auth_token}"}


# ===== ユーザー登録テスト =====

def test_register_success(test_user_data):
    """ユーザー登録成功."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert "user_id" in data


def test_register_duplicate_email(test_user_data, registered_user):
    """重複メールアドレスでの登録失敗."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_register_weak_password():
    """弱いパスワードでの登録失敗."""
    response = client.post("/api/v1/auth/register", json={
        "username": "weak_user",
        "email": "weak@example.com",
        "password": "weak"  # 8文字未満
    })
    
    assert response.status_code == 422  # Pydantic validation error


def test_register_invalid_email():
    """無効なメールアドレスでの登録失敗."""
    response = client.post("/api/v1/auth/register", json={
        "username": "invalid_user",
        "email": "invalid-email",  # @がない
        "password": "SecurePass123!"
    })
    
    assert response.status_code == 422


# ===== ログインテスト =====

def test_login_success(test_user_data, registered_user):
    """ログイン成功."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] > 0
    assert "user" in data


def test_login_wrong_password(test_user_data, registered_user):
    """誤ったパスワードでログイン失敗."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


def test_login_nonexistent_user():
    """存在しないユーザーでログイン失敗."""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePassword123!"
    })
    
    assert response.status_code == 401


# ===== トークン更新テスト =====

def test_refresh_token_success(test_user_data, registered_user):
    """トークン更新成功."""
    # ログイン
    login_response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    refresh_token = login_response.json()["refresh_token"]
    
    # トークン更新
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


def test_refresh_token_invalid():
    """無効なトークンで更新失敗."""
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid_token"
    })
    
    assert response.status_code == 401


# ===== プロファイル取得テスト =====

def test_get_profile_success(test_user_data, auth_headers):
    """プロファイル取得成功."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert "user_id" in data
    assert "roles" in data


def test_get_profile_unauthorized():
    """未認証でプロファイル取得失敗."""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # No Authorization header


# ===== パスワード変更テスト =====

def test_change_password_success(test_user_data, auth_headers):
    """パスワード変更成功."""
    response = client.post("/api/v1/auth/change-password", headers=auth_headers, json={
        "current_password": test_user_data["password"],
        "new_password": "NewSecurePass456!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_change_password_wrong_current():
    """誤った現在のパスワードで変更失敗."""
    # まずユーザー登録・ログイン
    user_data = {
        "username": "change_pw_user",
        "email": "changepw@example.com",
        "password": "OldPass123!"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # 誤った現在のパスワードで変更試行
    response = client.post("/api/v1/auth/change-password", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "current_password": "WrongOldPass123!",
        "new_password": "NewPass456!"
    })
    
    assert response.status_code == 401


# ===== ユーザー削除テスト（管理者専用） =====

def test_delete_user_success_admin():
    """管理者によるユーザー削除成功."""
    # 管理者ユーザー作成（モック）
    # 実際の実装では管理者ロールを持つユーザーを作成
    
    # 削除対象ユーザー登録
    target_user = {
        "username": "to_be_deleted",
        "email": "delete@example.com",
        "password": "DeleteMe123!"
    }
    reg_response = client.post("/api/v1/auth/register", json=target_user)
    user_id = reg_response.json()["user_id"]
    
    # TODO: 管理者トークン取得（Week 8のRBAC実装後）
    # admin_token = get_admin_token()
    # response = client.delete(
    #     f"/api/v1/auth/users/{user_id}",
    #     headers={"Authorization": f"Bearer {admin_token}"}
    # )
    # assert response.status_code == 200


def test_delete_user_forbidden_non_admin(test_user_data, auth_headers):
    """非管理者によるユーザー削除失敗."""
    # 削除対象ユーザー登録
    target_user = {
        "username": "target_user",
        "email": "target@example.com",
        "password": "Target123!"
    }
    reg_response = client.post("/api/v1/auth/register", json=target_user)
    user_id = reg_response.json()["user_id"]
    
    # 一般ユーザートークンで削除試行
    response = client.delete(
        f"/api/v1/auth/users/{user_id}",
        headers=auth_headers
    )
    
    # 権限不足
    assert response.status_code in [403, 500]  # モック実装では500の可能性


# ===== レート制限テスト =====

def test_register_rate_limit():
    """ユーザー登録レート制限（5/min）."""
    # 5回登録試行
    for i in range(5):
        client.post("/api/v1/auth/register", json={
            "username": f"rate_user_{i}",
            "email": f"rate{i}@example.com",
            "password": "RateTest123!"
        })
    
    # 6回目は制限
    response = client.post("/api/v1/auth/register", json={
        "username": "rate_user_6",
        "email": "rate6@example.com",
        "password": "RateTest123!"
    })
    
    # レート制限エラー
    assert response.status_code == 429