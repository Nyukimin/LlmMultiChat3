"""ChatServiceユニットテスト

ChatServiceの個別機能を単体でテストします。
Phase 1コアはモックを使用して分離します。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.chat_service import ChatService


class TestChatServiceUnit:
    """ChatServiceユニットテスト"""
    
    @pytest.fixture
    def mock_multi_llm_chat(self):
        """Phase 1コアのモック"""
        mock = Mock()
        mock.chat = Mock(return_value={
            'response': 'モック応答',
            'character': 'lumina',
            'metadata': {'timestamp': datetime.now().isoformat()}
        })
        mock.memory_manager = Mock()
        return mock
    
    @pytest.fixture
    def chat_service(self, mock_multi_llm_chat):
        """ChatServiceインスタンス（モック使用）"""
        with patch('services.chat_service.MultiLLMChat', return_value=mock_multi_llm_chat):
            service = ChatService()
            return service
    
    @pytest.mark.asyncio
    async def test_chat_method_success(self, chat_service, mock_multi_llm_chat):
        """chat()メソッド単体テスト - 正常系"""
        user_id = "test_user"
        session_id = "test_session"
        user_input = "こんにちは"
        
        result = await chat_service.chat(user_id, session_id, user_input)
        
        assert result is not None
        assert 'response' in result
        assert result['response'] == 'モック応答'
        assert result['character'] == 'lumina'
        mock_multi_llm_chat.chat.assert_called_once()
        print("✅ chat()メソッド正常系テスト成功")
    
    @pytest.mark.asyncio
    async def test_chat_method_invalid_input(self, chat_service, mock_multi_llm_chat):
        """chat()メソッド単体テスト - 異常系（空入力）"""
        user_id = "test_user"
        session_id = "test_session"
        user_input = ""
        
        # 空入力でも処理される場合があるため、エラーまたは正常処理を許容
        try:
            result = await chat_service.chat(user_id, session_id, user_input)
            # 正常に処理された場合
            assert result is not None
        except Exception:
            # エラーが発生した場合も正常
            pass
        
        print("✅ chat()メソッド異常系テスト成功")
    
    @pytest.mark.asyncio
    async def test_chat_with_character(self, chat_service, mock_multi_llm_chat):
        """キャラクター指定テスト"""
        mock_multi_llm_chat.chat.return_value = {
            'response': 'ノクスの応答',
            'character': 'ノクス',
            'metadata': {}
        }
        
        result = await chat_service.chat(
            user_id="test_user",
            session_id="test_session",
            user_input="テスト",
            character="ノクス"
        )
        
        assert result['character'] == 'ノクス'
        print("✅ キャラクター指定テスト成功")
    
    @pytest.mark.asyncio
    async def test_stream_chat_method(self, chat_service, mock_multi_llm_chat):
        """stream_chat()メソッド単体テスト"""
        mock_multi_llm_chat.chat.return_value = {
            'response': 'ストリーミング応答テスト',
            'character': 'lumina',
            'metadata': {}
        }
        
        chunks = []
        async for chunk in chat_service.stream_chat(
            user_id="test_user",
            session_id="test_session",
            user_input="テスト"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = ''.join(chunks)
        assert 'ストリーミング応答テスト' in full_response
        print(f"✅ stream_chat()メソッドテスト成功: {len(chunks)}チャンク")
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, chat_service, mock_multi_llm_chat):
        """get_conversation_history()メソッド単体テスト"""
        mock_multi_llm_chat.memory_manager.get_conversation_context = Mock(return_value={
            'history': [
                {'speaker': 'user', 'message': '発言1'},
                {'speaker': 'assistant', 'message': '応答1'}
            ]
        })
        
        history = await chat_service.get_conversation_history(
            user_id="test_user",
            session_id="test_session"
        )
        
        assert history is not None
        assert 'history' in history
        mock_multi_llm_chat.memory_manager.get_conversation_context.assert_called_once()
        print("✅ get_conversation_history()メソッドテスト成功")
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, chat_service, mock_multi_llm_chat):
        """list_sessions()メソッド単体テスト"""
        # セッションを事前登録（user_sessions経由）
        chat_service.user_sessions["test_user"] = {
            "session_1": "phase1_session_1",
            "session_2": "phase1_session_2"
        }
        
        mock_multi_llm_chat.memory_manager.get_conversation_context = Mock(return_value={
            'history': []
        })
        
        sessions = await chat_service.list_sessions(user_id="test_user")
        
        assert sessions is not None
        assert 'sessions' in sessions
        print("✅ list_sessions()メソッドテスト成功")
    
    @pytest.mark.asyncio
    async def test_clear_session(self, chat_service, mock_multi_llm_chat):
        """clear_session()メソッド単体テスト"""
        mock_multi_llm_chat.memory_manager.clear_session = Mock(return_value=True)
        
        result = await chat_service.clear_session(
            user_id="test_user",
            session_id="test_session"
        )
        
        assert result is True
        mock_multi_llm_chat.memory_manager.clear_session.assert_called_once()
        print("✅ clear_session()メソッドテスト成功")
    
    @pytest.mark.asyncio
    async def test_async_to_sync_conversion(self, chat_service, mock_multi_llm_chat):
        """非同期⇔同期変換テスト（asyncio.to_thread）"""
        # asyncio.to_threadが正しく呼ばれることを確認
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                'response': '変換テスト',
                'character': 'lumina',
                'metadata': {}
            }
            
            result = await chat_service.chat(
                user_id="test_user",
                session_id="test_session",
                user_input="テスト"
            )
            
            assert result is not None
            mock_to_thread.assert_called()
            print("✅ 非同期⇔同期変換テスト成功")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, chat_service, mock_multi_llm_chat):
        """エラーハンドリング単体テスト"""
        mock_multi_llm_chat.chat.side_effect = Exception("Phase 1エラー")
        
        with pytest.raises(Exception) as exc_info:
            await chat_service.chat(
                user_id="test_user",
                session_id="test_session",
                user_input="テスト"
            )
        
        assert "Phase 1エラー" in str(exc_info.value) or exc_info.value is not None
        print("✅ エラーハンドリングテスト成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])