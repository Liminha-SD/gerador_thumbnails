# Gerador de Thumbnails de Vídeo

![GIF da aplicação](https://imgur.com/a/sua-imagem.gif)

Uma aplicação de desktop simples e poderosa para extrair frames de vídeos, ideal para a criação de thumbnails e outras mídias.

## ✨ Funcionalidades Principais

-   **Interface Gráfica Intuitiva**: Uma interface limpa e fácil de usar, desenvolvida com Tkinter, que torna a extração de frames uma tarefa simples.
-   **Extração Aleatória e Precisa**: Extraia um número customizável de frames de pontos aleatórios do seu vídeo, garantindo uma grande variedade de thumbnails.
-   **Configuração Descomplicada**: A aplicação detecta automaticamente o FFmpeg no seu sistema. Caso não o encontre, você pode facilmente indicar o caminho da pasta.
-   **Feedback em Tempo Real**: Acompanhe o progresso da extração e visualize quaisquer erros ou avisos em um painel de log integrado.
-   **Memória de Configurações**: Seus caminhos de vídeo, pasta de saída e configurações de FFmpeg são salvos para que você não precise reconfigurar tudo a cada uso.

## 🚀 Começando

Para começar a usar o Gerador de Thumbnails, você precisará ter o Python 3 e o FFmpeg instalados em seu computador.

### Requisitos

-   **Python 3**: [Baixe o Python aqui](https://www.python.org/downloads/)
-   **FFmpeg**: [Baixe o FFmpeg aqui](https://ffmpeg.org/download.html)

### Instalação

1.  Clone este repositório para a sua máquina local:

    ```bash
    git clone https://github.com/seu-usuario/gerador_thumbnails.git
    ```

2.  Navegue até o diretório do projeto:

    ```bash
    cd gerador_thumbnails
    ```

3.  Execute a aplicação:

    ```bash
    python gui.py
    ```

## 📖 Como Usar

1.  **Configure o FFmpeg (se necessário)**: Na primeira execução, se o FFmpeg não for detectado, a aplicação solicitará que você aponte para a pasta `bin` da sua instalação do FFmpeg.
2.  **Selecione o Vídeo**: Clique em "Procurar..." para escolher o vídeo do qual deseja extrair os frames.
3.  **Escolha a Pasta de Saída**: Selecione a pasta onde os frames extraídos serão salvos.
4.  **Defina a Quantidade de Frames**: Use o controle deslizante para ajustar o número de frames que você deseja extrair.
5.  **Inicie a Extração**: Clique em "Iniciar Extração" e acompanhe o processo no painel de log.

## ⚙️ Configuração

A aplicação utiliza um arquivo `config.json` para armazenar suas preferências, como os caminhos do FFmpeg, do último vídeo utilizado e da pasta de saída. Este arquivo é gerenciado automaticamente pela aplicação.

```json
{
    "ffmpeg_bin_path": "C:/ffmpeg/bin",
    "video_path": "C:/Users/seu-usuario/Videos/meu_video.mp4",
    "output_dir": "C:/Users/seu-usuario/Pictures/Thumbnails"
}
```

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Se você tem alguma ideia para melhorar a aplicação, sinta-se à vontade para abrir uma issue ou enviar um pull request.

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.