import json
from pathlib import Path

from radar.domain.areas import catalogo_do_site

RAIZ = Path(__file__).parent.parent
ARQUIVO_DO_SITE = RAIZ / "web/assets/areas.json"


def conteudo_do_catalogo() -> str:
    return json.dumps(catalogo_do_site(), ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    ARQUIVO_DO_SITE.write_text(conteudo_do_catalogo())


if __name__ == "__main__":
    main()
