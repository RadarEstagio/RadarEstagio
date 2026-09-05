import assert from "assert";
import { PGlite } from "pglite";

interface Metricas {
  etapas: Record<string, number>;
  vagas_abertas: number;
  vagas_uteis: number;
  vagas_irrelevantes: number;
  recusas_por_motivo: Record<string, number>;
  utilidade_semanal: {
    semana: string;
    parcial: boolean;
    ativados: number;
    com_utilidade: number;
  }[];
  recusas_por_grupo: { grupo: string; entregas: number; recusas: number }[];
}

Deno.test("métricas deduplicam sinais, incluem abandono e medem semanas e denominadores", async () => {
  const db = new PGlite();
  try {
    await db.exec(`
      create table perfis(id int primary key, user_id text, criado_em timestamptz, ativado_em timestamptz, telegram_chat_id text);
      create table vagas(id int primary key, extracao jsonb, extraida_em timestamptz);
      create table envios(perfil_id int, vaga_id int, enviada_em timestamptz);
      create table eventos_produto(id serial, nome text, perfil_id int, vaga_id int, user_id text, sessao_id text, propriedades jsonb default '{}', ocorrido_em timestamptz);
      insert into perfis values (1,'dono','2026-09-03','2026-09-03','123'), (2,'antigo','2026-08-01','2026-08-02',null);
      insert into vagas values (1,'{"habilidades_obrigatorias":["Python"]}','2026-09-03'), (2,'{"habilidades_obrigatorias":["Python","SQL","Git"]}','2026-09-03'), (3,null,null);
      insert into envios values (1,1,'2026-09-03'),(1,2,'2026-09-03'),(1,3,'2026-09-04'),(2,1,'2026-09-08');
      insert into eventos_produto(nome,user_id,sessao_id,ocorrido_em) values
        ('conta_criada','antigo',null,'2026-08-01'),
        ('landing_visualizada',null,'s1','2026-09-03'),
        ('conta_criada','dono','s1','2026-09-03 01:00Z'),
        ('email_confirmado','dono','s1','2026-09-03 02:00Z'),
        ('landing_visualizada',null,'abandono','2026-09-04'),
        ('conta_criada','sem-confirmacao',null,'2026-09-04');
      insert into eventos_produto(nome,perfil_id,vaga_id,ocorrido_em,propriedades) values
        ('vaga_aberta',1,1,'2026-09-04','{}'),('vaga_aberta',1,1,'2026-09-04','{}'),
        ('vaga_util',1,1,'2026-09-04','{}'),('vaga_util',1,1,'2026-09-04','{}'),
        ('candidatura_iniciada',1,1,'2026-09-04','{}'),
        ('vaga_util',1,2,'2026-09-05','{}'),
        ('vaga_irrelevante',1,2,'2026-09-06','{"motivo":"motivo_nota"}'),
        ('vaga_irrelevante',1,2,'2026-09-06','{"motivo":"motivo_nota"}'),
        ('vaga_util',2,1,'2026-09-08','{}'),
        ('vaga_util',1,3,'2026-09-10','{}');
    `);
    const sql = (await Deno.readTextFile(
      new URL("../../radar/storage/metricas.sql", import.meta.url),
    ))
      .replaceAll("%(dias)s", "7").replaceAll(
        "now()",
        "timestamptz '2026-09-09 12:00Z'",
      );
    const result = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(result.etapas.landing_visualizada, 2);
    assert.equal(result.etapas.conta_criada, 2);
    assert.equal(result.etapas.email_confirmado, 1);
    assert.equal(result.vagas_abertas, 1);
    assert.equal(result.vagas_uteis, 1);
    assert.equal(result.vagas_irrelevantes, 1);
    assert.equal(result.recusas_por_motivo.motivo_nota, 1);
    assert.deepEqual(result.utilidade_semanal, [
      { semana: "2026-08-31", parcial: false, ativados: 2, com_utilidade: 1 },
      { semana: "2026-09-07", parcial: true, ativados: 2, com_utilidade: 1 },
    ]);
    assert.deepEqual(result.recusas_por_grupo, [
      { grupo: "sem_extracao", entregas: 1, recusas: 0, recusas_da_nota: 0 },
      { grupo: "tres_ou_mais", entregas: 1, recusas: 1, recusas_da_nota: 1 },
      { grupo: "uma_ou_duas", entregas: 2, recusas: 0, recusas_da_nota: 0 },
    ]);
    await db.exec(
      `insert into eventos_produto(nome,perfil_id,vaga_id,ocorrido_em) values ('vaga_irrelevante',2,1,'2026-09-09');`,
    );
    const changed = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(changed.utilidade_semanal[1].com_utilidade, 0);
    assert.equal(changed.utilidade_semanal[0].com_utilidade, 1);
    await db.exec(
      `update envios set enviada_em = '2026-09-06' where perfil_id = 2; insert into eventos_produto(nome,perfil_id,vaga_id,ocorrido_em) values ('vaga_util',2,1,'2026-09-07 02:00Z');`,
    );
    const limite = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(limite.utilidade_semanal[0].com_utilidade, 2);
    assert.equal(limite.utilidade_semanal[1].com_utilidade, 0);
    await db.exec("truncate eventos_produto, envios, perfis, vagas");
    const empty = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(empty.vagas_uteis, 0);
    await db.exec(
      `insert into eventos_produto(nome,user_id,sessao_id,ocorrido_em) values
      ('landing_visualizada',null,'compartilhada','2026-08-01'),
      ('conta_criada','a','compartilhada','2026-09-04'),
      ('conta_criada','b','compartilhada','2026-09-05');`,
    );
    const compartilhada = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(compartilhada.etapas.conta_criada, 2);
    assert.equal(compartilhada.etapas.landing_visualizada, undefined);

    assert.ok(
      empty.utilidade_semanal.every((s) =>
        s.ativados === 0 && s.com_utilidade === 0
      ),
    );
  } finally {
    await db.close();
  }
});
