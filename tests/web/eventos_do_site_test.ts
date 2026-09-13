import assert from "assert";
import { PGlite } from "pglite";

const TETO_DOS_VISITANTES = 2400;
const TETO_DAS_CONTAS = 900;
const LIMITE_POR_SESSAO = 60;
const LIMITE_POR_CONTA = 60;
const CADASTROS_NA_DIVULGACAO = 150;
const CURIOSOS_POR_CADASTRO = 3;
const LIMITE_EXCEDIDO = "PT429";
const CHECK_VIOLADO = "23514";

async function bancoComAsMigracoes(): Promise<PGlite> {
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
    grant usage on schema public, auth to authenticated, anon;
    grant execute on function auth.uid() to authenticated, anon;
  `);
  const diretorio = new URL("../../supabase/migrations/", import.meta.url);
  const arquivos: string[] = [];
  for await (const entrada of Deno.readDir(diretorio)) {
    if (entrada.name.endsWith(".sql")) arquivos.push(entrada.name);
  }
  for (const arquivo of arquivos.sort()) {
    await db.exec(await Deno.readTextFile(new URL(arquivo, diretorio)));
  }
  return db;
}

async function comoVisitante<T>(db: PGlite, acao: () => Promise<T>): Promise<T> {
  await db.exec("set role anon");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

async function comoConta<T>(
  db: PGlite,
  userId: string,
  acao: () => Promise<T>,
): Promise<T> {
  await db.query("select set_config('request.jwt.claim.sub', $1, false)", [userId]);
  await db.exec("set role authenticated");
  try {
    return await acao();
  } finally {
    await db.exec("reset role");
  }
}

async function registrar(
  db: PGlite,
  nome: string,
  sessao: string,
  userId: string | null = null,
  propriedades: Record<string, unknown> = {},
): Promise<string | null> {
  try {
    await db.query(
      "insert into eventos_produto(nome, sessao_id, user_id, propriedades) values ($1, $2, $3, $4)",
      [nome, sessao, userId, propriedades],
    );
    return null;
  } catch (erro) {
    return (erro as { code?: string }).code ?? "sem código";
  }
}

async function eventosDoSite(db: PGlite): Promise<number> {
  return (await db.query<{ n: number }>(
    "select count(*)::int n from eventos_produto where origem = 'web'",
  )).rows[0].n;
}

async function eventosDoSitePorQuem(db: PGlite): Promise<{ visitantes: number; contas: number }> {
  return (await db.query<{ visitantes: number; contas: number }>(
    `select count(*) filter (where user_id is null)::int visitantes,
            count(*) filter (where user_id is not null)::int contas
     from eventos_produto where origem = 'web'`,
  )).rows[0];
}

async function criarConta(db: PGlite, userId: string): Promise<void> {
  await db.query(
    "insert into auth.users(id, email, email_confirmed_at) values ($1, $2, now())",
    [userId, `${userId}@example.com`],
  );
}

function contaNumero(numero: number): string {
  return `00000000-0000-4000-8000-${numero.toString().padStart(12, "0")}`;
}

async function esgotarOTetoDosVisitantes(db: PGlite): Promise<void> {
  const recusas = await comoVisitante(db, async () => {
    let recusadas = 0;
    for (let i = 0; i < TETO_DOS_VISITANTES; i++) {
      if (await registrar(db, "landing_visualizada", crypto.randomUUID())) recusadas++;
    }
    return recusadas;
  });
  assert.equal(recusas, 0);
  assert.equal(
    await comoVisitante(db, () => registrar(db, "landing_visualizada", crypto.randomUUID())),
    LIMITE_EXCEDIDO,
  );
}

function cadastroDaSessao(sessao: string) {
  return {
    perfil: {
      curso: "Computação",
      periodo: 3,
      habilidades: ["Python"],
      cidade: "Recife, PE",
      modalidade: "remoto",
      areas_de_interesse: ["dados_ia"],
    },
    aceitou_termos: true,
    aceita_emails: false,
    versao_dos_termos: "2026-09-05",
    sessao_id: sessao,
  };
}

async function cadastrarConfirmarEVincular(
  db: PGlite,
  dono: string,
  sessao: string,
): Promise<(string | null)[]> {
  await db.query(
    "insert into auth.users(id, email, raw_user_meta_data) values ($1, $2, $3)",
    [dono, "pessoa@example.com", { cadastro_radar: cadastroDaSessao(sessao) }],
  );
  await db.query("update auth.users set email_confirmed_at = now() where id = $1", [dono]);
  const recusas = await comoConta(db, dono, async () => [
    await registrar(db, "perfil_salvo", sessao, dono),
    await registrar(db, "telegram_aberto", sessao, dono),
    await registrar(db, "telegram_aberto", sessao, dono),
  ]);
  const perfil = (await db.query<{ id: string }>(
    `update perfis set telegram_chat_id = '555', token_vinculo = gen_random_uuid()
     where user_id = $1 returning id`,
    [dono],
  )).rows[0].id;
  await db.query("update perfis set ativado_em = now() where id = $1", [perfil]);
  await db.query(
    `insert into eventos_produto(nome, origem, user_id, perfil_id)
     values ('vaga_aberta', 'telegram', $1, $2), ('vaga_util', 'telegram', $1, $2)`,
    [dono, perfil],
  );
  return recusas;
}

async function eventosPorNome(db: PGlite, dono: string, sessao: string) {
  const linhas = (await db.query<{ nome: string; origem: string; n: number }>(
    `select nome::text, origem, count(*)::int n from eventos_produto
     where sessao_id = $1 or user_id = $2 group by 1, 2 order by 2, 1`,
    [sessao, dono],
  )).rows;
  return Object.fromEntries(linhas.map((l) => [`${l.origem}:${l.nome}`, l.n]));
}

Deno.test("visitante que troca de sessão a cada evento para no teto da hora", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const antes = await eventosDoSite(db);
    const codigos = await comoVisitante(db, async () => {
      const resultado: (string | null)[] = [];
      for (let i = 0; i < TETO_DOS_VISITANTES + 100; i++) {
        resultado.push(
          await registrar(db, "landing_visualizada", crypto.randomUUID(), null, { pagina: "/" }),
        );
      }
      return resultado;
    });
    const depois = await eventosDoSite(db);
    console.log(
      `visitante tentou ${TETO_DOS_VISITANTES + 100} eventos com sessões novas: antes ${antes}, depois ${depois}`,
    );
    assert.equal(antes, 0);
    assert.equal(depois, TETO_DOS_VISITANTES);
    assert.deepEqual(
      codigos.slice(TETO_DOS_VISITANTES),
      Array(100).fill(LIMITE_EXCEDIDO),
    );
  } finally {
    await db.close();
  }
});

Deno.test("inserção em lote conta cada linha no teto da hora", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const lote = () =>
      comoVisitante(db, () =>
        db.query(
          `insert into eventos_produto(nome, sessao_id, propriedades)
           select 'landing_visualizada', gen_random_uuid(), '{}'
           from generate_series(1, $1::int)`,
          [TETO_DOS_VISITANTES + 1],
        ));
    await assert.rejects(lote, { code: LIMITE_EXCEDIDO });
    assert.equal(await eventosDoSite(db), 0);
  } finally {
    await db.close();
  }
});

Deno.test("propriedades grandes vindas do site são recusadas", async () => {
  const db = await bancoComAsMigracoes();
  const dono = contaNumero(1);
  try {
    await criarConta(db, dono);
    const lixo = { lixo: "x".repeat(300) };
    const doVisitante = await comoVisitante(db, async () => [
      await registrar(db, "landing_visualizada", crypto.randomUUID(), null, lixo),
      await registrar(db, "landing_visualizada", crypto.randomUUID(), null, { pagina: "/" }),
      await registrar(db, "cta_cadastro_aberto", crypto.randomUUID(), null, {
        origem: "como_funciona",
      }),
      await registrar(db, "etapa_habilidades_concluida", crypto.randomUUID(), null, {
        quantidade: 50,
      }),
    ]);
    const daConta = await comoConta(db, dono, async () => [
      await registrar(db, "telegram_aberto", crypto.randomUUID(), dono, lixo),
      await registrar(db, "telegram_aberto", crypto.randomUUID(), dono),
    ]);
    assert.deepEqual(doVisitante, [CHECK_VIOLADO, null, null, null]);
    assert.deepEqual(daConta, [CHECK_VIOLADO, null]);
  } finally {
    await db.close();
  }
});

Deno.test("uma sessão sozinha para no limite de eventos da hora", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const sessao = crypto.randomUUID();
    const codigos = await comoVisitante(db, async () => {
      const resultado: (string | null)[] = [];
      for (let i = 0; i <= LIMITE_POR_SESSAO; i++) {
        resultado.push(await registrar(db, "etapa_perfil_concluida", sessao));
      }
      return resultado;
    });
    assert.deepEqual(codigos.slice(0, LIMITE_POR_SESSAO), Array(LIMITE_POR_SESSAO).fill(null));
    assert.equal(codigos[LIMITE_POR_SESSAO], LIMITE_EXCEDIDO);
    assert.equal(
      await comoVisitante(db, () => registrar(db, "etapa_perfil_concluida", crypto.randomUUID())),
      null,
    );
  } finally {
    await db.close();
  }
});

Deno.test("conta autenticada que troca de sessão para no limite da conta", async () => {
  const db = await bancoComAsMigracoes();
  const dono = contaNumero(1);
  const outra = contaNumero(2);
  try {
    await criarConta(db, dono);
    await criarConta(db, outra);
    const codigos = await comoConta(db, dono, async () => {
      const resultado: (string | null)[] = [];
      for (let i = 0; i <= LIMITE_POR_CONTA; i++) {
        resultado.push(await registrar(db, "telegram_aberto", crypto.randomUUID(), dono));
      }
      return resultado;
    });
    assert.deepEqual(codigos.slice(0, LIMITE_POR_CONTA), Array(LIMITE_POR_CONTA).fill(null));
    assert.equal(codigos[LIMITE_POR_CONTA], LIMITE_EXCEDIDO);
    assert.equal(
      await comoConta(db, outra, () => registrar(db, "telegram_aberto", crypto.randomUUID(), outra)),
      null,
    );
  } finally {
    await db.close();
  }
});

Deno.test("contas autenticadas têm teto da hora próprio, separado dos visitantes", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const contas = TETO_DAS_CONTAS / LIMITE_POR_CONTA;
    for (let numero = 1; numero <= contas + 1; numero++) {
      await criarConta(db, contaNumero(numero));
    }
    for (let numero = 1; numero <= contas; numero++) {
      const dono = contaNumero(numero);
      const recusas = await comoConta(db, dono, async () => {
        let recusadas = 0;
        for (let i = 0; i < LIMITE_POR_CONTA; i++) {
          if (await registrar(db, "telegram_aberto", crypto.randomUUID(), dono)) recusadas++;
        }
        return recusadas;
      });
      assert.equal(recusas, 0);
    }
    const ultima = contaNumero(contas + 1);
    assert.equal(
      await comoConta(db, ultima, () => registrar(db, "perfil_salvo", crypto.randomUUID(), ultima)),
      LIMITE_EXCEDIDO,
    );
    assert.equal(
      await comoVisitante(db, () => registrar(db, "landing_visualizada", crypto.randomUUID())),
      null,
    );
  } finally {
    await db.close();
  }
});

Deno.test("pessoa da landing ao vínculo tem o funil inteiro gravado", async () => {
  const db = await bancoComAsMigracoes();
  const dono = contaNumero(1);
  const sessao = crypto.randomUUID();
  try {
    const jornada: [string, Record<string, unknown>][] = [
      ["landing_visualizada", { pagina: "/" }],
      ["cta_cadastro_aberto", { origem: "hero" }],
      ["etapa_perfil_concluida", {}],
      ["etapa_habilidades_concluida", { quantidade: 3 }],
      ["etapa_preferencias_concluida", {}],
      ["landing_visualizada", { pagina: "/" }],
      ["cta_cadastro_aberto", { origem: "cta_final" }],
      ["etapa_perfil_concluida", {}],
      ["etapa_habilidades_concluida", { quantidade: 4 }],
      ["etapa_preferencias_concluida", {}],
      ["etapa_preferencias_concluida", {}],
    ];
    const doVisitante = await comoVisitante(db, async () => {
      const resultado: (string | null)[] = [];
      for (const [nome, propriedades] of jornada) {
        resultado.push(await registrar(db, nome, sessao, null, propriedades));
      }
      return resultado;
    });
    const daConta = await cadastrarConfirmarEVincular(db, dono, sessao);

    assert.deepEqual(doVisitante, Array(jornada.length).fill(null));
    assert.deepEqual(daConta, [null, null, null]);
    assert.deepEqual(await eventosPorNome(db, dono, sessao), {
      "banco:conta_criada": 1,
      "banco:email_confirmado": 1,
      "banco:perfil_salvo": 1,
      "banco:primeira_recomendacao_enviada": 1,
      "banco:telegram_vinculado": 1,
      "telegram:vaga_aberta": 1,
      "telegram:vaga_util": 1,
      "web:cta_cadastro_aberto": 2,
      "web:etapa_habilidades_concluida": 2,
      "web:etapa_perfil_concluida": 2,
      "web:etapa_preferencias_concluida": 3,
      "web:landing_visualizada": 2,
      "web:perfil_salvo": 1,
      "web:telegram_aberto": 2,
    });
  } finally {
    await db.close();
  }
});

Deno.test("dia de divulgação com 150 cadastros e 450 curiosos na mesma hora grava tudo", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const funilComIdasEVoltas: [string, Record<string, unknown>][] = [
      ["landing_visualizada", { pagina: "/" }],
      ["cta_cadastro_aberto", { origem: "hero" }],
      ["etapa_perfil_concluida", {}],
      ["etapa_habilidades_concluida", { quantidade: 5 }],
      ["etapa_preferencias_concluida", {}],
      ["cta_cadastro_aberto", { origem: "cta_final" }],
      ["etapa_perfil_concluida", {}],
      ["etapa_habilidades_concluida", { quantidade: 6 }],
      ["etapa_preferencias_concluida", {}],
      ["etapa_preferencias_concluida", {}],
    ];
    const depoisDaConta = [
      "landing_visualizada",
      "perfil_salvo",
      "telegram_aberto",
      "telegram_aberto",
      "telegram_aberto",
      "perfil_salvo",
    ];
    const recusas: Record<string, number> = {};
    const anotar = (codigo: string | null) => {
      if (codigo) recusas[codigo] = (recusas[codigo] ?? 0) + 1;
    };
    for (let pessoa = 1; pessoa <= CADASTROS_NA_DIVULGACAO; pessoa++) {
      const sessao = crypto.randomUUID();
      const dono = contaNumero(pessoa);
      await comoVisitante(db, async () => {
        for (const [nome, propriedades] of funilComIdasEVoltas) {
          anotar(await registrar(db, nome, sessao, null, propriedades));
        }
        for (let curioso = 0; curioso < CURIOSOS_POR_CADASTRO; curioso++) {
          const sessaoDoCurioso = crypto.randomUUID();
          anotar(await registrar(db, "landing_visualizada", sessaoDoCurioso, null, { pagina: "/" }));
          anotar(
            await registrar(db, "cta_cadastro_aberto", sessaoDoCurioso, null, { origem: "hero" }),
          );
        }
      });
      await criarConta(db, dono);
      await comoConta(db, dono, async () => {
        for (const nome of depoisDaConta) anotar(await registrar(db, nome, sessao, dono));
      });
    }
    const gravados = await eventosDoSitePorQuem(db);
    console.log(
      `divulgação com ${CADASTROS_NA_DIVULGACAO} cadastros: ${JSON.stringify(gravados)}, recusas ${
        JSON.stringify(recusas)
      }`,
    );

    assert.deepEqual(recusas, {});
    assert.deepEqual(gravados, { visitantes: TETO_DOS_VISITANTES, contas: TETO_DAS_CONTAS });
  } finally {
    await db.close();
  }
});

Deno.test("teto dos visitantes esgotado não barra cadastro, conta, vínculo nem Telegram", async () => {
  const db = await bancoComAsMigracoes();
  const dono = contaNumero(1);
  const sessao = crypto.randomUUID();
  try {
    await esgotarOTetoDosVisitantes(db);
    const daConta = await cadastrarConfirmarEVincular(db, dono, sessao);

    assert.deepEqual(daConta, [null, null, null]);
    const eventos = await eventosPorNome(db, dono, sessao);
    for (
      const esperado of [
        "banco:conta_criada",
        "banco:email_confirmado",
        "banco:perfil_salvo",
        "banco:telegram_vinculado",
        "banco:primeira_recomendacao_enviada",
        "telegram:vaga_aberta",
        "telegram:vaga_util",
        "web:perfil_salvo",
        "web:telegram_aberto",
      ]
    ) {
      assert.ok(eventos[esperado] >= 1, `${esperado} não foi gravado`);
    }
  } finally {
    await db.close();
  }
});

Deno.test("limites valem por uma hora e a contagem antiga é apagada", async () => {
  const db = await bancoComAsMigracoes();
  try {
    const sessao = crypto.randomUUID();
    const aceitas = await comoVisitante(db, async () => {
      let total = 0;
      for (let i = 0; i < TETO_DOS_VISITANTES; i++) {
        const daMesmaSessao = i < LIMITE_POR_SESSAO;
        const codigo = await registrar(
          db,
          "etapa_perfil_concluida",
          daMesmaSessao ? sessao : crypto.randomUUID(),
        );
        if (codigo === null) total++;
      }
      return total;
    });
    assert.equal(aceitas, TETO_DOS_VISITANTES);
    assert.equal(
      await comoVisitante(db, () => registrar(db, "etapa_perfil_concluida", sessao)),
      LIMITE_EXCEDIDO,
    );
    assert.equal(
      await comoVisitante(db, () => registrar(db, "landing_visualizada", crypto.randomUUID())),
      LIMITE_EXCEDIDO,
    );

    await db.exec(`
      update eventos_produto set ocorrido_em = ocorrido_em - interval '61 minutes';
      update eventos_do_site_por_hora set hora = hora - interval '2 days';
    `);
    assert.equal(
      await comoVisitante(db, () => registrar(db, "landing_visualizada", crypto.randomUUID())),
      null,
    );
    assert.equal(
      await comoVisitante(db, () => registrar(db, "etapa_perfil_concluida", sessao)),
      null,
    );
    const horas = (await db.query<{ n: number }>(
      "select count(*)::int n from eventos_do_site_por_hora",
    )).rows[0].n;
    assert.equal(horas, 1);
    await assert.rejects(() =>
      comoVisitante(db, () => db.query("select * from eventos_do_site_por_hora"))
    );
  } finally {
    await db.close();
  }
});
