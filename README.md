# API Dataset Downloader 📥

![API](https://img.shields.io/badge/API-Dataset%20Downloader-brightgreen) ![Python](https://img.shields.io/badge/Python-3.7+-blue)

Este é um utilitário de interface gráfica (GUI) construído usando **Python** e **Tkinter** para baixar conjuntos de dados de APIs e salvá-los em um local de escolha do usuário.

Até o momento foi testado e usado com sucesso na api: https://api.stats.govt.nz/ utilizando o método http.

## 🌟 Características

- 🔗 Interface gráfica amigável para inserir URL da API e Secret Key.
- ✅ Validação de chave de API.
- 📁 Opção de escolher o local de salvamento.
- 📊 Baixa os conjuntos de dados e os organiza em pastas.
- ⏳ Apresenta uma barra de progresso e uma seção de log.
- 🗃️ Salva os conjuntos de dados em um arquivo zip após o download.

## 🚀 Como usar

1. Abra o programa.
2. Insira a URL da API e a Secret Key nos campos fornecidos.
3. Selecione o local de salvamento ou use o padrão (Desktop).
4. Clique em "Start Download" para iniciar o processo de download.
5. O progresso será mostrado na barra de progresso.
6. Após a conclusão, todos os conjuntos de dados baixados serão compactados em um arquivo zip no local de salvamento escolhido.

## 🛠️ Dependências

- Python 3.7+
- `requests`
- `pandas`
- `tkinter`

Para instalar as dependências, execute: pip install requests pandas

## 🖋️ Sobre o Autor

Este projeto foi criado por **Fledson Chagas**. Para saber mais sobre meu trabalho e experiências, conecte-se comigo no LinkedIn!

[![Fledson Chagas](https://img.shields.io/badge/LinkedIn-Fledson%20Chagas-blue?logo=linkedin)](https://www.linkedin.com/in/fledsonchagas/)
