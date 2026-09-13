import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const executar = promisify(execFile);
const script = fileURLToPath(new URL("../scripts/check-frontend-comments.mjs", import.meta.url));
const diretorios = [];

async function falhaAoVerificar(nome, conteudo) {
  const diretorio = await mkdtemp(join(tmpdir(), "radar-comentarios-"));
  diretorios.push(diretorio);
  await writeFile(join(diretorio, nome), conteudo);
  try {
    await executar(process.execPath, [script, diretorio]);
    return "";
  } catch (error) {
    return error.stderr;
  }
}

afterEach(async () => {
  await Promise.all(diretorios.splice(0).map((diretorio) => rm(diretorio, { recursive: true, force: true })));
});

describe("checagem de comentários do frontend", () => {
  it.each([
    ["modulo.js", 'const url = "https://radarestagio.pages.dev"; const barras = /\\/\\//; const texto = `/* não é comentário */`;'],
    ["componente.jsx", 'export const Aviso = () => <p title="// texto">{"/* texto */"}</p>;'],
    ["estilos.css", 'a { background: url("//cdn.example.com/logo.png"); content: "/* texto */"; }'],
  ])("aceita %s sem comentários, mesmo com barras em strings", async (nome, conteudo) => {
    expect(await falhaAoVerificar(nome, conteudo)).toBe("");
  });

  it.each([
    ["linha.js", "const valor = 1; // explica"],
    ["bloco.mjs", "/* explica */ export const valor = 1;"],
    ["jsx.jsx", "export const Aviso = () => <p>{/* explica */}</p>;"],
    ["estilos.css", "/* explica */ a { color: red; }"],
  ])("recusa comentário em %s", async (nome, conteudo) => {
    expect(await falhaAoVerificar(nome, conteudo)).toContain(`comentário encontrado`);
  });
});
