import tkinter as tk
from tkinter import messagebox
import os
from win32com.shell import shell, shellcon
import shutil


class Tooltip:
    """Dica flutuante com atraso."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.timer = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.timer = self.widget.after(800, self.show_tooltip)

    def on_leave(self, event):
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def show_tooltip(self):
        x = self.widget.winfo_rootx() + 5
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes("-topmost", True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("TkDefaultFont", 9),
            padx=6,
            pady=2
        )
        label.pack()


def format_size(bytes_):
    """Formata tamanho em bytes para KB, MB, GB."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_ < 1024.0:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024.0
    return f"{bytes_:.1f} TB"


def delete_permanently(path, frame=None):
    """Exclui permanentemente arquivo ou pasta."""
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        if frame:
            frame.destroy()
    except Exception as e:
        messagebox.showerror("Erro ao excluir", f"Não foi possível excluir:\n{str(e)}")


def create_item_frame(parent, item, level=0):
    """Cria o frame para um item com hover e cores escuras."""
    container = tk.Frame(parent, bg="white")
    container.pack(fill="x", expand=True)

    # Frame principal do item
    frame = tk.Frame(container, height=26, bg="white")
    frame.pack(fill="x", expand=True, pady=1)
    frame.pack_propagate(False)

    # Cores
    BG_NORMAL = "white"
    BG_HOVER = "#f0f8ff"
    FG_NAME = "#cc0000"
    FG_SIZE = "#0055aa"
    FG_EXT = "#007700"

    # Lista de widgets que mudam de cor no hover
    hoverable_widgets = [frame]

    # Conteúdo esquerdo com indentação
    content_frame = tk.Frame(frame, bg=BG_NORMAL)
    content_frame.pack(side="left", fill="x", expand=True, padx=(level * 18, 0))
    hoverable_widgets.append(content_frame)

    # Setinha de expansão
    if not item["is_file"]:
        expand_var = tk.BooleanVar(value=False)
        arrow_label = tk.Label(content_frame, text="▶", width=2, bg=BG_NORMAL, font=("Arial", 10))
        arrow_label.pack(side="left")
        hoverable_widgets.append(arrow_label)

        def toggle():
            if expand_var.get():
                inner_content_frame.pack_forget()
                arrow_label.config(text="▶")
            else:
                inner_content_frame.pack(fill="x", expand=True)
                arrow_label.config(text="▼")
            expand_var.set(not expand_var.get())

        arrow_label.bind("<Button-1>", lambda e: toggle())
    else:
        arrow_label = tk.Label(content_frame, text="", width=2, bg=BG_NORMAL)
        arrow_label.pack(side="left")
        hoverable_widgets.append(arrow_label)

    # Nome
    name_label = tk.Label(
        content_frame,
        text=item["name"],
        fg=FG_NAME,
        bg=BG_NORMAL,
        font=("Arial", 9)
    )
    name_label.pack(side="left", padx=(4, 8))
    hoverable_widgets.append(name_label)
    Tooltip(name_label, item["path"])

    # Tamanho
    size_label = tk.Label(
        content_frame,
        text=format_size(item["size"]),
        fg=FG_SIZE,
        bg=BG_NORMAL,
        font=("Arial", 9)
    )
    size_label.pack(side="left", padx=(0, 8))
    hoverable_widgets.append(size_label)

    # Extensão (só para arquivos)
    if item["is_file"]:
        ext_label = tk.Label(
            content_frame,
            text=item["ext"],
            fg=FG_EXT,
            bg=BG_NORMAL,
            font=("Arial", 9)
        )
        ext_label.pack(side="left", padx=(0, 8))
        hoverable_widgets.append(ext_label)

    # Botão de exclusão
    btn_frame = tk.Frame(frame, bg=BG_NORMAL)
    btn_frame.pack(side="right", padx=6)
    hoverable_widgets.append(btn_frame)

    del_btn = tk.Button(
        btn_frame,
        text="X",
        width=2,
        font=("Arial", 9, "bold"),
        fg="red",
        relief="flat",
        overrelief="solid",
        activebackground="#ff4444",
        activeforeground="white",
        command=lambda: delete_permanently(item["path"], container)
    )
    del_btn.pack()
    Tooltip(del_btn, "Excluir permanentemente")

    BTN_FG_NORMAL = "red"
    BTN_FG_HOVER = "white"
    BTN_BG_HOVER = "#ff0000"
    BTN_BG_NORMAL = del_btn.cget("bg")

    def on_enter_btn(e):
        del_btn.config(fg=BTN_FG_HOVER, bg=BTN_BG_HOVER)

    def on_leave_btn(e):
        del_btn.config(fg=BTN_FG_NORMAL, bg=BTN_BG_NORMAL)

    del_btn.bind("<Enter>", on_enter_btn)
    del_btn.bind("<Leave>", on_leave_btn)
    btn_frame.bind("<Enter>", on_enter_btn)
    btn_frame.bind("<Leave>", on_leave_btn)

    # Funções de hover para o item inteiro
    def on_enter_item(e):
        for widget in hoverable_widgets:
            widget.config(bg=BG_HOVER)

    def on_leave_item(e):
        for widget in hoverable_widgets:
            widget.config(bg=BG_NORMAL)

    # Aplica hover em todos os elementos do item
    for widget in hoverable_widgets:
        widget.bind("<Enter>", on_enter_item)
        widget.bind("<Leave>", on_leave_item)

    # Subitens (se for pasta)
    if not item["is_file"]:
        inner_content_frame = tk.Frame(container, bg="white")
        subitems = list_trash_items_in_folder(item["path"])
        for subitem in subitems:
            create_item_frame(inner_content_frame, subitem, level=level + 1)


# === Funções de sistema (mantidas) ===
def get_trash_items():
    items = []
    desktop = shell.SHGetDesktopFolder()
    pidl = shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_BITBUCKET)
    folder = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)
    enum = folder.EnumObjects(0, shellcon.SHCONTF_FOLDERS | shellcon.SHCONTF_NONFOLDERS)

    while True:
        chunk = enum.Next(1)
        if not chunk:
            break
        pidl_item = chunk[0]
        name = folder.GetDisplayNameOf(pidl_item, shellcon.SHGDN_NORMAL)
        full_path = folder.GetDisplayNameOf(pidl_item, shellcon.SHGDN_FORPARSING)
        is_folder = bool(folder.GetAttributesOf([pidl_item], shellcon.SFGAO_FOLDER) & shellcon.SFGAO_FOLDER)
        is_file = not is_folder
        ext = os.path.splitext(name)[1] if is_file else ""
        size = get_item_size(full_path)
        items.append({
            "name": name,
            "size": size,
            "ext": ext,
            "path": full_path,
            "is_file": is_file
        })
    return items


def get_item_size(path):
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except:
            return 0
    elif os.path.isdir(path):
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total += os.path.getsize(file_path)
                    except:
                        continue
        except:
            pass
        return total
    return 0


def list_trash_items_in_folder(path):
    items = []
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            is_file = os.path.isfile(full_path)
            ext = os.path.splitext(entry)[1] if is_file else ""
            size = get_item_size(full_path)
            items.append({
                "name": entry,
                "size": size,
                "ext": ext,
                "path": full_path,
                "is_file": is_file
            })
    except:
        pass
    return items


def main():
    root = tk.Tk()
    root.geometry("720x500")
    root.title("Lixeira do Windows")

    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
    v_scroll = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame")

    def resize_frame(event):
        canvas_width = event.width
        canvas.itemconfig("frame", width=canvas_width)

    canvas.bind("<Configure>", resize_frame)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    trash_items = get_trash_items()
    if not trash_items:
        tk.Label(scrollable_frame, text="A lixeira está vazia.", fg="gray", bg="white", font=("Arial", 10)).pack(pady=30)
    else:
        for item in trash_items:
            create_item_frame(scrollable_frame, item)

    root.mainloop()


if __name__ == "__main__": main()
