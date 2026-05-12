from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class WhatsAppConnection(Base):
    __tablename__ = "whatsapp_connections"
    __table_args__ = (
        UniqueConstraint("instance_name", name="uq_whatsapp_connections_instance_name"),
        Index("ix_whatsapp_connections_agency_status", "agency_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    instance_name = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(30), nullable=True)
    status = Column(String(40), nullable=False, server_default="disconnected")
    is_default = Column(Boolean, nullable=False, server_default="false")
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    connected_at = Column(DateTime(timezone=True), nullable=True)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("Agency")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    conversations = relationship(
        "WhatsAppConversation",
        back_populates="connection",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    messages = relationship(
        "WhatsAppMessage",
        back_populates="connection",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WhatsAppConversation(Base):
    __tablename__ = "whatsapp_conversations"
    __table_args__ = (
        UniqueConstraint("connection_id", "remote_phone", name="uq_whatsapp_conversations_connection_remote_phone"),
        Index("ix_whatsapp_conversations_agency_last_message", "agency_id", "last_message_at"),
        Index("ix_whatsapp_conversations_agency_unread", "agency_id", "unread_count"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(
        Integer,
        ForeignKey("whatsapp_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    opportunity_id = Column(
        Integer,
        ForeignKey("lead_form_submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    remote_phone = Column(String(30), nullable=False, index=True)
    remote_name = Column(String(255), nullable=True)
    avatar_url = Column(String(2048), nullable=True)
    last_message_text = Column(Text, nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    unread_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("WhatsAppConnection", back_populates="conversations")
    client = relationship("Client")
    opportunity = relationship("LeadFormSubmission")
    messages = relationship(
        "WhatsAppMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        UniqueConstraint("external_message_id", name="uq_whatsapp_messages_external_message_id"),
        Index("ix_whatsapp_messages_agency_created_at", "agency_id", "created_at"),
        Index("ix_whatsapp_messages_conversation_created_at", "conversation_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(
        Integer,
        ForeignKey("whatsapp_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        Integer,
        ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_message_id = Column(String(255), nullable=True, index=True)
    direction = Column(String(20), nullable=False, index=True)
    message_type = Column(String(40), nullable=False, server_default="text")
    body = Column(Text, nullable=False)
    status = Column(String(40), nullable=True)
    remote_phone = Column(String(30), nullable=False, index=True)
    media_url = Column(Text, nullable=True)
    media_mime_type = Column(String(255), nullable=True)
    media_file_name = Column(String(512), nullable=True)
    media_size = Column(Integer, nullable=True)
    media_duration = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    connection = relationship("WhatsAppConnection", back_populates="messages")
    conversation = relationship("WhatsAppConversation", back_populates="messages")


class WhatsAppInboxPermission(Base):
    __tablename__ = "whatsapp_inbox_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_whatsapp_inbox_permissions_user_id"),
        UniqueConstraint("agency_id", name="uq_whatsapp_inbox_permissions_agency_id"),
        Index("ix_whatsapp_inbox_permissions_enabled", "enabled"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    enabled = Column(Boolean, nullable=False, server_default="true")
    granted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("Agency", foreign_keys=[agency_id])
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by_user_id])
