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

async function criarPerfilComEnvio(db: PGlite): Promise<void> {
  await db.query("insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())", [
    USUARIO,
    "pessoa@example.com",
  ]);
  await db.query(
    `insert into perfis(id, user_id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id)
     values ($1, $2, 'Computação', 3, '{}', 'Recife, PE', 'remoto', '123')`,
    [PERFIL, USUARIO],
  );
  await db.query(
    `insert into vagas(id, fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
     overriding system value values (1, 'adzuna', 'a1', 'Estágio', 'Empresa', 'Recife, PE', 'texto', 'https://x', now())`,
  );
  await db.query("insert into envios(perfil_id, vaga_id) values ($1, 1)", [PERFIL]);
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
