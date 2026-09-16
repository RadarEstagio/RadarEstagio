import assert from "assert";
import { PGlite } from "pglite";

const MIGRACOES = new URL("../../supabase/migrations/", import.meta.url);
const CONTA_INDISPONIVEL = "42501";
const MINUTO = 60 * 1000;
const HORA = 60 * MINUTO;
const DIA = 24 * HORA;

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
  for (const nome of nomes.sort()) {
    await db.exec(await Deno.readTextFile(new URL(nome, MIGRACOES)));
  }
  return db;
}

function uuidNumero(prefixo: string, numero: number): string {
  return `${prefixo}-0000-4000-8000-${numero.toString().padStart(12, "0")}`;
}

function donoNumero(numero: number): string {
  return uuidNumero("00000000", numero);
}

function perfilNumero(numero: number): string {
  return uuidNumero("11111111", numero);
}

async function criarPerfil(db: PGlite, numero: number, criadoEm = new Date()): Promise<string> {
  const quando = criadoEm.toISOString();
  await db.query(
    "insert into auth.users(id, email, created_at, email_confirmed_at) values ($1, $2, $3, $3)",
    [donoNumero(numero), `pessoa${numero}@example.com`, quando],
  );
  await db.query(
    `insert into perfis(id, user_id, curso, periodo, habilidades, cidade, modalidade, criado_em)
     values ($1, $2, 'Direito', 3, '{Contratos}', 'Rio de Janeiro, RJ', 'presencial', $3)`,
    [perfilNumero(numero), donoNumero(numero), quando],
  );
  return perfilNumero(numero);
}

async function vincular(db: PGlite, perfil: string): Promise<number> {
  const resultado = await db.query(
    `update perfis set telegram_chat_id = $2, token_vinculo = gen_random_uuid()
     where id = $1 and telegram_chat_id is null returning id`,
    [perfil, `chat-${perfil}`],
  );
  return resultado.rows.length;
}

async function perfilVinculado(db: PGlite, numero: number, criadoEm = new Date()) {
  const perfil = await criarPerfil(db, numero, criadoEm);
  assert.equal(await vincular(db, perfil), 1);
  return perfil;
}

async function criarVaga(db: PGlite, numero: number): Promise<number> {
  const resultado = await db.query<{ id: number }>(
    `insert into vagas(fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em)
     values ('adzuna', $1, 'Estágio', 'Empresa', 'Rio de Janeiro', 'desc', $2, now())
     returning id::int`,
    [`vaga-${numero}`, `https://vaga.example/${numero}`],
  );
  return resultado.rows[0].id;
}

async function enviar(db: PGlite, perfil: string, vaga: number, quando = new Date()) {
  await db.query("insert into envios(perfil_id, vaga_id, enviada_em) values ($1, $2, $3)", [
    perfil,
    vaga,
    quando.toISOString(),
  ]);
}

async function abrir(
  db: PGlite,
  perfil: string,
  vaga: number,
  quando = new Date(),
): Promise<string | null> {
  try {
    await db.query(
      `insert into eventos_produto(nome, origem, user_id, perfil_id, vaga_id, ocorrido_em)
       select 'vaga_aberta', 'telegram', user_id, id, $2, $3 from perfis where id = $1`,
      [perfil, vaga, quando.toISOString()],
    );
    return null;
  } catch (erro) {
    return (erro as { code?: string }).code ?? "sem código";
  }
}

async function responder(
  db: PGlite,
  perfil: string,
  vaga: number,
  nome: string,
  quando: Date,
  motivo: string | null = null,
) {
  await db.query(
    `insert into eventos_produto(nome, origem, user_id, perfil_id, vaga_id, propriedades, ocorrido_em)
     select $2::nome_evento_produto, 'telegram', user_id, id, $3, $4, $5 from perfis where id = $1`,
    [perfil, nome, vaga, motivo ? { motivo } : {}, quando.toISOString()],
  );
}

async function eventos(db: PGlite, nome: string, perfil: string, vaga?: number): Promise<number> {
  const filtroDaVaga = vaga === undefined ? "" : "and vaga_id = $3";
  const parametros = vaga === undefined ? [nome, perfil] : [nome, perfil, vaga];
  return (await db.query<{ n: number }>(
    `select count(*)::int n from eventos_produto
     where nome = $1::nome_evento_produto and perfil_id = $2 ${filtroDaVaga}`,
    parametros,
  )).rows[0].n;
}

async function comoDono<T>(db: PGlite, numero: number, acao: () => Promise<T>): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [donoNumero(numero)]);
  await db.exec("set role authenticated");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

async function mudarEntregas(
  db: PGlite,
  numero: number,
  ativo: boolean,
  motivo: string | null,
): Promise<{ ativo: boolean; motivo_pausa: string | null }[]> {
  const resultado = await comoDono(
    db,
    numero,
    () =>
      db.query<{ ativo: boolean; motivo_pausa: string | null }>(
        `update perfis set ativo = $1, motivo_pausa = $2
         where user_id = $3 and ativo = $4 returning ativo, motivo_pausa`,
        [ativo, motivo, donoNumero(numero), !ativo],
      ),
  );
  return resultado.rows;
}

async function desvincularEVincular(db: PGlite, numero: number, perfil: string) {
  await comoDono(db, numero, () => db.exec("select public.desvincular_meu_telegram()"));
  assert.equal(await vincular(db, perfil), 1);
}

Deno.test("link de vaga chamado em laço grava uma abertura só por envio", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    const vaga = await criarVaga(db, 1);
    await enviar(db, perfil, vaga);

    const codigos: (string | null)[] = [];
    for (let i = 0; i < 300; i++) codigos.push(await abrir(db, perfil, vaga));

    assert.deepEqual(codigos, Array(300).fill(null));
    assert.equal(await eventos(db, "vaga_aberta", perfil, vaga), 1);
  } finally {
    await db.close();
  }
});

Deno.test("cada envio guarda a primeira abertura, inclusive a de outra pessoa na mesma vaga", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    const outro = await perfilVinculado(db, 2);
    const vaga = await criarVaga(db, 1);
    const outraVaga = await criarVaga(db, 2);
    const envio = new Date(Date.now() - DIA);
    for (const [quem, qual] of [[perfil, vaga], [perfil, outraVaga], [outro, vaga]] as const) {
      await enviar(db, quem, qual, envio);
    }
    const primeira = new Date(envio.getTime() + 2 * MINUTO);

    assert.equal(await abrir(db, perfil, vaga, primeira), null);
    assert.equal(await abrir(db, perfil, vaga, new Date(primeira.getTime() + HORA)), null);
    assert.equal(await abrir(db, outro, vaga, new Date(primeira.getTime() + 2 * HORA)), null);
    assert.equal(await abrir(db, perfil, outraVaga, new Date(primeira.getTime() + 3 * HORA)), null);

    assert.equal(await eventos(db, "vaga_aberta", perfil, vaga), 1);
    assert.equal(await eventos(db, "vaga_aberta", perfil, outraVaga), 1);
    assert.equal(await eventos(db, "vaga_aberta", outro, vaga), 1);
    const guardada = (await db.query<{ ocorrido_em: Date }>(
      "select ocorrido_em from eventos_produto where nome = 'vaga_aberta' and perfil_id = $1 and vaga_id = $2",
      [perfil, vaga],
    )).rows[0].ocorrido_em;
    assert.equal(guardada.getTime(), primeira.getTime());
  } finally {
    await db.close();
  }
});

Deno.test("abertura de conta pausada continua recusada depois da primeira abertura", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    const vaga = await criarVaga(db, 1);
    await enviar(db, perfil, vaga);
    assert.equal(await abrir(db, perfil, vaga), null);
    assert.equal((await mudarEntregas(db, 1, false, "frequencia")).length, 1);

    assert.equal(await abrir(db, perfil, vaga), CONTA_INDISPONIVEL);
  } finally {
    await db.close();
  }
});

Deno.test("pausar e retomar em laço muda o estado toda vez e grava uma pausa por dia", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    for (let i = 0; i < 100; i++) {
      assert.deepEqual(await mudarEntregas(db, 1, false, "frequencia"), [
        { ativo: false, motivo_pausa: "frequencia" },
      ]);
      assert.deepEqual(await mudarEntregas(db, 1, true, null), [
        { ativo: true, motivo_pausa: null },
      ]);
    }
    assert.deepEqual(await mudarEntregas(db, 1, false, "conseguiu_estagio"), [
      { ativo: false, motivo_pausa: "conseguiu_estagio" },
    ]);
    assert.equal(await eventos(db, "entregas_pausadas", perfil), 1);

    await db.query(
      "update eventos_produto set ocorrido_em = ocorrido_em - interval '25 hours' where perfil_id = $1",
      [perfil],
    );
    assert.equal((await mudarEntregas(db, 1, true, null)).length, 1);
    assert.equal((await mudarEntregas(db, 1, false, "outro")).length, 1);
    assert.equal(await eventos(db, "entregas_pausadas", perfil), 2);
  } finally {
    await db.close();
  }
});

Deno.test("pausa automática por falha de envio nunca falha por causa do evento", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    assert.equal((await mudarEntregas(db, 1, false, "frequencia")).length, 1);
    assert.equal((await mudarEntregas(db, 1, true, null)).length, 1);

    const pausado = await db.query<{ ativo: boolean }>(
      "update perfis set ativo = false, falhas_de_envio = 3 where id = $1 returning ativo",
      [perfil],
    );

    assert.deepEqual(pausado.rows, [{ ativo: false }]);
    assert.equal(await eventos(db, "entregas_pausadas", perfil), 1);
  } finally {
    await db.close();
  }
});

Deno.test("desvincular e vincular de novo em laço grava um vínculo por dia", async () => {
  const db = await banco();
  try {
    const perfil = await perfilVinculado(db, 1);
    for (let i = 0; i < 50; i++) await desvincularEVincular(db, 1, perfil);

    const vinculado = await db.query<{ chat: string | null }>(
      "select telegram_chat_id chat from perfis where id = $1",
      [perfil],
    );
    assert.equal(vinculado.rows[0].chat, `chat-${perfil}`);
    assert.equal(await eventos(db, "telegram_vinculado", perfil), 1);

    await db.query(
      "update eventos_produto set ocorrido_em = ocorrido_em - interval '25 hours' where perfil_id = $1",
      [perfil],
    );
    await desvincularEVincular(db, 1, perfil);
    assert.equal(await eventos(db, "telegram_vinculado", perfil), 2);
  } finally {
    await db.close();
  }
});

async function consultaDoRepositorio(nome: string): Promise<string> {
  const fonte = await Deno.readTextFile(
    new URL("../../radar/storage/postgres.py", import.meta.url),
  );
  const modulo: Record<string, string> = {};
  for (const constante of fonte.matchAll(/^([A-Z_]+) = (\d+)$/gm)) {
    modulo[constante[1]] = constante[2];
  }
  for (const bloco of fonte.matchAll(/^(SQL_\w+) = (f?)"""\n([\s\S]*?)"""$/gm)) {
    modulo[bloco[1]] = bloco[2]
      ? bloco[3].replace(/\{(\w+)\}/g, (trecho, nome: string) => modulo[nome] ?? trecho)
      : bloco[3];
  }
  if (modulo[nome]) return modulo[nome];
  throw new Error(`constante ${nome} não encontrada em postgres.py`);
}

async function historicoDoPiloto(db: PGlite, inicio: Date) {
  const em = (deslocamento: number) => new Date(inicio.getTime() + deslocamento);
  const [p1, p2, p3] = [
    await criarPerfil(db, 1, inicio),
    await criarPerfil(db, 2, em(HORA)),
    await criarPerfil(db, 3, inicio),
  ];
  for (const perfil of [p1, p2, p3]) assert.equal(await vincular(db, perfil), 1);
  for (let i = 0; i < 3; i++) await desvincularEVincular(db, 1, p1);
  const [v1, v2, v3, v4] = [
    await criarVaga(db, 1),
    await criarVaga(db, 2),
    await criarVaga(db, 3),
    await criarVaga(db, 4),
  ];
  await enviar(db, p1, v1, em(10 * MINUTO));
  await enviar(db, p1, v2, em(10 * MINUTO));
  await enviar(db, p1, v3, em(DIA));
  await enviar(db, p2, v1, em(2 * HORA));
  await enviar(db, p2, v4, em(2 * HORA));
  await enviar(db, p3, v4, em(DIA));

  const aberturas: [string, number, number][] = [
    [p1, v1, 12 * MINUTO],
    [p1, v1, 12 * MINUTO + 1000],
    [p1, v1, 40 * MINUTO],
    [p1, v1, 2 * DIA],
    [p1, v2, 15 * MINUTO],
    [p1, v2, 16 * MINUTO],
    [p1, v3, DIA + 5 * MINUTO],
    [p1, v3, DIA + 6 * MINUTO],
    [p1, v3, DIA + 30 * MINUTO],
    [p2, v1, 2 * HORA + MINUTO],
    [p2, v1, 2 * HORA + 2 * MINUTO],
  ];
  for (const [perfil, vaga, deslocamento] of aberturas) {
    assert.equal(await abrir(db, perfil, vaga, em(deslocamento)), null);
  }
  await responder(db, p1, v1, "vaga_util", em(20 * MINUTO));
  await responder(db, p1, v1, "vaga_irrelevante", em(DIA), "motivo_nota");
  await responder(db, p1, v1, "vaga_util", em(2 * DIA + MINUTO));
  await responder(db, p1, v2, "vaga_irrelevante", em(17 * MINUTO), "motivo_encerrada");
  await responder(db, p1, v3, "vaga_irrelevante", em(DIA + 5 * MINUTO + 30000), "motivo_encerrada");
  await responder(db, p2, v4, "vaga_irrelevante", em(3 * HORA), "motivo_encerrada");
  await responder(db, p2, v1, "vaga_irrelevante", em(2 * HORA + 3 * MINUTO), "motivo_area");

  for (let i = 0; i < 4; i++) {
    assert.equal((await mudarEntregas(db, 2, false, "frequencia")).length, 1);
    assert.equal((await mudarEntregas(db, 2, true, null)).length, 1);
  }
  assert.equal((await mudarEntregas(db, 3, false, "frequencia")).length, 1);
  assert.equal((await mudarEntregas(db, 3, true, null)).length, 1);
  assert.equal((await mudarEntregas(db, 3, false, "sem_vagas_uteis")).length, 1);
}

async function leiturasDoHistorico(db: PGlite, fim: Date) {
  const agora = `timestamptz '${fim.toISOString()}'`;
  const metricas = (await Deno.readTextFile(
    new URL("../../radar/storage/metricas.sql", import.meta.url),
  )).replaceAll("%(dias)s", "30").replaceAll("now()", agora);
  const encerradas = (await consultaDoRepositorio("SQL_VAGAS_ENCERRADAS"))
    .replaceAll("now()", agora);
  const brutos = await db.query<{ nome: string; n: number }>(
    "select nome::text, count(*)::int n from eventos_produto group by 1 order by 1",
  );
  return {
    metricas: JSON.parse(JSON.stringify((await db.query(metricas)).rows)),
    encerradas: (await db.query<{ id_externo: string }>(encerradas)).rows
      .map((linha) => linha.id_externo).sort(),
    brutos: Object.fromEntries(brutos.rows.map((linha) => [linha.nome, linha.n])),
  };
}

Deno.test("descartar repetições não muda nenhum número das métricas nem as vagas encerradas", async () => {
  const semRegra = await banco();
  const comRegra = await banco();
  try {
    await semRegra.exec("alter table eventos_produto disable trigger user");
    const inicio = new Date(Math.floor((Date.now() - 3 * DIA) / MINUTO) * MINUTO);
    const fim = new Date(inicio.getTime() + 4 * DIA);
    await historicoDoPiloto(semRegra, inicio);
    await historicoDoPiloto(comRegra, inicio);

    const antes = await leiturasDoHistorico(semRegra, fim);
    const depois = await leiturasDoHistorico(comRegra, fim);
    console.log(`eventos brutos sem a regra ${JSON.stringify(antes.brutos)}`);
    console.log(`eventos brutos com a regra ${JSON.stringify(depois.brutos)}`);

    assert.deepEqual(depois.metricas, antes.metricas);
    assert.deepEqual(depois.encerradas, antes.encerradas);
    assert.deepEqual(antes.encerradas, ["vaga-2", "vaga-3"]);
    assert.equal(antes.metricas[0].vagas_abertas, 4);
    assert.equal(antes.metricas[0].perfis_com_vaga_aberta, 2);
    assert.deepEqual(
      { ...antes.brutos, vaga_aberta: 4, entregas_pausadas: 2, telegram_vinculado: 3 },
      depois.brutos,
    );
    assert.deepEqual(
      [antes.brutos.vaga_aberta, antes.brutos.entregas_pausadas, antes.brutos.telegram_vinculado],
      [11, 6, 6],
    );
  } finally {
    await semRegra.close();
    await comRegra.close();
  }
});
