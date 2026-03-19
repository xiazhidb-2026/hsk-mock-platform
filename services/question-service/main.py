"""
HSK Mock Platform - Question Service
题库管理、试卷模板
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, SmallInteger, Boolean, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    correct_answer = Column(JSONB)
    explanation = Column(Text)
    difficulty = Column(SmallInteger, default=3)
    audio_url = Column(String(500))
    image_url = Column(String(500))
    tags = Column(JSONB)
    usage_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


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
    publish_count = Column(Integer, default=0)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============== Pydantic模型 ==============
class QuestionCreate(BaseModel):
    hsk_level: int
    section: str
    question_type: str
    content: dict
    options: Optional[list] = None
    correct_answer: dict
    explanation: Optional[str] = None
    difficulty: int = 3
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[list] = None


class QuestionResponse(BaseModel):
    id: str
    hsk_level: int
    section: str
    question_type: str
    content: dict
    options: Optional[list]
    explanation: Optional[str]
    difficulty: int
    audio_url: Optional[str]
    image_url: Optional[str]
    tags: Optional[list]
    is_active: bool
    created_at: datetime


class QuestionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[QuestionResponse]


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    hsk_level: int
    structure: dict
    time_limit: int
    total_questions: int
    total_score: int
    is_public: bool = True
    price: int = 0


class TemplateResponse(BaseModel):
    id: str
    creator_id: Optional[str]
    name: str
    description: Optional[str]
    hsk_level: int
    structure: dict
    time_limit: int
    total_questions: int
    total_score: int
    is_public: bool
    price: int
    status: str
    publish_count: int
    created_at: datetime


class TemplateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[TemplateResponse]


# ============== 依赖 ==============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== 应用 ==============
app = FastAPI(title="HSK Question Service", version="1.0.0")


# ============== 题目API ==============
@app.post("/questions", response_model=QuestionResponse)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """创建题目"""
    db_question = Question(
        hsk_level=question.hsk_level,
        section=question.section,
        question_type=question.question_type,
        content=question.content,
        options=question.options,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        difficulty=question.difficulty,
        audio_url=question.audio_url,
        image_url=question.image_url,
        tags=question.tags
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return QuestionResponse(
        id=str(db_question.id),
        hsk_level=db_question.hsk_level,
        section=db_question.section,
        question_type=db_question.question_type,
        content=db_question.content,
        options=db_question.options,
        explanation=db_question.explanation,
        difficulty=db_question.difficulty,
        audio_url=db_question.audio_url,
        image_url=db_question.image_url,
        tags=db_question.tags,
        is_active=db_question.is_active,
        created_at=db_question.created_at
    )


@app.get("/questions", response_model=QuestionListResponse)
def list_questions(
    level: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    query = db.query(Question).filter(Question.is_active == True)
    
    if level:
        query = query.filter(Question.hsk_level == level)
    if section:
        query = query.filter(Question.section == section)
    if question_type:
        query = query.filter(Question.question_type == question_type)
    
    total = query.count()
    questions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return QuestionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[
            QuestionResponse(
                id=str(q.id),
                hsk_level=q.hsk_level,
                section=q.section,
                question_type=q.question_type,
                content=q.content,
                options=q.options,
                explanation=q.explanation,
                difficulty=q.difficulty,
                audio_url=q.audio_url,
                image_url=q.image_url,
                tags=q.tags,
                is_active=q.is_active,
                created_at=q.created_at
            )
            for q in questions
        ]
    )


@app.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question(question_id: str, db: Session = Depends(get_db)):
    """获取题目详情"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return QuestionResponse(
        id=str(question.id),
        hsk_level=question.hsk_level,
        section=question.section,
        question_type=question.question_type,
        content=question.content,
        options=question.options,
        explanation=question.explanation,
        difficulty=question.difficulty,
        audio_url=question.audio_url,
        image_url=question.image_url,
        tags=question.tags,
        is_active=question.is_active,
        created_at=question.created_at
    )


@app.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(question_id: str, question: QuestionCreate, db: Session = Depends(get_db)):
    """更新题目"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db_question.hsk_level = question.hsk_level
    db_question.section = question.section
    db_question.question_type = question.question_type
    db_question.content = question.content
    db_question.options = question.options
    db_question.correct_answer = question.correct_answer
    db_question.explanation = question.explanation
    db_question.difficulty = question.difficulty
    db_question.audio_url = question.audio_url
    db_question.image_url = question.image_url
    db_question.tags = question.tags
    db_question.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_question)
    
    return QuestionResponse(
        id=str(db_question.id),
        hsk_level=db_question.hsk_level,
        section=db_question.section,
        question_type=db_question.question_type,
        content=db_question.content,
        options=db_question.options,
        explanation=db_question.explanation,
        difficulty=db_question.difficulty,
        audio_url=db_question.audio_url,
        image_url=db_question.image_url,
        tags=db_question.tags,
        is_active=db_question.is_active,
        created_at=db_question.created_at
    )


@app.delete("/questions/{question_id}")
def delete_question(question_id: str, db: Session = Depends(get_db)):
    """删除题目"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.is_active = False
    db.commit()
    
    return {"success": True, "message": "Question deleted"}


# ============== 试卷模板API ==============
@app.post("/templates", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """创建试卷模板"""
    db_template = ExamTemplate(
        name=template.name,
        description=template.description,
        hsk_level=template.hsk_level,
        structure=template.structure,
        time_limit=template.time_limit,
        total_questions=template.total_questions,
        total_score=template.total_score,
        is_public=template.is_public,
        price=template.price
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return TemplateResponse(
        id=str(db_template.id),
        creator_id=str(db_template.creator_id) if db_template.creator_id else None,
        name=db_template.name,
        description=db_template.description,
        hsk_level=db_template.hsk_level,
        structure=db_template.structure,
        time_limit=db_template.time_limit,
        total_questions=db_template.total_questions,
        total_score=db_template.total_score,
        is_public=db_template.is_public,
        price=db_template.price,
        status=db_template.status,
        publish_count=db_template.publish_count,
        created_at=db_template.created_at
    )


@app.get("/templates", response_model=TemplateListResponse)
def list_templates(
    level: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取试卷模板列表"""
    query = db.query(ExamTemplate).filter(ExamTemplate.is_public == True)
    
    if level:
        query = query.filter(ExamTemplate.hsk_level == level)
    if status:
        query = query.filter(ExamTemplate.status == status)
    
    total = query.count()
    templates = query.order_by(ExamTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return TemplateListResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[
            TemplateResponse(
                id=str(t.id),
                creator_id=str(t.creator_id) if t.creator_id else None,
                name=t.name,
                description=t.description,
                hsk_level=t.hsk_level,
                structure=t.structure,
                time_limit=t.time_limit,
                total_questions=t.total_questions,
                total_score=t.total_score,
                is_public=t.is_public,
                price=t.price,
                status=t.status,
                publish_count=t.publish_count,
                created_at=t.created_at
            )
            for t in templates
        ]
    )


@app.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """获取试卷模板详情"""
    template = db.query(ExamTemplate).filter(ExamTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse(
        id=str(template.id),
        creator_id=str(template.creator_id) if template.creator_id else None,
        name=template.name,
        description=template.description,
        hsk_level=template.hsk_level,
        structure=template.structure,
        time_limit=template.time_limit,
        total_questions=template.total_questions,
        total_score=template.total_score,
        is_public=template.is_public,
        price=template.price,
        status=template.status,
        publish_count=template.publish_count,
        created_at=template.created_at
    )


@app.post("/templates/{template_id}/publish")
def publish_template(template_id: str, db: Session = Depends(get_db)):
    """发布试卷模板"""
    template = db.query(ExamTemplate).filter(ExamTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.status == "published":
        raise HTTPException(status_code=400, detail="Template already published")
    
    template.status = "published"
    template.published_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Template published"}


# ============== 题型统计 ==============
@app.get("/statistics/question-types")
def get_question_type_stats(db: Session = Depends(get_db)):
    """获取各题型题目数量统计"""
    results = db.query(
        Question.hsk_level,
        Question.section,
        Question.question_type,
        func.count(Question.id).label("count")
    ).filter(Question.is_active == True).group_by(
        Question.hsk_level, Question.section, Question.question_type
    ).all()
    
    stats = {}
    for r in results:
        level_key = f"hsk{r.hsk_level}"
        if level_key not in stats:
            stats[level_key] = {}
        if r.section not in stats[level_key]:
            stats[level_key][r.section] = {}
        stats[level_key][r.section][r.question_type] = r.count
    
    return {"data": stats}


# ============== 健康检查 ==============
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "question-service"}


# ============== 启动 ==============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
