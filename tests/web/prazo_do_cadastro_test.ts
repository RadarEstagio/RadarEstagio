import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);

const semConfirmar = "00000000-0000-4000-8000-000000000001";
const recente = "00000000-0000-4000-8000-000000000002";
const confirmada = "00000000-0000-4000-8000-000000000003";
const reenviada = "00000000-0000-4000-8000-000000000004";
const semLink = "00000000-0000-4000-8000-000000000005";
const confirmadaSemPerfil = "00000000-0000-4000-8000-000000000006";
const sessaoDoCadastro = "00000000-0000-4000-8000-00000000000a";
const sessaoDeQuemFica = "00000000-0000-4000-8000-00000000000b";

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(new URL("../../radar/storage/postgres.py", import.meta.url));
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = f?"""\n([\s\S]*?)"""$/gm)) {
    if (bloco[1] === nome) return bloco[2].replaceAll("%(dias)s", "$1::int");
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
  return db;
}

function cadastro(sessao: string) {
  return {
    perfil: {
      curso: "Direito",
      periodo: 3,
      habilidades: ["Contratos"],
      cidade: "Rio de Janeiro, RJ",
      modalidade: "presencial",
      areas_de_interesse: [],
      pessoa_com_deficiencia: true,
    },
    aceitou_termos: true,
    aceita_emails: false,
    versao_dos_termos: "2026-09-05",
    sessao_id: sessao,
  };
}

async function contaCriadaHa(db: PGlite, id: string, dias: number, sessao: string) {
  await db.query(
    `insert into auth.users(id, email, created_at, raw_user_meta_data)
     values ($1, $2, now() - make_interval(days => $3), $4)`,
    [id, `${id}@x.com`, dias, { cadastro_radar: cadastro(sessao) }],
  );
  await db.query(
    `insert into auth.identities(provider_id, user_id, identity_data)
     values ($1::text, $1::uuid, jsonb_build_object('sub', $1::text))`,
    [id],
  );
  await db.query(
    `update cadastros_pendentes set recebido_em = now() - make_interval(days => $2) where user_id = $1`,
    [id, dias],
  );
  await db.query(
    `update auth.users set confirmation_sent_at = now() - make_interval(days => $2) where id = $1`,
    [id, dias],
  );
}

async function contar(db: PGlite, deOnde: string, parametros: unknown[] = []): Promise<number> {
  return (await db.query<{ n: number }>(`select count(*)::int n from ${deOnde}`, parametros)).rows[0].n;
}

async function anonimosDa(db: PGlite, sessao: string): Promise<number> {
  return await contar(db, "eventos_produto where sessao_id = $1 and user_id is null", [sessao]);
}

async function pendenteDe(db: PGlite, id: string): Promise<number> {
  return await contar(db, "cadastros_pendentes where user_id = $1", [id]);
}

Deno.test("cadastro pendente vence dois dias depois de recebido, sem apagar a conta", async () => {
  const db = await banco();
  try {
    await contaCriadaHa(db, semConfirmar, 3, sessaoDoCadastro);
    await contaCriadaHa(db, recente, 1, sessaoDoCadastro);

    const apagados = await db.query(await consulta("SQL_APAGAR_CADASTROS_PENDENTES"), [2]);

    assert.equal(apagados.affectedRows, 1);
    assert.equal(await pendenteDe(db, semConfirmar), 0);
    assert.equal(await pendenteDe(db, recente), 1);
    assert.equal(await contar(db, "auth.users"), 2);
  } finally {
    await db.close();
  }
});

Deno.test("conta sem confirmar 30 dias depois do último link some com o cadastro e os eventos", async () => {
  const db = await banco();
  try {
    await contaCriadaHa(db, semConfirmar, 31, sessaoDoCadastro);
    await contaCriadaHa(db, recente, 29, sessaoDeQuemFica);
    await contaCriadaHa(db, reenviada, 40, sessaoDeQuemFica);
    await db.query("update auth.users set confirmation_sent_at = now() - interval '1 day' where id = $1", [
      reenviada,
    ]);
    await contaCriadaHa(db, confirmada, 90, sessaoDeQuemFica);
    await db.query("update auth.users set email_confirmed_at = now() - interval '89 days' where id = $1", [
      confirmada,
    ]);
    await db.query(
      "insert into auth.users(id, email, created_at) values ($1, 'equipe@x.com', now() - interval '90 days')",
      [semLink],
    );
    await db.query(
      `insert into auth.users(id, email, confirmation_sent_at, email_confirmed_at)
       values ($1, 'sem-perfil@x.com', now() - interval '90 days', now() - interval '89 days')`,
      [confirmadaSemPerfil],
    );
    await db.query(
      `insert into eventos_produto(nome, origem, sessao_id, user_id) values
         ('landing_visualizada', 'web', $1, null),
         ('etapa_perfil_concluida', 'web', $1, null),
         ('landing_visualizada', 'web', $2, null)`,
      [sessaoDoCadastro, sessaoDeQuemFica],
    );

    const apagadas = await db.query(await consulta("SQL_APAGAR_CONTAS_NAO_CONFIRMADAS"), [30]);

    assert.equal(apagadas.affectedRows, 1);
    assert.equal(await contar(db, "auth.users where id = $1", [semConfirmar]), 0);
    assert.equal(await contar(db, "auth.identities where user_id = $1", [semConfirmar]), 0);
    assert.equal(await contar(db, "eventos_produto where user_id = $1", [semConfirmar]), 0);
    assert.equal(await anonimosDa(db, sessaoDoCadastro), 0);
    for (const mantida of [recente, reenviada, confirmada, semLink, confirmadaSemPerfil]) {
      assert.equal(await contar(db, "auth.users where id = $1", [mantida]), 1, mantida);
    }
    assert.equal(await contar(db, "eventos_produto where user_id = $1", [recente]), 1);
    assert.equal(await contar(db, "perfis where user_id = $1", [confirmada]), 1);
    assert.equal(await anonimosDa(db, sessaoDeQuemFica), 1);
  } finally {
    await db.close();
  }
});

Deno.test("conta sem confirmar que já tem perfil não é apagada pelo prazo do cadastro", async () => {
  const db = await banco();
  try {
    await db.query(
      "insert into auth.users(id, email, confirmation_sent_at) values ($1, 'a@x.com', now() - interval '60 days')",
      [semConfirmar],
    );
    await db.query(
      `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade)
       values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial')`,
      [semConfirmar],
    );

    const apagadas = await db.query(await consulta("SQL_APAGAR_CONTAS_NAO_CONFIRMADAS"), [30]);

    assert.equal(apagadas.affectedRows, 0);
    assert.equal(await contar(db, "perfis where user_id = $1", [semConfirmar]), 1);
  } finally {
    await db.close();
  }
});
