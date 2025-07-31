import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Поддерживаемые форматы
SUPPORTED_INPUT_FORMATS = {
    '.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', 
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp', '.amr'
}

OUTPUT_FORMATS = {
    'MP3': {
        'ext': '.mp3',
        'codec': 'mp3',
        'bitrates': ['128k', '192k', '256k', '320k'],
        'default_bitrate': '192k'
    },
    'WAV': {
        'ext': '.wav',
        'codec': 'pcm_s16le',
        'bitrates': ['не применимо'],
        'default_bitrate': None
    },
    'FLAC': {
        'ext': '.flac',
        'codec': 'flac',
        'bitrates': ['не применимо'],
        'default_bitrate': None
    },
    'AAC': {
        'ext': '.aac',
        'codec': 'aac',
        'bitrates': ['128k', '192k', '256k', '320k'],
        'default_bitrate': '192k'
    },
    'OGG': {
        'ext': '.ogg',
        'codec': 'libvorbis',
        'bitrates': ['128k', '192k', '256k', '320k'],
        'default_bitrate': '192k'
    },
    'M4A': {
        'ext': '.m4a',
        'codec': 'aac',
        'bitrates': ['128k', '192k', '256k', '320k'],
        'default_bitrate': '192k'
    },
    'WMA': {
        'ext': '.wma',
        'codec': 'wmav2',
        'bitrates': ['128k', '192k', '256k'],
        'default_bitrate': '192k'
    }
}

class AudioConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Универсальный Аудио Конвертер")
        self.root.geometry("600x500")
        self.folder_path = ""
        self.setup_ui()
    
    def setup_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Выбор папки
        ttk.Label(main_frame, text="1. Выберите папку с аудио файлами:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_label = ttk.Label(folder_frame, text="Папка не выбрана", relief="sunken", padding="5")
        self.folder_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder_frame, text="Выбрать папку", command=self.select_folder).grid(row=0, column=1)
        
        # Выбор выходного формата
        ttk.Label(main_frame, text="2. Выберите выходной формат:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.format_var = tk.StringVar(value="MP3")
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                        values=list(OUTPUT_FORMATS.keys()), state="readonly")
        self.format_combo.grid(row=0, column=0, padx=(0, 10))
        self.format_combo.bind('<<ComboboxSelected>>', self.on_format_change)
        
        # Выбор битрейта
        ttk.Label(format_frame, text="Битрейт:").grid(row=0, column=1, padx=(10, 5))
        
        self.bitrate_var = tk.StringVar(value="192k")
        self.bitrate_combo = ttk.Combobox(format_frame, textvariable=self.bitrate_var, width=10, state="readonly")
        self.bitrate_combo.grid(row=0, column=2)
        self.update_bitrate_options()
        
        # Дополнительные опции
        ttk.Label(main_frame, text="3. Дополнительные опции:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.delete_originals = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Удалять оригинальные файлы после конвертации", 
                       variable=self.delete_originals).grid(row=0, column=0, sticky=tk.W)
        
        self.overwrite_existing = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Перезаписывать существующие файлы", 
                       variable=self.overwrite_existing).grid(row=1, column=0, sticky=tk.W)
        
        self.preserve_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Сохранять структуру папок", 
                       variable=self.preserve_structure).grid(row=2, column=0, sticky=tk.W)
        
        # Кнопка конвертации
        self.convert_button = ttk.Button(main_frame, text="Начать конвертацию", 
                                       command=self.start_conversion, state="disabled")
        self.convert_button.grid(row=6, column=0, pady=10)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Текстовое поле для логов
        log_frame = ttk.LabelFrame(main_frame, text="Лог конвертации", padding="5")
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
    
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с аудио файлами")
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.config(text=folder_path)
            self.convert_button.config(state="normal")
            self.log(f"Выбрана папка: {folder_path}")
    
    def on_format_change(self, event=None):
        self.update_bitrate_options()
    
    def update_bitrate_options(self):
        format_name = self.format_var.get()
        if format_name in OUTPUT_FORMATS:
            bitrates = OUTPUT_FORMATS[format_name]['bitrates']
            self.bitrate_combo['values'] = bitrates
            self.bitrate_var.set(OUTPUT_FORMATS[format_name]['default_bitrate'] or bitrates[0])
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_conversion(self):
        if not self.folder_path:
            messagebox.showerror("Ошибка", "Выберите папку с файлами")
            return
        
        if not check_ffmpeg():
            messagebox.showerror("Ошибка", 
                               "FFmpeg не найден!\nУстановите FFmpeg и добавьте его в PATH.\n"
                               "Скачать можно с https://ffmpeg.org/download.html")
            return
        
        self.convert_button.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        
        try:
            self.convert_files()
        except Exception as e:
            self.log(f"Критическая ошибка: {e}")
        finally:
            self.convert_button.config(state="normal")
    
    def convert_files(self):
        format_info = OUTPUT_FORMATS[self.format_var.get()]
        
        self.log(f"Поиск аудио файлов в папке: {self.folder_path}")
        self.log(f"Целевой формат: {self.format_var.get()}")
        
        # Находим все поддерживаемые файлы
        audio_files = find_audio_files(self.folder_path)
        
        if not audio_files:
            self.log("Аудио файлы не найдены")
            return
        
        self.log(f"Найдено {len(audio_files)} аудио файлов")
        self.log("-" * 50)
        
        # Настройка прогресс бара
        self.progress['maximum'] = len(audio_files)
        self.progress['value'] = 0
        
        converted_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, audio_file in enumerate(audio_files):
            # Создаем имя выходного файла
            output_file = os.path.splitext(audio_file)[0] + format_info['ext']
            
            filename = os.path.basename(audio_file)
            self.log(f"[{i+1}/{len(audio_files)}] {filename}")
            
            # Проверяем, не существует ли уже файл
            if os.path.exists(output_file) and not self.overwrite_existing.get():
                self.log(f"  Файл {os.path.basename(output_file)} уже существует, пропускаем")
                skipped_count += 1
            else:
                # Конвертируем файл
                success, message = convert_audio_file(
                    audio_file, 
                    output_file, 
                    format_info,
                    self.bitrate_var.get()
                )
                
                if success:
                    converted_count += 1
                    self.log(f"  ✓ Успешно конвертирован")
                    
                    # Удаляем оригинальный файл если нужно
                    if self.delete_originals.get() and audio_file != output_file:
                        try:
                            os.remove(audio_file)
                            self.log(f"  ✓ Оригинальный файл удален")
                        except Exception as e:
                            self.log(f"  ⚠ Не удалось удалить оригинальный файл: {e}")
                else:
                    failed_count += 1
                    self.log(f"  ✗ Ошибка: {message}")
            
            # Обновляем прогресс
            self.progress['value'] = i + 1
            self.root.update_idletasks()
        
        # Показываем итоги
        self.log("-" * 50)
        self.log("Конвертация завершена!")
        self.log(f"Успешно конвертировано: {converted_count}")
        self.log(f"Пропущено (уже существует): {skipped_count}")
        self.log(f"Ошибок: {failed_count}")

def check_ffmpeg():
    """Проверяет наличие FFmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, 
                      encoding='utf-8', errors='ignore')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def find_audio_files(folder_path):
    """Находит все поддерживаемые аудио файлы в папке и подпапках"""
    audio_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in SUPPORTED_INPUT_FORMATS:
                audio_files.append(os.path.join(root, file))
    return audio_files

def convert_audio_file(input_file, output_file, format_info, bitrate):
    """Конвертирует аудио файл в указанный формат"""
    try:
        # Базовая команда FFmpeg
        cmd = ['ffmpeg', '-i', input_file]
        
        # Добавляем кодек
        cmd.extend(['-c:a', format_info['codec']])
        
        # Добавляем битрейт если применимо
        if bitrate and bitrate != 'не применимо':
            cmd.extend(['-b:a', bitrate])
        
        # Для FLAC добавляем уровень сжатия
        if format_info['codec'] == 'flac':
            cmd.extend(['-compression_level', '8'])
        
        # Для WAV устанавливаем частоту дискретизации
        if format_info['codec'] == 'pcm_s16le':
            cmd.extend(['-ar', '44100'])
        
        # Добавляем выходной файл
        cmd.extend(['-y', output_file])  # -y для перезаписи
        
        # Выполняем конвертацию
        process = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        
        if process.returncode == 0:
            return True, "Успешно"
        else:
            return False, process.stderr.strip() or "Неизвестная ошибка"
            
    except Exception as e:
        return False, str(e)

def main():
    """Запуск GUI приложения"""
    root = tk.Tk()
    app = AudioConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()