const URL_DO_SUPABASE = "https://radar-teste.supabase.co";
const CHAVE_DA_SESSAO = "sb-radar-teste-auth-token";
const CABECALHOS_CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "*",
  "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
  "access-control-expose-headers": "*",
};

export const usuario = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "teste@example.com",
  aud: "authenticated",
  role: "authenticated",
};

export const perfilDeExemplo = {
  curso: "Ciência da Computação",
  periodo: 3,
  habilidades: ["Python", "SQL"],
  cidade: "Recife, PE",
  modalidade: "remoto",
  areas_de_interesse: [],
  telegram_chat_id: null,
  token_vinculo: "token-de-teste",
  ativo: true,
  motivo_pausa: null,
  excluida_em: null,
  aceita_emails: false,
  termos_aceitos_em: "2026-09-05T12:00:00Z",
  versao_dos_termos: "2026-09-05",
};

function parteDoToken(dados) {
  return Buffer.from(JSON.stringify(dados)).toString("base64url");
}

export function sessaoDeExemplo() {
  const agora = Math.floor(Date.now() / 1000);
  const cabecalho = parteDoToken({ alg: "HS256", typ: "JWT" });
  const conteudo = parteDoToken({ sub: usuario.id, email: usuario.email, role: "authenticated", exp: agora + 3600 });
  return {
    access_token: `${cabecalho}.${conteudo}.assinatura`,
    refresh_token: "renovacao-de-teste",
    token_type: "bearer",
    expires_in: 3600,
    expires_at: agora + 3600,
    user: usuario,
  };
}

function lerCorpo(pedido) {
  const texto = pedido.postData();
  if (!texto) return null;
  try {
    return JSON.parse(texto);
  } catch {
    return texto;
  }
}

function responderRpc(nome, corpo, banco, responder) {
  if (nome === "concluir_meu_cadastro") {
    banco.perfil = { ...perfilDeExemplo, ...corpo.cadastro.perfil };
    return responder.vazio();
  }
  if (nome === "excluir_minha_conta") {
    banco.perfil = { ...banco.perfil, excluida_em: new Date().toISOString() };
    return responder.json(banco.perfil.excluida_em);
  }
  if (nome === "cancelar_exclusao_da_minha_conta") {
    banco.perfil = { ...banco.perfil, excluida_em: null };
    return responder.vazio();
  }
  if (nome === "desvincular_meu_telegram") {
    banco.perfil = { ...banco.perfil, telegram_chat_id: null };
    return responder.vazio();
  }
  if (nome === "baixar_meus_dados") return responder.json({ perfil: banco.perfil });
  if (nome === "apagar_minha_conta_sem_perfil") return responder.vazio();
  return responder.json({ message: `rpc ${nome} não simulada` }, 404);
}

async function responderAoSupabase(route, banco, chamadas) {
  const pedido = route.request();
  if (pedido.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CABECALHOS_CORS });
  const endereco = new URL(pedido.url());
  const corpo = lerCorpo(pedido);
  chamadas.push({ metodo: pedido.method(), caminho: endereco.pathname, busca: endereco.search, corpo });
  const responder = {
    json: (dados, status = 200) =>
      route.fulfill({ status, headers: { ...CABECALHOS_CORS, "content-type": "application/json" }, body: JSON.stringify(dados) }),
    vazio: (status = 204) => route.fulfill({ status, headers: CABECALHOS_CORS, body: "" }),
  };
  const pedeUmaLinha = (pedido.headers().accept ?? "").includes("vnd.pgrst.object");
  const linhasDoPerfil = () => {
    if (pedeUmaLinha) return banco.perfil ? responder.json(banco.perfil) : responder.json({ message: "sem linha" }, 406);
    return responder.json(banco.perfil ? [banco.perfil] : []);
  };
  const caminho = endereco.pathname;

  if (caminho === "/auth/v1/token") return responder.json(sessaoDeExemplo());
  if (caminho === "/auth/v1/signup") return responder.json({ ...usuario, email: corpo?.email ?? usuario.email });
  if (caminho === "/auth/v1/logout") return responder.vazio();
  if (caminho === "/auth/v1/user") return responder.json(usuario);
  if (caminho === "/auth/v1/recover" || caminho === "/auth/v1/resend") return responder.json({});
  if (caminho === "/rest/v1/eventos_produto") return responder.vazio(201);
  if (caminho === "/rest/v1/perfis" && pedido.method() === "GET") return linhasDoPerfil();
  if (caminho === "/rest/v1/perfis" && pedido.method() === "PATCH") {
    banco.perfil = { ...banco.perfil, ...corpo };
    return linhasDoPerfil();
  }
  if (caminho.startsWith("/rest/v1/rpc/")) return responderRpc(caminho.slice("/rest/v1/rpc/".length), corpo, banco, responder);
  return responder.json({ message: `rota ${caminho} não simulada` }, 404);
}

export async function prepararSite(page, { comSessao = false, perfil = null } = {}) {
  const chamadas = [];
  const errosDaPagina = [];
  const banco = { perfil: perfil ? structuredClone(perfil) : null };
  page.on("pageerror", (erro) => errosDaPagina.push(erro.message));
  await page.route(/^https?:\/\/(?!localhost|127\.0\.0\.1)/, (route) => route.abort());
  await page.route("**/config.js", (route) =>
    route.fulfill({
      contentType: "application/javascript",
      body: `window.RADAR_CONFIG = ${JSON.stringify({
        supabaseUrl: URL_DO_SUPABASE,
        supabasePublishableKey: "chave-de-teste",
        telegramBot: "bot_de_teste",
        turnstileSiteKey: "",
      })};`,
    }),
  );
  await page.route(`${URL_DO_SUPABASE}/**`, (route) => responderAoSupabase(route, banco, chamadas));
  if (comSessao) {
    await page.addInitScript(
      ([chave, sessao]) => window.localStorage.setItem(chave, JSON.stringify(sessao)),
      [CHAVE_DA_SESSAO, sessaoDeExemplo()],
    );
  }
  return { chamadas, errosDaPagina, banco };
}
