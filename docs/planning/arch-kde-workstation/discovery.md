# Descoberta e entrevista - Planning context

Observações técnicas de 2026-09-13 e entrevista encerrada em 2026-09-14, horário de America/Bahia. Este documento reúne evidências e perguntas; o [Decision ledger](decision-ledger.md) é a fonte das decisões confirmadas. O usuário confirmou o entendimento consolidado na resposta Q27. A [especificação foi publicada na issue #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1), e os [13 tickets aprovados foram publicados](ticket-plan.md). A implementação e sua verificação são as próximas etapas.

## Evidência local

A sessão de inspeção executou no Windows, em PowerShell, no checkout `C:\Users\msilvane\git\webtop-arch-kde-workstation`. As instruções genéricas sobre Arch/WSL não descrevem o shell efetivo desta sessão.

| Item | Resultado observado | Origem |
| --- | --- | --- |
| Modelo | Dell Latitude 5450 | `Win32_ComputerSystem` |
| Processador | Intel Core Ultra 7 165U, 12 núcleos, 14 processadores lógicos | `Win32_Processor` |
| Memória física | 32 GB nominais; 31,5 GiB reportados | `Win32_ComputerSystem` |
| Memória livre no instante da coleta | Aproximadamente 6,6 GiB | `Win32_OperatingSystem` |
| Sistema | Windows 11 Enterprise, build 26100 | `Win32_OperatingSystem` |
| Vídeo | Intel Graphics; modo reportado de 1920 x 1080 | `Win32_VideoController` |
| Disco C: | 474,8 GiB totais; 119,0 GiB livres no instante da coleta | `Win32_LogicalDisk` |
| Docker Desktop | 4.90.0 (238679), instalação por usuário | `docker version` e caminho do executável |
| Docker Engine | 29.7.2, Linux x86_64, kernel 7.0.12-linuxkit | `docker version` e `docker info` |
| Contexto Docker | `desktop-linux` | `docker context ls` |
| Recursos da VM | 14 CPUs lógicas; 4.165.656.576 bytes de RAM reportados pelo daemon | `docker info` |
| Limite de RAM salvo | `MemoryMiB=4096` | `%APPDATA%\Docker\settings-store.json` |
| Seleção de backend salva | `UseLibkrun=true`; processo `com.docker.sailor` presente | Configuração persistida e lista de processos |
| Carga Docker existente | Dois containers de pesquisa em execução, aproximadamente 166 MiB somados durante a amostra | `docker ps` e `docker stats --no-stream` |

O usuário informou que selecionou Docker VMM e que o notebook de destino possui o mesmo modelo/configuração, com Docker via Hyper-V e WSL2 bloqueado. O inventário acima é local; a equivalência do destino e seu backend foram informados pelo usuário, não medidos remotamente.

A memória livre é uma fotografia da carga atual, não um limite permanente. A alocação de 4 GiB da VM não define o dimensionamento final da workstation. Nenhuma configuração do Docker foi alterada nesta descoberta.

O daemon também anunciou um dispositivo CDI `docker.com/gpu=webgpu`. Esse anúncio não comprova disponibilidade de `/dev/dri`, renderização KDE ou codificação de vídeo acelerada no Webtop. A aceleração gráfica permanece sem validação.

## Fontes primárias consultadas

Os artefatos Markdown retornados pelo Scrape Golden foram lidos antes de registrar estas conclusões.

- [Webtop — LinuxServer.io](https://docs.linuxserver.io/images/docker-webtop/): a tabela de variantes inclui `arch-kde`; o desktop é transmitido ao navegador pela base Selkies. A documentação descreve operação sem GPU, HTTPS na porta 3001, autenticação opcional e o diretório pessoal em `/config`.
- [Virtual Machine Manager — Docker](https://docs.docker.com/desktop/features/vmm/): documenta Docker VMM no Windows e memória mínima de 4 GB para sua VM. Aponta que compartilhamentos de diretórios do host precisam ser cadastrados, pois não há compartilhamento automático de bind mounts.
- [Install Docker Desktop on Windows — Docker](https://docs.docker.com/desktop/setup/install/windows-install/): distingue WSL2, Hyper-V e Docker VMM. Hyper-V está disponível na instalação para todos os usuários; VMM também está disponível na instalação por usuário.
- [GPU support in Docker Desktop for Windows — Docker](https://docs.docker.com/desktop/features/gpu/): o suporte NVIDIA GPU-PV descrito exige WSL2. Essa documentação não demonstra aceleração gráfica do Webtop com o vídeo Intel deste notebook em Hyper-V ou VMM.

Recomendação técnica ainda sujeita aos testes: derivar da variante mantida `lscr.io/linuxserver/webtop:arch-kde` e ter um perfil funcional sem depender de GPU. A consulta posterior ao registry confirmou a tag e o manifesto `linux/amd64`, conforme o registro abaixo. Não há medição de desempenho do KDE nesta descoberta.

## Metadados remotos verificados

Consulta somente de leitura em 2026-09-13, horário de America/Bahia:

- `gh repo view manoelcalixto/webtop-arch-kde-workstation`: repositório GitHub privado, branch padrão `main`, permissão `ADMIN` para a conta autenticada. O remoto local `origin` aponta para esse mesmo repositório. Nenhuma alteração de visibilidade do GitHub foi solicitada; a escolha de imagens públicas no Docker Hub não a modifica.
- `docker buildx imagetools inspect lscr.io/linuxserver/webtop:arch-kde`: índice OCI `sha256:ed197a60c161b5d45a0d0137a5c47ecd136964c57791bf3151d01ad41ac6b988`; manifesto `linux/amd64` `sha256:da08c127461269d148bf8191a85b8da735c8516969100dc3c63d7877b15302aa`. O índice também contém `linux/arm64` e atestações. Esses valores são uma fotografia do registry; não houve download das camadas ou execução da imagem.
- Consultas anônimas a `electivus/webtop-arch-kde-base` e `electivus/webtop-arch-kde-salesforce` na API pública do Docker Hub retornaram HTTP 404. Isso significa que não estavam visíveis publicamente nessas consultas; não comprova disponibilidade para criação nem permissões de publicação. A verificação autenticada permanece necessária na preparação da publicação.

## Árvore da entrevista

```text
Workstation Arch/KDE via Webtop
|-- Uso: desenvolvimento [DEC-006]
|   |-- Aplicativos e terminal definidos [DEC-011, DEC-012]
|   |-- Controle do Docker Desktop [DEC-013]
|   |-- Configuracao opcional assistida de proxy e certificados [DEC-034]
|   `-- Equilibrio Windows/Linux, com ajuste de recursos por testes [DEC-023]
|-- Acesso individual no proprio notebook [DEC-007]
|   |-- Entrada direta no desktop local [DEC-016]
|   |-- Ingles, localizacao Brasil, ABNT2 e America/Bahia [DEC-017]
|   |-- Inicio sob demanda no Windows [DEC-025]
|   |-- Uma tela Full HD, Insiders e Chrome [DEC-031]
|   `-- Manter a sessao ao fechar a aba, ate o comando de parar [DEC-033]
|-- Distribuicao publica e generica na Electivus [DEC-008]
|   |-- Variante Salesforce [DEC-009]
|   |-- Duas imagens: base -> Salesforce [DEC-010]
|   |-- Dois repositorios, versoes coordenadas, tags fixas e stable [DEC-018]
|   |-- Publicacao automatica semanal e sob demanda apos testes [DEC-026]
|   |-- Nomes dos repositorios Docker Hub [DEC-035]
|   |-- Perfil inicial linux/amd64 [entendimento confirmado em Q27]
|   `-- Atualizacao da imagem e dos aplicativos por comando [DEC-027, DEC-028]
|-- Estado e dados
|   |-- Preservar programas pacman/AUR se viavel [DEC-019]
|   |-- Projetos no Linux e pasta de troca no Windows [DEC-015]
|   |-- Backup no Windows antes das atualizacoes e sob demanda; reter dois [DEC-029]
|   `-- Usar ambiente atualizado com relatorio, nova tentativa e recuperacao [DEC-032]
`-- Validacao no destino [DEC-030]
    |-- Evidencias que o VMM local consegue fornecer
    `-- Verificacao especifica no notebook com Hyper-V
```

## Rodada inicial

Decisões já explícitas no pedido: DEC-001, DEC-002, DEC-003, DEC-004, DEC-005.

1. **Q1 — Respondida.** Desenvolvimento com editor, navegador, terminal e ferramentas de projeto. Registrada como DEC-006. Os aplicativos e suas dependências foram definidos nas rodadas seguintes.
2. **Q2 — Respondida.** Uma pessoa, somente no próprio notebook. Registrada como DEC-007.
3. **Q3 — Respondida.** Imagem pública e genérica, reutilizável por outras pessoas. Registrada como DEC-008.

Decisões registradas nesta rodada: DEC-006, DEC-007, DEC-008.

## Ampliação para Salesforce e discussão de versões

O usuário acrescentou que também será criada uma imagem para desenvolvimento Salesforce: DEC-009. Na resposta Q4, confirmou somente duas imagens, base e desenvolvimento Salesforce, com Salesforce derivando diretamente da base: DEC-010. DEC-018 definiu depois dois repositórios, versões coordenadas, tags fixas e alias stable. DEC-035 registra os nomes confirmados em Q27; a verificação autenticada dos repositórios permanece para a preparação da publicação.

A [família de imagens e política de versões](image-family-proposal.md) consolida as escolhas confirmadas. Uma eventual ampliação da hierarquia fica para uma necessidade futura, conforme DEC-010. As rodadas seguintes documentam as respostas que concluíram a entrevista.

## Segunda rodada respondida

Decisão adicional registrada antes desta rodada: DEC-009. As respostas de Q4-Q11 estão registradas abaixo; as rodadas seguintes resolveram as escolhas sobre preservação dos programas, atualização, dimensionamento, backup/restauração e validação.

| Pergunta | Estado ou escolha pendente | Resposta ou recomendacao |
| --- | --- | --- |
| Q4 | Respondida: DEC-010 | Somente base e Salesforce; Salesforce deriva da base; rever hierarquia apenas se houver necessidade futura |
| Q5 | Respondida: DEC-011 e DEC-012 | VS Code Stable e Insiders; Chrome oficial; Git; Salesforce CLI e extensoes; Zsh padrao, Oh My Zsh e plugins recomendados |
| Q6 | Respondida apos ajuste: DEC-018 | Dois repositorios, versoes coordenadas, tags fixas e alias stable |
| Q7 | Respondida: DEC-013 | Controlar o engine Docker Desktop do notebook pela workstation |
| Q8 | Respondida e esclarecida: DEC-019 substitui DEC-014 | Preservar programas instalados com pacman/AUR somente se tecnicamente viavel |
| Q9 | Respondida: DEC-015 | Projetos no armazenamento Linux, com pasta de troca para Windows |
| Q10 | Respondida: DEC-016 | Entrada direta; controle pelo acesso a sessao Windows; endpoint somente local |
| Q11 | Respondida: DEC-017 | Interface em ingles; localizacao brasileira; teclado ABNT2; fuso America/Bahia |

Decisões registradas nesta rodada: DEC-010, DEC-011, DEC-012, DEC-013, DEC-014, DEC-015, DEC-016, DEC-017, DEC-018. Q6 foi reformulada para duas imagens e respondida; não há pergunta desta rodada aguardando resposta.

Esclarecimento posterior de Q8: DEC-019 substitui DEC-014 e condiciona a preservação dos programas à viabilidade técnica. A avaliação deve produzir uma opção concreta ou explicar a limitação; a preservação não está prometida incondicionalmente.

As [evidências técnicas](technical-findings.md) registram as condições de distribuição dos aplicativos oficiais, a seleção de plugins Zsh, o caminho documentado de inventário/restauração de pacotes e o requisito de compatibilidade dos caminhos com o daemon Docker. Ainda não há prova de execução desses mecanismos na workstation.

## Terceira rodada respondida

Decisões já registradas desde o início da segunda rodada: DEC-010, DEC-011, DEC-012, DEC-013, DEC-014, DEC-015, DEC-016, DEC-017, DEC-018, DEC-019. DEC-014 está substituída por DEC-019.

| Pergunta | Estado ou escolha pendente | Resposta ou recomendacao |
| --- | --- | --- |
| Q12 | Respondida: DEC-020 | Base como desktop utilizavel com KDE, Chrome, Git, Zsh e Oh My Zsh; Salesforce acrescenta os dois VS Codes, CLI, extensoes, Java e Node necessarios |
| Q13 | Respondida: DEC-021 | Preparacao automatica no primeiro inicio, retomavel e com progresso, baixando dos fornecedores para armazenamento persistente |
| Q14 | Respondida: DEC-022 | Inventario persistente e restauracao assistida; pacman/AUR separados; viabilidade a validar na implementacao |
| Q15 | Respondida: DEC-023 | Equilibrio Windows/Linux e ajuste por testes; 8 GiB e 6 CPUs logicas para a VM como ponto inicial |
| Q16 | Respondida: DEC-024 | VS Code Insiders como padrao; Stable separado e disponivel |
| Q17 | Respondida: DEC-025 | Sob demanda por comando ou atalho no Windows |

Decisões registradas nesta rodada: DEC-020, DEC-021, DEC-022, DEC-023, DEC-024, DEC-025. Q12-Q17 foram respondidas. As escolhas sobre atualizações, backup/restauração e validação foram resolvidas nas rodadas seguintes; o fluxo de instalação foi incluído no entendimento confirmado em Q27.

## Quarta rodada respondida

| Pergunta | Estado | Resposta |
| --- | --- | --- |
| Q18 | Respondida: DEC-026 | GitHub Actions semanal e sob demanda, publicacao automatica e promocao de stable apos testes |
| Q19 | Respondida: DEC-027 | Comando de atualizacao com backup antes da troca |
| Q20 | Respondida: DEC-028 | Comando explicito, independente da imagem, registrando versoes efetivas |
| Q21 | Respondida: DEC-029 | Antes das atualizacoes e sob demanda; manter os dois backups concluidos mais recentes no Windows |
| Q22 | Respondida: DEC-030 | Publicar apos testes VMM locais, declarar Hyper-V real pendente e entregar roteiro executavel para o destino |
| Q23 | Respondida: DEC-031 | Uma tela Full HD, Insiders com projeto Salesforce e Chrome |

Decisões registradas nesta rodada: DEC-026, DEC-027, DEC-028, DEC-029, DEC-030, DEC-031. Q18-Q23 foram respondidas. As respostas subsidiaram a quinta rodada, que definiu o comportamento após falhas de restauração de pacotes pessoais e o encerramento da sessão.

## Quinta rodada respondida

| Pergunta | Estado | Resposta |
| --- | --- | --- |
| Q24 | Respondida: DEC-032 | Disponibilizar o ambiente atualizado com os aplicativos restaurados, relatar falhas e permitir nova tentativa ou recuperacao do backup |
| Q25 | Respondida: DEC-033 | Manter a sessao e seus processos ate o comando de parar |
| Q26 | Respondida: DEC-034 | Configuracao opcional assistida na instalacao, com diagnostico de conexao e dados mantidos somente no notebook |

Decisões registradas nesta rodada: DEC-032, DEC-033, DEC-034. Q24-Q26 foram respondidas em 2026-09-14, após serem reapresentadas a pedido do usuário. Q24 trata de programas extras; falhas nos componentes fornecidos pelas imagens continuam sujeitas aos testes de entrega.

## Entendimento confirmado e encerramento

A fronteira de escolhas funcionais da entrevista está vazia. O entendimento consolidado está em [Família de imagens](image-family-proposal.md), com as decisões materiais no ledger. Em 2026-09-14, o usuário respondeu Q27 com "Confirmar o entendimento consolidado e encerrar a entrevista". A entrevista está concluída, sem perguntas pendentes.

DEC-035 registra os nomes públicos confirmados: `electivus/webtop-arch-kde-base` e `electivus/webtop-arch-kde-salesforce`. O entendimento inclui o perfil inicial `linux/amd64` correspondente ao notebook e comandos PowerShell para instalação e manutenção. A confirmação global reafirma as demais decisões ativas, sem duplicá-las no ledger. DEC-014 permanece substituída por DEC-019.

O encerramento da entrevista foi registrado em checkpoint intermediário de planejamento. A especificação e os tickets publicados cobrem as decisões aplicáveis, permitindo o checkpoint final de planejamento. Não há imagens construídas, testes de execução ou publicação no Docker Hub. A implementação deverá resolver e verificar os mecanismos de armazenamento e caminhos Docker/Compose, preparo de aplicativos, recuperação e desempenho; essas questões técnicas têm requisitos definidos e não são provas de viabilidade já obtidas. Caso uma restrição confirmada não possa ser atendida, será necessário retornar ao planejamento.

## Especificação publicada

Em 2026-09-14, o usuário solicitou `to-spec`. A [issue #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1) foi publicada no tracker configurado com a etiqueta `ready-for-agent`; a cópia local é [spec.md](spec.md). O texto contém 56 histórias de usuário, consequências para as 34 decisões ativas e 16 cenários de teste, preservando os testes de uso confirmados em Q27.

O corpo publicado foi comparado com a cópia local e validado pelo contrato Planning. Na publicação inicial, seu marcador referenciava o checkpoint da entrevista `ae055605e0972ad07787cc55a5d35fbe6b02b191`, cuja presença na branch remota configurada foi verificada antes da publicação. Após publicar, a cobertura `specification` das 34 decisões foi concluída pelo helper Planning, usando a URL da issue como evidência. Naquele momento, as coberturas `tickets` e `verification` permaneciam pendentes.

## Tickets aprovados e publicados

Em 2026-09-14, o usuário aprovou os 13 tickets do [plano de decomposição](ticket-plan.md), com a granularidade e as 17 dependências propostas, e autorizou a publicação. As issues #2 a #14 foram criadas como filhos nativos da especificação #1, todas com ready-for-agent e os bloqueios nativos correspondentes. O plano registra a correspondência entre T01-T13 e as issues, com links e dependências.

Os corpos publicados preservam os 97 critérios de aceitação aprovados e as consequências das decisões. Após cada publicação, o helper Planning acrescentou sua URL à cobertura tickets das decisões aplicáveis. As 34 decisões ativas têm specification e tickets completos; verification permanece pendente até a implementação e seus testes. O checkpoint final consolida essa cobertura, e os marcadores da especificação e de todos os tickets são atualizados para ele após confirmar sua presença na branch remota configurada.

A fronteira inicial de implementação contém somente [T01 / #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2), que entrega a abertura e o controle do desktop Arch/KDE pelo Windows. A autorização desta etapa encerra a publicação do planejamento.
