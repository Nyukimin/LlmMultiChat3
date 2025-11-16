#!/usr/bin/env python3
"""
パフォーマンスプロファイリングツール
Week 4-3: パフォーマンス最適化

主要コンポーネントのボトルネック分析：
- 記憶システム（短期・中期・長期・知識ベース）
- LangGraphフロー処理
- ファイルI/O操作
"""

import time
import cProfile
import pstats
import io
from typing import Dict, List, Any, Callable
from datetime import datetime
import json
from pathlib import Path

from memory_manager import MemorySystemManager
# from main import MultiLLMChat  # 循環参照回避のためコメントアウト


class PerformanceProfiler:
    """パフォーマンスプロファイリングクラス"""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.memory_manager = MemorySystemManager()

    def measure_time(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """関数実行時間を計測"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return {
            'elapsed_time': elapsed,
            'result': result
        }

    def profile_function(self, func: Callable, *args, **kwargs) -> str:
        """cProfileを使った詳細プロファイリング"""
        profiler = cProfile.Profile()
        profiler.enable()
        func(*args, **kwargs)
        profiler.disable()

        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # 上位20件
        return s.getvalue()

    def test_memory_initialization(self) -> Dict[str, Any]:
        """記憶システム初期化のパフォーマンス測定"""
        print("\n[1/7] 記憶システム初期化テスト...")
        
        def init_test():
            mgr = MemorySystemManager()
            mgr.initialize_characters()
            return mgr

        result = self.measure_time(init_test)
        
        return {
            'test_name': 'memory_initialization',
            'elapsed_time': result['elapsed_time'],
            'status': 'success'
        }

    def test_conversation_turn_save(self) -> Dict[str, Any]:
        """会話ターン保存のパフォーマンス測定"""
        print("[2/7] 会話ターン保存テスト...")
        
        session_id = f"perf_test_{datetime.now().timestamp()}"
        
        def save_turns():
            for i in range(50):  # 50ターン保存
                self.memory_manager.add_conversation_turn(
                    speaker=f"Speaker{i % 3}",
                    message=f"テストメッセージ {i}",
                    metadata={'turn': i, 'session_id': session_id}
                )

        result = self.measure_time(save_turns)
        
        return {
            'test_name': 'conversation_turn_save',
            'turns_count': 50,
            'elapsed_time': result['elapsed_time'],
            'avg_time_per_turn': result['elapsed_time'] / 50,
            'status': 'success'
        }

    def test_session_management(self) -> Dict[str, Any]:
        """セッション管理のパフォーマンス測定"""
        print("[3/7] セッション管理テスト...")
        
        def session_ops():
            sessions = []
            # 10セッション作成
            for i in range(10):
                session_id = f"session_{i}_{datetime.now().timestamp()}"
                history = [
                    {
                        'speaker': 'User',
                        'message': f'メッセージ {j}',
                        'timestamp': datetime.now().isoformat()
                    }
                    for j in range(20)  # 各セッション20ターン
                ]
                self.memory_manager.save_session(
                    session_id,
                    history,
                    {'test': True, 'index': i}
                )
                sessions.append(session_id)
            
            # セッション読み込み
            for sid in sessions:
                self.memory_manager.load_session(sid)
            
            return len(sessions)

        result = self.measure_time(session_ops)
        
        return {
            'test_name': 'session_management',
            'sessions_count': 10,
            'elapsed_time': result['elapsed_time'],
            'avg_time_per_session': result['elapsed_time'] / 10,
            'status': 'success'
        }

    def test_character_kpi_operations(self) -> Dict[str, Any]:
        """キャラクターKPI操作のパフォーマンス測定"""
        print("[4/7] キャラクターKPI操作テスト...")
        
        characters = ['ルミナ', 'クラリス', 'ノクス']
        
        def kpi_ops():
            # 各キャラクター100回KPI更新
            for char in characters:
                for i in range(100):
                    self.memory_manager.update_character_kpi(
                        char,
                        kpi_type='user_thumbs_up',
                        value=1
                    )
            
            # KPI読み込み
            kpis = {}
            for char in characters:
                kpis[char] = self.memory_manager.get_character_level(char)
            
            return kpis

        result = self.measure_time(kpi_ops)
        
        return {
            'test_name': 'character_kpi_operations',
            'characters_count': len(characters),
            'operations_per_char': 100,
            'elapsed_time': result['elapsed_time'],
            'avg_time_per_operation': result['elapsed_time'] / (len(characters) * 100),
            'status': 'success'
        }

    def test_knowledge_base_operations(self) -> Dict[str, Any]:
        """知識ベース操作のパフォーマンス測定"""
        print("[5/7] 知識ベース操作テスト...")
        
        def kb_ops():
            # 知識検索（既存の知識ベースから）
            results = []
            for i in range(10):
                results.append(
                    self.memory_manager.search_knowledge(f'テスト {i}')
                )
            
            return len(results)

        result = self.measure_time(kb_ops)
        
        return {
            'test_name': 'knowledge_base_operations',
            'items_added': 50,
            'searches_performed': 10,
            'elapsed_time': result['elapsed_time'],
            'status': 'success'
        }

    def test_file_io_operations(self) -> Dict[str, Any]:
        """ファイルI/O操作のパフォーマンス測定"""
        print("[6/7] ファイルI/O操作テスト...")
        
        test_data_dir = Path("./test_data_perf")
        test_data_dir.mkdir(exist_ok=True)
        
        def file_ops():
            # JSON書き込み/読み込み（50回）
            for i in range(50):
                file_path = test_data_dir / f"test_{i}.json"
                data = {
                    'index': i,
                    'content': f'テストデータ {i}' * 100,  # 大きめのデータ
                    'timestamp': datetime.now().isoformat()
                }
                
                # 書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
        
        result = self.measure_time(file_ops)
        
        # クリーンアップ
        import shutil
        shutil.rmtree(test_data_dir, ignore_errors=True)
        
        return {
            'test_name': 'file_io_operations',
            'operations_count': 50,
            'elapsed_time': result['elapsed_time'],
            'avg_time_per_operation': result['elapsed_time'] / 50,
            'status': 'success'
        }

    def test_full_workflow(self) -> Dict[str, Any]:
        """フルワークフロー統合テスト"""
        print("[7/7] フルワークフロー統合テスト...")
        
        def workflow():
            # セッション作成
            session_id = f"workflow_{datetime.now().timestamp()}"
            
            # 会話ターン追加（20ターン）
            for i in range(20):
                self.memory_manager.add_conversation_turn(
                    speaker=f"Speaker{i % 3}",
                    message=f"ワークフローテスト {i}",
                    metadata={'turn': i, 'session_id': session_id}
                )
            
            # セッション保存
            history = [
                {
                    'speaker': f'Speaker{i % 3}',
                    'message': f'ワークフローテスト {i}',
                    'timestamp': datetime.now().isoformat()
                }
                for i in range(20)
            ]
            self.memory_manager.save_session(
                session_id,
                history,
                {'workflow_test': True}
            )
            
            # KPI更新
            for char in ['ルミナ', 'クラリス', 'ノクス']:
                self.memory_manager.update_character_kpi(
                    char,
                    kpi_type='user_thumbs_up',
                    value=1
                )
            
            # 検索
            self.memory_manager.search_knowledge('ワークフロー')

        result = self.measure_time(workflow)
        
        return {
            'test_name': 'full_workflow',
            'elapsed_time': result['elapsed_time'],
            'status': 'success'
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """全テスト実行"""
        print("\n" + "="*60)
        print("パフォーマンスプロファイリング開始")
        print("="*60)
        
        start_time = time.perf_counter()
        
        tests = [
            self.test_memory_initialization,
            self.test_conversation_turn_save,
            self.test_session_management,
            self.test_character_kpi_operations,
            self.test_knowledge_base_operations,
            self.test_file_io_operations,
            self.test_full_workflow
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                results.append({
                    'test_name': test.__name__,
                    'status': 'error',
                    'error': str(e)
                })
        
        total_time = time.perf_counter() - start_time
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_elapsed_time': total_time,
            'tests': results,
            'summary': self._generate_summary(results)
        }
        
        return report

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果サマリー生成"""
        total_tests = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        
        # 最も遅いテスト
        slowest = max(
            (r for r in results if 'elapsed_time' in r),
            key=lambda r: r['elapsed_time'],
            default=None
        )
        
        # 最も速いテスト
        fastest = min(
            (r for r in results if 'elapsed_time' in r),
            key=lambda r: r['elapsed_time'],
            default=None
        )
        
        return {
            'total_tests': total_tests,
            'successful': successful,
            'failed': total_tests - successful,
            'slowest_test': {
                'name': slowest['test_name'],
                'time': slowest['elapsed_time']
            } if slowest else None,
            'fastest_test': {
                'name': fastest['test_name'],
                'time': fastest['elapsed_time']
            } if fastest else None
        }

    def save_report(self, report: Dict[str, Any], filepath: str = "performance_report.json"):
        """レポート保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n✓ レポート保存: {filepath}")

    def print_report(self, report: Dict[str, Any]):
        """レポート表示"""
        print("\n" + "="*60)
        print("パフォーマンスプロファイリング結果")
        print("="*60)
        
        print(f"\n総実行時間: {report['total_elapsed_time']:.4f}秒")
        
        summary = report['summary']
        print(f"\n総テスト数: {summary['total_tests']}")
        print(f"成功: {summary['successful']}")
        print(f"失敗: {summary['failed']}")
        
        if summary['slowest_test']:
            print(f"\n最も遅いテスト: {summary['slowest_test']['name']}")
            print(f"  実行時間: {summary['slowest_test']['time']:.4f}秒")
        
        if summary['fastest_test']:
            print(f"\n最も速いテスト: {summary['fastest_test']['name']}")
            print(f"  実行時間: {summary['fastest_test']['time']:.4f}秒")
        
        print("\n個別テスト結果:")
        print("-" * 60)
        for test in report['tests']:
            name = test.get('test_name', 'unknown')
            status = test.get('status', 'unknown')
            elapsed = test.get('elapsed_time', 0)
            
            print(f"\n{name}:")
            print(f"  ステータス: {status}")
            if elapsed:
                print(f"  実行時間: {elapsed:.4f}秒")
            
            # 追加情報
            if 'avg_time_per_turn' in test:
                print(f"  平均時間/ターン: {test['avg_time_per_turn']:.6f}秒")
            if 'avg_time_per_session' in test:
                print(f"  平均時間/セッション: {test['avg_time_per_session']:.4f}秒")
            if 'avg_time_per_operation' in test:
                print(f"  平均時間/操作: {test['avg_time_per_operation']:.6f}秒")


def main():
    """メイン関数"""
    profiler = PerformanceProfiler()
    report = profiler.run_all_tests()
    profiler.print_report(report)
    profiler.save_report(report)
    
    print("\n" + "="*60)
    print("プロファイリング完了")
    print("="*60)


if __name__ == "__main__":
    main()