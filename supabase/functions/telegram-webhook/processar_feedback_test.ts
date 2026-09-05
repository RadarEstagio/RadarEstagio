import { assertEquals, assertRejects } from "jsr:@std/assert@1";
import {
  type OperacoesDeFeedback,
  processarFeedback,
  responderConsultaDeFeedback,
} from "./processar_feedback.ts";

const consulta = {
  id: "callback",
  chatId: "123",
  mensagemId: 10,
  token: "token",
  acao: "feedback",
};
function operacoes(permitido = true) {
  const chamadas: string[] = [];
  const api: OperacoesDeFeedback = {
    envioDoToken: async (token, chat) => {
      assertEquals([token, chat], [consulta.token, consulta.chatId]);
      return permitido
        ? { perfilId: "p", userId: "u", vagaId: 1, titulo: "Vaga", empresa: "Empresa" }
        : null;
    },
    registrarFeedback: async (_, acao) => {
      chamadas.push(acao);
    },
    perguntarOMotivo: async () => {
      chamadas.push("abrir");
    },
    encerrarPergunta: async () => {
      chamadas.push("fechar");
    },
  };
  return { api, chamadas };
}

Deno.test("número abre feedback e resposta registra antes de fechar a pergunta", async () => {
  const { api, chamadas } = operacoes();
  await processarFeedback(consulta, api);
  assertEquals(chamadas, ["abrir"]);
  await processarFeedback({ ...consulta, acao: "util" }, api);
  assertEquals(chamadas, ["abrir", "util", "fechar"]);
});

Deno.test("conta ou chat reprovado não gera feedback nem mensagem", async () => {
  for (const acao of ["feedback", "recusa", "util", "motivo_nota"]) {
    const { api, chamadas } = operacoes(false);
    await processarFeedback({ ...consulta, acao }, api);
    assertEquals(chamadas, []);
  }
});

Deno.test("falha ao registrar mantém a pergunta para tentar novamente", async () => {
  const { api, chamadas } = operacoes();
  api.registrarFeedback = async () => {
    throw new Error("banco");
  };
  await assertRejects(() => processarFeedback({ ...consulta, acao: "motivo_nota" }, api));
  assertEquals(chamadas, []);
});

Deno.test("falhas cosméticas após gravar não solicitam reentrega do webhook", async () => {
  for (const falha of ["fechar", "confirmar", "ambas"]) {
    const { api, chamadas } = operacoes();
    api.encerrarPergunta = async () => {
      chamadas.push("fechar");
      if (falha !== "confirmar") throw new Error("message can't be deleted");
    };
    const resposta = await responderConsultaDeFeedback(
      { ...consulta, acao: "util" },
      api,
      async () => {
        chamadas.push("confirmar");
        if (falha !== "fechar") throw new Error("query is too old");
      },
    );
    assertEquals(resposta.status, 200);
    assertEquals(chamadas, ["util", "fechar", "confirmar"]);
  }
});

Deno.test("falha de persistência solicita retry sem fechar nem confirmar", async () => {
  const { api, chamadas } = operacoes();
  api.registrarFeedback = async () => {
    throw new Error("banco indisponível");
  };
  const resposta = await responderConsultaDeFeedback(
    { ...consulta, acao: "util" },
    api,
    async () => {
      chamadas.push("confirmar");
    },
  );
  assertEquals(resposta.status, 500);
  assertEquals(chamadas, []);
});
