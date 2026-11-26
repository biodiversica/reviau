# Revisão de Segmentos via SSH

*[English](../en/ssh.md) · Português (Brasil)*

Quando uma pasta remota é indicada, todas as operações são realizadas via SFTP: a
listagem da pasta, a leitura dos clipes, a movimentação para as pastas de
veredito e a gravação do registro e da tabela de anotações. Os clipes são
armazenados localmente em cache à medida que são abertos, de modo que o retorno a
um clipe anterior dispensa novo download.

```bash
reviau ssh://usuario@servidor:22/dados/segmentos
reviau servidor:/dados/segmentos           # endereço no estilo scp
reviau ssh://servidor/dados/segmentos --ssh-key ~/.ssh/id_campo
```

Uma pasta remota também pode ser digitada na caixa de pasta da interface;
consulte [Abertura de uma Pasta](reviewing.md#abertura-de-uma-pasta).

## Autenticação

O usuário e a porta são informados no endereço (`ssh://usuario@host:porta/caminho`)
ou obtidos de `~/.ssh/config`, juntamente com apelidos de host e arquivos de
identidade, e um agente SSH em execução é utilizado. Quando não é possível usar
uma chave nem um agente, a senha é lida da variável de ambiente
`REVIAU_SSH_PASSWORD`; ela nunca é aceita na linha de comando, onde ficaria
registrada no histórico do terminal. Uma chave de host desconhecida é recusada,
salvo se `--accept-new-host-key` for informado; `--known-hosts` acrescenta um
arquivo known_hosts a ser considerado confiável.

## O que É Gravado na Máquina Remota

Nada é gravado fora da pasta `reviau/` (ou da pasta de `--output`), e nenhum
clipe é apagado: os clipes revisados são apenas movidos da pasta de segmentos
para ela. `--cache-dir` define onde as cópias locais dos clipes são mantidas
(por padrão, numa pasta temporária).
