from uuid import UUID

CARACTERES_DO_TRECHO_DO_ID = 8


def trecho_do_id(identificador: UUID) -> str:
    return f"...{str(identificador)[:CARACTERES_DO_TRECHO_DO_ID]}..."
