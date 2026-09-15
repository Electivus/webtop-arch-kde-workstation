# T06 - conectividade corporativa

Ticket: [#7](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/7). Ponto inicial da implementação: `e41139ba27c2a0c0748a802aeb8cac82db998841`. O preflight do corpo obtido do GitHub passou com o checkpoint Planning `7575b9991bfbd00b514f6f75c0f555b2e9bd7236`, DEC-008, DEC-021 e DEC-034. O merge T04/T05 `a46fd42beb03aa7a5f9cf7886349851e7d986048` foi incorporado sem alterar o trabalho desta etapa.

## Ensaios de desenvolvimento

As verificações abaixo foram executadas pelos comandos CMD/EXE e por clientes reais dentro da workstation VMM. `tests/network_fixture.py` cria duas autoridades descartáveis e servidores HTTPS, um confiável e outro não configurado, além de um proxy CONNECT real em uma rede Docker exclusiva do teste. Não há credenciais de empresa ou de organização Salesforce nesses ensaios.

- O primeiro teste falhou porque `install` não reconhecia `--network-config`. O controlador passou a importar o JSON e suas CAs para o perfil e a transferi-los com `docker cp` antes do início, sem bind de uma pasta Windows adicional.
- O primeiro certificado de teste omitia `keyUsage` na CA. Python 3.14 o rejeitou com código 92, enquanto Git o aceitou. A extensão foi corrigida no gerador da fixture; a validação TLS do produto permaneceu ativa.
- A prova inicial passou em 107,801 s: preparação e Git conectaram pelo proxy com a CA configurada; a cadeia não confiável foi rejeitada; mais de cinquenta raízes do sistema permaneceram disponíveis; remover a configuração fez a CA anterior voltar a ser rejeitada.
- O preparo manual inicialmente ignorava o proxy salvo, e o teste falhou em 57,046 s. Após usar a configuração local também nesse caminho, a prova de falha e retomada passou em 138,694 s.
- Um Zsh novo conectava Git diretamente. O proxy registrou cinco conexões antes e depois da operação, reproduzindo a falha em 96,346 s. O ambiente de novos terminais e o lançador Chrome foram integrados à configuração. A prova ampliada passou em 121,295 s, com passagem efetiva pelo proxy e rejeição da CA inválida também no Chrome.
- Um proxy de teste devolveu usuário e senha descartáveis na mensagem HTTP 407. O relatório de preparação os reproduziu, e o teste falhou em 26,402 s. Após sanitizar erros, status e mensagens de subprocessos, a prova passou em 72,648 s, incluindo a retomada do preparo depois de remover o proxy.

ShellCheck e shfmt passaram no inicializador, no lançador Chrome e nos três lançadores Salesforce alterados. A sintaxe Python passou nos scripts de rede, preparação e testes. O build dos comandos passou em gofmt, go vet e compilação para Windows e Linux. O workflow foi validado com o parser YAML. A revisão independente e o fechamento Planning pertencem ao encerramento de T06.

## Editores e Salesforce

O cenário Salesforce preparou os aplicativos e o Extension Pack por um proxy real. Verificou nos registros do proxy conexões a Google, Microsoft, npm e Marketplace. Em seguida, o primeiro teste do extension host de Stable aceitou a CA configurada e rejeitou a inválida, mas passou diretamente pela rede: zero conexões ao destino da fixture no proxy. O cenário falhou em 324,105 s e reteve somente seus recursos próprios para diagnóstico.

Os lançadores Stable, Insiders e `sf` passaram a carregar a configuração local. Na mesma instalação descartável preparada, os testes públicos do editor confirmaram TLS positivo/negativo e passagem pelo proxy nos dois canais. O runtime observado de Stable foi Electron 42.10.0, Chromium 148.0.7778.280 e Node 24.18.1. O token fictício da prova Salesforce foi ajustado ao formato exigido pelo CLI; a CLI então conectou por TLS/proxy e recebeu a recusa de autenticação intencional do serviço descartável. Isso verifica o transporte, sem autorizar uma organização Salesforce. O [recibo direcionado](t06-apps-targeted.json) registra os resultados.

Esses lançadores foram copiados para a instalação de teste durante o diagnóstico; o recibo direcionado não substitui a execução em imagens reconstruídas. Após a prova, container, sidecar, volume e rede próprios foram removidos, com a propriedade da workstation e do volume conferida pelos labels da instalação.

A prova da base foi ampliada para importar a mesma CA que já existia no NSS sob um nome escolhido pelo usuário. Passou em 104,902 s: após `network --clear` e reinício, essa entrada anterior permaneceu intacta, enquanto a preparação e Git voltaram a rejeitar a CA removida do sistema.

## Separação dos artefatos

A inspeção de processos novos das duas imagens, sem executar seus inicializadores, encontrou 121 raízes públicas em cada uma, nenhum proxy por ambiente, nenhuma configuração da instalação, nenhum segredo/anchor de build e nenhum anchor corporativo de runtime. Os digests e resultados estão em [t06-image-privacy.json](t06-image-privacy.json). A leitura dos Dockerfiles confirmou que a CA temporária do BuildKit é removida e o trust é regenerado no mesmo `RUN`; os `COPY` selecionam apenas fontes genéricas do repositório. `.dockerignore` exclui `.local`, que contém os perfis e insumos dos ensaios. Não houve publicação dessas imagens.

## Bateria das imagens reconstruídas

As imagens locais finais são base `sha256:bf3720bfc27cdc42a9af6798137571e2d1c53e76678953f5a9619bb8e3d676c3` e Salesforce `sha256:34c0198a3b4164bd6bd844f2137da067c88240055b55d6ddbdcd5b2af5d7c512`. Os argumentos de versão/revisão dos builds locais foram reaproveitados de T02/T03 para preservar o cache; esses labels não representam uma release de T06. Os IDs acima identificam os artefatos efetivamente exercitados a partir da árvore de trabalho.

| Arquivo | Resultado | Tempo |
| --- | --- | --- |
| `test_commands.py` | 3 passaram | 120,548 s |
| `test_preparation.py` | 3 passaram | 163,545 s |
| `test_projects.py` | 2 passaram | 38,612 s |
| `test_docker_projects.py` | 1 passou | 59,540 s |
| `test_salesforce.py` | 2 passaram | 619,367 s |
| `test_network.py` | 2 passaram | 115,716 s |
| `test_network_apps.py` | 1 passou na repetição | 261,144 s |

O primeiro segmento parou no preflight do teste de projetos: a pasta do checkout T06 não estava compartilhada no Docker Desktop. Não abriu modal. A execução prosseguiu a partir de projetos, usando `WORKSTATION_TEST_EXCHANGE_DIRECTORY` para reutilizar a pasta T04 já autorizada. Nenhuma alteração adicional de File sharing foi necessária.

A primeira execução final de `test_network_apps.py` falhou em 228,749 s durante o download do Extension Pack do Insiders: o cliente informou desconexão antes de estabelecer TLS com o Marketplace. Chrome, Stable, Insiders, Salesforce CLI e as extensões de Stable já haviam sido preparados pelo proxy. A causa da desconexão não foi estabelecida. O cenário foi repetido isoladamente, sem alteração no código ou nas imagens, e passou em 261,144 s. O [recibo da imagem reconstruída](t06-apps-final.json) confirma a preparação pelos repositórios, o TLS positivo/negativo no extension host dos dois editores e o transporte da CLI Salesforce pelo proxy. Os recursos descartáveis foram removidos pelo teste.

Ao final, os 14 testes passaram, com as duas retomadas descritas acima. Os ensaios locais não representam execução no notebook corporativo Hyper-V nem autenticação em uma organização Salesforce.
