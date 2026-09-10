import assert from "assert";
import { JSDOM } from "jsdom";

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
      };
    };
  };
}
type Call =
  | ["signup", Signup]
  | ["login", { email: string; password: string }]
  | ["resend", { email: string }]
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
  }: {
    session?: Session | null;
    savedProfile?: Profile | null;
    url?: string;
    key?: string;
  } = {},
) {
  const dom = new JSDOM(html, { url, runScripts: "outside-only" });
  const w = dom.window;
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
      getSession: async () => ({ data: { session } }),
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
      resend: async (args: { email: string }) => {
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
        maybeSingle: async () => ({ data: savedProfile }),
        single: async () => ({ data: savedProfile }),
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
    assert.equal(form.elements.habilidades.value, "Python");
    assert.equal(form.elements.cidade.value, "Recife, PE");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 4 de 4");
    await settle();
  } finally { a.close(); }
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
    const form = fill(a.w, false);
    doc.querySelector("#next-step").click();
    const input = doc.querySelector("#custom-skill");
    const digitar = (valor: string) => {
      input.value = valor;
      input.dispatchEvent(
        new a.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }),
      );
    };
    digitar("x".repeat(150));
    assert.equal(form.elements.habilidades.value.length, 100);
    for (let indice = 1; indice < 50; indice += 1) digitar(`habilidade-${indice}`);
    assert.equal(form.elements.habilidades.value.split(",").length, 50);
    digitar("passou-do-limite");
    assert.equal(form.elements.habilidades.value.split(",").length, 50);
    assert.ok(doc.querySelector("#erro-do-campo").textContent.includes("50 habilidades"));
    await settle();
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
    assert.equal(form.elements.habilidades.value, "");
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
    assert.equal(form.elements.habilidades.value, "");
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
    const form = fill(a.w, false);
    a.w.fetch = async () => { throw new Error("offline"); };
    doc.querySelector("#next-step").click();
    await settle();
    const input = doc.querySelector("#custom-skill");
    input.value = "Python";
    input.dispatchEvent(new a.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
    await a.w.montarHabilidadesDoCurso();
    assert.deepEqual([...doc.querySelectorAll("#skill-picker [data-skill]")], []);
    assert.equal(form.elements.habilidades.value, "Python");
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
