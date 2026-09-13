import { useLayoutEffect, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { SECOES_DA_CONTA } from "../domain/conta.js";
import { Painel } from "./Painel.jsx";

function cliqueSimples(evento) {
  return evento.button === 0 && !evento.metaKey && !evento.ctrlKey && !evento.shiftKey && !evento.altKey;
}

export function App({ controlador }) {
  const estado = useSyncExternalStore(controlador.assinar, controlador.estado);
  const naPagina = estado.superficie === "pagina";

  useLayoutEffect(() => {
    if (estado.foco) controlador.documento.querySelector(estado.foco.seletor)?.focus();
  }, [controlador, estado.foco]);

  const painel = <Painel estado={estado} controlador={controlador} />;

  return (
    <>
      <div className="account-shell">
        <aside className="account-sidebar" aria-label="Navegação da conta">
          <div className="account-sidebar-inner">
            <a
              className="brand"
              href="./"
              id="account-home"
              aria-label="Radar de Estágio, início"
              onClick={(evento) => {
                if (!naPagina) return;
                evento.preventDefault();
                controlador.fecharCadastro();
              }}
            >
              <span className="radar-mark" aria-hidden="true">
                <i></i>
              </span>
              <span>
                Radar<span>Estágio</span>
              </span>
            </a>
            <button className="account-back" type="button" id="back-to-site" onClick={controlador.fecharCadastro}>
              <span aria-hidden="true">←</span> Voltar ao site
            </button>
            <nav className="account-nav" aria-label="Seções da conta">
              <p>Configurações</p>
              {SECOES_DA_CONTA.map((secao) => {
                const ativa = estado.conta.secao === secao.hash;
                return (
                  <a
                    key={secao.hash}
                    className={ativa ? "is-active" : undefined}
                    href={secao.hash}
                    aria-current={ativa ? "location" : undefined}
                    onClick={(evento) => {
                      if (!cliqueSimples(evento)) return;
                      evento.preventDefault();
                      controlador.mostrarSecaoDaConta(secao.hash);
                    }}
                  >
                    {secao.rotulo}
                  </a>
                );
              })}
            </nav>
          </div>
        </aside>
        <main className="account-main" id="account-main" aria-label="Minha conta">
          <div className="account-page-content">
            <div id="account-content">{naPagina ? painel : null}</div>
          </div>
        </main>
      </div>
      {naPagina ? null : createPortal(painel, controlador.dialogo)}
    </>
  );
}
