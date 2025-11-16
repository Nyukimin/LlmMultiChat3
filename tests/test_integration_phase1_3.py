"""Phase 1-3統合テスト

Integration Layer (ChatService, MemoryService) と
Phase 1 LangGraphコアの統合動作を検証します。
"""

import asyncio
import pytest

# 統合サービスのインポート
from services.chat_service import ChatService
from services.memory_service import MemoryService


class TestChatServiceIntegration:
    """ChatService統合テスト"""
    
    @pytest.fixture
    def chat_service(self):
        """ChatServiceインスタンス生成"""
        return ChatService()
    
    @pytest.mark.asyncio
    async def test_chat_basic(self, chat_service):
        """基本会話テスト"""
        user_id = "test_user_001"
        session_id = "test_session_001"
        user_input = "こんにちは"
        
        result = await chat_service.chat(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input
        )
        
        assert result is not None
        assert 'response' in result
        assert 'character' in result
        assert 'metadata' in result
        assert len(result['response']) > 0
        print(f"✅ 基本会話テスト成功: {result['response'][:50]}...")
    
    @pytest.mark.asyncio
    async def test_chat_with_character(self, chat_service):
        """キャラクター指定会話テスト"""
        user_id = "test_user_002"
        session_id = "test_session_002"
        user_input = "天気について教えて"
        character = "ノクス"
        
        result = await chat_service.chat(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            character=character
        )
        
        assert result is not None
        assert result.get('character') == character
        print(f"✅ キャラクター指定会話テスト成功: {character}")
    
    @pytest.mark.asyncio
    async def test_stream_chat(self, chat_service):
        """ストリーミング会話テスト"""
        user_id = "test_user_003"
        session_id = "test_session_003"
        user_input = "長い話をしてください"
        
        chunks = []
        async for chunk in chat_service.stream_chat(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = ''.join(chunks)
        assert len(full_response) > 0
        print(f"✅ ストリーミング会話テスト成功: {len(chunks)}チャンク受信")
    
    @pytest.mark.asyncio
    async def test_conversation_history(self, chat_service):
        """会話履歴取得テスト"""
        user_id = "test_user_004"
        session_id = "test_session_004"
        
        # 2ターン会話
        await chat_service.chat(user_id, session_id, "1回目の発言")
        await chat_service.chat(user_id, session_id, "2回目の発言")
        
        # 履歴取得
        history = await chat_service.get_conversation_history(
            user_id=user_id,
            session_id=session_id
        )
        
        assert history is not None
        assert len(history) >= 2
        print(f"✅ 会話履歴取得テスト成功: {len(history)}ターン")
    
    @pytest.mark.asyncio
    async def test_session_management(self, chat_service):
        """セッション管理テスト"""
        user_id = "test_user_005"
        
        # 複数セッション作成
        session_ids = ["session_a", "session_b", "session_c"]
        for session_id in session_ids:
            await chat_service.chat(user_id, session_id, "テスト発言")
        
        # セッション一覧取得
        sessions = await chat_service.list_sessions(user_id)
        
        assert len(sessions) >= len(session_ids)
        print(f"✅ セッション管理テスト成功: {len(sessions)}セッション")
    
    @pytest.mark.asyncio
    async def test_clear_session(self, chat_service):
        """セッションクリアテスト"""
        user_id = "test_user_006"
        session_id = "test_session_006"
        
        # 会話作成
        await chat_service.chat(user_id, session_id, "削除前の発言")
        
        # セッションクリア
        result = await chat_service.clear_session(user_id, session_id)
        
        assert result is True
        
        # クリア後の履歴確認
        history = await chat_service.get_conversation_history(user_id, session_id)
        assert len(history) == 0
        print("✅ セッションクリアテスト成功")


class TestMemoryServiceIntegration:
    """MemoryService統合テスト"""
    
    @pytest.fixture
    def memory_service(self):
        """MemoryServiceインスタンス生成"""
        return MemoryService()
    
    @pytest.mark.asyncio
    async def test_store_and_search_memory(self, memory_service):
        """記憶保存・検索テスト"""
        user_id = "test_user_007"
        
        # 記憶保存
        memory_data = {
            "content": "Pythonは動的型付け言語です",
            "layer": "long_term",
            "metadata": {"topic": "programming"}
        }
        
        store_result = await memory_service.store(
            user_id=user_id,
            session_id="test_session_007",
            content=memory_data["content"],
            layer=memory_data["layer"],
            metadata=memory_data.get("metadata")
        )
        assert store_result is not None
        
        # 記憶検索
        search_result = await memory_service.search(
            user_id=user_id,
            query="Python",
            layers=["long_term"]
        )
        
        assert search_result is not None
        assert len(search_result) > 0
        print(f"✅ 記憶保存・検索テスト成功: {len(search_result)}件検索")
    
    @pytest.mark.asyncio
    async def test_memory_stats(self, memory_service):
        """記憶統計テスト"""
        user_id = "test_user_008"
        
        # 記憶統計取得
        stats = await memory_service.get_stats(user_id)
        
        assert stats is not None
        assert 'total_memories' in stats
        assert 'layers' in stats
        print(f"✅ 記憶統計テスト成功: {stats['total_memories']}件")
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_service):
        """記憶削除テスト"""
        user_id = "test_user_009"
        
        # 記憶保存
        memory_data = {
            "content": "削除対象の記憶",
            "layer": "mid_term"
        }
        store_result = await memory_service.store(
            user_id=user_id,
            session_id="test_session_009",
            content=memory_data["content"],
            layer=memory_data["layer"]
        )
        memory_id = store_result.get('memory_id')
        
        # 記憶削除
        delete_result = await memory_service.delete(user_id, memory_id)
        
        assert delete_result is True
        print("✅ 記憶削除テスト成功")
    
    @pytest.mark.asyncio
    async def test_multi_layer_search(self, memory_service):
        """複数階層検索テスト"""
        user_id = "test_user_010"
        
        # 複数階層に記憶保存
        layers = ["short_term", "mid_term", "long_term"]
        for i, layer in enumerate(layers):
            await memory_service.store(
                user_id=user_id,
                session_id=f"test_session_010_{i}",
                content=f"{layer}の記憶内容",
                layer=layer
            )
        
        # 複数階層検索
        search_result = await memory_service.search(
            user_id=user_id,
            query="記憶内容",
            layers=layers
        )
        
        assert len(search_result) >= len(layers)
        print(f"✅ 複数階層検索テスト成功: {len(search_result)}件")
    
    @pytest.mark.asyncio
    async def test_health_check(self, memory_service):
        """ヘルスチェックテスト"""
        health = await memory_service.health_check()
        
        assert health is not None
        assert 'status' in health
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        print(f"✅ ヘルスチェックテスト成功: {health['status']}")


class TestEndToEndIntegration:
    """エンドツーエンド統合テスト"""
    
    @pytest.mark.asyncio
    async def test_chat_with_memory_retrieval(self):
        """記憶取得を含む会話テスト"""
        chat_service = ChatService()
        memory_service = MemoryService()
        
        user_id = "test_user_011"
        session_id = "test_session_011"
        
        # 事前に記憶を保存
        await memory_service.store(
            user_id=user_id,
            session_id=session_id,
            content="ユーザーは機械学習に興味がある",
            layer="long_term",
            metadata={"topic": "interest"}
        )
        
        # 関連する会話
        result = await chat_service.chat(
            user_id=user_id,
            session_id=session_id,
            user_input="私の興味について知っていますか？"
        )
        
        assert result is not None
        assert len(result['response']) > 0
        print("✅ 記憶統合会話テスト成功")
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_with_memory(self):
        """複数ターン会話と記憶蓄積テスト"""
        chat_service = ChatService()
        memory_service = MemoryService()
        
        user_id = "test_user_012"
        session_id = "test_session_012"
        
        # 3ターン会話
        turns = [
            "私の名前は田中です",
            "Pythonが好きです",
            "東京に住んでいます"
        ]
        
        for turn in turns:
            await chat_service.chat(user_id, session_id, turn)
        
        # 記憶統計確認
        stats = await memory_service.get_stats(user_id)
        
        assert stats['total_memories'] >= len(turns)
        print(f"✅ 複数ターン会話・記憶蓄積テスト成功: {stats['total_memories']}件記憶")
    
    @pytest.mark.asyncio
    async def test_concurrent_users(self):
        """複数ユーザー同時処理テスト"""
        chat_service = ChatService()
        
        # 3ユーザー同時会話
        users = [
            ("user_a", "session_a", "ユーザーAの発言"),
            ("user_b", "session_b", "ユーザーBの発言"),
            ("user_c", "session_c", "ユーザーCの発言")
        ]
        
        tasks = [
            chat_service.chat(user_id, session_id, message)
            for user_id, session_id, message in users
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(users)
        assert all(r is not None for r in results)
        print(f"✅ 複数ユーザー同時処理テスト成功: {len(results)}ユーザー")


def run_integration_tests():
    """統合テスト実行エントリーポイント"""
    print("=" * 60)
    print("Phase 1-3統合テスト開始")
    print("=" * 60)
    
    # pytest実行
    exit_code = pytest.main([
        __file__,
        "-v",
        "--asyncio-mode=auto",
        "--tb=short"
    ])
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ 全統合テスト成功")
    else:
        print(f"❌ 統合テスト失敗 (exit code: {exit_code})")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_integration_tests()
    exit(exit_code)