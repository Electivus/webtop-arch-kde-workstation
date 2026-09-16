# Retomada local em WSL2

Em 2026-09-16, o usuário substituiu o Docker VMM beta por Docker Desktop com WSL2 devido a problemas na engine anterior. DEC-037 e DEC-038 registram a mudança no checkpoint final `9c9f2c44531269dae4d785e4f8b7d197e56f0082`. A especificação e os 13 tickets foram sincronizados e validados. O destino continua sendo Windows com Docker via Hyper-V, operação por CMD e sem dependência de WSL2 ou PowerShell.

O daemon observado é Docker Desktop 29.8.0, kernel `6.18.35.2-microsoft-standard-WSL2`, com 14 CPUs lógicas e 15.718 MiB de memória disponíveis. Isso identifica o ambiente de execução, sem equivaler à aceitação Hyper-V nem ao perfil final de dimensionamento.

O armazenamento VMM antigo foi apagado após autorização explícita do usuário. A remoção liberou 93,39 GiB e preservou o disco WSL2 e os três serviços já ativos. Os repositórios e as evidências históricas foram preservados. As imagens de desenvolvimento foram reconstruídas; os antigos IDs não representam os artefatos desta execução.

## Incompatibilidade encontrada na reconstrução

O build original terminou com sucesso, mas o início pelo comando entregue falhou: o desktop não ficou saudável em quatro minutos. `nginx -t` isolou a mesma falha em menos de um segundo: nginx 1.30.5 recusava `nginx-mod-fancyindex` 0.5.2-1, compilado pelo upstream para nginx 1.30.4. O pacote externo não foi recompilado pela atualização completa do Arch.

A imagem agora usa a listagem nativa `autoindex` no endpoint de arquivos e remove o módulo externo e sua configuração. O visual dessa listagem passa a ser o padrão do nginx; o desktop Selkies e os caminhos de download permanecem. Essa escolha permite atualizar o pacote nginx sem depender da compatibilidade binária daquele módulo externo.

Pelo controlador Windows e seu ponto de entrada CMD, uma instalação descartável iniciou saudável. A listagem exibiu um arquivo com espaço e acento no nome; o download retornou o conteúdo esperado com `Content-Disposition: attachment` e `X-Content-Type-Options: nosniff`. `nginx -t` passou na configuração inicializada. A instalação e o volume de teste foram removidos ao final. Recibo: `.local/wsl-resume/native-file-listing-result.json`.

## Artefatos e verificações

| Artefato | Identidade local |
| --- | --- |
| Base | `sha256:2cf558e66f9778d69890d3be7db1ad72ad290feeea053739079d0522e873eae3` |
| Salesforce | `sha256:785fce737856b48c41bdb15b6b834ddab10f982a5df0262c95293a882a4eacaf` |
| Controlador Windows, exportado e dentro de ambas as imagens | SHA-256 `3ce8843aaace37a60a8b79f94dabb50ca8463c0b9bb54c03ee97578783edf91f` |

Os builds executaram gofmt, go vet Linux/Windows e as duas compilações. Os arquivos de construção e de identidade estão em `.local/wsl-resume/rebuild-wsl2-nginx/`. São imagens de desenvolvimento, com versão `t09-t10-wsl2` e revisão marcada `dirty`; não são uma entrega pública.

A reprodução inicialmente bloqueada por nginx foi preservada em `.local/resume-linux-corrections-nginx-red/`. Com as imagens corrigidas, o controlador Linux recuperou o perfil legado em 29,396 s e reconheceu a interrupção real dos dois comandos de atualização em 41,241 s. Recibo: `.local/resume-linux-corrections/result.json`. O acompanhamento delimitado Spec aprovou as duas correções no checkpoint `0e1df370678024f54e9d8a94cf46f4bbc92636b8`; a regressão Windows completa permanece pendente neste registro.

## Regressão Windows e proteção de recursos alheios

Os oito cenários de atualização de imagem passaram pelo controlador Windows em 942,914 s, incluindo envio ao registro local, seleção por tag, recuperação por digest e restauração dos programas extras. O registro permaneceu dentro do limite de memória. Recibo: `.local/resume-windows-regression/result.json` na cópia Windows usada pelos testes.

Na etapa seguinte, o ciclo normal e o pacote CMD com atalho e confiança TLS passaram, mas o cenário de recursos alheios encontrou um diagnóstico incorreto. A execução GitHub `35121001036`, job `104878454332`, reproduziu exatamente a falha: o volume de outra instalação era recusado como um perfil antigo sem identidade de imagem. Nenhum dado alheio foi modificado. A seleção agora verifica a propriedade do volume antes de orientar uma recuperação do perfil legado. O teste público existente verifica tanto a mensagem correta quanto a preservação do volume; nenhuma asserção foi removida.

A reconstrução e os testes dessa correção ficam em `.local/wsl-resume/rebuild-ownership-fix/` e `.local/resume-ownership-windows-regression/`. A execução mais ampla e o fechamento Planning ainda dependem dos resultados finais dessa rodada.

A verificação de isolamento passou no Linux em 2,328 s. A recuperação de perfil legado passou novamente no Windows em 51,657 s, preservando a exigência de identidade original antes de reutilizar o volume. Na rodada corrigida, os três cenários de comandos passaram no Windows em 96,291 s, incluindo atalho e confiança TLS. As duas imagens contêm o mesmo controlador Windows exportado, SHA-256 `fba6ce1b23bcb1efe7ddc37a135536760dc6bcdb7099a01e906e9a1d5c407ea2`:

| Artefato corrigido | Identidade local |
| --- | --- |
| Base | `sha256:b0ec5818f2e777e492a4a947960406803c01ee0f64a653713e4cb0e1d590dccf` |
| Salesforce | `sha256:f0aff2bc171cceff6ca0bf3c6a3ab4878671221e68687955fba148c41986c743` |

## Preparação pública e aviso dos editores no WSL2

A execução GitHub `35123540585`, job `104886937585`, aprovou o ciclo de comandos e encontrou uma fixture antiga: o teste de retomada do Chrome criava manualmente um volume sem identidade da imagem. O novo bloqueio de perfil legado recusou esse estado. A reprodução local falhou em 1,578 s. A fixture agora cria o ambiente pelo comando público, com downloads temporariamente bloqueados, e prepara a pasta sem permissão de escrita como o usuário do desktop. A falha de instalação, a retomada e a preservação do download verificado continuam exigidas. O caso passou em 44,338 s; os dois ajustes intermediários de propriedade da pasta foram falhas de fixture e estão registrados separadamente. Não houve alteração no bloqueio do produto.

Dos 13 cenários de backup Windows, 12 passaram. A preparação Salesforce ficou esperando a confirmação interativa que o lançador oficial do VS Code exibe quando detecta `Microsoft` no kernel. Uma chamada independente do mesmo executável retornou 1 com a pergunta; com `DONT_PROMPT_WSL_INSTALL=1`, retornou 0 e a versão `1.138.0`. O processo interativo identificado dentro do container descartável foi encerrado para liberar a execução e registrar a falha; a suíte conservou o diagnóstico real. Evidências: `.local/wsl-resume/vscode-wsl-prompt.json` e `.local/wsl-resume/windows-ownership-regression/`.

A imagem Salesforce declara essa variável, aplicável aos dois canais oficiais e à preparação automática. A imagem reconstruída é `sha256:956ff64450cad9575d3f635cff343b992942ab15f1eb48ef6c8337001547182d` ; a base e o controlador não mudaram. A variável na imagem e a identidade do controlador foram verificadas. A rodada `.local/resume-wsl-editor-windows-regression/` repete o backup Salesforce e continua pelas suítes de atualização de aplicativos e troca da imagem Salesforce; sua conclusão ainda é necessária.

Na imagem corrigida, a preparação automática concluiu ambos os editores sem intervenção: Stable e Insiders têm recibos de instalação e versões executadas em `.local/wsl-resume/wsl-editors-prepared.json`. A preparação avançou para a CLI Salesforce. Isso valida a variável no fluxo real do desktop WSL2, além da reprodução isolada.
