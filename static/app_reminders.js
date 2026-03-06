
// ========== 提醒功能 ==========

async function loadReminders() {
    const container = document.getElementById('reminders-list');
    if (!container) return;
    
    container.innerHTML = '<p style="text-align:center;color:#999;">加载中...⏳</p>';
    
    try {
        const data = await apiRequest('/reminders?upcoming_only=true');
        
        if (data.reminders.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#999;">暂无提醒，点击右上角按钮创建</p>';
            return;
        }
        
        container.innerHTML = data.reminders.map(r => {
            const remindTime = new Date(r.remind_at);
            const now = new Date();
            const isOverdue = remindTime < now;
            const timeStr = remindTime.toLocaleString('zh-CN');
            
            return `
                <div class="reminder-item ${r.status} ${isOverdue ? 'overdue' : ''}">
                    <div class="reminder-content">
                        <div class="reminder-title">${escapeHtml(r.title)}</div>
                        ${r.description ? `<div class="reminder-desc">${escapeHtml(r.description)}</div>` : ''}
                        <div class="reminder-meta">
                            <span class="reminder-time ${isOverdue ? 'overdue' : ''}">
                                ${isOverdue ? '⚠️ ' : '📅 '}${timeStr}
                            </span>
                            <span class="reminder-status">${getStatusText(r.status)}</span>
                        </div>
                    </div>
                    <div class="reminder-actions">
                        ${r.status === 'pending' ? `
                            <button onclick="snoozeReminder('${r.id}')" title="推迟10分钟">⏸️</button>
                        ` : ''}
                        <button onclick="dismissReminder('${r.id}')" title="关闭">✓</button>
                        <button onclick="deleteReminder('${r.id}')" title="删除">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('加载提醒失败:', error);
        container.innerHTML = `
            <p style="text-align:center;color:#ef4444;">
                加载失败: ${escapeHtml(error.message || '网络错误')}<br>
                <button onclick="loadReminders()" style="margin-top: 10px; padding: 8px 16px; background: var(--primary-color); color: white; border: none; border-radius: 6px; cursor: pointer;">
                    重试
                </button>
            </p>
        `;
    }
}

function getStatusText(status) {
    const map = {
        'pending': '⏳ 待发送',
        'sent': '✅ 已发送',
        'dismissed': '✓ 已关闭',
        'snoozed': '⏸️ 已推迟'
    };
    return map[status] || status;
}

async function createReminder() {
    const title = document.getElementById('reminder-title').value.trim();
    const desc = document.getElementById('reminder-desc').value.trim();
    const datetime = document.getElementById('reminder-datetime').value;
    const btn = document.querySelector('#reminder-modal .btn-confirm');
    
    if (!title) {
        showToast('请输入提醒标题', 'error');
        return;
    }
    
    if (!datetime) {
        showToast('请选择提醒时间', 'error');
        return;
    }
    
    try {
        btn.disabled = true;
        btn.textContent = '创建中...';
        
        await apiRequest('/reminders', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                description: desc,
                remind_at: new Date(datetime).toISOString(),
                notify_channels: ['in_app']
            })
        });
        
        closeModal('reminder-modal');
        loadReminders();
        loadStats();
        showToast('提醒创建成功！', 'success');
        
        // 清空表单
        document.getElementById('reminder-title').value = '';
        document.getElementById('reminder-desc').value = '';
        document.getElementById('reminder-datetime').value = '';
    } catch (error) {
        console.error('创建提醒失败:', error);
        showToast(error.message || '创建提醒失败', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '创建';
    }
}

async function snoozeReminder(reminderId) {
    try {
        await apiRequest(`/reminders/${reminderId}/snooze`, { method: 'POST' });
        loadReminders();
        showToast('提醒已推迟10分钟', 'success');
    } catch (error) {
        console.error('推迟提醒失败:', error);
        showToast('推迟失败', 'error');
    }
}

async function dismissReminder(reminderId) {
    try {
        await apiRequest(`/reminders/${reminderId}/dismiss`, { method: 'POST' });
        loadReminders();
        showToast('提醒已关闭', 'success');
    } catch (error) {
        console.error('关闭提醒失败:', error);
        showToast('关闭失败', 'error');
    }
}

async function deleteReminder(reminderId) {
    if (!confirm('确定要删除这个提醒吗？')) return;
    
    try {
        await apiRequest(`/reminders/${reminderId}`, { method: 'DELETE' });
        loadReminders();
        loadStats();
        showToast('提醒已删除', 'success');
    } catch (error) {
        console.error('删除提醒失败:', error);
        showToast('删除失败', 'error');
    }
}
