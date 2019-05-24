import os
from tkinter import *
from tkinter import ttk, filedialog
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 解决matplotlib标签中文乱码和'-'号显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

DEVICE_SERIALS = []
MEM_DATA = []
MEM_COUNT = []
CPU_DATA = []
CPU_COUNT = []
fig_mem = plt.figure(figsize=(8, 2))
ax_mem = fig_mem.add_subplot(111)
ax_mem.grid()
fig_cpu = plt.figure(figsize=(8, 2))
ax_cpu = fig_cpu.add_subplot(111)
ax_cpu.grid()
p, = ax_mem.plot(MEM_COUNT, MEM_DATA, 'r-')
q, = ax_cpu.plot(CPU_COUNT, CPU_DATA, 'b-')


# 启动测试app
def start_app(pkg_name):
    s = time.time()
    launch_activity = os.popen('adb shell monkey -v -v -v 0 | findstr {}'.format(pkg_name)).read().split()[5]
    os.popen('adb shell am start {}/{}'.format(pkg_name, launch_activity))
    e = time.time()
    print('重启app耗时：{}'.format(e - s))


# 获取内存数据
def get_mem_data(pkg_name):
    # s = time.time()
    try:
        mem = int(os.popen('adb -s {} shell dumpsys meminfo {} | findstr "TOTAL:"'.format(DEVICE_SERIALS[0],
                                                                                          pkg_name)).read().split()[
                      1]) / 1024
    except IndexError:
        print('测试app已停止运行，自动重启')
        start_app(pkg_name)
        time.sleep(1)
        print('已重启')
        mem = int(os.popen('adb -s {} shell dumpsys meminfo {} | findstr "TOTAL:"'.format(DEVICE_SERIALS[0],
                                                                                          pkg_name)).read().split()[
                      1]) / 1024
    # e = time.time()
    # print('内存：{}'.format(e-s))
    return mem


# 获取cpu数据
def get_cpu_data(pkg_name):
    # s = time.time()
    cpu = 0
    for i in os.popen(
            'adb -s {} shell dumpsys cpuinfo | findstr {}'.format(DEVICE_SERIALS[0], pkg_name)).readlines():
        if len(i) > 1:
            cpu += round(float(i.split()[0].replace('%', '')), 2)
    # e = time.time()
    # print('cpu：{}'.format(e-s))
    return cpu


# 主类
class MainWindow:
    # 初始化主界面
    def __init__(self):
        self.window = Tk()
        self.window.title("Android性能测试工具")
        self.window.geometry('830x770')
        self.window.resizable(0, 0)

        """device_frame"""
        self.device_frame = ttk.Frame(self.window, padding='10')
        self.device_check_label = ttk.Label(self.device_frame, text='选择执行设备')
        self.device_frame.grid(row=0, column=0)
        self.device_check_label.grid(row=0, column=0, columnspan=6)
        # 设备检测模块
        self.device_info = Listbox(self.device_frame, width=45, height=7)
        self.device_check_button = ttk.Button(self.device_frame, text='检查设备', command=self.get_serialno)
        self.device_add_button = ttk.Button(self.device_frame, text='添加', command=self.add_to_device_pool)
        self.select_all_button = ttk.Button(self.device_frame, text='全选', command=self.select_all)
        self.device_refresh_button = ttk.Button(self.device_frame, text='刷新', command=self.refresh)
        self.device_pool = Listbox(self.device_frame, width=45, height=7)
        self.device_info.grid(row=1, column=0, rowspan=4, columnspan=2)
        self.device_check_button.grid(row=1, column=2)
        self.device_add_button.grid(row=2, column=2)
        self.select_all_button.grid(row=3, column=2)
        self.device_refresh_button.grid(row=4, column=2)
        self.device_pool.grid(row=1, column=4, rowspan=4, columnspan=2)

        """self.setting_frame"""
        self.setting_frame = ttk.Frame(self.window, padding='10')
        self.label_setting = ttk.Label(self.setting_frame, text="参数设置")
        self.setting_frame.grid(row=1, column=0)
        self.label_setting.grid(row=0, column=0, columnspan=6)
        # monkey模块
        self.label_pkg = ttk.Label(self.setting_frame, text="app包名：")
        self.pkg_name = StringVar()
        self.pkg_name.set('com.tencent.mm')
        self.entry_pkg = ttk.Entry(self.setting_frame, width=20, textvariable=self.pkg_name)
        self.label_seed = ttk.Label(self.setting_frame, text="seed值：")
        self.monkey_seed = IntVar()
        self.monkey_throttle = IntVar()
        self.monkey_event = IntVar()
        self.monkey_seed.set(0)
        self.monkey_throttle.set(400)
        self.monkey_event.set(1000)
        self.entry_seed = ttk.Entry(self.setting_frame, textvariable=self.monkey_seed, width=20)
        self.label_throttle = ttk.Label(self.setting_frame, text="事件间隔(ms)：")
        self.entry_throttle = ttk.Entry(self.setting_frame, textvariable=self.monkey_throttle, width=20)
        self.label_event = ttk.Label(self.setting_frame, text="事件数：")
        self.entry_event = ttk.Entry(self.setting_frame, textvariable=self.monkey_event, width=20)
        self.crash_checked = IntVar()
        self.crash_checked.set(1)
        self.anr_checked = IntVar()
        self.anr_checked.set(1)
        self.checkbutton_crash = ttk.Checkbutton(self.setting_frame, text='忽略崩溃', variable=self.crash_checked)
        self.checkbutton_anr = ttk.Checkbutton(self.setting_frame, text='忽略ANR', variable=self.anr_checked)
        self.button_run = ttk.Button(self.setting_frame, text='执行monkey',
                                     command=self.start_monkey)
        self.button_stop = ttk.Button(self.setting_frame, text='停止', command=self.stop_monkey)
        self.label_pkg.grid(row=1, column=0, sticky=W)
        self.entry_pkg.grid(row=1, column=1)
        self.label_seed.grid(row=1, column=2, sticky=W)
        self.entry_seed.grid(row=1, column=3)
        self.label_throttle.grid(row=1, column=4, sticky=W)
        self.entry_throttle.grid(row=1, column=5)
        self.label_event.grid(row=2, column=0, sticky=W)
        self.entry_event.grid(row=2, column=1)
        self.checkbutton_crash.grid(row=3, column=0, sticky=W)
        self.checkbutton_anr.grid(row=3, column=1, sticky=W)
        self.button_run.grid(row=6, column=0, sticky=E)
        self.button_stop.grid(row=6, column=1, sticky=W)
        # 内存模块
        self.label_mem_time = ttk.Label(self.setting_frame, text='内存获取频率：')
        self.mem_frequency = IntVar()
        self.mem_frequency.set(3)
        self.entry_mem_time = ttk.Entry(self.setting_frame, width=20, textvariable=self.mem_frequency)
        self.mem_data_checked = IntVar()
        self.mem_data_checked.set(0)
        self.mem_img_checked = IntVar()
        self.mem_img_checked.set(1)
        self.checkbutton_mem_data = ttk.Checkbutton(self.setting_frame, text='保存数据', variable=self.mem_data_checked,
                                                    command=lambda: self.file_path('mem'))
        self.checkbutton_mem_img = ttk.Checkbutton(self.setting_frame, text='实时图形', variable=self.mem_img_checked)
        self.button_mem_run = ttk.Button(self.setting_frame, text='内存监控', command=lambda: self.draw_running('mem'))
        self.button_mem_stop = ttk.Button(self.setting_frame, text='停止', command=lambda: self.stop_monitor('mem'))
        self.label_mem_time.grid(row=2, column=2, sticky=W)
        self.entry_mem_time.grid(row=2, column=3)
        self.checkbutton_mem_data.grid(row=3, column=2, sticky=W)
        self.checkbutton_mem_img.grid(row=3, column=3, sticky=W)
        self.button_mem_run.grid(row=6, column=2, sticky=E)
        self.button_mem_stop.grid(row=6, column=3, sticky=W)
        # CPU模块
        self.label_cpu_time = ttk.Label(self.setting_frame, text='cpu获取频率：')
        self.cpu_frequency = IntVar()
        self.cpu_frequency.set(3)
        self.entry_cpu_time = ttk.Entry(self.setting_frame, width=20, textvariable=self.cpu_frequency)
        self.cpu_data_checked = IntVar()
        self.cpu_data_checked.set(0)
        self.cpu_img_checked = IntVar()
        self.cpu_img_checked.set(1)
        self.checkbutton_cpu_data = ttk.Checkbutton(self.setting_frame, text='保存数据', variable=self.cpu_data_checked,
                                                    command=lambda: self.file_path('cpu'))
        self.checkbutton_cpu_img = ttk.Checkbutton(self.setting_frame, text='实时图形', variable=self.cpu_img_checked)
        self.button_cpu_run = ttk.Button(self.setting_frame, text='cpu监控', command=lambda: self.draw_running('cpu'))
        self.button_cpu_stop = ttk.Button(self.setting_frame, text='停止', command=lambda: self.stop_monitor('cpu'))
        self.label_cpu_time.grid(row=2, column=4, sticky=W)
        self.entry_cpu_time.grid(row=2, column=5)
        self.checkbutton_cpu_data.grid(row=3, column=4, sticky=W)
        self.checkbutton_cpu_img.grid(row=3, column=5, sticky=W)
        self.button_cpu_run.grid(row=6, column=4, sticky=E)
        self.button_cpu_stop.grid(row=6, column=5, sticky=W)

        """graph_frame"""
        # 图表展示模块
        self.graph_frame = ttk.Frame(self.window, padding='10')
        self.graph_label = ttk.Label(self.graph_frame, text='图表展示')
        self.graph_frame.grid(row=2, column=0)
        self.graph_label.grid(row=0, column=0, columnspan=6)
        # 内存+cpu动态图
        self.mem_graph = Canvas(self.graph_frame, width=800, height=180, bg='white')
        self.cpu_graph = Canvas(self.graph_frame, width=800, height=180, bg='white')

        """主窗口循环"""
        self.pad_set()
        self.window.mainloop()

    # 设置元素的上下左右间距
    def pad_set(self):
        ele_list = self.device_frame.winfo_children() + self.setting_frame.winfo_children() + \
                   self.graph_frame.winfo_children()
        for ele in ele_list:
            ele.grid_configure(padx=5, pady=1)

    # 获取手机型号
    def get_serialno(self):
        exist = self.device_info.get(0, END)

        def device_name(num):
            name = ((os.popen('adb -s {} shell getprop | findstr brand'.format(num))).read().split(':')[
                        1].strip().replace('[', '').replace(']', '') + '：' + num)
            return name

        for i in os.popen('adb devices').readlines():
            if len(i) > 5 and i.split()[1] == 'device' and device_name(i.split()[0]) not in exist:
                self.device_info.insert(END, device_name(i.split()[0]))

    # 添加
    def add_to_device_pool(self):
        exist = self.device_pool.get(0, END)
        for i in self.device_info.curselection():
            if self.device_info.get(i) not in exist:
                self.device_pool.insert(END, self.device_info.get(i))
                print(self.device_info.get(i))
                DEVICE_SERIALS.append(self.device_info.get(i).split('：')[-1])
        return DEVICE_SERIALS

    # 全选
    def select_all(self):
        self.device_info.select_set(0, END)

    # 刷新
    def refresh(self):
        self.device_info.delete(0, END)
        self.get_serialno()

    # 设置内存数据存储路径
    def file_path(self, flag):
        global MEM_FILE_PATH, CPU_FILE_PATH
        if flag == 'mem':
            if self.mem_data_checked.get():
                MEM_FILE_PATH = filedialog.askdirectory()
                return MEM_FILE_PATH
        else:
            if self.cpu_data_checked.get():
                CPU_FILE_PATH = filedialog.askdirectory()
                return CPU_FILE_PATH

    # 执行monkey指令
    def start_monkey(self):
        """获取相关参数，拼接monkey指令，执行指令"""
        pkg_name = self.entry_pkg.get()
        seed = self.entry_seed.get()
        throttle = self.entry_throttle.get()
        event = self.entry_event.get()
        if len(DEVICE_SERIALS) > 0:
            print(DEVICE_SERIALS)
            if not (pkg_name or seed or throttle or event):
                print('请检查monkey参数是否填写正确')
            else:
                self.button_run.configure(state='disabled')
                for serial in DEVICE_SERIALS:
                    if self.crash_checked.get() and not self.anr_checked.get():
                        os.popen('adb -s {} shell monkey -p {} -s {} --throttle {} --ignore-crashes -v -v -v {}'
                                 .format(serial, pkg_name, seed, throttle, event))
                    elif self.anr_checked and not self.crash_checked:
                        os.popen('adb -s {} shell monkey -p {} -s {} --throttle {} --ignore-timeouts -v -v -v {}'
                                 .format(serial, pkg_name, seed, throttle, event))
                    elif not self.crash_checked.get() and not self.anr_checked.get():
                        os.popen('adb -s {} shell monkey -p {} -s {} --throttle {} -v -v -v {}'
                                 .format(serial, pkg_name, seed, throttle, event))
                    else:
                        os.popen('adb -s {} shell monkey -p {} -s {} --throttle {} --ignore-crashes --ignore-timeouts'
                                 ' -v -v -v {}'.format(serial, pkg_name, seed, throttle, event))
        else:
            print('请先选择设备 ')

    # 停止monkey
    def stop_monkey(self):
        for serial in DEVICE_SERIALS:
            for monkey_pid in os.popen('adb -s {} shell ps | findstr monkey'.format(serial)).readlines():
                if 'monkey' in monkey_pid:
                    os.popen('adb -s {} shell kill '.format(serial) + monkey_pid.split()[1])
        else:
            self.button_run.configure(state='enable')

    # 动态绘制图形
    def update(self, flag):
        global PKG_NAME
        frequency = int(self.entry_mem_time.get())
        PKG_NAME = self.entry_pkg.get()
        if flag == 'mem':
            MEM_COUNT.append(len(MEM_DATA))
            MEM_DATA.append(get_mem_data(PKG_NAME))
            ax_mem.set_xlim(0, max(MEM_COUNT) + 1)
            ax_mem.set_ylim(0, max(MEM_DATA) + 50)
            ax_mem.set_xlabel('time(s)')
            ax_mem.set_ylabel('内存占用(MB)')
            p.set_data(MEM_COUNT, MEM_DATA)
            # 防止绘制图形过程中卡住
            plt.pause(0.001)
            # matplotlib图像用TK显示
            fig_mem.canvas = FigureCanvasTkAgg(fig_mem, self.mem_graph)
            fig_mem.canvas.get_tk_widget().grid(row=0, column=0, columnspan=6)
            # matplotlib动态绘图对象
            FuncAnimation(fig=fig_mem, func=self.update, frames=1, interval=frequency)
            time.sleep(frequency)
        else:
            CPU_COUNT.append(len(CPU_DATA))
            CPU_DATA.append(get_cpu_data(PKG_NAME))
            q.set_data(CPU_COUNT, CPU_DATA)
            ax_cpu.set_xlim(0, max(CPU_COUNT) + 1)
            ax_cpu.set_ylim(0, max(CPU_DATA) + 1)
            ax_cpu.set_xlabel('time(s)')
            ax_cpu.set_ylabel('cpu占用(%)')
            plt.pause(0.001)
            fig_cpu.canvas = FigureCanvasTkAgg(fig_cpu, self.cpu_graph)
            fig_cpu.canvas.get_tk_widget().grid(row=1, column=0, columnspan=6)
            FuncAnimation(fig=fig_cpu, func=self.update, frames=60, interval=frequency)
            time.sleep(frequency)

    def show(self, flag):
        global MEM_MONITOR, CPU_MONITOR
        MEM_MONITOR = True
        CPU_MONITOR = True
        if flag == 'mem':
            while MEM_MONITOR:
                self.update(flag)
        else:
            while CPU_MONITOR:
                self.update(flag)

    def draw_running(self, flag):
        global PKG_NAME
        PKG_NAME = self.entry_pkg.get()
        try:
            if len(DEVICE_SERIALS) == 0:
                print('请先选定设备')
            else:
                if flag == 'mem':
                    self.button_mem_run.configure(state=DISABLED)
                else:
                    self.button_cpu_run.configure(state=DISABLED)
                show_thread = threading.Thread(target=self.show, args=(flag,))
                show_thread.start()
        except NameError:
            print('请先选定设备')

    # 停止绘制图形
    def stop_monitor(self, flag):
        if flag == 'mem':
            global MEM_MONITOR
            MEM_MONITOR = False
            self.button_mem_run.configure(state='enable')
        else:
            global CPU_MONITOR
            CPU_MONITOR = False
            self.button_cpu_run.configure(state='enable')


if __name__ == "__main__":
    MainWindow()
