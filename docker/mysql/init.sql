-- ============================================
-- MySQL 初始化脚本
-- 数据库: personal_assistant
-- 字符集: utf8mb4
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS personal_assistant
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE personal_assistant;

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login TIMESTAMP NULL COMMENT '最后登录时间',
    
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================
-- 2. 用户画像表 (user_profiles)
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '画像ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    display_name VARCHAR(100) COMMENT '显示名称',
    preferred_language VARCHAR(10) DEFAULT 'zh' COMMENT '偏好语言',
    communication_style VARCHAR(20) DEFAULT 'concise' COMMENT '沟通风格',
    tech_background JSON COMMENT '技术背景标签',
    common_tasks JSON COMMENT '常用任务',
    active_hours JSON COMMENT '活跃时段',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai' COMMENT '时区',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户画像表';

-- ============================================
-- 3. 会话表 (sessions)
-- ============================================
CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    title VARCHAR(200) COMMENT '会话标题',
    status ENUM('active', 'paused', 'closed') DEFAULT 'active' COMMENT '状态',
    context_summary TEXT COMMENT '上下文摘要',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后活跃',
    ended_at TIMESTAMP NULL COMMENT '结束时间',
    metadata JSON COMMENT '扩展元数据',
    
    UNIQUE KEY uk_session_id (session_id),
    KEY idx_user_sessions (user_id, status, last_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表';

-- ============================================
-- 4. 消息表 (messages) - 短期记忆
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    session_id BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    message_uuid VARCHAR(64) NOT NULL COMMENT '消息UUID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    content TEXT NOT NULL COMMENT '内容',
    tokens_used INT UNSIGNED DEFAULT 0 COMMENT '使用Token数',
    latency_ms INT UNSIGNED COMMENT '响应延迟(ms)',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_message_uuid (message_uuid),
    KEY idx_session_time (session_id, timestamp),
    KEY idx_user_time (user_id, timestamp),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- ============================================
-- 5. 长期记忆表 (memories)
-- ============================================
CREATE TABLE IF NOT EXISTS memories (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记忆ID',
    memory_id VARCHAR(64) NOT NULL COMMENT '记忆标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    content TEXT NOT NULL COMMENT '记忆内容',
    category ENUM('fact', 'event', 'preference', 'task', 'note') 
        DEFAULT 'fact' COMMENT '类别',
    importance TINYINT UNSIGNED DEFAULT 3 COMMENT '重要程度(1-5)',
    embedding_id VARCHAR(128) COMMENT '向量存储ID(ChromaDB)',
    source_session_id BIGINT UNSIGNED COMMENT '来源会话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_accessed TIMESTAMP NULL COMMENT '最后访问',
    access_count INT UNSIGNED DEFAULT 0 COMMENT '访问次数',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_memory_id (memory_id),
    KEY idx_user_category (user_id, category),
    KEY idx_user_importance (user_id, importance),
    KEY idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='长期记忆表';

-- ============================================
-- 6. 任务表 (tasks)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    parent_task_id BIGINT UNSIGNED COMMENT '父任务ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    description TEXT COMMENT '描述',
    status ENUM('pending', 'in_progress', 'completed', 'cancelled', 'failed') 
        DEFAULT 'pending' COMMENT '状态',
    priority TINYINT UNSIGNED DEFAULT 3 COMMENT '优先级(1-5)',
    tags JSON COMMENT '标签',
    due_date TIMESTAMP NULL COMMENT '截止日期',
    remind_at TIMESTAMP NULL COMMENT '提醒时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_task_id (task_id),
    KEY idx_user_status (user_id, status),
    KEY idx_user_priority (user_id, priority),
    KEY idx_due_date (due_date),
    KEY idx_remind_at (remind_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务表';

-- ============================================
-- 7. 对话摘要表 (conversation_summaries)
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '摘要ID',
    session_id BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    summary_content TEXT NOT NULL COMMENT '摘要内容',
    summary_level TINYINT DEFAULT 2 COMMENT '摘要级别(1-3)',
    message_count INT UNSIGNED DEFAULT 0 COMMENT '包含消息数',
    start_time TIMESTAMP NOT NULL COMMENT '起始时间',
    end_time TIMESTAMP NOT NULL COMMENT '结束时间',
    key_points JSON COMMENT '关键要点',
    extracted_memories JSON COMMENT '提取的记忆ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    KEY idx_session_level (session_id, summary_level),
    KEY idx_user_time (user_id, start_time),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话摘要表';

-- ============================================
-- 8. 系统配置表 (system_configs)
-- ============================================
CREATE TABLE IF NOT EXISTS system_configs (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '描述',
    is_encrypted BOOLEAN DEFAULT FALSE COMMENT '是否加密',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('app_name', 'Personal Assistant', '应用名称'),
('max_session_age_hours', '24', '会话最大存活时间(小时)'),
('default_language', 'zh', '默认语言'),
('memory_consolidation_interval', '86400', '记忆整合间隔(秒)');

-- 创建演示用户（用于测试）
-- 密码: test123 (bcrypt hashed)
INSERT INTO users (username, email, password_hash, is_active) VALUES
('demo', 'demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IyK', TRUE);

INSERT INTO user_profiles (user_id, display_name, preferred_language, communication_style) 
SELECT id, '演示用户', 'zh', 'concise' FROM users WHERE username = 'demo';
