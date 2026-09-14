# T06: Preparar proxy e certificados com diagnóstico

## Parent

[Especificacao #1](https://github.com/manoelcalixto/webtop-arch-kde-workstation/issues/1).

## What to build

A instalação recebe configuração corporativa opcional e valida a conexão dos aplicativos e da preparação inicial, preservando TLS.

## Acceptance criteria

- [ ] Receber proxy e certificados de confiança por configuração opcional assistida no notebook, mantendo o uso normal possível sem configuração corporativa.
- [ ] Aplicar a configuração à preparação inicial e às conexões relevantes de Chrome, Git, editores, Salesforce CLI e extensões; documentar configurações específicas quando não forem herdadas.
- [ ] Oferecer diagnóstico que identifique a etapa ou aplicativo com falha sem revelar credenciais ou material privado nos relatórios compartilháveis.
- [ ] Comprovar conexão por um proxy de teste e cadeia de confiança válida configurada, preservando raízes existentes e a verificação TLS.
- [ ] Comprovar que uma conexão com confiança inválida continua sendo rejeitada e que falhas na preparação podem ser retomadas após corrigir a configuração.
- [ ] Inspecionar as imagens e o processo de construção para confirmar que dados, certificados corporativos e credenciais da instalação não foram incorporados aos artefatos públicos.
- [ ] Entregar verificação repetível com infraestrutura de teste e instruções de configuração e remoção das opções locais.

## Planning context

- Format: v1
- Repository: manoelcalixto/webtop-arch-kde-workstation
- Effort: arch-kde-workstation
- Decision ledger: `docs/planning/arch-kde-workstation/decision-ledger.md`
- Planning checkpoint: c1f33c4e8e46de56cf622937e8e55f5adea5ffe7
- Decisions: DEC-008, DEC-021, DEC-034

### Decision consequences

- `DEC-008`: Preservar a separação entre imagem genérica e configuração privada da instalação.
- `DEC-021`: Permitir completar e retomar o preparo inicial usando a conectividade configurada.
- `DEC-034`: Entregar configuração corporativa opcional assistida e diagnóstico efetivo, mantendo TLS.

## Blocked by

- T03: Desenvolver Salesforce com Stable e Insiders.
