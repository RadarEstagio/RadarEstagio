import { assertEquals, assertThrows } from "jsr:@std/assert@1";
import { type SupabaseClient } from "jsr:@supabase/supabase-js@2";
import { criarTratadorDoRedirecionador } from "./servidor.ts";

type Linha = Record<string, unknown>;

const LANDING = "https://radarestagio.com";
const ENDERECO = "https://projeto.supabase.co/functions/v1/ir";
const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
const URL_DA_VAGA = "https://vaga.example/1";

function consultaFalsa(
  envios: Linha[],
  aberturas: Linha[],
  tabela: string,
  operacao: "select" | "insert",
  valores: Linha | null,
) {
  const filtros: [string, unknown][] = [];
  function executar() {
    if (operacao === "insert") {
      aberturas.push({ ...valores });
      return { data: null, error: null };
    }
    const atendem = envios.filter((linha) =>
      filtros.every(([coluna, valor]) => (linha[coluna] ?? null) === valor)
    );
    assertEquals(tabela, "envios");
    return { data: atendem.length === 1 ? { ...atendem[0] } : null, error: null };
  }
  const consulta = {
    eq(coluna: string, valor: unknown) {
      filtros.push([coluna, valor]);
      return consulta;
    },
    maybeSingle() {
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

function servidor(envios: Linha[] = [], landing: string | null = LANDING) {
  const aberturas: Linha[] = [];
  const supabase = {
    from: (tabela: string) => ({
      select: () => consultaFalsa(envios, aberturas, tabela, "select", null),
      insert: (valores: Linha) => consultaFalsa(envios, aberturas, tabela, "insert", valores),
    }),
  } as unknown as SupabaseClient;
  const criar = () =>
    criarTratadorDoRedirecionador({
      supabase,
      ambiente: { get: () => landing ?? undefined },
    });
  return { criar, aberturas };
}

function envioDoDono(): Linha {
  return {
    token: TOKEN,
    perfil_id: "perfil-1",
    vaga_id: 1,
    vagas: { url: URL_DA_VAGA },
    perfis: {
      user_id: "dono",
      ativo: true,
      excluida_em: null,
      telegram_chat_id: "111",
    },
  };
}

function requisicao(metodo: string, consulta = `?t=${TOKEN}`) {
  return new Request(`${ENDERECO}${consulta}`, { method: metodo });
}

Deno.test("método diferente de GET e HEAD é recusado com 405", async () => {
  const { criar, aberturas } = servidor([envioDoDono()]);
  const tratar = criar();

  for (const metodo of ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"]) {
    const resposta = await tratar(requisicao(metodo));

    assertEquals([metodo, resposta.status], [metodo, 405]);
    assertEquals(resposta.headers.get("location"), null);
  }
  assertEquals(aberturas, []);
});

Deno.test("GET com token do envio registra a abertura e manda para a vaga", async () => {
  const { criar, aberturas } = servidor([envioDoDono()]);

  const resposta = await criar()(requisicao("GET"));

  assertEquals(resposta.status, 302);
  assertEquals(resposta.headers.get("location"), URL_DA_VAGA);
  assertEquals(aberturas.length, 1);
  assertEquals(aberturas[0].nome, "vaga_aberta");
});

Deno.test("HEAD manda para a vaga sem registrar abertura", async () => {
  const { criar, aberturas } = servidor([envioDoDono()]);

  const resposta = await criar()(requisicao("HEAD"));

  assertEquals(resposta.status, 302);
  assertEquals(resposta.headers.get("location"), URL_DA_VAGA);
  assertEquals(aberturas, []);
});

Deno.test("token ausente, malformado ou desconhecido vai para a landing", async () => {
  const consultas = ["", "?t=abc123", "?t=3f2504e0-4f89-11d3-9a0c-0305e82c3302"];
  for (const consulta of consultas) {
    const { criar, aberturas } = servidor([envioDoDono()]);

    const resposta = await criar()(requisicao("GET", consulta));

    assertEquals([consulta, resposta.headers.get("location")], [consulta, LANDING]);
    assertEquals(aberturas, []);
  }
});

Deno.test("sem URL_DA_LANDING a função não sobe", () => {
  const { criar } = servidor([], null);

  assertThrows(criar, Error, "URL_DA_LANDING");
});
