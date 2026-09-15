# T07: revisão de backup e recuperação

Ponto fixo: `abccdd64047ec769199f6d3225320256b6962b47`. Checkpoint revisado: `fd1ca264b6a6b3582c269211b2be384205893ea1`. Dois agentes independentes leram o mesmo intervalo congelado, em sequência. Os commits herdados de T06/main até `3de7c81451b9d953a56f5f79710fbce9ad4f9690` não foram reabertos. Ambos confirmaram a árvore limpa e o preflight Planning final `7575b9991bfbd00b514f6f75c0f555b2e9bd7236` para DEC-015/DEC-029. A revisão foi de fonte e documentos, sem executar a suíte Docker ou modificar arquivos.

## Standards

O agente `t07_standards` encontrou **zero violações documentadas** e duas possibilidades heurísticas, sem caráter obrigatório:

- **Possível Repeated Switches**, `cmd/workstation/main.go:142–158,169–206`: as classificações `readOnly` e de comandos de certificado estão separadas do dispatcher. Um descritor por comando poderia reunir despacho e política de bloqueio. Nenhuma regra documentada obriga essa estrutura.
- **Possível Duplicated Code**, `tests/test_backups.py:62–67,121–125,168–171,251–257,292–297,317–321,369–374`: seleção e remoção de volumes de fixture e descarte de arquivos tar se repetem. Um helper restrito aos recursos da fixture poderia reunir futuras correções de cleanup.

As referências indicam as linhas no SHA congelado. As duas sugestões foram conferidas e ficaram adiadas: o dispatcher ainda tem poucas políticas, e a extração das fixtures não é necessária para resolver os problemas de integridade. O agente não identificou PowerShell/WSL2 no fluxo de destino, desativação de TLS ou Docker prune.

## Spec

O agente `t07_spec` encontrou dois problemas **P2**, citando a issue #8 integral:

1. **Uma cópia corrompida pode deslocar uma válida.** O requisito diz “preserva os backups válidos em caso de falha”. `backup.go:149` listava cópias sem conferir checksum; a retenção em `388–393` podia contar B corrompida, mas do mesmo tamanho, junto com C nova e apagar A válida. Uma rejeição prévia de B na restauração não mudava essa seleção.
2. **Manifesto sem perfil pode informar recuperação bem-sucedida.** O requisito diz “Diagnosticar falta de espaço, backup incompleto e falha de recuperação sem informar sucesso”. A validação em `backup.go:102` aceitava `profile` ausente/null, e `509–523` poderia gravar porta e limites zerados, perder o vínculo de troca, informar `state: restored` e remover o volume anterior.

Não foram identificados outros requisitos ausentes ou ampliações indevidas de escopo. Os dois cenários foram conclusões estáticas do revisor e depois reproduzidos pelo coordenador através dos comandos públicos.

## Correções e validação

Uma única rodada de correções trata os dois achados de Spec. A leitura de backup passou a verificar sempre o SHA-256, inclusive na listagem e na seleção da retenção. Os campos obrigatórios do perfil são validados antes de qualquer alteração da instalação: schema, identidade, nomes, imagem, contexto, porta e limites. Um perfil ausente, null ou parcial retorna erro específico.

O cenário de corrupção mantendo o tamanho falhou em 26,494 s: a cópia A havia sido apagada. Passou em 40,354 s após a correção, mantendo A/C, separando B corrompida e restaurando o conteúdo conhecido de A. O cenário de perfil ausente falhou em 38,689 s porque `restore` retornou sucesso; passou em 50,796 s depois da correção. Os 12 casos cobrem ausência, null, objeto vazio e campos obrigatórios inválidos, preservando o perfil atual, a sessão em execução, os dados e a cópia original.

As mudanças ficaram restritas às causas citadas e suas regressões. Nenhum revisor pediu outra passagem, e a correção não mudou requisitos, interface pública ou arquitetura fora desses achados. Aplica-se a regra terminal da skill, sem reiniciar os eixos.

Os Dockerfiles reais passaram novamente gofmt, go vet e builds Windows/Linux. Os dez cenários de backup passaram em 907,684 s nas duas imagens reconstruídas, incluindo as duas regressões, os casos de retenção/falha e a recuperação Salesforce com downloads indisponíveis. Os IDs dos artefatos e os limites da bateria estão no [relatório de validação](t07-backups.md#validação-após-a-revisão).

Contagens iniciais: Standards 0 violações e 2 heurísticas; Spec 2 problemas P2. Os dois problemas foram corrigidos e verificados pelo coordenador; as duas heurísticas permanecem adiadas.
