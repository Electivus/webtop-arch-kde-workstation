# Revisão T04/T05

Ponto inicial: `fdb0f82848fef50c77e25c36d64daba60f47c93a`. Checkpoint revisado: `55d3470c8cf5d49d8ecd6604eea919628e0d0741`. Dois revisores independentes trabalharam em sequência, somente com leitura, sobre o mesmo diff. Os relatórios foram reunidos antes de decidir sobre alterações.

## Standards

Zero violações de padrões documentados. Um possível **Duplicated Code**, julgamento opcional: `tests/test_projects.py:71` e `tests/test_docker_projects.py:51` repetem a sequência de parar, remover e iniciar a workstation, seguida da comparação de `containerId`. A instalação e a limpeza também têm estrutura semelhante. Um pequeno helper de recriação poderia concentrar esse protocolo caso ele cresça. Não é violação documentada nem defeito demonstrado. As outras onze categorias do baseline não produziram achados.

O revisor confirmou que os comandos entregues usam CMD/EXE, que o socket mantém suas permissões e proprietário e que a limpeza seleciona recursos próprios. Conferiu HEAD, árvore limpa, hunks, instruções, DEC-013/DEC-015 e recibos; executou `git diff --check`. Inspecionou a evidência dos onze testes sem reexecutá-los. Nenhum follow-up obrigatório.

Tratamento: a citação foi conferida e a sugestão fica registrada como manutenção opcional. A sequência é pequena e os dois testes exercitam cenários distintos com limpeza própria; não há falha de comportamento que exija refatoração nesta entrega.

## Spec

Zero achados concretos: nenhum requisito ausente ou parcial, comportamento não solicitado ou implementação incorreta identificado no escopo T04/T05.

A implementação corresponde aos critérios de persistência Linux, troca bidirecional, diagnóstico de compartilhamento e execução real de Compose sobre o engine existente. `tests/test_projects.py` verifica conteúdo, nomes, permissões, links e alterações nos dois sentidos após recriação. `tests/test_docker_projects.py` verifica identidade do engine, contexto local modificado, montagem, escrita persistente, recriação e diagnósticos.

O revisor confirmou refs, HEAD e árvore limpa, inspecionou o diff e executou `git diff --check` e a validação Planning dos dois tickets. A ancestralidade do checkpoint `7575b9991bfbd00b514f6f75c0f555b2e9bd7236` foi confirmada. Inspecionou os recibos JSON e o [relatório dos onze testes](t04-t05-projects.md), sem reexecutar a bateria ou alterar Docker. Nenhum follow-up corretivo exigido. A consolidação de DEC-013/DEC-015 no ledger é o fechamento da integração; a execução Hyper-V permanece no escopo T12.

## Encerramento

Nenhuma correção de código necessária e nenhum novo ciclo de revisão. Standards: zero violações e uma sugestão opcional de duplicação; Spec: zero achados. A validação local comprova VMM e não representa execução Hyper-V nem publicação de imagens.

## CI do PR

O [CI 34911976877](https://github.com/manoelcalixto/webtop-arch-kde-workstation/actions/runs/34911976877) aprovou builds, ciclo de vida e preparação da base, mas encontrou `PermissionError` ao alterar `from-windows.txt` na troca Linux. O diretório descartável já permitia escrita pelos dois usuários; os arquivos ainda tinham modo `0644`, e o UID do runner difere do UID 1000 da workstation. Um ensaio Linux com UIDs 1001/1000 reproduziu a recusa nos dois sentidos e confirmou a escrita com modo `0666` somente nesses arquivos de teste. A fixture passou a aplicar esse modo aos dois arquivos de troca; os projetos continuam sujeitos às mesmas verificações de propriedades Linux. A suíte de projetos Windows passou novamente: dois testes, 44,466 s. Trata-se de correção da fixture de CI, sem mudança no produto ou reabertura dos eixos de revisão.
