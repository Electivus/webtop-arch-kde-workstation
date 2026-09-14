# T01: Abrir e controlar o desktop Arch/KDE pelo Windows

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

Comando e atalho abrem um desktop local utilizável, com idioma e teclado acordados; fechar a aba mantém a sessão e parar encerra a execução.

## Acceptance criteria

- [ ] Construir e iniciar uma imagem Arch/KDE a partir do upstream correspondente, registrando o digest da base e a arquitetura linux/amd64.
- [ ] Instalar o perfil local e iniciar o desktop por comando CMD e atalho Windows, partindo de Docker Desktop com containers Linux disponível, sem chamar PowerShell direta ou indiretamente.
- [ ] Abrir o desktop por HTTPS apenas no próprio notebook, com entrada direta e procedimento de conexão local documentado.
- [ ] Configurar interface em inglês, formatos brasileiros, America/Bahia e ABNT2; verificar acentos, cedilha e símbolos na sessão.
- [ ] Fechar e reabrir a aba preserva uma tarefa observável e a sessão; o comando de parar encerra a execução e o comando de iniciar permite novo uso.
- [ ] Registrar o backend efetivamente usado no teste VMM, os pré-requisitos do destino Hyper-V e o perfil de hardware; o fluxo não exige WSL2 nem habilita virtualização no Windows.
- [ ] Entregar verificação repetível pelos comandos de uso e pelo desktop, com recursos de teste identificados e sem alterar containers alheios.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 7575b9991bfbd00b514f6f75c0f555b2e9bd7236
- Decisions: DEC-001, DEC-002, DEC-004, DEC-005, DEC-007, DEC-016, DEC-017, DEC-025, DEC-033, DEC-036

### Decision consequences

- `DEC-001`: Entregar o caminho completo entre uma imagem Webtop Arch/KDE e seu desktop em execução.
- `DEC-002`: Implementar operação Windows sobre Docker Linux compatível com o destino Hyper-V, sem dependência de WSL2.
- `DEC-004`: Identificar linux/amd64 e o hardware de referência no perfil inicial, deixando os recursos ajustáveis.
- `DEC-005`: Registrar Docker VMM como backend efetivamente exercitado nesta etapa local.
- `DEC-007`: Disponibilizar uma sessão pessoal por endpoint restrito ao notebook.
- `DEC-016`: Permitir entrada direta no desktop local sem senha adicional.
- `DEC-017`: Aplicar e testar idioma, formatos brasileiros, ABNT2 e America/Bahia.
- `DEC-025`: Fornecer comandos de início e parada e um atalho Windows que inicie sob demanda.
- `DEC-033`: Manter a sessão ao desconectar o navegador e encerrá-la pelo comando de parar.
- `DEC-036`: Entregar o ponto de entrada CMD, os componentes de operação necessários e o atalho sem dependência de PowerShell; esse contrato deve ser reutilizado nos comandos posteriores.

## Blocked by

- Nenhum; pode iniciar imediatamente.
