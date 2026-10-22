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
  return bloco[2]
    .replaceAll("%(perfil_id)s", "$1::uuid")
    .replaceAll("%(perfis)s", "$1::uuid[]")
    .replaceAll("%(dia)s", "$2::date");
}

async function migracoes(): Promise<string[]> {
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  return nomes.sort();
}

async function aplicar(db: PGlite, nome: string) {
  await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
}

async function banco(ate = "9999"): Promise<PGlite> {
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
    if (nome.slice(0, 4) <= ate) await aplicar(db, nome);
  }
  return db;
}

let contas = 0;
let vagas = 0;

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

async function enviar(db: PGlite, perfil: string, enviadaEm: string) {
  vagas += 1;
  const vaga = await db.query<{ id: string }>(
    `insert into vagas (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
     values ('adzuna', $1, 'Estágio', 'Empresa', 'Rio de Janeiro, RJ', 'Descrição', $2, now())
     returning id`,
    [String(vagas), `https://exemplo.com/${vagas}`],
  );
  await db.query("insert into envios(perfil_id, vaga_id, enviada_em) values ($1, $2, $3)", [
    perfil,
    vaga.rows[0].id,
    enviadaEm,
  ]);
}

function comoDia(valor: unknown): string | null {
  if (valor === null) return null;
  if (valor instanceof Date) return valor.toISOString().slice(0, 10);
  return String(valor).slice(0, 10);
}

async function diasDosAtivos(db: PGlite): Promise<Map<string, string | null>> {
  const linhas = await db.query<{ id: string; ultimo_dia_atendido: unknown }>(
    await consulta("SQL_USUARIOS_ATIVOS"),
  );
  return new Map(linhas.rows.map((linha) => [linha.id, comoDia(linha.ultimo_dia_atendido)]));
}

async function diaGravado(db: PGlite, perfil: string): Promise<string | null> {
  const linhas = await db.query<{ ultimo_dia_atendido: unknown }>(
    "select ultimo_dia_atendido from perfis where id = $1",
    [perfil],
  );
  return comoDia(linhas.rows[0].ultimo_dia_atendido);
}

async function marcar(db: PGlite, perfis: string[], dia: string) {
  await db.query(await consulta("SQL_MARCAR_ATENDIDOS_NO_DIA"), [perfis, dia]);
}

async function atendidoNoDia(db: PGlite, perfil: string, dia: string): Promise<boolean> {
  const linhas = await db.query<{ exists: boolean }>(
    await consulta("SQL_ATENDIDO_NO_DIA"),
    [perfil, dia],
  );
  return linhas.rows[0].exists;
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

Deno.test("perfil existente nasce sem dia atendido e a lista de ativos devolve nulo", async () => {
  const db = await banco();
  try {
    const { id } = await perfilVinculado(db);

    assert.equal(await diaGravado(db, id), null);
    const ativos = await diasDosAtivos(db);
    assert.ok(ativos.has(id));
    assert.equal(ativos.get(id), null);
  } finally {
    await db.close();
  }
});

Deno.test("marcar o dia grava só nos perfis da lista e a lista de ativos devolve a data", async () => {
  const db = await banco();
  try {
    const primeiro = await perfilVinculado(db);
    const segundo = await perfilVinculado(db);
    const deFora = await perfilVinculado(db);

    await marcar(db, [primeiro.id, segundo.id], "2026-10-21");

    assert.equal(await diaGravado(db, primeiro.id), "2026-10-21");
    assert.equal(await diaGravado(db, segundo.id), "2026-10-21");
    assert.equal(await diaGravado(db, deFora.id), null);
    const ativos = await diasDosAtivos(db);
    assert.equal(ativos.get(primeiro.id), "2026-10-21");
    assert.equal(ativos.get(segundo.id), "2026-10-21");
    assert.equal(ativos.get(deFora.id), null);
  } finally {
    await db.close();
  }
});

Deno.test("atendido no dia só vale para o mesmo dia e para perfil marcado", async () => {
  const db = await banco();
  try {
    const marcado = await perfilVinculado(db);
    const nuncaMarcado = await perfilVinculado(db);

    await marcar(db, [marcado.id], "2026-10-21");

    assert.equal(await atendidoNoDia(db, marcado.id, "2026-10-21"), true);
    assert.equal(await atendidoNoDia(db, marcado.id, "2026-10-22"), false);
    assert.equal(await atendidoNoDia(db, nuncaMarcado.id, "2026-10-21"), false);
  } finally {
    await db.close();
  }
});

Deno.test("marcar de novo num dia posterior substitui o dia anterior", async () => {
  const db = await banco();
  try {
    const { id } = await perfilVinculado(db);

    await marcar(db, [id], "2026-10-21");
    await marcar(db, [id], "2026-10-22");

    assert.equal(await diaGravado(db, id), "2026-10-22");
    assert.equal(await atendidoNoDia(db, id, "2026-10-21"), false);
    assert.equal(await atendidoNoDia(db, id, "2026-10-22"), true);
  } finally {
    await db.close();
  }
});

Deno.test("o navegador não consegue escrever o dia atendido no próprio perfil", async () => {
  const db = await banco();
  try {
    const { id, dono } = await perfilVinculado(db);

    const { rows } = await db.query<{ pode: boolean }>(
      "select has_column_privilege('authenticated', 'public.perfis', 'ultimo_dia_atendido', 'update') pode",
    );
    assert.equal(rows[0].pode, false);
    assert.equal(
      await comoDono(db, dono, () =>
        codigoDoErro(() =>
          db.query("update perfis set ultimo_dia_atendido = '2026-10-21' where id = $1", [id])
        )),
      PERMISSAO_NEGADA,
    );
    assert.equal(
      await comoDono(db, dono, () =>
        codigoDoErro(() =>
          db.query("update perfis set aceita_emails = true where id = $1", [id])
        )),
      null,
    );
    assert.equal(await diaGravado(db, id), null);
  } finally {
    await db.close();
  }
});

Deno.test("a migration preenche o dia com o último envio de cada perfil no dia de Brasília", async () => {
  const db = await banco("0035");
  try {
    const noFimDaNoite = await perfilVinculado(db);
    await enviar(db, noFimDaNoite.id, "2026-10-20T15:00:00Z");
    await enviar(db, noFimDaNoite.id, "2026-10-21T02:30:00Z");
    const comEnvioAntigo = await perfilVinculado(db);
    await enviar(db, comEnvioAntigo.id, "2026-10-21T10:30:00Z");
    await enviar(db, comEnvioAntigo.id, "2026-10-15T10:30:00Z");
    const semEnvio = await perfilVinculado(db);

    const migracao = (await migracoes()).find((nome) => nome.startsWith("0036_"));
    assert.ok(migracao, "migration 0036 não encontrada");
    await aplicar(db, migracao);

    assert.equal(await diaGravado(db, noFimDaNoite.id), "2026-10-20");
    assert.equal(await diaGravado(db, comEnvioAntigo.id), "2026-10-21");
    assert.equal(await diaGravado(db, semEnvio.id), null);
  } finally {
    await db.close();
  }
});
