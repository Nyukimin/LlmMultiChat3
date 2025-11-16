"""
main.py
LangGraphメインアプリケーション

マルチLLM会話システムのメインフロー制御。
LangGraphを使用して各キャラクターノードを接続し、会話フローを管理。
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Annotated
from datetime import datetime
import operator

from config import Config
from conversation_state import ConversationState
from llm_nodes import LuminaNode, ClarisNode, NoxNode, RouterNode
from memory_manager import MemorySystemManager
from exceptions import LLMNodeError
from metrics import get_metrics_collector


class GraphState(TypedDict):
    """LangGraphの状態型定義"""
    user_input: str
    history: Annotated[list, operator.add]
    current_turn: int
    max_turns: int
    last_speaker: str
    next_character: str
    session_id: str
    start_time: str


class MultiLLMChat:
    """マルチLLM会話システムのメインクラス"""
    
    def __init__(self):
        """初期化"""
        self.config = Config()
        self.conv_state = ConversationState()
        
        # 記憶システムの初期化
        self.memory = MemorySystemManager()
        self.memory.initialize_characters()
        
        # メトリクス収集の初期化
        self.metrics = get_metrics_collector()
        self.metrics.record_session_start()
        
        # キャラクターノードの初期化
        self.lumina_node = LuminaNode(self.config)
        self.claris_node = ClarisNode(self.config)
        self.nox_node = NoxNode(self.config)
        self.router_node = RouterNode(self.config)
        
        # LangGraphの構築
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """LangGraphのフロー構築"""
        
        # グラフの定義
        workflow = StateGraph(GraphState)
        
        # ノードの追加
        workflow.add_node("router", self._router_node)
        workflow.add_node("lumina", self._lumina_node)
        workflow.add_node("claris", self._claris_node)
        workflow.add_node("nox", self._nox_node)
        workflow.add_node("check_continue", self._check_continue)
        
        # エントリーポイント
        workflow.set_entry_point("router")
        
        # ルーターから各キャラへの条件付きエッジ
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "lumina": "lumina",
                "claris": "claris",
                "nox": "nox"
            }
        )
        
        # 各キャラから継続チェックへ
        workflow.add_edge("lumina", "check_continue")
        workflow.add_edge("claris", "check_continue")
        workflow.add_edge("nox", "check_continue")
        
        # 継続チェックからの分岐
        workflow.add_conditional_edges(
            "check_continue",
            self._should_continue,
            {
                "continue": END,
                "end": END
            }
        )
        
        return workflow
    
    def _router_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ルーターノード処理"""
        return self.router_node.decide_next(state)
    
    def _lumina_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ルミナノード処理（エラーハンドリング付き）"""
        try:
            return self.lumina_node.generate(state)
        except LLMNodeError as e:
            self.memory.logger.log_error(e, context="lumina_node")
            # エラー時もフローを継続（フォールバック応答）
            return {
                **state,
                "history": state.get("history", []) + [{
                    "speaker": "system",
                    "msg": "申し訳ございません。ルミナの応答生成中にエラーが発生しました。",
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _claris_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """クラリスノード処理（エラーハンドリング付き）"""
        try:
            return self.claris_node.generate(state)
        except LLMNodeError as e:
            self.memory.logger.log_error(e, context="claris_node")
            return {
                **state,
                "history": state.get("history", []) + [{
                    "speaker": "system",
                    "msg": "申し訳ございません。クラリスの応答生成中にエラーが発生しました。",
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _nox_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ノクスノード処理（エラーハンドリング付き）"""
        try:
            return self.nox_node.generate(state)
        except LLMNodeError as e:
            self.memory.logger.log_error(e, context="nox_node")
            return {
                **state,
                "history": state.get("history", []) + [{
                    "speaker": "system",
                    "msg": "申し訳ございません。ノクスの応答生成中にエラーが発生しました。",
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _route_decision(self, state: Dict[str, Any]) -> str:
        """ルーティング決定"""
        return state.get('next_character', 'lumina')
    
    def _check_continue(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """継続チェック"""
        state['current_turn'] = state.get('current_turn', 0) + 1
        return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """会話を継続すべきか判定"""
        current_turn = state.get('current_turn', 0)
        max_turns = state.get('max_turns', self.config.system.max_turns)
        
        if current_turn >= max_turns:
            return "end"
        return "continue"
    
    def chat(self, user_input: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        ユーザー入力を処理して応答を生成
        
        Args:
            user_input: ユーザーの入力テキスト
            session_id: セッションID（省略時: 内部セッションIDを使用）
            user_id: ユーザーID（Phase 3統合用、省略可能）
            
        Returns:
            応答を含む状態辞書
        """
        # 入力検証
        from validators import InputValidator
        try:
            user_input = InputValidator.validate_user_input(user_input)
        except Exception as e:
            self.memory.logger.log_error(e, context="chat_input_validation")
            return {
                "response": f"入力検証エラー: {str(e)}",
                "speaker": "system",
                "turn": self.conv_state.current_turn,
                "session_id": self.conv_state.session_id
            }
        
        # セッションIDの処理（外部指定 or 内部管理）
        if session_id:
            # Phase 3統合: 外部指定のセッションIDを使用
            if self.conv_state.session_id != session_id:
                # 新規セッションまたはセッション切替
                self.conv_state.session_id = session_id
                if not self.conv_state.history:
                    self.conv_state.start_new_session()
        else:
            # Phase 1互換: 内部セッションIDを使用
            if not self.conv_state.history:
                self.conv_state.start_new_session()
        
        # ユーザー入力を履歴に追加
        self.conv_state.add_turn("User", user_input)
        
        # グラフ状態の構築
        initial_state: GraphState = {
            "user_input": user_input,
            "history": self.conv_state.history.copy(),
            "current_turn": self.conv_state.current_turn,
            "max_turns": getattr(self.config, 'max_turns', 12),
            "last_speaker": self.conv_state.last_speaker or "",
            "next_character": "",
            "session_id": self.conv_state.session_id,
            "start_time": self.conv_state.start_time.isoformat()
        }
        
        # グラフ実行
        result = self.compiled_graph.invoke(initial_state)
        
        # 会話状態の更新
        self.conv_state.history = result['history']
        self.conv_state.current_turn = result['current_turn']
        self.conv_state.last_speaker = result['last_speaker']
        
        # 記憶システムに会話ターンを保存
        last_response = result['history'][-1] if result['history'] else None
        if last_response:
            self.memory.add_conversation_turn(
                session_id=result['session_id'],
                speaker=last_response['speaker'],
                content=last_response['msg'],
                metadata={
                    'turn': result['current_turn'],
                    'user_input': user_input
                }
            )
        
        return {
            "response": last_response['msg'] if last_response else "",
            "speaker": last_response['speaker'] if last_response else "",
            "turn": result['current_turn'],
            "session_id": result['session_id']
        }
    
    def reset_conversation(self):
        """会話状態をリセット"""
        # 現在のセッションを保存
        if self.conv_state.session_id:
            self.memory.save_session(self.conv_state.session_id)
        
        # メトリクスレポート出力
        print("\n" + self.metrics.get_performance_report())
        
        # メトリクスエクスポート
        self.metrics.record_session_end()
        filepath = self.metrics.export_to_json()
        print(f"\nメトリクスをエクスポート: {filepath}")
        
        # HTMLダッシュボード生成
        from dashboard import generate_html_report
        html_path = generate_html_report(self.metrics.get_summary())
        print(f"HTMLレポート生成: {html_path}")
        
        # 新しいセッション開始
        self.conv_state = ConversationState()
        self.metrics.reset()
        self.metrics.record_session_start()
        print("会話をリセットしました。")
    
    def get_history(self) -> list:
        """会話履歴を取得"""
        return self.conv_state.history
    
    def export_conversation(self, filename: str = None):
        """会話履歴をエクスポート"""
        return self.conv_state.export_to_json(filename)


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🌐 会話LLM - マルチLLM会話システム v3.0")
    print("=" * 60)
    print()
    print("キャラクター:")
    print("  - ルミナ（司会・雑談）")
    print("  - クラリス（解説・理論）")
    print("  - ノクス（検証・要約・検索）")
    print()
    print("コマンド:")
    print("  /reset   - 会話をリセット")
    print("  /export  - 会話履歴をエクスポート")
    print("  /history - 会話履歴を表示")
    print("  /memory  - 記憶システムサマリー")
    print("  /quit    - 終了")
    print()
    print("=" * 60)
    print()
    
    # システム初期化
    chat_system = MultiLLMChat()
    
    # 会話ループ
    while True:
        try:
            # ユーザー入力
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # コマンド処理
            if user_input.startswith('/'):
                command = user_input[1:].lower()
                
                if command == 'quit':
                    print("\n会話を終了します。")
                    break
                elif command == 'reset':
                    chat_system.reset_conversation()
                    continue
                elif command == 'export':
                    filename = chat_system.export_conversation()
                    print(f"会話履歴を {filename} にエクスポートしました。")
                    continue
                elif command == 'history':
                    history = chat_system.get_history()
                    print("\n=== 会話履歴 ===")
                    for turn in history:
                        print(f"{turn['speaker']}: {turn['msg']}")
                    print("=" * 60)
                    continue
                elif command == 'memory':
                    stats = chat_system.memory.get_statistics()
                    print("\n=== 記憶システムサマリー ===")
                    print(f"セッション数: {stats['sessions']['total']}")
                    print(f"会話ターン数: {stats['conversations']['total']}")
                    print(f"知識ベース項目数: {stats['knowledge']['total']}")
                    print("\nキャラクター成長:")
                    for char in ['lumina', 'claris', 'nox']:
                        kpi = stats['characters'].get(char, {})
                        print(f"  {char.capitalize()}: Lv{kpi.get('level', 0)} (KPI: {kpi.get('total_kpi', 0)})")
                    print("=" * 60)
                    continue
                else:
                    print(f"不明なコマンド: /{command}")
                    continue
            
            # 通常の会話処理
            response = chat_system.chat(user_input)
            print(f"\n{response['speaker']}: {response['response']}\n")
            
        except KeyboardInterrupt:
            print("\n\n会話を中断しました。")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            continue
    
    # 終了時の処理
    print("\n記憶システムを保存中...")
    chat_system.memory.save_all_sessions()
    print("保存完了。またお会いしましょう！")


if __name__ == "__main__":
    main()
