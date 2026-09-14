# T04/T05 - projetos, troca Windows e Docker

Escopo: [T04 / #5](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/5) e [T05 / #6](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/6). Ponto inicial: `fdb0f82848fef50c77e25c36d64daba60f47c93a`. As correções de CI de T02/T03 até `2cd45e23382864627e651fccc46d605f501234d5` foram integradas antes da bateria final, sem alterar as decisões aplicáveis DEC-013 e DEC-015.

## Comportamento verificado

O controlador oferece `install --exchange`, registra um caminho absoluto no perfil, verifica diretório e compartilhamento nas configurações conhecidas do Docker Desktop e testa leitura/gravação pelo backend. O início cria `/config/projects` apenas quando ausente e disponibiliza a pasta pelo menu do desktop. A troca aparece em `/exchange` e `~/WindowsExchange`.

O primeiro ensaio de persistência passou em 38,232 s: preservou os arquivos distintos `Readme` e `readme`, conteúdo com acentos, modo `0751`, proprietário e link simbólico executável após recriar o container. A pasta Windows tinha espaços, vírgula e acentos no caminho. Arquivos foram criados e alterados nos dois sentidos.

Um pedido de compartilhamento do Docker ficou aguardando confirmação e terminou por tempo limite. A configuração local foi copiada antes da alteração; somente `<checkout>\.local\exchange` foi acrescentado à lista. O Docker Desktop foi reiniciado e os containers SearxNG e Valkey foram restabelecidos com os mesmos IDs, saudáveis. Backup: `%LOCALAPPDATA%\Electivus\workstation\docker-sharing-20260914T200601`. Para reverter, remova apenas essa entrada em File sharing e aplique a mudança; os arquivos da pasta permanecem.

O novo teste de pasta não compartilhada inicialmente mostrou que `install` aceitava a configuração e adiava o problema. Após a correção, passou em 0,997 s: o comando informa File sharing e o caminho antes de criar o perfil ou solicitar uma montagem. Backends desconhecidos continuam sujeitos à prova real de leitura/gravação.

## Projeto Compose

O usuário do desktop acessa o socket do engine pelo grupo existente; o início não muda permissões nem proprietário do socket. A base já fornecia Docker 29.8.0 e Compose 5.5.1. O primeiro build do exemplo identificou a ausência de Buildx e recusou `COPY --chmod` no builder clássico; foi incluído o pacote oficial Arch `docker-buildx` 0.37.1-1. O exemplo usa Alpine 3.24 fixado pelo digest `sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b`.

O cenário completo passou em 57,449 s. A identidade `415af08d-7380-406d-a170-e065f212104f` retornada pelo cliente no desktop correspondeu ao engine Docker Desktop 29.7.2 do notebook. Um script foi alterado no projeto antes do build; o serviço produziu `local-build: primeira ação` e, após recriar a workstation e mudar a entrada, `local-build: segunda ação`.

A montagem usa o volume pessoal externo e `volume.subpath=projects/compose example`. O contexto de build parte do cliente, e o daemon monta o subdiretório Linux existente em `/workspace`. O teste verificou a montagem e os arquivos resultantes; também exercitou os diagnósticos de projeto inexistente e engine indisponível. A limpeza selecionou somente os recursos do exemplo por nome próprio e label Compose. O [guia de uso](../projects.md) reproduz esse fluxo no terminal e documenta a separação entre projeto Linux e pasta de troca.

## Artefatos e limites

| Imagem local | Digest |
| --- | --- |
| `electivus/webtop-arch-kde-base:t04` | `sha256:02c9caefbedc42657beba178501b24b29701720e2b5ca0eba30ebfce34cd3d1d` |
| `electivus/webtop-arch-kde-salesforce:t05` | `sha256:e5af4463b9e91e7dc738839a7baa2a1fb45853214228ad05f113ebc9cb1f89cf` |

Os builds locais preservaram os rótulos de versão T02/T03 e revisão `1896d8cb2eeea9fd6d7ff96ed0b3cdc1e0952ccb` para reutilizar as camadas anteriores. Os digests identificam as imagens da árvore de trabalho com as mudanças desta etapa; não são recibos de publicação. O ensaio usa o backend VMM e os recursos descritos na [validação T02/T03](t02-t03-apps.md). A aceitação Hyper-V permanece em T12.

ShellCheck e shfmt passaram no inicializador e no script do exemplo; o lançador passou em `desktop-file-validate`. O build verificou gofmt, go vet e compilação nativa para Windows e Linux. A bateria completa terminou com onze testes aprovados nas imagens acima:

| Suíte | Testes | Tempo |
| --- | --- | --- |
| `test_commands.py` | 3 | 117,234 s |
| `test_preparation.py` | 3 | 148,927 s |
| `test_projects.py` | 2 | 38,642 s |
| `test_docker_projects.py` | 1 | 52,387 s |
| `test_salesforce.py` | 2 | 745,022 s |

Os recibos de [arquivos](t04-files.json) e [Compose](t05-compose.json) pertencem a essa execução completa. Os serviços Apex/LWC, a recuperação do Extension Pack e a retomada de download também passaram na variante Salesforce reconstruída. O merge T02/T03 `addf745ab22129e1b175ad5f86a2461921f23770`, cuja árvore é idêntica ao head aprovado `2cd45e2`, foi integrado durante a validação sem alterar os arquivos exercitados.
