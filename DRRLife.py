from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
from PyQt5.QtWidgets import *
import folium
import sys, glob, os, json, requests, io, time
import numpy as np
import pandas as pd
from Data import apiKeys as key

PATH = "./Data/"


class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setGeometry(300, 300, 800, 600)

    def initUI(self):
        self.message = lineEdit()
        self.engine = webEngine()
        self.map = Map()

        self.message.returnPressed.connect(self.message.onEntered)
        self.message.sendText.connect(self.map.onGaved)
        self.map.mapChanged.connect(self.engine.changed)

        self.engine.setHtml(self.map.map_html.getvalue().decode())

        vbox = QVBoxLayout()
        vbox.addWidget(self.engine)
        vbox.addWidget(self.message)

        self.setLayout(vbox)


class webEngine(QWebEngineView):
    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def changed(self):
        print("changed")
        url = QUrl.fromLocalFile("/Users/sseungmn/Documents/workspace/ws1/map.html")
        if url.isValid():
            self.load(url)
        else:
            print("Invalid")


class lineEdit(QLineEdit):
    sendText = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def onEntered(self):
        print("onEntered")
        _txt = self.text()
        self.setText("")
        self.sendText.emit(_txt)


class Map(QObject):
    mapChanged = pyqtSignal()

    __src = glob.glob(os.path.join(PATH + "*.xlsx"))[0]
    __data = pd.read_excel(__src, sheet_name="대여소현황")
    __dataset = __data[["대여소_구", "대여소명", "대여소주소", "위도", "경도", "거치대수"]]

    __src_songpa = __dataset[__dataset["대여소_구"].str.contains("송파구")]
    __src_songpa.index = range(len(__src_songpa))
    __src_data_size = len(__src_songpa)

    __loc = [37.4952, 127.130]

    def __init__(self):
        super().__init__()
        self.map_dr_songpa = folium.Map(location=self.__loc, zoom_start=14)
        self.feature_group = folium.FeatureGroup(name="Markers")
        self.map_html = io.BytesIO()
        self.mark_buffer = []

        for i in range(self.__src_data_size):
            folium.Marker(
                list(self.__src_songpa.iloc[i][["위도", "경도"]]),
                popup=self.__src_songpa.iloc[i][["대여소주소"]],
                icon=folium.Icon(color="green"),
            ).add_to(self.feature_group)
        self.feature_group.add_to(self.map_dr_songpa)

        self.map_dr_songpa.save(self.map_html, close_file=False)

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

        for i in range(self.__src_data_size):
            temp = 100000 * np.sqrt(
                np.square(float(self.__src_songpa.iloc[i][["위도"]] - float(now[1])))
                + np.square(float(self.__src_songpa.iloc[i][["경도"]] - float(now[0])))
            )
            if min_ > temp:
                val = i
                min_ = temp
        return self.__src_songpa.iloc[val]

    def mark_closest_staion(self, text):
        if len(self.mark_buffer) == 0:
            pass
        else:
            prev = self.mark_buffer.pop(0)
            folium.Marker(
                list(prev.loc[["위도", "경도"]]),
                popup=prev.loc[["대여소주소"]],
                icon=folium.Icon(color="green"),
            ).add_to(self.feature_group)

        current = self.find_closest(text)
        self.mark_buffer.append(current)
        folium.Marker(
            list(current.loc[["위도", "경도"]]),
            popup=current.loc[["대여소주소"]],
            icon=folium.Icon(color="red"),
        ).add_to(self.feature_group)

        self.feature_group.add_to(self.map_dr_songpa)

    @pyqtSlot(str)
    def onGaved(self, text):
        print("textGaved")
        carrier = []
        self.mark_closest_staion(text)
        # self.map_dr_songpa.save(self.map_html, close_file=False)
        self.map_dr_songpa.save("map.html", close_file=False)
        # carrier.append(self.map_html)
        self.mapChanged.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
