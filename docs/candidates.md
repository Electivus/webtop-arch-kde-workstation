# Candidatas da workstation

O workflow **Checks** constrói a base e a variante Salesforce a partir do mesmo commit, com uma versão coordenada. A execução semanal ocorre às segundas-feiras, às 10:00 UTC. Em **Actions → Checks → Run workflow**, a execução manual aceita uma versão fixa; deixar o campo vazio gera uma identificação com data, número da execução e tentativa.

Cada execução semanal, manual ou originada por uma alteração em `main` conserva sua própria construção e validação. Uma nova alteração cancela somente os testes anteriores do mesmo pull request; não cancela uma candidata solicitada manualmente ou pelo calendário.

`candidate.json` identifica o commit, a arquitetura `linux/amd64`, os digests das imagens, a base usada pelo Salesforce e os checksums dos arquivos de transporte e comandos. O estado `built` informa que a construção terminou. A aprovação fica em `validation/validation.json`: ela exige `state: passed`, `approved: true`, os mesmos digests e o contrato completo de aceitação concluído. A conclusão do job também precisa ser bem-sucedida.

O contrato comum está em [tests/acceptance.json](../tests/acceptance.json). Ele inclui comandos, aplicativos, projetos, Docker/Compose, rede, certificados, backup, pacotes e atualizações, com os casos específicos de Salesforce. Cada verificação conserva seu log, duração e resultado em `validation/checks/`. Uma falha interrompe a aprovação e identifica as verificações que ainda não rodaram.

A [verificação de referência](verification/t11-candidates.md) registra uma execução completa aprovada, a rejeição de uma execução com falha e a importação dos mesmos artefatos no Windows com Docker Desktop WSL2.

## Levar a candidata ao Windows

Na execução identificada do GitHub Actions, baixe os três artefatos: `candidate-results-RUN-TENTATIVA`, `webtop-arch-kde-base-RUN-TENTATIVA` e `webtop-arch-kde-salesforce-RUN-TENTATIVA`. Extraia os ZIPs na mesma pasta. O repositório público permite consultar o código e os resultados; o download de artefatos pelo GitHub exige uma conta autenticada. A retenção é de sete dias. Nenhum desses arquivos deve conter perfis pessoais, credenciais ou configurações corporativas reais.

Confira a aprovação e anote a versão de `candidate.json`. O fluxo abaixo usa CMD e Docker Desktop. Substitua `VERSAO_DO_MANIFESTO` pela versão registrada:

```bat
cd /d "%USERPROFILE%\Downloads\Workstation-candidate"
set "CANDIDATE_VERSION=VERSAO_DO_MANIFESTO"
certutil -hashfile webtop-arch-kde-base.oci.tar SHA256
certutil -hashfile webtop-arch-kde-salesforce.oci.tar SHA256
certutil -hashfile commands.tar SHA256
```

Compare os resultados com `archiveSha256` de cada imagem e `commandsArchiveSha256` no manifesto. Depois importe os arquivos e confira os identificadores resultantes:

```bat
docker load --input webtop-arch-kde-base.oci.tar
docker load --input webtop-arch-kde-salesforce.oci.tar
docker image inspect --format "{{.Id}}" electivus/webtop-arch-kde-base:%CANDIDATE_VERSION%
docker image inspect --format "{{.Id}}" electivus/webtop-arch-kde-salesforce:%CANDIDATE_VERSION%
tar -xf commands.tar
```

Os identificadores precisam coincidir com `digest` no manifesto. A importação preserva o índice OCI; o Docker deve usar seu armazenamento de imagens baseado em containerd. A [documentação do Docker](https://docs.docker.com/build/ci/github-actions/multi-platform/) descreve essa capacidade e sua configuração no GitHub Actions. Para um engine que não preserve o índice, registre a incompatibilidade antes de usar o resultado como aceitação daquela candidata.

Para iniciar um perfil Salesforce separado para o ensaio:

```bat
set "WORKSTATION_PROFILE=%LOCALAPPDATA%\Electivus\Workstation-candidate"
commands\workstation.cmd install --profile "%WORKSTATION_PROFILE%" --name electivus-candidate --image electivus/webtop-arch-kde-salesforce:%CANDIDATE_VERSION%
commands\workstation.cmd start --profile "%WORKSTATION_PROFILE%"
commands\workstation.cmd prepare --profile "%WORKSTATION_PROFILE%"
commands\workstation.cmd trust --profile "%WORKSTATION_PROFILE%"
start "" "%WORKSTATION_PROFILE%\Start Workstation.lnk"
```

O perfil usa inicialmente o limite de 6 GiB e quatro CPUs da workstation. A medição no notebook define o dimensionamento final. Para ensaiar a base, selecione a referência `electivus/webtop-arch-kde-base` e outro nome/pasta de perfil. Se os dois perfis forem usados juntos, escolha portas distintas com `--port`.

Proxy e certificados opcionais seguem [a configuração de rede](network.md), antes da preparação dos aplicativos. Os projetos e aplicativos preparados ficam no volume pessoal. Os arquivos OCI e o pacote de comandos continuam sendo os artefatos originais; esses arquivos são os que devem acompanhar qualquer relato de validação por seus checksums e digests.

## Reproduzir a validação e provar a rejeição

Para manutenção, use um checkout limpo no commit exato de `revision` em `candidate.json`, inclusive quando a construção usou `--source`. Execute o script desse checkout. Python executa o mesmo contrato usado pelo CI:

```text
python scripts/candidate.py load --directory CAMINHO_DA_CANDIDATA
python scripts/candidate.py test --directory CAMINHO_DA_CANDIDATA --output .local/validacao-local
```

O comando de importação confere as duas imagens e o pacote de comandos antes de carregá-los. O teste usa os executáveis distribuídos com aquela candidata e registra um novo resultado na pasta escolhida. Uma validação local deve conservar o resultado original do CI e identificar o hardware/backend em que foi executada.

O teste recusa uma revisão diferente ou alterações locais no checkout, antes de importar as imagens, e confere novamente o código antes de aprovar. O resultado registra `validatorRevision`. Mantenha os artefatos e resultados fora do checkout ou dentro de sua pasta ignorada `.local`, para não criar arquivos de fonte não identificados.

O acionamento manual oferece `prove_test_failure` para demonstrar o bloqueio. Nesse ensaio, os testes recebem um caminho de controlador indisponível e falham pelo seu fluxo real. Os arquivos da candidata permanecem intactos, o relatório identifica `failureProof: true` e a aprovação continua falsa. Esse modo nunca produz uma entrega aprovada. A execução normal e a execução negativa devem ser relacionadas pelos números dos runs, commits e digests registrados.

As imagens são exportadas no [formato OCI](https://docs.docker.com/build/exporters/oci-docker/). Os artefatos do GitHub incluem arquivos de imagem, comandos genéricos e resultados de teste; o estado pessoal criado durante a aceitação permanece fora deles. O [upload de artefatos](https://github.com/actions/upload-artifact) permite baixar esses arquivos após a execução, respeitando acesso e retenção.
