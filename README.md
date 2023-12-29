# 简谱识别转化音频文件的方法研究

## 一、项目简介

提取简谱中的音乐信息，依据识别到的信息生成midi文件。
Extract music information from musical scores and generate a midi file according to it.

## 二、项目运行环境

* python=3.11.1
* 第三方库依赖
  * opencv-python=4.7.0.68
  * numpy=1.24.1

* 可以使用命令

```shell
pip install -r requirements.txt
```

来安装所需的第三方库。

## 三、项目运行步骤

* 运行main.py。
* 输入简谱路径：支持图片或文件夹，相对路径或绝对路径都可以。
* 输入简谱主音：它通常在第一页的左上角“1=”之后。
* 输入简谱速度：即每分钟拍数，同在左上角。
* 选择是否输出程序中间提示信息：请输入Y或N（不区分大小写，下同）。
* 选择匹配精度：请输入L或M或H，对应低/中/高精度，一般而言输入L即可。
* 选择使用的线程数：一般与CPU核数相同即可。虽然python的线程不是真正的多线程，但仍能起到加速作用。
* 估算字符上下间距：这与简谱中符号的密集程度有关，一般来说纵向符号越稀疏，这个值需要设置得越大，范围通常在1.0-2.5。
* 二值化算法：使用全局阈值则跳过该选项即可，或者也可输入OTSU、采用大津二值化算法。
* 设置全局阈值：如果上面选择全局阈值则需要手动设置全局阈值，对于`.\test.txt`中所提样例，使用全局阈值并在后面设置为160即可。
* 手动调整中间结果：若输入Y/y，则在识别简谱后会暂停代码，并生成一份txt文件，在其中展示识别结果，此时用户可以通过修改这份txt文件来更正识别结果。

## 四、文件结构说明

* templates：模版匹配算法所用的模版文件，可通过将模版图片添加至文件夹`.\templates_imgs`中，然后运行`.\KdTree.py`来生成。
* templates_：采样率更低的模板图片，具体情况请见于课程论文的 *2.2.4 减少采样频率* 。
* templates_imgs：模版对应的图片。
* test.txt：示例用图片，尊重图片方版权，仅提供链接。
* *.py：项目代码。
  * main_copy.py：创建UI，调用其他代码实现简谱识别。
  * recognition_copy.py：识别简谱、提取音乐信息。
  * KdTree.py：读取及创建模版，实现KD树算法。
  * midiMapping.py：建立简谱符号与midi通道的映射关系。
  * createmidi.py：生成midi文件。

* new_midi_file：生成的midi结果示例。

  * Canon.mid：《C大调卡农》，简谱图片来自https://www.everyonepiano.cn/Number-31.html。
  * unravel.mid：歌曲《unravel》，简谱图片来自https://www.qinyipu.cn/jianpu/jianpudaquan/253918.html。

  * unravel_after.mid：在识别图片时进行手动更正后的结果。
