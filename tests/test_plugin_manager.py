"""
プラグインマネージャーテスト

プラグインマネージャーの機能をテストします。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from core.plugin_manager import PluginManager
from plugins.base import (
    BasePlugin,
    PluginMetadata,
    PluginStatus,
    PluginError,
    PluginInitializationError,
    PluginExecutionError
)


# テスト用モックプラグイン
class MockPlugin(BasePlugin):
    """テスト用プラグイン"""
    
    def __init__(self):
        super().__init__(
            PluginMetadata(
                name="mock_plugin",
                version="1.0.0",
                description="Mock plugin for testing",
                author="Test"
            )
        )
    
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "success", "params": kwargs}


class FailingInitPlugin(BasePlugin):
    """初期化に失敗するプラグイン"""
    
    def __init__(self):
        super().__init__(
            PluginMetadata(
                name="failing_init",
                version="1.0.0",
                description="Failing initialization plugin",
                author="Test"
            )
        )
    
    async def initialize(self) -> bool:
        raise PluginInitializationError("Initialization failed")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "success"}


class FailingExecutionPlugin(BasePlugin):
    """実行に失敗するプラグイン"""
    
    def __init__(self):
        super().__init__(
            PluginMetadata(
                name="failing_exec",
                version="1.0.0",
                description="Failing execution plugin",
                author="Test"
            )
        )
    
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        raise PluginExecutionError("Execution failed")


class ParameterValidationPlugin(BasePlugin):
    """パラメータ検証プラグイン"""
    
    def __init__(self):
        super().__init__(
            PluginMetadata(
                name="param_validation",
                version="1.0.0",
                description="Parameter validation plugin",
                author="Test"
            )
        )
    
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, required_param: str, **kwargs) -> Dict[str, Any]:
        return {"required_param": required_param}
    
    async def validate_params(self, required_param=None, **kwargs) -> bool:
        return required_param is not None


@pytest.fixture
def plugin_manager():
    """プラグインマネージャーフィクスチャ"""
    return PluginManager()


@pytest.mark.asyncio
class TestPluginManager:
    """プラグインマネージャーテスト"""
    
    async def test_load_plugin(self, plugin_manager):
        """プラグインロードテスト"""
        success = await plugin_manager.load_plugin(MockPlugin)
        
        assert success is True
        assert "mock_plugin" in plugin_manager.list_plugins()
    
    async def test_load_duplicate_plugin(self, plugin_manager):
        """重複プラグインロードテスト"""
        await plugin_manager.load_plugin(MockPlugin)
        
        # 同じプラグインを再度ロード（警告が出るが成功する）
        success = await plugin_manager.load_plugin(MockPlugin)
        assert success is True
        assert len(plugin_manager.list_plugins()) == 1
    
    async def test_initialize_plugin(self, plugin_manager):
        """プラグイン初期化テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        success = await plugin_manager.initialize_plugin("mock_plugin")
        
        assert success is True
        
        plugin = plugin_manager.get_plugin("mock_plugin")
        assert plugin.status == PluginStatus.READY
    
    async def test_initialize_nonexistent_plugin(self, plugin_manager):
        """存在しないプラグイン初期化テスト"""
        with pytest.raises(PluginError):
            await plugin_manager.initialize_plugin("nonexistent")
    
    async def test_initialize_failing_plugin(self, plugin_manager):
        """初期化失敗プラグインテスト"""
        await plugin_manager.load_plugin(FailingInitPlugin)
        
        with pytest.raises(PluginInitializationError):
            await plugin_manager.initialize_plugin("failing_init")
        
        plugin = plugin_manager.get_plugin("failing_init")
        assert plugin.status == PluginStatus.ERROR
    
    async def test_initialize_all(self, plugin_manager):
        """全プラグイン初期化テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.load_plugin(FailingInitPlugin)
        
        results = await plugin_manager.initialize_all()
        
        assert results["mock_plugin"] is True
        assert results["failing_init"] is False
    
    async def test_execute_plugin(self, plugin_manager):
        """プラグイン実行テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        result = await plugin_manager.execute_plugin(
            "mock_plugin",
            param1="value1",
            param2="value2"
        )
        
        assert result["result"] == "success"
        assert result["params"]["param1"] == "value1"
        assert result["params"]["param2"] == "value2"
    
    async def test_execute_nonexistent_plugin(self, plugin_manager):
        """存在しないプラグイン実行テスト"""
        with pytest.raises(PluginError):
            await plugin_manager.execute_plugin("nonexistent")
    
    async def test_execute_disabled_plugin(self, plugin_manager):
        """無効化されたプラグイン実行テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        # プラグイン無効化
        plugin_manager.disable_plugin("mock_plugin")
        
        with pytest.raises(PluginError):
            await plugin_manager.execute_plugin("mock_plugin")
    
    async def test_execute_failing_plugin(self, plugin_manager):
        """実行失敗プラグインテスト"""
        await plugin_manager.load_plugin(FailingExecutionPlugin)
        await plugin_manager.initialize_plugin("failing_exec")
        
        with pytest.raises(PluginExecutionError):
            await plugin_manager.execute_plugin("failing_exec")
    
    async def test_parameter_validation(self, plugin_manager):
        """パラメータ検証テスト"""
        await plugin_manager.load_plugin(ParameterValidationPlugin)
        await plugin_manager.initialize_plugin("param_validation")
        
        # 有効なパラメータ
        result = await plugin_manager.execute_plugin(
            "param_validation",
            required_param="value"
        )
        assert result["required_param"] == "value"
        
        # 無効なパラメータ
        with pytest.raises(PluginExecutionError):
            await plugin_manager.execute_plugin("param_validation")
    
    async def test_cleanup_plugin(self, plugin_manager):
        """プラグインクリーンアップテスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        success = await plugin_manager.cleanup_plugin("mock_plugin")
        assert success is True
    
    async def test_cleanup_all(self, plugin_manager):
        """全プラグインクリーンアップテスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        results = await plugin_manager.cleanup_all()
        assert results["mock_plugin"] is True
    
    async def test_enable_disable_plugin(self, plugin_manager):
        """プラグイン有効化/無効化テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        # 無効化
        success = plugin_manager.disable_plugin("mock_plugin")
        assert success is True
        
        plugin = plugin_manager.get_plugin("mock_plugin")
        assert not plugin.is_enabled()
        
        # 有効化
        success = plugin_manager.enable_plugin("mock_plugin")
        assert success is True
        assert plugin.metadata.enabled is True
    
    async def test_unload_plugin(self, plugin_manager):
        """プラグインアンロードテスト"""
        await plugin_manager.load_plugin(MockPlugin)
        
        success = plugin_manager.unload_plugin("mock_plugin")
        assert success is True
        assert "mock_plugin" not in plugin_manager.list_plugins()
    
    async def test_get_plugin_info(self, plugin_manager):
        """プラグイン情報取得テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        
        info = plugin_manager.get_plugin_info("mock_plugin")
        assert info is not None
        assert info["name"] == "mock_plugin"
        assert info["version"] == "1.0.0"
        assert info["status"] == PluginStatus.UNINITIALIZED.value
    
    async def test_get_all_plugins_info(self, plugin_manager):
        """全プラグイン情報取得テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        
        all_info = plugin_manager.get_all_plugins_info()
        assert "mock_plugin" in all_info
        assert all_info["mock_plugin"]["name"] == "mock_plugin"
    
    async def test_execution_history(self, plugin_manager):
        """実行履歴テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        # 実行
        await plugin_manager.execute_plugin("mock_plugin", param="value")
        
        # 履歴取得
        history = plugin_manager.get_execution_history()
        assert len(history) > 0
        assert history[-1]["plugin_name"] == "mock_plugin"
        assert history[-1]["success"] is True
        
        # 履歴クリア
        plugin_manager.clear_execution_history()
        history = plugin_manager.get_execution_history()
        assert len(history) == 0
    
    async def test_statistics(self, plugin_manager):
        """統計情報テスト"""
        await plugin_manager.load_plugin(MockPlugin)
        await plugin_manager.initialize_plugin("mock_plugin")
        
        # 実行
        await plugin_manager.execute_plugin("mock_plugin")
        
        stats = plugin_manager.get_statistics()
        assert stats["total_plugins"] == 1
        assert stats["enabled_plugins"] == 1
        assert stats["ready_plugins"] == 1
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["success_rate"] == 100.0


@pytest.mark.asyncio
class TestPluginManagerIntegration:
    """プラグインマネージャー統合テスト"""
    
    async def test_multiple_plugins(self):
        """複数プラグイン管理テスト"""
        manager = PluginManager()
        
        # 複数プラグインロード
        await manager.load_plugin(MockPlugin)
        await manager.load_plugin(ParameterValidationPlugin)
        
        # 全プラグイン初期化
        results = await manager.initialize_all()
        assert all(results.values())
        
        # 各プラグイン実行
        result1 = await manager.execute_plugin("mock_plugin", param="test")
        result2 = await manager.execute_plugin(
            "param_validation",
            required_param="test"
        )
        
        assert result1["result"] == "success"
        assert result2["required_param"] == "test"
        
        # 統計情報確認
        stats = manager.get_statistics()
        assert stats["total_plugins"] == 2
        assert stats["total_executions"] == 2
        assert stats["success_rate"] == 100.0
    
    async def test_lifecycle(self):
        """プラグインライフサイクルテスト"""
        manager = PluginManager()
        
        # ロード
        await manager.load_plugin(MockPlugin)
        plugin = manager.get_plugin("mock_plugin")
        assert plugin.status == PluginStatus.UNINITIALIZED
        
        # 初期化
        await manager.initialize_plugin("mock_plugin")
        assert plugin.status == PluginStatus.READY
        
        # 実行
        result = await manager.execute_plugin("mock_plugin")
        assert result["result"] == "success"
        
        # 無効化
        manager.disable_plugin("mock_plugin")
        assert not plugin.is_enabled()
        
        # 有効化
        manager.enable_plugin("mock_plugin")
        assert plugin.metadata.enabled is True
        
        # クリーンアップ
        await manager.cleanup_plugin("mock_plugin")
        
        # アンロード
        manager.unload_plugin("mock_plugin")
        assert "mock_plugin" not in manager.list_plugins()