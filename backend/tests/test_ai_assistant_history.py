from types import SimpleNamespace

from app.api.v1.endpoints.ai_assistant import (
    AiAssistantConversationMessage,
    _pending_history_messages,
)


def message(role: str, content: str) -> AiAssistantConversationMessage:
    return AiAssistantConversationMessage(role=role, content=content)


def test_first_message_persists_full_initial_context() -> None:
    incoming = [
        message("assistant", "Como posso ajudar?"),
        message("user", "Crie uma página para Gramado"),
    ]

    assert _pending_history_messages([], incoming) == incoming


def test_existing_history_only_appends_new_messages() -> None:
    existing = [
        SimpleNamespace(role="assistant", content="Como posso ajudar?"),
        SimpleNamespace(role="user", content="Crie uma página para Gramado"),
        SimpleNamespace(role="assistant", content="Claro, vamos começar."),
    ]
    incoming = [
        message("assistant", "Como posso ajudar?"),
        message("user", "Crie uma página para Gramado"),
        message("assistant", "Claro, vamos começar."),
        message("user", "Inclua um roteiro de quatro dias"),
    ]

    pending = _pending_history_messages(existing, incoming)

    assert [(item.role, item.content) for item in pending] == [
        ("user", "Inclua um roteiro de quatro dias")
    ]


def test_divergent_client_history_does_not_duplicate_old_messages() -> None:
    existing = [SimpleNamespace(role="user", content="Mensagem já salva")]
    incoming = [
        message("assistant", "Contexto local divergente"),
        message("user", "Nova pergunta"),
    ]

    pending = _pending_history_messages(existing, incoming)

    assert [(item.role, item.content) for item in pending] == [("user", "Nova pergunta")]
