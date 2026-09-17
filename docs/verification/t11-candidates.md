# T11 — Produção e transporte de candidatas

A execução [35154433830](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35154433830) concluiu com sucesso a produção das duas candidatas e os treze grupos de aceitação. O mesmo par foi baixado, importado e inspecionado no notebook com Docker Desktop WSL2. O teste de Docker/Compose passou pelo CMD do Windows usando os comandos distribuídos com a candidata.

- Código validado: `85e13fae5732627ae24ff4393be2dc503d4481f7`.
- Versão coordenada: `2026.09.16-35154433830-1`.
- Arquitetura: `linux/amd64`.
- Checkpoint Planning: `9c9f2c44531269dae4d785e4f8b7d197e56f0082`.
- Evidência portátil: [t11-candidates.json](t11-candidates.json).

| Variante | Digest preservado na importação |
| --- | --- |
| `electivus/webtop-arch-kde-base` | `sha256:604acd325d7e4b462a2cd346718147fbad554f44c3bd02aa8f8531fba1ad9211` |
| `electivus/webtop-arch-kde-salesforce` | `sha256:6324a930fd6820f6afa7cee73e8d8cc3161a166e6b2f35f34871c34b3e7461c2` |

## Produção e aceitação

O workflow semanal e manual usa um commit limpo, uma versão coordenada e a base correspondente para Salesforce. O manifesto registra a relação entre as imagens, os digests e os checksums dos arquivos OCI e dos sete componentes de comandos/licenças. A construção compara o executável Windows distribuído com aquele incorporado à imagem.

Os cinco testes de contrato e transporte passaram. A aceitação completa executou 55 testes e deixou dois casos específicos de Windows marcados como ignorados no Linux; os treze grupos terminaram aprovados em 4.409,649 segundos. O relatório de aprovação foi confrontado com a conclusão real do job, o commit, os digests e o checksum do contrato. Os casos próprios de Windows continuam identificados para o ensaio completo de T12.

O CI conserva imagens, comandos e diagnóstico como artefatos privados por sete dias. O [guia de consumo](../candidates.md) descreve a importação pelo CMD e a relação entre o resultado local e os arquivos originais.

## Correções verificadas

O engine isolado instalado pela action usava um socket diferente do caminho padrão montado na workstation. A correção liga esse caminho ao engine selecionado somente no servidor efêmero do GitHub e compara seus identificadores antes da construção. O teste de Docker/Compose passou na execução final.

Um teste de backup ainda procurava o controlador na pasta de desenvolvimento antiga. O cenário real de falta de espaço reproduziu a falha em 29,203 segundos; usando o pacote selecionado, passou em 50,458 segundos no Linux e em 82,330 segundos pelo CMD. As verificações de preservação dos dados permaneceram iguais.

Os arquivos OCI e a recuperação completa de Salesforce exigem espaço adicional no CI. A preparação remove ferramentas do servidor que não são usadas pelo projeto e libera o cache de construção após exportar as imagens. A execução final registrou aproximadamente 56 GiB livres antes da construção e 36 GiB antes dos testes, após liberar 15,18 GB de cache. Os limites de espaço da aplicação não foram reduzidos. Essas limpezas são restritas ao servidor efêmero do GitHub.

## Transporte e conteúdo do par aprovado

O carregador conferiu os checksums das duas imagens e dos comandos antes da importação. Os digests permaneceram iguais no Docker Desktop WSL2, versão 29.8.0, kernel `6.18.35.2-microsoft-standard-WSL2`. O teste pelo CMD terminou em 82,737 segundos, comprovando construção de um projeto Linux, escrita no volume pessoal e preservação após recriar o container. O engine observado de dentro da workstation correspondeu ao Docker do notebook.

A inspeção conferiu os hashes de 35 camadas únicas e examinou 288.338 entradas. Não encontrou os locais conhecidos de projetos pessoais, aplicativos preparados nem configuração corporativa. Processos novos, sem inicializadores e sem rede, confirmaram nas duas imagens a ausência de proxy, configuração local e anchors corporativos, preservando 121 raízes públicas. Essa evidência cobre os locais e contratos conhecidos; não representa uma varredura universal de segredos.

## Rejeição comprovada e revisão

A execução [35147084812](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35147084812) falhou no teste real de Docker/Compose, manteve `approved: false`, marcou os nove grupos posteriores como não executados e reteve os três artefatos. Isso demonstra que a falha não declara uma candidata aprovada. O modo de falha deliberada também foi exercitado localmente contra seus arquivos completos: primeira verificação falhou, as outras doze não rodaram, os arquivos permaneceram intactos e o relatório original do CI foi preservado.

A [revisão registrada](t11-review.md) foi uma autorrevisão dos dois eixos: a delegação nativa atingiu o limite de agentes. Houve uma passagem inicial, um acompanhamento limitado ao eixo Spec e validação do lote final de correções, sem reiniciar o ciclo a cada commit.

T11 entrega candidatas verificadas e transportáveis. O dimensionamento do Latitude e o roteiro executável Hyper-V pertencem a T12; publicação pública e promoção de `stable`, a T13. A execução real no notebook Hyper-V continua pendente.
