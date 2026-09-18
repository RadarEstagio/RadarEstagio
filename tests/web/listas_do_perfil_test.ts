import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const MIGRACAO_DAS_DIMENSOES = "0031_";

const dono = "00000000-0000-4000-8000-000000000001";
const areasEmDuasDimensoes = `array[
  array['direito_contencioso', 'compliance'],
  array['direito_societario', 'direito_trabalhista']
]::text[]`;
const habilidadesEmDuasDimensoes = `array[array['Excel', 'Word'], array['SQL', 'Python']]::text[]`;

async function migracoes(): Promise<string[]> {
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  return nomes.sort();
}

async function aplicar(db: PGlite, nomes: string[]) {
  for (const nome of nomes) await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
}

async function bancoAntesDasDimensoes(): Promise<{ db: PGlite; restantes: string[] }> {
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
  const nomes = await migracoes();
  const indice = nomes.findIndex((nome) => nome.startsWith(MIGRACAO_DAS_DIMENSOES));
  assert.notEqual(indice, -1, `migração ${MIGRACAO_DAS_DIMENSOES} não encontrada`);
  await aplicar(db, nomes.slice(0, indice));
  return { db, restantes: nomes.slice(indice) };
}

async function banco(): Promise<PGlite> {
  const { db, restantes } = await bancoAntesDasDimensoes();
  await aplicar(db, restantes);
  return db;
}

async function perfilDe(db: PGlite, id: string) {
  await db.query("insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())", [
    id,
    `${id}@x.com`,
  ]);
  await db.query(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade)
     values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial')`,
    [id],
  );
}

async function comoUsuario<T>(db: PGlite, id: string, acao: () => Promise<T>): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [id]);
  await db.exec("set role authenticated");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

function atualizar(db: PGlite, coluna: string, expressao: string) {
  return comoUsuario(db, dono, () => db.exec(`update perfis set ${coluna} = ${expressao}`));
}

Deno.test("conta comum não grava lista de listas nas listas do perfil", async () => {
  const db = await banco();
  try {
    await perfilDe(db, dono);

    await assert.rejects(
      () => atualizar(db, "areas_de_interesse", areasEmDuasDimensoes),
      /check constraint/,
    );
    await assert.rejects(
      () => atualizar(db, "habilidades", habilidadesEmDuasDimensoes),
      /check constraint/,
    );

    const salvo = (await db.query<Record<string, unknown>>(
      `select coalesce(array_ndims(areas_de_interesse), 0) areas,
              coalesce(array_ndims(habilidades), 0) habilidades
       from perfis`,
    )).rows[0];
    assert.deepEqual({ ...salvo }, { areas: 0, habilidades: 1 });
  } finally {
    await db.close();
  }
});

Deno.test("lista de uma dimensão, lista vazia e área nenhuma continuam aceitas", async () => {
  const db = await banco();
  try {
    await perfilDe(db, dono);

    await atualizar(db, "areas_de_interesse", `array['direito_contencioso', 'compliance']`);
    await atualizar(db, "areas_de_interesse", `'{}'::text[]`);
    await atualizar(db, "areas_de_interesse", `null`);
    await atualizar(db, "habilidades", `array['Excel', 'Contratos']`);
    await atualizar(db, "habilidades", `'{}'::text[]`);

    const salvo = (await db.query<Record<string, unknown>>(
      "select areas_de_interesse, habilidades from perfis",
    )).rows[0];
    assert.deepEqual({ ...salvo }, { areas_de_interesse: null, habilidades: [] });
  } finally {
    await db.close();
  }
});

Deno.test("perfil antigo com lista de listas faz a migração falhar inteira", async () => {
  const { db, restantes } = await bancoAntesDasDimensoes();
  try {
    await perfilDe(db, dono);
    await db.exec(`update perfis set areas_de_interesse = ${areasEmDuasDimensoes}`);

    await assert.rejects(() => aplicar(db, restantes.slice(0, 1)), /check constraint/);

    const dimensoes = (await db.query<{ n: number }>(
      `select count(*)::int n from pg_constraint
       where conrelid = 'public.perfis'::regclass and conname like '%em_uma_dimensao'`,
    )).rows[0].n;
    assert.equal(dimensoes, 0);
  } finally {
    await db.close();
  }
});
