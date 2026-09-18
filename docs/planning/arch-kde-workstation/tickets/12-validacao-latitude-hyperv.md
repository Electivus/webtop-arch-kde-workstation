# T12: Validar a entrega no Latitude e preparar o roteiro Hyper-V

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

O candidato é instalado e medido no Docker Desktop com WSL2 em Full HD, o perfil de recursos é ajustado e um roteiro executável verifica o destino Hyper-V.

## Acceptance criteria

- [x] Instalar e exercitar no notebook de teste o candidato identificável produzido pelo CI, registrando seus digests, o backend WSL2 e o hardware.
- [x] Validar pelo CMD o fluxo Windows completo disponível: início e parada, aplicações, projetos e Compose, conectividade opcional, backup, recuperação e atualizações, sem executar PowerShell.
- [x] Medir o uso em uma tela 1920 x 1080 com Insiders, projeto Salesforce e Chrome, incluindo resposta do desktop, CPU e RAM.
- [x] Separar medições de preparo inicial das partidas seguintes e considerar a carga do Windows e dos demais containers.
- [x] Partir da proposta de 8 GiB e 6 CPUs lógicas para a VM e entregar o perfil ajustado com as medições que o sustentam e as limitações observadas.
- [x] Identificar o modo de renderização efetivamente utilizado e comprovar o perfil funcional sem assumir aceleração gráfica não demonstrada.
- [x] Entregar um roteiro executável pelo CMD de instalação/verificação para o notebook Hyper-V, com diagnóstico de pré-requisitos e resultados identificáveis, funcionando com PowerShell bloqueado.
- [x] Marcar a execução real no destino como pendente até haver evidência; a conclusão deste ticket não depende de obter acesso remoto ao notebook indisponível nesta sessão.
- [x] Se o ajuste mudar o candidato, produzir e verificar o candidato resultante antes de associar o relatório à primeira publicação.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 0dee9084ec3f3e1ad0fdb93a029a5c28a42d9d70
- Decisions: DEC-002, DEC-004, DEC-023, DEC-031, DEC-036, DEC-037, DEC-038

### Decision consequences

- `DEC-002`: Entregar o caminho de operação e verificação do destino Hyper-V preservando a ausência de dependência de WSL2.
- `DEC-004`: Validar o perfil final no modelo e configuração de referência.
- `DEC-037`: Produzir evidência de execução identificada como Docker Desktop com WSL2.
- `DEC-023`: Escolher o dimensionamento com base nas medições da carga conjunta.
- `DEC-038`: Preparar evidência local e roteiro de destino mantendo a validação Hyper-V real identificada como pendente.
- `DEC-031`: Usar o cenário Full HD com Insiders, projeto Salesforce e Chrome na avaliação.
- `DEC-036`: Verificar todos os comandos e o atalho pelo CMD e preparar o roteiro Hyper-V sem dependência direta ou indireta de PowerShell.

## Blocked by

- [T05 / #6](https://github.com/Electivus/webtop-arch-kde-workstation/issues/6): Executar Docker e Compose a partir dos projetos Linux.
- [T06 / #7](https://github.com/Electivus/webtop-arch-kde-workstation/issues/7): Preparar proxy e certificados com diagnóstico.
- [T09 / #10](https://github.com/Electivus/webtop-arch-kde-workstation/issues/10): Atualizar a imagem com backup e recuperação.
- [T10 / #11](https://github.com/Electivus/webtop-arch-kde-workstation/issues/11): Atualizar aplicativos independentemente da imagem.
- [T11 / #12](https://github.com/Electivus/webtop-arch-kde-workstation/issues/12): Produzir e testar candidatas no GitHub Actions.

## Verification

Aceitacao local concluida em 2026-09-18. Fonte revisada `33f5a07`, candidata `2026.09.17-35227601742-1`, evidencias finais no commit `a0978cda363c4034416a79d098a8979b4e092fa9`. O merge do estado publico ja revisado e preservado no historico; a nova candidata de publicacao sera identificada em T13. Execucao real Hyper-V pendente.

- DEC-002 | CI35227601742 native CMD destination guide passed installation, prerequisites, applications, projects, Compose, exchange, backup and restoration; real Hyper-V remains pending. docs/verification/t12-candidate.json.
- DEC-004 | Latitude5450 CoreUltra7165U, 32GB and one1920x1080 display measured with the exact33f5a07 candidate and preserved OCI digests. docs/verification/t12-latitude.json.
- DEC-011 | Both VS Codes, Salesforce tools and Code Analyzer preparation/update/recovery were verified; FullHD scenario opened the generic Salesforce project in Insiders. docs/verification/t12-code-analyzer.md.
- DEC-023 | Container6GiB/4CPU sustained the tested workload at5.561GiB peak; Windowsavailable3.586GiB minimum and other-container load recorded. ActualWSL VM15.35GiB/14CPU is distinguished from unvalidated HyperV8GiB/6CPU proposal.
- DEC-028 | Explicit CodeAnalyzer update preserved version receipts and absent-plugin preparation restored the recorded version; final native image-update/recovery retained functional applications. docs/verification/t12-code-analyzer.md; docs/verification/t12-candidate.json.
- DEC-031 | FullHD Insiders+Salesforce project+Chrome passed with120s/29resource samples,10visual response samples57.7-120.5ms and software CPU encoder evidence. docs/verification/t12-latitude.md.
- DEC-036 | All five final native Windows operations passed using the candidate CMD/controller bytes, including shortcut, certificate trust, browser reconnect and image update/recovery; no product PowerShell/hostPython dependency. docs/verification/t12-candidate.json.
- DEC-037 | Current acceptance reports DockerDesktop29.8.0 WSL2 kernel6.18.35.2 and actual engine resources; historical VMM results are not presented as new evidence.
- DEC-038 | Approved CI pair passed all13groups and all5final native operations. HyperV physical validation remains explicitly pending with CMD guide; the new MIT-containing public candidate needs its own CI identity in T13.
