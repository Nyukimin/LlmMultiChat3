"""
プラグインマネージャー

プラグインのロード、初期化、実行、管理を行います。
"""

import asyncio
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from plugins.base import (
    BasePlugin,
    PluginMetadata,
    PluginStatus,
    PluginError,
    PluginInitializationError,
    PluginExecutionError
)


logger = logging.getLogger(__name__)


class PluginManager:
    """
    プラグインマネージャー
    
    プラグインのライフサイクル管理を行います。
    - プラグインの動的ロード
    - 初期化・クリーンアップ
    - 実行・エラーハンドリング
    - 依存関係解決
    
    Example:
        manager = PluginManager()
        await manager.load_plugins_from_directory("plugins")
        await manager.initialize_all()
        
        result = await manager.execute_plugin("weather", city="Tokyo")
        print(result)
    """
    
    def __init__(self, plugin_directory: Optional[str] = None):
        """
        プラグインマネージャー初期化
        
        Args:
            plugin_directory: プラグインディレクトリパス（デフォルト: "plugins"）
        """
        self.plugin_directory = plugin_directory or "plugins"
        self._plugins: Dict[str, BasePlugin] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
    
    async def load_plugin(self, plugin_class: Type[BasePlugin]) -> bool:
        """
        プラグインクラスをロード
        
        Args:
            plugin_class: BasePluginを継承したプラグインクラス
        
        Returns:
            bool: ロード成功時True、失敗時False
        
        Raises:
            PluginError: プラグインロードに失敗した場合
        """
        try:
            # プラグインインスタンス作成
            plugin = plugin_class()
            
            # BasePluginを継承しているか確認
            if not isinstance(plugin, BasePlugin):
                raise PluginError(
                    f"{plugin_class.__name__} must inherit from BasePlugin"
                )
            
            # 既に同名プラグインが存在する場合は警告
            plugin_name = plugin.metadata.name
            if plugin_name in self._plugins:
                logger.warning(f"Plugin '{plugin_name}' already exists. Overwriting.")
            
            # プラグインを登録
            self._plugins[plugin_name] = plugin
            logger.info(f"Loaded plugin: {plugin_name} v{plugin.metadata.version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_class.__name__}: {e}")
            raise PluginError(f"Failed to load plugin: {e}")
    
    async def load_plugins_from_directory(self, directory: Optional[str] = None) -> int:
        """
        ディレクトリからプラグインを自動ロード
        
        Args:
            directory: プラグインディレクトリパス（デフォルト: self.plugin_directory）
        
        Returns:
            int: ロードしたプラグイン数
        """
        directory = directory or self.plugin_directory
        plugin_path = Path(directory)
        
        if not plugin_path.exists():
            logger.warning(f"Plugin directory '{directory}' does not exist")
            return 0
        
        loaded_count = 0
        
        # ディレクトリ内の.pyファイルを検索
        for py_file in plugin_path.glob("*.py"):
            # base.pyと__init__.pyはスキップ
            if py_file.stem in ["base", "__init__"]:
                continue
            
            try:
                # モジュールをインポート
                module_name = f"{directory.replace('/', '.')}.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # モジュール内のBasePluginサブクラスを検索
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BasePlugin) 
                        and obj is not BasePlugin
                        and obj.__module__ == module_name
                    ):
                        await self.load_plugin(obj)
                        loaded_count += 1
                
            except Exception as e:
                logger.error(f"Failed to load plugin from {py_file}: {e}")
        
        logger.info(f"Loaded {loaded_count} plugins from '{directory}'")
        return loaded_count
    
    async def initialize_plugin(self, plugin_name: str) -> bool:
        """
        特定プラグインを初期化
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            bool: 初期化成功時True、失敗時False
        
        Raises:
            PluginError: プラグインが存在しない場合
            PluginInitializationError: 初期化に失敗した場合
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise PluginError(f"Plugin '{plugin_name}' not found")
        
        try:
            plugin.set_status(PluginStatus.INITIALIZING)
            success = await plugin.initialize()
            
            if success:
                plugin.set_status(PluginStatus.READY)
                logger.info(f"Initialized plugin: {plugin_name}")
            else:
                plugin.set_status(
                    PluginStatus.ERROR,
                    "Initialization returned False"
                )
                logger.error(f"Failed to initialize plugin: {plugin_name}")
            
            return success
            
        except Exception as e:
            plugin.set_status(PluginStatus.ERROR, str(e))
            logger.error(f"Error initializing plugin '{plugin_name}': {e}")
            raise PluginInitializationError(f"Failed to initialize plugin: {e}")
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        全プラグインを初期化
        
        Returns:
            Dict[str, bool]: プラグイン名と初期化成功/失敗の辞書
        """
        results = {}
        
        for plugin_name in self._plugins:
            try:
                results[plugin_name] = await self.initialize_plugin(plugin_name)
            except Exception as e:
                results[plugin_name] = False
                logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
        
        return results
    
    async def execute_plugin(
        self,
        plugin_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        プラグインを実行
        
        Args:
            plugin_name: プラグイン名
            **kwargs: プラグイン固有のパラメータ
        
        Returns:
            Dict[str, Any]: 実行結果
        
        Raises:
            PluginError: プラグインが存在しない、または有効でない場合
            PluginExecutionError: 実行に失敗した場合
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise PluginError(f"Plugin '{plugin_name}' not found")
        
        if not plugin.is_enabled():
            raise PluginError(
                f"Plugin '{plugin_name}' is not enabled "
                f"(status: {plugin.status.value})"
            )
        
        start_time = datetime.utcnow()
        
        try:
            # パラメータ検証
            if not await plugin.validate_params(**kwargs):
                raise PluginExecutionError("Invalid parameters")
            
            # 実行
            result = await plugin.execute(**kwargs)
            
            # 実行履歴に記録
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._add_to_history(
                plugin_name=plugin_name,
                success=True,
                execution_time=execution_time,
                params=kwargs,
                result=result
            )
            
            logger.info(
                f"Executed plugin '{plugin_name}' "
                f"in {execution_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._add_to_history(
                plugin_name=plugin_name,
                success=False,
                execution_time=execution_time,
                params=kwargs,
                error=str(e)
            )
            
            logger.error(f"Error executing plugin '{plugin_name}': {e}")
            raise PluginExecutionError(f"Failed to execute plugin: {e}")
    
    async def cleanup_plugin(self, plugin_name: str) -> bool:
        """
        特定プラグインをクリーンアップ
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            bool: クリーンアップ成功時True、失敗時False
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        try:
            success = await plugin.cleanup()
            if success:
                logger.info(f"Cleaned up plugin: {plugin_name}")
            else:
                logger.warning(f"Cleanup returned False for plugin: {plugin_name}")
            return success
            
        except Exception as e:
            logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")
            return False
    
    async def cleanup_all(self) -> Dict[str, bool]:
        """
        全プラグインをクリーンアップ
        
        Returns:
            Dict[str, bool]: プラグイン名とクリーンアップ成功/失敗の辞書
        """
        results = {}
        
        for plugin_name in self._plugins:
            results[plugin_name] = await self.cleanup_plugin(plugin_name)
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        プラグインインスタンス取得
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            Optional[BasePlugin]: プラグインインスタンス（存在しない場合None）
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """
        ロード済みプラグイン名のリスト取得
        
        Returns:
            List[str]: プラグイン名のリスト
        """
        return list(self._plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        プラグイン情報取得
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            Optional[Dict[str, Any]]: プラグイン情報（存在しない場合None）
        """
        plugin = self._plugins.get(plugin_name)
        return plugin.to_dict() if plugin else None
    
    def get_all_plugins_info(self) -> Dict[str, Dict[str, Any]]:
        """
        全プラグイン情報取得
        
        Returns:
            Dict[str, Dict[str, Any]]: プラグイン名と情報の辞書
        """
        return {
            name: plugin.to_dict()
            for name, plugin in self._plugins.items()
        }
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        プラグインを有効化
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            bool: 成功時True、失敗時False
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        plugin.enable()
        logger.info(f"Enabled plugin: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        プラグインを無効化
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            bool: 成功時True、失敗時False
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        plugin.disable()
        logger.info(f"Disabled plugin: {plugin_name}")
        return True
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        プラグインをアンロード
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            bool: 成功時True、失敗時False
        """
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        del self._plugins[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")
        return True
    
    def get_execution_history(
        self,
        plugin_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        実行履歴取得
        
        Args:
            plugin_name: プラグイン名（指定時、該当プラグインのみ）
            limit: 取得件数
        
        Returns:
            List[Dict[str, Any]]: 実行履歴のリスト
        """
        history = self._execution_history
        
        if plugin_name:
            history = [
                h for h in history 
                if h["plugin_name"] == plugin_name
            ]
        
        return history[-limit:]
    
    def clear_execution_history(self):
        """実行履歴をクリア"""
        self._execution_history.clear()
        logger.info("Cleared execution history")
    
    def _add_to_history(
        self,
        plugin_name: str,
        success: bool,
        execution_time: float,
        params: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        実行履歴に追加
        
        Args:
            plugin_name: プラグイン名
            success: 成功/失敗
            execution_time: 実行時間（秒）
            params: パラメータ
            result: 実行結果（オプショナル）
            error: エラーメッセージ（オプショナル）
        """
        history_entry = {
            "plugin_name": plugin_name,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "execution_time": execution_time,
            "params": params,
            "result": result,
            "error": error
        }
        
        self._execution_history.append(history_entry)
        
        # 履歴サイズ制限
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        total_plugins = len(self._plugins)
        enabled_plugins = sum(
            1 for p in self._plugins.values() if p.is_enabled()
        )
        ready_plugins = sum(
            1 for p in self._plugins.values() 
            if p.status == PluginStatus.READY
        )
        
        total_executions = len(self._execution_history)
        successful_executions = sum(
            1 for h in self._execution_history if h["success"]
        )
        
        return {
            "total_plugins": total_plugins,
            "enabled_plugins": enabled_plugins,
            "ready_plugins": ready_plugins,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": total_executions - successful_executions,
            "success_rate": (
                successful_executions / total_executions * 100
                if total_executions > 0 else 0
            )
        }
    
    def __repr__(self) -> str:
        return (
            f"<PluginManager("
            f"plugins={len(self._plugins)}, "
            f"enabled={sum(1 for p in self._plugins.values() if p.is_enabled())}"
            f")>"
        )