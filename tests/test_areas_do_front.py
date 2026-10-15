import json
import re
from pathlib import Path

from radar.domain.areas import AREAS, area_do_curso, catalogo_do_site, normalizar_curso

ARQUIVO = Path(__file__).parent.parent / "web/assets/areas.json"
LANDING = Path(__file__).parent.parent / "web/index.html"


def test_o_catalogo_do_site_e_o_mesmo_do_backend():
    assert json.loads(ARQUIVO.read_text()) == catalogo_do_site()


def test_a_faixa_da_landing_mostra_exatamente_as_areas_do_catalogo():
    html = LANDING.read_text()
    faixa = html[html.index("data-areas-track") :]
    faixa = faixa[: faixa.index("</ul>")]

    assert re.findall(r'data-area="([a-z_]+)"', faixa) == [area.nome for area in AREAS]


def test_cada_area_da_faixa_tem_sua_ilustracao_leve_e_sem_texto_alternativo():
    html = LANDING.read_text()
    faixa = html[html.index("data-areas-track") :]
    faixa = faixa[: faixa.index("</ul>")]

    for area in AREAS:
        arquivo = LANDING.parent / f"assets/areas/{area.nome}.webp"
        conteudo = arquivo.read_bytes()
        assert conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP", area.nome
        assert len(conteudo) <= 12 * 1024, area.nome
        assert (
            f'<span class="area-tile"><img src="assets/areas/{area.nome}.webp" alt="" '
            f'width="144" height="144" decoding="async"></span>'
        ) in faixa, area.nome
    assert "<svg" not in faixa


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
