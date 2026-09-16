import assert from "assert";
import { PGlite } from "pglite";

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = f?"""\n([\s\S]*?)"""$/gm)) {
    if (bloco[1] === nome) return bloco[2];
  }
  throw new Error(`constante ${nome} não encontrada em postgres.py`);
}

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

Deno.test("resumo soma os eventos do site das últimas 24 horas e conta as horas no teto", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await db.exec(`
      insert into eventos_do_site_por_hora (hora, anonimo, total) values
        (date_trunc('hour', now(), 'UTC'), true, public.teto_de_eventos_do_site_por_hora(true)),
        (date_trunc('hour', now(), 'UTC'), false, 10),
        (date_trunc('hour', now(), 'UTC') - interval '3 hours', true, 100),
        (date_trunc('hour', now(), 'UTC') - interval '23 hours', false,
          public.teto_de_eventos_do_site_por_hora(false)),
        (date_trunc('hour', now(), 'UTC') - interval '30 hours', true, 500);
    `);

    const linha = (await db.query(await consulta("SQL_EVENTOS_DO_SITE_NAS_ULTIMAS_24_HORAS")))
      .rows[0];

    assert.deepEqual(linha, { visitantes: 2500, contas: 910, horas_no_teto: 2 });
  } finally {
    await db.close();
  }
});

Deno.test("sem eventos do site o resumo lê zero", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const linha = (await db.query(await consulta("SQL_EVENTOS_DO_SITE_NAS_ULTIMAS_24_HORAS")))
      .rows[0];

    assert.deepEqual(linha, { visitantes: 0, contas: 0, horas_no_teto: 0 });
  } finally {
    await db.close();
  }
});
