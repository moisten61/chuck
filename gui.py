import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from text_structurizer import TextStructurizer
from section_splitter import SectionSplitter
import asyncio
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

class TextStructurizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文本结构化工具")
        self.root.geometry("800x600")
        
        # 加载环境变量
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # 初始化处理器
        self.structurizer = TextStructurizer(self.api_key)
        self.splitter = SectionSplitter()
        
        # 设置日志
        self.setup_logging()
        
        # 创建界面
        self.create_widgets()
        
        self.output_dir = None  # 添加输出目录属性
        
    def setup_logging(self):
        """配置日志系统"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 创建处理器
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(handler)
        
    def create_widgets(self):
        """创建GUI组件"""
        # 文件选择区域
        file_frame = ttk.LabelFrame(self.root, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.select_btn = ttk.Button(file_frame, text="选择文件", command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.file_label = ttk.Label(file_frame, text="未选择文件")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        # 输出目录选择区域
        output_frame = ttk.LabelFrame(self.root, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.output_btn = ttk.Button(output_frame, text="选择输出目录", command=self.select_output_dir)
        self.output_btn.pack(side=tk.LEFT, padx=5)
        
        self.output_label = ttk.Label(output_frame, text="未选择输出目录")
        self.output_label.pack(side=tk.LEFT, padx=5)
        
        # 处理选项区域
        options_frame = ttk.LabelFrame(self.root, text="处理选项", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.need_structuring = tk.BooleanVar(value=True)
        self.structuring_check = ttk.Checkbutton(
            options_frame, 
            text="进行文本整理",
            variable=self.need_structuring
        )
        self.structuring_check.pack(side=tk.LEFT, padx=5)
        
        # 进度显示区域
        progress_frame = ttk.LabelFrame(self.root, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.pack(pady=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(self.root, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 开始处理按钮
        self.process_btn = ttk.Button(
            self.root, 
            text="开始处理",
            command=self.start_processing
        )
        self.process_btn.pack(pady=10)
        
    def select_files(self):
        """选择要处理的文件"""
        self.files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if self.files:
            self.file_label.config(text=f"已选择 {len(self.files)} 个文件")
            self.log_text.insert(tk.END, f"已选择文件：\n")
            for file in self.files:
                self.log_text.insert(tk.END, f"- {file}\n")
            self.log_text.see(tk.END)
            
    def select_output_dir(self):
        """选择输出目录"""
        self.output_dir = filedialog.askdirectory(title="选择输出目录")
        if self.output_dir:
            self.output_label.config(text=self.output_dir)
            self.log_text.insert(tk.END, f"已选择输出目录：{self.output_dir}\n")
            self.log_text.see(tk.END)

    async def process_file(self, file_path: str):
        """处理单个文件"""
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 文本整理（可选）
            if self.need_structuring.get():
                self.log_text.insert(tk.END, f"正在整理文本：{file_path}\n")
                content = await self.structurizer.process_text(content)
            
            # 章节分割
            self.log_text.insert(tk.END, f"正在分割章节：{file_path}\n")
            sections = self.splitter.split_sections(content)
            
            # 构建输出路径
            if self.output_dir:
                output_path = Path(self.output_dir) / f"{Path(file_path).stem}_processed.txt"
            else:
                output_path = Path(file_path).with_stem(Path(file_path).stem + "_processed")
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存结果
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sections))
            
            self.log_text.insert(tk.END, f"处理完成：{output_path}\n")
            self.log_text.see(tk.END)
            
        except Exception as e:
            self.logger.error(f"处理文件时出错：{str(e)}")
            self.log_text.insert(tk.END, f"错误：{str(e)}\n")
            self.log_text.see(tk.END)
            
    def start_processing(self):
        """开始处理文件"""
        if not hasattr(self, 'files') or not self.files:
            messagebox.showwarning("警告", "请先选择要处理的文件")
            return
            
        if not self.output_dir:
            if not messagebox.askyesno("确认", "未选择输出目录，文件将保存在原目录下，是否继续？"):
                return
            
        async def process_all_files():
            self.process_btn.config(state='disabled')
            self.progress['maximum'] = len(self.files)
            self.progress['value'] = 0
            
            for i, file in enumerate(self.files):
                self.status_label.config(text=f"正在处理：{Path(file).name}")
                await self.process_file(file)
                self.progress['value'] = i + 1
                self.root.update()
            
            self.status_label.config(text="处理完成")
            self.process_btn.config(state='normal')
            messagebox.showinfo("完成", "所有文件处理完成")
            
        asyncio.run(process_all_files())
        
    def run(self):
        """运行GUI程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TextStructurizerGUI()
    app.run() 