# T03: Desenvolver Salesforce com Stable e Insiders

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

A variante Salesforce abre projetos nos dois VS Codes oficiais, com CLI, extensões, Java e Node funcionais; Insiders é o padrão.

## Acceptance criteria

- [ ] Construir Salesforce diretamente da base correspondente e executar a variante em um único container, sem outra workstation base em execução.
- [ ] Disponibilizar VS Code Stable e Insiders oficiais por obtenção dos fornecedores para estado persistente, usando o preparo com progresso e retomada já existente.
- [ ] Instalar Salesforce CLI, Salesforce Extension Pack e as dependências Java e Node compatíveis, registrando as versões efetivas e as escolhas de compatibilidade.
- [ ] Abrir um projeto Salesforce de exemplo nos dois editores e comprovar que os serviços das extensões necessários ao trabalho estão disponíveis.
- [ ] Exercitar a CLI e as ferramentas do projeto pelo terminal; a verificação usa dados de exemplo e não depende de incluir credenciais de uma organização na imagem.
- [ ] Usar Insiders ao abrir arquivos e projetos por padrão e permitir iniciar Stable explicitamente.
- [ ] Recriar a variante com seu estado persistido, retomar um preparo interrompido de editor e verificar que aplicativos concluídos continuam disponíveis.
- [ ] Entregar testes do fluxo pelos lançadores, CLI, estado de preparo e desktop para as duas instalações de editor.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: 7575b9991bfbd00b514f6f75c0f555b2e9bd7236
- Decisions: DEC-006, DEC-009, DEC-010, DEC-011, DEC-020, DEC-021, DEC-024

### Decision consequences

- `DEC-006`: Completar o fluxo de desenvolvimento com editor, terminal, navegador e ferramentas de projeto.
- `DEC-009`: Disponibilizar uma workstation própria para desenvolvimento Salesforce.
- `DEC-010`: Implementar somente a especialização Salesforce, herdando diretamente da base e funcionando por si só.
- `DEC-011`: Disponibilizar os dois VS Codes oficiais, CLI e extensões Salesforce e verificar sua integração.
- `DEC-020`: Acrescentar à base o conjunto Salesforce com Java e Node necessários.
- `DEC-021`: Estender a preparação persistente e retomável aos dois canais oficiais do VS Code.
- `DEC-024`: Definir Insiders como editor padrão e manter Stable acessível separadamente.

## Blocked by

- [T02 / #3](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/3): Usar Chrome oficial e terminal preparado na base.
