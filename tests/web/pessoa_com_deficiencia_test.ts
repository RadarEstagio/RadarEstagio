import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);

const dono = "00000000-0000-4000-8000-000000000001";
const outro = "00000000-0000-4000-8000-000000000002";
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

function cadastro(resposta: Record<string, unknown>) {
  return {
    perfil: {
      curso: "Direito",
      periodo: 3,
      habilidades: ["Contratos"],
      cidade: "Rio de Janeiro, RJ",
      modalidade: "presencial",
      areas_de_interesse: [],
      ...resposta,
    },
    aceitou_termos: true,
    aceita_emails: false,
    versao_dos_termos: "2026-09-05",
    sessao_id: sessao,
  };
}

async function cadastrarEConfirmar(db: PGlite, id: string, payload: unknown) {
  await db.query("insert into auth.users(id, email, raw_user_meta_data) values ($1, $2, $3)", [
    id,
    `${id}@x.com`,
    { cadastro_radar: payload },
  ]);
  await db.query("update auth.users set email_confirmed_at = now() where id = $1", [id]);
}

async function respostaSalva(db: PGlite, id: string): Promise<unknown> {
  const linhas = await db.query<{ resposta: boolean | null }>(
    "select pessoa_com_deficiencia resposta from perfis where user_id = $1",
    [id],
  );
  assert.equal(linhas.rows.length, 1, "perfil não foi criado");
  return linhas.rows[0].resposta;
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

Deno.test("cadastro guarda sim e não, e resposta vazia ou ausente fica como não informada", async () => {
  const casos: [Record<string, unknown>, boolean | null][] = [
    [{ pessoa_com_deficiencia: true }, true],
    [{ pessoa_com_deficiencia: false }, false],
    [{ pessoa_com_deficiencia: null }, null],
    [{}, null],
  ];
  for (const [resposta, esperada] of casos) {
    const db = await banco();
    try {
      await cadastrarEConfirmar(db, dono, cadastro(resposta));
      assert.equal(await respostaSalva(db, dono), esperada, JSON.stringify(resposta));
    } finally {
      await db.close();
    }
  }
});

Deno.test("cadastro recusa resposta sobre deficiência que não é sim, não ou vazia", async () => {
  const db = await banco();
  try {
    for (const resposta of ["sim", 1, [], {}]) {
      await assert.rejects(
        () => cadastrarEConfirmar(db, dono, cadastro({ pessoa_com_deficiencia: resposta })),
        /inválid/,
        JSON.stringify(resposta),
      );
    }
    const pendentes = await db.query<{ n: number }>("select count(*)::int n from cadastros_pendentes");
    assert.equal(pendentes.rows[0].n, 0);
  } finally {
    await db.close();
  }
});

Deno.test("dono muda a própria resposta, volta a não informar e a vê na exportação", async () => {
  const db = await banco();
  try {
    await cadastrarEConfirmar(db, dono, cadastro({}));
    await cadastrarEConfirmar(db, outro, cadastro({ pessoa_com_deficiencia: false }));

    for (const resposta of [true, false, null]) {
      await comoUsuario(db, dono, () => db.query("update perfis set pessoa_com_deficiencia = $1", [resposta]));
      assert.equal(await respostaSalva(db, dono), resposta);
    }
    await comoUsuario(db, dono, () => db.query("update perfis set pessoa_com_deficiencia = true"));
    assert.equal(await respostaSalva(db, outro), false);

    const exportado = await comoUsuario(
      db,
      dono,
      () => db.query<{ resposta: unknown }>("select baixar_meus_dados()->'perfil'->'pessoa_com_deficiencia' resposta"),
    );
    assert.equal(exportado.rows[0].resposta, true);
  } finally {
    await db.close();
  }
});
