export function ErroDoCampo({ erro, campo }) {
  if (erro?.campo !== campo) return null;
  return (
    <span className="field-error" id="erro-do-campo">
      {erro.mensagem}
    </span>
  );
}

export function atributosDeErro(erro, campo) {
  if (erro?.campo !== campo) return {};
  return { "aria-invalid": "true", "aria-describedby": "erro-do-campo" };
}
