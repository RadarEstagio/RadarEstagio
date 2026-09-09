# Registro de execução

Estado em 08/09/2026: plano sincronizado com `40ed28c`. O00 foi implementado nesta branch;
C04 já possui implementação parcial anterior. As correções da auditoria estão na main.
Não reaplicar entregas existentes.

## Ponto de retomada

- ID atual: C01.
- Próximo passo: identificar a constraint de `habilidades` e preparar a migration incremental.
- Branch/HEAD: `codex/expansao-revenue-centric` / após O00, conferir com Git antes do commit.
- Alterações locais preexistentes: inventariar e preservar.
- Bloqueios reais: nenhum identificado para iniciar O00.

## Entregas

| ID | Estado | Arquivos/commit | Verificações e resultado | Pendência externa |
|---|---|---|---|---|
| O00 | Implementado/testado | `.github/workflows/radar-diario.yml` | `QUANTIDADE_VAGAS_ENVIADAS` mudou de 7 para 5; Python já tinha padrão 5 | Workflow versionado nesta branch; nenhuma execução remota verificada |
| C04 | Parcial | Catálogo e sugestões já existem na base | Falta concluir fallback e integração conforme ficha | Publicação não verificada |
| Demais IDs locais | Não iniciado | — | Executar na ordem do índice | — |

## O00

- Comportamento antes → depois: o workflow sobrescrevia a configuração com 7; diário e dispatch por perfil agora recebem 5.
- Arquivos/símbolos: `.github/workflows/radar-diario.yml`, `radar/settings.py` conferido; padrão Python continua 5.
- Casos obrigatórios: busca textual confirmou um único override de produção; nenhum parâmetro de fonte, cron ou filtro foi alterado.
- Comandos/exit code: `git diff --check` será executado no fechamento do commit; inspeção YAML/diff concluída. Pipeline real não foi executado.
- Inspeção visual: não aplicável.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit após a verificação final do ID. Sem deploy/publicação remota.
- Pendência real/próximo comando: nenhuma no código local; iniciar C01 e manter a sequência de publicação C02 → migration C01 → frontend C03.

Estados: Parcial; Não iniciado; Em execução; Implementado/testado; Preparado, falta evidência externa;
Bloqueado (descrever causa); Publicado/verificado. A coluna de publicação nunca decorre apenas
do status de teste ou merge. Detalhes ficam aqui; estado resumido fica no índice do plano.

## Verificação final

- Python: não executado nesta fila.
- Web/banco: não executado nesta fila.
- Lint/formatação: não executado nesta fila.
- Visual: não executado nesta fila.
- Versões remotas: não verificadas nesta fila.

## Decisões e evidências externas pendentes

Preencher durante E01–E05/D01, com link para os documentos produzidos. Não reproduzir chaves,
tokens, dados pessoais ou informações de conta desnecessárias.

## Referência anterior à execução da fila

Base `40ed28c`: 649 testes Python aprovados e 24 ignorados. Web/banco: 36 aprovados
em `a87f9fc`. Esses resultados são referência, não conclusão das tarefas futuras.

## Modelo de registro por tarefa

Copiar para cada ID em execução; não preencher resultados antes de verificar.

- ID/subpasso:
- Comportamento antes → depois:
- Arquivos/símbolos:
- Casos obrigatórios e teste correspondente:
- Comandos/exit code/aprovados/ignorados:
- Inspeção visual (se aplicável):
- Commit/branch e publicação:
- Pendência real/próximo comando:

A ordem de retomada segue os blocos do índice. Após O00, iniciar C01; landing vem após C05.
