import { expect, test } from "vitest";
import { $, abrirAplicacao, clicar, esperar, perfil, usuario } from "./ambiente.js";

const perfilVinculado = { ...perfil, telegram_chat_id: "123" };

function bancoQueRespeitaOAtivo(cliente, perfilNoBanco) {
  const from = cliente.from;
  cliente.from = (tabela) => {
    const antes = { ...perfilNoBanco };
    const consulta = from(tabela);
    let ativoExigido;
    consulta.eq = (coluna, valor) => {
      if (coluna === "ativo") ativoExigido = valor;
      return consulta;
    };
    const maybeSingle = consulta.maybeSingle;
    consulta.maybeSingle = async () => {
      if (ativoExigido === undefined || antes.ativo === ativoExigido) return maybeSingle();
      Object.assign(perfilNoBanco, antes);
      return { data: null };
    };
    return consulta;
  };
}

function falharLeiturasDoPerfil(cliente) {
  const from = cliente.from;
  cliente.from = (tabela) => {
    const consulta = from(tabela);
    const update = consulta.update;
    let atualizando = false;
    consulta.update = (args) => {
      atualizando = true;
      return update(args);
    };
    const maybeSingle = consulta.maybeSingle;
    consulta.maybeSingle = async () => {
      if (!atualizando) throw new TypeError("Failed to fetch");
      return maybeSingle();
    };
    return consulta;
  };
}

function bancoQueRecusaOUpdate(cliente) {
  const from = cliente.from;
  cliente.from = (tabela) => {
    const consulta = from(tabela);
    let atualizando = false;
    consulta.update = () => {
      atualizando = true;
      return consulta;
    };
    const maybeSingle = consulta.maybeSingle;
    consulta.maybeSingle = async () => (atualizando ? { data: null } : maybeSingle());
    return consulta;
  };
}

test("clicar em Pausar com a conta já pausada em outro lugar não retoma as entregas", async () => {
  const { calls, cliente, perfilNoBanco } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfilVinculado,
    url: "/?conta",
  });
  await esperar();
  bancoQueRespeitaOAtivo(cliente, perfilNoBanco);
  const botao = $("#toggle-deliveries");
  expect(botao.textContent).toBe("Pausar entregas");
  perfilNoBanco.ativo = false;
  perfilNoBanco.motivo_pausa = "outro";
  clicar(botao);
  await esperar();
  expect(calls.some(([nome, , dados]) => nome === "update" && dados.ativo === true)).toBe(false);
  expect(perfilNoBanco.ativo).toBe(false);
  expect(perfilNoBanco.motivo_pausa).toBe("outro");
  expect(botao.textContent).toBe("Retomar entregas");
  expect($("#account-delivery-title").textContent).toBe("Entregas pausadas");
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-notice").textContent).toMatch(/já tinham mudado/);
  expect($("#account-notice").textContent).toMatch(/Nada foi alterado/);
});

test("clicar em Retomar com a conta já reativada em outro lugar não pausa as entregas", async () => {
  const { calls, cliente, perfilNoBanco } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfilVinculado, ativo: false, motivo_pausa: "outro" },
    url: "/?conta",
  });
  await esperar();
  bancoQueRespeitaOAtivo(cliente, perfilNoBanco);
  const botao = $("#toggle-deliveries");
  expect(botao.textContent).toBe("Retomar entregas");
  perfilNoBanco.ativo = true;
  perfilNoBanco.motivo_pausa = null;
  clicar(botao);
  await esperar();
  expect(calls.some(([nome, , dados]) => nome === "update" && dados.ativo === false)).toBe(false);
  expect(perfilNoBanco.ativo).toBe(true);
  expect(botao.textContent).toBe("Pausar entregas");
  expect($("#account-delivery-title").textContent).toBe("Entregas ativas");
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-notice").textContent).toMatch(/já tinham mudado/);
});

test("pausa aplicada mostra a conta pausada e a pergunta mesmo se a leitura seguinte falharia", async () => {
  const { cliente, perfilNoBanco } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfilVinculado,
    url: "/?conta",
  });
  await esperar();
  falharLeiturasDoPerfil(cliente);
  const botao = $("#toggle-deliveries");
  clicar(botao);
  await esperar();
  expect(perfilNoBanco.ativo).toBe(false);
  expect($("#account-message").textContent).toBe("");
  expect(botao.textContent).toBe("Retomar entregas");
  expect($("#account-delivery-title").textContent).toBe("Entregas pausadas");
  expect($("#pause-reason").hidden).toBe(false);
});

test("pausar numa conta excluída em outro lugar mostra a exclusão sem o aviso das entregas", async () => {
  const { cliente, perfilNoBanco } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfilVinculado,
    url: "/?conta",
  });
  await esperar();
  bancoQueRecusaOUpdate(cliente);
  perfilNoBanco.excluida_em = new Date().toISOString();
  perfilNoBanco.telegram_chat_id = null;
  clicar("#toggle-deliveries");
  await esperar();
  expect($("#account-delivery-title").textContent).toBe("Exclusão agendada");
  expect($("#account-notice").textContent).toBe("");
  expect($("#pause-reason").hidden).toBe(true);
});
