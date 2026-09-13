import assert from "assert";
import { JSDOM, VirtualConsole } from "jsdom";

const html = await Deno.readTextFile(
  new URL("../../web/index.html", import.meta.url),
);
const script = await Deno.readTextFile(
  new URL("../../web/assets/app.js", import.meta.url),
);
const areasJson = JSON.parse(
  await Deno.readTextFile(new URL("../../web/assets/areas.json", import.meta.url)),
);
const cidadesJson = JSON.parse(
  await Deno.readTextFile(new URL("../../web/assets/cidades.json", import.meta.url)),
);
const catalogos: Record<string, unknown> = {
  "assets/areas.json": areasJson,
  "assets/cidades.json": cidadesJson,
};
const user = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "teste@example.com",
};
const profile = {
  curso: "Computação",
  periodo: 3,
  habilidades: ["Python"],
  cidade: "Recife, PE",
  modalidade: "remoto",
  areas_de_interesse: [],
  token_vinculo: "token",
  ativo: true,
  motivo_pausa: null as string | null,
  aceita_emails: false,
  telegram_chat_id: null,
};

type Session = { user: typeof user };
type Profile = Omit<typeof profile, "telegram_chat_id"> & {
  telegram_chat_id: string | null;
};
type Payload = Record<string, unknown>;
interface Signup {
  email: string;
  password: string;
  options: {
    captchaToken?: string;
    data: {
      cadastro_radar: {
        perfil: Profile;
        aceita_emails: boolean;
        versao_dos_termos: string;
        sessao_id: string;
      };
    };
  };
}
type Call =
  | ["signup", Signup]
  | ["login", { email: string; password: string }]
  | ["resend", { email: string; options?: { captchaToken?: string } }]
  | ["password", { password: string }]
  | ["reset", string, Payload]
  | ["logout"]
  | ["insert", string, Payload]
  | ["update", string, Payload]
  | ["rpc", string, Payload];
type AuthCallback = (event: string) => void;
type TestWindow = InstanceType<typeof JSDOM>["window"];

function called<K extends Call[0]>(
  calls: Call[],
  name: K,
): Extract<Call, [K, ...unknown[]]> {
  const call = calls.find((entry) => entry[0] === name);
  assert.ok(call, `chamada ${name} ausente`);
  return call as Extract<Call, [K, ...unknown[]]>;
}

function app(
  {
    session = null,
    savedProfile = null,
    url = "https://radarestagio.com/",
    key = "",
    temaSalvo = null,
    armazenamentoBloqueado = false,
    erroDaSessao = null,
    erroDoPerfil = null,
    armazenado = {},
  }: {
    session?: Session | null;
    savedProfile?: Profile | null;
    url?: string;
    key?: string;
    temaSalvo?: string | null;
    armazenamentoBloqueado?: boolean;
    erroDaSessao?: Error | null;
    erroDoPerfil?: Error | null;
    armazenado?: Record<string, string>;
  } = {},
) {
  const erros: Error[] = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.sendTo(console, { omitJSDOMErrors: true });
  virtualConsole.on("jsdomError", (erro: Error) => erros.push(erro));
  const dom = new JSDOM(html, {
    url,
    runScripts: "dangerously",
    virtualConsole,
    beforeParse: (janela: TestWindow) => {
      if (temaSalvo) janela.localStorage.setItem("radar-tema", temaSalvo);
      for (const [chave, valor] of Object.entries(armazenado)) janela.localStorage.setItem(chave, valor);
      if (armazenamentoBloqueado) {
        for (const armazenamento of ["localStorage", "sessionStorage"]) {
          Object.defineProperty(janela, armazenamento, {
            get() {
              throw new janela.DOMException("armazenamento bloqueado", "SecurityError");
            },
          });
        }
      }
    },
  });
  const w = dom.window;
  const temaAntesDoApp = w.document.documentElement.dataset.tema;
  w.scrollTo = () => {};
  w.requestAnimationFrame = (callback: (timestamp: number) => void) => {
    callback(0);
    return 1;
  };
  w.fetch = async (caminho: string) => ({
    ok: Object.hasOwn(catalogos, String(caminho)),
    json: async () => catalogos[String(caminho)],
  });
  const calls: Call[] = [];
  let authCallback: AuthCallback = () => {
    throw new Error("callback não registrado");
  };
  const client = {
    auth: {
      getSession: async (): Promise<{ data: { session: Session | null }; error?: Error | null }> =>
        erroDaSessao ? { data: { session: null }, error: erroDaSessao } : { data: { session } },
      onAuthStateChange: (callback: AuthCallback) => {
        authCallback = callback;
      },
      signUp: async (args: Signup): Promise<{ data: { session: Session | null }; error?: Error }> => {
        calls.push(["signup", args]);
        return { data: { session: null } };
      },
      signInWithPassword: async (args: { email: string; password: string }) => {
        calls.push(["login", args]);
        return { data: { session: { user } } };
      },
      resend: async (args: { email: string; options?: { captchaToken?: string } }) => {
        calls.push(["resend", args]);
        return {};
      },
      resetPasswordForEmail: async (email: string, options: Payload) => {
        calls.push(["reset", email, options]);
        return {};
      },
      updateUser: async (args: { password: string }) => {
        calls.push(["password", args]);
        return {};
      },
      signOut: async () => {
        calls.push(["logout"]);
        return {};
      },
    },
    from: (table: string) => {
      const query = {
        select: () => query,
        eq: () => query,
        insert: async (args: Payload) => {
          calls.push(["insert", table, args]);
          return {};
        },
        update: (args: Payload) => {
          calls.push(["update", table, args]);
          if (table === "perfis" && savedProfile) Object.assign(savedProfile, args);
          return query;
        },
        maybeSingle: async (): Promise<{ data: Profile | null; error?: Error | null }> =>
          table === "perfis" && erroDoPerfil ? { data: null, error: erroDoPerfil } : { data: savedProfile },
        single: async (): Promise<{ data: Profile | null; error?: Error | null }> => ({ data: savedProfile }),
      };
      return query;
    },
    rpc: async (name: string, args: Payload): Promise<{ data?: unknown; error?: Error }> => {
      calls.push(["rpc", name, args]);
      return { data: {} };
    },
  };
  w.RADAR_CONFIG = {
    supabaseUrl: "https://example.com",
    supabasePublishableKey: "public",
    telegramBot: "bot",
    turnstileSiteKey: key,
  };
  w.supabase = { createClient: () => client };
  w.eval(script);
  return {
    w,
    erros,
    temaAntesDoApp,
    calls,
    client,
    close: () => w.close(),
    authEvent: (event: string) => authCallback(event),
  };
}

async function settle() {
  await new Promise((resolve) => setTimeout(resolve, 15));
}

function fill(w: TestWindow, incluirHabilidade = true) {
  const form = w.document.querySelector("#signup-form");
  for (
    const [key, value] of Object.entries({
      curso: "Computação",
      periodo: "3",
      cidade: "Recife, PE",
      email: user.email,
      senha: "uma-senha-forte",
    })
  ) form.elements[key].value = value;
  form.querySelector('[value="remoto"]').checked = true;
  if (incluirHabilidade) w.document.querySelector('[data-skill="Python"]').click();
  form.elements.aceitou_termos.checked = true;
  return form;
}

Deno.test("demonstração do Telegram anima a chegada de duas vagas", async () => {
  const a = app();
  try {
    await settle();
    const demo = a.w.document.querySelector("[data-chat-demo]");
    assert.ok(demo);
    assert.equal(demo.classList.contains("is-waiting"), true);
    assert.equal(demo.classList.contains("is-playing"), false);
    Object.defineProperty(a.w, "scrollY", { value: 89, configurable: true });
    a.w.dispatchEvent(new a.w.Event("scroll"));
    assert.equal(demo.classList.contains("is-waiting"), true);
    Object.defineProperty(a.w, "scrollY", { value: 90, configurable: true });
    a.w.dispatchEvent(new a.w.Event("scroll"));
    assert.equal(demo.classList.contains("is-waiting"), false);
    assert.equal(demo.classList.contains("is-playing"), true);
    assert.equal(demo.querySelectorAll(".chat-vacancy").length, 2);
    assert.equal(demo.querySelector(".chat-vacancy-second .chat-vacancy-title").textContent, "2. Estágio em marketing e conteúdo");
    assert.ok(demo.querySelector(".chat-typing"));
    assert.ok(demo.querySelector(".chat-feedback"));
    assert.equal(demo.querySelector(".chat-composer-field").textContent.trim(), "Mensagem");
    assert.equal(demo.querySelectorAll(".chat-composer-icon").length, 2);
  } finally { a.close(); }
});

Deno.test("tema fica direto no cabeçalho, começa claro e guarda a escolha", () => {
  const a = app();
  try {
    const raiz = a.w.document.documentElement;
    const botao = a.w.document.querySelector("#theme-toggle");
    assert.equal(a.w.document.querySelector("#header-settings"), null);
    assert.ok(botao.matches(".header-utilities > button"));
    assert.equal(botao.getAttribute("aria-label"), "Modo escuro");
    assert.equal(raiz.dataset.tema, "claro");
    assert.equal(botao.getAttribute("aria-pressed"), "false");
    botao.click();
    assert.equal(raiz.dataset.tema, "escuro");
    assert.equal(botao.getAttribute("aria-pressed"), "true");
    assert.equal(a.w.localStorage.getItem("radar-tema"), "escuro");
    botao.click();
    assert.equal(raiz.dataset.tema, "claro");
    assert.equal(botao.getAttribute("aria-pressed"), "false");
    assert.equal(a.w.localStorage.getItem("radar-tema"), "claro");
  } finally {
    a.close();
  }
});

Deno.test("tema e login são controles separados com ações independentes", async () => {
  const a = app();
  try {
    await settle();
    const doc = a.w.document;
    const tema = doc.querySelector("#theme-toggle");
    const entrar = doc.querySelector(".header-login");
    assert.equal(tema.nextElementSibling, entrar);
    tema.click();
    assert.equal(doc.documentElement.dataset.tema, "escuro");
    assert.equal(doc.querySelector("#signup-dialog").open, false);
    entrar.click();
    await settle();
    assert.equal(doc.documentElement.dataset.tema, "escuro");
    assert.equal(doc.querySelector("#signup-dialog").open, true);
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Entre na sua conta");
  } finally {
    a.close();
  }
});

Deno.test("tema escuro salvo é aplicado no head, antes da aplicação carregar", () => {
  const a = app({ temaSalvo: "escuro" });
  try {
    const scriptsDoHead = [...a.w.document.head.querySelectorAll("script:not([src])")];
    assert.ok(scriptsDoHead.some((elemento) => elemento.textContent.includes("radar-tema")));
    assert.equal(a.temaAntesDoApp, "escuro");
    assert.equal(a.w.document.documentElement.dataset.tema, "escuro");
    assert.equal(a.w.document.querySelector("#theme-toggle").getAttribute("aria-pressed"), "true");
  } finally {
    a.close();
  }
});

Deno.test("tema alterna sem erro quando o navegador bloqueia o armazenamento", () => {
  const a = app({ armazenamentoBloqueado: true });
  try {
    assert.equal(a.w.document.documentElement.dataset.tema, "claro");
    a.w.document.querySelector("#theme-toggle").click();
    assert.equal(a.w.document.documentElement.dataset.tema, "escuro");
    assert.deepEqual(a.erros.map((erro) => erro.message), []);
  } finally {
    a.close();
  }
});

Deno.test("cadastro cria a conta com o armazenamento do navegador bloqueado", async () => {
  const a = app({ armazenamentoBloqueado: true });
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const form = fill(a.w);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const sessao = called(a.calls, "signup")[1].options.data.cadastro_radar.sessao_id;
    assert.match(sessao, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    const sessoesDosEventos = a.calls
      .filter(([nome]) => nome === "insert")
      .map(([, , payload]) => (payload as Payload).sessao_id);
    assert.ok(sessoesDosEventos.length > 0);
    assert.deepEqual([...new Set(sessoesDosEventos)], [sessao]);
    assert.equal(a.w.document.querySelector("#auth-assistance").hidden, false);
    assert.deepEqual(a.erros.map((erro) => erro.message), []);
  } finally {
    a.close();
  }
});

Deno.test("com o armazenamento funcionando, a sessão de eventos é a mesma entre cargas e no cadastro", async () => {
  const chave = "radar-sessao-eventos";
  const cadastrar = async (a: ReturnType<typeof app>) => {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    fill(a.w).dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    return {
      cadastro: called(a.calls, "signup")[1].options.data.cadastro_radar.sessao_id,
      eventos: [
        ...new Set(a.calls.filter(([nome]) => nome === "insert").map(([, , payload]) => (payload as Payload).sessao_id)),
      ],
    };
  };
  const primeira = app();
  let guardada = "";
  try {
    const { cadastro, eventos } = await cadastrar(primeira);
    guardada = String(primeira.w.localStorage.getItem(chave));
    assert.match(guardada, /^[0-9a-f-]{36}$/);
    assert.equal(cadastro, guardada);
    assert.deepEqual(eventos, [guardada]);
  } finally {
    primeira.close();
  }
  const segunda = app({ armazenado: { [chave]: guardada } });
  try {
    const { cadastro, eventos } = await cadastrar(segunda);
    assert.equal(cadastro, guardada);
    assert.deepEqual(eventos, [guardada]);
    assert.equal(segunda.w.localStorage.getItem(chave), guardada);
  } finally {
    segunda.close();
  }
});

Deno.test("nenhum evento do site passa de 256 bytes de propriedades, mesmo com URL de 1.000 caracteres", async () => {
  const limite = 256;
  const urlLonga = (sufixo: string) => {
    const base = "https://radarestagio.com/";
    const caminho = "estágio-remoto-no-rio/".repeat(60).slice(0, 1000 - base.length - sufixo.length);
    return base + caminho + sufixo;
  };
  const bytesComoNoBanco = (propriedades: Record<string, unknown>) =>
    new TextEncoder().encode(JSON.stringify(propriedades)).length + 2 * Object.keys(propriedades).length;
  type Evento = { nome: string; propriedades: Record<string, unknown> };
  const eventos = (a: ReturnType<typeof app>) =>
    a.calls
      .filter(([nome, tabela]) => nome === "insert" && tabela === "eventos_produto")
      .map(([, , payload]) => payload as unknown as Evento);
  const vistos: Evento[] = [];

  assert.equal(urlLonga("").length, 1000);
  const visitante = app({ url: urlLonga("") });
  try {
    await settle();
    for (const chamada of visitante.w.document.querySelectorAll(".js-open-signup")) {
      chamada.click();
      await settle();
    }
    fill(visitante.w);
    for (let passo = 0; passo < 3; passo++) visitante.w.document.querySelector("#next-step").click();
    await settle();
    vistos.push(...eventos(visitante));
  } finally {
    visitante.close();
  }

  assert.equal(urlLonga("?conta").length, 1000);
  const dono = app({ session: { user }, savedProfile: { ...profile }, url: urlLonga("?conta") });
  try {
    await settle();
    const doc = dono.w.document;
    const telegram = doc.querySelector("#telegram-link");
    telegram.addEventListener("click", (evento: Event) => evento.preventDefault());
    telegram.click();
    doc.querySelector("#success-account").click();
    await settle();
    doc.querySelector("#edit-profile").click();
    await settle();
    doc.querySelector("#signup-form").dispatchEvent(new dono.w.Event("submit", { cancelable: true }));
    await settle();
    vistos.push(...eventos(dono));
  } finally {
    dono.close();
  }

  const catalogo = new Set([...script.matchAll(/registerEvent\("([a-z_]+)"/g)].map((encontrado) => encontrado[1]));
  assert.deepEqual(new Set(vistos.map((evento) => evento.nome)), catalogo);
  for (const evento of vistos) {
    assert.ok(
      bytesComoNoBanco(evento.propriedades) <= limite,
      `${evento.nome}: ${bytesComoNoBanco(evento.propriedades)} bytes`,
    );
  }
  const pagina = vistos.find((evento) => evento.nome === "landing_visualizada")?.propriedades.pagina;
  assert.match(String(pagina), /^\/est/);
});

Deno.test("voltar do link de confirmação com o armazenamento bloqueado mostra a ativação", async () => {
  const a = app({
    armazenamentoBloqueado: true,
    session: { user },
    savedProfile: { ...profile },
    url: "https://radarestagio.com/#access_token=fake",
  });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#success-state").hidden, false);
    assert.equal(a.w.document.querySelector("#telegram-link").hidden, false);
    assert.equal(a.w.document.querySelector("#form-message").textContent, "");
  } finally {
    a.close();
  }
});

Deno.test("sair da conta com o armazenamento bloqueado volta ao site", async () => {
  const a = app({
    armazenamentoBloqueado: true,
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#account-page").hidden, false);
    a.w.document.querySelector("#logout-account").click();
    await settle();
    assert.ok(a.calls.some(([nome]) => nome === "logout"));
    assert.equal(a.w.document.querySelector("#account-page").hidden, true);
    assert.equal(a.w.document.querySelector("#landing-page").hidden, false);
  } finally {
    a.close();
  }
});

Deno.test("cadastro exige aceite e envia perfil e sessão sem guardar senha localmente", async () => {
  const a = app();
  try {
    const form = fill(a.w);
    form.elements.aceitou_termos.checked = false;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    assert.equal(
      a.calls.some(([name, , payload]) =>
        name === "insert" && (payload as Payload)?.nome === "etapa_preferencias_concluida"
      ),
      false,
    );
    form.elements.aceitou_termos.checked = true;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const signup = called(a.calls, "signup")[1];
    assert.equal(
      signup.options.data.cadastro_radar.perfil.cidade,
      "Recife, PE",
    );
    assert.equal(signup.options.data.cadastro_radar.aceita_emails, false);
    assert.equal(
      signup.options.data.cadastro_radar.versao_dos_termos,
      "2026-09-05",
    );
    assert.equal(a.w.localStorage.getItem("radar-perfil-pendente"), null);
    assert.equal(
      a.w.document.querySelector("#assistance-submit").disabled,
      true,
    );
    assert.equal(
      a.calls.some(([name, , payload]) =>
        name === "insert" && (payload as Payload)?.nome === "etapa_preferencias_concluida"
      ),
      false,
    );
    assert.equal(
      a.calls.some(([name, , payload]) => name === "insert" && (payload as Payload)?.nome === "conta_criada"),
      false,
    );
  } finally {
    a.close();
  }
});

Deno.test("confirmação em outro aparelho consulta banco sem perfil no navegador", async () => {
  const a = app({
    session: { user },
    savedProfile: profile,
    url: "https://radarestagio.com/#access_token=fake",
  });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#success-state").hidden, false);
    assert.equal(a.w.document.querySelector("#telegram-link").hidden, false);
    assert.equal(
      a.calls.filter(([name]) => name === "rpc" || name === "update").length,
      0,
    );
  } finally {
    a.close();
  }
});

Deno.test("login preserva perfil existente mesmo com formulário diferente", async () => {
  const a = app({ savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    const form = fill(a.w);
    a.w.setAuthMode("login");
    form.elements.cidade.value = "Outra cidade";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "login").length, 1);
    assert.equal(
      a.calls.filter(([name]) => name === "update" || name === "rpc").length,
      0,
    );
    assert.equal(a.w.document.querySelector("#account-state").hidden, false);
  } finally {
    a.close();
  }
});

Deno.test("edição após login mostra preferências e salva sem pedir novo aceite", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
  });
  try {
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.cidade.value = "Natal, RN";
    assert.equal(form.elements.cidade.closest(".field").hidden, false);
    assert.equal(form.elements.aceitou_termos.required, false);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[1], "perfis");
    assert.equal(update[2].cidade, "Natal, RN");
    assert.equal(update[2].versao_dos_termos, undefined);
    assert.equal(a.calls.some(([name]) => name === "signup"), false);
  } finally {
    a.close();
  }
});

Deno.test("preferência de e-mail pode ser revogada e falha preserva o valor anterior", async () => {
  const a = app({ session: { user }, savedProfile: profile });
  try {
    await settle();
    const checkbox = a.w.document.querySelector("#account-emails");
    checkbox.checked = false;
    checkbox.dispatchEvent(new a.w.Event("change"));
    await settle();
    assert.equal(
      called(a.calls, "update")[2].aceita_emails,
      false,
    );
    assert.equal(checkbox.checked, false);
    a.client.from = () => {
      throw new Error("indisponível");
    };
    checkbox.checked = true;
    checkbox.dispatchEvent(new a.w.Event("change"));
    await settle();
    assert.equal(checkbox.checked, false);
    assert.equal(checkbox.disabled, false);
  } finally {
    a.close();
  }
});

Deno.test("CAPTCHA válido segue na autenticação e é descartado após tentativa", async () => {
  const a = app({ key: "chave-publica" });
  try {
    let widget: { callback: (token: string) => void } | undefined;
    let resets = 0;
    a.w.turnstile = {
      render: (_: string, options: { callback: (token: string) => void }) => {
        widget = options;
        return 1;
      },
      reset: () => {
        resets++;
      },
    };
    a.w.radarCaptchaReady();
    assert.ok(widget);
    widget.callback("token-valido");
    const form = fill(a.w);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(
      called(a.calls, "signup")[1].options.captchaToken,
      "token-valido",
    );
    assert.equal(resets, 1);
    assert.throws(() => a.w.requireCaptcha());
  } finally {
    a.close();
  }
});

Deno.test("reenvio usa e-mail editado e bloqueia clique repetido por um minuto", async () => {
  const a = app();
  try {
    a.w.showAssistance("resend", user.email);
    a.w.document.querySelector("#assistance-email").value =
      "corrigido@example.com";
    const submit = () =>
      a.w.document.querySelector("#assistance-form").dispatchEvent(
        new a.w.Event("submit", { cancelable: true }),
      );
    submit();
    await settle();
    submit();
    await settle();
    const resend = a.calls.filter(([name]) => name === "resend");
    assert.equal(resend.length, 1);
    assert.equal(called(a.calls, "resend")[1].email, "corrigido@example.com");
  } finally {
    a.close();
  }
});

Deno.test("link expirado oferece e-mail editável sem contexto local", async () => {
  const a = app({ url: "https://radarestagio.com/#error_code=otp_expired" });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#auth-assistance").hidden, false);
    assert.equal(
      a.w.document.querySelector("#assistance-email").required,
      true,
    );
    assert.match(
      a.w.document.querySelector("#assistance-message").textContent,
      /expirou/,
    );
  } finally {
    a.close();
  }
});

Deno.test("CAPTCHA configurado impede autenticação sem token", async () => {
  const a = app({ key: "public-key" });
  try {
    const form = fill(a.w);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    assert.match(
      a.w.document.querySelector("#form-message").textContent,
      /verificação de segurança/,
    );
  } finally {
    a.close();
  }
});

Deno.test("recuperação exige evento autenticado antes de trocar senha", async () => {
  const a = app({ session: { user } });
  try {
    a.w.showAssistance("new-password");
    const submit = () => {
      a.w.document.querySelector("#assistance-password").value =
        "nova-senha-forte";
      a.w.document.querySelector("#assistance-form").dispatchEvent(
        new a.w.Event("submit", { cancelable: true }),
      );
    };
    submit();
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "password").length, 0);
    a.authEvent("PASSWORD_RECOVERY");
    await settle();
    submit();
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "password").length, 1);
    assert.equal(a.w.document.querySelector("#assistance-password").value, "");
  } finally {
    a.close();
  }
});

Deno.test("conta sai do modal e mantém edição na página autenticada", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    assert.equal(a.w.document.querySelector("#landing-page").hidden, true);
    assert.equal(a.w.document.querySelector("#account-page").hidden, false);
    assert.equal(a.w.document.querySelector("#signup-dialog").open, false);
    assert.equal(a.w.document.activeElement.id, "account-title");
    assert.equal(new URL(a.w.location.href).searchParams.has("conta"), true);
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    assert.equal(a.w.document.querySelector("#signup-form").hidden, false);
    assert.ok(a.w.document.querySelector("#account-content #signup-form"));
    a.w.document.querySelector("#back-to-site").click();
    await settle();
    assert.equal(a.w.document.querySelector("#landing-page").hidden, false);
    assert.equal(a.w.document.querySelector("#account-page").hidden, true);
    assert.equal(a.w.document.querySelector("#signup-dialog").open, false);
    assert.ok(a.w.document.querySelector("#signup-dialog #signup-form"));
    assert.equal(new URL(a.w.location.href).searchParams.has("conta"), false);
  } finally { a.close(); }
});

Deno.test("ações sensíveis ficam separadas e exigem confirmação", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    const rows = a.w.document.querySelectorAll(".account-danger-row");
    const confirm = a.w.document.querySelector("#account-confirm");
    assert.equal(rows.length, 2);

    a.w.document.querySelector("#unlink-telegram").click();
    assert.equal(confirm.hidden, false);
    assert.equal(confirm.dataset.acao, "desvincular");
    assert.equal(a.w.document.querySelector("#account-confirm-title").textContent, "Desvincular o Telegram?");
    assert.equal(a.w.document.activeElement.id, "account-confirm-no");

    a.w.document.querySelector("#account-confirm-no").click();
    assert.equal(confirm.hidden, true);
    assert.equal(a.w.document.activeElement.id, "unlink-telegram");

    a.w.document.querySelector("#delete-account").click();
    assert.equal(confirm.hidden, false);
    assert.equal(confirm.dataset.acao, "excluir");
    assert.equal(a.w.document.querySelector("#account-confirm-title").textContent, "Excluir sua conta?");

    a.w.document.querySelector("#account-confirm-close").click();
    assert.equal(confirm.hidden, true);
    assert.equal(a.w.document.activeElement.id, "delete-account");
  } finally { a.close(); }
});

Deno.test("navegação da conta atualiza a seção ativa", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const overview = a.w.document.querySelector('.account-nav a[href="#account-overview-panel"]');
    const deliveries = a.w.document.querySelector('.account-nav a[href="#account-delivery-panel"]');
    const privacy = a.w.document.querySelector('.account-nav a[href="#account-privacy-panel"]');

    assert.equal(overview.getAttribute("aria-current"), "location");
    deliveries.click();
    await settle();
    assert.equal(overview.classList.contains("is-active"), false);
    assert.equal(deliveries.classList.contains("is-active"), true);
    assert.equal(deliveries.getAttribute("aria-current"), "location");
    assert.equal(a.w.location.hash, "#account-delivery-panel");
    assert.equal(a.w.document.querySelector("#account-overview-panel").hidden, true);
    assert.equal(a.w.document.querySelector("#account-delivery-panel").hidden, false);
    assert.equal(a.w.document.querySelector("#account-title").textContent, "Entregas");

    privacy.click();
    await settle();
    assert.equal(deliveries.hasAttribute("aria-current"), false);
    assert.equal(privacy.classList.contains("is-active"), true);
    assert.equal(a.w.location.hash, "#account-privacy-panel");
    assert.equal(a.w.document.querySelector("#account-delivery-panel").hidden, true);
    assert.equal(a.w.document.querySelector("#account-privacy-panel").hidden, false);
    assert.equal(a.w.document.querySelector("#account-title").textContent, "Privacidade");
  } finally { a.close(); }
});

Deno.test("recarregar a conta restaura ativação e sair retorna ao site", async () => {
  const a = app({ session: { user }, savedProfile: profile, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#account-page").hidden, false);
    assert.equal(a.w.document.querySelector("#telegram-link").hidden, false);
    a.w.document.querySelector("#success-account").click();
    await settle();
    a.w.document.querySelector("#logout-account").click();
    await settle();
    assert.equal(a.w.document.querySelector("#account-page").hidden, true);
    assert.equal(a.w.document.querySelector("#signup-dialog").open, false);
    assert.equal(a.w.document.querySelector("#landing-page").hidden, false);
  } finally { a.close(); }
});

Deno.test("endereço da conta sem sessão exige login", async () => {
  const a = app({ url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#account-page").hidden, true);
    assert.equal(a.w.document.querySelector("#signup-dialog").open, true);
    assert.equal(a.w.document.querySelector("#signup-form").hidden, false);
  } finally { a.close(); }
});

function visivel(elemento: ReturnType<TestWindow["document"]["querySelector"]>): boolean {
  for (let no = elemento; no; no = no.parentElement) {
    if (no.hidden) return false;
    if (no.tagName === "DIALOG" && !no.open) return false;
  }
  return Boolean(elemento);
}

Deno.test("erro ao abrir minha conta na tela de ativação aparece na própria tela", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    assert.equal(visivel(doc.querySelector("#success-state")), true);
    a.client.auth.getSession = async () => ({ data: { session: null } });
    doc.querySelector("#success-account").click();
    await settle();
    const aviso = doc.querySelector("#success-message");
    assert.match(aviso?.textContent ?? "", /sessão expirou/);
    assert.equal(visivel(aviso), true);
    assert.equal(visivel(doc.querySelector("#success-state")), true);
  } finally { a.close(); }
});

Deno.test("conta confirmada sem perfil pode ser excluída pelo site", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao, estado } = simularConfirmacaoModal(doc);
    assert.match(doc.querySelector("#form-notice").textContent, /Complete seu perfil/);
    const botao = doc.querySelector("#delete-account-without-profile");
    assert.equal(visivel(botao), true);
    botao.click();
    assert.equal(visivel(confirmacao), true);
    assert.equal(doc.querySelector("#account-confirm-title").textContent, "Excluir sua conta?");
    doc.querySelector("#account-confirm-no").click();
    assert.equal(confirmacao.hidden, true);
    assert.equal(doc.activeElement.id, "delete-account-without-profile");
    botao.click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    assert.deepEqual(
      a.calls.filter(([nome]) => nome === "rpc").map(([, funcao]) => funcao),
      ["apagar_minha_conta_sem_perfil"],
    );
    assert.ok(a.calls.some(([nome]) => nome === "logout"));
    assert.equal(estado.fechou, true);
    assert.equal(confirmacao.hidden, true);
    assert.equal(doc.querySelector("#success-title").textContent, "Sua conta foi apagada.");
    assert.equal(visivel(doc.querySelector("#success-state")), true);
    assert.equal(doc.querySelector("#success-account").hidden, true);
    assert.equal(visivel(botao), false);
    assert.equal(doc.querySelector('[data-event-origin="cabecalho"]').textContent.trim(), "Cadastrar meu perfil");
  } finally { a.close(); }
});

Deno.test("falha ao excluir a conta sem perfil avisa na tela e mantém a sessão", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    simularConfirmacaoModal(doc);
    a.client.rpc = async (name: string, args: Payload) => {
      a.calls.push(["rpc", name, args]);
      return { error: new TypeError("Failed to fetch") };
    };
    doc.querySelector("#delete-account-without-profile").click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    const mensagem = doc.querySelector("#form-message");
    assert.match(mensagem.textContent, /conexão/);
    assert.equal(visivel(mensagem), true);
    assert.equal(a.calls.some(([nome]) => nome === "logout"), false);
    assert.equal(visivel(doc.querySelector("#delete-account-without-profile")), true);
  } finally { a.close(); }
});

Deno.test("falha ao excluir a conta sem perfil explica o motivo com mensagem da exclusão", async () => {
  const casos: [Error, RegExp][] = [
    [Object.assign(new Error("conta com perfil usa excluir_minha_conta"), { code: "55000" }), /já tem um perfil salvo/],
    [Object.assign(new Error("sem sessão"), { code: "42501" }), /sessão expirou.*excluir/],
    [new TypeError("Failed to fetch"), /Não foi possível excluir a conta agora/],
  ];
  for (const [erro, esperada] of casos) {
    const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
    try {
      await settle();
      const doc = a.w.document;
      simularConfirmacaoModal(doc);
      a.client.rpc = async (name: string, args: Payload) => {
        a.calls.push(["rpc", name, args]);
        return { error: erro };
      };
      doc.querySelector("#delete-account-without-profile").click();
      doc.querySelector("#account-confirm-yes").click();
      await settle();
      const mensagem = doc.querySelector("#form-message");
      assert.match(mensagem.textContent, esperada);
      assert.doesNotMatch(mensagem.textContent, /cadastro|salvar o perfil/);
      assert.equal(visivel(mensagem), true);
    } finally { a.close(); }
  }
});

Deno.test("enviar o perfil trava a exclusão da conta sem perfil até a resposta", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao } = simularConfirmacaoModal(doc);
    let liberar = () => {};
    a.client.rpc = async (name: string, args: Payload) => {
      a.calls.push(["rpc", name, args]);
      await new Promise<void>((resolve) => { liberar = resolve; });
      return { error: new TypeError("Failed to fetch") };
    };
    fill(a.w).dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const botao = doc.querySelector("#delete-account-without-profile");
    assert.equal(botao.disabled, true);
    botao.click();
    assert.equal(confirmacao.open, false);
    liberar();
    await settle();
    assert.equal(botao.disabled, false);
    assert.deepEqual(
      a.calls.filter(([nome]) => nome === "rpc").map(([, funcao]) => funcao),
      ["concluir_meu_cadastro"],
    );
  } finally { a.close(); }
});

Deno.test("excluir a conta sem perfil fica ocupado e trava o envio do perfil", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    simularConfirmacaoModal(doc);
    const liberar = segurarRpc(a, "apagar_minha_conta_sem_perfil");
    const botao = doc.querySelector("#delete-account-without-profile");
    botao.click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    assert.equal(botao.disabled, true);
    assert.equal(botao.getAttribute("aria-busy"), "true");
    assert.equal(doc.querySelector("#submit-profile").disabled, true);
    fill(a.w).dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    liberar();
    await settle();
    assert.deepEqual(
      a.calls.filter(([nome]) => nome === "rpc").map(([, funcao]) => funcao),
      ["apagar_minha_conta_sem_perfil"],
    );
    assert.equal(doc.querySelector("#success-title").textContent, "Sua conta foi apagada.");
    assert.equal(botao.getAttribute("aria-busy"), "false");
  } finally { a.close(); }
});

Deno.test("conta com perfil não oferece a exclusão imediata", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta#account-privacy-panel",
  });
  try {
    await settle();
    const doc = a.w.document;
    assert.equal(visivel(doc.querySelector("#delete-account")), true);
    assert.equal(visivel(doc.querySelector("#delete-account-without-profile")), false);
  } finally { a.close(); }
});

Deno.test("aviso de perfil pendente não usa o visual de erro", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/#access_token=fake" });
  try {
    await settle();
    const mensagem = a.w.document.querySelector("#form-notice");
    assert.equal(mensagem.hidden, false);
    assert.equal(mensagem.textContent.includes("Complete seu perfil"), true);
    assert.equal(mensagem.classList.contains("form-message-aviso"), true);
  } finally { a.close(); }
});

const CONTA_INDISPONIVEL = /Não conseguimos carregar sua conta/;

Deno.test("sessão que não renova abre o login com aviso honesto, sem dizer que a conta foi criada", async () => {
  const a = app({
    erroDaSessao: Object.assign(new Error("Invalid Refresh Token: Refresh Token Not Found"), {
      code: "refresh_token_not_found",
      status: 400,
    }),
  });
  try {
    await settle();
    const doc = a.w.document;
    const mensagem = doc.querySelector("#form-message").textContent;
    assert.equal(doc.querySelector("#signup-dialog").open, true);
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Entre na sua conta");
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    assert.match(mensagem, CONTA_INDISPONIVEL);
    assert.doesNotMatch(mensagem, /conta foi criada/);
  } finally { a.close(); }
});

Deno.test("falha de rede ao ler o perfil na volta do link não diz que o perfil falta", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/#access_token=fake",
    erroDoPerfil: new TypeError("Failed to fetch"),
  });
  try {
    await settle();
    const doc = a.w.document;
    const mensagem = doc.querySelector("#form-message").textContent;
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Entre na sua conta");
    assert.match(mensagem, CONTA_INDISPONIVEL);
    assert.doesNotMatch(mensagem, /perfil ainda não foi salvo/);
  } finally { a.close(); }
});

Deno.test("falha de rede ao abrir minha conta leva ao login, não ao começo do cadastro", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    erroDoPerfil: new TypeError("Failed to fetch"),
  });
  try {
    await settle();
    const doc = a.w.document;
    assert.equal(doc.querySelector("#signup-dialog").open, false);
    doc.querySelector('[data-event-origin="cabecalho"]').click();
    await settle();
    assert.equal(doc.querySelector("#signup-dialog").open, true);
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Entre na sua conta");
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    assert.match(doc.querySelector("#form-message").textContent, CONTA_INDISPONIVEL);
  } finally { a.close(); }
});

Deno.test("falha de rede ao salvar a edição do perfil não diz que a conta foi criada", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();
    const from = a.client.from;
    a.client.from = (table: string) => {
      const query = from(table);
      query.single = async () => ({ data: null, error: new TypeError("Failed to fetch") });
      return query;
    };
    doc.querySelector("#signup-form").dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const mensagem = doc.querySelector("#form-message").textContent;
    assert.doesNotMatch(mensagem, /conta foi criada/);
    assert.match(mensagem, /conexão/);
  } finally { a.close(); }
});

Deno.test("conta confirmada sem perfil que falha ao salvar o perfil recebe o aviso de perfil pendente", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    a.client.rpc = async (name: string, args: Payload) => {
      a.calls.push(["rpc", name, args]);
      return { error: new TypeError("Failed to fetch") };
    };
    fill(a.w).dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.deepEqual(
      a.calls.filter(([nome]) => nome === "rpc").map(([, funcao]) => funcao),
      ["concluir_meu_cadastro"],
    );
    const mensagem = doc.querySelector("#form-message");
    assert.match(mensagem.textContent, /Sua conta foi criada, mas o perfil ainda não foi salvo/);
    assert.equal(visivel(mensagem), true);
  } finally { a.close(); }
});

Deno.test("cadastro começa pelo perfil e só no final pede a conta", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    const passoAtivo = () => doc.querySelector(".form-step.is-active").dataset.step;
    const progresso = () => [
      doc.querySelector("#progress-percent").textContent,
      doc.querySelector("#progress-track").getAttribute("aria-valuenow"),
      doc.querySelector("#progress-bar").style.width,
    ];
    assert.equal(passoAtivo(), "2");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 1 de 4");
    assert.deepEqual(progresso(), ["0%", "0", "0%"]);
    assert.equal(doc.querySelector("#previous-step").hidden, true);
    assert.equal(doc.querySelector("#submit-profile").hidden, true);
    doc.querySelector("#next-step").click();
    assert.equal(passoAtivo(), "3");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 2 de 4");
    assert.deepEqual(progresso(), ["25%", "25", "25%"]);
    doc.querySelector("#next-step").click();
    assert.equal(passoAtivo(), "4");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 3 de 4");
    assert.deepEqual(progresso(), ["50%", "50", "50%"]);
    doc.querySelector("#next-step").click();
    assert.equal(passoAtivo(), "1");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 4 de 4");
    assert.deepEqual(progresso(), ["75%", "75", "75%"]);
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    assert.equal(form.elements.senha.value, "uma-senha-forte");
    await settle();
  } finally { a.close(); }
});

Deno.test("botão de entrar abre a conta sem passar pela triagem", async () => {
  const a = app();
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector(".js-open-login").click();
    await settle();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    assert.equal(doc.querySelector("#submit-label").textContent, "Entrar e continuar");
    assert.equal(doc.querySelector("#signup-consent").hidden, true);
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Entre na sua conta");
    assert.equal(doc.querySelector("#toggle-auth-mode").textContent, "Criar conta");
  } finally { a.close(); }
});

Deno.test("controle de senha usa ícone e anuncia mostrar e ocultar", async () => {
  const a = app();
  try {
    await settle();
    const doc = a.w.document;
    const password = doc.querySelector('input[name="senha"]');
    const toggle = doc.querySelector('[data-toggle-password="senha"]');
    assert.ok(password);
    assert.ok(toggle);
    assert.ok(toggle.querySelector("svg"));
    assert.equal(toggle.textContent.trim(), "");
    assert.equal(toggle.getAttribute("aria-label"), "Mostrar senha");
    assert.equal(password.getAttribute("type"), "password");
    toggle.click();
    assert.equal(password.getAttribute("type"), "text");
    assert.equal(toggle.getAttribute("aria-label"), "Ocultar senha");
    assert.equal(toggle.getAttribute("aria-pressed"), "true");
    toggle.click();
    assert.equal(password.getAttribute("type"), "password");
    assert.equal(toggle.getAttribute("aria-label"), "Mostrar senha");
    assert.equal(toggle.getAttribute("aria-pressed"), "false");
  } finally { a.close(); }
});

Deno.test("botão de cadastrar continua abrindo na triagem", async () => {
  const a = app();
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector(".js-open-signup").click();
    await settle();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "2");
    assert.equal(doc.querySelector("#submit-label").textContent, "Criar conta e continuar");
    assert.equal(doc.querySelector("#conta-titulo").textContent, "Comece pela sua conta");
  } finally { a.close(); }
});

Deno.test("alternar para login e voltar preserva o rascunho do perfil", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    doc.querySelector("#toggle-auth-mode").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    doc.querySelector("#toggle-auth-mode").click();
    assert.equal(form.elements.curso.value, "Computação");
    assert.deepEqual(habilidadesNaTela(a.w), ["Python"]);
    assert.equal(form.elements.cidade.value, "Recife, PE");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 4 de 4");
    await settle();
  } finally { a.close(); }
});

function fecharComEsc(w: TestWindow) {
  w.document.querySelector("#cidade").dispatchEvent(
    new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }),
  );
}

async function reabrirCadastro(w: TestWindow) {
  w.document.querySelector(".js-open-signup").click();
  await settle();
}

Deno.test("fechar o cadastro com Esc ou no X e reabrir devolve o rascunho na mesma etapa", async () => {
  const a = app();
  try {
    await settle();
    await reabrirCadastro(a.w);
    const doc = a.w.document;
    const form = fill(a.w);
    doc.querySelector("#next-step").click();
    await settle();
    digitarHabilidade(a.w, "Figma");
    doc.querySelector("#next-step").click();
    await settle();
    form.querySelector('input[name="areas"][value="dados_ia"]').checked = true;

    const conferirRascunho = () => {
      assert.equal(doc.querySelector("#signup-dialog").open, true);
      assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
      assert.equal(form.elements.curso.value, "Computação");
      assert.equal(form.elements.periodo.value, "3");
      assert.equal(form.elements.cidade.value, "Recife, PE");
      assert.equal(form.querySelector('[value="remoto"]').checked, true);
      assert.deepEqual(habilidadesNaTela(a.w), ["Python", "Figma"]);
      assert.equal(form.querySelector('input[name="areas"][value="dados_ia"]').checked, true);
      assert.equal(form.elements.senha.value, "");
    };
    fecharComEsc(a.w);
    assert.equal(doc.querySelector("#signup-dialog").open, false);
    await reabrirCadastro(a.w);
    conferirRascunho();
    doc.querySelector("#close-dialog").click();
    assert.equal(doc.querySelector("#signup-dialog").open, false);
    await reabrirCadastro(a.w);
    conferirRascunho();

    doc.querySelector("#next-step").click();
    form.elements.senha.value = "uma-senha-forte";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const perfil = called(a.calls, "signup")[1].options.data.cadastro_radar.perfil;
    assert.equal(perfil.curso, "Computação");
    assert.deepEqual(Array.from(perfil.habilidades), ["Python", "Figma"]);
    assert.deepEqual(Array.from(perfil.areas_de_interesse), ["dados_ia"]);
  } finally {
    a.close();
  }
});

Deno.test("fechar o cadastro depois de seguir sem habilidades não pede a escolha de novo", async () => {
  const a = app();
  try {
    await settle();
    await reabrirCadastro(a.w);
    const doc = a.w.document;
    const form = fill(a.w, false);
    doc.querySelector("#next-step").click();
    doc.querySelector("#continue-without-skills").click();
    fecharComEsc(a.w);
    await reabrirCadastro(a.w);

    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    assert.equal(form.elements.senha.value, "");
    form.elements.senha.value = "uma-senha-forte";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.deepEqual(
      Array.from(called(a.calls, "signup")[1].options.data.cadastro_radar.perfil.habilidades),
      [],
    );
  } finally {
    a.close();
  }
});

Deno.test("perfil carregado da conta não reaparece no cadastro depois que a sessão acaba", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();
    assert.equal(doc.querySelector("#signup-form").elements.curso.value, "Computação");
    a.client.auth.getSession = async () => ({ data: { session: null } });
    doc.querySelector("#back-to-site").click();
    await reabrirCadastro(a.w);

    const form = doc.querySelector("#signup-form");
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "2");
    assert.equal(form.elements.curso.value, "");
    assert.equal(form.elements.cidade.value, "");
    assert.deepEqual(habilidadesNaTela(a.w), []);
  } finally {
    a.close();
  }
});

function fecharCadastro(w: TestWindow, como: string) {
  if (como === "esc") fecharComEsc(w);
  else if (como === "x") w.document.querySelector("#close-dialog").click();
  else w.dispatchEvent(new w.PopStateEvent("popstate", { state: null }));
}

function conferirSenhaVaziaEEscondida(w: TestWindow, contexto: string) {
  const campo = w.document.querySelector("#signup-password");
  const botao = w.document.querySelector('[data-toggle-password="senha"]');
  assert.equal(campo.value, "", contexto);
  assert.equal(campo.type, "password", contexto);
  assert.equal(botao.getAttribute("aria-pressed"), "false", contexto);
  assert.equal(botao.getAttribute("aria-label"), "Mostrar senha", contexto);
}

Deno.test("fechar o cadastro apaga a senha e volta a escondê-la, mantendo o resto do rascunho", async () => {
  for (const como of ["esc", "x", "voltar"]) {
    const a = app();
    try {
      await settle();
      await reabrirCadastro(a.w);
      const form = fill(a.w);
      for (let passo = 0; passo < 3; passo += 1) a.w.document.querySelector("#next-step").click();
      await settle();
      a.w.document.querySelector('[data-toggle-password="senha"]').click();
      assert.equal(form.elements.senha.type, "text");

      fecharCadastro(a.w, como);
      await reabrirCadastro(a.w);

      conferirSenhaVaziaEEscondida(a.w, como);
      assert.equal(form.elements.curso.value, "Computação", como);
      assert.equal(form.elements.email.value, user.email, como);
      assert.equal(a.w.document.querySelector(".form-step.is-active").dataset.step, "1", como);
    } finally {
      a.close();
    }
  }
});

Deno.test("senha de um login recusado não fica no campo ao fechar e reabrir", async () => {
  const a = app();
  try {
    await settle();
    Object.assign(a.client.auth, {
      signInWithPassword: async () => ({
        data: { session: null },
        error: { code: "invalid_credentials", message: "Invalid login credentials", status: 400 },
      }),
    });
    await reabrirCadastro(a.w);
    a.w.document.querySelector("#toggle-auth-mode").click();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.email.value = "a@x.com";
    form.elements.senha.value = "senha-da-pessoa-A";
    a.w.document.querySelector('[data-toggle-password="senha"]').click();
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.match(a.w.document.querySelector("#form-message").textContent, /E-mail ou senha incorretos/);

    fecharComEsc(a.w);
    await reabrirCadastro(a.w);

    conferirSenhaVaziaEEscondida(a.w, "login recusado");
  } finally {
    a.close();
  }
});

const outraPessoa = { id: "00000000-0000-4000-8000-000000000002", email: "outra@example.com" };

function sessaoPassaASer(a: ReturnType<typeof app>, sessao: Session | null) {
  Object.assign(a.client.auth, { getSession: async () => ({ data: { session: sessao } }) });
}

function conferirCadastroVazio(a: ReturnType<typeof app>, contexto: string) {
  const form = a.w.document.querySelector("#signup-form");
  assert.equal(form.elements.curso.value, "", contexto);
  assert.equal(form.elements.email.value, "", contexto);
  assert.deepEqual(habilidadesNaTela(a.w), [], contexto);
}

Deno.test("rascunho e e-mail de uma conta não aparecem para quem abre o cadastro depois que a sessão acaba", async () => {
  const comPerfil = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    await reabrirCadastro(comPerfil.w);
    assert.equal(comPerfil.w.document.querySelector("#account-page").hidden, false);
    comPerfil.w.document.querySelector("#close-account").click();
    sessaoPassaASer(comPerfil, null);
    await reabrirCadastro(comPerfil.w);
    conferirCadastroVazio(comPerfil, "conta com perfil");
  } finally {
    comPerfil.close();
  }

  const semPerfil = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const form = semPerfil.w.document.querySelector("#signup-form");
    assert.equal(form.elements.email.value, user.email);
    form.elements.curso.value = "Direito";
    semPerfil.w.document.querySelector("#back-to-site").click();
    sessaoPassaASer(semPerfil, null);
    await reabrirCadastro(semPerfil.w);
    conferirCadastroVazio(semPerfil, "conta sem perfil");
    assert.equal(semPerfil.w.document.querySelector("#credenciais").hidden, false);
  } finally {
    semPerfil.close();
  }
});

Deno.test("outra conta que entra na mesma página não vê o rascunho da conta anterior", async () => {
  const a = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.curso.value = "Direito";
    a.w.document.querySelector("#back-to-site").click();
    sessaoPassaASer(a, { user: outraPessoa });
    await reabrirCadastro(a.w);

    assert.equal(a.w.document.querySelector("#missing-profile-deletion").hidden, false);
    assert.equal(form.elements.curso.value, "");
    assert.equal(form.elements.email.value, outraPessoa.email);
  } finally {
    a.close();
  }
});

Deno.test("visitante que confirma a conta continua com o próprio rascunho", async () => {
  const a = app();
  try {
    await settle();
    await reabrirCadastro(a.w);
    const form = fill(a.w);
    a.w.document.querySelector("#next-step").click();
    fecharComEsc(a.w);
    sessaoPassaASer(a, { user });
    await reabrirCadastro(a.w);

    assert.equal(a.w.document.querySelector("#missing-profile-deletion").hidden, false);
    assert.equal(form.elements.curso.value, "Computação");
    assert.deepEqual(habilidadesNaTela(a.w), ["Python"]);
    assert.equal(form.elements.email.value, user.email);
  } finally {
    a.close();
  }
});

Deno.test("sair ou excluir a conta deixa o cadastro vazio para a próxima pessoa", async () => {
  const saindo = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    await reabrirCadastro(saindo.w);
    saindo.w.document.querySelector("#edit-profile").click();
    await settle();
    saindo.w.document.querySelector("#back-to-site").click();
    await reabrirCadastro(saindo.w);
    saindo.w.document.querySelector("#logout-account").click();
    await settle();
    sessaoPassaASer(saindo, null);
    await reabrirCadastro(saindo.w);
    conferirCadastroVazio(saindo, "logout depois de editar");
  } finally {
    saindo.close();
  }

  const semPerfil = app({ session: { user }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    semPerfil.w.document.querySelector("#signup-form").elements.curso.value = "Direito";
    semPerfil.w.document.querySelector("#delete-account-without-profile").click();
    semPerfil.w.document.querySelector("#account-confirm-yes").click();
    await settle();
    sessaoPassaASer(semPerfil, null);
    semPerfil.w.document.querySelector("#finish-signup").click();
    await reabrirCadastro(semPerfil.w);
    conferirCadastroVazio(semPerfil, "exclusão sem perfil");
  } finally {
    semPerfil.close();
  }

  const comPerfil = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    await reabrirCadastro(comPerfil.w);
    comPerfil.w.document.querySelector("#delete-account").click();
    comPerfil.w.document.querySelector("#account-confirm-yes").click();
    await settle();
    comPerfil.w.document.querySelector("#finish-signup").click();
    sessaoPassaASer(comPerfil, null);
    await reabrirCadastro(comPerfil.w);
    conferirCadastroVazio(comPerfil, "exclusão com perfil e sessão encerrada depois");
  } finally {
    comPerfil.close();
  }
});

Deno.test("e-mail digitado num login não fica para quem abre o cadastro depois que a sessão acaba", async () => {
  const a = app({ savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    await reabrirCadastro(a.w);
    a.w.document.querySelector("#toggle-auth-mode").click();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.email.value = "a@x.com";
    form.elements.senha.value = "uma-senha-forte";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.w.document.querySelector("#account-page").hidden, false);
    a.w.document.querySelector("#close-account").click();
    await reabrirCadastro(a.w);

    conferirCadastroVazio(a, "login e sessão encerrada");
  } finally {
    a.close();
  }
});

Deno.test("envio duplicado durante a autenticação gera uma única tentativa", async () => {
  const a = app();
  let liberarCadastro = () => {};
  const cadastroLiberado = new Promise<void>((resolve) => { liberarCadastro = resolve; });
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    a.client.auth.signUp = async (args: Signup) => {
      a.calls.push(["signup", args]);
      await cadastroLiberado;
      return { data: { session: null } };
    };
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 1);
    assert.equal(doc.querySelector("#submit-profile").disabled, true);
    liberarCadastro();
    await settle();
  } finally { a.close(); }
});

Deno.test("entrar pede só a conta e edição do perfil pula esse passo", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    const doc = a.w.document;
    a.w.setAuthMode("login");
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "1");
    assert.equal(doc.querySelector(".progress-wrap").hidden, true);
    assert.equal(doc.querySelector("#next-step").hidden, true);
    assert.equal(doc.querySelector("#submit-profile").hidden, false);
    doc.querySelector("#edit-profile").click();
    await settle();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "2");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 1 de 3");
    assert.equal(doc.querySelector("#progress-percent").textContent, "0%");
    assert.equal(doc.querySelector("#credenciais").hidden, true);
  } finally { a.close(); }
});

Deno.test("sessão aberta troca a chamada da landing por minha conta", async () => {
  const a = app({ session: { user }, savedProfile: profile });
  try {
    await settle();
    const doc = a.w.document;
    const cabecalho = doc.querySelector('[data-event-origin="cabecalho"]');
    assert.equal(doc.querySelector("#landing-page").hidden, false);
    assert.equal(cabecalho.textContent.trim(), "Minha conta");
    assert.equal(
      doc.querySelector('[data-event-origin="hero"]').textContent.trim(),
      "Minha conta →",
    );
    cabecalho.click();
    await settle();
    assert.equal(
      a.calls.some(([name, , payload]) =>
        name === "insert" && (payload as Payload)?.nome === "cta_cadastro_aberto"
      ),
      false,
    );
    assert.equal(doc.querySelector("#account-page").hidden, false);
    doc.querySelector("#logout-account").click();
    await settle();
    assert.equal(cabecalho.textContent.trim(), "Cadastrar meu perfil");
  } finally { a.close(); }
});

Deno.test("quem já entrou vai para a conta sem piscar o modal", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    const doc = a.w.document;
    const dialogo = doc.querySelector("#signup-dialog");
    doc.querySelector('[data-event-origin="cabecalho"]').click();
    assert.equal(dialogo.open, false);
    await settle();
    assert.equal(dialogo.open, false);
    assert.equal(doc.querySelector("#account-page").hidden, false);
  } finally { a.close(); }
});

Deno.test("conta vinculada explica a espera sem afirmar que a busca rodou", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    a.w.document.querySelector('[data-event-origin="cabecalho"]').click();
    await settle();
    const texto = a.w.document.querySelector("#account-schedule").textContent;
    assert.equal(texto.includes("Telegram vinculado"), true);
    assert.equal(texto.includes("quando houver vagas compatíveis"), true);
    assert.equal(texto.includes("pode aguardar a próxima execução diária"), true);
    assert.equal(texto.includes("busca iniciou"), false);
    assert.equal(texto.includes("concluída"), false);
  } finally { a.close(); }
});

Deno.test("pausar mantém a conta pausada e oferece motivo opcional", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[2].ativo, false);
    assert.equal(update[2].motivo_pausa, undefined);
    assert.equal(doc.querySelector("#pause-reason").hidden, false);
    assert.equal(doc.activeElement.id, "pause-reason-title");
    doc.querySelector("#skip-pause-reason").click();
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
    assert.equal(doc.querySelector("#account-schedule").textContent.includes("pausadas"), true);
  } finally { a.close(); }
});

Deno.test("resposta de motivo é separada e não altera ativo", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    doc.querySelector('input[name="motivo-pausa"][value="sem_vagas_uteis"]').click();
    doc.querySelector("#save-pause-reason").click();
    await settle();
    const updates = a.calls.filter(([name]) => name === "update");
    assert.equal(updates.length, 2);
    const reasonUpdate = updates[1];
    assert.ok(reasonUpdate);
    const reasonPayload = reasonUpdate[2];
    assert.ok(reasonPayload);
    assert.deepEqual(reasonPayload.motivo_pausa, "sem_vagas_uteis");
    assert.equal(reasonPayload.ativo, undefined);
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
    assert.match(doc.querySelector("#account-notice").textContent, /Motivo salvo/);
  } finally { a.close(); }
});

Deno.test("erro ou corrida ao salvar motivo mantém pausa e permite pular", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const from = a.client.from;
    a.client.from = (table: string) => {
      const query = from(table);
      const update = query.update;
      query.update = (args: Payload) => {
        const chained = update(args);
        if ("motivo_pausa" in args) {
          chained.maybeSingle = async () => ({ data: { ...profile, ativo: true } as Profile });
        }
        return chained;
      };
      return query;
    };
    const doc = a.w.document;
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    doc.querySelector('input[name="motivo-pausa"][value="outro"]').click();
    doc.querySelector("#save-pause-reason").click();
    await settle();
    assert.equal(doc.querySelector("#pause-reason").hidden, false);
    assert.match(doc.querySelector("#pause-reason-message").textContent, /não está mais pausada/);
    doc.querySelector("#skip-pause-reason").click();
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
    assert.equal(doc.querySelector("#account-schedule").textContent.includes("pausadas"), true);
  } finally { a.close(); }
});

Deno.test("retomar limpa o motivo no mesmo update", async () => {
  const a = app({
    session: { user },
    savedProfile: {
      ...profile,
      ativo: false,
      motivo_pausa: "outro",
      telegram_chat_id: "123",
    },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    a.w.document.querySelector("#toggle-deliveries").click();
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[2].ativo, true);
    assert.equal(update[2].motivo_pausa, null);
    assert.equal(a.w.document.querySelector("#pause-reason").hidden, true);
    assert.equal(a.w.document.querySelector("#account-schedule").textContent.includes("recomendações chegarão"), true);
  } finally { a.close(); }
});

function simularConfirmacaoModal(doc: TestWindow["document"]) {
  const confirmacao = doc.querySelector("#account-confirm");
  const estado = { fechou: false };
  confirmacao.showModal = () => confirmacao.setAttribute("open", "");
  confirmacao.close = () => {
    estado.fechou = true;
    confirmacao.removeAttribute("open");
  };
  return { confirmacao, estado };
}

function segurarProximaSessao(a: ReturnType<typeof app>, falha?: Error) {
  const getSession = a.client.auth.getSession;
  let liberar = () => {};
  let primeira = true;
  a.client.auth.getSession = async () => {
    if (primeira) {
      primeira = false;
      await new Promise<void>((resolve) => { liberar = resolve; });
      if (falha) throw falha;
    }
    return getSession();
  };
  return () => liberar();
}

async function contaRecemVinculadaAoVoltarAAba() {
  const salvo: Profile = { ...profile };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  await settle();
  assert.equal(a.w.document.querySelector("#success-state").hidden, false);
  salvo.telegram_chat_id = "123";
  a.w.dispatchEvent(new a.w.Event("focus"));
  await settle();
  assert.equal(a.w.document.querySelector("#success-state").hidden, true);
  assert.equal(a.w.document.querySelector("#account-state").hidden, false);
  return a;
}

Deno.test("voltar à aba na ativação mostra a conta assim que o Telegram é vinculado", async () => {
  const a = await contaRecemVinculadaAoVoltarAAba();
  try {
    assert.equal(a.w.document.querySelector("#account-delivery-title").textContent, "Entregas ativas");
  } finally { a.close(); }
});

Deno.test("voltar à aba durante a edição do perfil não descarta o que foi digitado", async () => {
  const a = await contaRecemVinculadaAoVoltarAAba();
  try {
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();
    const formulario = doc.querySelector("#signup-form");
    formulario.elements.curso.value = "Direito";
    a.w.dispatchEvent(new a.w.Event("focus"));
    await settle();
    assert.equal(formulario.hidden, false);
    assert.equal(formulario.elements.curso.value, "Direito");
    assert.equal(doc.querySelector("#account-state").hidden, true);
  } finally { a.close(); }
});

Deno.test("voltar à aba com a confirmação aberta não esconde o diálogo modal", async () => {
  const a = await contaRecemVinculadaAoVoltarAAba();
  try {
    const { confirmacao, estado } = simularConfirmacaoModal(a.w.document);
    a.w.document.querySelector("#delete-account").click();
    assert.equal(confirmacao.open, true);
    a.w.dispatchEvent(new a.w.Event("focus"));
    await settle();
    assert.equal(confirmacao.hidden, false);
    assert.equal(confirmacao.open, true);
    assert.equal(estado.fechou, false);
    assert.equal(confirmacao.dataset.acao, "excluir");
  } finally { a.close(); }
});

Deno.test("voltar à aba mantém a pergunta do motivo da pausa", async () => {
  const a = await contaRecemVinculadaAoVoltarAAba();
  try {
    const doc = a.w.document;
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    assert.equal(doc.querySelector("#pause-reason").hidden, false);
    a.w.dispatchEvent(new a.w.Event("focus"));
    await settle();
    assert.equal(doc.querySelector("#pause-reason").hidden, false);
  } finally { a.close(); }
});

Deno.test("consulta do vínculo que termina depois de a pessoa sair da ativação não mexe na tela", async () => {
  const salvo: Profile = { ...profile };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    const liberar = segurarProximaSessao(a);
    a.w.dispatchEvent(new a.w.Event("focus"));
    await settle();
    salvo.telegram_chat_id = "123";
    doc.querySelector("#success-account").click();
    await settle();
    doc.querySelector("#edit-profile").click();
    await settle();
    const formulario = doc.querySelector("#signup-form");
    formulario.elements.curso.value = "Direito";
    liberar();
    await settle();
    assert.equal(formulario.hidden, false);
    assert.equal(formulario.elements.curso.value, "Direito");
  } finally { a.close(); }
});

Deno.test("resposta da pausa que chega com a confirmação aberta fecha o diálogo em vez de escondê-lo", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao, estado } = simularConfirmacaoModal(doc);
    const liberar = segurarProximaSessao(a);
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    doc.querySelector("#delete-account").click();
    assert.equal(confirmacao.open, true);
    liberar();
    await settle();
    assert.equal(estado.fechou, true);
    assert.equal(confirmacao.open, false);
    assert.equal(confirmacao.hidden, true);
  } finally { a.close(); }
});

Deno.test("voltar no histórico para a conta com a confirmação aberta fecha o diálogo em vez de escondê-lo", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao, estado } = simularConfirmacaoModal(doc);
    doc.querySelector("#delete-account").click();
    assert.equal(confirmacao.open, true);
    a.w.dispatchEvent(new a.w.PopStateEvent("popstate"));
    await settle();
    assert.equal(estado.fechou, true);
    assert.equal(confirmacao.open, false);
    assert.equal(confirmacao.hidden, true);
  } finally { a.close(); }
});

Deno.test("voltar no histórico para o site com a confirmação aberta fecha a confirmação", async () => {
  const casos: [string, Profile | null, string][] = [
    ["excluir", { ...profile, telegram_chat_id: "123" }, "#delete-account"],
    ["desvincular", { ...profile, telegram_chat_id: "123" }, "#unlink-telegram"],
    ["apagar-sem-perfil", null, "#delete-account-without-profile"],
  ];
  for (const [acao, salvo, origem] of casos) {
    const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
    try {
      await settle();
      const doc = a.w.document;
      const { confirmacao, estado } = simularConfirmacaoModal(doc);
      doc.querySelector(origem).click();
      assert.equal(confirmacao.dataset.acao, acao);
      assert.equal(confirmacao.open, true);
      a.w.history.replaceState(null, "", "/");
      a.w.dispatchEvent(new a.w.PopStateEvent("popstate"));
      await settle();
      assert.equal(doc.querySelector("#landing-page").hidden, false, acao);
      assert.equal(estado.fechou, true, acao);
      assert.equal(confirmacao.open, false, acao);
      assert.equal(confirmacao.hidden, true, acao);
    } finally { a.close(); }
  }
});

function bancoQueRespeitaOAtivo(a: ReturnType<typeof app>, salvo: Profile) {
  const from = a.client.from;
  a.client.from = (table: string) => {
    const antes = { ...salvo };
    const query = from(table);
    let ativoExigido: unknown;
    query.eq = (coluna?: string, valor?: unknown) => {
      if (coluna === "ativo") ativoExigido = valor;
      return query;
    };
    const maybeSingle = query.maybeSingle;
    query.maybeSingle = async () => {
      if (ativoExigido === undefined || antes.ativo === ativoExigido) return maybeSingle();
      Object.assign(salvo, antes);
      return { data: null };
    };
    return query;
  };
}

Deno.test("clicar em Pausar com a conta já pausada em outro lugar não retoma as entregas", async () => {
  const salvo: Profile = { ...profile, telegram_chat_id: "123" };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    bancoQueRespeitaOAtivo(a, salvo);
    const doc = a.w.document;
    const botao = doc.querySelector("#toggle-deliveries");
    assert.equal(botao.textContent, "Pausar entregas");
    salvo.ativo = false;
    salvo.motivo_pausa = "outro";
    botao.click();
    await settle();
    assert.equal(a.calls.some((call) => call[0] === "update" && call[2].ativo === true), false);
    assert.equal(salvo.ativo, false);
    assert.equal(salvo.motivo_pausa, "outro");
    assert.equal(botao.textContent, "Retomar entregas");
    assert.equal(doc.querySelector("#account-delivery-title").textContent, "Entregas pausadas");
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
    assert.match(doc.querySelector("#account-notice").textContent, /já tinham mudado/);
    assert.match(doc.querySelector("#account-notice").textContent, /Nada foi alterado/);
  } finally { a.close(); }
});

Deno.test("clicar em Retomar com a conta já reativada em outro lugar não pausa as entregas", async () => {
  const salvo: Profile = { ...profile, telegram_chat_id: "123", ativo: false, motivo_pausa: "outro" };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    bancoQueRespeitaOAtivo(a, salvo);
    const doc = a.w.document;
    const botao = doc.querySelector("#toggle-deliveries");
    assert.equal(botao.textContent, "Retomar entregas");
    salvo.ativo = true;
    salvo.motivo_pausa = null;
    botao.click();
    await settle();
    assert.equal(a.calls.some((call) => call[0] === "update" && call[2].ativo === false), false);
    assert.equal(salvo.ativo, true);
    assert.equal(botao.textContent, "Pausar entregas");
    assert.equal(doc.querySelector("#account-delivery-title").textContent, "Entregas ativas");
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
    assert.match(doc.querySelector("#account-notice").textContent, /já tinham mudado/);
  } finally { a.close(); }
});

function falharLeiturasDoPerfil(a: ReturnType<typeof app>) {
  const from = a.client.from;
  a.client.from = (table: string) => {
    const query = from(table);
    const update = query.update;
    let atualizando = false;
    query.update = (args: Payload) => {
      atualizando = true;
      return update(args);
    };
    const maybeSingle = query.maybeSingle;
    query.maybeSingle = async () => {
      if (!atualizando) throw new TypeError("Failed to fetch");
      return maybeSingle();
    };
    return query;
  };
}

Deno.test("pausa aplicada mostra a conta pausada e a pergunta mesmo se a leitura seguinte falharia", async () => {
  const salvo: Profile = { ...profile, telegram_chat_id: "123" };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    falharLeiturasDoPerfil(a);
    const doc = a.w.document;
    const botao = doc.querySelector("#toggle-deliveries");
    botao.click();
    await settle();
    assert.equal(salvo.ativo, false);
    assert.equal(doc.querySelector("#account-message").textContent, "");
    assert.equal(botao.textContent, "Retomar entregas");
    assert.equal(doc.querySelector("#account-delivery-title").textContent, "Entregas pausadas");
    assert.equal(doc.querySelector("#pause-reason").hidden, false);
  } finally { a.close(); }
});

function segurarRpc(a: ReturnType<typeof app>, nome: string) {
  const rpc = a.client.rpc;
  let liberar = () => {};
  a.client.rpc = async (chamada: string, args: Payload) => {
    if (chamada === nome) await new Promise<void>((resolve) => { liberar = resolve; });
    return rpc(chamada, args);
  };
  return () => liberar();
}

Deno.test("resposta do desvincular que chega com a exclusão aberta fecha a confirmação", async () => {
  const salvo: Profile = { ...profile, telegram_chat_id: "123" };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao } = simularConfirmacaoModal(doc);
    const liberar = segurarRpc(a, "desvincular_meu_telegram");
    doc.querySelector("#unlink-telegram").click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    salvo.telegram_chat_id = null;
    doc.querySelector("#delete-account").click();
    assert.equal(confirmacao.open, true);
    liberar();
    await settle();
    assert.equal(doc.querySelector("#success-state").hidden, false);
    assert.equal(doc.querySelector("#account-state").hidden, true);
    assert.equal(confirmacao.open, false);
    assert.equal(confirmacao.hidden, true);
  } finally { a.close(); }
});

Deno.test("resposta da exclusão que chega com o desvincular aberto fecha a confirmação", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao } = simularConfirmacaoModal(doc);
    const liberar = segurarRpc(a, "excluir_minha_conta");
    doc.querySelector("#delete-account").click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    doc.querySelector("#unlink-telegram").click();
    assert.equal(confirmacao.open, true);
    liberar();
    await settle();
    assert.equal(doc.querySelector("#success-title").textContent, "As entregas pararam agora.");
    assert.equal(confirmacao.open, false);
    assert.equal(confirmacao.hidden, true);
  } finally { a.close(); }
});

Deno.test("editar perfil que termina de carregar com a confirmação aberta fecha o diálogo", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    const { confirmacao } = simularConfirmacaoModal(doc);
    const liberar = segurarProximaSessao(a);
    doc.querySelector("#edit-profile").click();
    await settle();
    doc.querySelector("#delete-account").click();
    assert.equal(confirmacao.open, true);
    liberar();
    await settle();
    assert.equal(doc.querySelector("#signup-form").hidden, false);
    assert.equal(confirmacao.open, false);
    assert.equal(confirmacao.hidden, true);
  } finally { a.close(); }
});

Deno.test("consulta do vínculo que falha depois da exclusão não troca o texto da exclusão", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    const liberar = segurarProximaSessao(a, new TypeError("Failed to fetch"));
    a.w.dispatchEvent(new a.w.Event("focus"));
    await settle();
    doc.querySelector("#success-account").click();
    await settle();
    doc.querySelector("#delete-account").click();
    doc.querySelector("#account-confirm-yes").click();
    await settle();
    assert.equal(doc.querySelector("#success-title").textContent, "As entregas pararam agora.");
    liberar();
    await settle();
    assert.match(doc.querySelector("#success-copy").textContent, /apagados definitivamente/);
  } finally { a.close(); }
});

function bancoQueRecusaOUpdate(a: ReturnType<typeof app>) {
  const from = a.client.from;
  a.client.from = (table: string) => {
    const query = from(table);
    let atualizando = false;
    query.update = () => {
      atualizando = true;
      return query;
    };
    const maybeSingle = query.maybeSingle;
    query.maybeSingle = async () => (atualizando ? { data: null } : maybeSingle());
    return query;
  };
}

Deno.test("pausar numa conta excluída em outro lugar mostra a exclusão sem o aviso das entregas", async () => {
  const salvo: Profile & { excluida_em?: string | null } = { ...profile, telegram_chat_id: "123" };
  const a = app({ session: { user }, savedProfile: salvo, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    bancoQueRecusaOUpdate(a);
    salvo.excluida_em = new Date().toISOString();
    salvo.telegram_chat_id = null;
    const doc = a.w.document;
    doc.querySelector("#toggle-deliveries").click();
    await settle();
    assert.equal(doc.querySelector("#account-delivery-title").textContent, "Exclusão agendada");
    assert.equal(doc.querySelector("#account-notice").textContent, "");
    assert.equal(doc.querySelector("#pause-reason").hidden, true);
  } finally { a.close(); }
});

Deno.test("recarregar em ?conta abre a conta sem passar pelo modal", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    const dialogo = a.w.document.querySelector("#signup-dialog");
    let chegouAAbrir = false;
    new a.w.MutationObserver((registros: { oldValue: string | null }[]) => {
      if (registros.some((registro) => registro.oldValue === null)) chegouAAbrir = true;
    }).observe(dialogo, { attributes: true, attributeFilter: ["open"], attributeOldValue: true });
    await settle();
    assert.equal(chegouAAbrir, false);
    assert.equal(dialogo.open, false);
    assert.equal(a.w.document.querySelector("#account-page").hidden, false);
  } finally { a.close(); }
});

Deno.test("Enter adiciona habilidade sem avançar e Continuar ainda avança", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" }, url: "https://radarestagio.com/?conta" });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();
    doc.querySelector("#next-step").click();
    const input = doc.querySelector("#custom-skill");
    input.value = "Rust";
    input.dispatchEvent(new a.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
    assert.ok(doc.querySelector("#selected-skills").textContent.includes("Rust"));
    assert.equal(input.value, "");
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    await settle();
  } finally { a.close(); }
});

Deno.test("habilidade digitada respeita o tamanho e a quantidade que o banco aceita", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    fill(a.w, false);
    doc.querySelector("#next-step").click();
    const input = doc.querySelector("#custom-skill");
    const digitar = (valor: string) => {
      input.value = valor;
      input.dispatchEvent(
        new a.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }),
      );
    };
    digitar("x".repeat(150));
    assert.deepEqual(habilidadesNaTela(a.w), ["x".repeat(100)]);
    for (let indice = 1; indice < 50; indice += 1) digitar(`habilidade-${indice}`);
    assert.equal(habilidadesNaTela(a.w).length, 50);
    digitar("passou-do-limite");
    assert.equal(habilidadesNaTela(a.w).length, 50);
    assert.ok(doc.querySelector("#erro-do-campo").textContent.includes("50 habilidades"));
    await settle();
  } finally {
    a.close();
  }
});

function digitarHabilidade(w: TestWindow, valor: string) {
  const campo = w.document.querySelector("#custom-skill");
  campo.value = valor;
  campo.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
}

function habilidadesNaTela(w: TestWindow): string[] {
  return [...w.document.querySelectorAll("#selected-skills button")].map((chip) =>
    chip.getAttribute("aria-label").replace(/^Remover /, "")
  );
}

async function habilidadesEnviadas(a: ReturnType<typeof app>): Promise<string[]> {
  const doc = a.w.document;
  doc.querySelector("#next-step").click();
  doc.querySelector("#next-step").click();
  doc.querySelector("#signup-form").dispatchEvent(new a.w.Event("submit", { cancelable: true }));
  await settle();
  return Array.from(called(a.calls, "signup")[1].options.data.cadastro_radar.perfil.habilidades);
}

Deno.test("corte de 100 caracteres não parte emoji nem deixa espaço que o envio apagaria", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    fill(a.w, false);
    a.w.document.querySelector("#next-step").click();
    await settle();
    digitarHabilidade(a.w, `${"c".repeat(99)}😀`);
    digitarHabilidade(a.w, `${"a".repeat(99)} ${"b".repeat(20)}`);

    const naTela = habilidadesNaTela(a.w);
    assert.deepEqual(naTela, [`${"c".repeat(99)}😀`, "a".repeat(99)]);
    const enviadas = await habilidadesEnviadas(a);
    assert.deepEqual(enviadas, naTela);
    for (const habilidade of enviadas) {
      assert.equal(/[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/.test(habilidade), false);
      assert.ok(Array.from(habilidade).length <= 100);
    }
  } finally {
    a.close();
  }
});

Deno.test("habilidade digitada com vírgula é uma só na tela e no envio", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    fill(a.w, false);
    a.w.document.querySelector("#next-step").click();
    digitarHabilidade(a.w, "Pacote Office (Word, Excel)");
    digitarHabilidade(a.w, "Python, SQL");

    assert.deepEqual(habilidadesNaTela(a.w), ["Pacote Office (Word, Excel)", "Python, SQL"]);
    assert.deepEqual(await habilidadesEnviadas(a), ["Pacote Office (Word, Excel)", "Python, SQL"]);
  } finally {
    a.close();
  }
});

Deno.test("cinquenta habilidades com vírgula cabem no envio e a 51ª é recusada na tela", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    fill(a.w, false);
    a.w.document.querySelector("#next-step").click();
    for (let indice = 0; indice < 50; indice += 1) digitarHabilidade(a.w, `A${indice}, B${indice}`);
    digitarHabilidade(a.w, "A50, B50");

    assert.equal(habilidadesNaTela(a.w).length, 50);
    assert.match(a.w.document.querySelector("#erro-do-campo").textContent, /no máximo 50 habilidades/);
    a.w.document.querySelector("#custom-skill").value = "";
    const naTela = habilidadesNaTela(a.w);
    assert.deepEqual(await habilidadesEnviadas(a), naTela);
  } finally {
    a.close();
  }
});

Deno.test("campos do cadastro limitam a digitação aos tetos que o banco aceita", async () => {
  const lerMigracao = (nome: string) =>
    Deno.readTextFile(new URL(`../../supabase/migrations/${nome}`, import.meta.url));
  const tetos = await lerMigracao("0025_tamanho_dos_textos_do_perfil.sql");
  const listaDeHabilidades = await lerMigracao("0018_habilidades_vazias.sql");
  const numero = (texto: string, padrao: RegExp) => {
    const achado = texto.match(padrao);
    assert.ok(achado, `${padrao} não encontrado`);
    return Number(achado[1]);
  };
  const constanteDoSite = (nome: string) => numero(script, new RegExp(`const ${nome} = (\\d+);`));
  const maisSubareasDeUmCurso = Math.max(
    ...areasJson.areas.map((area: { subareas: unknown[] }) => area.subareas.length),
  );
  const a = app();
  try {
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    const noSite: Record<string, number> = {
      curso: form.elements.curso.maxLength,
      cidade: form.elements.cidade.maxLength,
      habilidade: a.w.document.querySelector("#custom-skill").maxLength,
    };
    const noBanco: Record<string, number[]> = {
      curso: [
        numero(tetos, /char_length\(curso\) <= (\d+)/),
        numero(tetos, /btrim\(perfil->>'curso'\)\) not between 2 and (\d+)/),
        numero(tetos, /length\(perfil->>'curso'\) > (\d+)/),
      ],
      cidade: [
        numero(tetos, /char_length\(cidade\) <= (\d+)/),
        numero(tetos, /btrim\(perfil->>'cidade'\)\) not between 2 and (\d+)/),
        numero(tetos, /length\(perfil->>'cidade'\) > (\d+)/),
      ],
      habilidade: [
        numero(tetos, /todos_os_textos_cabem\(habilidades, (\d+)\)/),
        numero(tetos, /btrim\(item #>> '\{\}'\)\) not between 1 and (\d+)/),
        numero(tetos, /length\(item #>> '\{\}'\) > (\d+)/),
        constanteDoSite("TAMANHO_MAXIMO_DA_HABILIDADE"),
      ],
    };
    for (const campo of Object.keys(noBanco)) {
      for (const valor of noBanco[campo]) assert.equal(valor, noSite[campo], campo);
    }
    const maximoDeHabilidades = constanteDoSite("MAXIMO_DE_HABILIDADES");
    const listaNoCadastro = numero(tetos, /jsonb_array_length\(perfil->lista\) > (\d+)/);
    assert.equal(listaNoCadastro, maximoDeHabilidades);
    assert.equal(numero(listaDeHabilidades, /cardinality\(valor\) between 0 and (\d+)/), maximoDeHabilidades);
    const areasNoPerfil = numero(tetos, /cardinality\(areas_de_interesse\) <= (\d+)/);
    assert.ok(areasNoPerfil >= maisSubareasDeUmCurso, `o perfil aceita ${areasNoPerfil} áreas`);
    assert.ok(listaNoCadastro >= maisSubareasDeUmCurso, `o cadastro aceita ${listaNoCadastro} áreas`);
  } finally {
    a.close();
  }
});

Deno.test("atalho permite cadastrar com habilidades vazias e preserva a escolha ao voltar", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w, false);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    assert.equal(doc.querySelector("#continue-without-skills").hidden, false);
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    doc.querySelector("#continue-without-skills").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    assert.deepEqual(habilidadesNaTela(a.w), []);
    doc.querySelector("#previous-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const signup = called(a.calls, "signup")[1];
    assert.deepEqual(Array.from(signup.options.data.cadastro_radar.perfil.habilidades), []);
    const evento = a.calls.find(([name, , payload]) =>
      name === "insert" && (payload as Payload)?.nome === "etapa_habilidades_concluida"
    );
    assert.equal(JSON.stringify(evento?.[2]).includes("continuarSemHabilidades"), false);
    await settle();
  } finally {
    a.close();
  }
});

Deno.test("edição de perfil salvo sem habilidades libera a etapa e remover a última exige escolha nova", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, habilidades: [], telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    doc.querySelector("#previous-step").click();
    doc.querySelector('[data-skill="Python"]').click();
    doc.querySelector('[data-skill="Python"]').click();
    assert.equal(doc.querySelector("#continue-without-skills").hidden, false);
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "3");
    doc.querySelector("#continue-without-skills").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    await settle();
  } finally {
    a.close();
  }
});

Deno.test("erro ao salvar perfil iniciante mantém dados e a opção de habilidades vazias", async () => {
  const a = app();
  try {
    await settle();
    a.client.auth.signUp = async () => ({ data: { session: { user } } });
    a.client.rpc = async () => ({ error: new Error("indisponível") });
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w, false);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#continue-without-skills").click();
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    assert.equal(form.elements.cidade.value, "Recife, PE");
    assert.deepEqual(habilidadesNaTela(a.w), []);
    doc.querySelector("#previous-step").click();
    doc.querySelector("#next-step").click();
    assert.equal(doc.querySelector(".form-step.is-active").dataset.step, "4");
    await settle();
  } finally {
    a.close();
  }
});


Deno.test("as areas de interesse acompanham o curso digitado", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    form.elements.curso.value = "Direito";
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    await settle();
    const valores = [...doc.querySelectorAll('input[name="areas"]')].map((c) => c.value);
    assert.equal(doc.querySelector("#campo-areas").hidden, false);
    assert.equal(valores.includes("direito_contencioso"), true);
    assert.equal(valores.includes("desenvolvimento_web"), false);
  } finally { a.close(); }
});

Deno.test("curso de computacao continua vendo as areas de tecnologia", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    fill(a.w);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    await settle();
    const valores = [...doc.querySelectorAll('input[name="areas"]')].map((c) => c.value);
    assert.equal(valores.includes("desenvolvimento_web"), true);
    assert.equal(valores.includes("direito_contencioso"), false);
  } finally { a.close(); }
});

Deno.test("curso sem area conhecida esconde o campo de areas", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    form.elements.curso.value = "Curso Que Ninguem Tem";
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    await settle();
    assert.equal(doc.querySelector("#campo-areas").hidden, true);
    assert.equal(doc.querySelectorAll('input[name="areas"]').length, 0);
  } finally { a.close(); }
});


for (const [curso, subarea] of [
  ["Medicina Veterinária", null],
  ["Design de Interiores", null],
  ["Tecnologia em Gestão Financeira", "financeiro"],
  ["Gestão de Recursos Humanos", "recrutamento_e_selecao"],
  ["Bacharelado em Ciência da Computação", "desenvolvimento_web"],
]) {
  Deno.test(`áreas respeitam o nome completo de ${curso}`, async () => {
    const a = app();
    try {
      await settle();
      a.w.document.querySelector(".js-open-signup").click();
      await settle();
      const doc = a.w.document;
      const form = fill(a.w);
      form.elements.curso.value = curso;
      for (let passo = 0; passo < 3; passo++) doc.querySelector("#next-step").click();
      await settle();
      const valores = [...doc.querySelectorAll('input[name="areas"]')].map((c) => c.value);
      if (subarea === null) assert.deepEqual(valores, []);
      else assert.ok(valores.includes(subarea));
    } finally { a.close(); }
  });
}


Deno.test("formacao e sinonimo no curso digitado ainda montam as areas certas", async () => {
  for (const [curso, esperada, indevida] of [
    ["Cursando Direito", "direito_contencioso", "desenvolvimento_web"],
    ["Estudante de Ciências Econômicas", "financeiro", "direito_contencioso"],
  ]) {
    const a = app();
    try {
      await settle();
      a.w.document.querySelector(".js-open-signup").click();
      await settle();
      const doc = a.w.document;
      const form = fill(a.w);
      form.elements.curso.value = curso;
      doc.querySelector("#next-step").click();
      doc.querySelector("#next-step").click();
      doc.querySelector("#next-step").click();
      await settle();
      const valores = [...doc.querySelectorAll('input[name="areas"]')].map((c) => c.value);
      assert.equal(valores.includes(esperada), true, curso);
      assert.equal(valores.includes(indevida), false, curso);
    } finally { a.close(); }
  }
});


Deno.test("catalogo indisponivel na edicao preserva as areas salvas em vez de apagar", async () => {
  const a = app({
    session: { user },
    savedProfile: {
      ...profile,
      telegram_chat_id: "123",
      areas_de_interesse: ["desenvolvimento_web"],
    } as unknown as Profile,
  });
  try {
    a.w.fetch = async () => {
      throw new Error("offline");
    };
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.cidade.value = "Natal, RN";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[2].cidade, "Natal, RN");
    assert.deepEqual(Array.from(update[2].areas_de_interesse as string[]), ["desenvolvimento_web"]);
  } finally {
    a.close();
  }
});

Deno.test("trocar o curso na edicao descarta as areas do curso antigo no payload", async () => {
  const a = app({
    session: { user },
    savedProfile: {
      ...profile,
      telegram_chat_id: "123",
      areas_de_interesse: ["desenvolvimento_web"],
    } as unknown as Profile,
  });
  try {
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.curso.value = "Direito";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[2].curso, "Direito");
    assert.deepEqual(Array.from(update[2].areas_de_interesse as string[]), []);
  } finally {
    a.close();
  }
});


Deno.test("habilidades sugeridas acompanham o curso digitado", async () => {
  for (const [curso, esperada, indevida] of [
    ["Direito", "Redação", "Python"],
    ["Computação", "Python", "Redação"],
    ["Curso Que Ninguem Tem", null, "Python"],
  ] as [string, string | null, string][]) {
    const a = app();
    try {
      await settle();
      a.w.document.querySelector(".js-open-signup").click();
      await settle();
      const doc = a.w.document;
      const form = fill(a.w, Boolean(esperada));
      form.elements.curso.value = curso;
      doc.querySelector("#next-step").click();
      doc.querySelector("#next-step").click();
      await settle();
      const sugeridas = [...doc.querySelectorAll("#skill-picker [data-skill]")].map((b) => b.dataset.skill);
      if (esperada) assert.equal(sugeridas.includes(esperada), true, curso);
      else assert.deepEqual(sugeridas, []);
      assert.equal(sugeridas.includes(indevida), false, curso);
      if (!esperada) assert.equal(doc.querySelector("#continue-without-skills").hidden, false);
    } finally { a.close(); }
  }
});

Deno.test("falha do catálogo limpa sugestões sem apagar habilidade escolhida", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    fill(a.w, false);
    a.w.fetch = async () => { throw new Error("offline"); };
    doc.querySelector("#next-step").click();
    await settle();
    const input = doc.querySelector("#custom-skill");
    input.value = "Python";
    input.dispatchEvent(new a.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
    await a.w.montarHabilidadesDoCurso();
    assert.deepEqual([...doc.querySelectorAll("#skill-picker [data-skill]")], []);
    assert.deepEqual(habilidadesNaTela(a.w), ["Python"]);
    assert.equal(doc.querySelector("#skills-catalog-notice").hidden, false);
    assert.equal(doc.querySelector("#continue-without-skills").hidden, true);
  } finally {
    a.close();
  }
});

Deno.test("resposta assíncrona de curso anterior não substitui o curso atual", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const form = fill(a.w, false);
    form.elements.curso.value = "Direito";
    a.w.catalogoDeAreas = null;
    const respostas: ((resposta: { ok: boolean; json: () => Promise<unknown> }) => void)[] = [];
    a.w.fetch = () => new Promise((resolve) => respostas.push(resolve));
    const primeira = a.w.montarHabilidadesDoCurso();
    form.elements.curso.value = "Computação";
    const segunda = a.w.montarHabilidadesDoCurso();
    respostas[1]({ ok: true, json: async () => areasJson });
    await segunda;
    respostas[0]({ ok: true, json: async () => areasJson });
    await primeira;
    const sugeridas = [...a.w.document.querySelectorAll("#skill-picker [data-skill]")].map((b) => b.dataset.skill);
    assert.equal(sugeridas.includes("Python"), true);
    assert.equal(sugeridas.includes("Redação"), false);
  } finally {
    a.close();
  }
});

Deno.test("sair da conta nao deixa as areas de interesse da pessoa anterior no proximo cadastro", async () => {
  const a = app({
    session: { user },
    savedProfile: {
      ...profile,
      telegram_chat_id: "123",
      areas_de_interesse: ["dados_ia"],
    } as unknown as Profile,
  });
  try {
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    a.w.document.querySelector("#logout-account").click();
    await settle();
    a.w.setAuthMode("signup");
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    fill(a.w);
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    await settle();
    const marcadas = [...doc.querySelectorAll('input[name="areas"]:checked')].map((c) => c.value);
    assert.deepEqual(Array.from(marcadas), []);
  } finally {
    a.close();
  }
});

Deno.test("preferências são registradas ao avançar, antes de criar conta", async () => {
  const a = app();
  try {
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const form = fill(a.w);
    const eventos = () =>
      a.calls.filter(([name, , payload]) =>
        name === "insert" &&
        (payload as Payload)?.nome === "etapa_preferencias_concluida"
      );
    a.w.document.querySelector("#next-step").click();
    a.w.document.querySelector("#next-step").click();
    await settle();
    form.elements.cidade.value = "";
    a.w.document.querySelector("#next-step").click();
    await settle();
    assert.equal(eventos().length, 0);
    form.elements.cidade.value = "Recife, PE";
    form.elements.aceitou_termos.checked = false;
    a.w.document.querySelector("#next-step").click();
    await settle();
    assert.equal(eventos().length, 1);
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    form.elements.aceitou_termos.checked = true;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(eventos().length, 1);
  } finally {
    a.close();
  }
});

Deno.test("login não emite conclusão de preferências e edição emite ao salvar", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
    url: "https://radarestagio.com/?conta",
  });
  try {
    await settle();
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    a.w.document.querySelector("#next-step").click();
    a.w.document.querySelector("#next-step").click();
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(
      a.calls.filter(([name, , payload]) =>
        name === "insert" &&
        (payload as Payload)?.nome === "etapa_preferencias_concluida"
      ).length,
      1,
    );
  } finally {
    a.close();
  }
  const b = app({ savedProfile: profile });
  try {
    fill(b.w);
    b.w.document.querySelector("#toggle-auth-mode").click();
    b.w.document.querySelector("#signup-form").dispatchEvent(
      new b.w.Event("submit", { cancelable: true }),
    );
    await settle();
    assert.equal(b.calls.filter(([name]) => name === "login").length, 1);
    assert.equal(
      b.calls.filter(([name, , payload]) =>
        name === "insert" &&
        (payload as Payload)?.nome === "etapa_preferencias_concluida"
      ).length,
      0,
    );
  } finally {
    b.close();
  }
});

Deno.test("curso escrito como tecnologia da informacao abre as areas de computacao", async () => {
  const a = app({ session: null, savedProfile: null });
  try {
    await settle();
    a.w.setAuthMode("signup");
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    form.elements.curso.value = "Bacharelado em Tecnologia da Informação";
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    await settle();
    assert.equal(doc.querySelector("#campo-areas").hidden, false);
    assert.ok(doc.querySelectorAll('input[name="areas"]').length > 0);
  } finally {
    a.close();
  }
});

Deno.test("normalizacao de curso do site bate com a do backend", async () => {
  const a = app({ session: null, savedProfile: null });
  try {
    await settle();
    const catalogo = JSON.parse(
      Deno.readTextFileSync(new URL("../../web/assets/areas.json", import.meta.url)),
    );
    const esperado = JSON.parse(
      Deno.readTextFileSync(new URL("../fixtures/cursos_normalizados.json", import.meta.url)),
    );
    for (const [curso, [normalizado, area]] of Object.entries(esperado) as [string, [string, string | null]][]) {
      assert.equal(a.w.normalizarCurso(curso, catalogo), normalizado, curso);
      assert.equal(a.w.areaDoCurso(curso, catalogo)?.nome ?? null, area, curso);
    }
  } finally {
    a.close();
  }
});

Deno.test("editar o perfil preserva o rótulo e o indicador de envio do botão", async () => {
  const a = app({ session: { user }, savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    await settle();
    const doc = a.w.document;
    doc.querySelector("#edit-profile").click();
    await settle();

    assert.equal(doc.querySelector("#submit-label").textContent, "Salvar alterações");
    assert.ok(doc.querySelector("#submit-profile .button-spinner"));

    doc.querySelector("#logout-account").click();
    await settle();
    a.w.setAuthMode("signup");

    assert.equal(doc.querySelector("#submit-label").textContent, "Criar conta e continuar");
  } finally { a.close(); }
});

Deno.test("confirmar o cadastro leva a barra a 100% enquanto a conta é criada", async () => {
  const a = app();
  let liberarCadastro = () => {};
  const cadastroLiberado = new Promise<void>((resolve) => { liberarCadastro = resolve; });
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    const progresso = () => [
      doc.querySelector("#progress-percent").textContent,
      doc.querySelector("#progress-track").getAttribute("aria-valuenow"),
      doc.querySelector("#progress-bar").style.width,
    ];
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    assert.deepEqual(progresso(), ["75%", "75", "75%"]);
    a.client.auth.signUp = async (args: Signup) => {
      a.calls.push(["signup", args]);
      await cadastroLiberado;
      return { data: { session: null } };
    };
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.deepEqual(progresso(), ["100%", "100", "100%"]);
    liberarCadastro();
    await settle();
  } finally { a.close(); }
});

Deno.test("cadastro recusado devolve a barra ao último passo", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const form = fill(a.w);
    const progresso = () => [
      doc.querySelector("#progress-percent").textContent,
      doc.querySelector("#progress-track").getAttribute("aria-valuenow"),
      doc.querySelector("#progress-bar").style.width,
    ];
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    doc.querySelector("#next-step").click();
    a.client.auth.signUp = async (args: Signup) => {
      a.calls.push(["signup", args]);
      return { data: { session: null }, error: new Error("falha simulada") };
    };
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(form.hidden, false);
    assert.deepEqual(progresso(), ["75%", "75", "75%"]);
  } finally { a.close(); }
});

async function abrirPreferencias(a: ReturnType<typeof app>) {
  await settle();
  a.w.document.querySelector(".js-open-signup").click();
  await settle();
  const form = fill(a.w);
  a.w.document.querySelector("#next-step").click();
  a.w.document.querySelector("#next-step").click();
  form.elements.cidade.focus();
  await settle();
  return form;
}

async function digitarCidade(a: ReturnType<typeof app>, texto: string) {
  const campo = a.w.document.querySelector("#cidade");
  campo.value = texto;
  campo.dispatchEvent(new a.w.Event("input", { bubbles: true }));
  await settle();
  return [...a.w.document.querySelectorAll("#lista-de-cidades [data-cidade]")].map(
    (opcao) => opcao.dataset.cidade,
  );
}

function teclar(a: ReturnType<typeof app>, key: string) {
  a.w.document.querySelector("#cidade").dispatchEvent(
    new a.w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }),
  );
}

Deno.test("cidade sugere municípios reais conforme a pessoa digita, sem exigir acento", async () => {
  const a = app();
  try {
    await abrirPreferencias(a);
    const rio = await digitarCidade(a, "rio");
    assert.equal(rio[0], "Rio de Janeiro, RJ");
    assert.ok(rio.length > 1 && rio.length <= 8);
    assert.ok(rio.every((cidade) => cidade.startsWith("Rio")));
    assert.equal(a.w.document.querySelector("#cidade").getAttribute("aria-expanded"), "true");
    assert.equal((await digitarCidade(a, "niteroi"))[0], "Niterói, RJ");
    assert.equal((await digitarCidade(a, "sao paulo"))[0], "São Paulo, SP");
    assert.deepEqual(await digitarCidade(a, "cidade que nao existe"), []);
    assert.equal(
      a.w.document.querySelector("#lista-de-cidades").textContent,
      "Nenhuma cidade encontrada. Confira a grafia.",
    );
  } finally {
    a.close();
  }
});

Deno.test("cidade com apóstrofo é achada com apóstrofo curvo ou acento agudo", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    const digitados = ["santa barbara d’oeste", "santa barbara d‘oeste", "santa barbara dʼoeste"];
    for (const digitado of [...digitados, "santa barbara d´oeste"]) {
      assert.equal((await digitarCidade(a, digitado))[0], "Santa Bárbara d'Oeste, SP");
    }
    form.elements.cidade.value = "Sant’Ana do Livramento";
    a.w.document.querySelector("#next-step").click();
    assert.equal(form.elements.cidade.value, "Sant'Ana do Livramento, RS");
  } finally {
    a.close();
  }
});

Deno.test("clicar numa sugestão preenche a cidade e fecha a lista", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    await digitarCidade(a, "curit");
    a.w.document.querySelector('#lista-de-cidades [data-cidade="Curitiba, PR"]').click();
    assert.equal(form.elements.cidade.value, "Curitiba, PR");
    assert.equal(a.w.document.querySelector("#lista-de-cidades").hidden, true);
    assert.equal(form.elements.cidade.getAttribute("aria-expanded"), "false");
  } finally {
    a.close();
  }
});

Deno.test("setinha abre as maiores cidades com o campo vazio e fecha no segundo clique", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    form.elements.cidade.value = "";
    const setinha = a.w.document.querySelector("#mostrar-cidades");
    setinha.click();
    await settle();
    const opcoes = [...a.w.document.querySelectorAll("#lista-de-cidades [data-cidade]")];
    assert.deepEqual(
      opcoes.slice(0, 3).map((opcao) => opcao.dataset.cidade),
      ["São Paulo, SP", "Rio de Janeiro, RJ", "Brasília, DF"],
    );
    assert.equal(setinha.getAttribute("aria-expanded"), "true");
    setinha.click();
    assert.equal(a.w.document.querySelector("#lista-de-cidades").hidden, true);
    assert.equal(setinha.getAttribute("aria-expanded"), "false");
  } finally {
    a.close();
  }
});

Deno.test("setas escolhem a sugestão e Enter confirma sem avançar o passo", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    await digitarCidade(a, "rio");
    teclar(a, "ArrowDown");
    teclar(a, "ArrowDown");
    teclar(a, "ArrowUp");
    const destacada = a.w.document.querySelector('#lista-de-cidades [aria-selected="true"]');
    assert.equal(destacada.dataset.cidade, "Rio de Janeiro, RJ");
    assert.equal(form.elements.cidade.getAttribute("aria-activedescendant"), destacada.id);
    teclar(a, "Enter");
    assert.equal(form.elements.cidade.value, "Rio de Janeiro, RJ");
    assert.equal(a.w.document.querySelector('.form-step[data-step="4"]').classList.contains("is-active"), true);
    await digitarCidade(a, "rio");
    teclar(a, "Escape");
    assert.equal(a.w.document.querySelector("#lista-de-cidades").hidden, true);
    assert.equal(a.w.document.querySelector("#signup-dialog").open, true);
  } finally {
    a.close();
  }
});

Deno.test("cidade fora da lista não avança e explica o que fazer", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    form.elements.cidade.value = "Cidade Inventada";
    a.w.document.querySelector("#next-step").click();
    assert.equal(
      a.w.document.querySelector("#erro-do-campo").textContent,
      "Escolha sua cidade na lista, como Rio de Janeiro, RJ.",
    );
    assert.equal(form.elements.cidade.getAttribute("aria-invalid"), "true");
    assert.equal(a.w.document.querySelector('.form-step[data-step="4"]').classList.contains("is-active"), true);
    form.elements.cidade.value = "Bom Jesus";
    a.w.document.querySelector("#next-step").click();
    assert.equal(
      a.w.document.querySelector("#erro-do-campo").textContent,
      "Existe mais de uma cidade com esse nome. Escolha a do seu estado na lista.",
    );
  } finally {
    a.close();
  }
});

Deno.test("cidade escrita sem acento ou sem estado é salva no formato da lista", async () => {
  const a = app();
  try {
    const form = await abrirPreferencias(a);
    form.elements.cidade.value = "niteroi";
    a.w.document.querySelector("#next-step").click();
    assert.equal(form.elements.cidade.value, "Niterói, RJ");
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const [, signup] = called(a.calls, "signup");
    assert.equal(signup.options.data.cadastro_radar.perfil.cidade, "Niterói, RJ");
  } finally {
    a.close();
  }
});

Deno.test("envio direto recusa cidade fora da lista mesmo sem a lista carregada antes", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const form = fill(a.w);
    form.elements.cidade.value = "Cidade Inventada";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.some(([name]) => name === "signup"), false);
    assert.equal(
      a.w.document.querySelector("#erro-do-campo").textContent,
      "Escolha sua cidade na lista, como Rio de Janeiro, RJ.",
    );
    assert.equal(a.w.document.querySelector('.form-step[data-step="4"]').classList.contains("is-active"), true);
  } finally {
    a.close();
  }
});

Deno.test("lista de cidades fora do ar avisa e não bloqueia o cadastro", async () => {
  const a = app();
  try {
    a.w.fetch = async (caminho: string) => ({
      ok: String(caminho).includes("areas.json"),
      json: async () => areasJson,
    });
    const form = await abrirPreferencias(a);
    assert.equal(a.w.document.querySelector("#cities-catalog-notice").hidden, false);
    form.elements.cidade.value = "Recife, PE";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const [, signup] = called(a.calls, "signup");
    assert.equal(signup.options.data.cadastro_radar.perfil.cidade, "Recife, PE");
  } finally {
    a.close();
  }
});

Deno.test("perfil antigo sem estado na cidade é corrigido ao salvar a edição", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, cidade: "Rio de Janeiro", telegram_chat_id: "123" },
  });
  try {
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const update = called(a.calls, "update");
    assert.equal(update[2].cidade, "Rio de Janeiro, RJ");
  } finally {
    a.close();
  }
});

function captchaComToken(a: ReturnType<typeof app>, token: string) {
  let widget: { callback: (valor: string) => void } | undefined;
  a.w.turnstile = {
    render: (_: string, options: { callback: (valor: string) => void }) => {
      widget = options;
      return 1;
    },
    reset: () => {},
  };
  a.w.radarCaptchaReady();
  assert.ok(widget);
  widget.callback(token);
}

function enviarAssistencia(a: ReturnType<typeof app>) {
  a.w.document.querySelector("#assistance-form").dispatchEvent(
    new a.w.Event("submit", { cancelable: true }),
  );
}

Deno.test("CAPTCHA acompanha o reenvio da confirmação", async () => {
  const a = app({ key: "chave-publica" });
  try {
    captchaComToken(a, "token-do-reenvio");
    a.w.showAssistance("resend", user.email);
    enviarAssistencia(a);
    await settle();
    assert.equal(called(a.calls, "resend")[1].options?.captchaToken, "token-do-reenvio");
  } finally {
    a.close();
  }
});

Deno.test("CAPTCHA acompanha o pedido de recuperação de senha", async () => {
  const a = app({ key: "chave-publica" });
  try {
    captchaComToken(a, "token-da-recuperacao");
    a.w.showAssistance("reset", user.email);
    enviarAssistencia(a);
    await settle();
    assert.equal(called(a.calls, "reset")[2].captchaToken, "token-da-recuperacao");
  } finally {
    a.close();
  }
});
