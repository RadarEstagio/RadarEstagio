import assert from "assert";
import { PGlite } from "pglite";

async function fusoDaEntrega(): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/domain/datas.py", import.meta.url),
  );
  const encontrado = fonte.match(/^FUSO_DA_ENTREGA = ZoneInfo\("([^"]+)"\)$/m);
  assert.ok(encontrado, "FUSO_DA_ENTREGA não encontrado em datas.py");
  return encontrado[1];
}

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  const fuso = await fusoDaEntrega();
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = f?"""\n([\s\S]*?)"""$/gm)) {
    if (bloco[1] === nome) {
      return bloco[2]
        .replaceAll("{FUSO_DA_ENTREGA.key}", fuso)
        .replaceAll("%(vaga_id)s", "$1")
        .replaceAll("%(dia)s", "$2::date");
    }
  }
  throw new Error(`constante ${nome} não encontrada em postgres.py`);
}

async function bancoComUmaVaga(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    set timezone = 'UTC';
    create table public.vagas (
      id bigint generated always as identity primary key,
      fonte text not null,
      id_externo text not null,
      titulo text not null,
      empresa text not null,
      localizacao text not null,
      descricao text not null,
      url text not null,
      publicada_em timestamptz not null,
      modalidade text,
      coletada_em timestamptz not null default now(),
      unique (fonte, id_externo)
    );
  `);
  for (const migracao of ["0010_extracao_das_vagas.sql", "0022_dias_sem_extracao.sql"]) {
    await db.exec(
      await Deno.readTextFile(
        new URL(`../../supabase/migrations/${migracao}`, import.meta.url),
      ),
    );
  }
  await db.exec(`
    insert into vagas (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
    values ('adzuna', '1', 'Estágio', 'Empresa', 'Rio de Janeiro', 'desc', 'https://x/1', '2026-09-01');
  `);
  return db;
}

async function registrar(db: PGlite, dia: string): Promise<number> {
  const linhas = await db.query<{ dias_sem_extracao: number }>(
    await consulta("SQL_REGISTRAR_VAGA_SEM_EXTRACAO"),
    [1, dia],
  );
  return linhas.rows[0].dias_sem_extracao;
}

Deno.test("cada dia diferente sem extração soma um e o mesmo dia conta uma vez", async () => {
  const db = await bancoComUmaVaga();
  try {
    assert.equal(await registrar(db, "2026-09-10"), 1);
    assert.equal(await registrar(db, "2026-09-10"), 1);
    assert.equal(await registrar(db, "2026-09-11"), 2);
    assert.equal(await registrar(db, "2026-09-13"), 3);
  } finally {
    await db.close();
  }
});

Deno.test("extração feita depois da última falta recomeça a contagem", async () => {
  const db = await bancoComUmaVaga();
  try {
    assert.equal(await registrar(db, "2026-09-10"), 1);
    assert.equal(await registrar(db, "2026-09-11"), 2);
    await db.exec(`
      update vagas set extracao = '{}', extraida_em = '2026-09-11 15:00+00',
        modelo_extracao = 'versao-antiga';
    `);
    assert.equal(await registrar(db, "2026-09-12"), 1);
  } finally {
    await db.close();
  }
});

Deno.test("extração anterior à primeira falta não recomeça a contagem", async () => {
  const db = await bancoComUmaVaga();
  try {
    await db.exec(`
      update vagas set extracao = '{}', extraida_em = '2026-08-01 10:00+00',
        modelo_extracao = 'versao-antiga';
    `);
    assert.equal(await registrar(db, "2026-09-10"), 1);
    assert.equal(await registrar(db, "2026-09-11"), 2);
  } finally {
    await db.close();
  }
});

Deno.test("extração às 22:00 de Brasília conta no dia de Brasília, não no da sessão", async () => {
  const db = await bancoComUmaVaga();
  try {
    await db.exec(`
      update vagas set extracao = '{}', extraida_em = '2026-09-10 22:00:00-03',
        modelo_extracao = 'versao-antiga';
    `);
    const dias = [];
    for (const dia of ["2026-09-11", "2026-09-12", "2026-09-13"]) {
      dias.push(await registrar(db, dia));
    }
    assert.deepEqual(dias, [1, 2, 3]);
  } finally {
    await db.close();
  }
});
