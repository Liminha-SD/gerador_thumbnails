import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json

# Importa as novas funções do nosso script de extração
from extrator_frame import encontrar_ffmpeg_tools, extrair_frames_aleatorios, carregar_caminho_ffmpeg, salvar_caminho_ffmpeg

# --- Configurações do Tema Escuro ---
DARK_THEME_CONFIG = {
    "bg": "#2E2E2E",
    "fg": "#FFFFFF",
    "insertbackground": "#FFFFFF",
    "selectbackground": "#555555",
    "selectforeground": "#FFFFFF",
    "button_bg": "#555555",
    "button_fg": "#FFFFFF",
    "button_active_bg": "#666666",
    "entry_bg": "#3E3E3E",
    "label_bg": "#2E2E2E",
    "log_bg": "#1E1E1E",
    "log_fg": "#EAEAEA"
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Extrator de Frames")
        self.geometry("700x500") # Reduzi um pouco a altura
        self.configure(bg=DARK_THEME_CONFIG["bg"])

        # --- Estilo ttk ---
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TLabel', background=DARK_THEME_CONFIG["label_bg"], foreground=DARK_THEME_CONFIG["fg"])
        style.configure('TButton', background=DARK_THEME_CONFIG["button_bg"], foreground=DARK_THEME_CONFIG["button_fg"])
        style.map('TButton', background=[('active', DARK_THEME_CONFIG["button_active_bg"])])
        style.configure('TEntry', fieldbackground=DARK_THEME_CONFIG["entry_bg"], foreground=DARK_THEME_CONFIG["fg"], insertcolor=DARK_THEME_CONFIG["insertbackground"])
        style.configure('TScale', background=DARK_THEME_CONFIG["label_bg"])

        # --- Variáveis ---
        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.ffmpeg_path = tk.StringVar()
        self.ffprobe_path = tk.StringVar()
        self.num_frames = tk.IntVar(value=300)

        # --- Carregar caminhos salvos ---
        self.load_paths()

        # --- Widgets ---
        self.create_widgets()

        # --- Verificação do FFmpeg/FFprobe ---
        self.check_ffmpeg_tools_on_startup()

    def load_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.video_path.set(config.get("video_path", ""))
                self.output_dir.set(config.get("output_dir", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is empty/corrupted, just start with empty paths
            pass

    def save_paths(self):
        # First, read the existing config to not overwrite the ffmpeg path
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        # Update the paths
        config["video_path"] = self.video_path.get()
        config["output_dir"] = self.output_dir.get()

        # Write the updated config back to the file
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Seção de Arquivos ---
        ttk.Label(main_frame, text="Arquivo de Vídeo:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.video_path, width=60).grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(main_frame, text="Procurar...", command=self.browse_video).grid(row=1, column=2, padx=5)

        ttk.Label(main_frame, text="Diretório de Saída:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=60).grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(main_frame, text="Procurar...", command=self.browse_output_dir).grid(row=3, column=2, padx=5)

        # --- Seção de Configurações ---
        settings_frame = ttk.Frame(main_frame, padding="0 10 0 0")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Número de Frames a Extrair:").grid(row=0, column=0, sticky="w")
        ttk.Scale(settings_frame, from_=1, to=300, orient=tk.HORIZONTAL, variable=self.num_frames, command=lambda s: self.num_frames.set(int(float(s)))).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(settings_frame, textvariable=self.num_frames).grid(row=0, column=2)

        # --- Botão de Execução ---
        self.run_button = ttk.Button(main_frame, text="Iniciar Extração", command=self.start_extraction_thread)
        self.run_button.grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

        # --- Log ---
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=6, column=0, columnspan=3, sticky="nsew")
        main_frame.rowconfigure(6, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, bg=DARK_THEME_CONFIG["log_bg"], fg=DARK_THEME_CONFIG["log_fg"], relief=tk.FLAT)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_video(self):
        path = filedialog.askopenfilename(title="Selecione um arquivo de vídeo", filetypes=(("Arquivos de Vídeo", "*.mp4 *.avi *.mkv *.mov"), ("Todos os arquivos", "*.* crescimento")))
        if path:
            self.video_path.set(path)
            self.save_paths()

    def browse_output_dir(self):
        path = filedialog.askdirectory(title="Selecione o diretório de saída")
        if path:
            self.output_dir.set(path)
            self.save_paths()

    def log(self, message):
        self.after(0, self._log_update, message)

    def _log_update(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def check_ffmpeg_tools_on_startup(self):
        self.log("Verificando ferramentas FFmpeg...")
        # A função encontrar_ffmpeg_tools agora lida com a lógica de carregar do config
        tools, error_msg = encontrar_ffmpeg_tools()
        
        if tools["ffmpeg"] and tools["ffprobe"]:
            self.ffmpeg_path.set(tools["ffmpeg"])
            self.ffprobe_path.set(tools["ffprobe"])
            ffmpeg_dir = os.path.dirname(tools["ffmpeg"])
            # Se o caminho for apenas 'ffmpeg', significa que está no PATH
            if ffmpeg_dir == "":
                self.log("FFmpeg e FFprobe encontrados no PATH do sistema.")
            else:
                self.log(f"FFmpeg e FFprobe carregados do caminho salvo: {ffmpeg_dir}")
        else:
            self.log("Aviso: FFmpeg/FFprobe não encontrados ou o caminho salvo é inválido.")
            if error_msg:
                self.log(f"Detalhes: {error_msg}")
            # Só pergunta ao usuário se não encontrou de nenhuma forma
            self.prompt_for_ffmpeg_folder()

    def prompt_for_ffmpeg_folder(self):
        if messagebox.askyesno("Ferramentas não encontradas", "Deseja apontar para a pasta 'bin' do FFmpeg agora?"):
            path = filedialog.askdirectory(title="Selecione a pasta 'bin' que contém ffmpeg.exe e ffprobe.exe")
            if path:
                self.log(f"Verificando a pasta selecionada: {path}")
                # Passa o caminho para a função verificar e salvar se for válido
                tools, error_msg = encontrar_ffmpeg_tools(path)
                if tools["ffmpeg"] and tools["ffprobe"]:
                    self.ffmpeg_path.set(tools["ffmpeg"])
                    self.ffprobe_path.set(tools["ffprobe"])
                    self.log(f"Sucesso! Ferramentas FFmpeg configuradas e o caminho foi salvo para futuras execuções.")
                else:
                    messagebox.showerror("Erro", f"A pasta selecionada é inválida ou as ferramentas não puderam ser executadas.\n\nDetalhes: {error_msg}")
                    self.log(f"Falha ao verificar a pasta selecionada.")

    def start_extraction_thread(self):
        if not self.video_path.get() or not self.output_dir.get():
            messagebox.showerror("Erro", "Por favor, especifique o arquivo de vídeo e o diretório de saída.")
            return
        if not self.ffmpeg_path.get() or not self.ffprobe_path.get():
            messagebox.showerror("Erro", "Caminhos para FFmpeg/FFprobe não definidos.")
            self.prompt_for_ffmpeg_folder()
            return

        self.log_text.delete(1.0, tk.END)
        self.run_button.config(state=tk.DISABLED, text="Extraindo...")

        extraction_thread = threading.Thread(
            target=self.run_extraction,
            daemon=True
        )
        extraction_thread.start()

    def run_extraction(self):
        extrair_frames_aleatorios(
            video_path=self.video_path.get(),
            output_dir=self.output_dir.get(),
            num_frames=self.num_frames.get(),
            ffmpeg_path=self.ffmpeg_path.get(),
            ffprobe_path=self.ffprobe_path.get(),
            logger_callback=self.log
        )
        self.run_button.config(state=tk.NORMAL, text="Iniciar Extração")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = App()
    app.mainloop()
