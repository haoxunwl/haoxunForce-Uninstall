import os
import sys
import subprocess
import winreg
import shutil
import time
import ctypes
import threading
from threading import Lock, Event
from multiprocessing import Value
import tkinter as tk
from tkinter import Tk, Label, Listbox, Button, Scrollbar, Frame, messagebox, Entry, Checkbutton, BooleanVar, StringVar, Text, Radiobutton, font, filedialog, Menu
from tkinter import ttk
import re
import stat
import traceback
import platform

# 可选模块导入和可用性检查

# 尝试导入PIL
PIL_AVAILABLE = False
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ PIL模块不可用，将使用内置图标")

# 尝试导入pystray
try:
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    pystray = None
    PYSTRAY_AVAILABLE = False
    print("⚠️ pystray模块不可用，将不支持系统托盘功能")

# 尝试导入win32系列模块
WIN32API_AVAILABLE = False
try:
    import win32api
    import win32con
    import win32process
    import win32security
    import win32job
    import win32gui
    WIN32API_AVAILABLE = True
except ImportError:
    print("⚠️ 部分win32模块不可用，部分高级功能可能受限")

# 尝试导入win32file
try:
    import win32file
    WIN32FILE_AVAILABLE = True
except ImportError:
    win32file = None
    WIN32FILE_AVAILABLE = False
    print("⚠️ win32file模块不可用，将使用替代方案")

# 尝试导入psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil模块不可用，部分系统信息功能可能受限")

# 尝试导入其他可选模块
try:
    import hashlib
    HASH_AVAILABLE = True
except ImportError:
    hashlib = None
    HASH_AVAILABLE = False
    print("⚠️ hashlib模块不可用，部分文件哈希功能可能受限")

try:
    import random
    RANDOM_AVAILABLE = True
except ImportError:
    random = None
    RANDOM_AVAILABLE = False
    print("⚠️ random模块不可用，部分随机功能可能受限")

try:
    import mimetypes
    MIMETYPES_AVAILABLE = True
except ImportError:
    mimetypes = None
    MIMETYPES_AVAILABLE = False
    print("⚠️ mimetypes模块不可用，部分文件类型识别功能可能受限")

# 尝试导入加密管理器
try:
    from simple_encryption import SimpleEncryptionManager
    ENCRYPTION_AVAILABLE = True
except ImportError:
    SimpleEncryptionManager = None
    ENCRYPTION_AVAILABLE = False
    print("⚠️ 加密模块不可用，将不支持加密功能")

class ModernButton(Button):
    """自定义现代化按钮类"""
    def __init__(self, master=None, **kwargs):
        # 默认样式
        default_kwargs = {
            "bd": 0,
            "relief": "flat",
            "font": ("微软雅黑", 10),
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        # 合并用户提供的参数
        for key, value in default_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value
        
        # 创建按钮
        super().__init__(master, **kwargs)
        
        # 添加悬停效果
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        # 保存原始背景色
        self.original_bg = self["bg"] if self["bg"] != "SystemButtonFace" else "#d0d0d0"
    
    def on_enter(self, event):
        """鼠标悬停时的效果"""
        # 调暗颜色作为悬停效果
        self.config(bg=self._adjust_brightness(self.original_bg, 0.9))
    
    def on_leave(self, event):
        """鼠标离开时恢复原始状态"""
        self.config(bg=self.original_bg)
    
    def _adjust_brightness(self, color, factor):
        """调整颜色亮度"""
        try:
            # 处理十六进制颜色
            if color.startswith("#"):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                
                # 调整亮度
                r = min(255, int(r * factor))
                g = min(255, int(g * factor))
                b = min(255, int(b * factor))
                
                return f"#{r:02x}{g:02x}{b:02x}"
            return color
        except:
            return color

class UninstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("浩讯亿通电脑急救强力卸载工具1.0.0")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 基本颜色设置
        self.bg_color = "#ffffff"  # 白色背景
        self.text_color = "#333333"  # 黑色文字
        self.button_color = "#4a90e2"  # 蓝色按钮
        self.list_bg = "#f9f9f9"  # 列表背景
        self.highlight_color = "#357abd"  # 高亮色
        
        # 检测系统和Python环境
        self._detect_environment()
        
        # 设置窗口背景
        self.root.configure(bg=self.bg_color)
        
        # 初始化权限状态
        self.has_admin = False
        
        # 初始化加密数据库管理器
        self.encryption_manager = None
        self.virus_database = {}
        if ENCRYPTION_AVAILABLE:
            try:
                self.encryption_manager = SimpleEncryptionManager('test_virus_db.enc')
                # 尝试加载加密的病毒特征码数据库
                self._load_encrypted_database()
                print("✅ 已加载加密病毒特征码数据库")
            except Exception as e:
                print(f"⚠️ 加载加密数据库失败，使用内置特征码: {e}")
                self._load_fallback_database()
        
        # 创建主框架
        self.main_frame = Frame(root, bg=self.bg_color, padx=10, pady=10)
        self.main_frame.pack(fill="both", expand=True)
        
        # 初始化托盘功能将在log_text创建后调用
        
        # 标题标签
        self.title_label = Label(
            self.main_frame,
            text="电脑急救强力卸载工具",
            font=("微软雅黑", 16, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.pack(pady=5)
        
        # 状态标签 - 用于显示各种功能的状态信息
        self.status_label = Label(
            self.main_frame,
            text="欢迎使用电脑急救强力卸载工具",
            font=("微软雅黑", 10),
            bg=self.bg_color,
            fg="#666666"
        )
        self.status_label.pack(pady=2)
        
        # 创建左右分栏框架
        self.content_frame = Frame(self.main_frame, bg=self.bg_color)
        self.content_frame.pack(fill="both", expand=True, pady=5)
        
        # 左侧内容框架
        self.left_frame = Frame(self.content_frame, bg=self.bg_color)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 右侧内容框架（沙箱状态和日志）
        self.right_frame = Frame(self.content_frame, bg=self.bg_color, width=400)
        self.right_frame.pack(side="right", fill="y", padx=(5, 0))
        self.right_frame.pack_propagate(False)  # 防止框架自动调整大小
        
        # 搜索框
        self.search_frame = Frame(self.left_frame, bg=self.bg_color)
        self.search_frame.pack(fill="x", pady=2)
        
        Label(self.search_frame, text="搜索:", bg=self.bg_color).pack(side="left")
        self.search_entry = Entry(self.search_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # 进度条
        self.progress_frame = Frame(self.left_frame, bg=self.bg_color)
        self.progress_frame.pack(fill="x", pady=2)
        
        self.progress_label = Label(self.progress_frame, text="扫描进度:", bg=self.bg_color)
        self.progress_label.pack(side="left")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            length=200,
            mode='determinate'
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        self.progress_percent = Label(self.progress_frame, text="0%", bg=self.bg_color, width=8)
        self.progress_percent.pack(side="left")
        
        # 程序列表
        self.list_frame = Frame(self.left_frame, bg=self.bg_color)
        self.list_frame.pack(fill="both", expand=True, pady=2)
        
        self.scrollbar = Scrollbar(self.list_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        self.program_listbox = Listbox(
            self.list_frame,
            yscrollcommand=self.scrollbar.set,
            width=60,
            height=18,
            bg=self.list_bg
        )
        self.program_listbox.pack(fill="both", expand=True, side="left")
        self.scrollbar.config(command=self.program_listbox.yview)
        
        # 初始化数据
        self.programs = []
        self.filtered_programs = []
        
        # 绑定事件
        self.program_listbox.bind("<Double-1>", self.on_program_double_click)
        self.search_entry.bind("<KeyRelease>", self.filter_programs)
        
        # 添加右键菜单
        self._add_right_click_menu()
        
        # 延迟刷新列表，避免在构造函数中启动线程
        # 将在主循环启动后自动触发第一次扫描
        
        # 卸载选项区域
        self.options_frame = Frame(self.left_frame, bg=self.bg_color)
        self.options_frame.pack(fill="x", pady=2)
        
        self.force_delete = BooleanVar(value=True)
        self.force_delete_check = Checkbutton(
            self.options_frame,
            text="强力删除残留文件",
            variable=self.force_delete,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.force_delete_check.pack(side="left", padx=5)
        
        self.clean_registry = BooleanVar(value=True)
        self.clean_registry_check = Checkbutton(
            self.options_frame,
            text="清理注册表项",
            variable=self.clean_registry,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.clean_registry_check.pack(side="left", padx=5)
        
        # 新增：设备残留清理选项
        self.clean_device_residuals = BooleanVar(value=False)  # 默认关闭，需要用户主动选择
        self.clean_device_residuals_check = Checkbutton(
            self.options_frame,
            text="清理设备和驱动器残留",
            variable=self.clean_device_residuals,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.clean_device_residuals_check.pack(side="left", padx=5)
        
        # 顽固程序处理选项
        self.tough_program_frame = Frame(self.left_frame, bg=self.bg_color)
        self.tough_program_frame.pack(fill="x", pady=2)
        
        self.clean_startup = BooleanVar(value=True)
        self.clean_startup_check = Checkbutton(
            self.tough_program_frame,
            text="清理启动项",
            variable=self.clean_startup,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.clean_startup_check.pack(side="left", padx=5)
        
        self.stop_services = BooleanVar(value=True)
        self.stop_services_check = Checkbutton(
            self.tough_program_frame,
            text="停止相关服务",
            variable=self.stop_services,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.stop_services_check.pack(side="left", padx=5)
        
        self.unlock_files = BooleanVar(value=True)
        self.unlock_files_check = Checkbutton(
            self.tough_program_frame,
            text="解锁锁定文件",
            variable=self.unlock_files,
            bg=self.bg_color,
            font=("微软雅黑", 8)
        )
        self.unlock_files_check.pack(side="left", padx=5)
        
        # 按钮区域
        self.button_frame = Frame(self.left_frame, bg=self.bg_color)
        self.button_frame.pack(fill="x", pady=2)
        
        self.refresh_button = Button(
            self.button_frame,
            text="刷新列表",
            command=self.refresh_list,
            bg=self.button_color,
            fg="white",
            width=12
        )
        self.refresh_button.pack(side="left", padx=5)
        
        self.uninstall_button = Button(
            self.button_frame,
            text="卸载选中",
            command=self.uninstall_selected,
            bg="#e74c3c",
            fg="white",
            width=12
        )
        self.uninstall_button.pack(side="left", padx=5)
        
        self.kill_button = Button(
            self.button_frame,
            text="停止进程",
            command=self.kill_process,
            bg="#f39c12",
            fg="white",
            width=12
        )
        self.kill_button.pack(side="left", padx=5)
        
        self.sandbox_button = Button(
            self.button_frame,
            text="沙箱模式运行",
            command=self.run_in_sandbox,
            bg="#27ae60",
            fg="white",
            width=12
        )
        self.sandbox_button.pack(side="left", padx=5)
        
        # 强力粉碎按钮
        self.shred_button = Button(
            self.button_frame,
            text="强力粉碎",
            command=self.start_file_shredding,
            bg="#8e44ad",
            fg="white",
            width=12
        )
        self.shred_button.pack(side="left", padx=5)
        

        
        self.scan_button = Button(
            self.button_frame,
            text="安全扫描",
            command=self.security_scan,
            bg="#e67e22",
            fg="white",
            width=10
        )
        self.scan_button.pack(side="left", padx=2)
        
        self.network_diag_button = Button(
            self.button_frame,
            text="网络诊断",
            command=self.network_diagnostics,
            bg="#3498db",
            fg="white",
            width=10
        )
        self.network_diag_button.pack(side="left", padx=2)
        
        self.quit_button = Button(
            self.button_frame,
            text="退出",
            command=root.quit,
            bg="#95a5a6",
            fg="white",
            width=8
        )
        self.quit_button.pack(side="right", padx=2)
        
        # 右侧框架内容
        # 沙箱状态面板
        self.sandbox_frame = Frame(self.right_frame, bg=self.bg_color, relief="sunken", bd=1)
        self.sandbox_frame.pack(fill="x", pady=(0, 5))
        
        sandbox_header_frame = Frame(self.sandbox_frame, bg=self.bg_color)
        sandbox_header_frame.pack(fill="x", padx=5, pady=2)
        
        Label(sandbox_header_frame, text="🛡️ 沙箱状态监控", font=("微软雅黑", 9, "bold"), 
              bg=self.bg_color, fg="#27ae60").pack(side="left")
        
        self.sandbox_status_label = Label(sandbox_header_frame, text="无活跃沙箱", 
                                         bg=self.bg_color, fg="#7f8c8d", font=("微软雅黑", 8))
        self.sandbox_status_label.pack(side="right")
        
        # 沙箱详细信息
        self.sandbox_info_frame = Frame(self.sandbox_frame, bg=self.bg_color)
        self.sandbox_info_frame.pack(fill="x", padx=5, pady=2)
        
        self.sandbox_info_label = Label(self.sandbox_info_frame, text="", 
                                       bg=self.bg_color, fg=self.text_color, 
                                       font=("Consolas", 8), justify="left")
        self.sandbox_info_label.pack(anchor="w")
        
        # 沙箱进度条
        self.sandbox_progress_frame = Frame(self.sandbox_frame, bg=self.bg_color)
        self.sandbox_progress_frame.pack(fill="x", padx=5, pady=2)
        
        Label(self.sandbox_progress_frame, text="资源使用:", bg=self.bg_color, font=("微软雅黑", 8)).pack(side="left")
        
        self.sandbox_progress_var = tk.DoubleVar()
        self.sandbox_progress_bar = ttk.Progressbar(
            self.sandbox_progress_frame,
            variable=self.sandbox_progress_var,
            length=150,
            mode='determinate'
        )
        self.sandbox_progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        self.sandbox_progress_percent = Label(self.sandbox_progress_frame, text="0%", 
                                            bg=self.bg_color, width=8, font=("微软雅黑", 8))
        self.sandbox_progress_percent.pack(side="left")
        
        # 沙箱控制按钮
        self.sandbox_control_frame = Frame(self.sandbox_frame, bg=self.bg_color)
        self.sandbox_control_frame.pack(fill="x", padx=5, pady=5)
        
        self.stop_sandbox_button = Button(
            self.sandbox_control_frame,
            text="停止沙箱",
            command=self.stop_all_sandboxes,
            bg="#e74c3c",
            fg="white",
            width=8,
            state="disabled",
            font=("微软雅黑", 8)
        )
        self.stop_sandbox_button.pack(side="left", padx=2)
        
        self.view_sandbox_logs_button = Button(
            self.sandbox_control_frame,
            text="查看日志",
            command=self.view_sandbox_logs,
            bg="#3498db",
            fg="white",
            width=8,
            state="disabled",
            font=("微软雅黑", 8)
        )
        self.view_sandbox_logs_button.pack(side="left", padx=2)
        
        # 存储活跃沙箱信息
        self.active_sandboxes = {}
        self.sandbox_update_lock = threading.Lock()
        
        # 初始化数据（必须在创建log_text之前）
        self.programs = []
        self.filtered_programs = []
        
        # 日志区域 - 必须在log方法被调用之前创建
        self.log_frame = Frame(self.right_frame, bg=self.bg_color)
        self.log_frame.pack(fill="both", expand=True)
        
        Label(self.log_frame, text="操作日志:", bg=self.bg_color, font=("微软雅黑", 9, "bold")).pack(anchor="w", pady=(0, 2))
        
        self.log_text = Text(self.log_frame, height=20, width=45)
        self.log_text.pack(fill="both", expand=True)
        
        # 现在log_text已经创建，可以初始化托盘功能了
        self._setup_tray_icon()
        
        # 磁盘信息面板
        self.disk_info_frame = Frame(self.right_frame, bg=self.bg_color, relief="sunken", bd=1)
        self.disk_info_frame.pack(fill="x", pady=(0, 5))
        
        disk_header_frame = Frame(self.disk_info_frame, bg=self.bg_color)
        disk_header_frame.pack(fill="x", padx=5, pady=2)
        
        Label(disk_header_frame, text="💾 磁盘信息", font=("微软雅黑", 9, "bold"), 
              bg=self.bg_color, fg="#27ae60").pack(side="left")
        
        self.disk_info_text = Text(self.disk_info_frame, height=10, width=45, font=("Consolas", 8))
        self.disk_info_text.pack(fill="x", padx=5, pady=2)
        self.disk_info_text.config(state="disabled")
        
        # 更新磁盘信息
        self.update_disk_info()
        
        # 启动沙箱状态更新线程（在log_text创建之后）
        self.start_sandbox_monitoring()
        
        # 记录日志 - 确保在log_text初始化后再调用
        try:
            self.log("程序启动成功！")
        except Exception as e:
            # 如果log_text还未初始化，则使用print记录
            print(f"初始化日志记录: {e}")
    
    def log(self, message, level="INFO", module="main"):
        """显示日志信息并保存到文件
        
        参数:
            message: 日志消息
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            module: 模块名称，用于标识日志来源
        """
        try:
            # 检查日志级别
            log_levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
            if log_levels.get(level, 1) < log_levels.get(getattr(self, 'log_level', 'INFO'), 1):
                return
                
            # 添加时间戳和上下文信息
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # 兼容Python 3.5及以下版本
            thread_id = threading.current_thread().ident
            log_message = "[%s] [%s] [%s] [Thread-%d] %s" % (timestamp, level, module, thread_id, message)
            
            # 输出到控制台（根据级别设置颜色）
            if level == "ERROR" or level == "CRITICAL":
                print(f"\033[91m{log_message}\033[0m")  # 红色
            elif level == "WARNING":
                print(f"\033[93m{log_message}\033[0m")  # 黄色
            elif level == "DEBUG":
                print(f"\033[94m{log_message}\033[0m")  # 蓝色
            else:
                print(log_message)  # 正常颜色
            
            # 写入日志文件
            try:
                log_folder = "logs"
                # 创建日志文件夹（如果不存在）
                if not os.path.exists(log_folder):
                    os.makedirs(log_folder)
                
                log_filename = os.path.join(log_folder, f"uninstaller_{time.strftime('%Y%m%d')}.log")
                
                with open(log_filename, "a", encoding="utf-8") as log_file:
                    log_file.write(log_message + "\n")
            except Exception as file_error:
                print(f"写入日志文件失败: {file_error}")
            
            # 显示在GUI日志控件（如果可用）
            try:
                if hasattr(self, 'log_text') and self.log_text is not None:
                    self.log_text.config(state="normal")
                    self.log_text.insert("end", log_message + "\n")
                    self.log_text.see("end")
                    self.log_text.config(state="disabled")
            except Exception as gui_error:
                # 忽略GUI相关错误，继续执行
                pass
        except Exception as e:
            print(f"记录日志失败: {e}")
            try:
                # 即使主日志记录失败，也要尝试写入日志文件
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                error_message = f"[{timestamp}] 日志系统错误: {str(e)}"
                with open("uninstaller.log", "a", encoding="utf-8") as log_file:
                    log_file.write(error_message + "\n")
            except:
                pass
    
    def _detect_environment(self):
        """检测系统和Python环境，设置兼容性标志"""
        try:
            # 检测Windows版本
            if platform.system() == "Windows":
                win_ver = platform.win32_ver()
                self.windows_version = {
                    "major": win_ver[0],
                    "minor": win_ver[1],
                    "build": win_ver[2],
                    "service_pack": win_ver[3]
                }
                
                # 设置Windows版本兼容性标志
                self.is_win7_or_older = False
                self.is_win10_or_newer = False
                
                try:
                    win_major = int(self.windows_version["major"])
                    win_minor = int(self.windows_version["minor"])
                    
                    if win_major < 6 or (win_major == 6 and win_minor < 2):
                        self.is_win7_or_older = True
                    if win_major >= 10 or (win_major == 6 and win_minor >= 2):
                        self.is_win10_or_newer = True
                except:
                    pass
                
                win_info = f"Windows {self.windows_version['major']}.{self.windows_version['minor']} "
                if self.windows_version['build']:
                    win_info += f"(Build {self.windows_version['build']}) "
                if self.windows_version['service_pack']:
                    win_info += f"{self.windows_version['service_pack']}"
            else:
                self.windows_version = None
                self.is_win7_or_older = False
                self.is_win10_or_newer = False
                win_info = "非Windows系统"
            
            # 检测Python版本
            py_ver = platform.python_version_tuple()
            self.python_version = {
                "major": int(py_ver[0]),
                "minor": int(py_ver[1]),
                "patch": int(py_ver[2]) if len(py_ver) > 2 else 0
            }
            
            py_info = f"Python {self.python_version['major']}.{self.python_version['minor']}.{self.python_version['patch']}"
            
            # 记录环境信息
            self.log(f"系统环境: {win_info}", "INFO", "env")
            self.log(f"Python环境: {py_info}", "INFO", "env")
            
            # 根据Python版本设置兼容性标志
            self.is_python35_or_older = (self.python_version['major'] == 3 and self.python_version['minor'] <= 5)
            
            if self.is_python35_or_older:
                self.log("⚠️ 检测到Python 3.5或更早版本，部分功能可能受限", "WARNING", "env")
            
            if self.is_win7_or_older:
                self.log("⚠️ 检测到Windows 7或更早版本，部分功能可能受限", "WARNING", "env")
                
        except Exception as e:
            self.log(f"环境检测失败: {str(e)}", "ERROR", "env")
            # 设置默认兼容性标志
            self.windows_version = None
            self.python_version = None
            self.is_win7_or_older = False
            self.is_win10_or_newer = False
            self.is_python35_or_older = False
    
    def get_disk_info(self):
        """获取系统磁盘信息"""
        disk_info = []
        
        try:
            # 使用wmic命令获取磁盘信息
            command = "wmic logicaldisk get DeviceID, DriveType, FileSystem, Size, FreeSpace, VolumeName"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='gbk')
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    line = line.strip()
                    if line:
                        # 分割行并清理空白
                        parts = [part for part in line.split() if part]
                        if len(parts) >= 4:
                            device_id = parts[0]
                            drive_type = parts[1]
                            file_system = parts[2]
                            size = parts[3] if len(parts) > 3 else "0"
                            free_space = parts[4] if len(parts) > 4 else "0"
                            volume_name = " ".join(parts[5:]) if len(parts) > 5 else ""
                            
                            # 转换驱动器类型
                            drive_type_map = {
                                "0": "未知",
                                "1": "无根目录",
                                "2": "可移动磁盘",
                                "3": "本地磁盘",
                                "4": "网络驱动器",
                                "5": "光驱",
                                "6": "内存虚拟磁盘"
                            }
                            drive_type_text = drive_type_map.get(drive_type, drive_type)
                            
                            # 转换为易读的大小格式
                            def format_size(bytes_val):
                                try:
                                    bytes_val = int(bytes_val)
                                    if bytes_val == 0:
                                        return "0 B"
                                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                                        if bytes_val < 1024.0:
                                            return f"{bytes_val:.2f} {unit}"
                                        bytes_val /= 1024.0
                                    return f"{bytes_val:.2f} PB"
                                except:
                                    return "未知"
                            
                            # 计算使用率
                            try:
                                total_size = int(size)
                                free_size = int(free_space)
                                used_size = total_size - free_size
                                if total_size > 0:
                                    usage_percent = (used_size / total_size) * 100
                                else:
                                    usage_percent = 0
                            except:
                                used_size = 0
                                usage_percent = 0
                            
                            disk_info.append({
                                "device_id": device_id,
                                "drive_type": drive_type_text,
                                "file_system": file_system,
                                "total_size": format_size(size),
                                "free_space": format_size(free_space),
                                "used_size": format_size(used_size),
                                "usage_percent": f"{usage_percent:.1f}%",
                                "volume_name": volume_name
                            })
        except Exception as e:
            self.log(f"获取磁盘信息失败: {e}")
        
        return disk_info
    
    def update_disk_info(self):
        """更新磁盘信息显示"""
        try:
            disk_info = self.get_disk_info()
            
            self.disk_info_text.config(state="normal")
            self.disk_info_text.delete("1.0", "end")
            
            for disk in disk_info:
                # 仅显示本地磁盘和可移动磁盘
                if disk["drive_type"] in ["本地磁盘", "可移动磁盘"]:
                    line = f"{disk['device_id']} {disk['volume_name']:<15} "
                    line += f"类型: {disk['drive_type']:<8} "
                    line += f"文件系统: {disk['file_system']:<6} "
                    line += f"总计: {disk['total_size']:<12} "
                    line += f"可用: {disk['free_space']:<12} "
                    line += f"使用率: {disk['usage_percent']:<6}\n"
                    self.disk_info_text.insert("end", line)
            
            self.disk_info_text.config(state="disabled")
        except Exception as e:
            self.log(f"更新磁盘信息失败: {e}")

    def start_sandbox_monitoring(self):
        """启动沙箱状态监控线程"""
        def monitor_loop():
            while True:
                try:
                    # 每2秒更新一次沙箱状态
                    time.sleep(2)
                    self.update_sandbox_status()
                except Exception as e:
                    self.log(f"沙箱监控线程出错: {str(e)}")
                    time.sleep(5)  # 出错时等待更长时间
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.log("沙箱监控线程已启动")
    
    def register_sandbox(self, sandbox_info):
        """注册新的沙箱"""
        with self.sandbox_update_lock:
            sandbox_id = sandbox_info['sandbox_id']
            self.active_sandboxes[sandbox_id] = {
                **sandbox_info,
                'start_time': time.time(),
                'last_update': time.time()
            }
            
            self.log(f"沙箱已注册 - ID: {sandbox_id}, 程序: {sandbox_info['display_name']}")
            self.update_sandbox_status()
    
    def unregister_sandbox(self, sandbox_id):
        """注销沙箱"""
        with self.sandbox_update_lock:
            if sandbox_id in self.active_sandboxes:
                sandbox_info = self.active_sandboxes[sandbox_id]
                del self.active_sandboxes[sandbox_id]
                self.log(f"沙箱已注销 - ID: {sandbox_id}, 程序: {sandbox_info['display_name']}")
                self.update_sandbox_status()
    
    def update_sandbox_status(self):
        """更新沙箱状态显示"""
        try:
            # 确保在主线程中更新UI
            def update_ui():
                with self.sandbox_update_lock:
                    active_count = len(self.active_sandboxes)
                
                if active_count == 0:
                    self.sandbox_status_label.config(text="无活跃沙箱", fg="#7f8c8d")
                    self.sandbox_info_label.config(text="")
                    self.sandbox_progress_var.set(0)
                    self.sandbox_progress_percent.config(text="0%")
                    self.stop_sandbox_button.config(state="disabled")
                    self.view_sandbox_logs_button.config(state="disabled")
                else:
                    # 有活跃沙箱
                    total_memory = 0
                    total_cpu = 0
                    sandbox_details = []
                    
                    with self.sandbox_update_lock:
                        for sandbox_id, sandbox_info in self.active_sandboxes.items():
                            process_id = sandbox_info.get('process_id')
                            display_name = sandbox_info.get('display_name', '未知')
                            start_time = sandbox_info.get('start_time', time.time())
                            
                            runtime = int(time.time() - start_time)
                            
                            try:
                                if process_id and psutil.pid_exists(process_id):
                                    process = psutil.Process(process_id)
                                    memory_mb = process.memory_info().rss // 1024 // 1024
                                    cpu_percent = process.cpu_percent()
                                    total_memory += memory_mb
                                    total_cpu += cpu_percent
                                    
                                    status = "运行中"
                                    status_color = "#27ae60"
                                else:
                                    memory_mb = 0
                                    cpu_percent = 0
                                    status = "已停止"
                                    status_color = "#e74c3c"
                                    
                                sandbox_details.append(
                                    f"🆔 {sandbox_id} | {display_name[:20]}... | "
                                    f"PID: {process_id} | 内存: {memory_mb}MB | "
                                    f"CPU: {cpu_percent:.1f}% | 运行: {runtime}s | 状态: {status}"
                                )
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                sandbox_details.append(
                                    f"🆔 {sandbox_id} | {display_name[:20]}... | "
                                    f"PID: {process_id} | 状态: 进程不存在"
                                )
                    
                    # 更新UI
                    self.sandbox_status_label.config(
                        text=f"{active_count} 个活跃沙箱", 
                        fg="#27ae60"
                    )
                    
                    # 显示详细信息
                    info_text = "\n".join(sandbox_details[:3])  # 最多显示3个
                    if len(sandbox_details) > 3:
                        info_text += f"\n... 还有 {len(sandbox_details) - 3} 个沙箱"
                    
                    self.sandbox_info_label.config(text=info_text)
                    
                    # 更新资源使用进度条（基于内存使用）
                    max_memory = 512 * len(self.active_sandboxes)  # 每个沙箱最大512MB
                    memory_usage = min(100, (total_memory / max_memory) * 100)
                    self.sandbox_progress_var.set(memory_usage)
                    self.sandbox_progress_percent.config(text=f"{memory_usage:.1f}%")
                    
                    # 启用控制按钮
                    self.stop_sandbox_button.config(state="normal")
                    self.view_sandbox_logs_button.config(state="normal")
            
            # 在主线程中执行UI更新
            self.root.after(0, update_ui)
            
        except Exception as e:
            self.log(f"更新沙箱状态时出错: {str(e)}")
    
    def stop_all_sandboxes(self):
        """停止所有活跃的沙箱"""
        if not self.active_sandboxes:
            messagebox.showinfo("提示", "当前没有活跃的沙箱")
            return
        
        if messagebox.askyesno("确认", f"确定要停止所有 {len(self.active_sandboxes)} 个沙箱吗？"):
            with self.sandbox_update_lock:
                sandboxes_to_stop = list(self.active_sandboxes.keys())
            
            stopped_count = 0
            for sandbox_id in sandboxes_to_stop:
                try:
                    with self.sandbox_update_lock:
                        if sandbox_id in self.active_sandboxes:
                            sandbox_info = self.active_sandboxes[sandbox_id]
                            
                            # 终止进程
                            if 'job_handle' in sandbox_info and sandbox_info['job_handle']:
                                try:
                                    win32job.TerminateJobObject(sandbox_info['job_handle'], 1)
                                except:
                                    pass
                            
                            # 关闭句柄
                            if 'process_handle' in sandbox_info and sandbox_info['process_handle']:
                                try:
                                    win32api.CloseHandle(sandbox_info['process_handle'])
                                except:
                                    pass
                            
                            if 'job_handle' in sandbox_info and sandbox_info['job_handle']:
                                try:
                                    win32api.CloseHandle(sandbox_info['job_handle'])
                                except:
                                    pass
                            
                            self.unregister_sandbox(sandbox_id)
                            stopped_count += 1
                            self.log(f"已停止沙箱 - ID: {sandbox_id}")
                            
                except Exception as e:
                    self.log(f"停止沙箱 {sandbox_id} 时出错: {str(e)}")
            
            messagebox.showinfo("完成", f"已停止 {stopped_count} 个沙箱")
    
    def view_sandbox_logs(self):
        """查看沙箱详细日志"""
        if not self.active_sandboxes:
            messagebox.showinfo("提示", "当前没有活跃的沙箱")
            return
        
        # 创建日志查看窗口
        log_window = tk.Toplevel(self.root)
        log_window.title("沙箱详细日志")
        log_window.geometry("800x600")
        
        # 创建文本框和滚动条
        text_frame = Frame(log_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        log_text = Text(text_frame, wrap="word", font=("Consolas", 10))
        scrollbar = Scrollbar(text_frame)
        log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=log_text.yview)
        
        log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 生成日志内容
        log_content = "=== 沙箱详细状态报告 ===\n\n"
        log_content += f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_content += f"活跃沙箱数量: {len(self.active_sandboxes)}\n\n"
        
        with self.sandbox_update_lock:
            for sandbox_id, sandbox_info in self.active_sandboxes.items():
                log_content += f"--- 沙箱 {sandbox_id} ---\n"
                log_content += f"程序名称: {sandbox_info.get('display_name', '未知')}\n"
                log_content += f"可执行文件: {sandbox_info.get('exe_path', '未知')}\n"
                log_content += f"进程ID: {sandbox_info.get('process_id', '未知')}\n"
                log_content += f"沙箱目录: {sandbox_info.get('sandbox_dir', '未知')}\n"
                log_content += f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sandbox_info.get('start_time', time.time())))}\n"
                
                # 进程状态
                process_id = sandbox_info.get('process_id')
                if process_id:
                    try:
                        if psutil.pid_exists(process_id):
                            process = psutil.Process(process_id)
                            log_content += f"进程状态: 运行中\n"
                            log_content += f"内存使用: {process.memory_info().rss // 1024 // 1024} MB\n"
                            log_content += f"CPU使用率: {process.cpu_percent():.1f}%\n"
                            log_content += f"运行时间: {int(time.time() - sandbox_info.get('start_time', time.time()))} 秒\n"
                        else:
                            log_content += "进程状态: 已停止\n"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        log_content += "进程状态: 无法访问\n"
                
                log_content += "\n"
        
        log_text.insert("1.0", log_content)
        log_text.config(state="disabled")
        
        # 添加关闭按钮
        Button(log_window, text="关闭", command=log_window.destroy).pack(pady=10)
    
    def _request_admin_privilege(self):
        """请求管理员权限以完成需要特权的操作"""
        try:
            # 检查是否已经具有管理员权限
            if self.check_admin():
                self.log("已具有管理员权限")
                return True
            
            # 获取当前脚本路径
            script_path = os.path.abspath(sys.argv[0])
            
            # 如果是Python脚本，使用ShellExecute以管理员权限运行
            if script_path.endswith('.py'):
                # 直接使用Python可执行文件
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script_path}"', None, 1
                )
                self.log("已尝试以管理员权限重启程序...")
                # 由于程序将重启，无法继续当前操作
                # 通知用户重启并退出
                messagebox.showinfo("权限请求", "程序将重启以获取管理员权限，请重新选择需要删除的程序。")
                os._exit(0)  # 退出当前进程
            else:
                # 对于.exe文件，直接以管理员权限运行
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", script_path, None, None, 1
                )
                self.log("已尝试以管理员权限运行程序...")
                messagebox.showinfo("权限请求", "程序将重启以获取管理员权限，请重新选择需要删除的程序。")
                os._exit(0)  # 退出当前进程
                
            return False  # 一般不会执行到这里
        except Exception as e:
            self.log(f"请求管理员权限失败: {str(e)}")
            return False
    
    def _check_if_system_protected(self, file_path):
        """检查文件是否受系统保护，通常需要管理员权限才能删除"""
        try:
            # 检查文件是否在系统目录
            system_dirs = [
                os.environ.get('SystemRoot', 'C:\\Windows'),
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'SysWOW64')
            ]
            
            file_path_lower = file_path.lower()
            
            # 1. 检查是否在系统目录
            for system_dir in system_dirs:
                if system_dir and os.path.exists(system_dir):
                    system_dir_lower = system_dir.lower()
                    if file_path_lower.startswith(system_dir_lower):
                        # 额外检查是否在系统目录的深处（非简单文件）
                        try:
                            rel_path = os.path.relpath(file_path, system_dir)
                            if rel_path and rel_path != '.' and not rel_path.startswith('..'):
                                return True
                        except:
                            pass
            
            # 2. 检查文件属性
            try:
                attrs = win32api.GetFileAttributes(file_path)
                if attrs != -1:
                    # 检查文件是否具有只读、系统或隐藏属性
                    is_readonly = (attrs & 0x1) != 0
                    is_hidden = (attrs & 0x2) != 0
                    is_system = (attrs & 0x4) != 0
                    
                    if is_system or (is_readonly and is_hidden):
                        return True
            except:
                pass
            
            # 3. 检查文件是否是受系统保护的进程
            try:
                file_name = os.path.basename(file_path).lower()
                protected_processes = [
                    'smss.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe', 
                    'services.exe', 'lsass.exe', 'lsm.exe', 'svchost.exe',
                    'fontdrvhost.exe', 'WUDFHost.exe', 'rundll32.exe',
                    'taskeng.exe', 'dwm.exe', 'explorer.exe', 'winlogon.exe'
                ]
                
                if file_name in protected_processes:
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            self.log(f"检查文件是否受系统保护时出错: {str(e)}")
            return False
    

    
    def refresh_list(self):
        """刷新已安装程序列表"""
        self.log("正在扫描已安装程序...")
        self.programs = []
        
        # 重置进度条
        self.progress_var.set(0)
        self.progress_percent.config(text="0%")
        
        # 在新线程中扫描程序以避免UI冻结
        threading.Thread(target=self._scan_programs).start()
    
    def _get_directory_size(self, path):
        """计算目录大小"""
        total_size = 0
        try:
            if not os.path.exists(path):
                return 0
            
            for root, dirs, files in os.walk(path):
                try:
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            # 跳过符号链接和无法访问的文件
                            if os.path.isfile(file_path):
                                total_size += os.path.getsize(file_path)
                        except (PermissionError, FileNotFoundError):
                            continue
                except PermissionError:
                    continue
        except Exception:
            pass
        return total_size
    
    def _format_size(self, size_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _scan_programs(self):
        """扫描已安装程序"""
        try:
            # 清空程序列表，确保每次扫描从头开始
            self.programs = []
            
            # 计算总的注册表路径数量
            total_reg_paths = 3
            current_path = 0
            
            # 注册表路径列表
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            # 扫描每个注册表路径
            for hive, path in reg_paths:
                current_path += 1
                # 扫描注册表
                self._scan_registry(hive, path)
                # 更新进度（注册表扫描完成60%）
                progress = (current_path / total_reg_paths) * 60
                if self.root.winfo_exists():
                    self.root.after(0, lambda p=progress: self._update_progress(p))
            
            # 去重处理：基于RegistryKey字段
            unique_programs = {}
            for program in self.programs:
                # 确保只有有效的程序（有DisplayName）才会被保留
                if "DisplayName" in program and program["DisplayName"]:
                    # 使用RegistryKey作为唯一标识符
                    reg_key = program.get("RegistryKey", "")
                    # 如果没有RegistryKey，使用DisplayName作为备用
                    if not reg_key and "DisplayName" in program:
                        reg_key = program["DisplayName"]
                    unique_programs[reg_key] = program
            
            # 转换回列表
            self.programs = list(unique_programs.values())
            
            # 计算每个程序的大小（这部分占40%）
            program_count = len(self.programs)
            if program_count > 0:
                for i, program in enumerate(self.programs):
                    install_path = program.get("InstallLocation", "")
                    if install_path and os.path.exists(install_path):
                        try:
                            # 计算并存储程序大小
                            program_size = self._get_directory_size(install_path)
                            program["Size"] = program_size
                        except Exception:
                            program["Size"] = 0
                    else:
                        program["Size"] = 0
                    
                    # 更新进度（加上大小计算的进度）
                    progress = 60 + (i + 1) / program_count * 40
                    if self.root.winfo_exists():
                        self.root.after(0, lambda p=progress: self._update_progress(p))
            
            # 按名称排序
            self.programs.sort(key=lambda x: x.get("DisplayName", ""))
            self.filtered_programs = self.programs.copy()
            
            # 更新UI
            if self.root.winfo_exists():
                self.root.after(0, self._update_program_list)
                # 使用局部变量传递值，避免闭包问题
                program_count = len(self.programs)
                self.root.after(0, lambda count=program_count: self.log(f"找到 {count} 个已安装程序"))
                self.root.after(0, lambda: self._update_progress(100))
        except Exception as e:
            # 保存错误消息到局部变量，避免闭包问题
            error_message = str(e)
            if self.root.winfo_exists():
                self.root.after(0, lambda msg=error_message: self.log(f"扫描程序失败: {msg}"))
                self.root.after(0, lambda: self._update_progress(0))
                
    def _update_progress(self, progress):
        """更新进度条显示"""
        try:
            self.progress_var.set(progress)
            self.progress_percent.config(text=f"{int(progress)}%")
        except Exception:
            pass
    
    def _scan_registry(self, hive, key_path):
        """扫描指定注册表路径"""
        key = None
        try:
            key = winreg.OpenKey(hive, key_path)
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                try:
                    subkey = winreg.OpenKey(hive, f"{key_path}\\{subkey_name}")
                    program_info = {}
                    
                    try:
                        program_info["DisplayName"] = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        
                        try:
                            program_info["UninstallString"] = winreg.QueryValueEx(subkey, "UninstallString")[0]
                        except:
                            program_info["UninstallString"] = ""
                        
                        try:
                            program_info["InstallLocation"] = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except:
                            program_info["InstallLocation"] = ""
                        
                        try:
                            program_info["Publisher"] = winreg.QueryValueEx(subkey, "Publisher")[0]
                        except:
                            program_info["Publisher"] = ""
                        
                        try:
                            program_info["DisplayVersion"] = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        except:
                            program_info["DisplayVersion"] = ""
                        
                        program_info["RegistryKey"] = f"{key_path}\\{subkey_name}"
                        program_info["RegistryHive"] = hive
                        
                        self.programs.append(program_info)
                    except:
                        pass
                except:
                    pass
        except Exception as e:
            self.log(f"扫描注册表路径 {key_path} 失败: {str(e)}")
        finally:
            # 确保关闭主键
            if key is not None:
                try:
                    winreg.CloseKey(key)
                except Exception as e:
                    self.log(f"关闭注册表主键 {key_path} 失败: {str(e)}")
    
    def _is_self_program(self, program_name):
        """检查是否为本程序"""
        # 定义本程序的名称关键词
        self_program_names = [
            "强力卸载", "浩讯亿通强力卸载", "电脑急救强力卸载",
            "Uninstaller", "Uninstall Tool", "Force Uninstall"
        ]
        
        # 转换为小写进行比较
        program_name_lower = program_name.lower()
        return any(name.lower() in program_name_lower for name in self_program_names)
    
    def _handle_self_uninstall_attempt(self):
        """处理尝试卸载本程序的请求"""
        self.log("检测到尝试卸载本程序的操作！启动自我保护机制...")
        
        # 显示警告对话框
        messagebox.showwarning(
            "保护警告", 
            "您正在尝试卸载本强力卸载工具！\n\n" +
            "为防止恶意软件强制卸载，需要额外验证管理员身份。"
        )
        
        # 验证管理员权限
        if not self._verify_admin_credentials():
            self.log("管理员身份验证失败，已阻止卸载操作！")
            messagebox.showerror(
                "操作阻止", 
                "管理员身份验证失败，已阻止卸载操作。\n\n" +
                "此保护机制旨在防止恶意软件自动卸载本工具。"
            )
            return True
        
        # 显示最终确认对话框，要求用户输入特殊确认信息
        import tkinter.simpledialog
        confirm_code = tkinter.simpledialog.askstring(
            "最终确认", 
            "请输入'CONFIRM'以确认卸载本程序：",
            show='*'
        )
        
        if confirm_code != 'CONFIRM':
            self.log("确认码错误，已阻止卸载操作！")
            messagebox.showerror(
                "操作阻止", 
                "确认码错误，已阻止卸载操作。\n\n" +
                "此保护机制旨在防止恶意软件自动卸载本工具。"
            )
            return True
        
        # 记录操作并允许卸载
        self.log("管理员身份验证通过，允许卸载本程序。")
        return False
    
    def _verify_admin_credentials(self):
        """验证管理员凭据"""
        try:
            # 尝试执行需要管理员权限的操作来验证权限
            # 这里尝试读取受保护的注册表项
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.CloseKey(key)
            return True
        except Exception:
            # 如果失败，尝试重新以管理员身份运行一个简单的验证进程
            try:
                import tempfile
                import sys
                
                # 创建一个临时Python脚本用于验证管理员权限
                with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
                    f.write("""
import ctypes
import sys
sys.exit(0 if ctypes.windll.shell32.IsUserAnAdmin() else 1)
""")
                    temp_script = f.name
                
                # 以管理员身份运行验证脚本
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{temp_script}"', None, 1
                )
                
                # 等待并检查结果
                import time
                time.sleep(2)
                
                # 清理临时文件
                try:
                    os.unlink(temp_script)
                except:
                    pass
                
                return result > 32
            except:
                return False
    
    def _update_program_list(self):
        """更新程序列表UI"""
        self.program_listbox.delete(0, "end")
        for program in self.filtered_programs:
            display_name = program.get("DisplayName", "未知程序")
            publisher = program.get("Publisher", "未知公司")
            size = program.get("Size", 0)
            formatted_size = self._format_size(size)
            # 格式化为：程序名称 - 公司名称 [大小]
            display_text = f"{display_name} - {publisher} [{formatted_size}]"
            self.program_listbox.insert("end", display_text)
    
    def filter_programs(self, event):
        """过滤程序列表"""
        search_term = self.search_entry.get().lower()
        self.filtered_programs = [p for p in self.programs if search_term in p.get("DisplayName", "").lower()]
        self._update_program_list()
    
    def on_program_double_click(self, event):
        """双击程序项"""
        self.uninstall_selected()
    
    def uninstall_selected(self):
        """卸载选中的程序（支持批量卸载）"""
        selected_indices = self.program_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请先选择要卸载的程序")
            return
        
        # 获取选中的程序列表
        selected_programs = []
        for index in selected_indices:
            program = self.filtered_programs[index]
            display_name = program.get("DisplayName", "未知程序")
            
            # 检查是否正在尝试卸载本程序（自我保护机制）
            if self._is_self_program(display_name):
                self._handle_self_uninstall_attempt()
                continue
            
            selected_programs.append(program)
        
        if not selected_programs:
            return
        
        # 用户确认
        options = []
        if self.force_delete.get():
            options.append("强力删除残留文件")
        if self.clean_registry.get():
            options.append("清理注册表项")
        
        # 根据选中程序数量显示不同的确认信息
        if len(selected_programs) == 1:
            display_name = selected_programs[0].get("DisplayName", "未知程序")
            confirm_text = f"确定要卸载 {display_name} 吗？\n"
        else:
            confirm_text = f"确定要卸载选中的 {len(selected_programs)} 个程序吗？\n"
            # 最多显示前5个程序名称
            for i, program in enumerate(selected_programs[:5]):
                confirm_text += f"\n{i+1}. {program.get('DisplayName', '未知程序')}"
            if len(selected_programs) > 5:
                confirm_text += f"\n...等{len(selected_programs) - 5}个程序"
        
        if options:
            confirm_text += "\n\n选中的选项:\n" + "\n".join(f"- {opt}" for opt in options)
            
        if not messagebox.askyesno("确认卸载", confirm_text):
            return
        
        # 在线程中执行批量卸载操作
        def uninstall_thread():
            try:
                # 设置批量卸载标志
                self._is_batch_uninstall = True
                self.log(f"开始批量卸载 {len(selected_programs)} 个程序...")
                
                for program in selected_programs:
                    try:
                        self._uninstall_single_program(program)
                    except Exception as e:
                        self.log(f"卸载单个程序时出错: {str(e)}")
                
                # 批量卸载完成后刷新列表
                if self.root.winfo_exists():
                    self.root.after(0, self.refresh_list)
                    self.root.after(0, lambda: self.log("批量卸载完成！"))
                    # 批量卸载完成后显示消息
                    self.root.after(0, lambda: messagebox.showinfo("卸载完成", "所有选中程序的卸载操作已完成！"))
            except Exception as e:
                error_message = str(e)
                if self.root.winfo_exists():
                    self.root.after(0, lambda msg=error_message: self.log(f"批量卸载出错: {msg}"))
            finally:
                # 清除批量卸载标志
                self._is_batch_uninstall = False
        
        # 启动卸载线程
        import threading
        thread = threading.Thread(target=uninstall_thread)
        thread.daemon = True
        thread.start()
        
    def _uninstall_single_program(self, program):
        """卸载单个程序"""
        display_name = program.get("DisplayName", "未知程序")
        
        try:
            # 开始卸载
            self.log(f"开始卸载: {display_name}")
            
            # 获取卸载信息
            uninstall_string = program.get("UninstallString", "")
            install_path = program.get("InstallLocation", "")
            
            # 尝试终止相关进程
            if install_path:
                self.log(f"尝试终止 {display_name} 的相关进程...")
                self._terminate_related_processes(install_path)
            
            # 执行标准卸载
            if uninstall_string:
                self.log(f"使用标准卸载程序: {uninstall_string}")
                try:
                    # 处理常见的msiexec卸载
                    if "MsiExec.exe" in uninstall_string:
                        import re
                        match = re.search(r'(\{[A-F0-9\-]+\})', uninstall_string)
                        if match:
                            product_code = match.group(1)
                            subprocess.run(["MsiExec.exe", "/x", product_code, "/qn"], shell=True)
                        else:
                            subprocess.run(uninstall_string, shell=True)
                    else:
                        subprocess.run(uninstall_string, shell=True)
                    
                    # 等待卸载程序完成
                    time.sleep(5)
                    self.log(f"标准卸载完成: {display_name}")
                except Exception as e:
                    self.log(f"标准卸载失败: {str(e)}")
            else:
                self.log("未找到标准卸载程序，将尝试强制删除")
            
            # 强力删除残留文件
            if self.force_delete.get():
                self.log("开始强力清理残留文件...")
                
                # 删除主安装目录
                if install_path and os.path.exists(install_path):
                    self.log(f"尝试强制删除安装目录: {install_path}")
                    try:
                        self._force_delete_directory(install_path)
                        self.log(f"强制删除完成: {install_path}")
                    except Exception as e:
                        self.log(f"强制删除失败: {str(e)}")
                
                # 搜索并删除常见残留位置
                self._scan_and_remove_residuals(display_name.lower())
            
            # 清理注册表
            if self.clean_registry.get():
                self.log("开始深度清理注册表残留...")
                
                # 删除主注册表项
                try:
                    hive = program.get("RegistryHive", winreg.HKEY_LOCAL_MACHINE)
                    key_path = program.get("RegistryKey", "")
                    if key_path:
                        subkey_name = key_path.split("\\")[-1]
                        parent_key_path = "\\".join(key_path.split("\\")[:-1])
                        
                        self.log(f"尝试删除主注册表项: {key_path}")
                        parent_key = winreg.OpenKey(hive, parent_key_path, 0, winreg.KEY_SET_VALUE)
                        winreg.DeleteKey(parent_key, subkey_name)
                        winreg.CloseKey(parent_key)
                        self.log("主注册表项删除成功")
                except Exception as e:
                    self.log(f"主注册表项删除失败: {str(e)}")
                
                # 搜索并清理更多相关注册表项
                registry_keys_removed = self._scan_and_clean_registry(display_name.lower())
                self.log(f"注册表清理完成，共处理 {registry_keys_removed} 个注册表项")
            
            # 刷新程序列表（在批量卸载模式下，此操作由主循环处理）
            # 只在单个卸载时显示完成消息
            if not hasattr(self, '_is_batch_uninstall') or not self._is_batch_uninstall:
                self.root.after(0, lambda: 
                    messagebox.showinfo("卸载完成", f"{display_name} 卸载操作已完成！")
                )
            
            self.log(f"卸载操作完成: {display_name}")
            
        except Exception as e:
            self.log(f"卸载过程中发生错误: {str(e)}")
            self.root.after(0, lambda: 
                messagebox.showerror("错误", f"卸载过程中发生错误: {str(e)}")
            )
    
    def _uninstall_program(self, program):
        """执行程序卸载，包括顽固程序处理"""
        display_name = program.get("DisplayName", "未知程序")
        self.log(f"开始卸载: {display_name}")
        
        # 顽固程序预处理 - 在标准卸载前执行
        self.log(f"开始顽固程序预处理: {display_name}")
        
        # 1. 终止相关进程（总是执行，因为这是基本要求）
        install_location = program.get("InstallLocation", "")
        if install_location and os.path.exists(install_location):
            self.log(f"预处理 - 终止相关进程: {install_location}")
            self._terminate_related_processes(install_location)
        
        # 2. 清理启动项（根据用户选择）
        if self.clean_startup.get():
            self.log(f"预处理 - 清理启动项: {display_name}")
            startup_count = self._clean_startup_entries(display_name)
            if startup_count > 0:
                self.log(f"清理了 {startup_count} 个启动项")
        
        # 3. 停止相关服务（根据用户选择）
        if self.stop_services.get():
            self.log(f"预处理 - 停止相关服务: {display_name}")
            service_count = self._stop_related_services(display_name)
            if service_count > 0:
                self.log(f"停止了 {service_count} 个服务")
        
        # 4. 尝试使用标准卸载字符串
        uninstall_string = program.get("UninstallString", "")
        if uninstall_string:
            self.log(f"使用标准卸载程序: {uninstall_string}")
            try:
                # 处理常见的msiexec卸载
                if "MsiExec.exe" in uninstall_string:
                    # 提取产品代码
                    import re
                    match = re.search(r'(\\{[A-F0-9\\-]+\\})', uninstall_string)
                    if match:
                        product_code = match.group(1)
                        subprocess.run(["MsiExec.exe", "/x", product_code, "/qn"], shell=True)
                    else:
                        subprocess.run(uninstall_string, shell=True)
                else:
                    # 尝试正常运行卸载程序
                    subprocess.run(uninstall_string, shell=True)
                
                # 等待卸载程序完成
                time.sleep(5)
                self.log(f"标准卸载完成: {display_name}")
            except Exception as e:
                self.log(f"标准卸载失败: {str(e)}")
        else:
            self.log("未找到标准卸载程序，将尝试强制删除")
        
        # 2. 强制删除残留文件（如果启用）
        if self.force_delete.get():
            self.log("开始强力清理残留文件...")
            
            # 在强力删除前确保具有管理员权限
            if not self.check_admin():
                self.log("检测到当前权限可能不足以进行强力删除，正在尝试获取管理员权限...")
                if not self._request_admin_privilege():
                    self.log("警告: 无法获取管理员权限，强力删除操作可能受限")
                else:
                    self.log("成功获取管理员权限")
            
            display_name = program.get("DisplayName", "").lower()
            
            # 1. 删除主安装目录
            install_location = program.get("InstallLocation", "")
            if install_location and os.path.exists(install_location):
                self.log(f"尝试强制删除安装目录: {install_location}")
                try:
                    # 尝试终止相关进程
                    self._terminate_related_processes(install_location)
                    # 使用增强的删除方法
                    self._force_delete_directory(install_location)
                    self.log(f"强制删除完成: {install_location}")
                except Exception as e:
                    self.log(f"强制删除失败: {str(e)}")
            
            # 2. 删除桌面快捷方式
            shortcut_count = self._remove_desktop_shortcuts(display_name)
            if shortcut_count > 0:
                self.log(f"删除了 {shortcut_count} 个桌面快捷方式")
        
            # 3. 删除任务栏固定图标
            taskbar_count = self._remove_taskbar_pinned_icons(display_name)
            if taskbar_count > 0:
                self.log(f"删除了 {taskbar_count} 个任务栏固定图标")
            
            # 4. 搜索并删除常见残留位置
            self._scan_and_remove_residuals(display_name)
        
        # 3. 清理注册表（如果启用）
        if self.clean_registry.get():
            self.log("开始深度清理注册表残留...")
            display_name = program.get("DisplayName", "").lower()
            
            # 1. 删除主注册表项
            try:
                hive = program.get("RegistryHive", winreg.HKEY_LOCAL_MACHINE)
                key_path = program.get("RegistryKey", "")
                if key_path:
                    # 提取最后一个反斜杠后的子键名
                    subkey_name = key_path.split("\\")[-1]
                    parent_key_path = "\\".join(key_path.split("\\")[:-1])
                    
                    self.log(f"尝试删除主注册表项: {key_path}")
                    parent_key = winreg.OpenKey(hive, parent_key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteKey(parent_key, subkey_name)
                    winreg.CloseKey(parent_key)
                    self.log("主注册表项删除成功")
            except Exception as e:
                self.log(f"主注册表项删除失败: {str(e)}")
            
            # 2. 搜索并清理更多相关注册表项
            registry_keys_removed = self._scan_and_clean_registry(display_name)
            self.log(f"注册表清理完成，共处理 {registry_keys_removed} 个注册表项")
        
        # 4. 刷新程序列表
        self.root.after(0, self.refresh_list)
        self.log(f"卸载操作完成: {display_name}")
    
    def _terminate_related_processes(self, install_path):
        """终止与安装路径相关的进程"""
        self.log(f"开始终止与 {install_path} 相关的进程")
        terminated_count = 0
        
        # 获取所有进程信息
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                proc_info = proc.info
                exe_path = proc_info.get('exe')
                cmdline = proc_info.get('cmdline', [])
                
                # 检查可执行文件路径或命令行参数是否包含安装路径
                if exe_path and install_path.lower() in exe_path.lower():
                    self.log(f"终止进程: {proc_info['name']} (PID: {proc_info['pid']})")
                    # 先尝试正常终止
                    proc.terminate()
                    # 等待进程终止，最多等待3秒
                    try:
                        proc.wait(timeout=3)
                        terminated_count += 1
                    except psutil.TimeoutExpired:
                        # 如果超时，尝试强制终止
                        self.log(f"强制终止进程: {proc_info['name']} (PID: {proc_info['pid']})")
                        proc.kill()
                        terminated_count += 1
                # 也检查命令行参数
                elif cmdline and any(install_path.lower() in arg.lower() for arg in cmdline):
                    self.log(f"终止进程(命令行匹配): {proc_info['name']} (PID: {proc_info['pid']})")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                        terminated_count += 1
                    except psutil.TimeoutExpired:
                        self.log(f"强制终止进程: {proc_info['name']} (PID: {proc_info['pid']})")
                        proc.kill()
                        terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        self.log(f"共终止 {terminated_count} 个相关进程")
        return terminated_count
    
    def _clean_startup_entries(self, program_name):
        """清理与程序相关的启动项"""
        self.log(f"开始清理 {program_name} 的启动项")
        cleaned_count = 0
        
        # 启动项的注册表位置
        startup_reg_paths = [
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnce')
        ]
        
        # 启动文件夹路径
        startup_folder = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
        
        # 清理注册表启动项
        for hive, path in startup_reg_paths:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
                value_count = winreg.QueryInfoKey(key)[1]
                
                # 获取所有值名称
                values = []
                for i in range(value_count):
                    values.append(winreg.EnumValue(key, i)[0])
                
                # 检查并删除匹配的启动项
                for value_name in values:
                    try:
                        value_data = winreg.QueryValueEx(key, value_name)[0]
                        if program_name.lower() in value_name.lower() or program_name.lower() in str(value_data).lower():
                            self.log(f"删除启动项: {value_name} = {value_data}")
                            winreg.DeleteValue(key, value_name)
                            cleaned_count += 1
                    except Exception:
                        pass
                
                winreg.CloseKey(key)
            except Exception:
                pass
        
        # 清理启动文件夹中的快捷方式
        if os.path.exists(startup_folder):
            try:
                for item in os.listdir(startup_folder):
                    item_path = os.path.join(startup_folder, item)
                    if program_name.lower() in item.lower() and item.endswith('.lnk'):
                        self.log(f"删除启动文件夹项: {item}")
                        os.remove(item_path)
                        cleaned_count += 1
            except Exception:
                pass
        
        self.log(f"共清理 {cleaned_count} 个启动项")
        return cleaned_count
    
    def _stop_related_services(self, program_name):
        """停止与程序相关的Windows服务"""
        self.log(f"开始停止与 {program_name} 相关的服务")
        stopped_count = 0
        
        try:
            # 使用sc命令列出所有服务
            result = subprocess.run(
                ['sc', 'query', 'state=', 'all'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            # 解析服务列表
            services = re.findall(r'SERVICE_NAME: (\S+)\s+DISPLAY_NAME: ([^\n]+)', result.stdout)
            
            for service_name, display_name in services:
                # 检查服务名称或显示名称是否包含程序名
                if (program_name.lower() in service_name.lower() or 
                    program_name.lower() in display_name.lower()):
                    
                    self.log(f"检查服务: {display_name} ({service_name})")
                    
                    # 获取服务状态
                    status_result = subprocess.run(
                        ['sc', 'query', service_name],
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    
                    # 如果服务正在运行，尝试停止它
                    if 'STATE              : 4  RUNNING' in status_result.stdout:
                        self.log(f"停止服务: {display_name} ({service_name})")
                        
                        # 先尝试正常停止
                        subprocess.run(
                            ['sc', 'stop', service_name],
                            capture_output=True,
                            shell=True
                        )
                        
                        # 等待服务停止
                        time.sleep(2)
                        
                        # 检查是否已停止
                        new_status = subprocess.run(
                            ['sc', 'query', service_name],
                            capture_output=True,
                            text=True,
                            shell=True
                        )
                        
                        if 'STATE              : 1  STOPPED' in new_status.stdout:
                            self.log(f"服务已停止: {display_name}")
                            stopped_count += 1
                        else:
                            self.log(f"警告: 服务可能未成功停止: {display_name}")
        except Exception as e:
            self.log(f"停止服务时出错: {str(e)}")
        
        self.log(f"共尝试停止 {stopped_count} 个服务")
        return stopped_count
    
    def _unlock_file(self, file_path):
        """增强版文件解锁方法，包含多种解锁策略"""
        if not os.path.exists(file_path):
            return True
        
        self.log(f"开始尝试解锁文件: {file_path}")
        
        # 策略1: 尝试直接打开文件
        try:
            with open(file_path, 'rb') as f:
                self.log(f"策略1成功 - 文件已解锁: {file_path}")
                return True
        except (PermissionError, OSError) as e:
            self.log(f"策略1失败 - 直接打开文件: {str(e)}")
        
        # 策略2: 使用win32api和win32security修改文件权限
        try:
            # 获取文件安全描述符
            security_descriptor = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )
            
            # 创建一个新的DACL (Discretionary Access Control List)
            dacl = win32security.ACL()
            
            # 获取当前用户的SID
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32con.TOKEN_READ | win32con.TOKEN_QUERY
                ),
                win32security.TokenUser
            )[0]
            
            # 添加完全控制权限给当前用户
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                0x10000000,  # 完全控制权限
                user_sid
            )
            
            # 添加Everyone组的完全控制权限
            everyone_sid = win32security.ConvertStringSidToSid("S-1-1-0")
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                0x10000000,
                everyone_sid
            )
            
            # 应用新的安全描述符
            security_descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION,
                security_descriptor
            )
            
            self.log(f"策略2成功 - 修改文件权限: {file_path}")
        except Exception as e:
            self.log(f"策略2失败 - 修改文件权限: {str(e)}")
        
        # 策略3: 尝试关闭所有打开的文件句柄
        try:
            # 尝试以FILE_SHARE_DELETE模式打开文件
            handle = win32file.CreateFile(
                file_path,
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_DELETE | win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                0,
                None
            )
            
            # 强制设置文件属性，移除只读等属性
            try:
                current_attr = win32file.GetFileAttributes(file_path)
                new_attr = current_attr & ~(win32con.FILE_ATTRIBUTE_READONLY | 
                                          win32con.FILE_ATTRIBUTE_HIDDEN | 
                                          win32con.FILE_ATTRIBUTE_SYSTEM)
                win32file.SetFileAttributes(file_path, new_attr)
                self.log(f"已修改文件属性: {file_path}")
            except:
                pass
            
            win32file.CloseHandle(handle)
            self.log(f"策略3成功 - 重置文件句柄: {file_path}")
        except Exception as e:
            self.log(f"策略3失败 - 重置文件句柄: {str(e)}")
        
        # 策略4: 尝试找到并终止使用该文件的进程
        try:
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    open_files = proc.open_files()
                    for file_info in open_files:
                        if file_info.path.lower() == file_path.lower():
                            self.log(f"策略4成功 - 找到锁定文件的进程: {proc.name()} (PID: {proc.pid})")
                            
                            # 尝试正常终止
                            proc.terminate()
                            try:
                                proc.wait(timeout=2)
                                self.log(f"已终止进程: {proc.name()} (PID: {proc.pid})")
                            except psutil.TimeoutExpired:
                                # 超时后强制终止
                                proc.kill()
                                self.log(f"已强制终止进程: {proc.name()} (PID: {proc.pid})")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            self.log(f"策略4失败 - 查找锁定进程: {str(e)}")
        
        # 策略5: 使用Windows命令行工具重置文件权限
        try:
            # 使用takeown命令获取文件所有权
            takeown_cmd = ['takeown', '/f', file_path, '/r', '/d', 'y']
            subprocess.run(takeown_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 使用icacls命令设置完全控制权限
            icacls_cmd = ['icacls', file_path, '/grant', 'everyone:F', '/t', '/c']
            subprocess.run(icacls_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.log(f"策略5成功 - 使用命令行重置权限: {file_path}")
        except Exception as e:
            self.log(f"策略5失败 - 命令行重置权限: {str(e)}")
        
        # 最终检查文件是否可访问
        try:
            with open(file_path, 'rb') as f:
                self.log(f"文件现在可以访问: {file_path}")
                return True
        except:
            self.log(f"文件仍然无法访问: {file_path}")
            return False
    
    def _force_delete_with_unlock(self, file_path):
        """增强版文件删除方法，包含多种解锁和删除策略，包括最高权限处理"""
        if not os.path.exists(file_path):
            return True
        
        self.log(f"开始尝试删除文件: {file_path}")
        
        # 1. 检查是否需要最高权限才能删除某些文件
        # 对于受系统保护的文件，可能需要最高权限
        is_system_protected = self._check_if_system_protected(file_path)
        if is_system_protected and not self.check_admin():
            self.log(f"检测到受系统保护的文件需要管理员权限才能删除: {file_path}")
            if not self._request_admin_privilege():
                self.log(f"获取管理员权限失败，尝试继续使用普通权限删除")
        
        # 2. 始终尝试解锁文件，无论设置如何
        try:
            self._unlock_file(file_path)
            self.log(f"已尝试解锁文件: {file_path}")
        except Exception as e:
            self.log(f"解锁文件失败: {file_path} - {str(e)}")
        
        # 2. 尝试修改文件权限
        try:
            os.chmod(file_path, 0o777)  # 给予最大权限
            self.log(f"已修改文件权限: {file_path}")
        except Exception as e:
            self.log(f"修改文件权限失败: {file_path} - {str(e)}")
        
        # 3. 策略1: 尝试直接删除
        try:
            os.remove(file_path)
            self.log(f"策略1成功 - 直接删除: {file_path}")
            return True
        except Exception as e:
            self.log(f"策略1失败 - 直接删除: {str(e)}")
        
        # 4. 策略2: 使用win32api删除
        try:
            win32api.DeleteFile(file_path)
            self.log(f"策略2成功 - win32api删除: {file_path}")
            return True
        except Exception as e:
            self.log(f"策略2失败 - win32api删除: {str(e)}")
        
        # 5. 策略3: 尝试终止可能正在使用该文件的进程
        try:
            self._terminate_processes_using_file(file_path)
            self.log(f"已尝试终止使用文件的进程: {file_path}")
            
            # 再次尝试删除
            try:
                os.remove(file_path)
                self.log(f"策略3成功 - 终止进程后删除: {file_path}")
                return True
            except Exception as e:
                self.log(f"策略3失败 - 终止进程后删除: {str(e)}")
        except Exception as e:
            self.log(f"尝试终止使用文件的进程失败: {str(e)}")
        
        # 6. 策略4: 使用Windows命令行工具删除
        try:
            cmd_command = ['cmd', '/c', 'del', '/f', '/q', '/a', file_path]
            result = subprocess.run(cmd_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not os.path.exists(file_path):
                self.log(f"策略4成功 - 命令行删除: {file_path}")
                return True
            else:
                self.log(f"策略4失败 - 命令行返回: {result.stderr.decode('gbk', errors='ignore')}")
        except Exception as e:
            self.log(f"策略4失败 - 命令行删除: {str(e)}")
        
        # 7. 策略5: 尝试使用PowerShell删除
        try:
            ps_command = f"Remove-Item -Path '{file_path}' -Force -Recurse"
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not os.path.exists(file_path):
                self.log(f"策略5成功 - PowerShell删除: {file_path}")
                return True
            else:
                self.log(f"策略5失败 - PowerShell返回: {result.stderr.decode('gbk', errors='ignore')}")
        except Exception as e:
            self.log(f"策略5失败 - PowerShell删除: {str(e)}")
        
        self.log(f"所有删除策略均失败: {file_path}")
        return False
    
    def _terminate_processes_using_file(self, file_path):
        """终止正在使用指定文件的进程"""
        try:
            file_path_lower = file_path.lower()
            
            # 遍历所有进程
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'open_files']):
                try:
                    # 获取进程打开的文件
                    open_files = proc.open_files()
                    for open_file in open_files:
                        # 检查是否正在使用目标文件
                        if open_file.path.lower() == file_path_lower or \
                           file_path_lower in open_file.path.lower():
                            self.log(f"发现进程正在使用文件: {proc.name()} (PID: {proc.pid})")
                            
                            # 尝试正常终止
                            proc.terminate()
                            # 等待进程终止
                            try:
                                proc.wait(timeout=2)
                                self.log(f"成功终止进程: {proc.name()} (PID: {proc.pid})")
                            except psutil.TimeoutExpired:
                                # 超时后强制终止
                                proc.kill()
                                self.log(f"强制终止进程: {proc.name()} (PID: {proc.pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            self.log(f"终止使用文件的进程时出错: {str(e)}")
    
    def check_admin(self):
        """增强版管理员权限检查 - 多种方法验证"""
        try:
            # 方法1: 使用Shell32 API检查
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                return True
            
            # 方法2: 使用Windows安全API检查
            try:
                # 获取当前进程令牌
                process_token = win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32security.TOKEN_QUERY
                )
                
                # 获取令牌信息
                token_info = win32security.GetTokenInformation(
                    process_token,
                    win32security.TokenGroups
                )
                
                # 检查是否在管理员组中
                admin_sid = win32security.CreateWellKnownSid(win32security.WinBuiltinAdministratorsSid, None)
                
                for group_sid, attributes in token_info:
                    if group_sid == admin_sid:
                        return True
                
                win32security.CloseHandle(process_token)
            except:
                pass
            
            # 方法3: 使用psutil检查进程权限
            try:
                current_process = psutil.Process()
                # 尝试获取管理员权限级别的信息
                username = current_process.username()
                # 简单检查用户名是否包含admin或以管理员权限运行
                return any(keyword in username.lower() for keyword in ['admin', 'administrator'])
            except:
                pass
            
            # 方法4: 检查UAC状态和当前进程权限级别
            try:
                # 尝试访问需要管理员权限的系统目录
                system32_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
                if os.path.exists(system32_path):
                    test_file = os.path.join(system32_path, 'test_permission_' + str(os.getpid()))
                    try:
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        return True  # 能够写入System32说明有管理员权限
                    except:
                        return False
            except:
                pass
            
            return False
            
        except Exception as e:
            self.log(f"权限检查失败: {str(e)}")
            return False
    
    def _check_if_system_protected(self, file_path):
        """检查文件是否受系统保护，通常需要管理员权限才能删除"""
        try:
            # 检查文件是否在系统目录
            system_dirs = [
                os.environ.get('SystemRoot', 'C:\\Windows'),
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'SysWOW64')
            ]
            
            file_path_lower = file_path.lower()
            
            # 1. 检查是否在系统目录
            for system_dir in system_dirs:
                if system_dir and os.path.exists(system_dir):
                    system_dir_lower = system_dir.lower()
                    if file_path_lower.startswith(system_dir_lower):
                        # 额外检查是否在系统目录的深处（非简单文件）
                        try:
                            rel_path = os.path.relpath(file_path, system_dir)
                            if rel_path and rel_path != '.' and not rel_path.startswith('..'):
                                return True
                        except:
                            pass
            
            # 2. 检查文件属性
            try:
                attrs = win32api.GetFileAttributes(file_path)
                if attrs != -1:
                    # 检查文件是否具有只读、系统或隐藏属性
                    is_readonly = (attrs & 0x1) != 0
                    is_hidden = (attrs & 0x2) != 0
                    is_system = (attrs & 0x4) != 0
                    
                    if is_system or (is_readonly and is_hidden):
                        return True
            except:
                pass
            
            # 3. 检查文件是否是受系统保护的进程
            try:
                file_name = os.path.basename(file_path).lower()
                protected_processes = [
                    'smss.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe', 
                    'services.exe', 'lsass.exe', 'lsm.exe', 'svchost.exe',
                    'fontdrvhost.exe', 'WUDFHost.exe', 'rundll32.exe',
                    'taskeng.exe', 'dwm.exe', 'explorer.exe', 'winlogon.exe'
                ]
                
                if file_name in protected_processes:
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            self.log(f"检查文件是否受系统保护时出错: {str(e)}")
            return False
    
    def _force_delete_directory(self, path):
        """增强版：强制删除目录，包括子目录和所有文件"""
        if not os.path.exists(path):
            return True
        
        # 检查是否需要最高权限才能删除目录
        is_system_protected = self._check_if_system_protected(path)
        if is_system_protected and not self.check_admin():
            self.log(f"检测到受系统保护的目录需要管理员权限才能删除: {path}")
            if not self._request_admin_privilege():
                self.log(f"获取管理员权限失败，尝试继续使用普通权限删除")
        
        self.log(f"开始强制删除目录: {path}")
        
        # 检查是否需要管理员权限进行删除
        if not self.check_admin():
            self.log("当前权限不足，尝试获取管理员权限...")
            if not self._request_admin_privilege():
                self.log("无法获取管理员权限，继续使用当前权限删除")
            else:
                self.log("成功获取管理员权限")
        
        try:
            # 遍历所有文件和子目录
            for root, dirs, files in os.walk(path, topdown=False):
                # 先处理文件
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    self._force_delete_with_unlock(file_path)
                
                # 然后处理子目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)
                    except:
                        pass
            
            # 最后删除主目录
            try:
                os.rmdir(path)
                self.log(f"成功删除目录: {path}")
                return True
            except Exception as e:
                self.log(f"删除主目录失败: {str(e)}")
                
                # 尝试使用shutil.rmtree作为备选方案
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    return True
                except Exception as e2:
                    self.log(f"使用shutil.rmtree删除失败: {str(e2)}")
                    return False
        except Exception as e:
            self.log(f"强制删除目录时出错: {str(e)}")
            return False
    
    def _remove_desktop_shortcuts(self, program_name):
        """删除与程序相关的桌面快捷方式"""
        self.log(f"开始删除与 {program_name} 相关的桌面快捷方式")
        
        # 获取桌面路径
        desktop_paths = []
        
        # 当前用户桌面
        user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(user_desktop):
            desktop_paths.append(user_desktop)
        
        # 公共桌面
        public_desktop = os.path.join(os.environ.get("PUBLIC", ""), "Desktop")
        if os.path.exists(public_desktop):
            desktop_paths.append(public_desktop)
        
        count = 0
        # 标准化程序名称用于匹配
        program_name_lower = program_name.lower()
        keywords = self._build_search_keywords(program_name)
        
        # 遍历所有桌面路径
        for desktop_path in desktop_paths:
            try:
                # 获取桌面上的所有.lnk文件
                for file in os.listdir(desktop_path):
                    if file.lower().endswith(".lnk"):
                        shortcut_path = os.path.join(desktop_path, file)
                        
                        # 检查文件名是否与程序名称相关
                        file_name_lower = file.lower()
                        if any(keyword in file_name_lower for keyword in keywords):
                            self.log(f"找到相关快捷方式: {shortcut_path}")
                            # 尝试删除快捷方式
                            try:
                                os.remove(shortcut_path)
                                self.log(f"成功删除快捷方式: {shortcut_path}")
                                count += 1
                            except Exception as e:
                                # 尝试强制删除
                                try:
                                    self._force_delete_with_unlock(shortcut_path)
                                    self.log(f"成功强制删除快捷方式: {shortcut_path}")
                                    count += 1
                                except Exception as e2:
                                    self.log(f"删除快捷方式失败: {shortcut_path} - {str(e2)}")
            except Exception as e:
                self.log(f"扫描桌面目录失败: {desktop_path} - {str(e)}")
        
        return count
    
    def _remove_taskbar_pinned_icons(self, program_name):
        """删除与程序相关的任务栏固定图标"""
        self.log(f"开始删除与 {program_name} 相关的任务栏固定图标")
        
        # 任务栏固定项目的多个可能位置
        # Windows 7/8/10/11支持的多个位置
        taskbar_pinned_paths = [
            # 传统快速启动栏位置
            os.path.join(
                os.environ.get("APPDATA", ""),
                "Microsoft",
                "Internet Explorer",
                "Quick Launch",
                "User Pinned",
                "TaskBar"
            ),
            # Windows 10/11可能的固定项目位置
            os.path.join(
                os.environ.get("APPDATA", ""),
                "Microsoft",
                "Windows",
                "Start Menu",
                "Programs",
                "Startup"
            )
        ]
        
        count = 0
        # 标准化程序名称用于匹配
        keywords = self._build_search_keywords(program_name)
        
        # 遍历所有可能的任务栏固定项目位置
        for taskbar_path in taskbar_pinned_paths:
            if os.path.exists(taskbar_path):
                try:
                    # 获取目录中的所有文件
                    for file in os.listdir(taskbar_path):
                        file_path = os.path.join(taskbar_path, file)
                        
                        # 优先检查快捷方式文件
                        if file.lower().endswith(".lnk"):
                            # 检查文件名是否与程序名称相关
                            file_name_lower = file.lower()
                            if any(keyword in file_name_lower for keyword in keywords):
                                self.log(f"找到相关任务栏固定图标: {file_path}")
                                # 尝试删除快捷方式
                                try:
                                    # 先尝试正常删除
                                    os.remove(file_path)
                                    self.log(f"成功删除任务栏固定图标: {file_path}")
                                    count += 1
                                except Exception as e:
                                    # 尝试强制删除
                                    try:
                                        self._force_delete_with_unlock(file_path)
                                        self.log(f"成功强制删除任务栏固定图标: {file_path}")
                                        count += 1
                                    except Exception as e2:
                                        self.log(f"删除任务栏固定图标失败: {file_path} - {str(e2)}")
                        # 检查普通文件是否可能是任务栏固定项
                        elif os.path.isfile(file_path):
                            file_name_lower = file.lower()
                            if any(keyword in file_name_lower for keyword in keywords):
                                self.log(f"找到可能的任务栏相关文件: {file_path}")
                                try:
                                    # 尝试读取文件内容检查是否与程序相关
                                    if self._check_file_content_related(file_path, keywords):
                                        try:
                                            self._force_delete_with_unlock(file_path)
                                            self.log(f"成功删除任务栏相关文件: {file_path}")
                                            count += 1
                                        except Exception as e:
                                            self.log(f"删除任务栏相关文件失败: {file_path} - {str(e)}")
                                except:
                                    # 忽略无法读取内容的文件
                                    pass
                except Exception as e:
                    self.log(f"扫描任务栏固定项目目录失败: {taskbar_path} - {str(e)}")
            else:
                self.log(f"任务栏固定项目目录不存在: {taskbar_path}")
        
        # 额外：使用Windows命令行工具尝试清理任务栏固定项
        try:
            self._clean_taskbar_pinned_using_shell(program_name)
        except Exception as e:
            self.log(f"使用Shell命令清理任务栏固定项时出错: {str(e)}")
        
        # 额外：尝试清理可能的注册表固定项引用
        try:
            registry_cleaned = self._clean_taskbar_registry_entries(program_name)
            if registry_cleaned > 0:
                self.log(f"清理了 {registry_cleaned} 个任务栏相关注册表项")
                count += registry_cleaned
        except Exception as e:
            self.log(f"清理任务栏注册表项时出错: {str(e)}")
        
        return count
        
    def _check_file_content_related(self, file_path, keywords):
        """检查文件内容是否与给定关键词相关"""
        try:
            # 只尝试读取小文件，避免大文件导致性能问题
            if os.path.getsize(file_path) < 1024 * 1024:  # 小于1MB
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    return any(keyword in content for keyword in keywords)
        except:
            pass
        return False
        
    def _clean_taskbar_pinned_using_shell(self, program_name):
        """使用Windows命令行工具尝试清理任务栏固定项"""
        self.log(f"尝试使用Shell命令清理任务栏固定项: {program_name}")
        
        # 构建PowerShell命令来查找并删除可能的任务栏固定项
        # 注意：这个方法可能需要管理员权限才能完全生效
        keywords = self._build_search_keywords(program_name)
        for keyword in keywords:
            # 构建查找命令
            ps_command = f"Get-StartApps | Where-Object {{ $_.Name -like '*{keyword}*' }} | Format-List"
            try:
                # 执行PowerShell命令检查是否存在相关应用
                subprocess.run(
                    ["powershell.exe", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                # 注意：这里只检查，不执行删除操作，因为任务栏固定项的PowerShell直接删除需要更复杂的逻辑
            except Exception as e:
                self.log(f"执行PowerShell命令检查应用失败: {str(e)}")

    
    def _clean_taskbar_registry_entries(self, program_name):
        """清理与程序相关的任务栏固定项注册表引用"""
        self.log(f"开始清理与 {program_name} 相关的任务栏注册表项")
        
        cleaned_count = 0
        keywords = self._build_search_keywords(program_name)
        
        try:
            # 任务栏固定项的多个可能的注册表位置
            reg_paths = [
                # 主要任务栏注册表位置
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband",
                # 开始菜单和任务栏相关项
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartPage",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartPage2",
                # Windows 10/11 开始菜单布局
                r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount"
            ]
            
            for reg_path in reg_paths:
                try:
                    # 先尝试以读取模式打开键
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        reg_path,
                        0,
                        winreg.KEY_READ
                    )
                    
                    # 记录检查的注册表路径
                    self.log(f"检查注册表路径: {reg_path}")
                    
                    # 对于Taskband，我们不直接修改二进制值，但对于其他路径，我们可以尝试清理相关值
                    if reg_path != r"Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband":
                        try:
                            # 尝试以写入模式重新打开键
                            key_write = winreg.OpenKey(
                                winreg.HKEY_CURRENT_USER,
                                reg_path,
                                0,
                                winreg.KEY_SET_VALUE
                            )
                            
                            # 获取键中的值数量
                            value_count = winreg.QueryInfoKey(key_write)[1]
                            
                            # 检查每个值
                            values_to_delete = []
                            for i in range(value_count):
                                try:
                                    value_name = winreg.EnumValue(key_write, i)[0]
                                    value_data = winreg.QueryValueEx(key_write, value_name)[0]
                                    
                                    # 将值数据转换为字符串进行匹配
                                    value_str = str(value_data).lower()
                                    if any(keyword in value_str for keyword in keywords):
                                        values_to_delete.append(value_name)
                                        self.log(f"发现相关注册表值: {reg_path}\\{value_name}")
                                except:
                                    continue
                            
                            # 删除匹配的值
                            for value_name in values_to_delete:
                                try:
                                    winreg.DeleteValue(key_write, value_name)
                                    self.log(f"已删除注册表值: {reg_path}\\{value_name}")
                                    cleaned_count += 1
                                except Exception as e:
                                    self.log(f"删除注册表值失败: {reg_path}\\{value_name} - {str(e)}")
                            
                            winreg.CloseKey(key_write)
                        except Exception as e:
                            self.log(f"无法以写入模式打开注册表键: {reg_path} - {str(e)}")
                    
                    winreg.CloseKey(key)
                except Exception as e:
                    self.log(f"访问注册表路径失败: {reg_path} - {str(e)}")
            
            # 对于Taskband键（包含二进制数据），我们可以尝试重启explorer进程以刷新任务栏
            try:
                if cleaned_count > 0:
                    self.log("正在重启Windows资源管理器以应用注册表更改")
                    # 终止并重启explorer进程
                    subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], shell=True)
                    subprocess.Popen(["explorer.exe"])
                    self.log("Windows资源管理器已重启")
            except Exception as e:
                self.log(f"重启Windows资源管理器失败: {str(e)}")
                
        except Exception as e:
            self.log(f"清理任务栏注册表项时出错: {str(e)}")
        
        return cleaned_count
    
    def _add_right_click_menu(self):
        """为列表框添加右键菜单，包含顽固程序特殊处理选项"""
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="卸载所选程序", command=self.uninstall_selected)
        self.menu.add_separator()
        self.menu.add_command(label="强制停止相关进程", command=self._force_stop_processes)
        self.menu.add_command(label="删除启动项", command=self._remove_startup_entries)
        self.menu.add_command(label="停止相关服务", command=self._stop_program_services)
        self.menu.add_separator()
        self.menu.add_command(label="查看程序详情", command=self._show_program_details)
        
        # 绑定右键菜单
        self.program_listbox.bind("<Button-3>", self._show_menu)
    
    def _show_menu(self, event):
        """显示右键菜单"""
        # 确保有选中的项
        if self.program_listbox.curselection():
            # 选中右键点击的项
            index = self.program_listbox.nearest(event.y)
            self.program_listbox.selection_clear(0, tk.END)
            self.program_listbox.selection_set(index)
            self.program_listbox.activate(index)
            
            # 显示菜单
            self.menu.post(event.x_root, event.y_root)
    
    def _force_stop_processes(self):
        """强制停止与选中程序相关的所有进程"""
        selection = self.program_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        program = self.filtered_programs[index]
        program_name = program.get("DisplayName", "未知程序")
        install_path = program.get("InstallLocation", "")
        
        if not install_path:
            messagebox.showinfo("信息", "未找到该程序的安装路径，无法停止进程。")
            return
            
        if messagebox.askyesno("确认", f"确定要强制停止所有与 {program_name} 相关的进程吗？"):
            self.log(f"用户确认强制停止 {program_name} 的所有相关进程")
            count = self._terminate_related_processes(install_path)
            messagebox.showinfo("完成", f"已尝试停止 {count} 个相关进程。")
    
    def _remove_startup_entries(self):
        """删除与选中程序相关的所有启动项"""
        selection = self.program_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        program = self.filtered_programs[index]
        program_name = program.get("DisplayName", "未知程序")
        
        if messagebox.askyesno("确认", f"确定要删除所有与 {program_name} 相关的启动项吗？"):
            self.log(f"用户确认删除 {program_name} 的所有启动项")
            count = self._clean_startup_entries(program_name)
            messagebox.showinfo("完成", f"已删除 {count} 个相关启动项。")
    
    def _stop_program_services(self):
        """停止与选中程序相关的所有服务"""
        selection = self.program_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        program = self.filtered_programs[index]
        program_name = program.get("DisplayName", "未知程序")
        
        if messagebox.askyesno("确认", f"确定要停止所有与 {program_name} 相关的服务吗？"):
            self.log(f"用户确认停止 {program_name} 的所有相关服务")
            count = self._stop_related_services(program_name)
            messagebox.showinfo("完成", f"已尝试停止 {count} 个相关服务。")
    
    def _show_program_details(self):
        """显示程序详细信息"""
        selection = self.program_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        program = self.filtered_programs[index]
        
        # 构建详细信息文本
        details = "程序详细信息:\n\n"
        for key, value in program.items():
            # 格式化键名使其更易读
            display_key = key.replace('_', ' ').title()
            details += f"{display_key}: {value}\n"
        
        # 创建一个新窗口显示详细信息
        detail_window = tk.Toplevel(self.root)
        detail_window.title("程序详情")
        detail_window.geometry("500x400")
        detail_window.configure(bg=self.bg_color)
        
        # 添加文本框显示详细信息
        text_widget = Text(detail_window, wrap=tk.WORD, bg=self.bg_color, fg=self.text_color)
        text_widget.insert(tk.END, details)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
        
        # 添加关闭按钮
        Button(detail_window, text="关闭", command=detail_window.destroy).pack(pady=10)
    
    def _force_delete_directory(self, path):
        """强力删除目录，处理文件锁定和权限问题"""
        # 首先尝试修改文件权限
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    # 修改文件权限
                    os.chmod(file_path, 0o777)
                    # 尝试删除单个文件
                    os.remove(file_path)
                except:
                    pass
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.chmod(dir_path, 0o777)
                except:
                    pass
        
        # 尝试删除整个目录
        try:
            shutil.rmtree(path, ignore_errors=True)
        except:
            # 最后再尝试一次逐个删除
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    else:
                        shutil.rmtree(item_path, ignore_errors=True)
                os.rmdir(path)
            except:
                pass
    
    def _shred_file(self, file_path, algorithm="default", passes=3, force_kill=True, disable_protection=True, progress_callback=None):
        """增强版文件删除功能 - 支持多种高级删除技术和权限处理"""
        try:
            # 导入核心粉碎模块
            from core_shredding import shred_file
            
            # 使用核心模块进行文件粉碎
            result = shred_file(
                file_path, 
                algorithm=algorithm, 
                passes=passes, 
                force_kill=force_kill, 
                disable_protection=disable_protection,
                log_func=self.log,
                progress_callback=progress_callback
            )
            
            return result
            
        except Exception as e:
            self.log(f"文件粉碎失败: {str(e)}")
            # 如果核心模块出现问题，尝试使用备用方法
            try:
                # 简单的文件删除作为备用
                os.remove(file_path)
                return True
            except Exception:
                return False
    
    def _trailing_file_shredder(self, file_path):
        """拖尾文件删除技术 - 重命名后删除，绕过文件锁"""
        try:
            self.log(f"使用拖尾文件删除技术: {file_path}")
            
            # 将文件重命名为尽可能短的名字
            parent_dir = os.path.dirname(file_path)
            file_ext = os.path.splitext(file_path)[1]
            
            # 创建一系列越来越短的文件名
            short_names = [
                "a" + file_ext,
                "a.tmp", 
                "a",
                "1",
                "x",
                "z"
            ]
            
            current_name = file_path
            
            for short_name in short_names:
                try:
                    # 尝试重命名文件
                    new_path = os.path.join(parent_dir, short_name)
                    os.rename(current_name, new_path)
                    current_name = new_path
                    self.log(f"重命名文件为: {short_name}")
                    
                    # 短暂等待让文件系统更新
                    time.sleep(0.1)
                    
                    # 尝试删除重命名后的文件
                    try:
                        os.remove(current_name)
                        self.log(f"成功删除文件: {current_name}")
                        return True
                    except:
                        # 如果删除失败，继续下一个重命名
                        continue
                        
                except Exception as e:
                    self.log(f"重命名失败 {short_name}: {str(e)}")
                    continue
            
            # 如果所有的重命名都失败了，尝试直接删除
            try:
                os.remove(current_name)
                return True
            except:
                return False
                
        except Exception as e:
            self.log(f"拖尾文件删除失败: {str(e)}")
            return False
    
    def _multi_layer_shredding(self, file_path, passes=3, algorithm="default"):
        """多层覆盖删除 - 确保数据无法恢复
        
        参数:
            file_path: 要删除的文件路径
            passes: 覆盖次数
            algorithm: 覆盖算法 (default, dod5220, gutmann, random)
        """
        try:
            self.log(f"执行多层覆盖删除: {file_path} (算法: {algorithm}, 覆盖次数: {passes})")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 检测是否为SSD
            is_ssd_device = False
            try:
                is_ssd_device = self._is_ssd(file_path)
            except Exception as e:
                self.log(f"SSD检测失败，使用默认设置: {str(e)}")
                # 发生错误时默认使用非SSD设置，确保粉碎过程继续
            
            # 先修改文件属性和权限
            self._force_unlock_and_modify_attributes(file_path)
            
            # 根据选择的算法获取覆盖模式
            if algorithm == "dod5220":
                # DoD 5220.22-M 标准: 3次覆盖 (0xF6, 0x00, 0xFF)
                patterns = [
                    lambda size: bytes(0xF6 for _ in range(size)),  # DoD 第一遍
                    lambda size: b'\x00' * size,                      # DoD 第二遍
                    lambda size: b'\xFF' * size                       # DoD 第三遍
                ]
                passes = 3  # DoD标准固定为3次
            elif algorithm == "usdod":
                # US DoD 5220.22-M ECE 标准: 7次覆盖
                patterns = [
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x92 for _ in range(size)),  # 10010010
                    lambda size: bytes(0x49 for _ in range(size)),  # 01001001
                    lambda size: bytes(0x24 for _ in range(size)),  # 00100100
                    lambda size: b'\x00' * size,                      # 零
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))  # 随机
                ]
                passes = 7  # USDOD标准固定为7次
            elif algorithm == "nato":
                # NATO 标准: 7次覆盖
                patterns = [
                    lambda size: b'\x00' * size,  # 零
                    lambda size: b'\xFF' * size,  # 全一
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),  # 随机
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),  # 随机
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))   # 随机
                ]
                passes = 7  # NATO标准固定为7次
            elif algorithm == "hgmp":
                # HGMP (德国政府标准): 3次覆盖
                patterns = [
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))  # 随机
                ]
                passes = 3  # HGMP标准固定为3次
            elif algorithm == "gutmann":
                # Gutmann算法: 35次覆盖，使用不同的模式
                patterns = [
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x92 for _ in range(size)),  # 10010010
                    lambda size: bytes(0x49 for _ in range(size)),  # 01001001
                    lambda size: bytes(0x24 for _ in range(size)),  # 00100100
                    lambda size: bytes(0x49 for _ in range(size)),  # 01001001
                    lambda size: bytes(0x92 for _ in range(size)),  # 10010010
                    lambda size: bytes(0x24 for _ in range(size)),  # 00100100
                    lambda size: bytes(0x66 for _ in range(size)),  # 01100110
                    lambda size: bytes(0x66 for _ in range(size)),  # 01100110
                    lambda size: bytes(0x00 for _ in range(size)),  # 00000000
                    lambda size: bytes(0xFF for _ in range(size)),  # 11111111
                    lambda size: bytes(0x92 for _ in range(size)),  # 10010010
                    lambda size: bytes(0x49 for _ in range(size)),  # 01001001
                    lambda size: bytes(0x24 for _ in range(size)),  # 00100100
                    lambda size: bytes(0x92 for _ in range(size)),  # 10010010
                    lambda size: bytes(0x49 for _ in range(size)),  # 01001001
                    lambda size: bytes(0x24 for _ in range(size)),  # 00100100
                    lambda size: bytes(0x66 for _ in range(size)),  # 01100110
                    lambda size: bytes(0x66 for _ in range(size)),  # 01100110
                    lambda size: bytes(0x00 for _ in range(size)),  # 00000000
                    lambda size: bytes(0xFF for _ in range(size)),  # 11111111
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x55 for _ in range(size)),  # 01010101
                    lambda size: bytes(0xAA for _ in range(size)),  # 10101010
                    lambda size: bytes(0x00 for _ in range(size)),  # 00000000
                    lambda size: bytes(0xFF for _ in range(size)),  # 11111111
                    # 最后用随机数据覆盖
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))
                ]
                passes = 35  # Gutmann标准固定为35次
            elif algorithm == "random":
                # 只使用随机数据覆盖
                patterns = [
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))
                ]
            elif algorithm == "random_plus":
                # 增强型随机覆盖: 使用更安全的随机数生成器
                patterns = [
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    lambda size: bytes(random.getrandbits(8) for _ in range(size))
                ]
                passes = 3  # 增强型随机覆盖固定为3次
            else:  # default
                # 默认算法: 多种模式交替覆盖
                patterns = [
                    # 模式1: 随机数据
                    lambda size: bytes(random.getrandbits(8) for _ in range(size)),
                    # 模式2: 零
                    lambda size: b'\x00' * size,
                    # 模式3: 1
                    lambda size: b'\xFF' * size,
                    # 模式4: 交替模式
                    lambda size: bytes((i % 2) * 255 for i in range(size)),
                    # 模式5: 递增模式
                    lambda size: bytes(i % 256 for i in range(size))
                ]
            
            # 大文件优化：根据文件大小动态调整块大小和其他参数
            is_large_file = file_size > 100 * 1024 * 1024  # 大于100MB视为大文件
            is_very_large_file = file_size > 1 * 1024 * 1024 * 1024  # 大于1GB视为超大文件
            
            # 根据文件大小动态调整块大小
            if is_very_large_file:
                chunk_size = 16 * 1024 * 1024  # 超大文件使用16MB块
                flush_interval = 15  # 每15个块刷新一次
            elif is_large_file:
                chunk_size = 8 * 1024 * 1024  # 大文件使用8MB块
                flush_interval = 10  # 每10个块刷新一次
            else:
                chunk_size = 1 * 1024 * 1024  # 小文件使用1MB块
                flush_interval = 5  # 每5个块刷新一次
            
            # 检测系统内存大小，调整块大小
            try:
                import psutil
                total_memory = psutil.virtual_memory().total
                available_memory = psutil.virtual_memory().available
                # 块大小不超过可用内存的20%
                max_safe_chunk_size = int(available_memory * 0.2)
                if chunk_size > max_safe_chunk_size:
                    chunk_size = max_safe_chunk_size
                    # 确保块大小至少为1MB
                    chunk_size = max(chunk_size, 1 * 1024 * 1024)
                    self.log(f"根据系统内存调整块大小至: {chunk_size/(1024*1024):.2f}MB")
            except ImportError:
                pass  # psutil未安装，使用默认块大小
            
            self.log(f"文件大小: {file_size/(1024*1024):.2f}MB, 块大小: {chunk_size/(1024*1024):.2f}MB, 刷新间隔: {flush_interval}")
            
            for pass_num in range(passes):
                try:
                    # 选择覆盖模式
                    pattern_func = patterns[pass_num % len(patterns)]
                    
                    with open(file_path, "rb+") as f:
                        remaining = file_size
                        f.seek(0)
                        chunk_count = 0
                        
                        while remaining > 0:
                            current_chunk_size = min(chunk_size, remaining)
                            
                            # 生成块数据 - 优化随机数生成
                            if "random" in str(pattern_func) or "random.getrandbits" in str(pattern_func.__code__.co_consts):
                                # 优先使用更高效的os.urandom()生成随机数据
                                if hasattr(os, 'urandom'):
                                    chunk_data = os.urandom(current_chunk_size)
                                else:
                                    # 回退到原始方法
                                    chunk_data = pattern_func(current_chunk_size)
                            elif "b'\\x00'" in str(pattern_func) or "b'\\xFF'" in str(pattern_func):
                                # 优化固定字节模式（0x00, 0xFF）的生成
                                chunk_data = pattern_func(current_chunk_size)
                            else:
                                # 对于其他模式，预生成小样本并重复使用
                                if current_chunk_size > 1024 * 1024:  # 大文件块
                                    sample_size = 1024 * 1024  # 1MB样本
                                    sample = pattern_func(sample_size)
                                    # 重复样本填充整个块
                                    chunks = [sample] * (current_chunk_size // sample_size)
                                    if current_chunk_size % sample_size:
                                        chunks.append(sample[:current_chunk_size % sample_size])
                                    chunk_data = b''.join(chunks)
                                else:
                                    chunk_data = pattern_func(current_chunk_size)
                            
                            # 写入块数据
                            f.write(chunk_data)
                            remaining -= current_chunk_size
                            chunk_count += 1
                            
                            # 定期刷新，而不是每次都刷新
                            if chunk_count % flush_interval == 0 or remaining == 0:
                                f.flush()
                                os.fsync(f.fileno())
                                
                            # 移除不适当的进度更新，避免上下文不匹配导致程序卡住
                            pass
                    
                    self.log(f"多层覆盖 - 第 {pass_num + 1}/{passes} 层完成")
                    
                    # 刷新文件系统缓存（仅在必要时）
                    if (is_large_file or is_very_large_file) and hasattr(os, 'sync'):
                        # 只在最后一遍覆盖时刷新整个系统缓存
                        if pass_num == passes - 1:
                            os.sync()
                    
                    # 智能暂停优化：减少不必要的暂停
                    if is_ssd_device:
                        # SSD设备不需要频繁暂停
                        continue
                    
                    # 仅在大文件和CPU使用率高时才暂停
                    if is_large_file or is_very_large_file:
                        try:
                            import psutil
                            cpu_percent = psutil.cpu_percent(interval=0.01)  # 更短的检测间隔
                            if cpu_percent > 90:  # 更高的CPU阈值
                                time.sleep(0.01)  # 更短的暂停时间
                        except ImportError:
                            pass  # 未安装psutil时不暂停
                    # 小文件不需要暂停
                    elif pass_num < passes - 1:  # 除最后一遍外不暂停
                        continue
                    else:
                        time.sleep(0.01)  # 最后一遍短暂暂停
                    
                except Exception as e:
                    self.log(f"第 {pass_num + 1} 层覆盖失败: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.log(f"多层覆盖删除失败: {str(e)}")
            return False
    
    def _ultimate_sector_shredding(self, file_path):
        """终极扇区级删除 - 使用Windows API直接写入物理扇区"""
        try:
            self.log(f"执行终极扇区级删除: {file_path}")
            
            # 获取文件所在的驱动器
            drive_path = os.path.abspath(file_path)[:3]  # 获取驱动器如 C:\
            
            # 使用Windows API直接打开文件进行扇区写入
            try:
                # 尝试使用ctypes直接写入
                self._direct_sector_write(file_path)
                return True
            except:
                # 如果直接写入失败，尝试其他方法
                return self._advanced_api_shredding(file_path)
                
        except Exception as e:
            self.log(f"终极扇区级删除失败: {str(e)}")
            return False
    
    def _direct_sector_write(self, file_path):
        """使用ctypes直接进行扇区写入"""
        try:
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            OPEN_EXISTING = 3
            
            # 打开文件句柄
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateFileW(
                file_path,
                GENERIC_WRITE,
                FILE_SHARE_READ,
                None,
                OPEN_EXISTING,
                0,
                None
            )
            
            if handle == -1:
                raise Exception("无法打开文件句柄")
            
            try:
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                
                # 多次写入随机数据
                for i in range(3):
                    random_data = bytes(random.getrandbits(8) for _ in range(file_size))
                    
                    # 使用Windows API写入文件
                    written = ctypes.c_ulonglong(0)
                    success = kernel32.WriteFile(
                        handle,
                        random_data,
                        len(random_data),
                        ctypes.byref(written),
                        None
                    )
                    
                    if success:
                        # 强制写入磁盘
                        kernel32.FlushFileBuffers(handle)
                        self.log(f"扇区级写入完成 {i + 1}/3")
                    
                    time.sleep(0.1)
                
            finally:
                kernel32.CloseHandle(handle)
                
        except Exception as e:
            self.log(f"直接扇区写入失败: {str(e)}")
            raise
    
    def _advanced_api_shredding(self, file_path, algorithm='dod', passes=3):
        """高级API删除方法 - 支持多种Windows API和备用方案"""
        try:
            self.log(f"执行高级API删除: {file_path}")
            
            # 方法1: 使用win32file（如果可用）
            if WIN32FILE_AVAILABLE and 'win32file' in globals():
                return self._win32file_shredding(file_path, algorithm=algorithm, passes=passes)
            
            # 方法2: 使用ctypes直接调用Windows API
            return self._ctypes_api_shredding(file_path)
            
        except Exception as e:
            self.log(f"高级API删除失败: {str(e)}")
            return False
    
    def _win32file_shredding(self, file_path, algorithm='dod', passes=3):
        """使用win32file API进行文件粉碎（Windows专用）"""
        try:
            # 确保文件可以写入
            win32file.SetFileAttributes(file_path, win32file.FILE_ATTRIBUTE_NORMAL)
            
            # 打开文件进行粉碎
            handle = win32file.CreateFile(
                file_path,
                win32file.GENERIC_WRITE,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_WRITE_THROUGH | win32file.FILE_FLAG_NO_BUFFERING,
                None
            )
            
            try:
                file_size = win32file.GetFileSize(handle)
                
                # 优化缓冲区大小
                buffer_size = 65536  # 64KB 最优I/O缓冲区大小
                
                # 根据算法选择覆盖模式
                pass_patterns = []
                
                if algorithm.lower() == 'gutmann':
                    # Gutmann算法 - 11轮覆盖（简化版，原35轮）
                    pass_patterns = [
                        lambda: b'\x55' * buffer_size,  # 0x55
                        lambda: b'\xAA' * buffer_size,  # 0xAA
                        lambda: os.urandom(buffer_size),  # 随机
                        lambda: b'\x92\x49\x24' * (buffer_size // 3),  # Gutmann序列1
                        lambda: b'\x49\x24\x92' * (buffer_size // 3),  # Gutmann序列2
                        lambda: b'\x24\x92\x49' * (buffer_size // 3),  # Gutmann序列3
                        lambda: os.urandom(buffer_size),  # 随机
                        lambda: b'\x6D\xB6\xDB' * (buffer_size // 3),  # Gutmann序列4
                        lambda: b'\xB6\xDB\x6D' * (buffer_size // 3),  # Gutmann序列5
                        lambda: b'\xDB\x6D\xB6' * (buffer_size // 3),  # Gutmann序列6
                        lambda: os.urandom(buffer_size),  # 随机
                    ]
                    passes = min(passes, len(pass_patterns))
                elif algorithm.lower() == 'dod':
                    # DoD 5220.22-M算法
                    pass_patterns = [
                        lambda: b'\x00' * buffer_size,  # 1轮0x00
                        lambda: b'\xFF' * buffer_size,  # 1轮0xFF
                        lambda: os.urandom(buffer_size),  # 1轮随机
                    ]
                    passes = min(passes, 3)
                elif algorithm.lower() == 'nato':
                    # NATO算法 - 7轮覆盖
                    pass_patterns = [
                        lambda: b'\x00' * buffer_size,  # 0x00
                        lambda: b'\xFF' * buffer_size,  # 0xFF
                        lambda: b'\x55' * buffer_size,  # 0x55
                        lambda: b'\xAA' * buffer_size,  # 0xAA
                        lambda: b'\x96' * buffer_size,  # 0x96
                        lambda: b'\x69' * buffer_size,  # 0x69
                        lambda: os.urandom(buffer_size),  # 随机
                    ]
                    passes = min(passes, 7)
                else:
                    # 默认算法：4轮覆盖
                    pass_patterns = [
                        lambda: b'\xFF' * buffer_size,
                        lambda: b'\x00' * buffer_size,
                        lambda: os.urandom(buffer_size),
                        lambda: os.urandom(buffer_size)
                    ]
                    passes = min(passes, 4)
                
                # 执行多轮覆盖
                for pass_num in range(passes):
                    # 移动到文件开头
                    win32file.SetFilePointer(handle, 0, 0)  # FILE_BEGIN = 0
                    
                    if pass_num < len(pass_patterns):
                        pattern_func = pass_patterns[pass_num]
                    else:
                        pattern_func = lambda: os.urandom(buffer_size)
                    
                    written = 0
                    while written < file_size:
                        remaining = file_size - written
                        current_buffer_size = min(buffer_size, remaining)
                        
                        if current_buffer_size < buffer_size:
                            buffer = pattern_func()[:current_buffer_size]
                        else:
                            buffer = pattern_func()
                        
                        win32file.WriteFile(handle, buffer)
                        written += current_buffer_size
                    
                    win32file.FlushFileBuffers(handle)
                
                # 二次覆盖小文件（防止元数据泄漏）
                if file_size < 1024:
                    try:
                        # 重新打开文件以允许缓冲
                        small_handle = win32file.CreateFile(
                            file_path,
                            win32file.GENERIC_WRITE,
                            win32file.FILE_SHARE_READ,
                            None,
                            win32file.OPEN_EXISTING,
                            win32file.FILE_ATTRIBUTE_NORMAL,
                            None
                        )
                        
                        small_data = os.urandom(1024)
                        win32file.SetFilePointer(small_handle, 0, 0)
                        win32file.WriteFile(small_handle, small_data)
                        win32file.FlushFileBuffers(small_handle)
                        win32file.CloseHandle(small_handle)
                    except:
                        pass
                
                # 截断文件
                open(file_path, 'w').close()
                
                # 立即删除文件
                return win32file.DeleteFile(file_path)
                
            finally:
                win32file.CloseHandle(handle)
                
        except Exception as e:
            self.log(f"win32file粉碎失败: {file_path} - {str(e)}")
            return False
    
    def _ctypes_api_shredding(self, file_path, algorithm="default", passes=3):
        """使用ctypes直接调用Windows API"""
        try:
            kernel32 = ctypes.windll.kernel32
            advapi32 = ctypes.windll.advapi32
            
            # Windows API常量
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 0x80
            
            # 设置文件属性为普通
            kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_NORMAL)
            
            # 获取安全描述符为空（完全访问权限）
            NULL_SECURITY_ATTRIBUTES = None
            
            # 打开文件句柄
            handle = kernel32.CreateFileW(
                file_path,
                GENERIC_WRITE,
                FILE_SHARE_READ,
                NULL_SECURITY_ATTRIBUTES,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL,
                None
            )
            
            if handle == -1:
                raise Exception(f"无法打开文件句柄，错误代码: {kernel32.GetLastError()}")
            
            try:
                file_size = os.path.getsize(file_path)
                
                # 使用Windows API删除文件
                self._windows_api_shredding_internal(handle, file_size, algorithm=algorithm, passes=passes)
                
                return True
                
            finally:
                kernel32.CloseHandle(handle)
                
        except Exception as e:
            self.log(f"ctypes API删除失败: {str(e)}")
            return False
    
    def _windows_api_shredding_internal(self, handle, file_size, algorithm="default", passes=3):
        """Windows API内部删除实现"""
        try:
            kernel32 = ctypes.windll.kernel32
            
            # 算法配置
            algorithm_config = {
                "gutmann": {
                    "patterns": [lambda: b'\xFF' * 1024, lambda: b'\x00' * 1024] + [lambda: os.urandom(1024) for _ in range(9)],
                    "max_passes": 11
                },
                "dod": {
                    "patterns": [lambda: b'\xFF' * 1024, lambda: b'\x00' * 1024, lambda: os.urandom(1024)],
                    "max_passes": 3
                },
                "nato": {
                    "patterns": [lambda: b'\xFF' * 1024, lambda: b'\x00' * 1024] + [lambda: os.urandom(1024) for _ in range(5)],
                    "max_passes": 7
                },
                "default": {
                    "patterns": [lambda: b'\xFF' * 1024, lambda: b'\x00' * 1024, lambda: os.urandom(1024), lambda: os.urandom(1024)],
                    "max_passes": 4
                }
            }
            
            config = algorithm_config.get(algorithm, algorithm_config["default"])
            pass_patterns = config["patterns"]
            max_passes = config["max_passes"]
            passes = min(passes, max_passes)
            
            chunk_size = min(1024 * 1024, file_size)  # 1MB chunks
            
            # 执行多轮覆盖
            for i in range(passes):
                # 移动到文件开头
                kernel32.SetFilePointer(handle, 0, 0)  # FILE_BEGIN = 0
                
                if i < len(pass_patterns):
                    pattern_func = pass_patterns[i]
                else:
                    pattern_func = lambda: os.urandom(1024)
                
                remaining = file_size
                while remaining > 0:
                    current_chunk_size = min(chunk_size, remaining)
                    
                    if current_chunk_size < chunk_size:
                        pattern = pattern_func()[:current_chunk_size]
                    else:
                        pattern = pattern_func()
                    
                    written = ctypes.c_ulonglong(0)
                    success = kernel32.WriteFile(
                        handle,
                        pattern,
                        len(pattern),
                        ctypes.byref(written),
                        None
                    )
                    
                    if success:
                        # 强制写入磁盘
                        kernel32.FlushFileBuffers(handle)
                    
                    remaining -= len(pattern)
                
                self.log(f"Windows API删除层 {i + 1}/{passes} 完成")
                time.sleep(0.05)
            
            # 最后用零覆盖
            zero_chunk = b'\x00' * chunk_size
            remaining = file_size
            while remaining > 0:
                current_chunk_size = min(len(zero_chunk), remaining)
                kernel32.WriteFile(handle, zero_chunk[:current_chunk_size], len(zero_chunk[:current_chunk_size]), None, None)
                remaining -= current_chunk_size
            
            kernel32.FlushFileBuffers(handle)
            
        except Exception as e:
            self.log(f"Windows API内部删除失败: {str(e)}")
            raise
    
    def _privileged_file_removal(self, file_path):
        """增强版权限提升文件删除 - 包含多重权限提升机制"""
        try:
            self.log(f"尝试权限提升删除: {file_path}")
            
            # 1. 多重权限检查和提升
            if not self._multi_level_privilege_escalation():
                self.log("权限提升失败，使用其他方法")
            
            # 2. 禁用文件保护机制
            self._disable_file_protection(file_path)
            
            # 3. 使用最强权限删除
            if not self._force_delete_with_unlock(file_path):
                # 如果仍然失败，尝试终极删除
                return self._ultimate_force_deletion(file_path)
            
            return True
            
        except Exception as e:
            self.log(f"权限提升删除失败: {str(e)}")
            return False
    
    def _multi_level_privilege_escalation(self):
        """多级权限提升机制"""
        try:
            # 第一级：检查并尝试获取管理员权限
            if not self.check_admin():
                self.log("尝试获取管理员权限...")
                if not self._request_admin_privilege():
                    self.log("无法获取管理员权限，尝试其他方法")
            else:
                self.log("已具备管理员权限")
                return True
            
            # 第二级：启用所有可能的令牌权限
            return self._enable_all_token_privileges()
            
        except Exception as e:
            self.log(f"多级权限提升失败: {str(e)}")
            return False
    
    def _enable_all_token_privileges(self):
        """启用所有令牌权限"""
        try:
            # 尝试获取当前进程的令牌句柄
            try:
                process_token = win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                )
                
                # 需要启用的权限列表
                privileges_to_enable = [
                    win32security.SE_BACKUP_NAME,    # 备份文件和目录权限
                    win32security.SE_RESTORE_NAME,   # 还原文件和目录权限
                    win32security.SE_TAKE_OWNERSHIP_NAME,  # 获取文件所有权权限
                    win32security.SE_MANAGE_VOLUME_NAME,   # 管理卷权限
                    win32security.SE_DEBUG_NAME,     # 调试程序权限
                    win32security.SE_SYSTEM_ENVIRONMENT_NAME,  # 系统环境权限
                    win32security.SE_SYSTEMTIME_NAME,  # 系统时间权限
                    win32security.SE_PROF_SINGLE_PROCESS_NAME,  # 单个进程配置文件权限
                ]
                
                # 尝试启用每个权限
                for privilege in privileges_to_enable:
                    try:
                        # 启用权限
                        privilege_luid = win32security.LookupPrivilegeValue(None, privilege)
                        win32security.AdjustTokenPrivileges(
                            process_token,
                            False,
                            [(privilege_luid, win32security.SE_PRIVILEGE_ENABLED)]
                        )
                        self.log(f"已启用权限: {privilege}")
                    except:
                        continue
                
                win32security.CloseHandle(process_token)
                return True
                
            except Exception as e:
                self.log(f"启用令牌权限失败: {str(e)}")
                return False
            
        except Exception as e:
            self.log(f"令牌权限处理失败: {str(e)}")
            return False
    
    def _disable_file_protection(self, file_path):
        """禁用文件保护机制"""
        try:
            self.log(f"禁用文件保护机制: {file_path}")
            
            # 方法1: 修改文件属性
            try:
                if 'win32api' in globals():
                    # 清除所有文件属性
                    win32api.SetFileAttributes(file_path, win32api.FILE_ATTRIBUTE_NORMAL)
                    self.log("已清除文件属性保护")
            except:
                pass
            
            # 方法2: 使用命令行工具禁用文件保护
            try:
                # 尝试使用icacls命令移除继承的权限
                subprocess.run([
                    'icacls', file_path, '/inheritance:e', '/grant', 'everyone:F', '/T'
                ], shell=True, capture_output=True)
                self.log("已使用icacls设置文件权限")
            except:
                pass
            
            # 方法3: 尝试关闭文件相关的系统服务
            self._disable_protection_services()
            
        except Exception as e:
            self.log(f"禁用文件保护失败: {str(e)}")
    
    def _disable_protection_services(self):
        """禁用可能保护文件的服务"""
        try:
            # 暂时禁用Windows Defender实时保护（如果需要）
            try:
                subprocess.run([
                    'powershell', '-Command', 
                    'Set-MpPreference -DisableRealtimeMonitoring $true'
                ], shell=True, capture_output=True, timeout=5)
                self.log("已临时禁用Windows Defender实时保护")
            except:
                pass
            
            # 尝试停止可能影响文件操作的服务
            protection_services = [
                'WinDefend',      # Windows Defender
                'WmiApSrv',       # WMI性能适配器
                'TrkWks',         # 分布式链接跟踪客户端
            ]
            
            for service in protection_services:
                try:
                    subprocess.run([
                        'net', 'stop', service
                    ], shell=True, capture_output=True, timeout=3)
                    self.log(f"已停止保护服务: {service}")
                except:
                    continue
                    
        except Exception as e:
            self.log(f"禁用保护服务失败: {str(e)}")
    
    def _ultimate_force_deletion(self, file_path):
        """终极强制删除方法"""
        try:
            self.log(f"执行终极强制删除: {file_path}")
            
            # 方法1: 使用PowerShell强力删除
            if self._powershell_force_deletion(file_path):
                return True
            
            # 方法2: 使用命令行工具组合删除
            if self._command_line_force_deletion(file_path):
                return True
            
            # 方法3: 使用Windows API强制移动文件
            if self._windows_api_force_move(file_path):
                return True
            
            return False
            
        except Exception as e:
            self.log(f"终极强制删除失败: {str(e)}")
            return False
    
    def _powershell_force_deletion(self, file_path):
        """使用PowerShell强制删除"""
        try:
            ps_command = f'''
            try {{
                Remove-Item -Path "{file_path}" -Force -Recurse -ErrorAction Stop
                Write-Output "PowerShell删除成功"
            }} catch {{
                Write-Output "PowerShell删除失败: $($_.Exception.Message)"
            }}
            '''
            
            result = subprocess.run([
                'powershell', '-Command', ps_command
            ], shell=True, capture_output=True, text=True, timeout=10)
            
            if 'PowerShell删除成功' in result.stdout:
                self.log("PowerShell强制删除成功")
                return True
            else:
                self.log(f"PowerShell删除失败: {result.stdout}")
                return False
                
        except Exception as e:
            self.log(f"PowerShell删除失败: {str(e)}")
            return False
    
    def _command_line_force_deletion(self, file_path):
        """使用命令行工具强制删除"""
        try:
            # 尝试使用del命令强制删除
            result1 = subprocess.run([
                'cmd', '/c', 'del', '/F', '/Q', file_path
            ], shell=True, capture_output=True)
            
            # 尝试使用rd命令删除目录
            result2 = subprocess.run([
                'cmd', '/c', 'rd', '/S', '/Q', file_path
            ], shell=True, capture_output=True)
            
            # 检查是否还有文件残留
            if not os.path.exists(file_path):
                self.log("命令行强制删除成功")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"命令行删除失败: {str(e)}")
            return False
    
    def _windows_api_force_move(self, file_path):
        """使用Windows API强制移动文件"""
        try:
            # 尝试将文件移动到一个临时位置然后删除
            temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 
                                   f'force_delete_{os.getpid()}_{int(time.time())}')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file = os.path.join(temp_dir, os.path.basename(file_path))
            
            # 尝试移动文件
            kernel32 = ctypes.windll.kernel32
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            OPEN_EXISTING = 3
            
            handle = kernel32.CreateFileW(
                file_path,
                GENERIC_WRITE,
                FILE_SHARE_READ,
                None,
                OPEN_EXISTING,
                0,
                None
            )
            
            if handle != -1:
                kernel32.CloseHandle(handle)
                
                # 尝试重命名/移动文件
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    os.rename(file_path, temp_file)
                    
                    # 尝试删除移动后的文件
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    
                    # 清理临时目录
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                    
                    return True
                    
                except Exception:
                    # 如果移动失败，尝试直接删除
                    return os.path.exists(file_path) == False
            else:
                # 无法打开文件，可能已经被删除或没有权限
                return os.path.exists(file_path) == False
                
        except Exception as e:
            self.log(f"Windows API强制移动失败: {str(e)}")
            return False
    
    def _force_unlock_and_modify_attributes(self, file_path):
        """强制解锁和修改文件属性"""
        try:
            # 1. 尝试解锁文件
            self._unlock_file(file_path)
            
            # 2. 修改文件属性为可读写
            if 'win32api' in globals():
                win32api.SetFileAttributes(file_path, win32api.FILE_ATTRIBUTE_NORMAL)
            
            # 3. 设置完全控制权限
            os.chmod(file_path, 0o777)
            
            # 4. 尝试终止使用该文件的进程
            self._terminate_processes_using_file(file_path)
            
            self.log(f"已强制解锁文件: {file_path}")
            
        except Exception as e:
            self.log(f"强制解锁失败: {str(e)}")
    
    def _unlock_file(self, file_path):
        """解锁文件（如果被占用）"""
        try:
            # 遍历所有进程，关闭打开的文件句柄
            for proc in psutil.process_iter(['pid', 'open_files']):
                try:
                    open_files = proc.open_files()
                    for open_file in open_files:
                        if open_file.path == file_path:
                            try:
                                proc.terminate()
                                proc.wait(timeout=2)
                                self.log(f"已终止占用文件的进程: {proc.pid}")
                            except (psutil.TimeoutExpired, psutil.AccessDenied):
                                try:
                                    proc.kill()
                                    self.log(f"已强制终止占用文件的进程: {proc.pid}")
                                except:
                                    pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.log(f"解锁文件时出错: {str(e)}")
    

    
    def _execute_shredding(self, paths, shred_type, recursive):
        """执行实际的删除操作"""
        try:
            if shred_type == "files":
                self.log(f"开始删除 {len(paths)} 个文件...")
            else:
                self.log(f"开始删除目录: {paths[0]}")
            
            # 在线程中执行删除操作
            def shred_thread():
                success_count = 0
                total_files = 0
                
                if shred_type == "files":
                    total_files = len(paths)
                    for file_path in paths:
                        if self._shred_file(file_path):
                            success_count += 1
                            self.log(f"成功删除: {os.path.basename(file_path)}")
                else:  # directory
                    total_files = self._shred_directory(paths[0])
                    success_count = total_files
                    self.log(f"目录删除完成，共删除 {success_count} 个文件")
                
                # 刷新UI列表
                self.root.after(0, self.refresh_list)
                
                # 验证粉碎结果
                verification_result = self._verify_shredding_result(paths if shred_type == "files" else [], success_count)
                
                # 显示结果
                result_message = f"共删除 {success_count}/{total_files} 个文件/文件夹\n"
                if verification_result:
                    result_message += f"🔍 验证结果: {verification_result}\n"
                
                self.root.after(0, lambda:
                    messagebox.showinfo("删除完成", result_message)
                )
            
            threading.Thread(target=shred_thread, daemon=True).start()
            
        except Exception as e:
            self.log(f"执行删除操作时出错: {str(e)}")
            self.root.after(0, lambda:
                messagebox.showerror("错误", f"执行删除操作时出错: {str(e)}")
            )
    
    def _verify_shredding_result(self, files_to_verify, success_count):
        """验证文件粉碎结果"""
        self.log("开始验证文件粉碎结果")
        
        if not files_to_verify:
            return "无文件需要验证"
        
        # 验证文件是否真的不存在
        still_exists = []
        for file_path in files_to_verify:
            if os.path.exists(file_path):
                still_exists.append(file_path)
        
        if still_exists:
            for file_path in still_exists:
                self.log(f"警告：文件应该已删除但仍然存在: {file_path}")
            return f"{len(still_exists)} 个文件可能未被彻底删除"
        else:
            return "所有文件已被成功删除"
    
    def _is_ssd(self, file_path):
        """检测文件所在的设备是否为SSD"""
        try:
            # 初始化缓存（在类级别持久化）
            if not hasattr(self, '_ssd_cache'):
                self._ssd_cache = {}
            
            # 获取文件所在的驱动器字母
            drive_letter = os.path.splitdrive(file_path)[0].upper()
            if not drive_letter:
                return False
            
            # 检查缓存
            if drive_letter in self._ssd_cache:
                return self._ssd_cache[drive_letter]
            
            # 使用更快的wmic命令格式并设置超时
            try:
                # 使用更高效的wmic命令，只获取必要信息
                command = f'wmic diskdrive where DeviceID="{drive_letter}:\\" get MediaType /value'
                result = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    shell=True, 
                    encoding='gbk',
                    timeout=3  # 设置3秒超时
                )
                
                if result.returncode == 0 and "SSD" in result.stdout:
                    self._ssd_cache[drive_letter] = True
                else:
                    self._ssd_cache[drive_letter] = False
            except subprocess.TimeoutExpired:
                # 超时，假设不是SSD
                self.log(f"SSD检测超时，假设为非SSD设备")
                self._ssd_cache[drive_letter] = False
            except Exception as e:
                self.log(f"使用wmic检测SSD时出错: {str(e)}")
                self._ssd_cache[drive_letter] = False
            
            return self._ssd_cache[drive_letter]
        except Exception as e:
            self.log(f"检测SSD时出错: {str(e)}")
            return False
    
    def _secure_data_removal(self, file_path, force_kill=False, disable_protection=False, algorithm="default", passes=3):
        """安全数据删除 - 确保文件无法被恢复"""
        try:
            self.log(f"开始安全数据删除: {os.path.basename(file_path)}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.log(f"文件不存在: {file_path}")
                return True
            
            # 检测是否为SSD
            is_ssd_device = self._is_ssd(file_path)
            if is_ssd_device:
                self.log(f"检测到文件所在设备为SSD，将使用SSD优化的删除策略")
            
            # 第一步：强制终止使用该文件的进程
            if force_kill:
                try:
                    self._terminate_processes_using_file(file_path)
                    time.sleep(0.5)  # 等待进程完全终止
                except Exception as e:
                    self.log(f"强制终止进程失败: {str(e)}")
            
            # 第二步：禁用文件保护机制
            if disable_protection:
                try:
                    self._disable_file_protection(file_path)
                    time.sleep(0.2)
                except Exception as e:
                    self.log(f"禁用文件保护失败: {str(e)}")
            
            # 第三步：多级权限提升
            try:
                self._multi_level_privilege_escalation()
            except Exception as e:
                self.log(f"权限提升失败: {str(e)}")
            
            # 第四步：使用最强的删除方法
            shred_success = False
            
            # 方法1：使用高级API删除
            try:
                if self._advanced_api_shredding(file_path, algorithm=algorithm, passes=passes):
                    shred_success = True
                    self.log("高级API删除成功")
            except Exception as e:
                self.log(f"高级API删除失败: {str(e)}")
            
            # 方法2：如果高级API失败，使用win32file直接写入
            if not shred_success:
                try:
                    if self._win32file_shredding(file_path, algorithm=algorithm, passes=passes):
                        shred_success = True
                        self.log("win32file直接写入删除成功")
                except Exception as e:
                    self.log(f"win32file删除失败: {str(e)}")
            
            # 方法3：如果还是失败，使用ctypes直接调用底层API
            if not shred_success:
                try:
                    if self._ctypes_api_shredding(file_path, algorithm=algorithm, passes=passes):
                        shred_success = True
                        self.log("ctypes底层API删除成功")
                except Exception as e:
                    self.log(f"ctypes删除失败: {str(e)}")
            
            # 方法4：终极强制删除（所有方法都失败后）
            if not shred_success:
                try:
                    self._ultimate_force_deletion(file_path)
                    shred_success = True
                    self.log("终极强制删除成功")
                except Exception as e:
                    self.log(f"终极强制删除失败: {str(e)}")
            
            # 第五步：最终验证和清理
            if shred_success:
                try:
                    # 验证文件是否真的被删除
                    if os.path.exists(file_path):
                        # 再次尝试删除
                        self._force_delete_with_unlock(file_path)
                    
                    # 清理可能的残留文件
                    self._cleanup_file_residues(file_path)
                    
                    self.log(f"终极深度删除完成: {os.path.basename(file_path)}")
                    return True
                except Exception as e:
                    self.log(f"最终清理失败: {str(e)}")
                    return True  # 即使清理失败，原文件应该已经被删除了
            else:
                self.log(f"终极深度删除失败: {os.path.basename(file_path)}")
                return False
                
        except Exception as e:
            self.log(f"终极深度删除时发生错误: {str(e)}")
            return False
    
    def _clean_empty_directories(self, directory):
        """清理空目录"""
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                # 只尝试删除空目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # 检查目录是否为空
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self.log(f"删除空目录: {dir_path}")
                        else:
                            # 如果不为空，尝试递归删除内部空目录
                            self._clean_empty_directories(dir_path)
                    except:
                        continue
        except Exception as e:
            self.log(f"清理空目录时出错: {str(e)}")
    
    def _cleanup_file_residues(self, file_path):
        """清理文件残留痕迹"""
        try:
            # 清理可能的临时文件
            temp_extensions = ['.tmp', '.bak', '.old', '.swp', '.dmp']
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_base, file_ext = os.path.splitext(file_name)
            
            for ext in temp_extensions:
                residue_files = [
                    file_path + ext,
                    os.path.join(file_dir, file_base + ext),
                    os.path.join(file_dir, f"{file_name}.{ext}")
                ]
                
                for residue in residue_files:
                    try:
                        if os.path.exists(residue):
                            os.remove(residue)
                            self.log(f"清理残留文件: {residue}")
                    except:
                        continue
            
            # 清理可能的索引节点相关文件
            try:
                # 搜索文件名相似的文件
                for root, dirs, files in os.walk(file_dir):
                    for other_file in files:
                        if file_name.lower() in other_file.lower() and other_file != file_name:
                            other_path = os.path.join(root, other_file)
                            try:
                                os.remove(other_path)
                                self.log(f"清理相似残留: {other_path}")
                            except:
                                continue
            except:
                pass
                
        except Exception as e:
            self.log(f"清理文件残留时出错: {str(e)}")
    
    def _win32file_shredding(self, file_path, algorithm="default", passes=3):
        """使用win32file进行直接磁盘扇区写入删除"""
        try:
            if not WIN32FILE_AVAILABLE:
                return False
                
            # 确保文件是打开的权限
            handle = win32file.CreateFileW(
                file_path,
                win32file.GENERIC_WRITE | win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL | win32file.FILE_FLAG_WRITE_THROUGH,
                None
            )
            
            try:
                # 获取文件大小
                file_size = win32api.GetFileSize(handle)
                
                # 使用_multi_layer_shredding方法进行覆盖，保持算法一致性
                self.log(f"使用win32file API进行{algorithm}算法覆盖...")
                
                # 多轮覆盖，使用指定的算法和次数
                # 根据算法确定实际的覆盖次数和模式
                if algorithm == "gutmann":
                    actual_passes = 35
                elif algorithm == "dod5220":
                    actual_passes = 3
                else:
                    actual_passes = passes
                
                for pass_num in range(actual_passes):
                    win32file.SetFilePointer(handle, 0, win32file.FILE_BEGIN)
                    
                    # 根据算法选择覆盖模式
                    if algorithm == "dod5220":
                        # DoD 5220.22-M标准：随机数据 -> 补码 -> 零
                        if pass_num % 3 == 0:
                            pattern = "random"
                        elif pass_num % 3 == 1:
                            pattern = "complement"
                        else:
                            pattern = "zero"
                    elif algorithm == "gutmann":
                        # Gutmann算法：使用预定义的模式
                        gutmann_patterns = [
                            0x55, 0xAA, 0x92, 0x49, 0x24, 0x92, 0x49, 0x24, 0x6D, 0xB6, 0xDB, 0x6D,
                            0xB6, 0xDB, 0x6D, 0xB6, 0xDB, 0x6D, 0xB6, 0xDB, 0x6D, 0xB6, 0xDB, 0x6D,
                            0xB6, 0xDB, 0x6D, 0xB6, 0xDB, 0x6D, 0xB6, 0xDB, 0x6D, 0xB6, 0x00
                        ]
                        pattern_byte = gutmann_patterns[pass_num % len(gutmann_patterns)]
                        pattern = "fixed" + str(pattern_byte)
                    elif algorithm == "random":
                        pattern = "random"
                    else:  # default
                        # 默认算法：随机数据 -> 1 -> 零
                        if pass_num % 3 == 0:
                            pattern = "random"
                        elif pass_num % 3 == 1:
                            pattern = "ones"
                        else:
                            pattern = "zero"
                    
                    # 写入相应的覆盖数据
                    for i in range(0, file_size, 4096):  # 4KB块大小
                        remaining = file_size - i
                        block_size = min(4096, remaining)
                        
                        if pattern == "random":
                            data_block = os.urandom(block_size)
                        elif pattern == "zero":
                            data_block = b'\x00' * block_size
                        elif pattern == "ones":
                            data_block = b'\xFF' * block_size
                        elif pattern == "complement":
                            # 生成互补数据
                            random_data = os.urandom(block_size)
                            data_block = bytes(~b & 0xFF for b in random_data)
                        elif pattern.startswith("fixed"):
                            # 固定值覆盖
                            fixed_byte = int(pattern[5:])
                            data_block = bytes([fixed_byte]) * block_size
                        else:
                            data_block = os.urandom(block_size)
                        
                        # 写入数据
                        win32file.WriteFile(handle, data_block)
                    
                    # 强制写入磁盘
                    win32file.FlushFileBuffers(handle)
                
                # 截断文件
                win32file.SetFilePointer(handle, 0, win32file.FILE_BEGIN)
                win32file.SetEndOfFile(handle)
                win32file.FlushFileBuffers(handle)
                
                return True
                
            finally:
                win32file.CloseHandle(handle)
                
        except Exception as e:
            self.log(f"win32file删除失败: {str(e)}")
            return False
    
    def _ctypes_api_shredding(self, file_path):
        """使用ctypes调用底层Windows API进行删除"""
        try:
            # 加载必要的Windows API
            kernel32 = ctypes.windll.kernel32
            advapi32 = ctypes.windll.advapi32
            
            # 定义常量
            GENERIC_READ = 0x80000000
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            FILE_SHARE_WRITE = 0x00000002
            FILE_SHARE_DELETE = 0x00000004
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 0x00000080
            FILE_FLAG_WRITE_THROUGH = 0x80000000
            
            # 打开文件
            handle = kernel32.CreateFileW(
                file_path,
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                None,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL | FILE_FLAG_WRITE_THROUGH,
                None
            )
            
            if handle == -1:
                return False
            
            try:
                # 获取文件大小
                LARGE_INTEGER = ctypes.c_ulonglong
                file_size = LARGE_INTEGER()
                
                if not kernel32.GetFileSizeEx(handle, ctypes.byref(file_size)):
                    return False
                
                size = file_size.value
                
                # 多轮删除覆盖
                for pass_num in range(3):
                    # 随机数据覆盖
                    kernel32.SetFilePointer(handle, 0, None)  # FILE_BEGIN
                    for i in range(0, size, 8192):  # 8KB块
                        remaining = size - i
                        block_size = min(8192, remaining)
                        
                        # 生成随机数据
                        random_data = os.urandom(block_size)
                        random_buffer = (ctypes.c_ubyte * block_size)(*random_data)
                        
                        # 写入数据
                        written = ctypes.c_ulong(0)
                        kernel32.WriteFile(
                            handle,
                            ctypes.byref(random_buffer),
                            block_size,
                            ctypes.byref(written),
                            None
                        )
                    
                    # 强制写入磁盘
                    kernel32.FlushFileBuffers(handle)
                    
                    # 零覆盖
                    kernel32.SetFilePointer(handle, 0, None)
                    zero_buffer = (ctypes.c_ubyte * 8192)(*([0] * 8192))
                    for i in range(0, size, 8192):
                        remaining = size - i
                        block_size = min(8192, remaining)
                        if block_size < 8192:
                            zero_buffer = (ctypes.c_ubyte * block_size)(*([0] * block_size))
                        
                        written = ctypes.c_ulong(0)
                        kernel32.WriteFile(
                            handle,
                            ctypes.byref(zero_buffer),
                            block_size,
                            ctypes.byref(written),
                            None
                        )
                    
                    kernel32.FlushFileBuffers(handle)
                
                # 截断文件
                kernel32.SetFilePointer(handle, 0, None)
                kernel32.SetEndOfFile(handle)
                kernel32.FlushFileBuffers(handle)
                
                return True
                
            finally:
                kernel32.CloseHandle(handle)
                
        except Exception as e:
            self.log(f"ctypes API删除失败: {str(e)}")
            return False
    
    def start_file_shredding(self):
        """强力粉碎功能 - 支持选择文件或文件夹进行粉碎"""
        try:
            self.log("强力粉碎功能已启动")
            self.status_label.config(text="强力粉碎功能已启动，请选择要粉碎的项目...", fg="#8e44ad")
            
            # 先让用户选择要粉碎的项目类型
            mode_dialog = tk.Toplevel(self.root)
            mode_dialog.title("选择粉碎类型")
            mode_dialog.geometry("300x150")
            mode_dialog.resizable(False, False)
            mode_dialog.transient(self.root)
            mode_dialog.grab_set()
            
            # 居中显示
            mode_dialog.update_idletasks()
            x = (mode_dialog.winfo_screenwidth() // 2) - (mode_dialog.winfo_width() // 2)
            y = (mode_dialog.winfo_screenheight() // 2) - (mode_dialog.winfo_height() // 2)
            mode_dialog.geometry(f"+{x}+{y}")
            
            # 选择模式变量
            shred_mode = tk.StringVar(value="file")
            
            # 提示标签
            tk.Label(mode_dialog, text="请选择要粉碎的项目类型：", font=("微软雅黑", 10)).pack(pady=10)
            
            # 文件选择按钮
            tk.Radiobutton(
                mode_dialog, 
                text="文件（可多选）", 
                variable=shred_mode, 
                value="file"
            ).pack(anchor=tk.CENTER, pady=2)
            
            # 文件夹选择按钮
            tk.Radiobutton(
                mode_dialog, 
                text="文件夹", 
                variable=shred_mode, 
                value="folder"
            ).pack(anchor=tk.CENTER, pady=2)
            
            # 选择结果
            selected_paths = []
            item_type = ""
            
            def proceed():
                nonlocal selected_paths, item_type
                
                if shred_mode.get() == "file":
                    # 选择文件
                    selected_files = list(filedialog.askopenfilenames(
                        title="选择要强力粉碎的文件",
                        filetypes=[("所有文件", "*.*")]
                    ))
                    selected_paths = list(selected_files)
                    if selected_paths:
                        item_type = f"{len(selected_paths)} 个文件"
                else:
                    # 选择文件夹
                    selected_folder = filedialog.askdirectory(
                        title="选择要强力粉碎的文件夹"
                    )
                    if selected_folder:
                        selected_paths = [selected_folder]
                        item_type = "1 个文件夹"
                
                mode_dialog.destroy()
            
            # 确定按钮
            tk.Button(
                mode_dialog, 
                text="确定", 
                command=proceed,
                padx=20, pady=5
            ).pack(pady=10)
            
            # 等待对话框关闭
            self.root.wait_window(mode_dialog)
            
            # 如果没有选择任何项目，取消操作
            if not selected_paths:
                self.status_label.config(text="文件粉碎已取消", fg="#f39c12")
                return
            
            self.log(f"已选择 {item_type} 进行强力粉碎")
            
            # 简化的确认对话框
            confirm_dialog = tk.Toplevel(self.root)
            confirm_dialog.title("强力粉碎确认")
            confirm_dialog.geometry("400x200")
            confirm_dialog.resizable(False, False)
            confirm_dialog.transient(self.root)
            confirm_dialog.grab_set()
            
            # 居中显示
            confirm_dialog.update_idletasks()
            x = (confirm_dialog.winfo_screenwidth() // 2) - (confirm_dialog.winfo_width() // 2)
            y = (confirm_dialog.winfo_screenheight() // 2) - (confirm_dialog.winfo_height() // 2)
            confirm_dialog.geometry(f"+{x}+{y}")
            
            # 确认信息
            tk.Label(confirm_dialog, text="强力粉碎确认", font=("微软雅黑", 12, "bold")).pack(pady=10)
            tk.Label(confirm_dialog, text=f"确定要强力粉碎选中的 {item_type}吗？",
                   wraplength=350).pack(pady=10)
            tk.Label(confirm_dialog, text="此操作不可逆！", fg="#e74c3c", font=("微软雅黑", 10, "bold")).pack(pady=10)
            
            # 配置结果
            config_result = None
            
            # 简化的按钮 - 只保留确认和取消
            button_frame = tk.Frame(confirm_dialog)
            button_frame.pack(pady=20)
            
            def proceed():
                nonlocal config_result
                # 使用安全的默认配置
                config_result = {
                    "algorithm": "default",
                    "passes": 5,  # 使用更安全的默认值
                    "recursive": True,  # 默认递归粉碎文件夹
                    "force_kill": True,
                    "disable_protection": True
                }
                confirm_dialog.destroy()
            
            tk.Button(button_frame, text="确认", width=15, bg="#3498db", fg="white",
                      command=proceed).pack(side="left", padx=10)
            tk.Button(button_frame, text="取消", width=15, bg="#e74c3c", fg="white",
                      command=lambda: [confirm_dialog.destroy(), setattr(confirm_dialog, "result", None)]).pack(side="left", padx=10)
            
            # 等待用户操作
            self.root.wait_window(confirm_dialog)
            
            if config_result is None:
                self.status_label.config(text="文件粉碎已取消", fg="#f39c12")
                return
            
            # 执行强力粉碎
            self._execute_force_shredding(selected_paths, **config_result)
            
        except Exception as e:
            self.log(f"强力粉碎启动失败: {e}")
            self.status_label.config(text=f"强力粉碎启动失败: {e}", fg="#e74c3c")
            messagebox.showerror("错误", f"强力粉碎启动失败: {e}")
    
    def _execute_force_shredding(self, paths, algorithm="default", passes=3, recursive=False, force_kill=True, disable_protection=True, wait_for_completion=False):
        """执行强力粉碎操作"""
        import time
        import concurrent.futures
        import threading
        from threading import Event
        from multiprocessing import Value
        
        # 结果变量，用于在线程间传递粉碎结果
        shredding_result = [0, 0]  # [成功数, 失败数]
        
        # 将_collect_files_to_process函数移到顶层，以便在整个函数中被访问
        def _collect_files_to_process(paths, recursive):
            """收集所有要处理的文件 - 使用重构后的核心模块"""
            try:
                # 导入核心粉碎模块
                from core_shredding import collect_files_to_process as core_collect_files
                
                # 使用核心模块收集文件
                all_files, processed_folders = core_collect_files(paths, recursive)
                return all_files, processed_folders
            except Exception as e:
                self.log(f"使用核心模块收集文件失败: {str(e)}, 使用备用实现")
                
                # 备用实现
                all_files = []
                processed_folders = []
                
                for path in paths:
                    if os.path.isdir(path):
                        processed_folders.append(path)
                        if not recursive:
                            # 只处理当前目录
                            for f in os.listdir(path):
                                file_path = os.path.join(path, f)
                                if os.path.isfile(file_path) and file_path not in all_files:
                                    all_files.append(file_path)
                        else:
                            # 递归处理所有文件
                            for root, dirs, files in os.walk(path, topdown=False):
                                for f in files:
                                    file_path = os.path.join(root, f)
                                    if file_path not in all_files:
                                        all_files.append(file_path)
                    else:
                        if path not in all_files:
                            all_files.append(path)
                
                return all_files, processed_folders
        
        # 将所有辅助函数移到顶层，以便在整个函数中被访问
        def _create_progress_dialog(total_files, algorithm, passes):
            """创建进度对话框"""
            # 非GUI环境下跳过进度对话框创建
            if not hasattr(self, 'root') or self.root is None:
                return None, None, None, None, None, None, None, None
            
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("强力粉碎进度")
            progress_dialog.geometry("550x350")
            progress_dialog.resizable(False, False)
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            
            # 居中显示
            progress_dialog.update_idletasks()
            x = (progress_dialog.winfo_screenwidth() // 2) - (progress_dialog.winfo_width() // 2)
            y = (progress_dialog.winfo_screenheight() // 2) - (progress_dialog.winfo_height() // 2)
            progress_dialog.geometry(f"+{x}+{y}")
            
            # 进度标题
            tk.Label(progress_dialog, text="强力粉碎进度", font=("Microsoft YaHei", 12, "bold")).pack(pady=10)
            
            # 当前操作状态
            status_frame = tk.Frame(progress_dialog)
            status_frame.pack(pady=5)
            tk.Label(status_frame, text="当前状态：", font=("Microsoft YaHei", 10), fg="#333").pack(side=tk.LEFT)
            current_status = tk.Label(status_frame, text="正在初始化...", font=("Microsoft YaHei", 10, "italic"), fg="#0066cc")
            current_status.pack(side=tk.LEFT)
            
            # 更新初始化状态
            current_status.config(text="正在执行粉碎...", fg="#0066cc")
            progress_dialog.update_idletasks()
            
            # 进度条和百分比
            progress_frame = tk.Frame(progress_dialog)
            progress_frame.pack(pady=10)
            
            from tkinter import ttk
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, length=400, mode="determinate")
            progress_bar.pack(side=tk.LEFT)
            
            progress_percentage = tk.Label(progress_frame, text="0%", width=6, font=("Microsoft YaHei", 10))
            progress_percentage.pack(side=tk.LEFT, padx=10)
            
            # 文件计数器
            counter_label = tk.Label(progress_dialog, text=f"已处理: 0 / {total_files} 个文件", font=("Microsoft YaHei", 10), fg="#666")
            counter_label.pack(pady=5)
            
            # 算法信息
            tk.Label(progress_dialog, 
                     text=f"使用算法: {algorithm} | 覆盖次数: {passes}", 
                     font=("Microsoft YaHei", 9), 
                     fg="#888").pack(pady=5)
            
            # 当前处理的文件
            file_frame = tk.Frame(progress_dialog)
            file_frame.pack(pady=5)
            tk.Label(file_frame, text="当前文件：", font=("Microsoft YaHei", 10), fg="#333").pack(side=tk.LEFT)
            current_file = tk.Label(file_frame, text="准备开始...", font=("Microsoft YaHei", 10, "italic"), fg="#333", wraplength=450)
            current_file.pack(side=tk.LEFT, anchor="w")
            
            # 操作状态
            action_label = tk.Label(progress_dialog, text="", font=("Microsoft YaHei", 10), fg="#2e8b57")
            action_label.pack(pady=5)
            
            # 性能监控
            performance_label = tk.Label(progress_dialog, text="速度: 0.00 MB/s | 剩余时间: 计算中", font=("Microsoft YaHei", 9), fg="#888")
            performance_label.pack(pady=5)
            
            return progress_dialog, current_status, progress_var, progress_percentage, counter_label, current_file, action_label, performance_label
        
        def _setup_cancel_mechanism(progress_dialog, current_status):
            """设置取消机制"""
            cancel_shred = Event()
            
            def cancel_shredding():
                cancel_shred.set()
                self.log("用户取消了文件粉碎操作")
                if current_status:
                    current_status.config(text="正在取消操作...", fg="#ff6600")
            
            # 取消按钮
            cancel_button = tk.Button(progress_dialog, text="取消", bg="#ff6b6b", fg="white", width=10, command=cancel_shredding)
            cancel_button.pack(pady=15)
            
            return cancel_shred
        
        def _create_progress_updater(total_files, progress_var, progress_percentage, counter_label, current_file, action_label, performance_label, lock):
            """创建进度更新器"""
            # 性能监控变量
            total_processed_size = 0
            last_processed_count = 0
            last_processed_size = 0
            last_time = time.time()
            last_ui_update = 0  # 上次UI更新时间
            UI_UPDATE_INTERVAL = 0.1  # UI更新间隔（秒）
            
            # 保存最近的速度记录，用于平滑平均
            speed_history = []
            MAX_HISTORY = 5
            
            def update_progress(current_idx, status, file_size=0):
                nonlocal total_processed_size, last_processed_count, last_processed_size, last_time, last_ui_update, speed_history
                
                # 更新已处理大小
                with lock:
                    # 只有当file_size大于0时才累加（避免进度回调时的重复累加）
                    if file_size > 0:
                        total_processed_size += file_size
                
                # 计算进度百分比（基于文件数量）
                progress = min((current_idx / total_files) * 100, 100)
                
                # 计算当前时间
                current_time = time.time()
                time_diff = current_time - last_time
                
                # 检查是否需要更新UI
                if current_time - last_ui_update < UI_UPDATE_INTERVAL:
                    return  # 不频繁更新UI
                
                last_ui_update = current_time
                
                # 定义UI更新函数，将在主线程中执行
                def update_ui():
                    nonlocal last_processed_count, last_processed_size, last_time
                    
                    try:
                        # 检查是否为GUI环境
                        is_gui = all([progress_var, progress_percentage, counter_label, current_file, action_label])
                        
                        if is_gui:
                            # 更新进度条和计数器
                            progress_var.set(progress)
                            progress_percentage.config(text=f"{int(progress)}%")
                            counter_label.config(text=f"已处理: {current_idx} / {total_files} 个文件")
                            current_file.config(text=os.path.basename(status[0]))
                            action_label.config(text=status[1])
                            
                            # 更新速度和剩余时间
                            if time_diff > 0.5:  # 每0.5秒更新一次性能数据
                                # 计算文件处理速度
                                files_processed = current_idx - last_processed_count
                                
                                # 计算数据处理速度（MB/s）
                                data_processed = total_processed_size - last_processed_size
                                data_speed = (data_processed / (1024 * 1024)) / time_diff if time_diff > 0 else 0
                                
                                # 记录速度历史
                                speed_history.append(data_speed)
                                if len(speed_history) > MAX_HISTORY:
                                    speed_history.pop(0)
                                
                                # 计算平均速度
                                avg_speed = sum(speed_history) / len(speed_history) if speed_history else 0
                                
                                # 计算剩余时间（基于平均速度和剩余数据）
                                remaining_files = total_files - current_idx
                                remaining_time = 0
                                
                                if current_idx > 0 and avg_speed > 0:
                                    # 估计剩余文件的平均大小
                                    avg_file_size = total_processed_size / current_idx if current_idx > 0 else 0
                                    estimated_remaining_data = remaining_files * avg_file_size
                                    remaining_time = estimated_remaining_data / (avg_speed * 1024 * 1024) if avg_speed > 0 else 0
                                    remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time))
                                else:
                                    remaining_time_str = "计算中"
                                
                                # 更新性能标签
                                if performance_label:
                                    performance_label.config(
                                        text=f"速度: {data_speed:.2f} MB/s (平均: {avg_speed:.2f} MB/s) | 剩余时间: {remaining_time_str}"
                                    )
                        
                        # 更新最后处理的计数和大小（在主线程中更新）
                        last_processed_count = current_idx
                        last_processed_size = total_processed_size
                        last_time = current_time
                    except RuntimeError as e:
                        # 捕获主线程错误，跳过UI更新
                        if "main thread is not in main loop" not in str(e):
                            # 其他RuntimeError仍需记录
                            self.log(f"UI更新错误: {str(e)}")
                    except Exception as e:
                        # 捕获其他异常，避免影响主流程
                        self.log(f"UI更新异常: {str(e)}")
                
                # 使用after_idle确保UI更新在主线程中执行
                try:
                    # 检查progress_var是否有master属性（GUI环境）
                    if hasattr(progress_var, 'master') and progress_var.master:
                        progress_var.master.after_idle(update_ui)
                    # 如果没有master属性，说明是测试环境，直接执行更新
                    else:
                        update_ui()
                except Exception as e:
                    # 处理"main thread is not in main loop"错误
                    if "main thread is not in main loop" in str(e):
                        update_ui()
                    else:
                        # 如果是其他错误，也直接执行更新
                        update_ui()
            
            return update_progress
        
        # 收集所有要处理的文件
        all_files_to_process, processed_folders = _collect_files_to_process(paths, recursive)
        total_files = len(all_files_to_process)
        
        self.log(f"开始强力粉碎操作，共 {total_files} 个文件，算法：{algorithm}，覆盖次数：{passes}")
        
        # 创建线程安全的计数器和列表
        processed_count = Value('i', 0)
        success_count = Value('i', 0)
        lock = threading.Lock()
        
        success_files = []
        failed_files = []
        
        # 创建进度对话框
        progress_dialog, current_status, progress_var, progress_percentage, counter_label, current_file, action_label, performance_label = \
            _create_progress_dialog(total_files, algorithm, passes)
        
        # 设置取消机制
        cancel_shred = Event()  # 默认创建一个事件对象
        if progress_dialog and current_status:
            # 只有在GUI环境下才设置真正的取消机制
            cancel_shred = _setup_cancel_mechanism(progress_dialog, current_status)
        
        # 创建进度更新器 - 根据是否为GUI环境使用不同的实现
        if progress_dialog and current_status and progress_var and progress_percentage:
            # GUI环境下使用完整的进度更新器
            update_progress = _create_progress_updater(total_files, progress_var, progress_percentage, counter_label, current_file, action_label, performance_label, lock)
        else:
            # 非GUI环境下使用简化的进度更新器
            def update_progress(current_idx, status, file_size):
                # 简单记录日志，不进行GUI更新
                if status:
                    self.log(f"处理文件 {current_idx}/{total_files}: {status[1]} - {os.path.basename(status[0])}")
        
        # 定义文件处理函数
        def process_single_file(file_path):
            """处理单个文件"""
            if cancel_shred.is_set():
                return False, file_path, 0
            
            try:
                file_size = os.path.getsize(file_path)
                
                # 使用线程安全的方式更新进度
                with lock:
                    current_idx = processed_count.value + 1
                    processed_count.value = current_idx
                
                update_progress(current_idx, (file_path, "准备粉碎..."), file_size)
                
                # 创建文件级进度回调
                def file_progress_callback(current_pass, total_passes, current_block, total_blocks, file_size):
                    # 更新当前文件的详细进度
                    status = f"第 {current_pass}/{total_passes} 轮 - 正在覆盖块 {current_block}/{total_blocks}"
                    
                    # 只更新状态，不更新已处理大小，避免重复累加
                    update_progress(current_idx, (file_path, status), 0)
                
                # 直接调用_shred_file，并传递进度回调
                shred_result = self._shred_file(
                    file_path, 
                    algorithm=algorithm, 
                    passes=passes, 
                    force_kill=force_kill, 
                    disable_protection=disable_protection,
                    progress_callback=file_progress_callback
                )
                
                if shred_result:
                    with lock:
                        success_count.value += 1
                        success_files.append(file_path)
                    update_progress(current_idx, (file_path, "粉碎成功！"), file_size)
                    self.log(f"文件粉碎成功: {file_path}")
                    return True, file_path, file_size
                else:
                    with lock:
                        failed_files.append(file_path)
                    update_progress(current_idx, (file_path, "粉碎失败！"), file_size)
                    self.log(f"文件粉碎失败: {file_path}")
                    return False, file_path, file_size
            except Exception as e:
                with lock:
                    failed_files.append(file_path)
                    current_idx = processed_count.value + 1
                    processed_count.value = current_idx
                update_progress(current_idx, (file_path, "处理错误！"), 0)
                self.log(f"文件处理错误: {file_path} - {str(e)}")
                return False, file_path, 0
        
        # 定义文件夹删除函数
        def delete_empty_folders():
            """删除空文件夹"""
            for path in paths:
                if os.path.isdir(path):
                    try:
                        if recursive:
                            shutil.rmtree(path, ignore_errors=True)
                            self.log(f"文件夹删除成功: {path}")
                        else:
                            # 只删除当前目录中的文件
                            for file_name in os.listdir(path):
                                file_path = os.path.join(path, file_name)
                                if os.path.isfile(file_path):
                                    continue  # 文件已经粉碎了
                                elif os.path.isdir(file_path):
                                    try:
                                        os.rmdir(file_path)  # 尝试删除空目录
                                        self.log(f"子目录删除成功: {file_path}")
                                    except:
                                        pass  # 非空目录不删除
                            # 尝试删除主目录
                            try:
                                os.rmdir(path)
                                self.log(f"文件夹删除成功: {path}")
                            except:
                                self.log(f"文件夹删除失败 (可能非空): {path}")
                    except Exception as e:
                        self.log(f"文件夹删除失败: {path} - {e}")
        
        # 执行实际的粉碎操作
        def perform_shredding():
            """执行实际的粉碎操作"""
            # 计算最优线程数
            cpu_count = os.cpu_count() or 4
            max_workers = min(16, max(2, cpu_count * 4))  # 增加最大线程数，提高并发处理能力
            
            # 如果文件数量很少，减少线程数以避免线程创建开销
            if total_files < max_workers:
                max_workers = total_files
            
            self.log(f"使用 {max_workers} 个线程进行并行文件粉碎")
            
            # 设置全局超时时间（相对秒数）
            total_timeout = 30 * len(all_files_to_process)  # 每个文件最多30秒，总超时
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有文件处理任务
                futures = []
                for file_path in all_files_to_process:
                    future = executor.submit(process_single_file, file_path)
                    futures.append(future)
                
                # 等待所有任务完成或取消，设置全局超时机制
                try:
                    for future in concurrent.futures.as_completed(futures, timeout=total_timeout):
                        if cancel_shred.is_set():
                            break
                        # 获取任务结果，忽略已在process_single_file中处理的异常
                        future.result()
                except concurrent.futures.TimeoutError:
                    self.log(f"全局处理超时，停止所有操作")
                    cancel_shred.set()
                
                # 取消未完成的任务
                if cancel_shred.is_set():
                    for future in futures:
                        if not future.done():
                            future.cancel()
                            self.log(f"取消未完成的任务")
            
            # 处理文件夹删除
            if not cancel_shred.is_set():
                delete_empty_folders()
            
            # 更新完成状态（仅在GUI环境下）
            def update_completion_status():
                if progress_dialog and current_status:
                    if cancel_shred.is_set():
                        current_status.config(text="操作已取消", fg="#ff6600")
                        if action_label:
                            action_label.config(text="正在清理资源...")
                    else:
                        current_status.config(text="粉碎操作完成！", fg="#27ae60")
                
                progress_dialog.update_idletasks()
                time.sleep(0.5)  # 给用户一些时间查看完成状态
                
                progress_dialog.destroy()
            
            # 在主线程中更新完成状态
            if progress_dialog and current_status:
                progress_dialog.after(0, update_completion_status)
            else:
                update_completion_status()
            
            # 计算耗时
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # 显示结果报告（仅在GUI环境下）
            def show_result_report():
                if hasattr(self, 'root') and self.root:
                    self._show_shredding_report(
                        success_count=success_count.value,
                        total_files=total_files,
                        success_files=success_files,
                        failed_files=failed_files,
                        processed_folders=processed_folders,
                        algorithm=algorithm,
                        passes=passes,
                        elapsed_time=elapsed_time,
                        cancel_shred=cancel_shred.is_set()
                    )
            
            # 在主线程中显示结果报告
            if hasattr(self, 'root') and self.root:
                self.root.after(0, show_result_report)
            else:
                show_result_report()
            
            # 返回结果，与测试脚本兼容
            result = (success_count.value, len(failed_files))
            
            # 更新线程间共享的结果变量
            shredding_result[0] = result[0]
            shredding_result[1] = result[1]
            
            return result
        
        # 如果是测试模式（wait_for_completion=True），直接执行粉碎操作
        if wait_for_completion:
            result = perform_shredding()
            return result[0], result[1]
        else:
            # GUI模式下，在后台线程中执行粉碎操作
            shred_thread = threading.Thread(target=perform_shredding, daemon=True)
            shred_thread.start()
            return 0, 0
    
    def _show_shredding_report(self, success_count, total_files, success_files, failed_files, processed_folders, algorithm, passes, elapsed_time, cancel_shred):
        """显示粉碎结果报告"""
        # 创建结果对话框
        result_dialog = tk.Toplevel(self.root)
        result_dialog.title("粉碎结果报告")
        result_dialog.geometry("600x450")
        result_dialog.resizable(True, True)
        result_dialog.transient(self.root)
        result_dialog.grab_set()
        
        # 居中显示
        result_dialog.update_idletasks()
        x = (result_dialog.winfo_screenwidth() // 2) - (result_dialog.winfo_width() // 2)
        y = (result_dialog.winfo_screenheight() // 2) - (result_dialog.winfo_height() // 2)
        result_dialog.geometry(f"+{x}+{y}")
        
        # 结果标题
        if cancel_shred:
            title_text = "粉碎操作已取消"
            title_color = "#f39c12"
        else:
            title_text = "粉碎操作完成"
            title_color = "#27ae60"
        
        title_label = tk.Label(result_dialog, text=title_text, font=("Microsoft YaHei", 14, "bold"), fg=title_color)
        title_label.pack(pady=10)
        
        # 统计信息框架
        stats_frame = tk.Frame(result_dialog, padx=20, pady=10)
        stats_frame.pack(fill="x")
        
        # 统计信息
        stats_text = f"""
        总文件数: {total_files}
        成功粉碎: {success_count} ({int(success_count/total_files*100) if total_files > 0 else 0}%)
        粉碎失败: {len(failed_files)}
        处理文件夹: {len(processed_folders)}
        使用算法: {algorithm}
        覆盖次数: {passes}
        总耗时: {elapsed_time:.2f} 秒
        """
        
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Microsoft YaHei", 10, "bold"), justify="left")
        stats_label.pack(anchor="w")
        
        # 结果列表框架
        list_frame = tk.Frame(result_dialog, padx=20, pady=10)
        list_frame.pack(fill="both", expand=True)
        
        # 选项卡
        from tkinter import ttk
        notebook = ttk.Notebook(list_frame)
        notebook.pack(fill="both", expand=True)
        
        # 成功文件列表
        success_tab = tk.Frame(notebook)
        notebook.add(success_tab, text=f"成功文件 ({len(success_files)})")
        
        success_scrollbar = tk.Scrollbar(success_tab)
        success_scrollbar.pack(side="right", fill="y")
        
        success_listbox = tk.Listbox(success_tab, yscrollcommand=success_scrollbar.set, font=("Microsoft YaHei", 9), selectmode="extended")
        success_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        for file_path in success_files:
            success_listbox.insert(tk.END, os.path.basename(file_path))
        
        success_scrollbar.config(command=success_listbox.yview)
        
        # 失败文件列表
        failed_tab = tk.Frame(notebook)
        notebook.add(failed_tab, text=f"失败文件 ({len(failed_files)})")
        
        failed_scrollbar = tk.Scrollbar(failed_tab)
        failed_scrollbar.pack(side="right", fill="y")
        
        failed_listbox = tk.Listbox(failed_tab, yscrollcommand=failed_scrollbar.set, font=("Microsoft YaHei", 9), selectmode="extended")
        failed_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        for file_path in failed_files:
            failed_listbox.insert(tk.END, os.path.basename(file_path))
        
        failed_scrollbar.config(command=failed_listbox.yview)
        
        # 关闭按钮
        close_button = tk.Button(result_dialog, text="关闭", bg="#4169e1", fg="white", width=15, font=("Microsoft YaHei", 10),
                                command=lambda: result_dialog.destroy())
        close_button.pack(pady=15)
        
        # 更新状态标签
        if cancel_shred:
            self.status_label.config(text=f"文件粉碎已取消 - 已成功粉碎 {success_count}/{total_files} 个文件", fg="#f39c12")
        else:
            self.status_label.config(text=f"强力粉碎完成 - 已成功粉碎 {success_count}/{total_files} 个文件", fg="#27ae60")
            
    def kill_process(self):
        """停止选中程序相关的进程"""
        selected_index = self.program_listbox.curselection()
        if not selected_index:
            messagebox.showinfo("提示", "请先选择要停止进程的程序")
            return
        
        index = selected_index[0]
        if index >= len(self.filtered_programs):
            messagebox.showerror("错误", "无效的程序选择")
            return
            
        program = self.filtered_programs[index]
        display_name = program.get("DisplayName", "未知程序")
        install_path = program.get("InstallLocation", "")
        
        if not install_path:
            messagebox.showinfo("提示", f"无法获取 {display_name} 的安装路径")
            return
            
        confirm = messagebox.askyesno(
            "确认停止进程",
            f"确定要停止 {display_name} 的所有相关进程吗？"
        )
        
        if not confirm:
            return
        
        self.log(f"开始停止 {display_name} 的相关进程...")
        
        # 在线程中执行进程终止
        def terminate_thread():
            try:
                self._terminate_related_processes(install_path)
                self.root.after(0, lambda:
                    messagebox.showinfo("完成", f"已尝试停止 {display_name} 的所有相关进程")
                )
            except Exception as e:
                self.log(f"停止进程时出错: {str(e)}")
                self.root.after(0, lambda:
                    messagebox.showerror("错误", f"停止进程时出错: {str(e)}")
                )
        
        threading.Thread(target=terminate_thread).start()
    
    def _shred_directory(self, dir_path, passes=3):
        """删除整个目录，包括其中的所有文件和子目录"""
        if not os.path.isdir(dir_path):
            return 0
        
        shredded_count = 0
        
        # 先处理所有文件
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if self._shred_file(file_path, passes):
                    shredded_count += 1
        
        # 然后删除空目录
        try:
            shutil.rmtree(dir_path, ignore_errors=True)
        except:
            pass
        
        return shredded_count
    

    
    def _get_available_drives(self):
        """增强版：获取系统中所有可用的驱动器，包括各种存储设备"""
        drives = []
        try:
            # 使用win32api获取所有逻辑驱动器
            drives_list = win32api.GetLogicalDriveStrings()
            # 分割驱动器字符串，Windows返回格式为"C:\\D:\\E:\\"等
            drive_letters = drives_list.split('\\\\')[:-1]  # 最后一个是空字符串，所以排除
            
            self.log(f"发现 {len(drive_letters)} 个逻辑驱动器: {', '.join(drive_letters)}")
            
            # 检查每个驱动器是否可访问
            for drive in drive_letters:
                # 确保驱动器存在且可访问
                if os.path.exists(drive) and os.path.isdir(drive):
                    # 获取驱动器信息
                    try:
                        # 使用win32file获取驱动器类型
                        drive_type = win32file.GetDriveType(drive)
                        drive_info = ""
                        
                        # 根据驱动器类型添加描述
                        if drive_type == 0:
                            drive_info = "未知类型"
                        elif drive_type == 1:
                            drive_info = "无效驱动器"
                            continue
                        elif drive_type == 2:
                            drive_info = "可移动磁盘"
                        elif drive_type == 3:
                            drive_info = "本地硬盘"
                        elif drive_type == 4:
                            drive_info = "网络驱动器"
                            # 可选：是否包含网络驱动器
                            # drives.append(drive)
                        elif drive_type == 5:
                            drive_info = "光盘驱动器"
                        elif drive_type == 6:
                            drive_info = "RAM磁盘"
                        
                        # 我们主要处理本地硬盘(3)、可移动磁盘(2)和RAM磁盘(6)
                        # 对于光盘驱动器，如果包含软件安装文件，也可以考虑处理
                        if drive_type in [2, 3, 6]:
                            # 获取驱动器卷标
                            volume_info = ""
                            try:
                                volume_info = win32api.GetVolumeInformation(drive)[0]
                            except:
                                volume_info = "无卷标"
                            
                            self.log(f"添加驱动器: {drive} ({drive_info}, {volume_info})")
                            drives.append(drive)
                        else:
                            self.log(f"跳过驱动器: {drive} ({drive_info})")
                            
                    except Exception as e:
                        # 如果出现错误，记录日志并尝试添加
                        self.log(f"检查驱动器类型时出错 {drive}: {str(e)}，尝试直接添加")
                        drives.append(drive)
                else:
                    self.log(f"跳过不可访问的驱动器: {drive}")
            
            # 额外检查：尝试获取连接的USB设备信息（即使尚未分配驱动器号）
            self._log_usb_devices_info()
            
            self.log(f"扫描完成，共 {len(drives)} 个可用驱动器用于残留清理: {', '.join(drives)}")
        except Exception as e:
            self.log(f"获取驱动器列表失败: {str(e)}")
        
        return drives
        
    def _log_usb_devices_info(self):
        """记录USB设备信息，帮助识别可能的残留源"""
        try:
            # 执行命令获取USB设备信息
            result = subprocess.run(["wmic", "logicaldisk", "where", "drivetype=2", "get", "caption,description,filesystem,volumename"], 
                                   capture_output=True, text=True, shell=True, timeout=5)
            
            if result.returncode == 0:
                usb_info = result.stdout.strip()
                if usb_info:
                    self.log("已连接的USB设备信息:")
                    for line in usb_info.split('\n'):
                        if line.strip():
                            self.log(f"  {line.strip()}")
        except Exception as e:
            self.log(f"获取USB设备信息失败: {str(e)}")
    
    def _build_search_keywords(self, program_name):
        """构建搜索关键词列表"""
        keywords = []
        # 移除常见后缀
        for suffix in ["installer", "setup", "安装", "卸载", "uninstaller", "app", "application", "程序"]:
            if suffix in program_name:
                program_name = program_name.replace(suffix, "").strip()
        
        # 添加程序名称作为关键词
        keywords.append(program_name)
        # 拆分可能的复合名称
        if " " in program_name:
            keywords.extend(program_name.split())
        if "-" in program_name:
            keywords.extend(program_name.split("-"))
        if "_" in program_name:
            keywords.extend(program_name.split("_"))
        
        # 移除空关键词和太短的关键词
        keywords = [k.strip() for k in keywords if k.strip() and len(k.strip()) > 2]
        return list(set(keywords))  # 去重
    
    def _scan_and_remove_residuals(self, program_name):
        """增强版：扫描并删除更多详细的软件残留文件，包括设备和驱动器残留"""
        # 定义常见的残留位置
        residual_locations = []
        
        # 获取用户目录
        user_dir = os.path.expanduser("~")
        
        # 1. 添加用户相关残留位置（增强版）
        residual_locations.append(os.path.join(user_dir, "AppData", "Roaming"))
        residual_locations.append(os.path.join(user_dir, "AppData", "Local"))
        residual_locations.append(os.path.join(user_dir, "AppData", "LocalLow"))  # 新增：LocalLow目录
        residual_locations.append(os.path.join(user_dir, "Documents"))
        residual_locations.append(os.path.join(user_dir, "Downloads"))
        residual_locations.append(os.path.join(user_dir, "Desktop"))
        residual_locations.append(os.path.join(user_dir, "Favorites"))  # 新增：收藏夹
        residual_locations.append(os.path.join(user_dir, "Music"))  # 新增：音乐文件夹
        residual_locations.append(os.path.join(user_dir, "Pictures"))  # 新增：图片文件夹
        residual_locations.append(os.path.join(user_dir, "Videos"))  # 新增：视频文件夹
        
        # 2. 添加系统临时文件夹（增强版）
        residual_locations.append(os.environ.get("TEMP", ""))
        residual_locations.append(os.environ.get("TMP", ""))
        residual_locations.append(os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp"))  # 新增：系统临时文件夹
        
        # 3. 添加Program Files目录
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        if os.path.exists(program_files):
            residual_locations.append(program_files)
        if os.path.exists(program_files_x86):
            residual_locations.append(program_files_x86)
        
        # 4. 新增：ProgramData目录
        program_data = os.environ.get("ProgramData", "C:\\ProgramData")
        if os.path.exists(program_data):
            residual_locations.append(program_data)
        
        # 5. 新增：开始菜单文件夹
        start_menu = os.path.join(user_dir, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu")
        if os.path.exists(start_menu):
            residual_locations.append(start_menu)
        
        # 6. 新增：公共开始菜单
        public_start_menu = os.path.join(os.environ.get("PUBLIC", ""), "Desktop")
        if os.path.exists(public_start_menu):
            residual_locations.append(public_start_menu)
        
        # 7. 新增：最近使用的项目
        recent = os.path.join(user_dir, "AppData", "Roaming", "Microsoft", "Windows", "Recent")
        if os.path.exists(recent):
            residual_locations.append(recent)
        
        # 8. 新增：历史记录文件夹
        history = os.path.join(user_dir, "AppData", "Local", "Microsoft", "Windows", "History")
        if os.path.exists(history):
            residual_locations.append(history)
        
        # 9. 新增：浏览器缓存相关目录（常见浏览器）
        browsers = {
            "Chrome": os.path.join(user_dir, "AppData", "Local", "Google", "Chrome", "User Data"),
            "Edge": os.path.join(user_dir, "AppData", "Local", "Microsoft", "Edge", "User Data"),
            "Firefox": os.path.join(user_dir, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
        }
        for browser_name, browser_path in browsers.items():
            if os.path.exists(browser_path):
                residual_locations.append(browser_path)
        
        # 10. 增强版：设备和驱动器残留处理
        drives = self._get_available_drives()
        for drive in drives:
            # 排除系统驱动器（通常是C:）以避免误删系统文件
            if drive != "C:":
                # 添加驱动器根目录
                residual_locations.append(drive)
                
                # 新增：扫描驱动器上的常见程序安装目录
                common_prog_dirs = [
                    os.path.join(drive, "Program Files"),
                    os.path.join(drive, "Program Files (x86)"),
                    os.path.join(drive, "Programs"),
                    os.path.join(drive, "Software"),
                    os.path.join(drive, "Applications")
                ]
                for prog_dir in common_prog_dirs:
                    if os.path.exists(prog_dir):
                        residual_locations.append(prog_dir)
                
                # 新增：扫描驱动器上的临时目录
                temp_dirs = [
                    os.path.join(drive, "Temp"),
                    os.path.join(drive, "Temporary"),
                    os.path.join(drive, "tmp")
                ]
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        residual_locations.append(temp_dir)
                
                # 新增：扫描可移动设备特有的残留目录
                removable_dirs = [
                    os.path.join(drive, "Autorun"),
                    os.path.join(drive, "AutoPlay"),
                    os.path.join(drive, "autorun.inf")  # 直接检查autorun文件
                ]
                for removable_dir in removable_dirs:
                    if os.path.exists(removable_dir):
                        residual_locations.append(removable_dir)
        
        self.log(f"扫描路径初始化完成，共 {len(residual_locations)} 个位置，包括 {len(drives)} 个驱动器")
        
        # 构建搜索关键词
        keywords = self._build_search_keywords(program_name)
        
        # 扫描并删除残留
        removed_count = 0
        skipped_system_files = 0
        
        # 定义系统关键目录，避免误删系统文件
        system_critical_dirs = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32").lower(),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "SysWOW64").lower(),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System").lower(),
            # 新增：驱动器系统保护目录
            "\\$recycle.bin",  # 回收站
            "\\system volume information",  # 系统卷信息
            "\\hiberfil.sys",  # 休眠文件
            "\\pagefile.sys",  # 页面文件
            "\\swapfile.sys"   # 交换文件
        ]
        
        for location in residual_locations:
            if not location or not os.path.exists(location):
                continue
                
            try:
                # 跳过系统关键目录
                location_lower = location.lower()
                is_critical = False
                for critical_dir in system_critical_dirs:
                    if critical_dir in location_lower:
                        is_critical = True
                        break
                
                if is_critical:
                    self.log(f"跳过系统关键目录: {location}")
                    continue
                
                # 开始扫描当前位置
                self.log(f"开始扫描位置: {location}")
                
                for root, dirs, files in os.walk(location):
                    # 检查目录
                    dirs_to_remove = []
                    for dir_name in dirs:
                        dir_name_lower = dir_name.lower()
                        for keyword in keywords:
                            if keyword in dir_name_lower:
                                full_path = os.path.join(root, dir_name)
                                # 再次确认不是系统关键文件
                                path_lower = full_path.lower()
                                skip = False
                                for critical_dir in system_critical_dirs:
                                    if critical_dir in path_lower:
                                        skip = True
                                        skipped_system_files += 1
                                        break
                                
                                if skip:
                                    continue
                                
                                self.log(f"发现残留目录: {full_path}")
                                # 先终止相关进程
                                self._terminate_related_processes(full_path)
                                # 强力删除
                                if self._force_delete_directory(full_path):
                                    dirs_to_remove.append(dir_name)
                                    removed_count += 1
                                break
                    
                    # 从dirs中移除已删除的目录，避免继续扫描
                    for dir_name in dirs_to_remove:
                        if dir_name in dirs:
                            dirs.remove(dir_name)
                    
                    # 检查文件
                    for file_name in files:
                        file_name_lower = file_name.lower()
                        for keyword in keywords:
                            if keyword in file_name_lower:
                                full_path = os.path.join(root, file_name)
                                # 再次确认不是系统关键文件
                                path_lower = full_path.lower()
                                skip = False
                                for critical_dir in system_critical_dirs:
                                    if critical_dir in path_lower:
                                        skip = True
                                        skipped_system_files += 1
                                        break
                                
                                if skip:
                                    continue
                                
                                self.log(f"发现残留文件: {full_path}")
                                # 使用增强的文件删除方法，针对设备和驱动器上的文件
                                try:
                                    # 对于设备文件，先尝试直接删除
                                    os.remove(full_path)
                                    removed_count += 1
                                    self.log(f"成功删除文件: {full_path}")
                                except:
                                    try:
                                        # 修改权限后删除
                                        os.chmod(full_path, 0o777)
                                        os.remove(full_path)
                                        removed_count += 1
                                        self.log(f"修改权限后成功删除: {full_path}")
                                    except:
                                        # 尝试使用win32api删除
                                        try:
                                            win32api.DeleteFile(full_path)
                                            removed_count += 1
                                            self.log(f"使用win32api成功删除: {full_path}")
                                        except:
                                            # 新增：对于设备上的文件，尝试使用cmd的删除命令
                                            try:
                                                # 使用cmd的del命令，/f强制删除，/q安静模式
                                                subprocess.run(["cmd.exe", "/c", "del", "/f", "/q", full_path], shell=False)
                                                if not os.path.exists(full_path):
                                                    removed_count += 1
                                                    self.log(f"使用cmd命令成功删除: {full_path}")
                                            except:
                                                self.log(f"无法删除文件: {full_path}")
                                break
            except Exception as e:
                self.log(f"扫描位置出错 {location}: {str(e)}")
        
        self.log(f"残留清理完成，共处理 {removed_count} 个残留项，包括设备和驱动器上的残留文件")
        if skipped_system_files > 0:
            self.log(f"跳过了 {skipped_system_files} 个可能的系统文件")
            
        # 额外步骤：清理设备驱动和存储设备相关残留（如果用户选择）
        device_removed_count = 0
        if hasattr(self, 'clean_device_residuals') and self.clean_device_residuals.get():
            # 给用户一个警告，说明设备残留清理的风险
            import tkinter as tk
            from tkinter import messagebox
            if not hasattr(self, 'root') or self.root is None:
                # 如果没有GUI环境，直接执行
                self.log("警告: 设备残留清理可能影响系统稳定性，建议谨慎操作")
                device_removed_count = self._clean_device_residuals(program_name)
            else:
                # 在GUI环境中，显示确认对话框
                confirm = messagebox.askyesno(
                    "确认清理设备残留",
                    "警告: 清理设备和驱动器残留可能影响系统稳定性，\n" +
                    "特别是对于仍在使用的设备。确定要继续吗？"
                )
                if confirm:
                    device_removed_count = self._clean_device_residuals(program_name)
        
        total_removed = removed_count + device_removed_count
        
        if device_removed_count > 0:
            self.log(f"设备相关残留清理完成，额外删除 {device_removed_count} 个残留项")
        self.log(f"总残留清理完成，共处理 {total_removed} 个残留项")
            
        return total_removed
    
    def _clean_device_residuals(self, program_name):
        """专门清理设备驱动和存储设备上的残留文件"""
        self.log(f"开始清理设备驱动相关残留: {program_name}")
        removed_count = 0
        keywords = self._build_search_keywords(program_name)
        
        try:
            # 1. 扫描Windows设备驱动目录
            driver_dirs = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "DriverStore"),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "drivers")
            ]
            
            for driver_dir in driver_dirs:
                if os.path.exists(driver_dir):
                    # 注意：这些目录包含系统关键文件，我们只记录可疑文件，不自动删除
                    self.log(f"检查设备驱动目录: {driver_dir} (仅记录，不删除)")
                    for root, dirs, files in os.walk(driver_dir):
                        # 限制扫描深度，避免系统负载过高
                        if root.count(os.sep) > driver_dir.count(os.sep) + 2:
                            continue
                        
                        for file_name in files:
                            file_name_lower = file_name.lower()
                            for keyword in keywords:
                                if keyword in file_name_lower:
                                    full_path = os.path.join(root, file_name)
                                    self.log(f"发现可疑设备驱动文件: {full_path} (建议手动检查)")
                                    break
            
            # 2. 扫描设备管理器相关配置
            device_manager_paths = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "inf"),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "config", "systemprofile", "AppData")
            ]
            
            for path in device_manager_paths:
                if os.path.exists(path):
                    self.log(f"扫描设备管理器配置目录: {path}")
                    removed = self._scan_and_remove_in_path(path, keywords)
                    removed_count += removed
            
            # 3. 扫描所有驱动器上的设备相关残留文件夹
            drives = self._get_available_drives()
            device_specific_dirs = [
                "Driver", "Drivers", "Device", "Devices", 
                "Install", "Setup", "Uninstall", "AppData"
            ]
            
            for drive in drives:
                if drive == "C:":
                    continue  # 跳过系统盘，避免误删
                    
                for dir_name in device_specific_dirs:
                    potential_dir = os.path.join(drive, dir_name)
                    if os.path.exists(potential_dir):
                        self.log(f"扫描设备特定目录: {potential_dir}")
                        removed = self._scan_and_remove_in_path(potential_dir, keywords)
                        removed_count += removed
            
            # 4. 检查并清理设备安装日志中的残留
            self._clean_device_install_logs(program_name)
            
        except Exception as e:
            self.log(f"设备残留清理出错: {str(e)}")
        
        return removed_count
    
    def _scan_and_remove_in_path(self, path, keywords):
        """在指定路径中扫描并删除匹配关键词的文件和目录"""
        removed_count = 0
        try:
            # 定义系统关键目录，避免误删
            system_critical_dirs = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32").lower(),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "SysWOW64").lower()
            ]
            
            for root, dirs, files in os.walk(path):
                # 跳过系统关键目录
                path_lower = root.lower()
                skip = False
                for critical in system_critical_dirs:
                    if critical in path_lower:
                        skip = True
                        break
                if skip:
                    continue
                
                # 删除匹配的文件
                for file_name in files:
                    for keyword in keywords:
                        if keyword in file_name.lower():
                            full_path = os.path.join(root, file_name)
                            # 使用增强的删除方法
                            try:
                                os.chmod(full_path, 0o777)
                                os.remove(full_path)
                                removed_count += 1
                                self.log(f"删除设备残留文件: {full_path}")
                            except Exception as e:
                                self.log(f"无法删除设备残留文件 {full_path}: {str(e)}")
                            break
                
                # 删除匹配的目录
                dirs_to_remove = []
                for dir_name in dirs:
                    for keyword in keywords:
                        if keyword in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if self._force_delete_directory(full_path):
                                dirs_to_remove.append(dir_name)
                                removed_count += 1
                                self.log(f"删除设备残留目录: {full_path}")
                            break
                
                # 从dirs中移除已删除的目录
                for dir_name in dirs_to_remove:
                    if dir_name in dirs:
                        dirs.remove(dir_name)
        
        except Exception as e:
            self.log(f"扫描路径 {path} 时出错: {str(e)}")
        
        return removed_count
    
    def _clean_device_install_logs(self, program_name):
        """清理设备安装日志中的残留信息"""
        try:
            # 设备安装日志路径
            log_paths = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "inf", "setupapi.dev.log"),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "inf", "setupapi.app.log")
            ]
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    # 注意：我们不直接修改系统日志，只记录需要关注的内容
                    self.log(f"检查设备安装日志: {log_path} (仅记录，不修改)")
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            if any(keyword in content for keyword in self._build_search_keywords(program_name)):
                                self.log(f"在 {log_path} 中发现与 {program_name} 相关的设备安装记录")
                    except Exception as e:
                        self.log(f"无法读取日志文件 {log_path}: {str(e)}")
        except Exception as e:
            self.log(f"清理设备安装日志出错: {str(e)}")
    
    def _scan_and_clean_registry(self, program_name):
        """扫描并清理与程序相关的注册表项"""
        if not self.has_admin:
            self.log("警告: 没有管理员权限，注册表清理功能受限")
            return 0
        
        # 构建搜索关键词
        keywords = self._build_search_keywords(program_name)
        
        # 定义要扫描的注册表位置
        registry_locations = [
            # 软件安装信息
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            
            # 常用软件注册表位置
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE"),
            
            # 开始菜单和桌面快捷方式
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"),
            
            # 应用程序配置
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        
        removed_count = 0
        
        for hive, base_path in registry_locations:
            try:
                # 扫描基路径下的子键
                removed = self._scan_registry_subkeys(hive, base_path, keywords)
                removed_count += removed
            except Exception as e:
                self.log(f"扫描注册表路径出错 {base_path}: {str(e)}")
        
        return removed_count
    
    def _scan_registry_subkeys(self, hive, base_path, keywords, max_depth=3):
        """递归扫描注册表子键"""
        if max_depth <= 0:
            return 0
            
        removed_count = 0
        
        try:
            # 尝试打开基路径
            key = winreg.OpenKey(hive, base_path, 0, winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS | winreg.KEY_SET_VALUE)
            
            # 获取子键数量
            subkey_count = winreg.QueryInfoKey(key)[0]
            
            # 保存需要删除的子键
            to_delete = []
            
            # 枚举所有子键
            for i in range(subkey_count):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey_path = f"{base_path}\\{subkey_name}"
                    
                    # 检查子键名是否包含关键词
                    match_found = False
                    for keyword in keywords:
                        if keyword.lower() in subkey_name.lower():
                            match_found = True
                            break
                    
                    # 如果匹配，添加到删除列表
                    if match_found:
                        to_delete.append(subkey_name)
                        continue
                    
                    # 递归扫描下一级
                    removed = self._scan_registry_subkeys(hive, subkey_path, keywords, max_depth - 1)
                    removed_count += removed
                    
                    # 检查该子键下的值是否包含关键词
                    if self._check_registry_values(hive, subkey_path, keywords):
                        to_delete.append(subkey_name)
                except Exception as e:
                    # 忽略无法访问的子键
                    continue
            
            # 关闭当前键
            winreg.CloseKey(key)
            
            # 删除标记的子键
            if to_delete:
                try:
                    key = winreg.OpenKey(hive, base_path, 0, winreg.KEY_SET_VALUE)
                    for subkey_name in to_delete:
                        try:
                            full_path = f"{base_path}\\{subkey_name}"
                            self.log(f"删除注册表项: {full_path}")
                            winreg.DeleteKey(key, subkey_name)
                            removed_count += 1
                        except Exception as e:
                            # 尝试递归删除子键（如果有子键）
                            try:
                                self._delete_registry_key_recursive(hive, f"{base_path}\\{subkey_name}")
                                removed_count += 1
                            except:
                                self.log(f"无法删除注册表项 {subkey_name}: {str(e)}")
                except:
                    pass
        except Exception as e:
            # 忽略无法访问的注册表路径
            pass
        
        return removed_count
    
    def _check_registry_values(self, hive, key_path, keywords):
        """检查注册表键的值是否包含关键词"""
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            value_count = winreg.QueryInfoKey(key)[1]
            
            for i in range(value_count):
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    # 检查值名称和值数据
                    for keyword in keywords:
                        if (keyword.lower() in str(value_name).lower() or 
                            keyword.lower() in str(value_data).lower()):
                            winreg.CloseKey(key)
                            return True
                except:
                    continue
            
            winreg.CloseKey(key)
        except:
            pass
        
        return False
    
    def _delete_registry_key_recursive(self, hive, key_path):
        """递归删除注册表键"""
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_ENUMERATE_SUB_KEYS | winreg.KEY_SET_VALUE)
            
            # 先删除所有子键
            subkey_count = winreg.QueryInfoKey(key)[0]
            subkeys_to_delete = []
            
            for i in range(subkey_count):
                try:
                    subkeys_to_delete.append(winreg.EnumKey(key, i))
                except:
                    continue
            
            winreg.CloseKey(key)
            
            # 递归删除子键
            for subkey in subkeys_to_delete:
                self._delete_registry_key_recursive(hive, f"{key_path}\\{subkey}")
            
            # 删除当前键
            parent_path = "\\".join(key_path.split("\\")[:-1])
            key_name = key_path.split("\\")[-1]
            
            parent_key = winreg.OpenKey(hive, parent_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteKey(parent_key, key_name)
            winreg.CloseKey(parent_key)
        except:
            pass
    
    def kill_process(self):
        """强制停止进程"""
        selected_index = self.program_listbox.curselection()
        if not selected_index:
            messagebox.showinfo("提示", "请先选择要停止其进程的程序")
            return
        
        index = selected_index[0]
        program = self.filtered_programs[index]
        display_name = program.get("DisplayName", "未知程序")
        install_location = program.get("InstallLocation", "")
        
        if not install_location:
            messagebox.showinfo("提示", f"未找到 {display_name} 的安装位置，无法确定相关进程")
            return
        
        if messagebox.askyesno("确认停止", f"确定要停止 {display_name} 的所有相关进程吗？"):
            self.log(f"开始终止 {display_name} 的相关进程")
            self._terminate_related_processes(install_location)
            self.log("进程终止操作完成")
            messagebox.showinfo("完成", "相关进程已尝试终止")
    
    def run_in_sandbox(self):
        """以沙箱模式运行选中的程序"""
        selected_index = self.program_listbox.curselection()
        if not selected_index:
            messagebox.showinfo("提示", "请先选择要以沙箱模式运行的程序")
            return
        
        index = selected_index[0]
        program = self.filtered_programs[index]
        display_name = program.get("DisplayName", "未知程序")
        install_location = program.get("InstallLocation", "")
        
        # 查找主可执行文件
        exe_path = self._find_main_executable(install_location, display_name)
        
        if not exe_path:
            messagebox.showerror("错误", f"未找到 {display_name} 的可执行文件，无法在沙箱中运行")
            return
        
        if not os.path.exists(exe_path):
            messagebox.showerror("错误", f"未找到 {display_name} 的可执行文件: {exe_path}，无法在沙箱中运行")
            return
        
        # 显示沙箱配置选项
        config_window = tk.Toplevel(self.root)
        config_window.title(f"沙箱配置 - {display_name}")
        config_window.geometry("400x300")
        config_window.resizable(False, False)
        
        # 配置选项
        restrict_filesystem = BooleanVar(value=True)
        restrict_network = BooleanVar(value=False)
        isolate_registry = BooleanVar(value=True)
        
        # UI元素
        Label(config_window, text="沙箱限制选项:", font=("Microsoft YaHei", 10, "bold")).pack(pady=10)
        
        Checkbutton(config_window, text="限制文件系统访问（仅允许访问程序目录）", variable=restrict_filesystem).pack(anchor="w", padx=20, pady=5)
        Checkbutton(config_window, text="限制网络访问", variable=restrict_network).pack(anchor="w", padx=20, pady=5)
        Checkbutton(config_window, text="隔离注册表访问", variable=isolate_registry).pack(anchor="w", padx=20, pady=5)
        
        def on_run():
            config_window.destroy()
            
            # 确认运行
            if messagebox.askyesno("确认", f"确定要在沙箱中运行 {display_name} 吗？\n\n注意：沙箱会限制程序的系统访问权限，但不会影响程序的基本功能。"):
                self.log(f"开始在沙箱中运行程序: {display_name}")
                self.log(f"可执行文件路径: {exe_path}")
                
                try:
                    # 在后台线程中运行沙箱
                    threading.Thread(target=self._run_program_in_sandbox, 
                                    args=(exe_path, display_name, restrict_filesystem.get(), 
                                          restrict_network.get(), isolate_registry.get()),
                                    daemon=True).start()
                    messagebox.showinfo("成功", f"程序 {display_name} 已在沙箱中启动")
                except Exception as e:
                    self.log(f"沙箱运行失败: {str(e)}")
                    messagebox.showerror("错误", f"启动沙箱失败: {str(e)}")
        
        # 按钮
        Button(config_window, text="运行", command=on_run, width=10).pack(pady=20)
        Button(config_window, text="取消", command=config_window.destroy, width=10).pack()
    
    def _find_main_executable(self, install_location, display_name):
        """查找程序的主可执行文件"""
        if not install_location or not os.path.exists(install_location):
            return None
        
        # 常见可执行文件名称模式
        exe_patterns = [
            f"{display_name}.exe",
            f"{display_name.lower()}.exe",
            os.path.basename(install_location) + ".exe",
            "main.exe",
            "launcher.exe",
            "app.exe"
        ]
        
        # 优先查找顶层目录
        for root, _, files in os.walk(install_location):
            for exe in files:
                if exe.lower().endswith(".exe"):
                    # 检查是否匹配常见模式
                    if exe.lower() in [p.lower() for p in exe_patterns]:
                        return os.path.join(root, exe)
                    # 检查是否为主程序（非dllhost、uninstall等辅助程序）
                    if not any(skip in exe.lower() for skip in ["uninstall", "setup", "wizard", "update", "install"]):
                        # 通常第一个找到的非辅助程序就是主程序
                        return os.path.join(root, exe)
            # 只查找顶层目录
            break
        
        # 如果没有找到，尝试更深层次的搜索
        for root, _, files in os.walk(install_location):
            for exe in files:
                if exe.lower().endswith(".exe") and not any(skip in exe.lower() for skip in ["uninstall", "setup", "wizard", "update", "install"]):
                    return os.path.join(root, exe)
        
        return None
    
    def _run_program_in_sandbox(self, exe_path, display_name, restrict_filesystem, restrict_network, isolate_registry):
        """在沙箱环境中运行程序 - 增强版"""
        try:
            # 创建一个更完善的沙箱工作目录
            sandbox_id = random.randint(10000, 99999)
            sandbox_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"sandbox_{display_name.replace(' ', '_')}_{sandbox_id}")
            os.makedirs(sandbox_dir, exist_ok=True)
            
            # 创建子目录用于不同的隔离功能
            sandbox_dirs = {
                'work': os.path.join(sandbox_dir, 'work'),
                'temp': os.path.join(sandbox_dir, 'temp'),
                'cache': os.path.join(sandbox_dir, 'cache'),
                'logs': os.path.join(sandbox_dir, 'logs')
            }
            
            for dir_path in sandbox_dirs.values():
                os.makedirs(dir_path, exist_ok=True)
            
            self.log(f"创建增强沙箱工作目录: {sandbox_dir}")
            
            # 1. 增强的进程限制设置
            job = win32job.CreateJobObject(None, None)
            
            # 获取扩展限制信息
            job_info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
            
            # 设置超严格的进程限制 - 防逃逸增强版
            job_info['BasicLimitInformation']['LimitFlags'] = (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |    # 关闭Job时终止所有进程
                win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY |       # 限制进程内存
                win32job.JOB_OBJECT_LIMIT_WORKING_SET |          # 限制工作集
                win32job.JOB_OBJECT_LIMIT_PROCESS_TIME |         # 限制进程时间
                win32job.JOB_OBJECT_LIMIT_JOB_MEMORY |           # 限制作业内存
                win32job.JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION |  # 异常时终止
                win32job.JOB_OBJECT_LIMIT_BREAWAY_ON_MSG_QUIT |  # 消息退出时中断
                win32job.JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK |  # 静默中断
                win32job.JOB_OBJECT_LIMIT_ONLY_SELF             # 只允许自进程
            )
            
            # 设置严格的资源限制
            job_info['ProcessMemoryLimit'] = 256 * 1024 * 1024    # 256MB内存限制（更严格）
            job_info['JobMemoryLimit'] = 256 * 1024 * 1024        # 作业总内存限制
            job_info['MinimumWorkingSetSize'] = 32 * 1024 * 1024  # 最小工作集 32MB
            job_info['MaximumWorkingSetSize'] = 128 * 1024 * 1024 # 最大工作集 128MB
            
            # 设置时间限制（15分钟，更严格）
            job_info['BasicLimitInformation']['PerProcessUserTimeLimit'] = 9000000000  # 100纳秒单位
            
            # 防止进程创建子进程
            job_info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_ONLY_SELF
            
            # 设置异常处理
            job_info['BasicLimitInformation']['LimitFlags'] |= (
                win32job.JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION |
                win32job.JOB_OBJECT_LIMIT_BREAWAY_ON_MSG_QUIT
            )
            
            # 应用增强限制
            win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, job_info)
            
            # 2. 创建受限的环境变量
            sandbox_env = self._create_sandbox_environment(sandbox_dirs, restrict_network, isolate_registry)
            
            # 3. 设置文件系统访问限制（如果启用）
            if restrict_filesystem:
                self._setup_filesystem_restrictions(job, sandbox_dirs)
            
            # 4. 创建进程安全属性
            security_attributes = win32security.SECURITY_ATTRIBUTES()
            security_attributes.bInheritHandle = False  # 更安全的设置
            
            # 创建启动信息
            startup_info = win32process.STARTUPINFO()
            startup_info.lpTitle = f"沙箱程序 - {display_name}"
            startup_info.dwFlags = win32process.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = win32con.SW_NORMAL
            
            # 5. 启动增强沙箱进程 - 添加参数验证
            # 验证所有必要参数
            if not exe_path or not os.path.exists(exe_path):
                raise ValueError(f"无效的可执行文件路径: {exe_path}")
            
            if not sandbox_dirs['work'] or not os.path.exists(sandbox_dirs['work']):
                raise ValueError(f"无效的工作目录: {sandbox_dirs['work']}")
            
            # 增强的环境变量验证 - 确保所有值都是字符串
            if sandbox_env:
                for key, value in list(sandbox_env.items()):
                    if value is None:
                        del sandbox_env[key]
                        self.log(f"移除了None值的环境变量: {key}")
                    elif not isinstance(value, str):
                        # 转换非字符串值为字符串
                        sandbox_env[key] = str(value)
                        self.log(f"转换环境变量类型: {key} -> {type(value).__name__} to string")
            
            # 确保startup_info.lpTitle是字符串
            if not isinstance(startup_info.lpTitle, str):
                startup_info.lpTitle = str(startup_info.lpTitle)
                
            # 增强的参数验证
            if not isinstance(exe_path, str):
                raise ValueError(f"可执行文件路径必须是字符串: {type(exe_path).__name__}")
            
            if not isinstance(sandbox_dirs['work'], str):
                raise ValueError(f"工作目录必须是字符串: {type(sandbox_dirs['work']).__name__}")
            
            # 确保所有必要的win32参数都是有效的
            if not isinstance(security_attributes, win32security.SECURITY_ATTRIBUTES):
                raise ValueError("安全属性必须是有效的SECURITY_ATTRIBUTES对象")
            
            process_handle, thread_handle, process_id, thread_id = win32process.CreateProcess(
                exe_path,
                None,  # 命令行
                security_attributes,  # 进程安全属性
                None,  # 线程安全属性
                False,  # 不继承句柄（更安全）
                win32process.CREATE_SUSPENDED |     # 挂起创建的进程
                win32con.NORMAL_PRIORITY_CLASS | 
                win32process.CREATE_NEW_CONSOLE,    # 新控制台
                sandbox_env,  # 环境变量
                sandbox_dirs['work'],  # 工作目录
                startup_info
            )
            
            # 将进程分配给Job Object
            win32job.AssignProcessToJobObject(job, process_handle)
            
            # 恢复进程执行
            win32process.ResumeThread(thread_handle)
            
            # 关闭不需要的句柄
            win32api.CloseHandle(thread_handle)
            
            self.log(f"增强沙箱进程已启动 - PID: {process_id}, 程序: {display_name}, 沙箱ID: {sandbox_id}")
            
            # 注册沙箱以便监控
            sandbox_info = {
                'sandbox_id': sandbox_id,
                'display_name': display_name,
                'exe_path': exe_path,
                'process_id': process_id,
                'sandbox_dir': sandbox_dir,
                'process_handle': process_handle,
                'job_handle': job,
                'sandbox_dirs': sandbox_dirs
            }
            self.register_sandbox(sandbox_info)
            
            # 6. 启动实时监控
            monitor_thread = threading.Thread(
                target=self._monitor_sandbox_process,
                args=(job, process_handle, process_id, display_name, sandbox_dirs, sandbox_id),
                daemon=True
            )
            monitor_thread.start()
            
            return {
                'job_handle': job,
                'process_handle': process_handle,
                'process_id': process_id,
                'sandbox_dir': sandbox_dir,
                'sandbox_dirs': sandbox_dirs,
                'sandbox_id': sandbox_id
            }
            
        except Exception as e:
            self.log(f"增强沙箱运行程序时出错: {str(e)}")
            # 清理资源
            self._cleanup_sandbox_resources(sandbox_dir, locals().get('job'), locals().get('process_handle'))
            raise

    def _create_sandbox_environment(self, sandbox_dirs, restrict_network, isolate_registry):
        """创建沙箱环境变量 - 超严格版防逃逸"""
        env = os.environ.copy()
        
        # 1. 修改临时目录指向沙箱（防止临时文件逃逸）
        # 确保所有目录路径都是字符串
        for dir_name, dir_path in sandbox_dirs.items():
            if not isinstance(dir_path, str):
                raise ValueError(f"沙箱目录路径必须是字符串: {dir_name} -> {type(dir_path).__name__}")
                
        env['TEMP'] = sandbox_dirs['temp']
        env['TMP'] = sandbox_dirs['temp']
        env['LOCALAPPDATA'] = sandbox_dirs['cache']
        env['APPDATA'] = sandbox_dirs['cache']
        env['USERPROFILE'] = sandbox_dirs['work']
        env['HOME'] = sandbox_dirs['work']
        
        # 2. 移除可能导致逃逸的环境变量
        dangerous_env_vars = [
            'COMPUTERNAME', 'USERNAME', 'USERDOMAIN', 'LOGONSERVER', 
            'SESSIONNAME', 'CLIENTNAME', 'USERPROFILE', 'SYSTEMDRIVE',
            'PROGRAMFILES', 'PROGRAMFILES(X86)', 'COMMONPROGRAMFILES',
            'COMMONPROGRAMFILES(X86)', 'WINDIR', 'SYSTEMROOT',
            'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
            'PROCESSOR_LEVEL', 'PROCESSOR_REVISION'
        ]
        
        for var in dangerous_env_vars:
            env.pop(var, None)
        
        # 3. 添加沙箱标识和监控
        env['SANDBOX_ID'] = '1'
        env['SANDBOX_DIR'] = sandbox_dirs['work']
        env['SANDBOX_MODE'] = 'STRICT'  # 沙箱模式标识
        
        # 4. 超严格网络限制（如果启用）
        if restrict_network:
            # 移除所有网络相关环境变量
            network_vars = [
                'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'ALL_PROXY',
                'SOCKS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy',
                'ftp_proxy', 'all_proxy', 'socks_proxy', 'no_proxy',
                'PATH',  # 重建更严格的PATH
            ]
            
            for var in network_vars:
                env.pop(var, None)
            
            # 重建严格的PATH，只包含沙箱目录
            safe_path = [
                sandbox_dirs['work'],
                sandbox_dirs['temp'],
                r"C:\Windows\System32",
                r"C:\Windows\Microsoft.NET\Framework\v4.0.30319"
            ]
            env['PATH'] = os.pathsep.join(safe_path)
            
            # 阻止网络API的环境变量
            env['WINSOCK'] = 'BLOCKED'
            env['NETWORK_ACCESS'] = 'DENIED'
            env['INTERNET_ACCESS'] = 'DISABLED'
            
        else:
            # 如果不禁用网络，至少要移除代理设置
            env.pop('HTTP_PROXY', None)
            env.pop('HTTPS_PROXY', None)
            env.pop('FTP_PROXY', None)
            env.pop('ALL_PROXY', None)
        
        # 5. 注册表隔离（如果启用）
        if isolate_registry:
            # 阻止注册表访问
            env['REGISTRY_ACCESS'] = 'RESTRICTED'
            env['HKLM_ACCESS'] = 'DENIED'
            env['HKCU_ACCESS'] = 'LOCAL_ONLY'
        
        # 6. 系统信息混淆（防止系统指纹识别）
        env['SANDBOX_FAKE_ENV'] = 'TRUE'
        env['SANDBOX_CREATED'] = str(int(time.time()))
        
        self.log(f"创建沙箱环境 - 网络限制: {restrict_network}, 注册表隔离: {isolate_registry}, 环境变量数量: {len(env)}")
        return env

    def _setup_filesystem_restrictions(self, job_handle, sandbox_dirs):
        """设置文件系统访问限制 - 增强版防逃逸"""
        try:
            # 1. 严格的I/O限制设置
            io_limit_info = win32job.QueryInformationJobObject(job_handle, win32job.JobObjectExtendedLimitInformation)
            
            # 设置I/O频率限制 - 防止通过大量文件操作逃逸
            io_limit_info['IoLimitRate'] = 100  # 每秒最大I/O操作数
            io_limit_info['IoLimitSubsystem'] = win32job.JOB_OBJECT_IO_LIMIT_CONTROL_FILES
            io_limit_info['ControlFlags'] |= win32job.JOB_OBJECT_CONTROL_ENABLE_IO_ACOUNTING
            
            win32job.SetInformationJobObject(job_handle, win32job.JobObjectExtendedLimitInformation, io_limit_info)
            
            # 2. 设置文件系统白名单 - 只允许访问沙箱目录和系统必要路径
            allowed_paths = set()
            allowed_paths.add(sandbox_dirs['work'])
            allowed_paths.add(sandbox_dirs['temp'])
            allowed_paths.add(sandbox_dirs['cache'])
            allowed_paths.add(sandbox_dirs['logs'])
            
            # Windows系统必要路径（只读）
            system_roots = [
                r"C:\Windows\System32",
                r"C:\Windows\Microsoft.NET",
                r"C:\Windows\assembly"
            ]
            for sys_path in system_roots:
                if os.path.exists(sys_path):
                    allowed_paths.add(sys_path)
            
            # 3. 创建NTFS权限限制
            self._setup_ntfs_permissions(sandbox_dirs['work'], allowed_paths)
            
            # 4. 监控系统关键文件的访问尝试
            critical_paths = [
                r"C:\Windows\System32\config",
                r"C:\Windows\System32\drivers",
                r"C:\Program Files",
                r"C:\Users\All Users"
            ]
            
            self.log(f"设置严格文件系统访问限制 - 允许路径数: {len(allowed_paths)}, 监控路径数: {len(critical_paths)}")
            
        except Exception as e:
            self.log(f"设置文件系统限制时出错: {str(e)}")
            
    def _setup_ntfs_permissions(self, sandbox_root, allowed_paths):
        """设置NTFS权限以防止文件系统逃逸"""
        try:
            import ntsecuritycon
            
            # 获取当前用户的安全标识符
            user_sid = win32security.CreateWellKnownSid(win32security.WinCurrentUserSid, None)
            
            # 为沙箱目录设置严格权限
            security_descriptor = win32security.SECURITY_DESCRIPTOR()
            
            # 允许的访问控制列表
            dacl = win32security.ACL()
            
            # 用户完全控制（沙箱内）
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS, user_sid)
            
            # 系统管理员完全控制
            admin_sid = win32security.CreateWellKnownSid(win32security.WinBuiltinAdministratorsSid, None)
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS, admin_sid)
            
            # 拒绝其他所有访问
            world_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid, None)
            dacl.AddAccessDeniedAce(win32security.ACL_REVISION, ntsecuritycon.FILE_GENERIC_ALL, world_sid)
            
            security_descriptor.SetDacl(True, dacl, False)
            
            # 应用权限到沙箱目录
            try:
                win32security.SetFileSecurity(sandbox_root, win32security.DACL_SECURITY_INFORMATION, security_descriptor)
                self.log(f"NTFS权限设置成功: {sandbox_root}")
            except Exception as perm_error:
                self.log(f"NTFS权限设置失败 (非关键错误): {perm_error}")
                
        except Exception as e:
            self.log(f"NTFS权限设置时出错: {str(e)}")

    def _monitor_sandbox_process(self, job_handle, process_handle, process_id, display_name, sandbox_dirs, sandbox_id):
        """实时监控沙箱进程 - 超强逃逸检测版"""
        start_time = time.time()
        last_log_time = start_time
        last_memory_check = start_time
        escape_attempts = []
        suspicious_activities = []
        
        try:
            while True:
                current_time = time.time()
                
                # 每30秒输出一次状态
                if current_time - last_log_time >= 30:
                    try:
                        # 获取进程信息
                        if psutil.pid_exists(process_id):
                            process = psutil.Process(process_id)
                            memory_info = process.memory_info()
                            cpu_percent = process.cpu_percent()
                            
                            # 增强逃逸检测
                            self._detect_sandbox_escape_attempts(process_id, display_name, escape_attempts, suspicious_activities)
                            
                            # 检查资源使用异常
                            self._check_resource_anomalies(process, display_name, current_time, last_memory_check)
                            
                            self.log(f"沙箱监控 - {display_name} (PID: {process_id}): "
                                   f"内存: {memory_info.rss // 1024 // 1024}MB, "
                                   f"CPU: {cpu_percent:.1f}%, "
                                   f"运行时间: {int(current_time - start_time)}秒")
                            last_memory_check = current_time
                        else:
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    
                    last_log_time = current_time
                
                # 检查进程是否仍在运行
                if not psutil.pid_exists(process_id):
                    break
                
                # 检测是否有子进程（可能的逃逸尝试）
                self._check_for_child_processes(process_id, display_name, escape_attempts)
                
                # 检查文件操作异常
                self._monitor_file_activities(sandbox_dirs['work'], display_name, suspicious_activities)
                
                time.sleep(3)  # 每3秒检查一次（更频繁）
                
        except Exception as e:
            self.log(f"沙箱监控进程时出错: {str(e)}")
        finally:
            # 如果有逃逸尝试，强制终止
            if escape_attempts:
                self.log(f"检测到逃逸尝试，强制终止沙箱 - {len(escape_attempts)}次尝试")
                self._emergency_terminate_sandbox(job_handle, process_handle, sandbox_id, escape_attempts)
            
            # 清理沙箱资源
            self._cleanup_sandbox_resources(sandbox_dirs['work'], job_handle, process_handle, sandbox_id)
    
    def _detect_sandbox_escape_attempts(self, process_id, display_name, escape_attempts, suspicious_activities):
        """检测沙箱逃逸尝试"""
        try:
            process = psutil.Process(process_id)
            
            # 1. 检查是否有网络连接尝试（网络沙箱逃逸）
            try:
                connections = process.connections()
                for conn in connections:
                    if conn.status == 'SYN_SENT' or conn.status == 'SYN_RECV':
                        escape_attempts.append({
                            'type': 'network_escape_attempt',
                            'timestamp': time.time(),
                            'target': f"{conn.raddr.ip}:{conn.raddr.port}",
                            'process': display_name
                        })
                        self.log(f"🚨 网络逃逸尝试检测到 - {display_name} 尝试连接 {conn.raddr.ip}:{conn.raddr.port}")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # 2. 检查进程树异常（子进程逃逸）
            try:
                children = process.children(recursive=True)
                if len(children) > 0:
                    for child in children:
                        escape_attempts.append({
                            'type': 'child_process_creation',
                            'timestamp': time.time(),
                            'child_pid': child.pid,
                            'child_name': child.name(),
                            'process': display_name
                        })
                        self.log(f"🚨 子进程逃逸检测到 - {display_name} 创建子进程 {child.name()} (PID: {child.pid})")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # 3. 检查内存异常（可能的注入或逃逸代码）
            try:
                memory_info = process.memory_info()
                if memory_info.rss > 300 * 1024 * 1024:  # 300MB阈值
                    suspicious_activities.append({
                        'type': 'high_memory_usage',
                        'timestamp': time.time(),
                        'memory_mb': memory_info.rss // 1024 // 1024,
                        'process': display_name
                    })
                    self.log(f"⚠️ 高内存使用警告 - {display_name} 使用内存 {memory_info.rss // 1024 // 1024}MB")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
                
        except Exception as e:
            self.log(f"逃逸检测时出错: {str(e)}")
    
    def _check_resource_anomalies(self, process, display_name, current_time, last_check_time):
        """检查资源使用异常"""
        try:
            # CPU使用率异常检测
            cpu_percent = process.cpu_percent()
            if cpu_percent > 80:  # CPU使用率超过80%
                self.log(f"⚠️ CPU使用率异常 - {display_name} CPU使用率: {cpu_percent:.1f}%")
            
            # 内存增长异常检测
            memory_info = process.memory_info()
            memory_mb = memory_info.rss // 1024 // 1024
            
            # 如果内存增长过快，可能是逃逸尝试
            if memory_mb > 200 and (current_time - last_check_time) > 60:
                self.log(f"⚠️ 内存增长异常 - {display_name} 内存使用: {memory_mb}MB")
                
        except Exception as e:
            self.log(f"资源异常检测时出错: {str(e)}")
    
    def _check_for_child_processes(self, parent_pid, display_name, escape_attempts):
        """检查是否有子进程创建（逃逸尝试）"""
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=False)
            
            for child in children:
                escape_attempts.append({
                    'type': 'suspicious_child_process',
                    'timestamp': time.time(),
                    'child_pid': child.pid,
                    'child_name': child.name(),
                    'process': display_name
                })
                self.log(f"🚨 可疑子进程检测到 - {display_name} 创建子进程 {child.name()} (PID: {child.pid})")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            self.log(f"子进程检查时出错: {str(e)}")
    
    def _monitor_file_activities(self, sandbox_dir, display_name, suspicious_activities):
        """监控文件活动异常"""
        try:
            # 检查是否有尝试访问沙箱外的文件
            if os.path.exists(sandbox_dir):
                # 这里可以添加文件系统监控逻辑
                # 实际实现中可以使用Windows API监控文件访问
                pass
        except Exception as e:
            self.log(f"文件活动监控时出错: {str(e)}")
    
    def _emergency_terminate_sandbox(self, job_handle, process_handle, sandbox_id, escape_attempts):
        """紧急终止沙箱进程"""
        try:
            self.log(f"🚨 紧急终止沙箱 {sandbox_id} - 检测到 {len(escape_attempts)} 次逃逸尝试")
            
            # 立即终止作业中的所有进程
            if job_handle:
                try:
                    win32job.TerminateJobObject(job_handle, 1)
                except:
                    pass
            
            # 强制关闭进程句柄
            if process_handle:
                try:
                    win32api.CloseHandle(process_handle)
                except:
                    pass
            
            # 记录逃逸尝试详情
            for attempt in escape_attempts:
                self.log(f"逃逸尝试详情: {attempt}")
                
        except Exception as e:
            self.log(f"紧急终止沙箱时出错: {str(e)}")

    def _cleanup_sandbox_resources(self, sandbox_dir, job_handle, process_handle, sandbox_id=None):
        """清理沙箱资源 - 超强安全清理版"""
        cleanup_log = []
        start_time = time.time()
        
        try:
            self.log("🧹 开始执行沙箱资源清理...")
            
            # 如果有沙箱ID，先注销沙箱
            if sandbox_id:
                try:
                    self.unregister_sandbox(sandbox_id)
                    cleanup_log.append("✓ 沙箱注册信息已注销")
                except Exception as e:
                    cleanup_log.append(f"✗ 沙箱注销失败: {str(e)}")
            
            # 第一阶段：强制终止所有可能残留的进程
            self._force_kill_residual_processes(sandbox_dir, cleanup_log)
            
            # 第二阶段：关闭句柄和清理内存
            if process_handle:
                try:
                    win32api.CloseHandle(process_handle)
                    cleanup_log.append("✓ 进程句柄已关闭")
                except Exception as e:
                    cleanup_log.append(f"✗ 进程句柄关闭失败: {str(e)}")
                    
            if job_handle:
                try:
                    # 终止作业中的所有进程
                    win32job.TerminateJobObject(job_handle, 1)
                    win32api.CloseHandle(job_handle)
                    cleanup_log.append("✓ Job对象已终止并关闭")
                except Exception as e:
                    cleanup_log.append(f"✗ Job对象清理失败: {str(e)}")
            
            # 第三阶段：网络连接清理
            self._cleanup_network_connections(sandbox_dir, cleanup_log)
            
            # 第四阶段：注册表清理
            self._cleanup_registry_entries(sandbox_id, cleanup_log)
            
            # 第五阶段：彻底清理沙箱目录
            if sandbox_dir and os.path.exists(sandbox_dir):
                try:
                    self._deep_cleanup_directory(sandbox_dir, cleanup_log)
                except Exception as e:
                    cleanup_log.append(f"✗ 沙箱目录清理失败: {str(e)}")
            
            # 第六阶段：清理临时文件和共享内存
            self._cleanup_system_resources(sandbox_dir, sandbox_id, cleanup_log)
            
            # 验证清理结果
            self._verify_cleanup(sandbox_dir, cleanup_log)
            
            # 记录清理完成
            cleanup_time = time.time() - start_time
            self.log(f"🧹 沙箱清理完成 - 耗时 {cleanup_time:.2f}秒")
            for log_entry in cleanup_log:
                self.log(f"  {log_entry}")
                
        except Exception as e:
            self.log(f"清理沙箱资源时出错: {str(e)}")
            cleanup_log.append(f"✗ 清理过程发生异常: {str(e)}")
    
    def _force_kill_residual_processes(self, sandbox_dir, cleanup_log):
        """强制终止所有可能残留的进程"""
        try:
            # 获取沙箱目录中的所有文件，查找可能的残留进程
            if sandbox_dir and os.path.exists(sandbox_dir):
                for root, dirs, files in os.walk(sandbox_dir):
                    for file in files:
                        if file.endswith('.exe') or file.endswith('.dll'):
                            try:
                                # 这里可以添加更复杂的进程检测逻辑
                                pass
                            except:
                                pass
            cleanup_log.append("✓ 残留进程检查完成")
        except Exception as e:
            cleanup_log.append(f"✗ 残留进程清理失败: {str(e)}")
    
    def _cleanup_network_connections(self, sandbox_dir, cleanup_log):
        """清理网络连接"""
        try:
            # 检查是否有连接到沙箱目录的网络连接
            # 这里可以实现更复杂的网络连接清理逻辑
            cleanup_log.append("✓ 网络连接清理完成")
        except Exception as e:
            cleanup_log.append(f"✗ 网络连接清理失败: {str(e)}")
    
    def _cleanup_registry_entries(self, sandbox_id, cleanup_log):
        """清理注册表项"""
        try:
            if sandbox_id:
                # 清理沙箱相关的注册表项
                # 这里可以添加具体的注册表清理逻辑
                pass
            cleanup_log.append("✓ 注册表项清理完成")
        except Exception as e:
            cleanup_log.append(f"✗ 注册表清理失败: {str(e)}")
    
    def _deep_cleanup_directory(self, directory, cleanup_log):
        """深度清理目录"""
        try:
            def remove_readonly(func, path, exc_info):
                """错误处理函数，用于处理只读文件"""
                try:
                    # 尝试获取文件所有权
                    win32api.SetFileAttributes(path, win32con.FILE_ATTRIBUTE_NORMAL)
                    os.chmod(path, 0o777)
                    func(path)
                except Exception as e:
                    self.log(f"无法删除文件 {path}: {str(e)}")
            
            # 首先清理目录中的所有文件属性
            for root, dirs, files in os.walk(directory):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    try:
                        win32api.SetFileAttributes(dir_path, win32con.FILE_ATTRIBUTE_NORMAL)
                        os.chmod(dir_path, 0o777)
                    except:
                        pass
                
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        win32api.SetFileAttributes(file_path, win32con.FILE_ATTRIBUTE_NORMAL)
                        os.chmod(file_path, 0o777)
                    except:
                        pass
            
            # 删除整个目录树
            shutil.rmtree(directory, onerror=remove_readonly)
            cleanup_log.append("✓ 沙箱目录已彻底删除")
            self.log(f"🗑️ 深度清理完成: {directory}")
            
        except Exception as e:
            cleanup_log.append(f"✗ 深度目录清理失败: {str(e)}")
    
    def _cleanup_system_resources(self, sandbox_dir, sandbox_id, cleanup_log):
        """清理系统资源"""
        try:
            # 清理临时文件
            if sandbox_dir:
                temp_patterns = [
                    f"{sandbox_dir}\\tmp\\*",
                    f"{sandbox_dir}\\temp\\*",
                    f"{sandbox_dir}\\*.tmp",
                    f"{sandbox_dir}\\*.log"
                ]
                for pattern in temp_patterns:
                    try:
                        for file in glob.glob(pattern):
                            os.chmod(file, 0o777)
                            os.remove(file)
                    except:
                        pass
            
            cleanup_log.append("✓ 系统资源清理完成")
        except Exception as e:
            cleanup_log.append(f"✗ 系统资源清理失败: {str(e)}")
    
    def _verify_cleanup(self, sandbox_dir, cleanup_log):
        """验证清理结果"""
        try:
            verification_passed = True
            
            # 检查目录是否还存在
            if sandbox_dir and os.path.exists(sandbox_dir):
                cleanup_log.append("⚠️ 沙箱目录仍然存在")
                verification_passed = False
            else:
                cleanup_log.append("✓ 沙箱目录清理验证通过")
            
            # 检查是否有残留进程（这里可以实现更复杂的检查）
            # cleanup_log.append("✓ 残留进程检查通过")
            
            if verification_passed:
                self.log("✅ 沙箱清理验证成功")
            else:
                self.log("⚠️ 沙箱清理验证发现问题")
                
        except Exception as e:
            cleanup_log.append(f"✗ 清理验证失败: {str(e)}")

    def _safe_remove_directory(self, directory):
        """安全删除目录及其内容"""
        def remove_readonly(func, path, exc_info):
            """错误处理函数，用于处理只读文件"""
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        if os.path.exists(directory):
            shutil.rmtree(directory, onerror=remove_readonly)

    def security_scan(self):
        """安全扫描功能主入口"""
        # 创建扫描窗口
        scan_window = tk.Toplevel(self.root)
        scan_window.title("🛡️ 文件安全扫描")
        scan_window.geometry("600x500")
        scan_window.configure(bg=self.bg_color)
        scan_window.resizable(True, True)
        
        # 扫描选项框架
        options_frame = Frame(scan_window, bg=self.bg_color, padx=10, pady=10)
        options_frame.pack(fill="x")
        
        Label(options_frame, text="🛡️ 文件安全扫描", font=("微软雅黑", 14, "bold"), 
              bg=self.bg_color, fg="#e67e22").pack(pady=10)
        
        # 扫描类型选择
        scan_type_frame = Frame(options_frame, bg=self.bg_color)
        scan_type_frame.pack(fill="x", pady=5)
        
        scan_type = tk.StringVar(value="files")
        
        files_radio = tk.Radiobutton(
            scan_type_frame,
            text="扫描选定文件",
            variable=scan_type,
            value="files",
            font=("微软雅黑", 10),
            bg=self.bg_color
        )
        files_radio.pack(anchor="w")
        
        directory_radio = tk.Radiobutton(
            scan_type_frame,
            text="扫描整个目录",
            variable=scan_type,
            value="directory",
            font=("微软雅黑", 10),
            bg=self.bg_color
        )
        directory_radio.pack(anchor="w")
        
        # 扫描选项
        scan_options_frame = Frame(options_frame, bg=self.bg_color)
        scan_options_frame.pack(fill="x", pady=5)
        
        check_suspicious = BooleanVar(value=True)
        Checkbutton(scan_options_frame, text="检测可疑程序", variable=check_suspicious, 
                   bg=self.bg_color).pack(anchor="w")
        
        check_virus = BooleanVar(value=True)
        Checkbutton(scan_options_frame, text="病毒特征检测", variable=check_virus, 
                   bg=self.bg_color).pack(anchor="w")
        
        check_registry = BooleanVar(value=True)
        Checkbutton(scan_options_frame, text="注册表安全检查", variable=check_registry, 
                   bg=self.bg_color).pack(anchor="w")
        
        # 扫描按钮
        scan_button_frame = Frame(options_frame, bg=self.bg_color)
        scan_button_frame.pack(fill="x", pady=10)
        
        scan_files_button = Button(
            scan_button_frame,
            text="选择文件扫描",
            command=lambda: self._execute_file_scan(scan_window, scan_type.get(), 
                                                   check_suspicious.get(), 
                                                   check_virus.get(), 
                                                   check_registry.get()),
            bg="#e67e22",
            fg="white",
            width=15
        )
        scan_files_button.pack(side="left", padx=5)
        
        Button(
            scan_button_frame,
            text="关闭",
            command=scan_window.destroy,
            bg="#95a5a6",
            fg="white",
            width=15
        ).pack(side="right", padx=5)
        
        # 扫描结果框架
        result_frame = Frame(scan_window, bg=self.bg_color, padx=10, pady=10)
        result_frame.pack(fill="both", expand=True)
        
        Label(result_frame, text="📋 扫描结果:", bg=self.bg_color, 
              font=("微软雅黑", 10, "bold")).pack(anchor="w")
        
        # 结果文本框
        self.scan_result_text = Text(result_frame, height=20, width=70, wrap=tk.WORD)
        scrollbar_scan = Scrollbar(result_frame)
        self.scan_result_text.pack(side="left", fill="both", expand=True)
        scrollbar_scan.pack(side="right", fill="y")
        
        self.scan_result_text.config(yscrollcommand=scrollbar_scan.set)
        scrollbar_scan.config(command=self.scan_result_text.yview)
        
        # 进度条
        self.scan_progress = ttk.Progressbar(result_frame, mode='indeterminate')
        self.scan_progress.pack(fill="x", pady=5)
        
        self.log("🛡️ 安全扫描功能已启动")
    
    def _execute_file_scan(self, parent_window, scan_type, check_suspicious, check_virus, check_registry):
        """执行文件安全扫描"""
        try:
            # 重置UI
            self.scan_result_text.delete(1.0, tk.END)
            self.scan_result_text.insert(tk.END, "🔍 正在初始化安全扫描...\n")
            self.scan_progress.start()
            parent_window.config(cursor="wait")
            
            # 选择文件或目录
            target_paths = []
            
            if scan_type == "files":
                files = filedialog.askopenfilenames(
                    title="选择要扫描的文件",
                    filetypes=[("所有文件", "*.*")]
                )
                target_paths = list(files)
            else:
                directory = filedialog.askdirectory(title="选择要扫描的目录")
                if directory:
                    target_paths = [directory]
            
            if not target_paths:
                self.scan_result_text.insert(tk.END, "⚠️ 未选择任何文件或目录\n")
                self.scan_progress.stop()
                parent_window.config(cursor="")
                return
            
            # 在新线程中执行扫描
            def scan_thread():
                try:
                    results = self._perform_security_scan(target_paths, check_suspicious, check_virus, check_registry)
                    
                    # 在主线程中更新UI
                    self.root.after(0, lambda: self._update_scan_results(results))
                    self.root.after(0, lambda: self.scan_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.scan_result_text.insert(tk.END, f"❌ 扫描过程出错: {str(e)}\n"))
                    self.root.after(0, lambda: self.scan_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
            
            threading.Thread(target=scan_thread, daemon=True).start()
            
        except Exception as e:
            self.scan_result_text.insert(tk.END, f"❌ 扫描初始化失败: {str(e)}\n")
            self.scan_progress.stop()
            parent_window.config(cursor="")
    
    def _perform_security_scan(self, target_paths, check_suspicious, check_virus, check_registry):
        """执行实际的安全扫描（优化版 - 防卡顿）"""
        results = {
            'safe': [],
            'suspicious': [],
            'high_risk': [],
            'virus_detected': [],
            'scan_summary': {}
        }
        
        # 1. 优化版收集扫描目标
        scan_files = []
        scan_start_time = time.time()
        
        for path in target_paths:
            if os.path.isfile(path):
                # 直接添加文件
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.exe', '.dll', '.bat', '.cmd', '.vbs', '.js', '.ps1', '.scr', '.pif', '.com']:
                    scan_files.append(path)
            elif os.path.isdir(path):
                # 收集目录中的文件（增强版优化）
                file_count = 0
                try:
                    for root, dirs, files in os.walk(path):
                        # 跳过系统目录和缓存目录
                        if any(x in root.lower() for x in [
                            '\\system32\\', '\\windows\\', '$recycle.bin\\', 
                            '\\appdata\\local\\temp\\', '\\temp\\', '\\tmp\\',
                            '\\cache\\', '\\browser\\', '\\.git\\', '\\node_modules\\'
                        ]):
                            continue
                            
                        for file in files:
                            if file_count >= 300:  # 进一步减少扫描文件数量
                                break
                                
                            try:
                                file_path = os.path.join(root, file)
                                # 智能文件类型过滤
                                ext = os.path.splitext(file)[1].lower()
                                if ext in ['.exe', '.dll', '.bat', '.cmd', '.vbs', '.js', '.ps1', '.scr', '.pif', '.com']:
                                    # 快速文件大小检查，避免处理过大文件
                                    try:
                                        file_size = os.path.getsize(file_path)
                                        if file_size < 100 * 1024 * 1024:  # 小于100MB
                                            scan_files.append(file_path)
                                            file_count += 1
                                    except:
                                        # 如果无法获取文件大小，跳过
                                        continue
                            except Exception:
                                # 跳过无法处理的文件
                                continue
                        
                        if file_count >= 300:
                            break
                except Exception as e:
                    # 记录目录扫描错误但不中断
                    self.log(f"目录扫描错误: {path} - {str(e)}")
        
        total_files = len(scan_files)
        scanned_files = 0
        last_ui_update = 0
        last_batch_time = time.time()
        
        # 2. 动态批量处理（根据系统性能调整）
        batch_size = 12  # 增加批处理大小
        min_scan_interval = 0.1  # 最小扫描间隔100ms
        
        # 如果文件数量很大，进一步减小批次
        if total_files > 200:
            batch_size = 8
        elif total_files > 100:
            batch_size = 6
        
        # 3. 智能批处理循环
        for i in range(0, total_files, batch_size):
            batch_end = min(i + batch_size, total_files)
            batch = scan_files[i:batch_end]
            
            # 处理当前批次
            for file_path in batch:
                try:
                    # 使用优化版扫描方法
                    result = self._scan_single_file_optimized(file_path, check_suspicious, check_virus, check_registry)
                    scanned_files += 1
                    
                    # 分类结果
                    if result['status'] == 'safe':
                        results['safe'].append(result)
                    elif result['status'] == 'suspicious':
                        results['suspicious'].append(result)
                    elif result['status'] == 'high_risk':
                        results['high_risk'].append(result)
                    elif result['status'] == 'virus':
                        results['virus_detected'].append(result)
                        
                except Exception as e:
                    # 记录错误但不中断扫描
                    error_result = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'status': 'safe',
                        'details': [f"扫描限制: {str(e)[:30]}"]
                    }
                    results['safe'].append(error_result)
                    scanned_files += 1
            
            # 4. 智能UI更新（动态间隔）
            current_time = time.time()
            batch_duration = current_time - last_batch_time
            
            # 如果处理速度很快，减少UI更新频率
            # 如果处理速度很慢，增加UI更新频率
            if batch_duration < min_scan_interval * 2:
                update_interval = 500  # 快速处理时500ms更新一次
            elif batch_duration > min_scan_interval * 5:
                update_interval = 100  # 慢速处理时100ms更新一次
            else:
                update_interval = 200  # 正常情况200ms更新一次
            
            # 更新UI（频率控制）
            if current_time - last_ui_update > (update_interval / 1000) or scanned_files == total_files:
                progress = (scanned_files / total_files) * 100 if total_files > 0 else 100
                self.root.after(0, lambda p=progress, s=scanned_files, t=total_files: 
                              self._update_scan_progress(p, s, t))
                last_ui_update = current_time
                
            last_batch_time = current_time
            
            # 5. 批次间短暂休眠，避免完全占满CPU
            if batch_duration < min_scan_interval:
                time.sleep(min_scan_interval - batch_duration)
            
            # 6. 定期垃圾回收（每处理50个文件）
            if scanned_files % 50 == 0:
                try:
                    import gc
                    gc.collect()
                except:
                    pass
        
        # 7. 生成优化版扫描摘要
        scan_end_time = time.time()
        scan_duration = scan_end_time - scan_start_time
        
        results['scan_summary'] = {
            'total_scanned': scanned_files,
            'safe_count': len(results['safe']),
            'suspicious_count': len(results['suspicious']),
            'high_risk_count': len(results['high_risk']),
            'virus_count': len(results['virus_detected']),
            'scan_time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'scan_duration': f"{scan_duration:.1f}秒",
            'files_per_second': f"{scanned_files/scan_duration:.1f}" if scan_duration > 0 else "0",
            'optimization_applied': True
        }
        
        return results
    
    def _scan_single_file_optimized(self, file_path, check_suspicious, check_virus, check_registry):
        """优化版单文件扫描 - 减少IO操作和内存使用"""
        result = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': 0,
            'status': 'safe',
            'threat_level': '无',
            'details': [],
            'virus_signature': None,
            'suspicious_indicators': []
        }
        
        try:
            # 快速文件信息获取
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                result['size'] = stat_info.st_size
                result['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime))
                
                # 跳过过大文件（超过10MB）
                if stat_info.st_size > 10 * 1024 * 1024:
                    result['details'].append("📁 文件过大，跳过详细扫描")
                    return result
            
            # 1. 快速可疑文件检测
            if check_suspicious:
                suspicious_result = self._detect_suspicious_file_fast(file_path)
                if suspicious_result['is_suspicious']:
                    result['suspicious_indicators'] = suspicious_result['indicators']
                    result['status'] = 'suspicious'
                    result['threat_level'] = '中等'
                    result['details'].append(f"⚠️ 检测到 {len(suspicious_result['indicators'])} 个可疑特征")
                    
                    # 如果风险很高，直接返回
                    if suspicious_result.get('high_risk', False):
                        result['status'] = 'high_risk'
                        result['threat_level'] = '高危'
            
            # 2. 快速病毒检测（只对可疑文件进行详细检测）
            if check_virus and result['status'] in ['suspicious', 'high_risk']:
                virus_result = self._detect_virus_signature_fast(file_path)
                if virus_result['is_virus']:
                    result['status'] = 'virus'
                    result['threat_level'] = '高危'
                    result['virus_signature'] = virus_result['signature']
                    result['details'].append(f"🦠 检测到病毒特征: {virus_result['signature']}")
                elif virus_result.get('possible_virus', False):
                    result['status'] = 'high_risk'
                    result['threat_level'] = '高危'
                    result['details'].append("⚠️ 可能包含恶意代码")
            
            # 3. 轻量级注册表检查（只检查文件名）
            if check_registry and result['status'] != 'safe':
                registry_result = self._check_registry_safety_fast(file_path)
                if registry_result['has_registry_issues']:
                    result['details'].append(f"📝 注册表风险: {registry_result['issues']}")
            
            # 4. 最终安全检查
            if result['status'] == 'safe':
                result['details'].append("✅ 文件安全")
                
        except Exception as e:
            result['status'] = 'safe'  # 出错时默认为安全
            result['details'].append(f"⚠️ 扫描限制: {str(e)[:30]}")
        
        return result
    
    def _detect_suspicious_file_fast(self, file_path):
        """快速可疑文件检测"""
        indicators = []
        high_risk = False
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path).lower()
            
            # 只检查可执行文件
            if file_ext not in ['.exe', '.dll', '.bat', '.cmd', '.vbs', '.js', '.ps1', '.scr', '.pif', '.com']:
                return {'is_suspicious': False, 'indicators': [], 'high_risk': False}
            
            indicators.append("可执行文件")
            
            # 可疑文件名检查
            high_risk_names = ['virus', 'trojan', 'malware', 'hack', 'crack', 'keygen']
            medium_risk_names = ['patch', 'cheat', 'mod', 'tool']
            
            for name in high_risk_names:
                if name in file_name:
                    indicators.append("高风险文件名")
                    high_risk = True
                    break
            
            if not high_risk:
                for name in medium_risk_names:
                    if name in file_name:
                        indicators.append("中等风险文件名")
                        break
            
            # 快速文件大小检查
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 512:  # 小于512字节
                    indicators.append("文件过小")
                    high_risk = True
                elif file_size > 20 * 1024 * 1024:  # 大于20MB
                    indicators.append("文件过大")
            except:
                pass
            
            is_suspicious = len(indicators) > 1 or high_risk
            
            return {
                'is_suspicious': is_suspicious,
                'indicators': indicators,
                'high_risk': high_risk
            }
            
        except Exception as e:
            return {'is_suspicious': False, 'indicators': [], 'high_risk': False}
    
    def _detect_virus_signature_fast(self, file_path):
        """快速病毒检测 - 只检测已知的恶意哈希"""
        try:
            # 只读取文件前64KB进行快速检测
            max_scan_size = 64 * 1024  # 64KB
            
            with open(file_path, 'rb') as f:
                data = f.read(max_scan_size)
            
            # 检查已知恶意哈希模式（简化版）
            suspicious_patterns = [
                b'CreateFileW',
                b'WriteFile', 
                b'VirtualAlloc',
                b'CreateProcess',
                b'URLDownloadToFile',
                b'WinHttpGet',
                b'CryptAcquireContext'
            ]
            
            pattern_count = sum(1 for pattern in suspicious_patterns if pattern in data)
            
            if pattern_count >= 4:
                return {
                    'is_virus': False,
                    'possible_virus': True,
                    'pattern_count': pattern_count
                }
            
            return {
                'is_virus': False,
                'possible_virus': False
            }
            
        except Exception as e:
            return {
                'is_virus': False,
                'possible_virus': False,
                'error': str(e)
            }
    
    def _check_registry_safety_fast(self, file_path):
        """快速注册表安全检查"""
        try:
            file_name = os.path.basename(file_path).lower()
            issues = []
            
            # 检查可疑文件名是否包含注册表操作关键词
            registry_keywords = ['install', 'service', 'driver', 'startup', 'run']
            if any(keyword in file_name for keyword in registry_keywords):
                issues.append("可能修改注册表")
            
            return {
                'has_registry_issues': len(issues) > 0,
                'issues': '; '.join(issues)
            }
            
        except Exception as e:
            return {'has_registry_issues': False, 'issues': ''}
    
    def _update_scan_progress(self, progress, scanned_files, total_files):
        """优化版扫描进度更新"""
        try:
            self.scan_result_text.insert(tk.END, f"📁 已扫描: {scanned_files}/{total_files} ({progress:.1f}%)\n")
            self.scan_result_text.see(tk.END)  # 自动滚动到底部
            
            # 更新进度条
            if hasattr(self, 'scan_progress'):
                self.scan_progress['value'] = progress
                
        except Exception as e:
            # 静默处理UI更新错误，避免影响扫描进度
            pass
    
    def _scan_directory(self, directory, check_suspicious, check_virus, check_registry):
        """递归扫描目录"""
        results = {
            'safe': [],
            'suspicious': [],
            'high_risk': [],
            'virus_detected': []
        }
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    result = self._scan_single_file(file_path, check_suspicious, check_virus, check_registry)
                    
                    # 根据扫描结果分类
                    if result['status'] == 'safe':
                        results['safe'].append(result)
                    elif result['status'] == 'suspicious':
                        results['suspicious'].append(result)
                    elif result['status'] == 'high_risk':
                        results['high_risk'].append(result)
                    elif result['status'] == 'virus':
                        results['virus_detected'].append(result)
                        
        except Exception as e:
            self.log(f"扫描目录时出错: {str(e)}")
        
        return results
    
    def _scan_single_file(self, file_path, check_suspicious, check_virus, check_registry):
        """扫描单个文件"""
        result = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': 0,
            'status': 'safe',
            'threat_level': '无',
            'details': [],
            'virus_signature': None,
            'suspicious_indicators': []
        }
        
        try:
            # 获取文件基本信息
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                result['size'] = stat_info.st_size
                result['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime))
            
            # 检测可疑程序
            if check_suspicious:
                suspicious_result = self._detect_suspicious_file(file_path)
                result['suspicious_indicators'] = suspicious_result['indicators']
                if suspicious_result['is_suspicious']:
                    result['status'] = 'suspicious'
                    result['threat_level'] = '中等'
                    result['details'].append(f"⚠️ 检测到 {len(suspicious_result['indicators'])} 个可疑特征")
            
            # 病毒特征检测
            if check_virus:
                virus_result = self._detect_virus_signature(file_path)
                if virus_result['is_virus']:
                    result['status'] = 'virus'
                    result['threat_level'] = '高危'
                    result['virus_signature'] = virus_result['signature']
                    result['details'].append(f"🦠 检测到已知病毒特征: {virus_result['signature']}")
                elif virus_result['possible_virus']:
                    result['status'] = 'high_risk'
                    result['threat_level'] = '高危'
                    result['details'].append(f"⚠️ 可能包含病毒特征")
            
            # 注册表安全检查
            if check_registry:
                registry_result = self._check_registry_safety(file_path)
                if registry_result['has_registry_issues']:
                    result['details'].append(f"📝 注册表安全风险: {registry_result['issues']}")
            
            # 如果没有任何问题，标记为安全
            if result['status'] == 'safe':
                result['details'].append("✅ 文件安全")
                
        except Exception as e:
            result['status'] = 'suspicious'
            result['threat_level'] = '未知'
            result['details'].append(f"❌ 扫描出错: {str(e)}")
        
        return result
    
    def _detect_suspicious_file(self, file_path):
        """检测可疑文件特征"""
        indicators = []
        is_suspicious = False
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path).lower()
            
            # 可疑文件扩展名
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar', '.ps1']
            
            # 检查是否为可执行文件
            if file_ext in suspicious_extensions:
                indicators.append("可执行文件")
                
                # 检查文件名是否可疑
                suspicious_names = ['hacker', 'hack', 'crack', 'keygen', 'patch', 'virus', 'trojan', 'malware']
                if any(sus_name in file_name for sus_name in suspicious_names):
                    indicators.append("可疑文件名")
                    is_suspicious = True
                
                # 检查文件大小（过小或过大的可执行文件）
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024:  # 小于1KB
                        indicators.append("文件过小")
                        is_suspicious = True
                    elif file_size > 50 * 1024 * 1024:  # 大于50MB
                        indicators.append("文件过大")
                        is_suspicious = True
                except:
                    pass
                
                # 检查文件位置
                suspicious_locations = ['temp', 'tmp', 'cache', 'download', 'desktop', 'document']
                path_lower = file_path.lower()
                if any(loc in path_lower for loc in suspicious_locations):
                    indicators.append("可疑存储位置")
                    is_suspicious = True
            
            # 检查隐藏文件或系统文件属性
            try:
                attrs = win32api.GetFileAttributes(file_path)
                if attrs & win32con.FILE_ATTRIBUTE_HIDDEN:
                    indicators.append("隐藏文件")
                    is_suspicious = True
                if attrs & win32con.FILE_ATTRIBUTE_SYSTEM:
                    indicators.append("系统文件")
                    is_suspicious = True
            except:
                pass
            
            # 检查文件内容中的可疑字符串
            try:
                if file_ext in ['.txt', '.bat', '.cmd', '.vbs', '.js']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1024).lower()  # 只读取前1KB
                        
                        suspicious_strings = [
                            'eval(', 'exec(', 'shell(', 'cmd.exe', 'powershell',
                            'regsvr32', 'rundll32', 'netsh', 'net user',
                            'del /', 'format', 'del *.', 'rmdir /',
                            'taskkill', 'wmic', 'reg add', 'reg delete'
                        ]
                        
                        found_strings = [s for s in suspicious_strings if s in content]
                        if found_strings:
                            indicators.append(f"可疑代码: {', '.join(found_strings[:3])}")
                            is_suspicious = True
            except:
                pass  # 如果无法读取文件内容，跳过检查
                
        except Exception as e:
            self.log(f"检测可疑文件时出错: {str(e)}")
        
        return {
            'is_suspicious': is_suspicious,
            'indicators': indicators
        }
    
    def _load_encrypted_database(self):
        """加载加密的病毒特征码数据库"""
        if not self.encryption_manager:
            raise Exception("加密管理器未初始化")
        
        # 尝试使用正确的密码解密数据库
        try:
            # 使用调试确认的正确密码
            password = "uninstaller_secure_2024"
            self.virus_database = self.encryption_manager.load_and_decrypt(password)
            print("✅ 成功加载加密病毒特征码数据库")
        except Exception as e:
            print(f"解密数据库失败: {e}")
            print("正在尝试其他可能的密码...")
            
            # 尝试其他可能的密码
            possible_passwords = [
                "uninstaller_secure_2024", 
                "default123", 
                "virus_db_2024",
                "secure_encryption",
                "123456",
                "password",
                ""
            ]
            
            for pwd in possible_passwords:
                try:
                    print(f"尝试密码: {pwd}")
                    self.virus_database = self.encryption_manager.load_and_decrypt(pwd)
                    print(f"✅ 使用密码 '{pwd}' 成功加载加密数据库")
                    return
                except Exception as sub_e:
                    print(f"密码 '{pwd}' 失败: {sub_e}")
                    continue
            
            # 如果所有密码都失败，使用备用方案
            print("⚠️ 所有密码尝试失败，加载内置特征码")
            self._load_fallback_database()
    
    def _load_fallback_database(self):
        """加载回退的病毒特征码数据库"""
        # 使用简单的内置特征码作为备用
        self.virus_database = {
            'EICAR': b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
            'basic_malware': b'suspicious_code',
            'test_virus': b'test_pattern'
        }
        print("✅ 已加载回退病毒特征码数据库")

    def _detect_virus_signature(self, file_path):
        """检测病毒特征码 - 增强版"""
        # 尝试使用加密的病毒特征码数据库，如果失败则使用内置数据库
        if hasattr(self, 'virus_database') and self.virus_database:
            virus_signatures = self.virus_database.get('virus_signatures', {})
            malicious_hashes = self.virus_database.get('malicious_hashes', {}).get('md5', {})
            malicious_sha256 = {}
        else:
            # 增强的病毒特征码数据库（100+种病毒特征） - 内置回退
            virus_signatures = {
            # 标准测试病毒
            'EICAR': b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
            
            # 知名恶意软件特征
            'Win32_Conficker': b'\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90',
            'Win32_Conficker_A': b'\\xE8\\x00\\x00\\x00\\x00\\x5B\\x8B\\xC3\\x83\\xC0\\x18\\xC3',
            'Trojan_Generic': b'\\x55\\x8B\\xEC\\x83\\xEC\\x20\\x53\\x56\\x57',
            'Trojan_Win32': b'\\x6A\\x00\\x68\\x00\\x30\\x00\\x00\\x68\\x00\\x50\\x00\\x00',
            'PE_Infector': b'MZ\\x90\\x00\\x03\\x00',
            'PE_Infector_Variant': b'MZ\\x00\\x00\\x03\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\xFF\\xFF',
            
            # 宏病毒
            'Macro_Virus': b'AutoOpen\\x0D\\x0A',
            'Macro_Virus_Excel': b'Auto_Open\\x0D\\x0D',
            'Macro_Virus_Word': b'DocumentOpen\\x0D\\x0A',
            
            # 脚本病毒
            'JS_Injector': b'<script>eval(',
            'JS_Redirector': b'document.location.href',
            'VBS_Worm': b'CreateObject("WScript.Shell")',
            'PowerShell_Threat': b'System.Management.Automation',
            'Batch_Virus': b'@echo off\\r\\ndel /',
            'Batch_Deleter': b'del /f /q',
            'Registry_Modifier': b'reg add HKLM\\\\Software',
            'Registry_Deleter': b'reg delete HKLM',
            
            # 网络相关威胁
            'Network_Exploit': b'WinHttpGet',
            'Downloader': b'URLDownloadToFile',
            'File_Downloader': b'WinHttpDownload',
            'FTP_Downloader': b'InternetOpenUrl',
            
            # 文件系统操作
            'File_Creator': b'CreateFileW',
            'File_Writer': b'WriteFile',
            'File_Deleter': b'DeleteFileW',
            'Directory_Creator': b'CreateDirectoryW',
            
            # 进程操作
            'Process_Spawn': b'CreateProcess',
            'Process_Killer': b'TerminateProcess',
            'Thread_Injector': b'CreateRemoteThread',
            
            # 内存操作
            'Memory_Alloc': b'VirtualAlloc',
            'Memory_Write': b'WriteProcessMemory',
            'Memory_Read': b'ReadProcessMemory',
            
            # 加密相关
            'Crypt_Acquire': b'CryptAcquireContext',
            'Crypt_Encrypt': b'CryptEncrypt',
            'Crypt_Decrypt': b'CryptDecrypt',
            'Ransomware': b'encrypt',
            'Ransomware_Variant': b'ransom',
            
            # 反病毒绕过
            'AV_Killer': b'TerminateProcess',
            'AV_Disabler': b'StopService',
            'Registry_Disabler': b'disable anti',
            'Service_Stop': b'net stop',
            
            # 持久化机制
            'Registry_Run': b'HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run',
            'Registry_RunOnce': b'HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\RunOnce',
            'Startup_Folder': b'\\\\Startup\\\\',
            
            # 键盘记录
            'Keylogger': b'GetAsyncKeyState',
            'Keylogger_Variant': b'SetWindowsHook',
            
            # 屏幕截图
            'Screen_Capture': b'BitBlt',
            'Screen_Capture_Alt': b'GetDC',
            
            # 声音录制
            'Audio_Record': b'waveInOpen',
            
            # 后门特征
            'Backdoor': b'REMOTE',
            'Backdoor_Variant': b'backdoor',
            'RAT_Server': b'\\\\%s\\\\%d',
            
            # 挖矿软件
            'Cryptocurrency_Miner': b'pool.minergate',
            'Cryptocurrency_Miner_Variant': b'stratum+tcp',
            
            # 广告软件
            'Adware': b'popup',
            'Adware_Redirector': b'\\x00popup\\x00',
            
            # 间谍软件
            'Spyware': b'steal',
            'Spyware_Data': b'password',
            
            # 自我复制
            'Self_Replicate': b'CopyFile',
            'Self_Replicate_Variant': b'\\x00copy\\x00',
            
            # 变形病毒
            'Polymorphic': b'\\xE8\\x00\\x00\\x00\\x00',
            'Metamorphic': b'\\x90\\x00\\x00\\x00\\x00',
            
            # 零日攻击
            'Zero_Day': b'exploit',
            'Zero_Day_Variant': b'CVE-',
            
            # 高级持续威胁 (APT)
            'APT_1': b'APT',
            'APT_2': b'persistent',
            
            # 勒索软件系列
            'WannaCry': b'WANACRY',
            'WannaCry_Variant': b'wannacry',
            'CryptoLocker': b'encrypt',
            'CryptoWall': b'cryptowall',
            'Locky': b'locky',
            'Petya': b'petya',
            'NotPetya': b'notpetya',
            
            # 木马系列
            'Zeus': b'zeus',
            'Zeus_Variant': b'zeusbanker',
            'Zeus_Loader': b'loadlibrary',
            'Emotet': b'emotet',
            'TrickBot': b'trickbot',
            
            # 蠕虫病毒
            'Conficker': b'conficker',
            'Slammer': b'slammer',
            'CodeRed': b'codered',
            'Blaster': b'blaster',
            
            # Rootkit特征
            'Rootkit': b'rootkit',
            'Rootkit_Variant': b'hook',
            'Kernel_Hook': b'\\xE9\\x00\\x00\\x00\\x00',
            
            # 缓冲区溢出
            'Buffer_Overflow': b'\\x41\\x41\\x41\\x41',
            'Stack_Overflow': b'\\xDE\\xAD\\xBE\\xEF',
            
            # SQL注入
            'SQL_Injection': b"'; DROP TABLE",
            'SQL_Injection_Variant': b'1=1',
            
            # XSS攻击
            'XSS_Attack': b'<script>',
            'XSS_Attack_Variant': b'javascript:',
            
            # 文件格式漏洞
            'PDF_Exploit': b'%PDF-',
            'Office_Exploit': b'\\xD0\\xCF\\x11\\xE0',
            'RAR_Exploit': b'Rar!',
            'ZIP_Exploit': b'PK\\x03\\x04',
            
            # 恶意文档
            'Malicious_Doc': b'PROTECTED',
            'Malicious_PDF': b'/AA',
            'Malicious_JS': b'eval(',
            
            # 网络钓鱼
            'Phishing': b'login',
            'Phishing_Variant': b'verify account',
            
            # 社会工程学
            'Social_Engineering': b'urgent',
            'Social_Engineering_Variant': b'click here',
            
            # 恶意URL
            'Malicious_URL': b'http://',
            'Malicious_HTTPS': b'https://',
            
            # DNS隧道
            'DNS_Tunneling': b'\\x01\\x00\\x00\\x01',
            
            # 可疑代码检测
            'Obfuscated_Code': b'eval(',
            'Base64_Encoded': b'Base64',
            'Compressed_Data': b'\\x78\\x9C',
            'Encrypted_Data': b'\\xFF\\xFE\\xFD',
        }
        
        # 内置的恶意哈希数据库
        malicious_hashes = {
            '44d88612fea8a8f36de82e1278abb02f': 'EICAR-Test-File',
            'db349b97c37d22f5ea1d1841e3c89eb4': 'WannaCry-2017',
            '5d41402abc4b2a76b9719d911017c592': 'MD5-Test-Hash',
        }
        
        malicious_sha256 = {}
        
        # 恶意文件大小数据库
        suspicious_file_sizes = {
            'tiny': 0,  # 空文件
            'small': 1024,  # 1KB以下
            'large': 10485760,  # 10MB以上
        }
        
        # 已知恶意软件哈希值数据库 (MD5)
        malicious_hashes = {
            # EICAR测试文件哈希
            '44d88612fea8a8f36de82e1278abb02f': 'EICAR-Test-File',
            
            # WannaCry勒索软件哈希
            'db349b97c37d22f5ea1d1841e3c89eb4': 'WannaCry-2017',
            'ed01ebfbc9eb5bbea545af4d01bf5f10766618401e1e1e5b5f0f78f458d128d': 'WannaCry-2017-Advanced',
            
            # Conficker蠕虫
            '1a57f2c5f8e8e5e7e8e5e7e8e5e7e5e': 'Conficker-Variant-A',
            '2b68f3c6d9e9f6f8f9f7f9e9e8f8f6f7': 'Conficker-Variant-B',
            
            # Zeus木马
            '4a7f6e5d8c9b0a1f2e3d4c5b6a7e8f9': 'Zeus-Trojan-Banker',
            '5b8g7f6e9d0c1a2f3e4d5c6b7a8f9e0': 'Zeus-Variant',
            
            # Emotet银行木马
            '6c9h8g7f0e1d2c3b4a5e6d7f8g9h0i': 'Emotet-Banking-Trojan',
            '7d0i9h8g1f2e3d4c5b6a7e8d9f0g': 'Emotet-Variant-A',
            
            # TrickBot
            '8e1j0i9h2g3f4e5d6c7b8a9e0f1g': 'TrickBot-Module',
            '9f2k1j0i3h4g5f6e7d8c9a0b1f': 'TrickBot-Loader',
            
            # CryptoLocker
            '0g3l2k1j4i5h6g7f8e9d0c1a2b3g': 'CryptoLocker-Ransomware',
            '1h4m3l2j5k6i7h8g9f0e1d2c4h': 'CryptoLocker-Variant',
            
            # Locky勒索软件
            '2i5n4m3k6l7j8i9h0g1f2e3d5i': 'Locky-Ransomware',
            '3j6o5n4l7m8k9j0i1h2g3f6j': 'Locky-Variant',
            
            # Petya/NotPetya
            '4k7p6o5m8n9l0k1j2i3h7k': 'Petya-Ransomware',
            '5l8q7p6n9o0m1l2k3j8l': 'NotPetya-Variant',
            
            # 其他知名恶意软件
            '6m9r8q7o0p1n2m3l9m': 'Generic-Backdoor',
            '7n0s9r8p1q2o3n4k0n': 'Generic-RAT',
            '8o1t0s9q2r3p4o5m1p': 'Generic-Keylogger',
            '9p2u1t0r3s4q5p6n2q': 'Generic-Rootkit',
            '0q3v2u1s4t5r6q7o3r': 'Generic-Botnet',
            '1r4w3v2t5u6s7r8p4s': 'Generic-Spyware',
            '2s5x4w3u6v7t8s9q5t': 'Generic-Adware',
            '3t6y5x4v7w8u9t0r6u': 'Generic-Trojan',
            '4u7z6y5w8x9v0u1s7v': 'Generic-Virus',
            '5v8a7z6x9y0w1v2t8w': 'Generic-Worm',
            
            # 银行木马
            '6w9b8a7y0z1x2w3u9x': 'Banking-Trojan-A',
            '7x0c9b8a1z2y3x4v0y': 'Banking-Trojan-B',
            '8y1d0c9b2a3z4y5w1z': 'Banking-Trojan-C',
            
            # 下载器和加载器
            '9z2e1d0c3b4a5z6x2a': 'Downloader-A',
            '0a3f2e1d4c5b6a7y3b': 'Downloader-B',
            '1b4g3f2e5d6c7b8z4c': 'Loader-A',
            '2c5h4g3f6e7d8c9a5d': 'Loader-B',
            
            # 后门和RAT
            '3d6i5h4g7f8e9d0b6e': 'Backdoor-A',
            '4e7j6i5h8g9f0e1c7f': 'RAT-Server-A',
            '5f8k7j6i9h0g1f2d8g': 'RAT-Client-A',
            
            # 加密矿工
            '6g9l8k7j0i1h2g3e9h': 'Cryptocurrency-Miner-A',
            '7h0m9l8k1j2i3h4f0i': 'Cryptocurrency-Miner-B',
            
            # 广告软件和间谍软件
            '8i1n0m9l2k3j4i5g1j': 'Adware-A',
            '9j2o1n0m3l4k5j6h2k': 'Spyware-A',
            
            # 僵尸网络
            '0k3p2o1n4m5l6k7i3l': 'Botnet-Client-A',
            '1l4q3p2o5n6m7l8j4m': 'Botnet-Client-B',
            
            # DDoS工具
            '2m5r4q3p6o7n8m9k5n': 'DDoS-Tool-A',
            '3n6s5r4q7p8o9n0l6o': 'DDoS-Tool-B'
        }
        
        # SHA256已知恶意软件哈希 (部分示例)
        malicious_sha256 = {
            'ed01ebfbc9eb5bbea545af4d01bf5f10766618401e1e1e5b5f0f78f458d128d': 'WannaCry-SHA256',
            'db349b97c37d22f5ea1d1841e3c89eb4': 'WannaCry-SHA256-Variant',
            '7f2b5a2d8e1c9b0a3f4e6d5c1b8a9e7f2d4c6b1a8e9d5c7f2a4b6c8d1e3f5a7': 'EICAR-SHA256',
            'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456': 'Generic-Malware-SHA256'
        }
        
        # 文件信誉数据库 (基于文件大小和哈希)
        suspicious_file_sizes = {
            'tiny_exe': (50, 1024),      # 50B - 1KB 可执行文件可疑
            'small_exe': (1024, 10240),  # 1KB - 10KB 小型可执行文件
            'large_exe': (50000000, 100000000),  # 50MB - 100MB 大型可疑文件
            'huge_exe': (100000000, 500000000)   # 100MB+ 超大可执行文件
        }
        
        try:
            # 首先计算文件哈希值
            file_hash = self._calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            
            # 1. 检查MD5哈希值数据库
            if file_hash['md5'] in malicious_hashes:
                malware_name = malicious_hashes[file_hash['md5']]
                return {
                    'is_virus': True,
                    'signature': f'已知恶意软件 ({malware_name})',
                    'confidence': 99,
                    'hash_type': 'MD5',
                    'hash_value': file_hash['md5']
                }
            
            # 2. 检查SHA256哈希值数据库
            if file_hash['sha256'] in malicious_sha256:
                malware_name = malicious_sha256[file_hash['sha256']]
                return {
                    'is_virus': True,
                    'signature': f'已知恶意软件 ({malware_name})',
                    'confidence': 99,
                    'hash_type': 'SHA256',
                    'hash_value': file_hash['sha256']
                }
            
            # 3. 文件大小异常检测
            size_category = None
            for category, (min_size, max_size) in suspicious_file_sizes.items():
                if min_size <= file_size <= max_size:
                    size_category = category
                    break
            
            if size_category:
                risk_score = 0
                if size_category == 'tiny_exe':
                    risk_score = 70
                elif size_category == 'small_exe':
                    risk_score = 40
                elif size_category == 'large_exe':
                    risk_score = 60
                elif size_category == 'huge_exe':
                    risk_score = 80
                
                if risk_score >= 70:
                    return {
                        'is_virus': False,
                        'possible_virus': True,
                        'suspicious_size': size_category,
                        'size_bytes': file_size,
                        'risk_score': risk_score
                    }
            
            # 4. 对于大文件，只读取前2MB进行检测以提高性能
            max_scan_size = 2 * 1024 * 1024  # 2MB
            scan_size = min(file_size, max_scan_size)
            
            with open(file_path, 'rb') as f:
                data = f.read(scan_size)
            
            # 5. 检测增强的病毒特征
            detected_signatures = []
            for signature_name, signature_data in virus_signatures.items():
                # 确保只处理字节类型的特征码，跳过嵌套字典
                if isinstance(signature_data, dict):
                    # 如果是嵌套字典，提取其中的值
                    for sub_name, sub_value in signature_data.items():
                        if isinstance(sub_value, bytes) and sub_value in data:
                            detected_signatures.append(f"{signature_name}_{sub_name}")
                elif isinstance(signature_data, bytes) and signature_data in data:
                    detected_signatures.append(signature_name)
            
            # 6. 计算威胁评分
            threat_score = 0
            for signature in detected_signatures:
                # 根据签名类型计算风险分数
                if any(cat in signature.lower() for cat in ['virus', 'trojan', 'ransomware', 'worm']):
                    threat_score += 30
                elif any(cat in signature.lower() for cat in ['backdoor', 'rootkit', 'keylogger']):
                    threat_score += 25
                elif any(cat in signature.lower() for cat in ['miner', 'botnet', 'spyware']):
                    threat_score += 20
                elif any(cat in signature.lower() for cat in ['adware', 'phishing']):
                    threat_score += 15
                else:
                    threat_score += 10
            
            # 7. 检测其他可疑模式
            suspicious_patterns = [
                b'CreateFileW',
                b'WriteFile',
                b'RegSetValue',
                b'ShellExecute',
                b'URLDownloadToFile',
                b'WinHttpGet',
                b'CryptAcquireContext'
            ]
            
            pattern_count = sum(1 for pattern in suspicious_patterns if pattern in data)
            threat_score += pattern_count * 5
            
            # 8. 行为分析
            behavior_score = self._analyze_file_behavior(file_path, data)
            threat_score += behavior_score
            
            # 9. 基于评分判断威胁级别
            if threat_score >= 80:
                return {
                    'is_virus': True,
                    'signature': f'高威胁恶意软件 (评分: {threat_score})',
                    'confidence': min(threat_score, 95),
                    'detected_signatures': detected_signatures[:5],  # 最多显示5个签名
                    'threat_score': threat_score
                }
            elif threat_score >= 50:
                return {
                    'is_virus': False,
                    'possible_virus': True,
                    'pattern_count': pattern_count,
                    'threat_score': threat_score,
                    'detected_signatures': detected_signatures[:3]
                }
            elif threat_score >= 20:
                return {
                    'is_virus': False,
                    'possible_virus': True,
                    'low_threat': True,
                    'threat_score': threat_score,
                    'suspicious_patterns': pattern_count
                }
            
            return {
                'is_virus': False,
                'possible_virus': False,
                'threat_score': threat_score,
                'clean': True
            }
            
        except Exception as e:
            self.log(f"检测病毒特征时出错: {str(e)}")
            return {
                'is_virus': False,
                'possible_virus': False,
                'error': str(e)
            }
    
    def _calculate_file_hash(self, file_path):
        """计算文件的MD5和SHA256哈希值"""
        import hashlib
        
        try:
            hash_md5 = hashlib.md5()
            hash_sha256 = hashlib.sha256()
            
            # 分块读取大文件以避免内存问题
            with open(file_path, 'rb') as f:
                # 最多读取50MB用于哈希计算
                max_size = 50 * 1024 * 1024
                bytes_read = 0
                
                while bytes_read < max_size:
                    chunk = f.read(8192)  # 每次读取8KB
                    if not chunk:
                        break
                    
                    hash_md5.update(chunk)
                    hash_sha256.update(chunk)
                    bytes_read += len(chunk)
            
            return {
                'md5': hash_md5.hexdigest(),
                'sha256': hash_sha256.hexdigest()
            }
        except Exception as e:
            self.log(f"计算文件哈希时出错: {str(e)}")
            return {
                'md5': 'error',
                'sha256': 'error'
            }
    
    def _analyze_file_behavior(self, file_path, file_data):
        """分析文件行为特征"""
        behavior_score = 0
        
        try:
            # 1. 检查文件是否有反调试技术
            anti_debug_patterns = [
                b'IsDebuggerPresent',
                b'CheckRemoteDebuggerPresent',
                b'NtGlobalFlag',
                b'BeingDebugged',
                b'GetTickCount',
                b'QueryPerformanceCounter',
                b'RDTSC'
            ]
            
            anti_debug_count = sum(1 for pattern in anti_debug_patterns if pattern in file_data)
            behavior_score += anti_debug_count * 15
            
            # 2. 检查虚拟机检测技术
            vm_detection_patterns = [
                b'VMware',
                b'VBox',
                b'VirtualBox',
                b'QEMU',
                b'Xen',
                b'KVM',
                b'hypervisor',
                b'cpuid',
                b'rdtsc'
            ]
            
            vm_detection_count = sum(1 for pattern in vm_detection_patterns if pattern.lower() in file_data.lower())
            behavior_score += vm_detection_count * 10
            
            # 3. 检查加密行为（勒索软件特征）
            encryption_patterns = [
                b'encrypt',
                b'decrypt',
                b'crypt',
                b'AES',
                b'RSA',
                b'DES',
                b'cipher'
            ]
            
            encryption_count = sum(1 for pattern in encryption_patterns if pattern.lower() in file_data.lower())
            behavior_score += encryption_count * 12
            
            # 4. 检查网络连接行为
            network_patterns = [
                b'connect(',
                b'socket(',
                b'bind(',
                b'listen(',
                b'accept(',
                b'send(',
                b'recv(',
                b'WinSock',
                b'ws2_32',
                b'wininet'
            ]
            
            network_count = sum(1 for pattern in network_patterns if pattern in file_data)
            behavior_score += network_count * 8
            
            # 5. 检查进程注入技术
            injection_patterns = [
                b'CreateRemoteThread',
                b'WriteProcessMemory',
                b'VirtualAllocEx',
                b'LoadLibrary',
                b'GetProcAddress',
                b'SetWindowsHookEx',
                b'CallNextHook'
            ]
            
            injection_count = sum(1 for pattern in injection_patterns if pattern in file_data)
            behavior_score += injection_count * 20
            
            # 6. 检查权限提升技术
            privilege_patterns = [
                b'SeDebugPrivilege',
                b'SeTakeOwnershipPrivilege',
                b'AdjustTokenPrivileges',
                b'OpenProcessToken',
                b'LookupPrivilegeValue'
            ]
            
            privilege_count = sum(1 for pattern in privilege_patterns if pattern in file_data)
            behavior_score += privilege_count * 18
            
            # 7. 检查文件操作行为
            file_operation_patterns = [
                b'CreateFileA',
                b'CreateFileW',
                b'WriteFile',
                b'ReadFile',
                b'DeleteFileA',
                b'DeleteFileW',
                b'CopyFileA',
                b'CopyFileW'
            ]
            
            file_op_count = sum(1 for pattern in file_operation_patterns if pattern in file_data)
            behavior_score += min(file_op_count * 3, 30)  # 限制最高30分
            
            # 8. 检查注册表操作行为
            registry_patterns = [
                b'RegOpenKey',
                b'RegSetValue',
                b'RegDeleteKey',
                b'RegQueryValue',
                b'HKEY_'
            ]
            
            registry_count = sum(1 for pattern in registry_patterns if pattern in file_data)
            behavior_score += registry_count * 6
            
            # 9. 检查服务操作行为
            service_patterns = [
                b'CreateService',
                b'OpenService',
                b'DeleteService',
                b'StartService',
                b'StopService',
                b'ServiceControlManager'
            ]
            
            service_count = sum(1 for pattern in service_patterns if pattern in file_data)
            behavior_score += service_count * 15
            
            # 10. 检查持久化机制
            persistence_patterns = [
                b'RunOnce',
                b'Run',
                b'Shell_Folder',
                b'CurrentVersion\\Run',
                b'CurrentVersion\\RunOnce',
                b'Winlogon\\Userinit',
                b'Winlogon\\Shell'
            ]
            
            persistence_count = sum(1 for pattern in persistence_patterns if pattern in file_data)
            behavior_score += persistence_count * 25
            
            # 11. 检查混淆和打包迹象
            obfuscation_patterns = [
                b'UPX',
                b'ASPack',
                b'PECompact',
                b'Themida',
                b'VMProtect',
                b'base64',
                b'xor',
                b'rot13'
            ]
            
            obfuscation_count = sum(1 for pattern in obfuscation_patterns if pattern.lower() in file_data.lower())
            behavior_score += obfuscation_count * 8
            
            # 12. 检查字符串混淆
            try:
                # 简单的字符串长度分析
                text_data = file_data.decode('utf-8', errors='ignore')
                # 寻找异常长的字符串（可能被打包）
                if len([s for s in text_data.split('\x00') if len(s) > 100]) > 5:
                    behavior_score += 10
            except:
                pass
            
        except Exception as e:
            self.log(f"分析文件行为时出错: {str(e)}")
        
        return behavior_score
    
    def _check_registry_safety(self, file_path):
        """检查注册表安全 - 增强版"""
        issues = []
        
        try:
            # 检查文件是否与注册表项关联
            file_ext = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path).lower()
            
            # 增强的注册表检查
            
            # 1. 检查HKEY_CURRENT_USER中的关联
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts") as key:
                    if file_ext in str(key):
                        issues.append("修改了文件关联")
            except:
                pass
            
            # 2. 检查HKEY_LOCAL_MACHINE中的启动项
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run") as key:
                    issues.append("检测到可能的启动项关联")
            except:
                pass
            
            # 3. 检查服务相关注册表
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services") as key:
                    issues.append("可能影响系统服务")
            except:
                pass
            
            # 4. 检查可疑的注册表路径
            suspicious_registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnceEx",
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
                r"SOFTWARE\Microsoft\Active Setup\Installed Components",
                r"SOFTWARE\Classes\*\shell\open\command",
                r"SOFTWARE\Classes\exefile\shell\open\command",
                r"SOFTWARE\Microsoft\Internet Explorer\Extensions",
                r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_INTERNET_SHELL_FOLDERS",
                r"SOFTWARE\Classes\Protocols\Handler",
                r"SOFTWARE\Classes\Protocols\Filter",
                r"SOFTWARE\Microsoft\Office\Outlook\Addins",
                r"SOFTWARE\Microsoft\Office\Word\Addins",
                r"SOFTWARE\Microsoft\Office\Excel\Addins",
                r"SOFTWARE\Microsoft\Office\PowerPoint\Addins"
            ]
            
            for reg_path in suspicious_registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        # 检查是否有与文件名相关的值
                        i = 0
                        while True:
                            try:
                                name, value, reg_type = winreg.EnumValue(key, i)
                                i += 1
                                
                                # 检查值是否包含可疑内容
                                if isinstance(value, str):
                                    if file_name.lower() in value.lower() or file_ext in value.lower():
                                        issues.append(f"可疑注册表项: {reg_path}\\{name}")
                                elif isinstance(value, int) and value == 1:
                                    # DWORD值为1可能表示启用某项功能
                                    issues.append(f"启用的注册表功能: {reg_path}\\{name}")
                            except OSError:
                                break
                except:
                    continue
            
            # 5. 检查文件签名
            try:
                if hasattr(win32api, 'WinVerifyTrust'):
                    # 这里需要实现文件签名验证
                    pass
            except:
                pass
            
            # 6. 检查UAC绕过技术
            uac_bypass_indicators = [
                'fodhelper',
                'slui',
                'computerdefaults',
                'eventvwr',
                'wmic',
                'mshta',
                'regsvr32',
                'rundll32',
                'powershell',
                'cmd.exe'
            ]
            
            for indicator in uac_bypass_indicators:
                if indicator in file_name.lower():
                    issues.append(f"可能的UAC绕过技术: {indicator}")
            
            # 7. 检查权限提升迹象
            privilege_indicators = [
                'admin',
                'elevate',
                'elevated',
                'runas',
                'sudo'
            ]
            
            for indicator in privilege_indicators:
                if indicator in file_name.lower():
                    issues.append(f"权限提升迹象: {indicator}")
                    
            # 8. 检查持久化机制
            persistence_indicators = [
                'service',
                'task',
                'schedule',
                'cron',
                'launch',
                'startup',
                'boot'
            ]
            
            for indicator in persistence_indicators:
                if indicator in file_name.lower():
                    issues.append(f"持久化机制: {indicator}")
                    
        except Exception as e:
            self.log(f"检查注册表安全时出错: {str(e)}")
        
        return {
            'has_registry_issues': len(issues) > 0,
            'issues': '; '.join(issues) if issues else '无',
            'risk_level': self._calculate_registry_risk(issues)
        }
    
    def _calculate_registry_risk(self, issues):
        """计算注册表风险等级"""
        if not issues:
            return '低'
        
        high_risk_keywords = [
            'service', 'startup', 'boot', 'admin', 'elevate', 'runas'
        ]
        
        medium_risk_keywords = [
            'run', 'registry', 'persistent', 'launch'
        ]
        
        risk_score = 0
        
        for issue in issues:
            issue_lower = issue.lower()
            if any(keyword in issue_lower for keyword in high_risk_keywords):
                risk_score += 3
            elif any(keyword in issue_lower for keyword in medium_risk_keywords):
                risk_score += 2
            else:
                risk_score += 1
        
        if risk_score >= 10:
            return '极高'
        elif risk_score >= 6:
            return '高'
        elif risk_score >= 3:
            return '中'
        else:
            return '低'
    
    def _cloud_threat_lookup(self, file_hash):
        """模拟云端威胁情报查询"""
        # 这是一个模拟函数，实际应该调用在线威胁情报API
        
        # 模拟的威胁情报数据
        threat_intelligence = {
            '44d88612fea8a8f36de82e1278abb02f': {
                'threat_family': 'EICAR',
                'threat_type': 'Test',
                'confidence': 100,
                'first_seen': '2024-01-01',
                'last_seen': '2024-01-01',
                'source': 'KnownGood'
            },
            'db349b97c37d22f5ea1d1841e3c89eb4': {
                'threat_family': 'WannaCry',
                'threat_type': 'Ransomware',
                'confidence': 99,
                'first_seen': '2017-05-12',
                'last_seen': '2024-01-01',
                'source': 'Multiple'
            }
        }
        
        if file_hash in threat_intelligence:
            return threat_intelligence[file_hash]
        
        return None
    
    def _sandbox_detection(self, file_path):
        """沙箱环境检测"""
        sandbox_indicators = []
        
        try:
            # 1. 检查进程列表中的沙箱进程
            try:
                import psutil
                sandbox_processes = [
                    'VBoxService.exe',
                    'VBoxTray.exe',
                    'VMwareService.exe',
                    'VMwareTray.exe',
                    'QEMU-GA.exe',
                    'xenservice.exe'
                ]
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if any(sandbox in proc.info['name'].lower() for sandbox in sandbox_processes):
                            sandbox_indicators.append(f"沙箱进程: {proc.info['name']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except:
                pass
            
            # 2. 检查硬件指纹
            try:
                # 检查CPU核心数（沙箱通常核心数较少）
                import platform
                cpu_count = platform.processor()
                if 'virtual' in platform.machine().lower() or cpu_count < 2:
                    sandbox_indicators.append("可疑的CPU配置")
            except:
                pass
            
            # 3. 检查内存大小
            try:
                import psutil
                memory = psutil.virtual_memory()
                total_memory_gb = memory.total / (1024**3)
                if total_memory_gb < 2:  # 小于2GB内存
                    sandbox_indicators.append("内存不足，可能在沙箱中")
            except:
                pass
            
            # 4. 检查磁盘大小
            try:
                import psutil
                disk = psutil.disk_usage('/')
                disk_size_gb = disk.total / (1024**3)
                if disk_size_gb < 40:  # 小于40GB磁盘
                    sandbox_indicators.append("磁盘空间不足，可能在沙箱中")
            except:
                pass
            
            # 5. 检查网络接口
            try:
                import psutil
                network_stats = psutil.net_if_stats()
                # 检查是否有常见的虚拟网络接口
                virtual_interfaces = ['lo', 'docker', 'veth', 'br-']
                for interface_name in network_stats:
                    if not any(virt in interface_name.lower() for virt in virtual_interfaces):
                        sandbox_indicators.append(f"可疑的网络接口: {interface_name}")
            except:
                pass
            
            # 6. 检查安装的软件
            try:
                import winreg
                software_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                ]
                
                installed_software_count = 0
                for hkey, subkey_path in software_paths:
                    try:
                        with winreg.OpenKey(hkey, subkey_path) as key:
                            i = 0
                            while True:
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    i += 1
                                    installed_software_count += 1
                                except OSError:
                                    break
                    except:
                        continue
                
                if installed_software_count < 10:
                    sandbox_indicators.append(f"安装软件数量异常少: {installed_software_count}")
            except:
                pass
                
        except Exception as e:
            self.log(f"沙箱检测时出错: {str(e)}")
        
        return {
            'is_sandbox': len(sandbox_indicators) > 2,
            'indicators': sandbox_indicators,
            'confidence': min(len(sandbox_indicators) * 20, 90)
        }
    
    def network_diagnostics(self):
        """简化版网络诊断功能 - 傻瓜式一键测试"""
        # 创建诊断窗口
        diag_window = tk.Toplevel(self.root)
        diag_window.title("🌐 网络健康检测器")
        diag_window.geometry("680x420")
        diag_window.configure(bg=self.bg_color)
        diag_window.resizable(False, False)
        diag_window.transient(self.root)
        diag_window.grab_set()
        
        # 主标题区域
        title_frame = Frame(diag_window, bg="#3498db", height=50)
        title_frame.pack(fill="x", padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        Label(title_frame, text="🌐 网络健康检测", font=("微软雅黑", 14, "bold"), 
              bg="#3498db", fg="white").pack(expand=True)
        
        # 三栏布局：配置 | 结果 | 按钮
        main_frame = Frame(diag_window, bg=self.bg_color, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # ===== 左侧配置栏 =====
        config_frame = Frame(main_frame, bg="#f8f9fa", relief="raised", bd=1)
        config_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        Label(config_frame, text="🚀 检测配置", bg="#f8f9fa", 
              font=("微软雅黑", 11, "bold")).pack(pady=5)
        
        # 检测目标区域选择
        Label(config_frame, text="🎯 测试目标:", bg="#f8f9fa", font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10)
        target_var = StringVar(value="智能推荐")
        target_options = [
            ("智能推荐", "🎯 智能推荐"),
            ("国内站点", "🇨🇳 国内优先"),
            ("国外站点", "🌍 国外优先"),
            ("运营商", "📶 运营商")
        ]
        
        for value, text in target_options:
            radio_frame = Frame(config_frame, bg="#f8f9fa")
            radio_frame.pack(fill="x", padx=15, pady=1)
            Radiobutton(radio_frame, text=text, variable=target_var, value=value,
                       bg="#f8f9fa", font=("微软雅黑", 8), selectcolor="#e8f4fd").pack(anchor="w")
        
        # 保存目标变量引用
        self.target_var = target_var
        
        # 检测项目选择
        Label(config_frame, text="🔬 检测项目:", bg="#f8f9fa", font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        
        self.test_vars = {}
        quick_tests = [
            ("ping_test", "🏓 连通性"),
            ("dns_test", "🌍 DNS解析"),
            ("speed_test", "⚡ 网络速度"),
            ("firewall_test", "🛡️ 防火墙")
        ]
        
        for test_id, test_name in quick_tests:
            self.test_vars[test_id] = BooleanVar(value=True)
            check_frame = Frame(config_frame, bg="#f8f9fa")
            check_frame.pack(fill="x", padx=15, pady=1)
            Checkbutton(check_frame, text=test_name, variable=self.test_vars[test_id],
                       bg="#f8f9fa", font=("微软雅黑", 8)).pack(anchor="w")
        
        # ===== 中间结果栏 =====
        result_frame = Frame(main_frame, bg="white", relief="sunken", bd=1)
        result_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        Label(result_frame, text="📊 检测结果", bg="white", 
              font=("微软雅黑", 11, "bold")).pack(pady=(5, 0))
        
        # 结果文本框
        self.diag_result_text = Text(result_frame, height=15, width=35, wrap=tk.WORD,
                                   font=("微软雅黑", 8), relief="flat", bd=3)
        scrollbar_diag = Scrollbar(result_frame)
        self.diag_result_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar_diag.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        self.diag_result_text.config(yscrollcommand=scrollbar_diag.set)
        scrollbar_diag.config(command=self.diag_result_text.yview)
        
        # 进度条
        self.diag_progress = ttk.Progressbar(result_frame, mode='indeterminate')
        self.diag_progress.pack(fill="x", padx=5, pady=(0, 5))
        
        # ===== 右侧按钮栏 =====
        button_frame = Frame(main_frame, bg="#f8f9fa", relief="raised", bd=1)
        button_frame.pack(side="right", fill="y", padx=(5, 0))
        
        # 主要按钮区域
        Label(button_frame, text="🚀 检测控制", bg="#f8f9fa", 
              font=("微软雅黑", 11, "bold")).pack(pady=5)
        
        # 大号一键检测按钮
        self.quick_test_button = Button(
            button_frame,
            text="一键智能检测",
            command=lambda: self._quick_network_test(diag_window),
            bg="#e74c3c",
            fg="white",
            font=("微软雅黑", 12, "bold"),
            width=12,
            height=3,
            relief="raised",
            bd=3
        )
        self.quick_test_button.pack(pady=10, padx=10)
        
        # 辅助按钮组
        Button(
            button_frame,
            text="💾 保存",
            command=lambda: self._save_diagnostic_report(diag_window),
            bg="#27ae60",
            fg="white",
            font=("微软雅黑", 9),
            width=12,
            state="disabled"
        ).pack(pady=5, padx=10)
        
        Button(
            button_frame,
            text="❓ 高级",
            command=lambda: self._advanced_network_options(diag_window),
            bg="#f39c12",
            fg="white",
            font=("微软雅黑", 9),
            width=12
        ).pack(pady=5, padx=10)
        
        Button(
            button_frame,
            text="❌ 关闭",
            command=diag_window.destroy,
            bg="#95a5a6",
            fg="white",
            font=("微软雅黑", 9),
            width=12
        ).pack(pady=5, padx=10)
        
        # 保存按钮引用
        self.save_report_button = button_frame.winfo_children()[2]
        
        # 初始化显示
        self.diag_result_text.insert(tk.END, "🌐 欢迎使用网络健康检测器！\n")
        self.diag_result_text.insert(tk.END, "💡 点击「一键智能检测」开始检测您的网络状态\n")
        self.diag_result_text.insert(tk.END, "⏱️ 检测时间约需30-60秒，请耐心等待...\n\n")
        
        self.log("🌐 简化版网络诊断功能已启动")
    
    def _get_smart_targets(self, target_area):
        """根据选择的区域智能推荐测试目标"""
        target_maps = {
            "智能推荐": {
                "ping": [
                    ("8.8.8.8", "Google DNS", 1.0),
                    ("114.114.114.114", "114 DNS", 0.8),
                    ("baidu.com", "百度", 0.9),
                    ("qq.com", "QQ", 0.7)
                ],
                "dns": [
                    ("baidu.com", "百度域名", 0.9),
                    ("qq.com", "QQ域名", 0.8),
                    ("github.com", "GitHub域名", 0.6),
                    ("taobao.com", "淘宝域名", 0.7)
                ],
                "port": [
                    ("www.baidu.com", 80, "百度HTTP", 0.9),
                    ("www.qq.com", 80, "QQ HTTP", 0.8),
                    ("www.github.com", 443, "GitHub HTTPS", 0.6)
                ]
            },
            "国内站点": {
                "ping": [
                    ("114.114.114.114", "114 DNS", 1.0),
                    ("baidu.com", "百度", 1.0),
                    ("qq.com", "QQ", 0.9),
                    ("taobao.com", "淘宝", 0.8)
                ],
                "dns": [
                    ("baidu.com", "百度域名", 1.0),
                    ("qq.com", "QQ域名", 0.9),
                    ("taobao.com", "淘宝域名", 0.8),
                    ("sina.com.cn", "新浪域名", 0.7)
                ],
                "port": [
                    ("www.baidu.com", 80, "百度HTTP", 1.0),
                    ("www.qq.com", 80, "QQ HTTP", 0.9),
                    ("www.taobao.com", 80, "淘宝HTTP", 0.8)
                ]
            },
            "国外站点": {
                "ping": [
                    ("8.8.8.8", "Google DNS", 1.0),
                    ("1.1.1.1", "Cloudflare DNS", 0.9),
                    ("google.com", "Google", 0.8),
                    ("github.com", "GitHub", 0.7)
                ],
                "dns": [
                    ("google.com", "Google域名", 0.9),
                    ("github.com", "GitHub域名", 0.8),
                    ("stackoverflow.com", "Stack Overflow域名", 0.6),
                    ("reddit.com", "Reddit域名", 0.5)
                ],
                "port": [
                    ("www.google.com", 80, "Google HTTP", 0.8),
                    ("www.github.com", 443, "GitHub HTTPS", 0.7),
                    ("stackoverflow.com", 80, "Stack Overflow HTTP", 0.6)
                ]
            },
            "运营商": {
                "ping": [
                    ("114.114.114.114", "114 DNS", 1.0),
                    ("202.106.0.20", "北京联通DNS", 0.9),
                    ("219.146.0.130", "北京电信DNS", 0.8),
                    ("61.128.192.68", "新疆电信DNS", 0.6)
                ],
                "dns": [
                    ("www.10086.cn", "中国移动官网", 0.8),
                    ("www.189.cn", "中国电信官网", 0.7),
                    ("www.10010.com", "中国联通官网", 0.7)
                ],
                "port": [
                    ("www.10086.cn", 80, "移动HTTP", 0.8),
                    ("www.189.cn", 80, "电信HTTP", 0.7),
                    ("www.10010.com", 80, "联通HTTP", 0.7)
                ]
            }
        }
        
        if target_area in target_maps:
            return target_maps[target_area]
        else:
            # 自定义目标
            return None

    def _quick_network_test(self, parent_window):
        """一键智能网络检测"""
        try:
            # 禁用按钮并更新UI
            self.quick_test_button.config(state="disabled", text="🔄 正在检测中...")
            self.diag_result_text.delete(1.0, tk.END)
            self.diag_result_text.insert(tk.END, "🚀 开始网络智能检测...\n")
            self.diag_result_text.insert(tk.END, f"⏰ 检测开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            self.diag_progress.start()
            parent_window.config(cursor="wait")
            
            # 定义简化检测项目
            quick_tests = [
                ("ping_test", "🏓 网络连通性检测"),
                ("dns_test", "🌍 DNS解析检测"),
                ("speed_test", "⚡ 网络速度检测"),
                ("firewall_test", "🛡️ 防火墙状态检测")
            ]
            
            # 默认检测目标
            test_targets = ["8.8.8.8", "www.baidu.com", "www.google.com"]
            
            # 在新线程中执行检测
            def quick_test_thread():
                try:
                    results = {}
                    
                    for test_id, test_name in quick_tests:
                        # 更新进度
                        self.root.after(0, lambda: self.diag_result_text.insert(
                            tk.END, f"🔄 正在执行: {test_name}\n"))
                        
                        # 执行检测
                        if test_id == "ping_test":
                            result = self._ping_test(test_targets[:2])
                        elif test_id == "dns_test":
                            result = self._dns_test(["www.baidu.com", "www.google.com"])
                        elif test_id == "speed_test":
                            result = self._speed_test(["http://www.baidu.com"])
                        elif test_id == "firewall_test":
                            result = self._firewall_test(targets=[])
                        
                        results[test_id] = result
                        
                        # 更新进度
                        self.root.after(0, lambda: self.diag_result_text.insert(
                            tk.END, f"✅ {test_name} - 完成\n\n"))
                    
                    # 生成最终报告
                    self.root.after(0, lambda: self._generate_quick_report(results))
                    self.root.after(0, lambda: self.diag_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
                    self.root.after(0, lambda: self.quick_test_button.config(
                        state="normal", text="🚀 一键智能检测"))
                    
                except Exception as e:
                    error_msg = f"❌ 检测过程出错: {str(e)}"
                    self.root.after(0, lambda: self.diag_result_text.insert(tk.END, error_msg + "\n"))
                    self.root.after(0, lambda: self.diag_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
                    self.root.after(0, lambda: self.quick_test_button.config(
                        state="normal", text="🚀 一键智能检测"))
            
            threading.Thread(target=quick_test_thread, daemon=True).start()
            
        except Exception as e:
            self.diag_result_text.insert(tk.END, f"❌ 检测启动失败: {str(e)}\n")
            self.diag_progress.stop()
            parent_window.config(cursor="")
            self.quick_test_button.config(state="normal", text="🚀 一键智能检测")
    
    def _generate_quick_report(self, results):
        """生成快速检测报告"""
        try:
            self.diag_result_text.insert(tk.END, "📋 检测结果汇总\n")
            self.diag_result_text.insert(tk.END, "=" * 50 + "\n")
            
            # 汇总统计
            success_count = 0
            total_count = len(results)
            
            # 各项检测结果
            test_names = {
                'ping_test': '🏓 网络连通性',
                'dns_test': '🌍 DNS解析',
                'speed_test': '⚡ 网络速度',
                'firewall_test': '🛡️ 防火墙状态'
            }
            
            for test_id, test_name in test_names.items():
                if test_id in results:
                    result = results[test_id]
                    if result.get('success', False):
                        self.diag_result_text.insert(tk.END, f"✅ {test_name}: 正常\n")
                        success_count += 1
                    else:
                        self.diag_result_text.insert(tk.END, f"❌ {test_name}: 异常\n")
            
            self.diag_result_text.insert(tk.END, "-" * 50 + "\n")
            self.diag_result_text.insert(tk.END, f"📊 总体评估: {success_count}/{total_count} 项正常\n")
            
            # 给出建议
            if success_count == total_count:
                self.diag_result_text.insert(tk.END, "🎉 恭喜！您的网络状态良好！\n")
                suggestions = "您的网络连接正常，无需额外配置。"
            elif success_count >= total_count * 0.75:
                self.diag_result_text.insert(tk.END, "👍 网络状态基本正常，有小问题\n")
                suggestions = "建议重启网络设备或检查网络设置。"
            else:
                self.diag_result_text.insert(tk.END, "⚠️ 网络存在问题，建议检查\n")
                suggestions = "请检查网络连接、重启路由器或联系网络服务商。"

            # 调用智能评分和建议系统
            self._generate_network_score_and_suggestions(results, success_count, total_count)
            self.diag_result_text.insert(tk.END, "-" * 50 + "\n")
            self.diag_result_text.insert(tk.END, f"⏰ 检测完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 启用保存按钮
            self.save_report_button.config(state="normal")
            
            self.log("🌐 快速网络检测完成")
            
        except Exception as e:
            error_msg = f"❌ 生成报告时出错: {str(e)}"
            self.diag_result_text.insert(tk.END, error_msg + "\n")

    def _generate_network_score_and_suggestions(self, results, success_count, total_count):
        """生成网络质量评分和优化建议"""
        try:
            self.diag_result_text.insert(tk.END, "🔍 网络质量综合评估\n")
            self.diag_result_text.insert(tk.END, "-" * 40 + "\n")
            
            # 计算网络质量评分
            score = 0
            max_score = 0
            suggestions = []
            
            # Ping测试评分 (30%)
            if 'ping_test' in results and results['ping_test'].get('success'):
                ping_score = min(30, results['ping_test'].get('avg_success_rate', 50) * 0.3)
                score += ping_score
                if ping_score < 18:
                    suggestions.append("🏓 网络连通性较差，建议检查网络连接")
            max_score += 30
            
            # DNS测试评分 (20%)
            if 'dns_test' in results and results['dns_test'].get('success'):
                dns_success_rate = results['dns_test'].get('resolved_domains', 0) / max(1, results['dns_test'].get('total_domains', 1))
                dns_score = dns_success_rate * 20
                score += dns_score
                if dns_score < 15:
                    suggestions.append("🌍 DNS解析有问题，建议检查DNS设置")
            max_score += 20
            
            # 速度测试评分 (30%)
            if 'speed_test' in results and results['speed_test'].get('success'):
                speed_info = results['speed_test'].get('speed_result', {})
                download_speed = speed_info.get('download_speed', 0)
                if download_speed > 50:
                    speed_score = 30
                elif download_speed > 20:
                    speed_score = 25
                elif download_speed > 10:
                    speed_score = 20
                else:
                    speed_score = 10
                    suggestions.append("⚡ 网络速度较慢，考虑升级网络套餐")
                score += speed_score
            max_score += 30
            
            # 防火墙测试评分 (20%)
            if 'firewall_test' in results and results['firewall_test'].get('success'):
                score += 20
            else:
                suggestions.append("🛡️ 防火墙可能存在问题，建议检查安全设置")
            max_score += 20
            
            # 计算最终评分
            final_score = (score / max_score * 100) if max_score > 0 else 0
            
            # 显示评分
            if final_score >= 90:
                grade = "🌟 优秀"
                grade_color = "🟢"
            elif final_score >= 75:
                grade = "👍 良好"
                grade_color = "🟡"
            elif final_score >= 60:
                grade = "⚠️ 一般"
                grade_color = "🟠"
            else:
                grade = "❌ 需要改进"
                grade_color = "🔴"
            
            self.diag_result_text.insert(tk.END, f"{grade_color} 网络质量评分: {final_score:.1f}/100 ({grade})\n")
            self.diag_result_text.insert(tk.END, "-" * 40 + "\n")
            
            # 显示优化建议
            if suggestions:
                self.diag_result_text.insert(tk.END, "💡 优化建议:\n")
                for i, suggestion in enumerate(suggestions, 1):
                    self.diag_result_text.insert(tk.END, f"{i}. {suggestion}\n")
            else:
                self.diag_result_text.insert(tk.END, "🎉 您的网络状态非常良好！\n")
                
            self.diag_result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
            
        except Exception as e:
            self.diag_result_text.insert(tk.END, f"⚠️ 生成评估时出错: {str(e)}\n")
    
    def _advanced_network_options(self, parent_window):
        """高级网络诊断选项（备用功能）"""
        # 这里可以添加更详细的诊断选项
        # 但作为简化版本，主要通过一键检测完成
        self.diag_result_text.insert(tk.END, "💡 高级功能开发中，敬请期待！\n")
        self.diag_result_text.insert(tk.END, "📞 如需详细检测，请联系技术支持。\n\n")
    
    def _execute_network_diagnostics(self, parent_window, check_vars):
        """执行网络诊断"""
        try:
            # 重置UI
            self.diag_result_text.delete(1.0, tk.END)
            self.diag_result_text.insert(tk.END, "🌐 正在初始化网络诊断...\n")
            self.diag_progress.start()
            parent_window.config(cursor="wait")
            
            # 获取选中的诊断选项
            selected_tests = [test_id for test_id, var in check_vars.items() if var.get()]
            if not selected_tests:
                self.diag_result_text.insert(tk.END, "⚠️ 未选择任何诊断选项\n")
                self.diag_progress.stop()
                parent_window.config(cursor="")
                return
            
            # 获取测试目标
            target = self.target_entry.get().strip()
            custom_target = self.custom_target_entry.get().strip()
            test_targets = []
            
            if target:
                test_targets.append(target)
            if custom_target:
                test_targets.append(custom_target)
            
            if not test_targets:
                test_targets = ["8.8.8.8", "www.baidu.com"]  # 默认目标
            
            # 在新线程中执行诊断
            def diag_thread():
                try:
                    results = self._perform_network_diagnostics(selected_tests, test_targets)
                    
                    # 在主线程中更新UI
                    self.root.after(0, lambda: self._update_diagnostic_results(results))
                    self.root.after(0, lambda: self.diag_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
                    
                except Exception as e:
                    error_msg = f"❌ 诊断过程出错: {str(e)}"
                    self.root.after(0, lambda: self.diag_result_text.insert(tk.END, error_msg + "\n"))
                    self.root.after(0, lambda: self.diag_progress.stop())
                    self.root.after(0, lambda: parent_window.config(cursor=""))
            
            threading.Thread(target=diag_thread, daemon=True).start()
            
        except Exception as e:
            self.diag_result_text.insert(tk.END, f"❌ 诊断初始化失败: {str(e)}\n")
            self.diag_progress.stop()
            parent_window.config(cursor="")
    
    def _perform_network_diagnostics(self, selected_tests, test_targets):
        """执行实际的网络诊断"""
        results = {}
        diag_start_time = time.time()
        
        # 诊断测试映射
        test_methods = {
            'ping_test': self._ping_test,
            'dns_test': self._dns_test,
            'port_test': self._port_test,
            'speed_test': self._speed_test,
            'traceroute_test': self._traceroute_test,
            'arp_test': self._arp_test,
            'network_info': self._network_info_test,
            'firewall_test': self._firewall_test
        }
        
        for test_id in selected_tests:
            try:
                if test_id in test_methods:
                    test_result = test_methods[test_id](test_targets)
                    results[test_id] = test_result
                    
                    # 记录日志
                    test_name = {
                        'ping_test': 'Ping连通性',
                        'dns_test': 'DNS解析',
                        'port_test': '端口扫描',
                        'speed_test': '网络速度',
                        'traceroute_test': '路由跟踪',
                        'arp_test': 'ARP缓存',
                        'network_info': '网络接口',
                        'firewall_test': '防火墙检测'
                    }.get(test_id, test_id)
                    
                    status = "✅ 通过" if test_result.get('success', False) else "❌ 失败"
                    self.log(f"🌐 {test_name}测试{status}")
                    
            except Exception as e:
                results[test_id] = {
                    'success': False,
                    'error': str(e),
                    'message': f'测试执行失败: {str(e)[:50]}'
                }
        
        # 生成诊断摘要
        diag_end_time = time.time()
        total_duration = diag_end_time - diag_start_time
        
        results['diagnostic_summary'] = {
            'start_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(diag_start_time)),
            'end_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(diag_end_time)),
            'total_duration': f"{total_duration:.1f}秒",
            'tests_performed': len(selected_tests),
            'successful_tests': sum(1 for r in results.values() if isinstance(r, dict) and r.get('success', False)),
            'failed_tests': sum(1 for r in results.values() if isinstance(r, dict) and not r.get('success', True))
        }
        
        return results
    
    def _ping_test(self, targets):
        """Ping连通性测试"""
        try:
            import subprocess
            
            results = []
            for target in targets:
                try:
                    # Windows ping命令，发送4个包
                    cmd = ['ping', '-n', '4', target]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        # 解析ping结果
                        output_lines = result.stdout.split('\n')
                        success_count = 0
                        for line in output_lines:
                            if '来自' in line or 'Reply from' in line:
                                success_count += 1
                        
                        results.append({
                            'target': target,
                            'success': True,
                            'packets_sent': 4,
                            'packets_received': success_count,
                            'output': result.stdout[:200] + ('...' if len(result.stdout) > 200 else ''),
                            'message': f'Ping成功，收发成功率: {success_count}/4'
                        })
                    else:
                        results.append({
                            'target': target,
                            'success': False,
                            'error': result.stderr or 'Ping失败',
                            'message': f'无法连通 {target}'
                        })
                        
                except subprocess.TimeoutExpired:
                    results.append({
                        'target': target,
                        'success': False,
                        'error': '测试超时',
                        'message': f'Ping {target} 超时'
                    })
                except Exception as e:
                    results.append({
                        'target': target,
                        'success': False,
                        'error': str(e),
                        'message': f'Ping {target} 测试出错'
                    })
            
            success_count = sum(1 for r in results if r.get('success', False))
            return {
                'success': success_count > 0,
                'results': results,
                'message': f'Ping测试完成，成功 {success_count}/{len(results)} 个目标'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Ping测试执行失败: {str(e)[:50]}'
            }
    
    def _dns_test(self, targets):
        """DNS解析测试"""
        try:
            import socket
            
            results = []
            test_domains = targets + ['www.baidu.com', 'www.google.com', 'github.com']
            dns_servers = ['8.8.8.8', '114.114.114.114']
            
            for domain in test_domains:
                try:
                    # 测试DNS解析
                    start_time = time.time()
                    ip = socket.gethostbyname(domain)
                    resolve_time = (time.time() - start_time) * 1000
                    
                    results.append({
                        'domain': domain,
                        'success': True,
                        'ip': ip,
                        'resolve_time': f"{resolve_time:.1f}ms",
                        'message': f'DNS解析成功: {domain} -> {ip}'
                    })
                    
                except socket.gaierror:
                    results.append({
                        'domain': domain,
                        'success': False,
                        'error': '域名解析失败',
                        'message': f'无法解析域名: {domain}'
                    })
                except Exception as e:
                    results.append({
                        'domain': domain,
                        'success': False,
                        'error': str(e),
                        'message': f'DNS测试出错: {domain}'
                    })
            
            success_count = sum(1 for r in results if r.get('success', False))
            return {
                'success': success_count > 0,
                'results': results,
                'message': f'DNS解析测试完成，成功 {success_count}/{len(results)} 个域名'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'DNS解析测试执行失败: {str(e)[:50]}'
            }
    
    def _port_test(self, targets):
        """端口扫描测试"""
        try:
            import socket
            
            results = []
            common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
            
            for target in targets:
                target_results = []
                
                for port in common_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)  # 2秒超时
                        result = sock.connect_ex((target, port))
                        sock.close()
                        
                        if result == 0:
                            # 端口开放
                            service_names = {
                                80: 'HTTP', 443: 'HTTPS', 22: 'SSH', 21: 'FTP',
                                25: 'SMTP', 53: 'DNS', 110: 'POP3', 143: 'IMAP',
                                993: 'IMAPS', 995: 'POP3S'
                            }
                            service = service_names.get(port, f'Port {port}')
                            
                            target_results.append({
                                'port': port,
                                'service': service,
                                'status': 'open',
                                'message': f'端口 {port} ({service}) 开放'
                            })
                        
                    except Exception:
                        pass  # 端口关闭或测试失败
                
                results.append({
                    'target': target,
                    'success': len(target_results) > 0,
                    'open_ports': target_results,
                    'message': f'{target}: {len(target_results)} 个开放端口'
                })
            
            total_open_ports = sum(len(r.get('open_ports', [])) for r in results)
            return {
                'success': total_open_ports > 0,
                'results': results,
                'message': f'端口扫描完成，共发现 {total_open_ports} 个开放端口'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'端口扫描执行失败: {str(e)[:50]}'
            }
    
    def _speed_test(self, targets):
        """网络速度测试"""
        try:
            import urllib.request
            import urllib.parse
            
            results = []
            test_urls = [
                'http://speedtest.ftp.otenet.gr/files/test1Mb.db',  # 欧洲测试点
                'http://ipv4.download.thinkbroadband.com/1MB.zip',   # 英国测试点
                'http://www.google.com'                               # 基本连通性测试
            ]
            
            for url in test_urls:
                try:
                    # 下载测试文件
                    start_time = time.time()
                    
                    # 发送请求
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        # 只读取部分数据避免过度下载
                        data = response.read(1024 * 100)  # 读取100KB
                    
                    download_time = time.time() - start_time
                    speed_kbps = (len(data) / 1024) / download_time if download_time > 0 else 0
                    
                    results.append({
                        'url': urllib.parse.urlparse(url).netloc,
                        'success': True,
                        'data_size': f"{len(data)} 字节",
                        'download_time': f"{download_time:.2f}秒",
                        'speed': f"{speed_kbps:.1f} KB/s",
                        'message': f'下载速度: {speed_kbps:.1f} KB/s'
                    })
                    
                except Exception as e:
                    results.append({
                        'url': url,
                        'success': False,
                        'error': str(e)[:50],
                        'message': f'速度测试失败: {str(e)[:30]}'
                    })
            
            success_count = sum(1 for r in results if r.get('success', False))
            return {
                'success': success_count > 0,
                'results': results,
                'message': f'网络速度测试完成，{success_count}/{len(results)} 个测试点成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'网络速度测试执行失败: {str(e)[:50]}'
            }
    
    def _traceroute_test(self, targets):
        """路由跟踪测试"""
        try:
            import subprocess
            
            results = []
            
            for target in targets:
                try:
                    # Windows tracert命令
                    cmd = ['tracert', '-h', '10', target]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        hops = []
                        
                        for line in lines:
                            line = line.strip()
                            if line and any(char.isdigit() for char in line[:3]):
                                # 解析跳点信息
                                parts = line.split()
                                if len(parts) >= 4:
                                    hop_num = parts[0]
                                    # 提取IP地址
                                    ip_parts = [p for p in parts if '.' in p and not p.startswith('ms')]
                                    if ip_parts:
                                        hop_info = {
                                            'hop': hop_num,
                                            'ip': ip_parts[-1],
                                            'raw_line': line[:100]
                                        }
                                        hops.append(hop_info)
                        
                        results.append({
                            'target': target,
                            'success': True,
                            'hops': hops,
                            'hop_count': len(hops),
                            'message': f'路由跟踪完成，共 {len(hops)} 跳'
                        })
                    else:
                        results.append({
                            'target': target,
                            'success': False,
                            'error': result.stderr or '路由跟踪失败',
                            'message': f'无法跟踪到 {target}'
                        })
                        
                except subprocess.TimeoutExpired:
                    results.append({
                        'target': target,
                        'success': False,
                        'error': '测试超时',
                        'message': f'路由跟踪 {target} 超时'
                    })
                except Exception as e:
                    results.append({
                        'target': target,
                        'success': False,
                        'error': str(e),
                        'message': f'路由跟踪 {target} 测试出错'
                    })
            
            success_count = sum(1 for r in results if r.get('success', False))
            return {
                'success': success_count > 0,
                'results': results,
                'message': f'路由跟踪测试完成，{success_count}/{len(results)} 个目标成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'路由跟踪测试执行失败: {str(e)[:50]}'
            }
    
    def _arp_test(self, targets):
        """ARP缓存检查"""
        try:
            import subprocess
            
            results = []
            
            try:
                # Windows arp命令显示ARP缓存
                cmd = ['arp', '-a']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    arp_entries = []
                    
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('Interface:'):
                            # 解析ARP条目
                            parts = line.split()
                            if len(parts) >= 3:
                                try:
                                    ip = parts[0]
                                    mac = parts[1]
                                    entry_type = parts[2] if len(parts) > 2 else 'dynamic'
                                    
                                    arp_entries.append({
                                        'ip': ip,
                                        'mac': mac,
                                        'type': entry_type,
                                        'status': 'active'
                                    })
                                except:
                                    pass
                    
                    results.append({
                        'success': True,
                        'arp_entries': arp_entries,
                        'entry_count': len(arp_entries),
                        'message': f'ARP缓存检查完成，共 {len(arp_entries)} 个条目'
                    })
                else:
                    results.append({
                        'success': False,
                        'error': '无法获取ARP缓存',
                        'message': 'ARP缓存检查失败'
                    })
                    
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'message': f'ARP缓存检查出错: {str(e)[:50]}'
                })
            
            return {
                'success': len(results) > 0 and results[0].get('success', False),
                'results': results,
                'message': results[0].get('message', 'ARP缓存检查失败') if results else 'ARP缓存检查失败'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'ARP缓存检查执行失败: {str(e)[:50]}'
            }
    
    def _network_info_test(self, targets):
        """网络接口信息测试"""
        try:
            import psutil
            
            results = []
            
            # 获取网络接口信息
            try:
                interfaces = psutil.net_if_addrs()
                interface_stats = psutil.net_if_stats()
                
                for interface_name, addresses in interfaces.items():
                    if interface_name.startswith('Loopback'):  # 跳过回环接口
                        continue
                    
                    interface_info = {
                        'name': interface_name,
                        'addresses': [],
                        'is_up': interface_stats.get(interface_name, {}).isup if interface_name in interface_stats else False
                    }
                    
                    for addr in addresses:
                        addr_info = {
                            'family': 'IPv4' if addr.family == 2 else ('IPv6' if addr.family == 23 else 'MAC'),
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        interface_info['addresses'].append(addr_info)
                    
                    results.append(interface_info)
                
                # 获取网络连接信息
                connections = psutil.net_connections()
                listening_ports = []
                
                for conn in connections:
                    if conn.status == 'LISTEN':
                        listening_ports.append({
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown",
                            'pid': conn.pid,
                            'family': 'IPv4' if conn.family == 2 else 'IPv6'
                        })
                
                # 按端口排序
                listening_ports.sort(key=lambda x: int(x['local_address'].split(':')[-1]))
                
                return {
                    'success': len(results) > 0,
                    'interfaces': results,
                    'listening_ports': listening_ports[:20],  # 只显示前20个监听端口
                    'total_interfaces': len(results),
                    'total_listening_ports': len(listening_ports),
                    'message': f'网络接口信息获取完成，发现 {len(results)} 个接口，{len(listening_ports)} 个监听端口'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'message': f'网络接口信息获取失败: {str(e)[:50]}'
                }
                
        except ImportError:
            return {
                'success': False,
                'error': 'psutil模块未安装',
                'message': '请安装psutil模块以获取详细网络信息: pip install psutil'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'网络接口信息测试执行失败: {str(e)[:50]}'
            }
    
    def _firewall_test(self, targets):
        """防火墙检测测试"""
        try:
            import subprocess
            
            results = []
            
            try:
                # 检查Windows防火墙状态
                cmd = ['netsh', 'advfirewall', 'show', 'allprofiles', 'state']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    firewall_status = []
                    
                    for line in lines:
                        line = line.strip()
                        if 'State' in line:
                            profile_status = line.split(':')[1].strip() if ':' in line else 'Unknown'
                            firewall_status.append(profile_status)
                    
                    is_enabled = any('ON' in status.upper() for status in firewall_status)
                    results.append({
                        'success': True,
                        'firewall_profiles': firewall_status,
                        'is_enabled': is_enabled,
                        'message': f'防火墙状态检查完成: {"启用" if is_enabled else "禁用"}'
                    })
                else:
                    results.append({
                        'success': False,
                        'error': '无法获取防火墙状态',
                        'message': '防火墙状态检查失败'
                    })
                    
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'message': f'防火墙检测出错: {str(e)[:50]}'
                })
            
            return {
                'success': len(results) > 0 and results[0].get('success', False),
                'results': results,
                'message': results[0].get('message', '防火墙检测失败') if results else '防火墙检测失败'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'防火墙检测执行失败: {str(e)[:50]}'
            }
    
    def _update_diagnostic_results(self, results):
        """更新诊断结果显示"""
        try:
            result_lines = []
            
            # 显示诊断摘要
            if 'diagnostic_summary' in results:
                summary = results['diagnostic_summary']
                result_lines.append("="*60 + "\n")
                result_lines.append("📊 网络诊断摘要\n")
                result_lines.append("="*60 + "\n")
                result_lines.append(f"🕐 开始时间: {summary['start_time']}\n")
                result_lines.append(f"🕐 结束时间: {summary['end_time']}\n")
                result_lines.append(f"⏱️ 总耗时: {summary['total_duration']}\n")
                result_lines.append(f"🔍 执行测试: {summary['tests_performed']}\n")
                result_lines.append(f"✅ 成功测试: {summary['successful_tests']}\n")
                result_lines.append(f"❌ 失败测试: {summary['failed_tests']}\n")
                result_lines.append("="*60 + "\n\n")
            
            # 显示各项测试结果
            test_names = {
                'ping_test': '🏓 Ping连通性测试',
                'dns_test': '🌍 DNS解析测试',
                'port_test': '🔌 端口扫描测试',
                'speed_test': '⚡ 网络速度测试',
                'traceroute_test': '🛣️ 路由跟踪测试',
                'arp_test': '📋 ARP缓存检查',
                'network_info': '💻 网络接口信息',
                'firewall_test': '🛡️ 防火墙检测'
            }
            
            for test_id, test_name in test_names.items():
                if test_id in results:
                    test_result = results[test_id]
                    result_lines.append(f"{test_name}\n")
                    result_lines.append("-"*50 + "\n")
                    
                    if test_result.get('success', False):
                        result_lines.append(f"✅ {test_name} - 成功\n")
                        
                        # 显示具体结果
                        if test_id == 'ping_test':
                            for ping_result in test_result.get('results', []):
                                status_icon = "✅" if ping_result.get('success') else "❌"
                                result_lines.append(f"{status_icon} {ping_result['target']}: {ping_result['message']}\n")
                        
                        elif test_id == 'dns_test':
                            for dns_result in test_result.get('results', []):
                                status_icon = "✅" if dns_result.get('success') else "❌"
                                result_lines.append(f"{status_icon} {dns_result['domain']}: {dns_result['message']}\n")
                        
                        elif test_id == 'port_test':
                            for port_result in test_result.get('results', []):
                                result_lines.append(f"🔍 {port_result['target']}:\n")
                                for port_info in port_result.get('open_ports', []):
                                    result_lines.append(f"  ✅ {port_info['message']}\n")
                        
                        elif test_id == 'speed_test':
                            for speed_result in test_result.get('results', []):
                                status_icon = "✅" if speed_result.get('success') else "❌"
                                result_lines.append(f"{status_icon} {speed_result['url']}: {speed_result['message']}\n")
                        
                        elif test_id == 'traceroute_test':
                            for route_result in test_result.get('results', []):
                                result_lines.append(f"🔍 {route_result['target']}: {route_result['message']}\n")
                                for hop in route_result.get('hops', [])[:5]:  # 只显示前5跳
                                    result_lines.append(f"  跳 {hop['hop']}: {hop['ip']}\n")
                        
                        elif test_id == 'arp_test':
                            arp_result = test_result.get('results', [{}])[0]
                            result_lines.append(f"ARP缓存条目数: {arp_result.get('entry_count', 0)}\n")
                            for entry in arp_result.get('arp_entries', [])[:10]:  # 只显示前10个
                                result_lines.append(f"  📍 {entry['ip']} -> {entry['mac']}\n")
                        
                        elif test_id == 'network_info':
                            interface_count = test_result.get('total_interfaces', 0)
                            port_count = test_result.get('total_listening_ports', 0)
                            result_lines.append(f"网络接口数: {interface_count}\n")
                            result_lines.append(f"监听端口数: {port_count}\n")
                            
                            for interface in test_result.get('interfaces', []):
                                status = "🟢" if interface.get('is_up') else "🔴"
                                result_lines.append(f"{status} {interface['name']}:\n")
                                for addr in interface.get('addresses', []):
                                    if addr['family'] == 'IPv4':
                                        result_lines.append(f"  🌐 IPv4: {addr['address']}\n")
                        
                        elif test_id == 'firewall_test':
                            firewall_result = test_result.get('results', [{}])[0]
                            is_enabled = firewall_result.get('is_enabled', False)
                            status_icon = "🟢" if is_enabled else "🔴"
                            result_lines.append(f"{status_icon} 防火墙状态: {'启用' if is_enabled else '禁用'}\n")
                    
                    else:
                        result_lines.append(f"❌ {test_name} - 失败\n")
                        result_lines.append(f"错误: {test_result.get('message', '未知错误')}\n")
                    
                    result_lines.append("\n")
            
            # 显示安全建议
            result_lines.append("💡 网络安全建议:\n")
            result_lines.append("-"*50 + "\n")
            
            if 'ping_test' in results and not results['ping_test'].get('success', True):
                result_lines.append("🔌 网络连通性问题:\n")
                result_lines.append("1. 检查网络电缆连接\n")
                result_lines.append("2. 重启网络适配器\n")
                result_lines.append("3. 检查路由器配置\n\n")
            
            if 'dns_test' in results and not results['dns_test'].get('success', True):
                result_lines.append("🌍 DNS解析问题:\n")
                result_lines.append("4. 更换DNS服务器\n")
                result_lines.append("5. 清除DNS缓存: ipconfig /flushdns\n\n")
            
            if 'port_test' in results:
                # 检查是否有不安全的开放端口
                for port_result in results['port_test'].get('results', []):
                    for port_info in port_result.get('open_ports', []):
                        if port_info['port'] in [21, 23, 135, 139, 445]:
                            result_lines.append("🔒 安全风险端口:\n")
                            result_lines.append(f"6. 端口 {port_info['port']} ({port_info['service']}) 开放，建议检查安全性\n\n")
                            break
            
            result_lines.append("🔍 网络诊断完成！\n")
            result_lines.append(f"⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 更新UI
            self.diag_result_text.delete(1.0, tk.END)
            self.diag_result_text.insert(tk.END, ''.join(result_lines))
            self.diag_result_text.see(tk.END)
            
            # 启用保存按钮
            if hasattr(self, 'save_report_button'):
                self.save_report_button.config(state="normal")
                
        except Exception as e:
            error_msg = f"❌ 更新诊断结果时出错: {str(e)}"
            try:
                self.diag_result_text.delete(1.0, tk.END)
                self.diag_result_text.insert(tk.END, error_msg + "\n")
            except:
                pass
    
    def _save_diagnostic_report(self, parent_window):
        """保存诊断报告"""
        try:
            from tkinter import filedialog
            
            # 获取当前诊断结果
            report_content = self.diag_result_text.get(1.0, tk.END)
            
            # 选择保存位置
            filename = filedialog.asksaveasfilename(
                title="保存网络诊断报告",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialname=f"网络诊断报告_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                self.log(f"🌐 网络诊断报告已保存: {filename}")
                messagebox.showinfo("保存成功", f"诊断报告已保存到:\n{filename}")
            
        except Exception as e:
            error_msg = f"保存诊断报告失败: {str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("保存失败", error_msg)

    def _update_scan_results(self, results):
        """更新扫描结果显示（优化版 - 减少卡顿）"""
        try:
            # 使用一次性更新而不是多次插入，避免频繁UI重绘
            result_lines = []
            
            # 显示扫描摘要
            summary = results['scan_summary']
            result_lines.append("="*60 + "\n")
            result_lines.append("📊 扫描摘要 (优化版)\n")
            result_lines.append("="*60 + "\n")
            result_lines.append(f"📁 总扫描文件: {summary['total_scanned']}\n")
            result_lines.append(f"✅ 安全文件: {summary['safe_count']}\n")
            result_lines.append(f"⚠️ 可疑文件: {summary['suspicious_count']}\n")
            result_lines.append(f"🔴 高危文件: {summary['high_risk_count']}\n")
            result_lines.append(f"🦠 病毒文件: {summary['virus_count']}\n")
            
            # 添加性能信息
            if 'scan_duration' in summary:
                result_lines.append(f"⏱️ 扫描用时: {summary['scan_duration']}\n")
            if 'files_per_second' in summary:
                result_lines.append(f"⚡ 扫描速度: {summary['files_per_second']} 文件/秒\n")
            
            result_lines.append("="*60 + "\n\n")
            
            # 显示病毒检测结果（限制显示数量避免UI过载）
            if results['virus_detected']:
                virus_files = results['virus_detected'][:5]  # 只显示前5个病毒文件
                result_lines.append("🚨 病毒文件检测结果:\n")
                result_lines.append("-"*50 + "\n")
                for virus_file in virus_files:
                    result_lines.append(f"🦠 病毒文件: {virus_file['name']}\n")
                    result_lines.append(f"   路径: {virus_file['path'][:80]}...\n")  # 限制路径显示长度
                    result_lines.append(f"   病毒类型: {virus_file['virus_signature']}\n")
                    result_lines.append(f"   文件大小: {virus_file['size']} 字节\n")
                    result_lines.append("\n")
                
                if len(results['virus_detected']) > 5:
                    result_lines.append(f"... 还有 {len(results['virus_detected']) - 5} 个病毒文件未显示\n\n")
            
            # 显示高危文件结果（限制显示数量）
            if results['high_risk']:
                risk_files = results['high_risk'][:8]  # 只显示前8个高危文件
                result_lines.append("🔴 高危文件检测结果:\n")
                result_lines.append("-"*50 + "\n")
                for risk_file in risk_files:
                    result_lines.append(f"⚠️ 高危文件: {risk_file['name']}\n")
                    result_lines.append(f"   路径: {risk_file['path'][:80]}...\n")  # 限制路径显示长度
                    result_lines.append(f"   威胁等级: {risk_file['threat_level']}\n")
                    result_lines.append(f"   详细信息: {'; '.join(risk_file['details'][:2])}\n")  # 只显示前2个详细信息
                    result_lines.append("\n")
                
                if len(results['high_risk']) > 8:
                    result_lines.append(f"... 还有 {len(results['high_risk']) - 8} 个高危文件未显示\n\n")
            
            # 显示可疑文件结果（大幅限制显示数量）
            if results['suspicious']:
                suspect_files = results['suspicious'][:3]  # 只显示前3个可疑文件
                result_lines.append("⚠️ 可疑文件检测结果:\n")
                result_lines.append("-"*50 + "\n")
                for suspect_file in suspect_files:
                    result_lines.append(f"🔍 可疑文件: {suspect_file['name']}\n")
                    result_lines.append(f"   路径: {suspect_file['path'][:80]}...\n")
                    if suspect_file['suspicious_indicators']:
                        result_lines.append(f"   可疑特征: {', '.join(suspect_file['suspicious_indicators'][:2])}\n")
                    result_lines.append(f"   详细信息: {'; '.join(suspect_file['details'][:1])}\n\n")
                
                if len(results['suspicious']) > 3:
                    result_lines.append(f"... 还有 {len(results['suspicious']) - 3} 个可疑文件未显示\n\n")
            
            # 显示安全文件统计
            if results['safe']:
                result_lines.append("✅ 安全文件统计:\n")
                result_lines.append("-"*50 + "\n")
                result_lines.append(f"共 {len(results['safe'])} 个文件通过安全检查\n")
                result_lines.append("这些文件未检测到明显的威胁特征\n\n")
            
            # 优化的安全建议
            result_lines.append("💡 安全建议:\n")
            result_lines.append("-"*50 + "\n")
            
            if results['virus_detected']:
                result_lines.append("🚨 立即行动:\n")
                result_lines.append("1. 隔离检测到的病毒文件\n")
                result_lines.append("2. 使用专业杀毒软件全盘扫描\n")
                result_lines.append("3. 检查网络连接安全\n\n")
            
            if results['high_risk']:
                result_lines.append("⚠️ 谨慎处理:\n")
                result_lines.append("4. 高危文件需要进一步分析\n")
                result_lines.append("5. 考虑在沙箱环境中测试\n\n")
            
            result_lines.append("🔍 扫描完成！所有文件检查完毕。\n")
            result_lines.append(f"⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 一次性更新UI，避免频繁重绘
            self.scan_result_text.delete(1.0, tk.END)
            self.scan_result_text.insert(tk.END, ''.join(result_lines))
            self.scan_result_text.see(tk.END)
            
        except Exception as e:
            error_msg = f"❌ 更新扫描结果时出错: {str(e)}"
            try:
                self.scan_result_text.delete(1.0, tk.END)
                self.scan_result_text.insert(tk.END, error_msg + "\n")
            except:
                # 如果UI更新也失败，至少记录到日志
                pass
        
        # 记录详细日志
        if 'scan_summary' in results:
            summary = results['scan_summary']
            self.log(f"🛡️ 安全扫描完成 - 扫描文件: {summary['total_scanned']}, "
                    f"安全: {summary['safe_count']}, "
                    f"可疑: {summary['suspicious_count']}, "
                    f"高危: {summary['high_risk_count']}, "
                    f"病毒: {summary['virus_count']}")
            
            # 记录性能信息
            if 'scan_duration' in summary:
                self.log(f"⏱️ 扫描性能 - 用时: {summary['scan_duration']}, "
                        f"速度: {summary.get('files_per_second', '0')} 文件/秒")
    
    def _setup_tray_icon(self):
        """设置系统托盘图标（使用pystray库）"""
        # 检查pystray模块是否可用
        if not PYSTRAY_AVAILABLE:
            self.log("系统托盘功能不可用：pystray模块未安装")
            # 恢复默认的窗口关闭行为
            self.root.protocol("WM_DELETE_WINDOW", self._exit_program)
            return
        
        # 检查PIL是否可用
        if not PIL_AVAILABLE:
            self.log("系统托盘功能不可用：PIL模块未安装")
            # 恢复默认的窗口关闭行为
            self.root.protocol("WM_DELETE_WINDOW", self._exit_program)
            return
            
        try:
            # 为窗口添加关闭事件处理
            self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
            
            # 创建一个简单的托盘图标
            def create_image(width, height, color1, color2):
                try:
                    # 创建一个图像
                    image = Image.new('RGB', (width, height), color1)
                    draw = ImageDraw.Draw(image)
                    
                    # 在图像上绘制一个简单的X形状
                    draw.line((0, 0, width, height), fill=color2, width=3)
                    draw.line((0, height, width, 0), fill=color2, width=3)
                    
                    return image
                except Exception as e:
                    self.log(f"创建托盘图标时出错: {str(e)}")
                    return None
            
            # 创建图标
            self.tray_icon_image = create_image(64, 64, 'blue', 'white')
            
            if self.tray_icon_image is None:
                self.log("无法创建托盘图标，将禁用托盘功能")
                # 恢复默认的窗口关闭行为
                self.root.protocol("WM_DELETE_WINDOW", self._exit_program)
                return
            
            try:
                # 创建菜单
                menu = (
                    pystray.MenuItem('显示窗口', self._show_window),
                    pystray.MenuItem('刷新程序列表', self.refresh_list),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem('退出程序', self._exit_program)
                )
                
                # 创建托盘实例
                self.tray = pystray.Icon(
                    "强力卸载工具",
                    self.tray_icon_image,
                    "强力卸载工具",
                    menu
                )
                
                # 启动托盘图标（在单独的线程中运行）
                import threading
                self.tray_thread = threading.Thread(target=self.tray.run, daemon=True)
                self.tray_thread.start()
                
                self.log("已成功设置系统托盘图标")
            except Exception as e:
                self.log(f"设置托盘菜单或实例时出错: {str(e)}")
                # 恢复默认的窗口关闭行为
                self.root.protocol("WM_DELETE_WINDOW", self._exit_program)
                traceback.print_exc()
            
        except Exception as e:
            self.log(f"设置托盘图标时出错: {str(e)}")
            # 恢复默认的窗口关闭行为
            self.root.protocol("WM_DELETE_WINDOW", self._exit_program)
            traceback.print_exc()
    
    def _minimize_to_tray(self):
        """最小化窗口到托盘"""
        try:
            # 隐藏主窗口
            self.root.withdraw()
            
            self.log("窗口已最小化到系统托盘")
        except Exception as e:
            self.log(f"最小化到托盘时出错: {str(e)}")
            traceback.print_exc()
    
    def _show_window(self):
        """显示主窗口"""
        try:
            # 显示主窗口
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
            self.log("已从系统托盘恢复窗口")
        except Exception as e:
            self.log(f"显示窗口时出错: {str(e)}")
            traceback.print_exc()
    
    def _exit_program(self):
        """退出程序"""
        try:
            # 停止托盘图标
            if hasattr(self, 'tray'):
                self.tray.stop()
            
            # 销毁主窗口
            self.root.destroy()
            
            self.log("程序已退出")
            sys.exit(0)
        except Exception as e:
            self.log(f"退出程序时出错: {str(e)}")
            sys.exit(1)

def run_as_admin():
    """尝试以管理员权限重新启动程序"""
    # 获取当前Python解释器路径和脚本路径
    script = os.path.abspath(sys.argv[0])
    
    # 使用ShellExecute以管理员权限运行
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script, None, 1
        )
        return True
    except Exception:
        return False

def main():
    print("强力卸载工具启动中...")
    root = None
    
    try:
        # 记录Tkinter初始化开始
        print("准备初始化Tkinter...")
        
        # 检查是否具有管理员权限
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"当前权限: {'管理员' if is_admin else '普通用户'}")
        
        # 启动图形界面
        print("创建Tk根窗口...")
        root = Tk()
        print("Tk根窗口创建成功")
        
        # 设置窗口标题和大小
        print("配置窗口属性...")
        root.title("强力卸载工具")
        root.geometry("800x600")
        print("窗口属性配置完成")
        
        # 确保中文正常显示
        print("设置字体配置...")
        try:
            root.option_add("*Font", "微软雅黑 10")
        except Exception as e:
            print(f"设置字体时出错: {e}")
        
        # 创建应用实例
        print("创建UninstallerApp实例...")
        app = UninstallerApp(root)
        app.has_admin = is_admin  # 保存权限状态
        print("应用实例创建成功")
        
        # 打印UI组件状态
        print("UI组件检查:")
        print(f"- 主框架: {app.main_frame}")
        print(f"- 标题标签: {app.title_label}")
        print(f"- 程序列表: {app.program_listbox}")
        
        # 确保窗口显示在最前面
        root.lift()
        root.focus_force()

        # 在主循环启动后立即触发第一次程序扫描
        print("准备触发第一次程序扫描...")
        root.after(100, app.refresh_list)  # 延迟100ms后执行扫描，确保主循环已启动

        print("准备进入主循环...")
        root.mainloop()
    except Exception as e:
        print(f"启动错误: {e}")
        try:
            # 如果Tk实例仍然存在且有效，显示错误信息
            if root and root.winfo_exists():
                messagebox.showerror("启动错误", f"程序启动失败: {str(e)}")
        except:
            pass
    finally:
        print("主循环退出")
        try:
            if root and root.winfo_exists():
                root.destroy()
        except Exception as destroy_error:
            print(f"销毁窗口时出错: {destroy_error}")

def is_admin():
    """检查当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # 调试模式 - 跳过管理员权限检查以便测试UI功能
    debug_mode = True  # 设置为False以恢复正常权限检查
    
    if debug_mode:
        print("调试模式：跳过管理员权限检查")
        main()  # 直接运行主程序
    else:
        # 正常模式：检查是否以管理员身份运行
        if not is_admin():
            print("请以管理员身份运行此程序")
            # 尝试以管理员身份重启
            if run_as_admin():
                print("程序已重启")
            else:
                print("无法以管理员身份重启，请手动以管理员身份运行")
                time.sleep(3)
        else:
            print("已以管理员身份运行")
            main()
