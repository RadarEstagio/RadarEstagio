import { assertEquals } from "jsr:@std/assert@1";
import {
  type OperacoesDeMensagemLivre,
  processarMensagemLivre,
} from "./processar_mensagem_livre.ts";
import { CONTATO_DA_EQUIPE, RESPOSTA_SEM_TOKEN } from "./vinculo.ts";

const CONTA = "https://radarestagio.com/?conta";
const PERFIL = "6f1d2c3a-0b4e-4c5d-8e7f-1a2b3c4d5e6f";

function operacoes(
  {
    perfilId = PERFIL as string | null,
    encaminha = true as boolean | "falha",
    ativo = true,
    banco = "ok" as "ok" | "falha",
  } = {},
) {
  const respostas: string[] = [];
  const encaminhadas: string[] = [];
  const api: OperacoesDeMensagemLivre = {
    perfilDoChat: async (chatId) => {
      assertEquals(chatId, "123");
      if (banco === "falha") throw new Error("banco fora do ar");
      return perfilId === null ? null : { id: perfilId, ativo };
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

const SURROGATE_SOLTO = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/;

Deno.test("o texto encaminhado nunca passa de 4096 unidades UTF-16, com ou sem emoji", async () => {
  for (
    const texto of ["a".repeat(10000), "😀".repeat(5000), "a😀".repeat(4000), "é".repeat(5000)]
  ) {
    const { api, encaminhadas } = operacoes();

    await processarMensagemLivre({ chatId: "123", texto }, api, CONTA);

    assertEquals(encaminhadas[0].length <= 4096, true, `${encaminhadas[0].length} unidades`);
    assertEquals(SURROGATE_SOLTO.test(encaminhadas[0]), false);
  }
});

Deno.test("o corte usa o espaço que sobra depois do cabeçalho e termina em reticências", async () => {
  const { api, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: "a".repeat(10000) }, api, CONTA);

  assertEquals(encaminhadas[0].length, 4096);
  assertEquals(encaminhadas[0].endsWith("a…"), true);
});

Deno.test("texto que cabe inteiro no limite vai sem corte", async () => {
  const { api, encaminhadas } = operacoes();
  const cabecalho = `Mensagem de um usuário pelo bot (perfil ${PERFIL}):\n\n`;
  const texto = "a".repeat(4096 - cabecalho.length);

  await processarMensagemLivre({ chatId: "123", texto }, api, CONTA);

  assertEquals(encaminhadas[0], cabecalho + texto);
});

Deno.test("falha ao consultar o perfil ainda responde, com o contato, e nada é encaminhado", async () => {
  const { api, respostas, encaminhadas } = operacoes({ banco: "falha" });

  await processarMensagemLivre({ chatId: "123", texto: "oi" }, api, CONTA);

  assertEquals(encaminhadas, []);
  assertEquals(respostas.length, 1);
  assertEquals(respostas[0].includes(CONTATO_DA_EQUIPE), true);
  assertEquals(respostas[0].includes("a equipe lê todas"), false);
});

Deno.test("comando de quem está com as entregas pausadas diz que estão pausadas e como retomar", async () => {
  const { api, respostas, encaminhadas } = operacoes({ ativo: false });

  await processarMensagemLivre({ chatId: "123", texto: "/start" }, api, CONTA);

  assertEquals(encaminhadas, []);
  assertEquals(respostas.length, 1);
  assertEquals(respostas[0].includes("pausadas"), true);
  assertEquals(respostas[0].includes(CONTA), true);
  assertEquals(respostas[0].includes("elas chegam aqui"), false);
});

Deno.test("texto livre de quem está pausado segue indo para a equipe", async () => {
  const { api, respostas, encaminhadas } = operacoes({ ativo: false });

  await processarMensagemLivre({ chatId: "123", texto: "quero voltar" }, api, CONTA);

  assertEquals(encaminhadas.length, 1);
  assertEquals(respostas[0].includes("a equipe lê todas"), true);
});

Deno.test("texto só com espaços é tratado como mensagem sem texto", async () => {
  const { api, encaminhadas } = operacoes();

  await processarMensagemLivre({ chatId: "123", texto: "   \n " }, api, CONTA);

  assertEquals(encaminhadas, []);
});
