import os
import cv2
import numpy as np


class KDNode:
    def __init__(self, value, split, left, right):
        self.value = value
        self.split = split
        self.right = right
        self.left = left


class KDTree:
    # expect data like [[x.1.1, x.1.2, ..., x.1.k], [x.2.1, x.2.2, ..., x.2.k], ..., [x.n.1, x.n.2, ..., x.n.k]]
    def __init__(self):
        self.KdTree = []
        self.kd_tree_root_node = KDNode([0, 0], 0, None, None)
        self.nearest_distance = -1

    def createKDTree(self, data, create_list=True):
        if not data:
            return None
        k = len(data[0])

        def createKDNode(data_set, split_order):
            data_set_length = len(data_set)
            if data_set_length == 0:
                return None
            data_set = sorted(data_set, key=lambda x: x[split_order])
            median_position = int(data_set_length / 2)
            median = data_set[median_position]
            return KDNode(median, split_order,
                          createKDNode(data_set[0:median_position], (split_order + 1) % k),
                          createKDNode(data_set[median_position + 1:], (split_order + 1) % k))

        self.kd_tree_root_node = createKDNode(data, 0)

        """
        def showKDTree(node):

            def showKDTreeInPreorder(preorder_node):
                if preorder_node:
                    print(str(preorder_node.value) + ", " + str(preorder_node.split))
                    showKDTreeInPreorder(preorder_node.left)
                    showKDTreeInPreorder(preorder_node.right)
                else:
                    print("None")

            def showKDTreeInLevel(level_node):
                node_queue = [level_node]
                pre_flag = 0
                while node_queue:
                    current_node = node_queue[0]
                    if current_node:
                        flag = current_node.split
                        if flag != pre_flag:
                            pre_flag = flag
                            print("")
                        print(str(current_node.value) + ", " + str(current_node.split), end="; ")
                        node_queue.append(current_node.left)
                        node_queue.append(current_node.right)
                    del node_queue[0]

            print("前序遍历：")
            showKDTreeInPreorder(node)
            print("层序遍历：")
            showKDTreeInLevel(node)
        showKDTree(kd_tree_root_node)#"""
        if type(create_list) is not bool or not create_list:
            return None

        def buildKDTreeList(node):
            node_queue = [[node, -1, -1]]
            kdtree_with_parent_index = []
            while node_queue:
                [current_node, parent_index, direction] = node_queue[0]
                if current_node:
                    kdtree_with_parent_index.append([current_node.value,
                                                     current_node.split,
                                                     parent_index,
                                                     direction])
                    node_queue.append([current_node.left, len(kdtree_with_parent_index) - 1, 0])
                    node_queue.append([current_node.right, len(kdtree_with_parent_index) - 1, 1])
                del node_queue[0]
            kdtree_node_num = len(kdtree_with_parent_index)
            for i in range(kdtree_node_num):
                self.KdTree.append(kdtree_with_parent_index[i][0:2])
                child_num = 0
                for j in range(i + 1, kdtree_node_num + 1):
                    if j == kdtree_node_num:
                        for l in range(0, 2 - child_num):
                            self.KdTree[i].append(65535)
                    elif i == kdtree_with_parent_index[j][2]:
                        if kdtree_with_parent_index[j][3] == 0:
                            self.KdTree[i].append(j)
                        else:
                            if child_num == 0:
                                self.KdTree[i].append(65535)
                                child_num += 1
                            self.KdTree[i].append(j)
                        child_num += 1
                    if child_num == 2:
                        break
        buildKDTreeList(self.kd_tree_root_node)

    def searchKDTreeInList(self, value, data_set):
        if type(data_set) is int:
            data_set = self.KdTree
        self.nearest_distance = -1

        def recursion(index):
            if index == 65535:
                return
            node = data_set[index]
            axis = node[1]
            axis_distance = value[axis] - node[0][axis]
            if axis_distance < 0:
                recursion(node[2])
            else:
                recursion(node[3])
            square_distance = sum((x1 - x2) ** 2 for x1, x2 in zip(value, node[0]))
            if self.nearest_distance > square_distance or self.nearest_distance == -1:
                self.nearest_distance = square_distance
            if self.nearest_distance > axis_distance ** 2:
                if axis_distance < 0:
                    recursion(node[3])
                else:
                    recursion(node[2])
        recursion(0)

        return self.nearest_distance

    def searchKDTreeInNode(self, value):
        self.nearest_distance = -1

        def recursion(node):
            if not node:
                return
            axis = node.split
            axis_distance = value[axis] - node.value[axis]
            if axis_distance < 0:
                recursion(node.left)
            else:
                recursion(node.right)
            square_distance = sum((x1 - x2) ** 2 for x1, x2 in zip(value, node.value))
            if self.nearest_distance > square_distance or self.nearest_distance == -1:
                self.nearest_distance = square_distance
            if self.nearest_distance > axis_distance ** 2:
                if axis_distance < 0:
                    recursion(node.right)
                else:
                    recursion(node.left)

        recursion(self.kd_tree_root_node)

        return self.nearest_distance

    def writeTemplate(self, name, img_path, sampling_rate=1):
        self_path = os.getcwd()

        def readTemplateImage(image_path):
            template = cv2.imread(image_path)
            if type(template) is not np.ndarray:
                print("未找到指定文件，请检查路径上是否存在该图片。")
                return None
            height, width = template.shape[:2]
            template_dst = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            template_ret, template_thImg = cv2.threshold(template_dst, 220, 255, cv2.THRESH_BINARY)
            template_contours_temp, template_hierarchy = cv2.findContours(template_thImg,
                                                                          cv2.RETR_TREE,
                                                                          cv2.CHAIN_APPROX_NONE)
            template_contours = template_contours_temp[1:]
            template_contours_set = []
            for contour in template_contours:
                for num, point in enumerate(contour):
                    if num % sampling_rate == sampling_rate - 1:
                        template_contours_set.append([point[0][0], point[0][1]])
            self.createKDTree(template_contours_set)
            return height, width
        template_height, template_width = readTemplateImage(img_path)

        if type(sampling_rate) is not int or sampling_rate < 1:
            sampling_rate = 1
        template_dir = self_path + "\\" + "templates" + "_" * (sampling_rate - 1)
        if not os.path.exists(template_dir):
            os.mkdir(template_dir)
        dir_path = template_dir + "\\" + name
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        template_num = len(os.listdir(dir_path)) + 1
        template_name = name + "_" + str(template_num) + ".merry"

        template_file = open(dir_path + "\\" + template_name, "wb")
        template_file.write(b"Template")
        template_file.write(b"\x00\x00")
        template_file.write(template_height.to_bytes(2, "big"))
        template_file.write(template_width.to_bytes(2, "big"))
        template_file.write(b"\x00\x00")
        for node in self.KdTree:
            for coordinate in node[0]:
                template_file.write(int(coordinate).to_bytes(2, "big"))
            template_file.write(node[1].to_bytes(1, "big"))
            template_file.write(node[2].to_bytes(2, "big"))
            template_file.write(node[3].to_bytes(2, "big"))
        template_file.write(b"\x00\x00")
        template_file.close()

    def readTemplate(self, template_path):
        template_file = open(template_path, "rb")
        content = template_file.read()
        template_height = int.from_bytes(content[10:12], "big")
        template_width = int.from_bytes(content[12:14], "big")
        for pointer in range(16, len(content) - 2, 9):
            x = int.from_bytes(content[pointer: pointer + 2], "big")
            y = int.from_bytes(content[pointer + 2: pointer + 4], "big")
            split = int.from_bytes(content[pointer + 4: pointer + 5], "big")
            child_left = int.from_bytes(content[pointer + 5: pointer + 7], "big")
            child_right = int.from_bytes(content[pointer + 7: pointer + 9], "big")
            self.KdTree.append([[x, y], split, child_left, child_right])
        template_file.close()
        return template_height, template_width, self.KdTree

    def getKDTree(self):
        return self.KdTree


if __name__ == "__main__":
    dirlist = os.listdir("templates_imgs")
    for i in dirlist:
        cha = os.listdir("templates_imgs\\" + i)
        for j in cha:
            k = KDTree()
            k.writeTemplate(i, "templates_imgs\\" + i + "\\" + j, sampling_rate=2)
