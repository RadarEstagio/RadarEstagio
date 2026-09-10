import { assertEquals } from "jsr:@std/assert@1";
import {
  chatIdDaMensagem,
  conversaPrivada,
  extrairPedidoDeVinculo,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";

const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";

Deno.test("extrai token e chat_id de /start com token", () => {
  const pedido = extrairPedidoDeVinculo({
    message: { chat: { id: 123456 }, text: `/start ${TOKEN}` },
  });
  assertEquals(pedido, { chatId: "123456", token: TOKEN });
});

Deno.test("normaliza token em maiúsculas", () => {
  const pedido = extrairPedidoDeVinculo({
    message: { chat: { id: 1 }, text: `/start ${TOKEN.toUpperCase()}` },
  });
  assertEquals(pedido?.token, TOKEN);
});

Deno.test("ignora /start sem token", () => {
  assertEquals(
    extrairPedidoDeVinculo({ message: { chat: { id: 1 }, text: "/start" } }),
    null,
  );
});

Deno.test("ignora token que não é uuid", () => {
  assertEquals(
    extrairPedidoDeVinculo({
      message: { chat: { id: 1 }, text: "/start abc123" },
    }),
    null,
  );
});

Deno.test("ignora texto comum", () => {
  assertEquals(
    extrairPedidoDeVinculo({ message: { chat: { id: 1 }, text: "oi" } }),
    null,
  );
});

Deno.test("ignora atualização sem mensagem", () => {
  assertEquals(extrairPedidoDeVinculo({}), null);
  assertEquals(chatIdDaMensagem({}), null);
});

Deno.test("devolve chat_id como texto", () => {
  assertEquals(chatIdDaMensagem({ message: { chat: { id: 987 } } }), "987");
});

Deno.test("cada resultado do vínculo tem uma resposta própria", () => {
  const resultados: ResultadoDoVinculo[] = [
    "vinculado",
    "token_ja_usado",
    "chat_de_outra_conta",
    "chat_ja_vinculado",
  ];
  const respostas = resultados.map((resultado) =>
    RESPOSTAS_DO_VINCULO[resultado]
  );

  assertEquals(new Set(respostas).size, resultados.length);
  assertEquals(respostas.filter((resposta) => !resposta).length, 0);
});

Deno.test("chat de outra conta ensina como liberar o Telegram", () => {
  assertEquals(
    RESPOSTAS_DO_VINCULO.chat_de_outra_conta.includes("Desvincular o Telegram"),
    true,
  );
});

Deno.test("o link usado uma vez não promete vínculo", () => {
  assertEquals(
    RESPOSTAS_DO_VINCULO.token_ja_usado.includes("já foi usado"),
    true,
  );
});

Deno.test("mensagem de grupo não vincula o chat à conta", () => {
  const emGrupo = {
    message: {
      chat: { id: -100200300, type: "supergroup" },
      text: "/start 3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
    },
  };

  assertEquals(extrairPedidoDeVinculo(emGrupo), null);
  assertEquals(conversaPrivada(emGrupo), false);
});

Deno.test("conversa privada continua vinculando", () => {
  const privada = {
    message: {
      chat: { id: 123, type: "private" },
      text: "/start 3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
    },
  };

  assertEquals(conversaPrivada(privada), true);
  assertEquals(extrairPedidoDeVinculo(privada)?.chatId, "123");
});

Deno.test("payload sem tipo de chat é tratado como privado", () => {
  const semTipo = {
    message: { chat: { id: 5 }, text: "/start 3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d" },
  };

  assertEquals(extrairPedidoDeVinculo(semTipo)?.chatId, "5");
});
