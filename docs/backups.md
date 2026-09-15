# Backup e recuperação

Os comandos funcionam no CMD e gravam as cópias no Windows. Antes de criar ou restaurar um backup, salve seu trabalho e encerre os serviços de projetos que escrevem no volume pessoal. O comando interrompe a workstation para obter uma cópia consistente e a deixa parada ao terminar. O backup cobre estado persistido; processos e alterações ainda não salvas não fazem parte da cópia.

```bat
set "WS_PROFILE=%LOCALAPPDATA%\Electivus\Workstation\base"
workstation.cmd backup --profile "%WS_PROFILE%"
workstation.cmd backup --profile "%WS_PROFILE%" --list
workstation.cmd start --profile "%WS_PROFILE%"
```

Por padrão, as cópias ficam em `backups` dentro do perfil. `--backup-directory "D:\Workstation Backups"` escolhe outra pasta local; use a mesma opção ao listar esse armazenamento. Cada instalação mantém suas próprias duas cópias concluídas mais recentes, mesmo quando várias instalações escolhem a mesma pasta. A listagem e a retenção verificam o SHA-256 dos arquivos. Cópias incompletas ou corrompidas aparecem separadamente e não contam para a retenção; o tempo dessa verificação depende do volume de dados armazenado.

O resultado de criação informa o identificador, a pasta, o tamanho e a imagem associada. Cada pasta contém `home.tar` e `manifest.json`. Copie a pasta inteira ao transferir um backup. Esses arquivos pertencem ao estado privado da instalação.

A criação estima o espaço necessário antes de interromper a workstation. Se não houver espaço suficiente, informa os valores estimado e disponível, preservando as cópias existentes e a sessão em execução. Durante uma operação que altera a instalação, outro comando de alteração retorna uma mensagem de operação em andamento; a listagem e o diagnóstico continuam disponíveis. Os comandos de certificado aguardam brevemente a finalização de um início pelo atalho antes de informar esse conflito. O bloqueio é liberado pelo sistema operacional quando o processo termina.

## O que é preservado

- Todo o volume pessoal Linux: projetos, preferências, aplicativos oficiais preparados, extensões, caches e demais arquivos persistidos. Um inventário de pacotes também será incluído quando existir nesse volume.
- Nomes que diferenciam maiúsculas/minúsculas, permissões, UID/GID, datas, links simbólicos e hard links. O arquivo é criado e extraído no Linux, preservando também ACLs e atributos estendidos suportados pelo filesystem.
- Perfil da instalação, configuração local de proxy/CA e arquivo de certificados de localhost. A imagem exata e os registros dos aplicativos acompanham os dados.

O conteúdo da pasta Windows de troca continua no Windows. O backup preserva o vínculo com ela, sem copiar seus arquivos. Alterações arbitrárias na camada de sistema do container ficam fora do volume pessoal; programas extras dependem do fluxo de inventário e restauração de pacotes.

## Restaurar uma cópia selecionada

Use o caminho completo retornado pela listagem/criação, na instalação da variante correspondente:

```bat
workstation.cmd restore --profile "%WS_PROFILE%" --backup "D:\Workstation Backups\IDENTIFICADOR-DA-COPIA"
workstation.cmd start --profile "%WS_PROFILE%"
```

A restauração verifica o manifesto, os campos obrigatórios do perfil, o tamanho e o SHA-256 do arquivo antes de alterar os dados atuais. A imagem registrada precisa estar disponível no Docker local. A cópia é extraída em um novo volume Linux e o perfil passa a usá-lo somente depois da extração. Isso também permite recuperar uma instalação cujo container e volume pessoal tenham sido perdidos.

Os certificados arquivados anteriormente no perfil continuam disponíveis para `untrust`. Restaurar arquivos de certificados não altera por si só a confiança do Windows; `certificate`, `trust` e `untrust` continuam sendo os comandos de administração dessa confiança.

Se outro container estiver usando o volume pessoal para escrita, o comando identifica esse container e pede que seu projeto/serviço seja parado. Nenhum serviço de outra instalação é encerrado automaticamente. Se o volume anterior ainda estiver anexado a outro container parado, a recuperação o preserva e informa seu nome no resultado.

O Docker documenta o [backup e a restauração de volumes](https://docs.docker.com/engine/storage/volumes/#back-up-restore-or-migrate-data-volumes). Nesta implementação, o transporte usa os fluxos do processo Docker, sem adicionar uma pasta ao File sharing do Docker Desktop.

Os containers temporários de transferência não gravam o arquivo binário como log Docker. As mensagens de falha continuam sendo retornadas pelo comando, e os logs de operação do desktop permanecem disponíveis.
