import json
from pathlib import Path

from radar.domain.areas import catalogo_do_site

ARQUIVO = Path(__file__).parent.parent / "web/assets/areas.json"


def test_o_catalogo_do_site_e_o_mesmo_do_backend():
    assert json.loads(ARQUIVO.read_text()) == catalogo_do_site()
