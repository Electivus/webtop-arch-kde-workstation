# T12 — Preparo do Code Analyzer

A extensão Code Analyzer requer o plugin separado da Salesforce CLI. A configuração da variante Salesforce passa a instalar `@salesforce/plugin-code-analyzer@5.15.0` no primeiro preparo, registrar a versão efetiva e recuperar a versão registrada se o plugin for removido. O comando explícito `update-apps` pode instalar uma versão posterior, após o backup. A dependência está descrita na [documentação oficial](https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/analyze-vscode.html).

## Validação local de desenvolvimento

Em 17 de setembro de 2026, os testes usaram o CMD nativo do Windows e Docker Desktop WSL2. O executável distribuído tem SHA-256 `fba6ce1b23bcb1efe7ddc37a135536760dc6bcdb7099a01e906e9a1d5c407ea2`. A imagem de desenvolvimento aplica o preparo e a configuração novos sobre a candidata anterior `2026.09.17-35164853337-1`; não é uma candidata aprovada para publicação.

- `SalesforceAcceptance.test_both_official_editors_and_cli_survive_recreation` passou em 561,647 segundos: preparo automático do plugin, análise PMD real de Apex, recriação do container, serviços Apex/LWC nos dois editores e recuperação de componentes removidos. As asserções finais de ausência do plugin e igualdade exata do recibo foram acrescentadas depois de esse processo Python iniciar; sua execução completa permanece a cargo do CI.
- `UpdateAcceptance.test_salesforce_cli_and_extensions_update_and_recover_with_the_project` passou em 1.401,620 segundos: CLI `2.149.1 → 2.150.6`, Code Analyzer `5.14.0 → 5.16.0` e Visualforce `67.14.0 → 67.17.2` nos dois editores. A recuperação restaurou as versões originais e o conteúdo do projeto. Os serviços dos dois editores e a análise PMD passaram novamente após atualizar e recuperar.

Os recibos portáteis [de preparo](t12-code-analyzer-preparation.json) e [de atualização](t12-code-analyzer-update.json) identificam esse alcance. O teste PMD usa uma classe Apex temporária com um bloco `catch` vazio e exige a ocorrência de `pmd:EmptyCatchBlock`; não acessa uma organização Salesforce.

## Limites da evidência

A execução inicial do CI [35219270598](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35219270598/attempts/1), no código `89e19f54e55122902cfe3d8cbea053ed3cf572d2`, falhou durante a instalação das extensões: o Marketplace retornou HTTP 503 em um caso e interrompeu a resposta no outro. A aprovação permaneceu falsa. Essa falha não aprova a imagem nem invalida os resultados locais acima; a candidata resultante ainda precisa da aceitação completa.

A [segunda tentativa](https://github.com/Electivus/webtop-arch-kde-workstation/actions/runs/35219270598/attempts/2) parou antes dos testes Salesforce: a composição ABNT2 a 80 ms entre teclas retornou `á ã ç êü  @ / ? |`, com um espaço fora de ordem. A investigação desse comportamento do desktop original foi encerrada por solicitação do usuário. Nenhuma correção experimental de teclado entrou na imagem. A aceitação de layout mantém a comparação exata dos caracteres, com digitação pausada a 250 ms; não verifica nem promete correção de digitação rápida.

O dimensionamento final do Latitude depende de um ensaio separado sobre a candidata identificada. A execução real no notebook Hyper-V permanece pendente.
