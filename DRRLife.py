from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium, sys, glob, os, json, requests, io
import pandas as pd
import numpy as np
from Data import apiKeys as key

PATH = "./Data/"


class DRRLife(QWidget):
    def __init__(self):

        super().__init__()
        self.initUI()
        self.setGeometry(300, 300, 800, 600)

    def initUI(self):

        self.instanceMap = Map()
        self.map = self.instanceMap.map_dr_songpa
        self.instanceMap.markStation()

        map_html = io.BytesIO()
        self.map.save(map_html, close_file=False)

        self.web = QWebEngineView()
        self.web.setHtml(map_html.getvalue().decode())

        self.address = QLineEdit()
        self.address.setText("경찰병원역")
        self.address.returnPressed.connect(self.enterPressed)

        lbl1 = QLabel("주소", self)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl1)
        hbox.addWidget(self.address)

        vbox = QVBoxLayout()
        vbox.addWidget(self.web)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def enterPressed(self):
        # 가까운 정거장의 데이터를 구한다.
        closest = self.instanceMap.find_closest(self.address.text())
        print(closest.loc["대여소명"])
        # map에 Marker을 표시한다
        try:
            folium.Marker(
                ((closest.loc["위도"], closest.loc["경도"])),
                popup=closest.loc["대여소주소"],
                icon=folium.Icon(color="red"),
            ).add_to(self.map)
        except Exception as e:
            print("error")
            # pyqt내에서 folium을 새로고침 하는 방법 ( 내일 할 일)

        # 기존에 Marker가 있을 시, 그 마커를 제거한다.
        # 마커가 표시된 곳으로 Zoom-in한다.
        pass

    def refreshWeb(self):
        pass


class Map:
    src = glob.glob(os.path.join(PATH + "*.xlsx"))[0]
    data = pd.read_excel(src, sheet_name="대여소현황")

    dataset = data[["대여소_구", "대여소명", "대여소주소", "위도", "경도", "거치대수"]]

    src_songpa = dataset[dataset["대여소_구"].str.contains("송파구")]
    src_songpa.index = range(len(src_songpa))
    src_data_size = len(src_songpa)
    loc = [37.4952, 127.130]  # 송파구 기본좌표
    map_dr_songpa = folium.Map(location=loc, zoom_start=14)

    def __init__(self):
        pass

    def markStation(self):
        for i in range(self.src_data_size):
            folium.Marker(
                list(self.src_songpa.iloc[i][["위도", "경도"]]),
                popup=self.src_songpa.iloc[i][["대여소주소"]],
                icon=folium.Icon(color="green"),
            ).add_to(self.map_dr_songpa)

    # return list of location
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

        for i in range(Map.src_data_size):
            temp = 100000 * np.sqrt(
                np.square(float(self.src_songpa.iloc[i][["위도"]] - float(now[1])))
                + np.square(float(self.src_songpa.iloc[i][["경도"]] - float(now[0])))
            )
            if min_ > temp:
                val = i
                min_ = temp
            return self.src_songpa.iloc[val]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DRRLife()
    w.show()
    sys.exit(app.exec_())
