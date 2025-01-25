import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import queue
import os
import sys

# Imports from drive_connection module
from src.drive_connection import (
    load_api_key,
    setup_drive_service,
    create_directories,
    download_file,
    process_file,
    list_files_in_folder,
    extract_folder_id,

)
BASE_DIR = "../data"  # "../" moves one level up from the current folder

def load_folder_config(config_file="drive_folders.txt"):
    """Load folder configurations from a text file"""
    folders = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ',' in line:
                    name, url = line.split(',', 1)
                    folders[name.strip()] = url.strip()
        return folders
    except Exception as e:
        print(f"Error loading folder config: {e}")
        return {}

class DriveDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive File Downloader")
        self.root.geometry("800x600")
        
        self.log_queue = queue.Queue()
        self.files = []
        self.folders_config = {}
        
        # Variables
        self.api_key_path = tk.StringVar()
        self.folder_id = tk.StringVar()
        self.selected_folder = tk.StringVar()
        self.download_status = tk.StringVar(value="En attente...")
        self.config_file_path = tk.StringVar(value="drive_folders.txt")
        
        # Setup folder selection callback
        self.selected_folder.trace('w', self.on_folder_selected)
        
        self.setup_gui()
        self.start_log_monitor()
        self.load_folders_config()

    def setup_gui(self):
        """Setup the GUI elements"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # API Key Selection
        ttk.Label(config_frame, text="Fichier API Key:").grid(row=0, column=0, padx=5)
        ttk.Entry(config_frame, textvariable=self.api_key_path, width=40).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="Parcourir", command=self.browse_api_key).grid(
            row=0, column=2, padx=5)

        # Folder Config File Selection
        ttk.Label(config_frame, text="Fichier Config Dossiers:").grid(row=1, column=0, padx=5)
        ttk.Entry(config_frame, textvariable=self.config_file_path, width=40).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="Parcourir", command=self.browse_config_file).grid(
            row=1, column=2, padx=5)

        # Folder Selection
        ttk.Label(config_frame, text="Sélection Dossier:").grid(row=2, column=0, padx=5)
        self.folder_combo = ttk.Combobox(
            config_frame,
            textvariable=self.selected_folder,
            values=[],
            width=37
        )
        self.folder_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="Rafraîchir", command=self.refresh_folders).grid(
            row=2, column=2, padx=5)

        # Manual Folder ID
        ttk.Label(config_frame, text="OU Folder ID manuel:").grid(row=3, column=0, padx=5)
        ttk.Entry(config_frame, textvariable=self.folder_id, width=40).grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="Lister Fichiers", command=self.list_files).grid(
            row=3, column=2, padx=5)

        # Files List Frame
        files_frame = ttk.LabelFrame(main_frame, text="Fichiers disponibles", padding="5")
        files_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Files Listbox with Scrollbar
        self.files_listbox = tk.Listbox(files_frame, height=6)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=scrollbar.set)

        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate')
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Label(progress_frame, textvariable=self.download_status).grid(row=1, column=0)

        # Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Button(button_frame, text="Télécharger", command=self.start_download).grid(
            row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Arrêter", command=self.stop_download).grid(
            row=0, column=1, padx=5)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

    def browse_api_key(self):
        """Open file dialog to select API key file"""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier API Key",
            filetypes=(("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*"))
        )
        if filename:
            self.api_key_path.set(filename)
            self.log_message(f"Fichier API key sélectionné: {filename}")

    def browse_config_file(self):
        """Open file dialog to select folder configuration file"""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier de configuration des dossiers",
            filetypes=(("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*"))
        )
        if filename:
            self.config_file_path.set(filename)
            self.log_message(f"Fichier de configuration sélectionné: {filename}")
            self.load_folders_config()

    def load_folders_config(self):
        """Load folder configuration from file"""
        try:
            self.folders_config = load_folder_config(self.config_file_path.get())
            self.folder_combo['values'] = list(self.folders_config.keys())
            self.log_message(f"Configuration chargée: {len(self.folders_config)} dossiers trouvés")
        except Exception as e:
            self.log_message(f"Erreur lors du chargement de la configuration: {str(e)}")

    def refresh_folders(self):
        """Refresh folder list from configuration file"""
        self.load_folders_config()
        self.log_message("Liste des dossiers mise à jour")

    def on_folder_selected(self, *args):
        """Handle folder selection from dropdown"""
        selected = self.selected_folder.get()
        if selected in self.folders_config:
            folder_url = self.folders_config[selected]
            folder_id = extract_folder_id(folder_url)
            self.folder_id.set(folder_id)
            self.log_message(f"Dossier sélectionné: {selected}")

    def log_message(self, message):
        self.log_queue.put(message)

    def update_log_display(self):
        while True:
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_queue.task_done()
            except queue.Empty:
                break
        self.root.after(100, self.update_log_display)

    def start_log_monitor(self):
        self.root.after(100, self.update_log_display)

    def update_progress(self, value):
        self.progress_bar['value'] = value
        self.download_status.set(f"Progression: {value}%")

    def list_files(self):
        try:
            if not self.api_key_path.get() or not self.folder_id.get():
                self.log_message("Erreur: API Key et nom/ID du dossier requis")
                return

            self.log_message(f"Tentative d'accès au dossier: {self.folder_id.get()}")
            api_key = load_api_key(self.api_key_path.get())
            drive_service = setup_drive_service(api_key)
            
            try:
                self.files = list_files_in_folder(drive_service, self.folder_id.get())
                
                self.files_listbox.delete(0, tk.END)
                for file in self.files:
                    size = int(file.get('size', 0)) // 1024 if file.get('size') else 0
                    self.files_listbox.insert(tk.END, f"{file['name']} ({size}KB)")
                
                self.log_message(f"Trouvé {len(self.files)} fichiers dans le dossier")
                
            except Exception as e:
                self.log_message(f"Erreur lors de la liste des fichiers: {str(e)}")
                self.log_message("Vérifiez que le nom/ID du dossier est correct")
                
        except Exception as e:
            self.log_message(f"Erreur: {str(e)}")

    def progress_callback(self, progress):
        self.root.after(0, lambda: self.update_progress(progress))

    def start_download(self):
        try:
            selection = self.files_listbox.curselection()
            if not selection:
                self.log_message("Erreur: Veuillez sélectionner un fichier")
                return

            file_index = selection[0]
            file = self.files[file_index]
            
            self.download_thread = threading.Thread(
                target=self.download_process,
                args=(file['id'], file['name'])
            )
            self.download_thread.daemon = True
            self.download_thread.start()
            
        except Exception as e:
            self.log_message(f"Erreur: {str(e)}")

    def stop_download(self):
        if hasattr(self, 'download_thread') and self.download_thread.is_alive():
            self.log_message("Arrêt demandé...")
            self.update_progress(0)

    def download_process(self, file_id, file_name):
        try:
            self.log_message(f"Téléchargement de {file_name}...")
            
            api_key = load_api_key(self.api_key_path.get())
            drive_service = setup_drive_service(api_key)
            create_directories()
            
            # Updated paths to use BASE_DIR
            destination_path = os.path.join(BASE_DIR, "download", file_name)
            download_file(drive_service, file_id, destination_path, self.progress_callback)
            
            if file_name.endswith('.csv'):
                self.log_message("Traitement du fichier CSV...")
                processed_file_path = os.path.join(BASE_DIR, "preprocessed", file_name)
                process_file(destination_path, processed_file_path)
                
            self.log_message("Opération terminée avec succès!")
            self.update_progress(100)
            
        except Exception as e:
            self.log_message(f"Erreur: {str(e)}")
            self.update_progress(0)

def main():
    root = tk.Tk()
    app = DriveDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()