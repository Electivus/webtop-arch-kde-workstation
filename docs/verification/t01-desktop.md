# T01 - desktop local no Windows

Validação de 2026-09-14. Escopo: [T01 / issue #2](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/2), a partir do checkpoint Git `61a50a5ac9e5f68d039297b62c99b6c23a2a6844`. Não representa a aceitação dos aplicativos e operações dos tickets posteriores.

## Plataforma e imagem

- Dell Latitude 5450, Intel Core Ultra 7 165U, 12 cores / 14 processadores lógicos, 33.777.467.392 bytes de RAM física.
- Windows, Docker Desktop 4.90.0, engine 29.7.2, `desktop-linux`, kernel `7.0.12-linuxkit`, linux/amd64.
- VMM: `UseLibkrun=true` na configuração e encaminhamento ativo `com.docker.backend.exe.sailorforward` para o endpoint de teste nos logs do backend. Esses sinais identificam o ensaio local; não são evidência Hyper-V.
- VM atual: 4.096 MiB configurados, 3.972 MiB reportados pelo engine e 14 CPUs. Workstation do teste gráfico: limite de 2.560 MiB / 4 CPUs, tela 1920 x 1080, codificação por CPU a 30 fps. A VM não foi reconfigurada; o perfil final de 8 GiB / 6 CPUs e as medições Salesforce pertencem a T12.
- Upstream consumido: `lscr.io/linuxserver/webtop:arch-kde@sha256:ed197a60c161b5d45a0d0137a5c47ecd136964c57791bf3151d01ad41ac6b988`.
- Candidata local: `electivus/webtop-arch-kde-base:t01`, versão `2026.09.14-t01`, identificador local `sha256:25ad1ac30fdec00d7744a27bce27590c381e28043e06631f707b5dc9058bf587`. Não foi publicada.

## Resultados observados

| Critério T01 | Evidência |
| --- | --- |
| Imagem Arch/KDE amd64 | Build pelo Dockerfile fixado; processo Plasma ativo e desktop renderizado. |
| Instalação e operação Windows | `install`, `start`, `status`, `stop`, `certificate`, `trust` exercitados em processos Windows PowerShell 5.1; `start` reutilizou o mesmo ID após `stop`. |
| Atalho | `Start Workstation.lnk` criado e executado pelo Windows, apontando para os comandos copiados dentro do perfil; container `ew-test-shortcut-t01` passou de ausente para saudável. |
| HTTPS local e entrada direta | Porta publicada unicamente em `127.0.0.1`; HTTP nessa porta retorna 400; HTTPS com confiança da instalação retorna 200 sem autenticação adicional. Browser abriu sem exceção de certificado. |
| Idioma, formatos e teclado | Ambiente do processo `plasmashell`: `LANG=en_US.UTF-8`, `LANGUAGE=en_US`, categorias regionais `pt_BR.UTF-8`, `TZ=America/Bahia`. XKB: modelo `abnt2`, layout `br`. Data UTC-03 e interface inglesa vistas na captura. |
| Acentos e símbolos | Texto recebido no Konsole e recuperado do arquivo: `ação ç áéíóú ãõ ê ü @ / ? |`. O teste usa eventos de teclado CDP para os caracteres compostos; a inserção de texto sem eventos não exercita esse transporte. Teste físico do teclado do destino continua no roteiro T12. |
| Continuidade da sessão | A aba foi fechada e outra abriu o mesmo endpoint. PID 1088 e instante de início do terminal permaneceram iguais; a tarefa avançou de `1789410324` para `1789410326` após a reconexão. |
| Isolamento dos testes | `Test-ResourceIsolation.ps1` recusou container e volume sem o identificador da instalação e confirmou que seus estados não foram alterados. Fixtures usam nomes próprios gerados por GUID. |
| Confiança reversível | `untrust` removeu o certificado de teste do armazenamento `CurrentUser/Root`; uma nova consulta confirmou sua ausência. |

![Desktop após fechar e reabrir a aba](t01-desktop.png)

## Repetição

```powershell
docker build --file images/base/Dockerfile --build-arg VERSION=2026.09.14-t01 --tag electivus/webtop-arch-kde-base:t01 .
pwsh -NoProfile -File tests/Test-Lifecycle.ps1 -KeepResources
pwsh -NoProfile -File tests/Test-DesktopBrowser.ps1 -ProfileDirectory '<profile-devolvido-pelo-teste>'
pwsh -NoProfile -File tests/Test-ResourceIsolation.ps1
```

Os relatórios brutos de ciclo e navegador ficam no perfil de teste em `.local/`; as capturas também ficam nesse diretório ignorado. ShellCheck, shfmt e o parser PowerShell verificam os scripts. O workflow `Checks` repete o build, o ciclo e o isolamento em Linux no GitHub; a prova específica Windows/VMM é este ensaio local.

Para o destino: Docker Desktop já configurado com containers Linux via Hyper-V, contexto local, capacidade disponível e permissão para confiar no certificado de `localhost`. Os comandos não instalam WSL, não habilitam virtualização e não modificam o backend. A execução real em Hyper-V permanece pendente e o roteiro executável completo será entregue em T12, conforme DEC-030.
