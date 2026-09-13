import { expect, test } from "vitest";
import {
  $,
  $$,
  abrirAplicacao,
  chamada,
  chamadas,
  clicar,
  dialogoAberto,
  esperar,
  perfil,
  usuario,
} from "./ambiente.js";

const perfilVinculado = { ...perfil, telegram_chat_id: "123" };

function abrirConta(perfilSalvo = perfilVinculado) {
  return abrirAplicacao({ sessao: { user: usuario }, perfilSalvo, url: "/?conta" });
}

test("preferência de e-mail pode ser revogada e falha preserva o valor anterior", async () => {
  const { calls, cliente } = abrirConta({ ...perfilVinculado, aceita_emails: true });
  await esperar();
  const caixa = $("#account-emails");
  expect(caixa.checked).toBe(true);
  clicar(caixa);
  await esperar();
  expect(chamada(calls, "update")[2]).toEqual({ aceita_emails: false });
  expect(caixa.checked).toBe(false);
  expect($("#account-notice").textContent).toBe("Preferência de e-mails atualizada.");
  cliente.from = () => {
    throw new Error("indisponível");
  };
  clicar(caixa);
  await esperar();
  expect(caixa.checked).toBe(false);
  expect(caixa.disabled).toBe(false);
});

test("conta sai do modal e mantém edição na página autenticada", async () => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado });
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  expect($("#landing-page").hidden).toBe(true);
  expect($("#account-page").hidden).toBe(false);
  expect(dialogoAberto()).toBe(false);
  expect(document.activeElement.id).toBe("account-title");
  expect(new URL(window.location.href).searchParams.has("conta")).toBe(true);
  expect(document.body.classList.contains("account-page-open")).toBe(true);
  expect(document.title).toBe("Minha conta — Radar de Estágio");
  clicar("#edit-profile");
  await esperar();
  expect($("#signup-form").hidden).toBe(false);
  expect($("#account-content #signup-form")).toBeTruthy();
  clicar("#back-to-site");
  await esperar();
  expect($("#landing-page").hidden).toBe(false);
  expect($("#account-page").hidden).toBe(true);
  expect(dialogoAberto()).toBe(false);
  expect($("#signup-dialog #signup-form")).toBeTruthy();
  expect(new URL(window.location.href).searchParams.has("conta")).toBe(false);
  expect(document.activeElement).toBe($(".js-open-signup"));
});

test("ações sensíveis ficam separadas e exigem confirmação", async () => {
  abrirConta();
  await esperar();
  expect($$(".account-danger-row")).toHaveLength(2);
  const confirmacao = $("#account-confirm");

  clicar("#unlink-telegram");
  expect(confirmacao.hidden).toBe(false);
  expect(confirmacao.dataset.acao).toBe("desvincular");
  expect($("#account-confirm-title").textContent).toBe("Desvincular o Telegram?");
  expect(document.activeElement.id).toBe("account-confirm-no");

  clicar("#account-confirm-no");
  expect(confirmacao.hidden).toBe(true);
  expect(document.activeElement.id).toBe("unlink-telegram");

  clicar("#delete-account");
  expect(confirmacao.hidden).toBe(false);
  expect(confirmacao.dataset.acao).toBe("excluir");
  expect($("#account-confirm-title").textContent).toBe("Excluir sua conta?");

  clicar("#account-confirm-close");
  expect(confirmacao.hidden).toBe(true);
  expect(document.activeElement.id).toBe("delete-account");
});

test("desvincular passa pela RPC e mostra de novo o vínculo do Telegram", async () => {
  const { calls, cliente } = abrirConta();
  await esperar();
  const rpc = cliente.rpc;
  cliente.rpc = async (nome, args) => {
    const resultado = await rpc(nome, args);
    cliente.from("perfis").update({ telegram_chat_id: null });
    return resultado;
  };
  clicar("#unlink-telegram");
  clicar("#account-confirm-yes");
  await esperar();
  expect(chamada(calls, "rpc")[1]).toBe("desvincular_meu_telegram");
  expect($("#success-state").hidden).toBe(false);
  expect($("#telegram-link").hidden).toBe(false);
});

test("excluir mantém a sessão, informa o prazo e permite cancelar pela RPC", async () => {
  const { calls, cliente } = abrirConta();
  await esperar();
  const rpc = cliente.rpc;
  cliente.rpc = async (nome, args) => {
    const resultado = await rpc(nome, args);
    if (nome === "excluir_minha_conta") {
      cliente.from("perfis").update({ excluida_em: "2026-09-13T12:00:00Z" });
      return { data: "2026-09-13T12:00:00Z" };
    }
    if (nome === "cancelar_exclusao_da_minha_conta") cliente.from("perfis").update({ excluida_em: null });
    return resultado;
  };
  clicar("#delete-account");
  clicar("#account-confirm-yes");
  await esperar();
  expect(chamadas(calls, "logout")).toHaveLength(0);
  expect($("#success-kicker").textContent).toBe("Exclusão agendada");
  expect($("#success-copy").textContent).toContain("12/11/2026");
  expect($("#success-copy").textContent).toContain("entre aqui de novo para cancelar");
  clicar("#success-account");
  await esperar();
  expect($("#cancel-deletion").hidden).toBe(false);
  expect($("#delete-account").hidden).toBe(true);
  expect($("#edit-profile").hidden).toBe(true);
  expect($("#account-emails").disabled).toBe(true);
  clicar("#cancel-deletion");
  await esperar();
  expect(chamadas(calls, "rpc").map(([, nome]) => nome)).toEqual([
    "excluir_minha_conta",
    "cancelar_exclusao_da_minha_conta",
  ]);
  expect($("#account-state").hidden).toBe(false);
  expect($("#cancel-deletion").hidden).toBe(true);
});

test("navegação da conta atualiza a seção ativa", async () => {
  abrirConta();
  await esperar();
  const visaoGeral = $('.account-nav a[href="#account-overview-panel"]');
  const entregas = $('.account-nav a[href="#account-delivery-panel"]');
  const privacidade = $('.account-nav a[href="#account-privacy-panel"]');

  expect(visaoGeral.getAttribute("aria-current")).toBe("location");
  clicar(entregas);
  await esperar();
  expect(visaoGeral.classList.contains("is-active")).toBe(false);
  expect(entregas.classList.contains("is-active")).toBe(true);
  expect(entregas.getAttribute("aria-current")).toBe("location");
  expect(window.location.hash).toBe("#account-delivery-panel");
  expect($("#account-overview-panel").hidden).toBe(true);
  expect($("#account-delivery-panel").hidden).toBe(false);
  expect($("#account-title").textContent).toBe("Entregas");

  clicar(privacidade);
  await esperar();
  expect(entregas.hasAttribute("aria-current")).toBe(false);
  expect(privacidade.classList.contains("is-active")).toBe(true);
  expect(window.location.hash).toBe("#account-privacy-panel");
  expect($("#account-delivery-panel").hidden).toBe(true);
  expect($("#account-privacy-panel").hidden).toBe(false);
  expect($("#account-title").textContent).toBe("Privacidade");
});

test("recarregar a conta restaura ativação e sair retorna ao site", async () => {
  abrirConta(perfil);
  await esperar();
  expect($("#account-page").hidden).toBe(false);
  expect($("#telegram-link").hidden).toBe(false);
  clicar("#success-account");
  await esperar();
  clicar("#logout-account");
  await esperar();
  expect($("#account-page").hidden).toBe(true);
  expect(dialogoAberto()).toBe(false);
  expect($("#landing-page").hidden).toBe(false);
  expect(localStorage.getItem("radar-tema")).toBeNull();
});

test("conta vinculada explica a espera sem afirmar que a busca rodou", async () => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado });
  await esperar();
  clicar('[data-event-origin="cabecalho"]');
  await esperar();
  const texto = $("#account-schedule").textContent;
  expect(texto).toContain("Telegram vinculado");
  expect(texto).toContain("quando houver vagas compatíveis");
  expect(texto).toContain("pode aguardar a próxima execução diária");
  expect(texto).not.toContain("busca iniciou");
  expect(texto).not.toContain("concluída");
});

test("pausar mantém a conta pausada e oferece motivo opcional", async () => {
  const { calls } = abrirConta();
  await esperar();
  clicar("#toggle-deliveries");
  await esperar();
  const atualizacao = chamada(calls, "update");
  expect(atualizacao[2].ativo).toBe(false);
  expect(atualizacao[2].motivo_pausa).toBeUndefined();
  expect($("#pause-reason").hidden).toBe(false);
  expect(document.activeElement.id).toBe("pause-reason-title");
  clicar("#skip-pause-reason");
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-schedule").textContent).toContain("pausadas");
});

test("resposta de motivo é separada e não altera ativo", async () => {
  const { calls } = abrirConta();
  await esperar();
  clicar("#toggle-deliveries");
  await esperar();
  clicar('input[name="motivo-pausa"][value="sem_vagas_uteis"]');
  clicar("#save-pause-reason");
  await esperar();
  const atualizacoes = chamadas(calls, "update");
  expect(atualizacoes).toHaveLength(2);
  expect(atualizacoes[1][2].motivo_pausa).toBe("sem_vagas_uteis");
  expect(atualizacoes[1][2].ativo).toBeUndefined();
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-notice").textContent).toMatch(/Motivo salvo/);
});

test("salvar motivo sem escolher pede a escolha sem gravar", async () => {
  const { calls } = abrirConta();
  await esperar();
  clicar("#toggle-deliveries");
  await esperar();
  clicar("#save-pause-reason");
  expect($("#pause-reason-message").textContent).toBe("Escolha um motivo ou clique em “Pular”.");
  expect(chamadas(calls, "update")).toHaveLength(1);
});

test("erro ou corrida ao salvar motivo mantém pausa e permite pular", async () => {
  const { cliente } = abrirConta();
  await esperar();
  const from = cliente.from;
  cliente.from = (tabela) => {
    const consulta = from(tabela);
    const update = consulta.update;
    consulta.update = (args) => {
      const encadeada = update(args);
      if ("motivo_pausa" in args) encadeada.maybeSingle = async () => ({ data: { ...perfil, ativo: true } });
      return encadeada;
    };
    return consulta;
  };
  clicar("#toggle-deliveries");
  await esperar();
  clicar('input[name="motivo-pausa"][value="outro"]');
  clicar("#save-pause-reason");
  await esperar();
  expect($("#pause-reason").hidden).toBe(false);
  expect($("#pause-reason-message").textContent).toMatch(/não está mais pausada/);
  clicar("#skip-pause-reason");
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-schedule").textContent).toContain("pausadas");
});

test("retomar limpa o motivo no mesmo update", async () => {
  const { calls } = abrirConta({ ...perfilVinculado, ativo: false, motivo_pausa: "outro" });
  await esperar();
  clicar("#toggle-deliveries");
  await esperar();
  const atualizacao = chamada(calls, "update");
  expect(atualizacao[2].ativo).toBe(true);
  expect(atualizacao[2].motivo_pausa).toBeNull();
  expect($("#pause-reason").hidden).toBe(true);
  expect($("#account-schedule").textContent).toContain("recomendações chegarão");
});

test("recarregar em ?conta abre a conta sem passar pelo modal", async () => {
  abrirConta();
  const dialogo = $("#signup-dialog");
  let chegouAAbrir = false;
  new MutationObserver((registros) => {
    if (registros.some((registro) => registro.oldValue === null)) chegouAAbrir = true;
  }).observe(dialogo, { attributes: true, attributeFilter: ["open"], attributeOldValue: true });
  await esperar();
  expect(chegouAAbrir).toBe(false);
  expect(dialogoAberto()).toBe(false);
  expect($("#account-page").hidden).toBe(false);
});

test("baixar dados usa a RPC, nomeia o arquivo e revoga o endereço temporário", async () => {
  const { calls } = abrirConta();
  await esperar();
  const criados = [];
  const revogados = [];
  URL.createObjectURL = () => {
    criados.push("blob:dados");
    return "blob:dados";
  };
  URL.revokeObjectURL = (url) => revogados.push(url);
  let baixado = null;
  const clique = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function registrarDownload() {
    baixado = this.download;
  };
  try {
    clicar("#download-data");
    await esperar(1100);
  } finally {
    HTMLAnchorElement.prototype.click = clique;
  }
  expect(chamada(calls, "rpc")[1]).toBe("baixar_meus_dados");
  expect(baixado).toBe("meus-dados-radar.json");
  expect(revogados).toEqual(criados);
  expect($("#account-notice").textContent).toBe("Seus dados foram preparados para download.");
});
