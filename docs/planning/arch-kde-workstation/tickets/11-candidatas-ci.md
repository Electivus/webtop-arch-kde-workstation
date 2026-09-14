# T11: Produzir e testar candidatas no GitHub Actions

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

Acionamentos semanal e manual produzem as duas imagens candidatas com versões, digests e resultados de testes identificáveis.

## Acceptance criteria

- [ ] Disponibilizar GitHub Actions acionável sob demanda e por agenda semanal para construir as duas imagens candidatas a partir do mesmo estado do código.
- [ ] Produzir Salesforce da base candidata correspondente e registrar arquitetura, versão coordenada, digests e relação entre as imagens.
- [ ] Executar a aceitação automatizável disponível por um contrato de validação comum, incorporando os cenários que forem entregues pelos demais tickets.
- [ ] Disponibilizar os artefatos candidatos e seus resultados para instalação e validação local, identificando exatamente o conteúdo que será testado.
- [ ] Uma falha de construção ou teste impede declarar a candidata aprovada e deixa diagnóstico e resultado acessíveis.
- [ ] Manter os nomes previstos dos artefatos e preservar o conteúdo público genérico, sem incorporar estado pessoal ou binários proprietários preparados durante os testes.
- [ ] Demonstrar uma execução bem-sucedida e uma execução com falha de teste; a promoção pública de stable será ativada pelo ticket de publicação.
- [ ] Documentar como consumir o mesmo candidato no notebook de teste e como relacionar um resultado ao código e aos digests utilizados.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: e3577ac0ff5e1cdb4719f65bbe821e729a597e2c
- Decisions: DEC-008, DEC-010, DEC-018, DEC-026, DEC-035

### Decision consequences

- `DEC-008`: Produzir artefatos candidatos genéricos e separar deles o estado usado durante a aceitação.
- `DEC-010`: Construir a família de duas imagens com herança direta e conteúdo coordenado.
- `DEC-018`: Identificar candidatas por versão, digests e relação entre base e Salesforce.
- `DEC-026`: Entregar a produção e os testes semanais e sob demanda, preparando a promoção condicionada aos resultados.
- `DEC-035`: Usar os nomes confirmados nos artefatos e metadados de distribuição.

## Blocked by

- [T03 / #4](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4): Desenvolver Salesforce com Stable e Insiders.
