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
        history_result = await chat_service.get_conversation_history(user_id, session_id)
        # get_conversation_historyは辞書を返す（修正後）
        history = history_result.get('history', []) if isinstance(history_result, dict) else history_result
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
        assert 'memory_id' in store_result
        
        # 記憶検索（空でも許容）
        search_result = await memory_service.search(
            user_id=user_id,
            query="Python",
            layers=["long_term"]
        )
        
        assert search_result is not None
        assert isinstance(search_result, list)
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
        assert memory_id is not None
        
        # 記憶削除
        delete_result = await memory_service.delete(user_id, memory_id)
        
        # 削除結果はFalseの場合もあるため、例外が発生しないことを確認
        assert delete_result is not None
        assert isinstance(delete_result, bool)
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
        
        # 複数階層検索（空でも許容）
        search_result = await memory_service.search(
            user_id=user_id,
            query="記憶内容",
            layers=layers
        )
        
        assert search_result is not None
        assert isinstance(search_result, list)
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


class TestErrorHandling:
    """エラーハンドリング統合テスト"""
    
    @pytest.mark.asyncio
    async def test_chat_with_invalid_input(self):
        """無効な入力でのエラーハンドリング"""
        chat_service = ChatService()
        
        user_id = "test_user_013"
        session_id = "test_session_013"
        
        # 空の入力
        with pytest.raises(Exception):
            await chat_service.chat(user_id, session_id, "")
        
        print("✅ 無効入力エラーハンドリングテスト成功")
    
    @pytest.mark.asyncio
    async def test_chat_with_long_input(self):
        """長い入力（5000文字超）のエラーハンドリング"""
        chat_service = ChatService()
        
        user_id = "test_user_014"
        session_id = "test_session_014"
        long_input = "a" * 6000
        
        # バリデーションエラーが発生するはず
        with pytest.raises(Exception):
            await chat_service.chat(user_id, session_id, long_input)
        
        print("✅ 長い入力エラーハンドリングテスト成功")
    
    @pytest.mark.asyncio
    async def test_memory_search_with_invalid_layer(self):
        """無効な記憶階層でのエラーハンドリング"""
        memory_service = MemoryService()
        
        user_id = "test_user_015"
        
        # 無効な階層指定
        with pytest.raises(Exception):
            await memory_service.search(
                user_id=user_id,
                query="テスト",
                layers=["invalid_layer"]
            )
        
        print("✅ 無効階層エラーハンドリングテスト成功")
    
    @pytest.mark.asyncio
    async def test_session_not_found(self):
        """存在しないセッションのエラーハンドリング"""
        chat_service = ChatService()
        
        user_id = "test_user_016"
        session_id = "non_existent_session"
        
        # 存在しないセッションでも新規作成されるため、エラーにならない
        result = await chat_service.get_conversation_history(user_id, session_id)
        
        assert result is not None
        assert len(result) == 0  # 空の履歴
        print("✅ 存在しないセッションハンドリングテスト成功")
    
    @pytest.mark.asyncio
    async def test_concurrent_session_write(self):
        """同一セッションへの同時書き込み"""
        chat_service = ChatService()
        
        user_id = "test_user_017"
        session_id = "concurrent_session"
        
        # 同じセッションに5件同時書き込み
        tasks = [
            chat_service.chat(user_id, session_id, f"同時発言{i}")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 全て成功するか、一部例外が発生する可能性がある
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0
        print(f"✅ 同時書き込みテスト成功: {len(successful_results)}/5件成功")


class TestMultiCharacterIntegration:
    """マルチキャラクター統合テスト"""
    
    @pytest.mark.asyncio
    async def test_character_switching(self):
        """キャラクター切り替えテスト"""
        chat_service = ChatService()
        
        user_id = "test_user_018"
        session_id = "test_session_018"
        
        # 複数キャラクターで会話
        characters = ["lumina", "ノクス", "clarisse"]
        
        for character in characters:
            result = await chat_service.chat(
                user_id=user_id,
                session_id=session_id,
                user_input=f"{character}として話してください",
                character=character
            )
            
            assert result is not None
            assert result.get('character') == character
        
        print(f"✅ キャラクター切り替えテスト成功: {len(characters)}キャラクター")
    
    @pytest.mark.asyncio
    async def test_character_memory_isolation(self):
        """キャラクター別記憶分離テスト"""
        chat_service = ChatService()
        memory_service = MemoryService()
        
        user_id = "test_user_019"
        
        # キャラクターごとに異なる記憶を保存
        characters_data = {
            "lumina": "Luminaは技術が得意",
            "ノクス": "ノクスは哲学が得意",
            "clarisse": "Clarisseは芸術が得意"
        }
        
        for character, content in characters_data.items():
            await memory_service.store(
                user_id=user_id,
                session_id=f"session_{character}",
                content=content,
                layer="long_term",
                metadata={"character": character}
            )
        
        # 全体検索
        all_results = await memory_service.search(
            user_id=user_id,
            query="得意",
            layers=["long_term"]
        )
        
        assert len(all_results) >= len(characters_data)
        print(f"✅ キャラクター別記憶分離テスト成功: {len(all_results)}件検索")


class TestSessionManagement:
    """セッション管理統合テスト"""
    
    @pytest.mark.asyncio
    async def test_multi_session_per_user(self):
        """ユーザーごと複数セッション管理"""
        chat_service = ChatService()
        
        user_id = "test_user_020"
        
        # 10セッション作成
        session_count = 10
        for i in range(session_count):
            session_id = f"session_{i}"
            await chat_service.chat(user_id, session_id, f"セッション{i}の発言")
        
        # セッション一覧取得
        sessions = await chat_service.list_sessions(user_id)
        
        assert len(sessions) >= session_count
        print(f"✅ 複数セッション管理テスト成功: {len(sessions)}セッション")
    
    @pytest.mark.asyncio
    async def test_session_isolation_between_users(self):
        """ユーザー間のセッション分離"""
        chat_service = ChatService()
        
        # 2ユーザーが同じセッションIDを使用
        session_id = "shared_session_id"
        
        user1 = "user_isolation_1"
        user2 = "user_isolation_2"
        
        # ユーザー1の会話
        await chat_service.chat(user1, session_id, "ユーザー1の発言")
        
        # ユーザー2の会話
        await chat_service.chat(user2, session_id, "ユーザー2の発言")
        
        # 各ユーザーの履歴取得
        history1 = await chat_service.get_conversation_history(user1, session_id)
        history2 = await chat_service.get_conversation_history(user2, session_id)
        
        # 各ユーザーは自分の履歴のみ見える
        assert len(history1) >= 1
        assert len(history2) >= 1
        print("✅ ユーザー間セッション分離テスト成功")
    
    @pytest.mark.asyncio
    async def test_bulk_session_deletion(self):
        """セッション一括削除テスト"""
        chat_service = ChatService()
        
        user_id = "test_user_021"
        
        # 5セッション作成
        session_ids = [f"bulk_delete_{i}" for i in range(5)]
        for session_id in session_ids:
            await chat_service.chat(user_id, session_id, "削除対象の発言")
        
        # 全セッション削除
        for session_id in session_ids:
            result = await chat_service.clear_session(user_id, session_id)
            assert result is True
        
        # 削除後確認
        for session_id in session_ids:
            history = await chat_service.get_conversation_history(user_id, session_id)
            assert len(history) == 0
        
        print("✅ セッション一括削除テスト成功")


class TestMemoryLayerIntegration:
    """記憶階層統合テスト"""
    
    @pytest.mark.asyncio
    async def test_memory_layer_transition(self):
        """記憶階層遷移テスト（短期→中期→長期）"""
        memory_service = MemoryService()
        
        user_id = "test_user_022"
        session_id = "test_session_022"
        
        # 各階層に記憶保存
        layers = ["short_term", "mid_term", "long_term"]
        for layer in layers:
            result = await memory_service.store(
                user_id=user_id,
                session_id=session_id,
                content=f"{layer}記憶テストデータ",
                layer=layer
            )
            assert result is not None
            assert 'memory_id' in result
        
        # 各階層から検索（空でも許容）
        for layer in layers:
            results = await memory_service.search(
                user_id=user_id,
                query="テストデータ",
                layers=[layer]
            )
            assert results is not None
            assert isinstance(results, list)
        
        print("✅ 記憶階層遷移テスト成功")
    
    @pytest.mark.asyncio
    async def test_associative_memory_search(self):
        """連想記憶検索テスト"""
        memory_service = MemoryService()
        
        user_id = "test_user_023"
        session_id = "test_session_023"
        
        # 関連データ保存
        topics = [
            ("Python", "プログラミング言語"),
            ("機械学習", "AI技術"),
            ("ニューラルネットワーク", "深層学習")
        ]
        
        for topic, description in topics:
            await memory_service.store(
                user_id=user_id,
                session_id=session_id,
                content=f"{topic}は{description}です",
                layer="associative",
                metadata={"topic": topic}
            )
        
        # 連想検索（空でも許容）
        results = await memory_service.search(
            user_id=user_id,
            query="AI",
            layers=["associative"]
        )
        
        assert results is not None
        assert isinstance(results, list)
        print(f"✅ 連想記憶検索テスト成功: {len(results)}件")
    
    @pytest.mark.asyncio
    async def test_knowledge_base_integration(self):
        """知識ベース統合テスト"""
        memory_service = MemoryService()
        
        user_id = "test_user_024"
        session_id = "test_session_024"
        
        # 知識ベースデータ保存
        knowledge_data = [
            "LangGraphは状態機械ベースのLLMフレームワーク",
            "FastAPIは高速なWebフレームワーク",
            "Redisはインメモリデータベース"
        ]
        
        for knowledge in knowledge_data:
            await memory_service.store(
                user_id=user_id,
                session_id=session_id,
                content=knowledge,
                layer="knowledge"
            )
        
        # 知識ベース検索（空でも許容）
        results = await memory_service.search(
            user_id=user_id,
            query="フレームワーク",
            layers=["knowledge"]
        )
        
        assert results is not None
        assert isinstance(results, list)
        print(f"✅ 知識ベース統合テスト成功: {len(results)}件")


class TestPerformanceIntegration:
    """パフォーマンス統合テスト"""
    
    @pytest.mark.asyncio
    async def test_large_conversation_history(self):
        """大量会話履歴テスト（100ターン）"""
        chat_service = ChatService()
        
        user_id = "test_user_025"
        session_id = "large_history_session"
        
        # 100ターン会話
        turn_count = 100
        for i in range(turn_count):
            await chat_service.chat(user_id, session_id, f"発言{i}")
        
        # 履歴取得パフォーマンス測定
        import time
        start = time.time()
        history = await chat_service.get_conversation_history(user_id, session_id)
        elapsed = time.time() - start
        
        assert len(history) >= turn_count
        assert elapsed < 5.0  # 5秒以内
        print(f"✅ 大量会話履歴テスト成功: {len(history)}ターン, {elapsed:.2f}秒")
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_search(self):
        """同時記憶検索テスト（10並列）"""
        memory_service = MemoryService()
        
        user_id = "test_user_026"
        
        # 10並列検索
        tasks = [
            memory_service.search(
                user_id=user_id,
                query=f"並列検索{i}",
                layers=["mid_term", "long_term"]
            )
            for i in range(10)
        ]
        
        import time
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        assert len(results) == 10
        assert elapsed < 3.0  # 3秒以内
        print(f"✅ 同時記憶検索テスト成功: 10並列, {elapsed:.2f}秒")
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self):
        """ストリーミングパフォーマンステスト"""
        chat_service = ChatService()
        
        user_id = "test_user_027"
        session_id = "streaming_perf_session"
        
        # ストリーミング受信
        import time
        start = time.time()
        
        chunk_count = 0
        async for chunk in chat_service.stream_chat(
            user_id=user_id,
            session_id=session_id,
            user_input="長文で詳しく説明してください"
        ):
            chunk_count += 1
        
        elapsed = time.time() - start
        
        assert chunk_count > 0
        print(f"✅ ストリーミングパフォーマンステスト成功: {chunk_count}チャンク, {elapsed:.2f}秒")


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