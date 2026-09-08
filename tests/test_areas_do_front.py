import json
from pathlib import Path

from radar.domain.areas import AREAS

ARQUIVO = Path(__file__).parent.parent / "web/assets/areas.json"


def esperado() -> dict:
    return {
        "areas": [
            {
                "nome": area.nome,
                "cursos": list(area.cursos),
                "subareas": [{"valor": valor, "rotulo": rotulo} for valor, rotulo in area.subareas],
            }
            for area in AREAS
        ]
    }


def test_o_catalogo_do_site_e_o_mesmo_do_backend():
    assert json.loads(ARQUIVO.read_text()) == esperado()
