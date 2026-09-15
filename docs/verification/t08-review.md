# T08: revisão independente

Ponto fixo `e8e2ae6d51c47c21f76096f175ae8b32237a09e5`; checkpoint revisado `af414e3cca872be5cbd213e1bdb2f161bc5ac108`, commit `feat: inventory and restore personal Arch packages`. Diff não vazio de 18 arquivos. Dois revisores independentes nativos, executados sequencialmente e sem alterações na árvore: `/root/t08_standards` e `/root/t08_spec`.

## Standards

Nenhuma violação obrigatória identificada, considerando AGENTS, documentos roteados e acordos fornecidos. Dois achados heurísticos, não bloqueantes:

- **Duplicated Code, restauração:** `workstation-packages`, linhas 210 e 239 do checkpoint, repete a seleção `--asdeps`, seguida de instalação, consulta `-Q` e classificação `missing`/`restored`. Uma função pequena poderia concentrar a política de instalação e confirmação, mantendo separadas a reconstrução e a obtenção pelo repositório.
- **Duplicated Code, fixtures:** `test_packages.py`, linhas 52, 99 e outros cenários, repete instalação e limpeza dos recursos Docker. Um contexto compartilhado reduziria a manutenção; o caso de backup precisa conservar sua limpeza específica dos volumes recuperados.

Validação do revisor: inspeção estática do diff congelado, regras e helpers; nenhuma execução de testes ou Docker. Os testes usam comandos públicos e ferramentas reais. As verificações pendentes no relatório não foram consideradas aprovadas. O revisor não exigiu follow-up para esses achados.

As duas sugestões ficam adiadas: os fluxos oficiais e de compilação permanecem visíveis, e a limpeza específica de cada cenário continua explícita. A correção funcional abaixo não exige essa refatoração.

## Spec

Um achado P2: a restauração perde a classificação explícita de pacotes desejados. Requisitos citados: manter inventário persistente e disponibilizar restauração assistida. Se dois extras oficiais eram explícitos e o primeiro instala o segundo como dependência, o ramo `installed` (`workstation-packages:236` no checkpoint) não restaura sua classificação. A captura posterior (`:85`) sobrescreve o inventário com `dependency`, embora o relatório informe `completed`. Uma remoção recursiva posterior pode excluir um programa escolhido explicitamente pelo usuário. Isso também contradiz o guia.

O revisor não identificou expansão indevida de escopo nem outro requisito ausente na implementação inspecionada. A renderização adicional do Chrome e as regressões finais foram corretamente classificadas como pendentes.

Validação do revisor: diff congelado completo, código/testes/documentação e preflight Planning válido. Uma sonda em memória reproduziu a classificação incorreta usando efeitos pacman simulados; isso não substitui a reprodução com pacman real. O revisor pediu um único follow-up Spec, limitado ao achado, regressões da correção e conclusão das verificações pendentes.

Resultado inicial: Standards, zero violações e duas sugestões opcionais; Spec, um P2 funcional. A reprodução real, a correção e o follow-up serão registrados neste mesmo checkpoint de revisão.

## Lote de correções

O P2 foi confirmado com pacman real: `httpie` e `python-requests-toolbelt` foram instalados explicitamente; depois da recriação e restauração, toolbelt tornou-se dependência e uma remoção recursiva de HTTPie também o excluiu. O teste falhou em 81,608 s, e a importação da biblioteca após a remoção terminou com código 1.

A restauração passou a reconciliar as razões salvas com `pacman -D` depois de resolver todos os extras, incluindo aqueles já presentes como dependências de instalações anteriores. A captura final registra essa classificação. Erro nessa etapa não pode produzir um relatório `completed`.

O novo cenário passou junto com a prova de falha/recompilação local em 154,828 s. Além de preservar os pacotes locais instalados como dependências, o segundo teste renderizou uma página real no Chrome depois da falha proposital de compilação e concluiu a nova tentativa. As sugestões heurísticas de Standards permaneceram adiadas; não há mudança que exija reiniciar aquele eixo.

As imagens foram reconstruídas. Os outros sete cenários de pacotes passaram em 369,493 s; todos os nove casos da implementação final foram cobertos em dois grupos sem sobreposição. A bateria completa de backup passou (13, 1.136,115 s), e o inventário Salesforce passou em 17,434 s incluindo o runner. O processo final terminou com código zero. O único follow-up Spec solicitado avaliará o achado original, regressões da correção e esses resultados concluídos, sem abrir outro ciclo inicial.
