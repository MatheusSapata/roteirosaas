"""Trechos de voo escritos pelo assistente de IA, para virar a seção Voos de verdade.

Formato pedido à IA (uma linha por trecho; conexão é "Ida 2", "Volta 2"...):
    Ida: 12/07/2026, voo LA3456, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM
    Volta: 19/07/2026, Recife (REC) 22:40 → São Paulo (GRU) 02:05 +1, GOL
    Bagagem: 1 mala de 23 kg

Com código e data, o voo é buscado na API (horários, aeroportos e companhia de verdade); sem
código, ou se a API não achar, fica com o que a mensagem trouxe (manual).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any

# Prefixo do voo → companhia (as mais comuns nos pacotes das agências).
AIRLINES_BY_CODE = {
    "LA": "LATAM", "JJ": "LATAM", "G3": "GOL", "AD": "Azul", "TP": "TAP Air Portugal", "CM": "Copa Airlines",
    "AV": "Avianca", "AA": "American Airlines", "UA": "United Airlines", "DL": "Delta", "AF": "Air France",
    "KL": "KLM", "IB": "Iberia", "EK": "Emirates", "AR": "Aerolíneas Argentinas", "JA": "JetSMART", "H2": "Sky Airline",
    "UX": "Air Europa", "LH": "Lufthansa", "QR": "Qatar Airways", "TK": "Turkish Airlines", "AZ": "ITA Airways",
    "BA": "British Airways", "AM": "Aeroméxico", "2Z": "Voepass",
}
AIRLINE_NAMES = sorted({name for name in AIRLINES_BY_CODE.values()} | {"Latam", "Gol", "Azul Linhas Aéreas"}, key=len, reverse=True)

LEG_LABEL_RE = re.compile(r"^\s*[-*•]?\s*(ida|volta|conex[aã]o|trecho)\s*(\d+)?\s*[:\-–]\s*(.+)$", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
# Código de voo: 2 caracteres da companhia (letras ou letra+número) e de 1 a 4 números.
FLIGHT_CODE_RE = re.compile(r"\b(?:voo|vôo|flight)?\s*\b([A-Z]{2}|[A-Z]\d|\d[A-Z])\s?(\d{1,4})\b")
AIRPORT_RE = re.compile(r"([A-Za-zÀ-ÿ'.\s]{2,40}?)\s*\(([A-Z]{3})\)\s*(?:(\d{1,2})\s*[:h]\s*(\d{2}))?\s*(\+\s*1)?")


def _plain(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c)).lower()


def _date(match: re.Match[str] | None, fallback_year: int) -> date | None:
    if not match:
        return None
    day, month, year = int(match.group(1)), int(match.group(2)), match.group(3)
    full_year = fallback_year if not year else (2000 + int(year) if len(year) == 2 else int(year))
    try:
        return date(full_year, month, day)
    except ValueError:
        return None


def _iso(day: date | None, hour: str | None, minute: str | None, next_day: bool = False) -> str | None:
    if not day or hour is None or minute is None:
        return None
    try:
        moment = datetime(day.year, day.month, day.day, int(hour), int(minute))
    except ValueError:
        return None
    if next_day:
        moment += timedelta(days=1)
    return moment.strftime("%Y-%m-%dT%H:%M:00")


def parse_leg(text: str, fallback_year: int, last_date: date | None = None) -> dict[str, Any]:
    """Um trecho ("12/07/2026, voo LA3456, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM")."""
    day = _date(DATE_RE.search(text), fallback_year) or last_date
    segment: dict[str, Any] = {"flight_date": day.isoformat() if day else None}
    without_dates = DATE_RE.sub(" ", text)
    airports = list(AIRPORT_RE.finditer(without_dates))
    code_text = without_dates
    for airport in airports:
        code_text = code_text.replace(airport.group(0), " ")
    code = FLIGHT_CODE_RE.search(code_text)
    if code:
        prefix = code.group(1).upper()
        segment["flight_number"] = f"{prefix}{code.group(2)}"
        segment["flight_iata"] = segment["flight_number"]
        segment["airline_iata"] = prefix
        if prefix in AIRLINES_BY_CODE:
            segment["airline_name"] = AIRLINES_BY_CODE[prefix]
    plain = _plain(text)
    for name in AIRLINE_NAMES:
        if _plain(name) in plain:
            segment["airline_name"] = name if name not in {"Latam", "Gol"} else name.upper()
            break
    for prefix, airport in zip(("departure", "arrival"), airports[:2]):
        city = re.sub(r"^[,\s→>-]+|(?:\bde\b|\bpara\b|\bsaindo\b)\s*$", "", airport.group(1).strip(), flags=re.IGNORECASE).strip(" ,-")
        segment[f"{prefix}_airport_iata"] = airport.group(2)
        if city:
            segment[f"{prefix}_city"] = city
        when = _iso(day, airport.group(3), airport.group(4), bool(airport.group(5)))
        if when:
            segment[f"{prefix}_datetime"] = when
    notes = []
    if "direto" in plain or "sem escala" in plain:
        notes.append("Voo direto")
    if "conex" in plain or "escala" in plain and "sem escala" not in plain:
        notes.append("Com conexão")
    if notes:
        segment["notes"] = ", ".join(notes)
    return segment


def parse_flight_legs(block: str, today: date | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Trechos de ida e volta da resposta e as outras linhas (bagagem, observações)."""
    year = (today or date.today()).year
    journeys: dict[str, dict[str, Any]] = {}
    other: list[str] = []
    direction = "outbound"
    last_date: dict[str, date | None] = {"outbound": None, "inbound": None}
    checked_bag = None
    for raw in (block or "").splitlines():
        line = raw.strip()
        match = LEG_LABEL_RE.match(line)
        if not match:
            if re.match(r"^\s*[-*•]?\s*bagage", _plain(line)):
                plain = _plain(line)
                checked_bag = bool(re.search(r"23|despach|mala|kg", plain)) and "sem bagagem" not in plain and "nao inclu" not in plain
                other.append(line.lstrip("-*• ").strip())
            elif line:
                other.append(line)
            continue
        kind = _plain(match.group(1))
        if kind.startswith("ida"):
            direction = "outbound"
        elif kind.startswith("volta"):
            direction = "inbound"
        # "Conexão"/"Trecho" continua na direção do trecho anterior.
        segment = parse_leg(match.group(3), year, last_date[direction])
        if not (segment.get("departure_airport_iata") or segment.get("flight_number")):
            other.append(line)
            continue
        if segment.get("flight_date"):
            last_date[direction] = date.fromisoformat(segment["flight_date"])
        journey = journeys.setdefault(direction, {"direction": direction, "title": "Ida" if direction == "outbound" else "Volta", "segments": []})
        journey["segments"].append(segment)
    result = [journeys[key] for key in ("outbound", "inbound") if key in journeys]
    if checked_bag is not None:
        for journey in result:
            for segment in journey["segments"]:
                segment["included_checked_bag"] = checked_bag
    return result, other
