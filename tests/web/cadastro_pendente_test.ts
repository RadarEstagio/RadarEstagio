import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);

const pessoa = "00000000-0000-4000-8000-000000000001";
const sessao = "00000000-0000-4000-8000-00000000000a";

async function banco(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    create role anon;
    create role authenticated;
    create schema auth;
    create table auth.users (
      id uuid primary key, email text, created_at timestamptz default now(),
      email_confirmed_at timestamptz, raw_user_meta_data jsonb default '{}',
      confirmation_token text, confirmation_sent_at timestamptz
    );
    create table auth.identities (
      id uuid primary key default gen_random_uuid(),
      provider_id text not null,
      user_id uuid not null references auth.users (id) on delete cascade,
      identity_data jsonb not null,
      provider text not null default 'email'
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

function cadastro(resposta: boolean | null) {
  return {
    perfil: {
      curso: "Direito",
      periodo: 3,
      habilidades: ["Contratos"],
      cidade: "Rio de Janeiro, RJ",
      modalidade: "presencial",
      areas_de_interesse: [],
      pessoa_com_deficiencia: resposta,
    },
    aceitou_termos: true,
    aceita_emails: false,
    versao_dos_termos: "2026-09-05",
    sessao_id: sessao,
  };
}

async function criarConta(db: PGlite, resposta: boolean | null) {
  const metadados = { cadastro_radar: cadastro(resposta) };
  const daIdentidade = { sub: pessoa, email: "pessoa@x.com", email_verified: false, ...metadados };
  await db.query("insert into auth.users(id, email, raw_user_meta_data) values ($1, 'pessoa@x.com', $2)", [
    pessoa,
    metadados,
  ]);
  await db.query("insert into auth.identities(provider_id, user_id, identity_data) values ($1::text, $1::uuid, $2)", [
    pessoa,
    daIdentidade,
  ]);
  await db.query("update auth.users set raw_user_meta_data = $2 where id = $1", [pessoa, daIdentidade]);
  await enviarLink(db, "now() - interval '10 minutes'");
}

async function enviarLink(db: PGlite, quando: string) {
  await db.query(
    `update auth.users set confirmation_token = gen_random_uuid()::text, confirmation_sent_at = ${quando}
     where id = $1`,
    [pessoa],
  );
}

async function confirmar(db: PGlite) {
  await db.query("update auth.users set confirmation_token = '', email_confirmed_at = now() where id = $1", [
    pessoa,
  ]);
}

async function contar(db: PGlite, deOnde: string): Promise<number> {
  return (await db.query<{ n: number }>(`select count(*)::int n from ${deOnde}`)).rows[0].n;
}

async function respostaNoPerfil(db: PGlite): Promise<boolean | null | undefined> {
  const linhas = await db.query<{ resposta: boolean | null }>(
    "select pessoa_com_deficiencia resposta from perfis where user_id = $1",
    [pessoa],
  );
  return linhas.rows[0]?.resposta;
}

async function comoPessoa<T>(db: PGlite, acao: () => Promise<T>): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [pessoa]);
  await db.exec("set role authenticated");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

Deno.test("o link enviado na criação da conta mantém o cadastro e a confirmação cria o perfil", async () => {
  const db = await banco();
  try {
    await criarConta(db, true);
    assert.equal(await contar(db, "cadastros_pendentes"), 1);

    await confirmar(db);

    assert.equal(await respostaNoPerfil(db), true);
    assert.equal(await contar(db, "cadastros_pendentes"), 0);
  } finally {
    await db.close();
  }
});

Deno.test("novo link antes da confirmação descarta o cadastro e a resposta antiga não vira perfil", async () => {
  const db = await banco();
  try {
    await criarConta(db, true);

    await enviarLink(db, "now()");
    assert.equal(await contar(db, "cadastros_pendentes"), 0);

    await confirmar(db);
    assert.equal(await contar(db, "perfis"), 0);

    await comoPessoa(db, () => db.query("select concluir_meu_cadastro($1)", [cadastro(null)]));
    assert.equal(await respostaNoPerfil(db), null);
  } finally {
    await db.close();
  }
});

Deno.test("conta já confirmada não perde o perfil se o horário do link mudar", async () => {
  const db = await banco();
  try {
    await criarConta(db, false);
    await confirmar(db);

    await enviarLink(db, "now()");

    assert.equal(await respostaNoPerfil(db), false);
  } finally {
    await db.close();
  }
});
