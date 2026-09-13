export function Sucesso({ estado, controlador }) {
  const { sucesso } = estado;
  return (
    <section className="success-state" id="success-state" aria-labelledby="success-title" hidden={estado.tela !== "sucesso"}>
      <div className="success-icon" aria-hidden="true">✓</div>
      <p className="eyebrow">
        <span id="success-kicker">{sucesso.kicker}</span>
      </p>
      <h2 id="success-title" tabIndex={-1}>{sucesso.titulo}</h2>
      <p id="success-copy">{sucesso.copy}</p>
      <div className="success-actions">
        <button className="button button-ghost" id="success-account" type="button" onClick={controlador.abrirContaDoSucesso}>
          Minha conta
        </button>
        <a
          className="button button-primary"
          id="telegram-link"
          target="_blank"
          rel="noopener"
          hidden={!sucesso.linkVisivel}
          href={sucesso.token ? controlador.linkDoTelegram(sucesso.token) : undefined}
          onClick={controlador.abrirTelegram}
        >
          Vincular e ativar no Telegram <span aria-hidden="true">→</span>
        </a>
        <button className="button button-ghost" type="button" id="finish-signup" onClick={controlador.fecharCadastro}>
          Voltar ao site
        </button>
      </div>
    </section>
  );
}
