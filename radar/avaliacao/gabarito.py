import json
from pathlib import Path
from uuid import UUID

from radar.avaliacao.julgar import amostrar
from radar.domain.datas import data_local
from radar.domain.models import ChaveDaEntrega, EntregaParaJulgar
from radar.storage.errors import ErroDeArmazenamento


def exportar_gabarito(entregas: list[EntregaParaJulgar], amostra: int, semente: int) -> list[dict]:
    return [
        {
            "perfil_id": str(entrega.perfil_id),
            "curso": entrega.perfil.curso,
            "fonte": entrega.vaga.fonte,
            "id_externo": entrega.vaga.id_externo,
            "titulo": entrega.vaga.titulo,
            "empresa": entrega.vaga.empresa,
            "localizacao": entrega.vaga.localizacao,
            "url": entrega.vaga.url,
            "enviada_em": data_local(entrega.enviada_em).isoformat(),
            "nota_do_radar": entrega.nota_do_radar,
            "relevante": None,
            "comentario": "",
        }
        for entrega in amostrar(entregas, amostra, semente)
    ]


def gravar_gabarito(itens: list[dict], caminho: Path) -> None:
    caminho.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n")


def carregar_gabarito(caminho: Path) -> dict[ChaveDaEntrega, bool]:
    try:
        itens = json.loads(caminho.read_text())
    except FileNotFoundError as erro:
        raise ErroDeArmazenamento(f"Gabarito não encontrado: {caminho}") from erro
    except json.JSONDecodeError as erro:
        raise ErroDeArmazenamento(f"Gabarito não é JSON válido: {caminho}") from erro
    try:
        return {
            (UUID(item["perfil_id"]), item["fonte"], item["id_externo"]): bool(item["relevante"])
            for item in itens
            if item.get("relevante") is not None
        }
    except (AttributeError, KeyError, TypeError, ValueError) as erro:
        raise ErroDeArmazenamento(f"Gabarito inválido em {caminho}: {erro}") from erro


def rotulos_fora_da_janela(
    gabarito: dict[ChaveDaEntrega, bool], selecionadas: list[EntregaParaJulgar]
) -> int:
    com_entrega = {entrega.chave() for entrega in selecionadas}
    return len(gabarito.keys() - com_entrega)


def selecionar_do_gabarito(
    entregas: list[EntregaParaJulgar], gabarito: dict[ChaveDaEntrega, bool]
) -> list[EntregaParaJulgar]:
    return [entrega for entrega in entregas if entrega.chave() in gabarito]
