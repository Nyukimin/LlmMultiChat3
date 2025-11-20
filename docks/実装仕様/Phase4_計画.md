# Phase 4実装計画書

**プロジェクト名**: LlmMultiChat3  
**フェーズ**: Phase 4 - フロントエンド実装  
**期間**: Week 11-14 (4週間)  
**作成日**: 2025-11-14  
**Phase 3完了**: `338a88c`

---

## 目次

1. [Phase 4概要](#1-phase-4概要)
2. [前提条件（Phase 1-3完了事項）](#2-前提条件phase-1-3完了事項)
3. [Week 11: React基盤・認証UI](#3-week-11-react基盤認証ui)
4. [Week 12: リアルタイム会話UI](#4-week-12-リアルタイム会話ui)
5. [Week 13: 記憶管理ダッシュボード](#5-week-13-記憶管理ダッシュボード)
6. [Week 14: 統合テスト・デプロイ](#6-week-14-統合テストデプロイ)
7. [技術スタック](#7-技術スタック)
8. [アーキテクチャ設計](#8-アーキテクチャ設計)
9. [UI/UXデザイン](#9-uiuxデザイン)
10. [Phase 5以降の展望](#10-phase-5以降の展望)

---

## 1. Phase 4概要

### 1.1 目的

Phase 3で実装したREST/WebSocket APIを活用し、**ユーザーフレンドリーなWebフロントエンド**を構築します。リアルタイム会話UI、記憶管理ダッシュボード、認証フローを実装し、LlmMultiChat3を完全なWebアプリケーションとして完成させます。

### 1.2 主要機能

| 機能カテゴリ | 説明 | Priority |
|-------------|------|----------|
| **認証UI** | ログイン・登録・プロファイル管理 | 🔴 High |
| **会話UI** | リアルタイムチャット・ストリーミング応答 | 🔴 High |
| **記憶ダッシュボード** | 記憶統計・検索・可視化 | 🟡 Medium |
| **レスポンシブデザイン** | モバイル・タブレット対応 | 🟡 Medium |
| **ダークモード** | テーマ切り替え機能 | 🟢 Low |

### 1.3 Phase 4達成目標

✅ React SPA完全実装  
✅ JWT認証フロー（ログイン・登録・自動更新）  
✅ WebSocketリアルタイム通信  
✅ ストリーミング応答UI  
✅ 記憶統計ダッシュボード  
✅ レスポンシブデザイン（モバイル・タブレット・デスクトップ）  
✅ E2Eテスト完備（Cypress）  
✅ Docker本番環境デプロイ

---

## 2. 前提条件（Phase 1-3完了事項）

### 2.1 Phase 1完了事項

✅ LangGraphコア実装  
✅ 3キャラクター（ルミナ・クラリス・ノクス）  
✅ 5階層記憶システム

**参照**: [`docks/Phase1_完了サマリー.md`](Phase1_完了サマリー.md:1)

### 2.2 Phase 2完了事項

✅ 18種類のカスタム例外クラス  
✅ 構造化ログ・メトリクス収集  
✅ Redis 2層キャッシュ  
✅ 入力検証（XSS/SQLインジェクション対策）

**参照**: [`docks/Phase2_完了サマリー.md`](Phase2_完了サマリー.md:1)

### 2.3 Phase 3完了事項（APIエンドポイント）

✅ REST API 23エンドポイント  
✅ WebSocket API（リアルタイム双方向通信）  
✅ JWT認証・RBAC  
✅ レート制限（5-100 req/min）  
✅ プラグインシステム（天気・翻訳）

**参照**: [`docks/Phase3_完了サマリー.md`](Phase3_完了サマリー.md:1)

**利用可能なAPIエンドポイント**:
- **認証**: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/profile`, `/api/v1/auth/change-password`, `/api/v1/auth/delete`
- **会話**: `/api/v1/chat/`, `/api/v1/chat/stream`, `/api/v1/chat/history`, `/api/v1/chat/sessions`, `/api/v1/chat/sessions/{session_id}`, `/api/v1/chat/sessions/{session_id}/clear`
- **記憶**: `/api/v1/memory/search`, `/api/v1/memory/store`, `/api/v1/memory/delete/{memory_id}`, `/api/v1/memory/stats`, `/api/v1/memory/sessions/{session_id}`, `/api/v1/memory/flush` (admin), `/api/v1/memory/health`
- **WebSocket**: `/ws/chat`

---

## 3. Week 11: React基盤・認証UI

### 3.1 実装タスク

#### Week 11-1: React基盤構築（3日）

**ディレクトリ構成**:
```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Loading.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   └── auth/
│   │       ├── LoginForm.tsx
│   │       ├── RegisterForm.tsx
│   │       └── ProfileCard.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── ChatPage.tsx
│   │   └── DashboardPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.service.ts
│   │   ├── chat.service.ts
│   │   └── websocket.service.ts
│   ├── store/
│   │   ├── authSlice.ts
│   │   ├── chatSlice.ts
│   │   └── store.ts
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

**ファイル作成**:
- `frontend/package.json` (100行)
- `frontend/vite.config.ts` (50行)
- `frontend/src/App.tsx` (150行)
- `frontend/src/index.tsx` (30行)

**実装機能**:

1. **Vite + React + TypeScript セットアップ**
   ```json
   // package.json
   {
     "name": "llmmultichat3-frontend",
     "version": "4.0.0",
     "type": "module",
     "scripts": {
       "dev": "vite",
       "build": "tsc && vite build",
       "preview": "vite preview",
       "test": "vitest",
       "test:e2e": "cypress open"
     },
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
       "@types/react": "^18.2.0",
       "@types/react-dom": "^18.2.0",
       "@vitejs/plugin-react": "^4.2.0",
       "typescript": "^5.3.0",
       "vite": "^5.0.0",
       "vitest": "^1.0.0",
       "cypress": "^13.6.0",
       "@testing-library/react": "^14.1.0",
       "@testing-library/jest-dom": "^6.1.0"
     }
   }
   ```

2. **Tailwind CSS設定**
   ```typescript
   // tailwind.config.js
   export default {
     content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
     theme: {
       extend: {
         colors: {
           primary: {
             50: '#f0f9ff',
             100: '#e0f2fe',
             500: '#0ea5e9',
             600: '#0284c7',
             700: '#0369a1',
           },
           secondary: {
             50: '#fdf4ff',
             500: '#d946ef',
             600: '#c026d3',
           },
         },
       },
     },
     plugins: [],
   };
   ```

3. **Redux Store設定**
   ```typescript
   // src/store/store.ts
   import { configureStore } from '@reduxjs/toolkit';
   import authReducer from './authSlice';
   import chatReducer from './chatSlice';
   
   export const store = configureStore({
     reducer: {
       auth: authReducer,
       chat: chatReducer,
     },
   });
   
   export type RootState = ReturnType<typeof store.getState>;
   export type AppDispatch = typeof store.dispatch;
   ```

#### Week 11-2: 認証サービス実装（3日）

**ファイル作成**:
- `frontend/src/services/api.ts` (150行)
- `frontend/src/services/auth.service.ts` (300行)
- `frontend/src/store/authSlice.ts` (250行)
- `frontend/src/hooks/useAuth.ts` (200行)

**実装機能**:

1. **Axios API クライアント**
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
         headers: {
           'Content-Type': 'application/json',
         },
       });
   
       // リクエストインターセプター（JWT自動付与）
       this.client.interceptors.request.use(
         (config) => {
           const token = localStorage.getItem('access_token');
           if (token) {
             config.headers.Authorization = `Bearer ${token}`;
           }
           return config;
         },
         (error) => Promise.reject(error)
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
               try {
                 const { data } = await this.client.post('/api/v1/auth/refresh', {
                   refresh_token: refreshToken,
                 });
                 localStorage.setItem('access_token', data.access_token);
                 originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                 return this.client(originalRequest);
               } catch (refreshError) {
                 localStorage.removeItem('access_token');
                 localStorage.removeItem('refresh_token');
                 window.location.href = '/login';
                 return Promise.reject(refreshError);
               }
             }
           }
           return Promise.reject(error);
         }
       );
     }
   
     get client() {
       return this.client;
     }
   }
   
   export const apiClient = new ApiClient().client;
   ```

2. **認証サービス**
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
       token_type: string;
       expires_in: number;
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
   
     async changePassword(oldPassword: string, newPassword: string): Promise<void> {
       await apiClient.post('/api/v1/auth/change-password', {
         old_password: oldPassword,
         new_password: newPassword,
       });
     }
   
     isAuthenticated(): boolean {
       return !!localStorage.getItem('access_token');
     }
   }
   
   export const authService = new AuthService();
   ```

3. **Redux Auth Slice**
   ```typescript
   // src/store/authSlice.ts
   import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
   import { authService } from '../services/auth.service';
   import { User, LoginCredentials, RegisterData } from '../types/auth.types';
   
   interface AuthState {
     user: User | null;
     isAuthenticated: boolean;
     isLoading: boolean;
     error: string | null;
   }
   
   const initialState: AuthState = {
     user: null,
     isAuthenticated: authService.isAuthenticated(),
     isLoading: false,
     error: null,
   };
   
   export const loginAsync = createAsyncThunk(
     'auth/login',
     async (credentials: LoginCredentials, { rejectWithValue }) => {
       try {
         await authService.login(credentials);
         const user = await authService.getProfile();
         return user;
       } catch (error: any) {
         return rejectWithValue(error.response?.data?.detail || 'Login failed');
       }
     }
   );
   
   export const registerAsync = createAsyncThunk(
     'auth/register',
     async (data: RegisterData, { rejectWithValue }) => {
       try {
         return await authService.register(data);
       } catch (error: any) {
         return rejectWithValue(error.response?.data?.detail || 'Registration failed');
       }
     }
   );
   
   const authSlice = createSlice({
     name: 'auth',
     initialState,
     reducers: {
       logout: (state) => {
         authService.logout();
         state.user = null;
         state.isAuthenticated = false;
       },
       clearError: (state) => {
         state.error = null;
       },
     },
     extraReducers: (builder) => {
       builder
         .addCase(loginAsync.pending, (state) => {
           state.isLoading = true;
           state.error = null;
         })
         .addCase(loginAsync.fulfilled, (state, action: PayloadAction<User>) => {
           state.isLoading = false;
           state.isAuthenticated = true;
           state.user = action.payload;
         })
         .addCase(loginAsync.rejected, (state, action) => {
           state.isLoading = false;
           state.error = action.payload as string;
         });
     },
   });
   
   export const { logout, clearError } = authSlice.actions;
   export default authSlice.reducer;
   ```

#### Week 11-3: 認証UI実装（3日）

**ファイル作成**:
- `frontend/src/components/auth/LoginForm.tsx` (250行)
- `frontend/src/components/auth/RegisterForm.tsx` (300行)
- `frontend/src/pages/LoginPage.tsx` (150行)
- `frontend/src/pages/RegisterPage.tsx` (150行)

**実装機能**:

1. **ログインフォーム**
   ```typescript
   // src/components/auth/LoginForm.tsx
   import React, { useState } from 'react';
   import { useDispatch, useSelector } from 'react-redux';
   import { useNavigate } from 'react-router-dom';
   import { loginAsync } from '../../store/authSlice';
   import { AppDispatch, RootState } from '../../store/store';
   import { Button, Input, Card } from '../common';
   
   export const LoginForm: React.FC = () => {
     const [email, setEmail] = useState('');
     const [password, setPassword] = useState('');
     const dispatch = useDispatch<AppDispatch>();
     const navigate = useNavigate();
     const { isLoading, error } = useSelector((state: RootState) => state.auth);
   
     const handleSubmit = async (e: React.FormEvent) => {
       e.preventDefault();
       const result = await dispatch(loginAsync({ email, password }));
       if (loginAsync.fulfilled.match(result)) {
         navigate('/chat');
       }
     };
   
     return (
       <Card className="max-w-md mx-auto mt-16">
         <h2 className="text-2xl font-bold mb-6 text-center">ログイン</h2>
         <form onSubmit={handleSubmit} className="space-y-4">
           <Input
             type="email"
             placeholder="メールアドレス"
             value={email}
             onChange={(e) => setEmail(e.target.value)}
             required
           />
           <Input
             type="password"
             placeholder="パスワード"
             value={password}
             onChange={(e) => setPassword(e.target.value)}
             required
           />
           {error && <div className="text-red-500 text-sm">{error}</div>}
           <Button type="submit" fullWidth loading={isLoading}>
             ログイン
           </Button>
         </form>
         <div className="mt-4 text-center">
           <a href="/register" className="text-primary-600 hover:underline">
             アカウント登録
           </a>
         </div>
       </Card>
     );
   };
   ```

2. **登録フォーム**
   ```typescript
   // src/components/auth/RegisterForm.tsx
   import React, { useState } from 'react';
   import { useDispatch, useSelector } from 'react-redux';
   import { useNavigate } from 'react-router-dom';
   import { registerAsync } from '../../store/authSlice';
   import { AppDispatch, RootState } from '../../store/store';
   import { Button, Input, Card } from '../common';
   
   export const RegisterForm: React.FC = () => {
     const [username, setUsername] = useState('');
     const [email, setEmail] = useState('');
     const [password, setPassword] = useState('');
     const [confirmPassword, setConfirmPassword] = useState('');
     const dispatch = useDispatch<AppDispatch>();
     const navigate = useNavigate();
     const { isLoading, error } = useSelector((state: RootState) => state.auth);
   
     const handleSubmit = async (e: React.FormEvent) => {
       e.preventDefault();
       if (password !== confirmPassword) {
         alert('パスワードが一致しません');
         return;
       }
       const result = await dispatch(registerAsync({ username, email, password }));
       if (registerAsync.fulfilled.match(result)) {
         navigate('/login');
       }
     };
   
     return (
       <Card className="max-w-md mx-auto mt-16">
         <h2 className="text-2xl font-bold mb-6 text-center">アカウント登録</h2>
         <form onSubmit={handleSubmit} className="space-y-4">
           <Input
             type="text"
             placeholder="ユーザー名"
             value={username}
             onChange={(e) => setUsername(e.target.value)}
             required
           />
           <Input
             type="email"
             placeholder="メールアドレス"
             value={email}
             onChange={(e) => setEmail(e.target.value)}
             required
           />
           <Input
             type="password"
             placeholder="パスワード"
             value={password}
             onChange={(e) => setPassword(e.target.value)}
             required
           />
           <Input
             type="password"
             placeholder="パスワード確認"
             value={confirmPassword}
             onChange={(e) => setConfirmPassword(e.target.value)}
             required
           />
           {error && <div className="text-red-500 text-sm">{error}</div>}
           <Button type="submit" fullWidth loading={isLoading}>
             登録
           </Button>
         </form>
         <div className="mt-4 text-center">
           <a href="/login" className="text-primary-600 hover:underline">
             ログインへ戻る
           </a>
         </div>
       </Card>
     );
   };
   ```

---

## 4. Week 12: リアルタイム会話UI

### 4.1 実装タスク

#### Week 12-1: WebSocket サービス実装（3日）

**ファイル作成**:
- `frontend/src/services/websocket.service.ts` (400行)
- `frontend/src/hooks/useWebSocket.ts` (250行)
- `frontend/src/store/chatSlice.ts` (400行)

**実装機能**:

1. **WebSocket サービス**
   ```typescript
   // src/services/websocket.service.ts
   import { io, Socket } from 'socket.io-client';
   
   const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
   
   export class WebSocketService {
     private socket: Socket | null = null;
     private messageHandlers: ((message: any) => void)[] = [];
   
     connect(token: string): void {
       this.socket = io(WS_URL, {
         path: '/ws/chat',
         auth: { token },
         transports: ['websocket'],
       });
   
       this.socket.on('connect', () => {
         console.log('WebSocket connected');
       });
   
       this.socket.on('message', (data) => {
         this.messageHandlers.forEach((handler) => handler(data));
       });
   
       this.socket.on('disconnect', () => {
         console.log('WebSocket disconnected');
       });
   
       this.socket.on('error', (error) => {
         console.error('WebSocket error:', error);
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
   
     offMessage(handler: (message: any) => void): void {
       this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
     }
   }
   
   export const websocketService = new WebSocketService();
   ```

2. **useWebSocket カスタムフック**
   ```typescript
   // src/hooks/useWebSocket.ts
   import { useEffect, useState } from 'react';
   import { websocketService } from '../services/websocket.service';
   
   export const useWebSocket = (token: string | null) => {
     const [isConnected, setIsConnected] = useState(false);
   
     useEffect(() => {
       if (token) {
         websocketService.connect(token);
         setIsConnected(true);
   
         return () => {
           websocketService.disconnect();
           setIsConnected(false);
         };
       }
     }, [token]);
   
     return { isConnected };
   };
   ```

#### Week 12-2: チャット UI 実装（4日）

**ファイル作成**:
- `frontend/src/components/chat/ChatWindow.tsx` (500行)
- `frontend/src/components/chat/MessageList.tsx` (300行)
- `frontend/src/components/chat/MessageInput.tsx` (200行)
- `frontend/src/components/chat/TypingIndicator.tsx` (100行)
- `frontend/src/pages/ChatPage.tsx` (300行)

**実装機能**:

1. **チャットウィンドウ**
   ```typescript
   // src/components/chat/ChatWindow.tsx
   import React, { useEffect, useState } from 'react';
   import { useDispatch, useSelector } from 'react-redux';
   import { MessageList } from './MessageList';
   import { MessageInput } from './MessageInput';
   import { TypingIndicator } from './TypingIndicator';
   import { websocketService } from '../../services/websocket.service';
   import { addMessage } from '../../store/chatSlice';
   import { RootState } from '../../store/store';
   
   export const ChatWindow: React.FC = () => {
     const dispatch = useDispatch();
     const { messages, currentSessionId } = useSelector((state: RootState) => state.chat);
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
   
       return () => {
         websocketService.offMessage(handleMessage);
       };
     }, [dispatch]);
   
     const handleSendMessage = (content: string) => {
       dispatch(addMessage({
         id: Date.now().toString(),
         content,
         role: 'user',
         timestamp: new Date().toISOString(),
       }));
       websocketService.sendMessage(content, currentSessionId);
     };
   
     return (
       <div className="flex flex-col h-screen">
         <div className="flex-1 overflow-y-auto p-4">
           <MessageList messages={messages} />
           {isTyping && <TypingIndicator />}
         </div>
         <MessageInput onSend={handleSendMessage} />
       </div>
     );
   };
   ```

2. **メッセージリスト**
   ```typescript
   // src/components/chat/MessageList.tsx
   import React from 'react';
   import ReactMarkdown from 'react-markdown';
   import { Message } from '../../types/chat.types';
   
   interface MessageListProps {
     messages: Message[];
   }
   
   export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
     return (
       <div className="space-y-4">
         {messages.map((message) => (
           <div
             key={message.id}
             className={`flex ${
               message.role === 'user' ? 'justify-end' : 'justify-start'
             }`}
           >
             <div
               className={`max-w-2xl px-4 py-2 rounded-lg ${
                 message.role === 'user'
                   ? 'bg-primary-600 text-white'
                   : 'bg-gray-200 text-gray-900'
               }`}
             >
               <ReactMarkdown>{message.content}</ReactMarkdown>
               <div className="text-xs mt-1 opacity-70">
                 {new Date(message.timestamp).toLocaleTimeString()}
               </div>
             </div>
           </div>
         ))}
       </div>
     );
   };
   ```

---

## 5. Week 13: 記憶管理ダッシュボード

### 5.1 実装タスク

#### Week 13-1: 記憶統計API実装（2日）

**ファイル作成**:
- `frontend/src/services/memory.service.ts` (300行)
- `frontend/src/store/memorySlice.ts` (250行)

**実装機能**:

1. **記憶サービス**
   ```typescript
   // src/services/memory.service.ts
   import { apiClient } from './api';
   import { MemoryStats, MemorySearchParams } from '../types/memory.types';
   
   export class MemoryService {
     async getStats(): Promise<MemoryStats> {
       const response = await apiClient.get('/api/v1/memory/stats');
       return response.data;
     }
   
     async search(params: MemorySearchParams): Promise<any[]> {
       const response = await apiClient.post('/api/v1/memory/search', params);
       return response.data.results;
     }
   
     async deleteMemory(memoryId: string): Promise<void> {
       await apiClient.delete(`/api/v1/memory/delete/${memoryId}`);
     }
   
     async clearSession(sessionId: string): Promise<void> {
       await apiClient.delete(`/api/v1/memory/sessions/${sessionId}`);
     }
   }
   
   export const memoryService = new MemoryService();
   ```

#### Week 13-2: ダッシュボードUI実装（5日）

**ファイル作成**:
- `frontend/src/components/dashboard/StatsCard.tsx` (150行)
- `frontend/src/components/dashboard/MemoryChart.tsx` (300行)
- `frontend/src/components/dashboard/MemorySearch.tsx` (250行)
- `frontend/src/pages/DashboardPage.tsx` (400行)

**実装機能**:

1. **統計カード**
   ```typescript
   // src/components/dashboard/StatsCard.tsx
   import React from 'react';
   import { Card } from '../common';
   
   interface StatsCardProps {
     title: string;
     value: number;
     icon: React.ReactNode;
     color: string;
   }
   
   export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
     return (
       <Card className={`bg-${color}-50 border-${color}-200`}>
         <div className="flex items-center justify-between">
           <div>
             <p className="text-sm text-gray-600">{title}</p>
             <p className="text-3xl font-bold mt-2">{value.toLocaleString()}</p>
           </div>
           <div className={`text-${color}-500 text-4xl`}>{icon}</div>
         </div>
       </Card>
     );
   };
   ```

2. **記憶統計チャート**
   ```typescript
   // src/components/dashboard/MemoryChart.tsx
   import React from 'react';
   import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
   
   interface MemoryChartProps {
     data: any[];
   }
   
   export const MemoryChart: React.FC<MemoryChartProps> = ({ data }) => {
     return (
       <div className="w-full h-96">
         <LineChart width={800} height={400} data={data}>
           <CartesianGrid strokeDasharray="3 3" />
           <XAxis dataKey="date" />
           <YAxis />
           <Tooltip />
           <Legend />
           <Line type="monotone" dataKey="short_term" stroke="#0ea5e9" name="短期記憶" />
           <Line type="monotone" dataKey="mid_term" stroke="#d946ef" name="中期記憶" />
           <Line type="monotone" dataKey="long_term" stroke="#f59e0b" name="長期記憶" />
         </LineChart>
       </div>
     );
   };
   ```

---

## 6. Week 14: 統合テスト・デプロイ

### 6.1 実装タスク

#### Week 14-1: E2Eテスト（3日）

**ファイル作成**:
- `frontend/cypress/e2e/auth.cy.ts` (200行)
- `frontend/cypress/e2e/chat.cy.ts` (300行)
- `frontend/cypress/e2e/dashboard.cy.ts` (250行)

**テストケース**（30件）:
- ユーザー登録・ログイン・ログアウト
- チャット送信・受信・ストリーミング
- 記憶検索・削除・統計表示
- レスポンシブデザイン検証

#### Week 14-2: Docker本番環境デプロイ（2日）

**ファイル作成**:
- `frontend/Dockerfile` (30行)
- `docker-compose.yml` 更新 (50行追加)
- `nginx.conf` (100行)

**Dockerfile**:
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml更新**:
```yaml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: llmmultichat3-frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://api:8000
      - VITE_WS_URL=ws://api:8000
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - llmmultichat3-network

  api:
    # ... 既存のAPI設定

networks:
  llmmultichat3-network:
    driver: bridge
```

#### Week 14-3: ドキュメント整備（2日）

**ドキュメント**:
- `docks/Phase4_完了サマリー.md` (500行)
- `frontend/README.md` (300行)
- `docks/フロントエンド開発ガイド.md` (400行)

---

## 7. 技術スタック

### 7.1 フロントエンド

| カテゴリ | 技術 | バージョン | 用途 |
|---------|------|----------|------|
| フレームワーク | React | 18.2.0 | UIライブラリ |
| ビルドツール | Vite | 5.0.0 | 高速ビルド |
| 言語 | TypeScript | 5.3.0 | 型安全性 |
| ルーティング | React Router | 6.20.0 | SPA ルーティング |
| 状態管理 | Redux Toolkit | 2.0.0 | グローバル状態 |
| データフェッチ | React Query | 5.10.0 | サーバー状態管理 |
| HTTP クライアント | Axios | 1.6.0 | API 通信 |
| WebSocket | Socket.io | 4.6.0 | リアルタイム通信 |
| CSS | Tailwind CSS | 3.3.0 | ユーティリティCSS |
| アイコン | Lucide React | 0.292.0 | アイコン |
| Markdown | React Markdown | 9.0.0 | Markdown レンダリング |
| チャート | Recharts | 2.10.0 | データ可視化 |

### 7.2 テスト

| カテゴリ | 技術 | バージョン | 用途 |
|---------|------|----------|------|
| ユニットテスト | Vitest | 1.0.0 | 単体テスト |
| E2Eテスト | Cypress | 13.6.0 | E2Eテスト |
| テストライブラリ | Testing Library | 14.1.0 | コンポーネントテスト |

### 7.3 デプロイ

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| コンテナ | Docker | コンテナ化 |
| オーケストレーション | Docker Compose | マルチコンテナ管理 |
| Webサーバー | Nginx | リバースプロキシ |

---

## 8. アーキテクチャ設計

### 8.1 フォルダ構成

```
frontend/
├── public/           # 静的ファイル
├── src/
│   ├── components/   # Reactコンポーネント
│   │   ├── common/   # 共通コンポーネント
│   │   ├── layout/   # レイアウトコンポーネント
│   │   ├── auth/     # 認証コンポーネント
│   │   ├── chat/     # チャットコンポーネント
│   │   └── dashboard/ # ダッシュボードコンポーネント
│   ├── pages/        # ページコンポーネント
│   ├── services/     # APIサービス
│   ├── store/        # Redux Store
│   ├── hooks/        # カスタムフック
│   ├── types/        # TypeScript型定義
│   ├── utils/        # ユーティリティ関数
│   ├── App.tsx       # ルートコンポーネント
│   └── index.tsx     # エントリーポイント
├── cypress/          # E2Eテスト
├── Dockerfile        # Docker設定
└── package.json      # 依存関係
```

### 8.2 状態管理設計

**Redux Store構成**:
- `authSlice`: ユーザー認証状態
- `chatSlice`: 会話履歴・現在のセッション
- `memorySlice`: 記憶統計・検索結果

**React Query使用箇所**:
- API データフェッチ（キャッシュ・自動更新）
- ページネーション・無限スクロール

### 8.3 ルーティング設計

| パス | コンポーネント | 認証 |
|------|--------------|------|
| `/` | LandingPage | 不要 |
| `/login` | LoginPage | 不要 |
| `/register` | RegisterPage | 不要 |
| `/chat` | ChatPage | 必要 |
| `/dashboard` | DashboardPage | 必要 |
| `/profile` | ProfilePage | 必要 |

---

## 9. UI/UXデザイン

### 9.1 デザインシステム

**カラーパレット**:
- **Primary**: `#0ea5e9` (Sky Blue) - メインアクション
- **Secondary**: `#d946ef` (Fuchsia) - 補助アクション
- **Success**: `#10b981` (Green) - 成功メッセージ
- **Error**: `#ef4444` (Red) - エラーメッセージ
- **Warning**: `#f59e0b` (Amber) - 警告
- **Neutral**: `#6b7280` (Gray) - テキスト

**タイポグラフィ**:
- **見出し**: `font-bold text-2xl-4xl`
- **本文**: `font-normal text-base`
- **キャプション**: `font-light text-sm`

**スペーシング**:
- **xs**: `4px`
- **sm**: `8px`
- **md**: `16px`
- **lg**: `24px`
- **xl**: `32px`

### 9.2 レスポンシブデザイン

**ブレークポイント**:
- **Mobile**: `< 640px`
- **Tablet**: `640px - 1024px`
- **Desktop**: `> 1024px`

**対応デバイス**:
- iPhone (375px × 667px)
- iPad (768px × 1024px)
- Desktop (1920px × 1080px)

### 9.3 アクセシビリティ

- **WCAG 2.1 AA準拠**
- **キーボードナビゲーション対応**
- **ARIA属性適切設定**
- **カラーコントラスト4.5:1以上**

---

## 10. Phase 5以降の展望

### Phase 5: 音声対応・多言語化（Week 15-17）

- **Whisper音声入力**: OpenAI Whisper API統合
- **VOICEVOX音声合成**: 日本語音声合成
- **多言語対応**: 英語・中国語・韓国語
- **i18n**: react-i18next

### Phase 6: 画像生成・RAG（Week 18-20）

- **Stable Diffusion**: 画像生成プラグイン
- **GPT-4V**: 画像理解プラグイン
- **Pinecone/Qdrant**: ベクトルデータベース
- **セマンティック検索**: 長期記憶強化

### Phase 7: モバイルアプリ（Week 21-24）

- **React Native**: iOS/Androidアプリ
- **プッシュ通知**: Firebase Cloud Messaging
- **オフライン対応**: SQLite

---

## 11. Phase 4成功基準

### 11.1 定量目標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| ページロード時間 | < 2秒 | Lighthouse |
| First Contentful Paint | < 1.5秒 | Lighthouse |
| Time to Interactive | < 3秒 | Lighthouse |
| Lighthouse スコア | > 90 | Lighthouse |
| E2Eテスト成功率 | 100% | Cypress |
| バンドルサイズ | < 500KB | Vite Bundle Analyzer |

### 11.2 定性目標

✅ レスポンシブデザイン完全対応  
✅ アクセシビリティ WCAG 2.1 AA準拠  
✅ ダークモード実装  
✅ PWA対応（オフライン動作）  
✅ Docker本番環境デプロイ完了  
✅ Phase 4完了サマリー作成

---

**Phase 4実装計画書 v1.0**  
**作成日**: 2025-11-14  
**ステータス**: ✅ レビュー待ち