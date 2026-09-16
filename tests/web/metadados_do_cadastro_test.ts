import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const MIGRACAO_DA_LIMPEZA = "0027_";

const pessoa = "00000000-0000-4000-8000-000000000001";
const antiga = "00000000-0000-4000-8000-000000000002";
const sessao = "00000000-0000-4000-8000-00000000000a";

async function banco(ate?: string): Promise<{ db: PGlite; restantes: string[] }> {
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
    create function auth.uid() returns uuid language sql stable as
      $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
    grant usage on schema public, auth to anon, authenticated;
    grant execute on function auth.uid() to anon, authenticated;
  `);
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  nomes.sort();
  const corte = ate ? nomes.findIndex((nome) => nome.startsWith(ate)) : nomes.length;
  assert.notEqual(corte, -1, `migração ${ate} não encontrada`);
  for (const nome of nomes.slice(0, corte)) {
    await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
  }
  return { db, restantes: nomes.slice(corte) };
}

function metadados(cadastroRadar: boolean) {
  const cadastro = {
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
  return cadastroRadar ? { cadastro_radar: cadastro, email_verified: true } : { email_verified: true };
}

async function metadadosDe(db: PGlite, id: string): Promise<Record<string, unknown>> {
  const linhas = await db.query<{ metadados: Record<string, unknown> }>(
    "select raw_user_meta_data metadados from auth.users where id = $1",
    [id],
  );
  return linhas.rows[0].metadados;
}

Deno.test("cadastro some dos metadados do Auth mesmo se a confirmação regravar os metadados", async () => {
  const { db } = await banco();
  try {
    await db.query("insert into auth.users(id, email, raw_user_meta_data) values ($1, 'a@x.com', $2)", [
      pessoa,
      metadados(true),
    ]);
    const pendente = await db.query<{ cadastro: Record<string, unknown> }>(
      "select cadastro from cadastros_pendentes where user_id = $1",
      [pessoa],
    );
    assert.equal(pendente.rows.length, 1);

    await db.query("update auth.users set email = email where id = $1", [pessoa]);
    assert.deepEqual(await metadadosDe(db, pessoa), { email_verified: true });

    await db.query("update auth.users set email_confirmed_at = now() where id = $1", [pessoa]);
    await db.query("update auth.users set raw_user_meta_data = $2 where id = $1", [pessoa, metadados(true)]);
    assert.deepEqual(await metadadosDe(db, pessoa), { email_verified: true });

    const perfil = await db.query<{ resposta: boolean }>(
      "select pessoa_com_deficiencia resposta from perfis where user_id = $1",
      [pessoa],
    );
    assert.equal(perfil.rows[0].resposta, true);
  } finally {
    await db.close();
  }
});

Deno.test("a migração limpa o cadastro que ficou nos metadados das contas antigas", async () => {
  const { db, restantes } = await banco(MIGRACAO_DA_LIMPEZA);
  try {
    await db.query("insert into auth.users(id, email, raw_user_meta_data) values ($1, 'b@x.com', $2)", [
      antiga,
      metadados(true),
    ]);
    await db.query("update auth.users set email_confirmed_at = now() where id = $1", [antiga]);
    await db.query("update auth.users set raw_user_meta_data = $2 where id = $1", [antiga, metadados(true)]);
    assert.ok("cadastro_radar" in await metadadosDe(db, antiga), "o cenário precisa reproduzir a conta antiga");

    for (const nome of restantes) await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));

    assert.deepEqual(await metadadosDe(db, antiga), { email_verified: true });
    const perfis = await db.query<{ n: number }>("select count(*)::int n from perfis where user_id = $1", [antiga]);
    assert.equal(perfis.rows[0].n, 1);
  } finally {
    await db.close();
  }
});
