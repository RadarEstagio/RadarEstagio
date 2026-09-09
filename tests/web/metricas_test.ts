import assert from "assert";
import { PGlite } from "pglite";

interface Metricas {
  etapas: Record<string, number>;
  vagas_abertas: number;
  vagas_uteis: number;
  vagas_irrelevantes: number;
  recomendacoes_elegiveis_feedback: number;
  recomendacoes_com_feedback: number;
  perfis_na_coorte: number;
  perfis_sem_entrega: number;
  mediana_segundos_ate_entrega: number | null;
  perfis_sem_abertura: number;
  mediana_segundos_ate_abertura: number | null;
  utilidade_semanal_fatos: {
    semana: string;
    parcial: boolean;
    perfil_id: number | string;
    curso: string;
    com_utilidade: boolean;
  }[];
  recusas_por_motivo: Record<string, number>;
  pausas_atuais: { motivo: string; total: number }[];
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
      create table perfis(id int primary key, user_id text, curso text, criado_em timestamptz, ativado_em timestamptz, telegram_chat_id text, ativo boolean default true, excluida_em timestamptz, motivo_pausa text);
      create table vagas(id int primary key, extracao jsonb, extraida_em timestamptz);
      create table envios(perfil_id int, vaga_id int, enviada_em timestamptz);
      create table eventos_produto(id serial, nome text, perfil_id int, vaga_id int, user_id text, sessao_id text, propriedades jsonb default '{}', ocorrido_em timestamptz);
      insert into perfis values
        (1,'dono','Computação','2026-09-03','2026-09-03','123',true,null,null),
        (2,'antigo','Direito','2026-08-01','2026-08-02',null,true,null,null),
        (10,'pausa-estagio','Computação','2020-01-01',null,null,false,null,'conseguiu_estagio'),
        (11,'pausa-busca','Computação','2020-01-01',null,null,false,null,'interrompeu_busca'),
        (12,'pausa-vagas','Computação','2020-01-01',null,null,false,null,'sem_vagas_uteis'),
        (13,'pausa-frequencia','Computação','2020-01-01',null,null,false,null,'frequencia'),
        (14,'pausa-outro','Computação','2020-01-01',null,null,false,null,'outro'),
        (15,'pausa-sem-motivo-a','Computação','2020-01-01',null,null,false,null,null),
        (16,'pausa-sem-motivo-b','Computação','2020-01-01',null,null,false,null,null),
        (17,'ativa-com-motivo','Computação','2020-01-01',null,null,true,null,'outro'),
        (18,'excluida','Computação','2020-01-01',null,null,false,'2026-09-01','outro');
      insert into vagas values (1,'{"habilidades_obrigatorias":["Python"]}','2026-09-03'), (2,'{"habilidades_obrigatorias":["Python","SQL","Git"]}','2026-09-03'), (3,null,null);
      insert into envios values (1,1,'2026-09-03'),(1,1,'2026-09-03 00:00:30'),(1,2,'2026-09-03'),(1,3,'2026-09-04'),(2,1,'2026-09-08');
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
        ('vaga_util',1,3,'2026-09-03','{}'),
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
    assert.deepEqual(result.pausas_atuais, [
      { motivo: "conseguiu_estagio", total: 1 },
      { motivo: "frequencia", total: 1 },
      { motivo: "interrompeu_busca", total: 1 },
      { motivo: "outro", total: 1 },
      { motivo: "sem_motivo", total: 2 },
      { motivo: "sem_vagas_uteis", total: 1 },
    ]);
    assert.equal(result.recomendacoes_elegiveis_feedback, 4);
    assert.equal(result.recomendacoes_com_feedback, 3);
    assert.equal(result.perfis_na_coorte, 1);
    assert.equal(result.perfis_sem_entrega, 0);
    assert.equal(result.mediana_segundos_ate_entrega, 0);
    assert.equal(result.perfis_sem_abertura, 0);
    assert.equal(result.mediana_segundos_ate_abertura, 86400);
    assert.equal(result.utilidade_semanal_fatos.length, 4);
    assert.equal(
      result.utilidade_semanal_fatos.filter((fato) => fato.curso === "Computação" && fato.com_utilidade).length,
      1,
    );
    assert.equal(
      result.utilidade_semanal_fatos.filter((fato) => fato.curso === "Direito" && fato.com_utilidade).length,
      1,
    );
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
    await db.exec("update perfis set ativo = true where id = 10");
    const resumed = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(resumed.pausas_atuais.reduce((total, pausa) => total + pausa.total, 0), 6);
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
    assert.equal(empty.recomendacoes_elegiveis_feedback, 0);
    assert.equal(empty.recomendacoes_com_feedback, 0);
    assert.equal(empty.perfis_na_coorte, 0);
    assert.equal(empty.perfis_sem_entrega, 0);
    assert.equal(empty.mediana_segundos_ate_entrega, null);
    assert.equal(empty.perfis_sem_abertura, 0);
    assert.equal(empty.mediana_segundos_ate_abertura, null);
    assert.deepEqual(empty.pausas_atuais, []);
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

Deno.test("medianas de entrega e abertura usam somente ocorrências observadas", async () => {
  const db = new PGlite();
  try {
    await db.exec(`
      create table perfis(id int primary key, user_id text, curso text, criado_em timestamptz, ativado_em timestamptz, telegram_chat_id text, ativo boolean default true, excluida_em timestamptz, motivo_pausa text);
      create table vagas(id int primary key, extracao jsonb, extraida_em timestamptz);
      create table envios(perfil_id int, vaga_id int, enviada_em timestamptz);
      create table eventos_produto(id serial, nome text, perfil_id int, vaga_id int, user_id text, sessao_id text, propriedades jsonb default '{}', ocorrido_em timestamptz);
      insert into perfis values
        (1,'a','Computação','2026-09-03 00:00Z',null,'1',true,null,null),
        (2,'b','Direito','2026-09-03 00:00Z',null,'2',true,null,null),
        (3,'c','Curso livre','2026-09-03 00:00Z',null,'3',true,null,null);
      insert into vagas values
        (1,'{"habilidades_obrigatorias":[]}','2026-09-03'),
        (2,'{"habilidades_obrigatorias":["Python"]}','2026-09-03');
      insert into envios values
        (1,1,'2026-09-03 00:01Z'),
        (1,1,'2026-09-03 00:02Z'),
        (2,2,'2026-09-03 00:03Z');
      insert into eventos_produto(nome,perfil_id,vaga_id,ocorrido_em) values
        ('vaga_aberta',1,1,'2026-09-03 00:00:30Z'),
        ('vaga_aberta',2,2,'2026-09-03 00:05Z'),
        ('vaga_aberta',1,1,'2026-09-05 00:05Z');
    `);
    const sql = (await Deno.readTextFile(
      new URL("../../radar/storage/metricas.sql", import.meta.url),
    ))
      .replaceAll("%(dias)s", "7").replaceAll(
        "now()",
        "timestamptz '2026-09-04 00:00Z'",
      );
    const result = (await db.query<Metricas>(sql)).rows[0];
    assert.equal(result.perfis_na_coorte, 3);
    assert.equal(result.perfis_sem_entrega, 1);
    assert.equal(result.mediana_segundos_ate_entrega, 120);
    assert.equal(result.perfis_sem_abertura, 2);
    assert.equal(result.mediana_segundos_ate_abertura, 300);
  } finally {
    await db.close();
  }
});
