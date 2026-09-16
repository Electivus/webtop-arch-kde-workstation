# T10: Atualizar aplicativos independentemente da imagem

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

Um comando atualiza editores, Chrome, CLI e extensões, registra versões e permite recuperar o backup correspondente.

## Acceptance criteria

- [ ] Oferecer comando de atualização de VS Code Stable/Insiders, Chrome, Salesforce CLI e extensões, independente da troca da imagem.
- [ ] Concluir o backup antes de modificar aplicativos e impedir a alteração quando o backup exigido falhar.
- [ ] Registrar versões e origem após a atualização, mantendo lançamento dos dois editores, Insiders como padrão e compatibilidade das extensões.
- [ ] Confirmar que os aplicativos podem ser atualizados sem alterar a versão da imagem e que iniciar a workstation não dispara uma atualização silenciosa dessas ferramentas.
- [ ] Exercitar falha de download ou instalação com resultado identificável e recuperação pelo backup correspondente.
- [ ] Abrir os aplicativos e um projeto de exemplo após atualizar e após recuperar o backup, conferindo versões e estado pessoal.
- [ ] Entregar testes pelos comandos de uso e lançadores, cobrindo atualização, falha e recuperação.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 9c9f2c44531269dae4d785e4f8b7d197e56f0082
- Decisions: DEC-011, DEC-028, DEC-029

### Decision consequences

- `DEC-011`: Preservar os produtos oficiais e a integração das ferramentas solicitadas durante a atualização.
- `DEC-028`: Implementar atualização explícita e independente dos aplicativos com versões efetivas registradas.
- `DEC-029`: Proteger a atualização dos aplicativos com backup consistente e recuperação.

## Blocked by

- [T07 / #8](https://github.com/Electivus/webtop-arch-kde-workstation/issues/8): Fazer backup e recuperar o estado pessoal.
