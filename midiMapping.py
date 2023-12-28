class createMidiInfo:

    FILE_NOT_FOUND_ERROR = "该路径下未发现指定文件，请检查输入的路径是否正确。"
    tonic_mapping = {'C': 60, 'D': 62, 'E': 64, 'F': 65, 'G': 67, 'A': 69, 'B': 71}
    minor_scale = [0, 0, 2, 3, 5, 7, 8, 10, 12]
    major_scale = [0, 0, 2, 4, 5, 7, 9, 11, 12]
    suffix_set = {'+': 12, '-': -12, '#': 1, 'b': -1}

    def __init__(self, filename, speed=60, tonic='C'):
        self.filename = filename
        self.speed = speed
        self.tonic = tonic
        self.timeline_offset = 0
        self.timeline = []
        self.midi_timeline = []

    def getTimeline(self):
        return self.timeline

    def getMidiTimeline(self):
        return self.midi_timeline

    def addTimeline(self, timeline):
        for i in timeline:
            self.timeline.append([i[0], i[1] + self.timeline_offset, i[2]])
        self.timeline_offset = self.timeline[-1][1] + self.timeline[-1][2]

    def mapping(self):
        if not self.timeline:
            return False
        tonic = self.tonic[0]
        tonic_midi_code = self.tonic_mapping[self.tonic[0].upper()]
        if len(self.tonic) > 1:
            for i in self.tonic[1:]:
                tonic_midi_code += self.suffix_set[i]

        def extendMidiTimeline(note):
            pitch = int(note[0][0])
            if pitch == 0:
                return
            if tonic.isupper():
                pitch = tonic_midi_code + self.major_scale[int(note[0][0])]
            else:
                pitch = tonic_midi_code + self.minor_scale[int(note[0][0])]
            if len(note) > 1:
                note_suffix = note[0][1:]
                for j in note_suffix:
                    pitch += self.suffix_set[j]
                    if pitch < 0 or pitch > 127:  # 避免识别错误导致midi文件中出现负数，加一个范围限制
                        pitch -= self.suffix_set[j]
            self.midi_timeline[-1][1].append([pitch, int(note[1] * 4 * 60 / self.speed * 1000), 64])

        note_stack = []
        timeline_pointer = 0
        for timeline_event in self.timeline:
            if timeline_event[1] != timeline_pointer:
                self.midi_timeline.append([int(timeline_pointer * 4 * 60 / self.speed * 1000), []])
                for note_info in note_stack:
                    extendMidiTimeline(note_info)
                note_stack = []
                timeline_pointer = timeline_event[1]
            for j in timeline_event[0]:
                note_stack.append([j, timeline_event[2]])
        # 单独处理最后一个时间点的音符事件
        self.midi_timeline.append([int(timeline_pointer * 4 * 60 / self.speed * 1000), []])
        for note_info in note_stack:
            extendMidiTimeline(note_info)

        # 因为作者比较懒，所以就再遍历一次这个按时间线整理的音符事件中，删除由休止符“0”触发的部分
        i = 0
        while i < len(self.midi_timeline):
            if not self.midi_timeline[i][1]:
                del self.midi_timeline[i]
            else:
                i += 1

    def readTimeline(self, timeline_path):
        try:
            timeline_file = open(timeline_path, 'r')
        except:
            print(self.FILE_NOT_FOUND_ERROR)
            return False
        self.timeline = []
        for line in timeline_file.readlines():
            self.timeline.append(eval(line))
        return True

    def writeMidiTimeline(self):
        if not self.midi_timeline:
            return False
        midi_file = open(self.filename + "_midi_info.txt", 'w')
        for i in self.midi_timeline:
            midi_file.write(str(i) + '\n')
        midi_file.close()
        return True


if __name__ == "__main__":
    recognition_timeline_file_path = input("请输入识别生成的时间线txt文件路径：")
    timeline_filename = recognition_timeline_file_path.split('/')[-1].split('\\')[-1].split('.')[0]
    music_speed = int(input("请输入乐曲速度(每分钟四分音符数)："))
    music_tonic = input("请输入乐曲的主音：")
    createMidiTimeline = createMidiInfo(timeline_filename, speed=music_speed, tonic=music_tonic)
    createMidiTimeline.readTimeline(recognition_timeline_file_path)
    createMidiTimeline.mapping()
    createMidiTimeline.writeMidiTimeline()
    print("已生成符合createmidi.py输入格式的txt文件.")
