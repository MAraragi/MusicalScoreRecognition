import os
from queue import Queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, simpledialog, scrolledtext
from recognition_UI import Recognition
from midiMapping import createMidiInfo
from createmidi import createMidi
# from mid2mp3 import convert

args = {
    "speed": 150, "tonic": 'C', 'beat': "4/4", "delta_range": 1.5, "print_info": 1, "match_precision": 2,
    "thread_num": 8, "sampling_rate": 2, "threshold_method": "global", "threshold": 160
}


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sheet_recognition = None
        self.output_queue = Queue()
        # 设置背景图片
        # self.background_image = tk.PhotoImage(file="meiqin.png")
        # self.background_label = tk.Label(self, image=self.background_image)
        # self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.title("简谱识别转MIDI")

        # 获取屏幕宽高
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 设置窗口大小
        window_width = 800
        window_height = 700

        # 计算窗口位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 设置窗口初始位置
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        # self.geometry("800x400")
        self.resizable(False, False)

        # 创建输入框和标签
        self.entry_path_var = tk.StringVar()
        self.label_path = tk.Label(self, text="文件/文件夹路径:")
        self.label_path.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.entry_path = tk.Entry(self, textvariable=self.entry_path_var, width=30)
        self.entry_path.grid(row=0, column=1, padx=10, pady=5)

        self.button_browse = tk.Button(self, text="浏览", command=self.browse_path)
        self.button_browse.grid(row=0, column=2, padx=10, pady=5)

        self.label_tonic = tk.Label(self, text="请输入简谱主音(在第一页左上角‘1=’后噢):")
        self.label_tonic.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.entry_tonic_var = tk.StringVar(value=args["tonic"])
        self.entry_tonic = tk.Entry(self, textvariable=self.entry_tonic_var)
        self.entry_tonic.grid(row=1, column=1, padx=10, pady=5)

        self.label_speed = tk.Label(self, text="请输入简谱速度(每分钟拍数，同在左上角，‘🎶=’后):")
        self.label_speed.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.entry_speed_var = tk.StringVar(value=str(args["speed"]))
        self.entry_speed = tk.Entry(self, textvariable=self.entry_speed_var)
        self.entry_speed.grid(row=2, column=1, padx=10, pady=5)

        self.label_do_print_info = tk.Label(self, text="是否输出中间信息[Y/N]:")
        self.label_do_print_info.grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.entry_do_print_info_var = tk.StringVar()
        self.entry_do_print_info = tk.Entry(self, textvariable=self.entry_do_print_info_var)
        self.entry_do_print_info.grid(row=3, column=1, padx=10, pady=5)

        self.label_match_precision = tk.Label(self, text="请选择匹配精度[L/M/H]:")
        self.label_match_precision.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.entry_match_precision_var = tk.StringVar()
        self.entry_match_precision = tk.Entry(self, textvariable=self.entry_match_precision_var)
        self.entry_match_precision.grid(row=4, column=1, padx=10, pady=5)

        self.label_thread_num = tk.Label(self, text="准备开几个线程来跑呢(跟CPU核数一样就好，1~16都可以):")
        self.label_thread_num.grid(row=5, column=0, sticky="w", padx=10, pady=5)

        self.entry_thread_num_var = tk.StringVar()
        self.entry_thread_num = tk.Entry(self, textvariable=self.entry_thread_num_var)
        self.entry_thread_num.grid(row=5, column=1, padx=10, pady=5)

        self.label_delta_range = tk.Label(self, text="估算一下字符上下间距(一般在1.0~2.5就好，我觉得1.5挺好的):")
        self.label_delta_range.grid(row=6, column=0, sticky="w", padx=10, pady=5)

        self.entry_delta_range_var = tk.StringVar()
        self.entry_delta_range = tk.Entry(self, textvariable=self.entry_delta_range_var)
        self.entry_delta_range.grid(row=6, column=1, padx=10, pady=5)

        self.label_threshold_method = tk.Label(self, text="二值化采取什么算法比较好(有水印的话用OTSU比较好，其他时候直接跳过这项即可):")
        self.label_threshold_method.grid(row=7, column=0, sticky="w", padx=10, pady=5)

        self.entry_threshold_method_var = tk.StringVar()
        self.entry_threshold_method = tk.Entry(self, textvariable=self.entry_threshold_method_var)
        self.entry_threshold_method.grid(row=7, column=1, padx=10, pady=5)

        self.label_threshold = tk.Label(self, text="全局阈值想要设置为多少呢(如果直接跳过的话默认160喔):")
        self.label_threshold.grid(row=8, column=0, sticky="w", padx=10, pady=5)

        self.entry_threshold_var = tk.StringVar()
        self.entry_threshold = tk.Entry(self, textvariable=self.entry_threshold_var)
        self.entry_threshold.grid(row=8, column=1, padx=10, pady=5)

        self.label_wanna_debug = tk.Label(self, text="需要自己手动调整一下中间过程吗(不输入Y/y就默认不改哈):")
        self.label_wanna_debug.grid(row=9, column=0, sticky="w", padx=10, pady=5)

        self.entry_wanna_debug_var = tk.StringVar()
        self.entry_wanna_debug = tk.Entry(self, textvariable=self.entry_wanna_debug_var)
        self.entry_wanna_debug.grid(row=9, column=1, padx=10, pady=5)

        self.run_button = tk.Button(self, text="运行", command=self.run_recognition)
        # self.run_button.grid(row=10, column=0, columnspan=2, pady=10)
        self.run_button.grid(row=9, column=2, columnspan=2, padx=10, pady=10)

        # 创建Text控件用于显示输出信息
        self.label_output = tk.Label(self, text="程序输出:")
        self.label_output.grid(row=11, column=0, columnspan=3, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(self, width=80, height=20, wrap=tk.WORD)
        self.output_text.grid(row=12, column=0, columnspan=3, padx=10, pady=10)
        

    def browse_path(self):
        path = filedialog.askdirectory()
        self.entry_path_var.set(path)

    def run_recognition(self):
        # 重定向输出到Text控件
        self.redirect_output()

        src_img_path = self.entry_path_var.get()
        music_name = os.path.basename(src_img_path).split('.')[0]

        args["tonic"] = self.entry_tonic_var.get()
        args["speed"] = int(self.entry_speed_var.get())
        args["print_info"] = 0 if self.entry_do_print_info_var.get().upper() == 'N' else 1
        args["match_precision"] = 1 if self.entry_match_precision_var.get().upper() == 'H' else 2
        args["sampling_rate"] = 1 if args["match_precision"] == 1 else 2
        args["thread_num"] = int(self.entry_thread_num_var.get()) if self.entry_thread_num_var.get() else 8
        args["delta_range"] = float(self.entry_delta_range_var.get()) if self.entry_delta_range_var.get() else 1.5
        args["threshold_method"] = self.entry_threshold_method_var.get().upper() if self.entry_threshold_method_var.get() else "GLOBAL"
        args["threshold"] = int(self.entry_threshold_var.get()) if self.entry_threshold_var.get() else 160
        wanna_debug = self.entry_wanna_debug_var.get().upper() if self.entry_wanna_debug_var.get() else 'N'

        midi_map = createMidiInfo(music_name, speed=args["speed"], tonic=args["tonic"])
        if os.path.isdir(src_img_path):
            music_sheets = []
            music_sheets_temp = os.listdir(src_img_path)
            music_sheets_temp = sorted(music_sheets_temp)
            print("路径“" + src_img_path + "”下有以下文件：")
            for num, detected_file_name in enumerate(music_sheets_temp):
                print(str(num) + ': ' + detected_file_name)
            ignored_file_num_dialog = InputDialog(self, "请输入不需要检测的文件的序号(以空格分隔):", "")
            self.wait_window(ignored_file_num_dialog)
            ignored_file_num = list(map(int, ignored_file_num_dialog.user_input.split()))
            event_list = []
            for num, i in enumerate(music_sheets_temp):
                if num not in ignored_file_num:
                    music_sheets.append(os.path.join(src_img_path, i))
                    self.sheet_recognition = Recognition(music_sheets[-1],
                                                    delta_range=args["delta_range"],
                                                    print_info=args["print_info"],
                                                    match_precision=args["match_precision"],
                                                    thread_num=args["thread_num"],
                                                    sampling_rate=args["sampling_rate"],
                                                    threshold_method=args["threshold_method"],
                                                    threshold=args["threshold"]
                                                    )
                                            
                    # self.sheet_recognition.recognize()
                    # 设置回调函数
                    self.sheet_recognition.set_callback_function(self.update_output_text)
                    # self.sheet_recognition.set_callback_function(self.check_output_queue)
                    # thread = threading.Thread(target=self.sheet_recognition.recognize)
                    # thread.start()
                    # done = False
                    # thread_event = threading.Event()
                    # # # thread = threading.Thread(target=self.sheet_recognition.recognize, args=(thread_event,))
                    # thread = threading.Thread(target=self.recognize_wrapper, args=(self.sheet_recognition,thread_event))
                    # thread.start()
                    # event_list.append(thread_event)
                    # self.after(500, self.check_output_queue)
                    # thread_event.wait()
                    # 创建并启动另一个线程，等待主线程完成后执行后续代码
                    # wait_thread = threading.Thread(target=self.wait_and_continue, args=(thread_event,))
                    # wait_thread.start()
                    # thread_event.set()
                    # done = True
                    # threading.Thread(target=self.sheet_recognition.recognize).start()
                    #　thread.start()
                    self.sheet_recognition.recognize()
                    # 启动定时器，定时检查实时输出变量
                    #self.after(500, self.check_output_queue)

                    # 等待线程结束
                    # self.sheet_recognition.join()
                    # thread.join()

                    # while not thread_event.is_set():
                    #     # self.after(500, self.check_output_queue)
                    #     time.sleep(0.1)
                    #     continue

                    if wanna_debug == 'Y':
                        self.sheet_recognition.saveInfo()
                        print("......请查看代码同目录下文件" + i.split('.')[0] + ".txt并订正......")
                        while True:
                            next_step_dialog = InputDialog(self, "......改好了就输入[Y/y]好接着分析哈.......：", "")
                            self.wait_window(next_step_dialog)
                            next_step = next_step_dialog.user_input.upper()
                            if next_step == 'Y':
                                break
                        self.sheet_recognition.readInfo(i.split('.')[0] + ".txt")
                    recognition_result = self.sheet_recognition.getTimelineResult()
                    midi_map.addTimeline(recognition_result)
        else:
            self.sheet_recognition = Recognition(src_img_path,
                                            delta_range=args["delta_range"],
                                            print_info=args["print_info"],
                                            match_precision=args["match_precision"],
                                            thread_num=args["thread_num"],
                                            sampling_rate=args["sampling_rate"],
                                            threshold_method=args["threshold_method"],
                                            threshold=args["threshold"])
            
            # 设置回调函数
            self.sheet_recognition.set_callback_function(self.update_output_text)
            self.sheet_recognition.recognize()

            if wanna_debug == 'Y':
                self.sheet_recognition.saveInfo()
                img_name = os.path.basename(src_img_path).split('.')[0]
                print("......请查看代码同目录下文件" + img_name + ".txt并订正......")
                while True:
                    next_step_dialog = InputDialog(self, "......改好了就输入[Y/y]好接着分析哈.......：", "")
                    self.wait_window(next_step_dialog)
                    next_step = next_step_dialog.user_input.upper()
                    if next_step == 'Y':
                        break
                self.sheet_recognition.readInfo(img_name + ".txt")
            recognition_result = self.sheet_recognition.getTimelineResult()
            midi_map.addTimeline(recognition_result)

        midi_map.mapping()
        midi_timeline = midi_map.getMidiTimeline()
        make_midi = createMidi(1, midi_timeline, midi_name=music_name)
        make_midi.createmidifile()

        # midi_path = f"new_midi_file/{music_name}.mid"
        # convert(midi_path)
        # 恢复标准输出
        # sys.stdout = sys.__stdout__
        # sys.stderr = sys.__stderr__
    
    def redirect_output(self):
        # 重定向标准输出到Text控件
        sys.stdout = TextRedirector(self.output_text, "stdout")
        sys.stderr = TextRedirector(self.output_text, "stderr")
    
    def update_output_text(self, line):
        # 在这里更新 UI，例如将实时输出追加到 Text 控件中
        self.output_text.insert(tk.END, line, ("stdout",))
        # 更新 Text 控件显示
        self.output_text.update()
        self.output_text.see(tk.END)
    
    # def check_output_queue(self, thread):
    #     try:
    #         # 从队列中获取信息并更新到 UI
    #         if not self.sheet_recognition.output_queue.empty() and thread.is_alive():
    #             message = self.sheet_recognition.output_queue.get_nowait()
    #             self.output_text.insert(tk.END, message, ("stdout",))
    #             # 更新 Text 控件显示
    #             self.output_text.update()
    #             self.output_text.see(tk.END)

    #     except Queue.empty:
    #         pass
    #     # 继续定时检查
    #     self.after(500, self.check_output_queue, thread)

    def check_output_queue(self):
        try:
            # 从队列中获取信息并更新到 UI
            if not self.output_queue.empty():
                message = self.output_queue.get_nowait()
                self.output_text.insert(tk.END, message, ("stdout",))
                # 更新 Text 控件显示
                self.output_text.update()
                self.output_text.see(tk.END)

        except Queue.empty:
            pass
        # 继续定时检查
        self.after(500, self.check_output_queue)
        
    # 新建一个包装函数，将事件设置为recognize函数执行完成
    def recognize_wrapper(self, sheet_recognition, event):
        sheet_recognition.recognize()
        event.set()
    
    # def wait_and_continue(self, event):
    #     event.wait()
        # 等待主线程中的线程执行完成
        # thread.join()

        # 这里可以添加你想要在线程执行完成后立即执行的代码
        # messagebox.showinfo("Thread Finished", "Processing complete!")


class InputDialog(tk.Toplevel):
    def __init__(self, parent, prompt, title):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.parent = parent

        self.prompt = tk.Label(self, text=prompt)
        self.prompt.pack(padx=10, pady=5)

        self.user_input_var = tk.StringVar()
        self.user_input_entry = tk.Entry(self, textvariable=self.user_input_var)
        self.user_input_entry.pack(padx=10, pady=5)

        self.ok_button = tk.Button(self, text="确定", command=self.ok)
        self.ok_button.pack(pady=10)
        # 居中对话框
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_reqwidth() // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_reqheight() // 2
        self.geometry("+%d+%d" % (x, y))

    def ok(self):
        self.user_input = self.user_input_var.get()
        self.destroy()

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.insert(tk.END, str, (self.tag,))
        self.widget.see(tk.END)

    def flush(self):
        pass


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
