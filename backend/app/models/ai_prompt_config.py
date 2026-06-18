from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AiPromptConfig(Base):
    __tablename__ = "ai_prompt_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    active_prompt = Column(Text, nullable=False)
    default_prompt = Column(Text, nullable=False)
    gpt_model = Column(String(100), nullable=False, server_default="gpt-4.1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_user_id])
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])
    versions = relationship(
        "AiPromptConfigVersion",
        back_populates="config",
        cascade="all, delete-orphan",
    )


class AiPromptConfigVersion(Base):
    __tablename__ = "ai_prompt_config_versions"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("ai_prompt_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, server_default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    config = relationship("AiPromptConfig", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
