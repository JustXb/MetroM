from PyQt5 import QtSvg
import sys
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QGraphicsView, QGraphicsScene, QLabel, QMessageBox
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from PyQt5.QtSvg import QSvgRenderer
import pickle
import re

class NoScrollGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

    def wheelEvent(self, event):
        # Override wheel event to prevent scrolling
        pass

class Metro(QWidget):

    def __init__(self):
        super().__init__()
        self.__k = 1
        self.__stations = self.reader()
        self.__ways = [None, None]
        self.__path = []
        self.__time = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle('МетроМ')
        self.setWindowIcon(QIcon('img/metro.svg'))

        self.setGeometry(0, 75, 1920, 1005)
        self.setFixedSize(1920, 1005)

        # Left side: SVG rendering
        self.scene = QGraphicsScene()
        self.view = NoScrollGraphicsView(self.scene)
        # hide scrollbars
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        fixed_size = 25  # Set the desired fixed size (both width and height)

        input_layout1 = QHBoxLayout()
        self.input1 = QLineEdit(self)
        self.input1.setReadOnly(True)
        self.input1.setFixedHeight(fixed_size)
        self.input1.setFixedWidth(200)
        input_layout1.addWidget(self.input1)

        self.clearButton1 = QPushButton('X', self)
        self.clearButton1.setFixedWidth(fixed_size)
        self.clearButton1.setFixedHeight(fixed_size)
        input_layout1.addWidget(self.clearButton1)

        input_layout2 = QHBoxLayout()
        self.input2 = QLineEdit(self)
        self.input2.setReadOnly(True)
        self.input2.setFixedHeight(fixed_size)
        self.input2.setFixedWidth(200)
        input_layout2.addWidget(self.input2)

        self.clearButton2 = QPushButton('X', self)
        self.clearButton2.setFixedWidth(fixed_size)
        self.clearButton2.setFixedHeight(fixed_size)
        input_layout2.addWidget(self.clearButton2)

        self.meeting_place = QLineEdit(self)
        self.meeting_place.setReadOnly(True)
        self.meeting_place.setFixedWidth(200)
        self.meeting_place.setFixedHeight(fixed_size)

        self.time = QLineEdit(self)
        self.time.setReadOnly(True)
        self.time.setFixedWidth(200)
        self.time.setFixedHeight(fixed_size)

        # Layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.view)

        fromL = QLabel("Откуда:")
        toL = QLabel("Куда:")
        timeL = QLabel("Время поездки:")
        meetL = QLabel("Место встречи:")

        control_layout = QVBoxLayout()
        control_layout.setAlignment(Qt.AlignTop)

        control_layout.addWidget(fromL)
        control_layout.addLayout(input_layout1)

        control_layout.addWidget(toL)
        control_layout.addLayout(input_layout2)

        control_layout.addWidget(timeL)
        control_layout.addWidget(self.time)

        control_layout.addWidget(meetL)
        control_layout.addWidget(self.meeting_place)

        layout.addLayout(control_layout)

        self.clearButton1.clicked.connect(self.clear_input1)
        self.clearButton2.clicked.connect(self.clear_input2)

        self.set_default_bg()
        self.draw_buttons()

        self.show()

    def showErrorMessage(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Станции отправления и назначения совпадают. Выберите другую станцию")
        msg.setWindowTitle("Ошибка")
        msg.exec_()

    def load_svg(self, filename, bg = Qt.white):
        renderer = QSvgRenderer(filename)
        pixmap = QPixmap(renderer.defaultSize())  # Create a pixmap with the SVG's size
        pixmap.fill(bg)  # Fill the pixmap with a white background
        painter = QPainter(pixmap)
        renderer.render(painter)  # Render the SVG onto the pixmap
        painter.end()  # End painting
        self.scene.addPixmap(pixmap)  # Add the rendered SVG to the scene

    def draw_buttons(self):
        for crd, st in self.__stations.items():
            button = QPushButton(str(crd), self)
            button.setFixedSize(4, 4)
            button.setStyleSheet(f"border-radius: 2; background: {st['col']};opacity: 0.1;")
            button.clicked.connect(self.on_station_click)
            button.setCursor(Qt.PointingHandCursor)
            button.move(QPoint(int(crd[0] / 2.88) - 3 + 321, int(crd[1] / 2.88) - 3 + 13))

        self.scene.addWidget(button)

    def isDejkstraMode(self):
        return self.__ways[0] is not None and self.__ways[1] is not None

    def set_default_bg(self):
        self.scene.clear()
        self.load_svg('graph.svg')

    def set_dejkstra_bg(self):
        self.scene.clear()
        self.load_svg('graph-50p.svg')

    def on_station_click(self):
        sender = self.sender()

        if not self.isDejkstraMode():
            if self.__ways[0] is None:
                point = tuple(map(int, re.findall(r'\d+', sender.text())))
                if point == self.__ways[1]:
                    self.showErrorMessage()
                    return
                self.__ways[0] = point
                name = str(self.__stations[self.__ways[0]]['name'])
                self.input1.setText(name)
                if self.__ways[1] is not None:
                    self.start_dejkstra()
            elif self.__ways[1] is None:
                point = tuple(map(int, re.findall(r'\d+', sender.text())))
                if point == self.__ways[0]:
                    self.showErrorMessage()
                    return
                self.__ways[1] = point
                name = str(self.__stations[self.__ways[1]]['name'])
                self.input2.setText(name)
                self.start_dejkstra()

    def start_dejkstra(self):
        self.dejkstra()
        self.scene.clear()
        self.prepareSvg()
        self.set_dejkstra_bg()
        self.time.setText(f"{self.__time} минут")
        self.load_svg('path.svg', bg=Qt.transparent)

    def clear_input1(self):
        self.__ways[0] = None
        self.clear_input(self.input1)

    def clear_input2(self):
        self.__ways[1] = None
        self.clear_input(self.input2)

    def clear_input(self, input):
        input.clear()
        self.__path = []
        self.__time = 0
        self.time.setText("")
        self.meeting_place.setText("")
        self.set_default_bg()

    def prepareSvg(self):
        res = """<?xml version="1.0" encoding="UTF-8"?><svg class="scheme-objects-view__scheme-svg" viewBox="0 0 3000 3500" width="1041.6667" height="1215" version="1.1">"""

        for crd in self.__path:
            res += self.__stations[crd]['svg']

        for i in range(len(self.__path) - 1):
            crd1 = self.__path[i]
            crd2 = self.__path[i+1]
            res += self.__stations[crd1]['ways'][crd2]['svg']
            # print('from', self.__stations[crd1]['name'], 'to', self.__stations[crd2]['name'], self.__stations[crd1]['ways'][crd2]['svg'])

        res += "</svg>"
        with open('path.svg', 'w', encoding="utf-8") as f:
            f.write(res)

    def dejkstra(self):
        inf = 1000000000
        data = self.__stations.keys()
        ptoi = dict()
        itop = dict()
        for i, p in enumerate(data):
            ptoi[p] = i
            itop[i] = p
        n = len(data)
        D = [inf] * n
        U = [False] * n
        P = [-1] * n
        start = ptoi[self.__ways[0]]
        D[start] = 0

        for i in range(n):
            v = 1000000
            for j in range(n):
                if not U[j] and (v == 1000000 or D[j] < D[v]):
                    v = j

            U[v] = True

            for to in self.__stations[itop[v]]['to']:
                toi = ptoi[to]
                w = self.__stations[itop[v]]['ways'][to]['w']
                if D[v] + w < D[toi]:
                    D[toi] = D[v] + w
                    P[toi] = v

        end = ptoi[self.__ways[1]]
        while end != -1:
            self.__path.append(itop[end])
            end = P[end]

        for i in range(len(self.__path) - 1):
            crd1 = self.__path[i]
            crd2 = self.__path[i+1]
            self.__time += self.__stations[crd1]['ways'][crd2]['w']

        a = 0

        for i in range(len(self.__path) - 1):
            crd1 = self.__path[i]
            crd2 = self.__path[i+1]
            a += self.__stations[crd1]['ways'][crd2]['w']
            if a > self.__time / 2:
                self.meeting_place.setText(self.__stations[crd1]['name'])
                break


    def reader(self):
        with open("stations_complete.pickle", "rb") as f:
            stations = pickle.load(f)
        return stations


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Metro()
    sys.exit(app.exec_())
