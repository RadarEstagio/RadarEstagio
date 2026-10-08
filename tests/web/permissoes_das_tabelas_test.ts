import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const PERMISSAO_NEGADA = "42501";
const TABELAS_DO_PIPELINE = ["vagas", "envios", "avaliacoes"];
const SEQUENCIAS_DE_IDENTIDADE = [
  "vagas_id_seq",
  "avaliacoes_id_seq",
  "eventos_produto_id_seq",
];
const OPERACOES_DA_TABELA = [
  "select",
  "insert",
  "update",
  "delete",
  "truncate",
  "references",
  "trigger",
  "maintain",
];
const OPERACOES_DA_SEQUENCIA = ["usage", "select", "update"];
const PAPEIS_DO_SITE = ["anon", "authenticated"];

const dono = "00000000-0000-4000-8000-000000000001";

async function bancoComAsMigracoes(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    create role anon;
    create role authenticated;
    create role service_role;
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
    grant usage on schema public, auth to anon, authenticated, service_role;
    grant execute on function auth.uid() to anon, authenticated, service_role;
    alter default privileges in schema public
      grant all on tables to anon, authenticated, service_role;
    alter default privileges in schema public
      grant all on sequences to anon, authenticated, service_role;
    alter default privileges in schema public
      grant execute on functions to anon, authenticated, service_role;
  `);
  const arquivos: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) arquivos.push(entrada.name);
  }
  for (const arquivo of arquivos.sort()) {
    await db.exec(await Deno.readTextFile(new URL(arquivo, MIGRACOES)));
  }
  return db;
}

async function comUmEnvioGravado(db: PGlite): Promise<void> {
  await db.query(
    "insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())",
    [dono, "dono@example.com"],
  );
  const perfil = await db.query<{ id: string }>(
    `insert into public.perfis
       (user_id, curso, periodo, habilidades, cidade, modalidade, areas_de_interesse)
     values ($1, 'Computação', 3, '{Python}', 'Recife, PE', 'remoto', '{dados_ia}')
     returning id`,
    [dono],
  );
  const vaga = await db.query<{ id: string }>(
    `insert into public.vagas
       (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
     values ('adzuna', '1', 'Estágio', 'Empresa', 'Recife, PE', 'Descrição',
       'https://exemplo.com/1', now())
     returning id`,
  );
  await db.query(
    "insert into public.envios(perfil_id, vaga_id) values ($1, $2)",
    [perfil.rows[0].id, vaga.rows[0].id],
  );
  await db.query(
    "insert into public.avaliacoes(perfil_id, vaga_id, nota, modelo) values ($1, $2, 80, 'teste')",
    [perfil.rows[0].id, vaga.rows[0].id],
  );
}

async function comoPapel<T>(db: PGlite, papel: string, acao: () => Promise<T>): Promise<T> {
  await db.exec(`set role ${papel}`);
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

async function codigoDoErro(acao: () => Promise<unknown>): Promise<string | null> {
  try {
    await acao();
    return null;
  } catch (erro) {
    return (erro as { code?: string }).code ?? "sem código";
  }
}

Deno.test("as tabelas do pipeline ficam fora do alcance da chave pública", async () => {
  const db = await bancoComAsMigracoes();
  try {
    for (const tabela of TABELAS_DO_PIPELINE) {
      for (const papel of PAPEIS_DO_SITE) {
        for (const operacao of OPERACOES_DA_TABELA) {
          const { rows } = await db.query<{ pode: boolean }>(
            "select has_table_privilege($1, $2, $3) pode",
            [papel, `public.${tabela}`, operacao],
          );
          assert.equal(rows[0].pode, false, `${papel} ${operacao} ${tabela}`);
        }
      }
    }
  } finally {
    await db.close();
  }
});

Deno.test("o histórico de envios e avaliações não é truncado pela chave pública", async () => {
  const db = await bancoComAsMigracoes();
  try {
    await comUmEnvioGravado(db);

    for (const tabela of ["envios", "avaliacoes"]) {
      for (const papel of PAPEIS_DO_SITE) {
        assert.equal(
          await comoPapel(db, papel, () =>
            codigoDoErro(() => db.exec(`truncate table public.${tabela}`))),
          PERMISSAO_NEGADA,
          `${papel} truncate ${tabela}`,
        );
      }
      const { rows } = await db.query<{ n: number }>(
        `select count(*)::int n from public.${tabela}`,
      );
      assert.equal(rows[0].n, 1, tabela);
    }
  } finally {
    await db.close();
  }
});

Deno.test("as sequências de identidade não têm grant e a visita continua entrando", async () => {
  const db = await bancoComAsMigracoes();
  try {
    for (const sequencia of SEQUENCIAS_DE_IDENTIDADE) {
      for (const papel of PAPEIS_DO_SITE) {
        for (const operacao of OPERACOES_DA_SEQUENCIA) {
          const { rows } = await db.query<{ pode: boolean }>(
            "select has_sequence_privilege($1, $2, $3) pode",
            [papel, `public.${sequencia}`, operacao],
          );
          assert.equal(rows[0].pode, false, `${papel} ${operacao} ${sequencia}`);
        }
      }
    }

    assert.equal(
      await comoPapel(db, "anon", () =>
        codigoDoErro(() =>
          db.query(
            `insert into public.eventos_produto(nome, sessao_id, propriedades)
             values ('landing_visualizada', $1, $2)`,
            [crypto.randomUUID(), { pagina: "/" }],
          ))),
      null,
    );
  } finally {
    await db.close();
  }
});

Deno.test("o service role continua escrevendo nas tabelas do pipeline", async () => {
  const db = await bancoComAsMigracoes();
  try {
    for (const tabela of TABELAS_DO_PIPELINE) {
      for (const operacao of ["select", "insert", "update", "delete"]) {
        const { rows } = await db.query<{ pode: boolean }>(
          "select has_table_privilege('service_role', $1, $2) pode",
          [`public.${tabela}`, operacao],
        );
        assert.equal(rows[0].pode, true, `service_role ${operacao} ${tabela}`);
      }
    }
  } finally {
    await db.close();
  }
});
