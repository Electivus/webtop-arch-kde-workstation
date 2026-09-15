# Proxy e certificados corporativos

A configuração é opcional e pertence ao perfil da instalação no notebook. Os comandos abaixo funcionam no CMD. As CAs configuradas são aplicadas aos aplicativos Linux quando a workstation inicia, sem um diálogo de confirmação por certificado. A confiança de `https://localhost` no navegador Windows continua administrada pelos comandos `trust` e `untrust`.

Crie um arquivo JSON local, por exemplo `network-input.json`, junto dos certificados PEM fornecidos pela sua empresa:

```json
{
  "proxy": "http://proxy.example:8080",
  "noProxy": [".internal.example"],
  "caFiles": ["corporate-ca.pem"]
}
```

Cada opção pode ser omitida. `proxy` aceita um proxy HTTP com CONNECT para destinos HTTPS; `noProxy` contém hosts ou domínios que devem usar conexão direta. `localhost`, `127.0.0.1` e `::1` já ficam fora do proxy. Cada entrada de `caFiles` é um arquivo PEM com uma ou mais CAs válidas, sem chaves privadas. Caminhos relativos são resolvidos a partir do JSON. Os certificados são copiados para o perfil; mudar o arquivo original não muda uma configuração já importada.

Na primeira instalação, acrescente `--network-config "C:\Workstation\network-input.json"` ao comando `install`. Para uma instalação existente:

```bat
set "WS_PROFILE=%LOCALAPPDATA%\Electivus\Workstation\base"
workstation.cmd network --profile "%WS_PROFILE%" --network-config "C:\Workstation\network-input.json"
workstation.cmd network --profile "%WS_PROFILE%"
```

O resultado informa apenas se há proxy e a quantidade de certificados. `restartRequired: true` indica que a workstation está aberta: salve seu trabalho e aplique a configuração no próximo início.

```bat
workstation.cmd stop --profile "%WS_PROFILE%"
workstation.cmd start --profile "%WS_PROFILE%"
workstation.cmd network --profile "%WS_PROFILE%" --check
workstation.cmd prepare --profile "%WS_PROFILE%"
```

A transferência usa `docker cp`, sem acrescentar uma pasta compartilhada do Windows. `network --check` faz conexões reais pelo transporte da preparação e pelo Git. O resultado identifica o aplicativo e a categoria da falha, como `tls`, proxy/rede ou tempo limite, omitindo endereços privados, credenciais e conteúdo recebido. O endpoint padrão é o repositório público Git; `--url` pode apontar para outro repositório Git HTTPS. Um servidor HTTPS sem o protocolo Git pode passar na preparação e falhar na etapa Git.

Uma falha de preparação continua disponível em `prepare --status`, com aplicativo e etapa. Depois de corrigir a configuração e reiniciar, execute `prepare` novamente para retomar os downloads e instalações pendentes.

## Aplicativos

| Aplicativo | Configuração aplicada |
| --- | --- |
| Preparação e Git | Proxy por ambiente e confiança do sistema, preservando as raízes existentes. Novos terminais Zsh carregam as opções do perfil. |
| Chrome | Proxy no lançador e CAs no sistema e no banco NSS do usuário. |
| Stable e Insiders | Proxy no lançador, CAs do sistema/NSS e ambiente para processos Node e extensões. |
| Salesforce CLI | Proxy e acréscimo de CAs no processo Node iniciado pelo lançador `sf`. |

A instalação do Salesforce Extension Pack usa a mesma configuração da preparação. Extensões que implementam sua própria conexão podem exigir opções do fornecedor; o [guia de rede do VS Code](https://code.visualstudio.com/docs/setup/network) documenta essa diferença. `network --check` cobre preparação e Git; não representa um login Salesforce nem uma verificação de todas as extensões instaladas pelo usuário.

Para proxies com autenticação, clientes de terminal podem usar uma URL com usuário e senha no JSON local, codificados como componentes de URL. O [Chromium não usa credenciais embutidas na URL do proxy](https://chromium.googlesource.com/chromium/src/+/HEAD/net/docs/proxy.md#proxy-credentials-in-manual-proxy-settings); Chrome e os editores usam suas próprias janelas de autenticação. Os lançadores passam somente o endereço do proxy ao Chromium. Os relatórios de rede e preparação removem credenciais, inclusive quando um proxy as repete em uma mensagem de erro.

## Remover a configuração

```bat
workstation.cmd network --profile "%WS_PROFILE%" --clear
workstation.cmd stop --profile "%WS_PROFILE%"
workstation.cmd start --profile "%WS_PROFILE%"
```

A remoção elimina as opções e CAs gerenciadas por esta instalação, preservando as raízes do sistema e os demais certificados. O JSON de entrada e os arquivos de certificados originais continuam no local escolhido por você. O perfil guarda `network.json`; esse arquivo pode conter credenciais e pertence à configuração privada da instalação.

## Referências

O [Chromium documenta o banco NSS no Linux](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/cert_management.md). O [VS Code descreve a configuração de rede e suas diferenças para extensões e CLI](https://code.visualstudio.com/docs/setup/network). O [Node documenta o acréscimo de CAs e o uso de proxy por ambiente](https://nodejs.org/docs/latest-v24.x/api/cli.html), também recomendado pelo [guia da Salesforce CLI](https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sfdx_setup.pdf).
