# Decomposição em tickets - Planning context

Status: proposta para revisão do usuário; nenhum ticket filho foi publicado. Fonte: [especificação #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1). O [ledger](decision-ledger.md) permanece a fonte das decisões; a cobertura abaixo é uma proposta, sem avançar a obrigação tickets.

O checkpoint da especificação é `c1f33c4e8e46de56cf622937e8e55f5adea5ffe7`. O marcador da issue fonte foi validado contra seu checkpoint declarado e a ancestralidade da branch atual. Não há comentários novos na issue nem código existente que exija uma etapa de refatoração prévia.

## Entregas propostas

Os identificadores T01-T13 são locais desta proposta, não números de issues GitHub. Cada entrega inclui o comportamento completo e seus testes de aceitação. As dependências representam requisitos de início; a ordem de execução pode seguir uma tarefa por vez entre as tarefas liberadas.

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

## Cobertura antes da redação dos tickets

Todas as 34 decisões ativas declaram a obrigação tickets. Cada entrada abaixo tem pelo menos uma entrega proposta. Não há decisão ativa sem essa obrigação nem justificativa non-ticket necessária. DEC-014 está substituída por DEC-019 e fica fora do conjunto ativo.

| Decisao | Tickets propostos | Cobertura no ledger |
| --- | --- | --- |
| DEC-001 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-002 | [T01](tickets/01-desktop-local.md), [T12](tickets/12-validacao-latitude-hyperv.md) | Pendente de aprovacao e publicacao |
| DEC-003 | [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |
| DEC-004 | [T01](tickets/01-desktop-local.md), [T12](tickets/12-validacao-latitude-hyperv.md) | Pendente de aprovacao e publicacao |
| DEC-005 | [T01](tickets/01-desktop-local.md), [T12](tickets/12-validacao-latitude-hyperv.md) | Pendente de aprovacao e publicacao |
| DEC-006 | [T02](tickets/02-base-chrome-terminal.md), [T03](tickets/03-desenvolvimento-salesforce.md) | Pendente de aprovacao e publicacao |
| DEC-007 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-008 | [T06](tickets/06-conectividade-corporativa.md), [T11](tickets/11-candidatas-ci.md), [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |
| DEC-009 | [T03](tickets/03-desenvolvimento-salesforce.md) | Pendente de aprovacao e publicacao |
| DEC-010 | [T03](tickets/03-desenvolvimento-salesforce.md), [T11](tickets/11-candidatas-ci.md) | Pendente de aprovacao e publicacao |
| DEC-011 | [T02](tickets/02-base-chrome-terminal.md), [T03](tickets/03-desenvolvimento-salesforce.md), [T10](tickets/10-atualizacao-aplicativos.md) | Pendente de aprovacao e publicacao |
| DEC-012 | [T02](tickets/02-base-chrome-terminal.md) | Pendente de aprovacao e publicacao |
| DEC-013 | [T05](tickets/05-docker-compose-projetos.md) | Pendente de aprovacao e publicacao |
| DEC-015 | [T04](tickets/04-projetos-troca-windows.md), [T05](tickets/05-docker-compose-projetos.md), [T07](tickets/07-backup-recuperacao.md) | Pendente de aprovacao e publicacao |
| DEC-016 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-017 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-018 | [T09](tickets/09-atualizacao-imagem.md), [T11](tickets/11-candidatas-ci.md), [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |
| DEC-019 | [T08](tickets/08-restauracao-pacotes.md) | Pendente de aprovacao e publicacao |
| DEC-020 | [T02](tickets/02-base-chrome-terminal.md), [T03](tickets/03-desenvolvimento-salesforce.md) | Pendente de aprovacao e publicacao |
| DEC-021 | [T02](tickets/02-base-chrome-terminal.md), [T03](tickets/03-desenvolvimento-salesforce.md), [T06](tickets/06-conectividade-corporativa.md) | Pendente de aprovacao e publicacao |
| DEC-022 | [T08](tickets/08-restauracao-pacotes.md), [T09](tickets/09-atualizacao-imagem.md) | Pendente de aprovacao e publicacao |
| DEC-023 | [T12](tickets/12-validacao-latitude-hyperv.md) | Pendente de aprovacao e publicacao |
| DEC-024 | [T03](tickets/03-desenvolvimento-salesforce.md) | Pendente de aprovacao e publicacao |
| DEC-025 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-026 | [T11](tickets/11-candidatas-ci.md), [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |
| DEC-027 | [T09](tickets/09-atualizacao-imagem.md) | Pendente de aprovacao e publicacao |
| DEC-028 | [T10](tickets/10-atualizacao-aplicativos.md) | Pendente de aprovacao e publicacao |
| DEC-029 | [T07](tickets/07-backup-recuperacao.md), [T08](tickets/08-restauracao-pacotes.md), [T09](tickets/09-atualizacao-imagem.md), [T10](tickets/10-atualizacao-aplicativos.md) | Pendente de aprovacao e publicacao |
| DEC-030 | [T12](tickets/12-validacao-latitude-hyperv.md), [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |
| DEC-031 | [T12](tickets/12-validacao-latitude-hyperv.md) | Pendente de aprovacao e publicacao |
| DEC-032 | [T08](tickets/08-restauracao-pacotes.md), [T09](tickets/09-atualizacao-imagem.md) | Pendente de aprovacao e publicacao |
| DEC-033 | [T01](tickets/01-desktop-local.md) | Pendente de aprovacao e publicacao |
| DEC-034 | [T06](tickets/06-conectividade-corporativa.md) | Pendente de aprovacao e publicacao |
| DEC-035 | [T11](tickets/11-candidatas-ci.md), [T13](tickets/13-publicacao-docker-hub.md) | Pendente de aprovacao e publicacao |

## Revisão necessária

Aprovar ou ajustar a granularidade, as dependências e eventuais fusões ou divisões. A publicação dos tickets e o registro de cobertura no ledger aguardam essa revisão.

Após a aprovação, publicar em ordem de dependências no tracker configurado, com ready-for-agent, marcadores Planning e relacionamentos nativos. Registrar a cobertura com as URLs efetivamente publicadas e criar o checkpoint final somente quando todas as obrigações specification e tickets estiverem cobertas.
