"""総合テスト実行スクリプト

Phase 1-3統合プロジェクトの全テストを順次実行し、
総合的なテスト結果レポートを生成します。

実行テスト:
- ユニットテスト (ChatService, MemoryService)
- Phase 1テスト (LangGraphコア)
- 統合テスト (Phase 1-3統合)
- APIテスト (REST/WebSocket)
- E2Eテスト (フルワークフロー)
- パフォーマンステスト (負荷テスト)
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """テスト実行管理クラス"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_test_suite(self, name: str, test_path: str, markers: str = None) -> dict:
        """テストスイート実行

        Args:
            name: テストスイート名
            test_path: テストファイルパス
            markers: pytestマーカー（optional）

        Returns:
            dict: 実行結果
        """
        print(f"\n{'='*80}")
        print(f"📋 {name} 実行中...")
        print(f"{'='*80}")

        cmd = ["uv", "run", "pytest", test_path, "-v", "--tb=short"]
        if markers:
            cmd.extend(["-k", markers])

        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start

        # 結果解析
        output = result.stdout
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        total = passed + failed

        test_result = {
            "name": name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "elapsed": elapsed,
            "success": result.returncode == 0,
            "output": output,
        }

        self.results[name] = test_result

        # 結果表示
        if test_result["success"]:
            print(f"✅ {name} 成功: {passed}/{total}件パス ({elapsed:.2f}秒)")
        else:
            print(
                f"❌ {name} 失敗: {passed}/{total}件パス, {failed}件失敗 ({elapsed:.2f}秒)"
            )

        return test_result

    def generate_report(self):
        """総合テストレポート生成"""
        print(f"\n{'='*80}")
        print("📊 総合テスト結果レポート")
        print(f"{'='*80}")
        print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"総実行時間: {self.end_time - self.start_time:.2f}秒")
        print()

        total_tests = 0
        total_passed = 0
        total_failed = 0
        all_success = True

        print(f"{'テストスイート':<40} {'合計':<8} {'成功':<8} {'失敗':<8} {'時間':<10}")
        print("-" * 80)

        for name, result in self.results.items():
            total_tests += result["total"]
            total_passed += result["passed"]
            total_failed += result["failed"]
            if not result["success"]:
                all_success = False

            status = "✅" if result["success"] else "❌"
            print(
                f"{status} {result['name']:<38} {result['total']:<8} {result['passed']:<8} {result['failed']:<8} {result['elapsed']:.2f}秒"
            )

        print("-" * 80)
        print(
            f"{'合計':<40} {total_tests:<8} {total_passed:<8} {total_failed:<8} {self.end_time - self.start_time:.2f}秒"
        )
        print()

        # 成功率計算
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 総合成功率: {success_rate:.1f}% ({total_passed}/{total_tests})")
        print()

        if all_success:
            print("🎉 全テストスイートが成功しました！")
        else:
            print("⚠️ 一部のテストスイートで失敗があります。")

        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": success_rate,
            "all_success": all_success,
        }

    def save_report(self, summary: dict):
        """レポート保存"""
        report_path = Path("test_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Phase 1-3統合プロジェクト 総合テストレポート\n")
            f.write(f"{'='*80}\n")
            f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"総実行時間: {self.end_time - self.start_time:.2f}秒\n\n")

            f.write(f"{'テストスイート':<40} {'合計':<8} {'成功':<8} {'失敗':<8} {'時間':<10}\n")
            f.write("-" * 80 + "\n")

            for name, result in self.results.items():
                status = "✅" if result["success"] else "❌"
                f.write(
                    f"{status} {result['name']:<38} {result['total']:<8} {result['passed']:<8} {result['failed']:<8} {result['elapsed']:.2f}秒\n"
                )

            f.write("-" * 80 + "\n")
            f.write(
                f"{'合計':<40} {summary['total_tests']:<8} {summary['total_passed']:<8} {summary['total_failed']:<8} {self.end_time - self.start_time:.2f}秒\n\n"
            )

            f.write(
                f"📈 総合成功率: {summary['success_rate']:.1f}% ({summary['total_passed']}/{summary['total_tests']})\n\n"
            )

            if summary["all_success"]:
                f.write("🎉 全テストスイートが成功しました！\n")
            else:
                f.write("⚠️ 一部のテストスイートで失敗があります。\n")

        print(f"\n📄 レポート保存: {report_path}")


def main():
    """メイン処理"""
    runner = TestRunner()
    runner.start_time = time.time()

    print("🚀 Phase 1-3統合プロジェクト 総合テスト開始")

    # 1. ユニットテスト
    runner.run_test_suite(
        name="ユニットテスト (ChatService)",
        test_path="tests/test_unit_chat_service.py",
    )

    runner.run_test_suite(
        name="ユニットテスト (MemoryService)",
        test_path="tests/test_unit_memory_service.py",
    )

    # 2. Phase 1テスト
    runner.run_test_suite(
        name="Phase 1テスト (LangGraphコア)", test_path="test_week2.py"
    )

    # 3. 統合テスト
    runner.run_test_suite(
        name="統合テスト (ChatService統合)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestChatServiceIntegration",
    )

    runner.run_test_suite(
        name="統合テスト (MemoryService統合)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestMemoryServiceIntegration",
    )

    runner.run_test_suite(
        name="統合テスト (E2E統合)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestEndToEndIntegration",
    )

    runner.run_test_suite(
        name="統合テスト (エラーハンドリング)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestErrorHandling",
    )

    runner.run_test_suite(
        name="統合テスト (マルチキャラクター)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestMultiCharacterIntegration",
    )

    runner.run_test_suite(
        name="統合テスト (セッション管理)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestSessionManagement",
    )

    runner.run_test_suite(
        name="統合テスト (記憶階層)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestMemoryLayerIntegration",
    )

    runner.run_test_suite(
        name="統合テスト (パフォーマンス)",
        test_path="tests/test_integration_phase1_3.py",
        markers="TestPerformanceIntegration",
    )

    # 4. APIテスト
    runner.run_test_suite(name="APIテスト (認証)", test_path="tests/test_api_auth.py")

    runner.run_test_suite(name="APIテスト (会話)", test_path="tests/test_api_chat.py")

    runner.run_test_suite(name="APIテスト (記憶)", test_path="tests/test_api_memory.py")

    runner.end_time = time.time()

    # レポート生成・保存
    summary = runner.generate_report()
    runner.save_report(summary)

    # 終了コード
    sys.exit(0 if summary["all_success"] else 1)


if __name__ == "__main__":
    main()