# Família de imagens - Planning context

Status em 2026-09-14: entendimento consolidado confirmado pelo usuário em Q27; entrevista encerrada e [especificação publicada na issue #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1), com cópia local em [spec.md](spec.md). Os [13 tickets aprovados foram publicados](ticket-plan.md). O [Decision ledger](decision-ledger.md) registra as escolhas confirmadas; este documento não as substitui. DEC-009 inclui Salesforce, DEC-010 limita a entrega atual a duas imagens, DEC-018 define dois repositórios Docker Hub com versões coordenadas, tags fixas e alias stable, e DEC-035 fixa os nomes públicos. A especificação e os tickets cobrem as 34 decisões ativas; a implementação e os testes de execução permanecem como próximas etapas.

## Variante e versão

Uma variante atende a um perfil de uso. Uma versão identifica uma entrega daquele perfil. Cada combinação pode resultar em uma imagem publicada. Várias tags também podem apontar para a mesma imagem, sem criar uma cópia de suas camadas.

Nomes confirmados em DEC-035, ainda não criados nem verificados com autenticação no Docker Hub; as tags abaixo são ilustrativas:

| Variante | Conteudo pretendido | Referencia ilustrativa |
| --- | --- | --- |
| Base | Arch, KDE, Webtop, Chrome oficial, Git, Zsh, Oh My Zsh e ajustes comuns | `electivus/webtop-arch-kde-base:1.0.0` |
| Salesforce | Base mais VS Code Stable/Insiders, Salesforce CLI, extensoes, Java e Node necessarios | `electivus/webtop-arch-kde-salesforce:1.0.0` |

Conforme DEC-018, serão dois repositórios Docker Hub, um por imagem. O código e as rotinas de construção podem continuar neste único repositório Git. Os nomes acima estão confirmados em DEC-035; a existência, a criação e as permissões de publicação precisam ser verificadas no registry. A separação dos repositórios não impede o compartilhamento das camadas.

## Herança confirmada

A entrega atual segue esta estrutura, conforme DEC-010:

```text
webtop:arch-kde (upstream)
`-- Electivus base
    `-- Electivus Salesforce
```

DEC-020 define a divisão de ferramentas: a base oferece um desktop utilizável e a variante Salesforce acrescenta o ambiente de desenvolvimento completo. DEC-021 define o preparo automático dos aplicativos oficiais no primeiro início, com progresso e retomada; a tabela descreve o conteúdo disponibilizado pela workstation, sem afirmar que todos os binários serão redistribuídos na imagem pública. Uma eventual ampliação ou reorganização será tratada quando existir uma necessidade concreta; esta entrega não inclui uma imagem dev geral nem uma hierarquia adicional.

O Docker compartilha camadas com conteúdo idêntico; não é necessário executar o container base para executar a variante Salesforce. Ao atualizar a base, é necessário reconstruir e validar a variante Salesforce que passará a consumi-la; imagens já publicadas não incorporam a mudança sozinhas.

## Política de entregas e detalhes pendentes

- Tags de entrega fixa, como `1.0.0` e `1.0.1`, sem sobrescrever um artefato publicado. Os exemplos identificam versões da workstation Electivus; as versões de Arch, KDE e ferramentas serão registradas separadamente.
- O alias móvel `stable` apontará para a última entrega aprovada, conforme DEC-018. DEC-026 define GitHub Actions semanal e sob demanda, com publicação automática das duas imagens e promoção de `stable` somente após os testes da entrega. Não é uma cópia adicional quando aponta para o mesmo conteúdo.
- No notebook de trabalho, usar a entrega fixa e seu digest para identificar exatamente o artefato escolhido. DEC-027 exige comando explícito e backup antes da troca de imagem; a publicação de um novo `stable` não atualiza sozinha uma workstation em uso.
- Fixar também a base consumida por digest e atualizar essa referência de forma controlada. Isso identifica a base exata; sozinho, não garante reconstrução idêntica quando a instalação consulta repositórios de pacotes que mudam, como no Arch.
- As duas imagens terão versões coordenadas, conforme DEC-018. A automação seguirá DEC-026; o procedimento de construção, validação e promoção conjunta ainda será detalhado.
- DEC-038 permite a primeira publicação após os testes locais em Docker Desktop com WSL2, identificando a validação real em Hyper-V como pendente e fornecendo um roteiro executável para o destino. Essa distinção deve acompanhar as evidências da entrega.
- No Docker Hub, há configuração de imutabilidade para todas as tags ou para padrões específicos. Tags numéricas fixas podem ser protegidas preservando a mobilidade de aliases. A disponibilidade/configuração efetiva dos repositórios Electivus ainda não foi inspecionada.

## Estado pessoal e atualização

O pacote de programas fornecido por uma variante é distinto dos arquivos e das preferências do usuário. A documentação Webtop/Selkies informa que pacotes instalados manualmente no sistema são perdidos quando o container é recriado; o diretório pessoal `/config` só persiste se tiver armazenamento persistente configurado.

DEC-019 substitui DEC-014 e condiciona a preservação dos programas instalados com pacman/AUR à viabilidade técnica. DEC-022 escolhe inventário persistente e restauração assistida, separando pacman e AUR, com viabilidade a validar na implementação. DEC-032 permite usar o ambiente atualizado com os aplicativos que funcionaram quando a restauração de programas extras falhar, apresentando relatório, nova tentativa e recuperação do backup. Essa tolerância se aplica aos programas extras do usuário; os componentes fornecidos pelas imagens continuam sujeitos aos testes de entrega. A conciliação dos pacotes com novas versões da base e o mecanismo de recuperação ainda precisam ser implementados e verificados. Voltar a uma imagem anterior não reverte automaticamente alterações no estado pessoal ou no sistema preservado.

DEC-028 define atualização de VS Code Stable/Insiders, Chrome, Salesforce CLI e extensões por comando explícito, independente da imagem, com registro das versões efetivas. DEC-029 exige backup local no Windows de projetos, perfil pessoal, aplicativos persistidos e inventário antes das atualizações e sob demanda, retendo os dois backups concluídos mais recentes. O procedimento deve permitir recuperar dados e versões de forma coerente.

DEC-015 mantém projetos no armazenamento Linux e uma pasta de troca com Windows. Como DEC-013 permite controlar o Docker Desktop pelo container, a solução deve tratar a diferença entre caminhos dentro da workstation e os caminhos que o daemon enxerga ao criar outros containers.

## Conteúdo e experiência confirmados

- DEC-020: base com KDE, Chrome oficial, Git e terminal preparado; Salesforce acrescenta os dois VS Codes, Salesforce CLI, extensões, Java e Node necessários.
- DEC-011 e DEC-021: VS Code Stable/Insiders e Google Chrome oficiais obtidos dos fornecedores no preparo inicial, com progresso e retomada, para armazenamento persistente; Git, Salesforce CLI e extensões compõem o ambiente. As fontes e condições consultadas constam das [evidências técnicas](technical-findings.md).
- DEC-012: Zsh como shell padrão, Oh My Zsh e plugins recomendados. A seleção delegada de `git`, `zsh-autosuggestions` e `zsh-syntax-highlighting` está registrada nas evidências técnicas, com suas fontes e validação pendente.
- DEC-016: entrada direta no desktop, restrito ao notebook, com controle pelo acesso à sessão Windows.
- DEC-017: interface em inglês, localização brasileira, teclado ABNT2 e fuso America/Bahia.
- DEC-023: equilíbrio entre Windows e Linux, com dimensionamento ajustado por testes; 8 GiB e 6 CPUs lógicas para a VM são o ponto inicial.
- DEC-024: VS Code Insiders como editor padrão, mantendo Stable disponível separadamente.
- DEC-025: início sob demanda por comando ou atalho no Windows.
- DEC-031: validação visual com uma tela Full HD de 1920 x 1080, Insiders com projeto Salesforce e Chrome.
- DEC-033: fechar a aba do Webtop mantém a sessão e seus processos até o comando de parar.
- DEC-034: configuração opcional assistida de proxy e certificados corporativos na instalação, com diagnóstico de conexão; as configurações permanecem no notebook, fora da imagem pública.

## Instalação e verificação a implementar

O perfil inicial será `linux/amd64`, correspondente ao Latitude 5450 com Core Ultra 7 165U e 32 GB. A instalação parte de Docker Desktop já disponível com containers Linux; o notebook de destino utiliza Hyper-V e o notebook de teste utiliza Docker Desktop com WSL2 desde 2026-09-16. O fluxo Windows será documentado para CMD, sem executar PowerShell (DEC-036), com operações para instalar, iniciar, parar, atualizar a imagem, atualizar aplicativos, fazer backup, restaurar e diagnosticar. O acesso ao desktop será por um endpoint HTTPS limitado ao próprio notebook.

Os comandos e as instruções necessários ao uso público deverão acompanhar a distribuição no Docker Hub. Em 2026-09-18, o usuário autorizou também tornar público o repositório de código, com licença MIT para o conteúdo próprio da Electivus e preservação das licenças de terceiros (DEC-039). Essa abertura é independente da aprovação das imagens.

A verificação deverá cobrir as duas variantes: desktop e localização ABNT2; aplicativos oficiais e extensões nos dois canais do VS Code; retomada do preparo inicial; persistência de projetos e preferências; troca de arquivos com Windows; backup e recuperação; inventário e restauração assistida, incluindo falha de pacote extra; manutenção da sessão ao fechar a aba; e configuração opcional de rede com diagnóstico.

O fluxo Docker/Compose será verificado com um projeto que use arquivos do armazenamento Linux, leitura e escrita em volume montado e construção a partir de contexto local. O dimensionamento será medido em Full HD com Insiders, um projeto Salesforce e Chrome, partindo dos recursos propostos em DEC-023. A automação de entrega só promoverá `stable` após seus testes; a evidência da primeira publicação identificará os testes WSL2 realizados e as evidências VMM históricas e a verificação Hyper-V ainda necessária no destino.

## Fontes primárias

Consultadas em 2026-09-13, horário de America/Bahia; os artefatos Markdown retornados pelo Scrape Golden foram lidos.

- [Docker image pull](https://docs.docker.com/reference/cli/docker/image/pull/): reutilização de camadas, múltiplas tags para o mesmo conteúdo e seleção por digest.
- [Docker — Building best practices](https://docs.docker.com/build/building/best-practices/): etapas reutilizáveis para imagens com componentes comuns, dependências necessárias e reconstrução de imagens para incorporar atualizações.
- [Docker Hub — Immutable tags](https://docs.docker.com/docker-hub/repos/manage/hub-images/immutable-tags/): proteção contra sobrescrita de tags e seleção de padrões para imutabilidade.
- [LinuxServer.io — Installing Applications](https://docs.linuxserver.io/selkies/user-guide/installing-apps/): diferenças entre pacotes do sistema, aplicações no diretório pessoal, instalação no início e imagens derivadas.
