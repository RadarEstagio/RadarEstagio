export function BotaoDeSenha({ alvo, visivel, aoAlternar }) {
  const rotulo = visivel ? "Ocultar senha" : "Mostrar senha";
  return (
    <button
      className="password-toggle"
      type="button"
      data-toggle-password={alvo}
      aria-label={rotulo}
      aria-pressed={visivel}
      title={rotulo}
      onClick={aoAlternar}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
        <circle cx="12" cy="12" r="2.75"></circle>
        <path className="password-eye-slash" d="m4 4 16 16"></path>
      </svg>
    </button>
  );
}
