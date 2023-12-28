import os
import sys

"""
将timeline_deltatime类型的txt文件转换为midi文件
"""


class createMidi:

    ANALYSIS_ERROR = '抱歉，不能解析该文件。'
    headInfoI = b'\x4d\x54\x68\x64\x00\x00\x00\x06\x00\x00\x00\x01\x01\xf4\x4d\x54\x72\x6b'
    body = b'\x00\xff\x51\x03\x07\xa1\x20\x00\xc0\x00'
    endInfo = b'\x00\xff\x2f\x00'

    def __init__(self, mode, midi_info_arg, midi_name='temp'):
        self.timePointer = 0
        self.content = b''
        self.ospath = os.getcwd()
        self.bodylen = len(self.body)
        if mode == 0:
            self.__readTimelineFile()
        elif mode == 1:
            self.__acceptTimelineInfo(midi_info_arg, midi_name)

    def __countDeltatime(self, deltatime):
        deltatimeString = ''
        deltatime = str(bin(deltatime))[2:]
        while len(deltatime) < 7:
            deltatime = '0' + deltatime
        deltatimeString = '0' + deltatime[-7:]
        if len(deltatime) == 7:
            return [int(deltatimeString, base=2).to_bytes(1, 'big'), 1]
        deltatime = deltatime[:-7]
        while len(deltatime) > 7:
            deltatimeString = '1' + deltatime[-7:] + deltatimeString
            deltatime = deltatime[:-7]
        while len(deltatime) < 7:
            deltatime = '0' + deltatime
        deltatimeString = '1' + deltatime + deltatimeString
        bytes_len = int(len(deltatimeString) / 8)
        return [int(deltatimeString, base=2).to_bytes(bytes_len, 'big'), bytes_len]

    def __bodyHandler(self):
        waitOff = []
        lasttime = 0
        isIntervalExists = False
        for num in range(len(self.bodycontent)):
            try:
                i = eval(self.bodycontent[num])
            except:
                print('Error happens in line %d.' % num)
                return False
            self.timePointer = int(i[0])
            while waitOff and self.timePointer >= waitOff[0][0]:
                [deltatime, deltatimeLength] = self.__countDeltatime(waitOff[0][0] - lasttime)
                self.bodylen += deltatimeLength
                self.body += deltatime
                isIntervalExists = True
                self.body += b'\x80' + waitOff[0][1].to_bytes(1, 'big') + b'\x40'
                self.bodylen += 3
                isIntervalExists = False
                lasttime = waitOff[0][0]
                del waitOff[0]
            [deltatime, deltatimeLength] = self.__countDeltatime(self.timePointer - lasttime)
            self.body += deltatime
            self.bodylen += deltatimeLength
            isIntervalExists = True
            for j in i[1]:
                if not isIntervalExists:
                    self.body += b'\x00'
                    self.bodylen += 1
                self.body += b'\x90' + j[0].to_bytes(1, 'big') + j[2].to_bytes(1, 'big')
                isIntervalExists = False
                self.bodylen += 3
                waitOff.append([self.timePointer + j[1], j[0]])
                waitOff = sorted(waitOff, key=lambda x: x[0])
            lasttime = self.timePointer
            num += 1
        while waitOff:
            [deltatime, deltatimeLength] = self.__countDeltatime(waitOff[0][0] - lasttime)
            self.bodylen += deltatimeLength
            self.body += deltatime
            isIntervalExists = True
            self.body += b'\x80' + waitOff[0][1].to_bytes(1, 'big') + b'\x40'
            self.bodylen += 3
            isIntervalExists = False
            lasttime = waitOff[0][0]
            del waitOff[0]
        self.body += self.endInfo
        self.bodylen += len(self.endInfo)
        return True

    def __contentHandler(self):
        self.content += self.headInfoI
        self.content += self.bodylen.to_bytes(4, 'big')
        self.content += self.body

    def __acceptTimelineInfo(self, timeline_info_list, target_name):
        self.bodycontent = []
        for i in timeline_info_list:
            self.bodycontent.append(str(i))
        self.targetfilename = target_name

    def __readTimelineFile(self):
        sourcefilename = input('请输入原始数据文件路径：')
        try:
            self.sourcefile = open(sourcefilename, 'r')
            self.targetfilename = sourcefilename.split('\\')[-1].split('.')[0]
            self.bodycontent = self.sourcefile.readlines()
        except:
            print('未找到文件\'' + sourcefilename + '\'。')
            raise FileNotFoundError

    def createmidifile(self):
        if not self.__bodyHandler():
            print(self.ANALYSIS_ERROR)
            return False
        self.__contentHandler()
        targetfileFolderPath = self.ospath + '\\new_midi_file'
        if not os.path.exists(targetfileFolderPath):
            os.mkdir(targetfileFolderPath)
        targetPath = targetfileFolderPath + '\\' + self.targetfilename + '.mid'
        targetfile = open(targetPath, 'wb')
        targetfile.write(self.content)
        targetfile.close()
        print('......已创建文件\'' + self.targetfilename + '.mid\'......')
        print('......请在目录\'new_midi_file\'下查看......')
        return True


if __name__ == '__main__':
    try:
        midi = createMidi(0, 0)
    except:
        sys.exit(1)
    midi.createmidifile()
