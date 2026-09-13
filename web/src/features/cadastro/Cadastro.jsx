import { BotaoDeSenha } from "../../components/BotaoDeSenha.jsx";
import { ErroDoCampo, atributosDeErro } from "../../components/ErroDoCampo.jsx";
import { CampoDeCidade } from "./CampoDeCidade.jsx";

const TEXTOS_DA_CONTA = {
  signup: {
    titulo: "Comece pela sua conta",
    ajuda: "O e-mail dá acesso à conta e confirma o cadastro. A senha protege seus dados.",
    senha: "Pelo menos 8 caracteres",
    pergunta: "Já possui uma conta? ",
    alternar: "Entrar",
  },
  login: {
    titulo: "Entre na sua conta",
    ajuda: "Use o e-mail e a senha que você cadastrou. Seu perfil continua salvo.",
    senha: "Sua senha",
    pergunta: "Ainda não possui uma conta? ",
    alternar: "Criar conta",
  },
};

const PERIODOS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

const MODALIDADES = [
  ["remoto", "Remoto"],
  ["hibrido", "Híbrido"],
  ["presencial", "Presencial"],
  ["indiferente", "Indiferente"],
];

function rotuloDoPeriodo(periodo) {
  return periodo === 10 ? "10º período ou mais" : `${periodo}º período`;
}

function rotuloDoEnvio(estado) {
  if (estado.edicao) return "Salvar alterações";
  return estado.modo === "signup" ? "Criar conta e continuar" : "Entrar e continuar";
}

export function Cadastro({ estado, controlador }) {
  const { campos, erro, modo, edicao, credenciaisOcultas, passo, passos } = estado;
  const textos = TEXTOS_DA_CONTA[modo];
  const posicao = passos.indexOf(passo);
  const consentimentoVisivel = modo === "signup" && !edicao;
  const classeDoPasso = (numero) => `form-step${passo === numero ? " is-active" : ""}`;
  const alterarTexto = (nome) => (evento) => controlador.alterarCampo(nome, evento.target.value);
  const alterarMarcacao = (nome) => (evento) => controlador.alterarCampo(nome, evento.target.checked);
  const mensagemDoFormulario = estado.tela === "assistencia" ? null : estado.mensagem;

  return (
    <form id="signup-form" noValidate hidden={estado.tela !== "formulario"} onSubmit={controlador.enviarCadastro}>
      <fieldset className={classeDoPasso(1)} data-step="1">
        <legend id="conta-titulo">{textos.titulo}</legend>
        <p className="step-help" id="conta-ajuda">{textos.ajuda}</p>
        <div className="field-grid" id="credenciais" hidden={credenciaisOcultas}>
          <label className="field field-full">
            <span>E-mail</span>
            <input
              name="email"
              type="email"
              autoComplete="email"
              spellCheck={false}
              required={!credenciaisOcultas}
              placeholder="voce@email.com"
              value={campos.email}
              onChange={alterarTexto("email")}
              {...atributosDeErro(erro, "email")}
            />
            <ErroDoCampo erro={erro} campo="email" />
          </label>
          <div className="field field-full">
            <label htmlFor="signup-password">Senha</label>
            <span className="password-field">
              <input
                id="signup-password"
                name="senha"
                type={estado.senhasVisiveis.senha ? "text" : "password"}
                autoComplete={modo === "signup" ? "new-password" : "current-password"}
                minLength={8}
                required={!credenciaisOcultas}
                placeholder={textos.senha}
                value={campos.senha}
                onChange={alterarTexto("senha")}
                {...atributosDeErro(erro, "senha")}
              />
              <BotaoDeSenha
                alvo="senha"
                visivel={Boolean(estado.senhasVisiveis.senha)}
                aoAlternar={() => controlador.alternarSenha("senha")}
              />
            </span>
            <ErroDoCampo erro={erro} campo="senha" />
          </div>
        </div>
        <div id="signup-consent" className="consent-fields" hidden={!consentimentoVisivel}>
          <label>
            <input
              type="checkbox"
              name="aceitou_termos"
              required={consentimentoVisivel}
              checked={campos.aceitou_termos}
              onChange={alterarMarcacao("aceitou_termos")}
              {...atributosDeErro(erro, "aceitou_termos")}
            />{" "}
            <span>
              Aceito os <a href="termos.html" target="_blank" rel="noopener">Termos de Uso</a> e a{" "}
              <a href="privacidade.html" target="_blank" rel="noopener">Política de Privacidade</a> (abrem em outra aba).
            </span>
          </label>
          <ErroDoCampo erro={erro} campo="aceitou_termos" />
          <label>
            <input
              type="checkbox"
              name="aceita_emails"
              checked={campos.aceita_emails}
              onChange={alterarMarcacao("aceita_emails")}
            />{" "}
            <span>Quero receber e-mails ocasionais do Radar.</span>
          </label>
        </div>
        <div className="auth-help" hidden={credenciaisOcultas}>
          <button type="button" id="forgot-password" onClick={() => controlador.mostrarAssistencia("reset")}>
            Esqueci minha senha
          </button>
          <button type="button" id="open-resend" onClick={() => controlador.mostrarAssistencia("resend")}>
            Não recebi a confirmação
          </button>
        </div>
        <p className="account-switch" id="account-switch" hidden={credenciaisOcultas}>
          {textos.pergunta}
          <button
            type="button"
            id="toggle-auth-mode"
            onClick={() => controlador.definirModo(modo === "signup" ? "login" : "signup")}
          >
            {textos.alternar}
          </button>
        </p>
      </fieldset>

      <fieldset className={classeDoPasso(2)} data-step="2">
        <legend>Em que momento você está?</legend>
        <p className="step-help">Isso evita recomendar vagas incompatíveis com seu curso ou período.</p>
        <div className="field-grid">
          <label className="field field-full">
            <span>Seu curso</span>
            <input
              name="curso"
              list="cursos-sugeridos"
              autoComplete="off"
              required
              placeholder="Digite ou escolha seu curso"
              value={campos.curso}
              onChange={alterarTexto("curso")}
              {...atributosDeErro(erro, "curso")}
            />
            <small>Use o nome que aparece na sua faculdade.</small>
            <ErroDoCampo erro={erro} campo="curso" />
          </label>
          <label className="field field-full">
            <span>Período atual</span>
            <select
              name="periodo"
              required
              value={campos.periodo}
              onChange={alterarTexto("periodo")}
              {...atributosDeErro(erro, "periodo")}
            >
              <option value="">Selecione</option>
              {PERIODOS.map((periodo) => (
                <option key={periodo} value={String(periodo)}>{rotuloDoPeriodo(periodo)}</option>
              ))}
            </select>
            <ErroDoCampo erro={erro} campo="periodo" />
          </label>
        </div>
      </fieldset>

      <fieldset className={classeDoPasso(3)} data-step="3">
        <legend>O que você já sabe usar?</legend>
        <p className="step-help" id="skills-help">
          Você pode começar pelo curso e pelas preferências. Depois, informe suas habilidades para melhorar as
          recomendações.
        </p>
        <input name="habilidades" type="hidden" value={estado.habilidades.join(",")} />
        <div className="skill-picker" id="skill-picker" role="group" aria-label="Habilidades sugeridas">
          {estado.sugeridas.map((habilidade) => {
            const escolhida = estado.habilidades.includes(habilidade);
            return (
              <button
                key={habilidade}
                type="button"
                data-skill={habilidade}
                aria-pressed={escolhida}
                className={escolhida ? "is-selected" : undefined}
                onClick={() => controlador.alternarHabilidadeSugerida(habilidade)}
              >
                {habilidade}
              </button>
            );
          })}
        </div>
        <p className="catalog-notice" id="skills-catalog-notice" role="status" hidden={!estado.avisoDeHabilidades}>
          Não foi possível carregar as sugestões agora. Você ainda pode digitar uma habilidade ou continuar sem informar.
        </p>
        <div className="field-grid">
          <label className="field field-full">
            <span>Não encontrou alguma?</span>
            <input
              id="custom-skill"
              autoComplete="off"
              maxLength={100}
              placeholder="Digite uma habilidade e pressione Enter"
              value={campos.habilidade_digitada}
              onChange={alterarTexto("habilidade_digitada")}
              onKeyDown={controlador.teclarNaHabilidade}
              {...atributosDeErro(erro, "custom-skill")}
            />
            <small>Ex.: C#, Figma, AWS ou suporte técnico.</small>
            <ErroDoCampo erro={erro} campo="custom-skill" />
          </label>
        </div>
        <div className="selected-skills" id="selected-skills" role="group" aria-label="Habilidades escolhidas" aria-live="polite">
          {estado.habilidades.map((habilidade) => (
            <button
              key={habilidade}
              type="button"
              aria-label={`Remover ${habilidade}`}
              onClick={() => controlador.removerHabilidade(habilidade)}
            >
              {`${habilidade} ×`}
            </button>
          ))}
        </div>
        <button
          className="text-link skill-empty-action"
          type="button"
          id="continue-without-skills"
          hidden={estado.habilidades.length > 0}
          onClick={controlador.continuarSemHabilidades}
        >
          Ainda não quero informar habilidades <span aria-hidden="true">→</span>
        </button>
      </fieldset>

      <fieldset className={classeDoPasso(4)} data-step="4">
        <legend>Onde as vagas devem chegar?</legend>
        <p className="step-help">Essas preferências serão usadas nas próximas buscas.</p>
        <div className="field-grid">
          <CampoDeCidade estado={estado} controlador={controlador} />
          <div className="field field-full">
            <span>Modalidade preferida</span>
            <div className="option-grid">
              {MODALIDADES.map(([valor, rotulo], indice) => (
                <label key={valor}>
                  <input
                    type="radio"
                    name="modalidade"
                    value={valor}
                    required={indice === 0}
                    checked={campos.modalidade === valor}
                    onChange={() => controlador.alterarCampo("modalidade", valor)}
                    {...(indice === 0 ? atributosDeErro(erro, "modalidade") : {})}
                  />
                  <span>{rotulo}</span>
                </label>
              ))}
            </div>
            <ErroDoCampo erro={erro} campo="modalidade" />
          </div>
          <div className="field field-full" id="campo-areas" hidden={!estado.subareas}>
            <span>Áreas de interesse (opcional)</span>
            <div className="option-grid" id="grade-de-areas">
              {(estado.subareas ?? []).map((subarea) => (
                <label key={subarea.valor}>
                  <input
                    type="checkbox"
                    name="areas"
                    value={subarea.valor}
                    checked={estado.areasEscolhidas.includes(subarea.valor)}
                    onChange={() => controlador.alternarArea(subarea.valor)}
                  />
                  <span>{subarea.rotulo}</span>
                </label>
              ))}
            </div>
            <small>Vagas dessas áreas ganham prioridade; fora delas, a nota cai e a vaga avisa.</small>
          </div>
        </div>
      </fieldset>

      <p className="form-message" id="form-message" role="alert">
        {mensagemDoFormulario?.tom === "erro" ? mensagemDoFormulario.texto : ""}
      </p>
      <p className="form-message form-message-aviso" id="form-notice" role="status">
        {mensagemDoFormulario?.tom === "aviso" ? mensagemDoFormulario.texto : ""}
      </p>
      <div className="form-actions" id="form-actions">
        <button className="button button-ghost" type="button" id="previous-step" hidden={posicao === 0} onClick={controlador.voltarPasso}>
          ← Voltar
        </button>
        <button
          className="button button-primary"
          type="button"
          id="next-step"
          hidden={posicao === passos.length - 1}
          onClick={controlador.avancarPasso}
        >
          Continuar <span aria-hidden="true">→</span>
        </button>
        <button
          className="button button-primary"
          type="submit"
          id="submit-profile"
          hidden={posicao !== passos.length - 1}
          disabled={estado.enviando}
          aria-busy={estado.enviando}
        >
          <span id="submit-label">{rotuloDoEnvio(estado)}</span>
          <span className="button-spinner" aria-hidden="true"></span>
          <span className="button-arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}
