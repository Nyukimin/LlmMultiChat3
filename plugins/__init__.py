"""
プラグインモジュール

プラグインシステムのエントリポイントを提供します。
"""

from plugins.base import (
    BasePlugin,
    PluginMetadata,
    PluginStatus,
    PluginError,
    PluginInitializationError,
    PluginExecutionError
)

from plugins.weather import WeatherPlugin
from plugins.translate import TranslatePlugin

__all__ = [
    # ベースクラス
    "BasePlugin",
    "PluginMetadata",
    "PluginStatus",
    
    # 例外
    "PluginError",
    "PluginInitializationError",
    "PluginExecutionError",
    
    # プラグイン
    "WeatherPlugin",
    "TranslatePlugin",
]

__version__ = "1.0.0"