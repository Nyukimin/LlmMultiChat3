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
7. [テスト計画（TDD実装）](#7-テスト計画tdd実装)
   - [Part A: フロントエンド実装 - テスト仕様（TDD）](#part-a-フロントエンド実装---テスト仕様tdd)
   - [Part B: バックエンド高度機能 - テスト仕様（TDD）](#part-b-バックエンド高度機能---テスト仕様tdd)
   - [テストフィクスチャ仕様](#テストフィクスチャ仕様)
   - [テスト実行戦略](#テスト実行戦略)
8. [デプロイ戦略](#8-デプロイ戦略)
9. [Phase 4成功基準](#9-phase-4成功基準)

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

### 1.2 TDD実装アプローチ

Phase 4は**テスト駆動開発（TDD）**で実装します。各機能は以下のサイクルで開発します：

```
1. 🔴 RED: テストを書く（失敗する）
2. 🟢 GREEN: 最小限の実装でテストを通す
3. 🔵 REFACTOR: コードをリファクタリング（テストは常に成功）
```

**TDDの原則**:
- ✅ 実装前に必ずテストを書く
- ✅ 1つのテスト → 1つの実装 → リファクタリングのサイクル
- ✅ Given-When-Then形式でテストを記述
- ✅ 各テストは独立して実行可能
- ✅ 外部依存はモックで分離

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

## 7. テスト計画（TDD実装）

### 7.1 テストカバレッジ目標

| カテゴリ | ファイル | テスト数 | カバレッジ目標 | 優先度 |
|---------|---------|---------|--------------|--------|
| **Part A: フロントエンド** |
| API Client | `api.test.ts` | 15 | 95%以上 | 🔴 High |
| 認証サービス | `auth.service.test.ts` | 20 | 95%以上 | 🔴 High |
| WebSocketサービス | `websocket.service.test.ts` | 15 | 90%以上 | 🔴 High |
| Redux Auth Slice | `authSlice.test.ts` | 15 | 95%以上 | 🔴 High |
| Redux Chat Slice | `chatSlice.test.ts` | 15 | 95%以上 | 🔴 High |
| LoginPage | `LoginPage.test.tsx` | 10 | 90%以上 | 🔴 High |
| ChatWindow | `ChatWindow.test.tsx` | 15 | 90%以上 | 🔴 High |
| MemoryDashboard | `MemoryDashboard.test.tsx` | 10 | 85%以上 | 🟡 Medium |
| **E2E (Cypress)** | `auth.cy.ts` | 10 | - | 🔴 High |
| | `chat.cy.ts` | 10 | - | 🔴 High |
| | `dashboard.cy.ts` | 5 | - | 🟡 Medium |
| **Part B: バックエンド** |
| 連想記憶システム | `test_associative_memory.py` | 30 | 95%以上 | 🟡 Medium |
| 感情モデル | `test_emotion.py` | 20 | 95%以上 | 🟡 Medium |
| 連想記憶API | `test_api_associative.py` | 15 | 90%以上 | 🟡 Medium |
| 感情API | `test_api_emotion.py` | 10 | 90%以上 | 🟡 Medium |
| **合計** | **20ファイル** | **215** | **平均90%以上** | - |

### 7.2 テスト実行方法

#### フロントエンド（Part A）

```bash
# Unitテスト実行（Vitest）
npm run test  # 全テスト実行
npm run test:watch  # ウォッチモード
npm run test:coverage  # カバレッジ付き

# E2Eテスト実行（Cypress）
npm run test:e2e  # ヘッドレスモード
npm run test:e2e:open  # インタラクティブモード

# 特定のテストのみ
npm run test -- api.test.ts
npm run test:e2e -- --spec "cypress/e2e/auth.cy.ts"
```

#### バックエンド（Part B）

```bash
# 全テスト実行
pytest tests/test_associative_memory.py tests/test_emotion.py -v

# カバレッジ付きテスト実行
pytest tests/test_associative_memory.py --cov=memory.associative --cov-report=html

# 特定のテストのみ
pytest tests/test_associative_memory.py::test_add_concept -v
```

---

## Part A: フロントエンド実装 - テスト仕様（TDD）

### Week 1: React基盤・認証UI - テスト仕様

#### 1. API Client テスト仕様

**テストファイル**: `src/services/__tests__/api.test.ts`

**テストクラス**: `ApiClientTest`

**テストケース一覧（15件）**:

```typescript
describe('ApiClient', () => {
  describe('初期化', () => {
    it('should create axios instance with correct base URL', () => {
      /**
       * Given: 環境変数でAPI_BASE_URLが設定されている
       * When: ApiClientを初期化
       * Then: axiosインスタンスが正しいbaseURLで作成される
       */
      const client = new ApiClient();
      expect(client.client.defaults.baseURL).toBe('http://localhost:8000');
    });

    it('should set default timeout to 30000ms', () => {
      /**
       * Given: ApiClientインスタンス
       * When: タイムアウト設定を確認
       * Then: タイムアウトが30000msに設定されている
       */
      const client = new ApiClient();
      expect(client.client.defaults.timeout).toBe(30000);
    });
  });

  describe('リクエストインターセプター', () => {
    it('should add Authorization header when token exists', async () => {
      /**
       * Given: localStorageにaccess_tokenが保存されている
       * When: APIリクエストを送信
       * Then: AuthorizationヘッダーにBearerトークンが含まれる
       */
      localStorage.setItem('access_token', 'test_token');
      const client = new ApiClient();
      
      // モックでリクエストをインターセプト
      const interceptor = vi.fn();
      client.client.interceptors.request.use(interceptor);
      
      await client.client.get('/test');
      expect(interceptor).toHaveBeenCalled();
    });

    it('should not add Authorization header when token does not exist', async () => {
      /**
       * Given: localStorageにaccess_tokenが保存されていない
       * When: APIリクエストを送信
       * Then: Authorizationヘッダーが追加されない
       */
      localStorage.removeItem('access_token');
      const client = new ApiClient();
      
      const interceptor = vi.fn();
      client.client.interceptors.request.use(interceptor);
      
      await client.client.get('/test');
      // トークンがない場合はヘッダーが追加されないことを確認
    });
  });

  describe('レスポンスインターセプター', () => {
    it('should refresh token on 401 error', async () => {
      /**
       * Given: 401エラーが発生し、refresh_tokenが存在する
       * When: APIリクエストが失敗する
       * Then: トークンが自動更新され、リクエストが再試行される
       */
      // モック実装
    });

    it('should logout on 401 error when refresh token is invalid', async () => {
      /**
       * Given: 401エラーが発生し、refresh_tokenが無効
       * When: APIリクエストが失敗する
       * Then: ログアウト処理が実行される
       */
      // モック実装
    });
  });
});
```

#### 2. 認証サービス テスト仕様

**テストファイル**: `src/services/__tests__/auth.service.test.ts`

**テストケース一覧（20件）**:

```typescript
describe('AuthService', () => {
  describe('register', () => {
    it('should register user successfully', async () => {
      /**
       * Given: 有効なユーザー登録情報
       * When: register()を呼び出す
       * Then: ユーザーが登録され、user_idが返される
       */
      const mockResponse = { data: { user_id: 'user_123' } };
      vi.spyOn(apiClient, 'post').mockResolvedValue(mockResponse);
      
      const result = await authService.register({
        username: 'test_user',
        email: 'test@example.com',
        password: 'SecurePass123!'
      });
      
      expect(result.user_id).toBe('user_123');
      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/register', {
        username: 'test_user',
        email: 'test@example.com',
        password: 'SecurePass123!'
      });
    });

    it('should throw error on duplicate email', async () => {
      /**
       * Given: 既存のメールアドレス
       * When: register()を呼び出す
       * Then: エラーが発生する
       */
      const mockError = { response: { status: 400, data: { detail: 'Email already exists' } } };
      vi.spyOn(apiClient, 'post').mockRejectedValue(mockError);
      
      await expect(authService.register({
        username: 'test_user',
        email: 'existing@example.com',
        password: 'SecurePass123!'
      })).rejects.toThrow();
    });
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      /**
       * Given: 有効な認証情報
       * When: login()を呼び出す
       * Then: トークンがlocalStorageに保存される
       */
      const mockResponse = {
        data: {
          access_token: 'access_token_123',
          refresh_token: 'refresh_token_123'
        }
      };
      vi.spyOn(apiClient, 'post').mockResolvedValue(mockResponse);
      
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });
      
      expect(localStorage.getItem('access_token')).toBe('access_token_123');
      expect(localStorage.getItem('refresh_token')).toBe('refresh_token_123');
    });

    it('should throw error on invalid credentials', async () => {
      /**
       * Given: 無効な認証情報
       * When: login()を呼び出す
       * Then: エラーが発生する
       */
      const mockError = { response: { status: 401, data: { detail: 'Invalid credentials' } } };
      vi.spyOn(apiClient, 'post').mockRejectedValue(mockError);
      
      await expect(authService.login({
        email: 'test@example.com',
        password: 'WrongPassword'
      })).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('should remove tokens from localStorage', () => {
      /**
       * Given: localStorageにトークンが保存されている
       * When: logout()を呼び出す
       * Then: トークンが削除される
       */
      localStorage.setItem('access_token', 'token');
      localStorage.setItem('refresh_token', 'refresh');
      
      authService.logout();
      
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('getProfile', () => {
    it('should fetch user profile', async () => {
      /**
       * Given: 認証済みユーザー
       * When: getProfile()を呼び出す
       * Then: ユーザープロファイルが返される
       */
      const mockProfile = {
        data: {
          user_id: 'user_123',
          username: 'test_user',
          email: 'test@example.com'
        }
      };
      vi.spyOn(apiClient, 'get').mockResolvedValue(mockProfile);
      
      const profile = await authService.getProfile();
      
      expect(profile.user_id).toBe('user_123');
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/profile');
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      /**
       * Given: localStorageにaccess_tokenが保存されている
       * When: isAuthenticated()を呼び出す
       * Then: trueが返される
       */
      localStorage.setItem('access_token', 'token');
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should return false when token does not exist', () => {
      /**
       * Given: localStorageにaccess_tokenが保存されていない
       * When: isAuthenticated()を呼び出す
       * Then: falseが返される
       */
      localStorage.removeItem('access_token');
      expect(authService.isAuthenticated()).toBe(false);
    });
  });
});
```

#### 3. Redux Auth Slice テスト仕様

**テストファイル**: `src/store/__tests__/authSlice.test.ts`

**テストケース一覧（15件）**:

```typescript
describe('authSlice', () => {
  describe('loginAsync', () => {
    it('should handle login success', async () => {
      /**
       * Given: 有効な認証情報
       * When: loginAsyncをdispatch
       * Then: 認証状態が更新され、ユーザー情報が保存される
       */
      const store = configureStore({ reducer: { auth: authReducer } });
      const mockUser = { user_id: 'user_123', username: 'test_user' };
      
      vi.spyOn(authService, 'login').mockResolvedValue({
        access_token: 'token',
        refresh_token: 'refresh'
      });
      vi.spyOn(authService, 'getProfile').mockResolvedValue(mockUser);
      
      await store.dispatch(loginAsync({
        email: 'test@example.com',
        password: 'password'
      }));
      
      const state = store.getState().auth;
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
    });

    it('should handle login failure', async () => {
      /**
       * Given: 無効な認証情報
       * When: loginAsyncをdispatch
       * Then: エラー状態が設定される
       */
      const store = configureStore({ reducer: { auth: authReducer } });
      
      vi.spyOn(authService, 'login').mockRejectedValue(new Error('Login failed'));
      
      await store.dispatch(loginAsync({
        email: 'test@example.com',
        password: 'wrong'
      }));
      
      const state = store.getState().auth;
      expect(state.error).toBeTruthy();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear user state on logout', () => {
      /**
       * Given: 認証済み状態
       * When: logoutアクションをdispatch
       * Then: ユーザー状態がクリアされる
       */
      const store = configureStore({
        reducer: { auth: authReducer },
        preloadedState: {
          auth: {
            user: { user_id: 'user_123' },
            isAuthenticated: true,
            isLoading: false,
            error: null
          }
        }
      });
      
      store.dispatch(logout());
      
      const state = store.getState().auth;
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });
});
```

### Week 2: リアルタイム会話UI - テスト仕様

#### 1. WebSocketサービス テスト仕様

**テストファイル**: `src/services/__tests__/websocket.service.test.ts`

**テストケース一覧（15件）**:

```typescript
describe('WebSocketService', () => {
  describe('connect', () => {
    it('should establish WebSocket connection', () => {
      /**
       * Given: 有効な認証トークン
       * When: connect()を呼び出す
       * Then: WebSocket接続が確立される
       */
      const service = new WebSocketService();
      const mockSocket = { on: vi.fn(), emit: vi.fn() };
      vi.spyOn(io, 'default').mockReturnValue(mockSocket as any);
      
      service.connect('test_token');
      
      expect(io.default).toHaveBeenCalledWith('ws://localhost:8000', {
        path: '/ws/chat',
        auth: { token: 'test_token' },
        transports: ['websocket']
      });
    });
  });

  describe('sendMessage', () => {
    it('should send message through WebSocket', () => {
      /**
       * Given: WebSocket接続済み
       * When: sendMessage()を呼び出す
       * Then: メッセージがWebSocket経由で送信される
       */
      const service = new WebSocketService();
      const mockSocket = { emit: vi.fn() };
      (service as any).socket = mockSocket;
      
      service.sendMessage('Hello', 'session_123');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('chat', {
        type: 'chat',
        user_input: 'Hello',
        session_id: 'session_123'
      });
    });

    it('should not send message when socket is not connected', () => {
      /**
       * Given: WebSocket未接続
       * When: sendMessage()を呼び出す
       * Then: エラーが発生しない（無視される）
       */
      const service = new WebSocketService();
      (service as any).socket = null;
      
      expect(() => {
        service.sendMessage('Hello', 'session_123');
      }).not.toThrow();
    });
  });

  describe('onMessage', () => {
    it('should register message handler', () => {
      /**
       * Given: WebSocketサービス
       * When: onMessage()でハンドラーを登録
       * Then: ハンドラーが登録される
       */
      const service = new WebSocketService();
      const handler = vi.fn();
      
      service.onMessage(handler);
      
      // メッセージ受信時にハンドラーが呼ばれることを確認
      const mockData = { type: 'chunk', content: 'test' };
      (service as any).messageHandlers.forEach((h: any) => h(mockData));
      
      expect(handler).toHaveBeenCalledWith(mockData);
    });
  });

  describe('disconnect', () => {
    it('should disconnect WebSocket', () => {
      /**
       * Given: WebSocket接続済み
       * When: disconnect()を呼び出す
       * Then: WebSocket接続が切断される
       */
      const service = new WebSocketService();
      const mockSocket = { disconnect: vi.fn() };
      (service as any).socket = mockSocket;
      
      service.disconnect();
      
      expect(mockSocket.disconnect).toHaveBeenCalled();
      expect((service as any).socket).toBeNull();
    });
  });
});
```

#### 2. ChatWindow コンポーネント テスト仕様

**テストファイル**: `src/components/chat/__tests__/ChatWindow.test.tsx`

**テストケース一覧（15件）**:

```typescript
describe('ChatWindow', () => {
  it('should render message list and input', () => {
    /**
     * Given: ChatWindowコンポーネント
     * When: レンダリング
     * Then: メッセージリストと入力欄が表示される
     */
    render(<ChatWindow />);
    
    expect(screen.getByTestId('message-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-input')).toBeInTheDocument();
  });

  it('should send message on submit', () => {
    /**
     * Given: メッセージ入力欄
     * When: メッセージを入力して送信
     * Then: メッセージが送信される
     */
    const mockSendMessage = vi.fn();
    vi.spyOn(websocketService, 'sendMessage').mockImplementation(mockSendMessage);
    
    render(<ChatWindow />);
    
    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByTestId('send-button'));
    
    expect(mockSendMessage).toHaveBeenCalledWith('Hello', expect.any(String));
  });

  it('should display typing indicator when receiving chunks', () => {
    /**
     * Given: WebSocket接続済み
     * When: チャンクメッセージを受信
     * Then: タイピングインジケーターが表示される
     */
    render(<ChatWindow />);
    
    // WebSocketメッセージをシミュレート
    const mockHandler = (websocketService as any).messageHandlers[0];
    mockHandler({ type: 'chunk', content: 'test' });
    
    expect(screen.getByText('入力中...')).toBeInTheDocument();
  });
});
```

### Week 3: 記憶管理ダッシュボード - テスト仕様

#### MemoryDashboard コンポーネント テスト仕様

**テストファイル**: `src/components/dashboard/__tests__/MemoryDashboard.test.tsx`

**テストケース一覧（10件）**:

```typescript
describe('MemoryDashboard', () => {
  it('should fetch and display memory stats', async () => {
    /**
     * Given: 記憶統計API
     * When: コンポーネントがマウントされる
     * Then: 記憶統計が取得され、表示される
     */
    const mockStats = {
      total_memories: 100,
      by_layer: {
        short_term: 20,
        mid_term: 30,
        long_term: 50
      }
    };
    
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: mockStats });
    
    render(<MemoryDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('総記憶数')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  it('should display loading state initially', () => {
    /**
     * Given: 記憶統計API（遅延）
     * When: コンポーネントがマウントされる
     * Then: ローディング状態が表示される
     */
    vi.spyOn(apiClient, 'get').mockImplementation(() => new Promise(() => {}));
    
    render(<MemoryDashboard />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

### Week 4: E2Eテスト（Cypress）

#### 認証フロー E2Eテスト

**テストファイル**: `cypress/e2e/auth.cy.ts`

**テストケース一覧（10件）**:

```typescript
describe('認証フロー', () => {
  it('should register new user successfully', () => {
    /**
     * Given: 新規ユーザー登録ページ
     * When: 有効な情報を入力して登録
     * Then: 登録が成功し、ログイン状態になる
     */
    cy.visit('/register');
    cy.get('[data-testid="username-input"]').type('test_user');
    cy.get('[data-testid="email-input"]').type('test@example.com');
    cy.get('[data-testid="password-input"]').type('SecurePass123!');
    cy.get('[data-testid="register-button"]').click();
    
    cy.url().should('include', '/chat');
    cy.get('[data-testid="user-profile"]').should('contain', 'test_user');
  });

  it('should login successfully', () => {
    /**
     * Given: ログインページ
     * When: 有効な認証情報を入力してログイン
     * Then: ログインが成功し、チャットページに遷移する
     */
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type('test@example.com');
    cy.get('[data-testid="password-input"]').type('SecurePass123!');
    cy.get('[data-testid="login-button"]').click();
    
    cy.url().should('include', '/chat');
  });

  it('should logout successfully', () => {
    /**
     * Given: ログイン済み状態
     * When: ログアウトボタンをクリック
     * Then: ログアウトされ、ログインページに遷移する
     */
    cy.login('test@example.com', 'SecurePass123!');
    cy.visit('/chat');
    
    cy.get('[data-testid="logout-button"]').click();
    
    cy.url().should('include', '/login');
    cy.get('[data-testid="login-form"]').should('be.visible');
  });

  it('should show error on invalid login', () => {
    /**
     * Given: ログインページ
     * When: 無効な認証情報を入力してログイン
     * Then: エラーメッセージが表示される
     */
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type('wrong@example.com');
    cy.get('[data-testid="password-input"]').type('WrongPassword');
    cy.get('[data-testid="login-button"]').click();
    
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid');
  });
});
```

#### 会話フロー E2Eテスト

**テストファイル**: `cypress/e2e/chat.cy.ts`

**テストケース一覧（10件）**:

```typescript
describe('会話フロー', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'SecurePass123!');
  });

  it('should send message and receive response', () => {
    /**
     * Given: チャットページ
     * When: メッセージを入力して送信
     * Then: メッセージが表示され、応答が受信される
     */
    cy.visit('/chat');
    
    cy.get('[data-testid="message-input"]').type('こんにちは');
    cy.get('[data-testid="send-button"]').click();
    
    cy.get('[data-testid="message-list"]').should('contain', 'こんにちは');
    
    // 応答が受信されるまで待機
    cy.wait(2000);
    cy.get('[data-testid="message-list"]').should('contain', 'assistant');
  });

  it('should display typing indicator during streaming', () => {
    /**
     * Given: チャットページ
     * When: メッセージを送信
     * Then: ストリーミング中にタイピングインジケーターが表示される
     */
    cy.visit('/chat');
    
    cy.get('[data-testid="message-input"]').type('Hello');
    cy.get('[data-testid="send-button"]').click();
    
    cy.get('[data-testid="typing-indicator"]').should('be.visible');
  });
});
```

---

## Part B: バックエンド高度機能 - テスト仕様（TDD）

### Week 5-6: 連想記憶システム - テスト仕様

#### テストファイル: `tests/test_associative_memory.py`

**テストクラス**: `TestAssociativeMemory`

**テストケース一覧（30件）**:

```python
class TestAssociativeMemory:
    """連想記憶システムのテスト"""
    
    def test_add_concept_success(self):
        """
        Given: 概念名、埋め込みベクトル、メタデータ
        When: add_concept()を呼び出す
        Then: 概念が追加され、concept_idが返される
        """
        memory = AssociativeMemory(":memory:")
        concept_id = memory.add_concept(
            concept="Python",
            embedding=[0.1, 0.2, 0.3],
            metadata={"category": "programming"}
        )
        
        assert concept_id is not None
        assert isinstance(concept_id, str)
    
    def test_add_concept_duplicate(self):
        """
        Given: 既存の概念名
        When: add_concept()を呼び出す
        Then: エラーが発生する（または更新される）
        """
        memory = AssociativeMemory(":memory:")
        memory.add_concept("Python", [0.1], {})
        
        # 実装に応じてエラーまたは更新
        with pytest.raises(ValueError):
            memory.add_concept("Python", [0.2], {})
    
    def test_link_concepts_success(self):
        """
        Given: 2つの概念と関連タイプ
        When: link_concepts()を呼び出す
        Then: エッジが作成され、edge_idが返される
        """
        memory = AssociativeMemory(":memory:")
        memory.add_concept("Python", [0.1], {})
        memory.add_concept("AI", [0.2], {})
        
        edge_id = memory.link_concepts(
            concept_a="Python",
            concept_b="AI",
            relationship_type="used_for",
            strength=0.9
        )
        
        assert edge_id is not None
    
    def test_link_concepts_nonexistent(self):
        """
        Given: 存在しない概念
        When: link_concepts()を呼び出す
        Then: エラーが発生する
        """
        memory = AssociativeMemory(":memory:")
        
        with pytest.raises(ValueError):
            memory.link_concepts("Nonexistent", "AI", "related", 0.5)
    
    def test_retrieve_associated_concepts(self):
        """
        Given: トリガー概念と関連概念
        When: retrieve_associated_concepts()を呼び出す
        Then: 関連概念のリストが返される
        """
        memory = AssociativeMemory(":memory:")
        memory.add_concept("Python", [0.1], {})
        memory.add_concept("AI", [0.2], {})
        memory.add_concept("Machine Learning", [0.3], {})
        
        memory.link_concepts("Python", "AI", "used_for", 0.9)
        memory.link_concepts("AI", "Machine Learning", "subset_of", 0.8)
        
        results = memory.retrieve_associated_concepts(
            trigger="Python",
            depth=2,
            threshold=0.5
        )
        
        assert len(results) >= 2
        assert any(r['name'] == 'AI' for r in results)
        assert any(r['name'] == 'Machine Learning' for r in results)
    
    def test_strengthen_association(self):
        """
        Given: 既存の関連
        When: strengthen_association()を呼び出す
        Then: 関連の強度が増加する（ヘッブの法則）
        """
        memory = AssociativeMemory(":memory:")
        memory.add_concept("A", [0.1], {})
        memory.add_concept("B", [0.2], {})
        memory.link_concepts("A", "B", "related", 0.5)
        
        initial_strength = memory.db.get_edge("A", "B")['strength']
        memory.strengthen_association("A", "B", delta=0.2)
        new_strength = memory.db.get_edge("A", "B")['strength']
        
        assert new_strength > initial_strength
        assert new_strength == pytest.approx(0.7, abs=0.01)
    
    def test_decay_inactive_associations(self):
        """
        Given: 非アクティブな関連
        When: decay_inactive_associations()を呼び出す
        Then: 関連の強度が減少する（忘却曲線）
        """
        memory = AssociativeMemory(":memory:")
        memory.add_concept("Old", [0.1], {})
        memory.add_concept("Forgotten", [0.2], {})
        memory.link_concepts("Old", "Forgotten", "weak", 0.2)
        
        # 非アクティブにする（last_activatedを過去に設定）
        # ...
        
        decayed_count = memory.decay_inactive_associations(
            days_threshold=1,
            decay_rate=0.3
        )
        
        assert decayed_count >= 0
    
    def test_retrieve_with_depth_limit(self):
        """
        Given: 多階層の関連
        When: retrieve_associated_concepts()をdepth制限付きで呼び出す
        Then: 指定された深さまでの関連のみが返される
        """
        # 実装
        pass
    
    def test_retrieve_with_threshold(self):
        """
        Given: 強度の異なる関連
        When: retrieve_associated_concepts()をthreshold付きで呼び出す
        Then: 閾値以上の強度の関連のみが返される
        """
        # 実装
        pass
    
    # ... 他20件（グラフ探索、最短パス、感情記憶、クラスタリング等）
```

### Week 7-8: 感情モデル基盤 - テスト仕様

#### テストファイル: `tests/test_emotion.py`

**テストクラス**: `TestEmotionalState`

**テストケース一覧（20件）**:

```python
class TestEmotionalState:
    """感情モデルのテスト"""
    
    def test_emotional_state_init(self):
        """
        Given: キャラクター名
        When: EmotionalStateを初期化
        Then: 全感情が中立値0.5で初期化される
        """
        state = EmotionalState("lumina")
        
        assert all(v == 0.5 for v in state.emotions.values())
        assert len(state.emotions) == 8
        assert state.character_name == "lumina"
    
    def test_update_from_conversation_positive(self):
        """
        Given: ポジティブな会話入力
        When: update_from_conversation()を呼び出す
        Then: 喜びと信頼の感情が増加する
        """
        state = EmotionalState("lumina")
        initial_joy = state.emotions['joy']
        initial_trust = state.emotions['trust']
        
        state.update_from_conversation("素晴らしい！", {})
        
        assert state.emotions['joy'] > initial_joy
        assert state.emotions['trust'] > initial_trust
    
    def test_update_from_conversation_negative(self):
        """
        Given: ネガティブな会話入力
        When: update_from_conversation()を呼び出す
        Then: 悲しみの感情が増加する
        """
        state = EmotionalState("lumina")
        initial_sadness = state.emotions['sadness']
        
        state.update_from_conversation("最悪だ...", {})
        
        assert state.emotions['sadness'] > initial_sadness
    
    def test_decay_emotions(self):
        """
        Given: 高い感情値
        When: _decay_emotions()を呼び出す
        Then: 感情値が中立値0.5に向かって減衰する
        """
        state = EmotionalState("lumina")
        state.emotions['joy'] = 1.0
        
        state._decay_emotions(rate=0.1)
        
        assert state.emotions['joy'] < 1.0
        assert state.emotions['joy'] >= 0.5
    
    def test_get_dominant_emotion(self):
        """
        Given: 異なる感情値
        When: get_dominant_emotion()を呼び出す
        Then: 最も高い感情が返される
        """
        state = EmotionalState("lumina")
        state.emotions['anger'] = 0.9
        state.emotions['joy'] = 0.6
        
        dominant = state.get_dominant_emotion()
        
        assert dominant == 'anger'
    
    def test_generate_emotional_modifier(self):
        """
        Given: 高い感情強度
        When: generate_emotional_modifier()を呼び出す
        Then: プロンプト修飾子が生成される
        """
        state = EmotionalState("lumina")
        state.emotions['joy'] = 0.9
        
        modifier = state.generate_emotional_modifier()
        
        assert 'joy' in modifier.lower() or '喜び' in modifier
    
    def test_analyze_mood_trend(self):
        """
        Given: 感情履歴
        When: analyze_mood_trend()を呼び出す
        Then: 感情トレンドが分析される
        """
        state = EmotionalState("lumina")
        
        # 履歴を追加
        for _ in range(10):
            state.update_from_conversation("楽しい！", {})
        
        trend = state.analyze_mood_trend(hours=24)
        
        assert 'trend' in trend
        assert 'description' in trend
    
    def test_sentiment_analysis_positive(self):
        """
        Given: ポジティブなテキスト
        When: _analyze_sentiment()を呼び出す
        Then: 正のスコアが返される
        """
        state = EmotionalState("lumina")
        score = state._analyze_sentiment("I love this!")
        
        assert score > 0
    
    def test_sentiment_analysis_negative(self):
        """
        Given: ネガティブなテキスト
        When: _analyze_sentiment()を呼び出す
        Then: 負のスコアが返される
        """
        state = EmotionalState("lumina")
        score = state._analyze_sentiment("I hate this!")
        
        assert score < 0
    
    # ... 他11件（履歴記録、トレンド分析、修飾子生成等）
```

---

## テストフィクスチャ仕様

### フロントエンド（Vitest）

**ファイル**: `src/__tests__/setup.ts`

```typescript
import { vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// 各テスト後にクリーンアップ
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// localStorageモック
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

// WebSocketモック
global.WebSocket = vi.fn() as any;
```

### バックエンド（pytest）

**ファイル**: `tests/conftest.py`（拡張）

```python
import pytest
import tempfile
import os
from memory.associative import AssociativeMemory
from core.emotion import EmotionalState

@pytest.fixture
def temp_db():
    """一時的なデータベース"""
    db_path = tempfile.mktemp(suffix='.db')
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def associative_memory(temp_db):
    """連想記憶システムインスタンス"""
    return AssociativeMemory(temp_db)

@pytest.fixture
def emotional_state():
    """感情状態インスタンス"""
    return EmotionalState("test_character")
```

---

## テスト実行戦略

### TDD実装順序

1. **Part A: フロントエンド（Week 1-4）**
   - Week 1: API Clientテスト（15件）→ 実装 → 認証サービステスト（20件）→ 実装
   - Week 2: WebSocketサービステスト（15件）→ 実装 → ChatWindowテスト（15件）→ 実装
   - Week 3: MemoryDashboardテスト（10件）→ 実装
   - Week 4: E2Eテスト（25件）→ 統合テスト・リファクタリング

2. **Part B: バックエンド（Week 5-8）**
   - Week 5-6: 連想記憶システムテスト（30件）→ 実装
   - Week 7-8: 感情モデルテスト（20件）→ 実装

### テスト品質基準

**必須要件**:
- ✅ **テスト成功率**: 100%（全215件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: フロントエンド5分以内、バックエンド3分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存は100%モックで分離

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
- **テスト**: 215件（FE 150 + BE 65）
- **期間**: 8週間

---

## 9. Phase 4成功基準

### TDD実装の成功基準

**必須要件**:
- ✅ **テストファースト**: 全機能がテスト駆動で実装されている
- ✅ **テスト成功率**: 100%（全215件のテストが成功）
- ✅ **コードカバレッジ**: 90%以上（平均）
- ✅ **テスト実行時間**: フロントエンド5分以内、バックエンド3分以内
- ✅ **テスト独立性**: 各テストは独立して実行可能
- ✅ **モック使用**: 外部依存は100%モックで分離

**TDDサイクル遵守**:
- ✅ RED: 実装前にテストを書いている
- ✅ GREEN: 最小限の実装でテストを通している
- ✅ REFACTOR: リファクタリング後もテストが成功している

### 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **テスト成功率** | **100%** | Vitest + pytest（全215件） |
| **コードカバレッジ** | **90%以上** | Vitest --coverage + pytest-cov |
| **テスト実行時間** | **< 8分** | Vitest + pytest --durations |
| フロントエンドビルド時間 | < 30秒 | Vite build |
| E2Eテスト実行時間 | < 5分 | Cypress |
| API応答時間 | < 200ms | Locust負荷テスト |

### 定性目標

✅ **TDD実装完了**: 全機能がテスト駆動で実装されている
✅ **テスト仕様完備**: 全215件のテストケースが定義されている
✅ **フロントエンド完全実装**: React SPA 15画面・30コンポーネント
✅ **バックエンド拡張完了**: 連想記憶システム・感情モデル実装
✅ **E2Eテスト完備**: Cypressテスト25件
✅ **デプロイ準備完了**: Docker Compose構成整備

---

## 次のステップ: Phase 5以降

Phase 4完了後の展望:

- **Phase 5**: 対話スタイル適応・自己省察（4週間）
- **Phase 6**: キャラクター成長・MCP対応（4週間）
- **Phase 7**: 3D可視化・自律サーチ（4週間）
- **Phase 8**: LoRAファインチューニング（3週間）

**参照**: `docks/実装仕様/Phase4-8_実装計画.md`