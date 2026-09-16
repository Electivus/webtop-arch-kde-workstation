# Atualizar aplicativos

O comando de atualização consulta as fontes dos fornecedores e atualiza os aplicativos no volume pessoal. A imagem da workstation permanece a mesma. Salve o trabalho antes de executar: o backup interrompe a sessão e a workstation é iniciada novamente para atualizar as ferramentas.

No CMD, com a workstation iniciada:

```bat
workstation.cmd update-apps
workstation.cmd update-apps --status
```

Acrescente `--profile "C:\caminho\do\perfil"` para selecionar outra instalação. Para guardar a cópia em outra pasta, use `--backup-directory "D:\Backups\Workstation"`. A transferência do backup usa o Docker sem exigir compartilhamento dessa pasta com a VM.

O backup precisa concluir e passar pela verificação de integridade antes de modificar aplicativos. Se essa etapa falhar, a atualização é interrompida; a instalação em uso é preservada e o mesmo container é retomado caso tenha sido parado. Corrija a causa indicada antes de tentar novamente.

## Ferramentas e versões

Na variante base, o comando atualiza o Google Chrome oficial. Na variante Salesforce, também atualiza VS Code Stable, VS Code Insiders, Salesforce CLI e extensões dos dois editores. O Insiders continua sendo o editor padrão.

Chrome e VS Codes usam os índices assinados dos repositórios dos fornecedores. A CLI usa a versão estável corrente do pacote oficial `@salesforce/cli`, verificando a origem, a integridade do arquivo e a versão executada. A atualização de extensões usa a seleção de versões compatíveis do próprio editor e verifica os membros necessários do Salesforce Extension Pack.

Iniciar a workstation ou executar `prepare` reutiliza os aplicativos já instalados. Uma nova consulta para atualização depende de `update-apps`. O relatório registra as versões efetivas e a origem em `applications.apps`; uma ferramenta que já esteja atualizada pode conservar a mesma versão.

## Resultado e recuperação

O relatório da tentativa inclui:

| Campo | Conteúdo |
| --- | --- |
| `state` | `running`, `completed`, `failed` ou `interrupted`. |
| `step` | Etapa atual ou etapa em que ocorreu a falha. |
| `previous` | Identidade da workstation antes da manutenção, incluindo a imagem. |
| `backup` | Cópia concluída, com `id` e `directory` para recuperação. |
| `applications` | Versões, origens e diagnóstico do trabalho nos aplicativos. |

`update-apps --status` consulta a última tentativa sem começar outra. Depois de uma falha de download ou instalação, confira esse relatório. Ferramentas atualizadas antes da falha podem continuar na nova versão; o backup permite recuperar o conjunto anterior e o estado pessoal.

`interrupted` indica que o processo do comando terminou sem registrar um resultado, por exemplo após reiniciar o Windows. A consulta preserva a última etapa e o backup já registrado. Confira a workstation com `workstation.cmd status`; depois escolha recuperar essa cópia ou iniciar a workstation e repetir explicitamente `update-apps`.

Para recuperar a cópia indicada em `backup.directory`:

```bat
workstation.cmd restore --backup "D:\Backups\Workstation\identificador-da-copia"
workstation.cmd start
workstation.cmd prepare --status
```

Use o mesmo `--profile` em todos os comandos quando a instalação não for a padrão. A recuperação restaura também projetos e preferências daquele backup; alterações feitas depois da cópia precisam ser preservadas antes. O [guia de backup](backups.md) descreve a verificação, a retenção das duas cópias concluídas mais recentes e a recuperação.

Após recuperar, `prepare --status` informa o conjunto recuperado. O histórico da última tentativa de atualização continua disponível em `update-apps --status`.
