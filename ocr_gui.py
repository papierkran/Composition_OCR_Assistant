import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json

CONFIG_FILE = "config.json"

# 默认配置
default_config = {
    "URL": "http://webapi.xfyun.cn/v1/service/v1/ocr/handwriting",
    "APPID": "",
    "API_KEY": "",
    "ROOT_DIR": ""
}

# 加载配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_config
    return default_config

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 主处理逻辑（替换为你自己完整的OCR处理函数）
def start_processing():
    config["URL"] = url_entry.get().strip()
    config["APPID"] = appid_entry.get().strip()
    config["API_KEY"] = apikey_entry.get().strip()
    config["ROOT_DIR"] = path_entry.get().strip()

    if not all([config["URL"], config["APPID"], config["API_KEY"], config["ROOT_DIR"]]):
        messagebox.showerror("错误", "请填写所有字段！")
        return

    if not os.path.isdir(config["ROOT_DIR"]):
        messagebox.showerror("错误", "路径无效，请选择正确的文件夹")
        return

    # 保存配置
    save_config(config)

    # 替换为你实际的识别处理函数
    try:
        messagebox.showinfo("开始", f"开始处理文件夹：\n{config['ROOT_DIR']}")
        from ocr_main import process_all  # 你自己的处理逻辑
        process_all(config["ROOT_DIR"])
        messagebox.showinfo("完成", "处理完成！")
    except Exception as e:
        messagebox.showerror("出错", f"处理失败：\n{e}")

# 浏览文件夹
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder)

# 初始化 GUI
config = load_config()

root = tk.Tk()
root.title("讯飞 OCR 工具")
root.geometry("500x300")
root.resizable(False, False)

tk.Label(root, text="接口 URL:").pack(anchor="w", padx=10, pady=5)
url_entry = tk.Entry(root, width=70)
url_entry.insert(0, config.get("URL", ""))
url_entry.pack(padx=10)

tk.Label(root, text="APPID:").pack(anchor="w", padx=10, pady=5)
appid_entry = tk.Entry(root, width=70)
appid_entry.insert(0, config.get("APPID", ""))
appid_entry.pack(padx=10)

tk.Label(root, text="API_KEY:").pack(anchor="w", padx=10, pady=5)
apikey_entry = tk.Entry(root, width=70)
apikey_entry.insert(0, config.get("API_KEY", ""))
apikey_entry.pack(padx=10)

tk.Label(root, text="文件夹路径:").pack(anchor="w", padx=10, pady=5)
frame = tk.Frame(root)
frame.pack(padx=10, pady=5)
path_entry = tk.Entry(frame, width=55)
path_entry.insert(0, config.get("ROOT_DIR", ""))
path_entry.pack(side="left")
browse_button = tk.Button(frame, text="浏览", command=browse_folder)
browse_button.pack(side="left", padx=5)

start_button = tk.Button(root, text="开始处理", command=start_processing, bg="green", fg="white", height=2)
start_button.pack(pady=20)

root.mainloop()
