import json
import os
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).parent.parent
SCRIPT = RAIZ / "scripts/build-web.sh"
HTMLS = ("index.html", "termos.html", "privacidade.html")
ASSETS = ("styles.css", "app.js", "areas.json", "cidades.json", "adzuna-logo.png")


def projeto_temporario(tmp_path):
    raiz = tmp_path / "projeto"
    (raiz / "scripts").mkdir(parents=True)
    web = raiz / "web"
    assets = web / "assets"
    assets.mkdir(parents=True)
    shutil.copy2(SCRIPT, raiz / "scripts/build-web.sh")
    (raiz / "scripts/build-web.sh").chmod(0o755)
    for nome in HTMLS:
        (web / nome).write_text(f"<{nome}>", encoding="utf-8")
    (web / "config.js").write_text("window.RADAR_CONFIG = {};", encoding="utf-8")
    for nome in ASSETS:
        (assets / nome).write_text(f"legado:{nome}", encoding="utf-8")
    return raiz, web


def executar(raiz, env=None):
    ambiente = os.environ.copy()
    if env:
        ambiente.update(env)
    return subprocess.run(
        [str(raiz / "scripts/build-web.sh")],
        cwd=raiz,
        env=ambiente,
        capture_output=True,
        text=True,
    )


def npm_simulado(raiz, resultado="valido"):
    bin_dir = raiz / "bin"
    bin_dir.mkdir()
    log = raiz / "npm.log"
    web = raiz / "web"
    script = bin_dir / "npm"
    script.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                'printf \'%s\\n\' "$*" >> "$FAKE_NPM_LOG"',
                'if [ "$3" = "ci" ] && [ "$FAKE_NPM_OUTPUT" = "ci-falha" ]; then exit 6; fi',
                'if [ "$3" = "run" ] && [ "$4" = "build" ]; then',
                f"  {'exit 7' if resultado == 'falha' else ':'}",
                '  if [ "$FAKE_NPM_OUTPUT" = "valido" ] || '
                '[ "$FAKE_NPM_OUTPUT" = "symlink" ]; then',
                '    mkdir -p "$FAKE_WEB_DIR/dist/assets"',
                "    printf '<vite-index>' > \"$FAKE_WEB_DIR/dist/index.html\"",
                "    printf '<vite-termos>' > \"$FAKE_WEB_DIR/dist/termos.html\"",
                "    printf '<vite-privacidade>' > \"$FAKE_WEB_DIR/dist/privacidade.html\"",
                "    printf 'window.RADAR_CONFIG = {};' > \"$FAKE_WEB_DIR/dist/config.js\"",
                "    printf 'vite-app' > \"$FAKE_WEB_DIR/dist/assets/app.js\"",
                "    printf 'vite-areas' > \"$FAKE_WEB_DIR/dist/assets/areas.json\"",
                "    printf 'vite-cidades' > \"$FAKE_WEB_DIR/dist/assets/cidades.json\"",
                "    printf 'vite-logo' > \"$FAKE_WEB_DIR/dist/assets/adzuna-logo.png\"",
                '    if [ "$FAKE_NPM_OUTPUT" = "symlink" ]; then',
                '      ln -s "$FAKE_WEB_DIR/dist/index.html" "$FAKE_WEB_DIR/dist/assets/leak.js"',
                "    fi",
                '  elif [ "$FAKE_NPM_OUTPUT" = "proibido" ]; then',
                '    mkdir -p "$FAKE_WEB_DIR/dist/assets"',
                "    printf '<vite-index>' > \"$FAKE_WEB_DIR/dist/index.html\"",
                "    printf '<vite-termos>' > \"$FAKE_WEB_DIR/dist/termos.html\"",
                "    printf '<vite-privacidade>' > \"$FAKE_WEB_DIR/dist/privacidade.html\"",
                "    printf 'window.RADAR_CONFIG = {};' > \"$FAKE_WEB_DIR/dist/config.js\"",
                "    printf 'vite-areas' > \"$FAKE_WEB_DIR/dist/assets/areas.json\"",
                "    printf 'vite-cidades' > \"$FAKE_WEB_DIR/dist/assets/cidades.json\"",
                "    printf 'vite-logo' > \"$FAKE_WEB_DIR/dist/assets/adzuna-logo.png\"",
                "    printf 'secret' > \"$FAKE_WEB_DIR/dist/.env\"",
                '  elif [ "$FAKE_NPM_OUTPUT" = "sem-recurso" ]; then',
                '    mkdir -p "$FAKE_WEB_DIR/dist/assets"',
                "    printf '<vite-index>' > \"$FAKE_WEB_DIR/dist/index.html\"",
                "    printf '<vite-termos>' > \"$FAKE_WEB_DIR/dist/termos.html\"",
                "    printf '<vite-privacidade>' > \"$FAKE_WEB_DIR/dist/privacidade.html\"",
                "    printf 'window.RADAR_CONFIG = {};' > \"$FAKE_WEB_DIR/dist/config.js\"",
                "    printf 'vite-cidades' > \"$FAKE_WEB_DIR/dist/assets/cidades.json\"",
                "    printf 'vite-logo' > \"$FAKE_WEB_DIR/dist/assets/adzuna-logo.png\"",
                "  fi",
                "fi",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir, log, web


def manifesto_vite(web):
    (web / "package.json").write_text(
        json.dumps({"name": "radar-web", "private": True, "scripts": {"build": "vite build"}}),
        encoding="utf-8",
    )
    (web / "package-lock.json").write_text(
        json.dumps({"name": "radar-web", "lockfileVersion": 3, "packages": {"": {}}}),
        encoding="utf-8",
    )
    (web / "vite.config.js").write_text("export default {};", encoding="utf-8")


def ambiente_npm(raiz, bin_dir, log, web, output="valido"):
    return {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "FAKE_NPM_LOG": str(log),
        "FAKE_NPM_OUTPUT": output,
        "FAKE_WEB_DIR": str(web),
    }


def test_build_legado_copia_allowlist_e_limpa_saida_anterior(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    destino = web / "dist"
    destino.mkdir()
    (destino / "sobra.txt").write_text("não publicar", encoding="utf-8")
    (web / "assets/extra.woff2").write_text("fonte nova", encoding="utf-8")
    (web / "tests").mkdir()
    (web / "tests/nao-publicar.txt").write_text("teste", encoding="utf-8")
    (web / "node_modules").mkdir()
    (web / "node_modules/nao-publicar.js").write_text("dependência", encoding="utf-8")
    (web / ".env").write_text("segredo", encoding="utf-8")
    (web / "reports").mkdir()
    (web / "reports/coverage.txt").write_text("relatório", encoding="utf-8")

    resultado = executar(raiz)

    assert resultado.returncode == 0, resultado.stderr
    arquivos = {p.relative_to(destino).as_posix() for p in destino.rglob("*") if p.is_file()}
    esperados = set(HTMLS) | {"config.js"} | {f"assets/{nome}" for nome in ASSETS}
    assert arquivos == esperados
    assert not (destino / "sobra.txt").exists()
    arquivos_gerados = [p for p in destino.rglob("*") if p.is_file()]
    assert all("não-publicar" not in p.read_text(encoding="utf-8") for p in arquivos_gerados)


def test_manifesto_incompleto_falha_sem_cair_no_legado(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    (web / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build"}}), encoding="utf-8"
    )
    (web / "package-lock.json").write_text("{}", encoding="utf-8")
    destino = web / "dist"
    destino.mkdir()
    (destino / "legado.txt").write_text("não usar", encoding="utf-8")

    resultado = executar(raiz)

    assert resultado.returncode != 0
    assert "vite.config.js" in resultado.stderr
    assert (destino / "legado.txt").exists()
    assert not (destino / "index.html").exists()


def test_manifesto_sem_script_build_falha_antes_do_npm(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    (web / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
    (web / "package-lock.json").write_text("{}", encoding="utf-8")
    (web / "vite.config.js").write_text("export default {};", encoding="utf-8")
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web))

    assert resultado.returncode != 0
    assert not log.exists()
    assert "package.json" in resultado.stderr


def test_package_json_invalido_falha_antes_do_npm(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    (web / "package.json").write_text("não é JSON", encoding="utf-8")
    (web / "package-lock.json").write_text("{}", encoding="utf-8")
    (web / "vite.config.js").write_text("export default {};", encoding="utf-8")
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web))

    assert resultado.returncode != 0
    assert not log.exists()
    assert "package.json" in resultado.stderr


def test_build_vite_exige_npm_ci_e_nao_copia_arquivos_legados(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web))

    assert resultado.returncode == 0, resultado.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [
        f"--prefix {web} ci",
        f"--prefix {web} run build",
    ]
    assert (web / "dist/index.html").read_text(encoding="utf-8") == "<vite-index>"
    assert not (web / "dist/assets/styles.css").exists()
    arquivos_gerados = [p for p in (web / "dist").rglob("*") if p.is_file()]
    assert not any("legado:" in p.read_text(encoding="utf-8") for p in arquivos_gerados)


def test_falha_do_build_vite_nao_faz_fallback_legado(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz, resultado="falha")

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web))

    assert resultado.returncode != 0
    assert log.read_text(encoding="utf-8").splitlines() == [
        f"--prefix {web} ci",
        f"--prefix {web} run build",
    ]
    assert not (web / "dist/index.html").exists()
    arquivos_gerados = [p for p in (web / "dist").rglob("*") if p.is_file()]
    assert not any("legado:" in p.read_text(encoding="utf-8") for p in arquivos_gerados)


def test_falha_do_npm_ci_nao_chama_build_nem_faz_fallback(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web, output="ci-falha"))

    assert resultado.returncode != 0
    assert log.read_text(encoding="utf-8").splitlines() == [f"--prefix {web} ci"]
    assert not (web / "dist/index.html").exists()


def test_build_vite_sem_artefato_valido_falha(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)
    ambiente = ambiente_npm(raiz, bin_dir, log, web)
    ambiente["FAKE_NPM_OUTPUT"] = "vazio"

    resultado = executar(raiz, ambiente)

    assert resultado.returncode != 0
    assert "artefato" in resultado.stderr
    assert not (web / "dist/index.html").exists()


def test_recurso_publico_vite_ausente_falha(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web, output="sem-recurso"))

    assert resultado.returncode != 0
    assert "recurso público ausente" in resultado.stderr
    assert "assets/areas.json" in resultado.stderr


def test_artefato_vite_com_arquivo_proibido_falha(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web, output="proibido"))

    assert resultado.returncode != 0
    assert ".env" in resultado.stderr


def test_link_simbolico_do_destino_nao_e_removido(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    externo = tmp_path / "externo"
    externo.mkdir()
    destino_externo = externo / "dist"
    destino_externo.mkdir()
    (destino_externo / "preservar.txt").write_text("fora do destino", encoding="utf-8")
    os.symlink(destino_externo, web / "dist")

    resultado = executar(raiz)

    assert resultado.returncode != 0
    assert "link simbólico" in resultado.stderr
    assert (destino_externo / "preservar.txt").exists()
    assert (web / "dist").is_symlink()


def test_link_simbolico_de_web_nao_e_removido(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    externo = tmp_path / "web-real"
    web.rename(externo)
    os.symlink(externo, raiz / "web")
    (externo / "preservar.txt").write_text("fora do destino", encoding="utf-8")

    resultado = executar(raiz)

    assert resultado.returncode != 0
    assert "diretório web" in resultado.stderr
    assert (externo / "preservar.txt").exists()
    assert (raiz / "web").is_symlink()


def test_link_simbolico_de_arquivo_publico_falha_sem_copiar_fora_do_projeto(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    externo = tmp_path / "segredo.js"
    externo.write_text("segredo externo", encoding="utf-8")
    (web / "assets/app.js").unlink()
    os.symlink(externo, web / "assets/app.js")

    resultado = executar(raiz)

    assert resultado.returncode != 0
    assert "arquivo público ausente ou inválido" in resultado.stderr
    assert not (web / "dist/assets/app.js").exists()


def test_link_simbolico_no_artefato_vite_falha(tmp_path):
    raiz, web = projeto_temporario(tmp_path)
    manifesto_vite(web)
    bin_dir, log, _ = npm_simulado(raiz)

    resultado = executar(raiz, ambiente_npm(raiz, bin_dir, log, web, output="symlink"))

    assert resultado.returncode != 0
    assert "link simbólico no artefato" in resultado.stderr
