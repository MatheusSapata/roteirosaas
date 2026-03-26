from __future__ import annotations

from typing import Tuple

DEVICE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("iphone", "iPhone"),
    ("ipad", "iPad"),
    ("mac os", "Mac"),
    ("macintosh", "Mac"),
    ("android", "Android"),
    ("windows phone", "Windows Phone"),
    ("windows nt", "Windows"),
    ("linux", "Linux"),
)

BROWSER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("edg", "Microsoft Edge"),
    ("chrome", "Google Chrome"),
    ("safari", "Safari"),
    ("firefox", "Firefox"),
    ("opera", "Opera"),
)


def summarize_user_agent(user_agent: str | None) -> Tuple[str, str]:
    """Return (device_label, client_name) from a raw user agent string."""
    if not user_agent:
        return ("Dispositivo desconhecido", "Navegador")
    agent = user_agent.lower()
    device_label = "Dispositivo desconhecido"
    for pattern, label in DEVICE_PATTERNS:
        if pattern in agent:
            device_label = label
            break

    client_name = "Navegador"
    for pattern, label in BROWSER_PATTERNS:
        if pattern in agent:
            client_name = label
            break

    return (device_label, client_name)
