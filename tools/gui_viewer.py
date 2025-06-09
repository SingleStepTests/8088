import json
import gzip
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def load_test_file(filename):
    try:
        if filename.endswith('.gz'):
            with gzip.open(filename, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return data
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to load file:\n{e}")
        return None

def highlight_changes(initial_regs, final_regs):
    regs = set(initial_regs.keys()) | set(final_regs.keys())
    changes = {}
    for r in regs:
        init_val = initial_regs.get(r, None)
        final_val = final_regs.get(r, init_val)  # fallback to initial if missing
        changed = (init_val != final_val)
        changes[r] = (init_val, final_val, changed)
    return changes

class TestViewerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Test Viewer")
        self.geometry("700x400")

        self.test_data = []

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Test File...", command=self.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

        columns = ("idx", "name")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.heading("idx", text="Index", anchor="e")
        self.tree.heading("name", text="Disassembly Name", anchor="w")
        self.tree.column("idx", width=60, anchor='e')   # right-align index column
        self.tree.column("name", width=600, anchor='w')

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_item_double_click)

    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Open JSON or JSON.GZ Test File",
            filetypes=[("JSON files", "*.json"), ("Gzipped JSON", "*.json.gz"), ("All files", "*.*")]
        )
        if not filename:
            return

        data = load_test_file(filename)
        if data is None:
            return

        self.test_data = data
        self.populate_test_list()

    def populate_test_list(self):
        self.tree.delete(*self.tree.get_children())
        for i, test in enumerate(self.test_data):
            name = test.get("name", "")
            self.tree.insert("", "end", iid=str(i), values=(i, name))

    def on_item_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        try:
            idx = int(item_id)
        except ValueError:
            return
        if idx < 0 or idx >= len(self.test_data):
            return
        test = self.test_data[idx]
        DetailDialog(self, test, idx, test.get("name", ""))

class DetailDialog(tk.Toplevel):
    def __init__(self, parent, test_entry, index, disasm_name):
        super().__init__(parent)
        self.title(f"Test Detail - idx {index}: {disasm_name}")
        self.geometry("900x600")
        self.test_entry = test_entry

        top_frame = ttk.Frame(self)
        bottom_frame = ttk.Frame(self)

        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=5, pady=0)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_registers_view(top_frame)
        self.create_queue_view(top_frame)
        self.create_cycles_view(bottom_frame)

    def create_registers_view(self, parent):
        initial_regs = self.test_entry.get("initial", {}).get("regs", {})
        final_regs = self.test_entry.get("final", {}).get("regs", {})
        changes = highlight_changes(initial_regs, final_regs)

        label = ttk.Label(parent, text="Registers", font=('Arial', 10, 'bold'))
        label.pack(anchor="w", pady=(0,5))

        reg_lines = [
            ["ax", "bx", "cx", "dx"],
            ["sp", "bp", "si", "di"],
            ["cs", "ds", "es", "ss"],
            ["ip", "flags"]
        ]

        font = ('Courier New', 11)
        fg_init = 'black'

        # Initial registers multiline text string
        init_lines = []
        for line_regs in reg_lines:
            parts = []
            for r in line_regs:
                val = initial_regs.get(r, 0)
                parts.append(f"{r.upper()}: {val:04X}")
            init_lines.append(" ".join(parts))
        init_text = "\n".join(init_lines)

        container = ttk.Frame(parent)
        container.pack(fill=tk.X)

        # Initial regs on left: simple Label
        init_frame = ttk.Frame(container)
        init_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,2))
        ttk.Label(init_frame, text="Initial Registers", font=('Arial', 10, 'underline')).pack(anchor="w", pady=(0,2))
        lbl_init = tk.Label(init_frame, text=init_text, font=font, justify=tk.LEFT, fg=fg_init)
        lbl_init.pack(anchor="w")

        # Final regs on right: Text widget with tags
        final_frame = ttk.Frame(container)
        final_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(final_frame, text="Final Registers", font=('Arial', 10, 'underline')).pack(anchor="w", pady=(0,2))

        txt_final = tk.Text(final_frame, font=font, height=8, width=40)
        txt_final.pack(anchor="w", fill=tk.BOTH, expand=True)
        txt_final.configure(
            bg=lbl_init.cget("background"),
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            cursor="arrow"
        )

        for line_regs in reg_lines:
            line_text = ""
            color_spans = []  # list of tuples (start_idx, end_idx) for changed values

            cursor = 0
            for r in line_regs:
                init_val = initial_regs.get(r, 0)
                final_val = final_regs.get(r, init_val)
                changed = (init_val != final_val)
                reg_str = f"{r.upper()}: {final_val:04X}"
                line_text += reg_str + " "
                # Mark the value part (after colon and space) if changed
                if changed:
                    # value starts at colon idx + 2 in reg_str
                    value_start = cursor + len(r) + 2
                    value_end = value_start + 4
                    color_spans.append((value_start, value_end))
                cursor += len(reg_str) + 1  # +1 for the space

            # Insert line and newline
            start_index = txt_final.index(tk.INSERT)
            txt_final.insert(tk.END, line_text.rstrip() + "\n")
            end_index = txt_final.index(tk.INSERT)

            # Apply red tag to changed values only
            for start, end in color_spans:
                start_idx = f"{start_index}+{start}c"
                end_idx = f"{start_index}+{end}c"
                txt_final.tag_add("changed", start_idx, end_idx)

        # Configure tag styles
        txt_final.tag_config("changed", foreground="red")

        txt_final.configure(state=tk.DISABLED)

    def create_queue_view(self, parent):
        # Show initial and final queue states as hex bytes or "empty"
        initial_queue = self.test_entry.get("initial", {}).get("queue", [])
        final_queue = self.test_entry.get("final", {}).get("queue", [])

        def format_queue(q):
            if not q:
                return "empty"
            return " ".join(f"{b:02X}" for b in q)

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0,5))

        # Initial queue
        init_frame = ttk.Frame(frame)
        init_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
        ttk.Label(init_frame, text="Initial Queue", font=('Arial', 10, 'underline')).pack(anchor="w")
        lbl_init_q = tk.Label(init_frame, text=format_queue(initial_queue), font=('Courier New', 11), justify=tk.LEFT)
        lbl_init_q.pack(anchor="w")

        # Final queue
        final_frame = ttk.Frame(frame)
        final_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(final_frame, text="Final Queue", font=('Arial', 10, 'underline')).pack(anchor="w")
        lbl_final_q = tk.Label(final_frame, text=format_queue(final_queue), font=('Courier New', 11), justify=tk.LEFT)
        lbl_final_q.pack(anchor="w")
        
    def create_cycles_view(self, parent):
        label = ttk.Label(parent, text="Cycle States", font=('Arial', 10, 'bold'))
        label.pack(anchor="w")

        columns = ["cycle", "ale", "addr", "seg", "mem", "io", "bhe", "data", "bus", "t", "qop", "qb"]
        fill_col = "fill"
        all_columns = columns + [fill_col]

        widths = {
            "cycle": 50,
            "ale": 20,
            "addr": 80,
            "seg": 40,
            "mem": 40,
            "io": 40,
            "bhe": 20,
            "data": 40,
            "bus": 40,
            "t": 40,
            "qop": 40,
            "qb": 40,
            fill_col: 0,  # filler column
        }

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=all_columns, show="headings")
        style = ttk.Style()
        style.configure("Treeview", font=('Courier New', 10))

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths[col], anchor='center', stretch=False)

        for col in columns:
            if col == "cycle" or col == "data":
                tree.column(col, width=widths[col], anchor='e', stretch=False)  # right-align cycle number
            else:
                tree.column(col, width=widths[col], anchor='center', stretch=False)            

        # Add the filler column last, no heading, stretch=True to fill space
        tree.heading(fill_col, text="")
        tree.column(fill_col, width=0, stretch=True)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        cycles = self.test_entry.get("cycles", [])
        for idx, c in enumerate(cycles):
            row = [str(idx)]  # cycle number as decimal string, no padding
            for i, val in enumerate(c):
                if isinstance(val, int):
                    if i == 0:  # ale, decimal string
                        row.append(str(val))
                    elif i == 1:  # addr, pad 5 hex digits
                        row.append(f"{val:05X}")
                    elif i == 5:  # bhe, pad 1 hex digit
                        row.append(f"{val:X}")
                    elif i == 6:  # data, dynamically pad it
                        if val > 255:
                            row.append(f"{val:04X}")
                        else:
                            row.append(f"{val:02X}")
                    elif i == 10:  # qb, pad 2 hex digits
                        row.append(f"{val:02X}")
                    else:
                        row.append(f"{val:02X}")
                else:
                    row.append(str(val))
            while len(row) < len(columns):
                row.append("")
            row.append("")  # filler empty value for last column
            tree.insert("", "end", values=row)

if __name__ == "__main__":
    app = TestViewerApp()
    app.mainloop()