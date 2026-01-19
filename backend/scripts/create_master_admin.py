"""
Script para criar ou atualizar o administrador master do painel.

Uso:
    python scripts/create_master_admin.py --email dono@empresa.com --password SenhaForte123 --name "Nome do Dono"

O script configura o usuário como superuser e garante que ele tenha plano Infinity.
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import auth as auth_service  # noqa: E402


def create_superuser(email: str, password: str, name: str, whatsapp: str | None, cpf: str | None) -> User:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.name = name
            if password:
                user.hashed_password = auth_service.get_password_hash(password)
            if whatsapp:
                user.whatsapp = whatsapp
            if cpf and not user.cpf:
                user.cpf = cpf
        else:
            user = User(
                email=email,
                name=name,
                whatsapp=whatsapp,
                cpf=cpf,
                plan="infinity",
                hashed_password=auth_service.get_password_hash(password),
            )
        user.is_superuser = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria/atualiza o administrador master.")
    parser.add_argument("--email", required=True, help="Email do admin master.")
    parser.add_argument("--password", required=True, help="Senha forte do admin master.")
    parser.add_argument("--name", default="Owner", help="Nome completo.")
    parser.add_argument("--whatsapp", default=None, help="WhatsApp no formato 5599999999.")
    parser.add_argument("--cpf", default=None, help="CPF (somente números).")
    args = parser.parse_args()

    auth_service.validate_password_strength(args.password)
    user = create_superuser(args.email, args.password, args.name, args.whatsapp, args.cpf)
    print(f"Usuário master atualizado/criado com sucesso: {user.email}")


if __name__ == "__main__":
    main()
