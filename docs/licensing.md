# Licenciamento e distribuição

O código original e a documentação da Electivus neste repositório usam a
[licença MIT](../LICENSE), escolhida pelo responsável pelo projeto em
2026-09-18. Preserve o aviso de copyright e o texto da licença nas cópias
distribuídas. A licença permite reutilização comercial e modificações, sem
garantia do software.

A licença MIT do projeto não substitui as licenças dos componentes de terceiros:

- O perfil `seccomp.json` deriva do Moby, sob Apache 2.0. Sua origem e alterações
  estão em [THIRD-PARTY.md](../cmd/workstation/THIRD-PARTY.md), e o texto da licença
  está em [MOBY-LICENSE](../cmd/workstation/MOBY-LICENSE).
- O compilador e a biblioteca padrão Go mantêm a licença fornecida pela
  distribuição oficial. O build copia esse texto para `licenses/GO-LICENSE` no
  pacote de comandos, junto de `ELECTIVUS-LICENSE`, `MOBY-LICENSE` e
  `THIRD-PARTY.md`. A imagem conserva esses avisos em
  `/opt/electivus/windows/licenses`.
- A imagem ancestral [LinuxServer Webtop](https://github.com/linuxserver/docker-webtop)
  e os pacotes Arch/KDE, Oh My Zsh e plugins conservam seus avisos e licenças.
  Consulte os respectivos projetos, os metadados de pacotes e os avisos
  instalados. A imagem agrega componentes com diferentes licenças; não se deve
  apresentar todo o seu conteúdo como exclusivamente MIT.
- Google Chrome, VS Code Stable/Insiders e as extensões conservam os termos dos
  fornecedores. Seus binários são baixados durante o preparo da workstation,
  para o volume pessoal, e não integram as camadas construídas pelos Dockerfiles
  deste projeto. A disponibilidade do instalador não concede direitos extras
  de redistribuição desses produtos.

A publicação do código é independente da aprovação e publicação de imagens.
Os [critérios das candidatas](candidates.md), a distribuição no Docker Hub e a
validação real em Hyper-V continuam com seus próprios resultados e pendências.
