import subprocess
import os
import json

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

    # Prioridade 1: Usar o caminho customizado fornecido (ex: da caixa de diálogo)
    caminho_a_verificar = caminho_custom

    # Prioridade 2: Se nenhum caminho customizado for fornecido, carregar do config.json
    if not caminho_a_verificar:
        caminho_a_verificar = carregar_caminho_ffmpeg()

    # Se um caminho foi encontrado (customizado ou do config), verifica as ferramentas nele
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
        
        # Se encontramos as ferramentas, e o caminho veio do prompt, salvamos no config
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"] and caminho_custom:
            salvar_caminho_ffmpeg(caminho_custom)
        
        # Se as ferramentas foram encontradas, retorna
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"]:
            return ferramentas, "".join(error_log)

    # Prioridade 3: Se ainda não encontrou, procura no PATH do sistema
    # Isso só executa se o caminho do config falhar ou não existir
    if not (ferramentas["ffmpeg"] and ferramentas["ffprobe"]):
        for nome in nomes:
            if not ferramentas[nome]: # Só procura no PATH se ainda não achou
                try:
                    subprocess.run([nome, '-version'], check=True, capture_output=True, startupinfo=_startupinfo)
                    ferramentas[nome] = nome # Usa o nome do comando, pois está no PATH
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
    import random

    if not os.path.exists(video_path):
        logger_callback(f"Erro: O arquivo de vídeo '{video_path}' não foi encontrado.")
        return

    if not os.path.exists(output_dir):
        logger_callback(f"Criando diretório de saída: {output_dir}")
        os.makedirs(output_dir)

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
        output_filename = f"frame_aleatorio_{i+1}_tempo_{random_timestamp:.2f}s.jpg"
        output_filepath = os.path.join(output_dir, output_filename)

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
            # Continua para o próximo frame mesmo se um falhar
        except Exception as e:
            logger_callback(f"Ocorreu um erro inesperado ao extrair frame: {e}")
            # Continua para o próximo frame

    logger_callback(f"""
Extração aleatória concluída. {extracted_count} de {num_frames} frames salvos em: {os.path.abspath(output_dir)}""")


