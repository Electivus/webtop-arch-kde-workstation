# T08: inventário e restauração de programas extras

Ticket: [#9](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/9). Ponto fixo para revisão: merge T07 `e8e2ae6d51c47c21f76096f175ae8b32237a09e5`. O preflight do corpo completo obtido do GitHub passou no checkpoint final `7575b9991bfbd00b514f6f75c0f555b2e9bd7236`, com DEC-019, DEC-022, DEC-029 e DEC-032.

## Comportamento demonstrado

Os testes de `tests/test_packages.py` entram pelo CMD e pelo executável distribuído, usam containers e volumes descartáveis e executam pacman e makepkg reais. O pacote oficial é `figlet`. O pacote local compila `tests/fixtures/extra-package/example.c` por meio de um `PKGBUILD`, produzindo o programa e seu pacote de depuração. As receitas, o inventário e os aplicativos preparados ficam no volume pessoal.

| Ensaio | Evidência observada |
| --- | --- |
| Instalação oficial, recriação, restauração e remoção | O hook registra `figlet`; a recriação conserva o registro ausente; a restauração instala e executa o programa; a remoção explícita retira seu registro. |
| Reconstrução local | A fonte e seu checksum são alterados, mantendo o arquivo binário antigo disponível. A restauração compila a nova fonte e o executável imprime o texto modificado; programa e símbolos compartilham a origem. |
| Falha e nova tentativa | Uma diretiva C `#error` com checksum válido provoca falha de compilação real. Ambos os pacotes aparecem como `build-failed`, o desktop continua saudável e o Chrome preparado ainda executa. Reparar a fonte e repetir conclui a restauração. |
| Intervenção necessária | Um registro persistente de pacote oficial retirado do catálogo produz erro real de busca do pacman; uma receita não registrada produz `manual-required`. |
| Componente obrigatório | Remover deliberadamente o Git da imagem descartável produz `image-component-failure` e erro de restauração antes da atualização Arch. |
| Backup | Um backup real recupera os registros exatos e a fonte original após remoção dos pacotes e alteração do arquivo. A restauração subsequente recompila os extras e executa os programas. |
| Escritas concorrentes | Duas avaliações reais de receitas, coordenadas por uma barreira da fixture, registram fontes diferentes ao mesmo tempo. Os quatro registros de programa/depuração preservam suas origens. |
| Dependências e rede | Pacotes instalados como dependências conservam essa classificação; o download de uma dependência pelo sudo do makepkg chega ao proxy do perfil. |

As receitas são avaliadas como `abc`. O lock do inventário cobre a leitura e a gravação, sem permanecer adquirido durante compilação ou transações pacman que executam o próprio hook. As gravações usam substituição atômica. O baseline de cada variante é registrado depois de instalar seus componentes; o hook herdado não captura estado pessoal durante a construção Salesforce.

## Falhas reproduzidas e correções

O primeiro ensaio de reconstrução restaurou o programa, mas deixou o pacote de depuração sem origem. A associação dos resultados reais da mesma receita e a compilação compartilhada corrigiram esse resultado; a prova passou em 45,850 s. O cenário completo de falha de compilação, continuidade do Chrome e nova tentativa passou em 73,893 s antes da extensão de classificação de dependências.

O ensaio concorrente inicialmente perdeu uma das origens mesmo com os dois processos concluindo com sucesso: falha em 24,560 s. A releitura do inventário sob lock durante cada atualização corrigiu a perda; passou em 25,562 s. Uma tentativa anterior da fixture falhou antes de chegar à concorrência por IDs de build iguais no pacote de depuração; corrigir a fonte da segunda fixture permitiu reproduzir o defeito real.

A reinstalação mudava `reason: dependency` para `explicit`: falha em 44,798 s. Preservar `--asdeps` na instalação corrigiu o comportamento; o cenário completo passou em 78,818 s.

O sudo descartava o proxy recebido pelo makepkg. Uma dependência ausente foi baixada diretamente apesar do proxy recusador configurado, reproduzindo a falha em 37,227 s. O caminho `PACMAN` agora reaplica a rede depois da elevação. A mesma prova passou em 40,060 s: o proxy local registrou a tentativa para o mirror citado pelo pacman e sua recusa HTTP 502 impediu o download. O ensaio não substitui Docker, pacman ou makepkg por adaptadores falsos.

Os cenários de intervenção e componente obrigatório passaram em 55,486 s; a integração de inventário/fontes com backup passou em 79,731 s. As execuções finais agrupadas são registradas abaixo para distinguir esses ensaios focados do estado final.

## Artefatos e validação final

Builds locais da árvore T08: base `sha256:d14aec63996ff2d0d43d899b854d0a357464a8966684f1d6c99d59c3a8fb808a` e Salesforce `sha256:dc153d561be8989a661572b57da5ea7763708ae79f28572753d71e04a088e15e`. Os rótulos de revisão desses builds de desenvolvimento não são recibos de release: a base reutiliza rótulos T02 para cache; Salesforce aponta ao merge T07. O CI constrói suas imagens com o SHA da PR.

O export dos comandos passou em gofmt, go vet e builds Windows/Linux. A sintaxe Python, ShellCheck, shfmt dos novos scripts e `git diff --check` passaram. A configuração de workflow foi analisada por yq. A bateria final está em execução; a aceitação Linux/CI e a revisão independente ainda serão registradas.

Antes do checkpoint de revisão, passaram os oito casos de pacotes em 367,297 s, comandos Windows (3, 89,083 s), preparo (3, 138,116 s), projetos/troca (2, 35,837 s) e Compose (1, 52,468 s); os tempos incluem o runner. O teste de falha local ganhou depois uma verificação de renderização real do Chrome, cuja execução adicional ainda está pendente. Os catorze blocos Bash do workflow também passaram em `bash -n`.

A primeira passagem Salesforce falhou em DNS durante o reparo de extensões (`ENOTFOUND marketplace.visualstudio.com`) e a resolução inicial do Chrome (`Name or service not known`), em 340,048 s. As sondas posteriores fizeram quarenta consultas em cada ambiente Windows, base e Salesforce, sem falhas, e não estabeleceram a causa original. Nenhuma configuração de DNS ou TLS foi alterada. A repetição já aprovou o cenário principal de editores/serviços/recriação e continua no cenário de interrupção, antes de rede e backup. A primeira saída foi preservada como evidência extraída do processo; o runner de desenvolvimento foi ajustado para não sobrescrever logs em tentativas futuras.

O primeiro build Salesforce local falhou em TLS porque `--secret env=SSL_CERT_FILE` entregava o caminho como conteúdo. A repetição com `--secret id=corporate_ca,src=.local/t08-corporate-ca.crt` passou. O arquivo privado contém apenas a raiz corporativa já validada e fica fora do Git; o Dockerfile remove o material de build na mesma camada. Não houve mudança de confiança do Windows nem novo compartilhamento de arquivos nesses ensaios.

## Limites

A viabilidade demonstrada abrange pacotes oficiais disponíveis e receitas AUR/locais conhecidas, com recompilação contra a base atual. Não há promessa de preservar binários arbitrários nem de resolver automaticamente dependências AUR. O guia [Programas extras](../packages.md) documenta registro, resultados parciais, nova tentativa e recuperação do backup. A presença dos pacotes fornecidos pela imagem é verificada separadamente do funcionamento dos aplicativos, coberto pela bateria de entrega.

Os testes locais usam Docker VMM. A validação real no Hyper-V de destino continua pertencendo à entrega T12 e não é inferida desses resultados.
