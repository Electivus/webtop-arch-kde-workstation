# T04: Preservar projetos Linux e trocar arquivos com Windows

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

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
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 9c9f2c44531269dae4d785e4f8b7d197e56f0082
- Decisions: DEC-015

### Decision consequences

- `DEC-015`: Implementar persistência dos projetos no Linux e transferência de arquivos com Windows.

## Blocked by

- [T01 / #2](https://github.com/Electivus/webtop-arch-kde-workstation/issues/2): Abrir e controlar o desktop Arch/KDE pelo Windows.
