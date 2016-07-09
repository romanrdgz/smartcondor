import Tkinter as tk
import tkMessageBox


class SelectionList(tk.Tk):
    def __init__(self, list_of_options):
        tk.Tk.__init__(self, None)
        self.title('Select an option')
        self.selection = None
        self.initialize(list_of_options)

    def initialize(self, list_of_options):
        frame = tk.LabelFrame(self, text='Select an option')
        frame.grid(
            row=0, columnspan=1, sticky='W', padx=5, pady=5, ipadx=5, ipady=5)
        self.listbox = tk.Listbox(self, width=25, height=10)
        self.listbox.grid(row=0, column=0, sticky='E', padx=5, pady=2)
        for opt in list_of_options:
            self.listbox.insert(tk.END, opt)
        self.listbox.bind('<Double-1>', self._get_selection)
        self.protocol('WM_DELETE_WINDOW', self._on_closing)

    def _get_selection(self, event):
        self.selection = self.listbox.get(self.listbox.curselection())
        self.destroy()

    def _on_closing(self):
        if tkMessageBox.askokcancel('Quit', 'Do you want to quit?'):
            self.destroy()
