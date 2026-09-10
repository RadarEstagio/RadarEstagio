import random

from radar.domain.datas import data_de_publicacao
from radar.domain.models import Usuario, Vaga
from radar.filtering.prefiltro import motivo_do_descarte


class DescarteDoPreFiltro:
    def __init__(self, usuario: Usuario, vaga: Vaga, motivo: str) -> None:
        self.usuario = usuario
        self.vaga = vaga
        self.motivo = motivo


def descartes_do_prefiltro(vagas: list[Vaga], usuarios: list[Usuario]) -> list[DescarteDoPreFiltro]:
    descartados = []
    for usuario in usuarios:
        for vaga in vagas:
            motivo = motivo_do_descarte(vaga, usuario.perfil)
            if motivo is not None:
                descartados.append(DescarteDoPreFiltro(usuario, vaga, motivo))
    return descartados


def contar_por_motivo(descartes: list[DescarteDoPreFiltro]) -> dict[str, int]:
    total: dict[str, int] = {}
    for descarte in descartes:
        total[descarte.motivo] = total.get(descarte.motivo, 0) + 1
    return dict(sorted(total.items(), key=lambda item: (-item[1], item[0])))


def amostrar_por_motivo(
    descartes: list[DescarteDoPreFiltro], amostra: int, semente: int
) -> list[DescarteDoPreFiltro]:
    por_motivo: dict[str, list[DescarteDoPreFiltro]] = {}
    for descarte in descartes:
        por_motivo.setdefault(descarte.motivo, []).append(descarte)
    sorteio = random.Random(semente)
    escolhidos: list[DescarteDoPreFiltro] = []
    filas = [sorteio.sample(grupo, len(grupo)) for _, grupo in sorted(por_motivo.items())]
    while filas and len(escolhidos) < amostra:
        for fila in list(filas):
            if len(escolhidos) == amostra:
                break
            escolhidos.append(fila.pop())
            if not fila:
                filas.remove(fila)
    return escolhidos


def exportar_descartes(
    descartes: list[DescarteDoPreFiltro], amostra: int, semente: int
) -> list[dict]:
    return [
        {
            "perfil_id": str(descarte.usuario.id),
            "curso": descarte.usuario.perfil.curso,
            "cidade_do_perfil": descarte.usuario.perfil.cidade,
            "modalidade_do_perfil": descarte.usuario.perfil.modalidade.value,
            "motivo_do_descarte": descarte.motivo,
            "fonte": descarte.vaga.fonte,
            "id_externo": descarte.vaga.id_externo,
            "titulo": descarte.vaga.titulo,
            "empresa": descarte.vaga.empresa,
            "localizacao": descarte.vaga.localizacao,
            "url": descarte.vaga.url,
            "publicada_em": data_de_publicacao(descarte.vaga.publicada_em).isoformat(),
            "descarte_correto": None,
            "comentario": "",
        }
        for descarte in amostrar_por_motivo(descartes, amostra, semente)
    ]
