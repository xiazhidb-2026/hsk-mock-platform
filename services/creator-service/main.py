"""
HSK Mock Platform - Creator Service
博主管理、数据统计
"""

import os
import uuid
import json
import secrets
import hashlib
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, SmallInteger, Boolean, Integer, Text, DateTime
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


class Creator(Base):
    __tablename__ = "creators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    youtube_channel_id = Column(String(50))
    youtube_channel_name = Column(String(100))
    avatar_url = Column(String(500))
    invite_code = Column(String(20), unique=True)
    status = Column(String(20), default="active")
    total_exams = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class InviteCode(Base):
    __tablename__ = "invite_codes"
    
    code = Column(String(20), primary_key=True)
    creator_id = Column(UUID(as_uuid=True))
    used_count = Column(Integer, default=0)
    max_uses = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============== Pydantic模型 ==============
class CreatorRegister(BaseModel):
    email: EmailStr
    password: str
    youtube_channel_id: Optional[str] = None
    youtube_channel_name: Optional[str] = None
    invite_code: str


class CreatorLogin(BaseModel):
    email: EmailStr
    password: str


class CreatorResponse(BaseModel):
    id: str
    email: str
    youtube_channel_id: Optional[str]
    youtube_channel_name: Optional[str]
    avatar_url: Optional[str]
    status: str
    total_exams: int
    total_users: int
    created_at: datetime


class CreatorStatsResponse(BaseModel):
    total_exams: int
    total_users: int
    avg_score: float
    pass_rate: float
    recent_exams: List[dict]
    popular_templates: List[dict]


class InviteCodeResponse(BaseModel):
    code: str
    max_uses: int
    used_count: int
    is_active: bool
    expires_at: Optional[datetime]


# ============== 依赖 ==============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def generate_invite_code() -> str:
    """生成邀请码"""
    return secrets.token_urlsafe(6)[:8].upper()


# ============== 应用 ==============
app = FastAPI(title="HSK Creator Service", version="1.0.0")


# ============== 认证API ==============
@app.post("/creator/register", response_model=CreatorResponse)
def register_creator(creator: CreatorRegister, db: Session = Depends(get_db)):
    """博主注册（需要邀请码）"""
    # 验证邀请码
    invite = db.query(InviteCode).filter(
        InviteCode.code == creator.invite_code,
        InviteCode.is_active == True
    ).first()
    
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid invite code")
    
    if invite.used_count >= invite.max_uses:
        raise HTTPException(status_code=400, detail="Invite code already used")
    
    # 检查邮箱是否已存在
    existing = db.query(Creator).filter(Creator.email == creator.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 创建博主
    db_creator = Creator(
        email=creator.email,
        password_hash=hash_password(creator.password),
        youtube_channel_id=creator.youtube_channel_id,
        youtube_channel_name=creator.youtube_channel_name,
        invite_code=generate_invite_code()
    )
    
    db.add(db_creator)
    
    # 更新邀请码使用次数
    invite.used_count += 1
    if invite.used_count >= invite.max_uses:
        invite.is_active = False
    
    db.commit()
    db.refresh(db_creator)
    
    return CreatorResponse(
        id=str(db_creator.id),
        email=db_creator.email,
        youtube_channel_id=db_creator.youtube_channel_id,
        youtube_channel_name=db_creator.youtube_channel_name,
        avatar_url=db_creator.avatar_url,
        status=db_creator.status,
        total_exams=db_creator.total_exams,
        total_users=db_creator.total_users,
        created_at=db_creator.created_at
    )


@app.post("/creator/login")
def login_creator(creator: CreatorLogin, db: Session = Depends(get_db)):
    """博主登录"""
    db_creator = db.query(Creator).filter(Creator.email == creator.email).first()
    
    if not db_creator:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(creator.password, db_creator.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if db_creator.status != "active":
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # 生成简单的token（实际应使用JWT）
    token = secrets.token_urlsafe(32)
    
    return {
        "token": token,
        "creator": CreatorResponse(
            id=str(db_creator.id),
            email=db_creator.email,
            youtube_channel_id=db_creator.youtube_channel_id,
            youtube_channel_name=db_creator.youtube_channel_name,
            avatar_url=db_creator.avatar_url,
            status=db_creator.status,
            total_exams=db_creator.total_exams,
            total_users=db_creator.total_users,
            created_at=db_creator.created_at
        )
    }


@app.get("/creator/me", response_model=CreatorResponse)
def get_current_creator(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取当前博主信息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 简化：token就是creator id
    creator = db.query(Creator).filter(Creator.id == authorization.replace("Bearer ", "")).first()
    
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    return CreatorResponse(
        id=str(creator.id),
        email=creator.email,
        youtube_channel_id=creator.youtube_channel_id,
        youtube_channel_name=creator.youtube_channel_name,
        avatar_url=creator.avatar_url,
        status=creator.status,
        total_exams=creator.total_exams,
        total_users=creator.total_users,
        created_at=creator.created_at
    )


# ============== 邀请码管理 ==============
@app.post("/creator/invite-codes", response_model=InviteCodeResponse)
def create_invite_code(
    max_uses: int = 1,
    expires_days: int = 30,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建邀请码"""
    creator_id = authorization.replace("Bearer ", "") if authorization else None
    
    from datetime import timedelta
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    invite = InviteCode(
        code=generate_invite_code(),
        creator_id=creator_id,
        max_uses=max_uses,
        expires_at=expires_at
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    return InviteCodeResponse(
        code=invite.code,
        max_uses=invite.max_uses,
        used_count=invite.used_count,
        is_active=invite.is_active,
        expires_at=invite.expires_at
    )


# ============== 数据统计 ==============
@app.get("/creator/stats", response_model=CreatorStatsResponse)
def get_creator_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取博主数据统计"""
    creator_id = authorization.replace("Bearer ", "") if authorization else None
    
    if not creator_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 简化返回，实际应查询数据库
    return CreatorStatsResponse(
        total_exams=0,
        total_users=0,
        avg_score=0.0,
        pass_rate=0.0,
        recent_exams=[],
        popular_templates=[]
    )


# ============== 健康检查 ==============
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "creator-service"}


# ============== 启动 ==============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
