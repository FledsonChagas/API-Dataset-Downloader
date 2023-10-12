import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import requests
import pandas as pd
import os
import zipfile
import shutil

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

def start_download():
    global cancel_download

    if start_button["text"] == "Cancel Download":
        cancel_download = True
        reset_interface()
        return

    menu_url = url_entry.get()
    secret_key = secret_key_entry.get()
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
        start_button.config(text="Cancel Download")
        progress_var.set(0)
        progress_label.config(text="0%")
        progress_bar.grid(row=4, column=0, columnspan=3, pady=5)
        progress_label.grid(row=4, column=1)
        thread = threading.Thread(target=main_function, args=(menu_url, headers, save_location))
        thread.start()
    else:
        messagebox.showerror("Error", validation_result)

    thread = threading.Thread(target=main_function, args=(menu_url, headers, save_location))
    thread.start()

def toggle_log():
    if log_text.winfo_ismapped():
        log_frame.grid_forget()
        expand_button.config(text="Show Log")
    else:
        log_frame.grid(row=6, column=0, columnspan=3, pady=10)
        expand_button.config(text="Hide Log")

def fetch_data_from_endpoint(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        log(f"Error {response.status_code} accessing URL {url}: {response.content}")
        return None

def log(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)

def main_function(menu_url, headers, save_location):
    global cancel_download
    try:
        response = requests.get(menu_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['dataset'])
            total_datasets = len(df)
            for index, row in df.iterrows():
                if cancel_download:
                    reset_interface()
                    return

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
