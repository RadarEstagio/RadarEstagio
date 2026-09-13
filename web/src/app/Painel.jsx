import { useLayoutEffect, useRef } from "react";
import { Assistencia } from "../features/autenticacao/Assistencia.jsx";
import { Cadastro } from "../features/cadastro/Cadastro.jsx";
import { Conta } from "../features/conta/Conta.jsx";
import { Sucesso } from "../features/conta/Sucesso.jsx";
import { captchaOculto } from "./controlador.js";

function Progresso({ estado }) {
  const posicao = estado.passos.indexOf(estado.passo);
  const percentual = estado.progresso ?? Math.round((posicao / estado.passos.length) * 100);
  return (
    <div className="progress-wrap" hidden={estado.tela !== "formulario" || estado.passos.length === 1}>
      <div className="progress-meta">
        <span id="progress-label">{`Etapa ${posicao + 1} de ${estado.passos.length}`}</span>
        <strong id="progress-percent">{`${percentual}%`}</strong>
      </div>
      <div
        className="progress-track"
        id="progress-track"
        role="progressbar"
        aria-labelledby="progress-label"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={String(percentual)}
      >
        <span id="progress-bar" style={{ width: `${percentual}%` }}></span>
      </div>
    </div>
  );
}

function EspacoDoCaptcha({ elemento, oculto }) {
  const espaco = useRef(null);

  useLayoutEffect(() => {
    espaco.current.append(elemento);
    return () => elemento.remove();
  }, [elemento]);

  useLayoutEffect(() => {
    elemento.hidden = oculto;
  }, [elemento, oculto]);

  return <div ref={espaco}></div>;
}

export function Painel({ estado, controlador }) {
  return (
    <div className="dialog-shell">
      <button className="dialog-close" id="close-dialog" type="button" aria-label="Fechar cadastro" onClick={controlador.fecharCadastro}>
        ×
      </button>
      <div className="dialog-intro">
        <span className="radar-mark radar-mark-dialog" aria-hidden="true">
          <i></i>
        </span>
        <p className="eyebrow eyebrow-light">Ative seu radar</p>
        <h2 id="signup-title">Seu perfil deixa cada busca mais certeira.</h2>
        <p>Preencha uma vez. O sistema usa essas informações para comparar as vagas com o que você procura.</p>
        <div className="privacy-note">
          <span aria-hidden="true">●</span> Seu perfil serve para selecionar vagas. O e-mail dá acesso à conta e o
          Telegram recebe as recomendações. Usamos fornecedores para operar o serviço. Consulte a{" "}
          <a href="privacidade.html" target="_blank" rel="noopener">
            Política de Privacidade (em revisão, abre em outra aba)
          </a>
          .
        </div>
      </div>
      <div className="dialog-form-area">
        <Progresso estado={estado} />
        <Cadastro estado={estado} controlador={controlador} />
        <Assistencia estado={estado} controlador={controlador} />
        <EspacoDoCaptcha elemento={controlador.elementoDoCaptcha} oculto={captchaOculto(estado)} />
        <Sucesso estado={estado} controlador={controlador} />
        <Conta estado={estado} controlador={controlador} />
      </div>
    </div>
  );
}
