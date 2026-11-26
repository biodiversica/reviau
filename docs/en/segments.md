# How a Segment Is Read

*English · [Português (Brasil)](../pt-BR/segments.md)*

Information about a segment is taken from two independent sources, both of which
are configurable in the [reading settings](reading-settings.md).

## The Folder Provides the Label

A collection under review is normally organised with one folder per class, so
the folder containing a clip is the label it currently carries:

```
segments/
├── PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav   → label BOAALB
├── PONTO_A/PHYLUT/PONTO_A_20240115_061500_3.5_8.5_det2.wav     → label PHYLUT
└── chuva/POCA_20240116_200000_5.0_10.0_det4.wav                → label chuva
```

Folders above the label are preserved: `2024/campo/PONTO_A/BOAALB/` labels the
clip `BOAALB` and retains the three folders above it. A clip placed directly in
the segments folder has no label.

## Collections with the Class Folder at the Top

Some collections are organised the other way round, with the sites *inside*
each class folder. In that case, the **label depth** in the
[reading settings](reading-settings.md) specifies which level carries the
label, counting down from the segments folder. The folders below that level are
read but not retained: they are not offered as labels, and a reviewed clip is
filed under its label alone, since the site and the date are already present in
the file name.

```
segments/                          # label depth 1
├── BOAALB/PONTO_A/20240115/clip.wav  → label BOAALB; the two folders below are not retained
├── BOAALB/POCA/clip.wav              → label BOAALB
└── PHYLUT/clip.wav                   → label PHYLUT (shallower than the depth, still labelled)
```

## The File Name Provides the Remaining Information

By default it is read as

```
[site]_[YYYYMMDD]_[HHMMSS]_[start]_[end]_*
     PONTO_A_20240115_053000_12.0_17.0_det1.wav
```

- `site` may contain underscores; the match is anchored on the date and time.
- `start` and `end` give the position of the clip, in seconds, within the
  recording from which it was cut. Both forms are accepted: `12.0_17.0` and
  `12.0-17.0s`.
- `_*` covers any remaining text, which the interface displays as *Other*.
- Every part after the site is optional, and **a name that matches no part of
  the pattern can still be reviewed**; the interface simply displays less
  information about it.

Collections named according to another convention can be described in the
[reading settings](reading-settings.md).
