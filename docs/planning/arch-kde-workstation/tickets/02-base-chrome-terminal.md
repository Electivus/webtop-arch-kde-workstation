# T02: Usar Chrome oficial e terminal preparado na base

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

A base oferece Chrome, Git e Zsh/Oh My Zsh; a preparação inicial mostra progresso, persiste os aplicativos e retoma falhas.

## Acceptance criteria

- [ ] A base permite abrir Google Chrome oficial, usar Git e iniciar um terminal Zsh com Oh My Zsh.
- [ ] Chrome é obtido diretamente do fornecedor no primeiro preparo e mantido no estado persistente; os binários proprietários não são incorporados às camadas públicas.
- [ ] Apresentar progresso e estado do preparo, distinguindo conclusão, execução e falha, e registrar versão, origem e verificação de integridade dos artefatos obtidos.
- [ ] Interromper uma etapa de download ou instalação e retomar pelo fluxo de uso, reaproveitando etapas concluídas e preservando uma instalação já funcional.
- [ ] Reiniciar e recriar a workstation mantendo seu estado pessoal não exige baixar novamente um Chrome já preparado e compatível.
- [ ] Ativar git, zsh-autosuggestions e zsh-syntax-highlighting; verificar uso interativo, preservação das personalizações e ausência de efeitos interativos em execução não interativa.
- [ ] Automatizar a aceitação do preparo e da retomada e comprovar a abertura do Chrome e o uso do terminal no desktop.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 9c9f2c44531269dae4d785e4f8b7d197e56f0082
- Decisions: DEC-006, DEC-011, DEC-012, DEC-020, DEC-021

### Decision consequences

- `DEC-006`: Disponibilizar navegador e terminal utilizáveis para atividades de desenvolvimento.
- `DEC-011`: Entregar Chrome oficial e Git na parte comum do ambiente.
- `DEC-012`: Preparar Zsh e Oh My Zsh com os três plugins selecionados e personalizações preservadas.
- `DEC-020`: Completar a base utilizável com Chrome, Git e terminal preparado.
- `DEC-021`: Implementar o preparo inicial persistente e retomável dos aplicativos, começando por Chrome.

## Blocked by

- [T01 / #2](https://github.com/Electivus/webtop-arch-kde-workstation/issues/2): Abrir e controlar o desktop Arch/KDE pelo Windows.
