import json
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


def test_o_formulario_nao_guarda_lista_propria_de_cursos():
    html = (Path(__file__).parent.parent / "web/index.html").read_text()
    javascript = (Path(__file__).parent.parent / "web/assets/app.js").read_text()

    assert "<datalist" not in html
    assert 'id="lista-de-cursos"' in html
    assert "area.cursos_sugeridos" in javascript
