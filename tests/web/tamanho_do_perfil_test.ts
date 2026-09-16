import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const MIGRACAO_DOS_TETOS = "0025_";
const catalogoDeAreas = JSON.parse(
  await Deno.readTextFile(new URL("../../web/assets/areas.json", import.meta.url)),
);
const catalogoDeCidades: string[] = JSON.parse(
  await Deno.readTextFile(new URL("../../web/assets/cidades.json", import.meta.url)),
);

function maisLongo(textos: string[]): string {
  return textos.reduce((maior, texto) => (texto.length > maior.length ? texto : maior));
}

const maiorCidade = maisLongo(catalogoDeCidades);
const maiorCursoSugerido = maisLongo(
  catalogoDeAreas.areas.flatMap((area: { cursos_sugeridos: string[] }) => area.cursos_sugeridos),
);
const maiorCursoDigitado = `${maisLongo(catalogoDeAreas.prefixos)} em ${maiorCursoSugerido} - ${
  maisLongo(catalogoDeAreas.sufixos)
}`;
const cinquentaHabilidadesCheias = Array.from(
  { length: 50 },
  (_, indice) => `Habilidade ${indice}, com vírgula (Word, Excel)`.padEnd(100, "x"),
);

const dono = "00000000-0000-4000-8000-000000000001";
const novo = "00000000-0000-4000-8000-000000000002";
const sessao = "00000000-0000-4000-8000-00000000000a";
const gigante = "Engenharia de ".repeat(15000);
const espacos = " ".repeat(200000);

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

async function bancoAntesDosTetos(): Promise<{ db: PGlite; restantes: string[] }> {
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
  const indice = nomes.findIndex((nome) => nome.startsWith(MIGRACAO_DOS_TETOS));
  assert.notEqual(indice, -1, `migração ${MIGRACAO_DOS_TETOS} não encontrada`);
  await aplicar(db, nomes.slice(0, indice));
  return { db, restantes: nomes.slice(indice) };
}

async function banco(): Promise<PGlite> {
  const { db, restantes } = await bancoAntesDosTetos();
  await aplicar(db, restantes);
  return db;
}

async function perfilDe(db: PGlite, id: string, curso = "Direito") {
  await db.query("insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())", [
    id,
    `${id}@x.com`,
  ]);
  await db.query(
    `insert into perfis(user_id, curso, periodo, habilidades, cidade, modalidade)
     values ($1, $2, 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial')`,
    [id, curso],
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

function atualizar(db: PGlite, coluna: string, valor: unknown) {
  return comoUsuario(db, dono, () => db.query(`update perfis set ${coluna} = $1`, [valor]));
}

function cadastro(perfil: Record<string, unknown> = {}, extra: Record<string, unknown> = {}) {
  return {
    perfil: {
      curso: "Direito",
      periodo: 3,
      habilidades: ["Contratos"],
      cidade: "Rio de Janeiro, RJ",
      modalidade: "presencial",
      areas_de_interesse: [],
      ...perfil,
    },
    aceitou_termos: true,
    aceita_emails: false,
    versao_dos_termos: "2026-09-05",
    sessao_id: sessao,
    ...extra,
  };
}

function cadastrar(db: PGlite, id: string, payload: unknown) {
  return db.query("insert into auth.users(id, email, raw_user_meta_data) values ($1, $2, $3)", [
    id,
    `${id}@x.com`,
    { cadastro_radar: payload },
  ]);
}

async function contar(db: PGlite, deOnde: string): Promise<number> {
  return (await db.query<{ n: number }>(`select count(*)::int n from ${deOnde}`)).rows[0].n;
}

Deno.test("conta comum não grava texto gigante no próprio perfil", async () => {
  const db = await banco();
  try {
    await perfilDe(db, dono);

    await assert.rejects(() => atualizar(db, "curso", gigante), /check constraint/);
    await assert.rejects(() => atualizar(db, "cidade", "Rio de Janeiro, ".repeat(12000)), /check constraint/);
    await assert.rejects(() => atualizar(db, "habilidades", [`Contratos${espacos}`]), /check constraint/);
    await assert.rejects(
      () => atualizar(db, "areas_de_interesse", Array(100000).fill("direito_contencioso")),
      /check constraint/,
    );

    const salvo = (await db.query<Record<string, unknown>>(
      "select curso, cidade, habilidades, cardinality(areas_de_interesse) areas from perfis",
    )).rows[0];
    assert.deepEqual({ ...salvo }, {
      curso: "Direito",
      cidade: "Rio de Janeiro, RJ",
      habilidades: ["Contratos"],
      areas: null,
    });
  } finally {
    await db.close();
  }
});

Deno.test("o teto de cada texto do perfil aceita o limite e recusa um caractere a mais", async () => {
  const db = await banco();
  try {
    await perfilDe(db, dono);

    await atualizar(db, "curso", "c".repeat(200));
    await assert.rejects(() => atualizar(db, "curso", "c".repeat(201)), /check constraint/);
    await atualizar(db, "cidade", "c".repeat(120));
    await assert.rejects(() => atualizar(db, "cidade", "c".repeat(121)), /check constraint/);
    await atualizar(db, "habilidades", ["h".repeat(100)]);
    await assert.rejects(() => atualizar(db, "habilidades", [`${"h".repeat(99)}  `]), /check constraint/);
    await atualizar(db, "areas_de_interesse", Array(50).fill("compliance"));
    await assert.rejects(
      () => atualizar(db, "areas_de_interesse", Array(51).fill("compliance")),
      /check constraint/,
    );
  } finally {
    await db.close();
  }
});

Deno.test("cadastro com campo desconhecido ou texto acolchoado não chega a cadastros_pendentes", async () => {
  const db = await banco();
  try {
    const recusados = [
      cadastro({}, { lixo: "x".repeat(200000) }),
      cadastro({ lixo: "x".repeat(200000) }),
      cadastro({ curso: `Direito${espacos}` }),
      cadastro({ cidade: `Rio de Janeiro, RJ${espacos}` }),
      cadastro({ habilidades: [`Contratos${espacos}`] }),
    ];
    for (const payload of recusados) {
      await assert.rejects(() => cadastrar(db, novo, payload), /inválid/);
    }

    assert.equal(await contar(db, "cadastros_pendentes"), 0);
    assert.equal(await contar(db, "auth.users"), 0);

    await db.query("insert into auth.users(id, email, email_confirmed_at) values ($1, 'c@x.com', now())", [
      dono,
    ]);
    await assert.rejects(
      () =>
        comoUsuario(
          db,
          dono,
          () => db.query("select public.concluir_meu_cadastro($1)", [cadastro({}, { lixo: "x" })]),
        ),
      /inválid/,
    );
    assert.equal(await contar(db, "perfis"), 0);
  } finally {
    await db.close();
  }
});

Deno.test("cadastro com o maior curso e a maior cidade dos catálogos passa e pode ser editado", async () => {
  const db = await banco();
  try {
    assert.ok(maiorCursoDigitado.length > maiorCursoSugerido.length);
    await cadastrar(
      db,
      dono,
      cadastro({
        curso: maiorCursoDigitado,
        cidade: maiorCidade,
        habilidades: cinquentaHabilidadesCheias,
        areas_de_interesse: ["desenvolvimento_web"],
      }),
    );
    await db.query("update auth.users set email_confirmed_at = now() where id = $1", [dono]);

    const criado = (await db.query<Record<string, unknown>>(
      "select curso, cidade, habilidades from perfis where user_id = $1",
      [dono],
    )).rows[0];
    assert.deepEqual({ ...criado }, {
      curso: maiorCursoDigitado,
      cidade: maiorCidade,
      habilidades: cinquentaHabilidadesCheias,
    });

    await atualizar(db, "curso", maiorCursoDigitado);
    await atualizar(db, "cidade", maiorCidade);
    await atualizar(db, "habilidades", cinquentaHabilidadesCheias);
  } finally {
    await db.close();
  }
});

Deno.test("perfil antigo acima do teto faz a migração falhar inteira, sem aplicar nada", async () => {
  const { db, restantes } = await bancoAntesDosTetos();
  try {
    await perfilDe(db, dono, "c".repeat(201));

    await assert.rejects(() => aplicar(db, restantes.slice(0, 1)), /check constraint/);

    const tetos = await contar(
      db,
      "pg_constraint where conrelid = 'public.perfis'::regclass and conname like '%cabe%'",
    );
    assert.equal(tetos, 0);
    await cadastrar(db, novo, cadastro({}, { lixo: "ainda aceito sem a migração" }));
  } finally {
    await db.close();
  }
});
