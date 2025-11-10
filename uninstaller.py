import os
import sys
import subprocess
import winreg
import shutil
import time
import ctypes
import psutil
import random
from tkinter import Tk, Label, Listbox, Button, Scrollbar, Frame, messagebox, Entry, Checkbutton, BooleanVar, Text, font, filedialog
from tkinter import ttk
import threading
import tkinter as tk
import re
import stat
import win32api
import win32con
import win32process
import win32security
import win32job

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
        self.root.title("浩讯亿通强力卸载工具")
        self.root.geometry("800x800")
        self.root.resizable(True, True)
        
        # 基本颜色设置
        self.bg_color = "#ffffff"  # 白色背景
        self.text_color = "#333333"  # 黑色文字
        self.button_color = "#4a90e2"  # 蓝色按钮
        self.list_bg = "#f9f9f9"  # 列表背景
        self.highlight_color = "#357abd"  # 高亮色
        
        # 设置窗口背景
        self.root.configure(bg=self.bg_color)
        
        # 初始化权限状态
        self.has_admin = False
        
        # 创建主框架
        self.main_frame = Frame(root, bg=self.bg_color, padx=10, pady=10)
        self.main_frame.pack(fill="both", expand=True)
        
        # 标题标签
        self.title_label = Label(
            self.main_frame,
            text="电脑急救强力卸载工具",
            font=("微软雅黑", 16, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.pack(pady=10)
        
        # 搜索框
        self.search_frame = Frame(self.main_frame, bg=self.bg_color)
        self.search_frame.pack(fill="x", pady=5)
        
        Label(self.search_frame, text="搜索:", bg=self.bg_color).pack(side="left")
        self.search_entry = Entry(self.search_frame, width=50)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # 进度条
        self.progress_frame = Frame(self.main_frame, bg=self.bg_color)
        self.progress_frame.pack(fill="x", pady=5)
        
        self.progress_label = Label(self.progress_frame, text="扫描进度:", bg=self.bg_color)
        self.progress_label.pack(side="left")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            length=100,
            mode='determinate'
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        self.progress_percent = Label(self.progress_frame, text="0%", bg=self.bg_color, width=5)
        self.progress_percent.pack(side="left")
        
        # 程序列表
        self.list_frame = Frame(self.main_frame, bg=self.bg_color)
        self.list_frame.pack(fill="both", expand=True, pady=5)
        
        self.scrollbar = Scrollbar(self.list_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        self.program_listbox = Listbox(
            self.list_frame,
            yscrollcommand=self.scrollbar.set,
            width=80,
            height=15,
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
        
        # 自动刷新列表
        self.refresh_list()
        
        # 卸载选项区域
        self.options_frame = Frame(self.main_frame, bg=self.bg_color, pady=5)
        self.options_frame.pack(fill="x")
        
        self.force_delete = BooleanVar(value=True)
        self.force_delete_check = Checkbutton(
            self.options_frame,
            text="强力删除残留文件",
            variable=self.force_delete,
            bg=self.bg_color
        )
        self.force_delete_check.pack(side="left", padx=10)
        
        self.clean_registry = BooleanVar(value=True)
        self.clean_registry_check = Checkbutton(
            self.options_frame,
            text="清理注册表项",
            variable=self.clean_registry,
            bg=self.bg_color
        )
        self.clean_registry_check.pack(side="left", padx=10)
        
        # 新增：设备残留清理选项
        self.clean_device_residuals = BooleanVar(value=False)  # 默认关闭，需要用户主动选择
        self.clean_device_residuals_check = Checkbutton(
            self.options_frame,
            text="清理设备和驱动器残留",
            variable=self.clean_device_residuals,
            bg=self.bg_color
        )
        self.clean_device_residuals_check.pack(side="left", padx=10)
        
        # 顽固程序处理选项
        self.tough_program_frame = Frame(self.main_frame, bg=self.bg_color, pady=5)
        self.tough_program_frame.pack(fill="x")
        
        self.clean_startup = BooleanVar(value=True)
        self.clean_startup_check = Checkbutton(
            self.tough_program_frame,
            text="清理启动项",
            variable=self.clean_startup,
            bg=self.bg_color
        )
        self.clean_startup_check.pack(side="left", padx=10)
        
        self.stop_services = BooleanVar(value=True)
        self.stop_services_check = Checkbutton(
            self.tough_program_frame,
            text="停止相关服务",
            variable=self.stop_services,
            bg=self.bg_color
        )
        self.stop_services_check.pack(side="left", padx=10)
        
        self.unlock_files = BooleanVar(value=True)
        self.unlock_files_check = Checkbutton(
            self.tough_program_frame,
            text="解锁锁定文件",
            variable=self.unlock_files,
            bg=self.bg_color
        )
        self.unlock_files_check.pack(side="left", padx=10)
        
        # 按钮区域
        self.button_frame = Frame(self.main_frame, bg=self.bg_color)
        self.button_frame.pack(fill="x", pady=10)
        
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
        
        self.shred_button = Button(
            self.button_frame,
            text="文件粉碎",
            command=self.file_shredder,
            bg="#9b59b6",
            fg="white",
            width=12
        )
        self.shred_button.pack(side="left", padx=5)
        
        self.quit_button = Button(
            self.button_frame,
            text="退出",
            command=root.quit,
            bg="#95a5a6",
            fg="white",
            width=12
        )
        self.quit_button.pack(side="right", padx=5)
        
        # 日志区域
        self.log_frame = Frame(self.main_frame, bg=self.bg_color)
        self.log_frame.pack(fill="both", expand=True, pady=5)
        
        Label(self.log_frame, text="操作日志:", bg=self.bg_color).pack(anchor="w")
        
        self.log_text = Text(self.log_frame, height=5, width=80)
        self.log_text.pack(fill="both", expand=True)
        
        # 初始化数据
        self.programs = []
        self.filtered_programs = []
        
        # 记录日志
        self.log("程序启动成功！")
    
    def log(self, message):
        """显示日志信息"""
        try:
            # 添加时间戳
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {message}"
            
            self.log_text.config(state="normal")
            self.log_text.insert("end", log_message + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def check_admin(self):
        """检查程序是否以管理员权限运行"""
        return self.has_admin
    
    def update_permission_display(self):
        """更新权限显示标签"""
        try:
            self.permission_label.config(
                text="以管理员权限运行" if self.has_admin else "以普通用户权限运行",
                bg=self.success_color if self.has_admin else self.warning_color
            )
        except Exception as e:
            self.log(f"更新权限显示出错: {str(e)}")
    

    
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
        except:
            pass
    
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
        """增强版文件删除方法，包含多种解锁和删除策略"""
        if not os.path.exists(file_path):
            return True
        
        self.log(f"开始尝试删除文件: {file_path}")
        
        # 1. 始终尝试解锁文件，无论设置如何
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
    
    def _force_delete_directory(self, path):
        """增强版：强制删除目录，包括子目录和所有文件"""
        if not os.path.exists(path):
            return True
        
        self.log(f"开始强制删除目录: {path}")
        
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
    
    def _shred_file(self, file_path, passes=3):
        """粉碎单个文件，通过多次写入随机数据确保无法恢复"""
        if not os.path.isfile(file_path):
            return False
        
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 修改文件权限
            os.chmod(file_path, 0o777)
            
            # 执行多次覆盖
            for pass_num in range(passes):
                with open(file_path, "rb+") as f:
                    # 生成随机数据
                    random_data = bytearray(random.getrandbits(8) for _ in range(min(1024*1024, file_size)))
                    
                    # 分块写入
                    remaining = file_size
                    f.seek(0)
                    while remaining > 0:
                        chunk_size = min(len(random_data), remaining)
                        f.write(random_data[:chunk_size])
                        remaining -= chunk_size
                        # 刷新缓冲区确保数据写入磁盘
                        f.flush()
                        os.fsync(f.fileno())
                
                self.log(f"文件粉碎进度: {os.path.basename(file_path)} 第 {pass_num + 1}/{passes} 次覆盖")
            
            # 最后一次用零覆盖
            with open(file_path, "wb") as f:
                f.write(b'\x00' * file_size)
            
            # 删除文件
            os.remove(file_path)
            return True
        except Exception as e:
            self.log(f"文件粉碎失败: {str(e)}")
            return False
    
    def file_shredder(self):
        """文件粉碎功能"""
        try:
            files = filedialog.askopenfilenames(
                title="选择要粉碎的文件",
                filetypes=[("所有文件", "*.*")]
            )
            
            if not files:
                return
            
            confirm = messagebox.askyesno(
                "确认粉碎",
                f"确定要粉碎选中的 {len(files)} 个文件吗？\n此操作不可逆！"
            )
            
            if not confirm:
                return
            
            self.log(f"开始粉碎 {len(files)} 个文件...")
            
            # 在线程中执行粉碎操作
            def shred_files_thread():
                success_count = 0
                for file_path in files:
                    if self._shred_file(file_path):
                        success_count += 1
                        self.log(f"成功粉碎: {os.path.basename(file_path)}")
                
                self.root.after(0, lambda:
                    messagebox.showinfo("粉碎完成", f"共粉碎 {success_count}/{len(files)} 个文件")
                )
            
            threading.Thread(target=shred_files_thread).start()
        except Exception as e:
            self.log(f"文件粉碎功能错误: {str(e)}")
            messagebox.showerror("错误", f"文件粉碎时出错: {str(e)}")
    
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
        """粉碎整个目录，包括其中的所有文件和子目录"""
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
    
    def file_shredder(self):
        """文件粉碎功能的用户界面入口"""
        # 询问用户是粉碎文件还是目录
        choice = messagebox.askquestion("选择粉碎类型", "请选择要粉碎的类型:\n\n是: 单个文件\n否: 整个目录")
        
        if choice == "yes":
            # 选择单个文件
            file_path = filedialog.askopenfilename(title="选择要粉碎的文件")
            if not file_path:
                return
            
            # 确认操作
            if not messagebox.askyesno("确认粉碎", f"确定要粉碎文件: {file_path} 吗？\n此操作不可恢复！"):
                return
            
            # 执行粉碎
            self.log(f"开始粉碎文件: {file_path}")
            if self._shred_file(file_path):
                self.log(f"文件粉碎成功: {file_path}")
                messagebox.showinfo("粉碎成功", "文件已成功粉碎，无法恢复！")
            else:
                self.log(f"文件粉碎失败: {file_path}")
                messagebox.showerror("粉碎失败", "文件粉碎失败，请检查权限或文件是否被占用！")
        else:
            # 选择目录
            dir_path = filedialog.askdirectory(title="选择要粉碎的目录")
            if not dir_path:
                return
            
            # 确认操作
            if not messagebox.askyesno("确认粉碎", f"确定要粉碎目录: {dir_path} 及其所有内容吗？\n此操作不可恢复！"):
                return
            
            # 执行粉碎
            self.log(f"开始粉碎目录: {dir_path}")
            shredded_count = self._shred_directory(dir_path)
            self.log(f"目录粉碎完成，共粉碎 {shredded_count} 个文件")
            messagebox.showinfo("粉碎完成", f"目录粉碎完成，共粉碎 {shredded_count} 个文件！")
    
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
        
        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror("错误", f"未找到 {display_name} 的可执行文件，无法在沙箱中运行")
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
        """在沙箱环境中运行程序"""
        try:
            # 创建一个临时的沙箱工作目录
            sandbox_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"sandbox_{display_name.replace(' ', '_')}_{random.randint(1000, 9999)}")
            os.makedirs(sandbox_dir, exist_ok=True)
            self.log(f"创建沙箱工作目录: {sandbox_dir}")
            
            # 创建Job Object用于限制进程
            job = win32job.CreateJobObject(None, None)
            
            # 设置Job Object的基本限制
            job_info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
            
            # 进程退出时自动终止所有关联进程
            job_info['BasicLimitInformation']['LimitFlags'] = (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |  # 关闭Job时终止所有进程
                win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY  # 限制进程内存
            )
            
            # 设置进程内存限制（1GB）
            job_info['ProcessMemoryLimit'] = 1024 * 1024 * 1024
            
            # 应用限制
            win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, job_info)
            
            # 创建进程安全属性
            security_attributes = win32security.SECURITY_ATTRIBUTES()
            security_attributes.bInheritHandle = True
            
            # 创建启动信息
            startup_info = win32process.STARTUPINFO()
            
            # 启动进程
            process_handle, thread_handle, process_id, thread_id = win32process.CreateProcess(
                exe_path,
                None,  # 命令行
                None,  # 进程安全属性
                None,  # 线程安全属性
                True,  # 继承句柄
                win32process.CREATE_SUSPENDED |  # 挂起创建的进程
                win32con.NORMAL_PRIORITY_CLASS,
                None,  # 环境变量
                os.path.dirname(exe_path),  # 工作目录
                startup_info
            )
            
            # 将进程分配给Job Object
            win32job.AssignProcessToJobObject(job, process_handle)
            
            # 恢复进程执行
            win32process.ResumeThread(thread_handle)
            
            # 关闭不需要的句柄
            win32api.CloseHandle(thread_handle)
            
            self.log(f"沙箱进程已启动 - PID: {process_id}, 程序: {display_name}")
            
            # 监控进程状态
            try:
                while True:
                    time.sleep(1)
                    # 检查进程是否仍然存在
                    if not psutil.pid_exists(process_id):
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            finally:
                # 关闭Job Object，这会终止所有相关进程
                win32api.CloseHandle(process_handle)
                win32api.CloseHandle(job)
                
                # 清理沙箱目录（如果是空的）
                try:
                    if os.path.exists(sandbox_dir) and not os.listdir(sandbox_dir):
                        os.rmdir(sandbox_dir)
                except:
                    pass
                
                self.log(f"沙箱进程已结束 - PID: {process_id}, 程序: {display_name}")
                
        except Exception as e:
            self.log(f"沙箱运行程序时出错: {str(e)}")
            raise

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
    # 检查是否以管理员身份运行
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