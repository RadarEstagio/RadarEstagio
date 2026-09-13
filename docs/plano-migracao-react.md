# Plano de migração incremental do frontend para React

**Revisado em 12/09/2026 após os comentários da PR #62.**

Igor autorizou ajustar o plano e iniciar a execução. Esta PR continua exclusivamente
documental; implementação será entregue em PRs menores, sem merge ou mudanças remotas
automáticas. O estado da iniciativa fica no [plano geral](plano-geral.md#23-migração-do-frontend-para-react-12092026).

## 1. Objetivo, decisão e escopo

Migrar autenticação, cadastro e conta para React com JavaScript, preservando aparência,
URLs, sessão e contratos. A landing permanece HTML com JavaScript modular nesta primeira
fase. Isso não é uma conversão completa de todo o frontend: converter o conteúdo público
para React fica para uma decisão posterior, sem bloquear a adoção nos fluxos interativos.

| Alternativa avaliada | Ganho e custo | Decisão |
|---|---|---|
| JavaScript em módulos ES, com Vite | Separa o arquivo monolítico com menor esforço; mantém coordenação manual entre estado e DOM | Alternativa válida se o objetivo fosse apenas separar arquivos |
| React + JavaScript nos fluxos interativos | Estado declarativo do cadastro e componentes compartilhados entre modal/conta; exige build, dependências e adaptação de testes | Escolhida para a evolução desses fluxos e pela familiaridade do Igor com React |
| Toda a landing em React com geração estática/hidratação | Unifica a autoria em JSX, mas acrescenta renderização no build e cuidados de hidratação para conteúdo pouco interativo | Adiada; sem `prerender.mjs`, SSR ou `hydrateRoot` nesta fase |

O custo de React se justifica pelo reuso e pela coordenação do formulário e da sessão, não
pelo número de linhas do arquivo. Não promete mais tráfego, ganho de velocidade ou aumento
da capacidade do backend. A [adoção parcial é suportada pelo React](https://react.dev/learn/add-react-to-an-existing-project).

Incluído: diálogos, Auth, cadastro, perfil pendente, edição, preferências, pausa, Telegram,
exportação/exclusão, serviços, testes, build e documentação. Landing, header, tema, hero,
FAQ e páginas legais mantêm conteúdo e CSS; seu JavaScript pode ser separado em módulos.

Fora do escopo: TypeScript na aplicação, redesign, novas funcionalidades, Next.js, Redux,
Tailwind, cobrança, regras de recomendação, fontes, schema, RLS, RPCs ou Edge Functions.
Não mudar domínio, Auth, CAPTCHA ou publicar em produção sem autorização própria.

## 2. Base e preservação do trabalho atual

Base remota conferida: `main` em `5ddf9a0`, após as PRs #60, #61 e #63. Atualizar e
registrar o SHA ao começar cada entrega; não recuperar dados reais ou alterações retiradas.

- #60: preservar header sempre visível, blur, dimensões, tema/login separados e seções atuais.
- #61: preservar selos “Jobs by Adzuna”, links e logo oficial; Gupy continua fora das fontes.
- #63: preservar fixtures sintéticas e a retirada dos arquivos reais de rotulagem do Git.
- A #63 restaurou a faixa de fontes sem Gupy. Igor confirmou preservar a `main` atual;
  manter essa faixa na migração, substituindo a orientação anterior de removê-la.

A revisão não autoriza mudanças de copy, logo ou layout. Registrar referência visual somente
depois de conciliar mudanças recentes; um teste antigo não é licença para revertê-las.

## 3. Organização e limites de responsabilidade

Stack: React/JSX com JavaScript, Vite/npm, CSS existente, Supabase e Vitest/Testing Library.
Manter inicialmente o SDK Supabase `2.116.0`; fixar versões compatíveis e Node no ambiente
local, CI e build. Usar estado local/`useReducer` e Context restrito à sessão, sem store geral.

Estrutura-alvo resumida:

```text
scripts/build-web.sh
web/
  index.html, termos.html, privacidade.html, config.js
  assets/                 CSS, catálogos e logo, nas fontes atuais
  package.json, package-lock.json, vite.config.js
  src/
    main.jsx              monta apenas as raízes interativas
    landing/              tema, hero, CTA e navegação pública
    app/                  sessão única e coordenação das telas
    features/
      autenticacao/
      cadastro/
      conta/
    components/           diálogo, campos e feedback compartilhados
    services/             Supabase, Auth, perfis, RPCs, eventos, catálogos
    domain/               validações e normalizações sem DOM/rede
  tests/                  unitários, integração, artefato e e2e
```

Manter as fontes dos catálogos, logo e `config.js` nos caminhos atuais. O build copia os
recursos públicos necessários para os mesmos URLs da saída; CSS pode ser processado pelo
Vite nas entradas HTML. Não criar cópias versionadas concorrentes nem mover os arquivos
apenas para seguir um template do Vite. Se um caminho precisar mudar, ajustar gerador e
todos os leitores sem mudar os dados ou exigir regeneração online.

### HTML, sessão e DOM

- `index.html` continua a única fonte da landing; conteúdo/metadados permanecem presentes
  sem JavaScript. Termos e privacidade continuam HTML, sem Auth/analytics e com seu `noindex`.
- React controla apenas raízes explícitas de Auth/cadastro/conta. Não montar sobre a landing
  inteira, renderizar a aplicação como string ou executar o `app.js` dentro de um efeito.
- Uma instância do cliente Supabase e uma fonte de sessão atendem legado e React durante a
  transição. Definir uma interface pequena de abrir fluxo/receber sessão, sem dois controllers.
- Ao migrar uma subárvore, retirar seus listeners e sua marcação antiga da entrada ativa.
  Nenhum nó pertence simultaneamente ao React e ao código imperativo.
- Cadastro e edição compartilham componentes; não mover nós React com `append`. Integrações
  de `<dialog>`, CAPTCHA, foco e download têm montagem/desmontagem explícitas.
- Tema antecipado continua no `<html>`, fora das raízes React. A ausência de hidratação
  elimina essa fonte de divergência, sem remover o teste de tema salvo antes do carregamento.

### URLs e configuração

Preservar `/`, `/index.html`, `?conta`, `?fluxo=recuperar`, âncoras da conta/landing e
páginas legais. Centralizar navegação sem inventar novas rotas ou usar HashRouter. Deixar
o SDK consumir `code`, tokens e erros do retorno antes de limpar a URL. Sessão na homepage
não deve abrir a conta sem a intenção existente. Dev usa `localhost:8000` com `strictPort`.

Manter `/config.js`, `window.RADAR_CONFIG` e o formato público. Configuração inválida exige
erro útil. Nunca copiar `.env`, `service_role`, conexão Postgres ou tokens para o frontend;
variáveis `VITE_*` são públicas. Preview/testes não usam produção por fallback silencioso.

## 4. Entregas pequenas

O planejamento fica na PR #62; implementação usa branches/PRs próprias. Testes acompanham
cada fatia. PRs dependentes podem ser preparados em sequência, com base declarada; não
fazer merge automático nem antecipar uma troca de publicação ainda não autorizada.

| Entrega | Conteúdo | Saída verificável |
|---|---|---|
| P1 — Build compatível | Script legado/Vite, testes isolados do artefato e roteiro Pages; sem mudar frontend ativo | HTML legado idêntico na saída, script falha corretamente e PR pronta para revisão |
| P2 — Ferramentas do frontend | Vite, lint com checagem de comentários, Vitest, conferência do artefato e job de CI; o navegador executa os mesmos arquivos | Build pelo `build-web.sh` com os caminhos públicos atuais e referências locais conferidas |
| P3 — Cadastro e Auth | React e SDK do Supabase por npm, serviços e sessão únicos, landing modular; componentes compartilhados, login, confirmação, recuperação, CAPTCHA e wizard | Jornadas e edição compartilhada equivalentes, sem duplo controller |
| P4 — Conta e fechamento | Controles da conta, limpeza do legado migrado, cobertura e documentação final | Todos os cenários mapeados e uma implementação ativa por fluxo |

P3/P4 não devem ser separados artificialmente se a edição compartilhada depender do wizard:
migrar o componente compartilhado com seu consumidor ou usar uma ponte explícita testada.
Não publicar um fluxo incompleto só para reduzir o tamanho da PR.

A execução começa por P1, que não depende da decisão visual nem de acesso ao Pages. O restante
pode ser desenvolvido/testado localmente; a abertura de branches com nova entrada pública
depende da preparação de preview da seção 7. Bloqueio de publicação não impede entregar código
e evidências locais, mas precisa ser comunicado, sem alegar preview validado.

## 5. Contratos e regressões obrigatórios

O [contrato frontend](contrato-front.md) é a referência completa. Estes são os pontos de
maior risco para mapear aos testes; não repetir esta lista no checklist final.

### Cadastro e perfil

- Perfil antes da conta; `signUp` só no envio final e sem submissão duplicada.
- Preservar `options.data.cadastro_radar`, consentimentos, versão dos termos e sessão do funil.
  Não inserir/upsert direto em `perfis`; manter confirmação e `concluir_meu_cadastro`.
- Confirmação em outro aparelho não depende de rascunho local. Login não sobrescreve perfil
  existente; edição limita colunas e filtra o usuário autenticado.
- Manter 0–50 habilidades, até 100 caracteres após trim, e escolha explícita por lista vazia.
  Preservar cursos livres, normalizações, áreas e sugestões dependentes do curso.
- Cidades: oito sugestões, normalização, estado para homônimos, teclado e fallback com aviso.
  Falha de catálogo na edição não apaga seleções válidas.
- Respostas antigas não sobrescrevem curso, perfil ou sessão novos. Manter tratamento do
  `radar-perfil-pendente` legado, sem persistir novos perfis/senhas no navegador.

### Auth e ciclo de vida

- Persistência, refresh e storage da sessão preservados; migração não exige novo login.
- Recuperação exige sessão/evento válido, não só query string; preservar logout após troca.
- Reenvio: e-mail editável, 60 segundos e tratamento de 429.
- CAPTCHA opcional: script/widget únicos, expiração, erros e descarte do token por tentativa.
- Limpar assinaturas/timers/listeners; Strict Mode não pode duplicar eventos ou mutações.
  Logout invalida respostas e estado transitório, sem limpar todo o storage do navegador.
- Senha vai apenas ao Auth, nunca a perfil, métricas, logs ou persistência própria.

### Conta, Telegram e privacidade

- Pausa salva antes do motivo opcional; falha/omissão do motivo não a desfaz. Retomar limpa o motivo.
- Preservar RPCs de desvínculo, exportação, exclusão e cancelamento, sem escritas substitutas.
- Exclusão: carência de 60 dias, sessão mantida, estado de pausa preservado e controles
  incompatíveis bloqueados; cancelamento exige novo vínculo quando aplicável.
- Ações sensíveis têm confirmação/foco corretos; falha não pode apresentar sucesso.
- Exportar `meus-dados-radar.json` e revogar a URL temporária.
- Telegram usa token atualizado e relê perfil ao retornar/abrir o bot, sem promessa de busca.

### Interface e eventos

- Preservar CSS, foco, Escape, labels, autofill, teclado e movimento reduzido; wrappers não
  podem quebrar seletores. Manter header, tema/login separados, seções e atribuição à Adzuna.
- Preservar `radar-tema`, `radar-sessao-eventos`, `radar-landing-vista`, nomes/origens dos
  eventos e deduplicação de `landing_visualizada` por sessão de navegador.
- Storage bloqueado e falha de analytics não interrompem a jornada; eventos não carregam
  senhas, tokens ou texto livre de dados pessoais.

## 6. Testes e CI proporcionais

Referência histórica anterior à #63: 1.037 testes Python passaram, 27 pulados, e 82 testes
web passaram. Reexecutar na base de cada entrega; não apresentar esses números como teste
da migração. Mapear individualmente os 73 cenários de `cadastro_test.ts`, não só a contagem.

| Cobertura atual | Tratamento |
|---|---|
| `tests/web/cadastro_test.ts` | Portar cenários para Vitest/Testing Library por fluxo; remover harness antigo só após equivalência |
| `tests/test_frontend_activation.py` | Migrar buscas por funções/CDN para comportamento de Auth e testes do artefato |
| `tests/test_product_copy.py` | Preservar conteúdo, atribuição e referência visual atual; HTML estático continua testável |
| `tests/test_product_events.py` | Verificar payloads, origem, deduplicação e falhas na fronteira do serviço |
| Testes de áreas, cidades e regiões | Preservar contratos Python e dados; mover apenas verificações de UI quando necessário |
| Demais testes Python, nove Deno e Edge Functions | Manter checks e cobertura, sem dependência nova de build no domínio Python |

Vitest cobre funções puras e componentes com serviços simulados. O teste do artefato verifica
HTML/recursos e ausência de arquivos privados. Playwright roda **Chromium no CI**, em desktop
e viewport mobile, para jornadas críticas; Safari e Firefox têm roteiro manual de login,
cadastro, tema, header/blur, foco e autofill. Não alegar validação manual não realizada.

Comparar screenshots dos estados afetados e bytes carregados antes/depois, nas mesmas
condições. Sem criar projeto de benchmark, meta arbitrária de cobertura ou nova matriz de
três motores no CI. Regressão visual ou de carregamento relevante precisa ser explicada.

Mocks/fixtures são sintéticos; não incluir perfis reais, tokens, e-mails ou snapshots de
produção. CI e preview não enviam e-mail/Telegram nem gravam eventos reais. Teste integrado
real exige conta e ambiente autorizados. Não silenciar avisos genéricos para esconder falhas.

### Comandos e regra de comentários

Preservar jobs Python/Deno. Adicionar, por etapa, Node fixado, instalação com lockfile, lint,
Vitest, build, artefato e Chromium. Scripts planejados:
`dev`, `lint`, `test:run`, `build`, `test:artifact`, `test:e2e`, `preview`.

A regra do `CLAUDE.md` vale também para JS/JSX e CSS próprios do projeto: adicionar uma
checagem de comentários baseada nos tokens/AST do parser JS com JSX e no parser CSS.
Rejeitar comentários de linha/bloco, JSX e CSS, com testes positivos/negativos; não tratar
URLs/strings como comentários. Dependências e artefatos gerados ficam fora dessa checagem.
Não depender do lint padrão ou de regex sobre o texto inteiro.

Rodar `uv run pytest -q` em comando separado antes de cada commit e conferir o resultado,
além dos testes afetados. Commits convencionais em português, identidade Git configurada,
sem coautoria de IA; preservar o ciclo add → commit → push e não reescrever histórico.

## 7. Transição concreta do Cloudflare Pages

O [guia](guia-publicacao-e-piloto.md) registra `exit 0` e saída `web`. Não assumir configurações
independentes entre preview e produção. A solução é um build compatível com saída fixa
`web/dist`, instalado em uma entrega anterior à mudança de frontend.

### Contrato do script `scripts/build-web.sh`

- Sem `web/package.json`: gerar `web/dist` copiando somente os HTML públicos, `config.js`
  e os recursos estáticos necessários de `assets/`, por lista explícita.
- Com configuração Vite: `npm --prefix web ci` e `npm --prefix web run build`; manifest
  incompleto ou falha do build encerra com erro, nunca cai no caminho legado.
- Não copiar `web/` recursivamente para dentro de si, `node_modules`, testes, fontes novas,
  secrets ou relatórios. O destino de limpeza é somente `web/dist`, com path validado.
- Testar ambos os modos em diretórios temporários: paths públicos, conteúdo e falhas; incluir
  arquivos proibidos nas fixtures para comprovar que não entram na saída.
- Retorno zero só com artefato válido. Preview/produção usam o mesmo contrato de arquivos;
  configuração de teste não pode substituir silenciosamente a de produção.

### Ordem operacional e dependências

1. Abrir P1 com script/testes fora da pasta pública; frontend ativo continua idêntico.
2. Após autorização de merge, integrar P1 à `main` e atualizar branches relevantes com o script.
3. Registrar settings e deployment anterior. Com autorização para alterar o Pages, definir
   Node compatível, build `bash scripts/build-web.sh` e saída `web/dist`.
4. Validar um deployment legado com a nova configuração antes de introduzir Vite na entrada
   publicada. O site continua estático e os próximos commits da `main` continuam publicáveis.
5. Só depois habilitar previews das branches migradas, usando a mesma saída e sem dados reais.
   Se não houver autorização/acesso para 2–4, manter desenvolvimento/artefatos locais e PRs
   sem ativar a nova entrada pública; comunicar a pendência, não mudar settings por conta própria.
6. Aprovar visual/fluxos no preview, conferir redirects com conta de teste autorizada e
   coordenar os merges seguintes. Não mudar domínio, Site URL, allowlist ou CAPTCHA.
7. Após cada publicação, registrar SHA, URL e verificações no guia. Merge/CI não comprovam
   sucesso do deployment ou funcionamento real de Auth.

A Cloudflare documenta [builds condicionais por script](https://developers.cloudflare.com/pages/how-to/build-commands-branches/).
Conferir settings continua necessário, mas valida essa estratégia definida, não substitui a
solução. Testar a versão nova localmente não exige alterar o ambiente de produção.

### Reversão

Perda de sessão, quebra de jornada, duplicação de operações ou assets ausentes bloqueiam
publicação. Se detectados depois, restaurar o último deployment de produção válido e
reverter a PR correspondente pelo fluxo normal do Git. Com P1 presente, o build compatível
continua aceitando a versão antiga; se reverter também P1, restaurar `exit 0`/saída `web`
para os próximos builds. Não há rollback de banco: contratos e dados permanecem compatíveis.
A [reversão do Pages](https://developers.cloudflare.com/pages/configuration/rollbacks/) usa
deployments de produção, não previews; conferir landing, assets, sessão e login depois.

## 8. Documentação e aceite por PR

Atualizar quando a implementação mudar, sem declarar recursos instalados antes da hora:

- `README.md`: “Frontend local”, descrição da stack e comandos de desenvolvimento/testes.
- `CLAUDE.md`: “Stack”, landing estática versus fluxos React, dependências e checagem de comentários.
- `docs/arquitetura.md`: dono do DOM, sessão única, serviços e adoção incremental.
- `docs/contrato-front.md`: novas referências executáveis, sem mudar regras de negócio.
- `docs/guia-publicacao-e-piloto.md`: build compatível, settings/evidências reais e rollback.
- Plano geral: avanço e pendências; `web/README.md` continua histórico.

Cada PR informa sua base/dependências, cenários migrados, comandos e resultados executados,
screenshots quando aplicável, diferença de carregamento e pendências de validação/publicação.

- [ ] Escopo da entrega completo, sem redesign ou mudança de contrato.
- [ ] Cenários afetados da seção 5 mapeados; testes, lint e artefato passam.
- [ ] Uma fonte de sessão e um controlador por subárvore; sem código morto para satisfazer testes.
- [ ] Comparação visual e roteiro manual registrados, com o não verificado explicitado.
- [ ] Documentação, dependências de merge, preview e reversão claros.
- [ ] Aprovação necessária obtida antes de merge, mudança remota ou publicação.

A conclusão desta fase é React nos fluxos interativos e landing estática preservada. A
conversão posterior da landing permanece uma decisão separada, não uma entrega concluída.
