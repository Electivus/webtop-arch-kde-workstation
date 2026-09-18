# T13 — Revisão de fonte e publicação

Ponto fixo `03cf1fa8944ce071a8cbf063fccef17d343ea316`; checkpoint inicial
`25ed6a19d2217785d82cc0f161366d9b03636a5b` (oito arquivos).
Dois agentes nativos independentes leram os mesmos objetos Git congelados,
sequencialmente e sem receber conclusões do outro eixo. Nenhum alterou a fonte
ou operou serviços externos. O preflight Planning passou em
`0dee9084ec3f3e1ad0fdb93a029a5c28a42d9d70` para as sete decisões de T13.

## Standards

Nenhuma violação documentada confirmada. A revisão conferiu `AGENTS.md`,
`CONTRIBUTING.md`, os documentos de agentes e a política pública do repositório.
Os gates e a ancestralidade foram preservados; as permissões de escrita estão
justificadas e o destino GitHub é explícito.

Duas observações opcionais de **Duplicated Code**: validação de versão/revisão
em `scripts/publish.py` (linhas 90–93 e 303–304 no checkpoint inicial), e forma
da resposta de execução GitHub em `tests/test_publication.py` (218–222 e 275–279).
As citações foram verificadas. Mantidas neste escopo: as entradas de candidata
e de release têm contratos distintos, e as fixtures mantêm explícitos os campos
relevantes de cada cenário. Não houve violação, correção obrigatória ou solicitação
de nova revisão desse eixo.

Resultado inicial: zero violações, duas sugestões de manutenção não bloqueantes.

## Spec

Um achado P2 confirmado: `release --draft=false` antecedia a conferência da tag
Git (linhas 347–351). Uma tag existente em outro commit podia tornar a entrega
pública antes de o publicador detectar a divergência. Isso contrariava o contrato
de não anunciar entrega parcial ou inconsistente como concluída (spec, linha 158).

A reprodução pelo limite externo da CLI GitHub confirmou `isDraft: false` após
a rejeição. O teste foi incorporado ao cenário de retomada de release e falhou
antes da correção. O lote de correção verifica a tag antes de criar o rascunho,
cria uma tag ausente somente após resposta explícita HTTP 404, confere o objeto
criado e repete a conferência antes de tornar o rascunho público. Tags divergentes
são preservadas e rejeitadas. O teste corrigido passou, incluindo upload
interrompido, retomada e nova execução idempotente. O formato HTTP 404 usado pelo
GitHub foi conferido por uma leitura real; nenhum erro de autenticação é tratado
como tag ausente.

O único acompanhamento solicitado pelo revisor foi concluído no SHA
`663c784ad6446067903c425a08c4192ccf424490`, mantendo o ponto fixo e o checkpoint
lógico inicial. O agente confirmou a correção da ordem nas linhas 345 e 370 e
executou independentemente os quatro testes direcionados, todos aprovados.
Não encontrou regressões introduzidas pela correção dentro do escopo do achado
e da retomada de uploads. O ciclo está encerrado, sem novo acompanhamento.

Resultado final: um defeito de fonte corrigido e verificado; nenhum achado residual de Spec.

## Validação e limites

Antes da revisão, passaram 11 testes de publicação, três do contrato de aceitação
e três do transporte real de candidatas; `actionlint`, sintaxe Python e diff também
passaram. A execução inicial dos três testes de contrato em um mount somente de
leitura falhou por não poder criar a fixture: foi um erro do invólucro local,
corrigido executando esses testes no host, sem mudar suas asserções ou o produto.
Após a correção, passaram novamente o cenário de release e os três cenários de
origem/ordem de execução GitHub afetados pelo tratamento de erros da API.

Os repositórios Docker Hub públicos e a regra `^[0-9].*$` de tags imutáveis foram
ativados e lidos novamente via API em 2026-09-18. A revisão de fonte não comprova
ativação OIDC, integração, primeiro push público, pull/início da imagem publicada
ou a aceitação física Hyper-V. Esses resultados continuam separados da evidência
local; o fechamento de T13 depende das provas de entrega que ainda faltam.
