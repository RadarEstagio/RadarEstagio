import re

NUL = "\x00"
CARACTERES_INVALIDOS = re.compile("[\x00\ud800-\udfff]")


def sem_caracteres_invalidos(texto: str) -> str:
    if not CARACTERES_INVALIDOS.search(texto):
        return texto
    sem_nul = texto.replace(NUL, "")
    return sem_nul.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "ignore")
