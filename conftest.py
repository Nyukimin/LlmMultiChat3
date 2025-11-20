"""pytest設定ファイル.

プロジェクトルートをsys.pathに追加し、tests/ディレクトリから
プロジェクトモジュール（api, services, security等）を
インポート可能にする。
"""

import sys
from pathlib import Path

# プロジェクトルートディレクトリを取得
project_root = Path(__file__).parent.absolute()

# sys.pathの先頭に追加（優先度を最高に）
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"[conftest.py] Added to sys.path: {project_root}")
