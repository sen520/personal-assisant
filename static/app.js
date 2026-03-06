/**
 * 个人助理前端应用
 */

// 全局状态
const state = {
    token: localStorage.getItem('token'),
    userId: localStorage.getItem('userId'),
    username: localStorage.getItem('username'),
    currentSession: null,
    currentPage: 'chat'
};

// API 基础 URL
const API_BASE = '/api';

// 请求配置
const REQUEST_CONFIG = {
    maxRetries: 3,
    retryDelay: 1000,  // 初始延迟 1秒
    timeout: 30000     // 30秒超时
};

// ========== 工具函数 ==========

/**
 * 带重试的 API 请求
 * @param {string} url - 请求路径
 * @param {Object} options - 请求选项
 * @param {number} retries - 剩余重试次数
 */
async function apiRequest(url, options = {}, retries = REQUEST_CONFIG.maxRetries) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (state.token) {
        headers['Authorization'] = state.token;
    }
    
    // 创建 AbortController 用于超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_CONFIG.timeout);
    
    try {
        const response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            // 处理特定状态码
            if (response.status === 429) {
                throw new Error('请求太频繁，请稍后再试');
            } else if (response.status === 401) {
                // Token 过期，清除登录状态
                logout();
                throw new Error('登录已过期，请重新登录');
            }
            
            const error = await response.text();
            throw new Error(error);
        }
        
        return response.json();
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        // 网络错误或超时，且还有重试次数
        if (retries > 0 && (error.name === 'TypeError' || error.name === 'AbortError')) {
            console.warn(`请求失败，${retries}秒后重试...`, error);
            await sleep(REQUEST_CONFIG.retryDelay * (REQUEST_CONFIG.maxRetries - retries + 1));
            return apiRequest(url, options, retries - 1);
        }
        
        throw error;
    }
}

/**
 * 延迟函数
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.textContent = '';
            element.style.display = 'none';
        }, 5000);
    }
}

/**
 * 显示全局提示
 */
function showToast(message, type = 'error') {
    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        color: white;
        font-size: 14px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        background: ${type === 'error' ? '#ef4444' : '#10b981'};
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 认证相关 ==========

async function login(username, password) {
    const btn = document.querySelector('#login-form button[type="submit"]');
    const originalText = btn.textContent;
    
    try {
        btn.disabled = true;
        btn.textContent = '登录中...';
        
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        saveAuth(data);
        showToast('登录成功！', 'success');
        showApp();
    } catch (error) {
        console.error('登录失败:', error);
        showToast(error.message || '登录失败，请检查用户名和密码', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

async function register(username, password, email) {
    const btn = document.querySelector('#register-form button[type="submit"]');
    const originalText = btn.textContent;
    
    try {
        btn.disabled = true;
        btn.textContent = '注册中...';
        
        const data = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, email })
        });
        
        saveAuth(data);
        showToast('注册成功！', 'success');
        showApp();
    } catch (error) {
        console.error('注册失败:', error);
        showToast(error.message || '注册失败，用户名可能已被使用', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function saveAuth(data) {
    state.token = data.access_token;
    state.userId = data.user_id;
    state.username = data.username;
    
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('userId', data.user_id);
    localStorage.setItem('username', data.username);
}

function logout() {
    localStorage.clear();
    state.token = null;
    state.userId = null;
    state.username = null;
    showAuth();
}

// ========== 页面切换 ==========

function showAuth() {
    document.getElementById('auth-page').classList.add('active');
    document.getElementById('app-page').classList.remove('active');
}

function showApp() {
    document.getElementById('auth-page').classList.remove('active');
    document.getElementById('app-page').classList.add('active');
    
    document.getElementById('user-name').textContent = state.username;
    
    // 加载初始数据
    loadSessions();
}

function showPage(pageName) {
    // 隐藏所有页面
    document.querySelectorAll('.content-page').forEach(page => {
        page.classList.remove('active');
    });
    
    // 显示目标页面
    document.getElementById(`${pageName}-page`).classList.add('active');
    
    // 更新导航
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });
    
    state.currentPage = pageName;
    
    // 加载页面数据
    if (pageName === 'tasks') loadTasks();
    if (pageName === 'memories') loadMemories();
    if (pageName === 'stats') loadStats();
}

// ========== 对话功能 ==========

async function loadSessions() {
    try {
        const data = await apiRequest('/sessions');
        const container = document.getElementById('sessions-container');
        
        if (data.sessions.length === 0) {
            container.innerHTML = '<div class="session-item" style="color: #999; font-size: 13px;">暂无会话</div>';
            return;
        }
        
        container.innerHTML = data.sessions.map(session => `
            <div class="session-item ${session.id === state.currentSession ? 'active' : ''}" 
                 data-id="${session.id}"
                 onclick="selectSession('${session.id}')">
                ${escapeHtml(session.title)}
            </div>
        `).join('');
    } catch (error) {
        console.error('加载会话失败:', error);
        const container = document.getElementById('sessions-container');
        container.innerHTML = '<div class="session-item" style="color: #ef4444; font-size: 13px;">加载失败，点击重试</div>';
        container.onclick = loadSessions;
    }
}

async function createSession() {
    try {
        const data = await apiRequest('/sessions', {
            method: 'POST',
            body: JSON.stringify({ title: '新对话' })
        });
        
        state.currentSession = data.id;
        await loadSessions();
        clearChat();
    } catch (error) {
        console.error('创建会话失败:', error);
    }
}

function selectSession(sessionId) {
    state.currentSession = sessionId;
    loadMessages(sessionId);
    
    // 更新活跃状态
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.id === sessionId) {
            item.classList.add('active');
        }
    });
}

function clearChat() {
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML = `
        <div class="welcome-message">
            <h2>👋 你好！</h2>
            <p>我是你的个人助理，可以帮你：</p>
            <ul>
                <li>💬 聊天对话</li>
                <li>🧠 记住重要信息</li>
                <li>📋 管理任务</li>
                <li>🔍 搜索信息</li>
            </ul>
        </div>
    `;
}

async function loadMessages(sessionId) {
    try {
        const data = await apiRequest(`/sessions/${sessionId}/messages`);
        const messagesDiv = document.getElementById('chat-messages');
        
        messagesDiv.innerHTML = data.messages.map(msg => `
            <div class="message ${msg.role}">
                <div class="message-avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
                <div class="message-content">${escapeHtml(msg.content)}</div>
            </div>
        `).join('');
        
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        console.error('加载消息失败:', error);
    }
}


function addMessageToChat(role, content) {
    const messagesDiv = document.getElementById('chat-messages');
    const id = 'msg-' + Date.now();
    
    const messageHtml = `
        <div id="${id}" class="message ${role}">
            <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <div class="message-content">${escapeHtml(content)}</div>
        </div>
    `;
    
    // 移除欢迎消息
    const welcomeMsg = messagesDiv.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();
    
    messagesDiv.insertAdjacentHTML('beforeend', messageHtml);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    return id;
}

function replaceMessage(id, content) {
    const msg = document.getElementById(id);
    if (msg) {
        msg.querySelector('.message-content').innerHTML = escapeHtml(content);
    }
}

// ========== 任务管理 ==========

async function loadTasks() {
    const container = document.getElementById('tasks-list');
    container.innerHTML = '<p style="text-align:center;color:#999;">加载中...⏳</p>';
    
    try {
        const data = await apiRequest('/tasks');
        
        if (data.tasks.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#999;">暂无任务，点击右上角按钮创建</p>';
            return;
        }
        
        container.innerHTML = data.tasks.map(task => `
            <div class="task-item ${task.status === 'completed' ? 'completed' : ''}">
                <input type="checkbox" class="task-checkbox" 
                       ${task.status === 'completed' ? 'checked' : ''}
                       onchange="toggleTask('${task.id}', this.checked)">
                <div class="task-content">
                    <div class="task-title">${escapeHtml(task.title)}</div>
                    ${task.description ? `<div class="task-desc">${escapeHtml(task.description)}</div>
                    ` : ''}
                    <div class="task-meta">
                        <span class="priority-${task.priority <= 2 ? 'high' : task.priority <= 3 ? 'medium' : 'low'}">
                            ${'🔴🟡🟢'.split('')[task.priority <= 2 ? 0 : task.priority <= 3 ? 1 : 2]}
                        </span>
                        <span>${new Date(task.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <button onclick="deleteTask('${task.id}')" style="background:none;border:none;cursor:pointer;">🗑️</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载任务失败:', error);
        container.innerHTML = `
            <p style="text-align:center;color:#ef4444;">
                加载失败: ${escapeHtml(error.message || '网络错误')}<br>
                <button onclick="loadTasks()" style="margin-top: 10px; padding: 8px 16px; background: var(--primary-color); color: white; border: none; border-radius: 6px; cursor: pointer;">
                    重试
                </button>
            </p>
        `;
    }
}

async function createTask() {
    const title = document.getElementById('task-title').value.trim();
    const desc = document.getElementById('task-desc').value.trim();
    const priority = parseInt(document.getElementById('task-priority').value);
    const btn = document.querySelector('#task-modal .btn-confirm');
    
    if (!title) {
        showToast('请输入任务标题', 'error');
        return;
    }
    
    try {
        btn.disabled = true;
        btn.textContent = '创建中...';
        
        await apiRequest('/tasks', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                description: desc,
                priority: priority
            })
        });
        
        closeModal('task-modal');
        loadTasks();
        showToast('任务创建成功！', 'success');
        
        // 清空表单
        document.getElementById('task-title').value = '';
        document.getElementById('task-desc').value = '';
    } catch (error) {
        console.error('创建任务失败:', error);
        showToast(error.message || '创建任务失败', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '创建';
    }
}
        document.getElementById('task-title').value = '';
        document.getElementById('task-desc').value = '';
    } catch (error) {
        console.error('创建任务失败:', error);
    }
}

async function toggleTask(taskId, completed) {
    try {
        await apiRequest(`/tasks/${taskId}?status=${completed ? 'completed' : 'pending'}`, {
            method: 'PATCH'
        });
        loadTasks();
    } catch (error) {
        console.error('更新任务失败:', error);
    }
}

async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) return;
    
    try {
        await apiRequest(`/tasks/${taskId}`, {
            method: 'DELETE'
        });
        loadTasks();
    } catch (error) {
        console.error('删除任务失败:', error);
    }
}

// ========== 记忆管理 ==========

async function loadMemories() {
    try {
        const data = await apiRequest('/memories');
        const container = document.getElementById('memories-list');
        
        if (data.memories.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#999;">暂无记忆</p>';
            return;
        }
        
        const categoryLabels = {
            'general': '📝 一般',
            'preference': '❤️ 偏好',
            'fact': '📚 事实',
            'task': '✅ 任务'
        };
        
        container.innerHTML = data.memories.map(memory => `
            <div class="memory-item">
                <div class="memory-header">
                    <span class="memory-category">${categoryLabels[memory.category] || '📝 一般'}</span>
                    <button onclick="deleteMemory('${memory.id}')" style="background:none;border:none;cursor:pointer;">🗑️</button>
                </div>
                <div class="memory-content">${escapeHtml(memory.content)}</div>
                <div class="memory-footer">
                    <span>重要性: ${'⭐'.repeat(memory.importance)}</span>
                    <span>${new Date(memory.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载记忆失败:', error);
    }
}

async function createMemory() {
    const content = document.getElementById('memory-content').value.trim();
    const category = document.getElementById('memory-category').value;
    
    if (!content) return;
    
    try {
        await apiRequest('/memories', {
            method: 'POST',
            body: JSON.stringify({
                content: content,
                category: category,
                importance: 3
            })
        });
        
        closeModal('memory-modal');
        loadMemories();
        
        // 清空表单
        document.getElementById('memory-content').value = '';
    } catch (error) {
        console.error('创建记忆失败:', error);
    }
}

async function deleteMemory(memoryId) {
    if (!confirm('确定要删除这条记忆吗？')) return;
    
    try {
        await apiRequest(`/memories/${memoryId}`, {
            method: 'DELETE'
        });
        loadMemories();
    } catch (error) {
        console.error('删除记忆失败:', error);
    }
}

// ========== 统计 ==========

async function loadStats() {
    try {
        const data = await apiRequest('/stats');
        const container = document.getElementById('stats-container');
        
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${data.sessions}</div>
                <div class="stat-label">对话会话</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.memories}</div>
                <div class="stat-label">记忆条目</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.tasks.total}</div>
                <div class="stat-label">总任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.tasks.completed}</div>
                <div class="stat-label">已完成任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.tasks.pending}</div>
                <div class="stat-label">待办任务</div>
            </div>
        `;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// ========== 弹窗控制 ==========

function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// ========== 工具函数 ==========

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== 事件绑定 ==========

document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已登录
    if (state.token) {
        showApp();
    } else {
        showAuth();
    }
    
    // 登录/注册标签切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const tab = btn.dataset.tab;
            if (tab === 'login') {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('register-form').classList.add('hidden');
            } else {
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('register-form').classList.remove('hidden');
            }
        });
    });
    
    // 登录表单
    document.getElementById('login-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        login(username, password);
    });
    
    // 注册表单
    document.getElementById('register-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        const email = document.getElementById('register-email').value;
        register(username, password, email);
    });
    
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // 导航菜单
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            showPage(item.dataset.page);
        });
    });
    
    // 新对话
    document.getElementById('new-chat-btn').addEventListener('click', createSession);
    
    // 发送消息
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 任务弹窗
    document.getElementById('new-task-btn').addEventListener('click', () => {
        openModal('task-modal');
    });
    document.querySelector('#task-modal .btn-cancel').addEventListener('click', () => {
        closeModal('task-modal');
    });
    document.querySelector('#task-modal .btn-confirm').addEventListener('click', createTask);
    
    // 记忆弹窗
    document.getElementById('new-memory-btn').addEventListener('click', () => {
        openModal('memory-modal');
    });
    document.querySelector('#memory-modal .btn-cancel').addEventListener('click', () => {
        closeModal('memory-modal');
    });
    document.querySelector('#memory-modal .btn-confirm').addEventListener('click', createMemory);
    
    // 点击弹窗外部关闭
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
});
