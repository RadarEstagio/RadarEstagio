import json
from pathlib import Path

from radar.domain.areas import area_do_curso, catalogo_do_site, normalizar_curso

ARQUIVO = Path(__file__).parent.parent / "web/assets/areas.json"


def test_o_catalogo_do_site_e_o_mesmo_do_backend():
    assert json.loads(ARQUIVO.read_text()) == catalogo_do_site()


def test_a_normalizacao_de_cursos_do_site_bate_com_o_backend():
    arquivo = Path(__file__).parent / "fixtures/cursos_normalizados.json"
    esperado = json.loads(arquivo.read_text())

    assert esperado == {
        curso: [normalizar_curso(curso), area_do_curso(curso)] for curso in esperado
    }
