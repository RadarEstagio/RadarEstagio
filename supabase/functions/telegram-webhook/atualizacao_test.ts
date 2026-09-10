import { assertEquals } from "jsr:@std/assert@1";
import {
  cliqueQuePrecisaDeResposta,
  interpretarCorpo,
  responderCliqueSemTratamento,
} from "./atualizacao.ts";

Deno.test("corpo que não é JSON vira nulo em vez de derrubar a função", async () => {
  const requisicao = {
    json: () => Promise.reject(new SyntaxError("Unexpected token")),
  };

  assertEquals(await interpretarCorpo(requisicao), null);
});

Deno.test("corpo que não é objeto vira nulo", async () => {
  assertEquals(await interpretarCorpo({ json: () => Promise.resolve("texto") }), null);
  assertEquals(await interpretarCorpo({ json: () => Promise.resolve(null) }), null);
  assertEquals(await interpretarCorpo({ json: () => Promise.resolve([1, 2]) }), null);
});

Deno.test("corpo válido volta como objeto", async () => {
  const atualizacao = { message: { chat: { id: 1 }, text: "/start" } };

  assertEquals(await interpretarCorpo({ json: () => Promise.resolve(atualizacao) }), atualizacao);
});

Deno.test("clique fora do formato conhecido ainda precisa de resposta", () => {
  const atualizacao = { callback_query: { id: "42", data: "formato:antigo" } };

  assertEquals(cliqueQuePrecisaDeResposta(atualizacao), "42");
});

Deno.test("mensagem comum não pede resposta de clique", () => {
  assertEquals(cliqueQuePrecisaDeResposta({ message: { chat: { id: 1 } } }), null);
  assertEquals(cliqueQuePrecisaDeResposta({ callback_query: {} }), null);
});

Deno.test("Telegram recusando a resposta do clique não vira 500 nem reentrega", async () => {
  const resposta = await responderCliqueSemTratamento("42", () => {
    return Promise.reject(new Error("Telegram recusou answerCallbackQuery"));
  });

  assertEquals(resposta.status, 200);
});

Deno.test("clique sem tratamento é respondido com o próprio id", async () => {
  const respondidos: string[] = [];

  const resposta = await responderCliqueSemTratamento("42", (id) => {
    respondidos.push(id);
    return Promise.resolve();
  });

  assertEquals(resposta.status, 200);
  assertEquals(respondidos, ["42"]);
});
