# Matriz de cobertura de estágios

Preparado em 08/09/2026 para E02. Este documento mede oferta observada em uma amostra quando
for preenchido; não mede o mercado inteiro e não transforma ausência de resposta em ausência
de vagas. A coleta deve ser somente leitura, sem envios a estudantes.

## Método e campos

Para cada janela, registrar data, fonte, consulta, curso, cidade, modalidade, paginação e
referência anonimizada do anúncio. Contar separadamente o total recebido, o resultado do
pré-filtro, anúncios com extração, avaliações aprovadas e recomendações elegíveis. Um anúncio
sem descrição completa, alias ausente ou erro técnico fica identificado como tal.

| Data | Fonte | Consulta/curso | Cidade | Modalidade | Recebidos | Pré-filtro | Extraídos | Recomendáveis | Descrição completa? | Erro/limite | Caso |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 08/09/2026 | fixture Adzuna | sintético | sintético | sintético | não medido | não medido | não medido | não medido | verificar no teste | fixture local, não anúncio observado | `tests/fixtures/adzuna_resposta.json` |
| 08/09/2026 | fixture Gupy | sintético | sintético | sintético | não medido | não medido | não medido | não medido | verificar no teste | fixture local, não anúncio observado | `tests/fixtures/gupy_resposta.json` |
| 08/09/2026 | fixture detalhe Adzuna | sintético | sintético | sintético | não medido | não medido | não medido | não medido | HTML disponível | fixture local, não anúncio observado | `tests/fixtures/adzuna_detalhe.html` |
| a definir | Adzuna | Administração — financeiro/RH | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Gupy | Software aplicado a laboratório | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna/Gupy | formação desconhecida | a definir | a definir | não medido | não medido | não medido | não medido | não medido | distinguir incompatibilidade de desconhecido | a definir |
| a definir | Adzuna/Gupy | saúde | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna/Gupy | engenharia | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna/Gupy | computação — controle | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |

As linhas sintéticas só documentam o procedimento e não entram em qualquer afirmação de
cobertura. As linhas reais precisam de janela e paginação antes de serem somadas.

## Casos de qualidade

| Entrada/caso | Resultado atual a registrar | Resultado esperado | Causa provável/teste sugerido | Estado |
|---|---|---|---|---|
| Administração com vaga financeira/RH | não medido | aceitar quando a área e a descrição forem compatíveis; desconhecido quando faltarem fatos | validar `area_do_curso`, interesses e pré-filtro com fixture anonimizada | pendente de amostra |
| Software aplicado a laboratório | não medido | não descartar só pelo domínio da empresa; avaliar descrição e requisitos | fixture de descrição completa e teste de pré-filtro | pendente de amostra |
| Formação desconhecida | catálogo atual não inventa área | manter como desconhecida ou curso livre, sem sugerir outra formação | registrar alias e decidir D01 separadamente | contrato atual preservado |
| Saúde | não medido | separar exigência profissional de estágio compatível | exemplo público anonimizado e teste de regra | pendente de amostra |
| Engenharia | não medido | não misturar especialidades sem evidência | exemplo público anonimizado e teste de área | pendente de amostra |
| Computação como controle | regressões de domínio já cobertas pelos testes locais | preservar áreas e limites existentes | `tests/test_areas.py`, `tests/test_areas_do_front.py` | coberto localmente |
| Descrição truncada | não medido em fonte real | marcar informação insuficiente, não reprovar como incompatível | comparar detalhe com resultado resumido | pendente de amostra |
| Alias ausente | não medido em fonte real | registrar o termo desconhecido antes de propor catálogo | caso anonimizado e decisão D01 | pendente de amostra |

Os casos A01–A06, resumidos na [arquitetura](arquitetura.md#correções-e-limites-preservados-da-auditoria-de-0809), são regressões já corrigidas e não serão refeitos
como mudança de ranking nesta ficha. Qualquer defeito novo deve ganhar uma entrada própria e um
teste ligado ao exemplo; não ajustar pesos para fazer uma amostra parecer melhor.

## Próximo passo da equipe

Executar `uv run python -m radar coletar` em janela autorizada, guardar apenas referências
públicas/anonimizadas e preencher uma linha por fonte/consulta. Depois rodar a avaliação sem
enviar mensagens, registrar falhas de coleta separadas de ausência de oferta e anexar a janela
ao relatório. Responsável e acesso às fontes: a definir.

Conclusão permitida neste estado: há fixtures locais e um método reproduzível. Cobertura real,
ausência de mercado e suficiência por área continuam não medidas.
