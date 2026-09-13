import assert from "assert";
import { PGlite } from "pglite";

async function consulta(nome: string, parametros: [string, string][]): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = f?"""\n([\s\S]*?)"""$/gm)) {
    if (bloco[1] === nome) {
      return parametros.reduce(
        (sql, [parametro, tipo], indice) =>
          sql.replaceAll(`%(${parametro})s`, `$${indice + 1}::${tipo}`),
        bloco[2],
      );
    }
  }
  throw new Error(`constante ${nome} não encontrada em postgres.py`);
}

async function bancoComUsoDasFontes(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec("create role anon; create role authenticated;");
  await db.exec(
    await Deno.readTextFile(
      new URL("../../supabase/migrations/0020_uso_das_fontes.sql", import.meta.url),
    ),
  );
  return db;
}

Deno.test("fonte registrada com zero requisições conta como registro do dia", async () => {
  const db = await bancoComUsoDasFontes();
  try {
    const registrar = await consulta("SQL_REGISTRAR_REQUISICOES_DA_FONTE", [
      ["fonte", "text"],
      ["dia", "date"],
      ["requisicoes", "int"],
    ]);
    const temRegistro = await consulta("SQL_FONTE_TEM_REGISTRO_NO_DIA", [
      ["fonte", "text"],
      ["dia", "date"],
    ]);
    const consultar = async (fonte: string, dia: string) =>
      (await db.query<{ exists: boolean }>(temRegistro, [fonte, dia])).rows[0].exists;

    assert.equal(await consultar("adzuna:diario", "2026-09-13"), false);
    await db.query(registrar, ["adzuna:diario", "2026-09-13", 0]);

    assert.equal(await consultar("adzuna:diario", "2026-09-13"), true);
    assert.equal(await consultar("adzuna:diario", "2026-09-12"), false);
    assert.equal(await consultar("adzuna", "2026-09-13"), false);
  } finally {
    await db.close();
  }
});
