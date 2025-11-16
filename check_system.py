"""
check_system.py
システム診断ツール（Phase 1必須）
"""

import sys
from pathlib import Path
from typing import Dict
import requests
from config import Config

# 設定読み込み
config = Config()


class SystemChecker:
    """システム環境チェッカー"""
    
    @staticmethod
    def check_ollama_connection() -> bool:
        """Ollama接続チェック"""
        try:
            response = requests.get(
                f"{config.model.ollama_host}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"  ❌ Ollama接続エラー: {e}")
            return False
    
    @staticmethod
    def check_models_availability(models: Dict[str, str]) -> Dict[str, bool]:
        """モデル可用性チェック"""
        results = {}
        try:
            response = requests.get(
                f"{config.model.ollama_host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                available_models = [m["name"] for m in response.json().get("models", [])]
                for char_name, model_name in models.items():
                    results[char_name] = model_name in available_models
            else:
                results = {char: False for char in models}
        except Exception as e:
            print(f"  ❌ モデルチェックエラー: {e}")
            results = {char: False for char in models}
        return results
    
    @staticmethod
    def check_api_key() -> bool:
        """APIキーチェック"""
        return bool(config.system.serper_api_key)
    
    @staticmethod
    def check_directories() -> Dict[str, bool]:
        """必須ディレクトリチェック"""
        required_dirs = [
            "data",
            "data/memories",
            "data/sessions",
            "data/knowledge_base",
            "characters"
        ]
        results = {}
        for dir_path in required_dirs:
            path = Path(dir_path)
            results[dir_path] = path.exists() and path.is_dir()
        return results


def main():
    """システムチェック実行"""
    print("=" * 50)
    print("🔍 LlmMultiChat3 システムチェック")
    print("=" * 50)
    
    # 1. Ollama接続
    print("\n📡 Ollama接続チェック...")
    ollama_ok = SystemChecker.check_ollama_connection()
    print(f"  {'✅' if ollama_ok else '❌'} Ollama: {'接続成功' if ollama_ok else '接続失敗'}")
    
    # 2. モデル可用性
    print("\n🤖 モデル可用性チェック...")
    models_status = SystemChecker.check_models_availability(config.model.models)
    for char_name, available in models_status.items():
        status = "✅" if available else "❌"
        model_name = config.model.models[char_name]
        print(f"  {status} {char_name}: {model_name}")
    
    # 3. APIキー
    print("\n🔑 APIキーチェック...")
    api_key_ok = SystemChecker.check_api_key()
    print(f"  {'✅' if api_key_ok else '❌'} Serper API Key: {'設定済' if api_key_ok else '未設定'}")
    
    # 4. ディレクトリ構造
    print("\n📁 ディレクトリ構造チェック...")
    dirs_status = SystemChecker.check_directories()
    for dir_path, exists in dirs_status.items():
        print(f"  {'✅' if exists else '❌'} {dir_path}")
    
    # 5. 総合判定
    print("\n" + "=" * 50)
    all_checks = [
        ollama_ok,
        all(models_status.values()),
        api_key_ok,
        all(dirs_status.values())
    ]
    
    if all(all_checks):
        print("✅ すべてのチェックに合格しました！")
        print("   → python main.py で実行できます")
        sys.exit(0)
    else:
        print("❌ 一部のチェックに失敗しました")
        print("\n🔧 対処方法:")
        
        if not ollama_ok:
            print("  1. Ollamaを起動してください")
            print("     ollama serve")
        
        if not all(models_status.values()):
            print("  2. 必要なモデルをダウンロードしてください")
            for char_name, available in models_status.items():
                if not available:
                    model_name = config.model.models[char_name]
                    print(f"     ollama pull {model_name}")
        
        if not api_key_ok:
            print("  3. .envファイルにSERPER_API_KEYを設定してください")
        
        if not all(dirs_status.values()):
            print("  4. 必須ディレクトリを作成してください")
            for dir_path, exists in dirs_status.items():
                if not exists:
                    print(f"     mkdir -p {dir_path}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()