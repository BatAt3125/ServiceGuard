# ServiceGuardPro - a utility for monitoring and managing Windows services
# Copyright (C) 2026 Timur
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys
import subprocess
import random
import ctypes
import json
from PyQt6 import sip
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, 
                             QLabel, QGraphicsDropShadowEffect, QTextEdit, QFrame,
                             QListWidgetItem, QDialog, QAbstractItemView, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF, QPropertyAnimation, QRect, QEasingCurve, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QIcon
import winreg
CRITICAL_SERVICES = (
    "RpcSs", "DcomLaunch", "LSM", "SamSs", "PlugPlay", 
    "Power", "EventLog", "RpcEptMapper", "Appinfo", 
    "CoreMessagingRegistrar", "KeyIso", "NlaSvc","CryptSvc","wuauserv","Schedule", "ProfSvc",
    "WSearch","SysMain", "bits"
)
def set_autostart(enabled=True):
    path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    name = "ServiceGuardPro"
    exe_path = f'"{sys.executable}"' # Путь к вашему exe
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, exe_path)
        else:
            try: winreg.DeleteValue(key, name)
            except: pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Ошибка реестра: {e}")
class MainBtn(QPushButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab = parent
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("background: transparent; border: none;") # Важно для центрирования

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Центр виджета кнопки
        cx = self.width() / 2
        cy = self.height() / 2

        # 1. Рисуем белое тело кнопки
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(QPointF(cx, cy), 75, 75) # Радиус 75 (диаметр 150)

        # 2. Определяем цвет шестерёнки
        if self.tab.is_err:
            gear_color = QColor(231, 76, 60)
        elif self.tab.is_running:
            gear_color = QColor(46, 204, 113)
        else:
            gear_color = QColor(189, 195, 199)

        # 3. Рисуем шестерёнку точно в центре cx, cy
        p.save()
        p.translate(cx, cy)
        
        p.setBrush(gear_color)
        for _ in range(8):
            p.drawRect(-12, -42, 24, 84) # Зубцы
            p.rotate(45)

        p.drawEllipse(QPointF(0, 0), 30, 30) # Тело
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QPointF(0, 0), 12, 12) # Дырка
        p.restore()
class LanguageItemWidget(QWidget):
    selected = pyqtSignal(str)
    def __init__(self, lang_name, is_active, btn_text="Select", parent=None):
        # Исправлено: передаем только parent в super().__init__
        super().__init__(parent) 
        layout = QHBoxLayout(self)
        self.lang_name = lang_name
        
        label = QLabel(lang_name)
        label.setStyleSheet(f"border: none; background: transparent; font-size: 13px; "
                            f"color: {'#007AFF' if is_active else '#333'}; "
                            f"font-weight: {'bold' if is_active else 'normal'};")
        
        # Используем переданный текст кнопки
        display_text = "✓" if is_active else btn_text
        self.apply_btn = QPushButton(display_text)
        self.apply_btn.setFixedSize(80, 30)
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {'#007AFF' if is_active else '#f2f2f2'}; 
                color: {'white' if is_active else '#666'}; 
                border: none; 
                border-radius: 15px; 
            }}
            QPushButton:hover {{ background-color: {'#0056b3' if is_active else '#e0e0e0'}; }}
        """)
        self.apply_btn.clicked.connect(lambda: self.selected.emit(self.lang_name))
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self.apply_btn)
        layout.setContentsMargins(15, 5, 10, 5)
LANGUAGES = {
    "Абаза бызшва": {
        "services": "СЛУЖБАКВА", "lang_tab": "БЫЖВКВА",
        "settings_tab": "НАСТРОЙКАКВА", "sett_app_auto": "Программа автоматла йагIайсра",
        "sett_srv_auto": "Службаква автоматла йарагIайсра",
        "main": "ПРОГРАММА", "start": "ргIайсра...", "stop": "ргIаншара...", 
        "running": "запущена", "stopped": "остановлена", "error": "гъалатI", 
        "add_btn": "+ Служба ацIара", "toast_no_srv": "ЙацIацI службаква", 
        "see_err": "ГЪАЛАТI АБАРА", "add_dialog_title": "Службаква ргIашара",
        "search_placeholder": "Служба йахь йагIахIва...", "search_label": "РгIашара:",
        "add_selected_btn": "Йалхху ацIара", "select_btn": "Йалых"
    },
    "Аԥсшәа": {
        "services": "АМАҴЗУРАҚӘА", "lang_tab": "АБЫЗШӘАҚӘА",
        "settings_tab": "АПАРЕМЕТРҚӘА", "sett_app_auto": "Автоматикла ахылаԥшра",
        "sett_srv_auto": "Амаҵзурақәа автоматикла рактивациа",
        "main": "ИХАДОУ", "start": "аус аура...", "stop": "аанкылара...", 
        "running": "аус ауеит", "stopped": "аанкылоуп", "error": "агха", 
        "add_btn": "+ Амаҵзура ацҵара", "toast_no_srv": "Иацҵатәуп амаҵзурақәа", 
        "see_err": "АГХА АБАРА", "add_dialog_title": "Амаҵзурақәа рыԥшаара",
        "search_placeholder": "Амаҵзура ахьӡ...", "search_label": "Аԥшаара:",
        "add_selected_btn": "Иалыху ацҵара", "select_btn": "Иалыхтәуп"
    },
    "Azərbaycanca": {
        "services": "XİDMƏTLƏR", "lang_tab": "DİLLƏR",
        "settings_tab": "PARİMETRLƏR", "sett_app_auto": "Tətbiqi avtomatik başlat",
        "sett_srv_auto": "Xidmətləri avtomatik başlat",
        "main": "ƏSAS", "start": "başladılır...", "stop": "dayandırılır...", 
        "running": "işləyir", "stopped": "dayandırıldı", "error": "xəta", 
        "add_btn": "+ Xidmət əlavə et", "toast_no_srv": "Xidmətləri əlavə edin", 
        "see_err": "XƏTANI GÖR", "add_dialog_title": "Xidmətləri axtar və əlavə et",
        "search_placeholder": "Xidmət adını daxil edin...", "search_label": "Axtar:",
        "add_selected_btn": "Seçilmişləri əlavə et", "select_btn": "Seç"
    },
    "Shqip": {
        "services": "SHËRBIMET", "lang_tab": "GJUHËT",
        "settings_tab": "CILËSIMET", "sett_app_auto": "Nis aplikacionin automatikisht",
        "sett_srv_auto": "Nis shërbimet automatikisht",
        "main": "KRYESORE", "start": "duke nisur...", "stop": "duke ndaluar...", 
        "running": "në punë", "stopped": "ndaluar", "error": "gabim", 
        "add_btn": "+ Shto Shërbim", "toast_no_srv": "Shtoni shërbime për të nisur", 
        "see_err": "SHIH GABIMIN", "add_dialog_title": "Kërko dhe Shto Shërbime",
        "search_placeholder": "Shkruani emrin e shërbimit...", "search_label": "Kërko:",
        "add_selected_btn": "Shto të përzgjedhurat", "select_btn": "Zgjidh"
    },
    "አማርኛ": {
        "services": "አገልግሎቶች", "lang_tab": "ቋንቋዎች",
        "settings_tab": "ቅንብሮች", "sett_app_auto": "መተግበሪያውን በራስ-ሰር ያስጀምሩ",
        "sett_srv_auto": "አገልግሎቶችን በራስ-ሰር ያስጀምሩ",
        "main": "ዋና", "start": "በመጀመር ላይ...", "stop": "በመቆም ላይ...", 
        "running": "እየሰራ ነው", "stopped": "ቆሟል", "error": "ስህተት", 
        "add_btn": "+ አገልግሎት ይጨምሩ", "toast_no_srv": "ለመጀመር አገልግሎቶችን ይጨምሩ", 
        "see_err": "ስህተትን ይመልከቱ", "add_dialog_title": "አገልግሎቶችን ይፈልጉ እና ይጨምሩ",
        "search_placeholder": "የአገልግሎት ስም ያስገቡ...", "search_label": "ፈልግ:",
        "add_selected_btn": "የተመረጡትን ጨምር", "select_btn": "ይምረጡ"
    },
    "English": {
        "services": "SERVICES", "lang_tab": "LANGUAGES",
        "settings_tab": "SETTINGS", "sett_app_auto": "Launch app automatically",
        "sett_srv_auto": "Start services automatically",
        "main": "MAIN", "start": "starting...", "stop": "stopping...", 
        "running": "running", "stopped": "stopped", "error": "error", 
        "add_btn": "+ Add Service", "toast_no_srv": "Add services to start", 
        "see_err": "SEE ERROR", "add_dialog_title": "Search and Add Services",
        "search_placeholder": "Enter service name...", "search_label": "Search:",
        "add_selected_btn": "Add Selected", "select_btn": "Select"
    },
    "العربية": {
        "services": "الخدمات", "lang_tab": "اللغات",
        "settings_tab": "الإعدادات", "sett_app_auto": "تشغيل التطبيق تلقائيًا",
        "sett_srv_auto": "بدء الخدمات تلقائيًا",
        "main": "الرئيسية", "start": "جاري البدء...", "stop": "جاري الإيقاف...", 
        "running": "يعمل", "stopped": "متوقف", "error": "خطأ", 
        "add_btn": "+ إضافة خدمة", "toast_no_srv": "أضف خدمات للبدء", 
        "see_err": "عرض الخطأ", "add_dialog_title": "البحث وإضافة الخدمات",
        "search_placeholder": "أدخل اسم الخدمة...", "search_label": "بحث:",
        "add_selected_btn": "إضافة المحدد", "select_btn": "اختر"
    },
    "Հայերեն": {
        "services": "ԾԱՌԱՅՈՒԹՅՈՒՆՆԵՐ", "lang_tab": "ԼԵԶՈՒՆԵՐ",
        "settings_tab": "ԿԱՐԳԱՎՈՐՈՒՄՆԵՐ", "sett_app_auto": "Գործարկել հավելվածը ավտոմատ",
        "sett_srv_auto": "Մեկնարկել ծառայությունները ավտոմատ",
        "main": "ԳԼԽԱՎՈՐ", "start": "մեկնարկ...", "stop": "դադարեցում...", 
        "running": "աշխատում է", "stopped": "կանգնեցված է", "error": "սխալ", 
        "add_btn": "+ Ավելացնել ծառայություն", "toast_no_srv": "Ավելացրեք ծառայություններ", 
        "see_err": "ՏԵՍՆԵԼ ՍԽԱԼԸ", "add_dialog_title": "Փնտրել և ավելացնել ծառայություններ",
        "search_placeholder": "Մուտքագրեք անունը...", "search_label": "Փնտրել:",
        "add_selected_btn": "Ավելացնել նշվածները", "select_btn": "Ընտրել"
    },
    "Afrikaans": {
        "services": "DIENSTE", "lang_tab": "TALE",
        "settings_tab": "INSTELLINGS", "sett_app_auto": "Begin toepassing outomaties",
        "sett_srv_auto": "Begin dienste outomaties",
        "main": "HOOF", "start": "begin...", "stop": "stop...", 
        "running": "loop", "stopped": "gestop", "error": "fout", 
        "add_btn": "+ Voeg Diens by", "toast_no_srv": "Voeg dienste by om te begin", 
        "see_err": "SIEN FOUT", "add_dialog_title": "Soek en Voeg Dienste by",
        "search_placeholder": "Tik diensnaam...", "search_label": "Soek:",
        "add_selected_btn": "Voeg Geselekteerde by", "select_btn": "Kies"
    },
    "Euskara": {
        "services": "ZERBITZUAK", "lang_tab": "HIZKUNTZAK",
        "settings_tab": "EZARPENAK", "sett_app_auto": "Abiarazi aplikazioa automatikoki",
        "sett_srv_auto": "Abiarazi zerbitzuak automatikoki",
        "main": "NAGUSIA", "start": "abiarazten...", "stop": "gelditzen...", 
        "running": "martxan", "stopped": "geldituta", "error": "errorea", 
        "add_btn": "+ Gehitu Zerbitzua", "toast_no_srv": "Gehitu zerbitzuak hasteko", 
        "see_err": "IKUSI ERROREA", "add_dialog_title": "Bilatu eta Gehitu Zerbitzuak",
        "search_placeholder": "Idatzi zerbitzuaren izena...", "search_label": "Bilatu:",
        "add_selected_btn": "Gehitu hautatutakoak", "select_btn": "Hautatu"
    },
    "Башҡортса": {
        "services": "ХЕҘМӘТТӘР", "lang_tab": "ТИЛДӘР",
        "settings_tab": "КӨՅЛӘҮҘӘР", "sett_app_auto": "Программаны автомат ебәреү",
        "sett_srv_auto": "Хеҙмәттәрҙе автомат ебәреү",
        "main": "ТӨП", "start": "ебәрелә...", "stop": "туҡтатыла...", 
        "running": "эшләй", "stopped": "туҡтатылды", "error": "хата", 
        "add_btn": "+ Хеҙмәт өҫтәү", "toast_no_srv": "Ебәреү өсөн хеҙмәттәр өҫтәгеҙ", 
        "see_err": "ХАТАНЫ КҮРЕҮ", "add_dialog_title": "Хеҙмәттәр эҙләү һәм өҫтәү",
        "search_placeholder": "Хеҙмәт исемен яҙығыҙ...", "search_label": "Эҙләү:",
        "add_selected_btn": "Һайланғандарҙы өҫтәү", "select_btn": "Һайларға"
    },
    "Беларуская": {
        "services": "СЛУЖБЫ", "lang_tab": "МОВЫ",
        "settings_tab": "НАЛАДКИ", "sett_app_auto": "Запускаць прыкладанне аўтаматычна",
        "sett_srv_auto": "Запускаць службы аўтаматычна",
        "main": "ГАЛОЎНАЯ", "start": "запуск...", "stop": "прыпынак...", 
        "running": "працуе", "stopped": "спынена", "error": "памылка", 
        "add_btn": "+ Дадаць службу", "toast_no_srv": "Дадайце службы для запуску", 
        "see_err": "ГЛЯДЗЕЦЬ ПАМЫЛКУ", "add_dialog_title": "Пошук і даданне службаў",
        "search_placeholder": "Увядзіце назву службы...", "search_label": "Пошук:",
        "add_selected_btn": "Дадаць выбраныя", "select_btn": "Выбраць"
    },
    "বাংলা": {
        "services": "পরিষেবা", "lang_tab": "ভাষা",
        "settings_tab": "সেটিংস", "sett_app_auto": "অ্যাপটি স্বয়ংক্রিয়ভাবে চালু করুন",
        "sett_srv_auto": "পরিষেবাগুলি স্বয়ংক্রিয়ভাবে শুরু করুন",
        "main": "প্রধান", "start": "শুরু হচ্ছে...", "stop": "বন্ধ হচ্ছে...", 
        "running": "চলছে", "stopped": "বন্ধ", "error": "ত্রুটি", 
        "add_btn": "+ পরিষেবা যোগ করুন", "toast_no_srv": "শুরু করতে পরিষেবা যোগ করুন", 
        "see_err": "ত্রুটি দেখুন", "add_dialog_title": "পরিষেবা খুঁজুন এবং যোগ করুন",
        "search_placeholder": "পরিষেবার নাম লিখুন...", "search_label": "অনুসন্ধান:",
        "add_selected_btn": "নির্বাচিত যোগ করুন", "select_btn": "নির্বাচন"
    },
    "မြန်မာဘာသာ": {
        "services": "ဝန်ဆောင်မှုများ", "lang_tab": "ဘာသာစကားများ",
        "settings_tab": "ဆက်တင်များ", "sett_app_auto": "အက်ပ်ကို အလိုအလျောက်ဖွင့်ရန်",
        "sett_srv_auto": "ဝန်ဆောင်မှုများကို အလိုအလျောက်စတင်ရန်",
        "main": "ပင်မ", "start": "စတင်နေသည်...", "stop": "ရပ်တန့်နေသည်...", 
        "running": "လည်ပတ်နေသည်", "stopped": "ရပ်တန့်သွားသည်", "error": "အမှား", 
        "add_btn": "+ ဝန်ဆောင်မှုထည့်ရန်", "toast_no_srv": "စတင်ရန် ဝန်ဆောင်မှုများထည့်ပါ", 
        "see_err": "အမှားကြည့်ရန်", "add_dialog_title": "ဝန်ဆောင်မှုများ ရှာဖွေထည့်သွင်းရန်",
        "search_placeholder": "အမည်ရိုက်ထည့်ပါ...", "search_label": "ရှာဖွေရန်:",
        "add_selected_btn": "ရွေးချယ်ထားသည်များထည့်ရန်", "select_btn": "ရွေးချယ်ပါ"
    },
    "Български": {
        "services": "УСЛУГИ", "lang_tab": "ЕЗИЦИ",
        "settings_tab": "НАСТРОЙКИ", "sett_app_auto": "Стартирай приложението автоматично",
        "sett_srv_auto": "Стартирай услугите автоматично",
        "main": "НАЧАЛО", "start": "стартиране...", "stop": "спиране...", 
        "running": "работи", "stopped": "спряно", "error": "грешка", 
        "add_btn": "+ Добави услуга", "toast_no_srv": "Добавете услуги за старт", 
        "see_err": "ВИЖ ГРЕШКАТА", "add_dialog_title": "Търсене и добавяне на услуги",
        "search_placeholder": "Въведете име на услуга...", "search_label": "Търсене:",
        "add_selected_btn": "Добави избраните", "select_btn": "Избери"
    },
    "Bosanski": {
        "services": "USLUGE", "lang_tab": "JEZICI",
        "settings_tab": "POSTAVKE", "sett_app_auto": "Pokreni aplikaciju automatski",
        "sett_srv_auto": "Pokreni usluge automatski",
        "main": "GLAVNO", "start": "pokretanje...", "stop": "zaustavljanje...", 
        "running": "radi", "stopped": "zaustavljeno", "error": "greška", 
        "add_btn": "+ Dodaj uslugu", "toast_no_srv": "Dodajte usluge za početak", 
        "see_err": "POGLEDAJ GREŠKU", "add_dialog_title": "Pretraži i dodaj usluge",
        "search_placeholder": "Unesite naziv usluge...", "search_label": "Traži:",
        "add_selected_btn": "Dodaj označeno", "select_btn": "Odaberi"
    },
    "Буряад хэлэн": {
        "services": "АЛБАУД", "lang_tab": "ХЭЛЭНҮҮД",
        "settings_tab": "ТОХИРООНУУД", "sett_app_auto": "Программа өөрөө ажаллаха",
        "sett_srv_auto": "Албаудые өөрөө залгаха",
        "main": "ГОЛ", "start": "залгагдажа байна...", "stop": "гэрэглэгдэжэ байна...", 
        "running": "ажаллана", "stopped": "гэрэглэгдээ", "error": "алдуу", 
        "add_btn": "+ Алба нэмэхэ", "toast_no_srv": "Залгахын тулада албануудые нэмэгты", 
        "see_err": "АЛДУУГЫЕ ХАРАХА", "add_dialog_title": "Албануудые бэдэрхэ ба нэмэхэ",
        "search_placeholder": "Албанай нэрэ...", "search_label": "Бэдэрэлгэ:",
        "add_selected_btn": "Шэлэгдэһэниие нэмэхэ", "select_btn": "Шэлэхэ"
    },
    "Cymraeg": {
        "services": "GWASANAETHAU", "lang_tab": "IEITHOEDD",
        "settings_tab": "GOSODIADAU", "sett_app_auto": "Lansio'r ap yn awtomatig",
        "sett_srv_auto": "Dechrau gwasanaethau'n awtomatig",
        "main": "PRIF", "start": "cychwyn...", "stop": "ataliad...", 
        "running": "yn rhedeg", "stopped": "wedi stopio", "error": "gwall", 
        "add_btn": "+ Ychwanegu Gwasanaeth", "toast_no_srv": "Ychwanegwch wasanaethau i ddechrau", 
        "see_err": "GWELD GWALL", "add_dialog_title": "Chwilio ac Ychwanegu Gwasanaethau",
        "search_placeholder": "Rhowch enw'r gwasanaeth...", "search_label": "Chwilio:",
        "add_selected_btn": "Ychwanegu Dewis", "select_btn": "Dewis"
    },
    "Magyar": {
        "services": "SZOLGÁLTATÁSOK", "lang_tab": "NYELVEK",
        "settings_tab": "BEÁLLÍTÁSOK", "sett_app_auto": "Alkalmazás automatikus indítása",
        "sett_srv_auto": "Szolgáltatások automatikus indítása",
        "main": "FŐOLDAL", "start": "indítás...", "stop": "leállítás...", 
        "running": "fut", "stopped": "leállítva", "error": "hiba", 
        "add_btn": "+ Szolgáltatás hozzáadása", "toast_no_srv": "Adjon hozzá szolgáltatást az indításhoz", 
        "see_err": "HIBA MEGTEKINTÉSE", "add_dialog_title": "Szolgáltatások keresése és hozzáadása",
        "search_placeholder": "Szolgáltatás neve...", "search_label": "Keresés:",
        "add_selected_btn": "Kiválasztottak hozzáadása", "select_btn": "Kiválaszt"
    },
    "Tiếng Việt": {
        "services": "DỊCH VỤ", "lang_tab": "NGÔN NGỮ",
        "settings_tab": "CÀI ĐẶT", "sett_app_auto": "Tự động chạy ứng dụng",
        "sett_srv_auto": "Tự động bắt đầu dịch vụ",
        "main": "CHÍNH", "start": "đang chạy...", "stop": "đang dừng...", 
        "running": "đang hoạt động", "stopped": "đã dừng", "error": "lỗi", 
        "add_btn": "+ Thêm dịch vụ", "toast_no_srv": "Thêm dịch vụ để bắt đầu", 
        "see_err": "XEM LỖI", "add_dialog_title": "Tìm kiếm và Thêm dịch vụ",
        "search_placeholder": "Nhập tên dịch vụ...", "search_label": "Tìm kiếm:",
        "add_selected_btn": "Thêm mục đã chọn", "select_btn": "Chọn"
    },
    "Kreyòl Ayisyen": {
        "services": "SÈVIS", "lang_tab": "LANG",
        "settings_tab": "PARAMÈT", "sett_app_auto": "Lanse aplikasyon an otomatikman",
        "sett_srv_auto": "Kòmanse sèvis yo otomatikman",
        "main": "PRENSIPAL", "start": "ap kòmanse...", "stop": "ap kanpe...", 
        "running": "ap mache", "stopped": "kanpe", "error": "erè", 
        "add_btn": "+ Ajoute Sèvis", "toast_no_srv": "Ajoute sèvis pou kòmanse", 
        "see_err": "GADE ERÈ", "add_dialog_title": "Chèche epi Ajoute Sèvis",
        "search_placeholder": "Antre non sèvis la...", "search_label": "Chèche:",
        "add_selected_btn": "Ajoute sa yo chwazi", "select_btn": "Chwazi"
    },
    "Galego": {
        "services": "SERVIZOS", "lang_tab": "LINGUAS",
        "settings_tab": "AXUSTES", "sett_app_auto": "Iniciar aplicación automaticamente",
        "sett_srv_auto": "Iniciar servizos automaticamente",
        "main": "PRINCIPAL", "start": "iniciando...", "stop": "detendo...", 
        "running": "en execución", "stopped": "detido", "error": "erro", 
        "add_btn": "+ Engadir servizo", "toast_no_srv": "Engade servizos para iniciar", 
        "see_err": "VER ERRO", "add_dialog_title": "Buscar e engadir servizos",
        "search_placeholder": "Nome do servizo...", "search_label": "Buscar:",
        "add_selected_btn": "Engadir seleccionados", "select_btn": "Seleccionar"
    },
    "Għalatar": {
        "services": "SERVIZZI", "lang_tab": "LINGWI",
        "settings_tab": "SETTINGS", "sett_app_auto": "Ibda l-app awtomatikament",
        "sett_srv_auto": "Ibda s-servizzi awtomatikament",
        "main": "MAIN", "start": "tiela'...", "stop": "waqfien...", 
        "running": "miexi", "stopped": "waqaf", "error": "żball", 
        "add_btn": "+ Żid Servizz", "toast_no_srv": "Żid servizzi biex tibda", 
        "see_err": "ARA L-ŻBALL", "add_dialog_title": "Fittex u Żid Servizzi",
        "search_placeholder": "Ikteb isem is-servizz...", "search_label": "Fittex:",
        "add_selected_btn": "Żid dawk magħżula", "select_btn": "Agħżel"
    },
    "Кырык мары": {
        "services": "СЛУЖБЫВЛÄ", "lang_tab": "ЙӸЛМӸВЛÄ",
        "settings_tab": "НАСТРОЙКЫВЛÄ", "sett_app_auto": "Программым автоматла колташ",
        "sett_srv_auto": "Службывлäм автоматла колташ",
        "main": "ТӸНГ", "start": "колташ...", "stop": "чараш...", 
        "running": "ажалыт", "stopped": "чарымы", "error": "йынгылыш", 
        "add_btn": "+ Службым пашаш колташ", "toast_no_srv": "Службывлäм ушыда", 
        "see_err": "ЙӸНГЫЛЫШЫМ АНЖАШ", "add_dialog_title": "Службывлäм кычалшы дä ушышы",
        "search_placeholder": "Службын лӹмжӹ...", "search_label": "Кычалмаш:",
        "add_selected_btn": "Айырымым ушаш", "select_btn": "Айыраш"
    },
    "Ελληνικά": {
        "services": "ΥΠΗΡΕΣΙΕΣ", "lang_tab": "ΓΛΩΣΣΕΣ",
        "settings_tab": "ΡΥΘΜΙΣΕΙΣ", "sett_app_auto": "Αυτόματη εκκίνηση εφαρμογής",
        "sett_srv_auto": "Αυτόματη εκκίνηση υπηρεσιών",
        "main": "ΚΥΡΙΟ", "start": "εκκίνηση...", "stop": "διακοπή...", 
        "running": "σε λειτουργία", "stopped": "διακόπηκε", "error": "σφάλμα", 
        "add_btn": "+ Προσθήκη Υπηρεσίας", "toast_no_srv": "Προσθέστε υπηρεσίες", 
        "see_err": "ΔΕΙΤΕ ΤΟ ΣΦΑΛΜΑ", "add_dialog_title": "Αναζήτηση και Προσθήκη Υπηρεσιών",
        "search_placeholder": "Όνομα υπηρεσίας...", "search_label": "Αναζήτηση:",
        "add_selected_btn": "Προσθήκη επιλεγμένων", "select_btn": "Επιλογή"
    },
    "ქართული": {
        "services": "სერვისები", "lang_tab": "ენები",
        "settings_tab": "პარამეტრები", "sett_app_auto": "აპლიკაციის ავტომატური გაშვება",
        "sett_srv_auto": "სერვისების ავტომატური გაშვება",
        "main": "მთავარი", "start": "გაშვება...", "stop": "შეჩერება...", 
        "running": "მუშაობს", "stopped": "შეჩერებულია", "error": "შეცდომა", 
        "add_btn": "+ სერვისის დამატება", "toast_no_srv": "დაამატეთ სერვისები", 
        "see_err": "შეცდომის ნახვა", "add_dialog_title": "სერვისების ძებნა და დამატება",
        "search_placeholder": "შეიყვანეთ სახელი...", "search_label": "ძებნა:",
        "add_selected_btn": "არჩეულის დამატება", "select_btn": "არჩევა"
    },
    "ગુજરાતી": {
        "services": "સેવાઓ", "lang_tab": "ભાષાઓ",
        "settings_tab": "સેટિંગ્સ", "sett_app_auto": "એપ્લિકેશન આપમેળે શરૂ કરો",
        "sett_srv_auto": "સેવાઓ આપમેળે શરૂ કરો",
        "main": "મુખ્ય", "start": "શરૂ થઈ રહ્યું છે...", "stop": "અટકી રહ્યું છે...", 
        "running": "ચાલુ છે", "stopped": "અટકી ગયું", "error": "ભૂલ", 
        "add_btn": "+ સેવા ઉમેરો", "toast_no_srv": "શરૂ કરવા માટે સેવાઓ ઉમેરો", 
        "see_err": "ભૂલ જુઓ", "add_dialog_title": "સેવાઓ શોધો અને ઉમેરો",
        "search_placeholder": "સેવાનું નામ લખો...", "search_label": "શોધો:",
        "add_selected_btn": "પસંદ કરેલ ઉમેરો", "select_btn": "પસંદ કરો"
    },
    "Dansk": {
        "services": "TJENESTER", "lang_tab": "SPROG",
        "settings_tab": "INDSTILLINGER", "sett_app_auto": "Start app automatisk",
        "sett_srv_auto": "Start tjenester automatisk",
        "main": "HOVEDMENU", "start": "starter...", "stop": "stopper...", 
        "running": "kører", "stopped": "stoppet", "error": "fejl", 
        "add_btn": "+ Tilføj tjeneste", "toast_no_srv": "Tilføj tjenester for at starte", 
        "see_err": "SE FEJL", "add_dialog_title": "Søg og tilføj tjenester",
        "search_placeholder": "Indtast tjenestenavn...", "search_label": "Søg:",
        "add_selected_btn": "Tilføj valgte", "select_btn": "Vælg"
    },
    "isiZulu": {
        "services": "IZINSIZAKALO", "lang_tab": "IZILIMI",
        "settings_tab": "IZILUNGISELELO", "sett_app_auto": "Qalisa uhlelo lokusebenza ngokuzenzakalelayo",
        "sett_srv_auto": "Qala izinsizakalo ngokuzenzakalelayo",
        "main": "OKUYINHLOKO", "start": "iyaqala...", "stop": "iyamisa...", 
        "running": "iyasebenza", "stopped": "imisiwe", "error": "iphutha", 
        "add_btn": "+ Engeza Insizakalo", "toast_no_srv": "Engeza izinsizakalo ukuze uqale", 
        "see_err": "BUKA IPHUTHA", "add_dialog_title": "Sesha futhi Wengeze Izinsizakalo",
        "search_placeholder": "Faka igama lensizakalo...", "search_label": "Sesha:",
        "add_selected_btn": "Engeza Okukhethiwe", "select_btn": "Khetha"
    },
    "עברית": {
        "services": "שירותים", "lang_tab": "שפות",
        "settings_tab": "הגדרות", "sett_app_auto": "הפעל אפליקציה אוטומטית",
        "sett_srv_auto": "הפעל שירותים אוטומטית",
        "main": "ראשי", "start": "מתחיל...", "stop": "מפסיק...", 
        "running": "פעיל", "stopped": "מופסק", "error": "שגיאה", 
        "add_btn": "+ הוסף שירות", "toast_no_srv": "הוסף שירותים כדי להתחיל", 
        "see_err": "ראה שגיאה", "add_dialog_title": "חפש והוסף שירותים",
        "search_placeholder": "הזן שם שירות...", "search_label": "חיפוש:",
        "add_selected_btn": "הוסף נבחרים", "select_btn": "בחר"
    },
    "ייִדיש": {
        "services": "סערוויסעס", "lang_tab": "שפּראַכן",
        "settings_tab": "סעטינגס", "sett_app_auto": "קאַטער אַפּ אויטאָמאַטיש",
        "sett_srv_auto": "אָנהייב סערוויסעס אויטאָמאַטיש",
        "main": "הויפּט", "start": "סטאַרטינג...", "stop": "סטאָפּפּינג...", 
        "running": "לויפט", "stopped": "אָפּגעשטעלט", "error": "טעות", 
        "add_btn": "+ לייג סערוויስ", "toast_no_srv": "לייג סערוויסעס צו אָנהייբ", 
        "see_err": "זען טעות", "add_dialog_title": "זוכן און לייגן סערוויסעס",
        "search_placeholder": "אַרייַן סערוויס נאָמען...", "search_label": "זוכן:",
        "add_selected_btn": "לייג אויסגעקליבן", "select_btn": "אויסקלייבן"
    },
    "Bahasa Indonesia": {
        "services": "LAYANAN", "lang_tab": "BAHASA",
        "settings_tab": "PENGATURAN", "sett_app_auto": "Luncurkan aplikasi otomatis",
        "sett_srv_auto": "Mulai layanan otomatis",
        "main": "UTAMA", "start": "memulai...", "stop": "menghentikan...", 
        "running": "berjalan", "stopped": "berhenti", "error": "kesalahan", 
        "add_btn": "+ Tambah Layanan", "toast_no_srv": "Tambah layanan untuk memulai", 
        "see_err": "LIHAT KESALAHAN", "add_dialog_title": "Cari dan Tambah Layanan",
        "search_placeholder": "Masukkan nama layanan...", "search_label": "Cari:",
        "add_selected_btn": "Tambah yang Dipilih", "select_btn": "Pilih"
    },
    "Gaeilge": {
        "services": "SEIRBHÍSÍ", "lang_tab": "TEANGACHA",
        "settings_tab": "SOCRUITHE", "sett_app_auto": "Seol an aip go huathoibríoch",
        "sett_srv_auto": "Tosaigh seirbhísí go huathoibríoch",
        "main": "PRÍOMH", "start": "ag tosú...", "stop": "ag stopadh...", 
        "running": "ag rith", "stopped": "stoppáilte", "error": "earráid", 
        "add_btn": "+ Cuir Seirbhís Leis", "toast_no_srv": "Cuir seirbhísí leis le tosú", 
        "see_err": "FÉACH EARRÁID", "add_dialog_title": "Cuardaigh agus Cuir Seirbhísí Leis",
        "search_placeholder": "Iontráil ainm na seirbhíse...", "search_label": "Cuardaigh:",
        "add_selected_btn": "Cuir Roghnaithe Leis", "select_btn": "Roghnaigh"
    },
    "Íslenska": {
        "services": "ÞJÓNUSTA", "lang_tab": "TUNGUMÁL",
        "settings_tab": "STILLINGAR", "sett_app_auto": "Ræsa forrit sjálfvirkt",
        "sett_srv_auto": "Ræsa þjónustu sjálfvirkt",
        "main": "AÐALVALMYND", "start": "ræsir...", "stop": "stöðvar...", 
        "running": "í gangi", "stopped": "stöðvað", "error": "villa", 
        "add_btn": "+ Bæta við þjónustu", "toast_no_srv": "Bættu við þjónustu til að ræsa", 
        "see_err": "SKOÐA VILLU", "add_dialog_title": "Leita og bæta við þjónustu",
        "search_placeholder": "Sláðu inn nafn...", "search_label": "Leita:",
        "add_selected_btn": "Bæta við völdum", "select_btn": "Velja"
    },
    "Español": {
        "services": "SERVICIOS", "lang_tab": "IDIOMAS",
        "settings_tab": "AJUSTES", "sett_app_auto": "Iniciar aplicación automáticamente",
        "sett_srv_auto": "Iniciar servicios automáticamente",
        "main": "PRINCIPAL", "start": "iniciando...", "stop": "deteniendo...", 
        "running": "en ejecución", "stopped": "detenido", "error": "error", 
        "add_btn": "+ Añadir Servicio", "toast_no_srv": "Añadir servicios para empezar", 
        "see_err": "VER ERROR", "add_dialog_title": "Buscar y Añadir Servicios",
        "search_placeholder": "Nombre del servicio...", "search_label": "Buscar:",
        "add_selected_btn": "Añadir seleccionados", "select_btn": "Seleccionar"
    },
    "Italiano": {
        "services": "SERVIZI", "lang_tab": "LINGUE",
        "settings_tab": "IMPOSTAZIONI", "sett_app_auto": "Avvia app automaticamente",
        "sett_srv_auto": "Avvia servizi automaticamente",
        "main": "PRINCIPALE", "start": "avvio...", "stop": "arresto...", 
        "running": "in esecuzione", "stopped": "arrestato", "error": "errore", 
        "add_btn": "+ Aggiungi Servizio", "toast_no_srv": "Aggiungi servizi per iniziare", 
        "see_err": "VEDI ERRORE", "add_dialog_title": "Cerca e Aggiungi Servizi",
        "search_placeholder": "Nome del servizio...", "search_label": "Cerca:",
        "add_selected_btn": "Aggiungi selezionati", "select_btn": "Seleziona"
    },
    "Адыгэбзэ": {
        "services": "СЛУЖБЭХЭР", "lang_tab": "БЗЭХЭР",
        "settings_tab": "ПАРЕМЕТРХЭР", "sett_app_auto": "Программэр езыр-езыру къызэIухын",
        "sett_srv_auto": "Службэхэр езыр-езыру къызэIухын",
        "main": "НЭХЪЫЩХЬЭ", "start": "къызэIουхын...", "stop": "гъэувыIэн...", 
        "running": "лажьэ", "stopped": "увыIащ", "error": "щыуагъэ", 
        "add_btn": "+ Службэ хэгъэхъοн", "toast_no_srv": "Службэ зыхэгъэхъуэ", 
        "see_err": "ЩЫУАГЪЭР ПЛЪЭН", "add_dialog_title": "Службэхэр лъыхъуэн икIи хэгъэхъуэн",
        "search_placeholder": "Службэм и цIэр...", "search_label": "Лъыхъуэн:",
        "add_selected_btn": "Хэхар хэгъэхъуэн", "select_btn": "Хэхын"
    },
    "Қазақша": {
        "services": "ҚЫЗМЕТТЕР", "lang_tab": "ТІЛДЕР",
        "settings_tab": "ΠΑΡΑΜΕΤРЛЕР", "sett_app_auto": "Бағдарламаны автоматты қосу",
        "sett_srv_auto": "Қызметтерді автоматты қосу",
        "main": "НЕГІЗГІ", "start": "қосылуда...", "stop": "тоқтатылуда...", 
        "running": "қосулы", "stopped": "тоқтатылды", "error": "қате", 
        "add_btn": "+ Қызмет қосу", "toast_no_srv": "Бастау үшін қызмет қосыңыз", 
        "see_err": "ҚАТЕНІ КӨРУ", "add_dialog_title": "Қызметтерді іздеу және қосу",
        "search_placeholder": "Қызмет атауын енгізіңіз...", "search_label": "Іздеу:",
        "add_selected_btn": "Таңдалғанды қосу", "select_btn": "Таңдау"
    },
    "Qazaqşa": {
        "services": "QYZMETTER", "lang_tab": "TILDER",
        "settings_tab": "PARAMETRLER", "sett_app_auto": "Bağdarlamany avtomatty qosu",
        "sett_srv_auto": "Qyzmetterdi avtomatty qosu",
        "main": "NEGIZGI", "start": "qosyluda...", "stop": "toqtatyluda...", 
        "running": "qosuly", "stopped": "toqtatyldy", "error": "qate", 
        "add_btn": "+ Qyzmet qosu", "toast_no_srv": "Bastau üşin qyzmet qosyñyz", 
        "see_err": "QATENI KÖRÜ", "add_dialog_title": "Qyzmetterdi izdeü jäne qosu",
        "search_placeholder": "Qyzmet ataüyn engiziñiz...", "search_label": "İzdeü:",
        "add_selected_btn": "Tañdalğandy qosu", "select_btn": "Tañdaü"
    },
    "ಕನ್ನಡ": {
        "services": "ಸೇವೆಗಳು", "lang_tab": "ಭಾಷೆಗಳು",
        "settings_tab": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು", "sett_app_auto": "ಅಪ್ಲಿಕೇಶನ್ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪ್ರಾರಂಭಿಸಿ",
        "sett_srv_auto": "ಸೇವೆಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪ್ರಾರಂಭಿಸಿ",
        "main": "ಮುಖ್ಯ", "start": "ಪ್ರಾರಂಭವಾಗುತ್ತಿದೆ...", "stop": "ನಿಲ್ಲಿಸಲಾಗುತ್ತಿದೆ...", 
        "running": "ಚಾಲನೆಯಲ್ಲಿದೆ", "stopped": "ನಿಲ್ಲಿಸಲಾಗಿದೆ", "error": "ದೋಷ", 
        "add_btn": "+ ಸೇವೆಯನ್ನು ಸೇರಿಸಿ", "toast_no_srv": "ಪ್ರಾರಂಭಿಸಲು ಸೇವೆಗಳನ್ನು ಸೇರಿಸಿ", 
        "see_err": "ದೋಷವನ್ನು ನೋಡಿ", "add_dialog_title": "ಸೇವೆಗಳನ್ನು ಹುಡುಕಿ ಮತ್ತು ಸೇರಿಸಿ",
        "search_placeholder": "ಸೇವೆಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ...", "search_label": "ಹುಡುಕಿ:",
        "add_selected_btn": "ಆಯ್ಕೆಮಾಡಿದ ಸೇರಿಸಿ", "select_btn": "ಆರಿಸಿ"
    },
    "Къарачай-Малкъар": {
        "services": "КЪУЛЛУКЪЛА", "lang_tab": "ТИЛЛЕ",
        "settings_tab": "ПАРЕМЕТРЛЕ", "sett_app_auto": "Программаны кеси аллына ий",
        "sett_srv_auto": "Къуллукъланы кеси аллына ий",
        "main": "БАШ", "start": "ийиле турады...", "stop": "тохтай турады...", 
        "running": "ишлейди", "stopped": "тохтады", "error": "халат", 
        "add_btn": "+ Къуллукъ къош", "toast_no_srv": "Ийир ючүн къуллукъла къош", 
        "see_err": "ХАЛАТНЫ КЪАРА", "add_dialog_title": "Къуллукъланы изле эм къош",
        "search_placeholder": "Къуллукъну аты...", "search_label": "Излеу:",
        "add_selected_btn": "Сайланнганны къош", "select_btn": "Сайла"
    },
    "Català": {
        "services": "SERVEIS", "lang_tab": "LLENGÜES",
        "settings_tab": "CONFIGURACIÓ", "sett_app_auto": "Inicia l'aplicació automàticament",
        "sett_srv_auto": "Inicia els serveis automàticament",
        "main": "PRINCIPAL", "start": "iniciant...", "stop": "aturant...", 
        "running": "en execució", "stopped": "aturat", "error": "error", 
        "add_btn": "+ Afegeix Servei", "toast_no_srv": "Afegeix serveis per començar", 
        "see_err": "VEURE ERROR", "add_dialog_title": "Cerca i Afegeix Serveis",
        "search_placeholder": "Nom del servei...", "search_label": "Cerca:",
        "add_selected_btn": "Afegeix seleccionats", "select_btn": "Selecciona"
    },
    "Кыргызча": {
        "services": "КЫЗМАТТАР", "lang_tab": "ТИЛДЕР",
        "settings_tab": "ПАРАМЕТРЛЕР", "sett_app_auto": "Тиркемени автоматтык түрдө иштетүү",
        "sett_srv_auto": "Кызматтарды автоматтык түрдө иштетүү",
        "main": "НЕГИЗГИ", "start": "иштетилүүдө...", "stop": "токтотулууда...", 
        "running": "иштеп жатат", "stopped": "токтотулду", "error": "ката", 
        "add_btn": "+ Кызмат кошуу", "toast_no_srv": "Баштоо үчүн кызмат кошуңуз", 
        "see_err": "КАТАНЫ КӨРҮҮ", "add_dialog_title": "Кызматтарды издөө жана кошуу",
        "search_placeholder": "Кызматтын атын жазыңыз...", "search_label": "Издөө:",
        "add_selected_btn": "Тандалганды кошуу", "select_btn": "Тандоо"
    },
    "中文": {
        "services": "服务", "lang_tab": "语言",
        "settings_tab": "设置", "sett_app_auto": "开机自启动",
        "sett_srv_auto": "自动启动服务",
        "main": "主界面", "start": "启动中...", "stop": "停止中...", 
        "running": "运行中", "stopped": "已停止", "error": "错误", 
        "add_btn": "+ 添加服务", "toast_no_srv": "请先添加服务", 
        "see_err": "查看错误", "add_dialog_title": "搜索并添加服务",
        "search_placeholder": "输入服务名称...", "search_label": "搜索:",
        "add_selected_btn": "添加所选", "select_btn": "选择"
    },
    "Коми": {
        "services": "УДЖТАЯС", "lang_tab": "КЫВЪЯС",
        "settings_tab": "ИНДӨДЪЯС", "sett_app_auto": "Программа ачысьны ачыс",
        "sett_srv_auto": "Уджтаястө заводитны ачыс",
        "main": "МЕДШӨР", "start": "заводитны...", "stop": "дугдывтны...", 
        "running": "уджалө", "stopped": "дугдывтіс", "error": "ошибка", 
        "add_btn": "+ Содтыны уджтас", "toast_no_srv": "Содты уджтас", 
        "see_err": "АДДЗЫНЫ ОШИБКА", "add_dialog_title": "Корсьны да содтыны уджтаястө",
        "search_placeholder": "Уджтаслөн нимыс...", "search_label": "Корсьны:",
        "add_selected_btn": "Содтыны бөрйөмсө", "select_btn": "Бөрйыны"
    },
    "한국어": {
        "services": "서비스", "lang_tab": "언어",
        "settings_tab": "설정", "sett_app_auto": "앱 자동 실행",
        "sett_srv_auto": "서비스 자동 시작",
        "main": "메인", "start": "시작 중...", "stop": "중지 중...", 
        "running": "실행 중", "stopped": "중지됨", "error": "오류", 
        "add_btn": "+ 서비스 추가", "toast_no_srv": "시작할 서비스를 추가하세요", 
        "see_err": "오류 보기", "add_dialog_title": "서비스 검색 및 추가",
        "search_placeholder": "서비스 이름 입력...", "search_label": "검색:",
        "add_selected_btn": "선택 항목 추가", "select_btn": "선택"
    },
    "isiXhosa": {
        "services": "IINKONZO", "lang_tab": "IILWIMI",
        "settings_tab": "IZILUNGISELELO", "sett_app_auto": "Vula i-app ngokuzenzekelayo",
        "sett_srv_auto": "Qala iinkonzo ngokuzenzekelayo",
        "main": "INGUNDOQO", "start": "iyaqalisa...", "stop": "iyamisa...", 
        "running": "iyasebenza", "stopped": "imisiwe", "error": "impazamo", 
        "add_btn": "+ Faka Inkonzo", "toast_no_srv": "Faka iinkonzo ukuze uqalise", 
        "see_err": "BONA IMPAZAMO", "add_dialog_title": "Khangela uze ufake iinkonzo",
        "search_placeholder": "Faka igama lenkonzo...", "search_label": "Khangela:",
        "add_selected_btn": "Faka ezikhethiweyo", "select_btn": "Khetha"
    },
    "ភាសាខ្មែរ": {
        "services": "សេវាកម្ម", "lang_tab": "ភាសា",
        "settings_tab": "ការកំណត់", "sett_app_auto": "បើកកម្មវិធីដោយស្វ័យប្រវត្តិ",
        "sett_srv_auto": "ចាប់ផ្តើមសេវាកម្មដោយស្វ័យប្រវត្តិ",
        "main": "មេ", "start": "កំពុងចាប់ផ្តើម...", "stop": "កំពុងបញ្ឈប់...", 
        "running": "កំពុងដំណើរការ", "stopped": "បានបញ្ឈប់", "error": "កំហុស", 
        "add_btn": "+ បន្ថែមសេវាកម្ម", "toast_no_srv": "បន្ថែមសេវាកម្មដើម្បីចាប់ផ្តើម", 
        "see_err": "មើលកំហុស", "add_dialog_title": "ស្វែងរក និងបន្ថែមសេវាកម្ម",
        "search_placeholder": "បញ្ចូលឈ្មោះសេវាកម្ម...", "search_label": "ស្វែងរក:",
        "add_selected_btn": "បន្ថែមអ្វីដែលបានជ្រើសរើស", "select_btn": "ជ្រើសរើស"
    },
    "ພາສາລາວ": {
        "services": "ບໍລິການ", "lang_tab": "ພາສາ",
        "settings_tab": "ການຕັ້ງຄ່າ", "sett_app_auto": "ເປີດແອັບໂດຍອັດຕະໂນມັດ",
        "sett_srv_auto": "ເລີ່ມບໍລິການໂດຍອັດຕະໂນມັດ",
        "main": "ຫຼັກ", "start": "ກຳລັງເລີ່ມ...", "stop": "ກຳລັງຢຸດ...", 
        "running": "ກຳລັງເຮັດວຽກ", "stopped": "ຢຸດແລ້ວ", "error": "ຂໍ້ຜິດພາດ", 
        "add_btn": "+ ເພີ່ມບໍລິການ", "toast_no_srv": "ເພີ່ມບໍລິການເພື່ອເລີ່ມຕົ້ນ", 
        "see_err": "ເບິ່ງຂໍ້ຜິດພาด", "add_dialog_title": "ຄົ້ນຫາ ແລະ ເພີ່ມບໍລິການ",
        "search_placeholder": "ໃສ່ຊື່ບໍລິການ...", "search_label": "ຄົ້ນຫາ:",
        "add_selected_btn": "ເພີ່ມທີ່ເລືອກ", "select_btn": "ເລືອກ"
    },
    "Latina": {
        "services": "OFFICIA", "lang_tab": "LINGUAE",
        "settings_tab": "CONFIGURATIONES", "sett_app_auto": "Incipit automatice",
        "sett_srv_auto": "Incipit officia automatice",
        "main": "PRINCIPIUM", "start": "incipiens...", "stop": "stans...", 
        "running": "currens", "stopped": "statum", "error": "error", 
        "add_btn": "+ Adde Officium", "toast_no_srv": "Adde officia ut incipias", 
        "see_err": "VIDE ERROREM", "add_dialog_title": "Quaere et Adde Officia",
        "search_placeholder": "Nomen officii...", "search_label": "Quaere:",
        "add_selected_btn": "Adde electa", "select_btn": "Elige"
    },
    "Latviešu": {
        "services": "PAKALPOJUMI", "lang_tab": "VALODAS",
        "settings_tab": "IESTATĪJUMI", "sett_app_auto": "Palaist lietotni automātiski",
        "sett_srv_auto": "Sākt pakalpojumus automātiski",
        "main": "GALVENĀ", "start": "palaiž...", "stop": "aptur...", 
        "running": "darbojas", "stopped": "apturēts", "error": "kļūda", 
        "add_btn": "+ Pievienot pakalpojumu", "toast_no_srv": "Pievienojiet pakalpojumus", 
        "see_err": "SKATĪT KĻŪDU", "add_dialog_title": "Meklēt un pievienot pakalpojumus",
        "search_placeholder": "Ievadiet nosaukumu...", "search_label": "Meklēt:",
        "add_selected_btn": "Pievienot atlasītos", "select_btn": "Atlasīt"
    },
    "Lietuvių": {
        "services": "PASLAUGOS", "lang_tab": "KALBOS",
        "settings_tab": "NUSTATYMAI", "sett_app_auto": "Paleisti programą automatiškai",
        "sett_srv_auto": "Paleisti paslaugas automatiškai",
        "main": "PAGRINDINIS", "start": "paleidžiama...", "stop": "stabdoma...", 
        "running": "veikia", "stopped": "sustabdyta", "error": "klaida", 
        "add_btn": "+ Pridėti paslaugą", "toast_no_srv": "Pridėkite paslaugas", 
        "see_err": "ŽIŪRĖTI KLAIDĄ", "add_dialog_title": "Ieškoti ir pridėti paslaugas",
        "search_placeholder": "Įveskite pavadinimą...", "search_label": "Ieškoti:",
        "add_selected_btn": "Pridėti pasirinktus", "select_btn": "Pasirinkti"
    },
    "Lëtzebuergesch": {
        "services": "SERVICES", "lang_tab": "SPROOCHEN",
        "settings_tab": "ASTELLUNGEN", "sett_app_auto": "App automatesch starten",
        "sett_srv_auto": "Servicer automatesch starten",
        "main": "HAAPTSEIT", "start": "starten...", "stop": "stoppen...", 
        "running": "leeft", "stopped": "gestoppt", "error": "Feeler", 
        "add_btn": "+ Service addéieren", "toast_no_srv": "Addéiert Servicer", 
        "see_err": "FEELER REISEN", "add_dialog_title": "Sichen an addéieren",
        "search_placeholder": "Numm vum Service...", "search_label": "Sichen:",
        "add_selected_btn": "Ausgewielten addéieren", "select_btn": "Wielen"
    },
    "Македонски": {
        "services": "УСЛУГИ", "lang_tab": "ЈАЗИЦИ",
        "settings_tab": "ПОСТАВКИ", "sett_app_auto": "Стартувај автоматски",
        "sett_srv_auto": "Стартувај ги услугите автоматски",
        "main": "ГЛАВНО", "start": "стартува...", "stop": "запира...", 
        "running": "работи", "stopped": "запрено", "error": "грешка", 
        "add_btn": "+ Додај услуга", "toast_no_srv": "Додајте услуги за старт", 
        "see_err": "ВИДИ ГРЕШКА", "add_dialog_title": "Пребарај и додај услуги",
        "search_placeholder": "Внесете име на услуга...", "search_label": "Барај:",
        "add_selected_btn": "Додај ги избраните", "select_btn": "Избери"
    },
    "Malagasy": {
        "services": "SERVISY", "lang_tab": "TENY",
        "settings_tab": "FAMETRAHANA", "sett_app_auto": "Handefa ho azy ny app",
        "sett_srv_auto": "Handefa ho azy ny servisy",
        "main": "LEHIBE", "start": "mandefa...", "stop": "mijano...", 
        "running": "mandeha", "stopped": "mijanona", "error": "diso", 
        "add_btn": "+ Hanampy servisy", "toast_no_srv": "Manampia servisy", 
        "see_err": "HIJERY NY DISO", "add_dialog_title": "Hitady sy hanampy servisy",
        "search_placeholder": "Anaran'ny servisy...", "search_label": "Hikaroka:",
        "add_selected_btn": "Hanampy ny voafidy", "select_btn": "Hifidy"
    },
    "Bahasa Melayu": {
        "services": "PERKHIDMATAN", "lang_tab": "BAHASA",
        "settings_tab": "TETAPAN", "sett_app_auto": "Lancarkan aplikasi automatik",
        "sett_srv_auto": "Mulakan perkhidmatan automatik",
        "main": "UTAMA", "start": "memulakan...", "stop": "memberhentikan...", 
        "running": "berjalan", "stopped": "berhenti", "error": "ralat", 
        "add_btn": "+ Tambah Perkhidmatan", "toast_no_srv": "Tambah perkhidmatan untuk bermula", 
        "see_err": "LIHAT RALAT", "add_dialog_title": "Cari dan Tambah Perkhidmatan",
        "search_placeholder": "Masukkan nama perkhidmatan...", "search_label": "Cari:",
        "add_selected_btn": "Tambah yang dipilih", "select_btn": "Pilih"
    },
    "മലയാളം": {
        "services": "സേവനങ്ങൾ", "lang_tab": "ഭാഷകൾ",
        "settings_tab": "ക്രമീകരണങ്ങൾ", "sett_app_auto": "അപ്ലിക്കേഷൻ സ്വയമേവ ആരംഭിക്കുക",
        "sett_srv_auto": "സേവനങ്ങൾ സ്വയമേവ ആരംഭിക്കുക",
        "main": "പ്രധാനം", "start": "ആരംഭിക്കുന്നു...", "stop": "നിർത്തുന്നു...", 
        "running": "പ്രവർത്തിക്കുന്നു", "stopped": "നിർത്തി", "error": "പിശക്", 
        "add_btn": "+ സേവനം ചേർക്കുക", "toast_no_srv": "ആരംഭിക്കാൻ സേവനങ്ങൾ ചേർക്കുക", 
        "see_err": "പിശക് കാണുക", "add_dialog_title": "സേവനങ്ങൾ തിരയുകയും ചേർക്കുകയും ചെയ്യുക",
        "search_placeholder": "സേവനത്തിന്റെ പേര് നൽകുക...", "search_label": "തിരയുക:",
        "add_selected_btn": "തിരഞ്ഞെടുത്തത് ചേർക്കുക", "select_btn": "തിരഞ്ഞെടുക്കുക"
    },
    "Malti": {
        "services": "SERVIZZI", "lang_tab": "LINGWI",
        "settings_tab": "SETTINGS", "sett_app_auto": "Ibda l-app awtomatikament",
        "sett_srv_auto": "Ibda s-servizzi awtomatikament",
        "main": "EWLENI", "start": "tiela'...", "stop": "niezel...", 
        "running": "jaħdem", "stopped": "waqaf", "error": "żball", 
        "add_btn": "+ Żid Servizz", "toast_no_srv": "Żid servizzi biex tibda", 
        "see_err": "ARA L-ŻBALL", "add_dialog_title": "Fittex u Żid Servizzi",
        "search_placeholder": "Ikteb isem is-servizz...", "search_label": "Fittex:",
        "add_selected_btn": "Żid dawk magħżula", "select_btn": "Agħżel"
    },
    "Маньси": {
        "services": "СЛУЖБАТ", "lang_tab": "ЛАТЫНГТ",
        "settings_tab": "НАСТРОЙКАТ", "sett_app_auto": "Программа ачись колтанкве",
        "sett_srv_auto": "Службат ачись колтанкве",
        "main": "МЕДШӨР", "start": "колты...", "stop": "чары...", 
        "running": "уджалы", "stopped": "чарымы", "error": "ошибка", 
        "add_btn": "+ Служба содтанкве", "toast_no_srv": "Службат содты", 
        "see_err": "ОШИБКА ВАНГКВЕ", "add_dialog_title": "Службат корсанкве",
        "search_placeholder": "Служба нам...", "search_label": "Корсанкве:",
        "add_selected_btn": "Содтанкве", "select_btn": "Айыртанкве"
    },
    "Māori": {
        "services": "RATONGA", "lang_tab": "REO",
        "settings_tab": "TANTUHINGA", "sett_app_auto": "Whakatuwhera aunoa",
        "sett_srv_auto": "Tīmata ratonga aunoa",
        "main": "MATUA", "start": "tīmata...", "stop": "whakamutua...", 
        "running": "e rere ana", "stopped": "kua tū", "error": "hapa", 
        "add_btn": "+ Tāpiri Ratonga", "toast_no_srv": "Tāpirihia he ratonga", 
        "see_err": "TIROhia TE HAPA", "add_dialog_title": "Rapu me te Tāpiri Ratonga",
        "search_placeholder": "Ingoa ratonga...", "search_label": "Rapu:",
        "add_selected_btn": "Tāpiri i tīpakohia", "select_btn": "Tīpako"
    },
    "मराठी": {
        "services": "सेवा", "lang_tab": "भाषा",
        "settings_tab": "सेटिंग्स", "sett_app_auto": "अॅप स्वयंचलितपणे लाँच करा",
        "sett_srv_auto": "सेवा स्वयंचलितपणे सुरू करा",
        "main": "मुख्य", "start": "सुरू होत आहे...", "stop": "थांबत आहे...", 
        "running": "चालू आहे", "stopped": "थांबले", "error": "त्रुटी", 
        "add_btn": "+ सेवा जोडा", "toast_no_srv": "सुरू करण्यासाठी सेवा जोडा", 
        "see_err": "त्रुटी पहा", "add_dialog_title": "सेवा शोधा आणि जोडा",
        "search_placeholder": "सेवेचे नाव प्रविष्ट करा...", "search_label": "शोधा:",
        "add_selected_btn": "निवडलेले जोडा", "select_btn": "निवडा"
    },
    "Марий": {
        "services": "СЛУЖБЫВЛА", "lang_tab": "ЙЫЛМЕВЛА",
        "settings_tab": "НАСТРОЙКЫВЛА", "sett_app_auto": "Программым автоматла колташ",
        "sett_srv_auto": "Службывла колташ автоматла",
        "main": "ТӰҤ", "start": "колташ...", "stop": "чараш...", 
        "running": "пашам ышта", "stopped": "чарныме", "error": "йоҥылыш", 
        "add_btn": "+ Службым ешараш", "toast_no_srv": "Службывла ешарыза", 
        "see_err": "ЙОҤЫЛЫШЫМ АНЖАШ", "add_dialog_title": "Службывла кычалшы да ешарышы",
        "search_placeholder": "Службын лӱмжӧ...", "search_label": "Кычалмаш:",
        "add_selected_btn": "Айырымым ешараш", "select_btn": "Айыраш"
    },
    "Мокшень": {
        "services": "СЛУЖБАТНЕ", "lang_tab": "КЯЛЬНЕ",
        "settings_tab": "НАСТРОЙКАТНЕ", "sett_app_auto": "Программоть автоматла пандамс",
        "sett_srv_auto": "Службатнень автоматла пандамс",
        "main": "ИНЬ ОЦУ", "start": "пандамс...", "stop": "лотксемс...", 
        "running": "пандаф", "stopped": "лотксеф", "error": "аф виде", 
        "add_btn": "+ Служба поладомс", "toast_no_srv": "Поладомс службатне", 
        "see_err": "НЯЕМС АФ ВИДЕТЬ", "add_dialog_title": "Вешемс службатне",
        "search_placeholder": "Службать лемоц...", "search_label": "Вешема:",
        "add_selected_btn": "Поладомс кочкафнень", "select_btn": "Кочкамс"
    },
    "Монгол": {
        "services": "ҮЙЛЧИЛГЭЭ", "lang_tab": "ХЭЛ",
        "settings_tab": "ТОХИРГОО", "sett_app_auto": "Автоматаар эхлүүлэх",
        "sett_srv_auto": "Үйлчилгээг автоматаар эхлүүлэх",
        "main": "ҮНДСЭН", "start": "эхэлж байна...", "stop": "зогсож байна...", 
        "running": "ажиллаж байна", "stopped": "зогссон", "error": "алдаа", 
        "add_btn": "+ Үйлчилгээ нэмэх", "toast_no_srv": "Үйлчилгээ нэмнэ үү", 
        "see_err": "АЛДААГ ХАРАХ", "add_dialog_title": "Үйлчилгээ хайх, нэмэх",
        "search_placeholder": "Нэр оруулна уу...", "search_label": "Хайх:",
        "add_selected_btn": "Сонгосныг нэмэх", "select_btn": "Сонгох"
    },
    "Deutsch": {
        "services": "DIENSTE", "lang_tab": "SPRACHEN",
        "settings_tab": "EINSTELLUNGEN", "sett_app_auto": "App automatisch starten",
        "sett_srv_auto": "Dienste automatisch starten",
        "main": "HAUPTMENÜ", "start": "startet...", "stop": "stoppt...", 
        "running": "läuft", "stopped": "gestoppt", "error": "Fehler", 
        "add_btn": "+ Dienst hinzufügen", "toast_no_srv": "Dienste zum Starten hinzufügen", 
        "see_err": "FEHLER ANZEIGEN", "add_dialog_title": "Dienste suchen & hinzufügen",
        "search_placeholder": "Dienstname eingeben...", "search_label": "Suche:",
        "add_selected_btn": "Auswahl hinzufügen", "select_btn": "Wählen"
    },
    "नेपाली": {
        "services": "सेवाहरू", "lang_tab": "भाषाहरू",
        "settings_tab": "सेटिङहरू", "sett_app_auto": "एप स्वतः सुरु गर्नुहोस्",
        "sett_srv_auto": "सेवाहरू स्वतः सुरु गर्नुहोस्",
        "main": "मुख्य", "start": "सुरु हुँदैछ...", "stop": "रोकिँदैछ...", 
        "running": "चलिरहेको छ", "stopped": "रोकियो", "error": "त्रुटि", 
        "add_btn": "+ सेवा थप्नुहोस्", "toast_no_srv": "सुरु गर्न सेवा थप्नुहोस्", 
        "see_err": "त्रुटि हेर्नुहोस्", "add_dialog_title": "खोज्नुहोस् र सेवा थप्नुहोस्",
        "search_placeholder": "सेवाको नाम लेख्नुहोस्...", "search_label": "खोज्नुहोस्:",
        "add_selected_btn": "छानिएको थप्नुहोस्", "select_btn": "छान्नुहोस्"
    },
    "Nederlands": {
        "services": "DIENSTEN", "lang_tab": "TALEN",
        "settings_tab": "INSTELLINGEN", "sett_app_auto": "App automatisch starten",
        "sett_srv_auto": "Diensten automatisch starten",
        "main": "HOOFDMENU", "start": "starten...", "stop": "stoppen...", 
        "running": "actief", "stopped": "gestopt", "error": "fout", 
        "add_btn": "+ Dienst toevoegen", "toast_no_srv": "Diensten toevoegen", 
        "see_err": "FOUT BEKIJKEN", "add_dialog_title": "Diensten zoeken & toevoegen",
        "search_placeholder": "Voer naam in...", "search_label": "Zoeken:",
        "add_selected_btn": "Geselecteerde toevoegen", "select_btn": "Kies"
    },
    "Ногайша": {
        "services": "СЛУЖБАЛАР", "lang_tab": "ТИЛЛЕР",
        "settings_tab": "ЙЫЙЫЛМАЛАР", "sett_app_auto": "Программады оьзликше косув",
        "sett_srv_auto": "Службаларды оьзликше косув",
        "main": "БАС", "start": "косылувда...", "stop": "токталувда...", 
        "running": "ислейди", "stopped": "токтады", "error": "хата", 
        "add_btn": "+ Служба косув", "toast_no_srv": "Службаларды косынъыз", 
        "see_err": "ХАТАДЫ КОРУЬВ", "add_dialog_title": "Службаларды излевуь эм косув",
        "search_placeholder": "Служба аты...", "search_label": "Излевуь:",
        "add_selected_btn": "Сайланганды косув", "select_btn": "Сайла"
    },
    "Norsk": {
        "services": "TJENESTER", "lang_tab": "SPRÅK",
        "settings_tab": "INNSTILLINGER", "sett_app_auto": "Start app automatisk",
        "sett_srv_auto": "Start tjenester automatisk",
        "main": "HOVEDMENY", "start": "starter...", "stop": "stopper...", 
        "running": "kjører", "stopped": "stoppet", "error": "feil", 
        "add_btn": "+ Legg til tjeneste", "toast_no_srv": "Legg til tjenester", 
        "see_err": "SE FEIL", "add_dialog_title": "Søk og legg til tjenester",
        "search_placeholder": "Skriv tjenestenavn...", "search_label": "Søk:",
        "add_selected_btn": "Legg til valgte", "select_btn": "Velg"
    },
    "Ирон": {
        "services": "ЛÆГГÆДТÆ", "lang_tab": "ÆВЗÆГТÆ",
        "settings_tab": "ÆРВÆРДТÆ", "sett_app_auto": "Автоматлагæй кусын кæнын",
        "sett_srv_auto": "Лæггæдтæ кусын кæнын автоматлагæй",
        "main": "СÆЙРАГ", "start": "кусын кæны...", "stop": "уромы...", 
        "running": "кусы", "stopped": "уромыд", "error": "рæдыд", 
        "add_btn": "+ Лæггæдтæ бафтауын", "toast_no_srv": "Бафтау лæггæдтæ", 
        "see_err": "РÆДЫД ФЕНЫН", "add_dialog_title": "Агурын æмæ бафтауын лæггæдтæ",
        "search_placeholder": "Лæггæдты ном...", "search_label": "Агурын:",
        "add_selected_btn": "Бафтауын равзæрстытæ", "select_btn": "Равзарын"
    },
    "ਪੰਜਾਬੀ": {
        "services": "ਸੇਵਾਵਾਂ", "lang_tab": "ਭਾਸ਼ਾਵਾਂ",
        "settings_tab": "ਸੈਟਿੰਗਾਂ", "sett_app_auto": "ਐਪ ਆਪਣੇ ਆਪ ਲਾਂਚ ਕਰੋ",
        "sett_srv_auto": "ਸੇਵਾਵਾਂ ਆਪਣੇ ਆਪ ਸ਼ੁਰੂ ਕਰੋ",
        "main": "ਮੁੱਖ", "start": "ਸ਼ੁਰੂ ਹੋ ਰਿਹਾ ਹੈ...", "stop": "ਰੁਕ ਰਿਹਾ ਹੈ...", 
        "running": "ਚੱਲ ਰਿਹਾ ਹੈ", "stopped": "ਰੁਕਿਆ", "error": "ਗਲਤੀ", 
        "add_btn": "+ ਸੇਵਾ ਜੋੜੋ", "toast_no_srv": "ਸੇਵਾਵਾਂ ਜੋੜੋ", 
        "see_err": "ਗਲਤੀ ਦੇਖੋ", "add_dialog_title": "ਸੇਵਾਵਾਂ ਖੋਜੋ ਅਤੇ ਜੋੜੋ",
        "search_placeholder": "ਸੇਵਾ ਦਾ ਨਾਮ ਲਿਖੋ...", "search_label": "ਖੋਜ:",
        "add_selected_btn": "ਚੁਣੇ ਹੋਏ ਜੋੜੋ", "select_btn": "ਚੁਣੋ"
    },
    "Papiamento": {
        "services": "SERVISIO", "lang_tab": "IDIOMA",
        "settings_tab": "INSTALASHON", "sett_app_auto": "Lanse aplikashon outomátikamente",
        "sett_srv_auto": "Kuminsá servisio outomátikamente",
        "main": "PRINSIPAL", "start": "kuminsando...", "stop": "parando...", 
        "running": "korendo", "stopped": "pará", "error": "eror", 
        "add_btn": "+ Añadí Servisio", "toast_no_srv": "Añadí servisio", 
        "see_err": "MIRA EROR", "add_dialog_title": "Buska i Añadí Servisio",
        "search_placeholder": "Nòmber di servisio...", "search_label": "Buska:",
        "add_selected_btn": "Añadí esnan selektá", "select_btn": "Selektá"
    },
    "فارسی": {
        "services": "سرویس‌ها", "lang_tab": "زبان‌ها",
        "settings_tab": "تنظیمات", "sett_app_auto": "اجرای خودکار برنامه",
        "sett_srv_auto": "شروع خودکار سرویس‌ها",
        "main": "اصلی", "start": "در حال شروع...", "stop": "در حال توقف...", 
        "running": "در حال اجرا", "stopped": "متوقف شد", "error": "خطا", 
        "add_btn": "+ افزودن سرویس", "toast_no_srv": "سرویس‌ها را اضافه کنید", 
        "see_err": "مشاهده خطا", "add_dialog_title": "جستجو و افزودن سرویس",
        "search_placeholder": "نام سرویس...", "search_label": "جستجو:",
        "add_selected_btn": "افزودن انتخاب شده", "select_btn": "انتخاب"
    },
    "Polski": {
        "services": "USŁUGI", "lang_tab": "JĘZYKI",
        "settings_tab": "USTAWIENIA", "sett_app_auto": "Uruchamiaj aplikację automatycznie",
        "sett_srv_auto": "Uruchamiaj usługi automatyчно",
        "main": "GŁÓWNY", "start": "uruchamianie...", "stop": "zatrzymywanie...", 
        "running": "działa", "stopped": "zatrzymano", "error": "błąd", 
        "add_btn": "+ Dodaj usługę", "toast_no_srv": "Dodaj usługi", 
        "see_err": "ZOBACZ BŁĄD", "add_dialog_title": "Szukaj i dodaj usługi",
        "search_placeholder": "Wpisz nazwę usługi...", "search_label": "Szukaj:",
        "add_selected_btn": "Dodaj wybrane", "select_btn": "Wybierz"
    },
    "Português": {
        "services": "SERVIÇOS", "lang_tab": "IDIOMAS",
        "settings_tab": "CONFIGURAÇÕES", "sett_app_auto": "Iniciar aplicação automaticamente",
        "sett_srv_auto": "Iniciar serviços automaticamente",
        "main": "PRINCIPAL", "start": "iniciando...", "stop": "parando...", 
        "running": "em execução", "stopped": "parado", "error": "erro", 
        "add_btn": "+ Adicionar Serviço", "toast_no_srv": "Adicionar serviços para começar", 
        "see_err": "VER ERRO", "add_dialog_title": "Buscar e Adicionar Serviços",
        "search_placeholder": "Nome do serviço...", "search_label": "Buscar:",
        "add_selected_btn": "Adicionar selecionados", "select_btn": "Selecionar"
    },
    "Português (Brasil)": {
        "services": "SERVIÇOS", "lang_tab": "IDIOMAS",
        "settings_tab": "CONFIGURAÇÕES", "sett_app_auto": "Iniciar app automaticamente",
        "sett_srv_auto": "Iniciar serviços automaticamente",
        "main": "PRINCIPAL", "start": "iniciando...", "stop": "parando...", 
        "running": "em execução", "stopped": "parado", "error": "erro", 
        "add_btn": "+ Adicionar Serviço", "toast_no_srv": "Adicione serviços", 
        "see_err": "VER ERRO", "add_dialog_title": "Buscar e Adicionar Serviços",
        "search_placeholder": "Nome do serviço...", "search_label": "Buscar:",
        "add_selected_btn": "Adicionar selecionados", "select_btn": "Selecionar"
    },
    "Română": {
        "services": "SERVICII", "lang_tab": "LIMBI",
        "settings_tab": "SETĂRI", "sett_app_auto": "Lansează aplicația automat",
        "sett_srv_auto": "Pornește serviciile automat",
        "main": "PRINCIPAL", "start": "pornire...", "stop": "oprire...", 
        "running": "rulează", "stopped": "oprit", "error": "eroare", 
        "add_btn": "+ Adaugă serviciu", "toast_no_srv": "Adăugați servicii pentru a începe", 
        "see_err": "VEZI EROAREA", "add_dialog_title": "Caută și adaugă servicii",
        "search_placeholder": "Introduceți numele...", "search_label": "Căutare:",
        "add_selected_btn": "Adaugă selectate", "select_btn": "Selectează"
    },
    "Русский": {
        "services": "СЛУЖБЫ", "lang_tab": "ЯЗЫКИ",
        "settings_tab": "НАСТРОЙКИ", "sett_app_auto": "Запускать приложение автоматически",
        "sett_srv_auto": "Запускать службы автоматически",
        "main": "ГЛАВНАЯ", "start": "запуск...", "stop": "остановка...", 
        "running": "работает", "stopped": "остановлено", "error": "ошибка", 
        "add_btn": "+ Добавить службу", "toast_no_srv": "Добавьте службы для запуска", 
        "see_err": "СМ. ОШИБКУ", "add_dialog_title": "Поиск и добавление служб",
        "search_placeholder": "Введите название службы...", "search_label": "Поиск:",
        "add_selected_btn": "Добавить выбранные", "select_btn": "Выбрать"
    },
    "Cebuano": {
        "services": "SERBISYO", "lang_tab": "PINULONGAN",
        "settings_tab": "SETTING", "sett_app_auto": "Awtomatikong ilunsad ang app",
        "sett_srv_auto": "Awtomatikong sugdan ang serbisyo",
        "main": "UNANG PANID", "start": "nagsugod...", "stop": "nihunong...", 
        "running": "nagdagan", "stopped": "nihunong", "error": "sayop", 
        "add_btn": "+ Idugang ang Serbisyo", "toast_no_srv": "Idugang ang mga serbisyo", 
        "see_err": "TAN-AWA ANG SAYOP", "add_dialog_title": "Pangitaa ug Idugang ang mga Serbisyo",
        "search_placeholder": "Isulod ang ngalan...", "search_label": "Pangitaa:",
        "add_selected_btn": "Idugang ang Napili", "select_btn": "Pilia"
    },
    "Српски": {
        "services": "УСЛУГЕ", "lang_tab": "ЈЕЗИЦИ",
        "settings_tab": "ПОДЕШАВАЊА", "sett_app_auto": "Покрени апликацију аутоматски",
        "sett_srv_auto": "Покрени услуге аутоматски",
        "main": "ГЛАВНО", "start": "покретање...", "stop": "заустављање...", 
        "running": "ради", "stopped": "заустављено", "error": "грешка", 
        "add_btn": "+ Додај услугу", "toast_no_srv": "Додајте услуге за почетак", 
        "see_err": "ВИДИ ГРЕШКУ", "add_dialog_title": "Претражи и додај услуге",
        "search_placeholder": "Унесите назив услуге...", "search_label": "Тражи:",
        "add_selected_btn": "Додај изабрано", "select_btn": "Изабери"
    },
    "Srpski (latinica)": {
        "services": "USLUGE", "lang_tab": "JEZICI",
        "settings_tab": "PODEŠAVANJA", "sett_app_auto": "Pokreni aplikaciju automatski",
        "sett_srv_auto": "Pokreni usluge automatski",
        "main": "GLAVNO", "start": "pokretanje...", "stop": "zaustavljanje...", 
        "running": "radi", "stopped": "zaustavljeno", "error": "greška", 
        "add_btn": "+ Dodaj uslugu", "toast_no_srv": "Dodajte usluge za početak", 
        "see_err": "VIDI GREŠKU", "add_dialog_title": "Pretraži i dodaj usluge",
        "search_placeholder": "Unesite naziv usluge...", "search_label": "Traži:",
        "add_selected_btn": "Dodaj izabrano", "select_btn": "Izaberi"
    },
    "සිංහල": {
        "services": "සේවා", "lang_tab": "භාෂා",
        "settings_tab": "සැකසුම්", "sett_app_auto": "යෙදුම ස්වයංක්‍රීයව දියත් කරන්න",
        "sett_srv_auto": "සේවා ස්වයංක්‍රීයව ආරම්භ කරන්න",
        "main": "ප්‍රධාන", "start": "ආරම්භ වෙමින්...", "stop": "නැවතෙමින්...", 
        "running": "ක්‍රියාත්මකයි", "stopped": "නතර විය", "error": "දෝෂයකි", 
        "add_btn": "+ සේවාවක් එක් කරන්න", "toast_no_srv": "ආරම්භ කිරීමට සේවා එක් කරන්න", 
        "see_err": "දෝෂය බලන්න", "add_dialog_title": "සේවා සොයා එක් කරන්න",
        "search_placeholder": "සේවා නම ඇතුළත් කරන්න...", "search_label": "සොයන්න:",
        "add_selected_btn": "තෝරාගත් ඒවා එක් කරන්න", "select_btn": "තෝරන්න"
    },
    "Slovenčina": {
        "services": "SLUŽBY", "lang_tab": "JAZYKY",
        "settings_tab": "NASTAVENIA", "sett_app_auto": "Spustiť aplikáciu automaticky",
        "sett_srv_auto": "Spustiť služby automaticky",
        "main": "HLAVNÉ", "start": "spúšťanie...", "stop": "zastavovanie...", 
        "running": "beží", "stopped": "zastavené", "error": "chyba", 
        "add_btn": "+ Pridať službu", "toast_no_srv": "Pridajte služby", 
        "see_err": "ZOBRAZIŤ CHYBU", "add_dialog_title": "Hľadať a pridať služby",
        "search_placeholder": "Zadajte názov služby...", "search_label": "Hľadať:",
        "add_selected_btn": "Pridať vybrané", "select_btn": "Vybrať"
    },
    "Slovenščina": {
        "services": "STORITVE", "lang_tab": "JEZIKI",
        "settings_tab": "NASTAVITVE", "sett_app_auto": "Zaženi aplikacijo samodejno",
        "sett_srv_auto": "Zaženi storitve samodejno",
        "main": "GLAVNO", "start": "zaganjanje...", "stop": "ustavljanje...", 
        "running": "deluje", "stopped": "ustavljeno", "error": "napaka", 
        "add_btn": "+ Dodaj storitev", "toast_no_srv": "Dodajte storitve", 
        "see_err": "POGLEDAJ NAPAKO", "add_dialog_title": "Išči in dodaj storitve",
        "search_placeholder": "Vnesite ime storitve...", "search_label": "Išči:",
        "add_selected_btn": "Dodaj izbrano", "select_btn": "Izberi"
    },
    "Kiswahili": {
        "services": "HUDUMA", "lang_tab": "LUGHA",
        "settings_tab": "MIPANGILIO", "sett_app_auto": "Anzisha programu kiotomatiki",
        "sett_srv_auto": "Anzisha huduma kiotomatiki",
        "main": "KUU", "start": "kuanzisha...", "stop": "kusitisha...", 
        "running": "inafanya kazi", "stopped": "imesitishwa", "error": "hitilafu", 
        "add_btn": "+ Ongeza Huduma", "toast_no_srv": "Ongeza huduma ili kuanza", 
        "see_err": "ANGALIA HITILAFU", "add_dialog_title": "Tafuta na Uongeze Huduma",
        "search_placeholder": "Ingiza jina la huduma...", "search_label": "Tafuta:",
        "add_selected_btn": "Ongeza zilizochaguliwa", "select_btn": "Chagua"
    },
    "Basa Sunda": {
        "services": "LAYANAN", "lang_tab": "BASA",
        "settings_tab": "SETÉLAN", "sett_app_auto": "Jalankeun aplikasi otomatis",
        "sett_srv_auto": "Mimitian layanan otomatis",
        "main": "UTAMA", "start": "ngamimitian...", "stop": "ngeureunkeun...", 
        "running": "jalan", "stopped": "eureun", "error": "kasalahan", 
        "add_btn": "+ Tambah Layanan", "toast_no_srv": "Tambah layanan pikeun ngamimitian", 
        "see_err": "TÉMBONGKEUN KASALAHAN", "add_dialog_title": "Milari jeung Tambah Layanan",
        "search_placeholder": "Lebu nami layanan...", "search_label": "Milari:",
        "add_selected_btn": "Tambah nu dipilih", "select_btn": "Pilih"
    },
    "Tagalog": {
        "services": "SERBISYO", "lang_tab": "WIKA",
        "settings_tab": "SETTING", "sett_app_auto": "Awtomatikong ilunsad ang app",
        "sett_srv_auto": "Awtomatikong simulan ang serbisyo",
        "main": "PANGUNAHIN", "start": "nagsisimula...", "stop": "humihinto...", 
        "running": "tumatakbo", "stopped": "huminto", "error": "error", 
        "add_btn": "+ Magdagdag ng Serbisyo", "toast_no_srv": "Magdagdag ng mga serbisyo", 
        "see_err": "TINGNAN ANG ERROR", "add_dialog_title": "Maghanap at Magdagdag ng Serbisyo",
        "search_placeholder": "Ilagay ang pangalan...", "search_label": "Maghanap:",
        "add_selected_btn": "Idagdag ang Napili", "select_btn": "Piliin"
    },
    "Тоҷикӣ": {
        "services": "ХИЗМАТРАСОНИҲО", "lang_tab": "ЗАБОНҲО",
        "settings_tab": "ТАНЗИМОТ", "sett_app_auto": "Оғози худкори барнома",
        "sett_srv_auto": "Оғози худкори хизматрасониҳо",
        "main": "АСОСӢ", "start": "оғоз...", "stop": "ист...", 
        "running": "фаъол", "stopped": "қатъшуда", "error": "хато", 
        "add_btn": "+ Иловаи хизматрасонӣ", "toast_no_srv": "Хизматрасониҳоро илова кунед", 
        "see_err": "ДИДАНИ ХАТО", "add_dialog_title": "Ҷустуҷӯ ва иловаи хизматрасониҳо",
        "search_placeholder": "Номи хизматрасониро ворид кунед...", "search_label": "Ҷустуҷӯ:",
        "add_selected_btn": "Иловаи интихобшуда", "select_btn": "Интихоб"
    },
    "ไทย": {
        "services": "บริการ", "lang_tab": "ภาษา",
        "settings_tab": "ตั้งค่า", "sett_app_auto": "เริ่มแอปโดยอัตโนมัติ",
        "sett_srv_auto": "เริ่มบริการโดยอัตโนมัติ",
        "main": "หลัก", "start": "กำลังเริ่ม...", "stop": "กำลังหยุด...", 
        "running": "กำลังทำงาน", "stopped": "หยุดแล้ว", "error": "ข้อผิดพลาด", 
        "add_btn": "+ เพิ่มบริการ", "toast_no_srv": "เพิ่มบริการเพื่อเริ่ม", 
        "see_err": "ดูข้อผิดพลาด", "add_dialog_title": "ค้นหาและเพิ่มบริการ",
        "search_placeholder": "ใส่ชื่อบริการ...", "search_label": "ค้นหา:",
        "add_selected_btn": "เพิ่มที่เลือก", "select_btn": "เลือก"
    },
    "தமிழ்": {
        "services": "சேவைகள்", "lang_tab": "மொழிகள்",
        "settings_tab": "அமைப்புகள்", "sett_app_auto": "தானாகவே பயன்பாட்டைத் தொடங்கு",
        "sett_srv_auto": "தானாகவே சேவைகளைத் தொடங்கு",
        "main": "முதன்மை", "start": "தொடங்குகிறது...", "stop": "நிற்கிறது...", 
        "running": "செயல்படுகிறது", "stopped": "நிறுத்தப்பட்டது", "error": "பிழை", 
        "add_btn": "+ சேவையைச் சேர்க்கவும்", "toast_no_srv": "தொடங்க சேவைகளைச் சேர்க்கவும்", 
        "see_err": "பிழையைப் பார்க்கவும்", "add_dialog_title": "சேவைகளைத் தேடிச் சேர்க்கவும்",
        "search_placeholder": "பெயரை உள்ளிடவும்...", "search_label": "தேடு:",
        "add_selected_btn": "தேர்ந்தெடுத்ததைச் சேர்க்கவும்", "select_btn": "தேர்வு"
    },
    "Татарча": {
        "services": "ХЕЗМӘТЛӘР", "lang_tab": "ТЕЛЛӘР",
        "settings_tab": "КӨЙЛӘМӘЛӘР", "sett_app_auto": "Программаны автомат җибәрү",
        "sett_srv_auto": "Хезмәтләрне автомат җибәрү",
        "main": "ТӨП", "start": "җибәрелә...", "stop": "туктатыла...", 
        "running": "эшли", "stopped": "туктатылды", "error": "хата", 
        "add_btn": "+ Хезмәт өстәү", "toast_no_srv": "Хезмәтләр өстәгез", 
        "see_err": "ХАТАНЫ КҮРҮ", "add_dialog_title": "Хезмәтләр эзләү һәм өстәү",
        "search_placeholder": "Хезмәт исеме...", "search_label": "Эзләү:",
        "add_selected_btn": "Сайланганны өстәү", "select_btn": "Сайлау"
    },
    "తెలుగు": {
        "services": "సేవలు", "lang_tab": "భాషలు",
        "settings_tab": "సెట్టింగ్‌లు", "sett_app_auto": "ఆటోమేటిక్‌గా ప్రారంభించు",
        "sett_srv_auto": "సేవలను ఆటోమేటిక్‌గా ప్రారంభించు",
        "main": "ప్రధానం", "start": "ప్రారంభమవుతోంది...", "stop": "ఆగిపోతోంది...", 
        "running": "నడుస్తోంది", "stopped": "ఆగిపోయింది", "error": "లోపం", 
        "add_btn": "+ సేవను జోడించు", "toast_no_srv": "ప్రారంభించడానికి సేవలను జోడించు", 
        "see_err": "లోపాన్ని చూడు", "add_dialog_title": "సేవలను వెతికి జోడించు",
        "search_placeholder": "సేవ పేరు రాయండి...", "search_label": "వెతుకు:",
        "add_selected_btn": "ఎంచుకున్నవి జోడించు", "select_btn": "ఎంచుకో"
    },
    "Тыва дыл": {
        "services": "АЛБАННАР", "lang_tab": "ДЫЛДАР",
        "settings_tab": "ТААРЫШТЫРЫГЛАР", "sett_app_auto": "Программаны автомат кылдыр ажыдар",
        "sett_srv_auto": "Албаннарны автомат кылдыр ажыдар",
        "main": "КОЛ", "start": "ажыттынып турар...", "stop": "туруп турар...", 
        "running": "ажылдап турар", "stopped": "тургузупкан", "error": "алдаа", 
        "add_btn": "+ Албан немеер", "toast_no_srv": "Албаннарны немеңер", 
        "see_err": "АЛДААНЫ КӨРӨӨР", "add_dialog_title": "Албаннарны дилеп немеер",
        "search_placeholder": "Албанның ады...", "search_label": "Дилээр:",
        "add_selected_btn": "Шилээнни немеер", "select_btn": "Шилээр"
    },
    "Türkçe": {
        "services": "SERVİSLER", "lang_tab": "DİLLER",
        "settings_tab": "AYARLAR", "sett_app_auto": "Uygulamayı otomatik başlat",
        "sett_srv_auto": "Servisleri otomatik başlat",
        "main": "ANA SAYFA", "start": "başlatılıyor...", "stop": "durduruluyor...", 
        "running": "çalışıyor", "stopped": "durduruldu", "error": "hata", 
        "add_btn": "+ Servis Ekle", "toast_no_srv": "Başlatmak için servis ekleyin", 
        "see_err": "HATAYI GÖR", "add_dialog_title": "Servis Ara ve Ekle",
        "search_placeholder": "Servis adı girin...", "search_label": "Ara:",
        "add_selected_btn": "Seçilenleri Ekle", "select_btn": "Seç"
    },
    "Удмурт": {
        "services": "УЖТАЯС", "lang_tab": "КЫЛЪЁС",
        "settings_tab": "ТУПАЛЪЯНЪЁС", "sett_app_auto": "Программаез ачиз лэзён",
        "sett_srv_auto": "Ужтаясты ачиз лэзён",
        "main": "ВАЛТӢСЬ", "start": "лэзиське...", "stop": "дугдытэ...", 
        "running": "уджа", "stopped": "дугдытэмын", "error": "янгыш", 
        "add_btn": "+ Ужтас ватсано", "toast_no_srv": "Ужтаясты ватсалэ", 
        "see_err": "ЯНГЫШЕЗ АДЗЫНЫ", "add_dialog_title": "Ужтаясты утчаны но ватсаны",
        "search_placeholder": "Ужтаслэн нимыз...", "search_label": "Утчан:",
        "add_selected_btn": "Быръемзэ ватсаны", "select_btn": "Быръяны"
    },
    "Oʻzbekcha": {
        "services": "XIZMATLAR", "lang_tab": "TILLAR",
        "settings_tab": "SOZLAMALAR", "sett_app_auto": "Ilovani avtomatik ishga tushirish",
        "sett_srv_auto": "Xizmatlarni avtomatik ishga tushirish",
        "main": "ASOSIY", "start": "ishga tushmoqda...", "stop": "toʻxtatilmoqda...", 
        "running": "ishlayapti", "stopped": "toʻxtatildi", "error": "xato", 
        "add_btn": "+ Xizmat qoʻshish", "toast_no_srv": "Xizmatlarni qoʻshing", 
        "see_err": "XATONI KOʻRISH", "add_dialog_title": "Xizmatlarni qidirish va qoʻshish",
        "search_placeholder": "Xizmat nomini kiriting...", "search_label": "Qidiruv:",
        "add_selected_btn": "Tanlanganlarni qoʻshish", "select_btn": "Tanlash"
    },
    "Ўзбекча (кириллица)": {
        "services": "ХИЗМАТЛАР", "lang_tab": "ТИЛЛАР",
        "settings_tab": "СОЗЛАМАЛАР", "sett_app_auto": "Иловани автоматик ишга тушириш",
        "sett_srv_auto": "Хизматларни автоматик ишга тушириш",
        "main": "АСОСИЙ", "start": "ишга тушмоқда...", "stop": "тўхтатилмоқда...", 
        "running": "ишлаяпти", "stopped": "тўхтатилди", "error": "хато", 
        "add_btn": "+ Хизмат қўшиш", "toast_no_srv": "Хизматларни қўшинг", 
        "see_err": "ХАТОНИ КЎРИШ", "add_dialog_title": "Хизматларни қидириш ва қўшиш",
        "search_placeholder": "Хизмат номини киритинг...", "search_label": "Қидирув:",
        "add_selected_btn": "Танланганларни қўшиш", "select_btn": "Танлаш"
    },
    "Українська": {
        "services": "СЛУЖБИ", "lang_tab": "МОВИ",
        "settings_tab": "НАЛАШТУВАННЯ", "sett_app_auto": "Запускати додаток автоматично",
        "sett_srv_auto": "Запускати служби автоматично",
        "main": "ГОЛОВНА", "start": "запуск...", "stop": "зупинка...", 
        "running": "працює", "stopped": "зупинено", "error": "помилка", 
        "add_btn": "+ Додати службу", "toast_no_srv": "Додайте служби для запуску", 
        "see_err": "ДИВ. ПОМИЛКУ", "add_dialog_title": "Пошук та додавання служб",
        "search_placeholder": "Введіть назву служби...", "search_label": "Пошук:",
        "add_selected_btn": "Додати вибрані", "select_btn": "Вибрати"
    },
    "اردو": {
        "services": "خدمات", "lang_tab": "زبانیں",
        "settings_tab": "ترتیبات", "sett_app_auto": "ایپ خود بخود شروع کریں",
        "sett_srv_auto": "خدمات خود بخود شروع کریں",
        "main": "مرکزی", "start": "شروع ہو رہا ہے...", "stop": "رک رہا ہے...", 
        "running": "چل رہا ہے", "stopped": "رک گیا", "error": "غلطی", 
        "add_btn": "+ سروس شامل کریں", "toast_no_srv": "سروسز شامل کریں", 
        "see_err": "غلطی دیکھیں", "add_dialog_title": "تلاش کریں اور سروس شامل کریں",
        "search_placeholder": "سروس کا نام لکھیں...", "search_label": "تلاش:",
        "add_selected_btn": "منتخب کردہ شامل کریں", "select_btn": "منتخب کریں"
    },
    "Suomi": {
        "services": "PALVELUT", "lang_tab": "KIELET",
        "settings_tab": "ASETUKSET", "sett_app_auto": "Käynnistä sovellus automaattisesti",
        "sett_srv_auto": "Käynnistä palvelut automaattisesti",
        "main": "PÄÄSIVU", "start": "käynnistetään...", "stop": "pysäytetään...", 
        "running": "käynnissä", "stopped": "pysäytetty", "error": "virhe", 
        "add_btn": "+ Lisää palvelu", "toast_no_srv": "Lisää palveluita", 
        "see_err": "NÄYTÄ VIRHE", "add_dialog_title": "Etsi ja lisää palveluita",
        "search_placeholder": "Kirjoita palvelun nimi...", "search_label": "Haku:",
        "add_selected_btn": "Lisää valitut", "select_btn": "Valitse"
    },
    "Français": {
        "services": "SERVICES", "lang_tab": "LANGUES",
        "settings_tab": "PARAMÈTRES", "sett_app_auto": "Lancer l'app automatiquement",
        "sett_srv_auto": "Démarrer les services automatiquement",
        "main": "PRINCIPAL", "start": "démarrage...", "stop": "arrêt...", 
        "running": "en cours", "stopped": "arrêté", "error": "erreur", 
        "add_btn": "+ Ajouter Service", "toast_no_srv": "Ajouter des services", 
        "see_err": "VOIR ERREUR", "add_dialog_title": "Chercher et ajouter des services",
        "search_placeholder": "Nom du service...", "search_label": "Chercher:",
        "add_selected_btn": "Ajouter sélectionnés", "select_btn": "Choisir"
    },
    "हिन्दी": {
        "services": "सेवाएं", "lang_tab": "भाषाएं",
        "settings_tab": "सेटिंग्स", "sett_app_auto": "ऐप स्वचालित रूप से लॉन्च करें",
        "sett_srv_auto": "सेवाएं स्वचालित रूप से शुरू करें",
        "main": "मुख्य", "start": "शुरू हो रहा है...", "stop": "रुक रहा है...", 
        "running": "चल रहा है", "stopped": "रुका हुआ", "error": "त्रुटि", 
        "add_btn": "+ सेवा जोड़ें", "toast_no_srv": "सेवाएं जोड़ें", 
        "see_err": "त्रुटि देखें", "add_dialog_title": "सेवाएं खोजें और जोड़ें",
        "search_placeholder": "सेवा का नाम दर्ज करें...", "search_label": "खोजें:",
        "add_selected_btn": "चयनित जोड़ें", "select_btn": "चुनें"
    },
    "Hrvatski": {
        "services": "USLUGE", "lang_tab": "JEZICI",
        "settings_tab": "POSTAVKE", "sett_app_auto": "Pokreni aplikaciju automatski",
        "sett_srv_auto": "Pokreni usluge automatski",
        "main": "GLAVNO", "start": "pokretanje...", "stop": "zaustavljanje...", 
        "running": "radi", "stopped": "zaustavljeno", "error": "pogreška", 
        "add_btn": "+ Dodaj uslugu", "toast_no_srv": "Dodajte usluge", 
        "see_err": "VIDI POGREŠKU", "add_dialog_title": "Pretraži i dodaj usluge",
        "search_placeholder": "Unesite naziv usluge...", "search_label": "Traži:",
        "add_selected_btn": "Dodaj odabrano", "select_btn": "Odaberi"
    },
    "Čeština": {
        "services": "SLUŽBY", "lang_tab": "JAZYKY",
        "settings_tab": "NASTAVENÍ", "sett_app_auto": "Spustit aplikaci automaticky",
        "sett_srv_auto": "Spustit služby automaticky",
        "main": "HLAVNÍ", "start": "spouštění...", "stop": "zastavování...", 
        "running": "běží", "stopped": "zastaveno", "error": "chyba", 
        "add_btn": "+ Přidat službu", "toast_no_srv": "Přidejte služby", 
        "see_err": "ZOBRAZIT CHYBU", "add_dialog_title": "Hledat a přidat služby",
        "search_placeholder": "Zadejte název služby...", "search_label": "Hledat:",
        "add_selected_btn": "Přidat vybrané", "select_btn": "Vybrat"
    },
    "Чӑвашла": {
        "services": "СЛУЖБĂСЕМ", "lang_tab": "ЧӖЛХЕСЕМ",
        "settings_tab": "ЛĂПКАЛАВ", "sett_app_auto": "Программăна автоматлă ярмалли",
        "sett_srv_auto": "Службăсене автоматлă ярмалли",
        "main": "ТӖП", "start": "ярать...", "stop": "чарать...", 
        "running": "Ӗҫлет", "stopped": "чарăнчӗ", "error": "йӑнӑш", 
        "add_btn": "+ Служба хуш", "toast_no_srv": "Службăсем хушӑр", 
        "see_err": "ЙĂНĂША ПĂХ", "add_dialog_title": "Службăсем шыра та хуш",
        "search_placeholder": "Служба ячӗ...", "search_label": "Шырав:",
        "add_selected_btn": "Суйласа илнине хуш", "select_btn": "Суйла"
    },
    "Svenska": {
        "services": "TJÄNSTER", "lang_tab": "SPRÅK",
        "settings_tab": "INSTÄLLNINGAR", "sett_app_auto": "Starta appen automatiskt",
        "sett_srv_auto": "Starta tjänster automatiskt",
        "main": "HUVUDMENY", "start": "startar...", "stop": "stoppar...", 
        "running": "körs", "stopped": "stoppad", "error": "fel", 
        "add_btn": "+ Lägg till tjänst", "toast_no_srv": "Lägg till tjänster", 
        "see_err": "VISA FEL", "add_dialog_title": "Sök och lägg till tjänster",
        "search_placeholder": "Ange tjänstenamn...", "search_label": "Sök:",
        "add_selected_btn": "Lägg till valda", "select_btn": "Välj"
    },
    "Gàidhlig": {
        "services": "SEIRBHEISEAN", "lang_tab": "CÀNANAN",
        "settings_tab": "ROGHNACHAIDHEAN", "sett_app_auto": "Tòisich an aplacaid gu fèin-obrachail",
        "sett_srv_auto": "Tòisich seirbheisean gu fèin-obrachail",
        "main": "PRÌOMH", "start": "a' tòiseachadh...", "stop": "a' stad...", 
        "running": "a' ruith", "stopped": "stadte", "error": "mearachd", 
        "add_btn": "+ Cuir seirbheis ris", "toast_no_srv": "Cuir seirbheisean ris", 
        "see_err": "FAIC MEARACHD", "add_dialog_title": "Lorg is cuir seirbheisean ris",
        "search_placeholder": "Ainm na seirbheis...", "search_label": "Lorg:",
        "add_selected_btn": "Cuir ris an fheadhainn thaghte", "select_btn": "Tagh"
    },
    "Sindarin": {
        "services": "LEVIATH", "lang_tab": "LAMBATH",
        "settings_tab": "EIDIATH", "sett_app_auto": "Beriad i-app nest",
        "sett_srv_auto": "Beriad leviath nest",
        "main": "THEL", "start": "beriad...", "stop": "darad...", 
        "running": "maer", "stopped": "daro", "error": "mist", 
        "add_btn": "+ Pannada Levia", "toast_no_srv": "Pannada leviath", 
        "see_err": "CENAD MIST", "add_dialog_title": "Tevalol a phannadol leviath",
        "search_placeholder": "Eneth levia...", "search_label": "Tevalol:",
        "add_selected_btn": "Pannada i-vail", "select_btn": "Cilad"
    },
    "Emoji": {
        "services": "🛠️", "lang_tab": "🌍",
        "settings_tab": "⚙️", "sett_app_auto": "🤖 ▶️",
        "sett_srv_auto": "🛠️ ▶️",
        "main": "🏠", "start": "⏳...", "stop": "🛑...", 
        "running": "✅", "stopped": "⏹️", "error": "⚠️", 
        "add_btn": "➕ 🛠️", "toast_no_srv": "➕ 🛠️ 🔜", 
        "see_err": "👁️ ⚠️", "add_dialog_title": "🔍 ➕ 🛠️",
        "search_placeholder": "✏️...", "search_label": "🔍:",
        "add_selected_btn": "➕ ✅", "select_btn": "🖱️"
    },
    "Erzjanj": {
        "services": "СЛУЖБАТНЕ", "lang_tab": "КЕЛЬТНЕ",
        "settings_tab": "ВИТНЕМАТНЕ", "sett_app_auto": "Программанть автоматла панжомазо",
        "sett_srv_auto": "Службатнень автоматла панжомаст",
        "main": "ПРЯВТ", "start": "панжови...", "stop": "лоткси...", 
        "running": "важоди", "stopped": "лотксезь", "error": "ильведевкс", 
        "add_btn": "+ Поладомс служба", "toast_no_srv": "Поладодо службат", 
        "see_err": "НЕЕМС ИЛЬВЕДЕВКС", "add_dialog_title": "Вешнемс ды поладомс службат",
        "search_placeholder": "Службанть лемезэ...", "search_label": "Вешнема:",
        "add_selected_btn": "Поладомс кочказь", "select_btn": "Кочкамс"
    },
    "Esperanto": {
        "services": "SERVOJ", "lang_tab": "LINGVOJ",
        "settings_tab": "AGORDOJ", "sett_app_auto": "Lanĉi aplikaĵon aŭtomate",
        "sett_srv_auto": "Lanĉi servojn aŭtomate",
        "main": "ĈEFA", "start": "lanĉante...", "stop": "haltigante...", 
        "running": "funkcianta", "stopped": "haltigita", "error": "eraro", 
        "add_btn": "+ Aldoni servon", "toast_no_srv": "Aldonu servojn por komenci", 
        "see_err": "VIDI ERARON", "add_dialog_title": "Serĉi kaj aldoni servojn",
        "search_placeholder": "Tajpu nomon...", "search_label": "Serĉi:",
        "add_selected_btn": "Aldoni elektitajn", "select_btn": "Elekti"
    },
    "Eesti": {
        "services": "TEENUSED", "lang_tab": "KEELED",
        "settings_tab": "SEADED", "sett_app_auto": "Käivita rakendus automaatselt",
        "sett_srv_auto": "Käivita teenused automaatselt",
        "main": "PEALEHT", "start": "käivitamine...", "stop": "peatamine...", 
        "running": "töötab", "stopped": "peatatud", "error": "viga", 
        "add_btn": "+ Lisa teenus", "toast_no_srv": "Lisa teenused käivitamiseks", 
        "see_err": "VAATA VIGA", "add_dialog_title": "Otsi ja lisa teenuseid",
        "search_placeholder": "Sisesta nimi...", "search_label": "Otsing:",
        "add_selected_btn": "Lisa valitud", "select_btn": "Vali"
    },
    "Basa Jawa": {
        "services": "LAYANAN", "lang_tab": "BASA",
        "settings_tab": "SETELAN", "sett_app_auto": "Bukak aplikasi otomatis",
        "sett_srv_auto": "Mulai layanan otomatis",
        "main": "UTAMA", "start": "miwiti...", "stop": "mandheg...", 
        "running": "mlaku", "stopped": "mandheg", "error": "luput", 
        "add_btn": "+ Tambah Layanan", "toast_no_srv": "Tambah layanan kanggo miwiti", 
        "see_err": "DELENG LUPUT", "add_dialog_title": "Golek lan Tambah Layanan",
        "search_placeholder": "Lebokake jeneng...", "search_label": "Golek:",
        "add_selected_btn": "Tambah sing dipilih", "select_btn": "Pilih"
    },
    "Саха тыла": {
        "services": "ХОНУКТАР", "lang_tab": "ТЫЛЛАР",
        "settings_tab": "ТУРУОРУУЛАР", "sett_app_auto": "Программаны бэйэтэ холбонор",
        "sett_srv_auto": "Хонуктары бэйэтэ холбонор",
        "main": "СҮРҮН", "start": "холбонор...", "stop": "тохтотуллар...", 
        "running": "үлэлиир", "stopped": "тохтоото", "error": "алҕас", 
        "add_btn": "+ Хонугу эбэргэ", "toast_no_srv": "Хонуктары эбэр наада", 
        "see_err": "АЛҔАҺЫ КӨРӨРГӨ", "add_dialog_title": "Хонуктары көрдөөһүн уонна эбии",
        "search_placeholder": "Хонук аата...", "search_label": "Көрдөөһүн:",
        "add_selected_btn": "Талыллыбыты эбэргэ", "select_btn": "Талар"
    },
    "日本語": {
        "services": "サービス", "lang_tab": "言語",
        "settings_tab": "設定", "sett_app_auto": "アプリを自動起動する",
        "sett_srv_auto": "サービスを自動開始する",
        "main": "メイン", "start": "起動中...", "stop": "停止中...", 
        "running": "稼働中", "stopped": "停止", "error": "エラー", 
        "add_btn": "+ サービスを追加", "toast_no_srv": "サービスを追加してください", 
        "see_err": "エラーを表示", "add_dialog_title": "サービスの検索と追加",
        "search_placeholder": "サービス名を入力...", "search_label": "検索:",
        "add_selected_btn": "選択項目を追加", "select_btn": "選択"
    }
}
class LanguagesTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.bg_rot=0.3
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        # Включаем плавную прокрутку по пикселям вместо перескоков по элементам
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            /* Сам список и его внутренняя область прокрутки */
            QListWidget, QListWidget::viewport { 
                background: transparent; 
                border: none; 
                outline: none; 
            }
            
            QListWidget::item { 
                background: white; 
                border-radius: 15px; 
                margin-bottom: 10px; 
                border: 1px solid #ddd; 
            }
            
            QListWidget::item:selected { 
                border: 2px solid #007AFF; 
                background: white; 
            }

            /* Полная прозрачность для всей дорожки скроллбара */
            QScrollBar:vertical {
                border: none;
                background: transparent; 
                width: 14px;
                margin: 0px;
            }

            /* Ползунок */
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 30px;
                border-radius: 4px;
                margin-left: 6px; /* Оставляем отступ только для самого ползунка */
            }

            QScrollBar::handle:vertical:hover {
                background: #AAAAAA;
            }

            /* Убираем все технические области фона скроллбара */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }
        """)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Настраиваем скорость и плавность через объект прокрутки
        delta_scroll = self.list_widget.verticalScrollBar()
        delta_scroll.setSingleStep(15) # Шаг прокрутки в пикселях
        layout.addWidget(self.list_widget)
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        # Получаем перевод слова "Выбрать" для текущего языка приложения
        current_t = LANGUAGES[self.main_win.current_lang]
        btn_label = current_t.get("select_btn", "Select") 

        for lang in LANGUAGES.keys():
            li = QListWidgetItem(self.list_widget)
            li.setSizeHint(QSize(0, 60))
            is_active = (lang == self.main_win.current_lang)
            
            # Исправлено: передаем btn_label как именованный или позиционный аргумент ДО parent
            w = LanguageItemWidget(lang, is_active, btn_label, self) 
            w.selected.connect(self.main_win.change_language)
            self.list_widget.setItemWidget(li, w)
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save(); p.translate(self.width()/2, self.height()/2); p.rotate(self.bg_rot)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(242, 242, 242))
        for _ in range(12):
            p.drawRect(-35, -245, 70, 490); p.rotate(30)
        p.drawEllipse(QPointF(0, 0), 200, 200); p.setBrush(QColor(248, 249, 250)); p.drawEllipse(QPointF(0, 0), 90, 90); p.restore()
    def update_animation(self):
        # Update the rotation value and trigger a repaint
        self.bg_rot += 0.3 
        self.update()
def get_config_path():
    # Путь: C:\Users\Имя\AppData\LocalLow\ServiceGuardPro
    user_profile = os.environ.get('USERPROFILE')
    low_path = os.path.join(user_profile, 'AppData', 'LocalLow', 'ServiceGuardPro')
    
    # Создаем папку, если её еще нет
    if not os.path.exists(low_path):
        os.makedirs(low_path)
    
    return os.path.join(low_path, 'services_config.json')
def get_autostart_config_path():
    # Путь: LOCALAPPDATA/ServiceGuardPro/autostart.json
    local_app_data = os.environ.get('LOCALAPPDATA')
    path = os.path.join(local_app_data, 'ServiceGuardPro')
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    return os.path.join(path, 'autostart.json')
# --- ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ---
class ToastNotification(QLabel):
    def __init__(self, parent, message):
        super().__init__(message, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(250, 45)
        # Белый фон, желтая рамка, закругление
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #f1c40f;
                border-radius: 10px;
                color: #333;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        # Начальная позиция (за пределами экрана внизу)
        self.start_pos = QPoint(125, 710) 
        # Конечная позиция (видимая часть снизу)
        self.end_pos = QPoint(125, 550)
        self.move(self.start_pos)
        
    def show_toast(self):
        self.show()
        # Анимация появления вверх
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(500)
        self.anim.setStartValue(self.start_pos)
        self.anim.setEndValue(self.end_pos)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Анимация ухода вниз
        self.anim_back = QPropertyAnimation(self, b"pos")
        self.anim_back.setDuration(500)
        self.anim_back.setStartValue(self.end_pos)
        self.anim_back.setEndValue(self.start_pos)
        self.anim_back.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # Таймер: держим 3 секунды, затем улетаем вниз
        self.anim.start()
        QTimer.singleShot(3000, self.anim_back.start)
        # Удаляем объект после завершения анимации
        self.anim_back.finished.connect(self.deleteLater)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# --- ПОТОК УПРАВЛЕНИЯ СЛУЖБАМИ ---
class ServiceWorker(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, services, start_mode):
        super().__init__()
        self.services = services
        self.start_mode = start_mode

    def run(self):
        success, log = True, ""
        action = "start" if self.start_mode else "stop"
        for srv in self.services:
            srv_name = srv.split('(')[-1].strip(')') if '(' in srv else srv
            try:
                res = subprocess.run(
                    ['sc', action, srv_name],
                    capture_output=True,
                    text=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Команды Windows (sc.exe) всегда возвращают CP866
                stdout = res.stdout.decode('cp866', errors='replace')
                stderr = res.stderr.decode('cp866', errors='replace')

                if res.returncode != 0 and "1056" not in stdout and "1062" not in stdout:
                    success = False
                    log += f"[{srv_name}]: {stderr or stdout}\n"
            except Exception as e:
                success = False
                log += f"Критический сбой {srv_name}: {str(e)}\n"
        self.finished.emit(success, log)

# --- ИСКРЫ ДЛЯ РЕЖИМА ОШИБКИ ---
class Spark:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.dx, self.dy = random.uniform(-9, 9), random.uniform(-15, 5)
        self.life = 255
        self.size = random.randint(4, 9)
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.7
        self.life -= 18

# --- ВИДЖЕТ ЭЛЕМЕНТА СПИСКА ---
class ServiceItemWidget(QWidget):
    removed = pyqtSignal(str)
    def __init__(self, name, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.name = name
        for i in CRITICAL_SERVICES:
            if i in name:
                name+=" ⚠️"
                break
        label = QLabel(name)
        label.setStyleSheet("border: none; background: transparent; font-size: 13px; color: #333;")
        
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(30, 30)
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton { background-color: #f2f2f2; border: none; border-radius: 15px; color: #999; }
            QPushButton:hover { background-color: #e0e0e0; color: #ff5555; }
        """)
        self.del_btn.clicked.connect(lambda: self.removed.emit(self.name))
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self.del_btn)
        layout.setContentsMargins(15, 5, 10, 5)

# --- ВКЛАДКА АКТИВАЦИИ ---
class ActivationTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.bg_rot, self.is_running, self.is_err = 0, False, False
        self.sparks = []
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        
        # 1. Исправленный основной лейаут
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Убираем внешние отступы

        # 2. Создание кнопки
        self.btn = MainBtn(self)
        self.btn.clicked.connect(self.toggle_state)
        
        # 3. Эффект свечения
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(30)
        self.glow.setOffset(0) 
        self.glow.setColor(QColor(0, 0, 0, 40))
        self.btn.setGraphicsEffect(self.glow)

        # 4. Центрирование: одна растяжка сверху, одна снизу
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch(1)

        # --- СТАТУСНЫЙ ТЕКСТ ---
        self.status_label = QLabel("остановлено", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 14px; 
                font-weight: bold; 
                color: #bdc3c7; 
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }
        """)
        self.status_label.setFixedWidth(200)
        # Координаты для размещения под кнопкой
        self.status_label.move(150, 440)

        # Панель ошибки
        self.error_panel = QFrame(self)
        self.error_panel.setGeometry(50, 520, 400, 80)
        self.error_panel.setObjectName("ErrorPanel")
        self.error_panel.hide()
        
        ov_layout = QVBoxLayout(self.error_panel)
        self.msg_btn = QPushButton("УВИДЕТЬ ОШИБКУ")
        self.msg_btn.setObjectName("ErrorMsgBtn")
        self.msg_btn.clicked.connect(self.expand_error)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseError")
        self.close_btn.clicked.connect(self.collapse_error)
        self.close_btn.hide()
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("LogView")
        self.log_view.hide()
        
        ov_layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignRight)
        ov_layout.addWidget(self.msg_btn, 1, Qt.AlignmentFlag.AlignCenter)
        ov_layout.addWidget(self.log_view)
    def burst_sparks(self):
        # Генерируем 20-30 искр в центре кнопки
        center_x, center_y = 250, 355 
        for _ in range(30):
            self.sparks.append(Spark(center_x, center_y))
    def set_status(self, text, color):
        """Удобный метод для обновления статуса"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"background: transparent; font-size: 14px; font-weight: bold; color: {color}; text-transform: uppercase; letter-spacing: 1.5px;")

    def get_active_services(self):
        services_tab = self.main_win.tabs.widget(1)
        active = []
        for i in range(services_tab.list_widget.count()):
            item = services_tab.list_widget.item(i)
            if item.isSelected():
                widget = services_tab.list_widget.itemWidget(item)
                active.append(widget.name)
        return active

    def toggle_state(self):
        t = LANGUAGES[self.main_win.current_lang] 
        active = self.get_active_services()
        if not active:
            # 1. Показываем уведомление
            self.toast = ToastNotification(self, t["toast_no_srv"])
            self.toast.show_toast()
            
            # 2. Создаем всплеск искр (без входа в режим системной ошибки)
            self.burst_sparks()
            
            # 3. Кратковременно подсвечиваем кнопку желтым (опционально)
            self.glow.setColor(QColor(241, 196, 15, 150))
            QTimer.singleShot(500, lambda: self.glow.setColor(QColor(0, 0, 0, 40)) if not self.is_running else None)
            return

        self.error_panel.hide()
        if self.is_running or self.is_err: 
            # Используем перевод для "stopping..."
            self.set_status(t["stop"], "#f39c12") 
            self.stop_services(active)
        else: 
            # Используем перевод для "start..."[cite: 3]
            self.set_status(t["start"], "#3498db") 
            self.start_services(active)
            self.set_status(t["running"], "#2ecc71") 

    def start_services(self, services):
        self.is_err = False
        self.worker = ServiceWorker(services, True)
        self.worker.finished.connect(self.on_start_finished)
        self.worker.start()
    def on_finished(self, ok, log):
        t = LANGUAGES[self.main_win.current_lang] #[cite: 3]
        if ok:
            if self.worker.start_mode:
                self.is_running, self.is_err = True, False
                self.glow.setColor(QColor(46, 204, 113, 200))
                # Вместо "запущено" пишем:[cite: 3]
                self.set_status(t["running"], "#2ecc71") 
            else:
                self.is_running, self.is_err = False, False
                self.glow.setColor(QColor(0, 0, 0, 40))
                # Вместо "остановлено" пишем:[cite: 3]
                self.set_status(t["stopped"], "#bdc3c7")
        else:
            self.is_running, self.is_err = False, True
            self.glow.setColor(QColor(231, 76, 60, 200))
            self.sparks = [Spark(250, 350) for _ in range(45)]
            self.log_view.setText(log)
            self.error_panel.show()
            self.set_status(t["error"], "#e74c3c")

    def stop_services(self, services):
        t = LANGUAGES[self.main_win.current_lang]
        for i in services:
            for j in CRITICAL_SERVICES:
                if j in i:
                    confirm = QMessageBox(self)
                    confirm.setIcon(QMessageBox.Icon.Warning)
                    confirm.setWindowTitle("Внимание: системная служба")
                    confirm.setText(f"Вы собираетесь остановить '{i}'.")
                    confirm.setInformativeText("Это жизненно важная служба. Хотите ли вы отключить её?")
                    confirm.setStyleSheet("""
                        QMessageBox { background-color: #f0f0f0; } 
                        QLabel { color: #333; }
                        QPushButton { padding: 5px 15px; }
                    """)     
                    yes_btn = confirm.addButton("Да, я уверен", QMessageBox.ButtonRole.YesRole)
                    no_btn = confirm.addButton("Нет, отменить", QMessageBox.ButtonRole.NoRole)
                    confirm.setDefaultButton(no_btn)
                    confirm.exec()
                    if confirm.clickedButton() == no_btn:
                        self.set_status(t["running"], "#2ecc71") 
                        return
                    else:
                        break
        self.is_running = self.is_err = False
        # Теперь статус меняется в toggle_state на "выключение", 
        # а в on_finished сменится на "остановлено"
        self.worker = ServiceWorker(services, False)
        self.worker.finished.connect(self.on_finished) # Не забудьте подключить сигнал
        self.worker.start()

    def on_start_finished(self, ok, log):
        if ok:
            self.is_running, self.is_err = True, False
            self.glow.setColor(QColor(46, 204, 113, 200))
            self.glow.setBlurRadius(60)
        else:
            self.is_running, self.is_err = False, True
            self.glow.setColor(QColor(231, 76, 60, 200))
            self.glow.setBlurRadius(60)
            self.sparks = [Spark(250, 350) for _ in range(45)]
            self.log_view.setText(log)
            self.error_panel.show()

    def update_animation(self):
        if self.is_running: self.bg_rot += 1.0
        elif self.is_err:
            self.bg_rot += random.randint(-4, 9)
            for s in self.sparks[:]:
                s.update()
                if s.life <= 0: self.sparks.remove(s)
        self.update()

    def expand_error(self):
        self.anim = QPropertyAnimation(self.error_panel, b"geometry")
        self.anim.setDuration(400)
        self.anim.setEndValue(QRect(20, 20, 460, 620))
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuint)
        self.anim.start()
        self.msg_btn.hide(); self.log_view.show(); self.close_btn.show()

    def collapse_error(self):
        self.anim = QPropertyAnimation(self.error_panel, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEndValue(QRect(50, 520, 400, 80)); self.anim.start()
        self.log_view.hide(); self.close_btn.hide(); self.msg_btn.show()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Получаем точный центр всей вкладки
        cx = self.width() / 2
        cy = self.height() / 2

        p.save()
        p.translate(cx, cy) # Переносим центр холста в центр окна
        p.rotate(self.bg_rot)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(235, 235, 235))
        
        # Рисуем лучи относительно нового центра (0,0)
        for _ in range(12):
            p.drawRect(-35, -250, 70, 500)
            p.rotate(30)
        
        p.drawEllipse(QPointF(0, 0), 200, 200)
        p.setBrush(QColor(248, 249, 250))
        p.drawEllipse(QPointF(0, 0), 90, 90)
        p.restore()
# --- ВКЛАДКА СПИСКА СЛУЖБ ---
class ServicesTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.bg_rot = 0
        # Включаем плавную прокрутку по пикселям вместо перескоков по элементам
        self.timer = QTimer(self); self.timer.timeout.connect(self.anim_bg); self.timer.start(16)
        layout = QVBoxLayout(self); layout.setContentsMargins(30, 30, 30, 100)
        self.list_widget = QListWidget(); self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            /* Сам список и его внутренняя область прокрутки */
            QListWidget, QListWidget::viewport { 
                background: transparent; 
                border: none; 
                outline: none; 
            }
            
            QListWidget::item { 
                background: white; 
                border-radius: 15px; 
                margin-bottom: 10px; 
                border: 1px solid #ddd; 
            }
            
            QListWidget::item:selected { 
                border: 2px solid #007AFF; 
                background: white; 
            }

            /* Полная прозрачность для всей дорожки скроллбара */
            QScrollBar:vertical {
                border: none;
                background: transparent; 
                width: 14px;
                margin: 0px;
            }

            /* Ползунок */
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 30px;
                border-radius: 4px;
                margin-left: 6px; /* Оставляем отступ только для самого ползунка */
            }

            QScrollBar::handle:vertical:hover {
                background: #AAAAAA;
            }

            /* Убираем все технические области фона скроллбара */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }
            QScrollArea {
                border: none;
                background-color: transparent; /* Фон самой области */
            }
        """)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        # Настраиваем скорость и плавность через объект прокрутки
        delta_scroll = self.list_widget.verticalScrollBar()
        delta_scroll.setSingleStep(1) # Шаг прокрутки в пикселях
        layout.addWidget(self.list_widget)
        self.plus_btn = QPushButton("+ Добавить службу", self)
        self.plus_btn.setObjectName("PlusBtn")
        self.plus_btn.clicked.connect(self.show_add_dialog)
        self.list_widget.itemSelectionChanged.connect(self.save_services) # Сохраняем при любом клике[cite: 1]
        self.load_services()
        self.refresh_plus_btn()
    def save_services(self):
        """Сохраняем имена и состояние выбора служб в JSON файл"""
        data_to_save = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                data_to_save.append({
                    "name": widget.name,
                    "selected": item.isSelected() # Сохраняем состояние выделения
                })
        
        try:
            with open(get_config_path(), 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_services(self):
        """Загружаем службы и их состояния при старте"""
        path = get_config_path()
        if not os.path.exists(path):
            return
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
                for item in services_data:
                    # Обработка как старого формата (строка), так и нового (словарь)
                    if isinstance(item, dict):
                        self.add_service_to_list(item["name"], item["selected"])
                    else:
                        self.add_service_to_list(item, True)
            self.refresh_plus_btn()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def add_service_to_list(self, name, selected=True):
        """Добавление виджета с учетом состояния выбора"""
        li = QListWidgetItem(self.list_widget)
        li.setSizeHint(QSize(0, 60))
        w = ServiceItemWidget(name)
        w.removed.connect(self.on_remove_service)
        self.list_widget.setItemWidget(li, w)
        li.setSelected(selected) # Устанавливаем сохраненное состояние
    def anim_bg(self): self.bg_rot += 0.3; self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save(); p.translate(self.width()/2, self.height()/2); p.rotate(self.bg_rot)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(242, 242, 242))
        for _ in range(12):
            p.drawRect(-35, -245, 70, 490); p.rotate(30)
        p.drawEllipse(QPointF(0, 0), 200, 200); p.setBrush(QColor(248, 249, 250)); p.drawEllipse(QPointF(0, 0), 90, 90); p.restore()

    def refresh_plus_btn(self):
        # Удаляем лишние отступы и фиксируем текст, чтобы не было "вить"
        t = LANGUAGES[self.main_win.current_lang]
        if self.list_widget.count() == 0:
            self.plus_btn.setText(t["add_btn"])
            self.plus_btn.setFixedSize(260, 60)
            self.plus_btn.move(120, 320)
            self.plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 30px; 
                    font-size: 16px; 
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover { background-color: #f2f2f2; }
            """)
        else:
            # Маленькая круглая кнопка
            self.plus_btn.setText("+")
            self.plus_btn.setFixedSize(70, 70)
            self.plus_btn.move(400, 560)
            self.plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 35px; 
                    font-size: 36px; 
                    font-weight: normal;
                    padding: 0px;
                    line-height: 70px;
                }
                QPushButton:hover { background-color: #f2f2f2; }
            """)

    def show_add_dialog(self):
        t = LANGUAGES[self.main_win.current_lang]
        from PyQt6.QtWidgets import QLineEdit  # Импорт локально или в начало файла

        powershell_cmd = (
            "$OutputEncoding = [System.Text.Encoding]::UTF8; "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "Get-Service | Select-Object DisplayName, Name | ConvertTo-Json"
        )
        
        try:
            res = subprocess.run(
                ["powershell", "-Command", powershell_cmd],
                capture_output=True,
                text=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=15
            )
            raw_output = res.stdout.decode('utf-8', errors='replace').strip()
            
            if not raw_output:
                names = ["Службы не найдены"]
            else:
                data = json.loads(raw_output)
                if isinstance(data, dict): data = [data]
                names = [f"{srv['DisplayName']} ({srv['Name']})" for srv in data]
        except Exception as e:
            names = [f"Ошибка: {str(e)}"]

        # Создание диалога
        d = QDialog(self)
        d.setWindowTitle(t["add_dialog_title"])
        d.setMinimumSize(450, 600)
        dl = QVBoxLayout(d)
        
        # Поле поиска
        search_bar = QLineEdit()
        search_bar.setPlaceholderText(t["search_placeholder"])
        search_bar.setFixedHeight(35)
        search_bar.setStyleSheet("""
            QLineEdit { 
                padding: 5px 10px; 
                border: 1px solid #ccc; 
                border-radius: 8px; 
                background: white; 
            }
        """)
        
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        lw.addItems(sorted(names))
        
        # Функция фильтрации
        def filter_list(text):
            for i in range(lw.count()):
                item = lw.item(i)
                # Скрываем элемент, если текст поиска не найден в названии (регистр игнорируется)
                item.setHidden(text.lower() not in item.text().lower())

        search_bar.textChanged.connect(filter_list)
        b = QPushButton(t["add_selected_btn"]) # Текст кнопки
        b.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: grey;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: dark-grey;
                background-color: grey;
            }
            QPushButton:pressed {
                color: dark-grey;
                background-color: grey;
            }
        """)
        b.setFixedHeight(40)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(d.accept)
        dl.addWidget(QLabel(t["search_label"])) # Лейбл поиска
        dl.addWidget(search_bar)
        dl.addWidget(lw)
        dl.addWidget(b)
        
        if d.exec():
            changes = False
            for item in lw.selectedItems():
                if not item.isHidden():
                    name = item.text()
                    exists = any(self.list_widget.itemWidget(self.list_widget.item(i)).name == name 
                                 for i in range(self.list_widget.count()))
                    
                    if not exists:
                        self.add_service_to_list(name) # Используем ваш готовый метод
                        changes = True
            
            if changes:
                self.refresh_plus_btn()
                # --- ДОБАВЛЕНО: Сохранение после добавления ---
                self.save_services()

    def on_remove_service(self, name):
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            if it and self.list_widget.itemWidget(it).name == name:
                self.list_widget.takeItem(i); break
        self.refresh_plus_btn()
        self.save_services()
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt
class SettingsTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.bg_rot = 0 
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        card_style = """
            QCheckBox {
                font-size: 16px;
                font-weight: 500;
                color: #2c3e50;
                background-color: #ffffff;
                border: 2px solid #dcdde1;
                border-radius: 15px;
                padding: 12px 20px;
                margin: 2px;
            }
            QCheckBox:checked {
                border-color: #007AFF;
                color: #3498db;
                background-color: #ffffff;
            }
            QCheckBox::indicator { width: 0px; height: 0px; }
        """

        self.app_auto = QCheckBox()
        self.app_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.app_auto.setStyleSheet(card_style)
        
        self.srv_auto = QCheckBox()
        self.srv_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.srv_auto.setStyleSheet(card_style)

        # Привязка событий
        self.app_auto.stateChanged.connect(self.handle_app_autostart)
        self.srv_auto.stateChanged.connect(self.save_settings)

        layout.addWidget(self.app_auto)
        layout.addWidget(self.srv_auto)
        layout.addStretch()
        # Загрузка сохраненных данных
        self.load_settings()

    def handle_app_autostart(self, state):
        is_checked = (state == 2)
        # 1. Включаем/выключаем второй чекбокс
        self.srv_auto.setEnabled(is_checked)
        if not is_checked:
            self.srv_auto.setChecked(False)
        
        # 2. Запись в реестр Windows
        set_autostart(is_checked)
        
        # 3. Сохранение в JSON
        self.save_settings()

    def save_settings(self):
        """Сохранение настроек в autostart.json"""
        data = {
            "launch_app": self.app_auto.isChecked(),
            "launch_services": self.srv_auto.isChecked()
        }
        try:
            with open(get_autostart_config_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения autostart.json: {e}")

    def load_settings(self):
        """Загрузка настроек из autostart.json"""
        path = get_autostart_config_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.app_auto.setChecked(data.get("launch_app", False))
                    self.srv_auto.setEnabled(self.app_auto.isChecked())
                    self.srv_auto.setChecked(data.get("launch_services", False))
            except Exception as e:
                print(f"Ошибка загрузки autostart.json: {e}")

    def update_animation(self):
        # Update the rotation value and trigger a repaint
        self.bg_rot += 0.3 
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save(); p.translate(self.width()/2, self.height()/2); p.rotate(self.bg_rot)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(242, 242, 242))
        for _ in range(12):
            p.drawRect(-35, -245, 70, 490); p.rotate(30)
        p.drawEllipse(QPointF(0, 0), 200, 200); p.setBrush(QColor(248, 249, 250)); p.drawEllipse(QPointF(0, 0), 90, 90); p.restore()

# --- ГЛАВНОЕ ОКНО ---
# --- ГЛАВНОЕ ОКНО ---
class HiddifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.setFixedSize(500, 710)
            self.setWindowTitle("Service Guard Pro")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "icon.ico")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"Файл иконки не найден по пути: {icon_path}")
            # --------------------------------
            # 1. Загружаем язык ПЕРЕД созданием интерфейса
            self.current_lang = self.load_language()
            
            # 2. Общие стили
            self.setStyleSheet("""
                QMainWindow, QWidget { 
                    background-color: #F8F9FA; 
                    font-family: 'Segoe UI'; 
                }
                QTabWidget::pane { border: none; }
                
                /* Стилизация полосы прокрутки */
                QScrollBar:vertical { 
                    border: none; 
                    background: transparent; 
                    width: 6px; /* Делаем её тонкой */
                    margin: 0px;
                }
                QScrollBar::handle:vertical { 
                    background: #CCCCCC; 
                    min-height: 20px; 
                    border-radius: 3px; /* Закругляем края */
                }
                QScrollBar::handle:vertical:hover { 
                    background: #AAAAAA; /* Темнеет при наведении */
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
                    height: 0px; /* Убираем стрелочки сверху и снизу */
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }

                /* Стили вкладок */
                QTabBar::tab { 
                    background: transparent; 
                    padding: 20px 45px; 
                    color: #bbb; 
                    font-weight: bold; 
                }
                QTabBar::tab:selected { 
                    color: #222; 
                    border-bottom: 3px solid #222; 
                }
                
                #ErrorPanel { background-color: white; border: 1px solid #ff4444; border-radius: 35px; }
                #LogView { border: none; background: #fffafa; border-radius: 15px; margin: 10px; }
            """)
            self.tabs = QTabWidget()
            self.act_tab = ActivationTab(self)
            self.srv_tab = ServicesTab(self)
            self.lang_tab = LanguagesTab(self)
            
            self.tabs.addTab(self.act_tab, "")
            self.tabs.addTab(self.srv_tab, "")
            self.tabs.addTab(self.lang_tab, "")
            self.setCentralWidget(self.tabs)

            # Создаем саму вкладку и добавляем её в QTabWidget
            self.sett_tab = SettingsTab(self)
            self.tabs.addTab(self.sett_tab, "SETTINGS")
            # 3. Инициализация вкладок

            # 4. Применяем тексты
            self.apply_styles()
            self.retranslate_ui()
            if self.sett_tab.srv_auto.isChecked():
                # Даем приложению секунду прогрузиться и запускаем службы
                QTimer.singleShot(1000, self.act_tab.toggle_state)
        except Exception as e:
            print(f"Критическая ошибка при запуске: {e}")

    def change_language(self, lang):
        try:
            self.current_lang = lang
            self.save_language(lang)
            self.retranslate_ui()
            self.lang_tab.refresh_list()
        except Exception as e:
            print(f"Ошибка при смене языка: {e}")

    def retranslate_ui(self):
        try:
            t = LANGUAGES[self.current_lang]
            # Перевод заголовков вкладок
            self.tabs.setTabText(0, t.get("main", "MAIN"))
            self.tabs.setTabText(1, t.get("services", "SERVICES"))
            self.tabs.setTabText(2, t.get("lang_tab", "LANGUAGES"))
            self.tabs.setTabText(3, t.get("settings_tab", "SETTINGS"))
            
            # Перевод текстов внутри вкладки настроек
            if hasattr(self, 'sett_tab'):
                self.sett_tab.app_auto.setText(t.get("sett_app_auto", "Auto-start App"))
                self.sett_tab.srv_auto.setText(t.get("sett_srv_auto", "Auto-start Services"))

            # Перевод текстов во вкладке активации
            if hasattr(self, 'act_tab'):
                self.act_tab.msg_btn.setText(t.get("see_err", "SEE ERROR"))
                status_text = t.get("stopped", "STOPPED")
                if self.act_tab.is_running: status_text = t.get("running", "RUNNING")
                elif self.act_tab.is_err: status_text = t.get("error", "ERROR")
                self.act_tab.set_status(status_text, "#bdc3c7" if not self.act_tab.is_running else "#2ecc71")
            
            if hasattr(self, 'srv_tab'):
                self.srv_tab.refresh_plus_btn()
                
        except Exception as e:
            print(f"Ошибка перевода: {e}")

    def save_language(self, lang):
        try:
            # Используем глобальную функцию get_config_path, но берем только папку
            config_file = get_config_path()
            settings_path = os.path.join(os.path.dirname(config_file), 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump({"lang": lang}, f)
        except Exception as e:
            print(f"Не удалось сохранить язык: {e}")

    def load_language(self):
        try:
            config_file = get_config_path()
            settings_path = os.path.join(os.path.dirname(config_file), 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("lang", "English")
        except:
            pass
        return "English"
    def toggle_settings(self):
        self.tabs.setCurrentIndex(2) # Переход на настройки
        self.update()
    def apply_styles(self):
        # Добавьте этот метод или вставьте содержимое в __init__
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #F8F9FA; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: transparent; padding: 15px 30px; color: #bbb; font-weight: bold; }
            QTabBar::tab:selected { color: #222; border-bottom: 3px solid #007AFF; }
            QPushButton#settings_btn { background: transparent; border: none; font-size: 28px; color: #888; }
        """)

    def draw_background_gear(self, painter):
        """Метод для отрисовки большой фоновой шестерни"""
        painter.save()
        
        # Цвет очень бледный (светло-серый), чтобы не мешать тексту
        gear_color = QColor(235, 235, 235, 100) 
        painter.setBrush(gear_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Центрируем шестерню на фоне
        painter.translate(self.width() / 2, self.height() / 2)
        
        # Рисуем зубцы большой шестерни
        for _ in range(12):
            painter.drawRect(-15, -120, 30, 240)
            painter.rotate(30)
        
        # Рисуем основной круг и вырез в центре
        painter.drawEllipse(QPointF(0, 0), 90, 90)
        painter.setBrush(QColor(248, 249, 250)) # Цвет фона окна
        painter.drawEllipse(QPointF(0, 0), 40, 40)
        
        painter.restore()
if __name__ == "__main__":
    # Фиксируем ID приложения (нужно для корректной работы UAC и иконок)
    myappid = 'service.guard.pro.v1'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    # Проверка прав администратора
    if not is_admin():
        # Получаем полный путь к текущему скрипту
        script = os.path.abspath(sys.argv[0])
        # Собираем аргументы, если они были
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # Вызов системного диалога UAC (запуск от имени администратора)
        # 'runas' — это стандартная команда Windows для повышения прав
        res = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script}" {params}', 
            None, 
            1
        )
        
        # Если пользователь нажал "Да", закрываем текущий процесс (откроется новый с правами)
        # Если "Нет" (res <= 32), программа просто закроется
        sys.exit(0)
    else:
        # Если права уже есть, запускаем интерфейс
        app = QApplication(sys.argv)
        try:
            ex = HiddifyApp()
            ex.show()
            sys.exit(app.exec())
        except Exception as e:
            # Выводим ошибку в консоль, чтобы понять, почему вылетело
            print(f"Критическая ошибка при работе: {e}")
            import traceback
            traceback.print_exc()
