# Evidências técnicas - Planning context

Levantamento de 2026-09-13, horário de America/Bahia. Os artefatos Markdown retornados pelo Scrape Golden foram lidos. Este registro distingue fatos das fontes, recomendações e escolhas técnicas delegadas; decisões materiais confirmadas pertencem ao [Decision ledger](decision-ledger.md).

## Aplicativos oficiais e imagem pública

A [licença do produto Visual Studio Code](https://code.visualstudio.com/license), seção 5, restringe compartilhar e publicar o software. A licença MIT do código-fonte não é a mesma licença do produto oficial solicitado em DEC-011. As [instruções Linux da Microsoft](https://code.visualstudio.com/docs/setup/linux) também distinguem seus pacotes oficiais dos empacotamentos comunitários para Arch.

Os [termos adicionais do Chrome](https://www.google.com/chrome/terms/) se aplicam ao executável e remetem aos [termos do Google](https://policies.google.com/terms?hl=en). A seção sobre software nesses termos restringe sua distribuição. Não foi identificada autorização adicional específica de redistribuição para a Electivus.

Empacotamento escolhido em DEC-021: a imagem pública fornece a preparação e as dependências; cada instalação obtém os aplicativos oficiais diretamente dos fornecedores para seu armazenamento persistente. Isso preserva os produtos solicitados, com um primeiro preparo automático dependente de internet, progresso visível e retomada após falhas.

O preparo deve ser retomável após falhas e manter versões, origem e integridade dos artefatos instalados registradas. A versão da imagem e as versões efetivas dos aplicativos são identificadores diferentes. A disponibilidade futura de um download específico e a política de atualização desses aplicativos ainda precisam ser tratadas; fixar uma tag de imagem sozinho não fixa um download feito depois.

Não houve instalação, construção de imagem ou validação de interface gráfica neste levantamento.

## Dependências Salesforce

- A [instalação das extensões Salesforce](https://developer.salesforce.com/docs/platform/sfvscode-extensions/guide/install.html) relaciona VS Code, Salesforce Extension Pack, Salesforce CLI e Java. O pacote de extensões indicado é `salesforce.salesforcedx-vscode`.
- O [guia de Java para o servidor de linguagem Apex](https://developer.salesforce.com/docs/platform/sfvscode-extensions/guide/java-setup.html) recomenda JDK 21. Também documenta um limite de memória configurável para o servidor de linguagem, relevante para o notebook de referência.
- Os [requisitos da Salesforce CLI](https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_setup_sys_req.htm) distinguem instaladores que incluem Node.js da instalação via npm, para a qual recomendam Node.js Active LTS. O mesmo documento informa que o suporte oficial se concentra na versão corrente da CLI.

JDK 21 e Node.js Active LTS são os candidatos técnicos para atender às dependências, sem acrescentar outros SDKs não solicitados. As versões exatas devem ser resolvidas e registradas na preparação da entrega, com verificação de compatibilidade das extensões nos dois canais do VS Code. Ainda não houve teste dessa combinação.

## Seleção técnica dos plugins Zsh

DEC-012 delega a seleção dos plugins recomendados. Seleção inicial, sujeita à validação de carregamento e uso interativo:

| Plugin | Utilidade | Fonte |
| --- | --- | --- |
| `git` | Atalhos para o trabalho com Git | [Oh My Zsh](https://github.com/ohmyzsh/ohmyzsh) |
| `zsh-autosuggestions` | Sugestoes de comandos pelo historico e completamento | [Projeto zsh-users](https://github.com/zsh-users/zsh-autosuggestions) |
| `zsh-syntax-highlighting` | Destaque de comandos durante a digitacao | [Projeto zsh-users](https://github.com/zsh-users/zsh-syntax-highlighting) |

O Oh My Zsh requer Git e descreve a ativação dos plugins em `.zshrc`. O projeto de destaque de sintaxe orienta carregá-lo depois dos componentes que alteram o editor de linha. A instalação deve preservar personalizações do usuário, registrar as revisões utilizadas e manter o shell não interativo livre de efeitos da interface interativa. Os plugins não foram carregados ou medidos nesta sessão.

## Preservação de programas pessoais

DEC-019 substitui DEC-014: a preservação depende de viabilidade técnica.

O [guia de aplicações Webtop/Selkies](https://docs.linuxserver.io/selkies/user-guide/installing-apps/) explica que programas instalados pelo gerenciador do sistema se perdem na recriação do container. Manter o diretório pessoal em volume preserva seu conteúdo, mas não equivale a preservar todos os arquivos do sistema.

A [ArchWiki sobre listas de pacotes](https://wiki.archlinux.org/title/Pacman/Tips_and_tricks#List_of_installed_packages) documenta inventário dos pacotes explicitamente instalados, uma lista separada de pacotes externos aos repositórios oficiais e restauração por lista. Um hook de transação do pacman pode manter esse inventário atualizado.

A [manutenção do Arch](https://wiki.archlinux.org/title/System_maintenance#Partial_upgrades_are_unsupported) exige atualizações completas quando as bases de pacotes são sincronizadas e alerta que pacotes locais/AUR podem precisar ser recompilados quando suas bibliotecas mudam. Assim, reaplicar um conjunto de binários antigos sobre uma base nova não é uma preservação confiável por si só.

Abordagem escolhida em DEC-022: inventário persistente e comando de restauração assistida, separando pacotes oficiais de pacotes locais/AUR, com viabilidade a validar na implementação. Um nome ausente ou uma compilação que falhe deve aparecer no resultado, com possibilidade de retomada, sem declarar sucesso completo. Pacotes locais não disponíveis em repositórios podem exigir seus arquivos ou fontes; a lista de nomes sozinha não garante sua recuperação.

Esse caminho tem apoio documental, mas a integração com a imagem ainda precisa de um ensaio representativo de instalação, recriação e restauração antes de ser considerada validada. Não há promessa de preservar versões binárias idênticas ou qualquer modificação arbitrária do sistema.

Montar diretórios centrais do sistema para reaproveitá-los cegamente não foi selecionado: montagens podem ocultar os arquivos fornecidos pela imagem nova, conforme a [documentação de bind mounts](https://docs.docker.com/engine/storage/bind-mounts/), e ainda deixam a compatibilidade dos pacotes sem resolução.

## Projetos Linux e controle do Docker Desktop

DEC-013 e DEC-015 combinam execução do cliente Docker dentro da workstation com projetos no armazenamento Linux. A [documentação Docker](https://docs.docker.com/engine/storage/bind-mounts/) esclarece que fontes de bind mounts são resolvidas no host do daemon. Um caminho válido dentro da workstation não é automaticamente um caminho válido para o daemon ao iniciar outro container.

A implementação precisará adotar e documentar uma estratégia de caminhos compatível com o armazenamento escolhido. A validação deve executar um projeto Compose representativo, incluindo leitura/escrita no diretório de trabalho e reconstrução de imagem a partir de contexto local. Apenas obter sucesso em `docker ps` não comprova esse fluxo. A estratégia concreta ainda não foi escolhida nem testada.

## Dimensionamento

DEC-023 escolhe equilíbrio entre Windows e Linux, partindo de 8 GiB de RAM e 6 CPUs lógicas para a VM Docker. O ponto inicial precisa ser ajustado por testes que considerem os demais containers, a carga do Windows, o KDE, o Chrome e o servidor de linguagem Apex. A alocação atual observada foi de 4 GiB; nenhuma configuração do Docker foi alterada. O ajuste final depende de medições com o fluxo escolhido.
