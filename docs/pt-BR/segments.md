# Como um Segmento É Lido

*[English](../en/segments.md) · Português (Brasil)*

As informações de um segmento provêm de duas fontes independentes, ambas
configuráveis nas [configurações de leitura](reading-settings.md).

## A Pasta Fornece o Rótulo

Um conjunto em revisão costuma ser organizado com uma pasta por classe, de modo
que a pasta em que o clipe se encontra é o rótulo que ele carrega:

```
segmentos/
├── PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav   → rótulo BOAALB
├── PONTO_A/PHYLUT/PONTO_A_20240115_061500_3.5_8.5_det2.wav     → rótulo PHYLUT
└── chuva/POCA_20240116_200000_5.0_10.0_det4.wav                → rótulo chuva
```

As pastas acima do rótulo são preservadas: `2024/campo/PONTO_A/BOAALB/` rotula o
clipe como `BOAALB` e mantém as três pastas acima dele. Um clipe situado
diretamente na pasta de segmentos não tem rótulo.

## Conjuntos com a Pasta da Classe no Topo

Alguns conjuntos são organizados de forma inversa, com os pontos *dentro* de
cada pasta de classe. Nesse caso, o **nível do rótulo**, nas
[configurações de leitura](reading-settings.md), indica qual nível carrega o
rótulo, contado a partir da pasta de segmentos. As pastas abaixo desse nível são
lidas, mas não mantidas: não são oferecidas como rótulos, e o clipe revisado é
arquivado apenas sob o seu rótulo, uma vez que o ponto e a data já constam no
nome do arquivo.

```
segmentos/                             # nível do rótulo 1
├── BOAALB/PONTO_A/20240115/clipe.wav  → rótulo BOAALB; as duas pastas abaixo não são mantidas
├── BOAALB/POCA/clipe.wav              → rótulo BOAALB
└── PHYLUT/clipe.wav                   → rótulo PHYLUT (menos profundo que o nível, ainda rotulado)
```

## O Nome do Arquivo Fornece as Demais Informações

Por padrão, o nome é lido como

```
[ponto]_[AAAAMMDD]_[HHMMSS]_[início]_[fim]_*
      PONTO_A_20240115_053000_12.0_17.0_det1.wav
```

- O ponto pode conter sublinhados; a leitura é ancorada na data e na hora.
- `início` e `fim` indicam a posição do clipe, em segundos, na gravação da qual
  ele foi recortado. As duas formas são aceitas: `12.0_17.0` e `12.0-17.0s`.
- `_*` corresponde a qualquer texto restante, exibido na interface como *Outros*.
- Todas as partes após o ponto são opcionais, e **um nome que não corresponda a
  nenhuma parte do padrão pode ainda assim ser revisado**; a interface apenas
  exibe menos informações sobre ele.

Conjuntos nomeados segundo outra convenção podem ser descritos nas
[configurações de leitura](reading-settings.md).
