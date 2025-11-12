"""
test_week3.py
Week 3 実装の統合テスト

記憶システム（短期・中期・長期・知識ベース）の基本動作を確認するテストスクリプト。
"""

import sys
from datetime import datetime

def print_section(title):
    """セクションヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_memory_base():
    """memory/base.py のテスト"""
    print_section("1. Memory Base モジュールのテスト")
    
    try:
        from memory.base import MemoryBackend, MemoryItem, MemoryConfig
        
        print("✓ Memory Base インポート成功")
        
        # MemoryConfig のテスト
        config = MemoryConfig()
        print(f"✓ MemoryConfig 初期化成功")
        print(f"  - 短期記憶最大アイテム数: {config.short_term_max_items}")
        print(f"  - 中期記憶TTL: {config.mid_term_ttl_seconds}秒")
        print(f"  - 知識ベース名前空間: {config.kb_namespaces}")
        
        # MemoryItem のテスト
        item = MemoryItem("test_key", "test_value", {"type": "test"})
        print(f"✓ MemoryItem 作成成功")
        print(f"  - キー: {item.key}")
        print(f"  - 値: {item.value}")
        
        return True
    except Exception as e:
        print(f"✗ Memory Base エラー: {e}")
        return False

def test_short_term_memory():
    """memory/short_term.py のテスト"""
    print_section("2. Short-Term Memory モジュールのテスト")
    
    try:
        from memory.short_term import ShortTermMemory, ConversationBuffer
        from memory.base import MemoryConfig
        
        print("✓ ShortTermMemory インポート成功")
        
        # ShortTermMemory のテスト
        stm = ShortTermMemory()
        print("✓ ShortTermMemory 初期化成功")
        
        # データの保存と取得
        stm.store("test1", "Hello World", {"type": "test"})
        retrieved = stm.retrieve("test1")
        print(f"✓ データ保存・取得成功: {retrieved}")
        
        # 統計情報
        stats = stm.get_stats()
        print(f"✓ 統計情報取得: {stats['current_items']} アイテム")
        
        # ConversationBuffer のテスト
        buffer = ConversationBuffer(max_turns=12)
        buffer.add_turn("User", "こんにちは")
        buffer.add_turn("ルミナ", "こんにちは！")
        print(f"✓ ConversationBuffer テスト: {len(buffer.get_recent_turns())} ターン")
        
        return True
    except Exception as e:
        print(f"✗ ShortTermMemory エラー: {e}")
        return False

def test_mid_term_memory():
    """memory/mid_term.py のテスト"""
    print_section("3. Mid-Term Memory モジュールのテスト")
    
    try:
        from memory.mid_term import MidTermMemory, SessionManager
        
        print("✓ MidTermMemory インポート成功")
        
        # MidTermMemory のテスト
        mtm = MidTermMemory(db_path="data/test_mid_term.db")
        print("✓ MidTermMemory 初期化成功")
        
        # セッションサマリーの保存
        session_id = "test_session_001"
        summary = {
            'total_turns': 10,
            'speakers': {'User': 5, 'ルミナ': 5}
        }
        mtm.store_session_summary(session_id, summary)
        print(f"✓ セッションサマリー保存成功")
        
        # セッションサマリーの取得
        retrieved = mtm.retrieve_session_summary(session_id)
        print(f"✓ セッションサマリー取得: {retrieved['total_turns']} ターン")
        
        # SessionManager のテスト
        session_mgr = SessionManager(mtm)
        print("✓ SessionManager 初期化成功")
        
        return True
    except Exception as e:
        print(f"✗ MidTermMemory エラー: {e}")
        return False

def test_long_term_memory():
    """memory/long_term.py のテスト"""
    print_section("4. Long-Term Memory モジュールのテスト")
    
    try:
        from memory.long_term import LongTermMemory, CharacterKPIManager
        
        print("✓ LongTermMemory インポート成功")
        
        # LongTermMemory のテスト
        ltm = LongTermMemory(data_dir="data/test_long_term")
        print("✓ LongTermMemory 初期化成功")
        
        # ユーザープロファイルの保存
        user_id = "user001"
        profile = {
            'name': 'テストユーザー',
            'preferences': {'language': 'ja', 'style': 'friendly'}
        }
        ltm.store_user_profile(user_id, profile)
        print(f"✓ ユーザープロファイル保存成功")
        
        # CharacterKPIManager のテスト
        kpi_mgr = CharacterKPIManager(ltm)
        kpi_mgr.initialize_character('ルミナ')
        kpi_mgr.increment_kpi('ルミナ', 'user_thumbs_up', 5)
        level = kpi_mgr.get_character_level('ルミナ')
        print(f"✓ CharacterKPI テスト: レベル {level}")
        
        return True
    except Exception as e:
        print(f"✗ LongTermMemory エラー: {e}")
        return False

def test_knowledge_base():
    """memory/knowledge_base.py のテスト"""
    print_section("5. Knowledge Base モジュールのテスト")
    
    try:
        from memory.knowledge_base import KnowledgeBase, KnowledgeBaseManager
        
        print("✓ KnowledgeBase インポート成功")
        
        # KnowledgeBase のテスト
        kb = KnowledgeBase(data_dir="data/test_kb")
        print("✓ KnowledgeBase 初期化成功")
        
        # ドキュメント追加
        kb.add_document("movie", "doc001", "スターウォーズは素晴らしいSF映画です")
        kb.add_document("movie", "doc002", "ジュラシックパークは恐竜映画の傑作です")
        print("✓ ドキュメント追加成功")
        
        # 検索テスト
        results = kb.search("映画", "movie", limit=5)
        print(f"✓ 検索テスト: {len(results)} 件の結果")
        
        # KnowledgeBaseManager のテスト
        kb_mgr = KnowledgeBaseManager(kb)
        summary = kb_mgr.get_summary()
        print(f"✓ KB Summary: {summary['total_items']} アイテム")
        
        return True
    except Exception as e:
        print(f"✗ KnowledgeBase エラー: {e}")
        return False

def test_memory_integration():
    """memory/__init__.py の統合テスト"""
    print_section("6. Memory統合テスト")
    
    try:
        from memory import (
            MemoryBackend, ShortTermMemory, MidTermMemory,
            LongTermMemory, KnowledgeBase
        )
        
        print("✓ Memory パッケージインポート成功")
        
        # 全記憶システムの初期化
        stm = ShortTermMemory()
        mtm = MidTermMemory(db_path="data/test_integration_mid.db")
        ltm = LongTermMemory(data_dir="data/test_integration_long")
        kb = KnowledgeBase(data_dir="data/test_integration_kb")
        
        print("✓ 全記憶システム初期化成功")
        print(f"  - 短期記憶: {stm.backend_type}")
        print(f"  - 中期記憶: {mtm.backend_type}")
        print(f"  - 長期記憶: {ltm.backend_type}")
        print(f"  - 知識ベース: {kb.backend_type}")
        
        # 統計情報の取得
        print("\n統計情報:")
        print(f"  - 短期記憶: {stm.get_stats()['current_items']} アイテム")
        print(f"  - 中期記憶: {mtm.get_stats()['current_items']} アイテム")
        print(f"  - 長期記憶: {ltm.get_stats()['total_profiles']} プロファイル")
        print(f"  - 知識ベース: {kb.get_stats()['total_items']} アイテム")
        
        return True
    except Exception as e:
        print(f"✗ Memory統合 エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("  Week 3 統合テスト")
    print("  記憶システムの動作確認")
    print("=" * 60)
    print(f"  実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 各テストの実行
    results.append(("Memory Base", test_memory_base()))
    results.append(("ShortTermMemory", test_short_term_memory()))
    results.append(("MidTermMemory", test_mid_term_memory()))
    results.append(("LongTermMemory", test_long_term_memory()))
    results.append(("KnowledgeBase", test_knowledge_base()))
    results.append(("Memory Integration", test_memory_integration()))
    
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
        print("\nWeek 3実装完了:")
        print("  ✓ memory/base.py - 記憶バックエンド基底クラス")
        print("  ✓ memory/short_term.py - 短期記憶（RAM）")
        print("  ✓ memory/mid_term.py - 中期記憶（DuckDB/JSON）")
        print("  ✓ memory/long_term.py - 長期記憶（JSON）")
        print("  ✓ memory/knowledge_base.py - 知識ベース")
        print("\n次のステップ（Week 4 - Phase 1完了）:")
        print("  - メインアプリと記憶システムの統合")
        print("  - 統合テスト・デバッグ")
        print("  - パフォーマンス最適化")
    else:
        print("\n⚠️  一部のテストに失敗しました。")
        print("エラー内容を確認して修正してください。")
    
    print("\n" + "=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)