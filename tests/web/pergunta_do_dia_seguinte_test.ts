import assert from "assert";
import { PGlite } from "pglite";

const PERFIL = "00000000-0000-4000-8000-0000000000a1";
const USUARIO = "00000000-0000-4000-8000-0000000000b1";

async function bancoComAsMigracoes(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    create role anon;
    create role authenticated;
    create schema auth;
    create table auth.users (
      id uuid primary key, email text, created_at timestamptz default now(),
      email_confirmed_at timestamptz, raw_user_meta_data jsonb default '{}',
      confirmation_sent_at timestamptz
    );
    create table auth.identities (
      id uuid primary key default gen_random_uuid(), provider_id text not null,
      user_id uuid not null references auth.users (id) on delete cascade,
      identity_data jsonb not null, provider text not null default 'email'
    );
    create function auth.uid() returns uuid language sql stable as
      $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
    grant usage on schema public, auth to authenticated, anon;
    grant execute on function auth.uid() to authenticated, anon;
  `);
  const diretorio = new URL("../../supabase/migrations/", import.meta.url);
  const arquivos: string[] = [];
  for await (const entrada of Deno.readDir(diretorio)) {
    if (entrada.name.endsWith(".sql")) arquivos.push(entrada.name);
  }
  for (const arquivo of arquivos.sort()) {
    await db.exec(await Deno.readTextFile(new URL(arquivo, diretorio)));
  }
  return db;
}

const OUTRO_PERFIL = "00000000-0000-4000-8000-0000000000a2";
const OUTRO_USUARIO = "00000000-0000-4000-8000-0000000000b2";
const HOJE = "2026-10-06";

async function criarPerfil(db: PGlite, perfil: string, usuario: string, chat: string) {
  await db.query("insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())", [
    usuario,
    `${usuario}@example.com`,
  ]);
  await db.query(
    `insert into perfis(id, user_id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id)
     values ($1, $2, 'Computação', 3, '{}', 'Recife, PE', 'remoto', $3)`,
    [perfil, usuario, chat],
  );
}

async function criarVaga(db: PGlite, id: number, titulo: string, empresa: string) {
  await db.query(
    `insert into vagas(id, fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
     overriding system value values ($1, 'adzuna', $2, $3, $4, 'Recife, PE', 'texto', 'https://x', now())`,
    [id, `a${id}`, titulo, empresa],
  );
}

async function criarEnvio(db: PGlite, perfil: string, vagaId: number, token: string) {
  await db.query(
    "insert into envios(perfil_id, vaga_id, token, enviada_em) values ($1, $2, $3, '2026-09-30 12:00Z')",
    [perfil, vagaId, token],
  );
}

async function registrarEvento(
  db: PGlite,
  nome: string,
  perfil: string,
  usuario: string,
  vagaId: number,
  ocorridoEm: string,
) {
  await db.query(
    `insert into eventos_produto(nome, origem, user_id, perfil_id, vaga_id, ocorrido_em)
     values ($1, 'telegram', $2, $3, $4, $5)`,
    [nome, usuario, perfil, vagaId, ocorridoEm],
  );
}

const TOKEN_A = "11111111-1111-4111-8111-111111111111";
const TOKEN_B = "22222222-2222-4222-8222-222222222222";
const TOKEN_C = "33333333-3333-4333-8333-333333333333";

async function criarPerfilComEnvio(db: PGlite): Promise<void> {
  await criarPerfil(db, PERFIL, USUARIO, "123");
  await criarVaga(db, 1, "Estágio", "Empresa");
  await criarEnvio(db, PERFIL, 1, TOKEN_A);
}

type Pendente = { token: string; titulo: string; empresa: string };

async function aberturaSemResposta(
  db: PGlite,
  perfil = PERFIL,
  hoje = HOJE,
): Promise<Pendente | null> {
  const sql = (await Deno.readTextFile(
    new URL("../../radar/storage/abertura_sem_resposta.sql", import.meta.url),
  ))
    .replaceAll("%(perfil_id)s", `'${perfil}'::uuid`)
    .replaceAll("%(hoje)s", `date '${hoje}'`);
  return (await db.query<Pendente>(sql)).rows[0] ?? null;
}

async function cenarioComTresVagas(db: PGlite): Promise<void> {
  await criarPerfil(db, PERFIL, USUARIO, "123");
  await criarVaga(db, 1, "Estágio A", "Alfa");
  await criarVaga(db, 2, "Estágio B", "Beta");
  await criarVaga(db, 3, "Estágio C", "Gama");
  await criarEnvio(db, PERFIL, 1, TOKEN_A);
  await criarEnvio(db, PERFIL, 2, TOKEN_B);
  await criarEnvio(db, PERFIL, 3, TOKEN_C);
}

Deno.test("o envio nasce sem pergunta do dia seguinte", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await criarPerfilComEnvio(db);

    const { rows } = await db.query<{ pergunta: string | null }>(
      "select pergunta_do_dia_seguinte_em as pergunta from envios",
    );

    assert.equal(rows.length, 1);
    assert.equal(rows[0].pergunta, null);
  } finally {
    await db.close();
  }
});

Deno.test("a pergunta sai sobre a abertura de ontem em Brasília, com título e empresa", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await criarPerfilComEnvio(db);
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 18:00Z");

    assert.deepEqual(await aberturaSemResposta(db), {
      token: TOKEN_A,
      titulo: "Estágio",
      empresa: "Empresa",
    });
  } finally {
    await db.close();
  }
});

Deno.test("o dia é o de Brasília: 23h30 de ontem entra, 0h30 de hoje e 23h30 de anteontem não", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await criarPerfilComEnvio(db);

    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-06 03:30Z");
    assert.equal(await aberturaSemResposta(db), null);
    await db.exec("delete from eventos_produto");

    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 02:30Z");
    assert.equal(await aberturaSemResposta(db), null);
    await db.exec("delete from eventos_produto");

    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-06 02:30Z");
    assert.equal((await aberturaSemResposta(db))?.token, TOKEN_A);
  } finally {
    await db.close();
  }
});

Deno.test("entre várias aberturas de ontem vale a mais recente", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await cenarioComTresVagas(db);
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 13:00Z");
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 2, "2026-10-05 21:00Z");
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 3, "2026-10-05 15:00Z");

    assert.equal((await aberturaSemResposta(db))?.token, TOKEN_B);
  } finally {
    await db.close();
  }
});

Deno.test("vaga já respondida sai da fila e a mais recente sem resposta ocupa o lugar", async () => {
  for (const resposta of ["vaga_util", "vaga_irrelevante", "candidatura_iniciada"]) {
    const db = await bancoComAsMigracoes();
    try {
      await cenarioComTresVagas(db);
      await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 13:00Z");
      await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 2, "2026-10-05 21:00Z");
      await registrarEvento(db, resposta, PERFIL, USUARIO, 2, "2026-10-05 22:00Z");

      assert.equal((await aberturaSemResposta(db))?.token, TOKEN_A, resposta);
    } finally {
      await db.close();
    }
  }
});

Deno.test("sem abertura ontem, com abertura só hoje ou só antes, não há pergunta", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await cenarioComTresVagas(db);
    assert.equal(await aberturaSemResposta(db), null);

    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-06 12:00Z");
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 2, "2026-10-04 12:00Z");
    assert.equal(await aberturaSemResposta(db), null);
  } finally {
    await db.close();
  }
});

Deno.test("a vaga perguntada uma vez não volta e só uma pergunta sai por pessoa por dia", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await cenarioComTresVagas(db);
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 13:00Z");
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 2, "2026-10-05 21:00Z");

    await db.exec(
      `update envios set pergunta_do_dia_seguinte_em = '2026-10-06 10:23Z' where vaga_id = 2`,
    );
    assert.equal(await aberturaSemResposta(db), null);

    await db.exec(
      `update envios set pergunta_do_dia_seguinte_em = '2026-10-05 10:23Z' where vaga_id = 2`,
    );
    assert.equal((await aberturaSemResposta(db))?.token, TOKEN_A);
  } finally {
    await db.close();
  }
});

Deno.test("a pergunta de outra pessoa não conta para esta nem vaza para ela", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await cenarioComTresVagas(db);
    await criarPerfil(db, OUTRO_PERFIL, OUTRO_USUARIO, "456");
    await criarEnvio(db, OUTRO_PERFIL, 1, "44444444-4444-4444-8444-444444444444");
    await registrarEvento(db, "vaga_aberta", PERFIL, USUARIO, 1, "2026-10-05 13:00Z");
    await db.exec(
      `update envios set pergunta_do_dia_seguinte_em = '2026-10-06 10:23Z' where perfil_id = '${OUTRO_PERFIL}'`,
    );

    assert.equal((await aberturaSemResposta(db))?.token, TOKEN_A);
    assert.equal(await aberturaSemResposta(db, OUTRO_PERFIL), null);
  } finally {
    await db.close();
  }
});
