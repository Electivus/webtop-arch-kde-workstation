# Electivus Arch/KDE Workstation

Workstation Linux local para Windows 11 com Docker Desktop em modo de containers Linux. O destino usa Hyper-V e opera pelo **CMD, com PowerShell bloqueado**. Os comandos e o atalho usam um executável Windows autossuficiente; não exigem WSL2, PowerShell, Python, Go ou habilitação de virtualização no notebook.

Esta candidata acrescenta Chrome oficial, Git, Zsh/Oh My Zsh e a variante Salesforce ao desktop local. A publicação de `stable` e as operações de manutenção seguem nos tickets da [especificação](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1). Ainda não existe uma entrega pública aprovada.

## Preparar e iniciar

Até a publicação das imagens, construa a candidata a partir deste checkout:

```bat
docker build --file images/base/Dockerfile --build-arg VERSION=local --tag electivus/webtop-arch-kde-base:local .
distribution\windows\setup.cmd electivus/webtop-arch-kde-base:local "%LOCALAPPDATA%\Electivus\workstation-tools"
cd /d "%LOCALAPPDATA%\Electivus\workstation-tools"
```

No Docker Desktop, selecione um contexto local e containers Linux. O perfil inicial acordado para a **VM Docker** é 8 GiB e 6 CPUs lógicas. A instalação reserva por padrão até 6 GiB e 4 CPUs para a workstation, deixando recursos para Windows e outros containers. Estes limites são ajustáveis; as medições do cenário Salesforce serão entregues em T12. A instalação recusa limites maiores que os disponíveis no engine.

```bat
workstation.cmd install --image electivus/webtop-arch-kde-base:local
workstation.cmd start
workstation.cmd certificate
workstation.cmd trust
workstation.cmd start --open-browser
```

O comando `trust` instala **apenas o certificado de servidor desta instalação**, limitado a `localhost` e `127.0.0.1`, no armazenamento de confiança do usuário Windows atual. Não requer administrador. `certificate` mostra SHA-256, impressão SHA-1 (`thumbprint`), validade e arquivo público. Na confirmação de segurança do Windows, confira `localhost` e a impressão SHA-1 antes de aceitar. A chave privada é criada no volume pessoal, nunca no build. Nenhum comando desativa a verificação TLS. Se a política corporativa impedir a instalação da confiança, apresente esse certificado ao suporte responsável antes de continuar.

Ao iniciar, a workstation renova o certificado quando restam até 30 dias de validade, inclusive se ele já venceu. O comando informa quando a impressão digital mudou. Nesse caso, execute `untrust` e `trust` para atualizar a confiança Windows. Cópias públicas dos certificados anteriores ficam no perfil para permitir a remoção da confiança mesmo após a renovação.

O desktop abre em `https://localhost:3001/`, sem outra senha. Somente `127.0.0.1` recebe a porta publicada; o acesso não é disponibilizado na rede do notebook. Fechar a aba desconecta o vídeo e preserva a sessão e seus processos. O container não inicia automaticamente com Docker ou com Windows.

```bat
workstation.cmd status
workstation.cmd stop
```

`stop` encerra os processos. `start` reutiliza o container parado e o volume, iniciando uma nova sessão. Os comandos retornam JSON com estado, imagem, digest upstream, limites e informações do engine. Uma tag nova no registry não atualiza a instalação ao iniciar.

## Atalho e perfil local

`install` grava o perfil e uma cópia de `workstation.cmd` e `workstation.exe` em `%LOCALAPPDATA%\Electivus\Workstation\base\tools`. O arquivo `Start Workstation.lnk` dentro do perfil inicia o desktop e abre o navegador. Pode ser copiado para a área de trabalho; ele aponta diretamente para o executável instalado e continua funcionando sem o checkout original. A criação do atalho e a confiança do certificado usam APIs nativas do Windows.

Para uma instalação adicional ou um teste, escolha diretório, nome e porta próprios:

```bat
workstation.cmd install --profile "%LOCALAPPDATA%\Electivus\Workstation\teste" --name electivus-teste --port 13001 --image electivus/webtop-arch-kde-base:local --memory 2560 --cpus 4
workstation.cmd start --profile "%LOCALAPPDATA%\Electivus\Workstation\teste"
```

O limite menor serve para ensaios locais em uma VM com 4 GiB; não representa o dimensionamento final do fluxo Salesforce. Os comandos fixam o contexto Docker escolhido na instalação e recusam containers ou volumes de outra instalação com o mesmo nome. Não há comandos globais de limpeza.

O desktop usa interface em inglês, formatos brasileiros, fuso `America/Bahia` e teclado ABNT2. Preferências existentes de idioma e teclado no perfil são preservadas.

## Projetos e Docker

Salve os projetos em `~/projects` (`/config/projects`); o menu **Workstation Projects** abre essa pasta no Dolphin. O volume Linux preserva conteúdo, nomes sensíveis a maiúsculas, permissões e links simbólicos após recriar o container.

Para habilitar a troca de arquivos, crie uma pasta Windows, adicione-a em **Docker Desktop > Settings > Resources > File sharing** e passe `--exchange "C:\caminho\da\pasta"` ao comando `install`. Ela aparece em `~/WindowsExchange` e `/exchange`. O controlador verifica o acesso nos dois sentidos e informa caminhos indisponíveis ou compartilhamento ausente.

Docker e Compose no terminal controlam o mesmo engine do notebook. `workstation-docker-check` verifica a conexão e informa o volume pessoal. O [guia de projetos e Compose](docs/projects.md) contém a configuração CMD, a estratégia de caminhos e um exemplo que constrói uma imagem, monta o projeto Linux e grava resultados persistentes.

## Aplicativos e terminal

No primeiro desktop, uma janela de terminal mostra o preparo automático. Chrome e os VS Codes são obtidos dos repositórios oficiais dos fornecedores: o preparo verifica a assinatura do índice, o hash e a versão de cada pacote. A imagem contém as fontes, as chaves esperadas e as dependências; os binários proprietários ficam no volume pessoal. Como Arch usa pacman, o preparo extrai os aplicativos dos pacotes oficiais sem executar um gerenciador APT dentro do Arch.

O menu oferece **Prepare applications** para uma nova tentativa e **Google Chrome** para abrir o navegador. Também é possível acompanhar e retomar pelo CMD:

```bat
workstation.cmd prepare --status
workstation.cmd prepare
```

`prepare` mostra as etapas no terminal e retorna JSON. `--status` distingue `pending`, `running`, `failed` e `completed`, informa o aplicativo e a etapa atuais e inclui o motivo de uma falha. Downloads parciais e etapas concluídas são reutilizados; uma versão nova só substitui `current` depois de validada. Iniciar ou recriar a workstation com o mesmo volume não baixa novamente aplicativos compatíveis.

O Chrome executa como o usuário do desktop, com o sandbox de namespaces ativo. O lançador incorpora um perfil seccomp baseado no Docker, acrescido das permissões de namespaces necessárias ao Chromium. A origem e a alteração estão em [THIRD-PARTY.md](cmd/workstation/THIRD-PARTY.md).

Na primeira abertura, o KDE Wallet pode solicitar a criação de uma carteira para guardar senhas e tokens dos aplicativos. Essa configuração pessoal fica no volume; escolha sua forma de proteção antes de salvar credenciais. Ela é independente do acesso HTTPS ao desktop.

O terminal usa Zsh com Oh My Zsh e os plugins `git`, `zsh-autosuggestions` e `zsh-syntax-highlighting`. `~/.zshrc` é criado somente quando ausente. Personalizações, histórico e diretórios `~/.config/oh-my-zsh/custom` e `~/.cache/oh-my-zsh` pertencem ao volume. Execuções não interativas não carregam a configuração interativa.

Proxy e CAs corporativas podem ser configurados por `install --network-config` ou pelo comando `network` em uma instalação existente. O [guia de conectividade](docs/network.md) mostra o arquivo opcional, o diagnóstico e a remoção pelo CMD. A configuração fica no perfil local e é aplicada no início da workstation.

## Variante Salesforce

A construção exige a base correspondente e produz um container autossuficiente:

```bat
docker build --file images/salesforce/Dockerfile --build-arg BASE_IMAGE=electivus/webtop-arch-kde-base:local --build-arg VERSION=local --tag electivus/webtop-arch-kde-salesforce:local .
workstation.cmd install --profile "%LOCALAPPDATA%\Electivus\Workstation\salesforce" --name electivus-salesforce --image electivus/webtop-arch-kde-salesforce:local --port 13002
workstation.cmd start --profile "%LOCALAPPDATA%\Electivus\Workstation\salesforce" --open-browser
workstation.cmd prepare --profile "%LOCALAPPDATA%\Electivus\Workstation\salesforce"
```

A variante oferece Node 24 LTS e Java 21, instala a CLI Salesforce selecionada com integridade SHA-512 e o Salesforce Extension Pack do Marketplace nos dois editores. O preparo confere todos os membros e dependências declarados pelo Pack e recupera componentes ausentes. O resultado registra as versões efetivas, fontes, hashes e extensões instaladas. A CLI e os aplicativos persistem no volume; Java e Node acompanham a imagem.

No terminal Linux, `code-insiders` abre o editor padrão, `code` abre Stable e `workstation-project` abre o diretório atual no Insiders. Arquivos de texto e projetos `.code-workspace` usam Insiders por padrão. `sf project generate --name exemplo --output-dir ~/projects` cria um projeto sem credenciais de organização.

Perfis novos dos editores desativam atualizações automáticas do editor e das extensões; configurações pessoais existentes são preservadas. O comando `prepare` recupera a preparação e mantém instalações já funcionais. O comando separado de atualização explícita pertence a T10.

Para remover a confiança local posteriormente, execute `untrust` e confirme a remoção do mesmo certificado caso o Windows apresente a janela:

```bat
workstation.cmd untrust
```

`untrust` usa os certificados públicos salvos no perfil, incluindo os anteriores e vencidos. Funciona com o container removido, com Docker Desktop parado ou sem o comando Docker disponível. Mantenha o perfil até concluir essa limpeza.

## Verificar

Para desenvolvimento, o próprio Docker compila os comandos Windows e Linux com o compilador fixado no Dockerfile. Os testes externos usam Python 3 apenas na máquina de desenvolvimento ou no CI; Python não integra a instalação do notebook.

```bat
docker build --file images/base/Dockerfile --target commands-export --output type=local,dest=.local/cli .
set WORKSTATION_TEST_IMAGE=electivus/webtop-arch-kde-base:local
set WORKSTATION_SALESFORCE_TEST_IMAGE=electivus/webtop-arch-kde-salesforce:local
python tests\test_commands.py
python tests\test_preparation.py
python tests\test_projects.py
python tests\test_docker_projects.py
python tests\test_salesforce.py
python tests\test_network.py
python tests\test_network_apps.py
python tests\browser_acceptance.py
python tests\browser_apps.py
```

O teste de comandos exercita o ponto de entrada CMD no Windows, inclusive caminhos com espaços, atalho, confiança reversível do certificado e preservação de recursos alheios. Também verifica sequências de teclas mortas e modificadores ABNT2 dentro da sessão X11. O teste de navegador exige Chrome e `playwright-cli`; abre uma sessão de automação isolada, verifica caracteres pelo transporte de teclado, fecha a aba e confirma que o mesmo processo continua trabalhando após reabri-la. Os testes removem seus próprios containers e volumes e mantêm relatórios e capturas em `.local/`.

Os testes de aplicativos usam os comandos entregues, uma falha real de permissão e a interrupção do container durante o download de um editor. O teste de serviços abre o projeto de exemplo em cada VS Code entregue e usa a API pública de testes do editor para verificar diagnóstico Apex, sua correção e conclusão de atributo LWC. Essa instrumentação fica somente em `tests/`. A variante Salesforce requer o perfil de recursos indicado acima; limites de 2,5 e 3,25 GiB encerraram o editor por falta de memória no ensaio local.

A validação local disponível usa VMM. O campo de backend do diagnóstico informa sua fonte (configuração do Docker Desktop); a evidência de execução é registrada separadamente. A primeira publicação dependerá das verificações completas e do roteiro executável de Hyper-V em T12/T13. Sucesso em VMM não declara Hyper-V validado.
