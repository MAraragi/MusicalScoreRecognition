import os
import cv2
import time
import threading
import numpy as np
from KdTree import KDTree
import subprocess
from threading import Thread
import tkinter as tk


class Recognition:
    IMAGE_NOT_FOUND_ERROR = "未找到指定文件，请检查路径上是否存在该图片。"
    FILE_NOT_OPENED_ERROR = "尚未打开图片，无法进行处理。"
    EMPTY_BAR_LINE_ERROR = "图片中未识别到小节线，无法进行分节。"
    FOLDER_NOT_FOUND_ERROR = "未发现采样数对应的系列模板，请检查同目录下是否存在文件夹"
    # 字典NAME_REFLECTION是为了方便输出debug信息而设立的，debug代码在__match()方法的尾段，正常运行时不会用到这个字典
    NAME_REFLECTION = {'b': "大括号", 'd': "点", 'f': "降号", 'h': "横线", 'n': "音符",
                       "sh": "升号", "sl": "连音线", 've': "竖线", 'vi': "颤音线"}
    NUMBER_SET = ['0', '1', '2', '3', '4', '5', '6', '7']

    """
    关于初始化类参数的说明：
    imgPath是图片在电脑硬盘中的路径，如果将图片放在该recognition.py同目录下，那么直接输入图片全名就好，包括扩展名；
    speed是曲谱的速度，一般写在简谱第一页的左上角；
    major是简谱的调性，像是C大调之类的，一般与也写在简谱第一页的左上角；
    beat是简谱的节拍，一般与调性一起写在简谱第一页的左上角；
    delta_range是一个可以灵活调整的参数，这与语法分析部分的算法有关，
    一般的原则是在简谱音符部分，字符上下间隔越大，delta_range就要设置得越大，一般默认在1.0左右，
    像我找的Flower Dance简谱，就设置在1.2就好，1.0的话偶尔会漏掉几个低音点或高音点；
    print_info是一个只能是1或0的伪布尔型常量，用以指示是否输出过程信息，
    1代表输出中间分析过程，0代表不输出，
    如果用其他py模块导入这个类，感觉还是不输出比较简洁，
    在调用类初始化方法时设置print_info为其他值即可，只要不是0，就会认作1；
    match_precision是用来控制匹配精度的，需要取正整数，默认为1，
    这个值越大，代表匹配精度越低，但匹配用时将呈倍数减少，可以权衡一下，
    通常设置为2时结果不会出错，但设置为3就会开始出现识别错误了；
    值得一提的是__match()方法的匹配方案目前采取KD树算法，时间复杂度相当于o(nlogn)，
    经代码作者计算，相较于先前的线性扫描法，结合match_precision参数，
    现在的KD树算法在精度没有任何损失的情况下，匹配部分的速度提升至3.52倍。
    """

    def __init__(self, imgPath, speed=120, tonic='C', beat="4/4", delta_range=1.0,
                 print_info=1, match_precision=1, thread_num=1, sampling_rate=1,
                 threshold_method="global", threshold=160):
        self.imgPath = imgPath
        self.srcImg = cv2.imread(imgPath)
        self.imgname = imgPath.split('/')[-1].split('/')[-1].split('.')[0]
        self.ospath = os.getcwd()
        self.speed = speed
        self.tonic = tonic
        self.beat_per_section, self.beat = list(map(lambda x: int(x), beat.split("/")))
        self.base_note = 4
        self.delta_range = delta_range
        self.print_info = 0 if type(print_info) == int and print_info == 0 else 1
        self.print_info_end = '' if self.print_info == 0 else '\n'
        self.match_precision = match_precision
        if type(thread_num) is int:
            if thread_num < 1:
                thread_num = 1
            elif thread_num > 16:
                thread_num = 16
            self.thread_num = thread_num
        else:
            self.thread_num = 1
        self.sampling_rate = sampling_rate
        if type(threshold_method) is str:
            threshold_method = threshold_method.upper()
        else:
            threshold_method = "global"
        if threshold_method != "OTSU":
            threshold_method = "global"
            self.threshold = threshold
        else:
            self.threshold = 0
        self.threshold_method = threshold_method

        self.frame = []
        self.sorted_frame = []
        self.contours = []
        self.isDoublePianoNMN = False
        self.sections = []
        self.contours_alter_index = {}
        self.recognition_result = []
        self.timeline_result = []
        self.long_bar_line_num = 0
        if type(self.srcImg) is not np.ndarray:
            # print(self.IMAGE_NOT_FOUND_ERROR)
            if self.callback_function:
                self.callback_function(self.IMAGE_NOT_FOUND_ERROR)
            # self.output_queue.put(self.IMAGE_NOT_FOUND_ERROR)
            # if self.callback_function:
            #     self.callback_function()
        
        # 回调函数
        self.callback_function = None
        # # 进度条
        # self.progress_bar = tk.IntVar()
        # self.progress_bar.set(0)
        # # sys.stdout = stdout
        # # sys.stderr = stderr
        # # self.stdout = sys.stdout
        # # self.stderr = sys.stderr
        # self.output_text = output_text
        # # 将标准输出重定向到 Text 控件
        # # sys.stdout = TextRedirector(self.output_text, "stdout")

    def recognize(self):
        # sys.stdout = TextRedirector(self.output_text, "stdout")
        if type(self.srcImg) is not np.ndarray:
            # print(self.FILE_NOT_OPENED_ERROR)
            if self.callback_function:
                self.callback_function(self.FILE_NOT_OPENED_ERROR)
            # self.output_queue.put(self.FILE_NOT_OPENED_ERROR)
            # if self.callback_function:
            #     self.callback_function()
            return False

        # print("......正在识别" + self.imgname + "......\n")
        # self.output_text.insert(tk.END, "......正在识别" + self.imgname + "......", ("stdout",))
        # self.output_text.update()
        # self.output_text.see(tk.END)
        # self.output_queue.put(f"......正在识别{self.imgname}......\n")
        if self.callback_function:
            self.callback_function(f"......正在识别{self.imgname}......\n")
        if self.__preProcess():
            # print("......已完成二值化处理......" * self.print_info, end=self.print_info_end)
            if self.callback_function:
                self.callback_function("......已完成二值化处理......\n")
            # self.output_queue.put("......已完成二值化处理......\n" * self.print_info)
            # if self.callback_function:
            #     self.callback_function()
        if self.__locate():
            # print("......已完成轮廓定位......" * self.print_info, end=self.print_info_end)
            if self.callback_function:
                self.callback_function("......已完成轮廓定位......\n")
            # self.output_queue.put("......已完成轮廓定位......\n" * self.print_info)
            # if self.callback_function:
            #     self.callback_function()
        if self.__match():
            # print("......已完成符号匹配......" * self.print_info, end=self.print_info_end)
            if self.callback_function:
                self.callback_function("......已完成符号匹配......\n")
            # self.output_queue.put("......已完成符号匹配......\n" * self.print_info)
            # if self.callback_function:
            #     self.callback_function()
        else:
            return False
        if self.__split():
            # print("......已完成小节分区......" * self.print_info, end=self.print_info_end)
            # self.output_queue.put("......已完成小节分区......\n" * self.print_info)
            # if self.callback_function:
            #     self.callback_function()
            if self.callback_function:
                self.callback_function("......已完成小节分区......\n")
            if self.isDoublePianoNMN:
                # print("......检测到钢琴双手简谱......" * self.print_info, end=self.print_info_end)
                if self.callback_function:
                    self.callback_function("......检测到钢琴双手简谱......\n")
                # self.output_queue.put("......检测到钢琴双手简谱......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
            if self.__category():
                # print("......已完成小节内符号定位......" * self.print_info, end=self.print_info_end)
                if self.callback_function:
                    self.callback_function("......已完成小节内符号定位......\n")
                # self.output_queue.put("......已完成小节内符号定位......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
        else:
            return False
        if self.__build_contours_alter_index():
            # print("......已完成所有符号定位......" * self.print_info, end=self.print_info_end)
            if self.callback_function:
                self.callback_function("......已完成所有符号定位......\n")
            # self.output_queue.put("......已完成所有符号定位......\n" * self.print_info)
            # if self.callback_function:
            #     self.callback_function()
        if self.__rhythm():
            # print("......已完成节奏识别......" * self.print_info, end=self.print_info_end)
            if self.callback_function:
                self.callback_function("......已完成节奏识别......\n")
                # self.output_queue.put("......已完成节奏识别......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
        if self.isDoublePianoNMN:
            if self.__process_Double_section():
                # print("......已完成钢琴双手简谱小节合并......" * self.print_info, end=self.print_info_end)
                # print("......已完成音符事件时间线整理......" * self.print_info, end=self.print_info_end)
                if self.callback_function:
                    self.callback_function("......已完成钢琴双手简谱小节合并......\n")
                    self.callback_function("......已完成音符事件时间线整理......\n")
                # self.output_queue.put("......已完成钢琴双手简谱小节合并......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
                # self.output_queue.put("......已完成音符事件时间线整理......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
        else:
            if self.__process_section():
                # print("......已完成音符事件时间线整理......" * self.print_info, end=self.print_info_end)
                if self.callback_function:
                    self.callback_function("......已完成音符事件时间线整理......\n")
                # self.output_queue.put("......已完成音符事件时间线整理......\n" * self.print_info)
                # if self.callback_function:
                #     self.callback_function()
        return True

    def getRecognitionResult(self):
        return self.recognition_result

    def getTimelineResult(self):
        return self.timeline_result

    def getSpeed(self):
        return self.speed

    def saveInfo(self):
        if self.recognition_result:
            result_recognition_file = open(self.imgname + ".txt", 'w', encoding="utf8")
            for i in self.recognition_result:
                result_recognition_file.write(str(i) + '\n')
            result_recognition_file.close()
        else:
            return False
        if self.print_info == 1:
            print("......已将识别信息保存至文件" + self.imgname + ".txt......")
            # if self.callback_function:
            #     self.callback_function("......已将识别信息保存至文件" + self.imgname + ".txt......\n")
            # self.output_queue.put("......已将识别信息保存至文件" + self.imgname + ".txt......\n")
            # if self.callback_function:
            #     self.callback_function()
        return True

    def saveTimelineInfo(self):
        if self.timeline_result:
            result_timeline_file = open(self.imgname + "_timeline.txt", "w", encoding="utf8")
            for i in self.timeline_result:
                result_timeline_file.write(str(i) + '\n')
            result_timeline_file.close()
        else:
            return False
        if self.print_info == 1:
            print("......已将时间线信息保存至文件" + self.imgname + "_timeline.txt......")
            # if self.callback_function:
            #     self.callback_function("......已将时间线信息保存至文件" + self.imgname + "_timeline.txt......\n")
            # self.output_queue.put("......已将时间线信息保存至文件" + self.imgname + "_timeline.txt......\n")
            # if self.callback_function:
            #     self.callback_function()

    def readInfo(self, recognition_result_path):
        try:
            recognition_result_name = recognition_result_path.split('/')[-1].split('/')[-1]
            recognition_result_file = open(recognition_result_path, "r", encoding="utf8")
            temp_recognition_result = []
            for line in recognition_result_file.readlines():
                temp_recognition_result.append(eval(line))
            self.recognition_result = temp_recognition_result
            if self.print_info == 1:
                print("......成功读取文件" + recognition_result_name + "......")
                # if self.callback_function:
                #     self.callback_function("......成功读取文件" + recognition_result_name + "......\n")
                # self.output_queue.put("......成功读取文件" + recognition_result_name + "......\n")
                # if self.callback_function:
                #     self.callback_function()
            return True
        except:
            return False

    def __preProcess(self):
        # 主要使用全局阈值进行二值化，包括灰度化处理.
        dst = cv2.cvtColor(self.srcImg, cv2.COLOR_BGR2GRAY)
        if self.threshold == "OTSU":
            self.ret, self.thImg = cv2.threshold(dst, self.threshold, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        else:
            self.ret, self.thImg = cv2.threshold(dst, self.threshold, 255, cv2.THRESH_BINARY)
        """ 显示二值化后的图片
        print("阈值为" + str(self.ret) + ".")
        #cv2.namedWindow("thresholding", cv2.WINDOW_NORMAL)
        cv2.imshow("thresholding", self.thImg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()#"""
        return True

    def __locate(self):
        # 使用轮廓检测定位
        contours, self.hierarchy = cv2.findContours(self.thImg, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        self.contours = contours[1:]
        """ 在原图基础上画上定位到的轮廓，并保存为一张新图片
        ctImg = cv2.drawContours(self.srcImg, self.contours, -1, (255, 0, 0), 1)
        ''' 直接显示含有轮廓的原图
        #cv2.namedWindow("contours", cv2.WINDOW_NORMAL)
        cv2.imshow("contours", ctImg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        #'''
        cv2.imwrite(self.imgname + "_contours.png", ctImg)
        print("......已生成轮廓图......"  * self.print_info)#"""
        # 提取包裹一个轮廓的最小矩形的顶点坐标(当然矩形的边一定是与坐标轴平行的)
        for i in self.contours:
            horizontal = list(map(lambda x: x[0][0], i))
            vertical = list(map(lambda x: x[0][1], i))
            self.frame.append([min(vertical), max(vertical), min(horizontal), max(horizontal)])
        return True

    def __match(self):
        """
        current_time = time.localtime()
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", current_time)
        print(time_str)#"""

        # print("......准备进行字符匹配，这可能需要一些时间......" * self.print_info, end=self.print_info_end)
        if self.callback_function:
            self.callback_function("......准备进行字符匹配，这可能需要一些时间......\n")
        # self.output_queue.put("......准备进行字符匹配，这可能需要一些时间......\n" * self.print_info)
        # if self.callback_function:
        #     self.callback_function()
        start_time = time.time()

        def readTemplate(tem_path):
            kdTree = KDTree()
            tem_height, tem_width, tem_KdTree_original = kdTree.readTemplate(tem_path)
            tem_KdTree = []
            for node in tem_KdTree_original:
                tem_KdTree.append([])
                tem_KdTree[-1].append([node[0][0], node[0][1]])
                tem_KdTree[-1].append(node[1])
                tem_KdTree[-1].append(node[2])
                tem_KdTree[-1].append(node[3])
            return [tem_height, tem_width, tem_KdTree]

        templates = []
        templates_dir_name = self.ospath + "/" + "templates" + "_" * (self.sampling_rate - 1)
        try:
            templates_dir = os.listdir(templates_dir_name)
        except:
            # print(self.FOLDER_NOT_FOUND_ERROR + "templates" + "_" * (self.sampling_rate - 1))
            if self.callback_function:
                self.callback_function(self.FOLDER_NOT_FOUND_ERROR + "templates" + "_" * (self.sampling_rate - 1) + "\n")
            # self.output_queue.put(self.FOLDER_NOT_FOUND_ERROR + "templates" + "_" * (self.sampling_rate - 1) + "\n")
            # if self.callback_function:
            #     self.callback_function()
            return False
        for i in templates_dir:
            template_dir_name = templates_dir_name + "/" + i
            template_dir = os.listdir(template_dir_name)
            for j in template_dir:
                template_path = template_dir_name + "/" + j
                templates.append([i, readTemplate(template_path)])

        def matchUsingThread(part_front, part_behind):
            for num in range(part_front, part_behind):
                i = self.frame[num]
                currentFrame = self.thImg[i[0]: i[1] + 1, i[2]: i[3] + 1]
                src_height, src_width = i[1] - i[0] + 1, i[3] - i[2] + 1
                preExcludeRuler = src_height / src_width
                src_contours_temp, src_hierarchy = cv2.findContours(currentFrame,
                                                                    cv2.RETR_TREE,
                                                                    cv2.CHAIN_APPROX_NONE)
                if len(src_contours_temp) == 1:
                    i.append("none")
                    i.append([])
                    continue
                src_contours = src_contours_temp[1:]
                # cdtf：coordinate transformation，坐标变换，但其实src的坐标没变，只是要template与src高和宽相同
                src_cdtf = []
                for j in src_contours:
                    for k in range(len(j)):
                        if k % self.match_precision == self.match_precision - 1:
                            src_cdtf.append([j[k][0][0], j[k][0][1]])
                if not src_cdtf:
                    i.append("none")
                    i.append([])
                    continue
                kdTree_src_cdtf = KDTree()
                kdTree_src_cdtf.createKDTree(src_cdtf, create_list=False)

                min_sum = -1
                result = "none"
                for j in templates:
                    template_name = j[0]
                    if preExcludeRuler >= 0.9 and template_name == "h":
                        continue
                    if template_name == "d":
                        if preExcludeRuler <= 0.666667 or preExcludeRuler >= 1.5:
                            continue
                    if preExcludeRuler <= 1.5 and template_name in ["ve", 'b', "vi"]:
                        continue

                    [template_height, template_width, template_KdTree_list] = j[1]
                    template_KdTree_list_current = []
                    distance_sum_temp = 0
                    for coordinate in template_KdTree_list:
                        template_KdTree_list_current.append([])
                        template_KdTree_list_current[-1].append([coordinate[0][0] * src_width / template_width,
                                                                 coordinate[0][1] * src_height / template_height])
                        template_KdTree_list_current[-1].append(coordinate[1])
                        template_KdTree_list_current[-1].append(coordinate[2])
                        template_KdTree_list_current[-1].append(coordinate[3])
                        distance_sum_temp += kdTree_src_cdtf.searchKDTreeInNode(template_KdTree_list_current[-1][0])
                    distance_sum_temp /= len(template_KdTree_list_current)

                    distance_sum_src = 0
                    for src_coordinate in src_cdtf:
                        distance_sum_src += kdTree_src_cdtf.searchKDTreeInList(src_coordinate,
                                                                               template_KdTree_list_current)
                    distance_sum_src /= len(src_cdtf)

                    distance_sum = distance_sum_temp + distance_sum_src
                    if distance_sum < min_sum or min_sum == -1:
                        min_sum = distance_sum
                        result = template_name
                i.append(result)
                i.append([])

        frame_length = len(self.frame)
        frame_parts = []
        part_length = int(frame_length / self.thread_num)
        front = 0
        behind = part_length
        if behind == 0:
            frame_parts.append([0, frame_length])
        else:
            while behind < frame_length:
                frame_parts.append([front, behind])
                front = behind
                behind += part_length
            frame_parts.append([front, frame_length])
        
        def showProgress():
            matched_num = 0
            last_progress = -1
            while matched_num != frame_length:
                matched_num = frame_length - list(map(lambda x: len(x), self.frame)).count(4)
                if matched_num > last_progress:
                    last_progress = matched_num
                    # print(self.imgname + ": match in progress (" + str(matched_num)
                    #       + "/" + str(frame_length) + ")")
                    # self.update_output_text(self.imgname + ": match in progress (" + str(matched_num)+ "/" + str(frame_length) + ")")
                    # if self.callback_function:
                    #     self.callback_function(f"{self.imgname}: match in progress ({matched_num}/{frame_length})\n")
                    # 将输出信息放入队列
                    # self.output_queue.put(f"{self.imgname}: match in progress ({matched_num}/{frame_length})\n")
                    percentage = int(matched_num / frame_length * 100)
                    bar_length = 25  # Adjust this value based on your desired total length of the progress bar
                    completed_length = int((percentage / 100) * bar_length)
                    remaining_length = bar_length - completed_length
                    # self.output_queue.put(f"{self.imgname}: match in progress [{'#' * completed_length}{' ' * remaining_length}] ({matched_num}/{frame_length})\n")
                    print(f"{self.imgname}: match in progress [{'#' * completed_length}{' ' * remaining_length}] ({matched_num}/{frame_length})")
                else:
                    time.sleep(0.01)

        if self.callback_function:
            self.callback_function("......开始字符匹配，请耐心等待......\n")
        thread_list = []
        for frame_part in frame_parts:
            thread = threading.Thread(target=matchUsingThread, args=(frame_part[0], frame_part[1]))
            thread_list.append(thread)
        #if self.print_info == 1:
        #    thread_list.append(threading.Thread(target=showProgress, args=()))
        # print("线程数：" + str(len(thread_list)))
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()
        """
        current_time = time.localtime()
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", current_time)
        print(time_str)#"""

        print("......匹配完成......\n")
        print("耗时：{:.2f}秒\n".format(time.time() - start_time))

        """ # 将轮廓划分结果的切片保存为图片，放在一个文件夹里
        dirpath = self.ospath + "/" + self.imgname + "_slices"
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        for num in range(len(self.frame)):
            i = self.frame[num]
            i[1] += 1 if i[0] == i[1] else 0
            i[3] += 1 if i[2] == i[3] else 0
            currentFrame = self.thImg[i[0]: i[1] + 1, i[2]: i[3] + 1]
            cv2.imwrite(dirpath + "/frame" + str(num) + ".png", currentFrame)
        print("......已生成切片......")
        # 将符号匹配结果保存为txt文档
        f = open(self.imgname + "_recogResult.txt", "w")
        for i in range(len(self.frame)):
            if self.frame[i][4] in self.NAME_REFLECTION.keys():
                f.write(f"{i}: {self.NAME_REFLECTION[self.frame[i][4]]}\n")
            else:
                f.write(f"{i}: {self.frame[i][4]}\n")
        f.close()  # """

        return True

    def __split(self):
        # 按照小节线，对原曲谱作出划分，照理来说有一定的抗干扰能力
        barLines = []
        for i in self.frame:
            if i[4] == "ve":
                barLines.append(i[:4])
        if not barLines:
            # print(self.EMPTY_BAR_LINE_ERROR)
            # if self.callback_function:
            #     self.callback_function(self.EMPTY_BAR_LINE_ERROR)
            self.output_queue.put(self.EMPTY_BAR_LINE_ERROR)
            if self.callback_function:
                self.callback_function()
            return False
        vertical_line_length = list(map(lambda x: x[1] - x[0] + 1, barLines))
        max_vertical_line_length = max(vertical_line_length)
        mode_vertical_line_length = max(vertical_line_length,
                                        key=lambda x: vertical_line_length.count(x))
        i = 0
        # 通常小节线长度相近，于是先删除长度短得异常的竖线
        while i < len(barLines):
            if barLines[i][1] - barLines[i][0] <= mode_vertical_line_length * 0.7:
                del barLines[i]
            else:
                i += 1
        # NMN：numbered musical notation，数字乐谱，即简谱
        # 双手钢琴谱需要同时看两列，与一般简谱不同
        if max_vertical_line_length / mode_vertical_line_length >= 2:
            self.isDoublePianoNMN = True
        # 如果是双手简谱，则先将并列的两行分开看待，即把最左侧的小节线划为两段
        if self.isDoublePianoNMN:
            i, long_bar_line_num = 0, 0
            long_bar_lines = []
            while i < len(barLines):
                length = barLines[i][1] - barLines[i][0]
                if length > 2 * mode_vertical_line_length:
                    vLine = barLines[i]
                    long_bar_lines.append([vLine[1], vLine[2]])
                i += 1
            long_bar_lines = sorted(long_bar_lines)
            inverted_long_bar_line_index = {}
            for num, i in enumerate(long_bar_lines):
                inverted_long_bar_line_index[str(i)] = num
            i = 0
            while i < len(barLines):
                length = barLines[i][1] - barLines[i][0]
                if length > 2 * mode_vertical_line_length:
                    vLine = barLines[i]
                    barLines.append([vLine[0], vLine[0] + mode_vertical_line_length,
                                     vLine[2], vLine[3],
                                     inverted_long_bar_line_index[str([vLine[1], vLine[2]])] * 2])
                    barLines.append([vLine[1] - mode_vertical_line_length, vLine[1],
                                     vLine[2], vLine[3],
                                     inverted_long_bar_line_index[str([vLine[1], vLine[2]])] * 2 + 1])
                    long_bar_line_num += 2
                    del barLines[i]
                else:
                    i += 1
            self.long_bar_line_num = long_bar_line_num
        right_matched_sections = []
        matched_sections = [-1, -1]
        sections = []
        for i in range(len(barLines)):
            left = barLines[i]
            matched = False
            closest_matched_bar_line = -1
            for j in range(len(barLines)):
                right = barLines[j]
                if i == j or j in right_matched_sections:
                    continue
                left_section_coordinate = [int((left[1] + left[0]) / 2),
                                           int((left[3] + left[2]) / 2)]
                right_section_coordinate = [int((right[1] + right[0]) / 2),
                                            int((right[3] + right[2]) / 2)]
                height_difference = abs(left_section_coordinate[0] - right_section_coordinate[0])
                width_difference = right_section_coordinate[1] - left_section_coordinate[1]
                contact_length = min(right[1] - left[0], left[1] - right[0])
                if contact_length > mode_vertical_line_length * 0.8:
                    if width_difference > height_difference:
                        if closest_matched_bar_line > width_difference or closest_matched_bar_line == -1:
                            matched = True
                            matched_sections = [i, j]
                            closest_matched_bar_line = width_difference
            if matched:
                right = barLines[matched_sections[1]]
                right_matched_sections.append(matched_sections[1])
                section = [min(left[0], right[0]), max(left[1], right[1]),
                           left[3], right[2], matched_sections[0], matched_sections[1]]
                if len(left) > 4:
                    section.append(left[4])
                sections.append(section)
        while sections:
            min_x_y_sum = -1
            first_section_index = 0
            for i in range(len(sections)):
                section = sections[i]
                if min_x_y_sum > section[0] + section[2] or min_x_y_sum == -1:
                    first_section_index = i
                    min_x_y_sum = section[0] + section[2]
            self.sections.append([])
            for i in sections[first_section_index]:
                self.sections[-1].append(i)
            del sections[first_section_index]
            while True:
                last = self.sections[-1][5]
                i = 0
                while i < len(sections):
                    if sections[i][4] == last:
                        self.sections.append([])
                        for j in sections[i]:
                            self.sections[-1].append(j)
                        del sections[i]
                        break
                    i += 1
                if i == len(sections):
                    break
        return True

    def __category(self):
        for i in self.frame:
            for num in range(len(self.sections)):
                j = self.sections[num]
                if i[4] == "ve":
                    continue
                if j[0] <= i[0] <= j[1] or j[0] <= i[1] <= j[1]:
                    if j[2] <= i[2] <= j[3] or j[2] <= i[3] <= j[3]:
                        i[5].append(num)
            if not i[5]:
                i[5].append(len(self.sections))
        self.sorted_frame = sorted(self.frame, key=lambda x: [x[5], x[2], -x[0]])
        return True

    def __build_contours_alter_index(self):
        for num in range(len(self.contours)):
            i = self.frame[num]
            for j in range(i[0] + 1, i[1]):
                for k in range(i[2] + 1, i[3]):
                    self.contours_alter_index[str([j, k])] = num
        return True

    def __rhythm(self):
        # 语义分析方法，整体思路为先横向扫描，找到每小节内的位置最低的数字，然后将每个数字拿去纵向扫描
        section_front = 0
        for i in range(len(self.sections)):
            # base_line即为一个小节中位置最低的数字的垂直中分线对应的高度
            [base_line,
             current_section_number_set,
             current_section_horizontal_line_num,
             section_front] = self.__get_base_line(i, section_front)
            # 如果这一小节里面没有数字，则该节为空
            if not current_section_number_set:
                # 如果这一小节里的横线数量大于等于每节拍数，则需要记录等待信息
                if current_section_horizontal_line_num >= self.beat_per_section:
                    for count in range(self.beat_per_section):
                        self.recognition_result.append([i, ['0'], self.base_note])
                continue
            # character_on_base_line即为基准线上的字符的索引
            character_on_base_line = self.__get_character_on_base_line(i, base_line)
            section_rhythm = []
            j = 0
            while j < len(character_on_base_line):
                if self.frame[character_on_base_line[j]][4] == 'd' and j != 0:
                    self.frame[character_on_base_line[j - 1]].append("dotted note")
                    del character_on_base_line[j]
                elif self.frame[character_on_base_line[j]][4] == 'h' and j != 0:
                    self.frame[character_on_base_line[j - 1]].append("add horizontal line")
                    del character_on_base_line[j]
                else:
                    j += 1
            for j in character_on_base_line:
                if self.frame[j][4] in self.NUMBER_SET or self.frame[j][4] == 'h':
                    section_rhythm.append(self.__analyze_vertical_information(j))
            for j in section_rhythm:
                if j[0][0] == 'h' and len(j[0]) == 1:
                    self.recognition_result.append([i, ['0'], j[1]])
                else:
                    self.recognition_result.append([i, j[0], j[1]])
        return True

    def __get_base_line(self, section_num, section_front_in_frame):
        current_section_number_set = []
        current_section_horizontal_line_num = 0
        base_line = 0
        bottom_line = 0
        i = section_front_in_frame
        while i < len(self.sorted_frame) and section_num in self.sorted_frame[i][5]:
            if self.sorted_frame[i][4] in self.NUMBER_SET:
                current_section_number_set.append(i)
                if self.sorted_frame[i][1] > bottom_line:
                    bottom_line = self.sorted_frame[i][1]
                    base_line = int((self.sorted_frame[i][0] + self.sorted_frame[i][1]) / 2)
            elif self.sorted_frame[i][4] == 'h':
                current_section_horizontal_line_num += 1
            i += 1
        return [base_line, current_section_number_set, current_section_horizontal_line_num, i]

    def __get_character_on_base_line(self, section_index, base_line):
        character_on_base_line = []
        scanner = self.sections[section_index][2] + 1
        while scanner < self.sections[section_index][3]:
            if self.thImg[base_line][scanner] == 0:
                index = self.contours_alter_index[str([base_line, scanner])]
                character_on_base_line.append(index)
                scanner = self.frame[index][3] + 1
            else:
                scanner += 1
        return character_on_base_line

    def __analyze_vertical_information(self, character_index):
        base_note, base_info, mid_line, extra_number = self.__analyze_character_on_base_line(character_index)
        if "dotted note" in self.frame[character_index]:
            base_note /= 1.5
            self.frame[character_index].remove("dotted note")
        while "add horizontal line" in self.frame[character_index]:
            base_note = base_note * self.base_note / (base_note + self.base_note)
            self.frame[character_index].remove("add horizontal line")
        info_set = [base_info]
        exists_extra_number = extra_number[0]
        index = extra_number[1] if exists_extra_number and len(extra_number) >= 2 else ''
        while exists_extra_number:
            exists_extra_number, index, info = self.__analyze_extra_numbers(index)
            info_set.append(info)
        return [info_set, 1 / base_note]

    def __analyze_character_on_base_line(self, character_index):
        character = self.frame[character_index]
        vertical_delta_range = (character[1] - character[0]) * self.delta_range
        start = character[1]
        end = start
        extra_number = [False]
        mid_line = int((character[2] + character[3]) / 2)
        base_note = self.base_note
        info_string = character[4]
        key_signature = self.__detect_sharp_and_flat(character_index)
        matched_dot = False
        above_number = ''
        for signature in key_signature:
            if signature == 'f':
                info_string += 'b'
            elif signature == "sh":
                info_string += '#'
        if info_string[0] in self.NUMBER_SET:
            # 检测下方信息，通常是减时线和表示降八度的音点
            while end - start <= character[1] - character[0] and end < len(self.thImg):
                if self.thImg[end][mid_line] == 0:
                    index = self.contours_alter_index[str([end, mid_line])]
                    meet_character = self.frame[index]
                    if meet_character[4] == 'h':
                        base_note *= 2
                    elif meet_character[4] == 'd':
                        info_string += '-'
                        matched_dot = True
                        self.frame[index].append("matched")
                    start = meet_character[1]
                    end = start
                else:
                    end += 1
            # 检测上方信息，通常是点以及其他数字
            start = character[0]
            end = start
            dot_stack = []
            while start - end <= vertical_delta_range and end >= 0:
                if self.thImg[end][mid_line] == 0:
                    index = self.contours_alter_index[str([end, mid_line])]
                    meet_character = self.frame[index]
                    if meet_character[4] == 'd' and not matched_dot:
                        dot_stack.append(index)
                    elif meet_character[4] in self.NUMBER_SET:
                        if meet_character[4] == '0':
                            meet_character[4] = '6'
                        above_number = meet_character
                        extra_number[0] = True
                        extra_number.append(index)
                        break
                    start = meet_character[0]
                    end = start
                else:
                    end -= 1
            if extra_number[0]:
                height_mid_character = (character[1] - character[0]) / 2
                height_above_number = (above_number[1] - above_number[0]) / 2
                for index in dot_stack:
                    dot = self.frame[index]
                    height_dot = (dot[1] - dot[0]) / 2
                    if height_dot - height_mid_character < height_above_number - height_dot:
                        info_string += '+'
                        height_mid_character = height_dot
                        self.frame[index].append("matched")
            else:
                info_string += '+' * len(dot_stack)
        return base_note, info_string, mid_line, extra_number

    def __detect_sharp_and_flat(self, character_index):
        character = self.frame[character_index]
        # 检测升号和降号
        horizontal_delta_range = (character[3] - character[2]) * self.delta_range
        up_side = character[0]
        start = character[2]
        end = start
        result = []
        while start - end <= horizontal_delta_range and end >= 0:
            if self.thImg[up_side][end] == 0:
                sig_nature_index = self.contours_alter_index[str([up_side, end])]
                sig_nature = self.frame[sig_nature_index]
                if sig_nature[4] in ['f', "sh"]:
                    result.append(sig_nature[4])
                else:
                    break
                start = sig_nature[2]
                end = start
                horizontal_delta_range = sig_nature[3] - sig_nature[2]
            else:
                end -= 1
        return result

    def __analyze_extra_numbers(self, character_index):
        character = self.frame[character_index]
        vertical_delta_range = (character[1] - character[0]) * self.delta_range
        start = character[1]
        end = start
        extra_number = [False, "none"]
        mid_line = int((character[2] + character[3]) / 2)
        info_string = character[4]
        matched_dot = False
        key_signature = self.__detect_sharp_and_flat(character_index)
        above_number = ''
        for signature in key_signature:
            if signature == 'f':
                info_string += 'b'
            elif signature == "sh":
                info_string += '#'
        # 对于额外的音，也是先检查下方降音用点
        while end - start <= vertical_delta_range and end < len(self.thImg):
            if self.thImg[end][mid_line] == 0:
                index = self.contours_alter_index[str([end, mid_line])]
                meet_character = self.frame[index]
                if meet_character[4] == 'd' and len(meet_character) == 6:
                    info_string += '-'
                    matched_dot = True
                    self.frame[index].append("matched")
                elif meet_character[4] in self.NUMBER_SET:
                    break
                start = meet_character[1]
                end = start
            else:
                end += 1
        # 然后检查上方
        start = character[0]
        end = start
        dot_stack = []
        while start - end <= vertical_delta_range and end >= 0:
            if self.thImg[end][mid_line] == 0:
                index = self.contours_alter_index[str([end, mid_line])]
                meet_character = self.frame[index]
                if meet_character[4] == 'd' and not matched_dot:
                    dot_stack.append(index)
                elif meet_character[4] in self.NUMBER_SET:
                    if meet_character[4] == '0':
                        meet_character[4] = '6'
                    above_number = meet_character
                    extra_number[0] = True
                    extra_number[1] = index
                    break
                start = meet_character[0]
                end = start
            else:
                end -= 1
        if extra_number[0]:
            height_mid_character = (character[1] - character[0]) / 2
            height_above_number = (above_number[1] - above_number[0]) / 2
            for index in dot_stack:
                dot = self.frame[index]
                height_dot = (dot[1] - dot[0]) / 2
                if height_dot - height_mid_character < height_above_number - height_dot:
                    info_string += '+'
                    height_mid_character = height_dot
                    self.frame[index].append("matched")
        else:
            info_string += '+' * len(dot_stack)
        return extra_number[0], extra_number[1], info_string

    def __process_Double_section(self):
        current_real_section = -1
        section_mapping = {}
        double_piano_NMN_result = {}
        for i, section in enumerate(self.sections):
            if len(section) == 7:
                current_real_section = section[6]
                double_piano_NMN_result[current_real_section] = []
            section_mapping[i] = current_real_section
        pre_section = -1
        timeline = 0
        for recognition_result in self.recognition_result:
            curr_section = recognition_result[0]
            if section_mapping[curr_section] != pre_section:
                pre_section = section_mapping[curr_section]
                timeline = 0
            note_and_time = [recognition_result[1], timeline, recognition_result[2]]
            timeline += recognition_result[2]
            double_piano_NMN_result[section_mapping[curr_section]].append(note_and_time)

        timeline_result = []
        keys = list(double_piano_NMN_result.keys())
        for i in range(0, self.long_bar_line_num, 2):
            real_section = []
            if i in keys:
                for j in double_piano_NMN_result[i]:
                    real_section.append(j)
            if i + 1 in keys:
                for j in double_piano_NMN_result[i + 1]:
                    real_section.append(j)
            timeline_result.append(sorted(real_section, key=lambda x: x[1]))

        timeline_offset = 0
        for section in timeline_result:
            for i in section:
                self.timeline_result.append([i[0], i[1] + timeline_offset, i[2]])
            if len(self.timeline_result) != 0:
                timeline_offset = self.timeline_result[-1][1] + self.timeline_result[-1][2]

        return True

    def __process_section(self):
        if not self.recognition_result:
            return False
        timeline = 0
        for event in self.recognition_result:
            note_and_time = [event[1], timeline, event[2]]
            timeline += event[2]
            self.timeline_result.append(note_and_time)
        return True
    
    def set_callback_function(self, callback_function):
        self.callback_function = callback_function


if __name__ == "__main__":
    imgPath = input("请输入图片的路径：")
    imgRecognition = Recognition(imgPath, delta_range=1.5, print_info=1,
                                 match_precision=2, thread_num=8, sampling_rate=2)
    imgRecognition.recognize()
    imgRecognition.saveInfo()
    imgRecognition.saveTimelineInfo()
