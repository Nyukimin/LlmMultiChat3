"""
翻訳プラグイン

Google Translate APIを使用してテキストを翻訳します。
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


class TranslatePlugin(BasePlugin):
    """
    翻訳プラグイン
    
    Google Translate APIを使用してテキストを翻訳します。
    
    Example:
        plugin = TranslatePlugin()
        await plugin.initialize()
        
        result = await plugin.execute(
            text="Hello, world!",
            target_lang="ja"
        )
        print(result)
        # {
        #     "original_text": "Hello, world!",
        #     "translated_text": "こんにちは、世界！",
        #     "source_lang": "en",
        #     "target_lang": "ja"
        # }
    """
    
    def __init__(self):
        """翻訳プラグイン初期化"""
        super().__init__(
            PluginMetadata(
                name="translate",
                version="1.0.0",
                description="Google Translate APIを使用してテキストを翻訳",
                author="LlmMultiChat3 Team",
                dependencies=["aiohttp"]
            )
        )
        
        self.api_key: Optional[str] = None
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
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
            self.api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
            
            if not self.api_key:
                raise PluginInitializationError(
                    "GOOGLE_TRANSLATE_API_KEY environment variable not set. "
                    "Get your API key from: https://cloud.google.com/translate/docs/setup"
                )
            
            # HTTPセッション作成
            self.session = aiohttp.ClientSession()
            
            logger.info("Translate plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize translate plugin: {e}")
            raise PluginInitializationError(f"Initialization failed: {e}")
    
    async def execute(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        format: str = "text"
    ) -> Dict[str, Any]:
        """
        テキスト翻訳
        
        Args:
            text: 翻訳するテキスト
            target_lang: 翻訳先言語コード（例: "ja", "en", "zh", "ko"）
            source_lang: 翻訳元言語コード（未指定時は自動検出）
            format: テキストフォーマット（"text" or "html"）
        
        Returns:
            Dict[str, Any]: 翻訳結果
                - original_text: 元のテキスト
                - translated_text: 翻訳されたテキスト
                - source_lang: 翻訳元言語コード
                - target_lang: 翻訳先言語コード
                - detected_source_lang: 検出された元言語コード（source_lang未指定時）
        
        Raises:
            PluginExecutionError: API呼び出しに失敗した場合
        """
        if not self.session:
            raise PluginExecutionError("Plugin not initialized")
        
        try:
            # APIパラメータ
            params = {
                "key": self.api_key,
                "q": text,
                "target": target_lang,
                "format": format
            }
            
            if source_lang:
                params["source"] = source_lang
            
            # API呼び出し
            async with self.session.post(self.base_url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    raise PluginExecutionError(
                        f"API request failed (status {response.status}): {error_message}"
                    )
                
                data = await response.json()
            
            # レスポンスパース
            translation = data["data"]["translations"][0]
            
            result = {
                "original_text": text,
                "translated_text": translation["translatedText"],
                "target_lang": target_lang,
                "source_lang": source_lang,
                "detected_source_lang": translation.get("detectedSourceLanguage")
            }
            
            logger.info(
                f"Successfully translated text from "
                f"{result.get('detected_source_lang') or source_lang} to {target_lang}"
            )
            return result
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error translating text: {e}")
            raise PluginExecutionError(f"HTTP error: {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise PluginExecutionError(f"Invalid API response: {e}")
        except Exception as e:
            logger.error(f"Error executing translate plugin: {e}")
            raise PluginExecutionError(f"Execution failed: {e}")
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        言語検出
        
        Args:
            text: 言語を検出するテキスト
        
        Returns:
            Dict[str, Any]: 検出結果
                - text: 元のテキスト
                - language: 検出された言語コード
                - confidence: 信頼度（0.0-1.0）
        
        Raises:
            PluginExecutionError: API呼び出しに失敗した場合
        """
        if not self.session:
            raise PluginExecutionError("Plugin not initialized")
        
        try:
            # APIパラメータ
            url = f"{self.base_url}/detect"
            params = {
                "key": self.api_key,
                "q": text
            }
            
            # API呼び出し
            async with self.session.post(url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    raise PluginExecutionError(
                        f"API request failed (status {response.status}): {error_message}"
                    )
                
                data = await response.json()
            
            # レスポンスパース
            detection = data["data"]["detections"][0][0]
            
            result = {
                "text": text,
                "language": detection["language"],
                "confidence": detection["confidence"]
            }
            
            logger.info(f"Detected language: {result['language']} (confidence: {result['confidence']})")
            return result
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            raise PluginExecutionError(f"Language detection failed: {e}")
    
    async def get_supported_languages(
        self,
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        サポート言語一覧取得
        
        Args:
            target_lang: 言語名の表示言語コード（デフォルト: "en"）
        
        Returns:
            Dict[str, Any]: サポート言語一覧
                - languages: 言語リスト
                    - language: 言語コード
                    - name: 言語名
        
        Raises:
            PluginExecutionError: API呼び出しに失敗した場合
        """
        if not self.session:
            raise PluginExecutionError("Plugin not initialized")
        
        try:
            # APIパラメータ
            url = f"{self.base_url}/languages"
            params = {
                "key": self.api_key,
                "target": target_lang
            }
            
            # API呼び出し
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    raise PluginExecutionError(
                        f"API request failed (status {response.status}): {error_message}"
                    )
                
                data = await response.json()
            
            # レスポンスパース
            languages = data["data"]["languages"]
            
            result = {
                "target_lang": target_lang,
                "languages": languages
            }
            
            logger.info(f"Retrieved {len(languages)} supported languages")
            return result
            
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            raise PluginExecutionError(f"Failed to get supported languages: {e}")
    
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
            
            logger.info("Translate plugin cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up translate plugin: {e}")
            return False
    
    async def validate_params(
        self,
        text: Optional[str] = None,
        target_lang: Optional[str] = None,
        source_lang: Optional[str] = None,
        format: str = "text",
        **kwargs
    ) -> bool:
        """
        パラメータ検証
        
        Args:
            text: 翻訳するテキスト
            target_lang: 翻訳先言語コード
            source_lang: 翻訳元言語コード
            format: テキストフォーマット
            **kwargs: その他のパラメータ
        
        Returns:
            bool: パラメータが有効な場合True、無効な場合False
        """
        # 必須パラメータチェック
        if not text:
            logger.error("Parameter 'text' is required")
            return False
        
        if not isinstance(text, str) or len(text.strip()) == 0:
            logger.error("Parameter 'text' must be a non-empty string")
            return False
        
        if not target_lang:
            logger.error("Parameter 'target_lang' is required")
            return False
        
        if not isinstance(target_lang, str) or len(target_lang) == 0:
            logger.error("Parameter 'target_lang' must be a non-empty string")
            return False
        
        # フォーマットチェック
        valid_formats = ["text", "html"]
        if format not in valid_formats:
            logger.error(
                f"Parameter 'format' must be one of {valid_formats}, "
                f"got '{format}'"
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
            "translate",
            "detect_language",
            "get_supported_languages"
        ]
    
    def get_required_params(self) -> List[str]:
        """
        必須パラメータ一覧取得
        
        Returns:
            List[str]: 必須パラメータ名のリスト
        """
        return ["text", "target_lang"]
    
    def get_optional_params(self) -> Dict[str, Any]:
        """
        オプショナルパラメータ一覧取得
        
        Returns:
            Dict[str, Any]: パラメータ名とデフォルト値の辞書
        """
        return {
            "source_lang": None,
            "format": "text"
        }