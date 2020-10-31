from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium, sys, glob, os, json, requests, io
import pandas as pd
import numpy as np
from Data import apiKeys as key


class DRRLife(QWidget):
    def __init__(self):

        super().__init__()
        self.initUI()
        self.setGeometry(300, 300, 800, 600)

    def initUI(self):

        self.web = QWebEngineView()

        self.address = QLineEdit()
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
        pass


class dr:
    def __init__(self):

        path = "./Data"
        file = glob.glob(os.path.join(path + "*.xlsx"))[0]
        df = pd.read_excel(file, sheet_name="대여소현황")

        dataset = df[["대여소_구", "대여소명", "대여소주소", "위도", "경도", "거치대수"]]

        dr_songpa = dataset[dataset["대여소_구"].str.contains("송파구")]
        dr_songpa.index = range(len(dr_songpa))
        data_size = len(dr_songpa)
        loc = [37.4952, 127.130]

        map_dr = folium.Map(location=loc, zoom_start=12)

        for i in range(data_size):
            folium.Marker(
                list(dr_songpa.iloc[i][["위도", "경도"]]),
                popup=dr_songpa.iloc[i][["대여소주소"]],
                icon=folium.Icon(color="green"),
            ).add_to(map_dr)

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

        for i in range(self.data_size):
            temp = 100000 * np.sqrt(
                np.square(float(self.dr_songpa.iloc[i][["위도"]] - float(now[1])))
                + np.square(float(self.dr_songpa.iloc[i][["경도"]] - float(now[0])))
            )
            if min_ > temp:
                val = i
                min_ = temp
            return self.dr_songpa.iloc[val]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ll = dr()
    m = ll.map_dr
    data = io.BytesIO()
    m.save(data, close_file=False)

    w = DRRLife()
    w.setHtml(data.getvalue().decode())
    w.show()
    sys.exit(app.exec_())
