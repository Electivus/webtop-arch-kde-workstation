# T06: revisão de conectividade corporativa

Ponto fixo: `e41139ba27c2a0c0748a802aeb8cac82db998841`. Checkpoint revisado: `abccdd64047ec769199f6d3225320256b6962b47`. Dois agentes independentes leram o mesmo diff congelado, em sequência. A árvore estava limpa e o checkpoint Planning final `7575b9991bfbd00b514f6f75c0f555b2e9bd7236` passou no preflight. Nenhum revisor executou fixtures Docker ou modificou arquivos.

## Standards

O agente `t06_standards` encontrou duas violações da promessa documentada de remoção em `docs/network.md:59`:

1. **P2, exclusão NSS:** `workstation-network:71` ignorava o retorno de `certutil -D` e a linha 94 descartava o rastreamento da CA mesmo quando a exclusão falhava.
2. **P2, aplicação parcial:** `workstation-network:77` importava a CA antes de persistir seu rastreamento. Uma falha na atualização do trust da linha 83 deixava essa importação fora do recibo utilizado por `--clear`.

Essas linhas referem-se ao SHA revisado. O coordenador conferiu as citações e reproduziu ambos os casos no NSS real: o primeiro falhou em 17,520 s porque a exclusão sem permissão retornava sucesso; após corrigir esse retorno, o segundo falhou em 20,738 s porque a CA permanecia confiada depois da tentativa de limpeza.

O mesmo agente registrou dois possíveis casos de **Duplicated Code**, sem caráter obrigatório: escrita de arquivos temporários em `network.go:93` e `116`, e preparação das fixtures em `test_network.py:25`, `76` e `test_network_apps.py:24`. Ficaram adiados: as rotinas curtas têm finalidades diferentes e a extração de fixtures não é necessária para corrigir os comportamentos observados.

## Spec

O agente `t06_spec` encontrou **zero** requisitos ausentes/parciais demonstráveis, **zero** comportamentos incorretos e **zero** ampliações indevidas de escopo. Confrontou a issue #7 completa, o ticket idêntico, a especificação e DEC-008/021/034. Conferiu os caminhos CMD, a aplicação opcional de proxy/CA, as evidências e os limites do diagnóstico público.

O relatório mantém os limites da prova: o diagnóstico público cobre preparação/Git; Chrome, editores e Salesforce têm cenários próprios no harness. A desconexão anterior do Marketplace permanece sem causa determinada. VMM local e transporte para um serviço Salesforce descartável não comprovam Hyper-V nem autorização em uma organização real.

## Correção e encerramento

Uma única rodada de correções trata os dois achados de Standards. A aplicação enumera os nicknames existentes para distinguir ausência de erro de exclusão, verifica o resultado de operações NSS e grava atomicamente um recibo que inclui as mudanças anteriores e pretendidas antes de alterar os stores. Somente após completar as operações reduz o recibo ao conjunto efetivo. A prova dos dois casos de falha e recuperação passou em 19,688 s.

As correções ficaram restritas às causas citadas e sua regressão. Não houve pedido explícito dos revisores por outra passagem, nem mudança de interface pública, requisito ou arquitetura fora desses achados; aplica-se a regra terminal da skill, sem reiniciar os dois eixos. A verificação final dos cenários afetados nas imagens reconstruídas está registrada no relatório de conectividade.

Contagens iniciais: Standards 2 violações P2 e 2 heurísticas; Spec 0. As duas violações foram corrigidas e verificadas pelo coordenador; as duas heurísticas permanecem adiadas. Nenhum outro achado residual foi identificado nesta rodada.
