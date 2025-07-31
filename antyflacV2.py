import os
import shutil
import re
import random
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# Поддерживаемые аудио форматы
AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.wma'}

class MusicOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Продвинутый организатор музыки")
        self.root.geometry("700x600")
        self.folder_path = ""
        self.audio_files = []
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Выбор папки
        ttk.Label(main_frame, text="1. Выберите папку с музыкой:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_label = ttk.Label(folder_frame, text="Папка не выбрана", relief="sunken", padding="5")
        self.folder_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder_frame, text="Выбрать папку", command=self.select_folder).grid(row=0, column=1)
        ttk.Button(folder_frame, text="Сканировать", command=self.scan_files).grid(row=0, column=2, padx=(5, 0))
        
        # Фильтры файлов
        filter_frame = ttk.LabelFrame(main_frame, text="2. Фильтры файлов", padding="5")
        filter_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        filter_frame.columnconfigure(0, weight=1)
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(2, weight=1)
        
        # Выбор форматов
        self.format_vars = {}
        formats_row1 = ['.mp3', '.m4a', '.wav', '.flac']
        formats_row2 = ['.aac', '.ogg', '.wma']
        
        for i, fmt in enumerate(formats_row1):
            var = tk.BooleanVar(value=True)
            self.format_vars[fmt] = var
            ttk.Checkbutton(filter_frame, text=fmt.upper(), variable=var).grid(
                row=0, column=i, sticky=tk.W, padx=(0, 10))
        
        for i, fmt in enumerate(formats_row2):
            var = tk.BooleanVar(value=True)
            self.format_vars[fmt] = var
            ttk.Checkbutton(filter_frame, text=fmt.upper(), variable=var).grid(
                row=1, column=i, sticky=tk.W, padx=(0, 10))
        
        # Опции обработки
        options_frame = ttk.LabelFrame(main_frame, text="3. Опции обработки", padding="5")
        options_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Обработка имен файлов
        name_frame = ttk.Frame(options_frame)
        name_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.remove_numbers = tk.BooleanVar(value=True)
        ttk.Checkbutton(name_frame, text="Убирать номера из начала названий (01. Song.mp3 → Song.mp3)", 
                       variable=self.remove_numbers).grid(row=0, column=0, sticky=tk.W)
        
        self.remove_brackets = tk.BooleanVar(value=False)
        ttk.Checkbutton(name_frame, text="Убирать содержимое в скобках [feat. Artist] (Artist)", 
                       variable=self.remove_brackets).grid(row=1, column=0, sticky=tk.W)
        
        self.normalize_spaces = tk.BooleanVar(value=True)
        ttk.Checkbutton(name_frame, text="Нормализовать пробелы", 
                       variable=self.normalize_spaces).grid(row=2, column=0, sticky=tk.W)
        
        # Опции файлов
        file_frame = ttk.Frame(options_frame)
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.shuffle_files = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Перемешать файлы случайным образом", 
                       variable=self.shuffle_files).grid(row=0, column=0, sticky=tk.W)
        
        self.replace_existing = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Заменять существующие файлы", 
                       variable=self.replace_existing).grid(row=1, column=0, sticky=tk.W)
        
        self.remove_empty_folders = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Удалять пустые папки после обработки", 
                       variable=self.remove_empty_folders).grid(row=2, column=0, sticky=tk.W)
        
        self.create_backup = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_frame, text="Создать резервную копию (список файлов)", 
                       variable=self.create_backup).grid(row=3, column=0, sticky=tk.W)
        
        # Дополнительные фильтры
        advanced_frame = ttk.LabelFrame(main_frame, text="4. Дополнительные фильтры", padding="5")
        advanced_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Минимальный размер файла
        size_frame = ttk.Frame(advanced_frame)
        size_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.use_min_size = tk.BooleanVar(value=False)
        ttk.Checkbutton(size_frame, text="Фильтр по размеру файла", 
                       variable=self.use_min_size, command=self.toggle_size_filter).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Label(size_frame, text="Мин. размер (КБ):").grid(row=0, column=1, padx=(10, 5))
        self.min_size_var = tk.StringVar(value="100")
        self.size_entry = ttk.Entry(size_frame, textvariable=self.min_size_var, width=10, state="disabled")
        self.size_entry.grid(row=0, column=2)
        
        # Исключить файлы по маске
        exclude_frame = ttk.Frame(advanced_frame)
        exclude_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.use_exclude_pattern = tk.BooleanVar(value=False)
        ttk.Checkbutton(exclude_frame, text="Исключить файлы по маске", 
                       variable=self.use_exclude_pattern, command=self.toggle_exclude_filter).grid(row=0, column=0, padx=(0, 10))
        
        self.exclude_pattern = tk.StringVar(value="")
        self.exclude_entry = ttk.Entry(exclude_frame, textvariable=self.exclude_pattern, width=30, state="disabled")
        self.exclude_entry.grid(row=0, column=1, padx=(10, 0))
        
        # Информация о найденных файлах
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="5")
        info_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.info_label = ttk.Label(info_frame, text="Сначала выберите папку и нажмите 'Сканировать'")
        self.info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, pady=10)
        
        self.organize_button = ttk.Button(button_frame, text="Организовать файлы", 
                                         command=self.start_organization, state="disabled")
        self.organize_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="Сохранить настройки", 
                  command=self.save_settings).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="Сбросить настройки", 
                  command=self.reset_settings).grid(row=0, column=2)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог операций", padding="5")
        log_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Настройка растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
    
    def toggle_size_filter(self):
        """Включает/выключает фильтр по размеру файла"""
        if self.use_min_size.get():
            self.size_entry.config(state="normal")
        else:
            self.size_entry.config(state="disabled")
    
    def toggle_exclude_filter(self):
        """Включает/выключает фильтр исключения файлов"""
        if self.use_exclude_pattern.get():
            self.exclude_entry.config(state="normal")
        else:
            self.exclude_entry.config(state="disabled")
    
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с музыкой")
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.config(text=folder_path)
            self.log(f"Выбрана папка: {folder_path}")
    
    def scan_files(self):
        if not self.folder_path:
            messagebox.showerror("Ошибка", "Сначала выберите папку")
            return
        
        self.log("Сканирование файлов...")
        
        # Получаем выбранные форматы
        selected_formats = {fmt for fmt, var in self.format_vars.items() if var.get()}
        
        if not selected_formats:
            messagebox.showerror("Ошибка", "Выберите хотя бы один формат файлов")
            return
        
        # Сканируем файлы
        self.audio_files = []
        min_size = 0
        if self.use_min_size.get():
            try:
                min_size = int(self.min_size_var.get() or 0) * 1024  # Конвертируем в байты
            except ValueError:
                min_size = 0
        
        exclude_pattern = ""
        if self.use_exclude_pattern.get():
            exclude_pattern = self.exclude_pattern.get().strip()
        
        for root, dirs, files in os.walk(self.folder_path):
            # Пропускаем файлы в главной папке
            if root == self.folder_path:
                continue
                
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in selected_formats:
                    file_path = os.path.join(root, file)
                    
                    # Проверяем размер файла только если фильтр включен
                    if self.use_min_size.get() and min_size > 0:
                        try:
                            if os.path.getsize(file_path) < min_size:
                                continue
                        except OSError:
                            continue
                    
                    # Проверяем паттерн исключения только если фильтр включен
                    if self.use_exclude_pattern.get() and exclude_pattern and re.search(exclude_pattern, file, re.IGNORECASE):
                        continue
                    
                    self.audio_files.append(file_path)
        
        # Обновляем информацию
        formats_info = ", ".join(fmt.upper() for fmt in selected_formats)
        self.info_label.config(text=f"Найдено {len(self.audio_files)} файлов ({formats_info})")
        self.log(f"Найдено {len(self.audio_files)} аудио файлов")
        
        # Активируем кнопку организации
        if self.audio_files:
            self.organize_button.config(state="normal")
        else:
            self.organize_button.config(state="disabled")
    
    def start_organization(self):
        if not self.audio_files:
            messagebox.showerror("Ошибка", "Сначала отсканируйте файлы")
            return
        
        # Подтверждение
        result = messagebox.askyesno(
            "Подтверждение", 
            f"Вы собираетесь переместить {len(self.audio_files)} файлов в главную папку.\n"
            "Продолжить?"
        )
        
        if not result:
            return
        
        self.organize_button.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        
        # Запускаем организацию в отдельном потоке
        thread = threading.Thread(target=self.organize_files)
        thread.daemon = True
        thread.start()
    
    def organize_files(self):
        try:
            # Создаем резервную копию если нужно
            if self.create_backup.get():
                self.create_backup_list()
            
            # Перемешиваем файлы если нужно
            files_to_process = self.audio_files.copy()
            if self.shuffle_files.get():
                random.shuffle(files_to_process)
                self.log("Файлы перемешаны случайным образом")
            
            # Настройка прогресс бара
            self.progress['maximum'] = len(files_to_process)
            self.progress['value'] = 0
            
            moved_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, file_path in enumerate(files_to_process):
                try:
                    filename = os.path.basename(file_path)
                    new_filename = self.process_filename(filename)
                    new_file_path = os.path.join(self.folder_path, new_filename)
                    
                    # Проверяем существование файла
                    if os.path.exists(new_file_path) and not self.replace_existing.get():
                        self.log(f"Пропущен (уже существует): {new_filename}")
                        skipped_count += 1
                    else:
                        # Перемещаем файл
                        if os.path.exists(new_file_path):
                            os.remove(new_file_path)
                        
                        shutil.move(file_path, new_file_path)
                        self.log(f"Перемещен: {filename} → {new_filename}")
                        moved_count += 1
                    
                except Exception as e:
                    self.log(f"Ошибка при обработке {os.path.basename(file_path)}: {e}")
                    error_count += 1
                
                # Обновляем прогресс
                self.progress['value'] = i + 1
                self.root.update_idletasks()
            
            # Удаляем пустые папки если нужно
            if self.remove_empty_folders.get():
                removed_folders = self.remove_empty_folders_func()
                self.log(f"Удалено {removed_folders} пустых папок")
            
            # Итоги
            self.log("-" * 50)
            self.log("Организация завершена!")
            self.log(f"Перемещено: {moved_count}")
            self.log(f"Пропущено: {skipped_count}")
            self.log(f"Ошибок: {error_count}")
            
        except Exception as e:
            self.log(f"Критическая ошибка: {e}")
        finally:
            self.organize_button.config(state="normal")
            # Обновляем список файлов
            self.scan_files()
    
    def process_filename(self, filename):
        """Обрабатывает имя файла согласно настройкам"""
        name, ext = os.path.splitext(filename)
        
        # Убираем номера из начала
        if self.remove_numbers.get():
            name = re.sub(r'^\d+\.\s*', '', name)
        
        # Убираем содержимое в скобках
        if self.remove_brackets.get():
            name = re.sub(r'\[.*?\]', '', name)
            name = re.sub(r'\(.*?\)', '', name)
        
        # Нормализуем пробелы
        if self.normalize_spaces.get():
            name = re.sub(r'\s+', ' ', name).strip()
        
        return name + ext
    
    def create_backup_list(self):
        """Создает резервный список файлов"""
        try:
            backup_file = os.path.join(self.folder_path, f"backup_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"Резервный список файлов\n")
                f.write(f"Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Папка: {self.folder_path}\n")
                f.write("-" * 50 + "\n\n")
                
                for file_path in self.audio_files:
                    rel_path = os.path.relpath(file_path, self.folder_path)
                    f.write(f"{rel_path}\n")
            
            self.log(f"Создан резервный список: {os.path.basename(backup_file)}")
        except Exception as e:
            self.log(f"Ошибка создания резервной копии: {e}")
    
    def remove_empty_folders_func(self):
        """Удаляет пустые папки"""
        removed_count = 0
        
        for root, dirs, files in os.walk(self.folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        removed_count += 1
                except Exception:
                    pass
        
        return removed_count
    
    def save_settings(self):
        """Сохраняет текущие настройки"""
        settings = {
            'formats': {fmt: var.get() for fmt, var in self.format_vars.items()},
            'remove_numbers': self.remove_numbers.get(),
            'remove_brackets': self.remove_brackets.get(),
            'normalize_spaces': self.normalize_spaces.get(),
            'shuffle_files': self.shuffle_files.get(),
            'replace_existing': self.replace_existing.get(),
            'remove_empty_folders': self.remove_empty_folders.get(),
            'create_backup': self.create_backup.get(),
            'use_min_size': self.use_min_size.get(),
            'min_size': self.min_size_var.get(),
            'use_exclude_pattern': self.use_exclude_pattern.get(),
            'exclude_pattern': self.exclude_pattern.get()
        }
        
        try:
            with open('music_organizer_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.log("Настройки сохранены")
        except Exception as e:
            self.log(f"Ошибка сохранения настроек: {e}")
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        try:
            with open('music_organizer_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Применяем настройки
            for fmt, value in settings.get('formats', {}).items():
                if fmt in self.format_vars:
                    self.format_vars[fmt].set(value)
            
            self.remove_numbers.set(settings.get('remove_numbers', True))
            self.remove_brackets.set(settings.get('remove_brackets', False))
            self.normalize_spaces.set(settings.get('normalize_spaces', True))
            self.shuffle_files.set(settings.get('shuffle_files', True))
            self.replace_existing.set(settings.get('replace_existing', True))
            self.remove_empty_folders.set(settings.get('remove_empty_folders', True))
            self.create_backup.set(settings.get('create_backup', False))
            self.use_min_size.set(settings.get('use_min_size', False))
            self.min_size_var.set(settings.get('min_size', '100'))
            self.use_exclude_pattern.set(settings.get('use_exclude_pattern', False))
            self.exclude_pattern.set(settings.get('exclude_pattern', ''))
            
            # Обновляем состояние полей ввода
            self.toggle_size_filter()
            self.toggle_exclude_filter()
            
        except FileNotFoundError:
            pass  # Файл настроек не существует - используем значения по умолчанию
        except Exception as e:
            self.log(f"Ошибка загрузки настроек: {e}")
    
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        for var in self.format_vars.values():
            var.set(True)
        
        self.remove_numbers.set(True)
        self.remove_brackets.set(False)
        self.normalize_spaces.set(True)
        self.shuffle_files.set(True)
        self.replace_existing.set(True)
        self.remove_empty_folders.set(True)
        self.create_backup.set(False)
        self.use_min_size.set(False)
        self.min_size_var.set('100')
        self.use_exclude_pattern.set(False)
        self.exclude_pattern.set('')
        
        # Обновляем состояние полей ввода
        self.toggle_size_filter()
        self.toggle_exclude_filter()
        
        self.log("Настройки сброшены к значениям по умолчанию")
    
    def log(self, message):
        """Добавляет сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = MusicOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()