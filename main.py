# -*- coding: utf-8 -*-

"""
Este arquivo combina a lógica de extração de frames (originalmente em extrator_frame.py)
com a interface gráfica do usuário (originalmente em gui_pyside.py).
"""

import sys
import threading
import os
import json
import subprocess
import random
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QSlider, QListWidget
)
from PySide6.QtCore import Qt, Signal, QObject

# ==============================================================================
# --- Lógica de Extração de Frames (do extrator_frame.py) ---
# ==============================================================================

# Para esconder a janela do console no Windows
if os.name == 'nt':
    _CREATE_NO_WINDOW = 0x08000000
    _startupinfo = subprocess.STARTUPINFO()
    _startupinfo.dwFlags |= _CREATE_NO_WINDOW
else:
    _startupinfo = None

CONFIG_FILE = "config.json"

def salvar_caminho_ffmpeg(path):
    """Salva o caminho da pasta 'bin' do FFmpeg no arquivo de configuração."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"ffmpeg_bin_path": path}, f)
        return True
    except IOError as e:
        print(f"Erro ao salvar o arquivo de configuração: {e}")
        return False

def carregar_caminho_ffmpeg():
    """Carrega o caminho da pasta 'bin' do FFmpeg do arquivo de configuração."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get("ffmpeg_bin_path")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar ou decodificar o arquivo de configuração: {e}")
        return None

def encontrar_ffmpeg_tools(caminho_custom=None):
    """Verifica se ffmpeg e ffprobe estão disponíveis e retorna o erro se não estiverem."""
    ferramentas = {"ffmpeg": None, "ffprobe": None}
    nomes = ["ffmpeg", "ffprobe"]
    error_log = []

    caminho_a_verificar = caminho_custom

    if not caminho_a_verificar:
        caminho_a_verificar = carregar_caminho_ffmpeg()

    if caminho_a_verificar:
        for nome in nomes:
            try:
                exec_name = f"{nome}.exe" if os.name == 'nt' and not nome.endswith('.exe') else nome
                full_path = os.path.join(caminho_a_verificar, exec_name)
                if os.path.exists(full_path):
                    subprocess.run([full_path, '-version'], check=True, capture_output=True, startupinfo=_startupinfo)
                    ferramentas[nome] = full_path
                else:
                    error_log.append(f"'{exec_name}' não encontrado em '{caminho_a_verificar}'.")
            except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
                error_log.append(f"Erro ao verificar '{nome}' em '{caminho_a_verificar}': {e}")
        
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"] and caminho_custom:
            salvar_caminho_ffmpeg(caminho_custom)
        
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"]:
            return ferramentas, "".join(error_log)

    if not (ferramentas["ffmpeg"] and ferramentas["ffprobe"]):
        for nome in nomes:
            if not ferramentas[nome]:
                try:
                    subprocess.run([nome, '-version'], check=True, capture_output=True, startupinfo=_startupinfo)
                    ferramentas[nome] = nome
                except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
                    error_log.append(f"'{nome}' não encontrado ou com erro no PATH do sistema: {e}")

    return ferramentas, "".join(error_log)

def get_video_duration(video_path, ffprobe_path='ffprobe', logger_callback=print):
    """Obtém a duração de um vídeo em segundos usando ffprobe."""
    command = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', startupinfo=_startupinfo)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger_callback(f"Erro ao obter duração do vídeo com ffprobe: {e.stderr}")
        return None
    except ValueError:
        logger_callback(f"Não foi possível converter a duração para número: {result.stdout.strip()}")
        return None
    except Exception as e:
        logger_callback(f"Erro inesperado ao obter duração do vídeo: {e}")
        return None

def extrair_frames_aleatorios(video_path, output_dir, num_frames=1, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe', logger_callback=print, stop_event=None):
    """
    Extrai um número especificado de frames aleatórios de um vídeo.
    """
    if not os.path.exists(video_path):
        logger_callback(f"Erro: O arquivo de vídeo '{video_path}' não foi encontrado.")
        return

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    new_output_dir = os.path.join(output_dir, video_name)

    if not os.path.exists(new_output_dir):
        logger_callback(f"Criando diretório de saída: {new_output_dir}")
        os.makedirs(new_output_dir)

    video_digits = ''.join(re.findall(r'\d', video_name))[-3:]
    if not video_digits or len(video_digits) < 3:
        logger_callback("Aviso: Não foi possível extrair 3 dígitos do nome do vídeo. Usando '000' como padrão.")
        video_digits = "000"

    duration = get_video_duration(video_path, ffprobe_path, logger_callback)
    if duration is None:
        logger_callback("Não foi possível determinar a duração do vídeo. Abortando extração aleatória.")
        return

    logger_callback(f"Duração do vídeo: {duration:.2f} segundos.")
    logger_callback(f"Extraindo {num_frames} frames aleatórios...")

    extracted_count = 0
    for i in range(num_frames):
        if stop_event and stop_event.is_set():
            logger_callback("Extração interrompida pelo usuário.")
            break
        
        random_timestamp = random.uniform(0, duration)
        
        output_filename = f"{video_digits}-{i+1}.jpg"
        output_filepath = os.path.join(new_output_dir, output_filename)

        command_extraction = [
            ffmpeg_path,
            '-ss', str(random_timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_filepath
        ]

        try:
            logger_callback(f"Extraindo frame aleatório em {random_timestamp:.2f}s para '{output_filepath}'")
            subprocess.run(command_extraction, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=_startupinfo)
            extracted_count += 1
        except subprocess.CalledProcessError as e:
            logger_callback(f"""
Ocorreu um erro ao extrair frame em {random_timestamp:.2f}s.""")
            logger_callback(f"Comando: {' '.join(e.cmd)}")
            if e.stdout:
                logger_callback(f"""--- Saída (stdout) ---
{e.stdout}""")
            if e.stderr:
                logger_callback(f"""--- Erro (stderr) ---
{e.stderr}""")
            else:
                logger_callback("Nenhuma saída de erro específica foi capturada (stderr estava vazio).")
        except Exception as e:
            logger_callback(f"Ocorreu um erro inesperado ao extrair frame: {e}")

    logger_callback(f"""
Extração aleatória concluída. {extracted_count} de {num_frames} frames salvos em: {os.path.abspath(new_output_dir)}""")

# ==============================================================================
# --- Interface Gráfica (do gui_pyside.py) ---
# ==============================================================================

DARK_STYLESHEET = """
    QWidget {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    QLineEdit {
        background-color: #3E3E3E;
        border: 1px solid #555555;
        padding: 5px;
    }
    QPushButton {
        background-color: #555555;
        border: 1px solid #666666;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #666666;
    }
    QPushButton:pressed {
        background-color: #777777;
    }
    QTextEdit {
        background-color: #1E1E1E;
        border: 1px solid #555555;
    }
    QLabel {
        background-color: #2E2E2E;
    }
    QSlider::groove:horizontal {
        border: 1px solid #bbb;
        background: white;
        height: 10px;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
        border: 1px solid #777;
        width: 18px;
        margin: -2px 0;
        border-radius: 4px;
    }
    QListWidget {
        background-color: #3E3E3E;
        border: 1px solid #555555;
    }
"""

class Worker(QObject):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, video_path, output_dir, num_frames, ffmpeg_path, ffprobe_path, stop_event):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.num_frames = num_frames
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.stop_event = stop_event

    def run(self):
        extrair_frames_aleatorios(
            video_path=self.video_path,
            output_dir=self.output_dir,
            num_frames=self.num_frames,
            ffmpeg_path=self.ffmpeg_path,
            ffprobe_path=self.ffprobe_path,
            logger_callback=self.log_signal.emit,
            stop_event=self.stop_event
        )
        self.finished_signal.emit()

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Extrator de Frames")
        self.setGeometry(100, 100, 700, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.ffmpeg_path = ""
        self.ffprobe_path = ""
        self.stop_event = None
        self.worker_thread = None
        self.video_queue = []

        self.create_widgets()
        self.load_paths()
        self.check_ffmpeg_tools_on_startup()

    def load_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.output_dir_input.setText(config.get("output_dir", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["output_dir"] = self.output_dir_input.text()

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    def create_widgets(self):
        # Video Queue
        self.layout.addWidget(QLabel("Fila de Vídeos:"))
        self.video_list_widget = QListWidget()
        self.layout.addWidget(self.video_list_widget)

        queue_buttons_layout = QHBoxLayout()
        add_videos_btn = QPushButton("Adicionar Vídeos")
        add_videos_btn.clicked.connect(self.add_videos)
        queue_buttons_layout.addWidget(add_videos_btn)

        remove_video_btn = QPushButton("Remover Selecionado")
        remove_video_btn.clicked.connect(self.remove_selected_video)
        queue_buttons_layout.addWidget(remove_video_btn)

        clear_queue_btn = QPushButton("Limpar Fila")
        clear_queue_btn.clicked.connect(self.clear_queue)
        queue_buttons_layout.addWidget(clear_queue_btn)
        self.layout.addLayout(queue_buttons_layout)

        # Output Directory
        self.layout.addWidget(QLabel("Diretório de Saída:"))
        output_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        output_layout.addWidget(self.output_dir_input)
        browse_output_btn = QPushButton("Procurar...")
        browse_output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_output_btn)
        self.layout.addLayout(output_layout)

        # Number of Frames
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Número de Frames a Extrair:"))
        self.num_frames_slider = QSlider(Qt.Horizontal)
        self.num_frames_slider.setRange(1, 300)
        self.num_frames_slider.setValue(300)
        settings_layout.addWidget(self.num_frames_slider)
        self.num_frames_label = QLabel("300")
        self.num_frames_slider.valueChanged.connect(lambda v: self.num_frames_label.setText(str(v)))
        settings_layout.addWidget(self.num_frames_label)
        self.layout.addLayout(settings_layout)

        # Action Buttons
        action_layout = QHBoxLayout()
        self.run_button = QPushButton("Iniciar Extração")
        self.run_button.clicked.connect(self.start_extraction_thread)
        action_layout.addWidget(self.run_button)
        self.stop_button = QPushButton("Parar Extração")
        self.stop_button.clicked.connect(self.stop_extraction)
        self.stop_button.setEnabled(False)
        action_layout.addWidget(self.stop_button)
        self.layout.addLayout(action_layout)

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

    def add_videos(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecione os arquivos de vídeo", "", "Arquivos de Vídeo (*.mp4 *.avi *.mkv *.mov);;Todos os arquivos (*.*)")
        if paths:
            for path in paths:
                self.video_list_widget.addItem(path)

    def remove_selected_video(self):
        for item in self.video_list_widget.selectedItems():
            self.video_list_widget.takeItem(self.video_list_widget.row(item))

    def clear_queue(self):
        self.video_list_widget.clear()

    def browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Selecione o diretório de saída")
        if path:
            self.output_dir_input.setText(path)
            self.save_paths()

    def log(self, message):
        self.log_text.append(message)

    def check_ffmpeg_tools_on_startup(self):
        self.log("Verificando ferramentas FFmpeg...")
        tools, error_msg = encontrar_ffmpeg_tools()
        if tools["ffmpeg"] and tools["ffprobe"]:
            self.ffmpeg_path = tools["ffmpeg"]
            self.ffprobe_path = tools["ffprobe"]
            ffmpeg_dir = os.path.dirname(tools["ffmpeg"])
            if ffmpeg_dir == "":
                self.log("FFmpeg e FFprobe encontrados no PATH do sistema.")
            else:
                self.log(f"FFmpeg e FFprobe carregados do caminho salvo: {ffmpeg_dir}")
        else:
            self.log("Aviso: FFmpeg/FFprobe não encontrados ou o caminho salvo é inválido.")
            if error_msg:
                self.log(f"Detalhes: {error_msg}")
            self.prompt_for_ffmpeg_folder()

    def prompt_for_ffmpeg_folder(self):
        reply = QMessageBox.question(self, "Ferramentas não encontradas", "Deseja apontar para a pasta 'bin' do FFmpeg agora?")
        if reply == QMessageBox.Yes:
            path = QFileDialog.getExistingDirectory(self, "Selecione a pasta 'bin' que contém ffmpeg.exe e ffprobe.exe")
            if path:
                self.log(f"Verificando a pasta selecionada: {path}")
                tools, error_msg = encontrar_ffmpeg_tools(path)
                if tools["ffmpeg"] and tools["ffprobe"]:
                    self.ffmpeg_path = tools["ffmpeg"]
                    self.ffprobe_path = tools["ffprobe"]
                    self.log("Sucesso! Ferramentas FFmpeg configuradas e o caminho foi salvo para futuras execuções.")
                else:
                    QMessageBox.critical(self, "Erro", f"A pasta selecionada é inválida ou as ferramentas não puderam ser executadas.\n\nDetalhes: {error_msg}")
                    self.log("Falha ao verificar a pasta selecionada.")

    def stop_extraction(self):
        if self.stop_event:
            self.log("Sinal de parada enviado...")
            self.stop_event.set()
            self.stop_button.setEnabled(False)

    def start_extraction_thread(self):
        self.video_queue = [self.video_list_widget.item(i).text() for i in range(self.video_list_widget.count())]
        output_dir = self.output_dir_input.text()

        if not self.video_queue:
            QMessageBox.critical(self, "Erro", "A fila de vídeos está vazia.")
            return
        if not output_dir:
            QMessageBox.critical(self, "Erro", "Por favor, especifique o diretório de saída.")
            return
        if not self.ffmpeg_path or not self.ffprobe_path:
            QMessageBox.critical(self, "Erro", "Caminhos para FFmpeg/FFprobe não definidos.")
            self.prompt_for_ffmpeg_folder()
            return

        self.log_text.clear()
        self.run_button.setEnabled(False)
        self.run_button.setText("Extraindo...")
        self.stop_button.setEnabled(True)

        self.process_next_video()

    def process_next_video(self):
        if not self.video_queue:
            self.on_extraction_finished(is_queue_finished=True)
            return

        video_path = self.video_queue.pop(0)
        self.log(f"--- Iniciando extração para: {video_path} ---")

        self.stop_event = threading.Event()
        self.worker = Worker(
            video_path,
            self.output_dir_input.text(),
            self.num_frames_slider.value(),
            self.ffmpeg_path,
            self.ffprobe_path,
            self.stop_event
        )
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_extraction_finished)
        self.worker_thread.start()

    def on_extraction_finished(self, is_queue_finished=False):
        if is_queue_finished:
            self.log("--- Fila de extração concluída ---")
            self.run_button.setEnabled(True)
            self.run_button.setText("Iniciar Extração")
            self.stop_button.setEnabled(False)
            self.worker_thread = None
        else:
            self.process_next_video()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
