# Verificação das configurações públicas

Data: 2026-09-18. Decisão: DEC-040. Base da alteração:
`e5c2f6ea35b36e9cd396b74591360a19c26e91db`.

## Configurações e validação local

- Rulesets ativos `Protect main` (23657276) e `Protect published tags`
  (23657280), sem bypass. A API retornou PR obrigatório, verificações exigidas,
  CodeQL, bloqueio de force push/exclusão da main e alteração/exclusão de tags.
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

Os resultados do PR e a conferência final das configurações serão registrados
após a execução dos novos workflows. Esta mudança configura o repositório e
não valida o notebook Hyper-V nem publica imagens no Docker Hub.
