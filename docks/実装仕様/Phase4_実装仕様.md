# Phase 4 実装仕様書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 4 - フロントエンド実装 + 記憶システム拡張  
**期間**: 8週間（2部構成）  
**作成日**: 2025-11-20  
**Phase 1-3統合完了**: 実施中

---

## 目次

1. [Phase 4概要](#1-phase-4概要)
2. [前提条件](#2-前提条件)
3. [Part A: フロントエンド実装（Week 1-4）](#3-part-a-フロントエンド実装week-1-4)
4. [Part B: バックエンド高度機能（Week 5-8）](#4-part-b-バックエンド高度機能week-5-8)
5. [技術スタック](#5-技術スタック)
6. [アーキテクチャ設計](#6-アーキテクチャ設計)
7. [テスト計画](#7-テスト計画)
8. [デプロイ戦略](#8-デプロイ戦略)

---

## 1. Phase 4概要

### 1.1 目的

Phase 4は**2つのパート**に分かれています：

**Part A（Week 1-4）**: Phase 1-3統合後のフロントエンド実装
- React SPA + WebSocket UIの構築
- JWT認証フロー・リアルタイム会話UI・記憶ダッシュボード

**Part B（Week 5-8）**: バックエンド高度機能の追加
- 連想記憶システム（SQLite Graph）
- 8基本感情モデル（Plutchik）

### 1.2 全体目標

| カテゴリ | 目標 | Priority |
|---------|------|----------|
| **フロントエンド** | React SPA完全実装 | 🔴 High |
| **認証UI** | JWT認証フロー | 🔴 High |
| **会話UI** | リアルタイムチャット | 🔴 High |
| **記憶拡張** | 連想記憶システム | 🟡 Medium |
| **感情基盤** | 8基本感情モデル | 🟡 Medium |

### 1.3 成果物

**フロントエンド（Part A）**:
- React SPA（約3,000行 TypeScript）
- 15画面・30コンポーネント
- E2Eテスト（Cypress）

**バックエンド（Part B）**:
- 連想記憶システム（400行 Python）
- 感情モデル（300行 Python）
- 35統合テスト

---

## 2. 前提条件

### 2.1 Phase 1-3統合完了

✅ Phase 1: LangGraphコア・5階層記憶システム  
✅ Phase 2: エラーハンドリング・セキュリティ  
✅ Phase 3: REST/WebSocket API（23エンドポイント）  
✅ **Phase 1-3統合**: [`services/chat_service.py`](../../services/chat_service.py:1), [`services/memory_service.py`](../../services/memory_service.py:1)

### 2.2 利用可能なAPI

**認証API（6エンドポイント）**:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/profile`
- `POST /api/v1/auth/change-password`
- `DELETE /api/v1/auth/delete`

**会話API（6エンドポイント）**:
- `POST /api/v1/chat/`
- `POST /api/v1/chat/stream`
- `GET /api/v1/chat/history`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`
- `DELETE /api/v1/chat/sessions/{session_id}/clear`

**記憶API（7エンドポイント）**:
- `POST /api/v1/memory/search`
- `POST /api/v1/memory/store`
- `DELETE /api/v1/memory/delete/{memory_id}`
- `GET /api/v1/memory/stats`
- `GET /api/v1/memory/sessions/{session_id}`
- `POST /api/v1/memory/flush` (admin)
- `GET /api/v1/memory/health`

**WebSocket API**:
- `WS /ws/chat`

---

## 3. Part A: フロントエンド実装（Week 1-4）

### 3.1 Week 1: React基盤・認証UI

#### 3.1.1 ディレクトリ構成

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── common/          # Button, Input, Card, Loading
│   │   ├── layout/          # Header, Sidebar, Footer
│   │   └── auth/            # LoginForm, RegisterForm, ProfileCard
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── ChatPage.tsx
│   │   └── DashboardPage.tsx
│   ├── services/
│   │   ├── api.ts           # Axios client
│   │   ├── auth.service.ts  # 認証サービス
│   │   ├── chat.service.ts  # 会話サービス
│   │   └── websocket.service.ts # WebSocketサービス
│   ├── store/
│   │   ├── authSlice.ts     # Redux認証スライス
│   │   ├── chatSlice.ts     # Redux会話スライス
│   │   └── store.ts         # Redux Store
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   └── useChat.ts
│   ├── types/
│   │   ├── auth.types.ts
│   │   ├── chat.types.ts
│   │   └── memory.types.ts
│   ├── utils/
│   │   ├── localStorage.ts
│   │   └── formatters.ts
│   ├── App.tsx
│   └── index.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

#### 3.1.2 技術スタック（package.json）

```json
{
  "name": "llmmultichat3-frontend",
  "version": "4.0.0",
  "type": "module",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@reduxjs/toolkit": "^2.0.0",
    "react-redux": "^9.0.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.10.0",
    "socket.io-client": "^4.6.0",
    "recharts": "^2.10.0",
    "react-markdown": "^9.0.0",
    "lucide-react": "^0.292.0",
    "tailwindcss": "^3.3.0",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "cypress": "^13.6.0",
    "@testing-library/react": "^14.1.0"
  }
}
```

#### 3.1.3 主要実装ファイル

**1. API Client（150行）**

```typescript
// src/services/api.ts
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });

    // リクエストインターセプター（JWT自動付与）
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
      }
    );

    // レスポンスインターセプター（トークン自動更新）
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            const { data } = await this.client.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
            localStorage.setItem('access_token', data.access_token);
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
            return this.client(originalRequest);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get client() { return this.client; }
}

export const apiClient = new ApiClient().client;
```

**2. 認証サービス（300行）**

```typescript
// src/services/auth.service.ts
import { apiClient } from './api';
import { LoginCredentials, RegisterData, User } from '../types/auth.types';

export class AuthService {
  async register(data: RegisterData): Promise<{ user_id: string }> {
    const response = await apiClient.post('/api/v1/auth/register', data);
    return response.data;
  }

  async login(credentials: LoginCredentials): Promise<{
    access_token: string;
    refresh_token: string;
  }> {
    const response = await apiClient.post('/api/v1/auth/login', credentials);
    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return response.data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async getProfile(): Promise<User> {
    const response = await apiClient.get('/api/v1/auth/profile');
    return response.data;
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }
}

export const authService = new AuthService();
```

**3. Redux Auth Slice（250行）**

```typescript
// src/store/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../services/auth.service';
import { User, LoginCredentials } from '../types/auth.types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      await authService.login(credentials);
      return await authService.getProfile();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    isAuthenticated: authService.isAuthenticated(),
    isLoading: false,
    error: null,
  } as AuthState,
  reducers: {
    logout: (state) => {
      authService.logout();
      state.user = null;
      state.isAuthenticated = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.user = action.payload;
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

### 3.2 Week 2: リアルタイム会話UI

#### 3.2.1 WebSocketサービス（400行）

```typescript
// src/services/websocket.service.ts
import { io, Socket } from 'socket.io-client';

export class WebSocketService {
  private socket: Socket | null = null;
  private messageHandlers: ((message: any) => void)[] = [];

  connect(token: string): void {
    this.socket = io('ws://localhost:8000', {
      path: '/ws/chat',
      auth: { token },
      transports: ['websocket'],
    });

    this.socket.on('message', (data) => {
      this.messageHandlers.forEach((handler) => handler(data));
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  sendMessage(message: string, sessionId: string): void {
    if (this.socket) {
      this.socket.emit('chat', {
        type: 'chat',
        user_input: message,
        session_id: sessionId,
      });
    }
  }

  onMessage(handler: (message: any) => void): void {
    this.messageHandlers.push(handler);
  }
}

export const websocketService = new WebSocketService();
```

#### 3.2.2 チャットウィンドウ（500行）

```typescript
// src/components/chat/ChatWindow.tsx
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { websocketService } from '../../services/websocket.service';
import { addMessage } from '../../store/chatSlice';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

export const ChatWindow: React.FC = () => {
  const dispatch = useDispatch();
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const handleMessage = (data: any) => {
      if (data.type === 'chunk') {
        setIsTyping(true);
        dispatch(addMessage({
          id: Date.now().toString(),
          content: data.content,
          role: 'assistant',
          timestamp: new Date().toISOString(),
        }));
        setTimeout(() => setIsTyping(false), 1000);
      }
    };

    websocketService.onMessage(handleMessage);
    return () => { /* cleanup */ };
  }, [dispatch]);

  const handleSendMessage = (content: string) => {
    dispatch(addMessage({
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date().toISOString(),
    }));
    websocketService.sendMessage(content, 'session-001');
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={[]} />
        {isTyping && <div>入力中...</div>}
      </div>
      <MessageInput onSend={handleSendMessage} />
    </div>
  );
};
```

### 3.3 Week 3: 記憶管理ダッシュボード

#### 3.3.1 記憶統計ダッシュボード（400行）

```typescript
// src/components/dashboard/MemoryDashboard.tsx
import React, { useEffect, useState } from 'react';
import { apiClient } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export const MemoryDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchStats = async () => {
      const response = await apiClient.get('/api/v1/memory/stats');
      setStats(response.data);
    };
    fetchStats();
  }, []);

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">記憶統計</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <h3>総記憶数</h3>
          <p className="text-3xl">{stats.total_memories}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <h3>階層別記憶</h3>
          <BarChart width={300} height={200} data={Object.entries(stats.by_layer).map(([k, v]) => ({ name: k, value: v }))}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#0ea5e9" />
          </BarChart>
        </div>
      </div>
    </div>
  );
};
```

### 3.4 Week 4: 統合テスト・デプロイ

#### 3.4.1 E2Eテスト（Cypress）

```typescript
// cypress/e2e/auth.cy.ts
describe('認証フロー', () => {
  it('ログイン成功', () => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('test@example.com');
    cy.get('input[type="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/chat');
  });

  it('ログアウト', () => {
    cy.visit('/chat');
    cy.get('[data-testid="logout-button"]').click();
    cy.url().should('include', '/login');
  });
});
```

```typescript
// cypress/e2e/chat.cy.ts
describe('会話フロー', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
  });

  it('メッセージ送信', () => {
    cy.visit('/chat');
    cy.get('[data-testid="message-input"]').type('こんにちは');
    cy.get('[data-testid="send-button"]').click();
    cy.contains('こんにちは').should('be.visible');
  });
});
```

#### 3.4.2 Dockerデプロイ

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/llm
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
```

---

## 4. Part B: バックエンド高度機能（Week 5-8）

### 4.1 Week 5-6: 連想記憶システム

#### 4.1.1 実装内容

**参照**: `docks/仕様書/05_会話LLM_連想記憶仕様.md`

**主要機能**:
1. **SQLite Graph実装**
   - ノード管理（概念・トピック・感情）
   - エッジ管理（関連性・強度）
   - 再帰CTE連想検索

2. **学習メカニズム**
   - ヘッブの法則（共起強化）
   - 時間的近接性学習
   - 感情的関連学習

3. **忘却曲線**
   - 未使用記憶の減衰
   - 弱い関連性の自動削除

#### 4.1.2 ファイル構成

```python
# memory/associative.py (400行)
class AssociativeMemory:
    """連想記憶システム."""
    
    def __init__(self, db_path: str = "memory/associative.db"):
        self.db = SQLiteGraph(db_path)
    
    def add_concept(
        self,
        concept: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """概念追加."""
        return self.db.create_node(
            label="concept",
            properties={
                "name": concept,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": time.time(),
                "activation_count": 0
            }
        )
    
    def link_concepts(
        self,
        concept_a: str,
        concept_b: str,
        relationship_type: str,
        strength: float = 1.0
    ) -> str:
        """概念関連付け."""
        return self.db.create_relationship(
            from_node=concept_a,
            to_node=concept_b,
            rel_type=relationship_type,
            properties={"strength": strength, "co_occurrence": 1}
        )
    
    def retrieve_associated_concepts(
        self,
        trigger: str,
        depth: int = 3,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """連想検索."""
        return self.db.find_associated_concepts(
            start_concept=trigger,
            depth=depth,
            threshold=threshold
        )
    
    def strengthen_association(
        self,
        concept_a: str,
        concept_b: str,
        delta: float = 0.1
    ) -> None:
        """ヘッブの法則: 共起強化."""
        edge = self.db.get_edge(concept_a, concept_b)
        new_strength = min(edge['strength'] + delta, 10.0)
        self.db.update_edge(edge['id'], {"strength": new_strength})
    
    def decay_inactive_associations(
        self,
        days_threshold: int = 30,
        decay_rate: float = 0.1
    ) -> int:
        """忘却曲線処理."""
        cutoff = time.time() - (days_threshold * 86400)
        inactive_edges = self.db.query("""
            SELECT id, strength FROM edges
            WHERE last_activated < ? AND strength > 0.1
        """, (cutoff,))
        
        for edge in inactive_edges:
            new_strength = max(edge['strength'] - decay_rate, 0.0)
            if new_strength < 0.1:
                self.db.delete_edge(edge['id'])
            else:
                self.db.update_edge(edge['id'], {"strength": new_strength})
        
        return len(inactive_edges)


class SQLiteGraph:
    """SQLite-based graph database."""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        """スキーマ初期化."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                type TEXT,
                metadata JSON,
                created_at INTEGER,
                activation_count INTEGER DEFAULT 0,
                emotional_valence REAL DEFAULT 0.0
            );
            
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                from_id INTEGER,
                to_id INTEGER,
                rel_type TEXT,
                strength REAL DEFAULT 1.0,
                co_occurrence INTEGER DEFAULT 1,
                last_activated INTEGER,
                FOREIGN KEY(from_id) REFERENCES nodes(id),
                FOREIGN KEY(to_id) REFERENCES nodes(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
            CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
        """)
    
    def find_associated_concepts(
        self,
        start_concept: str,
        depth: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """再帰CTE連想検索."""
        query = """
            WITH RECURSIVE associated AS (
                -- ベースケース
                SELECT n.id, n.name, n.type, 0 AS depth, 1.0 AS strength
                FROM nodes n
                WHERE n.name = ?
                
                UNION
                
                -- 再帰ケース
                SELECT n.id, n.name, n.type, a.depth + 1, e.strength
                FROM associated a
                JOIN edges e ON a.id = e.from_id
                JOIN nodes n ON e.to_id = n.id
                WHERE a.depth < ? AND e.strength >= ?
            )
            SELECT DISTINCT name, type, depth, strength
            FROM associated
            ORDER BY depth, strength DESC
        """
        
        cursor = self.conn.execute(query, (start_concept, depth, threshold))
        return [dict(zip(['name', 'type', 'depth', 'strength'], row)) for row in cursor.fetchall()]
```

#### 4.1.3 API追加

```python
# api/routes/memory.py に追加

from memory.associative import AssociativeMemory

associative_memory = AssociativeMemory()

@router.post("/api/v1/memory/associate")
async def create_association(
    concept_a: str,
    concept_b: str,
    strength: float = 1.0,
    current_user: User = Depends(get_current_user)
):
    """2つの概念を関連付け."""
    edge_id = associative_memory.link_concepts(
        concept_a=concept_a,
        concept_b=concept_b,
        relationship_type="semantic",
        strength=strength
    )
    return {"edge_id": edge_id, "status": "created"}

@router.get("/api/v1/memory/associations/{concept}")
async def get_associations(
    concept: str,
    depth: int = 3,
    threshold: float = 0.3,
    current_user: User = Depends(get_current_user)
):
    """連想検索."""
    results = associative_memory.retrieve_associated_concepts(
        trigger=concept,
        depth=depth,
        threshold=threshold
    )
    return {"concept": concept, "associations": results, "count": len(results)}
```

#### 4.1.4 テスト（20件）

```python
# tests/test_associative_memory.py

def test_add_concept():
    """概念追加テスト."""
    memory = AssociativeMemory(":memory:")
    concept_id = memory.add_concept("Python", [0.1, 0.2], {"category": "programming"})
    assert concept_id is not None

def test_link_concepts():
    """関連付けテスト."""
    memory = AssociativeMemory(":memory:")
    memory.add_concept("Python", [0.1], {})
    memory.add_concept("AI", [0.2], {})
    edge_id = memory.link_concepts("Python", "AI", "used_for", 0.9)
    assert edge_id is not None

def test_retrieve_associated_concepts():
    """連想検索テスト."""
    memory = AssociativeMemory(":memory:")
    memory.add_concept("Python", [0.1], {})
    memory.add_concept("AI", [0.2], {})
    memory.link_concepts("Python", "AI", "used_for", 0.9)
    results = memory.retrieve_associated_concepts("Python", depth=2, threshold=0.5)
    assert len(results) > 0
    assert any(r['name'] == 'AI' for r in results)

def test_strengthen_association():
    """関連性強化テスト（ヘッブの法則）."""
    memory = AssociativeMemory(":memory:")
    memory.add_concept("A", [0.1], {})
    memory.add_concept("B", [0.2], {})
    memory.link_concepts("A", "B", "related", 0.5)
    memory.strengthen_association("A", "B", delta=0.2)
    # 強度が0.7になっているか確認

def test_decay_inactive_associations():
    """忘却処理テスト."""
    memory = AssociativeMemory(":memory:")
    memory.add_concept("Old", [0.1], {})
    memory.add_concept("Forgotten", [0.2], {})
    memory.link_concepts("Old", "Forgotten", "weak", 0.2)
    decayed = memory.decay_inactive_associations(days_threshold=1, decay_rate=0.3)
    assert decayed >= 0

# ... 他15件（グラフ探索、最短パス、感情記憶、クラスタリング等）
```

### 4.2 Week 7-8: 感情モデル基盤

#### 4.2.1 実装内容

**参照**: `docks/仕様書/04_会話LLM_感情・対話仕様.md`

**主要機能**:
1. **8基本感情管理**（Plutchikの感情の輪）
   - 喜び、信頼、恐れ、驚き、悲しみ、嫌悪、怒り、期待

2. **感情の自然な減衰**
   - ホメオスタシス（中立値0.5へ）
   - 時間経過による自動減衰

3. **ユーザー感情分析**
   - sentiment analysis統合
   - 共感的応答（ミラーリング）

#### 4.2.2 ファイル構成

```python
# core/emotion.py (300行)
from typing import Dict, List
import time
from textblob import TextBlob

class EmotionalState:
    """キャラクター感情状態管理."""
    
    EMOTIONS = ['joy', 'trust', 'fear', 'surprise', 'sadness', 'disgust', 'anger', 'anticipation']
    
    def __init__(self, character_name: str):
        self.character_name = character_name
        # 全感情を中立値0.5で初期化
        self.emotions: Dict[str, float] = {e: 0.5 for e in self.EMOTIONS}
        self.mood_history: List[Dict] = []
    
    def update_from_conversation(
        self,
        user_input: str,
        context: Dict
    ) -> None:
        """会話から感情更新."""
        # ユーザー感情分析
        user_sentiment = self._analyze_sentiment(user_input)
        
        # 共感的応答（ミラーリング）
        if user_sentiment > 0.5:
            self.emotions['joy'] = min(self.emotions['joy'] + 0.1, 1.0)
            self.emotions['trust'] = min(self.emotions['trust'] + 0.05, 1.0)
        elif user_sentiment < -0.5:
            self.emotions['sadness'] = min(self.emotions['sadness'] + 0.1, 1.0)
        
        # 履歴記録
        self.mood_history.append({
            'timestamp': time.time(),
            'emotions': self.emotions.copy(),
            'dominant': self.get_dominant_emotion()
        })
        
        # 自動減衰
        self._decay_emotions(rate=0.05)
    
    def _analyze_sentiment(self, text: str) -> float:
        """センチメント分析（-1.0 ~ 1.0）."""
        blob = TextBlob(text)
        return blob.sentiment.polarity
    
    def _decay_emotions(self, rate: float = 0.05) -> None:
        """感情減衰（ホメオスタシス）."""
        for emotion in self.emotions:
            if self.emotions[emotion] > 0.5:
                self.emotions[emotion] = max(self.emotions[emotion] - rate, 0.5)
            elif self.emotions[emotion] < 0.5:
                self.emotions[emotion] = min(self.emotions[emotion] + rate, 0.5)
    
    def get_dominant_emotion(self) -> str:
        """支配的感情取得."""
        return max(self.emotions, key=self.emotions.get)
    
    def generate_emotional_modifier(self) -> str:
        """プロンプト修飾子生成."""
        dominant = self.get_dominant_emotion()
        intensity = self.emotions[dominant] - 0.5  # 0.0 ~ 0.5
        
        if intensity > 0.3:
            return f"（現在、{dominant}の感情が強い状態です）"
        elif intensity > 0.1:
            return f"（やや{dominant}な気持ちです）"
        else:
            return ""
    
    def analyze_mood_trend(self, hours: int = 24) -> Dict[str, str]:
        """感情トレンド分析."""
        cutoff = time.time() - (hours * 3600)
        recent_moods = [m for m in self.mood_history if m['timestamp'] > cutoff]
        
        if not recent_moods:
            return {"trend": "neutral", "description": "データ不足"}
        
        # 最頻感情
        dominant_emotions = [m['dominant'] for m in recent_moods]
        most_common = max(set(dominant_emotions), key=dominant_emotions.count)
        
        return {
            "trend": most_common,
            "description": f"過去{hours}時間、{most_common}が優勢",
            "sample_count": len(recent_moods)
        }
```

#### 4.2.3 API追加

```python
# api/routes/chat.py に追加

from core.emotion import EmotionalState

# キャラクターごとの感情状態
character_emotions = {
    "lumina": EmotionalState("lumina"),
    "clarisse": EmotionalState("clarisse"),
    "nox": EmotionalState("nox")
}

@router.get("/api/v1/character/{name}/emotion")
async def get_character_emotion(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """キャラクター感情状態取得."""
    if name not in character_emotions:
        raise HTTPException(status_code=404, detail="Character not found")
    
    emotion_state = character_emotions[name]
    return {
        "character": name,
        "emotions": emotion_state.emotions,
        "dominant": emotion_state.get_dominant_emotion(),
        "mood_trend": emotion_state.analyze_mood_trend(hours=24),
        "modifier": emotion_state.generate_emotional_modifier()
    }
```

#### 4.2.4 テスト（15件）

```python
# tests/test_emotion.py

def test_emotional_state_init():
    """初期化テスト."""
    state = EmotionalState("lumina")
    assert all(v == 0.5 for v in state.emotions.values())

def test_update_from_conversation():
    """感情更新テスト."""
    state = EmotionalState("lumina")
    state.update_from_conversation("素晴らしい！", {})
    assert state.emotions['joy'] > 0.5

def test_decay_emotions():
    """減衰テスト."""
    state = EmotionalState("lumina")
    state.emotions['joy'] = 1.0
    state._decay_emotions(rate=0.1)
    assert state.emotions['joy'] < 1.0

def test_get_dominant_emotion():
    """支配的感情テスト."""
    state = EmotionalState("lumina")
    state.emotions['anger'] = 0.9
    assert state.get_dominant_emotion() == 'anger'

def test_sentiment_analysis():
    """センチメント分析テスト."""
    state = EmotionalState("lumina")
    pos_score = state._analyze_sentiment("I love this!")
    neg_score = state._analyze_sentiment("I hate this!")
    assert pos_score > 0
    assert neg_score < 0

# ... 他10件（履歴記録、トレンド分析、修飾子生成等）
```

---

## 5. 技術スタック

### 5.1 フロントエンド

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **Framework** | React 18 + TypeScript | UI構築 |
| **Build Tool** | Vite 5 | 高速ビルド |
| **State管理** | Redux Toolkit | グローバル状態 |
| **HTTP Client** | Axios | REST API通信 |
| **WebSocket** | socket.io-client | リアルタイム通信 |
| **UI Library** | Tailwind CSS | スタイリング |
| **Chart** | Recharts | 記憶統計可視化 |
| **Testing** | Cypress + Vitest | E2E + Unit |

### 5.2 バックエンド（Part B追加）

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **Graph DB** | SQLite（再帰CTE） | 連想記憶 |
| **NLP** | TextBlob | 感情分析 |

---

## 6. アーキテクチャ設計

### 6.1 フロントエンド全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    React SPA (Port 3000)                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ LoginPage  │  │ ChatPage   │  │ Dashboard  │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
│        │               │               │                │
│  ┌─────┴────────────────┴───────────────┴──────┐        │
│  │         Redux Store                          │        │
│  │  - authSlice (認証状態)                      │        │
│  │  - chatSlice (会話履歴)                      │        │
│  └─────┬────────────────────────────────────────┘        │
│        │                                                 │
│  ┌─────┴──────────────────────────────┐                 │
│  │  Services                           │                 │
│  │  - api.ts (Axios + JWT Interceptor)│                 │
│  │  - websocket.service.ts             │                 │
│  └─────┬──────────────────────────────┘                 │
└────────┼─────────────────────────────────────────────────┘
         │
         ├─ REST: POST /api/v1/auth/login
         ├─ REST: GET /api/v1/chat/history
         └─ WebSocket: /ws/chat
```

### 6.2 バックエンド拡張構成

```
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (Port 8000)               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 3 REST/WebSocket API                    │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                         │
│  ┌────────────┴───────────────────────────────────┐    │
│  │  Phase 1-3統合サービス                         │    │
│  │  - ChatService                                 │    │
│  │  - MemoryService                               │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                         │
│  ┌────────────┴───────────────────────────────────┐    │
│  │  Phase 4拡張（Part B）                         │    │
│  │  - AssociativeMemory (SQLite Graph)            │    │
│  │  - EmotionalState (8感情モデル)                │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                         │
│  ┌────────────┴───────────────────────────────────┐    │
│  │  Phase 1 LangGraph Core                        │    │
│  │  - MultiLLMChat                                │    │
│  │  - MemoryManager (5階層)                       │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 7. テスト計画

### 7.1 フロントエンド（Part A）

| カテゴリ | ツール | テスト数 | 内容 |
|---------|--------|---------|------|
| **Unit** | Vitest | 50件 | コンポーネント・Service |
| **E2E** | Cypress | 20件 | 認証・会話・ダッシュボード |

```typescript
// cypress/e2e/auth.cy.ts
describe('認証フロー', () => {
  it('ログイン成功', () => { /* ... */ });
  it('ログアウト', () => { /* ... */ });
});

// cypress/e2e/chat.cy.ts
describe('会話フロー', () => {
  it('メッセージ送信', () => { /* ... */ });
  it('WebSocketストリーミング', () => { /* ... */ });
});
```

### 7.2 バックエンド（Part B）

| カテゴリ | テスト数 | 内容 |
|---------|---------|------|
| **連想記憶** | 20件 | 概念追加、リンク、検索、強化、忘却 |
| **感情モデル** | 15件 | 初期化、更新、減衰、分析 |

---

## 8. デプロイ戦略

### 8.1 Docker Compose構成

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on: [backend]

  backend:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/llm
      - REDIS_URL=redis://redis:6379
    depends_on: [db, redis]
    volumes:
      - ./memory:/app/memory  # 連想記憶DB永続化

  db:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

volumes:
  postgres_data:
  redis_data:
```

### 8.2 デプロイ手順

```bash
# 1. フロントエンドビルド
cd frontend && npm run build

# 2. Docker Compose起動
docker-compose up -d

# 3. 初期化スクリプト実行
docker-compose exec backend python -m scripts.init_db

# 4. ヘルスチェック
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## Phase 4 成果物まとめ

### Part A: フロントエンド実装（Week 1-4）

**実装コード**:
- React SPA: 約3,000行（TypeScript）
- コンポーネント: 30個
- ページ: 15画面

**テスト**:
- Unit: 50件
- E2E: 20件

### Part B: バックエンド高度機能（Week 5-8）

**実装コード**:
- 連想記憶システム: 400行（Python）
- 感情モデル: 300行（Python）
- **合計**: 700行

**テスト**:
- 連想記憶: 20件
- 感情モデル: 15件
- **合計**: 35件

### 総計

- **コード**: 3,700行（TS 3,000 + Py 700）
- **テスト**: 105件（FE 70 + BE 35）
- **期間**: 8週間

---

## 次のステップ: Phase 5以降

Phase 4完了後の展望:

- **Phase 5**: 対話スタイル適応・自己省察（4週間）
- **Phase 6**: キャラクター成長・MCP対応（4週間）
- **Phase 7**: 3D可視化・自律サーチ（4週間）
- **Phase 8**: LoRAファインチューニング（3週間）

**参照**: `docks/実装仕様/Phase4-8_実装計画.md`