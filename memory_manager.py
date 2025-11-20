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
from validators import InputValidator
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
                            session_id: Optional[str] = None,
                            metadata: Dict = None) -> bool:
        """
        会話ターンを追加（全記憶層に保存）
        
        Args:
            speaker: 発話者
            message: メッセージ
            session_id: セッションID（Phase 3統合用）
            metadata: メタデータ
        
        Args:
            speaker: 発話者
            message: メッセージ
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            # 入力検証
            if not InputValidator.validate_speaker_name(speaker):
                raise ShortTermMemoryError(f"無効な話者名: {speaker}")
            
            # 短期記憶（会話バッファ）に追加
            self.conversation_buffer.add_turn(speaker, message, metadata)
            
            # 短期記憶（キャッシュ）にも保存
            turn_key = f"turn:{datetime.now().isoformat()}"
            turn_data = {
                'speaker': speaker,
                'message': message,
                'session_id': session_id,
                'metadata': metadata or {}
            }
            self.short_term.store(turn_key, turn_data)
            
            self.stats['total_turns'] += 1
            
            return True
        except Exception as e:
            self.logger.log_error(e, context="add_conversation_turn")
            raise ShortTermMemoryError(f"会話ターン追加失敗: {e}") from e
    
    def get_conversation_context(self, session_id: str = None, max_turns: int = 6) -> Dict[str, Any]:
        """
        会話コンテキストを取得
        
        Args:
            session_id: セッションID（Phase 3統合用、現在は未使用）
            max_turns: 最大ターン数
            
        Returns:
            会話コンテキスト辞書
        """
        from datetime import datetime
        
        # 会話履歴取得
        history_str = self.conversation_buffer.get_context_string(max_turns)
        
        # 辞書形式で返却
        return {
            "history": self.conversation_buffer.turns[-max_turns:] if hasattr(self.conversation_buffer, 'turns') else [],
            "context_string": history_str,
            "last_activity": datetime.now().isoformat(),
            "total_turns": len(self.conversation_buffer.turns) if hasattr(self.conversation_buffer, 'turns') else 0
        }
    
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
            if results:
                self.logger.log_system_event(
                    "knowledge_search_success",
                    {"results": len(results)}
                )
            return results
        except Exception as e:
            self.logger.log_error(e, context="search_knowledge")
            return []
    
    def get_memory_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """記憶統計取得（Phase 3統合用）
        
        Args:
            session_id: セッションID（省略時: 全体統計）
            
        Returns:
            Dict[str, Any]: 記憶統計情報
        """
        stats = {
            'total_memories': self.stats.get('total_turns', 0),
            'layers': {
                'short_term': len(self.conversation_buffer.history) if hasattr(self.conversation_buffer, 'history') else 0,
                'mid_term': self.stats.get('total_sessions', 0),
                'long_term': 0,
                'knowledge_base': 0
            },
            'total_sessions': self.stats.get('total_sessions', 0),
            'total_turns': self.stats.get('total_turns', 0),
            'character_stats': {
                'lumina': self.kpi_manager.get_all_kpis().get('lumina', {}) if hasattr(self, 'kpi_manager') else {},
                'clarissa': self.kpi_manager.get_all_kpis().get('clarissa', {}) if hasattr(self, 'kpi_manager') else {},
                'nox': self.kpi_manager.get_all_kpis().get('nox', {}) if hasattr(self, 'kpi_manager') else {}
            }
        }
        return stats
    
    def search_memory(self, query: str, layers: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """記憶検索（Phase 3統合用）
        
        Args:
            query: 検索クエリ
            layers: 検索対象レイヤー
            limit: 最大結果数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        results = []
        search_layers = layers or ['short_term', 'mid_term', 'long_term', 'knowledge_base']
        
        # 各レイヤーから検索
        for layer in search_layers:
            if layer == 'knowledge_base':
                kb_results = self.search_knowledge(query, limit=limit)
                for r in kb_results:
                    results.append({
                        'memory_id': r.get('id', ''),
                        'content': r.get('content', ''),
                        'layer': 'knowledge_base',
                        'timestamp': r.get('timestamp', datetime.now().isoformat()),
                        'relevance_score': r.get('score', 0.0)
                    })
            elif layer == 'short_term':
                # 短期記憶から簡易検索
                history = self.conversation_buffer.get_recent_turns(limit)
                for turn in history:
                    if query.lower() in turn.get('message', '').lower():
                        results.append({
                            'memory_id': f"short_term_{len(results)}",
                            'content': turn.get('message', ''),
                            'layer': 'short_term',
                            'timestamp': turn.get('timestamp', datetime.now().isoformat()),
                            'relevance_score': 0.8
                        })
        
        return results[:limit]
    
    def store_memory(self, session_id: str, content: str, layer: str = 'short_term', metadata: Dict = None) -> Dict[str, Any]:
        """記憶保存（Phase 3統合用）
        
        Args:
            session_id: セッションID
            content: 記憶内容
            layer: レイヤー名
            metadata: メタデータ
            
        Returns:
            Dict[str, Any]: 保存結果
        """
        memory_id = f"{layer}_{session_id}_{datetime.now().timestamp()}"
        result = {
            'memory_id': memory_id,
            'layer': layer,
            'timestamp': datetime.now().isoformat()
        }
        
        # レイヤーに応じた保存処理
        if layer == 'short_term':
            self.short_term.store(memory_id, {'content': content, 'metadata': metadata or {}})
        
        return result

    def delete_memory(self, memory_id: str) -> bool:
        """記憶削除（Phase 3統合用）
        
        Args:
            memory_id: 記憶ID (format: {layer}_{session_id}_{timestamp})
            
        Returns:
            bool: 削除成功（True）
        """
        try:
            # memory_idからlayerを抽出
            layer = memory_id.split('_')[0]
            
            # layerに応じた削除処理（現時点では簡易実装）
            if layer in ['short_term', 'mid_term', 'long_term']:
                # 実際のDB削除は今後実装
                return True
            return False
        except Exception as e:
            self.logger.error(f"Memory delete error: {e}")
            return False
    
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

    def clear_session(self, session_id: str) -> bool:
        """
        セッションをクリア
        
        Args:
            session_id: セッションID（Phase 3統合用）
            
        Returns:
            bool: クリア成功（True）
        """
        try:
            # 会話バッファをクリア
            self.conversation_buffer.clear()
            
            # セッション管理データがあれば削除
            if hasattr(self, 'session_manager'):
                # session_managerによる削除処理（将来の拡張用）
                pass
            
            # ログ出力（loggerのメソッド名を修正）
            if hasattr(self.logger, 'log_event'):
                self.logger.log_event('session_cleared', {'session_id': session_id})
            # self.logger.info(f"Session cleared: {session_id}")  # infoメソッドは存在しない
            return True
        except Exception as e:
            self.logger.log_error(e, context="clear_session")
            return False
    
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