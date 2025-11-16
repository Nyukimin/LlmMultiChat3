"""
翻訳プラグインテスト

翻訳プラグインの機能をテストします。
"""

import pytest
from unittest.mock import AsyncMock, patch
import os

from plugins.translate import TranslatePlugin
from plugins.base import (
    PluginStatus,
    PluginInitializationError,
    PluginExecutionError
)


@pytest.fixture
def translate_plugin():
    """翻訳プラグインフィクスチャ"""
    return TranslatePlugin()


@pytest.fixture
def mock_translate_response():
    """モック翻訳APIレスポンス"""
    return {
        "data": {
            "translations": [
                {
                    "translatedText": "こんにちは、世界！",
                    "detectedSourceLanguage": "en"
                }
            ]
        }
    }


@pytest.fixture
def mock_detect_response():
    """モック言語検出APIレスポンス"""
    return {
        "data": {
            "detections": [
                [
                    {
                        "language": "en",
                        "confidence": 0.95
                    }
                ]
            ]
        }
    }


@pytest.fixture
def mock_languages_response():
    """モックサポート言語APIレスポンス"""
    return {
        "data": {
            "languages": [
                {"language": "en", "name": "English"},
                {"language": "ja", "name": "Japanese"},
                {"language": "zh", "name": "Chinese"}
            ]
        }
    }


@pytest.mark.asyncio
class TestTranslatePlugin:
    """翻訳プラグインテスト"""
    
    async def test_initialization_success(self, translate_plugin):
        """初期化成功テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            success = await translate_plugin.initialize()
            
            assert success is True
            assert translate_plugin.api_key == "test_api_key"
            assert translate_plugin.session is not None
            
            # クリーンアップ
            await translate_plugin.cleanup()
    
    async def test_initialization_no_api_key(self, translate_plugin):
        """APIキーなし初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(PluginInitializationError) as exc_info:
                await translate_plugin.initialize()
            
            assert "GOOGLE_TRANSLATE_API_KEY" in str(exc_info.value)
    
    async def test_execute_success(self, translate_plugin, mock_translate_response):
        """翻訳成功テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            # モックレスポンス設定
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_translate_response)
            
            with patch.object(
                translate_plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await translate_plugin.execute(
                    text="Hello, world!",
                    target_lang="ja"
                )
                
                assert result["original_text"] == "Hello, world!"
                assert result["translated_text"] == "こんにちは、世界！"
                assert result["target_lang"] == "ja"
                assert result["detected_source_lang"] == "en"
            
            await translate_plugin.cleanup()
    
    async def test_execute_with_source_lang(self, translate_plugin, mock_translate_response):
        """翻訳元言語指定テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_translate_response)
            
            with patch.object(
                translate_plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await translate_plugin.execute(
                    text="Hello, world!",
                    target_lang="ja",
                    source_lang="en"
                )
                
                assert result["source_lang"] == "en"
            
            await translate_plugin.cleanup()
    
    async def test_execute_html_format(self, translate_plugin, mock_translate_response):
        """HTMLフォーマット翻訳テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_translate_response)
            
            with patch.object(
                translate_plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await translate_plugin.execute(
                    text="<p>Hello, world!</p>",
                    target_lang="ja",
                    format="html"
                )
                
                assert result["translated_text"] is not None
            
            await translate_plugin.cleanup()
    
    async def test_execute_api_error(self, translate_plugin):
        """API呼び出しエラーテスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            # モックエラーレスポンス
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value={
                "error": {"message": "Invalid request"}
            })
            
            with patch.object(
                translate_plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                with pytest.raises(PluginExecutionError) as exc_info:
                    await translate_plugin.execute(
                        text="Test",
                        target_lang="invalid"
                    )
                
                assert "400" in str(exc_info.value)
            
            await translate_plugin.cleanup()
    
    async def test_execute_not_initialized(self, translate_plugin):
        """未初期化実行テスト"""
        with pytest.raises(PluginExecutionError) as exc_info:
            await translate_plugin.execute(
                text="Hello",
                target_lang="ja"
            )
        
        assert "not initialized" in str(exc_info.value)
    
    async def test_detect_language(self, translate_plugin, mock_detect_response):
        """言語検出テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_detect_response)
            
            with patch.object(
                translate_plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await translate_plugin.detect_language("Hello, world!")
                
                assert result["text"] == "Hello, world!"
                assert result["language"] == "en"
                assert result["confidence"] == 0.95
            
            await translate_plugin.cleanup()
    
    async def test_get_supported_languages(self, translate_plugin, mock_languages_response):
        """サポート言語一覧取得テスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_languages_response)
            
            with patch.object(
                translate_plugin.session,
                "get",
                return_value=mock_response
            ) as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await translate_plugin.get_supported_languages()
                
                assert result["target_lang"] == "en"
                assert len(result["languages"]) == 3
                assert result["languages"][0]["language"] == "en"
            
            await translate_plugin.cleanup()
    
    async def test_validate_params_valid(self, translate_plugin):
        """パラメータ検証（有効）テスト"""
        is_valid = await translate_plugin.validate_params(
            text="Hello",
            target_lang="ja",
            source_lang="en",
            format="text"
        )
        
        assert is_valid is True
    
    async def test_validate_params_no_text(self, translate_plugin):
        """パラメータ検証（テキストなし）テスト"""
        is_valid = await translate_plugin.validate_params(target_lang="ja")
        assert is_valid is False
        
        is_valid = await translate_plugin.validate_params(
            text="",
            target_lang="ja"
        )
        assert is_valid is False
    
    async def test_validate_params_no_target_lang(self, translate_plugin):
        """パラメータ検証（翻訳先言語なし）テスト"""
        is_valid = await translate_plugin.validate_params(text="Hello")
        assert is_valid is False
    
    async def test_validate_params_invalid_format(self, translate_plugin):
        """パラメータ検証（無効なフォーマット）テスト"""
        is_valid = await translate_plugin.validate_params(
            text="Hello",
            target_lang="ja",
            format="invalid"
        )
        
        assert is_valid is False
    
    async def test_cleanup(self, translate_plugin):
        """クリーンアップテスト"""
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await translate_plugin.initialize()
            
            success = await translate_plugin.cleanup()
            
            assert success is True
            assert translate_plugin.session is None
    
    async def test_get_capabilities(self, translate_plugin):
        """機能一覧取得テスト"""
        capabilities = translate_plugin.get_capabilities()
        
        assert "translate" in capabilities
        assert "detect_language" in capabilities
        assert "get_supported_languages" in capabilities
    
    async def test_get_required_params(self, translate_plugin):
        """必須パラメータ取得テスト"""
        required = translate_plugin.get_required_params()
        
        assert "text" in required
        assert "target_lang" in required
    
    async def test_get_optional_params(self, translate_plugin):
        """オプショナルパラメータ取得テスト"""
        optional = translate_plugin.get_optional_params()
        
        assert "source_lang" in optional
        assert optional["source_lang"] is None
        assert "format" in optional
        assert optional["format"] == "text"


@pytest.mark.asyncio
class TestTranslatePluginIntegration:
    """翻訳プラグイン統合テスト"""
    
    async def test_full_lifecycle(self):
        """フルライフサイクルテスト"""
        plugin = TranslatePlugin()
        
        # メタデータ確認
        metadata = plugin.get_metadata()
        assert metadata.name == "translate"
        assert metadata.version == "1.0.0"
        
        # 初期ステータス
        assert plugin.status == PluginStatus.UNINITIALIZED
        
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            # 初期化
            await plugin.initialize()
            assert plugin.status == PluginStatus.READY
            
            # モック実行
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "data": {
                    "translations": [
                        {
                            "translatedText": "こんにちは",
                            "detectedSourceLanguage": "en"
                        }
                    ]
                }
            })
            
            with patch.object(
                plugin.session,
                "post",
                return_value=mock_response
            ) as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await plugin.execute(
                    text="Hello",
                    target_lang="ja"
                )
                assert result["translated_text"] == "こんにちは"
            
            # クリーンアップ
            await plugin.cleanup()
            assert plugin.session is None
    
    async def test_multiple_translations(self):
        """複数翻訳テスト"""
        plugin = TranslatePlugin()
        
        with patch.dict(os.environ, {"GOOGLE_TRANSLATE_API_KEY": "test_api_key"}):
            await plugin.initialize()
            
            texts = [
                ("Hello", "ja", "こんにちは"),
                ("Thank you", "ja", "ありがとう"),
                ("Goodbye", "ja", "さようなら")
            ]
            
            for text, target_lang, expected in texts:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "data": {
                        "translations": [
                            {
                                "translatedText": expected,
                                "detectedSourceLanguage": "en"
                            }
                        ]
                    }
                })
                
                with patch.object(
                    plugin.session,
                    "post",
                    return_value=mock_response
                ) as mock_post:
                    mock_post.return_value.__aenter__.return_value = mock_response
                    
                    result = await plugin.execute(
                        text=text,
                        target_lang=target_lang
                    )
                    assert result["translated_text"] == expected
            
            await plugin.cleanup()