import os
import shutil
import re
import random
from pathlib import Path

def collect_mp3_files(root_folder):
    """
    Собирает все MP3 файлы из подпапок в главную папку,
    убирает номера из начала названий и перемешивает файлы
    """
    
    # Проверяем, что папка существует
    if not os.path.exists(root_folder):
        print(f"Папка {root_folder} не найдена!")
        return
    
    # Список для хранения найденных MP3 файлов
    mp3_files = []
    
    # Рекурсивно ищем все MP3 файлы
    print("Поиск MP3 файлов...")
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                file_path = os.path.join(root, file)
                # Пропускаем файлы, которые уже в главной папке
                if root != root_folder:
                    mp3_files.append(file_path)
    
    print(f"Найдено {len(mp3_files)} MP3 файлов")
    
    if not mp3_files:
        print("MP3 файлы не найдены!")
        return
    
    # Перемешиваем список файлов
    random.shuffle(mp3_files)
    
    # Обрабатываем каждый файл
    moved_count = 0
    for file_path in mp3_files:
        try:
            # Получаем имя файла
            filename = os.path.basename(file_path)
            
            # Убираем номера из начала названия (например, "18. Sweden.mp3" -> "Sweden.mp3")
            # Регулярное выражение для поиска номера и точки/пробела в начале
            new_filename = re.sub(r'^\d+\.\s*', '', filename)
            
            # Путь для нового файла в главной папке
            new_file_path = os.path.join(root_folder, new_filename)
            
            # Если файл с таким именем уже существует, заменяем его
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
                print(f"Заменен существующий файл: {new_filename}")
            
            # Перемещаем файл
            shutil.move(file_path, new_file_path)
            print(f"Перемещен: {filename} -> {new_filename}")
            moved_count += 1
            
        except Exception as e:
            print(f"Ошибка при обработке {file_path}: {e}")
    
    print(f"\nОбработка завершена! Перемещено {moved_count} файлов.")
    
    # Удаляем пустые папки
    remove_empty_folders(root_folder)

def remove_empty_folders(root_folder):
    """
    Удаляет пустые папки после перемещения файлов
    """
    print("\nУдаление пустых папок...")
    removed_count = 0
    
    for root, dirs, files in os.walk(root_folder, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Проверяем, пуста ли папка
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Удалена пустая папка: {dir_path}")
                    removed_count += 1
            except Exception as e:
                print(f"Ошибка при удалении папки {dir_path}: {e}")
    
    print(f"Удалено {removed_count} пустых папок.")

def main():
    """
    Основная функция
    """
    # Запрашиваем путь к главной папке
    root_folder = input("Введите путь к главной папке с музыкой: ").strip()
    
    # Убираем кавычки, если они есть
    root_folder = root_folder.strip('"\'')
    
    if not root_folder:
        print("Путь не может быть пустым!")
        return
    
    # Конвертируем в абсолютный путь
    root_folder = os.path.abspath(root_folder)
    
    print(f"Обрабатываем папку: {root_folder}")
    
    # Подтверждение действия
    confirm = input("Вы уверены, что хотите переместить все MP3 файлы в главную папку? (y/n): ").strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        collect_mp3_files(root_folder)
    else:
        print("Операция отменена.")

if __name__ == "__main__":
    main()