import { readFile, readdir, stat } from "node:fs/promises";
import { join, relative, resolve } from "node:path";
import { parse } from "@babel/parser";
import postcss from "postcss";

const extensoesJavaScript = new Set([".js", ".jsx", ".mjs"]);
const extensoesCss = new Set([".css"]);
const alvos = process.argv.slice(2);

async function arquivosEm(caminho) {
  const informacao = await stat(caminho);
  if (informacao.isFile()) return [caminho];
  const entradas = await readdir(caminho, { withFileTypes: true });
  const caminhos = await Promise.all(
    entradas
      .filter((entrada) => !entrada.name.startsWith(".") && entrada.name !== "node_modules" && entrada.name !== "dist")
      .map((entrada) => arquivosEm(join(caminho, entrada.name))),
  );
  return caminhos.flat();
}

function extensaoDe(caminho) {
  return caminho.slice(caminho.lastIndexOf("."));
}

function validarJavaScript(caminho, codigo) {
  const arvore = parse(codigo, {
    sourceType: "unambiguous",
    plugins: ["jsx", "importMeta", "topLevelAwait"],
    attachComment: true,
  });
  if (arvore.comments.length > 0) {
    throw new Error(`comentário encontrado em ${caminho}`);
  }
}

function validarCss(caminho, codigo) {
  const arvore = postcss.parse(codigo, { from: caminho });
  let encontrouComentario = false;
  arvore.walkComments(() => {
    encontrouComentario = true;
  });
  if (encontrouComentario) throw new Error(`comentário encontrado em ${caminho}`);
}

async function main() {
  if (alvos.length === 0) throw new Error("informe os diretórios ou arquivos a verificar");
  const caminhos = (await Promise.all(alvos.map((alvo) => arquivosEm(resolve(alvo))))).flat();
  for (const caminho of caminhos) {
    const extensao = extensaoDe(caminho);
    if (!extensoesJavaScript.has(extensao) && !extensoesCss.has(extensao)) continue;
    const codigo = await readFile(caminho, "utf8");
    if (extensoesJavaScript.has(extensao)) validarJavaScript(relative(process.cwd(), caminho), codigo);
    else validarCss(relative(process.cwd(), caminho), codigo);
  }
}

try {
  await main();
} catch (error) {
  process.stderr.write(`frontend-lint: ${error.message}\n`);
  process.exitCode = 1;
}
