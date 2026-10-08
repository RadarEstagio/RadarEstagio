import { assertEquals } from "jsr:@std/assert@1";
import { type SupabaseClient } from "jsr:@supabase/supabase-js@2";
import { CABECALHO_DO_SEGREDO, criarTratadorDoWebhook } from "./servidor.ts";
import {
  RESPOSTA_CHAT_JA_VINCULADO,
  RESPOSTA_TOKEN_JA_USADO,
  RESPOSTA_VINCULADO,
  RESPOSTA_VINCULADO_COM_BUSCA,
} from "./vinculo.ts";
import { AVISO_DE_CONSULTA_DESCONHECIDA, AVISO_DE_RECUSA_REGISTRADA } from "./feedback.ts";

type Linha = Record<string, unknown>;
type Tabelas = Record<string, Linha[]>;

const SEGREDO = "segredo-do-webhook";
const ENDERECO = "https://projeto.supabase.co/functions/v1/telegram-webhook";
const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
const CHAT_DO_DONO = "111";
const CHAT_ALHEIO = "222";
const FORA_DA_JANELA = new Date("2026-10-08T23:00:00Z");

function consultaFalsa(
  tabelas: Tabelas,
  tabela: string,
  operacao: "select" | "update" | "insert",
  valores: Linha | null,
) {
  const filtros: [string, unknown][] = [];
  let unica = false;
  function executar() {
    const linhas = tabelas[tabela] ?? (tabelas[tabela] = []);
    if (operacao === "insert") {
      linhas.push({ ...valores });
      return { data: null, error: null };
    }
    const atendem = linhas.filter((linha) =>
      filtros.every(([coluna, valor]) => (linha[coluna] ?? null) === valor)
    );
    if (operacao === "update") {
      for (const linha of atendem) Object.assign(linha, valores);
    }
    if (unica) {
      if (atendem.length > 1) {
        return { data: null, error: { code: "PGRST116", message: "mais de uma linha" } };
      }
      return { data: atendem.length === 1 ? { ...atendem[0] } : null, error: null };
    }
    return { data: atendem.map((linha) => ({ ...linha })), error: null };
  }
  const consulta = {
    eq(coluna: string, valor: unknown) {
      filtros.push([coluna, valor]);
      return consulta;
    },
    is(coluna: string, valor: unknown) {
      filtros.push([coluna, valor]);
      return consulta;
    },
    select() {
      return consulta;
    },
    maybeSingle() {
      unica = true;
      return consulta;
    },
    then(
      resolver: (resultado: unknown) => unknown,
      rejeitar?: (erro: unknown) => unknown,
    ) {
      return Promise.resolve().then(executar).then(resolver, rejeitar);
    },
  };
  return consulta;
}

function bancoFalso(tabelas: Tabelas): SupabaseClient {
  return {
    from: (tabela: string) => ({
      select: () => consultaFalsa(tabelas, tabela, "select", null),
      update: (valores: Linha) => consultaFalsa(tabelas, tabela, "update", valores),
      insert: (valores: Linha) => consultaFalsa(tabelas, tabela, "insert", valores),
    }),
  } as unknown as SupabaseClient;
}

function servidor(tabelas: Tabelas = {}) {
  const chamadas: { metodo: string; corpo: Linha }[] = [];
  const disparos: string[] = [];
  const variaveis: Record<string, string> = {
    TELEGRAM_BOT_TOKEN: "token-do-bot",
    TELEGRAM_WEBHOOK_SECRET: SEGREDO,
    TELEGRAM_CHAT_ID: "chat-de-operacao",
    URL_DA_LANDING: "https://radarestagio.com",
  };
  const enviar = ((entrada: string, opcoes: { body?: string }) => {
    chamadas.push({
      metodo: entrada.slice(entrada.lastIndexOf("/") + 1),
      corpo: JSON.parse(opcoes.body ?? "{}"),
    });
    return Promise.resolve(
      new Response(JSON.stringify({ ok: true }), {
        headers: { "content-type": "application/json" },
      }),
    );
  }) as unknown as typeof fetch;
  const tratar = criarTratadorDoWebhook({
    supabase: bancoFalso(tabelas),
    ambiente: { get: (nome: string) => variaveis[nome] },
    agora: () => FORA_DA_JANELA,
    enviar,
    dispararEntregaImediata: (perfilId: string) => {
      disparos.push(perfilId);
      return Promise.resolve(true);
    },
  });
  return { tratar, tabelas, chamadas, disparos };
}

function requisicao(
  corpo: unknown,
  opcoes: { metodo?: string; segredo?: string | null } = {},
) {
  const metodo = opcoes.metodo ?? "POST";
  const cabecalhos = new Headers({ "content-type": "application/json" });
  const segredo = opcoes.segredo === undefined ? SEGREDO : opcoes.segredo;
  if (segredo !== null) cabecalhos.set(CABECALHO_DO_SEGREDO, segredo);
  return new Request(ENDERECO, {
    method: metodo,
    headers: cabecalhos,
    body: metodo === "POST" ? JSON.stringify(corpo) : undefined,
  });
}

function inicio(chatId: string, token = TOKEN) {
  return { message: { chat: { id: Number(chatId), type: "private" }, text: `/start ${token}` } };
}

function clique(chatId: string, acao: string, token = TOKEN) {
  return {
    callback_query: {
      id: "clique-1",
      data: `${acao}:${token}`,
      message: { message_id: 7, chat: { id: Number(chatId) } },
    },
  };
}

function perfilPendente(ajustes: Linha = {}): Linha {
  return {
    id: "perfil-1",
    token_vinculo: TOKEN,
    telegram_chat_id: null,
    excluida_em: null,
    entrega_imediata_disparada_em: null,
    ativo: true,
    atualizado_em: null,
    ...ajustes,
  };
}

function envioDoDono(ajustes: Linha = {}): Linha {
  return {
    token: TOKEN,
    perfil_id: "perfil-1",
    vaga_id: 1,
    vagas: { titulo: "Estágio em dados", empresa: "Empresa" },
    perfis: {
      user_id: "dono",
      ativo: true,
      excluida_em: null,
      telegram_chat_id: CHAT_DO_DONO,
      ...ajustes,
    },
  };
}

function respostas(chamadas: { metodo: string; corpo: Linha }[]) {
  return chamadas.filter((chamada) => chamada.metodo === "sendMessage").map((chamada) =>
    chamada.corpo.text
  );
}

Deno.test("requisição sem o cabeçalho do segredo é recusada com 401 e nada é tocado", async () => {
  const { tratar, tabelas, chamadas } = servidor({ perfis: [perfilPendente()] });

  const resposta = await tratar(requisicao(inicio(CHAT_DO_DONO), { segredo: null }));

  assertEquals(resposta.status, 401);
  assertEquals(chamadas, []);
  assertEquals(tabelas.perfis[0].telegram_chat_id, null);
});

Deno.test("segredo diferente do configurado é recusado com 401", async () => {
  const { tratar, chamadas } = servidor({ perfis: [perfilPendente()] });

  const resposta = await tratar(requisicao(inicio(CHAT_DO_DONO), { segredo: "outro" }));

  assertEquals(resposta.status, 401);
  assertEquals(chamadas, []);
});

Deno.test("segredo igual ao configurado é aceito e trata a atualização", async () => {
  const { tratar, chamadas } = servidor({ perfis: [perfilPendente()] });

  const resposta = await tratar(requisicao(inicio(CHAT_DO_DONO)));

  assertEquals(resposta.status, 200);
  assertEquals(respostas(chamadas), [RESPOSTA_VINCULADO_COM_BUSCA]);
});

Deno.test("método diferente de POST é recusado com 405 mesmo com o segredo certo", async () => {
  for (const metodo of ["GET", "HEAD", "PUT", "DELETE", "OPTIONS"]) {
    const { tratar, chamadas } = servidor({ perfis: [perfilPendente()] });

    const resposta = await tratar(requisicao(null, { metodo }));

    assertEquals([metodo, resposta.status], [metodo, 405]);
    assertEquals(chamadas, []);
  }
});

Deno.test("o vínculo rotaciona o token, então o link vazado não vincula outro chat", async () => {
  const { tratar, tabelas, chamadas } = servidor({ perfis: [perfilPendente()] });

  await tratar(requisicao(inicio(CHAT_DO_DONO)));
  await tratar(requisicao(inicio(CHAT_ALHEIO)));

  assertEquals(tabelas.perfis[0].telegram_chat_id, CHAT_DO_DONO);
  assertEquals(tabelas.perfis[0].token_vinculo === TOKEN, false);
  assertEquals(respostas(chamadas), [RESPOSTA_VINCULADO_COM_BUSCA, RESPOSTA_TOKEN_JA_USADO]);
});

Deno.test("o mesmo chat com o token relido ouve que já está vinculado", async () => {
  const { tratar, chamadas } = servidor({ perfis: [perfilPendente()] });

  await tratar(requisicao(inicio(CHAT_DO_DONO)));
  await tratar(requisicao(inicio(CHAT_DO_DONO)));

  assertEquals(respostas(chamadas), [RESPOSTA_VINCULADO_COM_BUSCA, RESPOSTA_CHAT_JA_VINCULADO]);
});

Deno.test("conta marcada para exclusão não recebe o chat nem com o token válido", async () => {
  const excluida = perfilPendente({ excluida_em: "2026-10-01T00:00:00Z" });
  const { tratar, tabelas, chamadas } = servidor({ perfis: [excluida] });

  await tratar(requisicao(inicio(CHAT_DO_DONO)));

  assertEquals(tabelas.perfis[0].telegram_chat_id, null);
  assertEquals(tabelas.perfis[0].token_vinculo, TOKEN);
  assertEquals(respostas(chamadas), [RESPOSTA_TOKEN_JA_USADO]);
});

Deno.test("perfil com disparo anterior não reivindica a entrega imediata de novo", async () => {
  const jaDisparado = perfilPendente({
    entrega_imediata_disparada_em: "2026-10-07T12:00:00Z",
  });
  const { tratar, chamadas, disparos } = servidor({ perfis: [jaDisparado] });

  await tratar(requisicao(inicio(CHAT_DO_DONO)));

  assertEquals(disparos, []);
  assertEquals(respostas(chamadas), [RESPOSTA_VINCULADO]);
});

Deno.test("primeiro vínculo reivindica a entrega imediata e marca a hora do disparo", async () => {
  const { tratar, tabelas, disparos } = servidor({ perfis: [perfilPendente()] });

  await tratar(requisicao(inicio(CHAT_DO_DONO)));

  assertEquals(disparos, ["perfil-1"]);
  assertEquals(
    tabelas.perfis[0].entrega_imediata_disparada_em,
    FORA_DA_JANELA.toISOString(),
  );
});

Deno.test("chat alheio não vota no envio de outra pessoa", async () => {
  const { tratar, tabelas, chamadas } = servidor({ envios: [envioDoDono()] });

  const resposta = await tratar(requisicao(clique(CHAT_ALHEIO, "util")));

  assertEquals(resposta.status, 200);
  assertEquals(tabelas.eventos_produto ?? [], []);
  assertEquals(chamadas, [
    {
      metodo: "answerCallbackQuery",
      corpo: { callback_query_id: "clique-1", text: AVISO_DE_CONSULTA_DESCONHECIDA },
    },
  ]);
});

Deno.test("o dono do envio vota e o feedback é gravado", async () => {
  const { tratar, tabelas, chamadas } = servidor({ envios: [envioDoDono()] });

  await tratar(requisicao(clique(CHAT_DO_DONO, "util")));

  assertEquals(tabelas.eventos_produto.length, 1);
  assertEquals(tabelas.eventos_produto[0].nome, "vaga_util");
  assertEquals(tabelas.eventos_produto[0].perfil_id, "perfil-1");
  assertEquals(
    chamadas.at(-1),
    {
      metodo: "answerCallbackQuery",
      corpo: { callback_query_id: "clique-1", text: AVISO_DE_RECUSA_REGISTRADA },
    },
  );
});

Deno.test("conta pausada ou desvinculada não vota nem com o chat do envio", async () => {
  for (const ajuste of [{ ativo: false }, { telegram_chat_id: null }]) {
    const { tratar, tabelas } = servidor({ envios: [envioDoDono(ajuste)] });

    await tratar(requisicao(clique(CHAT_DO_DONO, "util")));

    assertEquals(tabelas.eventos_produto ?? [], []);
  }
});
