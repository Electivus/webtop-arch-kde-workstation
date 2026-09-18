# Verificação das configurações públicas

Data: 2026-09-18. Decisão: DEC-041 (substitui DEC-040). Base da alteração:
`e5c2f6ea35b36e9cd396b74591360a19c26e91db`.

## Configurações e validação local

- Rulesets ativos `Protect main` (23657276) e `Protect published tags`
  (23657280), sem bypass. A API retornou PR obrigatório, verificações exigidas,
  CodeQL, bloqueio de force push/exclusão da main e alteração/exclusão de tags.
- Ruleset `Require review with admin PR bypass` (23657404) exige uma aprovação.
  A API confirmou somente `RepositoryRole` Admin (5), em modo `pull_request`,
  como bypass dessa regra. Os outros dois rulesets mantêm bypass vazio.
- Actions restritas ao GitHub e às duas Actions Docker utilizadas, com SHA
  obrigatório. Token padrão somente leitura, sem aprovação de reviews; todos os
  contribuidores externos precisam de aprovação para executar workflows de forks.
- Merge commit habilitado; squash e rebase desabilitados. Exclusão automática
  de branches integradas, atualização de branch e auto-merge disponíveis.
- Alertas de dependências e correções de segurança habilitados. O default setup
  do CodeQL concluiu Go, Python, JavaScript/TypeScript e Actions com sucesso:
  [execução 35345180165](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35345180165).
- Secret scanning, proteção de pushes e relatos privados permanecem ativos.
- `actionlint`, parsing de YAML/JSON e `git diff --check` passaram. O resolvedor
  de política de segurança reconheceu o novo `SECURITY.md` na raiz.
- A imagem Gitleaks fixada por digest no workflow examinou o histórico completo
  da base sem encontrar segredos. Um repositório local descartável contendo uma
  credencial GitHub fictícia foi rejeitado, com código de saída 1 e regra
  `github-pat`. A credencial de teste não foi publicada.

## Alertas existentes

A primeira execução CodeQL abriu cinco alertas de severidade alta nos testes:
`py/insecure-protocol` em `tests/network_fixture.py` e quatro
`py/weak-sensitive-data-hashing` em `tests/browser_acceptance.py`,
`tests/browser_apps.py` e `tests/test_commands.py`.

As ocorrências de SHA-1 calculam identificadores de certificados usados pelo
Windows. Isso contextualiza a triagem, mas não substitui sua validação. Nenhum
alerta foi dispensado e nenhuma pasta foi excluída da análise para obter sucesso.
Os alertas estão na [área de CodeQL](https://github.com/Electivus/webtop-arch-kde-workstation/security/code-scanning).

## Integração

O [PR #23](https://github.com/Electivus/webtop-arch-kde-workstation/pull/23)
exerce as regras com as novas restrições de Actions ativas. No commit
`9e14e3e6d9b63365545a89e8837ed10bb332c99a`,
[Security 35346654169](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35346654169)
passou em `secrets` e `dependency-review`;
[CodeQL 35346652169](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35346652169)
passou nas quatro análises e no check agregado. A API de CODEOWNERS retornou
`errors: []`.

Após adicionar a exigência de aprovação, a leitura do PR retornou
`reviewDecision: REVIEW_REQUIRED` e `mergeStateStatus: BLOCKED`, com o teste
`desktop-lifecycle` ainda em execução. Isso comprova que a exigência de revisão
está efetiva; o bypass não é uma aprovação de autoria própria. A configuração
foi relida pela API de regras efetivas de `main`, além de cada ruleset.

Os checks do PR registram os resultados da revisão final e a integração depende
do sucesso dos testes, usando bypass administrativo somente da aprovação.
Nenhum resultado desse PR comprova Hyper-V ou publica imagens no Docker Hub.
