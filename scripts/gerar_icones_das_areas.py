import json
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

RAIZ = Path(__file__).parent.parent
ARQUIVO_DAS_AREAS = RAIZ / "web/assets/areas.json"
PASTA_DE_SAIDA = RAIZ / "web/assets/areas"
EXTENSOES_ACEITAS = (".jpg", ".jpeg", ".png", ".webp")
LADO_EM_PIXELS = 144
PROPORCAO_DO_OBJETO = 0.84
BRANCO_MINIMO = 250
MENOR_AREA_DE_FUNDO = 1500
RAIO_DA_ERODIDA = 3
RAIO_DO_SUAVIZADO = 1.5
QUALIDADE_DO_WEBP = 90


def nomes_das_areas() -> list[str]:
    conteudo = json.loads(ARQUIVO_DAS_AREAS.read_text(encoding="utf-8"))
    return [area["nome"] for area in conteudo["areas"]]


def arquivo_da_area(pasta: Path, area: str) -> Path | None:
    for extensao in EXTENSOES_ACEITAS:
        candidato = pasta / f"{area}{extensao}"
        if candidato.exists():
            return candidato
    return None


def pixels_brancos(imagem: Image.Image) -> bytes:
    vermelho, verde, azul = imagem.split()
    menor_canal = ImageChops.darker(ImageChops.darker(vermelho, verde), azul)
    return menor_canal.point(lambda valor: 255 if valor >= BRANCO_MINIMO else 0).tobytes()


def componentes_de_fundo(brancos: bytes, largura: int, altura: int) -> bytearray:
    fundo = bytearray(largura * altura)
    visitado = bytearray(largura * altura)
    for inicio in range(largura * altura):
        if not brancos[inicio] or visitado[inicio]:
            continue
        componente = []
        fila = deque([inicio])
        visitado[inicio] = 1
        while fila:
            atual = fila.popleft()
            componente.append(atual)
            coluna = atual % largura
            vizinhos = []
            if coluna > 0:
                vizinhos.append(atual - 1)
            if coluna < largura - 1:
                vizinhos.append(atual + 1)
            if atual >= largura:
                vizinhos.append(atual - largura)
            if atual < largura * (altura - 1):
                vizinhos.append(atual + largura)
            for vizinho in vizinhos:
                if brancos[vizinho] and not visitado[vizinho]:
                    visitado[vizinho] = 1
                    fila.append(vizinho)
        if len(componente) >= MENOR_AREA_DE_FUNDO:
            for indice in componente:
                fundo[indice] = 1
    return fundo


def transparencia_do_objeto(imagem: Image.Image) -> Image.Image:
    largura, altura = imagem.size
    fundo = componentes_de_fundo(pixels_brancos(imagem), largura, altura)
    objeto = bytes(fundo).translate(bytes([255, 0]) + bytes(254))
    mascara = Image.frombytes("L", imagem.size, objeto)
    mascara = mascara.filter(ImageFilter.MinFilter(RAIO_DA_ERODIDA * 2 + 1))
    return mascara.filter(ImageFilter.GaussianBlur(RAIO_DO_SUAVIZADO))


def recortar_e_centralizar(imagem: Image.Image, transparencia: Image.Image) -> Image.Image:
    recorte = imagem.convert("RGBA")
    recorte.putalpha(transparencia)
    caixa = transparencia.point(lambda valor: 255 if valor > 8 else 0).getbbox()
    recorte = recorte.crop(caixa)
    maior_lado = max(recorte.size)
    escala = LADO_EM_PIXELS * PROPORCAO_DO_OBJETO / maior_lado
    tamanho = (round(recorte.width * escala), round(recorte.height * escala))
    reduzido = recorte.resize(tamanho, Image.Resampling.LANCZOS)
    quadro = Image.new("RGBA", (LADO_EM_PIXELS, LADO_EM_PIXELS), (0, 0, 0, 0))
    deslocamento = (
        (LADO_EM_PIXELS - tamanho[0]) // 2,
        (LADO_EM_PIXELS - tamanho[1]) // 2,
    )
    quadro.paste(reduzido, deslocamento)
    return quadro


def gerar_icone(origem: Path, destino: Path) -> int:
    imagem = Image.open(origem).convert("RGB")
    icone = recortar_e_centralizar(imagem, transparencia_do_objeto(imagem))
    icone.save(destino, "WEBP", quality=QUALIDADE_DO_WEBP, method=6)
    return destino.stat().st_size


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: gerar_icones_das_areas.py <pasta com uma imagem por area>")
        return 2
    pasta = Path(sys.argv[1])
    areas = nomes_das_areas()
    origens = {area: arquivo_da_area(pasta, area) for area in areas}
    faltando = [area for area, origem in origens.items() if origem is None]
    if faltando:
        print("sem imagem para:", ", ".join(faltando))
        return 1
    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    for area, origem in origens.items():
        tamanho = gerar_icone(origem, PASTA_DE_SAIDA / f"{area}.webp")
        print(f"{area}.webp {tamanho / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
