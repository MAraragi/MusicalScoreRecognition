import os
from recognition import Recognition
from midiMapping import createMidiInfo
from createmidi import createMidi


args = {"speed": 150, "tonic": 'C', 'beat': "4/4", "delta_range": 1.5, "print_info": 1, "match_precision": 2,
        "thread_num": 8, "sampling_rate": 2, "threshold_method": "global", "threshold": 160}


def main():

    src_img_path = input("请输入简谱图片路径或文件夹路径：")
    music_name = src_img_path.split('/')[-1].split('\\')[-1].split('.')[0]
    tonic = input("请输入简谱主音(在第一页左上角‘1=’后噢)：")
    if tonic != '':
        args["tonic"] = tonic
    speed = input("请输入简谱速度(每分钟拍数，同在左上角，‘🎶=’后)：")
    if speed != '':
        args["speed"] = int(speed)
    do_print_info = input("是否输出中间信息[Y/N]：").upper()
    if do_print_info != '':
        if do_print_info == 'N':
            args["print_info"] = 0
    match_precision = input("请选择匹配精度[L/M/H]：").upper()
    if match_precision != '':
        if match_precision[0] == 'H':
            args["match_precision"] = 1
            args["sampling_rate"] = 1
        elif match_precision[0] == 'M':
            args["match_precision"] = 2
            args["sampling_rate"] = 1
    thread_num = input("准备开几个线程来跑呢(跟cpu核数一样就好，1~16都可以)：")
    if thread_num != '':
        args["thread_num"] = int(thread_num)
    delta_range = input("估算一下字符上下间距(一般在1.0~2.5就好，我觉得1.5挺好的)：")
    if delta_range != '':
        args["delta_range"] = float(delta_range)
    threshold_method = input("二值化采取什么算法比较好(有水印的话用OTSU比较好，其他时候直接跳过这项即可)：").upper()
    if threshold_method != '':
        args["threshold_method"] = threshold_method
        if threshold_method != "OTSU":
            threshold = input("全局阈值想要设置为多少呢(如果直接跳过的话默认160喔)：")
            if threshold != '':
                args["threshold"] = int(threshold)
    else:
        threshold = input("全局阈值想要设置为多少呢(如果直接跳过的话默认160喔)：")
        if threshold != '':
            args["threshold"] = int(threshold)
    wanna_debug = input("需要自己手动调整一下中间过程吗(不输入Y/y就默认不改哈)：").upper()

    midi_map = createMidiInfo(music_name, speed=args["speed"], tonic=args["tonic"])
    if os.path.isdir(src_img_path):
        music_sheets = []
        music_sheets_temp = os.listdir(src_img_path)
        music_sheets_temp = sorted(music_sheets_temp)
        print("路径”" + src_img_path + "“下有以下文件：")
        for num, detected_file_name in enumerate(music_sheets_temp):
            print(str(num) + ': ' + detected_file_name)
        ignored_file_num = list(map(lambda x: int(x), input("请输入不需要检测的文件的序号(以空格分隔)：").split()))
        for num, i in enumerate(music_sheets_temp):
            if num not in ignored_file_num:
                music_sheets.append(src_img_path + "\\" + i)
                sheet_recognition = Recognition(music_sheets[-1],
                                                delta_range=args["delta_range"],
                                                print_info=args["print_info"],
                                                match_precision=args["match_precision"],
                                                thread_num=args["thread_num"],
                                                sampling_rate=args["sampling_rate"],
                                                threshold_method=args["threshold_method"],
                                                threshold=args["threshold"])
                sheet_recognition.recognize()
                if wanna_debug == 'Y':
                    sheet_recognition.saveInfo()
                    print("......请查看代码同目录下文件" + i.split('.')[0] + ".txt并订正......")
                    while True:
                        next_step = input("......改好了就输入[Y/y]好接着分析哈.......：").upper()
                        if next_step == 'Y':
                            break
                    sheet_recognition.readInfo(i.split('.')[0] + ".txt")
                recognition_result = sheet_recognition.getTimelineResult()
                midi_map.addTimeline(recognition_result)
    else:
        sheet_recognition = Recognition(src_img_path,
                                        delta_range=args["delta_range"],
                                        print_info=args["print_info"],
                                        match_precision=args["match_precision"],
                                        thread_num=args["thread_num"],
                                        sampling_rate=args["sampling_rate"],
                                        threshold_method=args["threshold_method"],
                                        threshold=args["threshold"])
        sheet_recognition.recognize()
        if wanna_debug == 'Y':
            sheet_recognition.saveInfo()
            img_name = src_img_path.split("\\")[-1].split("/")[-1].split('.')[0]
            print("......请查看代码同目录下文件" + img_name + ".txt并订正......")
            while True:
                next_step = input("......改好了就输入[Y/y]好接着分析哈.......：").upper()
                if next_step == 'Y':
                    break
            sheet_recognition.readInfo(img_name + ".txt")
        recognition_result = sheet_recognition.getTimelineResult()
        midi_map.addTimeline(recognition_result)
    midi_map.mapping()
    midi_timeline = midi_map.getMidiTimeline()
    make_midi = createMidi(1, midi_timeline, midi_name=music_name)
    make_midi.createmidifile()


if __name__ == "__main__":
    main()
