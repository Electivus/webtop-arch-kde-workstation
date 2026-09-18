# Configurações do repositório público

Política inicial de 2026-09-18 para
`Electivus/webtop-arch-kde-workstation` (DEC-041, que substitui DEC-040). Os arquivos abaixo registram a
configuração esperada; consulte também o estado efetivo em **Settings** e os
resultados das execuções em **Actions**.

## Integração e histórico

O ruleset [Protect main](../.github/rulesets/main.json) exige PR, branch
atualizada, conversas resolvidas e os checks `desktop-lifecycle`, `secrets` e
`dependency-review`, produzidos pelo GitHub Actions. CodeQL deve fornecer
resultados e bloqueia novos alertas de erro e vulnerabilidades de severidade alta
ou crítica introduzidos pelo PR. Alertas anteriores continuam abertos para triagem.
Force push e exclusão da branch principal são bloqueados, sem atores de bypass.

O ruleset adicional [Require review with admin PR bypass](../.github/rulesets/review.json)
exige **uma aprovação** e permite bypass a `RepositoryRole` Admin (ID 5) somente
em `pull_request`. O GitHub não permite aprovar o próprio PR; nos seus PRs, o
administrador pode dispensar essa aprovação para integrar após os checks.

As regras se acumulam: a aprovação fica separada para que seu bypass não
dispense testes, CodeQL, conversas resolvidas ou as demais proteções de
`Protect main`. O campo de zero aprovações em `main.json` não anula a exigência
de uma aprovação em `review.json`. `CODEOWNERS` encaminha a responsabilidade
ao mantenedor `@manoelcalixto`.

Somente **merge commit** é permitido. Squash, rebase e a exigência de histórico
linear são incompatíveis com a preservação dos SHAs de Planning checkpoints
referenciados pelas especificações e tickets. A opção de atualizar a branch
está disponível; auto-merge depende de habilitação explícita em cada PR e não
ignora as regras. Branches de PRs integrados são removidas automaticamente.

O ruleset [Protect published tags](../.github/rulesets/tags.json) permite criar
tags Git, mas impede alterar ou excluir tags existentes. Isso não controla as
tags de imagens no Docker Hub, que seguem o fluxo de distribuição.

## Actions e dependências

- O token padrão tem apenas leitura e não pode aprovar PRs. Workflows que
  precisarem de escrita devem declarar a permissão específica e justificar seu
  uso. Os checkouts do projeto não persistem credenciais Git.
- Todos os contribuidores externos precisam de aprovação para executar
  workflows originados de forks. São permitidas Actions do GitHub e as duas
  Actions Docker já utilizadas (`docker/setup-docker-action` e
  `docker/setup-buildx-action`), exigindo referências de commit completas.
- O workflow [Security](../.github/workflows/security.yml) verifica todo o
  histórico Git com Gitleaks fixado por digest, sem rede dentro do scanner e
  com valores sensíveis ocultos na saída. Não há chave comercial do Gitleaks.
  A versão desse scanner deve ser revisada manualmente ao atualizá-lo.
- A revisão de dependências dos PRs rejeita vulnerabilidades novas de nível
  alto ou crítico. Alertas existentes continuam disponíveis para triagem.
- [Dependabot](../.github/dependabot.yml) propõe atualizações semanais de Actions
  e das imagens ancestrais de `/images/base`. GitHub também mantém alertas e
  propostas de correções de segurança para os ecossistemas que reconhece.
  Pacotes instalados pelo pacman e aplicativos preparados no volume não são
  cobertos integralmente pelo grafo de dependências do GitHub.
- CodeQL usa o **default setup** gerenciado pelo GitHub para Go, Python,
  JavaScript/TypeScript e Actions, com a suíte padrão e execução semanal além
  dos eventos de desenvolvimento. Não há um segundo workflow CodeQL duplicado.

## Relatos e manutenção

Secret scanning, proteção de pushes e relatos privados de vulnerabilidades
permanecem habilitados. [SECURITY.md](../SECURITY.md) define o canal e os limites
do produto; [CONTRIBUTING.md](../CONTRIBUTING.md) descreve o fluxo de contribuição.
Os formulários de issues orientam a enviar apenas exemplos e logs sem dados
sensíveis. Nenhuma dessas configurações aprova automaticamente uma candidata
ou comprova execução em Hyper-V.

Um administrador pode ler a configuração efetiva com:

```sh
gh api repos/Electivus/webtop-arch-kde-workstation/rulesets
gh api repos/Electivus/webtop-arch-kde-workstation/rules/branches/main
gh api repos/Electivus/webtop-arch-kde-workstation/actions/permissions
gh api repos/Electivus/webtop-arch-kde-workstation/actions/permissions/selected-actions
gh api repos/Electivus/webtop-arch-kde-workstation/actions/permissions/workflow
gh api repos/Electivus/webtop-arch-kde-workstation/code-scanning/default-setup
gh api repos/Electivus/webtop-arch-kde-workstation/private-vulnerability-reporting
```

Para alterar uma regra, revise o JSON correspondente por PR e atualize o ruleset
existente pelo seu ID. Preserve regras e configurações que não pertençam à
alteração. Não crie regras duplicadas nem use bypass para ocultar falhas de CI.
