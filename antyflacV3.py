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
from ttkthemes import ThemedTk

# Поддерживаемые аудио форматы
AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.wma'}

class MusicOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Продвинутый организатор музыки")
        self.root.geometry("750x700")
        self.folder_path = ""
        self.audio_files = []

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        # Меню
        self.setup_menu()

        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Блок 1: Выбор папки ---
        ttk.Label(main_frame, text="1. Выберите папку с музыкой:", font="-weight bold").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        folder_frame.columnconfigure(0, weight=1)
        self.folder_label = ttk.Label(folder_frame, text="Папка не выбрана", relief="sunken", padding="5")
        self.folder_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(folder_frame, text="Выбрать папку", command=self.select_folder).grid(row=0, column=1)
        ttk.Button(folder_frame, text="Сканировать", command=self.scan_files).grid(row=0, column=2, padx=(5, 0))

        # --- Блок 2: Фильтры файлов ---
        filter_frame = ttk.LabelFrame(main_frame, text="2. Фильтры сканирования", padding="10")
        filter_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        filter_frame.columnconfigure(1, weight=1)

        # Выбор форматов
        self.format_vars = {}
        formats_label = ttk.Label(filter_frame, text="Форматы:")
        formats_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        format_checks_frame = ttk.Frame(filter_frame)
        format_checks_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))

        all_formats = sorted(list(AUDIO_FORMATS))
        for i, fmt in enumerate(all_formats):
            var = tk.BooleanVar(value=True)
            self.format_vars[fmt] = var
            ttk.Checkbutton(format_checks_frame, text=fmt.upper(), variable=var).grid(
                row=i // 4, column=i % 4, sticky=tk.W, padx=(0, 15))

        self.scan_root_folder = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Сканировать файлы в корневой папке",
                        variable=self.scan_root_folder).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # --- Блок 3: Опции обработки ---
        options_frame = ttk.LabelFrame(main_frame, text="3. Опции обработки", padding="10")
        options_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Режим организации
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(mode_frame, text="Режим:").grid(row=0, column=0, sticky=tk.W)
        self.organization_mode = tk.StringVar(value="move_and_rename")
        ttk.Radiobutton(mode_frame, text="Переместить и переименовать", variable=self.organization_mode,
                        value="move_and_rename").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(mode_frame, text="Только переместить", variable=self.organization_mode,
                        value="move_only").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(mode_frame, text="Только переименовать", variable=self.organization_mode,
                        value="rename_only").grid(row=0, column=3, sticky=tk.W, padx=5)


        # Обработка имен файлов
        name_frame = ttk.Frame(options_frame)
        name_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
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
        file_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
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

        # --- Блок 4: Дополнительные фильтры ---
        advanced_frame = ttk.LabelFrame(main_frame, text="4. Дополнительные фильтры", padding="10")
        advanced_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        size_frame = ttk.Frame(advanced_frame)
        size_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.use_min_size = tk.BooleanVar(value=False)
        ttk.Checkbutton(size_frame, text="Фильтр по размеру файла (Мин. КБ):",
                       variable=self.use_min_size, command=self.toggle_size_filter).grid(row=0, column=0, padx=(0, 10))
        self.min_size_var = tk.StringVar(value="100")
        self.size_entry = ttk.Entry(size_frame, textvariable=self.min_size_var, width=10, state="disabled")
        self.size_entry.grid(row=0, column=1)

        exclude_frame = ttk.Frame(advanced_frame)
        exclude_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 5))
        self.use_exclude_pattern = tk.BooleanVar(value=False)
        ttk.Checkbutton(exclude_frame, text="Исключить файлы по маске (regex):",
                       variable=self.use_exclude_pattern, command=self.toggle_exclude_filter).grid(row=0, column=0, padx=(0, 10))
        self.exclude_pattern = tk.StringVar(value="")
        self.exclude_entry = ttk.Entry(exclude_frame, textvariable=self.exclude_pattern, width=30, state="disabled")
        self.exclude_entry.grid(row=0, column=1, padx=(4, 0))

        # --- Блок 5: Информация и управление ---
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="10")
        info_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.info_label = ttk.Label(info_frame, text="Сначала выберите папку и нажмите 'Сканировать'")
        self.info_label.grid(row=0, column=0, sticky=tk.W)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, pady=10)
        self.organize_button = ttk.Button(button_frame, text="Организовать файлы",
                                         command=self.start_organization, state="disabled")
        self.organize_button.grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Сохранить настройки",
                  command=self.save_settings).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="Сбросить настройки",
                  command=self.reset_settings).grid(row=0, column=2)

        # --- Блок 6: Прогресс и лог ---
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

        log_frame = ttk.LabelFrame(main_frame, text="Лог операций", padding="10")
        log_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, relief="sunken", borderwidth=1)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)

    def setup_menu(self):
        """Создает верхнее меню"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Меню "Вид" для смены темы
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Вид", menu=view_menu)
        self.theme_var = tk.StringVar(value="light")
        view_menu.add_radiobutton(label="Светлая тема", variable=self.theme_var, value="light", command=self.toggle_theme)
        view_menu.add_radiobutton(label="Тёмная тема", variable=self.theme_var, value="dark", command=self.toggle_theme)

    def toggle_theme(self):
        """Переключает тему оформления"""
        theme = self.theme_var.get()
        if theme == "dark":
            self.root.set_theme("equilux")
            self.log_text.config(bg="#464646", fg="white")
        else:
            self.root.set_theme("arc")
            self.log_text.config(bg="white", fg="black")
        self.log(f"Тема изменена на: {'Тёмная' if theme == 'dark' else 'Светлая'}")

    def toggle_size_filter(self):
        self.size_entry.config(state="normal" if self.use_min_size.get() else "disabled")

    def toggle_exclude_filter(self):
        self.exclude_entry.config(state="normal" if self.use_exclude_pattern.get() else "disabled")

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с музыкой")
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.config(text=folder_path)
            self.log(f"Выбрана папка: {folder_path}")
            self.organize_button.config(state="disabled")
            self.info_label.config(text="Нажмите 'Сканировать', чтобы найти файлы.")


    def scan_files(self):
        if not self.folder_path:
            messagebox.showerror("Ошибка", "Сначала выберите папку")
            return

        self.log("Сканирование файлов...")
        selected_formats = {fmt for fmt, var in self.format_vars.items() if var.get()}
        if not selected_formats:
            messagebox.showerror("Ошибка", "Выберите хотя бы один формат файлов")
            return

        self.audio_files = []
        min_size = int(self.min_size_var.get() or 0) * 1024 if self.use_min_size.get() else 0
        exclude_pattern = self.exclude_pattern.get().strip() if self.use_exclude_pattern.get() else ""

        for root, dirs, files in os.walk(self.folder_path):
            if root == self.folder_path and not self.scan_root_folder.get():
                # Пропускаем файлы в главной папке, если опция выключена
                # но продолжаем обход вложенных папок
                pass

            for file in files:
                if root == self.folder_path and not self.scan_root_folder.get():
                    continue

                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in selected_formats:
                    file_path = os.path.join(root, file)
                    if self.use_min_size.get() and os.path.getsize(file_path) < min_size:
                        continue
                    if exclude_pattern and re.search(exclude_pattern, file, re.IGNORECASE):
                        continue
                    self.audio_files.append(file_path)

        formats_info = ", ".join(sorted([fmt.upper() for fmt in selected_formats]))
        self.info_label.config(text=f"Найдено {len(self.audio_files)} файлов ({formats_info})")
        self.log(f"Найдено {len(self.audio_files)} аудио файлов")

        if self.audio_files:
            self.organize_button.config(state="normal")
        else:
            self.organize_button.config(state="disabled")

    def start_organization(self):
        if not self.audio_files:
            messagebox.showerror("Ошибка", "Сначала отсканируйте файлы")
            return

        mode_text = {
            "move_and_rename": "переместить и переименовать",
            "move_only": "только переместить",
            "rename_only": "только переименовать"
        }.get(self.organization_mode.get(), "неизвестный режим")

        result = messagebox.askyesno(
            "Подтверждение",
            f"Вы собираетесь обработать {len(self.audio_files)} файлов в режиме '{mode_text}'.\n"
            "Это действие нельзя будет отменить.\n\nПродолжить?"
        )
        if not result:
            return

        self.organize_button.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        thread = threading.Thread(target=self.organize_files, daemon=True)
        thread.start()

    def organize_files(self):
        try:
            if self.create_backup.get():
                self.create_backup_list()

            files_to_process = self.audio_files.copy()
            if self.shuffle_files.get():
                random.shuffle(files_to_process)
                self.log("Файлы перемешаны случайным образом")

            self.progress['maximum'] = len(files_to_process)
            self.progress['value'] = 0
            moved_count, renamed_count, skipped_count, error_count = 0, 0, 0, 0
            mode = self.organization_mode.get()

            for i, file_path in enumerate(files_to_process):
                try:
                    original_dir = os.path.dirname(file_path)
                    original_filename = os.path.basename(file_path)
                    new_filename = self.process_filename(original_filename)

                    # Определяем пути и действия в зависимости от режима
                    if mode == "move_and_rename":
                        target_path = os.path.join(self.folder_path, new_filename)
                        action = self.perform_move(file_path, target_path)
                    elif mode == "move_only":
                        target_path = os.path.join(self.folder_path, original_filename)
                        action = self.perform_move(file_path, target_path)
                    elif mode == "rename_only":
                        if original_filename == new_filename:
                             action = "skipped" # Пропускаем, если имя не изменилось
                        else:
                            target_path = os.path.join(original_dir, new_filename)
                            action = self.perform_move(file_path, target_path)
                    else:
                        action = "error"

                    # Логирование результатов
                    if action == "processed":
                        log_msg = ""
                        if mode == "move_and_rename":
                            log_msg = f"Перемещен и переименован: {original_filename} → {new_filename}"
                            moved_count += 1; renamed_count +=1
                        elif mode == "move_only":
                            log_msg = f"Перемещен: {original_filename}"
                            moved_count += 1
                        elif mode == "rename_only":
                            log_msg = f"Переименован: {original_filename} → {new_filename}"
                            renamed_count += 1
                        self.log(log_msg)
                    elif action == "skipped":
                        self.log(f"Пропущен (файл уже существует или имя не изменилось): {original_filename}")
                        skipped_count += 1
                    
                except Exception as e:
                    self.log(f"Ошибка при обработке {original_filename}: {e}")
                    error_count += 1
                finally:
                    self.progress['value'] = i + 1
                    self.root.update_idletasks()

            if self.remove_empty_folders.get() and (mode == "move_and_rename" or mode == "move_only"):
                removed_folders = self.remove_empty_folders_func()
                self.log(f"Удалено {removed_folders} пустых папок")

            self.log("-" * 50)
            self.log("Организация завершена!")
            self.log(f"Обработано (перемещено/переименовано): {moved_count or renamed_count}")
            self.log(f"Пропущено: {skipped_count}")
            self.log(f"Ошибок: {error_count}")

        except Exception as e:
            self.log(f"Критическая ошибка: {e}")
        finally:
            self.organize_button.config(state="normal")
            self.scan_files() # Обновляем список файлов

    def perform_move(self, source_path, dest_path):
        """Перемещает или переименовывает файл, обрабатывая конфликты."""
        if os.path.exists(dest_path):
            if self.replace_existing.get():
                if source_path.lower() != dest_path.lower(): # Защита от перезаписи самого себя
                    os.remove(dest_path)
                else:
                    return "skipped" # Файл уже на месте
            else:
                return "skipped"
        
        shutil.move(source_path, dest_path)
        return "processed"

    def process_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if self.remove_numbers.get():
            name = re.sub(r'^\d+\.\s*', '', name)
        if self.remove_brackets.get():
            name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
        if self.normalize_spaces.get():
            name = re.sub(r'\s+', ' ', name).strip()
        return name + ext

    def create_backup_list(self):
        try:
            backup_file = os.path.join(self.folder_path, f"backup_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"Резервный список файлов\nСоздан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Папка: {self.folder_path}\n" + "-" * 50 + "\n\n")
                for file_path in self.audio_files:
                    f.write(f"{os.path.relpath(file_path, self.folder_path)}\n")
            self.log(f"Создан резервный список: {os.path.basename(backup_file)}")
        except Exception as e:
            self.log(f"Ошибка создания резервной копии: {e}")

    def remove_empty_folders_func(self):
        removed_count = 0
        for root, dirs, files in os.walk(self.folder_path, topdown=False):
            if root == self.folder_path: continue
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        removed_count += 1
                except OSError:
                    pass
        return removed_count

    def save_settings(self):
        settings = {
            'theme': self.theme_var.get(),
            'formats': {fmt: var.get() for fmt, var in self.format_vars.items()},
            'organization_mode': self.organization_mode.get(),
            'scan_root_folder': self.scan_root_folder.get(),
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
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.log("Настройки сохранены")
        except Exception as e:
            self.log(f"Ошибка сохранения настроек: {e}")

    def load_settings(self):
        try:
            with open('music_organizer_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.theme_var.set(settings.get('theme', 'light'))
            self.toggle_theme()

            for fmt, value in settings.get('formats', {}).items():
                if fmt in self.format_vars: self.format_vars[fmt].set(value)
            
            self.organization_mode.set(settings.get('organization_mode', 'move_and_rename'))
            self.scan_root_folder.set(settings.get('scan_root_folder', False))
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

            self.toggle_size_filter()
            self.toggle_exclude_filter()
            self.log("Настройки загружены")

        except FileNotFoundError:
            self.reset_settings(log_msg=False) # Используем значения по умолчанию, если файла нет
            self.log("Файл настроек не найден, использованы значения по умолчанию.")
        except Exception as e:
            self.log(f"Ошибка загрузки настроек: {e}")

    def reset_settings(self, log_msg=True):
        self.theme_var.set("light")
        self.toggle_theme()
        for var in self.format_vars.values(): var.set(True)

        self.organization_mode.set("move_and_rename")
        self.scan_root_folder.set(False)
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

        self.toggle_size_filter()
        self.toggle_exclude_filter()
        if log_msg:
            self.log("Настройки сброшены к значениям по умолчанию")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

def main():
    root = ThemedTk(theme="arc")
    app = MusicOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()