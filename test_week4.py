"""
test_week4.py
Week 4統合テスト: メインアプリと記憶システムの統合テスト

テスト項目:
1. 記憶システム統合の動作確認
2. セッション管理テスト
3. 会話ターン記録テスト
4. キャラクター成長システムテスト
5. /memoryコマンドテスト
"""

import unittest
import shutil
from datetime import datetime
from pathlib import Path

from memory_manager import MemorySystemManager
from memory.base import MemoryConfig


class TestWeek4Integration(unittest.TestCase):
    """Week 4統合テスト"""

    def setUp(self):
        """テスト前準備"""
        self.test_data_dir = Path("test_data_week4")
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
        self.test_data_dir.mkdir(exist_ok=True)

        # テスト用の記憶システムマネージャー
        self.config = MemoryConfig()
        self.memory = MemorySystemManager(self.config)

        # データディレクトリをテスト用に設定
        self.memory.short_term.data_dir = self.test_data_dir / "short"
        self.memory.mid_term.data_dir = self.test_data_dir / "mid"
        self.memory.long_term.data_dir = self.test_data_dir / "long"
        self.memory.knowledge_base.data_dir = self.test_data_dir / "kb"

        # ディレクトリ作成
        for attr in ['short_term', 'mid_term',
                     'long_term', 'knowledge_base']:
            getattr(self.memory, attr).data_dir.mkdir(
                parents=True, exist_ok=True)

        # キャラクター初期化
        self.memory.initialize_characters()

    def tearDown(self):
        """テスト後クリーンアップ"""
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)

    def test_01_memory_system_initialization(self):
        """テスト1: 記憶システム初期化"""
        print("\n=== テスト1: 記憶システム初期化 ===")

        # 各記憶層の初期化確認
        self.assertIsNotNone(self.memory.short_term)
        self.assertIsNotNone(self.memory.mid_term)
        self.assertIsNotNone(self.memory.long_term)
        self.assertIsNotNone(self.memory.knowledge_base)

        # キャラクター初期化確認
        for char in ['ルミナ', 'クラリス', 'ノクス']:
            level = self.memory.kpi_manager.get_character_level(char)
            self.assertIsNotNone(level, f"{char}のレベルが取得できない")

        print("[OK] 記憶システム初期化成功")

    def test_02_conversation_turn_recording(self):
        """テスト2: 会話ターン記録"""
        print("\n=== テスト2: 会話ターン記録 ===")

        # 会話ターン追加
        test_turns = [
            ("User", "こんにちは"),
            ("lumina", "こんにちは！今日はどんな話をしましょうか？"),
            ("User", "天気について教えて"),
            ("claris", "気象について説明します。天気は大気の状態です。"),
        ]

        for speaker, content in test_turns:
            success = self.memory.add_conversation_turn(
                speaker=speaker,
                message=content,
                metadata={"test": True}
            )
            self.assertTrue(success, f"{speaker}の会話ターン追加失敗")

        # 統計確認
        self.assertEqual(self.memory.stats['total_turns'], len(test_turns))

        print(f"[OK] {len(test_turns)}ターンの会話を記録")

    def test_03_session_management(self):
        """テスト3: セッション管理"""
        print("\n=== テスト3: セッション管理 ===")

        # 複数セッション作成
        sessions = []
        for i in range(3):
            session_id = f"session_{i}_{datetime.now().timestamp()}"
            history = [
                {
                    "speaker": "User",
                    "message": f"メッセージ {i}",
                    "timestamp": datetime.now().isoformat()
                }
            ]

            success = self.memory.save_session(
                session_id=session_id,
                history=history,
                metadata={"index": i}
            )
            self.assertTrue(success, f"セッション{i}の保存失敗")
            sessions.append(session_id)

        # セッション読み込み確認
        for session_id in sessions:
            loaded = self.memory.load_session(session_id)
            self.assertIsNotNone(loaded, f"{session_id}の読み込み失敗")

        print(f"[OK] {len(sessions)}個のセッションを管理")

    def test_04_character_growth_system(self):
        """テスト4: キャラクター成長システム"""
        print("\n=== テスト4: キャラクター成長システム ===")

        # ルミナのKPI更新（正しいAPI形式）
        test_kpis = [
            ("user_thumbs_up", 5),
            ("answer_hits", 3),
            ("search_success", 2),
        ]

        for kpi_type, value in test_kpis:
            success = self.memory.update_character_kpi(
                "ルミナ", kpi_type, value
            )
            self.assertTrue(success, f"KPI更新失敗: {kpi_type}")

        # 成長確認
        level = self.memory.get_character_level("ルミナ")
        self.assertGreaterEqual(level, 1, "レベルが正しく計算されていない")

        print(f"[OK] ルミナのレベル: {level}")

    def test_05_knowledge_base_integration(self):
        """テスト5: 知識ベース統合"""
        print("\n=== テスト5: 知識ベース統合 ===")

        # 知識追加（正しいAPI形式: add_documentを使用）
        test_knowledge = [
            ("general", "doc001", "今日は晴れです"),
            ("general", "doc002",
             "Pythonは高級プログラミング言語です"),
            ("general", "doc003", "AIは人工知能の略です"),
        ]

        for namespace, doc_id, content in test_knowledge:
            self.memory.knowledge_base.add_document(
                namespace=namespace,
                doc_id=doc_id,
                content=content
            )

        # 知識検索
        results = self.memory.search_knowledge("Python", "general")
        self.assertGreater(len(results), 0, "知識検索結果が空")

        print(f"[OK] 知識ベース: {len(test_knowledge)}件追加")
        print(f"[OK] 検索結果: {len(results)}件")

    def test_06_full_workflow(self):
        """テスト6: フルワークフロー統合テスト"""
        print("\n=== テスト6: フルワークフロー統合テスト ===")

        # 1. セッション開始
        session_id = f"test_{datetime.now().timestamp()}"
        print(f"[OK] セッション作成: {session_id}")

        # 2. 会話実行
        conversation = [
            ("User", "こんにちは、AIについて教えてください"),
            ("lumina",
             "こんにちは！AIについてですね。クラリスさん、説明をお願いできますか？"),
            ("claris",
             "AIは人工知能のことです。機械が学習し、判断する技術です。"),
            ("User", "面白いですね。具体例はありますか？"),
            ("nox",
             "具体例を検索します。音声認識、画像認識、自動運転などがあります。"),
        ]

        for speaker, content in conversation:
            self.memory.add_conversation_turn(
                speaker=speaker,
                message=content,
                metadata={"workflow": "full_test"}
            )

        print(f"[OK] 会話記録: {len(conversation)}ターン")

        # 3. KPI更新
        kpis = {
            "ルミナ": [("user_thumbs_up", 5), ("answer_hits", 4)],
            "クラリス": [("answer_hits", 5)],
            "ノクス": [("search_success", 5)],
        }

        for char, kpi_list in kpis.items():
            for kpi_type, value in kpi_list:
                self.memory.update_character_kpi(char, kpi_type, value)

        print("[OK] KPI更新完了")

        # 4. 知識追加
        self.memory.knowledge_base.add_document(
            namespace="ai_topics",
            doc_id="ai_001",
            content="AIは機械学習、深層学習、自然言語処理などを含む"
        )
        print("[OK] 知識ベース更新")

        # 5. セッション保存
        history = [
            {
                "speaker": s,
                "message": m,
                "timestamp": datetime.now().isoformat()
            } for s, m in conversation
        ]
        self.memory.save_session(session_id, history)
        print("[OK] セッション保存完了")

        # 6. 統計確認
        stats = self.memory.get_all_stats()
        print("\n統計サマリー:")
        print(f"  - 短期記憶: {stats['short_term']['current_items']}件")
        print(f"  - 中期記憶: {stats['mid_term']['current_items']}件")
        print(f"  - 長期記憶: {stats['long_term']['total_profiles']}件")
        print(f"  - 知識ベース: {stats['knowledge_base']['total_items']}件")

        # アサーション
        self.assertGreater(
            self.memory.stats['total_turns'], 0, "会話が記録されていない"
        )

        print("\n[OK] フルワークフロー統合テスト成功")


def run_tests():
    """テスト実行"""
    print("="*60)
    print("Week 4統合テスト開始")
    print("="*60)

    # テストスイート作成
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWeek4Integration)

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    print(f"実行: {result.testsRun}件")
    success = result.testsRun - len(result.failures) - len(result.errors)
    print(f"成功: {success}件")
    print(f"失敗: {len(result.failures)}件")
    print(f"エラー: {len(result.errors)}件")

    if result.wasSuccessful():
        print("\n[OK] 全テスト成功！Week 4統合完了")
    else:
        print("\n[FAILED] テスト失敗")

    return result


if __name__ == "__main__":
    result = run_tests()
    exit(0 if result.wasSuccessful() else 1)
