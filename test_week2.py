"""
test_week2.py
Week 2 実装の統合テスト

各モジュールの基本動作を確認するテストスクリプト。
"""

import sys
from datetime import datetime

def print_section(title):
    """セクションヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_config():
    """config.py のテスト"""
    print_section("1. Config モジュールのテスト")
    
    try:
        from config import Config
        config = Config()
        
        print("✓ Config インポート成功")
        print(f"  - Ollama Host: {config.ollama_host}")
        print(f"  - Max Turns: {config.max_turns}")
        print(f"  - Search Enabled: {config.enable_search}")
        print(f"  - Models: {list(config.models.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Config エラー: {e}")
        return False

def test_conversation_state():
    """conversation_state.py のテスト"""
    print_section("2. ConversationState モジュールのテスト")
    
    try:
        from conversation_state import ConversationState
        
        state = ConversationState()
        print("✓ ConversationState インポート成功")
        
        # セッション開始
        state.start_new_session()
        print(f"✓ セッション開始: {state.session_id}")
        
        # ターン追加
        state.add_turn("User", "こんにちは")
        state.add_turn("ルミナ", "こんにちは！")
        print(f"✓ ターン追加: {len(state.history)} ターン")
        
        # 履歴取得
        history = state.get_recent_history(2)
        print(f"✓ 履歴取得: {len(history)} ターン")
        
        return True
    except Exception as e:
        print(f"✗ ConversationState エラー: {e}")
        return False

def test_llm_nodes():
    """llm_nodes.py のテスト"""
    print_section("3. LLMNodes モジュールのテスト")
    
    try:
        from llm_nodes import LuminaNode, ClarisNode, NoxNode, RouterNode
        from config import Config
        
        config = Config()
        
        # ノードの初期化
        lumina = LuminaNode(config)
        claris = ClarisNode(config)
        nox = NoxNode(config)
        router = RouterNode(config)
        
        print("✓ LLMNodes インポート成功")
        print(f"  - ルミナ: {lumina.character_name}")
        print(f"  - クラリス: {claris.character_name}")
        print(f"  - ノクス: {nox.character_name}")
        
        # ルーティングテスト
        test_state = {
            'user_input': 'こんにちは',
            'history': [],
            'last_speaker': ''
        }
        next_char = router.route(test_state)
        print(f"✓ ルーティングテスト: {next_char}")
        
        return True
    except Exception as e:
        print(f"✗ LLMNodes エラー: {e}")
        return False

def test_utils():
    """utils.py のテスト"""
    print_section("4. Utils モジュールのテスト")
    
    try:
        from utils import Logger, ConversationExporter, SystemValidator
        from utils import format_timestamp, truncate_text, sanitize_filename
        
        print("✓ Utils インポート成功")
        
        # Logger テスト
        logger = Logger()
        print("✓ Logger 初期化成功")
        
        # Exporter テスト
        exporter = ConversationExporter()
        print("✓ ConversationExporter 初期化成功")
        
        # Validator テスト
        from config import Config
        config = Config()
        validation = SystemValidator.validate_config(config)
        print(f"✓ SystemValidator テスト: {validation}")
        
        # ユーティリティ関数テスト
        ts = format_timestamp()
        print(f"✓ format_timestamp: {ts}")
        
        text = truncate_text("これは長いテキストです" * 10, 20)
        print(f"✓ truncate_text: {text}")
        
        filename = sanitize_filename("test<>file.txt")
        print(f"✓ sanitize_filename: {filename}")
        
        return True
    except Exception as e:
        print(f"✗ Utils エラー: {e}")
        return False

def test_main():
    """main.py のテスト"""
    print_section("5. Main モジュールのテスト")
    
    try:
        from main import MultiLLMChat
        
        print("✓ Main インポート成功")
        print("  注意: 実際の実行にはOllamaサーバーが必要です")
        
        # 初期化テスト（Ollamaなしでもエラーにならない）
        try:
            chat = MultiLLMChat()
            print("✓ MultiLLMChat 初期化成功")
        except Exception as e:
            print(f"  注意: 初期化エラー（Ollamaサーバー未起動の可能性）: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Main エラー: {e}")
        return False

def test_check_system():
    """check_system.py のテスト"""
    print_section("6. CheckSystem モジュールのテスト")
    
    try:
        from check_system import SystemChecker
        
        print("✓ CheckSystem インポート成功")
        
        # システムチェック実行
        checker = SystemChecker()
        results = checker.run_all_checks()
        
        print("システムチェック結果:")
        for check, result in results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}: {result}")
        
        return True
    except Exception as e:
        print(f"✗ CheckSystem エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("  Week 2 統合テスト")
    print("  LangGraphコア実装の動作確認")
    print("=" * 60)
    print(f"  実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 各テストの実行
    results.append(("Config", test_config()))
    results.append(("ConversationState", test_conversation_state()))
    results.append(("LLMNodes", test_llm_nodes()))
    results.append(("Utils", test_utils()))
    results.append(("Main", test_main()))
    results.append(("CheckSystem", test_check_system()))
    
    # 結果サマリー
    print_section("テスト結果サマリー")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n🎉 すべてのテストに成功しました！")
        print("\n次のステップ:")
        print("  1. Ollamaサーバーを起動: ollama serve")
        print("  2. モデルをプル:")
        print("     ollama pull 7shi/llm-jp-3-ezo-humanities:3.7b-instruct-q8_0")
        print("     ollama pull amoral-gemma3:latest")
        print("     ollama pull dsasai/llama3-elyza-jp-8b:latest")
        print("  3. システムチェック: python check_system.py")
        print("  4. メイン実行: python main.py")
    else:
        print("\n⚠️  一部のテストに失敗しました。")
        print("エラー内容を確認して修正してください。")
    
    print("\n" + "=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)