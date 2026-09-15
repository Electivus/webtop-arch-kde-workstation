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

As imagens foram reconstruídas. Os outros sete cenários de pacotes passaram em 369,493 s; todos os nove casos daquele lote foram cobertos em dois grupos sem sobreposição. A bateria completa de backup passou (13, 1.136,115 s), e o inventário Salesforce passou em 17,434 s incluindo o runner. O processo final terminou com código zero. Esses resultados foram apresentados ao único follow-up Spec solicitado, junto do achado original e das regressões da correção.

## Único follow-up Spec

O revisor examinou `fa550f5a095513e1c3817729221d68d646edc769`, mantendo o ponto fixo original. Confirmou todos os recibos locais acima e a validade da ancestralidade Planning, sem executar Docker ou testes. A revisão não usou o relatório do outro eixo.

O P2 foi considerado parcialmente resolvido: se o novo `pacman -D` falhasse, os hooks anteriores já poderiam ter sobrescrito a razão persistente, enquanto a escolha original existia apenas em memória. Uma nova tentativa poderia terminar com sucesso e ainda perder o pacote durante uma remoção recursiva. O revisor citou o requisito de inventário persistente e nova tentativa; identificou o caminho por inspeção, deixando a reprodução real para o coordenador.

## Lote final de correções

O coordenador confirmou que `pacman -D` recusa uma base bloqueada. A primeira fixture não posicionou o bloqueio no intervalo correto: terminou em 94,247 s sem provocar a falha exigida e não conta como reprodução do defeito. A fixture corrigida usa um hook real, pausa apenas seu comando ancestral de restauração, espera a transação liberar a base e injeta um arquivo de lock antes de retomar o comando. A coordenação tem prazo de 20 segundos e retoma o processo ao terminar.

O cenário reproduziu a falha em 145,779 s: a primeira restauração foi rejeitada por `unable to lock database`; depois de recriar o container e repetir, o relatório terminou `completed`, mas toolbelt estava como dependência e a importação falhou após remover HTTPie. A fixture não substitui pacman ou Docker. A recriação remove o lock e o hook de ensaio, conservando somente o volume pessoal.

A correção grava as razões desejadas antes da primeira transação. Os hooks e a captura de inicialização preservam essa intenção enquanto a restauração está pendente. Sua remoção acontece na mesma gravação atômica da captura final e do relatório concluído; erros mantêm a intenção para outra tentativa.

As imagens finais foram reconstruídas: base `sha256:9472b7644b4c4de11d2fdd3669edcb5b5a50035f8ed1dc3cd1bb2a54f7f0a641` e Salesforce `sha256:77615b11ba11d7a0efcc9f5a3dc764403f9c2415c3ee2eb553a109650939a272`. O novo cenário e os nove anteriores passaram juntos em 557,390 s, incluindo a integração com backup, concorrência, dependências explícitas e implícitas, proxy, falha/retry e DOM do Chrome. O inventário Salesforce também passou, em 16,265 s incluindo o runner. O processo final terminou com código zero; sintaxe Python e `git diff --check` passaram.

O lote final foi validado pelo coordenador, sem nova revisão independente. O ciclo delimitado está encerrado: o P2 inicial e seu caminho residual foram corrigidos e reproduzidos em testes reais; permanecem adiadas as duas sugestões opcionais de Standards. Não há achado funcional conhecido pendente. O CI Linux novo e a validação real Hyper-V continuam sendo evidências separadas da aceitação local VMM.

## Feedback publicado na PR #20

O acompanhamento da PR identificou dois P2 do bot no SHA publicado `bc7ad6e4d849e4e6310fd0f86f64f1795251fa09`. Eles foram tratados no fluxo de feedback publicado, mantendo encerrado o ciclo de revisão independente acima.

- [Pacotes divididos interdependentes](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/20#discussion_r4014130530): dois resultados da mesma receita dependem um do outro. A instalação original conjunta passa, mas a restauração anterior chama `pacman -U` separadamente e deixa ambos ausentes. Reprodução real em 89,995 s. A restauração agora instala todos os resultados registrados da mesma receita em uma transação e reconcilia suas razões salvas depois. O cenário e a regressão de compilação/falha/nova tentativa passaram juntos em 188,516 s; um pacote permanece explícito, o outro dependência, e ambos executam.
- [Substituições de componentes Arch](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/20#discussion_r4014130543): uma fixture deriva a imagem e instala um componente compilado. Um repositório local com banco e pacotes assinados disponibiliza seu sucessor; o `pacman -Syu` aceita a substituição, mas o inventário anterior rejeita o nome original ausente. Reprodução em 56,967 s. A primeira tentativa da fixture falhou em 2,132 s porque o contexto de build excluía os arquivos de teste; não conta como reprodução do produto.

O inventário reconhece `replaces` nos metadados instalados e confere condições com `vercmp`. A identidade do sucessor fica vinculada à lista de componentes da imagem no estado persistente, permitindo uma segunda substituição que só declare o nome intermediário. Sucessores continuam sendo componentes fornecidos, sem virar extras. Um componente original presente prevalece sobre associações antigas; a ausência do último sucessor permanece um erro.

O ensaio assinado passou em 125,873 s: duas substituições sucessivas, reinicializações, execução do programa, exclusão dos sucessores da lista de extras e falha obrigatória depois de remover o último. As chaves efêmeras pertencem apenas ao container de teste; as verificações de assinatura ficam habilitadas e o teste não modifica a confiança do host. Imagens reconstruídas com ambos os ajustes: base `sha256:d56738d149113a051bc8c00aed9db968176e9d27d66475431126fc19885f1887` e Salesforce `sha256:21be649d5ef2d5606006ab3592fecb013336b2aa153f2757443ba21810269d9f`.

Os outros onze cenários de pacotes passaram em 918,278 s, incluindo backup, concorrência, razões de instalação, interrupção/retry, pacotes divididos, proxy, DOM do Chrome e componente realmente ausente. Junto do cenário assinado, os doze casos foram exercitados sem sobreposição nas mesmas imagens finais. O inventário Salesforce passou em 30,018 s incluindo o runner. O SHA-256 do helper em ambas as imagens coincide com a fonte local: `a9ed338d232d70801e34aa4f50a33d0618bbe375cf6e02c099cd094230e095a8`. Sintaxe Python, ShellCheck, shfmt e diff sem erros de whitespace foram verificados; o ajuste final de indentação da receita de ensaio não altera seu comportamento.

O CI do SHA publicado original também passou: run `34952711884`, job `104327142437`, 41 min 57 s, concluído em 2026-09-15 às 10:10:59 UTC. Esse recibo pertence ao estado anterior às duas correções; o novo SHA exige sua própria execução. Ambos os P2 publicados foram reproduzidos e corrigidos localmente, sem reiniciar a revisão independente.
