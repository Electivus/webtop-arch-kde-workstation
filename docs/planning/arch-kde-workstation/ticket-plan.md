# Decomposição em tickets - Planning context

Status em 2026-09-14: os 13 tickets aprovados foram publicados no GitHub como filhos da [especificação #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1), com ready-for-agent e as 17 dependências nativas aprovadas. O [ledger](decision-ledger.md) permanece a fonte das decisões; a cobertura tickets registra as URLs efetivamente publicadas.

A proposta aprovada partiu do checkpoint de cobertura da especificação `c1f33c4e8e46de56cf622937e8e55f5adea5ffe7`. O marcador da issue fonte foi validado contra seu checkpoint declarado e a ancestralidade da branch atual. Após registrar a cobertura dos tickets, o checkpoint final consolida o planejamento, e os marcadores da especificação e dos tickets passam a referenciá-lo. Não havia comentários novos na issue nem código existente que exigisse uma etapa de refatoração prévia.

## Entregas aprovadas

Os identificadores T01-T13 são locais deste plano; sua correspondência com as issues GitHub está no registro de publicação abaixo. Cada entrega inclui o comportamento completo e seus testes de aceitação. As dependências representam requisitos de início; a ordem de execução pode seguir uma tarefa por vez entre as tarefas liberadas.

1. **T01 - Abrir e controlar o desktop Arch/KDE pelo Windows.** Bloqueado por: nenhum. Comando e atalho abrem um desktop local utilizável, com idioma e teclado acordados; fechar a aba mantém a sessão e parar encerra a execução.
2. **T02 - Usar Chrome oficial e terminal preparado na base.** Bloqueado por: T01. A base oferece Chrome, Git e Zsh/Oh My Zsh; a preparação inicial mostra progresso, persiste os aplicativos e retoma falhas.
3. **T03 - Desenvolver Salesforce com Stable e Insiders.** Bloqueado por: T02. A variante Salesforce abre projetos nos dois VS Codes oficiais, com CLI, extensões, Java e Node funcionais; Insiders é o padrão.
4. **T04 - Preservar projetos Linux e trocar arquivos com Windows.** Bloqueado por: T01. Projetos sobrevivem à recriação da workstation e uma pasta de troca permite transferências nos dois sentidos.
5. **T05 - Executar Docker e Compose a partir dos projetos Linux.** Bloqueado por: T04. O terminal controla o Docker Desktop existente; um projeto Compose monta seus arquivos, grava resultados e constrói uma imagem por contexto local.
6. **T06 - Preparar proxy e certificados com diagnóstico.** Bloqueado por: T03. A instalação recebe configuração corporativa opcional e valida a conexão dos aplicativos e da preparação inicial, preservando TLS.
7. **T07 - Fazer backup e recuperar o estado pessoal.** Bloqueado por: T03, T04. Um comando salva e recupera projetos, perfil e aplicativos no Windows, mantém duas cópias concluídas e preserva os backups válidos em caso de falha.
8. **T08 - Inventariar e restaurar programas extras.** Bloqueado por: T07. Pacman e AUR têm inventário persistente e restauração assistida; falhas parciais ficam visíveis, com nova tentativa e recuperação disponíveis.
9. **T09 - Atualizar a imagem com backup e recuperação.** Bloqueado por: T08. O usuário escolhe quando trocar de imagem; o fluxo faz backup, verifica o novo ambiente e reaplica os programas extras sem ocultar falhas.
10. **T10 - Atualizar aplicativos independentemente da imagem.** Bloqueado por: T07. Um comando atualiza editores, Chrome, CLI e extensões, registra versões e permite recuperar o backup correspondente.
11. **T11 - Produzir e testar candidatas no GitHub Actions.** Bloqueado por: T03. Acionamentos semanal e manual produzem as duas imagens candidatas com versões, digests e resultados de testes identificáveis.
12. **T12 - Validar a entrega no Latitude e preparar o roteiro Hyper-V.** Bloqueado por: T05, T06, T09, T10, T11. O candidato é instalado e medido no VMM em Full HD, o perfil de recursos é ajustado e um roteiro executável verifica o destino Hyper-V.
13. **T13 - Publicar a primeira entrega e automatizar stable.** Bloqueado por: T12. As duas imagens aprovadas chegam ao Docker Hub com instruções públicas, tags fixas e stable; entregas posteriores seguem a automação semanal e sob demanda.

## Cobertura das decisões

Todas as 34 decisões ativas declaram a obrigação tickets. Cada entrada abaixo tem pelo menos uma entrega publicada, totalizando 58 associações entre decisões e tickets. Não há decisão ativa sem essa obrigação nem justificativa non-ticket necessária. DEC-014 está substituída por DEC-019 e fica fora do conjunto ativo.

| Decisao | Tickets publicados | Cobertura no ledger |
| --- | --- | --- |
| DEC-001 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-002 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2), [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Completa |
| DEC-003 | [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |
| DEC-004 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2), [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Completa |
| DEC-005 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2), [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Completa |
| DEC-006 | [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3), [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Completa |
| DEC-007 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-008 | [T06 / #7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7), [T11 / #12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12), [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |
| DEC-009 | [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Completa |
| DEC-010 | [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4), [T11 / #12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12) | Completa |
| DEC-011 | [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3), [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4), [T10 / #11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11) | Completa |
| DEC-012 | [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3) | Completa |
| DEC-013 | [T05 / #6](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/6) | Completa |
| DEC-015 | [T04 / #5](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/5), [T05 / #6](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/6), [T07 / #8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8) | Completa |
| DEC-016 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-017 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-018 | [T09 / #10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10), [T11 / #12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12), [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |
| DEC-019 | [T08 / #9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9) | Completa |
| DEC-020 | [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3), [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Completa |
| DEC-021 | [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3), [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4), [T06 / #7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7) | Completa |
| DEC-022 | [T08 / #9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9), [T09 / #10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10) | Completa |
| DEC-023 | [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Completa |
| DEC-024 | [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Completa |
| DEC-025 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-026 | [T11 / #12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12), [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |
| DEC-027 | [T09 / #10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10) | Completa |
| DEC-028 | [T10 / #11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11) | Completa |
| DEC-029 | [T07 / #8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8), [T08 / #9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9), [T09 / #10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10), [T10 / #11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11) | Completa |
| DEC-030 | [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13), [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |
| DEC-031 | [T12 / #13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Completa |
| DEC-032 | [T08 / #9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9), [T09 / #10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10) | Completa |
| DEC-033 | [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Completa |
| DEC-034 | [T06 / #7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7) | Completa |
| DEC-035 | [T11 / #12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12), [T13 / #14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | Completa |

## Aprovação e publicação

Em 2026-09-14, o usuário respondeu "Aprovar os 13 tickets e publicar". A granularidade e as 17 dependências foram aprovadas sem alterações de escopo.

Os tickets foram publicados em ordem de dependências no tracker configurado, com ready-for-agent, marcadores Planning e relacionamentos nativos. A cobertura foi registrada após cada publicação, pelo helper Planning, com as URLs das issues. Todas as obrigações specification e tickets estão completas; o checkpoint final registra essa cobertura. A verificação da implementação permanece pendente.

Os 97 critérios de aceitação aprovados foram preservados. A fronteira inicial contém somente [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2); os demais tickets aguardam seus bloqueadores. Este registro conclui a decomposição e a publicação dos tickets.

## Registro de publicação

| Ticket | Issue GitHub | Bloqueado por | Estado da publicação |
| --- | --- | --- | --- |
| [T01](tickets/01-desktop-local.md) | [#2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Nenhum | Publicado e vinculado |
| [T02](tickets/02-base-chrome-terminal.md) | [#3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3) | [#2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Publicado e vinculado |
| [T03](tickets/03-desenvolvimento-salesforce.md) | [#4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | [#3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3) | Publicado e vinculado |
| [T04](tickets/04-projetos-troca-windows.md) | [#5](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/5) | [#2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2) | Publicado e vinculado |
| [T05](tickets/05-docker-compose-projetos.md) | [#6](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/6) | [#5](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/5) | Publicado e vinculado |
| [T06](tickets/06-conectividade-corporativa.md) | [#7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7) | [#4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Publicado e vinculado |
| [T07](tickets/07-backup-recuperacao.md) | [#8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8) | [#4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4), [#5](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/5) | Publicado e vinculado |
| [T08](tickets/08-restauracao-pacotes.md) | [#9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9) | [#8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8) | Publicado e vinculado |
| [T09](tickets/09-atualizacao-imagem.md) | [#10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10) | [#9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9) | Publicado e vinculado |
| [T10](tickets/10-atualizacao-aplicativos.md) | [#11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11) | [#8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8) | Publicado e vinculado |
| [T11](tickets/11-candidatas-ci.md) | [#12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12) | [#4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4) | Publicado e vinculado |
| [T12](tickets/12-validacao-latitude-hyperv.md) | [#13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | [#6](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/6), [#7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7), [#10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10), [#11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11), [#12](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/12) | Publicado e vinculado |
| [T13](tickets/13-publicacao-docker-hub.md) | [#14](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/14) | [#13](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/13) | Publicado e vinculado |
