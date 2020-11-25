from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import folium
import sys, glob, os, json, requests, io, time
import numpy as np
import pandas as pd
from Data import apiKeys as key

PATH = "/Users/sseungmn/Documents/workspace/ws1/Data/"
NUMLIST = 10


class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initLayout()
        self.setGeometry(300, 300, 900, 600)

    def initUI(self):
        self.lbl1 = QLabel("출발지")
        self.lbl2 = QLabel("도착지")
        self.starting = lineEdit("starting")
        self.destination = lineEdit("destination")
        self.engine = webEngine()
        self.map = Map()
        self.route = Route()
        self.space = QSpacerItem(0, 0, QSizePolicy.Expanding)
        self.resetBtn = pushButton("reset")
        self.engine.load(QUrl.fromLocalFile(PATH + "map.html"))
        self.trabletimeLbl = label("예상시간 : ")
        self.mruView = listWidget()

        self.starting.returnPressed.connect(self.starting.onEntered)
        self.destination.returnPressed.connect(self.destination.onEntered)
        self.starting.sendText.connect(self.map.onGaved)
        self.starting.sendText.connect(self.route.onEntered)
        self.destination.sendText.connect(self.map.onGaved)
        self.destination.sendText.connect(self.route.onEntered)
        self.route.timeCalculated.connect(self.trabletimeLbl.onEntered)
        self.map.mapChanged.connect(self.engine.changed)

        self.resetBtn.resetPressed.connect(self.starting.resetPressed)
        self.resetBtn.resetPressed.connect(self.destination.resetPressed)
        self.resetBtn.resetPressed.connect(self.map.resetPressed)
        self.resetBtn.resetPressed.connect(self.trabletimeLbl.resetPressed)
        # self.map.mapChanged.connect(self.engine.changed)

        self.mruView.itemDoubleClicked.connect(self.starting.itemDoubleClicked)
        self.mruView.itemDoubleClicked.connect(self.destination.itemDoubleClicked)

    def initLayout(self):
        txt1 = QHBoxLayout()
        txt1.addWidget(self.lbl1)
        txt1.addWidget(self.starting)

        txt2 = QHBoxLayout()
        txt2.addWidget(self.lbl2)
        txt2.addWidget(self.destination)

        txtbox = QVBoxLayout()
        txtbox.addLayout(txt1)
        txtbox.addLayout(txt2)

        searchbox = QHBoxLayout()
        searchbox.addLayout(txtbox)
        searchbox.addWidget(self.resetBtn)

        vbox = QVBoxLayout()
        vbox.addLayout(searchbox)
        vbox.addWidget(self.trabletimeLbl)
        vbox.addWidget(self.mruView)
        vbox.addSpacerItem(self.space)
        # vbox.addSpacing(300)

        hbox = QHBoxLayout()
        hbox.addWidget(self.engine)
        hbox.addLayout(vbox)

        self.setLayout(hbox)


class listWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.showMaximized()
        self.refresh()

        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def refresh(self):
        with open("./Data/test.txt", "rt") as f:
            for line in f.readlines():
                print(line.rstrip("\n"))
                self.addItem(line.rstrip("\n"))


class webEngine(QWebEngineView):
    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def changed(self):
        print("engine changed")
        url = QUrl.fromLocalFile(PATH + "map.html")
        if url.isValid():
            self.load(url)
        else:
            print("Invalid")


class label(QLabel):
    def __init__(self, text):
        super().__init__()
        self.setText(text)

    @pyqtSlot(str)
    def onEntered(self, message):
        print("label onEntered")
        self.setText(message)

    @pyqtSlot()
    def resetPressed(self):
        print("label resetPressed")
        self.setText("")


class pushButton(QPushButton):
    resetPressed = pyqtSignal()

    def __init__(self, text):
        super().__init__()
        self.setText(text)

    def mousePressEvent(self, QMouseEvent):
        print("reset Pressed")
        self.resetPressed.emit()


class lineEdit(QLineEdit):
    sendText = pyqtSignal(str, str)

    def __init__(self, ID):
        super().__init__()
        self.id = ID

    @pyqtSlot()
    def onEntered(self):
        print("lineEdit onEntered")
        _txt = self.text()

        if self.id == "starting":
            with open("./Data/test.txt", mode="r+", encoding="utf-8") as f:
                lines = f.readlines()
                count = len(lines)

                if count >= NUMLIST:
                    f.seek(0)
                    for i in range(count - (NUMLIST - 1), count):
                        f.write(lines[i])
                    f.truncate()

        with open("./Data/test.txt", mode="at", encoding="utf-8") as f:
            if self.id == "destination":
                f.write(" " + _txt + "\n")
            else:
                f.write(_txt)
        self.sendText.emit(self.id, _txt)

    @pyqtSlot()
    def resetPressed(self):
        print("lineEdit resetPressed")
        self.setText("")

    @pyqtSlot(QListWidgetItem)
    def itemDoubleClicked(self, item):
        _txt = ""
        if self.id == "starting":
            _txt = item.text().split()[0]
        elif self.id == "destination":
            _txt = item.text().split()[1]

        self.setText(_txt)
        self.sendText.emit(self.id, _txt)

class Map(QObject):
    mapChanged = pyqtSignal()

    _src = glob.glob(os.path.join(PATH + "*.xlsx"))[0]
    _data = pd.read_excel(_src, sheet_name="대여소현황")
    _dataset = _data[["대여소_구", "대여소명", "대여소주소", "위도", "경도", "거치대수"]]

    _src_songpa = _dataset[_dataset["대여소_구"].str.contains("송파구")]
    _src_songpa.index = range(len(_src_songpa))
    _src_data_size = len(_src_songpa)

    _loc = [37.4952, 127.130]

    def __init__(self):
        super().__init__()
        self.raw_map_dr_songpa = folium.Map(
            location=self._loc, zoom_start=14
        )  # 아무것도 없는 맵
        self.map_dr_songpa = folium.Map(
            location=self._loc, zoom_start=14
        )  # 모든 정류장이 나와있는 맵
        self.marked_map_dr_songpa = folium.Map(
            location=self._loc, zoom_start=14
        )  # 검색한 정류장만 나와있는 맵
        self.map_dr_songpa.save(PATH + "rawMap.html", close_file=False)

        self.station_group = folium.FeatureGroup(name="Stations")  # 모든 정류장 마커
        self.marker_group = folium.FeatureGroup(name="Stations")  # 검색한 정류장 마커
        # print(self.feature_group) #debuging
        self.mark_buffer = {"starting": False, "destination": False}

        for i in range(self._src_data_size):
            folium.Marker(
                list(self._src_songpa.iloc[i][["위도", "경도"]]),
                popup=self._src_songpa.iloc[i][["대여소주소"]],
                icon=folium.Icon(color="green"),
            ).add_to(self.station_group)
        self.station_group.add_to(self.map_dr_songpa)

        self.map_dr_songpa.save(PATH + "map.html", close_file=False)

    def find_location(self, address):
        URL = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={address}"
        HEADERS = {"Authorization": f"KakaoAK {key.KAKAO_RESTAPI_KEY}"}
        places = requests.get(URL, headers=HEADERS).text
        jObject = json.loads(places).get("documents")[0]
        des = [jObject.get("x"), jObject.get("y")]
        return des

    # return pandas object of the closest station
    def find_closest(self, address):
        min_ = 10000
        val = 0
        now = self.find_location(address)

        for i in range(self._src_data_size):
            temp = 100000 * np.sqrt(
                np.square(float(self._src_songpa.iloc[i][["위도"]] - float(now[1])))
                + np.square(float(self._src_songpa.iloc[i][["경도"]] - float(now[0])))
            )
            if min_ > temp:
                val = i
                min_ = temp
        return self._src_songpa.iloc[val]

    #                            (ID , Address)
    def mark_closest_staion(self, obj, text):
        current = self.find_closest(text)
        self.mark_buffer[obj] = current
        folium.Marker(
            list(current.loc[["위도", "경도"]]),
            popup=current.loc[["대여소주소"]],
            icon=folium.Icon(color="blue"),
        ).add_to(self.marker_group)

        self.marker_group.add_to(self.marked_map_dr_songpa)

    @pyqtSlot(str, str)
    def onGaved(self, obj, text):
        print("map onGaved : " + obj + "," + text)
        self.mark_closest_staion(obj, text)
        self.marked_map_dr_songpa.save(PATH + "map.html", close_file=False)
        self.mapChanged.emit()

    @pyqtSlot()
    def resetPressed(self):
        print("map resetPressed")
        self.marker_group = folium.FeatureGroup(name="Markers")
        self.map_dr_songpa.save(PATH + "map.html", close_file=False)
        self.marked_map_dr_songpa = self.raw_map_dr_songpa
        self.mapChanged.emit()


class Route(QObject):
    timeCalculated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.starting = ""
        self.destination = ""

    def find_location(self, address):
        _url = f"https://search.map.daum.net/mapsearch/map.daum?&q={address}&msFlag=A&sort=0&gb=R"
        _headers = {"Host": "search.map.daum.net", "Referer": "https://map.kakao.com/"}
        _raw = requests.get(_url, headers=_headers)
        _json = _raw.json().get("place")[0]
        _location = (_json.get("x"), _json.get("y"), _json.get("sourceId"))
        return _location

    def find_route(self, s, e, method):
        _sX, _sY, _sID = self.find_location(s)
        _eX, _eY, _eID = self.find_location(e)

        _headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)\
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
        }

        if method == "bikeset":
            _url = f"https://map.kakao.com/route/bikeset.json?sX={_sX}&sY={_sY}&eX={_eX}&eY={_eY}"
        elif method == "walkset":
            _url = f"https://map.kakao.com/route/walkset.json?\
                    sX={_sX}&sY={_sY}&eX={_eX}&eY={_eY}&ids={_sID},{_eID}"

        _raw = requests.get(_url, headers=_headers)

        if _raw.status_code == 200:
            _json = _raw.json().get("directions")
            _time = _json[0].get("time") // 60
            _message = "[" + method + "] " + s + "->" + e + ":" + str(_time) + "분"
            return _message
        else:
            print("ERROR : ", _raw.status_code)
            return -1

    @pyqtSlot(str, str)
    def onEntered(self, Id, address):
        print("route onEnterd" + Id)
        if Id == "starting":
            self.starting = address
            print("starting : " + address)
        elif Id == "destination":
            self.destination = address
            print("destination : " + address)
            message = self.find_route(self.starting, self.destination, "bikeset")
            if message == -1:
                message = "ERROR"
            self.timeCalculated.emit(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
