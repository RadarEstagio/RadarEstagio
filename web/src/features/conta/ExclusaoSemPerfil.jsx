export function ExclusaoSemPerfil({ estado, controlador }) {
  const { semPerfil } = estado;
  return (
    <section
      className="missing-profile-deletion"
      id="missing-profile-deletion"
      aria-labelledby="missing-profile-deletion-title"
      hidden={!semPerfil.visivel}
    >
      <div>
        <h3 id="missing-profile-deletion-title">Prefere não continuar?</h3>
        <p>Sua conta ainda não tem perfil. Se quiser, exclua a conta agora: o e-mail e o acesso são apagados na hora.</p>
      </div>
      <button
        className="button button-danger-ghost"
        type="button"
        id="delete-account-without-profile"
        disabled={estado.enviando || semPerfil.ocupado}
        aria-busy={semPerfil.ocupado}
        onClick={() => controlador.pedirConfirmacao("apagar-sem-perfil")}
      >
        Excluir minha conta
      </button>
    </section>
  );
}
