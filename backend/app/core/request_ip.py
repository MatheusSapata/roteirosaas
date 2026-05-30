from fastapi import Request
from ipaddress import ip_address


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        candidates = [part.strip() for part in x_forwarded_for.split(",") if part.strip()]
        for candidate in candidates:
            try:
                parsed = ip_address(candidate)
                if not (parsed.is_private or parsed.is_loopback or parsed.is_link_local):
                    return candidate
            except ValueError:
                continue
        if candidates:
            return candidates[0]

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip

    if request.client and request.client.host:
        return request.client.host
    return "unknown"
