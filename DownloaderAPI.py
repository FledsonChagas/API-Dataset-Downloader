import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import requests
import pandas as pd
import os
import zipfile
import shutil
import time
import logging

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)
    logging.info(message)  # Esta linha grava a mensagem no arquivo de log.


default_location_text = "Default location: Desktop"
cancel_download = False

def validate_api(menu_url, headers):
    try:
        response = requests.get(menu_url, headers=headers)
        if response.status_code == 200:
            return True
        elif response.status_code == 401:  # Erro de autenticação (Secret Key inválido)
            return "Invalid credentials"
        else:
            return "Bad API"
    except:
        return "Bad API"


def show_endpoint_selection(endpoints):
    selection_window = tk.Toplevel(app)
    selection_window.title("Choose Files")
    selection_window.resizable(False, False)  # Bloqueia redimensionamento da janela de seleção


    check_vars = {}  # Para armazenar as variáveis de controle dos checkboxes

    for index, endpoint in enumerate(endpoints):
        check_var = tk.IntVar()
        tk.Checkbutton(selection_window, text=endpoint, variable=check_var).grid(row=index, sticky=tk.W)
        check_vars[endpoint] = check_var

    def select_all_deselect_all():
        if select_deselect_button["text"] == "Select All":
            for var in check_vars.values():
                var.set(1)
            select_deselect_button.config(text="Deselect All")
        else:
            for var in check_vars.values():
                var.set(0)
            select_deselect_button.config(text="Select All")

    select_deselect_button = tk.Button(selection_window, text="Select All", command=select_all_deselect_all)
    select_deselect_button.grid(row=len(endpoints) + 1, column=0, pady=5, sticky=tk.W)

    tk.Button(selection_window, text="OK", command=selection_window.destroy).grid(row=len(endpoints) + 1, column=0,
                                                                                  pady=5, sticky=tk.E)

    selection_window.mainloop()

    # Retorna uma lista dos endpoints selecionados
    return [endpoint for endpoint, var in check_vars.items() if var.get() == 1]

def start_download():
    global cancel_download

    menu_url = url_entry.get()
    secret_key = secret_key_entry.get()

    if start_button["text"] == "Cancel Download":
        cancel_download = True
        reset_interface()
        return

    entered_location = location_entry.get()

    if entered_location == default_location_text:
        save_location = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    else:
        save_location = entered_location

    headers = {
        'User-Agent': 'curl/7.64.0',
        'Ocp-Apim-Subscription-Key': secret_key,
    }

    validation_result = validate_api(menu_url, headers)
    if validation_result == True:
        response = requests.get(menu_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['dataset'])
            endpoint_titles = list(df['title'])  # Obtemos os títulos dos endpoints para exibir na janela de seleção

            selected_datasets = show_endpoint_selection(endpoint_titles)
            if not selected_datasets:
                log("No datasets selected.")
                return  # Se nenhum dataset for selecionado, interrompemos aqui.

            start_button.config(text="Cancel Download")
            progress_var.set(0)
            progress_label.config(text="0%")
            progress_bar.grid(row=4, column=0, columnspan=3, pady=5)
            progress_label.grid(row=4, column=1)
            thread = threading.Thread(target=main_function, args=(menu_url, headers, save_location, selected_datasets))
            thread.start()
        else:
            messagebox.showerror("Error", "Failed to fetch API endpoints.")
    else:
        messagebox.showerror("Error", validation_result)

def toggle_log():
    if log_text.winfo_ismapped():
        log_frame.grid_forget()
        expand_button.config(text="Show Log")
    else:
        log_frame.grid(row=6, column=0, columnspan=3, pady=10)
        expand_button.config(text="Hide Log")

def fetch_data_from_endpoint(url, headers, retries=5):
    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()

            # Rate Limit Exceeded - Retry Logic
            elif response.status_code == 429:
                wait_time = response.json().get('message', '').split(' ')[-2]  # Assumes the message format is "Rate limit is exceeded. Try again in X seconds."
                if wait_time and wait_time.isdigit():
                    log(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                    time.sleep(int(wait_time))
                    continue
                else:
                    log(f"Error {response.status_code} accessing URL {url}: {response.content}")
                    return None

            # Other errors
            elif response.status_code == 400:
                log("Bad request. Please check the API URL and parameters.")
                return None

            elif response.status_code == 401:
                log("Unauthorized. Please check your API secret key.")
                return None

            elif response.status_code == 403:
                log("Forbidden. You don't have permission to access this resource.")
                return None

            elif response.status_code == 404:
                log("Resource not found. Please check the API URL.")
                return None

            elif response.status_code in [500, 501, 502, 503, 504]:
                log(f"Server error ({response.status_code}). Please try again later.")
                return None

            else:
                log(f"Error {response.status_code} accessing URL {url}: {response.content}")
                return None

        except requests.ConnectionError:
            log("Failed to connect. Please check your internet connection.")
            if _ == retries - 1:
                return None
            time.sleep(5)  # Let's add a small wait time before retrying, just in case there's a temporary connectivity issue.

        except Exception as e:
            log(f"An unexpected error occurred: {str(e)}")
            return None

    log(f"Failed to fetch data after {retries} retries.")
    return None


def log(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)

def main_function(menu_url, headers, save_location, selected_datasets):
    total_datasets = len(df)
    log("Starting download process...")
    global cancel_download
    try:
        response = requests.get(menu_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['dataset'])
            for index, row in df.iterrows():
                title = row['title']
                if title not in selected_datasets:  # Ignora os datasets não selecionados
                    continue

                title = row['title']
                endpoint = row['distribution'][0]['accessURL']

                folder_name = os.path.join(save_location, title.replace(" ", "_"))
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)

                data_main_endpoint = fetch_data_from_endpoint(endpoint, headers)
                if data_main_endpoint:
                    main_df = pd.DataFrame(data_main_endpoint)
                    filename_main = os.path.join(folder_name, "main_data.csv")
                    main_df.to_csv(filename_main, index=False)
                    log(f"Saved {filename_main} successfully!")

                subendpoints = fetch_data_from_endpoint(endpoint, headers)
                if subendpoints and 'value' in subendpoints:
                    for subendpoint in subendpoints['value']:
                        if 'url' in subendpoint:
                            data_url = f"{endpoint}/{subendpoint['url']}"
                            data = fetch_data_from_endpoint(data_url, headers)
                            if data:
                                sub_df = pd.DataFrame(data)
                                filename = os.path.join(folder_name, f"{subendpoint['name']}.csv")
                                sub_df.to_csv(filename, index=False)
                                log(f"Saved {filename} successfully!")

                percent_complete = (index + 1) / total_datasets * 100
                progress_var.set(percent_complete)
                progress_label.config(text=f"{int(percent_complete)}%")

        else:
            log(f"Error {response.status_code}: {response.content}")

    except Exception as e:
        log(str(e))
    finally:
        cancel_download = False

    with zipfile.ZipFile('Datasets.zip', 'w') as zipf:
        for root, _, files in os.walk(save_location):
            for file in files:
                if file.endswith(".csv"):
                    zipf.write(os.path.join(root, file))

    shutil.move("Datasets.zip", os.path.join(save_location, "Datasets.zip"))
    log("Download completed!")
    start_button.config(text="Start Download")  # Reset the button text
    messagebox.showinfo("Success", "Download completed successfully!")  # Show success message


def reset_interface():
    location_entry.delete(0, tk.END)
    location_entry.insert(tk.END, default_location_text)
    location_entry.config(fg="gray")
    progress_var.set(0)
    progress_label.config(text="")
    progress_bar.grid_remove()
    progress_label.grid_remove()
    start_button.config(text="Start Download")
    log_text.delete(1.0, tk.END)
    if log_text.winfo_ismapped():
        toggle_log()

def browse_location():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        location_entry.delete(0, tk.END)
        location_entry.insert(tk.END, folder_selected)

def handle_focus_in(_):
    if location_entry.get() == default_location_text:
        location_entry.delete(0, tk.END)
        location_entry.config(fg="black")

def handle_focus_out(_):
    if not location_entry.get():
        location_entry.insert(tk.END, default_location_text)
        location_entry.config(fg="gray")

app = tk.Tk()
app.title("API Dataset Downloader - v1.2")
app.resizable(False, False)  # Lock the window size

frame = tk.Frame(app)
frame.pack(padx=10, pady=10)

url_label = tk.Label(frame, text="API URL:")
url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
url_entry = tk.Entry(frame, width=40)
url_entry.grid(row=0, column=1, pady=5)

secret_key_label = tk.Label(frame, text="API Secret Key:")
secret_key_label.grid(row=1, column=0, sticky=tk.W, pady=5)
secret_key_entry = tk.Entry(frame, show='*', width=40)
secret_key_entry.grid(row=1, column=1, pady=5)

location_label = tk.Label(frame, text="Save as:")
location_label.grid(row=2, column=0, sticky=tk.W, pady=5)
location_entry = tk.Entry(frame, width=40)
location_entry.insert(tk.END, default_location_text)
location_entry.config(fg="gray")
location_entry.grid(row=2, column=1, pady=5)

location_entry.bind("<FocusIn>", handle_focus_in)
location_entry.bind("<FocusOut>", handle_focus_out)

browse_button = tk.Button(frame, text="Browse", command=browse_location)
browse_button.grid(row=2, column=2, pady=5)

start_button = tk.Button(frame, text="Start Download", command=start_download)
start_button.grid(row=3, column=0, columnspan=3, pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, orient='horizontal', length=320, mode='determinate', variable=progress_var)
progress_label = tk.Label(frame, text="")

expand_button = tk.Button(frame, text="Show Log", command=toggle_log)
expand_button.grid(row=5, column=0, columnspan=3, pady=10)

log_frame = tk.Frame(frame)
log_scroll = tk.Scrollbar(log_frame)
log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

log_text = tk.Text(log_frame, height=10, width=50, yscrollcommand=log_scroll.set)
log_text.pack(side=tk.LEFT, fill=tk.BOTH)

log_scroll.config(command=log_text.yview)

# Copyright Label
def open_linkedin(event):
    import webbrowser
    webbrowser.open("https://www.linkedin.com/in/fledsonchagas/")

copyright_label = tk.Label(frame, text="Copyright Fledson Chagas", cursor="hand2", fg="blue")  # A cor azul para se parecer com um link
copyright_label.grid(row=7, column=0, columnspan=3, pady=2, sticky=tk.SE)  # SE = South-East, para alinhar ao canto inferior direito
copyright_label.bind("<Button-1>", open_linkedin)  # Vincula o clique esquerdo do mouse ao evento open_linkedin


app.mainloop()
