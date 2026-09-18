# T12 — Revisão de fonte

Revisão independente por dois agentes nativos, executada sequencialmente com contextos separados. Ambos receberam os mesmos objetos Git congelados e não receberam conclusões do outro eixo. Nenhum agente alterou arquivos, executou testes pesados ou operou o tracker.

- Ponto fixo: `144eed60570c33a6d746c49d74f14faf61fd5756`.
- Código revisado: `33f5a07ddf4951f0d5740643e5ff1888336e45a1`.
- Diff: `git diff 144eed60570c33a6d746c49d74f14faf61fd5756...33f5a07ddf4951f0d5740643e5ff1888336e45a1` — 24 arquivos.
- Commits: `89e19f5` e `33f5a07`.
- Planning: `9c9f2c44531269dae4d785e4f8b7d197e56f0082`; preflight final de T12 válido.

## Standards

Fontes: `AGENTS.md`, `docs/agents/{issue-tracker,domain,planning}.md`, `CONTEXT.md` e os doze smells da skill `code-review`. Nenhum padrão de codificação adicional foi encontrado.

Nenhuma violação documentada foi identificada. Os 24 arquivos respeitam o vocabulário de domínio e distinguem ferramentas de medição Windows dos requisitos de operação no destino.

Uma observação de manutenção, sem bloqueio: possível **Duplicated Code** em `distribution/windows/verify-target.cmd`, linhas 51 e 54 no código revisado. Os dois caminhos repetem os argumentos de instalação e diferem pelo argumento opcional `--network-config`. Uma futura mudança de dimensionamento deve atualizar ambos.

Decisão do implementador após conferir a citação: manter os dois comandos explícitos neste escopo. A pequena repetição preserva aspas e o fluxo de erro do CMD, inclusive para caminhos com espaços; não justifica alterar um roteiro já exercitado em Windows. Não há correção de fonte ou acompanhamento de Standards requerido.

Resultado: zero violações; uma observação de manutenção não bloqueante.

## Spec

Fontes: ticket T12, especificação e ledger do esforço, incluindo as decisões de ferramentas e atualizações. O agente confirmou o checkpoint ancestral e leu os objetos no SHA congelado; verificou sintaxe Python/JSON e `git diff --check`.

Nenhum defeito de implementação ou expansão de escopo foi confirmado. O plugin Code Analyzer atende ao pedido do usuário; o preparo preserva a versão existente, recupera a versão registrada quando ausente e atualiza apenas pelo comando explícito. O roteiro usa Python dentro do container, mantendo CMD no Windows. O teste ABNT2 conserva a comparação exata a 250 ms; a imagem não recebe correção de teclado.

Pendências conhecidas, separadas de defeitos de fonte: T12 exige a candidata identificável produzida pelo CI, os fluxos Windows sobre essa candidata, o ensaio Full HD e o relatório de dimensionamento. Os recibos de desenvolvimento não substituem essas provas. A verificação real em Hyper-V permanece pendente conforme o escopo aprovado.

Resultado: zero defeitos de fonte; aceitação em execução ainda pendente. Nenhuma correção ou nova passagem de fonte é solicitada. As evidências finais serão registradas após sua execução, sem reiniciar a revisão a cada commit.

## Evidência final de aceitação

Em 2026-09-18, o CI35227601742 foi confirmado aprovado no SHA33f5a07, com os treze grupos do contrato passando. O mesmo par OCI foi importado com digests preservados e exercitado em cinco operações nativas Windows aprovadas: cenário Latitude Full HD, roteiro de destino, atalho/confiança, navegador/reconexão e atualização/recuperação da imagem. As versões de atualização desse último teste derivam da candidata Salesforce.

[t12-candidate.json](t12-candidate.json) identifica a fonte, os digests e os cinco recibos; [t12-latitude.md](t12-latitude.md) apresenta medidas, perfil e limites. As pendências locais apontadas na revisão inicial foram satisfeitas sem correção adicional da fonte revisada. O merge das proteções públicas já revisadas em PR23 também incorporou o arquivo MIT; a nova candidata pública terá seus próprios testes e digests. A execução física Hyper-V continua pendente por decisão explícita e dispõe do roteiro CMD. O ciclo de revisão permanece encerrado, sem repetição dos eixos.
