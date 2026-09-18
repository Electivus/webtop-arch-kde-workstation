# Contribuir

Abra uma issue para relatar um defeito ou discutir uma alteração relevante.
Vulnerabilidades seguem o [canal privado de segurança](SECURITY.md). Use exemplos
genéricos; não envie credenciais, projetos corporativos, perfis ou backups reais.
Mantenha a comunicação respeitosa e focada no problema técnico.

Crie uma branch a partir de `main` e abra um PR com problema, solução e evidência
de validação. Mantenha a mudança focada e preserve alterações de outros autores.
O [README](README.md) e o [guia das candidatas](docs/candidates.md) descrevem os
comandos de construção e os testes do projeto.

O teste completo `desktop-lifecycle`, a verificação de segredos, a revisão de
dependências e a análise CodeQL participam da proteção da branch. Resolva
conversas pendentes e mantenha a branch atualizada com `main`. Não desative ou
enfraqueça uma verificação para integrar uma mudança que falha nela.

Integre por **merge commit**. Não use squash nem rebase de commits já publicados
com checkpoints de planejamento: especificações, tickets e evidências apontam
para esses SHAs. Leia `docs/agents/planning.md` quando o trabalho consumir um
marcador de Planning context.

Há um único mantenedor com escrita no início desta política. PRs continuam
obrigatórios, mas não exigem uma segunda aprovação humana. `CODEOWNERS` indica
o responsável; não concede acesso de escrita a contribuidores. O mantenedor
decide a integração após as verificações. Ao ampliar a equipe, revise a
quantidade de aprovações exigidas.

Dependabot propõe atualizações de Actions e das imagens ancestrais. Esses PRs
seguem as mesmas verificações. Versões e digests devem ser revisados juntos;
as atualizações não promovem `stable` automaticamente fora do fluxo de entrega.

As [configurações do repositório](docs/repository-security.md) documentam as
proteções e os arquivos que as representam.
