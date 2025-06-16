# RPGWiki

This project provides a simple desktop wiki for managing RPG campaigns and worlds.

## Features
- Load separate world and campaign directories of Markdown files.
- Automatically build a keyword map from Markdown headers using special rules.
- Clickable links inside the text area jump to linked files and sections.
- Persistent configuration for recently loaded folders and case sensitivity.

## Running
Install Python 3.11+ and run the application with:

```bash
python main.py
```

You can also run it as a module:

```bash
python -m rpgwiki
```

Note that the GUI requires a display environment (Tkinter).
