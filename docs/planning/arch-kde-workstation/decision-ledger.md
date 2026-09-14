# Decision ledger

- Format: v1
- Effort: arch-kde-workstation

Decision meanings are immutable after a Planning checkpoint. Coverage advances from pending to complete, and evidence may be appended without replacing prior values.

## DEC-001
- Status: active
- Decision: Criar uma workstation Linux baseada em Webtop com Arch Linux e KDE.
- Context: O usuario quer trabalhar em um desktop Linux usando o Docker disponivel no notebook corporativo.
- Rationale: Arch Linux, KDE e Webtop foram escolhidos explicitamente no pedido inicial.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-002
- Status: active
- Decision: Suportar o notebook de destino com containers Linux no Docker via Hyper-V, sem depender de WSL2.
- Context: No notebook de destino o WSL2 e bloqueado, mas Docker via Hyper-V esta disponivel segundo o usuario.
- Rationale: A workstation precisa funcionar dentro das condicoes existentes no destino.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-003
- Status: active
- Decision: Publicar a imagem no Docker Hub da organizacao Electivus.
- Context: O usuario pediu uma imagem distribuivel na sua organizacao; nome do repositorio, visibilidade e politica de tags ainda dependem da entrevista.
- Rationale: O Docker Hub e o canal de distribuicao escolhido para instalar a workstation no outro notebook.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-004
- Status: active
- Decision: Otimizar o perfil de execucao para o mesmo modelo e configuracao de hardware deste notebook.
- Context: O usuario informou que o notebook de destino e equivalente ao notebook atual; o inventario local identificou um Dell Latitude 5450 com Core Ultra 7 165U e 32 GB de RAM nominais.
- Rationale: O hardware local serve como referencia de dimensionamento; limites efetivos do Docker e carga concorrente ainda precisam ser definidos.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-005
- Status: active
- Decision: Usar o Docker VMM deste notebook como ambiente local de teste, preservando Hyper-V como requisito de destino.
- Context: O usuario configurou Docker VMM porque habilitar Hyper-V neste notebook exige administrador; nao ha autorizacao ou necessidade de habilitar esse recurso durante a entrevista.
- Rationale: O ambiente local e a aproximacao disponivel; resultados em Docker VMM nao constituem prova de execucao no backend Hyper-V.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-006
- Status: active
- Decision: Priorizar desenvolvimento com editor, navegador, terminal e ferramentas de projeto.
- Context: Na resposta Q1, o usuario escolheu desenvolvimento como atividade principal; aplicativos, linguagens, CLIs e versoes especificas ainda nao foram definidos.
- Rationale: O perfil de aplicativos e a carga de validacao devem corresponder ao trabalho de desenvolvimento.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-007
- Status: active
- Decision: Oferecer uma workstation individual acessada somente pelo navegador do proprio notebook.
- Context: Na resposta Q2, o usuario escolheu uma pessoa e acesso apenas local.
- Rationale: O acesso remoto e o uso por varias pessoas ficam fora do escopo acordado; o endpoint do desktop deve se restringir ao notebook.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-008
- Status: active
- Decision: Distribuir uma imagem publica e generica, reutilizavel por outras pessoas, sem configuracoes ou conteudo corporativos embutidos.
- Context: Na resposta Q3, o usuario escolheu publicacao publica e generica no Docker Hub da Electivus.
- Rationale: A imagem precisa ser compartilhavel; personalizacao e configuracoes especificas de cada usuario ou empresa ficam fora do artefato publico.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-009
- Status: active
- Decision: Incluir uma variante da workstation especializada em desenvolvimento Salesforce.
- Context: Ao discutir versionamento, o usuario informou que tambem sera criada uma imagem para desenvolvimento Salesforce; a decomposicao exata entre base, dev geral e Salesforce ainda e uma proposta.
- Rationale: A familia de imagens deve atender ao fluxo Salesforce sem exigir esse conjunto de ferramentas de todos os usuarios.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-010
- Status: active
- Decision: Limitar a entrega atual a duas imagens: base e desenvolvimento Salesforce, com Salesforce derivando diretamente da base.
- Context: Na resposta Q4, o usuario descartou a variante dev geral e pediu somente base e dev Salesforce; uma revisao da hierarquia fica para uma necessidade futura.
- Rationale: Atender ao uso atual com uma hierarquia simples, sem antecipar variantes ou camadas para necessidades hipoteticas.
- ADR: none
- Constraints: Nao incluir uma imagem dev geral nem preparar uma hierarquia adicional nesta entrega.
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-011
- Status: active
- Decision: Disponibilizar VS Code Stable e VS Code Insiders, Google Chrome oficial, Git, Salesforce CLI e extensoes Salesforce na workstation de desenvolvimento Salesforce.
- Context: Na resposta Q5, o usuario aceitou as ferramentas propostas e especificou os dois canais do VS Code e o navegador Google Chrome oficial; linguagens, versoes e plugins Salesforce extras ainda dependem de levantamento.
- Rationale: Esses sao os aplicativos e ferramentas solicitados para o trabalho diario; a distribuicao publica deve preservar as condicoes dos fornecedores.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-012
- Status: active
- Decision: Usar Zsh como shell padrao, com Oh My Zsh e plugins recomendados.
- Context: Na resposta Q5, o usuario pediu explicitamente Zsh padrao, Oh My Zsh e autorizou a selecao de plugins recomendados.
- Rationale: Oferecer um terminal preparado para desenvolvimento; a selecao concreta dos plugins sera feita a partir de suas fontes oficiais e compatibilidade.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-013
- Status: active
- Decision: Permitir executar Docker e Compose na workstation para controlar o Docker Desktop existente no notebook.
- Context: Na resposta Q7, o usuario escolheu controlar o Docker Desktop do notebook a partir do terminal Linux.
- Rationale: Reutilizar o engine disponivel e seus containers; a workstation nao precisa de um segundo engine isolado para esse fluxo.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-014
- Status: superseded
- Superseded by: DEC-019
- Decision: Preservar os programas que o usuario instalar manualmente com pacman ou AUR ao atualizar ou recriar a workstation.
- Context: Na resposta Q8, o usuario pediu persistencia tambem para programas instalados manualmente no sistema; a base Webtop padrao nao atende so com a persistencia do diretorio pessoal.
- Rationale: A workstation deve manter as ferramentas adicionadas pelo usuario durante o uso; o mecanismo e o comportamento de conciliacao com atualizacoes ainda precisam ser definidos.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none
## DEC-015
- Status: active
- Decision: Manter os projetos no armazenamento Linux do Docker e oferecer uma pasta de troca com o Windows.
- Context: Na resposta Q9, o usuario escolheu projetos no Linux com uma pasta de troca para o Windows.
- Rationale: O trabalho principal ocorre no ambiente Linux, com uma area explicita para transferencia de arquivos com o notebook.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-016
- Status: active
- Decision: Abrir o desktop local diretamente, sem senha propria da workstation, usando o acesso a sessao do Windows como controle.
- Context: Na resposta Q10, o usuario escolheu entrada direta; DEC-007 ja restringe o uso ao navegador do proprio notebook.
- Rationale: Evitar um segundo login no fluxo pessoal local; a publicacao do endpoint deve permanecer restrita ao notebook.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-017
- Status: active
- Decision: Usar interface em ingles com localizacao brasileira, teclado ABNT2 e fuso America/Bahia.
- Context: Na resposta Q11, o usuario escolheu interface em ingles, mantendo localizacao para o Brasil e especificando teclado ABNT2; o fuso America/Bahia proposto na pergunta permanece aplicavel.
- Rationale: Combinar menus e mensagens em ingles com formatos regionais e entrada de texto brasileiros.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-018
- Status: active
- Decision: Publicar base e Salesforce em dois repositorios Docker Hub, com versoes coordenadas, tags fixas e alias stable.
- Context: Na resposta Q6 reformulada para duas imagens, o usuario escolheu dois repositorios, entregas coordenadas e tags fixas como 1.0.0 mais stable.
- Rationale: Identificar cada perfil separadamente, manter as entregas da familia alinhadas e oferecer um alias para a versao aprovada sem sobrescrever tags fixas.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-019
- Status: active
- Decision: Preservar programas instalados manualmente com pacman ou AUR somente se houver uma solucao tecnicamente viavel.
- Context: Apos a resposta Q8, o usuario esclareceu que a preservacao dos programas instalados e condicionada a viabilidade; ela nao deve ser tratada como garantia incondicional.
- Rationale: Avaliar primeiro a compatibilidade com atualizacoes do Arch, o mecanismo de recuperacao e o custo de manutencao antes de fechar a abordagem.
- ADR: none
- Obligations: specification, tickets, verification
- Supersedes: DEC-014
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-020
- Status: active
- Decision: Oferecer KDE, Chrome oficial, Git, Zsh e Oh My Zsh na base; a variante Salesforce acrescenta VS Code Stable e Insiders, Salesforce CLI, extensoes Salesforce, Java e Node necessarios.
- Context: Na resposta Q12, o usuario escolheu a base como desktop utilizavel e o desenvolvimento completo na variante Salesforce; o modo de preparar os aplicativos oficiais continua pendente em Q13.
- Rationale: Tornar a base util por si so e concentrar as ferramentas especializadas na variante Salesforce, mantendo a heranca direta ja definida.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-021
- Status: active
- Decision: Preparar automaticamente os aplicativos oficiais no primeiro inicio, com progresso e retomada apos falhas, baixando dos fornecedores para armazenamento persistente.
- Context: Na resposta Q13, o usuario escolheu preparacao automatica no primeiro inicio para VS Code Stable/Insiders e Chrome oficiais, ciente de que o preparo inicial exige internet.
- Rationale: Entregar os aplicativos oficiais sem republicar seus binarios na imagem publica e reduzir o trabalho manual de instalacao.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-022
- Status: active
- Decision: Incluir inventario persistente de pacotes e restauracao assistida para programas extras, tratando pacman e AUR separadamente e validando a viabilidade na implementacao.
- Context: Na resposta Q14, o usuario escolheu inventario e restauracao assistida; DEC-019 condiciona a preservacao a viabilidade, e pacotes AUR podem exigir recompilacao ou intervencao.
- Rationale: Recuperar o conjunto de ferramentas pessoais por um procedimento verificavel, sem prometer preservacao arbitraria de binarios ou de todo o sistema.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-023
- Status: active
- Decision: Priorizar equilibrio entre Windows e Linux e dimensionar os recursos por testes, usando 8 GiB de RAM e 6 CPUs logicas para a VM Docker como ponto inicial proposto.
- Context: Na resposta Q15, o usuario escolheu equilibrio com ajuste por testes; a proposta considera o notebook com 32 GB e a existencia de outros containers no mesmo Docker Desktop.
- Rationale: Evitar comprometer o uso do Windows e ajustar o perfil a carga medida da workstation.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-024
- Status: active
- Decision: Usar VS Code Insiders como editor padrao para abrir projetos e arquivos, mantendo VS Code Stable disponivel separadamente.
- Context: Na resposta Q16, o usuario escolheu explicitamente VS Code Insiders.
- Rationale: Fazer a abertura habitual de projetos seguir o canal preferido pelo usuario sem remover o canal Stable.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-025
- Status: active
- Decision: Iniciar a workstation sob demanda por comando ou atalho no Windows.
- Context: Na resposta Q17, o usuario escolheu inicio sob demanda, em vez de inicio automatico junto ao Docker Desktop.
- Rationale: Consumir os recursos da workstation quando o usuario decidir utiliza-la.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-026
- Status: active
- Decision: Produzir e publicar automaticamente as duas imagens pelo GitHub Actions, em rotina semanal e sob demanda, promovendo stable somente apos os testes definidos para a entrega.
- Context: Na resposta Q18, o usuario escolheu publicacao automatica apos testes, semanal e sob demanda; DEC-018 ja define dois repositorios, versoes coordenadas e tags fixas mais stable.
- Rationale: Manter entregas regulares e permitir atualizacoes extraordinarias com o mesmo processo de validacao.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-027
- Status: active
- Decision: Aplicar novas versoes da imagem no notebook por comando explicito, com backup antes da troca.
- Context: Na resposta Q19, o usuario escolheu atualizacao por comando com backup antes da troca; a workstation inicia sob demanda conforme DEC-025.
- Rationale: Preservar o controle do usuario sobre a interrupcao da sessao e manter um ponto de recuperacao anterior a atualizacao.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-028
- Status: active
- Decision: Atualizar VS Code Stable/Insiders, Google Chrome, Salesforce CLI e extensoes por comando explicito, independente da imagem, registrando as versoes efetivas.
- Context: Na resposta Q20, o usuario escolheu atualizacao por comando com versoes registradas; DEC-021 preve aplicativos oficiais preparados para armazenamento persistente.
- Rationale: Permitir atualizar as ferramentas separadamente da imagem e identificar o conjunto efetivamente instalado para diagnostico e reproducao do ambiente.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-029
- Status: active
- Decision: Fazer backup local no Windows de projetos, perfil pessoal, aplicativos persistidos e inventario antes das atualizacoes e sob demanda, mantendo os dois backups concluidos mais recentes.
- Context: Na resposta Q21, o usuario escolheu backup antes das atualizacoes e por comando manual, com retencao das duas copias concluidas mais recentes.
- Rationale: Manter recuperacao do estado pessoal com armazenamento limitado e excluir da retencao as tentativas incompletas.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-030
- Status: active
- Decision: Permitir a primeira publicacao apos os testes locais no Docker VMM, declarando a validacao real em Hyper-V como pendente e entregando um roteiro executavel de verificacao para o notebook de destino.
- Context: Na resposta Q22, o usuario escolheu publicar apos testes locais e entregar a verificacao para o destino, que nao esta acessivel nesta sessao; DEC-002 mantem Hyper-V como requisito.
- Rationale: Avancar com a evidencia disponivel sem apresentar testes no VMM como comprovacao de funcionamento real em Hyper-V.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none

## DEC-031
- Status: active
- Decision: Usar uma tela Full HD de 1920 x 1080, VS Code Insiders com projeto Salesforce e Google Chrome como cenario visual de validacao.
- Context: Na resposta Q23, o usuario escolheu uma tela Full HD com Insiders e Chrome para orientar os testes de uso no notebook.
- Rationale: Avaliar a experiencia com uma carga representativa do uso escolhido e dimensionar recursos com esse perfil.
- ADR: none
- Obligations: specification, tickets, verification
- Coverage:
  - specification: pending
  - tickets: pending
  - verification: pending
- Evidence:
  - specification: none
  - tickets: none
  - verification: none
