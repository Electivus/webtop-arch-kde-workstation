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

## Feedback publicado na PR

O bot `chatgpt-codex-connector` publicou três achados adicionais na [PR #19](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/19), no head `031f945d337793783b5d07faa970da5660d0a6c3`:

- [P1, integridade do manifesto](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/19#discussion_r4012142397): um valor de porta válido ou uma configuração de rede alterada podiam passar porque só o tar tinha checksum. O cenário falhou em 36,241 s e passou em 33,170 s após adicionar `manifest.sha256`, exigido na leitura. A prova rejeita porta/rede alteradas e checksum ausente antes da interrupção, sem mudar o perfil, a rede ou a sessão. Uma cópia só informa conclusão e participa da retenção depois de passar pela verificação completa.
- [P2, troca do tar depois da verificação](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/19#discussion_r4012142401): o teste substitui o arquivo por outro tar válido depois do aviso público de parada, antes da extração. Falhou em 36,076 s porque a recuperação retornou sucesso. O fluxo lido para extrair passou a ser verificado antes do commit do perfil; a prova passou em 48,141 s, mantendo perfil e dados originais.
- [P2, perda da tag antiga](https://github.com/manoelcalixto/webtop-arch-kde-workstation/pull/19#discussion_r4012142408): o teste de perda agora também remove uma tag descartável, preservando o ID da imagem. Falhou em 20,373 s por exigir essa tag. A restauração passou a validar primeiro a imagem registrada e, na ausência de container/imagem atual, usar a variante do backup quando ele pertence à mesma instalação. A prova passou em 33,884 s. Cópias de outra instalação continuam exigindo uma variante verificável no destino.

Essas correções respondem ao feedback publicado do watcher, sem reiniciar os dois eixos independentes. As fixtures de perfil inválido e tar malformado passaram a fornecer um checksum de manifesto coerente para continuar exercitando as falhas estruturais e de extração, além da verificação de integridade.

A bateria completa de backup passou nos artefatos reconstruídos: 12 testes em 1.030,865 s, incluindo recuperação Salesforce e os três casos do review. Gofmt, go vet e builds Windows/Linux também passaram. A aceitação Linux/CI deste novo commit e o fechamento dos três threads serão registrados na integração.

## Correções orientadas pelo CI

O primeiro CI da PR aprovou os 16 cenários anteriores e oito dos dez cenários de backup publicados, mas falhou por falta de disco na recuperação Salesforce e por classificar a workstation como escritora depois da parada. A preparação do runner libera ferramentas não utilizadas e exige 32 GiB antes do build; o bloqueio consulta o estado atual da inspeção. A hipótese de listagem desatualizada não foi reproduzida na sonda local de 150 ciclos e será confrontada com o novo CI.

A amplificação do diagnóstico foi reproduzida com extração real e corrigida com um limite de 16 KiB mais aviso, sem deixar de drenar a saída. Os quatro cenários afetados passaram em 279,397 s, com os dados originais preservados. O [relatório de validação](t07-backups.md#falhas-do-primeiro-ci-da-pr) registra os logs, o contraste entre evidência e hipótese, os checks de build/workflow e os limites desta repetição. Não houve nova rodada dos eixos independentes.
