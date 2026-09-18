# Segurança

## Relatar uma vulnerabilidade

Use o [relato privado do GitHub](https://github.com/Electivus/webtop-arch-kde-workstation/security/advisories/new).
Informe commit ou versão/digest, backend Docker, componente afetado, passos
mínimos e impacto observado. Use dados fictícios e remova tokens, certificados
privados, perfis, backups e informações de clientes. Não publique detalhes
exploráveis em uma issue comum enquanto o relato estiver sendo avaliado.

O projeto ainda está na fase de candidatas. Identifique a versão afetada; a
publicação de fontes ou um build bem-sucedido não comprova aceitação em Hyper-V.

## Sistema e limites de confiança

A workstation é um desktop Linux pessoal acessado pelo navegador do próprio
notebook Windows. O controlador nativo opera Docker Desktop e administra
instalação, aplicativos, rede, atualizações e backups. O endpoint foi projetado
para HTTPS em `127.0.0.1`, sem senha adicional, confiando na sessão do Windows.

Projetos, páginas web, dependências, downloads, pacotes AUR, arquivos de troca e
backups importados podem conter conteúdo hostil. Perfis e arquivos recebidos
não devem ganhar autoridade para modificar recursos de outras instalações.
Dados e credenciais pessoais pertencem ao estado local; fontes, imagens e
artefatos públicos de CI não devem incorporá-los.

O acesso ao socket Docker é uma funcionalidade explícita do produto e permite
controlar o engine do notebook. A workstation não oferece isolamento contra
programas que o usuário autorize a usar esse socket. Isso aumenta o impacto
potencial de uma execução de código obtida por um atacante e não é motivo
para descartar automaticamente esse tipo de relato.

## Propriedades que devem ser preservadas

- O desktop não deve ser publicado na rede externa por padrão. TLS e as
  verificações de integridade e autenticidade dos fornecedores devem permanecer
  ativos; certificados corporativos não devem desativar a validação existente.
- Certificados privados, credenciais Salesforce, proxies autenticados e perfis
  pessoais devem ficar fora das camadas, logs e artefatos públicos.
- Comandos de manutenção devem respeitar a identidade da instalação e não
  remover ou alterar containers, volumes e arquivos alheios.
- Dados de backup e caminhos de extração não devem permitir escrita fora do
  destino esperado. Falhas de validação devem preservar os dados atuais.
- Atualizações devem exigir ação explícita e o backup previsto, sem apresentar
  uma execução incompleta como bem-sucedida.
- PRs e seus arquivos são entrada não confiável. Workflows devem usar o mínimo
  de permissões e não executar código de forks com credenciais privilegiadas.

Essas são propriedades esperadas para implementação e revisão, não uma
declaração de que todos os controles foram comprovados em todos os ambientes.

## Avaliação dos relatos

Relate violações desses limites com o caminho de entrada, os privilégios
necessários e o impacto em dados ou recursos reais. A avaliação deve distinguir
controle intencional pelo usuário de ações obtidas sem sua autorização.
Dependências e imagens ancestrais mantêm seus próprios responsáveis, mas falhas
que afetem esta distribuição também podem ser comunicadas pelo canal privado.

O uso multiusuário e a exposição do desktop à internet não fazem parte do
modelo atual. Essa limitação não exclui falhas exploráveis no uso local
suportado. Não há exclusões gerais adicionais por classe de vulnerabilidade.
