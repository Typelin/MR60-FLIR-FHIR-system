import os

# 匯出的檔名
OUTPUT_FILE = "project_context.md"

# 限制「單一文字檔」的最大容量（單位：KB）。超過此大小只記錄檔名，不寫入內容
# 程式碼通常不應該單檔超過 500 KB
MAX_FILE_SIZE_KB = 500  

# 預設忽略的資料夾
IGNORE_DIRS = {
    ".git", ".svn", "node_modules", "__pycache__", ".venv", "venv", 
    "env", "dist", "build", ".next", ".vscode", ".idea", "coverage", "out"
}

# 預設忽略的檔案
IGNORE_FILES = {
    OUTPUT_FILE, "export_project.py", ".DS_Store", "thumbs.db", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
}

# 純文字/程式碼副檔名清單
TEXT_EXTENSIONS = {
    ".c", ".h", ".cpp", ".hpp", ".py", ".txt", ".md", ".json", 
    ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".vue", ".sql", 
    ".sh", ".bat", ".cmd", ".yaml", ".yml", ".xml", ".ini", ".conf", 
    ".env.example", ".java", ".cs", ".go", ".rs", ".php", ".rb"
}

def is_text_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    # 避開 .min.js 或 .map 檔
    if filename.endswith(".min.js") or filename.endswith(".map"):
        return False
    return ext in TEXT_EXTENSIONS

def generate_export():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(root_dir, OUTPUT_FILE)
    
    skipped_large_files = []
    
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"# 專案絕對路徑: `{root_dir}`\n\n")
        
        # 1. 產生目錄結構樹
        out.write("## 1. 目錄結構 (Directory Structure)\n\n```text\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            rel_path = os.path.relpath(root, root_dir)
            level = 0 if rel_path == "." else rel_path.count(os.sep) + 1
            indent = "  " * level
            folder_name = os.path.basename(root) if rel_path != "." else "."
            out.write(f"{indent}{folder_name}/\n")
            
            sub_indent = "  " * (level + 1)
            for file in sorted(files):
                if file in IGNORE_FILES:
                    continue
                out.write(f"{sub_indent}{file}\n")
        out.write("```\n\n---\n\n")
        
        # 2. 寫入各檔案內容
        out.write("## 2. 檔案內容 (File Contents)\n\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in sorted(files):
                if file in IGNORE_FILES:
                    continue
                
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, root_dir)
                ext = os.path.splitext(file)[1].lower().lstrip(".")
                
                file_size_kb = os.path.getsize(abs_path) / 1024
                
                out.write(f"### 📄 `{rel_path}`\n\n")
                
                if is_text_file(file):
                    # 檔案太大的保護機制
                    if file_size_kb > MAX_FILE_SIZE_KB:
                        out.write(f"*[檔案過大 ({file_size_kb:.1f} KB > {MAX_FILE_SIZE_KB} KB)，已自動省略內文]*\n\n")
                        skipped_large_files.append(f"{rel_path} ({file_size_kb:.1f} KB)")
                        continue
                        
                    out.write(f"```{ext if ext else 'text'}\n")
                    try:
                        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"// 讀取檔案失敗: {e}\n")
                    out.write("\n```\n\n")
                else:
                    out.write("*[非文字檔或未支援檔型，僅紀錄檔名，省略內文]*\n\n")
                    
    print(f"✅ 成功打包！生成檔案：{output_path}")
    if skipped_large_files:
        print("\n⚠️ 以下檔案因容量過大被省略內容（避免爆 Context）：")
        for f in skipped_large_files:
            print(f"  - {f}")

if __name__ == "__main__":
    generate_export()