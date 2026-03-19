"""
HSK Mock Platform - Exam Service
考试管理、答题、评分
"""

import os
import uuid
import json
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, SmallInteger, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import NullPool

# ============== 配置 ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hskuser:hsk123456@localhost:5432/hskdb")

# ============== 数据库模型 ==============
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True))
    hsk_level = Column(SmallInteger)
    section = Column(String(20))
    question_type = Column(String(50))
    content = Column(JSONB)
    options = Column(JSONB)
    correct_answer = Column(JSONB, nullable=False)
    explanation = Column(Text)
    difficulty = Column(SmallInteger, default=3)
    audio_url = Column(String(500))
    image_url = Column(String(500))
    tags = Column(JSONB)
    is_active = Column(Boolean, default=True)


class ExamTemplate(Base):
    __tablename__ = "exam_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True))
    name = Column(String(100))
    description = Column(Text)
    hsk_level = Column(SmallInteger)
    structure = Column(JSONB)
    time_limit = Column(Integer)
    total_questions = Column(Integer)
    total_score = Column(Integer)
    is_public = Column(Boolean, default=True)
    price = Column(Integer, default=0)
    status = Column(String(20), default="draft")


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_uuid = Column(String(36))
    creator_id = Column(UUID(as_uuid=True))
    template_id = Column(UUID(as_uuid=True))
    questions = Column(JSONB)
    answers = Column(JSONB, default={})
    status = Column(String(20), default="in_progress")
    section_scores = Column(JSONB)
    total_score = Column(Integer)
    correct_count = Column(Integer)
    level_result = Column(String(20))
    time_spent = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)


# ============== Pydantic模型 ==============
class ExamStartRequest(BaseModel):
    template_id: str
    device_uuid: str


class ExamStartResponse(BaseModel):
    session_id: str
    started_at: datetime
    expires_at: datetime
    time_limit: int
    sections: List[dict]
    questions: List[dict]


class AnswerSubmit(BaseModel):
    question_id: str
    answer: Any
    time_spent: Optional[int] = 0


class ProgressUpdate(BaseModel):
    answers: Dict[str, Any]
    current_section: Optional[str] = None
    current_question_index: Optional[int] = None


class ExamSubmitResponse(BaseModel):
    session_id: str
    status: str
    total_score: Optional[int]
    correct_count: Optional[int]
    level_result: Optional[str]
    section_scores: Optional[dict]


class ExamResultResponse(BaseModel):
    session_id: str
    total_score: int
    max_score: int
    passing_score: int
    passed: bool
    level_result: str
    section_scores: dict
    correct_count: int
    total_questions: int
    weak_points: List[dict]


# ============== 依赖 ==============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== 辅助函数 ==============
def get_hsk_config(level: int) -> dict:
    """HSK等级配置"""
    configs = {
        4: {
            "name": "HSK4级",
            "total_score": 300,
            "passing_score": 180,
            "sections": {
                "listening": {"questions": 45, "score_per": 2},
                "reading": {"questions": 40, "score_per": 2.5},
                "writing": {"questions": 10, "score_per": 10}
            }
        },
        5: {
            "name": "HSK5级",
            "total_score": 300,
            "passing_score": 180,
            "sections": {
                "listening": {"questions": 45, "score_per": 2},
                "reading": {"questions": 45, "score_per": 2},
                "writing": {"questions": 8, "score_per": 12.5}
            }
        }
    }
    return configs.get(level, configs[4])


def generate_questions_for_exam(db: Session, template: ExamTemplate, device_uuid: str) -> List[dict]:
    """根据试卷模板生成考试题目"""
    structure = template.structure
    questions = []
    
    for section_name, section_config in structure.get("sections", {}).items():
        question_types = section_config.get("question_types", {})
        
        for qtype, count in question_types.items():
            # 从题库抽取题目
            pool = db.query(Question).filter(
                Question.hsk_level == template.hsk_level,
                Question.section == section_name,
                Question.question_type == qtype,
                Question.is_active == True
            ).all()
            
            if len(pool) >= count:
                selected = random.sample(pool, count)
            else:
                selected = pool
                # 如果题库不足，重复使用
            
            for q in selected:
                # 选项随机排序
                options = q.options.copy() if q.options else []
                if options and isinstance(options, list):
                    random.shuffle(options)
                
                questions.append({
                    "id": str(q.id),
                    "section": q.section,
                    "question_type": q.question_type,
                    "content": q.content,
                    "options": options,
                    "score": section_config.get("score_per", 1),
                    "difficulty": q.difficulty
                })
    
    random.shuffle(questions)
    return questions


def grade_exam(questions: List[dict], answers: dict) -> dict:
    """评分"""
    total_score = 0
    total_correct = 0
    section_scores = defaultdict(lambda: {"score": 0, "correct": 0, "total": 0})
    
    for q in questions:
        qid = q["id"]
        correct_ans = None
        user_ans = answers.get(qid, {}).get("answer")
        
        # 从题目内容中获取正确答案
        if isinstance(q.get("content"), dict):
            correct_ans = q["content"].get("correct_answer")
        elif isinstance(q.get("correct_answer"), dict):
            correct_ans = q["correct_answer"]
        
        # 评分
        is_correct = False
        if user_ans is not None and correct_ans is not None:
            if isinstance(correct_ans, dict):
                is_correct = user_ans == correct_ans.get("answer") or user_ans == correct_ans.get("key")
            else:
                is_correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
        
        if is_correct:
            total_score += q.get("score", 1)
            total_correct += 1
            section_scores[q["section"]]["correct"] += 1
        
        section_scores[q["section"]]["total"] += 1
        section_scores[q["section"]]["score"] += q.get("score", 1) if is_correct else 0
    
    # 转换为普通dict
    section_scores = dict(section_scores)
    
    # 判定等级
    level_result = "不合格"
    if total_score >= 270:
        level_result = "优秀"
    elif total_score >= 240:
        level_result = "良好"
    elif total_score >= 180:
        level_result = "合格"
    
    return {
        "total_score": total_score,
        "correct_count": total_correct,
        "section_scores": section_scores,
        "level_result": level_result
    }


# ============== 应用 ==============
app = FastAPI(title="HSK Exam Service", version="1.0.0")


# ============== 考试API ==============
@app.post("/exam/start", response_model=ExamStartResponse)
def start_exam(request: ExamStartRequest, db: Session = Depends(get_db)):
    """开始考试"""
    # 获取试卷模板
    template = db.query(ExamTemplate).filter(
        ExamTemplate.id == request.template_id,
        ExamTemplate.status == "published"
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Exam template not found")
    
    # 生成题目
    questions = generate_questions_for_exam(db, template, request.device_uuid)
    
    if not questions:
        raise HTTPException(status_code=400, detail="No questions available for this template")
    
    # 创建考试记录
    session = ExamSession(
        device_uuid=request.device_uuid,
        creator_id=template.creator_id,
        template_id=template.id,
        questions=questions,
        answers={},
        status="in_progress",
        started_at=datetime.utcnow()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 计算截止时间
    expires_at = session.started_at + timedelta(seconds=template.time_limit)
    
    # 按部分组织返回
    sections = []
    for section_name in ["listening", "reading", "writing"]:
        section_questions = [q for q in questions if q["section"] == section_name]
        if section_questions:
            sections.append({
                "name": section_name,
                "question_count": len(section_questions),
                "question_ids": [q["id"] for q in section_questions]
            })
    
    return ExamStartResponse(
        session_id=str(session.id),
        started_at=session.started_at,
        expires_at=expires_at,
        time_limit=template.time_limit,
        sections=sections,
        questions=questions
    )


@app.get("/exam/{session_id}")
def get_exam_session(session_id: str, db: Session = Depends(get_db)):
    """获取考试详情（不含答案）"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    # 返回不含正确答案的题目
    questions = session.questions or []
    safe_questions = []
    for q in questions:
        safe_q = {
            "id": q["id"],
            "section": q["section"],
            "question_type": q["question_type"],
            "content": q["content"],
            "options": q.get("options"),
            "score": q.get("score")
        }
        safe_questions.append(safe_q)
    
    return {
        "session_id": str(session.id),
        "status": session.status,
        "started_at": session.started_at,
        "questions": safe_questions
    }


@app.put("/exam/{session_id}/progress")
def update_progress(session_id: str, progress: ProgressUpdate, db: Session = Depends(get_db)):
    """更新答题进度"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam already submitted")
    
    # 合并答案
    current_answers = session.answers or {}
    current_answers.update(progress.answers)
    session.answers = current_answers
    
    db.commit()
    
    return {"success": True, "answered_count": len(current_answers)}


@app.post("/exam/{session_id}/submit", response_model=ExamSubmitResponse)
def submit_exam(session_id: str, db: Session = Depends(get_db)):
    """提交试卷"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam already submitted")
    
    # 计算用时
    session.submitted_at = datetime.utcnow()
    session.time_spent = int((session.submitted_at - session.started_at).total_seconds())
    
    # 评分
    questions = session.questions or []
    answers = session.answers or {}
    result = grade_exam(questions, answers)
    
    session.total_score = result["total_score"]
    session.correct_count = result["correct_count"]
    session.section_scores = result["section_scores"]
    session.level_result = result["level_result"]
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    
    db.commit()
    
    return ExamSubmitResponse(
        session_id=str(session.id),
        status="completed",
        total_score=session.total_score,
        correct_count=session.correct_count,
        level_result=session.level_result,
        section_scores=session.section_scores
    )


@app.get("/exam/{session_id}/result", response_model=ExamResultResponse)
def get_exam_result(session_id: str, db: Session = Depends(get_db)):
    """获取考试成绩"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Exam not completed")
    
    # 获取HSK配置
    template = db.query(ExamTemplate).filter(ExamTemplate.id == session.template_id).first()
    config = get_hsk_config(template.hsk_level if template else 4)
    
    # 计算弱项（简单示例：随机）
    weak_points = [
        {"topic": "结果补语", "correct_rate": 0.4},
        {"topic": "把字句", "correct_rate": 0.5}
    ]
    
    return ExamResultResponse(
        session_id=str(session.id),
        total_score=session.total_score or 0,
        max_score=config["total_score"],
        passing_score=config["passing_score"],
        passed=(session.total_score or 0) >= config["passing_score"],
        level_result=session.level_result or "不合格",
        section_scores=session.section_scores or {},
        correct_count=session.correct_count or 0,
        total_questions=len(session.questions or []),
        weak_points=weak_points
    )


# ============== 历史记录API ==============
@app.get("/exam/history/{device_uuid}")
def get_exam_history(device_uuid: str, db: Session = Depends(get_db)):
    """获取考试历史"""
    sessions = db.query(ExamSession).filter(
        ExamSession.device_uuid == device_uuid,
        ExamSession.status == "completed"
    ).order_by(ExamSession.completed_at.desc()).limit(20).all()
    
    return {
        "data": [
            {
                "session_id": str(s.id),
                "total_score": s.total_score,
                "level_result": s.level_result,
                "completed_at": s.completed_at,
                "time_spent": s.time_spent
            }
            for s in sessions
        ]
    }


# ============== 健康检查 ==============
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "exam-service"}


# ============== 启动 ==============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
