import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


class MoyuReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Slack on")

        # --- ⚙️ 核心参数配置 ---
        self.scroll_speed = 2  # 【关键】滚轮速度倍率 (数字越大滚得越快)
        self.keyboard_speed = 1  # 键盘按一下滚动的单位

        # --- 配色 ---
        self.transparent_key = "#111111"
        self.grip_color = "#333333"
        self.text_color = "gray"

        self.highlight_bg = "#ffff00"
        self.highlight_fg = "#000000"
        self.active_bg = "#ff4500"
        self.active_fg = "#ffffff"

        self.font_config = ("微软雅黑", 12)

        # --- 窗口设置 ---
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", self.transparent_key)
        self.root.configure(bg=self.transparent_key)
        self.root.geometry("400x500+300+100")

        # --- 组件布局 ---
        self.grip_bar = tk.Frame(self.root, bg=self.grip_color, height=10, cursor="fleur")
        self.grip_bar.pack(side="top", fill="x")

        self.text_area = tk.Text(self.root, font=self.font_config, fg=self.text_color,
                                 bg=self.transparent_key, bd=0, highlightthickness=0,
                                 relief="flat", cursor="arrow")
        self.text_area.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_area.tag_config("search_hit", background=self.highlight_bg, foreground=self.highlight_fg)
        self.text_area.tag_config("active_hit", background=self.active_bg, foreground=self.active_fg)

        self.resize_grip = tk.Label(self.root, text="◢", font=("Arial", 14),
                                    fg=self.grip_color, bg=self.transparent_key, cursor="size_nw_se")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se")

        # --- 初始数据 ---
        self.match_positions = []
        self.current_match_idx = -1
        self.default_text = "Slack time \n\n 已重写滚动逻辑：\n1. 方向键直接控制视图\n2. 体验更像浏览器\n\n(按 F3 搜索下一个)"
        self.set_text(self.default_text)

        # ==========================================
        # 🎮 核心事件绑定 (覆盖默认行为)
        # ==========================================

        # 1. 鼠标滚轮 (Windows下是 <MouseWheel>)
        self.text_area.bind("<MouseWheel>", self.custom_scroll_wheel)
        self.root.bind("<MouseWheel>", self.custom_scroll_wheel)  # 即使焦点不在文字上也能滚

        # 2. 键盘方向键 (拦截默认的光标移动，改为视图滚动)
        self.root.bind("<Up>", lambda e: self.custom_scroll_key("up"))
        self.root.bind("<Down>", lambda e: self.custom_scroll_key("down"))
        self.text_area.bind("<Up>", lambda e: self.custom_scroll_key("up"))
        self.text_area.bind("<Down>", lambda e: self.custom_scroll_key("down"))

        # 3. 翻页键
        self.root.bind("<Prior>", lambda e: self.custom_scroll_key("pageup"))  # PageUp
        self.root.bind("<Next>", lambda e: self.custom_scroll_key("pagedown"))  # PageDown

        # 4. 其他原有绑定
        self.grip_bar.bind("<Button-1>", self.start_move)
        self.grip_bar.bind("<B1-Motion>", self.do_move)
        self.grip_bar.bind("<Double-Button-1>", lambda e: self.root.quit())
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)
        self.root.bind("<Control-f>", self.ask_search)
        self.root.bind("<F3>", self.find_next)
        self.root.bind("<Escape>", self.handle_escape)
        self.text_area.bind("<Button-3>", self.show_menu)
        self.grip_bar.bind("<Button-3>", self.show_menu)

        # 屏蔽打字，但允许快捷键
        self.text_area.bind("<Key>", self.prevent_typing)

        # 菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="📂 打开小说", command=self.load_file)
        self.menu.add_separator()
        self.menu.add_command(label="🔍 查找 (Ctrl+F)", command=self.ask_search)
        self.menu.add_command(label="⬇️ 下一个 (F3)", command=self.find_next)
        self.menu.add_command(label="🧹 清除高亮", command=self.clear_highlight)
        self.menu.add_separator()
        self.menu.add_command(label="❌ 退出", command=self.root.quit)

        self.x = 0;
        self.y = 0;
        self.start_w = 0;
        self.start_h = 0

    # ==========================================
    # 🚀 自定义滚动逻辑 (核心修改区)
    # ==========================================
    def custom_scroll_wheel(self, event):
        """处理鼠标滚轮，实现倍速滚动"""
        if event.delta > 0:
            # 向上滚
            self.text_area.yview_scroll(-1 * self.scroll_speed, "units")
        else:
            # 向下滚
            self.text_area.yview_scroll(1 * self.scroll_speed, "units")
        return "break"  # 阻止默认的慢速滚动

    def custom_scroll_key(self, direction):
        """处理键盘按键，实现像浏览器一样的视图滚动"""
        if direction == "up":
            self.text_area.yview_scroll(-1 * self.keyboard_speed, "units")
        elif direction == "down":
            self.text_area.yview_scroll(1 * self.keyboard_speed, "units")
        elif direction == "pageup":
            self.text_area.yview_scroll(-1, "pages")
        elif direction == "pagedown":
            self.text_area.yview_scroll(1, "pages")
        return "break"  # 阻止默认的光标移动行为

    # --- 原有功能保持不变 ---
    def set_text(self, content):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", content)
        self.text_area.config(state="disabled")

    def prevent_typing(self, event):
        if (event.state & 0x0004) and event.keysym.lower() == 'f': return
        if event.keysym in ["Escape", "F3"]: return
        # 注意：上下左右和翻页键现在由 custom_scroll_key 接管，这里也全部 break 掉
        return "break"

    def ask_search(self, event=None):
        target = simpledialog.askstring("查找", "请输入关键词：", parent=self.root)
        if target: self.do_search_all(target)

    def do_search_all(self, target):
        self.clear_highlight()
        self.match_positions = []
        self.current_match_idx = -1
        self.text_area.config(state="normal")
        start_pos = "1.0"
        while True:
            pos = self.text_area.search(target, start_pos, stopindex="end")
            if not pos: break
            end_pos = f"{pos}+{len(target)}c"
            self.match_positions.append((pos, end_pos))
            self.text_area.tag_add("search_hit", pos, end_pos)
            start_pos = end_pos
        self.text_area.config(state="disabled")
        if self.match_positions:
            self.jump_to_match(0)
        else:
            messagebox.showinfo("提示", f"未找到：{target}")

    def find_next(self, event=None):
        if not self.match_positions: return
        next_idx = (self.current_match_idx + 1) % len(self.match_positions)
        self.jump_to_match(next_idx)

    def jump_to_match(self, index):
        if self.current_match_idx != -1:
            old_start, old_end = self.match_positions[self.current_match_idx]
            self.text_area.tag_remove("active_hit", old_start, old_end)
            self.text_area.tag_add("search_hit", old_start, old_end)
        self.current_match_idx = index
        start_pos, end_pos = self.match_positions[index]
        self.text_area.tag_remove("search_hit", start_pos, end_pos)
        self.text_area.tag_add("active_hit", start_pos, end_pos)
        self.text_area.see(start_pos)

    def clear_highlight(self):
        self.text_area.tag_remove("search_hit", "1.0", "end")
        self.text_area.tag_remove("active_hit", "1.0", "end")
        self.match_positions = []

    def handle_escape(self, event):
        if self.match_positions:
            self.clear_highlight()
        else:
            self.root.quit()

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        self.root.geometry(f"+{self.root.winfo_x() + (event.x - self.x)}+{self.root.winfo_y() + (event.y - self.y)}")

    def start_resize(self, event):
        self.x, self.y = event.x_root, event.y_root
        self.start_w, self.start_h = self.root.winfo_width(), self.root.winfo_height()

    def do_resize(self, event):
        self.root.geometry(
            f"{max(self.start_w + (event.x_root - self.x), 100)}x{max(self.start_h + (event.y_root - self.y), 100)}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.set_text(f.read())
            except:
                try:
                    with open(file_path, "r", encoding="gbk") as f:
                        self.set_text(f.read())
                except:
                    messagebox.showerror("错误", "无法读取")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = MoyuReader(root)
    root.mainloop()