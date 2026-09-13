import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);

async function consulta(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  const bloco = [...fonte.matchAll(/^(SQL_\w+) = """\n([\s\S]*?)"""$/gm)]
    .find((encontrado) => encontrado[1] === nome);
  assert.ok(bloco, `constante ${nome} não encontrada em postgres.py`);
  return bloco[2]
    .replaceAll("%(perfil_id)s", "$1::uuid")
    .replaceAll("%(perfis)s", "$1::uuid[]");
}

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

async function banco(antesDaMarca?: (db: PGlite) => Promise<void>): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    create role anon;
    create role authenticated;
    create schema auth;
    create table auth.users (
      id uuid primary key, email text, created_at timestamptz default now(),
      email_confirmed_at timestamptz, raw_user_meta_data jsonb default '{}'
    );
    create function auth.uid() returns uuid language sql stable as
      $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
  `);
  const nomes = await migracoes();
  const indiceDaMarca = nomes.findIndex((nome) => nome.startsWith("0021_"));
  assert.notEqual(indiceDaMarca, -1);
  await aplicar(db, nomes.slice(0, indiceDaMarca));
  if (antesDaMarca) await antesDaMarca(db);
  await aplicar(db, nomes.slice(indiceDaMarca));
  return db;
}

let contas = 0;

async function perfilVinculado(db: PGlite): Promise<string> {
  contas += 1;
  const dono = `00000000-0000-4000-8000-${String(contas).padStart(12, "0")}`;
  await db.query("insert into auth.users(id, email) values ($1, $2)", [dono, `p${contas}@x.com`]);
  const criado = await db.query<{ id: string }>(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id)
     values ($1, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial', $2)
     returning id`,
    [dono, String(contas)],
  );
  return criado.rows[0].id;
}

async function webhookReivindica(db: PGlite, perfil: string): Promise<boolean> {
  const reivindicado = await db.query(
    `update perfis set entrega_imediata_disparada_em = now()
     where id = $1 and entrega_imediata_disparada_em is null returning id`,
    [perfil],
  );
  return reivindicado.rows.length === 1;
}

async function execucaoImediata(db: PGlite, perfil: string): Promise<string[]> {
  const atendidos = await db.query<{ id: string }>(
    await consulta("SQL_REIVINDICAR_ENTREGAS_IMEDIATAS"),
    [perfil],
  );
  return atendidos.rows.map((linha) => linha.id).sort();
}

async function diario(db: PGlite, atendidos: string[]) {
  await db.query(await consulta("SQL_MARCAR_ENTREGAS_IMEDIATAS_ATENDIDAS"), [atendidos]);
}

Deno.test("rajada de vínculos: execução cancelada na espera não deixa ninguém sem entrega", async () => {
  const db = await banco();
  try {
    const primeiro = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, primeiro));
    assert.deepEqual(await execucaoImediata(db, primeiro), [primeiro]);

    const turma: string[] = [];
    for (let i = 0; i < 9; i++) {
      const perfil = await perfilVinculado(db);
      assert.ok(await webhookReivindica(db, perfil));
      turma.push(perfil);
    }
    const ultimo = turma[turma.length - 1];

    assert.deepEqual(await execucaoImediata(db, ultimo), [...turma].sort());
    assert.deepEqual(await execucaoImediata(db, ultimo), []);
  } finally {
    await db.close();
  }
});

Deno.test("disparo recusado deixa o perfil pendente para a próxima execução", async () => {
  const db = await banco();
  try {
    const semDisparo = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, semDisparo));
    assert.equal(await webhookReivindica(db, semDisparo), false);

    const seguinte = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, seguinte));

    assert.deepEqual(await execucaoImediata(db, seguinte), [semDisparo, seguinte].sort());
  } finally {
    await db.close();
  }
});

Deno.test("o diário marca quem atendeu e a entrega imediata seguinte não repete", async () => {
  const db = await banco();
  try {
    const pendente = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, pendente));
    const doDiario = await perfilVinculado(db);
    await diario(db, [pendente, doDiario]);

    const novo = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, novo));

    assert.deepEqual(await execucaoImediata(db, novo), [novo]);
    assert.deepEqual(await execucaoImediata(db, doDiario), []);
  } finally {
    await db.close();
  }
});

Deno.test("pendente pausado ou desvinculado espera e é atendido ao voltar", async () => {
  const db = await banco();
  try {
    const pausado = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, pausado));
    await db.query("update perfis set ativo = false where id = $1", [pausado]);
    const desvinculado = await perfilVinculado(db);
    assert.ok(await webhookReivindica(db, desvinculado));
    await db.query("update perfis set telegram_chat_id = null where id = $1", [desvinculado]);

    const outro = await perfilVinculado(db);
    assert.deepEqual(await execucaoImediata(db, outro), [outro]);

    await db.query("update perfis set ativo = true where id = $1", [pausado]);
    const depois = await perfilVinculado(db);
    assert.deepEqual(await execucaoImediata(db, depois), [pausado, depois].sort());
  } finally {
    await db.close();
  }
});

Deno.test("perfil que já recebia antes da marca não dispara nem é reivindicado", async () => {
  let antigo = "";
  const db = await banco(async (antes) => {
    antigo = await perfilVinculado(antes);
  });
  try {
    assert.equal(await webhookReivindica(db, antigo), false);
    assert.deepEqual(await execucaoImediata(db, antigo), []);
  } finally {
    await db.close();
  }
});
