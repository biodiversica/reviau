# Opções da Linha de Comando

*[English](../en/cli.md) · Português (Brasil)*

## Exemplos

```bash
# Iniciar sem pasta e abrir uma pelo navegador
reviau --lang pt-BR

# Abrir uma pasta local na inicialização, com a interface nesta máquina
reviau ~/segmentos --lang pt-BR

# Uma lista de rótulos compartilhada por todas as pastas e tabela de anotações
reviau ~/segmentos --lang pt-BR --labels-file ~/classes.txt --annotations

# Segmentos num servidor, revisados a partir de outro computador
reviau ssh://usuario@servidor/dados/segmentos --lang pt-BR

# Disponibilizar a interface para a rede (rede local, Tailscale, …)
reviau /dados/segmentos --host 0.0.0.0 --port 8765
```

O comando exibe um resumo e o endereço a ser aberto.

## Opções

```
reviau [SEGMENTOS] [OPÇÕES]

  SEGMENTOS                     Pasta a abrir na inicialização: caminho local, ou
                                ssh://[usuário@]host[:porta]/caminho. Opcional; a
                                pasta pode ser aberta, e trocada, no navegador

  -l, --lang TEXT               Idioma inicial da interface: en, pt-BR  [padrão: en]
      --labels-file TEXT        Local da lista de rótulos, um rótulo por linha.
                                Caminhos relativos ficam dentro da pasta reviau; um
                                caminho absoluto compartilha uma lista entre as
                                pastas  [padrão: <saída>/labels.txt]
      --no-multi-label          Limita cada segmento a um rótulo (por padrão, um
                                segmento pode receber vários rótulos)
      --annotations             Grava também a tabela de rótulos confirmados
      --annotations-path TEXT   Local da tabela  [padrão: <saída>/annotations.csv]

  -o, --output TEXT             Pasta em que os segmentos revisados, o reviews.csv,
                                o labels.txt e o settings.json são gravados
                                [padrão: <SEGMENTOS>/reviau]

      --host TEXT               Endereço de vinculação  [padrão: 127.0.0.1]
  -p, --port INTEGER            Porta  [padrão: 8765]
      --token TEXT              Token de acesso da interface
      --no-auth                 Disponibiliza a interface sem token de acesso
      --open / --no-open        Abre o navegador na inicialização  [padrão: abre]

      --ssh-key TEXT            Arquivo de chave privada para conexões SSH
      --known-hosts TEXT        Arquivo known_hosts adicional a ser considerado
                                confiável
      --accept-new-host-key     Aceita uma chave de host SSH desconhecida
      --cache-dir TEXT          Local do cache dos clipes remotos
                                [padrão: uma pasta temporária]

      --version                 Exibe a versão e encerra

  Ambiente: REVIAU_SSH_PASSWORD  Senha SSH, quando não é possível usar chave ou agente
```

O padrão de nome, o formato de data e hora, a origem do rótulo e o nível do
rótulo são definidos por pasta nas
[configurações de leitura](reading-settings.md), e a visualização do
espectrograma é definida na interface e armazenada no navegador.

| Assunto | Opções | Página |
| --- | --- | --- |
| Rótulos e tabela de anotações | `--labels-file`, `--no-multi-label`, `--annotations`, `--annotations-path` | [A Pasta reviau](reviau-folder.md) |
| Resultados em outro local | `--output` | [Gravação em Outro Local](reviau-folder.md#gravação-em-outro-local) |
| Pastas remotas | `--ssh-key`, `--known-hosts`, `--accept-new-host-key`, `--cache-dir` | [SSH](ssh.md) |
| Disponibilização para a rede | `--host`, `--port`, `--token`, `--no-auth`, `--no-open` | [Execução num Servidor](server.md) |
