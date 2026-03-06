/**
 * 模型管理 - LLM 切换功能
 */

// 当前模型信息
let currentModel = null;
let availableModels = [];

/**
 * 加载可用模型列表
 */
async function loadModels() {
    try {
        const data = await apiRequest('/models');
        availableModels = data.models || [];
        currentModel = data.current_model;
        
        // 更新 UI
        renderModelSelector();
        updateCurrentModelDisplay();
        
        return data;
    } catch (error) {
        console.error('加载模型列表失败:', error);
        return null;
    }
}

/**
 * 获取当前模型信息
 */
async function getCurrentModel() {
    try {
        const data = await apiRequest('/models/current');
        currentModel = data;
        updateCurrentModelDisplay();
        return data;
    } catch (error) {
        console.error('获取当前模型失败:', error);
        return null;
    }
}

/**
 * 切换模型
 */
async function selectModel(modelId) {
    try {
        showToast('正在切换模型...', 'info');
        
        const data = await apiRequest('/models/select', {
            method: 'POST',
            body: JSON.stringify({ model_id: modelId })
        });
        
        currentModel = modelId;
        updateCurrentModelDisplay();
        
        showToast(`已切换到 ${data.model.name}`, 'success');
        closeModal('model-modal');
        
        return data;
    } catch (error) {
        console.error('切换模型失败:', error);
        showToast(error.message || '切换模型失败', 'error');
        return null;
    }
}

/**
 * 渲染模型选择器
 */
function renderModelSelector() {
    const container = document.getElementById('model-list');
    if (!container) return;
    
    if (availableModels.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;">暂无可用模型</p>';
        return;
    }
    
    // 按提供商分组
    const byProvider = {};
    availableModels.forEach(model => {
        if (!byProvider[model.provider]) {
            byProvider[model.provider] = [];
        }
        byProvider[model.provider].push(model);
    });
    
    // 提供商显示名称
    const providerNames = {
        'openai': '🟢 OpenAI',
        'anthropic': '🟣 Anthropic',
        'moonshot': '🔴 Moonshot (Kimi)',
        'deepseek': '🔵 DeepSeek',
        'qwen': '🟠 通义千问',
        'siliconflow': '⚪ SiliconFlow'
    };
    
    let html = '';
    for (const [provider, models] of Object.entries(byProvider)) {
        const providerName = providerNames[provider] || provider;
        html += `
            <div class="model-provider">
                <div class="provider-header">${providerName}</div>
                <div class="model-list">
                    ${models.map(model => `
                        <div class="model-item ${model.id === currentModel ? 'selected' : ''} ${!model.is_available ? 'disabled' : ''}" 
                             onclick="${model.is_available ? `selectModel('${model.id}')` : ''}">
                            <div class="model-info">
                                <div class="model-name">${model.name}</div>
                                <div class="model-desc">${model.description}</div>
                                <div class="model-meta">
                                    <span class="model-tokens">Max: ${formatNumber(model.max_tokens)} tokens</span>
                                    ${model.supports_tools ? '<span class="model-badge">支持工具</span>' : ''}
                                    ${model.supports_streaming ? '<span class="model-badge">支持流式</span>' : ''}
                                </div>
                            </div>
                            ${model.id === currentModel ? '<span class="model-check">✓</span>' : ''}
                            ${!model.has_api_key ? '<span class="model-warning" title="未配置 API Key">⚠️</span>' : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * 更新当前模型显示
 */
function updateCurrentModelDisplay() {
    const display = document.getElementById('current-model-display');
    if (!display) return;
    
    if (!currentModel) {
        display.innerHTML = '<span class="model-tag">默认模型</span>';
        return;
    }
    
    const model = availableModels.find(m => m.id === currentModel);
    if (model) {
        display.innerHTML = `
            <span class="model-tag active" onclick="openModal('model-modal'); loadModels();" title="点击切换模型">
                ${model.name}
                <span class="model-arrow">▼</span>
            </span>
        `;
    } else {
        display.innerHTML = `
            <span class="model-tag active" onclick="openModal('model-modal'); loadModels();" title="点击切换模型">
                ${currentModel}
                <span class="model-arrow">▼</span>
            </span>
        `;
    }
}

/**
 * 格式化数字
 */
function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(0) + '万';
    }
    return num.toLocaleString();
}

/**
 * 对比模型
 */
async function compareModels(query, modelIds) {
    if (!query || modelIds.length === 0) {
        showToast('请输入查询内容并选择模型', 'error');
        return null;
    }
    
    try {
        showToast('正在对比模型...', 'info');
        
        const data = await apiRequest('/models/compare', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                model_ids: modelIds
            })
        });
        
        renderComparisonResults(data.comparisons);
        return data;
    } catch (error) {
        console.error('模型对比失败:', error);
        showToast(error.message || '对比失败', 'error');
        return null;
    }
}

/**
 * 渲染对比结果
 */
function renderComparisonResults(comparisons) {
    const container = document.getElementById('model-comparison-results');
    if (!container) return;
    
    if (!comparisons || comparisons.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;">暂无对比结果</p>';
        return;
    }
    
    container.innerHTML = comparisons.map(result => `
        <div class="comparison-item ${result.success ? '' : 'error'}">
            <div class="comparison-header">
                <span class="comparison-model">${result.model}</span>
                ${result.success ? `
                    <span class="comparison-meta">
                        <span class="comparison-latency">⏱️ ${result.latency_ms}ms</span>
                        <span class="comparison-tokens">📝 ${result.tokens} tokens</span>
                    </span>
                ` : '<span class="comparison-error">❌ 失败</span>'}
            </div>
            <div class="comparison-content">
                ${result.success ? escapeHtml(result.response) : escapeHtml(result.error)}
            </div>
        </div>
    `).join('');
}

// 初始化时加载模型信息
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        loadModels();
    }
});
