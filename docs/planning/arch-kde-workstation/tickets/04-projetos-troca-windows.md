# T04: Preservar projetos Linux e trocar arquivos com Windows

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

Projetos sobrevivem à recriação da workstation e uma pasta de troca permite transferências nos dois sentidos.

## Acceptance criteria

- [ ] Disponibilizar um local de projetos no armazenamento Linux do Docker e informar ao usuário como acessá-lo no desktop e no terminal.
- [ ] Salvar um projeto, recriar a workstation conservando seu estado e comprovar conteúdo, nomes e propriedades necessárias ao trabalho Linux.
- [ ] Configurar uma pasta de troca com Windows e comprovar cópia e alteração de arquivos nos dois sentidos.
- [ ] Tratar os pré-requisitos de compartilhamento de diretórios do backend em uso, identificando de forma clara uma configuração necessária ou um caminho indisponível.
- [ ] Manter a distinção entre armazenamento de projetos e pasta de troca, com instruções de uso e evidência repetível pelos comandos e pelos arquivos resultantes.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: e3577ac0ff5e1cdb4719f65bbe821e729a597e2c
- Decisions: DEC-015

### Decision consequences

- `DEC-015`: Implementar persistência dos projetos no Linux e transferência de arquivos com Windows.

## Blocked by

- [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2): Abrir e controlar o desktop Arch/KDE pelo Windows.
