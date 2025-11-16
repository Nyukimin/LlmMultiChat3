"""Ollama疎通確認スクリプト"""
import requests
import json

def check_ollama_connection():
    """Ollama APIの疎通確認"""
    print("🔍 Ollama疎通確認開始...\n")
    
    # 1. Ollamaサーバー起動確認
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollamaサーバー: 起動中")
            models = response.json().get("models", [])
            print(f"✅ 登録モデル数: {len(models)}")
            for model in models:
                print(f"  - {model['name']} ({model['details']['parameter_size']})")
        else:
            print(f"❌ Ollamaサーバー: エラー (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Ollamaサーバー: 接続失敗 ({e})")
        return False
    
    # 2. phi3:mini推論テスト
    print("\n🧪 phi3:mini推論テスト...")
    try:
        payload = {
            "model": "phi3:mini",
            "prompt": "Hello! Please respond in one sentence.",
            "stream": False
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 推論成功")
            print(f"   応答: {result.get('response', '')[:100]}...")
            print(f"   所要時間: {result.get('total_duration', 0) / 1e9:.2f}秒")
            return True
        else:
            print(f"❌ 推論失敗 (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 推論エラー: {e}")
        return False

if __name__ == "__main__":
    success = check_ollama_connection()
    print("\n" + "="*50)
    if success:
        print("✅ Ollama疎通確認: 成功")
        print("テスト実行可能です。")
    else:
        print("❌ Ollama疎通確認: 失敗")
        print("Ollamaサーバーを起動してください: ollama serve")
    print("="*50)