import base64
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import threading
from datetime import datetime


CONFIG_FILE = "config.json"

default_config = {
    "URL": "http://webapi.xfyun.cn/v1/service/v1/ocr/handwriting",
    "APPID": "",
    "API_KEY": "",
    "ROOT_DIR": ""
}

icon_base64="""
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
"""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_config
    return default_config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def append_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_text.configure(state="normal")
    log_text.insert(tk.END, f"[{timestamp}] {message}\n")
    log_text.see(tk.END)
    log_text.configure(state="disabled")

def start_processing():
    def task():
        config["URL"] = url_entry.get().strip()
        config["APPID"] = appid_entry.get().strip()
        config["API_KEY"] = apikey_entry.get().strip()
        config["ROOT_DIR"] = path_entry.get().strip()

        if not all([config["URL"], config["APPID"], config["API_KEY"], config["ROOT_DIR"]]):
            append_log("错误：请填写所有字段！")
            return

        if not os.path.isdir(config["ROOT_DIR"]):
            append_log("错误：路径无效，请选择正确的文件夹")
            return

        save_config(config)

        try:
            append_log(f"开始处理文件夹：{config['ROOT_DIR']}")
            from ocr_main import process_all

            # 传入回调函数
            process_all(config["ROOT_DIR"], log_callback=append_log)

            append_log("处理完成！")
        except Exception as e:
            append_log(f"处理失败：{e}")

    threading.Thread(target=task, daemon=True).start()


def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder)

config = load_config()

root = tk.Tk()
root.title("Composition_OCR_Assistant V0.2")
root.geometry("800x600")

icon_data = base64.b64decode(icon_base64)
photo = tk.PhotoImage(data=icon_base64)
root.iconphoto(True, photo)

root.resizable(False, False)

tk.Label(root, text="接口 URL:").pack(anchor="w", padx=10, pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.insert(0, config.get("URL", ""))
url_entry.pack(padx=10)

tk.Label(root, text="APPID:").pack(anchor="w", padx=10, pady=5)
appid_entry = tk.Entry(root, width=80)
appid_entry.insert(0, config.get("APPID", ""))
appid_entry.pack(padx=10)

tk.Label(root, text="API_KEY:").pack(anchor="w", padx=10, pady=5)
apikey_entry = tk.Entry(root, width=80)
apikey_entry.insert(0, config.get("API_KEY", ""))
apikey_entry.pack(padx=10)

tk.Label(root, text="文件夹路径:").pack(anchor="w", padx=10, pady=5)
frame = tk.Frame(root)
frame.pack(padx=10, pady=5, fill="x")
path_entry = tk.Entry(frame, width=65)
path_entry.insert(0, config.get("ROOT_DIR", ""))
path_entry.pack(side="left", fill="x", expand=True)
browse_button = tk.Button(frame, text="浏览", command=browse_folder)
browse_button.pack(side="left", padx=8)

start_button = tk.Button(root, text="开始处理", command=start_processing, bg="#4CAF50", fg="white", height=2)
start_button.pack(pady=10)

tk.Label(root, text="日志输出：").pack(anchor="w", padx=10, pady=5)
log_text = tk.Text(root, height=10, state=tk.DISABLED, bg="#f0f0f0")
log_text.pack(padx=10, pady=(0,10), fill="both", expand=True)

root.mainloop()
