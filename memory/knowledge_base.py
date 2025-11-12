"""
memory/knowledge_base.py
知識ベースの実装

RAG検索用の知識ベース管理。
Phase 1では簡易実装、Phase 2以降でVectorDB統合。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
from .base import MemoryBackend, MemoryConfig


class KnowledgeBase(MemoryBackend):
    """知識ベースの実装（Phase 1: 簡易版）"""
    
    def __init__(self, config: MemoryConfig = None, data_dir: str = "data/kb"):
        """
        初期化
        
        Args:
            config: メモリ設定
            data_dir: データディレクトリ
        """
        super().__init__()
        self.backend_type = "knowledge_base"
        self.config = config or MemoryConfig()
        self.data_dir = Path(data_dir)
        
        # データディレクトリ作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 名前空間別データストレージ
        self.namespaces: Dict[str, Dict[str, Any]] = {}
        self._load_namespaces()
        
        # 統計情報
        self.stats = {
            'total_stores': 0,
            'total_retrievals': 0,
            'total_searches': 0
        }
    
    def _load_namespaces(self):
        """名前空間データを読み込み"""
        for ns in self.config.kb_namespaces:
            ns_file = self.data_dir / f"{ns}.json"
            if ns_file.exists():
                try:
                    with open(ns_file, 'r', encoding='utf-8') as f:
                        self.namespaces[ns] = json.load(f)
                except Exception as e:
                    print(f"Knowledge base load error ({ns}): {e}")
                    self.namespaces[ns] = {}
            else:
                self.namespaces[ns] = {}
    
    def _save_namespace(self, namespace: str):
        """名前空間データを保存"""
        try:
            ns_file = self.data_dir / f"{namespace}.json"
            with open(ns_file, 'w', encoding='utf-8') as f:
                json.dump(self.namespaces.get(namespace, {}), f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Knowledge base save error ({namespace}): {e}")
    
    def store(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """
        データを保存
        
        Args:
            key: 保存キー（namespace:id形式）
            value: 保存する値
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            # 名前空間とIDを分離
            if ':' in key:
                namespace, item_id = key.split(':', 1)
            else:
                namespace = 'default'
                item_id = key
            
            # 名前空間が存在しない場合は作成
            if namespace not in self.namespaces:
                self.namespaces[namespace] = {}
            
            # データ保存
            self.namespaces[namespace][item_id] = {
                'value': value,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.stats['total_stores'] += 1
            self._save_namespace(namespace)
            
            return True
            
        except Exception as e:
            print(f"Knowledge base store error: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        データを取得
        
        Args:
            key: 取得キー（namespace:id形式）
            
        Returns:
            保存されたデータ、存在しない場合None
        """
        self.stats['total_retrievals'] += 1
        
        try:
            # 名前空間とIDを分離
            if ':' in key:
                namespace, item_id = key.split(':', 1)
            else:
                namespace = 'default'
                item_id = key
            
            if namespace in self.namespaces:
                if item_id in self.namespaces[namespace]:
                    return self.namespaces[namespace][item_id]['value']
            
            return None
            
        except Exception as e:
            print(f"Knowledge base retrieve error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        データを削除
        
        Args:
            key: 削除キー
            
        Returns:
            成功した場合True
        """
        try:
            if ':' in key:
                namespace, item_id = key.split(':', 1)
            else:
                namespace = 'default'
                item_id = key
            
            if namespace in self.namespaces:
                if item_id in self.namespaces[namespace]:
                    del self.namespaces[namespace][item_id]
                    self._save_namespace(namespace)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Knowledge base delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        キーが存在するか確認
        
        Args:
            key: 確認キー
            
        Returns:
            存在する場合True
        """
        try:
            if ':' in key:
                namespace, item_id = key.split(':', 1)
            else:
                namespace = 'default'
                item_id = key
            
            if namespace in self.namespaces:
                return item_id in self.namespaces[namespace]
            
            return False
            
        except Exception:
            return False
    
    def clear(self) -> bool:
        """
        全データを削除
        
        Returns:
            成功した場合True
        """
        for namespace in self.namespaces.keys():
            self.namespaces[namespace] = {}
            self._save_namespace(namespace)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        total_items = sum(len(items) for items in self.namespaces.values())
        
        return {
            'backend_type': self.backend_type,
            'total_items': total_items,
            'namespaces': list(self.namespaces.keys()),
            'items_per_namespace': {
                ns: len(items) for ns, items in self.namespaces.items()
            },
            **self.stats
        }
    
    def search(self, query: str, namespace: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        簡易検索（Phase 1: 単純な文字列マッチング）
        
        Args:
            query: 検索クエリ
            namespace: 検索対象の名前空間（Noneの場合は全体）
            limit: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        self.stats['total_searches'] += 1
        results = []
        
        # 検索対象の名前空間を決定
        target_namespaces = [namespace] if namespace else list(self.namespaces.keys())
        
        for ns in target_namespaces:
            if ns not in self.namespaces:
                continue
            
            for item_id, item_data in self.namespaces[ns].items():
                value = str(item_data['value'])
                
                # 簡易マッチング
                if query.lower() in value.lower():
                    results.append({
                        'namespace': ns,
                        'id': item_id,
                        'value': item_data['value'],
                        'metadata': item_data.get('metadata', {}),
                        'score': 1.0  # Phase 1では固定スコア
                    })
                
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
        
        return results[:limit]
    
    def add_document(self, namespace: str, doc_id: str, content: str, 
                    metadata: Dict = None) -> bool:
        """
        ドキュメントを追加
        
        Args:
            namespace: 名前空間
            doc_id: ドキュメントID
            content: コンテンツ
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        key = f"{namespace}:{doc_id}"
        return self.store(key, content, metadata)
    
    def get_namespace_list(self) -> List[str]:
        """
        名前空間一覧を取得
        
        Returns:
            名前空間のリスト
        """
        return list(self.namespaces.keys())
    
    def get_namespace_size(self, namespace: str) -> int:
        """
        名前空間のアイテム数を取得
        
        Args:
            namespace: 名前空間
            
        Returns:
            アイテム数
        """
        if namespace in self.namespaces:
            return len(self.namespaces[namespace])
        return 0


class KnowledgeBaseManager:
    """知識ベース管理クラス"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        初期化
        
        Args:
            knowledge_base: 知識ベースインスタンス
        """
        self.kb = knowledge_base
    
    def search_all(self, query: str, limit: int = 5) -> Dict[str, List[Dict]]:
        """
        全名前空間を検索
        
        Args:
            query: 検索クエリ
            limit: 名前空間ごとの最大結果数
            
        Returns:
            名前空間別の検索結果
        """
        results = {}
        for namespace in self.kb.get_namespace_list():
            ns_results = self.kb.search(query, namespace, limit)
            if ns_results:
                results[namespace] = ns_results
        return results
    
    def bulk_add(self, namespace: str, documents: List[Dict[str, Any]]) -> int:
        """
        複数ドキュメントを一括追加
        
        Args:
            namespace: 名前空間
            documents: ドキュメントリスト（各要素は{'id', 'content', 'metadata'}）
            
        Returns:
            追加成功数
        """
        success_count = 0
        for doc in documents:
            doc_id = doc.get('id')
            content = doc.get('content')
            metadata = doc.get('metadata', {})
            
            if doc_id and content:
                if self.kb.add_document(namespace, doc_id, content, metadata):
                    success_count += 1
        
        return success_count
    
    def get_summary(self) -> Dict[str, Any]:
        """
        知識ベースのサマリーを取得
        
        Returns:
            サマリー情報
        """
        stats = self.kb.get_stats()
        return {
            'total_namespaces': len(stats['namespaces']),
            'total_items': stats['total_items'],
            'namespaces': stats['items_per_namespace'],
            'statistics': {
                'total_stores': stats['total_stores'],
                'total_retrievals': stats['total_retrievals'],
                'total_searches': stats['total_searches']
            }
        }