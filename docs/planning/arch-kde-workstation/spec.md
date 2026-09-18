# Workstation Arch/KDE Electivus: base e desenvolvimento Salesforce

## Problem Statement

O usuário precisa de uma workstation Linux para desenvolvimento em um notebook corporativo Windows 11 no qual WSL2 é bloqueado, mas Docker Desktop com containers Linux via Hyper-V está disponível. Ele quer trabalhar com editor, navegador, terminal e ferramentas Salesforce, mantendo os projetos no armazenamento Linux e trocando arquivos com Windows quando necessário.

Uma imagem de desktop isolada não resolve todo o uso diário: também são necessários instalação e início pelo Windows, aplicativos oficiais, continuidade da sessão, atualização controlada, backup e recuperação dos dados. Programas instalados manualmente no sistema podem desaparecer quando o container é recriado; sua recuperação precisa ser tratada explicitamente, dentro da viabilidade técnica.

O notebook de teste é um Dell Latitude 5450, com Core Ultra 7 165U e 32 GB de RAM, equivalente ao notebook de destino segundo o usuário. Desde 2026-09-16, Docker Desktop com backend WSL2 oferece o ambiente de teste disponível, após o usuário substituir o Docker VMM beta por problemas de funcionamento. A entrega precisa distinguir essa evidência da validação real em Hyper-V no destino.

## Solution

Distribuir duas imagens públicas e genéricas no Docker Hub da Electivus. A workstation base será um desktop utilizável; a workstation Salesforce herdará diretamente dela e acrescentará o ambiente de desenvolvimento. Cada variante deve funcionar com seu próprio container, sem exigir outro container executando a variante ancestral.

| Variante | Repositorio Docker Hub | Conteudo disponibilizado |
| --- | --- | --- |
| Base | electivus/webtop-arch-kde-base | Arch Linux, KDE, Webtop, Chrome oficial, Git, Zsh e Oh My Zsh |
| Salesforce, derivada da base | electivus/webtop-arch-kde-salesforce | Conteudo da base, VS Code Stable e Insiders, Salesforce CLI, extensoes Salesforce, Java e Node necessarios |

O perfil inicial será linux/amd64. O usuário instalará e administrará a workstation por comandos CMD e poderá iniciá-la por um atalho no Windows, partindo de Docker Desktop já disponível e configurado para containers Linux. PowerShell é bloqueado no notebook de destino: os comandos e o atalho não podem chamá-lo direta ou indiretamente. Essa restrição se aplica também a diagnóstico, backup, restauração e atualizações. O desktop será acessível apenas pelo navegador do próprio notebook, por HTTPS e sem senha adicional. Fechar a aba manterá a sessão e seus processos; o comando de parar encerrará a execução da workstation.

Chrome e os dois canais oficiais do VS Code serão obtidos diretamente dos fornecedores durante a preparação automática inicial, em armazenamento persistente, com progresso e retomada. A imagem pública fornecerá a preparação e as dependências correspondentes. O ambiente terá interface em inglês, formatos brasileiros, teclado ABNT2 e fuso America/Bahia. Insiders será o editor padrão.

Projetos, perfil e aplicativos persistidos serão acompanhados de backup local no Windows, realizado antes das atualizações e também sob demanda, mantendo os dois backups concluídos mais recentes. Programas extras terão inventário e restauração assistida separados para pacman e AUR, com relatório, nova tentativa e recuperação disponíveis. Sua preservação depende de viabilidade técnica.

As imagens terão versões coordenadas, tags fixas e um alias stable. GitHub Actions construirá e publicará entregas semanalmente e sob demanda, promovendo stable depois dos testes. A workstation em uso receberá novas imagens e atualizações de aplicativos por comandos explícitos separados. A primeira publicação poderá seguir após os testes locais no WSL2, acompanhada do roteiro executável de verificação Hyper-V no notebook de destino.

## User Stories

1. Como desenvolvedor em um notebook corporativo, quero executar uma workstation Linux pelo Docker disponível, para trabalhar sem depender de WSL2.
2. Como usuário, quero acessar um desktop KDE completo pelo navegador local, para usar aplicativos Linux no notebook Windows.
3. Como usuário da workstation base, quero um desktop com navegador, Git e terminal preparados, para realizar atividades comuns sem instalar o conjunto Salesforce.
4. Como desenvolvedor Salesforce, quero uma variante que acrescente as ferramentas de desenvolvimento à base, para obter um ambiente completo em uma única workstation.
5. Como usuário, quero Google Chrome oficial, para utilizar o navegador solicitado no ambiente Linux.
6. Como desenvolvedor, quero VS Code Stable e Insiders oficiais disponíveis separadamente, para escolher o canal adequado a cada atividade.
7. Como desenvolvedor, quero abrir arquivos e projetos com Insiders por padrão, para seguir meu fluxo habitual.
8. Como desenvolvedor Salesforce, quero CLI, extensões e dependências Java e Node prontas, para iniciar o trabalho com projetos Salesforce.
9. Como desenvolvedor, quero Git disponível no terminal, para trabalhar com o versionamento dos meus projetos.
10. Como usuário do terminal, quero Zsh como shell padrão com Oh My Zsh, para usar um ambiente interativo preparado.
11. Como usuário do terminal, quero atalhos Git, sugestões e destaque de sintaxe, para reduzir o trabalho de digitação e perceber erros de comandos.
12. Como usuário, quero a interface em inglês, para manter menus e mensagens nesse idioma.
13. Como usuário no Brasil, quero formatos regionais brasileiros e fuso America/Bahia, para interpretar datas, números e horários corretamente.
14. Como usuário de teclado ABNT2, quero digitar acentos, cedilha e símbolos corretamente, para trabalhar sem adaptar a digitação ao layout de outro país.
15. Como usuário em uma instalação nova, quero que os aplicativos oficiais sejam preparados automaticamente, para reduzir as etapas manuais de configuração.
16. Como usuário, quero acompanhar o progresso dessa preparação, para distinguir uma instalação em andamento de uma falha.
17. Como usuário com uma conexão interrompida, quero retomar a preparação, para completar a instalação sem descartar etapas já concluídas.
18. Como usuário, quero reutilizar os aplicativos persistidos ao reiniciar ou recriar a workstation, para evitar downloads e configurações desnecessários.
19. Como usuário, quero consultar as versões e a origem dos aplicativos instalados, para identificar o ambiente efetivamente em uso.
20. Como usuário do Windows com PowerShell bloqueado, quero instalar e administrar a workstation por comandos CMD documentados, para operar o ambiente a partir do notebook.
21. Como usuário, quero iniciar a workstation sob demanda por comando ou atalho, para consumir seus recursos quando decidir trabalhar.
22. Como único usuário do desktop local, quero entrar diretamente pela sessão Windows, para evitar uma segunda autenticação na workstation.
23. Como usuário, quero que o acesso ao desktop fique limitado ao próprio notebook, para manter o modelo de uso pessoal acordado.
24. Como desenvolvedor, quero fechar a aba e voltar à mesma sessão com tarefas em andamento, para não interromper o trabalho por uma desconexão do navegador.
25. Como usuário, quero um comando explícito de parar, para encerrar a execução e liberar os recursos da workstation.
26. Como desenvolvedor, quero manter os projetos no armazenamento Linux do Docker, para trabalhar com arquivos no ambiente em que as ferramentas executam.
27. Como usuário, quero uma pasta de troca com Windows, para transferir arquivos entre o notebook e a workstation.
28. Como desenvolvedor, quero executar Docker e Compose no terminal Linux usando o engine existente do notebook, para administrar meus containers no mesmo Docker Desktop.
29. Como desenvolvedor, quero que um projeto Compose consiga montar seus arquivos e construir imagens a partir do contexto local, para executar fluxos reais de desenvolvimento dentro da workstation.
30. Como usuário, quero preservar meus projetos e preferências ao recriar a workstation, para continuar o trabalho após uma atualização da imagem.
31. Como usuário que instala programas extras, quero um inventário persistente dos pacotes oficiais, para poder restaurá-los após a recriação.
32. Como usuário de AUR ou pacotes locais, quero um inventário separado desses programas, para identificar necessidades de recompilação ou intervenção.
33. Como usuário, quero restauração assistida dos programas extras quando tecnicamente viável, para recuperar meu conjunto de ferramentas pessoais.
34. Como usuário, quero utilizar o ambiente atualizado quando apenas programas extras falharem na restauração, para continuar trabalhando com os aplicativos disponíveis.
35. Como usuário, quero um relatório dos programas não restaurados e uma nova tentativa, para resolver falhas sem confundi-las com sucesso completo.
36. Como usuário, quero recuperar um backup quando precisar voltar ao estado anterior, para ter uma alternativa à correção do ambiente atualizado.
37. Como usuário, quero backups locais no Windows que incluam projetos, perfil, aplicativos persistidos e inventário, para proteger o estado necessário à recuperação.
38. Como usuário, quero backup concluído antes da troca de imagem ou atualização de aplicativos, para ter um ponto de recuperação anterior às alterações.
39. Como usuário, quero criar um backup sob demanda, para guardar um ponto de recuperação mesmo sem atualizar o ambiente.
40. Como usuário, quero manter os dois backups concluídos mais recentes, para limitar o espaço utilizado sem contar tentativas incompletas como cópias válidas.
41. Como usuário, quero aplicar uma nova imagem por comando explícito, para controlar a interrupção da sessão.
42. Como usuário, quero que publicar um novo stable não altere automaticamente minha workstation em uso, para escolher quando atualizar.
43. Como desenvolvedor, quero atualizar os aplicativos por um comando independente da imagem, para acompanhar suas versões sem recriar toda a workstation.
44. Como usuário, quero consultar as versões efetivas depois de uma atualização, para diagnosticar mudanças de comportamento.
45. Como usuário em rede corporativa, quero configurar proxy e certificados de forma opcional e assistida, para preparar a conectividade necessária no meu notebook.
46. Como usuário, quero um diagnóstico de conexão, para identificar problemas de configuração sem desativar a verificação TLS.
47. Como responsável pela distribuição pública, quero manter configurações e conteúdo corporativos fora das imagens, para disponibilizar artefatos genéricos reutilizáveis.
48. Como usuário de um notebook com 32 GB, quero ajustar recursos equilibrando Windows, workstation e outros containers, para manter o conjunto utilizável.
49. Como desenvolvedor, quero avaliar o ambiente em Full HD com Insiders, projeto Salesforce e Chrome, para medir uma carga representativa do meu uso.
50. Como responsável pela entrega, quero testar localmente no WSL2 e identificar o backend usado em cada evidência, para saber o que foi efetivamente verificado.
51. Como usuário do notebook de destino, quero um roteiro executável de verificação em Hyper-V, para comprovar o funcionamento no ambiente real.
52. Como consumidor das imagens públicas, quero escolher uma versão fixa e identificar seu digest, para saber qual artefato da workstation estou usando.
53. Como responsável pela distribuição, quero versões coordenadas de base e Salesforce, para identificar uma entrega compatível da família.
54. Como responsável pela manutenção, quero produzir entregas semanalmente e sob demanda com testes antes de stable, para distribuir atualizações por um processo consistente.
55. Como consumidor das imagens públicas, quero instruções e comandos de uso disponíveis com a distribuição, para instalar o ambiente sem precisar clonar o repositório de código.
56. Como responsável pelo suporte, quero distinguir versão da imagem, versões dos aplicativos, resultado de restauração e backend testado, para interpretar corretamente um diagnóstico.
57. Como responsável pelo projeto, quero disponibilizar o repositório GitHub público com licença MIT para o código próprio e avisos de terceiros preservados, após revisar o conteúdo que será exposto.

## Implementation Decisions

A implementação será organizada em três responsabilidades: composição e preparação das variantes; operação da workstation e do estado pessoal pelos comandos de uso; e produção, verificação e distribuição das entregas. Os contratos de uso devem permitir instalar, iniciar, parar, diagnosticar, atualizar a imagem, atualizar aplicativos, fazer backup, restaurar o estado e restaurar programas extras. A escolha dos componentes internos deve preservar essas operações observáveis.

- DEC-001: Construir a família sobre Webtop com Arch Linux e KDE, usando a variante upstream correspondente e identificando a base consumida por digest.
- DEC-002: Fornecer execução em containers Linux do Docker Desktop via Hyper-V e instruções Windows que não dependam de WSL2.
- DEC-003: Preparar a distribuição pública das imagens e das instruções de uso no Docker Hub da Electivus.
- DEC-004: Disponibilizar um perfil inicial linux/amd64 ajustável para o Latitude 5450 com Core Ultra 7 165U e 32 GB.
- DEC-037: Executar a validação disponível no Docker Desktop com WSL2 local e registrar o backend nas evidências, preservando a distinção em relação ao destino Hyper-V.
- DEC-006: Tornar editor, navegador, terminal e ferramentas de projeto utilizáveis em conjunto no fluxo principal de desenvolvimento.
- DEC-007: Limitar a publicação do endpoint do desktop ao próprio notebook e atender uma sessão pessoal.
- DEC-008: Manter imagens e conteúdo público genéricos, recebendo dados, configurações corporativas e credenciais somente na instalação em uso.
- DEC-009: Entregar a variante Salesforce com preparação e validação próprias do conjunto de ferramentas especializado.
- DEC-010: Construir Salesforce diretamente da base da entrega coordenada, mantendo somente as duas variantes e execução independente de cada uma.
- DEC-011: Disponibilizar Chrome e VS Code Stable/Insiders oficiais, Git, Salesforce CLI e Salesforce Extension Pack, validando as extensões nos dois editores.
- DEC-012: Inicializar sessões interativas em Zsh com Oh My Zsh e os plugins git, zsh-autosuggestions e zsh-syntax-highlighting, preservando personalizações existentes.
- DEC-013: Conectar os clientes Docker e Compose da workstation ao Docker Desktop existente e suportar projetos com montagem de arquivos e construção por contexto local.
- DEC-015: Persistir projetos no armazenamento Linux e disponibilizar uma pasta de troca com Windows, conciliando os caminhos vistos pela workstation e pelo daemon Docker.
- DEC-016: Oferecer entrada direta no desktop local sem senha adicional, mantendo a restrição de acesso do endpoint ao notebook.
- DEC-017: Configurar idioma da interface em inglês, formatos brasileiros, teclado ABNT2 e fuso America/Bahia na sessão e nos aplicativos aplicáveis.
- DEC-018: Publicar versões coordenadas com tags fixas preservadas e stable móvel; registrar digests e a relação entre Salesforce e sua base.
- DEC-019: Validar a viabilidade de recuperação de programas pessoais e documentar os limites encontrados, sem garantir preservação arbitrária de todo o sistema.
- DEC-020: Disponibilizar KDE, Chrome, Git e terminal preparado na base; acrescentar os dois VS Codes, CLI, extensões, Java e Node necessários na Salesforce.
- DEC-021: Implementar preparo inicial automático e retomável de Chrome e dos dois VS Codes, com progresso, integridade e versões registradas, baixando dos fornecedores para armazenamento persistente.
- DEC-022: Manter inventário persistente de pacotes extras e restauração assistida, separando pacotes oficiais de AUR/locais e indicando dependências, recompilações ou arquivos faltantes.
- DEC-023: Partir de 8 GiB e 6 CPUs lógicas para a VM Docker e ajustar o perfil por medições que incluam Windows, workstation e outros containers.
- DEC-024: Associar a abertura padrão de projetos e arquivos ao Insiders, mantendo o lançamento explícito do Stable.
- DEC-025: Fornecer início sob demanda por comando e atalho Windows, com estado de execução consultável e instruções de operação.
- DEC-026: Automatizar produção semanal e sob demanda no GitHub Actions, validando as duas imagens antes da promoção de stable e registrando o resultado da entrega.
- DEC-027: Exigir atualização da imagem por comando explícito e conclusão do backup antes da troca, mantendo identificação da versão anterior para recuperação.
- DEC-028: Disponibilizar atualização explícita dos aplicativos separada da imagem, incluindo os dois editores, Chrome, CLI e extensões, com registro das versões resultantes.
- DEC-029: Incluir projetos, perfil, aplicativos persistidos e inventário em backups no Windows, antes das atualizações e sob demanda, retendo as duas cópias concluídas mais recentes.
- DEC-038: Permitir a primeira publicação após os testes locais definidos, entregar o roteiro Hyper-V executável e identificar a validação real no destino como pendente até sua execução.
- DEC-031: Medir e verificar a experiência em uma tela 1920 x 1080 com Insiders, projeto Salesforce e Chrome ativos.
- DEC-032: Tratar falha de restauração de programa extra como resultado parcial visível, mantendo o ambiente atualizado disponível e oferecendo nova tentativa ou recuperação do backup.
- DEC-033: Preservar sessão e processos quando a aba for fechada e encerrar a execução apenas pelo comando de parar ou por encerramento do próprio ambiente anfitrião.
- DEC-034: Receber proxy e certificados necessários por configuração opcional assistida, manter os dados no notebook e diagnosticar a conectividade preservando TLS.
- DEC-035: Usar electivus/webtop-arch-kde-base e electivus/webtop-arch-kde-salesforce nos artefatos publicados, comandos, documentação e automação.
- DEC-036: Implementar todos os comandos de operação e o atalho usando CMD, sem executar PowerShell no notebook de destino; distribuir os componentes necessários e verificar o fluxo nessa condição.
- DEC-039: Abrir o repositório GitHub após revisar histórico Git, conteúdo do tracker e resultados do Actions; aplicar MIT ao conteúdo próprio, distribuir os avisos de licença com os comandos e preservar as licenças dos terceiros. A abertura não aprova uma candidata nem publica imagens no Docker Hub.

JDK 21 e Node.js Active LTS são os candidatos levantados para atender às dependências Salesforce; as versões exatas devem ser resolvidas e registradas com a verificação de compatibilidade da entrega. Pacotes Arch precisam de uma estratégia coerente de atualização, inclusive para recompilações AUR, sem combinar uma base nova com partes arbitrárias de um sistema antigo.

A preparação e as atualizações devem distinguir etapa pendente, em execução, concluída e com falha. Repetir uma operação deve permitir retomada e produzir um resultado que indique o estado real, inclusive quando apenas programas extras não forem recuperados. Falha nos componentes fornecidos pela variante deve continuar impedindo que a entrega seja declarada aprovada.

O backup deve representar um ponto consistente do estado pessoal. Falha ou falta de espaço para concluí-lo deve impedir a alteração que depende desse backup; tentativas incompletas não podem substituir cópias válidas na retenção. A recuperação deve selecionar explicitamente um backup e relacionar o estado restaurado à imagem e às versões de aplicativos correspondentes. Trocar apenas a imagem não equivale a recuperar os dados.

## Testing Decisions

A interface principal de aceitação será a workstation entregue: os comandos públicos de instalação e operação, o desktop resultante e os artefatos publicados. Os testes devem observar comportamento, arquivos produzidos, disponibilidade dos aplicativos e resultados dos comandos, evitando depender da organização interna dos módulos. Essa interface reúne os cenários de instalação e verificação apresentados no entendimento consolidado e confirmados pelo usuário em Q27; a especificação preserva essa aprovação.

Na entrevista inicial, o repositório continha documentação de descoberta, vocabulário e decisões, e a automação de aceitação ainda precisava ser criada no nível dessas operações públicas. O CI executará os cenários automatizáveis das imagens e da operação; o notebook de teste verificará o fluxo Windows com Docker Desktop e WSL2. O roteiro de destino verificará o mesmo comportamento aplicável com Hyper-V, registrando separadamente o resultado.

Os cenários devem usar projetos, dados e recursos Docker dedicados à validação, com resultados repetíveis e diagnóstico suficiente para localizar a etapa que falhou.

1. **Instalação das duas variantes:** partir de estado novo, iniciar o desktop e abrir seus aplicativos esperados. A base deve funcionar por si só; Salesforce deve abrir um projeto de exemplo com CLI e serviços das extensões disponíveis nos dois canais do VS Code.
2. **Preparo inicial e retomada:** observar progresso, interromper uma etapa de download ou instalação e executar a retomada. Etapas concluídas devem ser reaproveitadas, versões e integridade registradas, e a falha não pode aparecer como preparo completo.
3. **Uso local e localização:** verificar o endpoint restrito ao notebook, entrada direta, interface em inglês, formatos brasileiros, fuso e digitação ABNT2 de acentos, cedilha e símbolos no terminal, navegador e editor.
4. **Ciclo da sessão:** iniciar pelo Windows, manter uma tarefa observável, fechar e reabrir a aba e comprovar continuidade da tarefa e da sessão. O comando de parar deve encerrar a execução; iniciar novamente deve recuperar os dados persistidos, sem prometer continuidade dos processos encerrados.
5. **Projetos e troca de arquivos:** salvar um projeto e preferências, recriar o container e comprovar o conteúdo persistido. Transferir arquivos nos dois sentidos entre Windows e workstation e verificar conteúdo e propriedades necessárias ao trabalho Linux.
6. **Docker e Compose:** a partir da workstation, executar um projeto representativo que construa uma imagem por contexto local, monte arquivos do projeto e realize leitura e escrita observáveis. Confirmar o uso do mesmo engine Docker Desktop; listar containers sozinho não comprova esse fluxo.
7. **Inventário e restauração:** instalar programas extras representativos, registrar inventários oficiais e AUR/locais, recriar o ambiente e exercer a restauração assistida. Comprovar ao menos o caminho viável encontrado e relatar os limites de recuperação sem confundir inventário com preservação de binários.
8. **Restauração parcial:** provocar indisponibilidade ou falha de compilação de um programa extra, observar o relatório e continuar usando o desktop e os aplicativos que funcionaram. Exercer nova tentativa e recuperação; repetir a falha com um componente fornecido pela variante deve impedir a aprovação da entrega.
9. **Backup e recuperação:** criar um estado conhecido com projeto, preferências, aplicativo persistido e inventário; concluir um backup, alterar o estado e recuperá-lo. Comprovar consistência dos dados e das versões associadas, retenção das duas cópias concluídas e preservação de cópias válidas quando uma nova tentativa falhar.
10. **Atualização da imagem:** publicar ou disponibilizar um candidato e verificar que a instalação existente só muda após o comando explícito e o backup concluído. Exercitar falha no backup, falha de atualização e recuperação, conferindo versão escolhida e estado pessoal resultante.
11. **Atualização dos aplicativos:** atualizar ferramentas pelo comando próprio e verificar lançadores, extensões e versões registradas. Confirmar que a operação pode ocorrer independentemente da troca de imagem e que existe recuperação pelo backup correspondente.
12. **Configuração corporativa opcional:** verificar uso sem configuração corporativa e uso com proxy e cadeia de confiança de teste. Diagnosticar falhas de conexão, aceitar a cadeia válida configurada e continuar rejeitando conexões inválidas; confirmar que configurações privadas não entram nos artefatos públicos.
13. **Dimensionamento e experiência:** medir partida com preparo inicial separado das partidas seguintes, CPU, RAM e comportamento do desktop em Full HD durante uso de Insiders, projeto Salesforce e Chrome. Avaliar a carga conjunta do Windows e dos demais containers, registrar o perfil escolhido e eventuais limitações de renderização ou resposta.
14. **Contrato da entrega:** verificar os nomes públicos, arquitetura, digests, versões coordenadas, relação entre base e Salesforce, preservação de tags fixas e destino de stable. Uma falha nos testes deve impedir a promoção; uma falha parcial de publicação deve ser visível e não pode ser anunciada como entrega coordenada concluída.
15. **Automação e conteúdo público:** exercitar o acionamento sob demanda e validar a configuração semanal, além das instruções que permitem usar a distribuição pública. Inspecionar os artefatos para confirmar a estratégia de obtenção dos aplicativos oficiais e a ausência de configurações, credenciais e conteúdo corporativos embutidos.
16. **Evidência de plataforma:** produzir relatório da validação WSL2 local e fornecer o roteiro executável Hyper-V com resultados e limitações identificáveis. A primeira publicação pode ocorrer com a execução no destino pendente; sucesso no WSL2 não deve ser reportado como teste real em Hyper-V.
17. **Operação pelo CMD:** executar instalação, atalho e comandos de operação a partir de `cmd.exe`, sem invocar `powershell.exe` ou `pwsh.exe`; o roteiro de destino e as instruções públicas devem exercer o mesmo contrato.
18. **Código público:** registrar o escopo e os limites da revisão de exposição, verificar as licenças no pacote de comandos e confirmar acesso anônimo ao código e reconhecimento de MIT pelo GitHub após a mudança de visibilidade.

Os testes dos componentes fornecidos são critérios de aprovação da entrega. A tolerância à restauração parcial se limita aos programas extras do usuário. Não foi acordado um número fixo de latência, consumo ou tempo de instalação; o perfil deverá ser escolhido a partir das medições do cenário confirmado.

## Out of Scope

- Uma terceira imagem de desenvolvimento geral ou uma hierarquia preparada para necessidades futuras.
- Dependência de WSL2, instalação de um segundo engine Docker dentro da workstation ou habilitação automática de Hyper-V no Windows.
- Dependência de PowerShell para instalar, operar, diagnosticar ou recuperar a workstation no notebook de destino.
- Desktop compartilhado por várias pessoas, acesso pela rede ou exposição pública do endpoint sem a revisão do modelo de acesso local.
- Substituição dos produtos oficiais solicitados por Chromium, VSCodium ou code-server; redistribuição dos binários de Chrome e VS Code na imagem pública.
- Preservação incondicional de todos os programas, versões binárias, pacotes indisponíveis ou modificações arbitrárias no sistema; a recuperação de programas extras segue a avaliação de viabilidade e o fluxo assistido.
- Instalação automática de uma nova imagem ou atualização silenciosa dos aplicativos ao iniciar a workstation.
- Backup em nuvem, rotina periódica de backup independente das atualizações ou retenção diferente das duas cópias concluídas acordadas.
- Suporte inicial validado para outras arquiteturas, múltiplas telas ou resoluções maiores que o cenário Full HD escolhido.
- Garantia de aceleração gráfica ou desempenho que ainda não tenha sido medido no backend utilizado.
- Inclusão de contas, projetos reais, credenciais ou configurações corporativas nos artefatos públicos; desativação de TLS como mecanismo de conectividade.
- Configuração de autenticação de organizações Salesforce específicas como parte da imagem genérica.

## Further Notes

O escopo resulta da entrevista Q1–Q27, encerrada e confirmada em 2026-09-14. O levantamento técnico anterior identificou a variante upstream Arch/KDE, o hardware local e Docker VMM; naquele momento, ainda não havia executado uma workstation derivada nem demonstrado desempenho, restauração, integração Compose ou compatibilidade real no notebook de destino. Esses resultados são entregáveis da implementação. As evidências VMM produzidas posteriormente permanecem históricas; novos testes locais usam WSL2.

As 35 decisões ativas anteriores a DEC-039 declaram as obrigações specification, tickets e verification. DEC-039 acrescenta specification e verification; não exige novo ticket funcional porque é uma manutenção da publicação do repositório autorizada diretamente pelo usuário. Cada decisão ativa possui uma consequência acionável em Implementation Decisions e está incluída no marcador abaixo. DEC-014 está substituída por DEC-019 e não constitui uma obrigação ativa desta especificação. DEC-036 registra a correção do usuário em 2026-09-14: a operação no destino deve usar CMD, pois PowerShell é bloqueado. DEC-037 e DEC-038 substituem DEC-005 e DEC-030 após a mudança do ambiente local para WSL2 em 2026-09-16, mantendo Hyper-V como requisito de destino. DEC-039 remove a exclusão anterior da mudança de visibilidade GitHub, conforme pedido de 2026-09-18.

A publicação desta especificação conclui a cobertura de specification, após seu registro no ledger. A decomposição em tickets e as evidências de execução são etapas posteriores; o checkpoint de planejamento usado aqui é intermediário. O marcador deverá ser atualizado para o checkpoint final quando a cobertura dos tickets estiver concluída, antes de uma nova sessão de implementação.

O requisito de destino Hyper-V permanece válido. DEC-038 autoriza a primeira publicação com testes locais e roteiro de destino, sem converter a validação Hyper-V pendente em resultado aprovado. A preparação da publicação também deverá verificar, com autenticação, os repositórios Docker Hub e as permissões necessárias.

O mecanismo de caminhos compartilhados com Docker/Compose, o preparo dos aplicativos e a recuperação consistente dos dados precisam de validação concreta. Se a implementação não puder atender uma decisão ativa, a limitação deverá voltar ao planejamento para ajuste explícito, preservando a condição de viabilidade já acordada para programas extras.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 6b9f83fa52a61d2c655064f2c74d1b4476571886
- Decisions: DEC-001, DEC-002, DEC-003, DEC-004, DEC-006, DEC-007, DEC-008, DEC-009, DEC-010, DEC-011, DEC-012, DEC-013, DEC-015, DEC-016, DEC-017, DEC-018, DEC-019, DEC-020, DEC-021, DEC-022, DEC-023, DEC-024, DEC-025, DEC-026, DEC-027, DEC-028, DEC-029, DEC-031, DEC-032, DEC-033, DEC-034, DEC-035, DEC-036, DEC-037, DEC-038, DEC-039
