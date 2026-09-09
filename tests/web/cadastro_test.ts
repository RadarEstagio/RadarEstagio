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
  w.fetch = async (caminho: string) => ({
    ok: String(caminho).includes("areas.json"),
    json: async () => areasJson,
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

Deno.test("cadastro exige aceite e envia perfil e sessão sem guardar senha localmente", async () => {
  const a = app();
  try {
    const form = fill(a.w);
    form.elements.aceitou_termos.checked = false;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
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

Deno.test("cadastro começa pela conta e só depois pede o perfil", async () => {
  const a = app();
  try {
    await settle();
    a.w.document.querySelector(".js-open-signup").click();
    await settle();
    const doc = a.w.document;
    const passoAtivo = () =>
      doc.querySelector(".form-step.is-active").dataset.step;
    assert.equal(passoAtivo(), "1");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 1 de 4");
    assert.equal(doc.querySelector("#previous-step").hidden, true);
    assert.equal(doc.querySelector("#submit-profile").hidden, true);
    doc.querySelector("#next-step").click();
    assert.equal(passoAtivo(), "1");
    const form = doc.querySelector("#signup-form");
    form.elements.email.value = user.email;
    form.elements.senha.value = "uma-senha-forte";
    form.elements.aceitou_termos.checked = true;
    doc.querySelector("#next-step").click();
    assert.equal(passoAtivo(), "2");
    assert.equal(doc.querySelector("#progress-label").textContent, "Etapa 2 de 4");
    assert.equal(doc.querySelector("#previous-step").hidden, false);
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
    ["Curso Que Ninguem Tem", "Excel", "Python"],
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
      await settle();
      const sugeridas = [...doc.querySelectorAll("#skill-picker [data-skill]")].map((b) => b.dataset.skill);
      assert.equal(sugeridas.includes(esperada), true, curso);
      assert.equal(sugeridas.includes(indevida), false, curso);
    } finally { a.close(); }
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
