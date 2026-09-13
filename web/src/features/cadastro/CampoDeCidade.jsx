import { useLayoutEffect, useRef } from "react";
import { ErroDoCampo, atributosDeErro } from "../../components/ErroDoCampo.jsx";

export function CampoDeCidade({ estado, controlador }) {
  const { cidades, erro } = estado;
  const lista = useRef(null);

  useLayoutEffect(() => {
    if (cidades.destacada < 0) return;
    lista.current?.querySelector('[aria-selected="true"]')?.scrollIntoView?.({ block: "nearest" });
  }, [cidades.destacada]);

  return (
    <div className="field field-full">
      <label htmlFor="cidade">Cidade principal</label>
      <div className="city-combobox">
        <input
          id="cidade"
          name="cidade"
          required
          minLength={2}
          maxLength={120}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={cidades.aberta}
          aria-controls="lista-de-cidades"
          aria-activedescendant={cidades.aberta && cidades.destacada >= 0 ? `cidade-sugerida-${cidades.destacada}` : undefined}
          autoComplete="off"
          placeholder="Digite e escolha sua cidade"
          value={estado.campos.cidade}
          onFocus={controlador.focarNaCidade}
          onChange={(evento) => controlador.digitarCidade(evento.target.value)}
          onKeyDown={controlador.teclarNaCidade}
          onBlur={controlador.sairDaCidade}
          {...atributosDeErro(erro, "cidade")}
        />
        <button
          type="button"
          className="city-toggle"
          id="mostrar-cidades"
          tabIndex={-1}
          aria-label="Mostrar cidades"
          aria-controls="lista-de-cidades"
          aria-expanded={cidades.aberta}
          onMouseDown={(evento) => evento.preventDefault()}
          onClick={controlador.alternarListaDeCidades}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
        <ul
          className="city-options"
          id="lista-de-cidades"
          role="listbox"
          aria-label="Cidades"
          hidden={!cidades.aberta}
          ref={lista}
          onMouseDown={(evento) => evento.preventDefault()}
        >
          {cidades.opcoes?.length === 0 ? (
            <li role="option" aria-disabled="true" aria-selected={false}>
              Nenhuma cidade encontrada. Confira a grafia.
            </li>
          ) : (
            cidades.opcoes?.map((cidade, posicao) => {
              const separador = cidade.nome.lastIndexOf(", ");
              return (
                <li
                  key={cidade.nome}
                  id={`cidade-sugerida-${posicao}`}
                  role="option"
                  aria-selected={posicao === cidades.destacada}
                  data-cidade={cidade.nome}
                  onClick={() => controlador.escolherCidade(cidade.nome)}
                >
                  <span>{cidade.nome.slice(0, separador)}</span>
                  <span>{cidade.nome.slice(separador + 2)}</span>
                </li>
              );
            })
          )}
        </ul>
      </div>
      <p className="catalog-notice" id="cities-catalog-notice" role="status" hidden={!cidades.avisoDeCatalogo}>
        Não foi possível carregar a lista de cidades agora. Confira se o nome está certo, como Rio de Janeiro, RJ.
      </p>
      <small>
        Vagas das cidades vizinhas também entram, como Niterói para quem é do Rio. Vagas remotas de outros lugares
        entram se você não escolher presencial.
      </small>
      <ErroDoCampo erro={erro} campo="cidade" />
    </div>
  );
}
