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

O revisor pediu um único follow-up limitado a essa correção e suas regressões. Ele revisou `ea1927c5034c6e9bd7a261ec2c1f8f6dd56d2ab6` e concluiu: **P2 resolvido, nenhuma regressão concreta identificada no escopo do follow-up**. Conferiu fonte, teste e recibos direcionados sem repetir a execução. A bateria completa das imagens reconstruídas ainda estava rodando naquele momento; seu resultado é registrado separadamente em [T02/T03 - aplicativos](t02-t03-apps.md). Esse follow-up encerrou o eixo Spec.

## Verificação das correções

- Antes da correção, remover Visualforce de Stable e executar `prepare` produziu `state=completed` com a extensão ainda ausente. O novo teste rejeitou esse resultado.
- Antes da correção, alterar o recibo da versão de Chrome e reiniciar manteve o preparo automático como `completed`. O novo teste rejeitou esse resultado.
- Com o código corrigido aplicado ao container descartável já preparado, o ensaio removeu e restaurou Visualforce em Stable e Insiders pelos CLIs oficiais, preservando os manifestos dos aplicativos. O ensaio de reinício detectou o recibo incompatível e registrou a falha automaticamente. O manifesto original foi restaurado no encerramento do teste.
- Os dois cenários foram incorporados a `tests/test_salesforce.py` e `tests/test_preparation.py`, sem acesso às funções internas do preparo.
- Os testes Salesforce agora limitam CPUs ao menor valor entre quatro e a capacidade do engine. O repositório é privado, e o [runner Linux padrão do GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) oferece duas CPUs; a reserva de memória do teste permanece em 6 GiB. Isso adapta o ensaio à máquina que o executa sem alterar os padrões do notebook.

T01 e T04–T13 não foram reabertos nesta revisão. Publicação, atualização explícita, configuração corporativa e aceitação Hyper-V continuam nos respectivos tickets.

## Acompanhamento do PR

O [comentário automático 4010337396](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/16#discussion_r4010337396) afirmou que o contexto de build excluiria Salesforce. O [CI 34906271384](https://github.com/manoelcalixto/webtop-arch-kde-workstation/actions/runs/34906271384) construiu com sucesso as duas imagens do mesmo head, inclusive todos os `COPY` citados. O apontamento foi rejeitado e a thread encerrada sem alteração de código.

Esse CI passou também os testes de ciclo de vida e da base, mas falhou nos dois preparos Salesforce por `ENOSPC` ao instalar a CLI. O runner registrou somente 69 MB livres. O workflow passou a remover apenas seu SDK Android pré-instalado, que não participa deste projeto, antes dos builds; registra o espaço antes/depois e exige um runner hospedado pelo GitHub. A validação do ajuste ocorre na próxima execução do mesmo conjunto de testes.

O [CI 34907654289](https://github.com/manoelcalixto/webtop-arch-kde-workstation/actions/runs/34907654289) confirmou a liberação de 14 para 25 GB. Em seguida, expôs uma corrida no teste PTY: a coleta de meio segundo retornou vazia antes de Zsh terminar de iniciar. Um comando de usuário `sleep 3` no `.zshrc` do perfil descartável reproduziu a falha localmente. O driver agora aguarda o sinal de entrada no editor de linha e cada saída esperada, com prazo de 20 segundos, mantendo as mesmas verificações de cores e sugestão. O caso com início lento passou em 50,144 s após a correção; o atraso pertence somente ao teste.
