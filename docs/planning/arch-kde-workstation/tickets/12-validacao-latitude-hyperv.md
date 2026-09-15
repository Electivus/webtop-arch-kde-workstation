# T12: Validar a entrega no Latitude e preparar o roteiro Hyper-V

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

O candidato é instalado e medido no VMM em Full HD, o perfil de recursos é ajustado e um roteiro executável verifica o destino Hyper-V.

## Acceptance criteria

- [ ] Instalar e exercitar no notebook de teste o candidato identificável produzido pelo CI, registrando seus digests, o backend VMM e o hardware.
- [ ] Validar pelo CMD o fluxo Windows completo disponível: início e parada, aplicações, projetos e Compose, conectividade opcional, backup, recuperação e atualizações, sem executar PowerShell.
- [ ] Medir o uso em uma tela 1920 x 1080 com Insiders, projeto Salesforce e Chrome, incluindo resposta do desktop, CPU e RAM.
- [ ] Separar medições de preparo inicial das partidas seguintes e considerar a carga do Windows e dos demais containers.
- [ ] Partir da proposta de 8 GiB e 6 CPUs lógicas para a VM e entregar o perfil ajustado com as medições que o sustentam e as limitações observadas.
- [ ] Identificar o modo de renderização efetivamente utilizado e comprovar o perfil funcional sem assumir aceleração gráfica não demonstrada.
- [ ] Entregar um roteiro executável pelo CMD de instalação/verificação para o notebook Hyper-V, com diagnóstico de pré-requisitos e resultados identificáveis, funcionando com PowerShell bloqueado.
- [ ] Marcar a execução real no destino como pendente até haver evidência; a conclusão deste ticket não depende de obter acesso remoto ao notebook indisponível nesta sessão.
- [ ] Se o ajuste mudar o candidato, produzir e verificar o candidato resultante antes de associar o relatório à primeira publicação.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 7575b9991bfbd00b514f6f75c0f555b2e9bd7236
- Decisions: DEC-002, DEC-004, DEC-005, DEC-023, DEC-030, DEC-031, DEC-036

### Decision consequences

- `DEC-002`: Entregar o caminho de operação e verificação do destino Hyper-V preservando a ausência de dependência de WSL2.
- `DEC-004`: Validar o perfil final no modelo e configuração de referência.
- `DEC-005`: Produzir evidência de execução identificada como Docker VMM.
- `DEC-023`: Escolher o dimensionamento com base nas medições da carga conjunta.
- `DEC-030`: Preparar evidência local e roteiro de destino mantendo a validação Hyper-V real identificada como pendente.
- `DEC-031`: Usar o cenário Full HD com Insiders, projeto Salesforce e Chrome na avaliação.
- `DEC-036`: Verificar todos os comandos e o atalho pelo CMD e preparar o roteiro Hyper-V sem dependência direta ou indireta de PowerShell.

## Blocked by

- [T05 / #6](https://github.com/Electivus/webtop-arch-kde-workstation/issues/6): Executar Docker e Compose a partir dos projetos Linux.
- [T06 / #7](https://github.com/Electivus/webtop-arch-kde-workstation/issues/7): Preparar proxy e certificados com diagnóstico.
- [T09 / #10](https://github.com/Electivus/webtop-arch-kde-workstation/issues/10): Atualizar a imagem com backup e recuperação.
- [T10 / #11](https://github.com/Electivus/webtop-arch-kde-workstation/issues/11): Atualizar aplicativos independentemente da imagem.
- [T11 / #12](https://github.com/Electivus/webtop-arch-kde-workstation/issues/12): Produzir e testar candidatas no GitHub Actions.
