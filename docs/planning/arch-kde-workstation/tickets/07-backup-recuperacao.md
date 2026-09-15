# T07: Fazer backup e recuperar o estado pessoal

## Parent

[Especificacao #1](https://github.com/Electivus/webtop-arch-kde-workstation/issues/1).

## What to build

Um comando salva e recupera projetos, perfil e aplicativos no Windows, mantém duas cópias concluídas e preserva os backups válidos em caso de falha.

## Acceptance criteria

- [ ] Oferecer comandos Windows para criar, listar e recuperar backups locais do estado pessoal da workstation.
- [ ] Incluir os projetos Linux, perfil, aplicativos persistidos e demais conteúdos persistidos necessários à recuperação; o inventário de pacotes será incluído quando for gerado pelo fluxo correspondente.
- [ ] Obter um ponto consistente e identificar no backup a imagem, os aplicativos e os dados correspondentes, informando a interrupção necessária ao usuário.
- [ ] Criar um estado conhecido nas variantes base e Salesforce, fazer backup, alterar arquivos e preferências e recuperar a cópia selecionada com os aplicativos associados.
- [ ] Manter os dois backups concluídos mais recentes; uma tentativa incompleta ou com falha não substitui uma cópia válida na retenção.
- [ ] Diagnosticar falta de espaço, backup incompleto e falha de recuperação sem informar sucesso nem descartar as cópias válidas.
- [ ] Verificar conteúdo e propriedades dos arquivos restaurados, e documentar que o backup cobre estado persistido, não processos em execução.
- [ ] Entregar testes de recuperação por operações públicas e um procedimento reutilizável pelos comandos de atualização posteriores.

## Planning context

- Format: v1
- Repository: Electivus/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 7575b9991bfbd00b514f6f75c0f555b2e9bd7236
- Decisions: DEC-015, DEC-029

### Decision consequences

- `DEC-015`: Recuperar projetos no armazenamento Linux sem convertê-los em uma pasta de trabalho Windows.
- `DEC-029`: Entregar backup sob demanda e recuperação do estado pessoal completo, com retenção de duas cópias concluídas.

## Blocked by

- [T03 / #4](https://github.com/Electivus/webtop-arch-kde-workstation/issues/4): Desenvolver Salesforce com Stable e Insiders.
- [T04 / #5](https://github.com/Electivus/webtop-arch-kde-workstation/issues/5): Preservar projetos Linux e trocar arquivos com Windows.
