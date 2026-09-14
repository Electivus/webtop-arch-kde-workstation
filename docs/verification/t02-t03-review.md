# Revisão T02/T03

Ponto inicial: `959f3bf3bc02f073e345c3ff351c2d2af6d9766b`. Checkpoint da revisão inicial: `d3fc05b4b2d6030ea693d8ac5866409fcacb785f`. Dois revisores independentes trabalharam em sequência, somente com leitura, sobre o mesmo diff. Os relatórios foram reunidos antes das correções.

## Standards

Resultado: zero violações demonstráveis de padrões documentados; dois possíveis casos de **Duplicated Code**, classificados como julgamentos de manutenção.

1. `workstation-apps`: `ready()` aceitava o sucesso de `--version`, enquanto o preparo explícito comparava também o manifesto instalado. A preparação automática poderia aceitar um estado que o comando manual rejeitava.
2. `browser_apps.py` e `browser_acceptance.py`: repetem o ciclo de isolamento Playwright, confiança de certificado, log e limpeza das instalações descartáveis.

Tratamento: o primeiro foi corrigido com validação compartilhada da instalação persistida. O segundo fica registrado como dívida de manutenção, sem refatoração nesta entrega: os dois cenários já têm isolamento e limpeza verificados; extrair essa infraestrutura ampliaria a alteração sem corrigir uma falha de comportamento identificada. O revisor não exigiu follow-up por violação de padrão.

## Spec

Resultado: um achado P2 e nenhum desvio de escopo. O critério T03 exige instalar o Salesforce Extension Pack. A condição de conclusão conferia somente Pack/Core/Apex/LWC e poderia ignorar a ausência de Visualforce, SOQL ou outro membro do Pack.

Tratamento: a condição agora percorre `extensionPack` e `extensionDependencies` dos [manifestos do fornecedor](https://code.visualstudio.com/api/references/extension-manifest), incluindo dependências transitivas. O CLI de cada editor localiza o Pack; somente os manifestos correspondentes às versões efetivamente instaladas participam da conferência. O preparo instala os membros ausentes e verifica novamente o conjunto completo antes de concluir. A preparação automática usa essa mesma condição.

O revisor pediu um único follow-up limitado a essa correção e suas regressões. Esse follow-up está pendente neste registro.

## Verificação das correções

- Antes da correção, remover Visualforce de Stable e executar `prepare` produziu `state=completed` com a extensão ainda ausente. O novo teste rejeitou esse resultado.
- Antes da correção, alterar o recibo da versão de Chrome e reiniciar manteve o preparo automático como `completed`. O novo teste rejeitou esse resultado.
- Com o código corrigido aplicado ao container descartável já preparado, o ensaio removeu e restaurou Visualforce em Stable e Insiders pelos CLIs oficiais, preservando os manifestos dos aplicativos. O ensaio de reinício detectou o recibo incompatível e registrou a falha automaticamente. O manifesto original foi restaurado no encerramento do teste.
- Os dois cenários foram incorporados a `tests/test_salesforce.py` e `tests/test_preparation.py`, sem acesso às funções internas do preparo.
- Os testes Salesforce agora limitam CPUs ao menor valor entre quatro e a capacidade do engine. O repositório é privado, e o [runner Linux padrão do GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) oferece duas CPUs; a reserva de memória do teste permanece em 6 GiB. Isso adapta o ensaio à máquina que o executa sem alterar os padrões do notebook.

T01 e T04–T13 não foram reabertos nesta revisão. Publicação, atualização explícita, configuração corporativa e aceitação Hyper-V continuam nos respectivos tickets.
