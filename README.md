# RPGWiki

This project provides a simple desktop wiki for managing RPG campaigns and worlds.

## Features
- Load separate world and campaign directories of Markdown files.
- Automatically build a keyword map from Markdown headers using special rules.
  A header must contain a symbol such as `!`, `*`, `foo/s` or `/` to create
  keywords. Plain headers without symbols are ignored.
- Clickable links inside the text area jump to linked files and sections.
- Persistent configuration for recently loaded folders and case sensitivity.
- Search headers via `File -> Search` or by pressing <kbd>Space</kbd> or
  <kbd>Up</kbd> during normal use.

## Running
Install Python 3.11+ and `PyQt5` then run the application with:

```bash
python main.py
```

You can also run it as a module:

```bash
python -m rpgwiki
```

Note that the GUI requires a display environment (PyQt5).
