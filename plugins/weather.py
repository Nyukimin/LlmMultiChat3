"""
天気プラグイン

OpenWeatherMap APIを使用して天気情報を取得します。
"""

import os
import logging
from typing import Any, Dict, List, Optional
import aiohttp

from plugins.base import (
    BasePlugin,
    PluginMetadata,
    PluginInitializationError,
    PluginExecutionError
)


logger = logging.getLogger(__name__)


class WeatherPlugin(BasePlugin):
    """
    天気プラグイン
    
    OpenWeatherMap APIを使用して都市の天気情報を取得します。
    
    Example:
        plugin = WeatherPlugin()
        await plugin.initialize()
        
        result = await plugin.execute(city="Tokyo")
        print(result)
        # {
        #     "city": "Tokyo",
        #     "temperature": 20.5,
        #     "feels_like": 19.8,
        #     "weather": "Clear",
        #     "description": "clear sky",
        #     "humidity": 65,
        #     "pressure": 1013,
        #     "wind_speed": 3.5
        # }
    """
    
    def __init__(self):
        """天気プラグイン初期化"""
        super().__init__(
            PluginMetadata(
                name="weather",
                version="1.0.0",
                description="OpenWeatherMap APIを使用して天気情報を取得",
                author="LlmMultiChat3 Team",
                dependencies=["aiohttp"]
            )
        )
        
        self.api_key: Optional[str] = None
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> bool:
        """
        プラグイン初期化
        
        環境変数からAPIキーを取得し、HTTPセッションを作成します。
        
        Returns:
            bool: 初期化成功時True、失敗時False
        
        Raises:
            PluginInitializationError: APIキーが設定されていない場合
        """
        try:
            # 環境変数からAPIキー取得
            self.api_key = os.getenv("OPENWEATHER_API_KEY")
            
            if not self.api_key:
                raise PluginInitializationError(
                    "OPENWEATHER_API_KEY environment variable not set. "
                    "Get your API key from: https://openweathermap.org/api"
                )
            
            # HTTPセッション作成
            self.session = aiohttp.ClientSession()
            
            logger.info("Weather plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize weather plugin: {e}")
            raise PluginInitializationError(f"Initialization failed: {e}")
    
    async def execute(
        self,
        city: str,
        units: str = "metric",
        lang: str = "ja"
    ) -> Dict[str, Any]:
        """
        天気情報取得
        
        Args:
            city: 都市名（例: "Tokyo", "London", "New York"）
            units: 単位系（"metric"=摂氏, "imperial"=華氏, "standard"=ケルビン）
            lang: 言語コード（デフォルト: "ja"）
        
        Returns:
            Dict[str, Any]: 天気情報
                - city: 都市名
                - temperature: 気温
                - feels_like: 体感温度
                - weather: 天気（短い説明）
                - description: 天気（詳細説明）
                - humidity: 湿度（%）
                - pressure: 気圧（hPa）
                - wind_speed: 風速（m/s or mph）
                - visibility: 視程（m）
                - clouds: 雲量（%）
        
        Raises:
            PluginExecutionError: API呼び出しに失敗した場合
        """
        if not self.session:
            raise PluginExecutionError("Plugin not initialized")
        
        try:
            # APIパラメータ
            params = {
                "q": city,
                "appid": self.api_key,
                "units": units,
                "lang": lang
            }
            
            # API呼び出し
            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("message", "Unknown error")
                    raise PluginExecutionError(
                        f"API request failed (status {response.status}): {error_message}"
                    )
                
                data = await response.json()
            
            # レスポンスパース
            result = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "temp_min": data["main"]["temp_min"],
                "temp_max": data["main"]["temp_max"],
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_deg": data["wind"].get("deg"),
                "visibility": data.get("visibility"),
                "clouds": data["clouds"]["all"],
                "sunrise": data["sys"]["sunrise"],
                "sunset": data["sys"]["sunset"],
                "timezone": data["timezone"],
                "units": units
            }
            
            logger.info(f"Successfully fetched weather for {city}")
            return result
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching weather for {city}: {e}")
            raise PluginExecutionError(f"HTTP error: {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise PluginExecutionError(f"Invalid API response: {e}")
        except Exception as e:
            logger.error(f"Error executing weather plugin: {e}")
            raise PluginExecutionError(f"Execution failed: {e}")
    
    async def cleanup(self) -> bool:
        """
        プラグインクリーンアップ
        
        HTTPセッションを閉じます。
        
        Returns:
            bool: クリーンアップ成功時True、失敗時False
        """
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            logger.info("Weather plugin cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up weather plugin: {e}")
            return False
    
    async def validate_params(
        self,
        city: Optional[str] = None,
        units: str = "metric",
        lang: str = "ja",
        **kwargs
    ) -> bool:
        """
        パラメータ検証
        
        Args:
            city: 都市名
            units: 単位系
            lang: 言語コード
            **kwargs: その他のパラメータ
        
        Returns:
            bool: パラメータが有効な場合True、無効な場合False
        """
        # 必須パラメータチェック
        if not city:
            logger.error("Parameter 'city' is required")
            return False
        
        if not isinstance(city, str) or len(city.strip()) == 0:
            logger.error("Parameter 'city' must be a non-empty string")
            return False
        
        # 単位系チェック
        valid_units = ["metric", "imperial", "standard"]
        if units not in valid_units:
            logger.error(
                f"Parameter 'units' must be one of {valid_units}, "
                f"got '{units}'"
            )
            return False
        
        return True
    
    def get_capabilities(self) -> List[str]:
        """
        プラグイン機能一覧取得
        
        Returns:
            List[str]: 機能名のリスト
        """
        return [
            "current_weather",
            "temperature",
            "humidity",
            "wind_speed",
            "pressure",
            "visibility"
        ]
    
    def get_required_params(self) -> List[str]:
        """
        必須パラメータ一覧取得
        
        Returns:
            List[str]: 必須パラメータ名のリスト
        """
        return ["city"]
    
    def get_optional_params(self) -> Dict[str, Any]:
        """
        オプショナルパラメータ一覧取得
        
        Returns:
            Dict[str, Any]: パラメータ名とデフォルト値の辞書
        """
        return {
            "units": "metric",
            "lang": "ja"
        }