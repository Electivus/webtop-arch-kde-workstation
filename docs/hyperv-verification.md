# Verificação no notebook com Hyper-V

Este roteiro usa CMD, Docker Desktop já instalado e os comandos distribuídos com a imagem. O script Python que acompanha o roteiro roda **dentro do container**; o Windows não precisa de Python, Git, WSL2 ou PowerShell.

A execução real no notebook de destino permanece pendente. Uma execução deste roteiro em WSL2 verifica o roteiro nesse backend e não comprova Hyper-V.

## Antes de executar

1. Confirme no Docker Desktop do destino que os containers são Linux e o backend é Hyper-V. A virtualização precisa estar previamente habilitada pela administração do notebook. Este roteiro não altera o backend.
2. Comece pela proposta de VM com 8 GiB e seis CPUs lógicas, reservando recursos para Windows e outros containers. O perfil do ensaio usa 6 GiB e quatro CPUs para a workstation. Confira o relatório de dimensionamento da entrega antes de ajustar esses valores.
3. Reserve uma pasta local para resultados, backups e troca de arquivos. Em Hyper-V, compartilhe sua pasta pai em **Docker Desktop → Settings → Resources → File sharing**, antes do ensaio. O diretório de resultados escolhido deve ser novo; o roteiro não sobrescreve evidências anteriores.
4. Tenha espaço para a imagem, os aplicativos baixados e suas cópias de segurança. A verificação de backup informa os bytes estimados e disponíveis e recusa uma cópia sem espaço suficiente.
5. Copie `setup.cmd`, `verify-target.cmd` e `verify-target.py` para a mesma pasta. Use a versão fixa ou o digest da entrega que pretende verificar. Se a imagem ainda não estiver carregada, o Docker precisará baixá-la. Os aplicativos oficiais são obtidos durante o primeiro preparo.
6. Se a rede exigir proxy ou certificados, prepare o JSON e as CAs conforme [configuração de rede](network.md). Os arquivos permanecem no notebook.

Confirme a disponibilidade do Docker no CMD:

```bat
docker version
docker info --format "{{.OSType}} {{.Architecture}} {{.KernelVersion}}"
```

O resultado deve identificar Linux amd64. Uma falha de acesso ao daemon deve ser resolvida no Docker Desktop antes de continuar. A porta local 14513 precisa estar livre. O controlador verifica também contexto local, capacidade da VM e acesso à pasta de troca.

## Ensaio automático com perfil separado

Substitua `VERSAO_DA_ENTREGA` pela versão registrada na publicação. Não use uma tag inventada como evidência de uma entrega.

```bat
set "WS_IMAGE=electivus/webtop-arch-kde-salesforce:VERSAO_DA_ENTREGA"
set "WS_REPORT=%USERPROFILE%\WorkstationChecks\salesforce-01"
verify-target.cmd "%WS_IMAGE%" "%WS_REPORT%"
```

Com configuração corporativa opcional:

```bat
verify-target.cmd "%WS_IMAGE%" "%WS_REPORT%" "C:\WorkstationNetwork\network-input.json"
```

O roteiro instala um perfil de teste próprio, prepara os aplicativos, verifica a rede, consulta versões e extensões, cria um projeto Salesforce e constrói um serviço Compose que escreve no projeto Linux. Ele confere a troca de arquivos com o Windows, salva um marcador em backup, altera esse marcador e verifica sua recuperação. Ao terminar com sucesso, a workstation de teste fica parada.

`result.txt` identifica sucesso ou a etapa que falhou. Os arquivos JSON registram imagem, backend observado, limites, preparação, aplicações, projetos, backup e recuperação. O perfil e os relatórios ficam disponíveis para diagnóstico. Uma falha não transforma etapas posteriores em aprovadas. Guarde a pasta local: os backups e a configuração de rede podem conter dados privados e não devem ser publicados como parte da imagem.

## Desktop, atalho e teclado

Use o perfil criado pelo roteiro:

```bat
set "WS_PROFILE=%WS_REPORT%\profile"
set "WS_CMD=%WS_REPORT%\tools\workstation.cmd"
call "%WS_CMD%" start --profile "%WS_PROFILE%"
call "%WS_CMD%" trust --profile "%WS_PROFILE%"
start "" "%WS_PROFILE%\Start Workstation.lnk"
```

Confira a impressão digital apresentada pelo comando e a confirmação de certificado do Windows. O acesso é HTTPS local, sem senha adicional da workstation.

No desktop, registre em `visual-checks.txt`, junto dos relatórios, o resultado e a data de cada verificação:

- Uma tela da workstation em 1920 × 1080, interface inglesa e formatos brasileiros.
- Abra `~/projects/destination-salesforce` com Insiders e confirme que Stable também abre separadamente. Abra Chrome e um terminal Zsh.
- Digite com o teclado físico ABNT2: `ação ç áéíóú ãõ ê ü @ / ? |`. Isso complementa os testes automatizados de teclado; não presuma que o layout físico do destino foi verificado pelo CI.
- Faça essa verificação digitando pausadamente. A composição de acentos durante digitação rápida pode falhar no desktop original; essa limitação foi aceita para esta entrega, sem alteração do teclado do produto. O teste automatizado de composição usa intervalo de 250 ms entre teclas e exige todos os caracteres na ordem correta.
- Abra um arquivo Apex e um componente Lightning e confira os serviços das extensões durante a edição.
- Inicie uma tarefa observável no terminal, feche somente a aba do navegador, abra o atalho novamente e confira que a tarefa continua.
- Registre lentidão, interrupções da imagem, resolução efetiva e carga concorrente do Windows. Não declare aceleração gráfica sem evidência do renderizador/encoder utilizado.

Para observar recursos no CMD enquanto usa o desktop:

```bat
call "%WS_CMD%" status --profile "%WS_PROFILE%"
docker stats --no-stream
```

Registre também a memória e CPU do Windows no Gerenciador de Tarefas. O primeiro preparo inclui downloads; compare as partidas seguintes separadamente. Os percentuais de CPU do Docker podem ultrapassar 100%, pois somam o uso dos processadores.

## Atualizações e recuperação

Salve o trabalho e encerre serviços Compose que estejam escrevendo nos projetos. Os comandos fazem backup antes de uma alteração e mantêm as duas cópias concluídas mais recentes.

```bat
call "%WS_CMD%" update-apps --profile "%WS_PROFILE%"
call "%WS_CMD%" update-apps --profile "%WS_PROFILE%" --status
call "%WS_CMD%" backup --profile "%WS_PROFILE%" --list
```

Anote as versões efetivas. Se os fornecedores ainda oferecerem as mesmas versões, registre que o comando terminou sem uma troca de versão; isso não demonstra uma atualização de versão distinta.

Para testar outra versão de imagem, selecione uma entrega existente da **mesma variante** e substitua `PROXIMA_VERSAO`. O comando pode interromper a sessão e executa o backup antes de trocar a imagem:

```bat
call "%WS_CMD%" update-image --profile "%WS_PROFILE%" --image electivus/webtop-arch-kde-salesforce:PROXIMA_VERSAO
call "%WS_CMD%" update-image --profile "%WS_PROFILE%" --status
call "%WS_CMD%" start --profile "%WS_PROFILE%"
```

Se a candidata já foi importada como arquivo OCI, acrescente `--pull=false`. Usar novamente o mesmo digest é uma verificação de seleção/idempotência, não evidência de troca de imagem. Confira o projeto, os aplicativos e o inventário após a atualização. Para recuperar uma cópia identificada pela listagem:

```bat
call "%WS_CMD%" restore --profile "%WS_PROFILE%" --backup "CAMINHO_COMPLETO_DA_COPIA"
call "%WS_CMD%" start --profile "%WS_PROFILE%"
```

Finalize o uso e retire a confiança do certificado de teste quando não precisar mais dela:

```bat
call "%WS_CMD%" stop --profile "%WS_PROFILE%"
call "%WS_CMD%" untrust --profile "%WS_PROFILE%"
```

## Resultado identificável

Conserve a versão/digest de `image.json`, os resultados dos comandos, a confirmação do backend no Docker Desktop, o hardware e as anotações visuais. O campo de backend do controlador identifica a configuração encontrada; ele não substitui a confirmação de que o ensaio foi executado no notebook Hyper-V.

Classifique cada verificação como aprovada, falhou ou pendente. A primeira publicação admite a execução real em Hyper-V pendente, conforme o escopo aprovado; essa pendência só é encerrada com os resultados do destino. Os procedimentos de [backup](backups.md), [atualização da imagem](image-updates.md) e [atualização dos aplicativos](application-updates.md) detalham diagnóstico e recuperação.
