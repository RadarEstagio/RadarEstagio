import { lstat, readFile, readdir } from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";

const paginas = ["index.html", "termos.html", "privacidade.html"];
const obrigatorios = [...paginas, "config.js", "assets/app.js", "assets/areas.json", "assets/cidades.json", "assets/adzuna-logo.png"];
const proibidos = new Set(["package.json", "package-lock.json", "node_modules", "scripts", "tests", "coverage", "reports", ".git"]);
const referenciaNoHtml = /\s(?:src|href)="([^"]*)"/g;
const referenciaExterna = /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i;

async function exigirArquivo(destino, caminho) {
  const informacao = await lstat(caminho).catch(() => null);
  if (!informacao?.isFile()) throw new Error(`arquivo ausente no artefato: ${relative(destino, caminho)}`);
}

async function percorrer(destino, caminho) {
  const informacao = await lstat(caminho);
  if (informacao.isSymbolicLink()) throw new Error(`link simbólico no artefato: ${relative(destino, caminho)}`);
  if (!informacao.isDirectory()) return;
  for (const nome of await readdir(caminho)) {
    if (proibidos.has(nome) || nome.startsWith(".env")) {
      throw new Error(`arquivo proibido no artefato: ${relative(destino, join(caminho, nome))}`);
    }
    await percorrer(destino, join(caminho, nome));
  }
}

function arquivoDaReferencia(destino, pagina, referencia) {
  const caminho = referencia.split(/[?#]/)[0];
  const base = caminho.startsWith("/") ? destino : dirname(join(destino, pagina));
  const alvo = resolve(base, `.${caminho.startsWith("/") ? "" : "/"}${caminho}`);
  if (alvo !== destino && !alvo.startsWith(destino + sep)) {
    throw new Error(`referência fora do artefato em ${pagina}: ${referencia}`);
  }
  return caminho === "" || caminho.endsWith("/") ? join(alvo, "index.html") : alvo;
}

async function conferirReferencias(destino) {
  for (const pagina of paginas) {
    const html = await readFile(join(destino, pagina), "utf8");
    for (const [, referencia] of html.matchAll(referenciaNoHtml)) {
      if (referenciaExterna.test(referencia)) continue;
      await exigirArquivo(destino, arquivoDaReferencia(destino, pagina, referencia));
    }
  }
}

async function verificarArtefato(destino) {
  const raiz = await lstat(destino).catch(() => null);
  if (!raiz?.isDirectory()) throw new Error("destino do artefato inválido");
  await percorrer(destino, destino);
  for (const arquivo of obrigatorios) await exigirArquivo(destino, join(destino, arquivo));
  await conferirReferencias(destino);
}

try {
  await verificarArtefato(resolve(process.argv[2] ?? "dist"));
} catch (error) {
  process.stderr.write(`web-artifact: ${error.message}\n`);
  process.exitCode = 1;
}
