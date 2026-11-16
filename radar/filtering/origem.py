from radar.domain.models import OrigemDoAnuncio, Vaga

ID_DO_PARCEIRO_EMPREGO_PT = "79986"
NOME_DO_PARCEIRO_EMPREGO_PT = "emprego"
DOMINIO_DO_EMPREGO_PT = "emprego.pt"
MOTIVO_DE_CADA_DOMINIO_BLOQUEADO = {
    "gupy.io": "os termos da Gupy proíbem agregar, copiar ou duplicar as vagas dela",
    "linkedin.com": "o LinkedIn bloqueia coleta automatizada e está fora do escopo do projeto",
    DOMINIO_DO_EMPREGO_PT: "o emprego.pt publica como novos anúncios brasileiros já vencidos",
}


def origem_bloqueada(origem: OrigemDoAnuncio | None) -> bool:
    return motivo_do_bloqueio(origem) is not None


def motivo_do_bloqueio(origem: OrigemDoAnuncio | None) -> str | None:
    if origem is None:
        return None
    if e_o_parceiro_emprego_pt(origem):
        return MOTIVO_DE_CADA_DOMINIO_BLOQUEADO[DOMINIO_DO_EMPREGO_PT]
    bloqueado = dominio_bloqueado(origem.dominio)
    return MOTIVO_DE_CADA_DOMINIO_BLOQUEADO[bloqueado] if bloqueado else None


def e_o_parceiro_emprego_pt(origem: OrigemDoAnuncio) -> bool:
    identificador = (origem.id_do_parceiro or "").strip()
    nome = (origem.parceiro or "").strip().casefold()
    return identificador == ID_DO_PARCEIRO_EMPREGO_PT or nome == NOME_DO_PARCEIRO_EMPREGO_PT


def dominio_bloqueado(dominio: str | None) -> str | None:
    informado = (dominio or "").strip().casefold()
    for bloqueado in MOTIVO_DE_CADA_DOMINIO_BLOQUEADO:
        if informado == bloqueado or informado.endswith(f".{bloqueado}"):
            return bloqueado
    return None


def separar_as_de_origem_bloqueada(vagas: list[Vaga]) -> tuple[list[Vaga], list[Vaga]]:
    seguem = [vaga for vaga in vagas if not origem_bloqueada(vaga.origem)]
    bloqueadas = [vaga for vaga in vagas if origem_bloqueada(vaga.origem)]
    return seguem, bloqueadas
