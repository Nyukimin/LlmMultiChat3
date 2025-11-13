"""Role-Based Access Control (RBAC) Manager for LlmMultiChat3.

このモジュールはロールベースアクセス制御（RBAC）を提供します。

Phase 3 Week 8-2:
- ロール定義（admin/user/premium/guest）
- 権限管理（read/write/delete/manage_users等）
- ロール割り当て・削除
- 権限チェック

使用例:
    >>> role_manager = RoleManager()
    >>> user = User(user_id="user123", roles=["user"])
    >>> role_manager.has_permission(user, "read")
    True
    >>> role_manager.has_permission(user, "manage_users")
    False
"""

from typing import List, Set, Dict, Optional
import logging
from security.models import User
from exceptions import (
    AuthorizationError,
    InsufficientPermissionsError,
    ValidationError
)


logger = logging.getLogger(__name__)


class RoleManager:
    """ロールベースアクセス制御（RBAC）マネージャー.
    
    階層的なロールシステムを実装し、各ロールに権限を割り当てます。
    
    ロール階層:
    - admin: 全権限（システム管理者）
    - premium: ユーザー権限 + 拡張機能
    - user: 標準ユーザー権限
    - guest: 読み取り専用
    
    権限タイプ:
    - read: データ読み取り
    - write: データ書き込み
    - delete: データ削除
    - manage_users: ユーザー管理
    - manage_roles: ロール管理
    - view_metrics: メトリクス閲覧
    - export_data: データエクスポート
    - api_access: API利用
    """
    
    # ロール定義（ロール名 -> 権限リスト）
    ROLES: Dict[str, Set[str]] = {
        "admin": {
            "read", "write", "delete",
            "manage_users", "manage_roles",
            "view_metrics", "export_data",
            "api_access", "plugin_management",
            "system_config"
        },
        "premium": {
            "read", "write", "delete",
            "view_metrics", "export_data",
            "api_access", "plugin_access"
        },
        "user": {
            "read", "write",
            "api_access"
        },
        "guest": {
            "read"
        }
    }
    
    # 権限説明
    PERMISSION_DESCRIPTIONS: Dict[str, str] = {
        "read": "データの読み取り権限",
        "write": "データの書き込み権限",
        "delete": "データの削除権限",
        "manage_users": "ユーザー管理権限（作成・更新・削除）",
        "manage_roles": "ロール管理権限（割り当て・解除）",
        "view_metrics": "メトリクス・統計情報の閲覧権限",
        "export_data": "データエクスポート権限",
        "api_access": "API利用権限",
        "plugin_management": "プラグイン管理権限（インストール・削除）",
        "plugin_access": "プラグイン利用権限",
        "system_config": "システム設定変更権限"
    }
    
    # ロール階層（上位ロールは下位ロールの権限を継承）
    ROLE_HIERARCHY = {
        "admin": ["premium", "user", "guest"],
        "premium": ["user", "guest"],
        "user": ["guest"],
        "guest": []
    }
    
    def __init__(self):
        """RoleManagerを初期化."""
        logger.info("RoleManager initialized")
    
    def has_permission(self, user: User, permission: str) -> bool:
        """ユーザーが特定の権限を持っているかチェック.
        
        Args:
            user: ユーザーオブジェクト
            permission: チェックする権限名
        
        Returns:
            bool: 権限を持っている場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> user = User(user_id="user123", roles=["user"])
            >>> role_manager.has_permission(user, "read")
            True
            >>> role_manager.has_permission(user, "delete")
            False
        """
        if not user.is_active:
            logger.warning(f"Inactive user {user.user_id} attempted to check permission")
            return False
        
        # ユーザーの全ロールをチェック
        for role in user.roles:
            if role not in self.ROLES:
                logger.warning(f"Unknown role: {role} for user {user.user_id}")
                continue
            
            # ロールが権限を持っているかチェック
            if permission in self.ROLES[role]:
                logger.debug(
                    f"User {user.user_id} has permission '{permission}' via role '{role}'"
                )
                return True
        
        logger.debug(f"User {user.user_id} lacks permission '{permission}'")
        return False
    
    def has_any_permission(self, user: User, permissions: List[str]) -> bool:
        """ユーザーが指定された権限のいずれかを持っているかチェック.
        
        Args:
            user: ユーザーオブジェクト
            permissions: チェックする権限名のリスト
        
        Returns:
            bool: いずれかの権限を持っている場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> user = User(user_id="user123", roles=["user"])
            >>> role_manager.has_any_permission(user, ["write", "delete"])
            True
        """
        for permission in permissions:
            if self.has_permission(user, permission):
                return True
        return False
    
    def has_all_permissions(self, user: User, permissions: List[str]) -> bool:
        """ユーザーが指定された全ての権限を持っているかチェック.
        
        Args:
            user: ユーザーオブジェクト
            permissions: チェックする権限名のリスト
        
        Returns:
            bool: 全ての権限を持っている場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> admin = User(user_id="admin1", roles=["admin"])
            >>> role_manager.has_all_permissions(admin, ["read", "write", "delete"])
            True
        """
        for permission in permissions:
            if not self.has_permission(user, permission):
                return False
        return True
    
    def require_permission(
        self,
        user: User,
        permission: str,
        raise_error: bool = True
    ) -> bool:
        """権限チェック（不足時に例外発生）.
        
        Args:
            user: ユーザーオブジェクト
            permission: 必要な権限
            raise_error: Trueの場合、権限不足時に例外を発生
        
        Returns:
            bool: 権限を持っている場合True
        
        Raises:
            InsufficientPermissionsError: 権限不足かつraise_error=True
        
        Example:
            >>> role_manager = RoleManager()
            >>> user = User(user_id="user123", roles=["guest"])
            >>> role_manager.require_permission(user, "write")
            InsufficientPermissionsError: Required permission: write
        """
        if self.has_permission(user, permission):
            return True
        
        if raise_error:
            raise InsufficientPermissionsError(
                f"User {user.user_id} lacks required permission: {permission}",
                required_permission=permission
            )
        
        return False
    
    def get_user_permissions(self, user: User) -> Set[str]:
        """ユーザーの全権限を取得.
        
        Args:
            user: ユーザーオブジェクト
        
        Returns:
            Set[str]: ユーザーが持つ全権限の集合
        
        Example:
            >>> role_manager = RoleManager()
            >>> user = User(user_id="user123", roles=["user", "premium"])
            >>> permissions = role_manager.get_user_permissions(user)
            >>> print(permissions)
            {'read', 'write', 'delete', 'view_metrics', ...}
        """
        permissions: Set[str] = set()
        
        for role in user.roles:
            if role in self.ROLES:
                permissions.update(self.ROLES[role])
            else:
                logger.warning(f"Unknown role: {role} for user {user.user_id}")
        
        return permissions
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """特定のロールの権限を取得.
        
        Args:
            role: ロール名
        
        Returns:
            Set[str]: ロールが持つ権限の集合
        
        Raises:
            ValidationError: 無効なロール名
        
        Example:
            >>> role_manager = RoleManager()
            >>> permissions = role_manager.get_role_permissions("admin")
            >>> print(permissions)
            {'read', 'write', 'delete', 'manage_users', ...}
        """
        if role not in self.ROLES:
            raise ValidationError(
                f"Invalid role: {role}",
                field="role"
            )
        
        return self.ROLES[role].copy()
    
    def is_valid_role(self, role: str) -> bool:
        """ロール名の有効性をチェック.
        
        Args:
            role: ロール名
        
        Returns:
            bool: 有効なロールの場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> role_manager.is_valid_role("admin")
            True
            >>> role_manager.is_valid_role("superadmin")
            False
        """
        return role in self.ROLES
    
    def is_valid_permission(self, permission: str) -> bool:
        """権限名の有効性をチェック.
        
        Args:
            permission: 権限名
        
        Returns:
            bool: 有効な権限の場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> role_manager.is_valid_permission("read")
            True
            >>> role_manager.is_valid_permission("fly")
            False
        """
        all_permissions = set()
        for permissions in self.ROLES.values():
            all_permissions.update(permissions)
        return permission in all_permissions
    
    def get_all_roles(self) -> List[str]:
        """全ロールのリストを取得.
        
        Returns:
            List[str]: ロール名のリスト
        
        Example:
            >>> role_manager = RoleManager()
            >>> roles = role_manager.get_all_roles()
            >>> print(roles)
            ['admin', 'premium', 'user', 'guest']
        """
        return list(self.ROLES.keys())
    
    def get_all_permissions(self) -> List[str]:
        """全権限のリストを取得.
        
        Returns:
            List[str]: 権限名のリスト
        
        Example:
            >>> role_manager = RoleManager()
            >>> permissions = role_manager.get_all_permissions()
            >>> print(permissions)
            ['read', 'write', 'delete', ...]
        """
        all_permissions = set()
        for permissions in self.ROLES.values():
            all_permissions.update(permissions)
        return sorted(list(all_permissions))
    
    def can_assign_role(self, assigner: User, target_role: str) -> bool:
        """ロール割り当て権限チェック.
        
        adminロールのみが他ユーザーにロールを割り当てられます。
        
        Args:
            assigner: ロールを割り当てようとするユーザー
            target_role: 割り当て先のロール
        
        Returns:
            bool: 割り当て可能な場合True
        
        Example:
            >>> role_manager = RoleManager()
            >>> admin = User(user_id="admin1", roles=["admin"])
            >>> role_manager.can_assign_role(admin, "premium")
            True
        """
        return self.has_permission(assigner, "manage_roles")
    
    def get_permission_description(self, permission: str) -> str:
        """権限の説明を取得.
        
        Args:
            permission: 権限名
        
        Returns:
            str: 権限の説明
        
        Example:
            >>> role_manager = RoleManager()
            >>> desc = role_manager.get_permission_description("read")
            >>> print(desc)
            'データの読み取り権限'
        """
        return self.PERMISSION_DESCRIPTIONS.get(
            permission,
            "説明なし"
        )
    
    def get_role_info(self, role: str) -> dict:
        """ロールの詳細情報を取得.
        
        Args:
            role: ロール名
        
        Returns:
            dict: ロール情報（名前・権限・階層）
        
        Example:
            >>> role_manager = RoleManager()
            >>> info = role_manager.get_role_info("admin")
            >>> print(info)
            {
                'role': 'admin',
                'permissions': ['read', 'write', ...],
                'permission_count': 10,
                'inherits_from': ['premium', 'user', 'guest']
            }
        """
        if not self.is_valid_role(role):
            raise ValidationError(
                f"Invalid role: {role}",
                field="role"
            )
        
        return {
            'role': role,
            'permissions': sorted(list(self.ROLES[role])),
            'permission_count': len(self.ROLES[role]),
            'inherits_from': self.ROLE_HIERARCHY.get(role, [])
        }
