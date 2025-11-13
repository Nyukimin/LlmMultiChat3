"""
memory_manager.py
記憶システム統合マネージャー

5階層記憶システム（短期・中期・長期・知識ベース）を統合管理。
メインアプリケーションとのインターフェースを提供。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from memory import ShortTermMemory, MidTermMemory, LongTermMemory, KnowledgeBase
from exceptions import ShortTermMemoryError, MidTermMemoryError, LongTermMemoryError
from utils import Logger
from memory.base import MemoryConfig
from memory.short_term import ConversationBuffer
from memory.mid_term import SessionManager
from memory.long_term import CharacterKPIManager
from memory.knowledge_base import KnowledgeBaseManager


class MemorySystemManager:
    """記憶システム統合マネージャー"""
    
    def __init__(self, config: MemoryConfig = None):
        """
        初期化
        
        Args:
            config: メモリ設定
        """
        self.config = config or MemoryConfig()
        self.logger = Logger()  # ログマネージャー追加
        
        # 各記憶システムの初期化
        self.short_term = ShortTermMemory(self.config)
        self.mid_term = MidTermMemory(self.config)
        self.long_term = LongTermMemory(self.config)
        self.knowledge_base = KnowledgeBase(self.config)
        
        # 補助マネージャーの初期化
        self.conversation_buffer = ConversationBuffer(max_turns=12)
        self.session_manager = SessionManager(self.mid_term)
        self.kpi_manager = CharacterKPIManager(self.long_term)
        self.kb_manager = KnowledgeBaseManager(self.knowledge_base)
        
        # 統計情報
        self.stats = {
            'total_conversations': 0,
            'total_turns': 0,
            'total_sessions': 0
        }
    
    def add_conversation_turn(self, speaker: str, message: str, 
                            metadata: Dict = None) -> bool:
        """
        会話ターンを追加（全記憶層に保存）
        
        Args:
            speaker: 発話者
            message: メッセージ
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            # 短期記憶（会話バッファ）に追加
            self.conversation_buffer.add_turn(speaker, message, metadata)
            
            # 短期記憶（キャッシュ）にも保存
            turn_key = f"turn:{datetime.now().isoformat()}"
            turn_data = {
                'speaker': speaker,
                'message': message,
                'metadata': metadata or {}
            }
            self.short_term.store(turn_key, turn_data)
            
            self.stats['total_turns'] += 1
            
            return True
        except Exception as e:
            self.logger.log_error(e, context="add_conversation_turn")
            raise ShortTermMemoryError(f"会話ターン追加失敗: {e}") from e
    
    def get_conversation_context(self, max_turns: int = 6) -> str:
        """
        会話コンテキストを取得
        
        Args:
            max_turns: 最大ターン数
            
        Returns:
            フォーマットされた会話文字列
        """
        return self.conversation_buffer.get_context_string(max_turns)
    
    def save_session(self, session_id: str, history: List[Dict],
                    metadata: Dict = None) -> bool:
        """
        セッションを中期記憶に保存
        
        Args:
            session_id: セッションID
            history: 会話履歴
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            self.logger.log_system_event(
                "session_save_start",
                {"session_id": session_id, "turns": len(history)}
            )
            success = self.session_manager.save_session(
                session_id, history, metadata
            )
            if success:
                self.stats['total_sessions'] += 1
                self.logger.log_system_event(
                    "session_save_success",
                    {"session_id": session_id}
                )
            return success
        except Exception as e:
            self.logger.log_error(e, context="save_session")
            raise MidTermMemoryError(f"セッション保存失敗: {e}") from e
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションを中期記憶から読み込み
        
        Args:
            session_id: セッションID
            
        Returns:
            セッション情報、存在しない場合None
        """
        try:
            self.logger.log_system_event(
                "session_load",
                {"session_id": session_id}
            )
            session = self.session_manager.load_session(session_id)
            if session:
                self.logger.log_system_event(
                    "session_load_success",
                    {"session_id": session_id}
                )
            return session
        except Exception as e:
            self.logger.log_error(e, context="load_session")
            raise MidTermMemoryError(f"セッション読み込み失敗: {e}") from e
    
    def update_character_kpi(self, character: str, kpi_type: str, 
                           value: int = 1) -> bool:
        """
        キャラクターKPIを更新
        
        Args:
            character: キャラクター名
            kpi_type: KPI種別（user_thumbs_up, answer_hits, search_success）
            value: 増加量
            
        Returns:
            成功した場合True
        """
        try:
            self.logger.log_system_event(
                "kpi_update",
                {"character": character, "kpi_type": kpi_type, "value": value}
            )
            success = self.kpi_manager.increment_kpi(character, kpi_type, value)
            if success:
                self.logger.log_system_event(
                    "kpi_update_success",
                    {"character": character, "kpi_type": kpi_type}
                )
            return success
        except Exception as e:
            self.logger.log_error(e, context="update_character_kpi")
            raise LongTermMemoryError(f"KPI更新失敗: {e}") from e
    
    def get_character_level(self, character: str) -> int:
        """
        キャラクターレベルを取得
        
        Args:
            character: キャラクター名
            
        Returns:
            レベル
        """
        return self.kpi_manager.get_character_level(character)
    
    def search_knowledge(self, query: str, namespace: str = None, 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """
        知識ベースを検索
        
        Args:
            query: 検索クエリ
            namespace: 名前空間（Noneの場合は全体）
            limit: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        try:
            self.logger.log_system_event(
                "knowledge_search",
                {"query": query, "namespace": namespace, "limit": limit}
            )
            results = self.knowledge_base.search(query, namespace, limit)
            self.logger.log_system_event(
                "knowledge_search_success",
                {"result_count": len(results)}
            )
            return results
        except Exception as e:
            self.logger.log_error(e, context="search_knowledge")
            # 検索失敗時は空リストを返す（システムを止めない）
            return []
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        全記憶システムの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'short_term': self.short_term.get_stats(),
            'mid_term': self.mid_term.get_stats(),
            'long_term': self.long_term.get_stats(),
            'knowledge_base': self.knowledge_base.get_stats(),
            'manager_stats': self.stats
        }
    
    def cleanup(self) -> Dict[str, int]:
        """
        期限切れデータのクリーンアップ
        
        Returns:
            削除件数の辞書
        """
        return {
            'short_term': self.short_term.cleanup_expired(),
            'mid_term': self.mid_term.cleanup_expired()
        }
    
    def reset_conversation(self):
        """会話バッファをリセット"""
        self.conversation_buffer.clear()
        self.stats['total_conversations'] += 1
    
    def initialize_characters(self):
        """全キャラクターのKPIを初期化"""
        characters = ['ルミナ', 'クラリス', 'ノクス']
        for char in characters:
            self.kpi_manager.initialize_character(char)
    
    def get_memory_summary(self) -> str:
        """
        記憶システムのサマリーを文字列で取得
        
        Returns:
            サマリー文字列
        """
        stats = self.get_all_stats()
        
        summary = []
        summary.append("=== 記憶システムサマリー ===")
        summary.append(f"短期記憶: {stats['short_term']['current_items']} アイテム")
        summary.append(f"中期記憶: {stats['mid_term']['current_items']} アイテム")
        summary.append(f"長期記憶: {stats['long_term']['total_profiles']} プロファイル")
        summary.append(f"知識ベース: {stats['knowledge_base']['total_items']} アイテム")
        summary.append(f"総会話数: {self.stats['total_conversations']}")
        summary.append(f"総ターン数: {self.stats['total_turns']}")
        
        return "\n".join(summary)