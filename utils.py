"""
utils.py
ユーティリティ関数群

ログ管理、エクスポート機能、システム検証などの補助機能を提供。
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from logging.handlers import RotatingFileHandler


class Logger:
    """ログ管理クラス"""
    
    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        初期化
        
        Args:
            log_dir: ログ出力ディレクトリ
            log_level: ログレベル
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # ロガーの設定
        self.logger = logging.getLogger("MultiLLMChat")
        self.logger.setLevel(log_level)
        
        # ハンドラの設定
        if not self.logger.handlers:
            # RotatingFileHandlerに変更（ログローテーション対応）
            log_file = self.log_dir / "chat.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            
            # コンソールハンドラ
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # フォーマッター
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_conversation(self, speaker: str, message: str, turn: int, 
                        session_id: str = "", metadata: Dict = None):
        """
        会話ログを記録
        
        Args:
            speaker: 発話者
            message: メッセージ
            turn: ターン数
            session_id: セッションID
            metadata: 追加メタデータ
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "speaker": speaker,
            "message": message
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_error(self, error: Exception, context: str = ""):
        """
        エラーログを記録
        
        Args:
            error: 例外オブジェクト
            context: エラーコンテキスト
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        self.logger.error(json.dumps(error_data, ensure_ascii=False))
    
    def log_info(self, message: str, context: str = ""):
        """
        情報ログを記録
        
        Args:
            message: ログメッセージ
            context: コンテキスト
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_warning(self, message: str, context: str = ""):
        """
        警告ログを記録
        
        Args:
            message: 警告メッセージ
            context: コンテキスト
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context
        }
        self.logger.warning(json.dumps(log_data, ensure_ascii=False))
    
    def log_system_event(self, event: str, details: Dict = None):
        """
        システムイベントを記録
        
        Args:
            event: イベント名
            details: イベント詳細
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details or {}
        }
        self.logger.info(json.dumps(event_data, ensure_ascii=False))


class ConversationExporter:
    """会話履歴エクスポートクラス"""
    
    def __init__(self, export_dir: str = "exports"):
        """
        初期化
        
        Args:
            export_dir: エクスポート先ディレクトリ
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_to_json(self, history: List[Dict], 
                      filename: str = None,
                      metadata: Dict = None) -> str:
        """
        会話履歴をJSON形式でエクスポート
        
        Args:
            history: 会話履歴
            filename: 出力ファイル名（Noneの場合は自動生成）
            metadata: 追加メタデータ
            
        Returns:
            エクスポートしたファイルのパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        filepath = self.export_dir / filename
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "conversation": history
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def export_to_markdown(self, history: List[Dict],
                          filename: str = None,
                          title: str = "会話履歴") -> str:
        """
        会話履歴をMarkdown形式でエクスポート
        
        Args:
            history: 会話履歴
            filename: 出力ファイル名（Noneの場合は自動生成）
            title: タイトル
            
        Returns:
            エクスポートしたファイルのパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.md"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"エクスポート日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for turn in history:
                speaker = turn.get('speaker', 'Unknown')
                message = turn.get('msg', '')
                timestamp = turn.get('timestamp', '')
                
                f.write(f"## {speaker}\n\n")
                if timestamp:
                    f.write(f"*{timestamp}*\n\n")
                f.write(f"{message}\n\n")
                f.write("---\n\n")
        
        return str(filepath)
    
    def export_summary(self, history: List[Dict],
                      filename: str = None) -> str:
        """
        会話履歴のサマリーをエクスポート
        
        Args:
            history: 会話履歴
            filename: 出力ファイル名（Noneの場合は自動生成）
            
        Returns:
            エクスポートしたファイルのパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"
        
        filepath = self.export_dir / filename
        
        # 統計情報の計算
        speakers = {}
        for turn in history:
            speaker = turn.get('speaker', 'Unknown')
            speakers[speaker] = speakers.get(speaker, 0) + 1
        
        summary = {
            "total_turns": len(history),
            "speakers": speakers,
            "start_time": history[0].get('timestamp', '') if history else '',
            "end_time": history[-1].get('timestamp', '') if history else '',
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return str(filepath)


class SystemValidator:
    """システム検証クラス"""
    
    @staticmethod
    def validate_config(config) -> Dict[str, bool]:
        """
        設定の妥当性を検証
        
        Args:
            config: Config オブジェクト
            
        Returns:
            検証結果の辞書
        """
        results = {
            "ollama_host": bool(config.ollama_host),
            "models_defined": bool(config.models),
            "max_turns": config.max_turns > 0,
            "serper_key": bool(config.serper_api_key) if config.enable_search else True
        }
        return results
    
    @staticmethod
    def check_ollama_connection(host: str) -> bool:
        """
        Ollamaサーバーへの接続を確認
        
        Args:
            host: Ollamaホスト
            
        Returns:
            接続可否
        """
        try:
            import requests
            response = requests.get(f"{host}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    @staticmethod
    def check_models_availability(host: str, models: Dict[str, str]) -> Dict[str, bool]:
        """
        モデルの利用可能性を確認
        
        Args:
            host: Ollamaホスト
            models: モデル辞書
            
        Returns:
            各モデルの利用可能性
        """
        results = {}
        try:
            import requests
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                available_models = [m['name'] for m in response.json().get('models', [])]
                for key, model_name in models.items():
                    results[key] = model_name in available_models
            else:
                results = {key: False for key in models.keys()}
        except Exception:
            results = {key: False for key in models.keys()}
        
        return results
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        システム情報を取得
        
        Returns:
            システム情報の辞書
        """
        import platform
        import sys
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "timestamp": datetime.now().isoformat()
        }


def format_timestamp(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    タイムスタンプをフォーマット
    
    Args:
        dt: datetime オブジェクト（Noneの場合は現在時刻）
        format_str: フォーマット文字列
        
    Returns:
        フォーマットされた文字列
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    テキストを指定長で切り詰め
    
    Args:
        text: 入力テキスト
        max_length: 最大長
        suffix: 省略記号
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズ
    
    Args:
        filename: 入力ファイル名
        
    Returns:
        サニタイズされたファイル名
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename