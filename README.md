# Electivus Arch/KDE Workstation

Workstation Linux local para Windows 11 com Docker Desktop em modo de containers Linux. O destino usa Hyper-V; os comandos não exigem WSL2, administrador ou habilitação de virtualização.

Esta entrega implementa o desktop e sua operação local (T01). Chrome oficial e terminal preparado entram em T02; a variante Salesforce e a publicação de `stable` seguem nos tickets seguintes da [especificação](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1). Ainda não existe uma entrega pública aprovada.

## Preparar e iniciar

Até a publicação das imagens, construa a candidata a partir deste checkout:

```powershell
docker build --file images/base/Dockerfile --build-arg VERSION=local --tag electivus/webtop-arch-kde-base:local .
```

No Docker Desktop, selecione um contexto local e containers Linux. O perfil inicial acordado para a **VM Docker** é 8 GiB e 6 CPUs lógicas. A instalação reserva por padrão até 6 GiB e 4 CPUs para a workstation, deixando recursos para Windows e outros containers. Estes limites são ajustáveis; as medições do cenário Salesforce serão entregues em T12. A instalação recusa limites maiores que os disponíveis no engine.

```powershell
.\scripts\Workstation.ps1 install -Image electivus/webtop-arch-kde-base:local
.\scripts\Workstation.ps1 start
.\scripts\Workstation.ps1 certificate
.\scripts\Workstation.ps1 trust
.\scripts\Workstation.ps1 start -OpenBrowser
```

O comando `trust` instala **apenas o certificado de servidor desta instalação**, limitado a `localhost` e `127.0.0.1`, no armazenamento de confiança do usuário Windows atual. Não requer administrador. `certificate` mostra a impressão SHA-256, validade e arquivo público. A chave privada é criada no volume pessoal, nunca no build. Nenhum comando desativa a verificação TLS. Se a política corporativa impedir a instalação da confiança, apresente esse certificado ao suporte responsável antes de continuar.

O desktop abre em `https://localhost:3001/`, sem outra senha. Somente `127.0.0.1` recebe a porta publicada; o acesso não é disponibilizado na rede do notebook. Fechar a aba desconecta o vídeo e preserva a sessão e seus processos. O container não inicia automaticamente com Docker ou com Windows.

```powershell
.\scripts\Workstation.ps1 status
.\scripts\Workstation.ps1 stop
```

`stop` encerra os processos. `start` reutiliza o container parado e o volume, iniciando uma nova sessão. Os comandos retornam JSON com estado, imagem, digest upstream, limites e informações do engine. Uma tag nova no registry não atualiza a instalação ao iniciar.

## Atalho e perfil local

`install` grava o perfil e uma cópia dos comandos em `%LOCALAPPDATA%\Electivus\Workstation\base`. O arquivo `Start Workstation.lnk` desse diretório inicia o desktop e abre o navegador. Pode ser copiado para a área de trabalho; o atalho continua funcionando sem o checkout original.

Para uma instalação adicional ou um teste, escolha diretório, nome e porta próprios:

```powershell
.\scripts\Workstation.ps1 install -ProfileDirectory "$env:LOCALAPPDATA\Electivus\Workstation\teste" -Name electivus-teste -Port 13001 -Image electivus/webtop-arch-kde-base:local -MemoryMiB 2560 -Cpus 4
.\scripts\Workstation.ps1 start -ProfileDirectory "$env:LOCALAPPDATA\Electivus\Workstation\teste"
```

O limite menor serve para ensaios locais em uma VM com 4 GiB; não representa o dimensionamento final do fluxo Salesforce. Os comandos fixam o contexto Docker escolhido na instalação e recusam containers ou volumes de outra instalação com o mesmo nome. Não há comandos globais de limpeza.

O desktop usa interface em inglês, formatos brasileiros, fuso `America/Bahia` e teclado ABNT2. Preferências existentes de idioma e teclado no perfil são preservadas. O upstream usa Chromium nesta etapa; ele não representa a entrega do Chrome oficial de T02.

Para remover a confiança local posteriormente:

```powershell
.\scripts\Workstation.ps1 untrust
```

## Verificar

Execute os testes com PowerShell 7. Os comandos de uso também são compatíveis com Windows PowerShell 5.1.

```powershell
pwsh -NoProfile -File tests/Test-Lifecycle.ps1 -Image electivus/webtop-arch-kde-base:local -KeepResources
# Use exatamente o campo profile devolvido pelo teste anterior:
pwsh -NoProfile -File tests/Test-DesktopBrowser.ps1 -ProfileDirectory '<profile-do-teste>'
```

O teste de navegador exige Chrome e `playwright-cli`; abre uma sessão de automação isolada, sem usar abas pessoais. Verifica caracteres acentuados pelo transporte de teclado, fecha a aba e confirma que o mesmo processo continua trabalhando após reabri-la. Os testes produzem JSON e capturas em `.local/`. Sem `-KeepResources`, o teste de ciclo remove somente seu próprio container e volume; com a opção, mantenha os recursos para o teste de navegador e remova-os pelos nomes retornados ao terminar.

A validação local disponível usa VMM. O campo de backend do diagnóstico informa sua fonte (configuração do Docker Desktop); a evidência de execução é registrada separadamente. A primeira publicação dependerá das verificações completas e do roteiro executável de Hyper-V em T12/T13. Sucesso em VMM não declara Hyper-V validado.
