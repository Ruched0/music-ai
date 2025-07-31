import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image
import threading

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Переименователь файлов с конвертацией в PNG")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.folder_path = ""
        self.files_list = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Конфигурация растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Выбор папки
        ttk.Label(main_frame, text="Папка с файлами:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state="readonly")
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(folder_frame, text="Выбрать папку", command=self.select_folder).grid(row=0, column=1)
        ttk.Button(folder_frame, text="Сканировать файлы", command=self.scan_files).grid(row=0, column=2, padx=(5, 0))
        
        # Опции
        options_frame = ttk.LabelFrame(main_frame, text="Настройки", padding="5")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.convert_to_png = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Конвертировать все изображения в PNG", 
                       variable=self.convert_to_png).grid(row=0, column=0, sticky=tk.W)
        
        self.keep_original = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Сохранить оригинальные файлы", 
                       variable=self.keep_original).grid(row=1, column=0, sticky=tk.W)
        
        # Превью файлов
        preview_frame = ttk.LabelFrame(main_frame, text="Превью переименования", padding="5")
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15, width=80)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопки действий
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Выполнить переименование", 
                  command=self.start_rename_process).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_preview).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(buttons_frame, text="Выход", command=self.root.quit).grid(row=0, column=2)
        
        # Прогресс бар
        self.progress_var = tk.StringVar(value="Готов к работе")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=5, column=0, columnspan=3, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с файлами")
        if folder:
            self.folder_path = folder
            self.folder_var.set(folder)
            self.scan_files()
    
    def scan_files(self):
        if not self.folder_path:
            messagebox.showwarning("Предупреждение", "Сначала выберите папку!")
            return
        
        # Поддерживаемые форматы изображений
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        
        try:
            all_files = []
            for item in os.listdir(self.folder_path):
                item_path = os.path.join(self.folder_path, item)
                if os.path.isfile(item_path):
                    file_ext = os.path.splitext(item)[1].lower()
                    if file_ext in image_extensions:
                        all_files.append(item)
            
            self.files_list = sorted(all_files)
            self.update_preview()
            
            if self.files_list:
                self.progress_var.set(f"Найдено {len(self.files_list)} изображений")
            else:
                self.progress_var.set("Изображения не найдены")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сканировании папки: {e}")
    
    def update_preview(self):
        self.preview_text.delete(1.0, tk.END)
        
        if not self.files_list:
            self.preview_text.insert(tk.END, "Файлы не найдены или папка не выбрана.")
            return
        
        self.preview_text.insert(tk.END, f"Будет переименовано {len(self.files_list)} файлов:\n\n")
        
        for i, filename in enumerate(self.files_list, 1):
            old_name = filename
            
            if self.convert_to_png.get():
                new_name = f"{i}.png"
                action = " (конвертация в PNG)" if not filename.lower().endswith('.png') else ""
            else:
                file_ext = os.path.splitext(filename)[1]
                new_name = f"{i}{file_ext}"
                action = ""
            
            self.preview_text.insert(tk.END, f"{i:3d}. {old_name} → {new_name}{action}\n")
    
    def start_rename_process(self):
        if not self.files_list:
            messagebox.showwarning("Предупреждение", "Нет файлов для обработки!")
            return
        
        # Подтверждение
        if not messagebox.askyesno("Подтверждение", 
                                  f"Переименовать {len(self.files_list)} файлов?\n"
                                  f"Конвертация в PNG: {'Да' if self.convert_to_png.get() else 'Нет'}\n"
                                  f"Сохранить оригиналы: {'Да' if self.keep_original.get() else 'Нет'}"):
            return
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.rename_files_thread, daemon=True)
        thread.start()
    
    def rename_files_thread(self):
        success_count = 0
        total_files = len(self.files_list)
        
        self.progress_bar['maximum'] = total_files
        self.progress_bar['value'] = 0
        
        for i, filename in enumerate(self.files_list, 1):
            try:
                old_path = os.path.join(self.folder_path, filename)
                
                if self.convert_to_png.get():
                    new_name = f"{i}.png"
                    new_path = os.path.join(self.folder_path, new_name)
                    
                    # Конвертация в PNG
                    if not filename.lower().endswith('.png'):
                        # Создаем резервную копию если нужно
                        if self.keep_original.get():
                            backup_name = f"original_{filename}"
                            backup_path = os.path.join(self.folder_path, backup_name)
                            if not os.path.exists(backup_path):
                                os.rename(old_path, backup_path)
                                old_path = backup_path
                        
                        # Конвертируем в PNG
                        with Image.open(old_path) as img:
                            # Конвертируем в RGB если нужно (для JPEG совместимости)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                img = img.convert('RGBA')
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            img.save(new_path, 'PNG')
                        
                        # Удаляем оригинал если не нужно сохранять
                        if not self.keep_original.get():
                            os.remove(old_path)
                    else:
                        # Простое переименование PNG файла
                        os.rename(old_path, new_path)
                else:
                    # Простое переименование без конвертации
                    file_ext = os.path.splitext(filename)[1]
                    new_name = f"{i}{file_ext}"
                    new_path = os.path.join(self.folder_path, new_name)
                    os.rename(old_path, new_path)
                
                success_count += 1
                
                # Обновляем прогресс в главном потоке
                self.root.after(0, self.update_progress, i, total_files, f"Обработано: {filename}")
                
            except Exception as e:
                self.root.after(0, self.show_error, f"Ошибка при обработке {filename}: {e}")
        
        # Завершение
        self.root.after(0, self.finish_process, success_count, total_files)
    
    def update_progress(self, current, total, message):
        self.progress_bar['value'] = current
        self.progress_var.set(f"{message} ({current}/{total})")
        self.root.update_idletasks()
    
    def show_error(self, error_message):
        messagebox.showerror("Ошибка", error_message)
    
    def finish_process(self, success_count, total_files):
        self.progress_var.set(f"Готово! Обработано {success_count} из {total_files} файлов")
        messagebox.showinfo("Завершено", f"Успешно обработано {success_count} из {total_files} файлов!")
        
        # Обновляем список файлов
        self.scan_files()
    
    def clear_preview(self):
        self.preview_text.delete(1.0, tk.END)
        self.files_list = []
        self.progress_var.set("Готов к работе")
        self.progress_bar['value'] = 0

def main():
    # Проверяем наличие PIL
    try:
        from PIL import Image
    except ImportError:
        print("Ошибка: Требуется установить библиотеку Pillow")
        print("Выполните команду: pip install Pillow")
        return
    
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()