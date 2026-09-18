# Publicação e versões

As imagens públicas são [base](https://hub.docker.com/r/electivus/webtop-arch-kde-base)
e [Salesforce](https://hub.docker.com/r/electivus/webtop-arch-kde-salesforce).
Cada entrega usa a mesma versão fixa nos dois repositórios; `stable` identifica
a entrega aprovada. A Salesforce já inclui a base: o consumidor inicia somente
o container da variante escolhida.

Uma tag fixa nunca deve ser sobrescrita. Para reprodução exata, prefira a referência
por digest registrada em `candidate.json`. Arch é uma distribuição rolling release:
reconstruir o mesmo código posteriormente pode produzir outros pacotes e digests.
Por isso a promoção importa e publica os arquivos OCI testados, sem reconstruí-los.
Uma versão corrigida recebe outra tag.

As versões públicas começam por um número, por exemplo `1.0.0` ou a data gerada
pelo CI. A regra `^[0-9].*$` de tags imutáveis está ativada nos dois repositórios
Docker Hub; `stable` permanece mutável. Essa proteção no servidor complementa
a verificação do publicador e bloqueia sobrescritas concorrentes. A configuração
segue a [documentação de tags imutáveis](https://docs.docker.com/docker-hub/repos/manage/hub-images/immutable-tags/).

## Consumir uma entrega

Baixe o ZIP Windows na [entrega publicada](https://github.com/Electivus/webtop-arch-kde-workstation/releases/latest)
e extraia pelo Explorador de Arquivos. Siga `START-HERE.md` no CMD. O ZIP inclui
os comandos autossuficientes, suas licenças, digests e o roteiro Hyper-V; não exige
checkout Git, PowerShell, Python ou WSL2 no destino.

`SHA256SUMS` permite conferir o ZIP antes de extrair. No CMD, substitua o nome pela
versão baixada e compare o resultado com a linha correspondente no arquivo:

```bat
certutil -hashfile workstation-VERSAO-windows.zip SHA256
```

O guia usa a variante Salesforce fixada por digest. Para a base, use o digest da
entrada `base` do mesmo `candidate.json`. Instalações existentes não mudam ao
iniciar; a [atualização da imagem](image-updates.md) é explícita e faz backup.
Chrome e os dois VS Codes são baixados dos fornecedores no primeiro preparo e
ficam no volume pessoal, fora da imagem pública.

A primeira validação local é em Docker Desktop WSL2. A execução no notebook
Hyper-V continua pendente até os resultados do [roteiro de destino](hyperv-verification.md).
Imagens disponíveis no Hub e CI verde não comprovam o backend de destino.

## Autenticação da automação

O workflow `Publish` usa uma conexão OIDC da organização Docker `electivus`, com
permissão de push apenas nos dois repositórios. O subject exato deve ser:

```text
repo:Electivus@228091504/webtop-arch-kde-workstation@1368946436:ref:refs/heads/main
```

Os IDs são os identificadores imutáveis do owner e repositório no GitHub. Forks,
PRs e outras branches não recebem essa relação de confiança. A configuração usa
credenciais temporárias, sem token permanente em um secret do GitHub. Não conceda
exclusão de imagens, administração da organização, Build Cloud ou acesso a outros
repositórios nessa conexão.

Depois de ativar a conexão, registre seu ID na variável de repositório
`DOCKERHUB_OIDC_CONNECTIONID`. A política de Actions deve permitir
`docker/login-action@*` além das duas Actions Docker de preparação existentes;
a exigência de SHA completo permanece. O workflow fixa a versão compatível com
OIDC, `v4.5.0`, pelo commit. Sem o ID configurado, a publicação falha antes do envio.

As instruções oficiais de [OIDC no Docker Hub](https://docs.docker.com/security/authentication/oidc-connections/)
e [claims e regras](https://docs.docker.com/security/authentication/oidc-connections/rulesets-claims/)
descrevem os pré-requisitos da conta e o formato da relação de confiança.

## Executar e acompanhar

`Checks` roda toda segunda-feira às 10:00 UTC (07:00 em `America/Bahia`) e também
manualmente ou após integração na `main`. Uma execução aprovada na `main` aciona
`Publish`. PRs geram candidatas e testes, sem publicar. O publicador confirma pelo
GitHub o workflow, repositório, branch, commit, tentativa e sucesso; confere também
todo o contrato de aceitação e os hashes dos arquivos. Uma aprovação antiga não
substitui uma execução mais recente já aprovada.

Para gerar uma versão fixa escolhida:

```sh
gh workflow run checks.yml --repo Electivus/webtop-arch-kde-workstation --ref main -f version=1.0.0
```

Não repita esse comando para retomar uma publicação: ele reconstrói uma candidata.
Sem `version`, o CI gera uma versão coordenada com data, run ID e tentativa.
O fluxo mantém testes, autenticação e publicação como etapas distintas. As permissões
de escrita são declaradas somente no job que cria a entrega.

O publicador verifica as duas tags fixas antes do envio. Se alguma já aponta para
outro digest, interrompe sem sobrescrever. Envia e verifica primeiro as duas tags
fixas; depois promove `stable` e confere os digests no registry. Não existe transação
atômica entre os dois repositórios: uma interrupção pode deixar um `stable` avançado
e o outro anterior. `publication.json` fica marcado como `partially-published`,
com `complete: false`, até completar a promoção. Use versões/digests coordenados
enquanto a retomada estiver pendente.

Para retomar, use o ID do mesmo `Checks` aprovado, dentro da retenção de sete dias:

```sh
gh workflow run publish.yml --repo Electivus/webtop-arch-kde-workstation --ref main -f run_id=ID_DO_CHECKS
```

Os digests já presentes são reaproveitados. A entrega GitHub começa como rascunho;
só se torna pública depois que todos os arquivos foram enviados e baixados novamente
para verificar seus hashes. O pacote é determinístico para a mesma candidata, o que
permite retomar um upload parcial sem sobrescrever arquivos. Conflitos de conteúdo
são interrompidos para inspeção. Os relatórios de cada tentativa ficam nos artefatos
`publication-RUN-TENTATIVA`, por 30 dias; o relatório anterior não é substituído.

Se uma candidata mais recente já foi aprovada, use-a. Se os artefatos expiraram,
gere outra versão fixa, nunca reconstrua a versão anterior para sobrescrevê-la.
O workflow de falha deliberada (`prove_test_failure=true`) não pode aprovar nem
promover uma candidata. Os testes de publicação exercitam falha de aceitação,
contrato incompleto, origem de PR, conflito de versão, ordem de aprovação,
interrupção de `stable` e retomada dos arquivos de entrega.

## Inspeção e confidencialidade

Somente artefatos de construção e comandos genéricos são distribuídos. Perfis,
projetos, backups, certificados locais e configurações de proxy pertencem à instalação.
A primeira entrega precisa registrar a inspeção das camadas e do estado inicial,
o pull público por digest e o início pelo CMD. Não anexe logs corporativos ou volumes
pessoais aos releases. As [licenças](licensing.md) dos componentes continuam preservadas.
