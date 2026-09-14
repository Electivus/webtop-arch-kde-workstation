# T08: Inventariar e restaurar programas extras

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

Pacman e AUR têm inventário persistente e restauração assistida; falhas parciais ficam visíveis, com nova tentativa e recuperação disponíveis.

## Acceptance criteria

- [ ] Manter inventário persistente dos programas extras instalados, distinguindo pacotes oficiais de AUR ou pacotes locais e os componentes fornecidos pela imagem.
- [ ] Disponibilizar restauração assistida e um relatório que identifique pacotes restaurados, ausentes, com compilação falha ou que dependam de intervenção.
- [ ] Executar um ensaio de instalação, inventário, recriação e restauração de pacote oficial e de pacote AUR/local representativo, registrando a viabilidade e os limites encontrados.
- [ ] Tratar compatibilidade com a nova base Arch por uma estratégia coerente, incluindo recompilações necessárias; a recuperação não reutiliza cegamente partes arbitrárias de um sistema antigo.
- [ ] Provocar falha de um programa extra e manter o desktop e os aplicativos disponíveis, com relatório, nova tentativa e acesso ao fluxo de recuperação do backup.
- [ ] Comprovar que o inventário integra o backup e é recuperado junto com o estado pessoal.
- [ ] Uma falha em componente fornecido pela variante não pode ser classificada como falha tolerada de programa extra.
- [ ] Entregar testes repetíveis de restauração e falha parcial; caso a abordagem não seja viável, registrar a evidência e retornar ao planejamento antes de prometer recuperação.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: c1f33c4e8e46de56cf622937e8e55f5adea5ffe7
- Decisions: DEC-019, DEC-022, DEC-029, DEC-032

### Decision consequences

- `DEC-019`: Demonstrar a viabilidade da abordagem e explicitar limites de preservação.
- `DEC-022`: Implementar inventário persistente e restauração assistida separados para pacman e AUR/locais.
- `DEC-029`: Integrar o inventário real ao conteúdo recuperável dos backups.
- `DEC-032`: Permitir uso do ambiente atualizado com resultado parcial visível, nova tentativa e recuperação.

## Blocked by

- [T07 / #8](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/8): Fazer backup e recuperar o estado pessoal.
