# T02/T03 - aplicativos oficiais e desenvolvimento Salesforce

Candidata de 2026-09-14, validada localmente. Escopo: [T02](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3) e [T03](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/4). Ponto inicial da implementação: `959f3bf3bc02f073e345c3ff351c2d2af6d9766b`; a árvore recebeu depois o merge T01 `1896d8cb2eeea9fd6d7ff96ed0b3cdc1e0952ccb`, sem mudança de conteúdo nessa integração.

## Obtenção e persistência

As fontes ficam em `/etc/electivus/applications.d`. O preparo usa os repositórios APT oficiais como fontes autenticadas de arquivos, mantendo Arch/pacman como sistema. Verifica a assinatura de `Release`, o SHA-256 do índice, o tamanho e o SHA-256 do pacote e a versão do executável extraído. O índice Microsoft contém versões históricas: a seleção compara versões em vez de escolher a primeira entrada.

| Aplicativo | Versão observada | Origem e verificação |
| --- | --- | --- |
| Chrome | 153.0.8010.36-1 | Google APT; chave `EB4C1BFD4F042F6DDDCCEC917721F63BD38B4796`; SHA-256 `9bb44e33031c2f2857cf36b4343051a12f93058e4b781e3c76313df87f6c8d32`. |
| VS Code Stable | 1.137.0-1788902055 | Microsoft APT; chave `BC528686B50D79E339D3721CEB3E94ADBE1229CF`; SHA-256 `fd4dff72c44598d3acb885b448256f5d82cf53f59538d97fc7d3c8d8d9d574d3`. |
| VS Code Insiders | 1.138.0-1789320271 | Mesmo repositório Microsoft; SHA-256 `9b3c53bb97d02c7a74ac1a2a19ba3d8bde0fd64f9f9df01481f9c2dd0d926df6`. |
| Salesforce CLI | 2.150.6 | Pacote oficial npm; integridade SHA-512 selecionada no catálogo, verificada antes da instalação; dependências e integridades registradas no package-lock. |
| Salesforce Apex / LWC | 67.17.2 | Salesforce Extension Pack, instalado pelo CLI oficial de cada VS Code a partir do Marketplace. |
| Node / Java | Node 24.21.0 / OpenJDK 21 | Pacotes Arch `nodejs-lts-krypton` e `jdk21-openjdk`. |

Fontes primárias: [Google Linux repositories](https://www.google.com/linuxrepositories/), [VS Code no Linux](https://code.visualstudio.com/docs/setup/linux), [repositórios e chaves Microsoft](https://learn.microsoft.com/en-us/linux/packages), [Java para Salesforce](https://developer.salesforce.com/docs/platform/sfvscode-extensions/guide/java-setup.html) e [ciclo de versões Node](https://nodejs.org/en/about/previous-releases).

Os executáveis e manifestos ficam em `~/.local/share/electivus/apps`, com versões separadas e troca atômica de `current`. Downloads completos/parciais ficam em `~/.cache/electivus/downloads`; estado e exclusão mútua ficam em `~/.local/state/electivus`. O preparo existente é reutilizado após recriação. Atualização explícita e backup são entregas dos tickets posteriores.

## Plataforma e dimensionamento do ensaio

Notebook Windows Dell Latitude 5450, Core Ultra 7 165U e 32 GB. Docker Desktop 4.90.0, engine 29.7.2, kernel `7.0.12-linuxkit`, linux/amd64. O backend local continuou VMM: `UseLibkrun=true` e encaminhamentos novos `com.docker.backend.exe.sailorforward` foram observados após a alteração de recursos.

Os primeiros ensaios usaram a VM anterior de 4 GiB e limites de 2,5 e 3,25 GiB para Salesforce. O renderizador foi encerrado; o primeiro ensaio registrou `OOMKilled=true`. Isso motivou aplicar o ponto inicial já definido em DEC-023: VM com 8 GiB e 6 CPUs. Após reiniciar, o engine reportou 8.000 MiB e 6 CPUs. Os containers SearxNG e Valkey foram restabelecidos com os mesmos IDs e ficaram saudáveis. A configuração anterior foi copiada para `%LOCALAPPDATA%\Electivus\workstation\docker-resources-20260914T212036Z` antes da mudança.

Os testes funcionais Salesforce usam 6.144 MiB e até 4 CPUs, limitadas à capacidade do engine; os testes menores da base usam 2.560 MiB e 2 CPUs. A execução final local usou 4 CPUs para Salesforce. A medição completa de carga, os artefatos de CI instalados localmente e o roteiro Hyper-V continuam em T12. Esta etapa não comprova execução no notebook Hyper-V.

## Resultados registrados

- Regressão T01: três testes passaram em 93,276 s, incluindo CMD, atalho, confiança reversível e preservação de recursos alheios.
- Base T02: três testes passaram em 119,517 s. Chrome renderizou uma página com sandbox ativo, sobreviveu à recriação e retomou uma instalação impedida por permissão sem baixar novamente o pacote verificado.
- Zsh: sessão interativa exibiu sugestão do histórico e aceitou seu sufixo com a seta; comandos válidos e inválidos receberam cores distintas. O alias Git funcionou, execução não interativa ficou limpa e a personalização de `.zshrc` persistiu.
- Ensaio Salesforce com volume novo: passou em 368,700 s, incluindo geração de projeto com `sf`, recriação e serviços nas duas instalações de editor. Verificou diagnóstico `Missing ';' at '}'`, sua remoção após correção, conclusão do método `System.debug` e do atributo `label` de `lightning-button`. Não foram usadas credenciais de organização. Recibos: [Stable](t03-stable-services.json) e [Insiders](t03-insiders-services.json).
- A primeira versão do teste esperava um erro semântico, mas a extensão 67.17.2 declara `salesforcedx-vscode-apex.enable-semantic-errors=false` por padrão. O teste foi corrigido para sintaxe e conclusões disponíveis nessa configuração, mantendo os padrões do fornecedor.
- ShellCheck 0.11.0 e shfmt 3.14.1 (`-i 4`) passaram nos scripts Linux. Foram executados nas ferramentas Arch da máquina de desenvolvimento; os comandos entregues ao notebook continuam CMD/EXE. O build verifica gofmt e go vet para Linux e Windows.
- Interrupção real de Insiders: o container foi encerrado com 10.485.760 dos 237.424.394 bytes no arquivo parcial. A retomada concluiu o preparo e manteve exatamente os manifestos anteriores de Chrome e Stable. O ensaio passou em `tests/test_salesforce.py`.
- A associação de `.code-workspace` foi verificada com o backend KDE 6 de `xdg-mime`, que consulta a base compartilhada de tipos de arquivo. O `docker exec` não herda as variáveis da sessão Plasma; sem elas, o fallback `file` reconhece apenas o conteúdo JSON.
- Regressão do navegador na base atual: digitação com acentos, fechamento/reabertura da aba e continuidade do mesmo processo passaram (`pid=1333`, contador de `1789423497` para `1789423499`).
- Os testes funcionais passaram por arquivo/caso após as correções de validação descritas acima. A revisão de padrões e especificação e a bateria de CI acompanham o PR desta candidata.

O ensaio de serviços usa somente a [API pública de testes de extensões do VS Code](https://code.visualstudio.com/api/working-with-extensions/testing-extension), carregada no editor entregue. Os arquivos de instrumentação e o projeto de exemplo ficam em `tests/`; não são acrescentados ao perfil do produto.

A abertura padrão foi exercitada com `kioclient exec /config/projects/sample.code-workspace` e produziu a janela `Welcome - sample (Workspace) - Visual Studio Code - Insiders`. A abertura explícita pelo lançador Stable, `gtk-launch code /config/projects/sample`, produziu `sample - Visual Studio Code`. O ensaio usou o perfil descartável já preparado, fechou cada editor antes do seguinte e removeu sua confiança HTTPS temporária. Recibo: [abertura dos editores](t03-desktop-launch.json); capturas: [Insiders padrão](t03-default-project.png) e [Stable explícito](t03-explicit-stable.png). As telas preservam o fluxo inicial do fornecedor; nenhuma conta foi conectada. A confiança do workspace permanece uma escolha do usuário; o teste de serviços habilita apenas seu projeto de exemplo controlado.

## Desktop e proteção

A abertura do Chrome foi exercitada pelo terminal do desktop transmitido. O ensaio espera o título real da página na janela X11 antes de capturar o resultado, evitando registrar somente a tela inicial de carregamento. Capturas: [terminal Git/Chrome/Zsh](t02-terminal.png) e [página renderizada no Chrome](t02-chrome.png). Em um primeiro ensaio também apareceu o assistente KDE Wallet para armazenamento pessoal de credenciais; essa etapa é descrita no README. O teste de navegação não salva senhas.

O perfil Docker padrão impedia os namespaces do sandbox. O perfil incorporado ao lançador parte do Moby e acrescenta `clone`, `setns` e `unshare`, conforme a receita publicada pelo Playwright. O teste headless renderizou HTML e o teste gráfico encontrou processos de renderização sem `--no-sandbox`. O container mantém seccomp e suas capacidades padrão. Veja [origem e licença do perfil](../../cmd/workstation/THIRD-PARTY.md).

O build usa `pacman -Syu` com um limite global de 20 minutos e `--disable-download-timeout`: a rede de teste demorava mais de 10 segundos para começar a entregar alguns pacotes. TLS e assinaturas permanecem ativos. A opção é documentada para gateways/proxies no [manual pacman](https://man.archlinux.org/man/pacman.8).

A inspeção da imagem Salesforce construída confirmou ausência da âncora CA usada somente durante o build, de raízes Zscaler, dos binários proprietários preparados no volume e de arquivos de pacotes no cache pacman. O segredo CA foi removido na mesma camada que o utilizou. Nenhuma imagem desta etapa foi publicada no Docker Hub.

## Artefatos locais

Os builds da árvore de trabalho usaram o rótulo de revisão `1896d8cb2eeea9fd6d7ff96ed0b3cdc1e0952ccb`; os digests abaixo identificam as imagens com as alterações T02/T03 ainda não commitadas nesse momento. Não são recibos de publicação ou de CI.

| Artefato | Identificação |
| --- | --- |
| Base `2026.09.14-t02` | `sha256:805de94e071f177f55967eed4842d0b927e1f394c2626b32bbbb3d96109bb060` |
| Salesforce `2026.09.14-t03` | `sha256:37cb15f74997fe56e1552bfa28539ca6c3114db3143cd137e0333a5b17ca0605` |
| Controlador Windows | SHA-256 `38e7dce0fbbf229ff29fe0412cee834940ec80189b721b85730531f058ecf62c` |

A inspeção de camadas confirmou que Salesforce contém as 25 camadas da base correspondente, seguidas por cinco camadas próprias. Os avisos de licença Moby e Go acompanham os comandos exportados e o bundle Windows dentro da imagem.

O ensaio completo de serviços usou `sha256:2564364fef912a4d3b85455a6337bab8fae57e99f0feb936025974c4242abb64`. A imagem final altera somente as classes dos lançadores para os valores efetivamente observados em X11 (`code` e `code-insiders`); os arquivos passaram em `desktop-file-validate`. A interrupção e as capturas adicionais dos editores usaram `sha256:30a6d43e7131ebb783594f686206489d66e4afcfdde2aa01efb46d0506b27209`, anterior também à inclusão dos avisos de licença. O código de preparo e os aplicativos preparados são os mesmos nesses ensaios.

## Validação final após a revisão

A [revisão independente](t02-t03-review.md) foi encerrada sobre `ea1927c5034c6e9bd7a261ec2c1f8f6dd56d2ab6`, após a implementação `d3fc05b4b2d6030ea693d8ac5866409fcacb785f`. As imagens foram reconstruídas com essas correções e a bateria completa terminou com oito testes aprovados:

| Suíte | Resultado | Tempo |
| --- | --- | --- |
| `tests/test_commands.py` | 3 testes; CMD, atalho, confiança HTTPS e ciclo de vida | 108,982 s |
| `tests/test_preparation.py` | 3 testes; Chrome, retomada, Zsh e detecção automática de manifesto incompatível | 145,439 s |
| `tests/test_salesforce.py` | 2 testes; persistência, serviços Apex/LWC em ambos os canais, restauração de Visualforce e retomada após interrupção | 585,775 s |

| Imagem reconstruída | Identificação |
| --- | --- |
| Base `2026.09.14-t02` | `sha256:624ad9f4fd4365026c4aa21ee78a7f94ded66f23c3745cfd74c6a40f635afd94` |
| Salesforce `2026.09.14-t03` | `sha256:6e255e46f320867a0ed57b93b2c413b1229fd163892d92cfe72c65151cb0e048` |

Esses builds locais conservaram o rótulo de revisão `1896d8cb2eeea9fd6d7ff96ed0b3cdc1e0952ccb`; os digests identificam o conteúdo efetivamente testado. As capturas e os recibos anteriores mantêm a proveniência descrita acima. A validação final não representa publicação no Docker Hub nem aceitação Hyper-V.
