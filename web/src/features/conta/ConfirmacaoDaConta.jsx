import { useLayoutEffect, useRef } from "react";
import { CONFIRMACOES } from "../../domain/conta.js";

export function ConfirmacaoDaConta({ acao, controlador }) {
  const dialogo = useRef(null);
  const textos = acao ? CONFIRMACOES[acao] : null;

  useLayoutEffect(() => {
    const elemento = dialogo.current;
    if (acao && typeof elemento.showModal === "function" && !elemento.open) elemento.showModal();
    if (!acao && elemento.open && typeof elemento.close === "function") elemento.close();
  }, [acao]);

  useLayoutEffect(() => {
    const elemento = dialogo.current;
    return () => {
      if (elemento.open && typeof elemento.close === "function") elemento.close();
    };
  }, []);

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
