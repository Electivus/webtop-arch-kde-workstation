# Revisão T01

Base fixa: `61a50a5ac9e5f68d039297b62c99b6c23a2a6844`.
Primeiro checkpoint revisado: `eca0b3ccbeb34442594a1f3afc2978dc5ef07586`.
Acompanhamento limitado: `bb082747b1a8c38132c07768f097795fe3a94872`.

Dois agentes independentes revisaram os mesmos checkpoints, um por vez. A mudança material da interface pública para CMD e APIs nativas justificou um acompanhamento de cada eixo. Não houve novas rodadas depois dele.

## Standards

Nenhuma violação documentada na revisão inicial ou no acompanhamento da substituição CMD/Go, bootstrap, APIs Windows e testes.

O acompanhamento apontou uma recomendação opcional de baixa prioridade, **Primitive Obsession**: a tabela de métodos COM usava índices numéricos em `platform_windows.go`, dificultando conferir a operação sem consultar a ordem externa da interface. O ajuste final nomeou esses índices, conservando os valores e as chamadas, e passou pela formatação, análise e compilação Go para Windows e Linux. Não altera o comportamento exercitado pelos testes.

## Spec

O primeiro passe encontrou uma lacuna P2 na evidência ABNT2: eventos com caracteres Unicode já compostos comprovavam o transporte pelo navegador, mas não a composição por teclas mortas. O acompanhamento confirmou a correção: `keyboard-abnt2.py` envia códigos físicos X11 e modificadores e compara o texto produzido pelo Konsole.

O acompanhamento não encontrou nova omissão, regressão material ou ampliação indevida em T01. Conferiu extração por `setup.cmd`, entrada por `workstation.cmd`, atalho nativo, propriedade dos recursos Docker, loopback, início sob demanda e continuidade da sessão. A aceitação automática de diálogos ficou restrita aos certificados descartáveis dos testes.

Os agentes inspecionaram o diff, fontes, documentação e evidências congeladas; não repetiram os testes. Os ensaios executados pelo coordenador estão em [T01 desktop](t01-desktop.md). A execução real em Hyper-V e o teclado físico do destino continuam no escopo de T12.

Resultado: Standards teve uma recomendação opcional atendida, sem violação; Spec teve uma lacuna P2 corrigida, sem novo achado no acompanhamento.

## Acompanhamento do PR #15

O revisor automático apontou dois problemas de certificados, reproduzidos antes da correção: o marcador permanente impedia renovação e `untrust` exigia Docker para recuperar um certificado já salvo. O início agora renova a folha dentro de 30 dias do vencimento e preserva seu histórico público; a remoção usa esse histórico, inclusive vencido, sem acessar Docker. Os testes exercitam as duas regressões e passaram no Windows.

O terceiro comentário pediu retornar a cobertura de DEC-036 para `pending`. O contrato de Planning exige avanço monotônico da cobertura já checkpointada. A evidência foi ampliada com o limite explícito de T01: todos os comandos posteriores continuam sujeitos à decisão CMD, e diagnóstico, backup, recuperação e atualização ainda dependem de seus tickets e da aceitação T12/T13. A marca desta etapa não comprova essas operações futuras. Nenhum gate desses tickets foi dispensado.
