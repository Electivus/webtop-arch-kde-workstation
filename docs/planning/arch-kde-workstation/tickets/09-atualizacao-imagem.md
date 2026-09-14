# T09: Atualizar a imagem com backup e recuperação

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

O usuário escolhe quando trocar de imagem; o fluxo faz backup, verifica o novo ambiente e reaplica os programas extras sem ocultar falhas.

## Acceptance criteria

- [ ] Oferecer um comando para escolher e aplicar uma nova imagem, registrando a versão e o digest efetivamente selecionados.
- [ ] Publicar ou disponibilizar uma nova referência stable de ensaio não altera a workstation existente até o comando explícito.
- [ ] Concluir o backup antes da troca; se o backup falhar, a atualização não deve alterar o ambiente ativo.
- [ ] Aplicar a imagem selecionada, preservar projetos e perfil e executar as verificações dos componentes fornecidos antes de declarar o novo ambiente utilizável.
- [ ] Integrar a restauração assistida dos programas extras, distinguindo falhas toleradas desses programas de falhas nos componentes fornecidos.
- [ ] Expor o resultado da atualização, a versão anterior e o backup correspondente, permitindo recuperação explícita do estado anterior.
- [ ] Exercitar por comandos públicos uma atualização bem-sucedida, falha de backup, falha do novo ambiente e resultado parcial de pacote extra.
- [ ] Usar imagens versionadas de ensaio para a aceitação, sem depender da primeira publicação pública no Docker Hub.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: c1f33c4e8e46de56cf622937e8e55f5adea5ffe7
- Decisions: DEC-018, DEC-022, DEC-027, DEC-029, DEC-032

### Decision consequences

- `DEC-018`: Resolver a referência escolhida em uma versão e digest identificáveis, preservando o significado de tags fixas e stable.
- `DEC-022`: Usar o inventário e a restauração assistida após a troca da imagem.
- `DEC-027`: Entregar atualização da imagem sob controle do usuário, com backup concluído antes da troca.
- `DEC-029`: Acoplar o backup consistente à operação de atualização da imagem.
- `DEC-032`: Preservar a distinção entre atualização utilizável com falhas extras e falha de componente obrigatório.

## Blocked by

- T08: Inventariar e restaurar programas extras.
