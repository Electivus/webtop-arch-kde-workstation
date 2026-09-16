# Atualizar a imagem da workstation

Uma imagem nova só é aplicada por uma atualização explícita. Na primeira inicialização, o perfil grava o identificador da imagem escolhida; as próximas inicializações e recriações mantêm essa seleção, mesmo que a tag `stable` mude. Se a imagem selecionada for removida do Docker, carregue novamente essa imagem antes de iniciar ou atualizar. O comando não avança para outra imagem por causa dessa ausência.

Perfis antigos adotam a imagem do container existente. Se esse container foi perdido antes da adoção e ainda há um volume pessoal, os comandos recusam usar uma imagem de origem desconhecida. Recupere o container original ou restaure um backup concluído da própria instalação; o backup registra a imagem correta.

Salve o trabalho antes de atualizar. O comando cria e verifica um backup, encerra a sessão, troca o container, restaura os programas extras registrados e verifica o novo ambiente. Projetos, aplicativos preparados e preferências permanecem no volume pessoal. Processos em execução não fazem parte do backup.

## Escolher e aplicar

No CMD, indique a referência da mesma variante instalada:

```bat
workstation.cmd update-image --image electivus/webtop-arch-kde-base:stable
workstation.cmd update-image --status
```

Para Salesforce, use `electivus/webtop-arch-kde-salesforce:stable` e o `--profile` dessa instalação. Também é possível escolher uma tag de versão ou uma referência com digest. O comando consulta o registry por padrão. Para uma imagem já carregada, como uma candidata construída localmente:

```bat
workstation.cmd update-image --image electivus/webtop-arch-kde-base:local --pull=false
```

`--pull=false` evita baixar a imagem; a restauração de programas extras e a preparação dos aplicativos ainda podem precisar de rede. Acrescente `--backup-directory "D:\Backups\Workstation"` para escolher o destino do backup. Essa pasta recebe a cópia por transferência pelo Docker e não precisa ser compartilhada com a VM.

Se o backup falhar, a imagem e o perfil não são trocados. O container original é retomado se estava em execução, mantendo a rede já aplicada antes da tentativa. Corrija a causa indicada antes de tentar novamente.

## Resultado e verificações

`update-image --status` consulta a última tentativa sem começar outra. O relatório contém:

| Campo | Conteúdo |
| --- | --- |
| `previous` | Referência, versão e identidade efetiva da imagem anterior. |
| `selected` | Referência, versão, `imageId` e `repositoryDigests` da imagem escolhida. |
| `backup` | Cópia concluída e caminho para recuperação. |
| `packages` | Resultado da restauração dos programas extras. |
| `applications` | Versões e origens dos aplicativos preparados. |
| `checks` | Resultado da execução dos componentes fornecidos. |
| `state`, `step`, `usable` | Resultado, etapa atual e conclusão das verificações de uso. |

`imageId` identifica a imagem no Docker. `repositoryDigests` registra as associações entre referência e digest informadas pelo Docker. Essa lista pode estar vazia ou conter um digest mesmo para uma construção local; sua presença, isoladamente, não comprova publicação em um registry. A [documentação de download do Docker](https://docs.docker.com/reference/cli/docker/image/pull/) descreve a seleção de uma referência por digest.

As verificações executam a saúde do desktop, Git, Zsh, Konsole, o acesso ao Docker e Compose e uma renderização do Chrome. A preparação verifica os aplicativos persistidos e, em Salesforce, os dois editores, CLI, runtimes e membros necessários do Extension Pack. A troca de imagem reutiliza os aplicativos compatíveis; a atualização explícita dessas ferramentas é descrita no [guia de aplicativos](application-updates.md).

`completed` com `usable: true` indica que as verificações passaram. Uma falha de programa extra pode produzir `partial` com `usable: true`, mantendo o desktop disponível e o diagnóstico em `packages`. Use `workstation.cmd packages --restore` para tentar novamente depois de corrigir a causa. O [guia de programas extras](packages.md) explica o registro de fontes e a recompilação.

Falhas de componentes fornecidos produzem `failed` com `usable: false`. Um desktop que ainda esteja acessível não significa que a atualização foi aprovada. Consulte a etapa e o diagnóstico; o backup anterior continua disponível para recuperação.

`interrupted` indica que o processo do comando terminou sem registrar um resultado, por exemplo após reiniciar o Windows. O relatório preserva a última etapa, a seleção e o backup já registrado, sem inventar um horário de conclusão. Confira o estado com `workstation.cmd status` e escolha recuperar o backup indicado ou repetir explicitamente a atualização.

## Recuperar a imagem anterior

Preserve alterações pessoais feitas depois do backup antes de recuperar. Use o caminho indicado por `backup.directory`:

```bat
workstation.cmd restore --backup "D:\Backups\Workstation\identificador-da-copia"
workstation.cmd start
workstation.cmd prepare
workstation.cmd packages --restore
```

Acrescente o mesmo `--profile` a todos os comandos quando usar uma instalação adicional. A recuperação seleciona a imagem registrada no backup e recupera seu estado pessoal. A imagem anterior precisa continuar disponível no Docker. Os programas extras são restaurados a partir do inventário e das fontes recuperados, conforme a viabilidade de cada pacote.

O histórico da última tentativa permanece acessível em `update-image --status`. O [guia de backup](backups.md) explica integridade, retenção das duas cópias concluídas mais recentes e recuperação em outra instalação.
