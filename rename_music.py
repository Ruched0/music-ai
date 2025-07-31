import os
import re # Импортируем модуль для регулярных выражений
import tkinter as tk
from tkinter import filedialog, messagebox

def rename_files_in_folder(folder_path, status_label):
    """
    Улучшенная функция для переименования файлов.
    Более гибко удаляет префиксы.
    """
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Ошибка", "Папка не выбрана или не существует.")
        return

    renamed_count = 0
    processed_count = 0
    try:
        filenames = os.listdir(folder_path)
        for filename in filenames:
            processed_count += 1
            old_file_path = os.path.join(folder_path, filename)

            if not os.path.isfile(old_file_path):
                continue

            # Создаем копию имени для изменений
            new_filename = filename

            # --- ШАГ 1: Более гибко удаляем числовой префикс в начале ---
            # Эта строка удаляет цифры в начале, а также возможные точки, тире и пробелы после них
            # Например, "01. ", "1- ", "2. " и т.д.
            temp_name = re.sub(r'^\s*\d+\s*[\.\-]?\s*', '', new_filename)
            
            # --- ШАГ 2: Ищем разделитель " - " и отделяем название песни ---
            # Разделяем строку по " - ", чтобы отделить исполнителя от названия
            parts = temp_name.split(' - ', 1)
            
            # Если разделитель " - " найден, мы берем вторую часть (название песни)
            if len(parts) > 1:
                new_filename = parts[1].strip() # .strip() убирает случайные пробелы в начале/конце
            else:
                # Если разделитель не найден, возможно, есть только числовой префикс
                # В этом случае мы используем имя файла без числового префикса
                new_filename = temp_name.strip()


            # --- ШАГ 3: Переименовываем, только если имя действительно изменилось ---
            if new_filename != filename and new_filename:
                new_file_path = os.path.join(folder_path, new_filename)
                
                # Проверяем, не существует ли уже файл с таким именем
                if os.path.exists(new_file_path):
                    print(f"Пропущено (файл с именем '{new_filename}' уже существует): '{filename}'")
                    continue

                os.rename(old_file_path, new_file_path)
                renamed_count += 1
                print(f"Переименовано: '{filename}' -> '{new_filename}'")
            else:
                print(f"Пропущено (формат не соответствует): '{filename}'")
        
        status_label.config(text=f"Готово! Обработано: {processed_count}. Переименовано: {renamed_count}")
        messagebox.showinfo("Завершено", f"Процесс завершен.\n\nОбработано файлов: {processed_count}\nПереименовано файлов: {renamed_count}")

    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Произошла ошибка: {e}")
        status_label.config(text="Ошибка!")

def select_folder(folder_path_var, status_label):
    """Открывает диалог выбора папки и сохраняет путь."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path_var.set(folder_selected)
        status_label.config(text=f"Выбрана папка. Готов к запуску.")

def create_gui():
    window = tk.Tk()
    window.title("Переименовщик файлов (Улучшенная версия)")
    window.geometry("550x220")
    window.resizable(False, False)

    folder_path_var = tk.StringVar()

    main_frame = tk.Frame(window, padx=15, pady=15)
    main_frame.pack(fill="both", expand=True)
    
    # --- Верхняя рамка ---
    top_frame = tk.Frame(main_frame)
    top_frame.pack(fill="x", pady=(0, 10))

    select_folder_button = tk.Button(top_frame, text="Выбрать папку...", command=lambda: select_folder(folder_path_var, status_label))
    select_folder_button.pack(side="left", padx=(0, 10))

    folder_label = tk.Label(top_frame, textvariable=folder_path_var, relief="sunken", bg="white", anchor="w", padx=5)
    folder_label.pack(side="left", fill="x", expand=True)

    # --- Кнопка запуска ---
    start_button = tk.Button(main_frame, text="Начать переименование",
                             font=("Arial", 12, "bold"),
                             bg="#28a745", fg="white",
                             command=lambda: rename_files_in_folder(folder_path_var.get(), status_label))
    start_button.pack(pady=10, ipady=8, fill="x")

    # --- Статусная строка внизу ---
    status_label = tk.Label(window, text="1. Выберите папку, затем нажмите 'Начать'", bd=1, relief="sunken", anchor="w", padx=10)
    status_label.pack(side="bottom", fill="x")
    
    window.mainloop()

if __name__ == "__main__":
    create_gui()