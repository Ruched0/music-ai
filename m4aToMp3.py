import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def select_folder():
    """Открывает диалог выбора папки"""
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    folder_path = filedialog.askdirectory(
        title="Выберите папку с M4A файлами для конвертации в MP3"
    )
    
    root.destroy()
    return folder_path

def check_ffmpeg():
    """Проверяет наличие FFmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, encoding='utf-8', errors='ignore')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def find_m4a_files(folder_path):
    """Находит все M4A файлы в папке и подпапках"""
    m4a_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.m4a'):
                m4a_files.append(os.path.join(root, file))
    return m4a_files

def convert_file(input_file, output_file):
    """Конвертирует один файл из M4A в MP3"""
    try:
        # Команда FFmpeg для конвертации
        cmd = [
            'ffmpeg', '-i', input_file,
            '-c:a', 'mp3',   # Аудио кодек
            '-b:a', '128k',  # Битрейт аудио
            '-f', 'mp3',     # Формат выходного файла
            '-y',            # Перезаписать файл если существует
            output_file
        ]
        
        # Выполняем конвертацию с правильной кодировкой
        process = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        
        if process.returncode == 0:
            return True, "Успешно"
        else:
            return False, process.stderr
            
    except Exception as e:
        return False, str(e)

def main():
    print("M4A to MP3 Converter")
    print("=" * 30)
    
    # Выбираем папку через диалог
    print("Выберите папку с M4A файлами...")
    folder_path = select_folder()
    
    if not folder_path:
        print("Папка не выбрана. Выход.")
        return
    
    print(f"Выбрана папка: {folder_path}")
    print()
    
    # Проверяем наличие FFmpeg
    if not check_ffmpeg():
        print("Ошибка: FFmpeg не найден!")
        print("Установите FFmpeg и добавьте его в PATH.")
        print("Скачать можно с https://ffmpeg.org/download.html")
        input("Нажмите Enter для выхода...")
        return
    
    print(f"Поиск M4A файлов в папке: {folder_path}")
    print("Поиск во всех подпапках...")
    
    # Находим все M4A файлы
    m4a_files = find_m4a_files(folder_path)
    
    if not m4a_files:
        print("M4A файлы не найдены")
        input("Нажмите Enter для выхода...")
        return
    
    print(f"Найдено {len(m4a_files)} M4A файлов")
    print("-" * 50)
    
    # Конвертируем каждый файл
    converted_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, m4a_file in enumerate(m4a_files, 1):
        # Создаем имя выходного файла
        output_file = os.path.splitext(m4a_file)[0] + '.mp3'
        
        # Показываем прогресс
        filename = os.path.basename(m4a_file)
        print(f"[{i}/{len(m4a_files)}] {filename}")
        
        # Проверяем, не существует ли уже MP3 файл
        if os.path.exists(output_file):
            print(f"  Файл {os.path.basename(output_file)} уже существует, пропускаем")
            skipped_count += 1
            continue
        
        # Конвертируем файл
        success, message = convert_file(m4a_file, output_file)
        
        if success:
            converted_count += 1
            print(f"  ✓ Успешно конвертирован")
            
            # Удаляем оригинальный M4A файл
            try:
                os.remove(m4a_file)
                print(f"  ✓ Оригинальный файл удален")
            except Exception as e:
                print(f"  ⚠ Не удалось удалить оригинальный файл: {e}")
        else:
            failed_count += 1
            print(f"  ✗ Ошибка: {message}")
    
    # Показываем итоги
    print("-" * 50)
    print("Конвертация завершена!")
    print(f"Успешно конвертировано: {converted_count}")
    print(f"Пропущено (уже существует): {skipped_count}")
    print(f"Ошибок: {failed_count}")
    
    input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()