-- HSK Mock Platform Database Initialization
-- Version: 1.0
-- Date: 2026-03-19

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- HSK等级配置表
CREATE TABLE IF NOT EXISTS hsk_levels (
    level SMALLINT PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    vocab_count INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    passing_score INTEGER NOT NULL,
    exam_duration INTEGER NOT NULL,
    listening_questions INTEGER NOT NULL,
    reading_questions INTEGER NOT NULL,
    writing_questions INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 初始化HSK 4-5级配置
INSERT INTO hsk_levels (level, name, vocab_count, total_score, passing_score, exam_duration, listening_questions, reading_questions, writing_questions) VALUES
(4, 'HSK4级', 1200, 300, 180, 6000, 45, 40, 10) ON CONFLICT (level) DO NOTHING,
(5, 'HSK5级', 2500, 300, 180, 6900, 45, 45, 8) ON CONFLICT (level) DO NOTHING;

-- 设备表（用户无需注册）
CREATE TABLE IF NOT EXISTS devices (
    uuid VARCHAR(36) PRIMARY KEY,
    nickname VARCHAR(50),
    device_info JSONB,
    native_language VARCHAR(20) DEFAULT 'en',
    target_level SMALLINT,
    is_subscriber BOOLEAN DEFAULT FALSE,
    subscriber_level VARCHAR(20),
    free_exam_remaining SMALLINT DEFAULT 3,
    last_free_reset DATE DEFAULT CURRENT_DATE,
    total_exams INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);

-- 博主表
CREATE TABLE IF NOT EXISTS creators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    youtube_channel_id VARCHAR(50),
    youtube_channel_name VARCHAR(100),
    avatar_url VARCHAR(500),
    invite_code VARCHAR(20) UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    total_exams INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 题目表
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    hsk_level SMALLINT CHECK (hsk_level IN (4, 5)),
    section VARCHAR(20) CHECK (section IN ('listening', 'reading', 'writing')),
    question_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    options JSONB,
    correct_answer JSONB NOT NULL,
    explanation TEXT,
    difficulty SMALLINT DEFAULT 3 CHECK (difficulty BETWEEN 1 AND 5),
    audio_url VARCHAR(500),
    image_url VARCHAR(500),
    tags TEXT[],
    usage_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 试卷模板表
CREATE TABLE IF NOT EXISTS exam_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    hsk_level SMALLINT CHECK (hsk_level IN (4, 5)),
    structure JSONB NOT NULL,
    time_limit INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT TRUE,
    price INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    publish_count INTEGER DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 考试记录表
CREATE TABLE IF NOT EXISTS exam_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_uuid VARCHAR(36) REFERENCES devices(uuid) ON DELETE SET NULL,
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    template_id UUID REFERENCES exam_templates(id) ON DELETE SET NULL,
    questions JSONB,
    answers JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'in_progress',
    section_scores JSONB,
    total_score INTEGER,
    correct_count INTEGER,
    level_result VARCHAR(20),
    time_spent INTEGER,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- 订阅表
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_uuid VARCHAR(36) REFERENCES devices(uuid) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    payment_method VARCHAR(50),
    amount DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 邀请码表
CREATE TABLE IF NOT EXISTS invite_codes (
    code VARCHAR(20) PRIMARY KEY,
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    used_count INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_questions_level ON questions(hsk_level);
CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type);
CREATE INDEX IF NOT EXISTS idx_questions_creator ON questions(creator_id);
CREATE INDEX IF NOT EXISTS idx_templates_creator ON exam_templates(creator_id);
CREATE INDEX IF NOT EXISTS idx_templates_level ON exam_templates(hsk_level);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_device ON exam_sessions(device_uuid);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_template ON exam_sessions(template_id);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_status ON exam_sessions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_device ON subscriptions(device_uuid);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 添加触发器
CREATE TRIGGER update_creators_updated_at BEFORE UPDATE ON creators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_templates_updated_at BEFORE UPDATE ON exam_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 输出初始化完成
SELECT 'Database initialized successfully!' as message;
