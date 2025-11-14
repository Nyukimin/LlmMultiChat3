"""
プラグインベースクラス

プラグインエコシステムの基底クラスを提供します。
全てのプラグインはこのクラスを継承する必要があります。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PluginStatus(Enum):
    """プラグインステータス"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """プラグインメタデータ"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginError(Exception):
    """プラグイン例外"""
    pass


class PluginInitializationError(PluginError):
    """プラグイン初期化エラー"""
    pass


class PluginExecutionError(PluginError):
    """プラグイン実行エラー"""
    pass


class BasePlugin(ABC):
    """
    プラグインベースクラス
    
    全てのプラグインはこのクラスを継承し、必須メソッドを実装する必要があります。
    
    Example:
        class MyPlugin(BasePlugin):
            def __init__(self):
                super().__init__(
                    PluginMetadata(
                        name="my_plugin",
                        version="1.0.0",
                        description="My custom plugin",
                        author="Developer"
                    )
                )
            
            async def initialize(self) -> bool:
                # 初期化処理
                return True
            
            async def execute(self, **kwargs) -> Dict[str, Any]:
                # 実行処理
                return {"result": "success"}
    """
    
    def __init__(self, metadata: PluginMetadata):
        """
        プラグイン初期化
        
        Args:
            metadata: プラグインメタデータ
        """
        self.metadata = metadata
        self.status = PluginStatus.UNINITIALIZED
        self._error_message: Optional[str] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        プラグイン初期化処理
        
        プラグインの初期化を行います。
        外部API接続、設定ファイル読み込みなどを行います。
        
        Returns:
            bool: 初期化成功時True、失敗時False
        
        Raises:
            PluginInitializationError: 初期化に失敗した場合
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        プラグイン実行処理
        
        プラグインのメイン処理を実行します。
        
        Args:
            **kwargs: プラグイン固有のパラメータ
        
        Returns:
            Dict[str, Any]: 実行結果
        
        Raises:
            PluginExecutionError: 実行に失敗した場合
        """
        pass
    
    async def cleanup(self) -> bool:
        """
        プラグインクリーンアップ処理
        
        プラグインのリソース解放を行います。
        オーバーライド可能なオプショナルメソッドです。
        
        Returns:
            bool: クリーンアップ成功時True、失敗時False
        """
        return True
    
    async def validate_params(self, **kwargs) -> bool:
        """
        パラメータ検証
        
        executeメソッドに渡されるパラメータを検証します。
        オーバーライド可能なオプショナルメソッドです。
        
        Args:
            **kwargs: 検証するパラメータ
        
        Returns:
            bool: パラメータが有効な場合True、無効な場合False
        """
        return True
    
    def get_metadata(self) -> PluginMetadata:
        """
        プラグインメタデータ取得
        
        Returns:
            PluginMetadata: プラグインメタデータ
        """
        return self.metadata
    
    def get_status(self) -> PluginStatus:
        """
        プラグインステータス取得
        
        Returns:
            PluginStatus: 現在のステータス
        """
        return self.status
    
    def get_error_message(self) -> Optional[str]:
        """
        エラーメッセージ取得
        
        Returns:
            Optional[str]: エラーメッセージ（エラーがない場合はNone）
        """
        return self._error_message
    
    def set_status(self, status: PluginStatus, error_message: Optional[str] = None):
        """
        プラグインステータス設定
        
        Args:
            status: 新しいステータス
            error_message: エラーメッセージ（オプショナル）
        """
        self.status = status
        self._error_message = error_message
    
    def is_enabled(self) -> bool:
        """
        プラグイン有効状態確認
        
        Returns:
            bool: 有効な場合True、無効な場合False
        """
        return self.metadata.enabled and self.status == PluginStatus.READY
    
    def enable(self):
        """プラグインを有効化"""
        self.metadata.enabled = True
    
    def disable(self):
        """プラグインを無効化"""
        self.metadata.enabled = False
        self.status = PluginStatus.DISABLED
    
    def get_capabilities(self) -> List[str]:
        """
        プラグイン機能一覧取得
        
        プラグインが提供する機能のリストを返します。
        オーバーライド可能なオプショナルメソッドです。
        
        Returns:
            List[str]: 機能名のリスト
        """
        return []
    
    def get_required_params(self) -> List[str]:
        """
        必須パラメータ一覧取得
        
        executeメソッドで必要なパラメータのリストを返します。
        オーバーライド可能なオプショナルメソッドです。
        
        Returns:
            List[str]: 必須パラメータ名のリスト
        """
        return []
    
    def get_optional_params(self) -> Dict[str, Any]:
        """
        オプショナルパラメータ一覧取得
        
        executeメソッドで使用可能なオプショナルパラメータと
        そのデフォルト値を返します。
        オーバーライド可能なオプショナルメソッドです。
        
        Returns:
            Dict[str, Any]: パラメータ名とデフォルト値の辞書
        """
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        プラグイン情報を辞書形式で取得
        
        Returns:
            Dict[str, Any]: プラグイン情報
        """
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "author": self.metadata.author,
            "dependencies": self.metadata.dependencies,
            "enabled": self.metadata.enabled,
            "status": self.status.value,
            "error_message": self._error_message,
            "capabilities": self.get_capabilities(),
            "required_params": self.get_required_params(),
            "optional_params": self.get_optional_params()
        }
    
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"status='{self.status.value}'"
            f")>"
        )