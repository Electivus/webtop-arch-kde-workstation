# Família de imagens - Planning context

Status: composição, herança, versões, publicação, atualização e backup confirmados; detalhes de recuperação e encerramento da sessão ainda em discussão. O [Decision ledger](decision-ledger.md) registra as escolhas confirmadas; este documento não as substitui. DEC-009 inclui Salesforce, DEC-010 limita a entrega atual a duas imagens e DEC-018 define dois repositórios Docker Hub com versões coordenadas, tags fixas e alias stable.

## Variante e versão

Uma variante atende a um perfil de uso. Uma versão identifica uma entrega daquele perfil. Cada combinação pode resultar em uma imagem publicada. Várias tags também podem apontar para a mesma imagem, sem criar uma cópia de suas camadas.

Proposta de nomes, ainda não criados nem verificados com autenticação no Docker Hub:

| Variante | Conteudo pretendido | Referencia ilustrativa |
| --- | --- | --- |
| Base | Arch, KDE, Webtop, Chrome oficial, Git, Zsh, Oh My Zsh e ajustes comuns | `electivus/webtop-arch-kde-base:1.0.0` |
| Salesforce | Base mais VS Code Stable/Insiders, Salesforce CLI, extensoes, Java e Node necessarios | `electivus/webtop-arch-kde-salesforce:1.0.0` |

Conforme DEC-018, serão dois repositórios Docker Hub, um por imagem. O código e as rotinas de construção podem continuar neste único repositório Git. Os nomes exatos acima ainda são propostas e precisam ser verificados no registry. A separação dos repositórios não impede o compartilhamento das camadas.

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
- DEC-030 permite a primeira publicação após os testes locais em VMM, identificando a validação real em Hyper-V como pendente e fornecendo um roteiro executável para o destino. Essa distinção deve acompanhar as evidências da entrega.
- No Docker Hub, há configuração de imutabilidade para todas as tags ou para padrões específicos. Tags numéricas fixas podem ser protegidas preservando a mobilidade de aliases. A disponibilidade/configuração efetiva dos repositórios Electivus ainda não foi inspecionada.

## Estado pessoal e atualização

O pacote de programas fornecido por uma variante é distinto dos arquivos e das preferências do usuário. A documentação Webtop/Selkies informa que pacotes instalados manualmente no sistema são perdidos quando o container é recriado; o diretório pessoal `/config` só persiste se tiver armazenamento persistente configurado.

DEC-019 substitui DEC-014 e condiciona a preservação dos programas instalados com pacman/AUR à viabilidade técnica. DEC-022 escolhe inventário persistente e restauração assistida, separando pacman e AUR, com viabilidade a validar na implementação. A conciliação com novas versões da base, falhas de restauração e o procedimento de recuperação ainda precisam ser detalhados. Voltar a uma imagem anterior não reverte automaticamente alterações no estado pessoal ou no sistema preservado.

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

## Fontes primárias

Consultadas em 2026-09-13, horário de America/Bahia; os artefatos Markdown retornados pelo Scrape Golden foram lidos.

- [Docker image pull](https://docs.docker.com/reference/cli/docker/image/pull/): reutilização de camadas, múltiplas tags para o mesmo conteúdo e seleção por digest.
- [Docker — Building best practices](https://docs.docker.com/build/building/best-practices/): etapas reutilizáveis para imagens com componentes comuns, dependências necessárias e reconstrução de imagens para incorporar atualizações.
- [Docker Hub — Immutable tags](https://docs.docker.com/docker-hub/repos/manage/hub-images/immutable-tags/): proteção contra sobrescrita de tags e seleção de padrões para imutabilidade.
- [LinuxServer.io — Installing Applications](https://docs.linuxserver.io/selkies/user-guide/installing-apps/): diferenças entre pacotes do sistema, aplicações no diretório pessoal, instalação no início e imagens derivadas.
