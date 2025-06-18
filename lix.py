import tkinter as tk
from tkinter import messagebox, ttk
import winshell
import os
import win32clipboard
import win32con
from win32com.shell import shell, shellcon

class DicaFlutuante:
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.dica = None
        self.widget.bind("<Enter>", self.entrar)
        self.widget.bind("<Leave>", self.sair)
        self.widget.bind("<Motion>", self.sair)
        self.temporizador = None

    def entrar(self, evento=None):
        self.temporizador = self.widget.after(5000, self.mostrar_dica)

    def sair(self, evento=None):
        if self.temporizador:
            self.widget.after_cancel(self.temporizador)
            self.temporizador = None
        if self.dica:
            self.dica.destroy()
            self.dica = None

    def mostrar_dica(self):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.dica = tk.Toplevel(self.widget)
        self.dica.wm_overrideredirect(True)
        self.dica.wm_geometry(f"+{x}+{y}")

        rotulo = tk.Label(self.dica, text=self.texto, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        rotulo.pack()

def excluir_permanentemente(caminho_arquivo, frame_pai=None):
    try:
        if os.path.isfile(caminho_arquivo):
            os.remove(caminho_arquivo)
        else:
            # Usar rmdir /s/q para excluir pasta e conteúdo
            os.system(f'rmdir "{caminho_arquivo}" /s/q')
        
        # Atualizar a interface removendo o frame do item excluído
        if frame_pai:
            frame_pai.destroy()
            
    except Exception as erro:
        messagebox.showerror("Erro", str(erro))

def criar_frame_item(pai, item, nivel=0):
    # Container principal que agrupa o item e seu conteúdo (se for pasta)
    container = tk.Frame(pai)
    container.pack(fill="x", expand=True)

    # Frame do item (pasta ou arquivo)
    frame_item = tk.Frame(container, height=30, bd=1, relief="solid")
    frame_item.pack(fill="x", expand=True, padx=2+nivel*15, pady=1)

    # Frame para o conteúdo da pasta (inicialmente escondido)
    frame_conteudo = tk.Frame(container)
    
    # Frame para os elementos do item
    frame_elementos = tk.Frame(frame_item)
    frame_elementos.pack(side="left", fill="x", expand=True)
    
    # Expand/Collapse para pastas (apenas para pastas)
    if not item["eh_arquivo"]:
        expandido = tk.BooleanVar(value=False)
        botao_expandir = tk.Label(frame_elementos, text="▶", width=2)
        botao_expandir.pack(side="left")
        def alternar():
            if expandido.get():
                frame_conteudo.pack_forget()
                expandido.set(False)
                botao_expandir.config(text="▶")
            else:
                frame_conteudo.pack(fill="x", expand=True)
                expandido.set(True)
                botao_expandir.config(text="▼")
        botao_expandir.bind("<Button-1>", lambda e: alternar())
    else:
        tk.Label(frame_elementos, text="", width=2).pack(side="left")

    # Nome (vermelho) - apenas nome do arquivo
    rotulo_nome = tk.Label(frame_elementos, text=item["nome"], fg="red")
    rotulo_nome.pack(side="left", padx=(5, 10))
    # Adicionar dica flutuante com caminho completo
    DicaFlutuante(rotulo_nome, item["caminho"])

    # Tamanho (azul)
    rotulo_tamanho = tk.Label(frame_elementos, text=f"{item['tamanho']} bytes", fg="blue")
    rotulo_tamanho.pack(side="left", padx=(0, 10))

    # Extensão (verde, se for arquivo)
    rotulo_extensao = tk.Label(frame_elementos, text=item["extensao"], fg="green")
    rotulo_extensao.pack(side="left", padx=(0, 10))

    # Frame para os botões
    frame_botoes = tk.Frame(frame_item)
    frame_botoes.pack(side="right", fill="y")

    # Botão excluir com ícone
    botao_excluir = tk.Button(frame_botoes, text="🗑️ Excluir", 
                             command=lambda: excluir_permanentemente(item["caminho"], container))
    botao_excluir.pack(side="right", padx=5)

    # Subitens se for pasta
    if not item["eh_arquivo"]:
        subitens = listar_itens_pasta_winapi(item["caminho"])
        for subitem in subitens:
            criar_frame_item(frame_conteudo, subitem, nivel=nivel+1)

def obter_itens_lixeira_winapi():
    itens = []
    desktop = shell.SHGetDesktopFolder()
    pidl = shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_BITBUCKET)
    pasta = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)
    enumerador = pasta.EnumObjects(0, shellcon.SHCONTF_FOLDERS | shellcon.SHCONTF_NONFOLDERS)
    while True:
        item = enumerador.Next(1)
        if not item:
            break
        pidl_item = item[0]
        nome_exibicao = pasta.GetDisplayNameOf(pidl_item, shellcon.SHGDN_NORMAL)
        nome_parsing = pasta.GetDisplayNameOf(pidl_item, shellcon.SHGDN_FORPARSING)
        atributos = pasta.GetAttributesOf([pidl_item], shellcon.SFGAO_FOLDER)
        eh_pasta = bool(atributos & shellcon.SFGAO_FOLDER)
        eh_arquivo = not eh_pasta
        extensao = os.path.splitext(nome_exibicao)[1] if eh_arquivo else ""
        tamanho = obter_tamanho_item(nome_parsing)
        itens.append({
            "nome": nome_exibicao,
            "tamanho": tamanho,
            "extensao": extensao,
            "caminho": nome_parsing,
            "eh_arquivo": eh_arquivo
        })
    return itens

def obter_tamanho_item(caminho):
    if os.path.isfile(caminho):
        try:
            return os.path.getsize(caminho)
        except:
            return 0
    elif os.path.isdir(caminho):
        total = 0
        for raiz, pastas, arquivos in os.walk(caminho):
            for arquivo in arquivos:
                caminho_completo = os.path.join(raiz, arquivo)
                try:
                    total += os.path.getsize(caminho_completo)
                except:
                    pass
        return total
    return 0

def listar_itens_pasta_winapi(caminho_pasta):
    itens = []
    try:
        for entrada in os.listdir(caminho_pasta):
            caminho_completo = os.path.join(caminho_pasta, entrada)
            eh_arquivo = os.path.isfile(caminho_completo)
            extensao = os.path.splitext(entrada)[1] if eh_arquivo else ""
            tamanho = obter_tamanho_item(caminho_completo)
            itens.append({
                "nome": entrada,
                "tamanho": tamanho,
                "extensao": extensao,
                "caminho": caminho_completo,
                "eh_arquivo": eh_arquivo
            })
    except Exception as erro:
        pass
    return itens

def principal():
    janela = tk.Tk()
    janela.geometry("600x400")
    janela.title("lix => lixeira do windows")

    # Criar frame principal com scrollbar
    container_principal = tk.Frame(janela)
    container_principal.pack(fill="both", expand=True)

    # Canvas para scroll
    canvas = tk.Canvas(container_principal)
    barra_rolagem = ttk.Scrollbar(container_principal, orient="vertical", command=canvas.yview)
    frame_rolavel = tk.Frame(canvas)

    frame_rolavel.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=frame_rolavel, anchor="nw")
    canvas.configure(yscrollcommand=barra_rolagem.set)

    # Pack do canvas e scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    barra_rolagem.pack(side="right", fill="y")

    # Mouse wheel scrolling
    def _ao_rolar_mouse(evento):
        canvas.yview_scroll(int(-1*(evento.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _ao_rolar_mouse)

    itens = obter_itens_lixeira_winapi()
    for item in itens:
        criar_frame_item(frame_rolavel, item)

    janela.mainloop()

if __name__ == "__main__":
    principal()
