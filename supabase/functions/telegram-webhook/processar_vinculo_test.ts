import { assertEquals } from "jsr:@std/assert@1";
import { type OperacoesDeVinculo, processarVinculo } from "./processar_vinculo.ts";
import { RESPOSTAS_DO_VINCULO, type ResultadoDoVinculo } from "./vinculo.ts";

const PEDIDO = { chatId: "123", token: "3f2504e0-4f89-11d3-9a0c-0305e82c3301" };
const FORA_DA_JANELA = new Date("2026-09-05T23:00:00Z");
const DENTRO_DA_JANELA = new Date("2026-09-05T09:30:00Z");

function operacoes(resultado: ResultadoDoVinculo) {
  const respostas: string[] = [];
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
    dispararEntregaImediata: async (perfilId) => {
      disparos.push(perfilId);
    },
  };
  return { api, respostas, disparos };
}

Deno.test("vínculo aceito responde e pede a entrega imediata do perfil", async () => {
  const { api, respostas, disparos } = operacoes("vinculado");
  await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
  assertEquals(respostas, [RESPOSTAS_DO_VINCULO.vinculado]);
  assertEquals(disparos, ["perfil"]);
});

Deno.test("vínculo recusado só responde", async () => {
  const recusas: ResultadoDoVinculo[] = [
    "token_ja_usado",
    "chat_de_outra_conta",
    "chat_ja_vinculado",
  ];
  for (const resultado of recusas) {
    const { api, respostas, disparos } = operacoes(resultado);
    await processarVinculo(PEDIDO, api, FORA_DA_JANELA);
    assertEquals(respostas, [RESPOSTAS_DO_VINCULO[resultado]]);
    assertEquals(disparos, []);
  }
});

Deno.test("vínculo aceito na janela do diário espera o diário", async () => {
  const { api, respostas, disparos } = operacoes("vinculado");
  await processarVinculo(PEDIDO, api, DENTRO_DA_JANELA);
  assertEquals(respostas, [RESPOSTAS_DO_VINCULO.vinculado]);
  assertEquals(disparos, []);
});
