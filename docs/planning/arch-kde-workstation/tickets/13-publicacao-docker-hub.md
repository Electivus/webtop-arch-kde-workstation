# T13: Publicar a primeira entrega e automatizar stable

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

As duas imagens aprovadas chegam ao Docker Hub com instruções públicas, tags fixas e stable; entregas posteriores seguem a automação semanal e sob demanda.

## Acceptance criteria

- [ ] Verificar com autenticação a organização, os nomes e as permissões necessários e disponibilizar os dois repositórios públicos confirmados.
- [ ] Publicar os mesmos artefatos aprovados, preservando os digests testados, com versões coordenadas, tags fixas e stable apontando para a entrega aprovada.
- [ ] Ativar a publicação semanal e sob demanda após os testes definidos; falha de teste impede a promoção de stable.
- [ ] Tratar falha parcial de publicação com resultado visível e recuperação ou retomada da promoção, sem anunciar uma entrega coordenada incompleta como concluída.
- [ ] Disponibilizar instruções, comandos CMD e componentes suficientes para um consumidor instalar e operar a workstation partindo de Docker Desktop, sem executar PowerShell e sem precisar acessar o repositório GitHub privado.
- [ ] Verificar o consumo de uma imagem publicada por versão/digest e o fluxo documentado de início, identificando os artefatos efetivamente utilizados.
- [ ] Acompanhar a primeira publicação com a evidência local WSL2 (evidências VMM anteriores permanecem históricas) e o roteiro Hyper-V, deixando o estado da verificação real no destino explícito.
- [ ] Inspecionar o conteúdo distribuído para manter os aplicativos oficiais obtidos na instalação e a ausência de configurações, conteúdo ou credenciais corporativas.
- [ ] Registrar as URLs, versões, digests e resultados da primeira entrega e demonstrar o bloqueio de promoção quando os testes falham.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 9c9f2c44531269dae4d785e4f8b7d197e56f0082
- Decisions: DEC-003, DEC-008, DEC-018, DEC-026, DEC-035, DEC-036, DEC-038

### Decision consequences

- `DEC-003`: Concluir a distribuição da workstation pelo Docker Hub da Electivus.
- `DEC-008`: Entregar imagens e instruções públicas genéricas sem alterar a privacidade do código ou divulgar estado da instalação.
- `DEC-018`: Publicar e verificar tags fixas, stable e a coordenação das duas imagens.
- `DEC-026`: Ativar a publicação automática semanal e sob demanda condicionada aos testes.
- `DEC-038`: Publicar com a evidência local permitida e o roteiro Hyper-V, preservando o estado real da validação de destino.
- `DEC-035`: Disponibilizar os repositórios electivus/webtop-arch-kde-base e electivus/webtop-arch-kde-salesforce.
- `DEC-036`: Publicar instruções e componentes que permitam o fluxo completo pelo CMD com PowerShell bloqueado.

## Blocked by

- [T12 / #13](https://github.com/Electivus/webtop-arch-kde-workstation/issues/13): Validar a entrega no Latitude e preparar o roteiro Hyper-V.
