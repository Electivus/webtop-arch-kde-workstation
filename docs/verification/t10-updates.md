# T10: atualização explícita dos aplicativos

Ticket [#11](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/11), com preflight válido para DEC-011, DEC-028 e DEC-029 no checkpoint final `7575b9991bfbd00b514f6f75c0f555b2e9bd7236`. A implementação começou sobre `bc7ad6e4d849e4e6310fd0f86f64f1795251fa09`, enquanto T08 estava em revisão. Depois de incorporar T08, o preflight foi repetido com sucesso; o ponto fixo de integração/revisão é `97f539dea2742fdf349c2f188ca6e1fffd72ae4d`.

## Comando, backup e recuperação na base

Os testes entram pelo CMD e pelo executável nativo distribuído. Usam Docker real, volumes próprios e Chrome oficial no volume pessoal. O primeiro teste falhou em 19,939 s porque `update-apps` ainda não existia. Depois da implementação, passou em 241,376 s: backup verificado, atualização explícita, imagem e versão da workstation preservadas, registro de versão/origem do Chrome, projeto renderizado, reutilização após reiniciar e recuperação do estado original pela cópia indicada no relatório.

Dois cenários adicionais passaram sem outra mudança de produção:

- **Falha de conexão, 182,646 s:** após preparar o Chrome, um proxy local indisponível provoca uma recusa real na consulta ao fornecedor. O comando falha, conserva o backup concluído e registra o erro. Reiniciar e preparar reutiliza o programa funcional sem repetir a atualização; o relatório da tentativa continua acessível. A recuperação devolve o projeto e os aplicativos anteriores, com nova renderização do Chrome.
- **Falhas de backup, 70,423 s:** uma pasta de destino ocupada por um arquivo impede o backup antes da parada. Um certificado de arquivo danificado provoca outra falha depois da parada. Nos dois casos, perfil, imagem, container e versões permanecem os mesmos. O caso posterior retoma o container original e mantém a rede já aplicada, embora haja um proxy recusador pendente para a próxima inicialização normal. A conexão real ao fornecedor confirma esse comportamento.

Esses resultados pertencem à imagem base de desenvolvimento `sha256:0ee16e6691ddd572dfb9b8bfe46460f4e464e259259f690966e9c158aa623100`. O export dos comandos passou por gofmt, go vet Windows/Linux e builds para os dois sistemas. A execução local do CMD não exige PowerShell no notebook de destino. Os scripts PowerShell usados para desenvolver e compilar permanecem no ambiente local ignorado pelo Git.

## CLI e extensões Salesforce

A fixture deriva a imagem Salesforce e seleciona a CLI oficial 2.149.1 para a primeira preparação, com a integridade SHA-512 confirmada nos metadados do npm. Os dois editores recebem Visualforce 67.14.0 pelo seu comando real de instalação. A API do Marketplace confirmou essa versão estável anterior; uma consulta inicial à versão inexistente 67.16.0 foi descartada antes de construir o teste.

O primeiro teste falhou em 484,209 s: a atualização concluiu e criou seu backup, mas a CLI 2.149.1 e a Visualforce 67.14.0 continuaram instaladas nos dois editores. A correção consulta a versão estável atual da CLI no registro oficial, confere nome, endereço, integridade e versão executada e solicita a atualização compatível das extensões em cada editor. A preparação normal continua reutilizando o conjunto existente.

As imagens reconstruídas são base `sha256:3914e36aa5463f9cc770e5b33fe81d03bd5c632cd2f8a1eabf6acec32920fdb1` e Salesforce `sha256:e94f611ec6f24d8b7cc1937375f444fd3ed16142e8f2d079e7d82d2f11edd98b`. Os rótulos de desenvolvimento reutilizados para cache não representam proveniência de uma release.

O ensaio completo passou em **997,014 s**. A CLI avançou de **2.149.1 para 2.150.6** e a Visualforce de **67.14.0 para 67.17.2 nos dois editores**, mantendo o identificador da imagem. A execução real da CLI confirmou o recibo. Os testes pelos serviços públicos dos editores verificaram diagnóstico, correção e conclusão Apex, além de conclusão LWC, no Stable e no Insiders. O Chrome renderizou o projeto e o Insiders permaneceu como editor padrão.

Após reiniciar, a preparação reutilizou exatamente os aplicativos atualizados. A recuperação do backup de 6.691.737.600 bytes devolveu as versões anteriores e o arquivo pessoal original. Os mesmos serviços Apex/LWC passaram novamente nos dois editores, e o Chrome voltou a renderizar o projeto. Os quatro recibos dos serviços e o resultado completo estão no diretório local ignorado `.local/ew-update-sf-6deac34650/`; o log de execução é `.local/t10-salesforce-first-green.log`.

## Falha individual de extensão

O [código público do VS Code](https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/platform/extensionManagement/common/extensionManagementCLI.ts) registra erros individuais dentro da operação de atualização sem lançar uma exceção naquele ramo. A inspeção de `main` inicialmente era apenas uma hipótese sobre a versão empacotada. O teste real confirmou o problema em **479,288 s**: uma pasta de extensões sem permissão de escrita provocou `Error while updating extension ... EACCES`, mas o processo retornou zero e o comando declarou a atualização concluída.

A correção reconhece esse diagnóstico individual, conserva a saída para diagnóstico e devolve falha mesmo quando o editor retorna zero. O comando usa explicitamente inglês nessa operação para que a configuração de idioma do editor não mude a mensagem reconhecida. A orientação de erro passa a indicar nova tentativa por `update-apps` ou recuperação do backup correspondente. A preparação normal mantém sua orientação anterior.

Depois de incorporar T08, as imagens para este ensaio são base `sha256:c8dc4b025cd389a1e92f806b967ee72b019180eb87aa9c85f91f031f63392583` e Salesforce `sha256:c33a3269d0d8a36cd8349ded8405d4df245982d7f612f29da4ea36101451efd2`. O teste de falha e recuperação passou em **693,791 s**: o comando informou falha na extensão do Stable, preservou o backup concluído e a extensão anterior, e manteve o desktop utilizável com o projeto renderizado no Chrome. A recuperação devolveu exatamente os aplicativos e o projeto anteriores, mantendo o relatório da tentativa disponível. Recibo local: `.local/ew-update-extension-cd0877c040/extension-failure-update-result.json`; log: `.local/t10-extension-install-failure-first-green.log`.

## Verificações pendentes

O workflow inclui as duas novas suítes de manutenção, preservando os testes anteriores. O limite do job passa de 60 para 120 minutos: o CI final de T08 levou 44 min 24 s e os cinco casos T10, medidos individualmente no Windows, somaram aproximadamente 36 min 25 s. Esses tempos vêm de ambientes diferentes e não são uma medição do novo CI completo; justificam reservar tempo para as suítes adicionais, sem remover verificações.

Ainda faltam a regressão final, a revisão delimitada, os registros Planning de implementação e o CI da futura PR. Os resultados locais usam Docker VMM; não são aceitação real no Hyper-V.
