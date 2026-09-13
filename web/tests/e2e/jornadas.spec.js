import { expect, test } from "@playwright/test";
import { perfilDeExemplo, prepararSite, usuario } from "./supabase-falso.js";

const perfilVinculado = { ...perfilDeExemplo, telegram_chat_id: "123" };

function botaoContinuar(page) {
  return page.getByRole("button", { name: "Continuar", exact: true });
}

test("landing abre sem erro de script, registra a visita e mantém o tema escolhido", async ({ page }) => {
  const { chamadas, errosDaPagina } = await prepararSite(page);
  await page.goto("/");
  await expect(page.locator(".hero-title-primary")).toHaveText("Cansado de procurar estágio?");
  await expect
    .poll(() => chamadas.some(({ caminho, corpo }) => caminho === "/rest/v1/eventos_produto" && corpo?.nome === "landing_visualizada"))
    .toBe(true);
  await page.locator("#theme-toggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-tema", "escuro");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-tema", "escuro");
  await expect(page.locator("#theme-toggle")).toHaveAttribute("aria-pressed", "true");
  expect(errosDaPagina).toEqual([]);
});

test("visitante preenche o cadastro inteiro e chega à confirmação do e-mail", async ({ page }) => {
  const { chamadas, errosDaPagina } = await prepararSite(page);
  await page.goto("/");
  await page.locator('[data-event-origin="hero"]').click();
  await expect(page.locator("#signup-dialog")).toBeVisible();
  await expect(page.locator("#progress-label")).toHaveText("Etapa 1 de 4");

  await botaoContinuar(page).click();
  await expect(page.locator("#erro-do-campo")).toHaveText("Informe o nome do seu curso.");
  await page.getByLabel("Seu curso").fill("Ciência da Computação");
  await page.getByLabel("Período atual").selectOption("3");
  await botaoContinuar(page).click();

  await page.locator('#skill-picker [data-skill="Python"]').click();
  await botaoContinuar(page).click();

  await page.getByLabel("Cidade principal").fill("recife");
  await page.locator('#lista-de-cidades [data-cidade="Recife, PE"]').click();
  await expect(page.getByLabel("Cidade principal")).toHaveValue("Recife, PE");
  await page.getByLabel("Remoto").check();
  await botaoContinuar(page).click();

  await page.locator('#signup-form input[name="email"]').fill("pessoa@example.com");
  await page.locator("#signup-password").fill("uma-senha-forte");
  await page.locator('#signup-form input[name="aceitou_termos"]').check();
  await page.getByRole("button", { name: /Criar conta e continuar/ }).click();

  await expect(page.locator("#assistance-title")).toHaveText("Confirme seu e-mail");
  const cadastro = chamadas.find(({ caminho }) => caminho === "/auth/v1/signup");
  expect(cadastro.corpo.data.cadastro_radar.perfil).toMatchObject({
    curso: "Ciência da Computação",
    periodo: 3,
    habilidades: ["Python"],
    cidade: "Recife, PE",
    modalidade: "remoto",
  });
  expect(JSON.stringify(cadastro.corpo.data)).not.toContain("uma-senha-forte");
  expect(errosDaPagina).toEqual([]);
});

test("login pelo endereço da conta abre a conta vinculada", async ({ page }) => {
  const { chamadas, errosDaPagina } = await prepararSite(page, { perfil: perfilVinculado });
  await page.goto("/?conta");
  await expect(page.locator("#conta-titulo")).toHaveText("Entre na sua conta");
  await page.locator('#signup-form input[name="email"]').fill(usuario.email);
  await page.locator("#signup-password").fill("uma-senha-forte");
  await page.getByRole("button", { name: /Entrar e continuar/ }).click();
  await expect(page.locator("#account-title")).toHaveText("Conta");
  await expect(page.locator("#signup-dialog")).toBeHidden();
  expect(chamadas.some(({ caminho }) => caminho === "/auth/v1/token")).toBe(true);
  expect(errosDaPagina).toEqual([]);
});

test("conta vinculada pausa as entregas e fecha a confirmação de exclusão com Esc", async ({ page }) => {
  const { chamadas, errosDaPagina, banco } = await prepararSite(page, { comSessao: true, perfil: perfilVinculado });
  await page.goto("/?conta#account-delivery-panel");
  await expect(page.locator("#account-delivery-title")).toHaveText("Entregas ativas");
  await page.getByRole("button", { name: "Pausar entregas" }).click();
  await expect(page.locator("#pause-reason")).toBeVisible();
  expect(banco.perfil.ativo).toBe(false);
  await page.getByRole("button", { name: "Pular" }).click();
  await expect(page.locator("#account-delivery-title")).toHaveText("Entregas pausadas");

  await page.goto("/?conta#account-privacy-panel");
  const excluir = page.locator("#delete-account");
  await excluir.click();
  await expect(page.locator("#account-confirm")).toBeVisible();
  await expect(page.locator("#account-confirm-title")).toHaveText("Excluir sua conta?");
  await expect(page.locator("#account-confirm-no")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("#account-confirm")).toBeHidden();
  await expect(excluir).toBeFocused();
  expect(chamadas.some(({ caminho }) => caminho === "/rest/v1/rpc/excluir_minha_conta")).toBe(false);
  expect(errosDaPagina).toEqual([]);
});
