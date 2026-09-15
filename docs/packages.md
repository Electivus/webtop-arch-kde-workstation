# Programas extras

O inventário separa os pacotes fornecidos pela imagem dos programas extras instalados pelo usuário. Ele fica no volume pessoal, acompanha o [backup](backups.md) e conserva os registros dos extras ausentes quando o container é recriado. Instalações, atualizações e remoções feitas pelo pacman atualizam esse inventário automaticamente.

No CMD, com a workstation iniciada:

```bat
workstation.cmd packages
workstation.cmd packages --restore
```

Acrescente `--profile "C:\caminho\do\perfil"` para outra instalação. No terminal Linux, os equivalentes são `sudo workstation-packages status` e `sudo workstation-packages restore`.

O diagnóstico informa os componentes da imagem, os extras desejados, as versões efetivamente instaladas e o resultado da última restauração. `origin: official` identifica pacotes presentes nos repositórios pacman configurados; na imagem distribuída, são os repositórios oficiais Arch. `origin: foreign` identifica pacotes AUR/locais que não estão nesses repositórios. Essa classificação não autentica um repositório adicional que o usuário tenha configurado.

## Registrar uma receita AUR ou local

Mantenha a receita e seus arquivos em uma pasta dentro de `~/projects`, construa e instale o pacote como usuário do desktop e registre a origem persistente:

```sh
cd ~/projects/meu-pacote
makepkg --syncdeps --install
```

```bat
workstation.cmd packages --register nome-do-pacote --source /config/projects/meu-pacote
```

O equivalente Linux é `sudo workstation-packages register --package nome-do-pacote --source /config/projects/meu-pacote`. O pacote precisa ser um extra já instalado. O registro avalia o `PKGBUILD` como usuário `abc`; também associa os outros pacotes instalados produzidos pela mesma receita, incluindo o pacote de símbolos de depuração. Um clone com origem HTTPS/SSH em `aur.archlinux.org` recebe `source.kind: aur`; outras receitas recebem `local`.

O registro não busca uma receita desconhecida na internet. Mantenha os arquivos necessários no volume e revise suas receitas antes de registrá-las. A restauração usa a receita existente, com as verificações de fonte do makepkg; não atualiza automaticamente o Git da receita. O comando pacman usado pelo makepkg reaplica proxy e CAs do perfil depois da elevação por sudo, usando a variável [PACMAN suportada pelo makepkg](https://man.archlinux.org/man/makepkg.8.en#ENVIRONMENT_VARIABLES).

## Restaurar e interpretar o resultado

A restauração verifica os componentes fornecidos pela imagem, executa uma atualização completa `pacman -Syu`, instala os extras oficiais ausentes e recompila as receitas registradas contra o Arch atual. Ela conserva a classificação de instalação explícita ou dependência. Não copia bibliotecas nem binários arbitrários do sistema antigo. Uma receita compartilhada por vários pacotes é compilada uma vez por tentativa.

O relatório JSON inclui um resultado por extra:

| Estado | Significado |
| --- | --- |
| `restored` | Instalado ou recompilado nesta tentativa. |
| `installed` | Extra oficial já presente depois da atualização completa. |
| `missing` | O repositório ou a instalação não disponibilizou o pacote. |
| `build-failed` | A receita falhou ou não produziu o pacote esperado. |
| `manual-required` | Falta registrar ou recuperar uma origem de compilação válida. |

Um resultado geral `partial` termina com código zero e mantém o relatório em `lastRestore`; confira seus itens antes de considerar a recuperação concluída. Corrija a receita, o acesso à rede ou a disponibilidade dos pacotes indicados e execute novamente `packages --restore`. O desktop e os aplicativos preparados continuam disponíveis quando apenas um extra falha. Falha na atualização Arch ou ausência de componente fornecido pela imagem encerra o comando com erro e exige reparar ou recuperar a instalação.

As receitas AUR podem exigir dependências que não existem nos repositórios oficiais; o fluxo não resolve automaticamente um conjunto arbitrário de dependências AUR. A restauração também não garante compatibilidade de toda receita antiga. O teste incluído demonstra reconstrução de um programa C local, seus símbolos, alteração real da fonte e nova tentativa depois de uma falha de compilação.

## Backup e limites do inventário

Antes de uma manutenção, crie um backup. Ele preserva os registros, as receitas que estão no volume e os aplicativos preparados. Depois de recuperar uma cópia e iniciar a workstation, execute `packages --restore` para reconstruir os extras na imagem recuperada. O [guia de recuperação](backups.md) descreve a interrupção e a seleção da cópia.

Uma remoção explícita pelo pacman também retira o pacote do inventário desejado. Mudanças diretas de metadados, como `pacman -D`, não executam o hook de transação; use `sudo workstation-packages capture` depois delas. Arquivos instalados manualmente fora do volume e sem um pacote não entram no inventário.

O diagnóstico dos componentes da imagem verifica a presença dos pacotes, não a integridade de cada arquivo nem o funcionamento de cada aplicação. Os testes de desktop e de aplicativos verificam esses comportamentos separadamente. Chrome, VS Codes e CLI/extensões Salesforce preparados no volume são preservados pelo fluxo de aplicativos e backup, não tratados como pacotes pacman extras.
