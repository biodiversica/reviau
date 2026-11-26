# Reviewing in the Browser

*English · [Português (Brasil)](../pt-BR/reviewing.md)*

## Opening a Folder

The **folder box** at the top of the page shows which segments folder is under
review. Typing another path and pressing <kbd>Enter</kbd>, or selecting a folder
with **Browse…**, opens that folder in place of the current one without
restarting the command. When the command is started without a `SEGMENTS`
folder, the page displays only the folder box.

- The folder box accepts the same paths as the command line: a local folder, a
  path beginning with `~/`, or `ssh://user@host/path` for a remote folder, which
  is reached with the SSH settings of the command line (`--ssh-key`,
  `~/.ssh/config`, the SSH agent, and so on); see [SSH](ssh.md).
- Every folder opened receives the options with which the command was started,
  such as `--output`, `--labels-file` and `--annotations`. How its names are
  read is the folder's own setting; see [Reading Settings](reading-settings.md).
- **Opening a folder does not write to it.** The `reviau/` folder is created when
  the first segment is reviewed, so a folder opened by mistake, through a typing
  error or one level too high, is left unchanged.
- A `reviau/` folder that holds the results of a review cannot itself be opened
  as a segments folder, since its reviewed clips would be offered for review a
  second time; the folder that contains it is opened instead.
- A folder that cannot be opened is rejected with an explanation, and the review
  in progress is not affected.
- **Browse…** lists the folders of the machine on which the reviewer runs, which
  is the machine that reads the clips; when the interface is served to another
  computer, this is not the computer running the browser. Folders that contain
  clips are marked with ♪. Remote `ssh://` folders cannot be browsed and must be
  typed.
- Recently opened folders are suggested while typing. This history is stored in
  the browser.
- When the filename pattern recognises only some of the names in the folder just
  opened, a notice below the folder box reports it, together with one name that
  was not recognised.

## Controls

| Control | Function |
| --- | --- |
| **Label buttons** | Labels for anything *else* present in the clip, or for what the clip actually contains. Each segment starts with no label selected; clicking a label selects it, and clicking it again deselects it. The button of the predicted label is marked **◆ predicted** and cannot be selected: the prediction is assessed with Correct or Incorrect instead. <kbd>1</kbd>…<kbd>9</kbd> select the first nine labels. |
| **✔ Correct** | The prediction is correct. The segment is saved with the prediction and any selected label, for example a second species vocalising at the same time. The button shows what will be saved: *✔ Correct + PHYLUT*. |
| **✘ Incorrect** | The prediction is incorrect. The segment is saved with the selected labels, which describe what the clip actually contains, or, if none is selected, as containing no label from the list. The button shows which applies: *✘ Incorrect → TURDRU* or *✘ Incorrect · no label from the list*. |
| **? Uncertain** | The clip cannot be assessed. It is filed under `uncertain/` and excluded from the correct and incorrect counts and from the annotation table. |
| **← Previous / Next →** | Move between segments without recording a decision. |
| **Type / Minimum (Hz) / Maximum (Hz) / Floor (dB)** | Redraw the spectrogram immediately, on a mel, linear or logarithmic frequency axis. The audio player is not affected, so playback continues while the view changes. The view is stored in the browser. |
| **✎** | Edit the label list: each button displays a **×** that removes it, and the field below adds a new label. Changes are saved to the [label list](reviau-folder.md#the-label-list) file (`reviau/labels.txt` by default). |
| **⚙** | Open the [reading settings](reading-settings.md) of the folder: filename pattern, date-time format, label source and label depth. |
| **⟳** | Rescan the folder, for example after new segments have been added. |
| **Language** | Switch the interface between English and Português. |
| **◐ / ☀ / ☾** | Theme: system default, light or dark; each click selects the next. The selected theme is stored in the browser. The spectrogram keeps its colours in both themes. |

## How the Outcome Is Decided

The prediction is the question, and Correct or Incorrect is the answer; the label
buttons only add what else is present. No label is ever selected in advance, so a
segment rejected without further selection is saved as containing no label from
the list, and never with a label carried over from the previous clip. When a
segment has no prediction to assess, a single **✔ Save** button files the
selected labels. The server derives the outcome from the labels it receives,
according to a single rule:

| Labels saved | Outcome |
| --- | --- |
| the prediction | correct |
| the prediction and other labels | correct (the other labels are recorded as *added*) |
| other labels only | incorrect; the clip contains those labels |
| none | incorrect; the clip contains no label from the list |
| any, with Uncertain | uncertain |

Once reviewed, the clip leaves the list and the next one is shown
automatically.

Several labels may be assigned to one segment, for example when two species
vocalise at the same time. This is the default behaviour; `--no-multi-label`
restricts each segment to a single label.

Where each reviewed clip goes, and what is recorded about it, is described in
[The reviau Folder](reviau-folder.md).

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| <kbd>←</kbd> / <kbd>→</kbd> | Previous / next segment |
| <kbd>T</kbd> | Correct |
| <kbd>F</kbd> | Incorrect |
| <kbd>U</kbd> | Uncertain |
| <kbd>1</kbd>…<kbd>9</kbd> | Select or deselect the first nine labels |
| <kbd>Space</kbd> | Play or pause the audio |
