import assert from "assert";
import { PGlite } from "pglite";

const CHECK_VIOLADO = "23514";
const TETO_DAS_PROPRIEDADES = 256;

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

async function visitar(
  db: PGlite,
  propriedades: Record<string, unknown>,
  nome = "landing_visualizada",
): Promise<string | null> {
  await db.exec("set role anon");
  try {
    await db.query(
      "insert into eventos_produto(nome, sessao_id, propriedades) values ($1, $2, $3)",
      [nome, crypto.randomUUID(), propriedades],
    );
    return null;
  } catch (erro) {
    return (erro as { code?: string }).code ?? "sem código";
  } finally {
    await db.exec("reset role");
  }
}

Deno.test("a visita guarda o domínio de origem e a campanha", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const propriedades = {
      pagina: "/",
      referrer_dominio: "l.instagram.com",
      utm_source: "grupo-ccet",
      utm_medium: "whatsapp",
      utm_campaign: "outubro-2026",
    };

    assert.equal(await visitar(db, propriedades), null);
    assert.equal(await visitar(db, { pagina: "/" }), null);
    assert.equal(await visitar(db, {}), null);

    const gravada = await db.query<{ propriedades: Record<string, string> }>(
      "select propriedades from eventos_produto where propriedades ? 'utm_source'",
    );
    assert.deepEqual(gravada.rows[0].propriedades, propriedades);
  } finally {
    await db.close();
  }
});

Deno.test("a visita recusa propriedade fora da lista da origem", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const recusadas = [
      { pagina: "/", referrer: "https://l.instagram.com/?u=1" },
      { pagina: "/", email: "a@b.com" },
      { pagina: "/", utm_term: "estagio" },
      { pagina: "/", utm_content: "banner" },
    ];

    for (const propriedades of recusadas) {
      assert.equal(await visitar(db, propriedades), CHECK_VIOLADO, JSON.stringify(propriedades));
    }
  } finally {
    await db.close();
  }
});

Deno.test("a origem aceita só domínio e rótulo em letras minúsculas, sem caminho nem query", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const recusadas = [
      { referrer_dominio: "https://l.instagram.com/" },
      { referrer_dominio: "l.instagram.com/post/123" },
      { referrer_dominio: "L.Instagram.com" },
      { referrer_dominio: "" },
      { referrer_dominio: "a".repeat(41) },
      { referrer_dominio: 5 },
      { referrer_dominio: ["l.instagram.com"] },
      { utm_source: "Grupo CCET" },
      { utm_medium: "e-mail?x=1" },
      { utm_campaign: "a".repeat(25) },
      { utm_source: "voce@email.com" },
      { utm_campaign: { nome: "x" } },
    ];

    for (const propriedades of recusadas) {
      assert.equal(await visitar(db, propriedades), CHECK_VIOLADO, JSON.stringify(propriedades));
    }
    assert.equal(await visitar(db, { referrer_dominio: "a".repeat(40) }), null);
    assert.equal(await visitar(db, { utm_campaign: "a".repeat(24) }), null);
    assert.equal(await visitar(db, { utm_source: "grupo_ccet.2026-b" }), null);
  } finally {
    await db.close();
  }
});

Deno.test("a visita mais cheia que o site grava cabe no teto de 256 bytes", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const maisCheia = {
      pagina: "/".padEnd(40, "a"),
      referrer_dominio: "a".repeat(40),
      utm_source: "b".repeat(24),
      utm_medium: "c".repeat(24),
      utm_campaign: "d".repeat(24),
    };

    assert.equal(await visitar(db, maisCheia), null);
    const { rows } = await db.query<{ bytes: number }>(
      "select octet_length(propriedades::text)::int bytes from eventos_produto",
    );
    assert.ok(rows[0].bytes <= TETO_DAS_PROPRIEDADES, `${rows[0].bytes} bytes`);
    assert.equal(
      await visitar(db, { ...maisCheia, pagina: "x".repeat(200) }),
      CHECK_VIOLADO,
    );
  } finally {
    await db.close();
  }
});

Deno.test("os outros eventos do site seguem sem lista de propriedades", async () => {
  const db = await bancoComAsMigracoes();
  try {
    assert.equal(await visitar(db, { origem: "hero" }, "cta_cadastro_aberto"), null);
    assert.equal(
      await visitar(db, { quantidade: 3 }, "etapa_habilidades_concluida"),
      null,
    );
  } finally {
    await db.close();
  }
});

Deno.test("a lista da origem não revalida as visitas já gravadas", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const { rows } = await db.query<{ convalidated: boolean }>(
      "select convalidated from pg_constraint where conname = 'origem_da_visita_permitida'",
    );
    assert.equal(rows.length, 1);
    assert.equal(rows[0].convalidated, false);
  } finally {
    await db.close();
  }
});
