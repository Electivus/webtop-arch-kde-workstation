# Revisão delimitada das atualizações

Os dois eixos revisaram o checkpoint `4657086af926c1e27195793ef74a4a395844881a`, com ponto fixo `97f539dea2742fdf349c2f188ca6e1fffd72ae4d`. A migração para Electivus foi incorporada pelo merge `5cd2549f5e4cecf49059fe953bb5bed663deb8fc`, preservando as alterações de manutenção.

## Standards

Nenhuma violação documentada. A observação P3 sobre duplicação da leitura, persistência e registro de falhas foi tratada pelo relatório compartilhado de atualização, necessário também para reconhecer interrupções. O revisor não solicitou nova passagem desse eixo.

## Spec

Os dois achados P2 foram reproduzidos pelos comandos entregues:

- **Perfil antigo sem container:** mover a tag e perder o container antes de adotar `imageId` permitia iniciar a imagem nova no volume existente. O teste falhou em 49,649 s. A seleção agora exige recuperar a identidade original; iniciar, fazer backup e atualizar recusam a substituição implícita. Um backup da própria instalação recupera a imagem anterior e seu arquivo pessoal. O cenário passou em 59,426 s, com recibo em `.local/ew-image-legacy-lost-7acc9bf581/lost-legacy-result.json`.
- **Comando do host encerrado:** os dois relatórios continuavam em `running` depois de matar o processo real. O teste reproduziu ambos os erros em 82,096 s. Cada atualização agora mantém sua própria trava de processo; consultas compartilham a trava de leitura e distinguem término anormal de execução ativa. Não usam PID nem inventam horário de conclusão. A correção passou em 80,028 s, incluindo outra atualização ativa sem reativar o relatório anterior, preservação da etapa e início explícito posterior. Recibo: `.local/ew-update-interrupted-3ff70fb5af/host-interruption-result.json`.

O teste de interrupção estabiliza uma solicitação de parada do Docker que pode sobreviver ao processo do host. O primeiro ensaio dessa fixture encontrou essa corrida adicional; a repetição estabilizada acima demonstrou os dois erros esperados. Recibos iniciais que haviam sido marcados incorretamente após falhas de subtestes foram corrigidos para `failed`; a fixture passou a registrar o resultado efetivo.

O revisor Spec solicitou uma única passagem de acompanhamento para esses achados e regressões das correções. Essa passagem e o fechamento Planning ainda serão registrados após a validação.

## Regressão e identidade dos artefatos

Na regressão anterior, os cinco cenários de aplicativos passaram em 1.916,652 s. Seis cenários de imagem passaram; o registry descartável falhou no primeiro envio. O evento Docker `oom` de 2026-09-15 às 14:52:47 UTC identifica exatamente o container `ew-image-registry-567ed03890-registry`, então limitado a 512 MiB. A fixture agora dispõe de 1 GiB, limita a memória gerenciada do Go a 768 MiB e preserva logs e inspeção antes de remover seu serviço. Nenhuma asserção foi removida.

As imagens reconstruídas para a regressão desta correção são:

| Artefato | Identidade |
| --- | --- |
| Base | `sha256:3549c411e14d788f0c5aae543b876ae6a38f13878c5ca49651a6937261855e2d` |
| Salesforce | `sha256:0c277289da5a0541bad634a622f5f9ceb6912f2d0e2f73e123d03e0f942e1040` |
| Executável Windows | SHA-256 `3ce8843aaace37a60a8b79f94dabb50ca8463c0b9bb54c03ee97578783edf91f` |

O executável entregue e os exemplares dentro das duas imagens têm o mesmo hash. O estágio de construção executou gofmt, go vet para Linux e Windows e as duas compilações. A análise sintática dos testes Python e `git diff --check` passaram.

A regressão iniciada em `.local/t09-t10-review-regression/` ficou interrompida durante a migração; seu estado histórico `running`, sem resultado final, não constitui aprovação nem processo ainda ativo. A regressão ampla anterior dos demais componentes está documentada em `.local/t09-t10-regression-after-diagnostic/result.json` e nos documentos anteriores de verificação. Estes artefatos de desenvolvimento não representam publicação pública nem aceitação Hyper-V.

A retomada em 2026-09-16 usa Docker Desktop com WSL2, conforme DEC-037/DEC-038. Os dois cenários das correções passaram também pelo controlador Linux: recuperação do perfil legado em 29,396 s e interrupção do comando em 41,241 s. A preparação e a correção da incompatibilidade de nginx encontrada ao reconstruir as imagens estão em [Retomada WSL2](wsl2-resume.md). A regressão Windows das imagens reconstruídas e o acompanhamento Spec permanecem necessários antes do fechamento.
