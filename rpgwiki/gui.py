import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict
from .parser import scan_folder, KeywordTarget
from .config import Config, load_config, save_config

class WikiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RPG Wiki")
        self.geometry('1000x600')

        self.config_data: Config = load_config()
        self.keyword_map: Dict[str, KeywordTarget] = {}

        self._build_gui()
        self._load_saved_folders()

    def _build_gui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Load World Folder', command=self.load_world)
        file_menu.add_command(label='Load Campaign Folder', command=self.load_campaign)
        file_menu.add_separator()
        file_menu.add_command(label='Rescan', command=self.rescan)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.destroy)
        menubar.add_cascade(label='File', menu=file_menu)
        self.config(menu=menubar)

        # Treeview navigation
        self.tree = ttk.Treeview(self)
        self.tree.bind('<<TreeviewOpen>>', self._on_open_node)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.grid(row=0, column=0, sticky='ns')

        # Scroll for tree
        tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=0, column=0, sticky='nse')

        # Content text
        self.text = tk.Text(self, wrap='word')
        self.text.grid(row=0, column=1, sticky='nsew')
        self.text.tag_config('link', foreground='blue', underline=1)
        self.text.tag_bind('link', '<Button-1>', self._on_link_click)

        text_scroll = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.text.configure(yscrollcommand=text_scroll.set)
        text_scroll.grid(row=0, column=2, sticky='ns')

    def _load_saved_folders(self):
        if self.config_data.world_dir:
            self._add_folder_to_tree(self.config_data.world_dir, 'World')
        if self.config_data.campaign_dir:
            self._add_folder_to_tree(self.config_data.campaign_dir, 'Campaign')
        self.rescan()

    def _add_folder_to_tree(self, folder: str, tag: str):
        node = self.tree.insert('', 'end', text=f'{tag}: {folder}', open=True, values=(folder, 'dir'))
        self._populate_tree(node, folder)

    def _populate_tree(self, parent, path):
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                node = self.tree.insert(parent, 'end', text=entry, values=(full, 'dir'))
                # optionally populate on open
            elif entry.lower().endswith('.md'):
                self.tree.insert(parent, 'end', text=entry, values=(full, 'file'))

    def _on_open_node(self, event):
        item = self.tree.focus()
        path, typ = self.tree.item(item, 'values')
        if typ == 'dir':
            if not self.tree.get_children(item):
                self._populate_tree(item, path)

    def _on_select(self, event):
        item = self.tree.focus()
        if not item:
            return
        path, typ = self.tree.item(item, 'values')
        if typ == 'file':
            self.open_file(path)

    def load_world(self):
        folder = filedialog.askdirectory()
        if folder:
            self.config_data.world_dir = folder
            self.tree.delete(*self.tree.get_children())
            self._add_folder_to_tree(folder, 'World')
            if self.config_data.campaign_dir:
                self._add_folder_to_tree(self.config_data.campaign_dir, 'Campaign')
            self.rescan()
            save_config(self.config_data)

    def load_campaign(self):
        folder = filedialog.askdirectory()
        if folder:
            self.config_data.campaign_dir = folder
            self.tree.delete(*self.tree.get_children())
            if self.config_data.world_dir:
                self._add_folder_to_tree(self.config_data.world_dir, 'World')
            self._add_folder_to_tree(folder, 'Campaign')
            self.rescan()
            save_config(self.config_data)

    def rescan(self):
        self.keyword_map.clear()
        if self.config_data.world_dir:
            self.keyword_map.update(scan_folder(self.config_data.world_dir))
        if self.config_data.campaign_dir:
            camp_map = scan_folder(self.config_data.campaign_dir)
            # campaign keywords override world
            self.keyword_map.update(camp_map)

    def open_file(self, path: str):
        self.text.delete('1.0', tk.END)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror('Error', str(e))
            return
        self.text.insert('1.0', content)
        self._apply_links(content)

    def _apply_links(self, content: str):
        self.text.tag_remove('link', '1.0', tk.END)
        # sort keywords by length descending
        keywords = sorted(self.keyword_map.keys(), key=len, reverse=True)
        case = 0 if self.config_data.case_sensitive else 1
        for kw in keywords:
            idx = '1.0'
            while True:
                idx = self.text.search(kw, idx, nocase=case, stopindex=tk.END)
                if not idx:
                    break
                end = f"{idx}+{len(kw)}c"
                self.text.tag_add('link', idx, end)
                self.text.tag_bind('link', '<Enter>', lambda e: self.text.config(cursor="hand2"))
                self.text.tag_bind('link', '<Leave>', lambda e: self.text.config(cursor=""))
                idx = end

    def _on_link_click(self, event):
        index = self.text.index("@%d,%d" % (event.x, event.y))
        for tag in self.text.tag_names(index):
            if tag == 'link':
                word = self.text.get(index, f"{index} wordend")
                target = self.keyword_map.get(word)
                if not target and not self.config_data.case_sensitive:
                    lower = word.lower()
                    for kw, tgt in self.keyword_map.items():
                        if kw.lower() == lower:
                            target = tgt
                            break
                if target:
                    self.open_file(target.file)
                    self.text.see(f"{target.line}.0")
                break


def main():
    app = WikiApp()
    app.mainloop()


if __name__ == '__main__':
    main()
