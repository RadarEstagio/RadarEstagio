import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);

const vencida = "00000000-0000-4000-8000-000000000001";
const naCarencia = "00000000-0000-4000-8000-000000000002";
const noUltimoDia = "00000000-0000-4000-8000-000000000003";
const ativa = "00000000-0000-4000-8000-000000000004";
const pausada = "00000000-0000-4000-8000-000000000005";
const sessaoDaExcluida = "00000000-0000-4000-8000-00000000000a";
const sessaoDeQuemFica = "00000000-0000-4000-8000-00000000000b";
const sessaoDividida = "00000000-0000-4000-8000-00000000000c";

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(new URL("../../radar/storage/postgres.py", import.meta.url));
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = f?"""\n([\s\S]*?)"""$/gm)) {
    if (bloco[1] === nome) {
      return bloco[2].replaceAll("%(dias)s", "$1::int").replaceAll("%(sessoes)s", "$1");
    }
  }
  throw new Error(`constante ${nome} não encontrada em postgres.py`);
}

async function banco(): Promise<PGlite> {
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
    grant usage on schema public, auth to anon, authenticated;
    grant execute on function auth.uid() to anon, authenticated;
  `);
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  for (const nome of nomes.sort()) await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
  await db.exec(`
    insert into vagas (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
    values ('adzuna', '1', 'Estágio', 'Empresa', 'Rio de Janeiro', 'descricao', 'https://x/1', now());
  `);
  return db;
}

async function conta(db: PGlite, id: string): Promise<string> {
  await db.query("insert into auth.users(id, email) values ($1, $2)", [id, `${id}@x.com`]);
  await db.query(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id)
     values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial', $2)`,
    [id, `chat-${id}`],
  );
  return await perfilDe(db, id);
}

async function excluidaEm(db: PGlite, id: string, marca: string): Promise<void> {
  await db.query(
    `update perfis
     set excluida_em = ${marca},
         telegram_chat_id = null,
         token_vinculo = gen_random_uuid()
     where user_id = $1`,
    [id],
  );
}

async function excluidaHaMenosDe(db: PGlite, id: string, dias: number): Promise<void> {
  await excluidaEm(db, id, `now() - interval '${dias} days' + interval '1 minute'`);
}

async function excluidaHaMaisDe(db: PGlite, id: string, dias: number): Promise<void> {
  await excluidaEm(db, id, `now() - interval '${dias} days' - interval '1 minute'`);
}

async function pausar(db: PGlite, id: string): Promise<void> {
  await db.query("update perfis set ativo = false where user_id = $1", [id]);
}

async function perfilDe(db: PGlite, id: string): Promise<string> {
  return (await db.query<{ id: string }>("select id from perfis where user_id = $1", [id])).rows[0]
    .id;
}

async function historicoDa(db: PGlite, id: string, sessao: string): Promise<void> {
  const perfil = await perfilDe(db, id);
  const vaga = (await db.query<{ id: number }>("select id from vagas limit 1")).rows[0].id;
  await db.query(
    "insert into avaliacoes(perfil_id, vaga_id, nota, modelo) values ($1, $2, 80, 'gemini')",
    [perfil, vaga],
  );
  await db.query("insert into envios(perfil_id, vaga_id) values ($1, $2)", [perfil, vaga]);
  await db.query(
    `insert into eventos_produto(nome, origem, sessao_id, user_id, perfil_id, vaga_id)
     values ('vaga_aberta', 'telegram', $2, $1, $3, $4)`,
    [id, sessao, perfil, vaga],
  );
  await db.query(
    `insert into eventos_produto(nome, origem, sessao_id, user_id)
     values ('etapa_perfil_concluida', 'web', $2, $1)`,
    [id, sessao],
  );
  await db.query(
    "insert into eventos_produto(nome, origem, sessao_id) values ('landing_visualizada', 'web', $1)",
    [sessao],
  );
}

async function apagarContasExcluidas(db: PGlite, dias: number): Promise<number> {
  const sessoes = (
    await db.query<{ sessao_id: string }>(await consulta("SQL_SESSOES_DAS_CONTAS_EXCLUIDAS"), [
      dias,
    ])
  ).rows.map((linha) => linha.sessao_id);
  if (sessoes.length > 0) {
    await db.query(await consulta("SQL_APAGAR_EVENTOS_ANONIMOS"), [sessoes]);
  }
  const apagadas = await db.query(await consulta("SQL_APAGAR_CONTAS_EXCLUIDAS"), [dias]);
  return apagadas.affectedRows ?? 0;
}

async function contar(db: PGlite, deOnde: string, parametros: unknown[] = []): Promise<number> {
  return (await db.query<{ n: number }>(`select count(*)::int n from ${deOnde}`, parametros)).rows[0]
    .n;
}

async function eventosDa(db: PGlite, id: string): Promise<number> {
  return await contar(db, "eventos_produto where user_id = $1", [id]);
}

async function anonimosDa(db: PGlite, sessao: string): Promise<number> {
  return await contar(db, "eventos_produto where sessao_id = $1 and user_id is null", [sessao]);
}

Deno.test("conta excluída dentro da carência não é apagada", async () => {
  const db = await banco();
  try {
    await conta(db, naCarencia);
    await conta(db, noUltimoDia);
    await historicoDa(db, naCarencia, sessaoDaExcluida);
    await excluidaHaMenosDe(db, naCarencia, 59);
    await excluidaHaMenosDe(db, noUltimoDia, 60);
    const eventos = await eventosDa(db, naCarencia);

    assert.equal(await apagarContasExcluidas(db, 60), 0);

    assert.equal(await contar(db, "auth.users"), 2);
    assert.equal(await contar(db, "perfis"), 2);
    assert.equal(await contar(db, "avaliacoes"), 1);
    assert.equal(await contar(db, "envios"), 1);
    assert.equal(await eventosDa(db, naCarencia), eventos);
    assert.equal(await anonimosDa(db, sessaoDaExcluida), 1);
  } finally {
    await db.close();
  }
});

Deno.test("no dia seguinte ao prazo a conta some com perfil, avaliações, envios e eventos", async () => {
  const db = await banco();
  try {
    const perfil = await conta(db, vencida);
    await historicoDa(db, vencida, sessaoDaExcluida);
    await excluidaHaMaisDe(db, vencida, 61);

    assert.equal(await apagarContasExcluidas(db, 60), 1);

    assert.equal(await contar(db, "auth.users where id = $1", [vencida]), 0);
    assert.equal(await contar(db, "perfis where id = $1", [perfil]), 0);
    assert.equal(await contar(db, "avaliacoes where perfil_id = $1", [perfil]), 0);
    assert.equal(await contar(db, "envios where perfil_id = $1", [perfil]), 0);
    assert.equal(await eventosDa(db, vencida), 0);
    assert.equal(await contar(db, "eventos_produto where perfil_id = $1", [perfil]), 0);
    assert.equal(await anonimosDa(db, sessaoDaExcluida), 0);
    assert.equal(await contar(db, "vagas"), 1);
  } finally {
    await db.close();
  }
});

Deno.test("conta ativa e conta pausada não são tocadas pelo apagamento", async () => {
  const db = await banco();
  try {
    await conta(db, ativa);
    await conta(db, pausada);
    await conta(db, vencida);
    await historicoDa(db, ativa, sessaoDeQuemFica);
    await historicoDa(db, pausada, sessaoDeQuemFica);
    await pausar(db, pausada);
    await excluidaHaMaisDe(db, vencida, 61);
    const daAtiva = await eventosDa(db, ativa);
    const daPausada = await eventosDa(db, pausada);

    assert.equal(await apagarContasExcluidas(db, 60), 1);

    for (const mantida of [ativa, pausada]) {
      assert.equal(await contar(db, "auth.users where id = $1", [mantida]), 1, mantida);
      assert.equal(await contar(db, "perfis where user_id = $1", [mantida]), 1, mantida);
    }
    assert.equal(await eventosDa(db, ativa), daAtiva);
    assert.equal(await eventosDa(db, pausada), daPausada);
    assert.equal(await contar(db, "avaliacoes"), 2);
    assert.equal(await contar(db, "envios"), 2);
    assert.equal(await anonimosDa(db, sessaoDeQuemFica), 2);
  } finally {
    await db.close();
  }
});

Deno.test("o navegador dividido perde os eventos sem dono, não os de quem fica", async () => {
  const db = await banco();
  try {
    await conta(db, vencida);
    await conta(db, ativa);
    await conta(db, naCarencia);
    await historicoDa(db, vencida, sessaoDividida);
    await historicoDa(db, ativa, sessaoDividida);
    await historicoDa(db, naCarencia, sessaoDeQuemFica);
    await excluidaHaMaisDe(db, vencida, 61);
    await excluidaHaMenosDe(db, naCarencia, 59);
    const daAtiva = await eventosDa(db, ativa);
    const daCarencia = await eventosDa(db, naCarencia);

    assert.equal(await apagarContasExcluidas(db, 60), 1);

    assert.equal(await anonimosDa(db, sessaoDividida), 0);
    assert.equal(await eventosDa(db, ativa), daAtiva);
    assert.equal(await anonimosDa(db, sessaoDeQuemFica), 1);
    assert.equal(await eventosDa(db, naCarencia), daCarencia);
  } finally {
    await db.close();
  }
});
