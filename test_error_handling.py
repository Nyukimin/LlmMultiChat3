"""
test_error_handling.py
エラーハンドリング機能のユニットテスト

Week 5で実装したエラーハンドリング機能の動作を検証。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from exceptions import (
    ShortTermMemoryError,
    MidTermMemoryError,
    LongTermMemoryError,
    LLMNodeError,
    LLMInvocationError
)
from memory_manager import MemorySystemManager
from memory.base import MemoryConfig


class TestMemoryManagerErrorHandling:
    """MemorySystemManagerのエラーハンドリングテスト"""
    
    def test_add_conversation_turn_raises_on_failure(self):
        """会話ターン追加失敗時に例外が発生することを確認"""
        manager = MemorySystemManager()
        
        # short_term.storeを失敗させる
        with patch.object(manager.short_term, 'store', side_effect=Exception("DB Error")):
            with pytest.raises(ShortTermMemoryError) as excinfo:
                manager.add_conversation_turn("User", "テスト")
            
            assert "会話ターン追加失敗" in str(excinfo.value)
    
    def test_save_session_raises_on_failure(self):
        """セッション保存失敗時に例外が発生することを確認"""
        manager = MemorySystemManager()
        
        with patch.object(manager.session_manager, 'save_session', side_effect=Exception("JSON Error")):
            with pytest.raises(MidTermMemoryError) as excinfo:
                manager.save_session("session_001", [])
            
            assert "セッション保存失敗" in str(excinfo.value)
    
    def test_load_session_raises_on_failure(self):
        """セッション読み込み失敗時に例外が発生することを確認"""
        manager = MemorySystemManager()
        
        with patch.object(manager.session_manager, 'load_session', side_effect=Exception("File Not Found")):
            with pytest.raises(MidTermMemoryError) as excinfo:
                manager.load_session("session_001")
            
            assert "セッション読み込み失敗" in str(excinfo.value)
    
    def test_update_character_kpi_raises_on_failure(self):
        """KPI更新失敗時に例外が発生することを確認"""
        manager = MemorySystemManager()
        
        with patch.object(manager.kpi_manager, 'increment_kpi', side_effect=Exception("KPI Error")):
            with pytest.raises(LongTermMemoryError) as excinfo:
                manager.update_character_kpi("ルミナ", "user_thumbs_up")
            
            assert "KPI更新失敗" in str(excinfo.value)
    
    def test_search_knowledge_returns_empty_on_failure(self):
        """知識検索失敗時は空リストを返す（システムを止めない）"""
        manager = MemorySystemManager()
        
        with patch.object(manager.knowledge_base, 'search', side_effect=Exception("Search Error")):
            results = manager.search_knowledge("テスト")
            assert results == []
    
    def test_logger_integration(self):
        """ログマネージャーが正しく統合されていることを確認"""
        manager = MemorySystemManager()
        assert hasattr(manager, 'logger')
        assert manager.logger is not None


class TestLLMNodeErrorHandling:
    """LLMNodeのエラーハンドリングテスト（ollamaがある環境でのみ実行）"""
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('llm_nodes.ollama.chat')
    def test_call_ollama_with_retry_success(self, mock_chat):
        """LLM呼び出しが成功する場合"""
        from llm_nodes import LuminaNode
        from config import Config
        
        mock_chat.return_value = {'message': {'content': 'テスト応答'}}
        
        node = LuminaNode(Config())
        response = node._call_ollama("テストプロンプト")
        
        assert response == 'テスト応答'
        assert mock_chat.call_count == 1
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('llm_nodes.ollama.chat')
    @patch('llm_nodes.time.sleep')
    def test_call_ollama_with_retry_recovers(self, mock_sleep, mock_chat):
        """LLM呼び出しがリトライで回復する場合"""
        from llm_nodes import LuminaNode
        from config import Config
        
        mock_chat.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            {'message': {'content': 'リトライ成功'}}
        ]
        
        node = LuminaNode(Config())
        response = node._call_ollama("テストプロンプト", max_retries=3)
        
        assert response == 'リトライ成功'
        assert mock_chat.call_count == 3
        assert mock_sleep.call_count == 2
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('llm_nodes.ollama.chat')
    @patch('llm_nodes.time.sleep')
    def test_call_ollama_with_retry_fallback(self, mock_sleep, mock_chat):
        """LLM呼び出しが全て失敗した場合フォールバック応答"""
        from llm_nodes import LuminaNode
        from config import Config
        
        mock_chat.side_effect = Exception("Timeout")
        
        node = LuminaNode(Config())
        response = node._call_ollama("テストプロンプト", max_retries=3)
        
        assert "申し訳ございません" in response or "エラー" in response
        assert mock_chat.call_count == 3
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    def test_fallback_response_varies_by_character(self):
        """キャラクターごとに異なるフォールバック応答"""
        from llm_nodes import LuminaNode, ClarisNode, NoxNode
        from config import Config
        
        config = Config()
        
        lumina = LuminaNode(config)
        claris = ClarisNode(config)
        nox = NoxNode(config)
        
        assert lumina._get_fallback_response() != claris._get_fallback_response()
        assert claris._get_fallback_response() != nox._get_fallback_response()
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    def test_logger_integration_in_llm_node(self):
        """LLMNodeにログマネージャーが統合されていることを確認"""
        from llm_nodes import LuminaNode
        from config import Config
        
        node = LuminaNode(Config())
        assert hasattr(node, 'logger')
        assert node.logger is not None


class TestMainAppErrorHandling:
    """main.pyのエラーハンドリングテスト（ollamaがある環境でのみ実行）"""
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('main.LuminaNode.generate')
    def test_lumina_node_error_recovery(self, mock_generate):
        """ルミナノードエラー時のリカバリー"""
        from main import MultiLLMChat
        
        mock_generate.side_effect = LLMNodeError("LLM Error", node_name="ルミナ")
        
        app = MultiLLMChat()
        state = {
            'user_input': 'テスト',
            'history': [],
            'current_turn': 1
        }
        
        result = app._lumina_node(state)
        
        assert 'history' in result
        assert len(result['history']) > 0
        assert 'system' in result['history'][-1]['speaker']
        assert 'エラー' in result['history'][-1]['msg']
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('main.ClarisNode.generate')
    def test_claris_node_error_recovery(self, mock_generate):
        """クラリスノードエラー時のリカバリー"""
        from main import MultiLLMChat
        
        mock_generate.side_effect = LLMNodeError("LLM Error", node_name="クラリス")
        
        app = MultiLLMChat()
        state = {
            'user_input': 'テスト',
            'history': [],
            'current_turn': 1
        }
        
        result = app._claris_node(state)
        
        assert 'history' in result
        assert len(result['history']) > 0
        assert 'クラリス' in result['history'][-1]['msg']
    
    @pytest.mark.skip(reason="ollama未インストール環境ではスキップ")
    @patch('main.NoxNode.generate')
    def test_nox_node_error_recovery(self, mock_generate):
        """ノクスノードエラー時のリカバリー"""
        from main import MultiLLMChat
        
        mock_generate.side_effect = LLMNodeError("LLM Error", node_name="ノクス")
        
        app = MultiLLMChat()
        state = {
            'user_input': 'テスト',
            'history': [],
            'current_turn': 1
        }
        
        result = app._nox_node(state)
        
        assert 'history' in result
        assert len(result['history']) > 0
        assert 'ノクス' in result['history'][-1]['msg']


class TestErrorHandlingIntegration:
    """エラーハンドリング統合テスト"""
    
    def test_exception_chaining(self):
        """例外チェーンが正しく機能することを確認"""
        manager = MemorySystemManager()
        
        with patch.object(manager.short_term, 'store', side_effect=ValueError("Original Error")):
            try:
                manager.add_conversation_turn("User", "テスト")
            except ShortTermMemoryError as e:
                assert e.__cause__ is not None
                assert isinstance(e.__cause__, ValueError)
                assert "Original Error" in str(e.__cause__)
    
    def test_error_logging(self):
        """エラーが正しくログに記録されることを確認"""
        manager = MemorySystemManager()
        
        with patch.object(manager.short_term, 'store', side_effect=Exception("Test Error")):
            with patch.object(manager.logger, 'log_error') as mock_log:
                try:
                    manager.add_conversation_turn("User", "テスト")
                except ShortTermMemoryError:
                    pass
                
                # log_errorが呼ばれたことを確認
                assert mock_log.call_count == 1
                call_args = mock_log.call_args
                assert call_args[1]['context'] == "add_conversation_turn"
    
    def test_multiple_errors_handled_gracefully(self):
        """複数のエラーが適切に処理されることを確認"""
        manager = MemorySystemManager()
        
        # 複数の操作でエラーが発生しても、それぞれ適切に処理される
        errors = []
        
        with patch.object(manager.short_term, 'store', side_effect=Exception("Error 1")):
            try:
                manager.add_conversation_turn("User", "テスト1")
            except ShortTermMemoryError as e:
                errors.append(e)
        
        with patch.object(manager.session_manager, 'save_session', side_effect=Exception("Error 2")):
            try:
                manager.save_session("session_001", [])
            except MidTermMemoryError as e:
                errors.append(e)
        
        assert len(errors) == 2
        assert isinstance(errors[0], ShortTermMemoryError)
        assert isinstance(errors[1], MidTermMemoryError)


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])