# Electivus Arch/KDE Workstation

Workstation Linux local para Windows 11 com Docker Desktop em modo de containers Linux. O destino usa Hyper-V e opera pelo **CMD, com PowerShell bloqueado**. Os comandos e o atalho usam um executável Windows autossuficiente; não exigem WSL2, PowerShell, Python, Go ou habilitação de virtualização no notebook.

Esta entrega implementa o desktop e sua operação local (T01). Chrome oficial e terminal preparado entram em T02; a variante Salesforce e a publicação de `stable` seguem nos tickets seguintes da [especificação](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1). Ainda não existe uma entrega pública aprovada.

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

O desktop usa interface em inglês, formatos brasileiros, fuso `America/Bahia` e teclado ABNT2. Preferências existentes de idioma e teclado no perfil são preservadas. O upstream usa Chromium nesta etapa; ele não representa a entrega do Chrome oficial de T02.

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
python tests\test_commands.py
python tests\browser_acceptance.py
```

O teste de comandos exercita o ponto de entrada CMD no Windows, inclusive caminhos com espaços, atalho, confiança reversível do certificado e preservação de recursos alheios. Também verifica sequências de teclas mortas e modificadores ABNT2 dentro da sessão X11. O teste de navegador exige Chrome e `playwright-cli`; abre uma sessão de automação isolada, verifica caracteres pelo transporte de teclado, fecha a aba e confirma que o mesmo processo continua trabalhando após reabri-la. Os testes removem seus próprios containers e volumes e mantêm relatórios e capturas em `.local/`.

A validação local disponível usa VMM. O campo de backend do diagnóstico informa sua fonte (configuração do Docker Desktop); a evidência de execução é registrada separadamente. A primeira publicação dependerá das verificações completas e do roteiro executável de Hyper-V em T12/T13. Sucesso em VMM não declara Hyper-V validado.
