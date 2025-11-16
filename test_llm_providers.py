"""LLMプロバイダー疎通確認スクリプト"""
import os
import requests
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

def test_ollama():
    """Ollama疎通確認"""
    print("🔍 Ollama疎通確認...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama: 起動中（モデル数: {len(models)}）")
            for model in models:
                print(f"  - {model['name']}")
            return True
        else:
            print(f"❌ Ollama: エラー (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Ollama: 接続失敗 ({e})")
        return False

def test_openai():
    """OpenAI API疎通確認"""
    print("\n🔍 OpenAI API疎通確認...")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠️ OpenAI: APIキー未設定")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ OpenAI: 認証成功（利用可能モデル: {len(response.json().get('data', []))}）")
            return True
        else:
            print(f"❌ OpenAI: 認証失敗 (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ OpenAI: 接続失敗 ({e})")
        return False

def test_anthropic():
    """Anthropic Claude API疎通確認"""
    print("\n🔍 Anthropic Claude API疎通確認...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("⚠️ Anthropic: APIキー未設定")
        return False
    
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Anthropic: 認証成功（Claude 3 Haiku利用可能）")
            return True
        else:
            print(f"❌ Anthropic: 認証失敗 (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Anthropic: 接続失敗 ({e})")
        return False

def test_google_ai():
    """Google AI API疎通確認"""
    print("\n🔍 Google AI API疎通確認...")
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "your_google_api_key_here":
        print("⚠️ Google AI: APIキー未設定")
        return False
    
    try:
        response = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Google AI: 認証成功（利用可能モデル: {len(models)}）")
            return True
        else:
            print(f"❌ Google AI: 認証失敗 (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Google AI: 接続失敗 ({e})")
        return False

if __name__ == "__main__":
    print("="*50)
    print("LLMプロバイダー疎通確認")
    print("="*50)
    
    results = {
        "Ollama": test_ollama(),
        "OpenAI": test_openai(),
        "Anthropic": test_anthropic(),
        "Google AI": test_google_ai()
    }
    
    print("\n" + "="*50)
    print("📊 結果サマリー")
    print("="*50)
    
    for provider, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{provider:15} : {status}")
    
    available_count = sum(results.values())
    print(f"\n利用可能プロバイダー: {available_count}/4")
    
    if available_count >= 2:
        print("✅ フォールバック機能利用可能（複数プロバイダー設定済み）")
    elif available_count == 1:
        print("⚠️ 単一プロバイダーのみ（フォールバック不可）")
    else:
        print("❌ 利用可能なプロバイダーなし")
    
    print("="*50)