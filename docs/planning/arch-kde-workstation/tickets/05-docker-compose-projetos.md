# T05: Executar Docker e Compose a partir dos projetos Linux

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

O terminal controla o Docker Desktop existente; um projeto Compose monta seus arquivos, grava resultados e constrói uma imagem por contexto local.

## Acceptance criteria

- [ ] Executar Docker e Compose pelo terminal da workstation controlando o mesmo Docker Desktop do notebook, com diagnóstico de acesso ao engine.
- [ ] Definir e documentar uma estratégia de caminhos que permita ao daemon acessar os projetos mantidos no armazenamento Linux.
- [ ] A partir de um projeto de exemplo, construir uma imagem usando contexto local e iniciar seus serviços pelo Compose.
- [ ] Montar arquivos do projeto, produzir alterações por um serviço e conferir os resultados pela workstation; listar containers isoladamente não satisfaz o teste.
- [ ] Verificar o fluxo após recriar a workstation com o projeto persistido e limpar somente os recursos de teste criados.
- [ ] Entregar um cenário repetível do projeto completo, incluindo falha de caminho ou acesso ao engine com diagnóstico utilizável.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: c1f33c4e8e46de56cf622937e8e55f5adea5ffe7
- Decisions: DEC-013, DEC-015

### Decision consequences

- `DEC-013`: Habilitar clientes Docker e Compose no terminal com operações reais sobre o engine existente.
- `DEC-015`: Conciliar o armazenamento Linux dos projetos com os caminhos resolvidos pelo daemon.

## Blocked by

- T04: Preservar projetos Linux e trocar arquivos com Windows.
