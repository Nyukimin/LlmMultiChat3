"""
metrics.py
メトリクス収集システム

LLM呼び出し、記憶操作、エラーなどのメトリクスを収集・集計。
セッション終了時にレポートをエクスポート。
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import statistics


class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        """初期化"""
        self.metrics = {
            # LLM関連メトリクス
            'llm_calls': 0,
            'llm_call_times': [],  # ミリ秒単位
            'llm_errors': 0,
            'llm_retries': 0,
            'llm_fallbacks': 0,
            
            # 記憶システムメトリクス
            'memory_operations': 0,
            'memory_writes': 0,
            'memory_reads': 0,
            'memory_errors': 0,
            
            # 会話メトリクス
            'total_turns': 0,
            'total_sessions': 0,
            'user_inputs': 0,
            'system_responses': 0,
            
            # エラーメトリクス
            'total_errors': 0,
            'error_by_type': {},  # {error_type: count}
            
            # キャラクター別メトリクス
            'character_responses': {
                'ルミナ': 0,
                'クラリス': 0,
                'ノクス': 0
            },
            
            # タイムスタンプ
            'session_start': datetime.now().isoformat(),
            'session_end': None
        }
        
        # 詳細ログ（デバッグ用）
        self.detailed_logs = []
    
    def record_llm_call(self, duration_ms: float, character: str = "", 
                       success: bool = True, retry_count: int = 0):
        """
        LLM呼び出しを記録
        
        Args:
            duration_ms: 実行時間（ミリ秒）
            character: キャラクター名
            success: 成功したかどうか
            retry_count: リトライ回数
        """
        self.metrics['llm_calls'] += 1
        self.metrics['llm_call_times'].append(duration_ms)
        
        if character:
            if character in self.metrics['character_responses']:
                self.metrics['character_responses'][character] += 1
        
        if not success:
            self.metrics['llm_errors'] += 1
        
        if retry_count > 0:
            self.metrics['llm_retries'] += retry_count
        
        # 詳細ログ
        self.detailed_logs.append({
            'type': 'llm_call',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': duration_ms,
            'character': character,
            'success': success,
            'retry_count': retry_count
        })
    
    def record_llm_fallback(self, character: str = ""):
        """
        LLMフォールバック（全リトライ失敗）を記録
        
        Args:
            character: キャラクター名
        """
        self.metrics['llm_fallbacks'] += 1
        
        self.detailed_logs.append({
            'type': 'llm_fallback',
            'timestamp': datetime.now().isoformat(),
            'character': character
        })
    
    def record_memory_operation(self, operation_type: str, duration_ms: float = 0,
                                success: bool = True):
        """
        記憶操作を記録
        
        Args:
            operation_type: 操作種別（read, write, update, delete）
            duration_ms: 実行時間（ミリ秒）
            success: 成功したかどうか
        """
        self.metrics['memory_operations'] += 1
        
        if operation_type == 'read':
            self.metrics['memory_reads'] += 1
        elif operation_type in ['write', 'update', 'delete']:
            self.metrics['memory_writes'] += 1
        
        if not success:
            self.metrics['memory_errors'] += 1
        
        # 詳細ログ
        self.detailed_logs.append({
            'type': 'memory_operation',
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'duration_ms': duration_ms,
            'success': success
        })
    
    def record_conversation_turn(self, speaker: str, user_input: bool = False):
        """
        会話ターンを記録
        
        Args:
            speaker: 発話者
            user_input: ユーザー入力かどうか
        """
        self.metrics['total_turns'] += 1
        
        if user_input:
            self.metrics['user_inputs'] += 1
        else:
            self.metrics['system_responses'] += 1
    
    def record_error(self, error_type: str, context: str = ""):
        """
        エラーを記録
        
        Args:
            error_type: エラー型名
            context: エラーコンテキスト
        """
        self.metrics['total_errors'] += 1
        
        if error_type not in self.metrics['error_by_type']:
            self.metrics['error_by_type'][error_type] = 0
        self.metrics['error_by_type'][error_type] += 1
        
        # 詳細ログ
        self.detailed_logs.append({
            'type': 'error',
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'context': context
        })
    
    def record_session_start(self):
        """セッション開始を記録"""
        self.metrics['total_sessions'] += 1
        self.metrics['session_start'] = datetime.now().isoformat()
    
    def record_session_end(self):
        """セッション終了を記録"""
        self.metrics['session_end'] = datetime.now().isoformat()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        メトリクスサマリーを取得
        
        Returns:
            メトリクスサマリーの辞書
        """
        # LLM呼び出し統計
        llm_stats = {
            'total_calls': self.metrics['llm_calls'],
            'total_errors': self.metrics['llm_errors'],
            'total_retries': self.metrics['llm_retries'],
            'total_fallbacks': self.metrics['llm_fallbacks'],
            'avg_call_time_ms': 0.0,
            'median_call_time_ms': 0.0,
            'min_call_time_ms': 0.0,
            'max_call_time_ms': 0.0
        }
        
        if self.metrics['llm_call_times']:
            call_times = self.metrics['llm_call_times']
            llm_stats['avg_call_time_ms'] = statistics.mean(call_times)
            llm_stats['median_call_time_ms'] = statistics.median(call_times)
            llm_stats['min_call_time_ms'] = min(call_times)
            llm_stats['max_call_time_ms'] = max(call_times)
        
        # 記憶システム統計
        memory_stats = {
            'total_operations': self.metrics['memory_operations'],
            'total_reads': self.metrics['memory_reads'],
            'total_writes': self.metrics['memory_writes'],
            'total_errors': self.metrics['memory_errors']
        }
        
        # 会話統計
        conversation_stats = {
            'total_turns': self.metrics['total_turns'],
            'user_inputs': self.metrics['user_inputs'],
            'system_responses': self.metrics['system_responses'],
            'total_sessions': self.metrics['total_sessions']
        }
        
        # エラー統計
        error_stats = {
            'total_errors': self.metrics['total_errors'],
            'errors_by_type': self.metrics['error_by_type']
        }
        
        # キャラクター統計
        character_stats = self.metrics['character_responses']
        
        # セッション時間
        session_duration = None
        if self.metrics['session_start'] and self.metrics['session_end']:
            start = datetime.fromisoformat(self.metrics['session_start'])
            end = datetime.fromisoformat(self.metrics['session_end'])
            session_duration = (end - start).total_seconds()
        
        return {
            'session_info': {
                'start': self.metrics['session_start'],
                'end': self.metrics['session_end'],
                'duration_seconds': session_duration
            },
            'llm_stats': llm_stats,
            'memory_stats': memory_stats,
            'conversation_stats': conversation_stats,
            'character_stats': character_stats,
            'error_stats': error_stats
        }
    
    def export_to_json(self, filepath: str = None) -> str:
        """
        メトリクスをJSON形式でエクスポート
        
        Args:
            filepath: 出力ファイルパス（Noneの場合は自動生成）
            
        Returns:
            エクスポートしたファイルのパス
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"metrics/metrics_{timestamp}.json"
        
        # ディレクトリ作成
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # メトリクスエクスポート
        export_data = {
            'summary': self.get_summary(),
            'raw_metrics': self.metrics,
            'detailed_logs': self.detailed_logs[-100:]  # 最新100件のみ
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def reset(self):
        """メトリクスをリセット"""
        self.__init__()
    
    def get_performance_report(self) -> str:
        """
        パフォーマンスレポートを文字列で取得
        
        Returns:
            レポート文字列
        """
        summary = self.get_summary()
        
        report = []
        report.append("=" * 60)
        report.append("パフォーマンスレポート")
        report.append("=" * 60)
        
        # セッション情報
        session = summary['session_info']
        report.append(f"\n【セッション情報】")
        report.append(f"開始時刻: {session['start']}")
        if session['end']:
            report.append(f"終了時刻: {session['end']}")
            report.append(f"実行時間: {session['duration_seconds']:.2f}秒")
        
        # LLM統計
        llm = summary['llm_stats']
        report.append(f"\n【LLM呼び出し】")
        report.append(f"総呼び出し数: {llm['total_calls']}回")
        report.append(f"平均応答時間: {llm['avg_call_time_ms']:.2f}ms")
        report.append(f"中央値: {llm['median_call_time_ms']:.2f}ms")
        report.append(f"最小/最大: {llm['min_call_time_ms']:.2f}ms / {llm['max_call_time_ms']:.2f}ms")
        report.append(f"エラー数: {llm['total_errors']}回")
        report.append(f"リトライ数: {llm['total_retries']}回")
        report.append(f"フォールバック数: {llm['total_fallbacks']}回")
        
        # 記憶システム統計
        memory = summary['memory_stats']
        report.append(f"\n【記憶システム】")
        report.append(f"総操作数: {memory['total_operations']}回")
        report.append(f"読み込み: {memory['total_reads']}回")
        report.append(f"書き込み: {memory['total_writes']}回")
        report.append(f"エラー数: {memory['total_errors']}回")
        
        # 会話統計
        conv = summary['conversation_stats']
        report.append(f"\n【会話統計】")
        report.append(f"総ターン数: {conv['total_turns']}回")
        report.append(f"ユーザー入力: {conv['user_inputs']}回")
        report.append(f"システム応答: {conv['system_responses']}回")
        report.append(f"総セッション数: {conv['total_sessions']}回")
        
        # キャラクター統計
        char = summary['character_stats']
        report.append(f"\n【キャラクター別応答数】")
        for character, count in char.items():
            report.append(f"{character}: {count}回")
        
        # エラー統計
        error = summary['error_stats']
        report.append(f"\n【エラー統計】")
        report.append(f"総エラー数: {error['total_errors']}回")
        if error['errors_by_type']:
            report.append("エラー種別:")
            for error_type, count in error['errors_by_type'].items():
                report.append(f"  {error_type}: {count}回")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# グローバルインスタンス（シングルトン）
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """
    グローバルMetricsCollectorインスタンスを取得
    
    Returns:
        MetricsCollectorインスタンス
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector():
    """グローバルMetricsCollectorをリセット"""
    global _metrics_collector
    _metrics_collector = None