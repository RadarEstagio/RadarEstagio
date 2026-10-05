import { assertEquals } from "jsr:@std/assert@1";
import { type OperacoesDeVinculo, processarVinculo } from "./processar_vinculo.ts";
import {
  RESPOSTA_VINCULADO_COM_BUSCA,
  RESPOSTA_VINCULADO_NA_JANELA,
  RESPOSTA_VINCULADO_SEM_DISPARO,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";

const PEDIDO = { chatId: "123", token: "3f2504e0-4f89-11d3-9a0c-0305e82c3301" };
const FORA_DA_JANELA = new Date("2026-09-05T23:00:00Z");
const DENTRO_DA_JANELA = new Date("2026-09-05T09:30:00Z");

function operacoes(resultado: ResultadoDoVinculo, disparou = true) {
  const respostas: string[] = [];
  const reivindicacoes: string[] = [];
  const disparos: string[] = [];
  const api: OperacoesDeVinculo = {
    vincularChat: async (token, chatId) => {
      assertEquals([token, chatId], [PEDIDO.token, PEDIDO.chatId]);
      return { resultado, perfilId: resultado === "vinculado" ? "perfil" : null };
    },
    responder: async (chatId, texto) => {
      assertEquals(chatId, PEDIDO.chatId);
      respostas.push(texto);
    },
    reivindicarEntregaImediata: async (perfilId) => {
      reivindicacoes.push(perfilId);
      return true;
    },
    dispararEntregaImediata: async (perfilId) => {
      disparos.push(perfilId);
      return disparou;
    },
  };
  return { api, respostas, reivindicacoes, disparos };
}

function banco() {
  const perfil = {
    id: "perfil",
    token: PEDIDO.token,
    chatId: null as string | null,
    entregaImediataDisparadaEm: null as Date | null,
  };
  const respostas: string[] = [];
  const reivindicacoes: string[] = [];
  const disparos: string[] = [];
  const api: OperacoesDeVinculo = {
    vincularChat: async (token, chatId) => {
      if (token !== perfil.token) return { resultado: "token_ja_usado", perfilId: null };
      perfil.chatId = chatId;
      perfil.token = crypto.randomUUID();
      return { resultado: "vinculado", perfilId: perfil.id };
    },
    responder: async (_, texto) => {
      respostas.push(texto);
    },
    reivindicarEntregaImediata: async (perfilId) => {
      reivindicacoes.push(perfilId);
      if (perfilId !== perfil.id || perfil.entregaImediataDisparadaEm) return false;
      perfil.entregaImediataDisparadaEm = new Date();
      return true;
    },
    dispararEntregaImediata: async (perfilId) => {
      disparos.push(perfilId);
      return true;
    },
  };
  const tokenRelido = () => ({ chatId: PEDIDO.chatId, token: perfil.token });
  const desvincular = () => {
    perfil.chatId = null;
    perfil.token = crypto.randomUUID();
  };
  return { api, respostas, reivindicacoes, disparos, tokenRelido, desvincular };
}

Deno.test("vínculo aceito responde, reivindica e pede a entrega imediata do perfil", async () => {
  const { api, respostas, reivindicacoes, disparos } = operacoes("vinculado");
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  assertEquals(respostas, [RESPOSTA_VINCULADO_COM_BUSCA]);
  assertEquals(reivindicacoes, ["perfil"]);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("vínculo recusado só responde", async () => {
  const recusas: ResultadoDoVinculo[] = [
    "token_ja_usado",
    "chat_de_outra_conta",
    "chat_ja_vinculado",
  ];
  for (const resultado of recusas) {
    const { api, respostas, reivindicacoes, disparos } = operacoes(resultado);
    await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
    assertEquals(respostas, [RESPOSTAS_DO_VINCULO[resultado]]);
    assertEquals(reivindicacoes, []);
    assertEquals(disparos, []);
  }
});

Deno.test("primeiro vínculo dispara a entrega imediata uma vez", async () => {
  const { api, respostas, disparos } = banco();
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  assertEquals(respostas, [RESPOSTA_VINCULADO_COM_BUSCA]);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("/start repetido do mesmo chat com o token relido não dispara de novo", async () => {
  const { api, respostas, disparos, tokenRelido } = banco();
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  await processarVinculo(tokenRelido(), api, FORA_DA_JANELA);
  await processarVinculo(tokenRelido(), api, FORA_DA_JANELA);
  assertEquals(respostas, [
    RESPOSTA_VINCULADO_COM_BUSCA,
    RESPOSTAS_DO_VINCULO.vinculado,
    RESPOSTAS_DO_VINCULO.vinculado,
  ]);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("desvincular e vincular de novo não dispara de novo", async () => {
  const { api, respostas, disparos, tokenRelido, desvincular } = banco();
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  desvincular();
  await processarVinculo(tokenRelido(), api, FORA_DA_JANELA);
  assertEquals(respostas, [RESPOSTA_VINCULADO_COM_BUSCA, RESPOSTAS_DO_VINCULO.vinculado]);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("vínculo na janela do diário não reivindica nem dispara", async () => {
  const { api, respostas, reivindicacoes, disparos, tokenRelido } = banco();
  await processarVinculo(PEDIDO, api, DENTRO_DA_JANELA);
  assertEquals(respostas, [RESPOSTA_VINCULADO_NA_JANELA]);
  assertEquals(reivindicacoes, []);
  assertEquals(disparos, []);
  await processarVinculo(tokenRelido(), api, FORA_DA_JANELA);
  await processarVinculo(tokenRelido(), api, FORA_DA_JANELA);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("na janela do diário a resposta manda esperar a execução da manhã, não uma busca em instantes", () => {
  assertEquals(RESPOSTA_VINCULADO_NA_JANELA.includes("execução da manhã"), true);
  assertEquals(/instantes|agora|começou/.test(RESPOSTA_VINCULADO_NA_JANELA), false);
});

Deno.test("disparo que não saiu (sem token ou recusado) não promete busca em andamento", async () => {
  const { api, respostas, disparos } = operacoes("vinculado", false);
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  assertEquals(disparos, ["perfil"]);
  assertEquals(respostas, [RESPOSTA_VINCULADO_SEM_DISPARO]);
  assertEquals(/instantes|agora|começou/.test(RESPOSTA_VINCULADO_SEM_DISPARO), false);
  assertEquals(RESPOSTA_VINCULADO_SEM_DISPARO.includes("próxima execução"), true);
});

Deno.test("entrega imediata já reivindicada antes não promete nova busca", async () => {
  const { api, respostas, disparos } = operacoes("vinculado");
  api.reivindicarEntregaImediata = async () => false;
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  assertEquals(respostas, [RESPOSTAS_DO_VINCULO.vinculado]);
  assertEquals(disparos, []);
  assertEquals(/instantes|agora|começou/.test(RESPOSTAS_DO_VINCULO.vinculado), false);
});
