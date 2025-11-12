"""
memory/long_term.py
長期記憶の実装

永続的なプロファイル・成長データの保存。
Phase 1では簡易実装、Phase 2以降でVectorDB統合。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
from .base import MemoryBackend, MemoryItem, MemoryConfig


class LongTermMemory(MemoryBackend):
    """長期記憶の実装（JSON/SQLiteバックエンド）"""
    
    def __init__(self, config: MemoryConfig = None, data_dir: str = "data/long_term"):
        """
        初期化
        
        Args:
            config: メモリ設定
            data_dir: データディレクトリ
        """
        super().__init__()
        self.backend_type = "long_term"
        self.config = config or MemoryConfig()
        self.data_dir = Path(data_dir)
        
        # データディレクトリ作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # プロファイルデータ
        self.profiles_path = self.data_dir / "profiles.json"
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self._load_profiles()
        
        # 統計情報
        self.stats = {
            'total_stores': 0,
            'total_retrievals': 0,
            'total_profiles': 0
        }
    
    def _load_profiles(self):
        """プロファイルデータを読み込み"""
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, 'r', encoding='utf-8') as f:
                    self.profiles = json.load(f)
            except Exception as e:
                print(f"Long-term memory load error: {e}")
    
    def _save_profiles(self):
        """プロファイルデータを保存"""
        try:
            with open(self.profiles_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Long-term memory save error: {e}")
    
    def store(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """
        データを保存
        
        Args:
            key: 保存キー
            value: 保存する値
            metadata: メタデータ
            
        Returns:
            成功した場合True
        """
        try:
            item = MemoryItem(key, value, metadata)
            self.profiles[key] = item.to_dict()
            self.stats['total_stores'] += 1
            self._save_profiles()
            return True
        except Exception as e:
            print(f"Long-term memory store error: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        データを取得
        
        Args:
            key: 取得キー
            
        Returns:
            保存されたデータ、存在しない場合None
        """
        self.stats['total_retrievals'] += 1
        
        if key in self.profiles:
            item_data = self.profiles[key]
            item = MemoryItem.from_dict(item_data)
            item.update_access()
            self.profiles[key] = item.to_dict()
            return item.value
        
        return None
    
    def delete(self, key: str) -> bool:
        """
        データを削除
        
        Args:
            key: 削除キー
            
        Returns:
            成功した場合True
        """
        if key in self.profiles:
            del self.profiles[key]
            self._save_profiles()
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """
        キーが存在するか確認
        
        Args:
            key: 確認キー
            
        Returns:
            存在する場合True
        """
        return key in self.profiles
    
    def clear(self) -> bool:
        """
        全データを削除
        
        Returns:
            成功した場合True
        """
        self.profiles.clear()
        self._save_profiles()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'backend_type': self.backend_type,
            'total_profiles': len(self.profiles),
            **self.stats
        }
    
    def store_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        ユーザープロファイルを保存
        
        Args:
            user_id: ユーザーID
            profile: プロファイル情報
            
        Returns:
            成功した場合True
        """
        key = f"user:{user_id}"
        metadata = {
            'type': 'user_profile',
            'user_id': user_id
        }
        return self.store(key, profile, metadata)
    
    def retrieve_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ユーザープロファイルを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            プロファイル情報、存在しない場合None
        """
        key = f"user:{user_id}"
        return self.retrieve(key)
    
    def update_character_kpi(self, character: str, kpi_data: Dict[str, Any]) -> bool:
        """
        キャラクターKPIを更新
        
        Args:
            character: キャラクター名
            kpi_data: KPIデータ
            
        Returns:
            成功した場合True
        """
        key = f"character:{character}:kpi"
        existing = self.retrieve(key) or {}
        existing.update(kpi_data)
        
        metadata = {
            'type': 'character_kpi',
            'character': character,
            'updated_at': datetime.now().isoformat()
        }
        return self.store(key, existing, metadata)
    
    def get_character_kpi(self, character: str) -> Optional[Dict[str, Any]]:
        """
        キャラクターKPIを取得
        
        Args:
            character: キャラクター名
            
        Returns:
            KPIデータ、存在しない場合None
        """
        key = f"character:{character}:kpi"
        return self.retrieve(key)


class CharacterKPIManager:
    """キャラクターKPI管理クラス"""
    
    def __init__(self, long_term_memory: LongTermMemory):
        """
        初期化
        
        Args:
            long_term_memory: 長期記憶インスタンス
        """
        self.memory = long_term_memory
    
    def initialize_character(self, character: str) -> bool:
        """
        キャラクターKPIを初期化
        
        Args:
            character: キャラクター名
            
        Returns:
            成功した場合True
        """
        initial_kpi = {
            'user_thumbs_up': 0,
            'answer_hits': 0,
            'search_success': 0,
            'total_responses': 0,
            'level': 0,
            'created_at': datetime.now().isoformat()
        }
        return self.memory.update_character_kpi(character, initial_kpi)
    
    def increment_kpi(self, character: str, kpi_type: str, value: int = 1) -> bool:
        """
        KPI値をインクリメント
        
        Args:
            character: キャラクター名
            kpi_type: KPI種別
            value: 増加量
            
        Returns:
            成功した場合True
        """
        kpi = self.memory.get_character_kpi(character)
        if kpi is None:
            self.initialize_character(character)
            kpi = self.memory.get_character_kpi(character)
        
        if kpi_type in kpi:
            kpi[kpi_type] += value
            
            # レベル計算（level = floor(sqrt(total_kpi / 10))）
            total_kpi = (
                kpi.get('user_thumbs_up', 0) + 
                kpi.get('answer_hits', 0) + 
                kpi.get('search_success', 0)
            )
            kpi['level'] = int((total_kpi / 10) ** 0.5)
            
            return self.memory.update_character_kpi(character, kpi)
        
        return False
    
    def get_character_level(self, character: str) -> int:
        """
        キャラクターレベルを取得
        
        Args:
            character: キャラクター名
            
        Returns:
            レベル
        """
        kpi = self.memory.get_character_kpi(character)
        if kpi:
            return kpi.get('level', 0)
        return 0
    
    def get_all_kpis(self) -> Dict[str, Dict[str, Any]]:
        """
        全キャラクターのKPIを取得
        
        Returns:
            キャラクター別KPI辞書
        """
        characters = ['ルミナ', 'クラリス', 'ノクス']
        kpis = {}
        for char in characters:
            kpi = self.memory.get_character_kpi(char)
            if kpi:
                kpis[char] = kpi
        return kpis