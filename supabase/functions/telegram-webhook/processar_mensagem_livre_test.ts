import { assertEquals } from "jsr:@std/assert@1";
import {
  type OperacoesDeMensagemLivre,
  processarMensagemLivre,
  TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO,
} from "./processar_mensagem_livre.ts";
import { CONTATO_DA_EQUIPE, RESPOSTA_SEM_TOKEN } from "./vinculo.ts";

const CONTA = "https://radarestagio.com/?conta";
const PERFIL = "6f1d2c3a-0b4e-4c5d-8e7f-1a2b3c4d5e6f";

function operacoes(
  { perfilId = PERFIL as string | null, encaminha = true as boolean | "falha" } = {},
) {
  const respostas: string[] = [];
  const encaminhadas: string[] = [];
  const api: OperacoesDeMensagemLivre = {
    perfilDoChat: async (chatId) => {
      assertEquals(chatId, "123");
      return perfilId;
    },
    responder: async (chatId, texto) => {
      assertEquals(chatId, "123");
      respostas.push(texto);
    },
    encaminharParaOperacao: async (texto) => {
      if (encaminha === "falha") throw new Error("telegram fora do ar");
      encaminhadas.push(texto);
      return encaminha;
    },
  };
  return { api, respostas, encaminhadas };
}

Deno.test("chat vinculado recebe o aviso da equipe e o texto vai ao chat de operação", async () => {
  const { api, respostas, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: "como pauso?" }, api, CONTA);

  assertEquals(respostas.length, 1);
  assertEquals(respostas[0].includes("Recebemos sua mensagem; a equipe lê todas"), true);
  assertEquals(respostas[0].includes(CONTATO_DA_EQUIPE), true);
  assertEquals(respostas[0].includes(CONTA), true);
  assertEquals(encaminhadas.length, 1);
  assertEquals(encaminhadas[0].includes("como pauso?"), true);
  assertEquals(encaminhadas[0].includes(PERFIL), true);
});

Deno.test("chat não vinculado continua recebendo a instrução de vínculo e nada é encaminhado", async () => {
  const { api, respostas, encaminhadas } = operacoes({ perfilId: null });

  await processarMensagemLivre({ chatId: "123", texto: "oi" }, api, CONTA);

  assertEquals(respostas, [RESPOSTA_SEM_TOKEN]);
  assertEquals(encaminhadas, []);
});

Deno.test("a resposta só promete leitura da equipe quando o encaminhamento aconteceu", async () => {
  for (const encaminha of [false, "falha"] as const) {
    const { api, respostas } = operacoes({ encaminha });

    await processarMensagemLivre({ chatId: "123", texto: "oi" }, api, CONTA);

    assertEquals(respostas.length, 1);
    assertEquals(respostas[0].includes("a equipe lê todas"), false);
    assertEquals(respostas[0].includes(CONTATO_DA_EQUIPE), true);
  }
});

Deno.test("mensagem sem texto não é encaminhada e a resposta aponta o contato", async () => {
  const { api, respostas, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: null }, api, CONTA);

  assertEquals(encaminhadas, []);
  assertEquals(respostas.length, 1);
  assertEquals(respostas[0].includes("texto"), true);
  assertEquals(respostas[0].includes(CONTATO_DA_EQUIPE), true);
});

Deno.test("comando solto de chat vinculado não vai para a equipe", async () => {
  for (const comando of ["/start", "/ajuda", "  /start "]) {
    const { api, respostas, encaminhadas } = operacoes();

    await processarMensagemLivre({ chatId: "123", texto: comando }, api, CONTA);

    assertEquals(encaminhadas, []);
    assertEquals(respostas.length, 1);
    assertEquals(respostas[0].includes("já está vinculado"), true);
  }
});

Deno.test("texto longo é cortado antes de ir ao chat de operação", async () => {
  const { api, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: "a".repeat(10000) }, api, CONTA);

  assertEquals(encaminhadas[0].length < 4096, true);
  assertEquals(encaminhadas[0].includes("a".repeat(TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO)), true);
  assertEquals(
    encaminhadas[0].includes("a".repeat(TAMANHO_MAXIMO_DO_TEXTO_ENCAMINHADO + 1)),
    false,
  );
});

Deno.test("texto só com espaços é tratado como mensagem sem texto", async () => {
  const { api, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: "   \n " }, api, CONTA);

  assertEquals(encaminhadas, []);
});
