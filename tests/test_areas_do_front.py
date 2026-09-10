import json
import re
from pathlib import Path

from radar.domain.areas import AREAS, area_do_curso, catalogo_do_site, normalizar_curso

ARQUIVO = Path(__file__).parent.parent / "web/assets/areas.json"


def test_o_catalogo_do_site_e_o_mesmo_do_backend():
    assert json.loads(ARQUIVO.read_text()) == catalogo_do_site()


def test_a_normalizacao_de_cursos_do_site_bate_com_o_backend():
    arquivo = Path(__file__).parent / "fixtures/cursos_normalizados.json"
    esperado = json.loads(arquivo.read_text())

    assert esperado == {
        curso: [normalizar_curso(curso), area_do_curso(curso)] for curso in esperado
    }


def test_todo_curso_sugerido_e_reconhecido_na_propria_area():
    for area in AREAS:
        for curso in area.cursos_sugeridos:
            assert area_do_curso(curso) == area.nome, f"{curso} não cai em {area.nome}"


def test_toda_area_oferece_ao_menos_um_curso_sugerido():
    assert [area.nome for area in AREAS if not area.cursos_sugeridos] == []


def test_curso_sugerido_e_escrito_para_leitura_e_nao_normalizado():
    sugeridos = [curso for area in AREAS for curso in area.cursos_sugeridos]

    assert all(curso[0].isupper() for curso in sugeridos)
    assert any("ç" in curso or "ã" in curso or "é" in curso for curso in sugeridos)


def test_as_sugestoes_do_formulario_sao_as_do_catalogo():
    html = (Path(__file__).parent.parent / "web/index.html").read_text()
    lista = re.search(r'<datalist id="cursos-sugeridos">(.*?)</datalist>', html, re.S)
    no_formulario = re.findall(r'<option value="([^"]+)"></option>', lista.group(1))
    do_catalogo = sorted({c for area in AREAS for c in area.cursos_sugeridos}, key=str.casefold)

    assert no_formulario == do_catalogo


def test_o_formulario_sugere_curso_de_area_fora_da_computacao():
    html = (Path(__file__).parent.parent / "web/index.html").read_text()

    for curso in ("Direito", "Enfermagem", "Pedagogia", "Engenharia Civil", "Turismo"):
        assert f'<option value="{curso}"></option>' in html
