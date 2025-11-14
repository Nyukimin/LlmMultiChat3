"""
天気プラグインテスト

天気プラグインの機能をテストします。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientError
import os

from plugins.weather import WeatherPlugin
from plugins.base import (
    PluginStatus,
    PluginInitializationError,
    PluginExecutionError
)


@pytest.fixture
def weather_plugin():
    """天気プラグインフィクスチャ"""
    return WeatherPlugin()


@pytest.fixture
def mock_weather_response():
    """モック天気APIレスポンス"""
    return {
        "name": "Tokyo",
        "sys": {
            "country": "JP",
            "sunrise": 1234567890,
            "sunset": 1234567890
        },
        "main": {
            "temp": 20.5,
            "feels_like": 19.8,
            "temp_min": 18.0,
            "temp_max": 23.0,
            "humidity": 65,
            "pressure": 1013
        },
        "weather": [
            {
                "main": "Clear",
                "description": "clear sky"
            }
        ],
        "wind": {
            "speed": 3.5,
            "deg": 180
        },
        "clouds": {
            "all": 10
        },
        "visibility": 10000,
        "timezone": 32400
    }


@pytest.mark.asyncio
class TestWeatherPlugin:
    """天気プラグインテスト"""
    
    async def test_initialization_success(self, weather_plugin):
        """初期化成功テスト"""
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            success = await weather_plugin.initialize()
            
            assert success is True
            assert weather_plugin.api_key == "test_api_key"
            assert weather_plugin.session is not None
            
            # クリーンアップ
            await weather_plugin.cleanup()
    
    async def test_initialization_no_api_key(self, weather_plugin):
        """APIキーなし初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(PluginInitializationError) as exc_info:
                await weather_plugin.initialize()
            
            assert "OPENWEATHER_API_KEY" in str(exc_info.value)
    
    async def test_execute_success(self, weather_plugin, mock_weather_response):
        """天気取得成功テスト"""
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            await weather_plugin.initialize()
            
            # モックレスポンス設定
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_weather_response)
            
            with patch.object(
                weather_plugin.session,
                "get",
                return_value=mock_response
            ) as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await weather_plugin.execute(city="Tokyo")
                
                assert result["city"] == "Tokyo"
                assert result["country"] == "JP"
                assert result["temperature"] == 20.5
                assert result["feels_like"] == 19.8
                assert result["weather"] == "Clear"
                assert result["description"] == "clear sky"
                assert result["humidity"] == 65
                assert result["pressure"] == 1013
                assert result["wind_speed"] == 3.5
            
            await weather_plugin.cleanup()
    
    async def test_execute_with_units(self, weather_plugin, mock_weather_response):
        """単位系指定テスト"""
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            await weather_plugin.initialize()
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_weather_response)
            
            with patch.object(
                weather_plugin.session,
                "get",
                return_value=mock_response
            ) as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                # Imperial単位系
                result = await weather_plugin.execute(
                    city="New York",
                    units="imperial"
                )
                
                assert result["units"] == "imperial"
            
            await weather_plugin.cleanup()
    
    async def test_execute_api_error(self, weather_plugin):
        """API呼び出しエラーテスト"""
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            await weather_plugin.initialize()
            
            # モックエラーレスポンス
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.json = AsyncMock(return_value={
                "message": "city not found"
            })
            
            with patch.object(
                weather_plugin.session,
                "get",
                return_value=mock_response
            ) as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                with pytest.raises(PluginExecutionError) as exc_info:
                    await weather_plugin.execute(city="InvalidCity")
                
                assert "404" in str(exc_info.value)
            
            await weather_plugin.cleanup()
    
    async def test_execute_not_initialized(self, weather_plugin):
        """未初期化実行テスト"""
        with pytest.raises(PluginExecutionError) as exc_info:
            await weather_plugin.execute(city="Tokyo")
        
        assert "not initialized" in str(exc_info.value)
    
    async def test_validate_params_valid(self, weather_plugin):
        """パラメータ検証（有効）テスト"""
        is_valid = await weather_plugin.validate_params(
            city="Tokyo",
            units="metric",
            lang="ja"
        )
        
        assert is_valid is True
    
    async def test_validate_params_no_city(self, weather_plugin):
        """パラメータ検証（都市名なし）テスト"""
        is_valid = await weather_plugin.validate_params()
        assert is_valid is False
        
        is_valid = await weather_plugin.validate_params(city="")
        assert is_valid is False
    
    async def test_validate_params_invalid_units(self, weather_plugin):
        """パラメータ検証（無効な単位系）テスト"""
        is_valid = await weather_plugin.validate_params(
            city="Tokyo",
            units="invalid"
        )
        
        assert is_valid is False
    
    async def test_cleanup(self, weather_plugin):
        """クリーンアップテスト"""
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            await weather_plugin.initialize()
            
            success = await weather_plugin.cleanup()
            
            assert success is True
            assert weather_plugin.session is None
    
    async def test_get_capabilities(self, weather_plugin):
        """機能一覧取得テスト"""
        capabilities = weather_plugin.get_capabilities()
        
        assert "current_weather" in capabilities
        assert "temperature" in capabilities
        assert "humidity" in capabilities
        assert "wind_speed" in capabilities
    
    async def test_get_required_params(self, weather_plugin):
        """必須パラメータ取得テスト"""
        required = weather_plugin.get_required_params()
        
        assert "city" in required
    
    async def test_get_optional_params(self, weather_plugin):
        """オプショナルパラメータ取得テスト"""
        optional = weather_plugin.get_optional_params()
        
        assert "units" in optional
        assert optional["units"] == "metric"
        assert "lang" in optional
        assert optional["lang"] == "ja"


@pytest.mark.asyncio
class TestWeatherPluginIntegration:
    """天気プラグイン統合テスト"""
    
    async def test_full_lifecycle(self):
        """フルライフサイクルテスト"""
        plugin = WeatherPlugin()
        
        # メタデータ確認
        metadata = plugin.get_metadata()
        assert metadata.name == "weather"
        assert metadata.version == "1.0.0"
        
        # 初期ステータス
        assert plugin.status == PluginStatus.UNINITIALIZED
        
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            # 初期化
            await plugin.initialize()
            assert plugin.status == PluginStatus.READY
            
            # モック実行
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "name": "Tokyo",
                "sys": {"country": "JP", "sunrise": 0, "sunset": 0},
                "main": {
                    "temp": 20.5,
                    "feels_like": 19.8,
                    "temp_min": 18.0,
                    "temp_max": 23.0,
                    "humidity": 65,
                    "pressure": 1013
                },
                "weather": [{"main": "Clear", "description": "clear sky"}],
                "wind": {"speed": 3.5, "deg": 180},
                "clouds": {"all": 10},
                "visibility": 10000,
                "timezone": 32400
            })
            
            with patch.object(
                plugin.session,
                "get",
                return_value=mock_response
            ) as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await plugin.execute(city="Tokyo")
                assert result["city"] == "Tokyo"
            
            # クリーンアップ
            await plugin.cleanup()
            assert plugin.session is None
    
    async def test_multiple_cities(self):
        """複数都市取得テスト"""
        plugin = WeatherPlugin()
        
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_api_key"}):
            await plugin.initialize()
            
            cities = ["Tokyo", "London", "New York"]
            
            for city in cities:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "name": city,
                    "sys": {"country": "XX", "sunrise": 0, "sunset": 0},
                    "main": {
                        "temp": 20.0,
                        "feels_like": 19.0,
                        "temp_min": 18.0,
                        "temp_max": 22.0,
                        "humidity": 60,
                        "pressure": 1010
                    },
                    "weather": [{"main": "Clear", "description": "clear"}],
                    "wind": {"speed": 3.0, "deg": 180},
                    "clouds": {"all": 0},
                    "visibility": 10000,
                    "timezone": 0
                })
                
                with patch.object(
                    plugin.session,
                    "get",
                    return_value=mock_response
                ) as mock_get:
                    mock_get.return_value.__aenter__.return_value = mock_response
                    
                    result = await plugin.execute(city=city)
                    assert result["city"] == city
            
            await plugin.cleanup()