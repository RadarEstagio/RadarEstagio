from radar.domain.models import OrigemDoAnuncio, Vaga

ID_DO_PARCEIRO_EMPREGO_PT = "79986"
NOME_DO_PARCEIRO_EMPREGO_PT = "emprego"


def origem_bloqueada(origem: OrigemDoAnuncio | None) -> bool:
    if origem is None:
        return False
    identificador = (origem.id_do_parceiro or "").strip()
    nome = (origem.parceiro or "").strip().casefold()
    return identificador == ID_DO_PARCEIRO_EMPREGO_PT or nome == NOME_DO_PARCEIRO_EMPREGO_PT


def separar_as_de_origem_bloqueada(vagas: list[Vaga]) -> tuple[list[Vaga], list[Vaga]]:
    seguem = [vaga for vaga in vagas if not origem_bloqueada(vaga.origem)]
    bloqueadas = [vaga for vaga in vagas if origem_bloqueada(vaga.origem)]
    return seguem, bloqueadas
