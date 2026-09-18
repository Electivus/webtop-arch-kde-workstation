# T12 — Validação local no Latitude

Ensaio de 2026-09-18 no Dell Latitude 5450, Intel Core Ultra 7 165U, 32 GB de RAM,
uma tela física 1920×1080. O Docker Desktop 29.8.0 executou containers Linux pelo
backend **WSL2**, kernel `6.18.35.2-microsoft-standard-WSL2`.
A verificação real no notebook **Hyper-V permanece pendente**.

## Candidata identificada

Foi importado o mesmo par aprovado no [CI 35227601742](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35227601742),
versão `2026.09.17-35227601742-1`, código e validador
`33f5a07ddf4951f0d5740643e5ff1888336e45a1`. Os treze grupos do contrato de aceitação
passaram. Os hashes dos arquivos OCI e dos comandos foram conferidos e a importação
preservou os índices OCI:

| Variante | Digest |
| --- | --- |
| Base | `sha256:54a82d2cacd384e06ced2e9e713b701f563e6f55ec947c1d039b9bb5a007a6df` |
| Salesforce | `sha256:430ca4d5abdf50f111df696ac0c401882360a6b2cb523522f7763bf0b11800e2` |

O controlador Windows foi extraído desses artefatos; seu SHA-256 é
`fba6ce1b23bcb1efe7ddc37a135536760dc6bcdb7099a01e906e9a1d5c407ea2`.
O Python Windows e a instrumentação de navegador serviram apenas ao ensaio.
Os comandos distribuídos e o roteiro de destino usam CMD e o executável
autossuficiente; o Python do roteiro executa dentro do container.

Esta candidata antecede a inclusão do arquivo MIT da Electivus no pacote da
imagem pública. T13 deve publicar uma nova candidata que inclua esse arquivo e
identificar seus próprios digests. Estes números de desempenho continuam
atribuídos à candidata acima, sem substituição silenciosa pela versão publicada.

## Recursos e desempenho

O container Salesforce usou **6 GiB de RAM e 4 CPUs lógicas**. O engine realmente
observado tinha **15,35 GiB e 14 CPUs lógicas**. Embora as configurações salvas
do Docker Desktop mostrassem a proposta de 8 GiB e 6 CPUs, elas não eram o limite
ativo deste backend WSL2. O ensaio não alterou nem reiniciou a VM.

| Medida | Resultado |
| --- | --- |
| Primeira partida até disponibilidade | 15,119 s |
| Primeiro preparo dos aplicativos | 398,754 s (6 min 39 s) |
| Três partidas seguintes | 12,412 s; 12,328 s; 13,577 s |
| Verificação do preparo nas partidas seguintes | 4,595 s; 3,942 s; 4,664 s |
| RAM da workstation no cenário visual, mediana / pico | 5,130 / 5,561 GiB |
| RAM dos outros containers, mediana / pico | 0,342 / 0,428 GiB |
| RAM disponível no Windows, mediana / mínimo | 3,686 / 3,586 GiB |
| CPU do Windows, mediana / p95 | 31,874% / 67,495% |
| CPU da workstation, mediana / p95 | 33,90% / 402,77% |
| Resposta visual observada, mediana / p95 | 98,7 / 120,5 ms |

A janela de uso visual teve 120 segundos e 29 amostras, sem erro de coleta.
A porcentagem Docker soma CPUs lógicas: aproximadamente 400% representa quatro
CPUs ocupadas e não deve ser comparada diretamente ao percentual global Windows.
Oscilações do contador podem ultrapassar ligeiramente esse valor.

A resposta visual usou dez entradas de teclado no Webtop até observar a cor
esperada já decodificada no Chrome Linux, entre 57,7 e 120,5 ms. Ela inclui a
automação e a captura de tela; não representa latência pura da rede ou garante
o mesmo resultado para todas as interações do editor. Insiders abriu um projeto
Salesforce genérico ao lado do Chrome. Não houve autenticação em uma organização
Salesforce corporativa nem teste de múltiplos monitores ou grandes projetos.

O KWin informou composição inativa, `/dev/dri` não disponibilizou dispositivos,
e o log do vídeo registrou `No GPU Encoder available -> Using CPU Software Encoding`.
O perfil funcional demonstrado usa codificação por CPU; não há comprovação de
aceleração gráfica nesse backend.

## Perfil para o destino

Mantenha inicialmente os **6 GiB e 4 CPUs da workstation** para uma sessão Full HD
com Insiders, projeto Salesforce e Chrome. O pico de 5,561 GiB não justifica
reduzir esse limite. Projetos maiores, mais abas ou outras ferramentas exigem
nova observação; este ensaio não estabelece uma margem confortável para cargas
maiores. Não houve mudança do perfil da imagem após as medições.

Os **8 GiB e 6 CPUs propostos para a VM Hyper-V** continuam um ponto inicial para
o ensaio no destino, não um limite homologado nesta máquina. Reserve também espaço
para o sistema da VM e os outros containers. A carga Windows já deixou apenas
cerca de 3,6 GiB disponíveis durante este cenário: aumentar indiscriminadamente
a VM pode prejudicar o host. Confirme no destino os limites efetivos e registre
os resultados do [roteiro Hyper-V](../hyperv-verification.md) antes de ajustá-los.

## Operação e evidências

O roteiro CMD completo passou em 1.207,676 segundos, incluindo preparo, conectividade
opcional, projeto Salesforce, Compose no engine do notebook, troca Windows/Linux,
backup, alteração do projeto e recuperação do conteúdo original. A cópia sintética
de 7.128.995.840 bytes foi conferida por SHA-256 e removida somente depois da prova
de recuperação; manifestos, relatórios e recibo de limpeza foram preservados.
Nenhum perfil pessoal ou serviço não relacionado foi removido.

O teste nativo de atalho e confiança do certificado passou em 40,528 segundos.
O teste de navegador passou em 85,336 segundos, verificando HTTPS, desktop,
digitação ABNT2 com comparação exata e continuidade após desconectar/reconectar.
O intervalo de 250 ms entre teclas é uma condição declarada do ensaio;
não representa uma correção do problema upstream de digitação rápida.

O ensaio nativo de atualização e recuperação da imagem passou em 1499.994 segundos.
Ele usou versões de teste derivadas da candidata Salesforce, verificando backup
antes da troca, restauração de pacotes extras, aplicativos funcionais e recuperação
da versão anterior com o projeto original. Os digests da candidata usada e os
cinco fluxos nativos aprovados constam em [t12-candidate.json](t12-candidate.json).
As evidências de atualização explícita
do Code Analyzer e restauração da versão registrada estão no
[relatório próprio](t12-code-analyzer.md). A revisão independente de fonte está
em [t12-review.md](t12-review.md), sem defeitos de fonte confirmados.

Os dados selecionados estão em [t12-latitude.json](t12-latitude.json), incluindo
hashes dos coletores e dos resultados originais. A [captura do cenário](t12-desktop.png)
foi inspecionada visualmente. Perfis, certificados, configurações corporativas,
backups e logs brutos permanecem locais, fora destes arquivos públicos.
