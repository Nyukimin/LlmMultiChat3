"""
dashboard.py
簡易ダッシュボード基盤（Phase 2実装）

セッションレポートをHTML形式で生成。
Phase 3でWebSocketリアルタイムダッシュボードに拡張予定。
"""

from datetime import datetime
from typing import Dict, Any
from pathlib import Path


def generate_html_report(metrics: Dict[str, Any], output_file: str = None) -> str:
    """
    HTMLレポート生成
    
    Args:
        metrics: メトリクスデータ
        output_file: 出力ファイルパス（Noneの場合は自動生成）
        
    Returns:
        生成したHTMLファイルのパス
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"exports/report_{timestamp}.html"
    
    # ディレクトリ作成
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # HTMLテンプレート
    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LlmMultiChat3 - セッションレポート</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-card h3 {{
            color: #555;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .metric-card .unit {{
            color: #777;
            font-size: 0.8em;
            margin-left: 5px;
        }}
        .chart-container {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            color: #555;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #777;
            font-size: 0.9em;
        }}
        .status-success {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .status-error {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 LlmMultiChat3</h1>
            <p>セッションレポート</p>
        </div>
        
        <div class="content">
            <!-- セッション情報 -->
            <div class="section">
                <h2>📅 セッション情報</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>開始時刻</h3>
                        <div class="value">{metrics['session_info']['start'][:19]}</div>
                    </div>
                    <div class="metric-card">
                        <h3>終了時刻</h3>
                        <div class="value">{metrics['session_info']['end'][:19] if metrics['session_info']['end'] else '実行中'}</div>
                    </div>
                    <div class="metric-card">
                        <h3>実行時間</h3>
                        <div class="value">{metrics['session_info']['duration_seconds']:.2f if metrics['session_info']['duration_seconds'] else 0:.2f}<span class="unit">秒</span></div>
                    </div>
                </div>
            </div>
            
            <!-- LLM統計 -->
            <div class="section">
                <h2>🤖 LLM呼び出し統計</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>総呼び出し数</h3>
                        <div class="value">{metrics['llm_stats']['total_calls']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>平均応答時間</h3>
                        <div class="value">{metrics['llm_stats']['avg_call_time_ms']:.2f}<span class="unit">ms</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>エラー数</h3>
                        <div class="value {'status-success' if metrics['llm_stats']['total_errors'] == 0 else 'status-error'}">{metrics['llm_stats']['total_errors']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>リトライ数</h3>
                        <div class="value">{metrics['llm_stats']['total_retries']}<span class="unit">回</span></div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>応答時間統計</h3>
                    <table>
                        <tr>
                            <th>指標</th>
                            <th>値</th>
                        </tr>
                        <tr>
                            <td>最小値</td>
                            <td>{metrics['llm_stats']['min_call_time_ms']:.2f} ms</td>
                        </tr>
                        <tr>
                            <td>中央値</td>
                            <td>{metrics['llm_stats']['median_call_time_ms']:.2f} ms</td>
                        </tr>
                        <tr>
                            <td>平均値</td>
                            <td>{metrics['llm_stats']['avg_call_time_ms']:.2f} ms</td>
                        </tr>
                        <tr>
                            <td>最大値</td>
                            <td>{metrics['llm_stats']['max_call_time_ms']:.2f} ms</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <!-- 記憶システム統計 -->
            <div class="section">
                <h2>💾 記憶システム統計</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>総操作数</h3>
                        <div class="value">{metrics['memory_stats']['total_operations']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>読み込み</h3>
                        <div class="value">{metrics['memory_stats']['total_reads']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>書き込み</h3>
                        <div class="value">{metrics['memory_stats']['total_writes']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>エラー数</h3>
                        <div class="value {'status-success' if metrics['memory_stats']['total_errors'] == 0 else 'status-error'}">{metrics['memory_stats']['total_errors']}<span class="unit">回</span></div>
                    </div>
                </div>
            </div>
            
            <!-- 会話統計 -->
            <div class="section">
                <h2>💬 会話統計</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>総ターン数</h3>
                        <div class="value">{metrics['conversation_stats']['total_turns']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>ユーザー入力</h3>
                        <div class="value">{metrics['conversation_stats']['user_inputs']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>システム応答</h3>
                        <div class="value">{metrics['conversation_stats']['system_responses']}<span class="unit">回</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>総セッション数</h3>
                        <div class="value">{metrics['conversation_stats']['total_sessions']}<span class="unit">回</span></div>
                    </div>
                </div>
            </div>
            
            <!-- キャラクター統計 -->
            <div class="section">
                <h2>👥 キャラクター別応答数</h2>
                <div class="chart-container">
                    <table>
                        <tr>
                            <th>キャラクター</th>
                            <th>応答数</th>
                        </tr>
                        {_generate_character_rows(metrics['character_stats'])}
                    </table>
                </div>
            </div>
            
            <!-- エラー統計 -->
            <div class="section">
                <h2>⚠️ エラー統計</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>総エラー数</h3>
                        <div class="value {'status-success' if metrics['error_stats']['total_errors'] == 0 else 'status-error'}">{metrics['error_stats']['total_errors']}<span class="unit">回</span></div>
                    </div>
                </div>
                {_generate_error_table(metrics['error_stats']['errors_by_type']) if metrics['error_stats']['errors_by_type'] else ''}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by LlmMultiChat3 Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # HTMLファイル書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file


def _generate_character_rows(character_stats: Dict[str, int]) -> str:
    """キャラクター統計のテーブル行を生成"""
    rows = []
    for character, count in character_stats.items():
        rows.append(f"""
                        <tr>
                            <td>{character}</td>
                            <td>{count}回</td>
                        </tr>
        """)
    return ''.join(rows)


def _generate_error_table(errors_by_type: Dict[str, int]) -> str:
    """エラー統計のテーブルを生成"""
    if not errors_by_type:
        return ""
    
    rows = []
    for error_type, count in errors_by_type.items():
        rows.append(f"""
                        <tr>
                            <td>{error_type}</td>
                            <td>{count}回</td>
                        </tr>
        """)
    
    return f"""
                <div class="chart-container">
                    <h3>エラー種別</h3>
                    <table>
                        <tr>
                            <th>エラー型</th>
                            <th>発生回数</th>
                        </tr>
                        {''.join(rows)}
                    </table>
                </div>
    """