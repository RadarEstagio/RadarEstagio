import { useLayoutEffect, useRef } from "react";
import {
  CONFIRMACOES,
  MOTIVOS_DE_PAUSA,
  SECOES_DA_CONTA,
  estadoDasEntregas,
  resumoDoPerfil,
  visualDasEntregas,
} from "../../domain/conta.js";

function ConfirmacaoDaConta({ acao, controlador }) {
  const dialogo = useRef(null);
  const textos = acao ? CONFIRMACOES[acao] : null;

  useLayoutEffect(() => {
    const elemento = dialogo.current;
    if (acao && typeof elemento.showModal === "function" && !elemento.open) elemento.showModal();
    if (!acao && elemento.open && typeof elemento.close === "function") elemento.close();
  }, [acao]);

  return (
    <dialog
      className="account-confirm"
      id="account-confirm"
      aria-labelledby="account-confirm-title"
      aria-describedby="account-confirm-copy"
      hidden={!acao}
      data-acao={acao ?? undefined}
      ref={dialogo}
      onCancel={(evento) => {
        evento.preventDefault();
        controlador.fecharConfirmacao();
      }}
    >
      <div className="account-confirm-header">
        <span className="account-confirm-icon" aria-hidden="true">!</span>
        <div>
          <p>Confirme a ação</p>
          <h2 id="account-confirm-title">{textos?.titulo ?? "Confirmar ação"}</h2>
        </div>
        <button
          className="account-confirm-close"
          type="button"
          id="account-confirm-close"
          aria-label="Fechar confirmação"
          onClick={() => controlador.fecharConfirmacao()}
        >
          ×
        </button>
      </div>
      <div className="account-confirm-warning">
        <strong id="account-confirm-warning-title">{textos?.aviso}</strong>
        <p id="account-confirm-warning-copy">{textos?.detalhe}</p>
      </div>
      <p id="account-confirm-copy">{textos?.copy}</p>
      <div className="account-actions">
        <button className="button button-ghost" type="button" id="account-confirm-no" onClick={() => controlador.fecharConfirmacao()}>
          Cancelar
        </button>
        <button className="button button-danger" type="button" id="account-confirm-yes" onClick={controlador.confirmarAcao}>
          {textos?.confirmar ?? "Confirmar"}
        </button>
      </div>
    </dialog>
  );
}

function HabilidadesDaConta({ habilidades }) {
  if (!habilidades.length) {
    return <span className="account-skills-empty">Habilidades ainda não informadas</span>;
  }
  return habilidades.map((habilidade) => <span key={habilidade}>{habilidade}</span>);
}

export function Conta({ estado, controlador }) {
  const { conta } = estado;
  const perfil = conta.perfil;
  const secao = SECOES_DA_CONTA.find(({ hash }) => hash === conta.secao) ?? SECOES_DA_CONTA[0];
  const emExclusao = Boolean(perfil?.excluida_em);
  const vinculado = Boolean(perfil?.telegram_chat_id);
  const visual = perfil ? visualDasEntregas(perfil) : { estado: undefined, titulo: "Entregas ativas", simbolo: "✓" };
  const painelOculto = (hash) => conta.secao !== hash;

  return (
    <section className="account-state" id="account-state" aria-labelledby="account-title" hidden={estado.tela !== "conta"}>
      <div className="account-heading">
        <p className="eyebrow">Sua conta</p>
        <h1 id="account-title" tabIndex={-1}>{secao.titulo}</h1>
        <p>{secao.descricao}</p>
      </div>
      <div className="account-panel">
        <p className="form-message" id="account-message" role="alert">
          {conta.mensagem.tom === "erro" ? conta.mensagem.texto : ""}
        </p>
        <p className="form-message form-message-aviso" id="account-notice" role="status">
          {conta.mensagem.tom === "aviso" ? conta.mensagem.texto : ""}
        </p>
        <div className="account-tab-panel" id="account-overview-panel" hidden={painelOculto("#account-overview-panel")}>
          <section className="account-profile-card account-row" id="account-overview-section" aria-labelledby="account-profile-title">
            <div className="account-row-content">
              <div className="account-card-heading">
                <span className="account-card-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <circle cx="12" cy="8" r="3.5"></circle>
                    <path d="M5.5 19c.7-3.4 3-5.2 6.5-5.2s5.8 1.8 6.5 5.2"></path>
                  </svg>
                </span>
                <div>
                  <p>Perfil de busca</p>
                  <h2 id="account-profile-title">Seu Radar</h2>
                </div>
              </div>
              <p id="account-summary">{perfil ? resumoDoPerfil(perfil) : ""}</p>
              <div className="account-skills" id="account-skills" aria-label="Habilidades do perfil">
                {perfil ? <HabilidadesDaConta habilidades={perfil.habilidades} /> : null}
              </div>
            </div>
            <button className="button button-primary" type="button" id="edit-profile" hidden={emExclusao} onClick={controlador.editarPerfil}>
              Editar perfil
            </button>
          </section>
        </div>
        <div className="account-tab-panel" id="account-delivery-panel" hidden={painelOculto("#account-delivery-panel")}>
          <section className="account-delivery-card account-row" id="account-delivery-card" data-status={visual.estado} aria-labelledby="account-delivery-title">
            <span className="account-status-icon" id="account-status-icon" aria-hidden="true">{visual.simbolo}</span>
            <div className="account-row-content">
              <p>Telegram</p>
              <h2 id="account-delivery-title">{visual.titulo}</h2>
              <p className="account-schedule" id="account-schedule">{perfil ? estadoDasEntregas(perfil) : ""}</p>
            </div>
            <button
              className="button button-ghost"
              type="button"
              id="toggle-deliveries"
              hidden={!vinculado || emExclusao}
              disabled={conta.alternando}
              onClick={controlador.alternarEntregas}
            >
              {perfil?.ativo ? "Pausar entregas" : "Retomar entregas"}
            </button>
          </section>
          <fieldset className="account-confirm pause-reason" id="pause-reason" hidden={!conta.pausa.aberta}>
            <legend id="pause-reason-title" tabIndex={-1}>Por que você pausou as entregas?</legend>
            <p>Responder é opcional e ajuda a entender o momento do seu perfil.</p>
            <div className="option-grid">
              {MOTIVOS_DE_PAUSA.map(([valor, rotulo]) => (
                <label key={valor}>
                  <input
                    type="radio"
                    name="motivo-pausa"
                    value={valor}
                    checked={conta.pausa.motivo === valor}
                    onChange={() => controlador.escolherMotivo(valor)}
                  />
                  <span>{rotulo}</span>
                </label>
              ))}
            </div>
            <p className="form-message" id="pause-reason-message" role="alert">{conta.pausa.mensagem}</p>
            <div className="account-actions">
              <button
                className="button button-primary"
                type="button"
                id="save-pause-reason"
                disabled={conta.pausa.ocupada}
                aria-busy={conta.pausa.ocupada}
                onClick={controlador.salvarMotivoDaPausa}
              >
                Salvar motivo
              </button>
              <button
                className="button button-ghost"
                type="button"
                id="skip-pause-reason"
                disabled={conta.pausa.ocupada}
                onClick={controlador.pularMotivoDaPausa}
              >
                Pular
              </button>
            </div>
          </fieldset>
          <section className="account-settings account-row" id="account-preferences-section" aria-labelledby="account-preferences-title">
            <div className="account-section-heading">
              <p>Preferências</p>
              <h2 id="account-preferences-title">Comunicações</h2>
              <span>Escolha se o Radar também pode falar com você por e-mail.</span>
            </div>
            <label className="consent-fields account-email-setting">
              <span>
                <input
                  type="checkbox"
                  id="account-emails"
                  checked={conta.emails.valor}
                  disabled={conta.emails.ocupado || emExclusao}
                  onChange={(evento) => controlador.alterarEmails(evento.target.checked)}
                />{" "}
                <span>Receber e-mails ocasionais do Radar</span>
              </span>
            </label>
          </section>
        </div>
        <div className="account-tab-panel" id="account-data-panel" hidden={painelOculto("#account-data-panel")}>
          <section className="account-settings account-row" id="account-data-section" aria-labelledby="account-data-title">
            <div className="account-section-heading">
              <p>Seus dados</p>
              <h2 id="account-data-title">Dados e acesso</h2>
              <span>Baixe uma cópia das suas informações ou encerre esta sessão.</span>
            </div>
            <div className="account-actions account-actions-secondary">
              <button
                className="button button-ghost"
                type="button"
                id="download-data"
                disabled={conta.baixando}
                aria-busy={conta.baixando}
                onClick={controlador.baixarDados}
              >
                Baixar meus dados
              </button>
              <button className="button button-ghost" type="button" id="logout-account" onClick={controlador.sairDaConta}>
                Sair da conta
              </button>
              <button className="button button-ghost" type="button" id="close-account" onClick={controlador.fecharCadastro}>
                Voltar ao site
              </button>
            </div>
          </section>
        </div>
        <div className="account-tab-panel" id="account-privacy-panel" hidden={painelOculto("#account-privacy-panel")}>
          <section className="account-danger" id="account-danger-section" aria-labelledby="account-danger-title">
            <div className="account-section-heading account-danger-heading">
              <p>Privacidade</p>
              <h2 id="account-danger-title">Ações sensíveis</h2>
              <span>Revise as consequências antes de alterar o vínculo ou excluir sua conta.</span>
            </div>
            <div className="account-danger-list">
              <section className="account-danger-row" aria-labelledby="unlink-telegram-title">
                <div>
                  <h3 id="unlink-telegram-title">Desvincular o Telegram</h3>
                  <p>Interrompe as entregas neste chat. Você poderá vinculá-lo novamente depois.</p>
                </div>
                <button
                  className="button button-danger-ghost"
                  type="button"
                  id="unlink-telegram"
                  hidden={!vinculado || emExclusao}
                  onClick={() => controlador.pedirConfirmacao("desvincular")}
                >
                  Desvincular
                </button>
              </section>
              <section className="account-danger-row" aria-labelledby="delete-account-title">
                <div>
                  <h3 id="delete-account-title">Excluir minha conta</h3>
                  <p>Interrompe as entregas agora e agenda a remoção definitiva dos seus dados.</p>
                </div>
                <button
                  className="button button-danger"
                  type="button"
                  id="delete-account"
                  hidden={emExclusao}
                  onClick={() => controlador.pedirConfirmacao("excluir")}
                >
                  Excluir conta
                </button>
                <button className="button button-primary" type="button" id="cancel-deletion" hidden={!emExclusao} onClick={controlador.cancelarExclusao}>
                  Cancelar a exclusão
                </button>
              </section>
            </div>
            <ConfirmacaoDaConta acao={conta.confirmacao} controlador={controlador} />
          </section>
        </div>
      </div>
    </section>
  );
}
