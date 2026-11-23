import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const PERMISSAO_NEGADA = "42501";

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  const bloco = [...fonte.matchAll(/^(SQL_\w+) = """\n([\s\S]*?)"""$/gm)]
    .find((encontrado) => encontrado[1] === nome);
  assert.ok(bloco, `constante ${nome} não encontrada em postgres.py`);
  return bloco[2].replaceAll("%(perfil_id)s", "$1::uuid");
}

async function migracoes(): Promise<string[]> {
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  return nomes.sort();
}

async function banco(): Promise<PGlite> {
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
  for (const nome of await migracoes()) {
    await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
  }
  return db;
}

let contas = 0;

function donoNumero(numero: number): string {
  return `00000000-0000-4000-8000-${String(numero).padStart(12, "0")}`;
}

async function perfilVinculado(db: PGlite): Promise<{ id: string; dono: string }> {
  contas += 1;
  const dono = donoNumero(contas);
  await db.query(
    "insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())",
    [dono, `p${contas}@x.com`],
  );
  const criado = await db.query<{ id: string }>(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id)
     values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial', $2)
     returning id`,
    [dono, String(contas)],
  );
  return { id: criado.rows[0].id, dono };
}

async function contarFalha(db: PGlite, perfil: string): Promise<number> {
  const linhas = await db.query<{ falhas_de_envio: number }>(
    await consulta("SQL_CONTAR_FALHA_DE_ENVIO"),
    [perfil],
  );
  return linhas.rows[0].falhas_de_envio;
}

async function zerarFalhas(db: PGlite, perfil: string): Promise<number> {
  const resultado = await db.query(await consulta("SQL_ZERAR_FALHAS_DE_ENVIO"), [perfil]);
  return resultado.affectedRows ?? 0;
}

async function falhasGravadas(db: PGlite, perfil: string): Promise<number> {
  const linhas = await db.query<{ falhas_de_envio: number }>(
    "select falhas_de_envio from perfis where id = $1",
    [perfil],
  );
  return linhas.rows[0].falhas_de_envio;
}

async function ativos(db: PGlite): Promise<string[]> {
  const linhas = await db.query<{ id: string }>(await consulta("SQL_USUARIOS_ATIVOS"));
  return linhas.rows.map((linha) => linha.id);
}

async function pausasRegistradas(db: PGlite, perfil: string): Promise<number> {
  const linhas = await db.query<{ total: number }>(
    `select count(*)::int as total from eventos_produto
     where perfil_id = $1 and nome = 'entregas_pausadas'`,
    [perfil],
  );
  return linhas.rows[0].total;
}

async function comoDono<T>(db: PGlite, dono: string, acao: () => Promise<T>): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [dono]);
  await db.exec("set role authenticated");
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

Deno.test("cada recusa soma uma falha só no perfil que recusou", async () => {
  const db = await banco();
  try {
    const bloqueou = await perfilVinculado(db);
    const outro = await perfilVinculado(db);

    assert.equal(await contarFalha(db, bloqueou.id), 1);
    assert.equal(await contarFalha(db, bloqueou.id), 2);
    assert.equal(await contarFalha(db, bloqueou.id), 3);

    assert.equal(await falhasGravadas(db, outro.id), 0);
  } finally {
    await db.close();
  }
});

Deno.test("zerar apaga as falhas acumuladas e a recusa seguinte recomeça do um", async () => {
  const db = await banco();
  try {
    const bloqueou = await perfilVinculado(db);
    const outro = await perfilVinculado(db);
    await contarFalha(db, bloqueou.id);
    await contarFalha(db, bloqueou.id);
    await contarFalha(db, outro.id);

    assert.equal(await zerarFalhas(db, bloqueou.id), 1);

    assert.equal(await falhasGravadas(db, bloqueou.id), 0);
    assert.equal(await falhasGravadas(db, outro.id), 1);
    assert.equal(await contarFalha(db, bloqueou.id), 1);
  } finally {
    await db.close();
  }
});

Deno.test("zerar perfil sem falha nenhuma não escreve na linha", async () => {
  const db = await banco();
  try {
    const { id } = await perfilVinculado(db);

    assert.equal(await zerarFalhas(db, id), 0);
    assert.equal(await falhasGravadas(db, id), 0);
  } finally {
    await db.close();
  }
});

Deno.test("perfil pausado sai da lista de ativos e a pausa vira evento uma vez", async () => {
  const db = await banco();
  try {
    const bloqueou = await perfilVinculado(db);
    const outro = await perfilVinculado(db);

    await db.query(await consulta("SQL_PAUSAR"), [bloqueou.id]);
    await db.query(await consulta("SQL_PAUSAR"), [bloqueou.id]);

    assert.deepEqual(await ativos(db), [outro.id]);
    assert.equal(await pausasRegistradas(db, bloqueou.id), 1);
    assert.equal(await pausasRegistradas(db, outro.id), 0);
  } finally {
    await db.close();
  }
});

Deno.test("quem retoma pelo site volta para a lista de ativos", async () => {
  const db = await banco();
  try {
    const { id, dono } = await perfilVinculado(db);
    await db.query(await consulta("SQL_PAUSAR"), [id]);

    await comoDono(db, dono, () =>
      db.query(
        "update perfis set ativo = true, motivo_pausa = null, atualizado_em = now() where user_id = $1",
        [dono],
      ));

    assert.deepEqual(await ativos(db), [id]);
  } finally {
    await db.close();
  }
});

Deno.test("o navegador não escreve no contador de falhas de envio", async () => {
  const db = await banco();
  try {
    const { id, dono } = await perfilVinculado(db);
    await contarFalha(db, id);
    await contarFalha(db, id);

    const codigo = await comoDono(db, dono, () =>
      codigoDoErro(() =>
        db.query("update perfis set falhas_de_envio = 0 where user_id = $1", [dono])
      ));

    assert.equal(codigo, PERMISSAO_NEGADA);
    assert.equal(await falhasGravadas(db, id), 2);
  } finally {
    await db.close();
  }
});
