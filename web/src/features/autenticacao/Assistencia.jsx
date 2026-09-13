import { BotaoDeSenha } from "../../components/BotaoDeSenha.jsx";

const TEXTOS_DA_ASSISTENCIA = {
  resend: {
    titulo: "Confirme seu e-mail",
    copy: "Abra o link em qualquer aparelho. Se precisar, corrija o endereço e solicite outro link.",
    enviar: "Reenviar confirmação",
  },
  reset: {
    titulo: "Recuperar senha",
    copy: "Informe o e-mail da sua conta para receber um link de recuperação.",
    enviar: "Enviar link de recuperação",
  },
  "new-password": {
    titulo: "Defina sua nova senha",
    copy: "Use uma senha com pelo menos 8 caracteres.",
    enviar: "Salvar nova senha",
  },
};

export function Assistencia({ estado, controlador }) {
  const { assistencia } = estado;
  const textos = TEXTOS_DA_ASSISTENCIA[assistencia.modo] ?? { titulo: "Confirme seu e-mail", copy: "", enviar: "Reenviar confirmação" };
  const definindoSenha = assistencia.modo === "new-password";
  const aguardandoReenvio = assistencia.modo === "resend" && assistencia.restante > 0;
  const mensagem = estado.tela === "assistencia" ? estado.mensagem : null;

  return (
    <section id="auth-assistance" hidden={estado.tela !== "assistencia"} aria-labelledby="assistance-title">
      <h2 id="assistance-title">{textos.titulo}</h2>
      <p id="assistance-copy">{textos.copy}</p>
      <form id="assistance-form" onSubmit={controlador.enviarAssistencia}>
        <label className="field" id="assistance-email-field" hidden={definindoSenha}>
          <span>E-mail</span>
          <input
            id="assistance-email"
            type="email"
            autoComplete="email"
            spellCheck={false}
            required={!definindoSenha}
            value={assistencia.email}
            onChange={(evento) => controlador.alterarAssistencia("email", evento.target.value)}
          />
        </label>
        <div className="field" id="assistance-password-field" hidden={!definindoSenha}>
          <label htmlFor="assistance-password">Nova senha</label>
          <span className="password-field">
            <input
              id="assistance-password"
              type={estado.senhasVisiveis["assistance-password"] ? "text" : "password"}
              autoComplete="new-password"
              minLength={8}
              required={definindoSenha}
              value={assistencia.senha}
              onChange={(evento) => controlador.alterarAssistencia("senha", evento.target.value)}
            />
            <BotaoDeSenha
              alvo="assistance-password"
              visivel={Boolean(estado.senhasVisiveis["assistance-password"])}
              aoAlternar={() => controlador.alternarSenha("assistance-password")}
            />
          </span>
        </div>
        <p className="form-message" id="assistance-message" role="alert">
          {mensagem?.tom === "erro" ? mensagem.texto : ""}
        </p>
        <p className="form-message form-message-aviso" id="assistance-notice" role="status">
          {mensagem?.tom === "aviso" ? mensagem.texto : ""}
        </p>
        <button
          className="button button-primary"
          id="assistance-submit"
          type="submit"
          disabled={assistencia.ocupada || aguardandoReenvio}
          aria-busy={assistencia.ocupada}
        >
          {aguardandoReenvio ? `Reenviar em ${assistencia.restante}s` : textos.enviar}
        </button>
      </form>
      <button className="button button-ghost" id="assistance-back" type="button" onClick={controlador.voltarParaEntrar}>
        Voltar para entrar
      </button>
    </section>
  );
}
