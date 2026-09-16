import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const FUNCAO = "public.apagar_minha_conta_sem_perfil()";

const semPerfil = "00000000-0000-4000-8000-000000000001";
const outraSemPerfil = "00000000-0000-4000-8000-000000000002";
const comPerfil = "00000000-0000-4000-8000-000000000003";
const sessaoDaConta = "00000000-0000-4000-8000-00000000000a";
const sessaoDaOutraConta = "00000000-0000-4000-8000-00000000000b";

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
    create function auth.uid() returns uuid language sql stable as
      $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
    grant usage on schema public, auth to anon, authenticated;
    grant execute on function auth.uid() to anon, authenticated;
    alter default privileges in schema public grant execute on functions to anon, authenticated;
  `);
  const nomes: string[] = [];
  for await (const entrada of Deno.readDir(MIGRACOES)) {
    if (entrada.name.endsWith(".sql")) nomes.push(entrada.name);
  }
  for (const nome of nomes.sort()) await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
  await db.query(
    `insert into auth.users(id, email, email_confirmed_at) values
       ($1, 'sem-perfil@x.com', now()), ($2, 'outra@x.com', now()), ($3, 'com-perfil@x.com', now())`,
    [semPerfil, outraSemPerfil, comPerfil],
  );
  await db.query(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade)
     values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial')`,
    [comPerfil],
  );
  await db.query(
    `insert into eventos_produto(nome, origem, sessao_id, user_id) values
       ('landing_visualizada', 'web', $1, null),
       ('cta_cadastro_aberto', 'web', $1, $3),
       ('landing_visualizada', 'web', $2, null),
       ('cta_cadastro_aberto', 'web', $2, $4)`,
    [sessaoDaConta, sessaoDaOutraConta, semPerfil, outraSemPerfil],
  );
  return db;
}

async function contar(db: PGlite, deOnde: string, parametros: unknown[] = []): Promise<number> {
  const resultado = await db.query<{ n: number }>(`select count(*)::int n from ${deOnde}`, parametros);
  return resultado.rows[0].n;
}

async function comoUsuario<T>(db: PGlite, id: string | null, acao: () => Promise<T>): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [id ?? ""]);
  await db.exec("set role authenticated");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

Deno.test("conta confirmada sem perfil é apagada na hora, com os eventos dela", async () => {
  const db = await banco();
  try {
    await comoUsuario(db, semPerfil, () => db.exec(`select ${FUNCAO}`));

    assert.equal(await contar(db, "auth.users where id = $1", [semPerfil]), 0);
    assert.equal(await contar(db, "eventos_produto where user_id = $1", [semPerfil]), 0);
    assert.equal(await contar(db, "eventos_produto where sessao_id = $1", [sessaoDaConta]), 0);
    assert.equal(await contar(db, "auth.users where id = $1", [outraSemPerfil]), 1);
    assert.ok(await contar(db, "eventos_produto where user_id = $1", [outraSemPerfil]) > 0);
    assert.equal(
      await contar(db, "eventos_produto where sessao_id = $1 and user_id is null", [sessaoDaOutraConta]),
      1,
    );
    assert.equal(await contar(db, "auth.users where id = $1", [comPerfil]), 1);
  } finally {
    await db.close();
  }
});

Deno.test("conta com perfil não é apagada por essa função", async () => {
  const db = await banco();
  try {
    await assert.rejects(() => comoUsuario(db, comPerfil, () => db.exec(`select ${FUNCAO}`)));

    assert.equal(await contar(db, "auth.users where id = $1", [comPerfil]), 1);
    assert.equal(await contar(db, "perfis where user_id = $1", [comPerfil]), 1);
  } finally {
    await db.close();
  }
});

Deno.test("anon não chama a função e sessão sem usuário não apaga ninguém", async () => {
  const db = await banco();
  try {
    const privilegios = (await db.query<{ anon: boolean; autenticado: boolean }>(
      `select has_function_privilege('anon', '${FUNCAO}', 'execute') anon,
              has_function_privilege('authenticated', '${FUNCAO}', 'execute') autenticado`,
    )).rows[0];
    assert.deepEqual({ ...privilegios }, { anon: false, autenticado: true });

    await db.exec("set role anon");
    try {
      await assert.rejects(() => db.exec(`select ${FUNCAO}`));
    } finally {
      await db.exec("reset role");
    }
    await assert.rejects(() => comoUsuario(db, null, () => db.exec(`select ${FUNCAO}`)));

    assert.equal(await contar(db, "auth.users"), 3);
  } finally {
    await db.close();
  }
});

Deno.test("ninguém apaga a conta de outra pessoa", async () => {
  const db = await banco();
  try {
    await assert.rejects(() =>
      comoUsuario(
        db,
        semPerfil,
        () => db.query("select public.apagar_minha_conta_sem_perfil($1::uuid)", [outraSemPerfil]),
      )
    );
    await assert.rejects(() =>
      comoUsuario(db, semPerfil, () => db.exec(`delete from auth.users where id = '${outraSemPerfil}'`))
    );

    assert.equal(await contar(db, "auth.users where id = $1", [outraSemPerfil]), 1);
    assert.equal(await contar(db, "auth.users where id = $1", [semPerfil]), 1);
  } finally {
    await db.close();
  }
});
