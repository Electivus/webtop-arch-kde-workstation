# Projetos Linux, troca de arquivos e Compose

## Armazenamento e pasta Windows

O diretório `~/projects` (`/config/projects`) pertence ao volume Linux informado por `workstation.cmd status` em `homeVolume`. O menu **Workstation Projects** abre essa pasta. Use-a para os projetos ativos, conservando nomes sensíveis a maiúsculas, permissões de execução e links simbólicos.

A pasta de troca é opcional. Crie uma pasta Windows e compartilhe-a em **Docker Desktop > Settings > Resources > File sharing**, aplicando a configuração, antes de usá-la na instalação. Hyper-V e o VMM local exigem esse compartilhamento. Uma solicitação do Docker pode aguardar confirmação em outra janela; o controlador identifica a ausência nas configurações conhecidas e faz uma prova de leitura/gravação pelo backend antes de iniciar.

Para uma nova instalação com troca habilitada, execute no CMD:

```bat
mkdir "%USERPROFILE%\WorkstationExchange"
workstation.cmd install --image electivus/webtop-arch-kde-base:local --exchange "%USERPROFILE%\WorkstationExchange"
workstation.cmd start
```

No desktop, abra `~/WindowsExchange`; no terminal, use `/exchange`. Copie arquivos para essa pasta ou altere seus arquivos para vê-los nos dois sistemas. O caminho escolhido fica no perfil e em `status.storage.exchange`. Se a pasta for removida ou ficar inacessível, restaure o acesso antes de iniciar. Para instalar outra workstation, escolha também `--profile`, `--name` e `--port` próprios, como nos exemplos do README.

## Engine e caminhos

Os clientes Docker e Compose da workstation usam o Docker Desktop do notebook. O controlador monta o socket do engine e o início concede acesso ao usuário do desktop pelo grupo existente do socket, preservando suas permissões. Os comandos podem administrar recursos desse engine. Serviços Compose continuam executando quando a workstation é parada, até você encerrá-los pelo Compose.

`workstation-docker-check` verifica o acesso e mostra a identificação do engine, a versão do Compose e o volume pessoal. Com um diretório como argumento, verifica também se o projeto existe no armazenamento Linux e informa seu subdiretório no volume.

O contexto de build é enviado pelo cliente a partir do projeto. Para os arquivos usados pelo serviço, o exemplo monta um subdiretório do volume pessoal:

```text
/config/projects/compose-demo
  -> volume pessoal, subpath projects/compose-demo
  -> /workspace no servico Compose
```

Um bind como `.:/workspace` é resolvido pelo daemon, que tem seu próprio filesystem. Para projetos mantidos no volume da workstation, use `type: volume`, o nome em `WORKSTATION_HOME_VOLUME` e `volume.subpath`, conforme o exemplo entregue e a [documentação Compose](https://docs.docker.com/reference/compose-file/services/#volumes). O subdiretório precisa existir antes da montagem.

## Exemplo completo

Execute no terminal Linux:

```sh
cp -r /etc/electivus/examples/compose-demo ~/projects/compose-demo
cd ~/projects/compose-demo
export COMPOSE_PROJECT_NAME="${WORKSTATION_HOME_VOLUME}-demo"
export WORKSTATION_PROJECT_SUBPATH=compose-demo
workstation-docker-check "$PWD"
docker compose up --detach --build --wait
cat result.txt
docker compose down --rmi all
```

O build copia `write-result.sh` do contexto local. O serviço lê `input.txt` e grava `result.txt` no projeto persistido. Altere a entrada e repita `up` após `down` para conferir o resultado. Depois de recriar a workstation, entre novamente na pasta, defina as duas variáveis e repita o fluxo. Cada instalação usa seu nome de projeto Compose; `down --rmi all` remove os serviços e a imagem desse exemplo, mantendo o volume externo e seus arquivos.

Se o diagnóstico informar um caminho inexistente, crie ou corrija a pasta e confira `WORKSTATION_PROJECT_SUBPATH` no `compose.yaml`. Se informar engine indisponível, confira Docker Desktop, `DOCKER_HOST` e se a workstation foi iniciada pelo controlador. O socket utiliza Linux containers; não é necessário iniciar outro daemon dentro da workstation.

## Ensaio repetível

`tests/test_projects.py` exercita conteúdo, nomes, modo executável, links, troca nos dois sentidos e recriação pelos comandos entregues. No Windows, o teste também verifica a mensagem para uma pasta não compartilhada. Para o ensaio local, compartilhe somente `<checkout>\.local\exchange` no Docker Desktop; as pastas de dados descartáveis são criadas abaixo desse caminho.

`tests/test_docker_projects.py` compara a identidade do engine com o host, modifica um script do contexto antes do build, sobe o serviço, verifica sua escrita no projeto e repete após recriar a workstation. Também verifica diagnósticos para caminho inexistente e engine inacessível. Os testes limpam somente seus containers, imagens de exemplo e volumes; recibos ficam em `.local/`.
