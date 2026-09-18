# Revisão para abertura do repositório

Revisão realizada em 2026-09-18 para tornar público
`Electivus/webtop-arch-kde-workstation`, conforme DEC-039. O responsável pelo
projeto escolheu MIT para o conteúdo próprio da Electivus. Esta revisão trata
da exposição do repositório; não é uma aprovação de entrega das imagens nem
uma auditoria completa de vulnerabilidades dos componentes instalados.

## Escopo e resultados

- Espelho remoto anterior à abertura: `main` em
  `144eed60570c33a6d746c49d74f14faf61fd5756`, dez branches e oito referências de
  PRs; 78 commits alcançáveis e 476 blobs históricos únicos. Gitleaks do pacote
  Arch `8.30.1-1`, com regras padrão e achados redigidos, não encontrou segredos
  nos diffs históricos nem no conteúdo integral desses blobs. As exceções por
  comentários `gitleaks:allow` foram desconsideradas.
- GitHub: corpos de 14 issues e oito PRs, oito comentários de issues, 20
  comentários de revisão e 14 reviews, incluindo conteúdo encerrado. Nenhum
  segredo encontrado no conteúdo destinado à publicação. Não havia releases,
  wiki, discussions, environments, variáveis ou secrets de Actions cadastrados
  diretamente no repositório. Isso não é uma afirmação sobre secrets de outras
  organizações ou serviços.
- Actions: todos os 38 runs existentes e suas 39 tentativas tiveram os logs
  baixados. Os dez artefatos `candidate-results` disponíveis foram inspecionados
  como arquivos ZIP, incluindo arquivos aninhados. A varredura não encontrou
  segredos. A busca adicional nos 242 arquivos de texto, totalizando cerca de
  31,9 MB, não encontrou os identificadores pessoais/corporativos conhecidos
  nem marcadores de chaves privadas.
- As cinco capturas de tela versionadas mostram sessões e projetos de teste,
  sem contas autenticadas, dados corporativos ou conteúdo pessoal identificado.
- O caminho pessoal do checkout foi substituído por `%USERPROFILE%` na
  documentação atual. O histórico não foi reescrito: o caminho antigo, a
  autoria Git e as evidências técnicas de hardware continuam consultáveis nos
  commits anteriores. Nenhuma credencial real foi identificada que exigisse
  revogação ou remoção do histórico.

## Imagens e arquivos de distribuição

O inventário remoto também identificou 18 artefatos OCI das imagens. Esses
arquivos grandes não foram todos baixados e reanalisados nesta revisão. Foram
revistos os Dockerfiles, o contexto de build permitido, os manifestos e logs
das construções, além das verificações de privacidade já registradas em
[T06](t06-review.md) e [T11](t11-candidates.json).

Os Dockerfiles constroem imagens genéricas. Configuração corporativa de build
entra como secret temporário; configurações pessoais, autenticação Salesforce,
projetos e aplicativos proprietários preparados pertencem ao estado local da
workstation. Os artefatos de CI são produzidos em runners descartáveis a partir
dos fontes versionados. A evidência anterior de camadas continua limitada aos
digests registrados nela; não deve ser apresentada como nova varredura de todos
os arquivos OCI ou como aprovação de uma nova versão.

A licença MIT foi comparada com o modelo canônico da API GitHub. O build dos
comandos inclui `ELECTIVUS-LICENSE` no mesmo diretório dos avisos Moby e Go;
`setup.cmd` extrai esse diretório junto dos executáveis. Consulte
[licenciamento e distribuição](../licensing.md) para o escopo das licenças.

O target `commands-export` foi construído com sucesso a partir do Dockerfile
alterado. O build executou a verificação de formatação, `go vet` para Linux e
Windows e compilou ambos os executáveis. Os arquivos MIT, Moby e de atribuição
exportados foram comparados byte a byte com os fontes; a presença da licença
Go e dos quatro arquivos de comandos também foi confirmada. Essa verificação
exercita a alteração de empacotamento, sem representar novo teste do desktop.

## Registro e limites

O espelho de recuperação, respostas brutas da API, logs e relatórios redigidos
do scanner permanecem em armazenamento local restrito, fora do repositório e
do contexto de build. Dados de autenticação produzidos pela própria API não
são conteúdo público do projeto e foram excluídos da cópia de metadados usada
na revisão. Não foram adicionados ao Git.

Uma varredura sem achados não prova ausência absoluta de dados sensíveis.
Novos commits, comentários e artefatos precisam conservar a mesma separação
entre material público e estado pessoal. A confirmação de visibilidade pública,
acesso anônimo e configurações de proteção deve ser registrada após a mudança.
