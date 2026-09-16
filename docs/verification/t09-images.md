# T09: atualização explícita da imagem

Ticket [#10](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/10). O corpo completo passou pelo preflight após incorporar T08 em `97f539dea2742fdf349c2f188ca6e1fffd72ae4d`, sobre o checkpoint final `7575b9991bfbd00b514f6f75c0f555b2e9bd7236`, para DEC-018, DEC-022, DEC-027, DEC-029 e DEC-032. O mesmo commit de integração é o ponto fixo da futura revisão T09/T10.

## Seleção preservada ao recriar

O primeiro teste usa duas imagens de ensaio derivadas da base, com versões `1.0.0-t09` e `1.1.0-t09`. A tag `stable` começa apontando para a primeira e depois é movida para a segunda. Parar e iniciar o container existente preservava a seleção, mas remover o container e iniciar novamente alterou a imagem sem uma atualização explícita. O teste reproduziu essa falha em **88,353 s**.

A correção persiste o identificador da imagem durante a primeira criação. Perfis anteriores adotam a imagem efetiva do container existente. A recriação passa a usar esse identificador, preservando a referência escolhida para consulta. Uma imagem selecionada indisponível deve produzir erro; a presença de uma tag que agora aponta para outra imagem não autoriza avançar. O backup e a recuperação foram ajustados para conservar a seleção correta com o campo opcional novo, mantendo leitura dos perfis antigos.

Os comandos passaram por gofmt, go vet Windows/Linux e builds nativos. O mesmo teste passou em **76,816 s**: preservou a seleção e o arquivo pessoal ao recriar e, depois de remover a imagem escolhida, informou sua ausência sem usar a tag movida nem remover o volume pessoal. Log: `.local/t09-image-selection-first-green.log`; recibo: `.local/ew-image-pin-1c45d045aa/selection-result.json`.

## Troca explícita e recuperação

O segundo teste prepara Chrome, um projeto pessoal, o pacote oficial `figlet` e um programa C com fonte registrada. Depois move a tag de ensaio e solicita uma atualização explícita. O primeiro resultado foi uma falha em **84,736 s**, porque o comando e sua opção de seleção local ainda não existiam.

A implementação resolve a imagem escolhida, registra separadamente seu identificador Docker e as associações de digest informadas pelo engine, conclui o backup antes de substituir o container e conserva o volume pessoal. A restauração assistida dos extras e a preparação antecedem verificações reais do desktop, Git, shell, terminal, Docker/Compose e renderização Chrome. O relatório mantém imagem anterior, seleção, backup, etapas e diagnósticos; só marca o novo ambiente utilizável depois das verificações.

Na primeira execução após a implementação, a atualização e suas verificações concluíram. O teste parou em **100,283 s** por esperar que uma imagem local tivesse `repositoryDigests` vazio. Este Docker informou uma associação válida para a construção local, reproduzida corretamente no relatório. A expectativa foi corrigida para usar os metadados reais do engine como referência; essa falha de expectativa não é classificada como defeito do produto.

O caso completo passou em **174,950 s**. A nova imagem restaurou `figlet` e recompilou o programa pessoal, manteve os aplicativos e configurações, renderizou o projeto e registrou as verificações executadas. A recuperação selecionou a imagem anterior, devolveu os aplicativos e o projeto originais e restaurou os extras a partir das fontes recuperadas. Recibo: `.local/ew-image-update-eb9a95ef89/image-update-result.json`; log: `.local/t09-image-update-second-green.log`.

## Falhas de backup, componente fornecido e programa extra

Os três casos seguintes passaram sem outra mudança de produção:

- **Backup, 63,226 s:** um destino ocupado por arquivo falha antes da parada; um certificado de arquivo danificado falha depois. Perfil, imagem, container, aplicativos e projeto permanecem os mesmos. A retomada posterior mantém a rede já aplicada e alcança o fornecedor mesmo com um proxy recusador pendente. Recibo: `.local/ew-image-backup-6d0a96cf72/image-backup-failures-result.json`.
- **Componente fornecido, 133,106 s:** a candidata mantém o registro do pacote Git, mas seu executável retorna 73. A verificação real produz `failed` com `usable: false` e mantém o backup. A recuperação devolve a imagem anterior, o Git funcional, os aplicativos e o projeto. Recibo: `.local/ew-image-core-4fa17d9007/provided-failure-result.json`.
- **Programa extra, 105,469 s:** uma fonte pessoal com erro real de compilação impede sua reconstrução e a do pacote debug. O resultado é `partial` com `usable: true`; as seis verificações dos componentes fornecidos passam, `figlet` funciona e o Chrome renderiza o projeto. Depois de corrigir a fonte, `packages --restore` recupera o programa na imagem atualizada, preservando o histórico da atualização. Recibo: `.local/ew-image-extra-bdac1d3afa/extra-failure-result.json`.

## Registry, perfil antigo e variante Salesforce

O ensaio com registry passou em **178,647 s**. Um serviço dedicado ao teste, limitado ao loopback da VM, recebeu as duas imagens completas de ensaio. Mover `stable` no registry não alterou o ambiente ao parar e iniciar; `update-image` fez o pull explícito e selecionou a nova versão. Depois, uma seleção pelo digest antigo recuperou a versão anterior, mantendo o projeto nos dois casos. A consulta HTTP independente conferiu o SHA-256 dos bytes do manifesto e o cabeçalho `Docker-Content-Digest`. Recibo: `.local/ew-image-registry-ca0aa5287f/registry-selection-result.json`; log: `.local/t09-image-registry-first.log`.

O registry de teste usa `registry@sha256:1be55279f18a2fe1a74edf2664cac61c1bea305b7b4642dab412e7affdcb3e33`, verificado na origem. Os recursos próprios foram removidos ao terminar. Não houve publicação externa, alteração nas configurações do engine ou novo compartilhamento de arquivos Windows.

A compatibilidade com perfil anterior passou em **53,424 s**. O teste remove somente o novo campo do seu perfil descartável, move a tag e chama o comando atualizado. Ele adota a imagem do container existente e preserva essa seleção e o arquivo pessoal após remover e recriar o container. Isso verifica a leitura do perfil antigo pelo executável novo; não representa atualização automática de um executável anteriormente copiado. Log: `.local/t09-image-legacy-first.log`.

O caso completo de troca e recuperação também passou com a variante Salesforce em **802,017 s**. Além dos extras oficial e compilado, preservou um projeto criado pela CLI Salesforce e seu `sfdx-project.json`. Os serviços reais verificaram diagnóstico, correção e conclusão Apex e conclusão LWC no Stable e no Insiders, tanto depois da troca quanto depois da recuperação. Os quatro recibos de serviços foram lidos e confirmaram sucesso; o Chrome renderizou o projeto e o Insiders permaneceu como editor padrão. Recibos: `.local/ew-image-update-0713addb1c/`; log: `.local/t09-salesforce-image-update-first.log`.

## Fechamento

ShellCheck, análise sintática Python e leitura do workflow com Mike Farah yq passaram. Os ensaios descritos acima são históricos, feitos em Docker VMM. A [revisão delimitada](t09-t10-review.md) foi concluída, e a [regressão final em WSL2](wsl2-resume.md#fechamento-da-regressão-windows-em-wsl2) aprovou os oito cenários da base e a troca/recuperação Salesforce, incluindo os serviços Apex/LWC dos dois editores. Nenhuma dessas execuções representa aceitação no Hyper-V.
