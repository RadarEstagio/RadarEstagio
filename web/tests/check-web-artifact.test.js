import { execFile } from "node:child_process";
import { mkdir, mkdtemp, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const executar = promisify(execFile);
const script = resolve(dirname(fileURLToPath(import.meta.url)), "../scripts/check-web-artifact.mjs");
const diretorios = [];

async function artefatoValido() {
  const destino = await mkdtemp(join(tmpdir(), "radar-artefato-"));
  diretorios.push(destino);
  await mkdir(join(destino, "assets"));
  await writeFile(
    join(destino, "index.html"),
    '<link href="./assets/index.css"><script src="config.js"></script><script src="assets/app.js?v=1"></script>' +
      '<img src="./assets/adzuna-logo.png"><a href="termos.html#topo">Termos</a><a href="https://www.adzuna.com.br">Jobs</a>' +
      '<a href="#faq">FAQ</a><a href="./">Início</a><a href="mailto:contato@example.com">Contato</a>',
  );
  await writeFile(join(destino, "termos.html"), '<link href="/assets/index.css"><a href="index.html">Início</a>');
  await writeFile(join(destino, "privacidade.html"), '<link href="./assets/index.css">');
  for (const arquivo of ["config.js", "assets/app.js", "assets/areas.json", "assets/cidades.json", "assets/adzuna-logo.png", "assets/index.css"]) {
    await writeFile(join(destino, arquivo), arquivo);
  }
  return destino;
}

async function falhaDaVerificacao(destino) {
  try {
    await executar(process.execPath, [script, destino]);
    return "";
  } catch (error) {
    return error.stderr;
  }
}

afterEach(async () => {
  await Promise.all(diretorios.splice(0).map((diretorio) => rm(diretorio, { recursive: true, force: true })));
});

describe("verificação do artefato publicado", () => {
  it("aceita artefato com recursos e referências locais presentes", async () => {
    expect(await falhaDaVerificacao(await artefatoValido())).toBe("");
  });

  it.each(["config.js", "assets/areas.json", "assets/cidades.json", "assets/adzuna-logo.png"])(
    "recusa artefato sem %s",
    async (arquivo) => {
      const destino = await artefatoValido();
      await rm(join(destino, arquivo));
      expect(await falhaDaVerificacao(destino)).toContain(arquivo);
    },
  );

  it("recusa referência local que não existe na saída", async () => {
    const destino = await artefatoValido();
    await writeFile(join(destino, "termos.html"), '<link href="assets/styles.css?v=2">');
    expect(await falhaDaVerificacao(destino)).toContain("assets/styles.css");
  });

  it("recusa referência que aponta para fora do artefato", async () => {
    const destino = await artefatoValido();
    await writeFile(join(destino, "privacidade.html"), '<script src="../segredo.js"></script>');
    expect(await falhaDaVerificacao(destino)).toContain("fora do artefato");
  });

  it.each(["node_modules", "package.json", ".env.local", "tests"])("recusa %s na saída", async (nome) => {
    const destino = await artefatoValido();
    await writeFile(join(destino, "assets", nome), "");
    expect(await falhaDaVerificacao(destino)).toContain(`arquivo proibido no artefato: assets/${nome}`);
  });

  it("recusa link simbólico na saída", async () => {
    const destino = await artefatoValido();
    await symlink(join(destino, "index.html"), join(destino, "assets", "atalho.html"));
    expect(await falhaDaVerificacao(destino)).toContain("link simbólico");
  });
});
