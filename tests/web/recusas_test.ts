import assert from "assert";
import { PGlite } from "pglite";

async function consulta(nome: string): Promise<string> {
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
  const sql = modulo[nome];
  assert.ok(sql, `constante ${nome} não encontrada em postgres.py`);
  return sql.replaceAll("%(perfil_id)s", "$1").replaceAll("%(limiar)s", "$2::int");
}

async function bancoComFeedback(): Promise<PGlite> {
  const db = new PGlite();
  await db.exec(`
    create table vagas(id int primary key, fonte text, id_externo text, titulo text,
      empresa text, localizacao text, descricao text, url text, publicada_em timestamptz,
      modalidade text, extracao jsonb);
    create table perfis(id int primary key, ativo boolean not null default true,
      excluida_em timestamptz, telegram_chat_id text default 'chat');
    insert into perfis(id) select generate_series(1, 9);
    create table eventos_produto(id serial, nome text, perfil_id int, vaga_id int,
      propriedades jsonb default '{}', ocorrido_em timestamptz);
    insert into vagas values
      (1,'adzuna','1','Estágio A','Empresa','Rio de Janeiro','desc','https://x/1',
       '2026-09-01','presencial','{"areas_da_vaga":["direito_civil"]}'),
      (2,'adzuna','2','Estágio B','Empresa','Rio de Janeiro','desc','https://x/2',
       '2026-09-01','presencial','{"areas_da_vaga":["direito_civil"]}');
  `);
  return db;
}

async function recusa(db: PGlite, vaga: number, motivo: string, quando: string) {
  await db.query(
    `insert into eventos_produto(nome, perfil_id, vaga_id, propriedades, ocorrido_em)
     values ('vaga_irrelevante', 1, $1, jsonb_build_object('motivo', $2::text), ${quando})`,
    [vaga, motivo],
  );
}

async function elogio(db: PGlite, vaga: number, quando: string) {
  await db.query(
    `insert into eventos_produto(nome, perfil_id, vaga_id, ocorrido_em)
     values ('vaga_util', 1, $1, ${quando})`,
    [vaga],
  );
}

Deno.test("área recusada nas duas vagas desconta o interesse da subárea", async () => {
  const db = await bancoComFeedback();
  try {
    await recusa(db, 1, "motivo_area", "now()");
    await recusa(db, 2, "motivo_area", "now()");

    const linhas = await db.query(await consulta("SQL_AREAS_RECUSADAS"), [1, 2]);

    assert.deepEqual(linhas.rows, [{ area: "direito_civil" }]);
  } finally {
    await db.close();
  }
});

Deno.test("recusa corrigida para 'essa serviu' deixa de contar como recusa de área", async () => {
  const db = await bancoComFeedback();
  try {
    await recusa(db, 1, "motivo_area", "now() - interval '2 hours'");
    await recusa(db, 2, "motivo_area", "now() - interval '2 hours'");
    await elogio(db, 1, "now() - interval '1 hour'");
    await elogio(db, 2, "now() - interval '1 hour'");

    const linhas = await db.query(await consulta("SQL_AREAS_RECUSADAS"), [1, 2]);

    assert.deepEqual(linhas.rows, []);
  } finally {
    await db.close();
  }
});

Deno.test("uma correção só derruba a contagem abaixo do limiar", async () => {
  const db = await bancoComFeedback();
  try {
    await recusa(db, 1, "motivo_area", "now() - interval '2 hours'");
    await recusa(db, 2, "motivo_area", "now() - interval '2 hours'");
    await elogio(db, 2, "now() - interval '1 hour'");

    const linhas = await db.query(await consulta("SQL_AREAS_RECUSADAS"), [1, 2]);

    assert.deepEqual(linhas.rows, []);
  } finally {
    await db.close();
  }
});

Deno.test("'já vi essa' corrigido para positivo volta a permitir a vaga", async () => {
  const db = await bancoComFeedback();
  try {
    await recusa(db, 1, "motivo_repetida", "now() - interval '2 hours'");
    await recusa(db, 2, "motivo_repetida", "now() - interval '2 hours'");
    await elogio(db, 1, "now() - interval '1 hour'");

    const linhas = await db.query(
      await consulta("SQL_VAGAS_QUE_NAO_VOLTAM"),
      [1],
    );

    assert.deepEqual(linhas.rows.map((linha) => (linha as { id_externo: string }).id_externo), [
      "2",
    ]);
  } finally {
    await db.close();
  }
});

Deno.test("resposta positiva antiga não apaga a recusa mais recente", async () => {
  const db = await bancoComFeedback();
  try {
    await elogio(db, 1, "now() - interval '3 hours'");
    await elogio(db, 2, "now() - interval '3 hours'");
    await recusa(db, 1, "motivo_area", "now() - interval '1 hour'");
    await recusa(db, 2, "motivo_area", "now() - interval '1 hour'");

    const linhas = await db.query(await consulta("SQL_AREAS_RECUSADAS"), [1, 2]);

    assert.deepEqual(linhas.rows, [{ area: "direito_civil" }]);
  } finally {
    await db.close();
  }
});

async function eventoDaVaga(
  db: PGlite,
  { nome, perfil, vaga, quando, motivo }: {
    nome: string;
    perfil: number;
    vaga: number;
    quando: string;
    motivo?: string;
  },
) {
  await db.query(
    `insert into eventos_produto(nome, perfil_id, vaga_id, propriedades, ocorrido_em)
     values ($1, $2, $3, $4::jsonb, ${quando})`,
    [nome, perfil, vaga, JSON.stringify(motivo ? { motivo } : {})],
  );
}

async function encerradas(db: PGlite) {
  const linhas = await db.query<{ fonte: string; id_externo: string; titulo: string }>(
    await consulta("SQL_VAGAS_ENCERRADAS"),
  );
  return linhas.rows.map((linha) => `${linha.fonte}:${linha.id_externo}:${linha.titulo}`).sort();
}

async function vagasAte(db: PGlite, ultima: number) {
  await db.query(
    `insert into vagas
     select n, 'adzuna', n::text, 'Estágio ' || n, 'Empresa', 'Rio de Janeiro', 'desc',
            'https://x/' || n, '2026-09-01', 'presencial', '{}'
     from generate_series(3, $1::int) n`,
    [ultima],
  );
}

async function marcarComoEncerrada(
  db: PGlite,
  perfil: number,
  vaga: number,
  { abriuAntes = true, horasAtras = 1 }: { abriuAntes?: boolean; horasAtras?: number } = {},
) {
  if (abriuAntes) {
    await eventoDaVaga(db, {
      nome: "vaga_aberta",
      perfil,
      vaga,
      quando: `now() - interval '${horasAtras + 1} hours'`,
    });
  }
  await eventoDaVaga(db, {
    nome: "vaga_irrelevante",
    perfil,
    vaga,
    quando: `now() - interval '${horasAtras} hours'`,
    motivo: "motivo_encerrada",
  });
}

async function queNaoVoltam(db: PGlite, perfil: number) {
  const linhas = await db.query<{ id_externo: string }>(
    await consulta("SQL_VAGAS_QUE_NAO_VOLTAM"),
    [perfil],
  );
  return linhas.rows.map((linha) => linha.id_externo).sort();
}

Deno.test("vaga marcada como encerrada por quem a abriu fica de fora para todos", async () => {
  const db = await bancoComFeedback();
  try {
    await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 2, vaga: 1, quando: "now() - interval '2 hours'" });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 1,
      quando: "now() - interval '1 hour'",
      motivo: "motivo_encerrada",
    });

    assert.deepEqual(await encerradas(db), ["adzuna:1:Estágio A"]);
  } finally {
    await db.close();
  }
});

Deno.test("marcar como encerrada sem ter aberto a vaga antes não tira a vaga de ninguém", async () => {
  const db = await bancoComFeedback();
  try {
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 1,
      quando: "now() - interval '2 hours'",
      motivo: "motivo_encerrada",
    });
    await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 2, vaga: 1, quando: "now() - interval '1 hour'" });
    await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 3, vaga: 2, quando: "now() - interval '2 hours'" });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 4,
      vaga: 2,
      quando: "now() - interval '1 hour'",
      motivo: "motivo_encerrada",
    });

    assert.deepEqual(await encerradas(db), []);
  } finally {
    await db.close();
  }
});

Deno.test("encerrada trocada por outra resposta ou outro motivo não conta como encerrada", async () => {
  const db = await bancoComFeedback();
  try {
    for (const vaga of [1, 2]) {
      await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 2, vaga, quando: "now() - interval '3 hours'" });
    }
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 1,
      quando: "now() - interval '2 hours'",
      motivo: "motivo_encerrada",
    });
    await eventoDaVaga(db, { nome: "vaga_util", perfil: 2, vaga: 1, quando: "now() - interval '1 hour'" });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 2,
      quando: "now() - interval '2 hours'",
      motivo: "motivo_encerrada",
    });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 2,
      quando: "now() - interval '1 hour'",
      motivo: "motivo_repetida",
    });

    assert.deepEqual(await encerradas(db), []);
  } finally {
    await db.close();
  }
});

Deno.test("abrir outra vaga não vale como abertura da vaga marcada como encerrada", async () => {
  const db = await bancoComFeedback();
  try {
    await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 2, vaga: 2, quando: "now() - interval '2 hours'" });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 1,
      quando: "now() - interval '1 hour'",
      motivo: "motivo_encerrada",
    });

    assert.deepEqual(await encerradas(db), []);
  } finally {
    await db.close();
  }
});

Deno.test("marcação de vaga encerrada com mais de 30 dias deixa de contar", async () => {
  const db = await bancoComFeedback();
  try {
    await eventoDaVaga(db, { nome: "vaga_aberta", perfil: 2, vaga: 1, quando: "now() - interval '32 days'" });
    await eventoDaVaga(db, {
      nome: "vaga_irrelevante",
      perfil: 2,
      vaga: 1,
      quando: "now() - interval '31 days'",
      motivo: "motivo_encerrada",
    });

    assert.deepEqual(await encerradas(db), []);
  } finally {
    await db.close();
  }
});

Deno.test("marcação de conta excluída ou já apagada não tira a vaga dos outros", async () => {
  const db = await bancoComFeedback();
  try {
    await db.exec("update perfis set excluida_em = now() where id = 2;");
    for (const perfil of [2, 99]) {
      await marcarComoEncerrada(db, perfil, 1);
    }
    await marcarComoEncerrada(db, 5, 2);

    assert.deepEqual(await encerradas(db), ["adzuna:2:Estágio B"]);
  } finally {
    await db.close();
  }
});

Deno.test("marcação de conta pausada ou sem Telegram continua tirando a vaga dos outros", async () => {
  const db = await bancoComFeedback();
  try {
    await vagasAte(db, 3);
    await db.exec(`
      update perfis set ativo = false where id = 3;
      update perfis set telegram_chat_id = null where id = 4;
      update perfis set ativo = false, telegram_chat_id = null where id = 5;
    `);
    await marcarComoEncerrada(db, 3, 1);
    await marcarComoEncerrada(db, 4, 2);
    await marcarComoEncerrada(db, 5, 3);

    assert.deepEqual(await encerradas(db), [
      "adzuna:1:Estágio A",
      "adzuna:2:Estágio B",
      "adzuna:3:Estágio 3",
    ]);
  } finally {
    await db.close();
  }
});

Deno.test("as três primeiras marcações do perfil saem para todos e da quarta em diante só para quem marcou", async () => {
  const db = await bancoComFeedback();
  try {
    await vagasAte(db, 7);
    for (const [vaga, horasAtras] of [[7, 7], [6, 6], [5, 5]]) {
      await marcarComoEncerrada(db, 3, vaga, { horasAtras });
    }

    assert.deepEqual(await encerradas(db), [
      "adzuna:5:Estágio 5",
      "adzuna:6:Estágio 6",
      "adzuna:7:Estágio 7",
    ]);

    await marcarComoEncerrada(db, 3, 4, { horasAtras: 1 });

    assert.deepEqual(await encerradas(db), [
      "adzuna:5:Estágio 5",
      "adzuna:6:Estágio 6",
      "adzuna:7:Estágio 7",
    ]);
    assert.deepEqual(await queNaoVoltam(db, 3), ["4", "5", "6", "7"]);
  } finally {
    await db.close();
  }
});

Deno.test("marcações no mesmo instante entram na ordem pela vaga", async () => {
  const db = await bancoComFeedback();
  try {
    await vagasAte(db, 8);
    await db.exec(`
      insert into eventos_produto(nome, perfil_id, vaga_id, propriedades, ocorrido_em)
      select evento.nome, 2, vaga, evento.propriedades::jsonb, now() - evento.atraso
      from unnest(array[8, 3, 2, 1]) vaga,
           (values ('vaga_aberta', '{}', interval '2 hours'),
                   ('vaga_irrelevante', '{"motivo":"motivo_encerrada"}', interval '1 hour'))
             evento(nome, propriedades, atraso);
    `);

    assert.deepEqual(await encerradas(db), [
      "adzuna:1:Estágio A",
      "adzuna:2:Estágio B",
      "adzuna:3:Estágio 3",
    ]);
  } finally {
    await db.close();
  }
});

Deno.test("marcação sem abertura ocupa lugar na ordem e desfazer uma marcação faz a seguinte subir", async () => {
  const db = await bancoComFeedback();
  try {
    await vagasAte(db, 4);
    await marcarComoEncerrada(db, 2, 1, { abriuAntes: false, horasAtras: 4 });
    await marcarComoEncerrada(db, 2, 2, { horasAtras: 3 });
    await marcarComoEncerrada(db, 2, 3, { horasAtras: 2 });
    await marcarComoEncerrada(db, 2, 4, { horasAtras: 1 });

    assert.deepEqual(await encerradas(db), ["adzuna:2:Estágio B", "adzuna:3:Estágio 3"]);

    await eventoDaVaga(db, { nome: "vaga_util", perfil: 2, vaga: 1, quando: "now()" });

    assert.deepEqual(await encerradas(db), [
      "adzuna:2:Estágio B",
      "adzuna:3:Estágio 3",
      "adzuna:4:Estágio 4",
    ]);
    assert.deepEqual(await queNaoVoltam(db, 2), ["2", "3", "4"]);
  } finally {
    await db.close();
  }
});

Deno.test("vaga marcada como encerrada não volta para quem marcou, mesmo sem efeito para os outros", async () => {
  const db = await bancoComFeedback();
  try {
    await vagasAte(db, 5);
    await db.exec("update perfis set ativo = false where id = 1;");
    for (const vaga of [1, 2, 3, 4]) {
      await marcarComoEncerrada(db, 1, vaga, { abriuAntes: false });
    }
    await recusa(db, 5, "motivo_repetida", "now() - interval '1 hour'");
    await marcarComoEncerrada(db, 2, 3);

    assert.deepEqual(await queNaoVoltam(db, 1), ["1", "2", "3", "4", "5"]);
    assert.deepEqual(await encerradas(db), ["adzuna:3:Estágio 3"]);
  } finally {
    await db.close();
  }
});
