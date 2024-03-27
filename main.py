import dearpygui.dearpygui as dpg
import win32con
import win32gui
import numpy as np
import win32ui
import easyocr
from pynput import keyboard
import json

with open('data.json', 'r', encoding="UTF8") as r:
    data = [json.load(r)]


class Item:

    def __init__(self, raw_text):
        self.coef = 100
        self.stats = []

        scan_for_stats = False
        for tuple in raw_text:
            for rune in data[0]:
                if not scan_for_stats and tuple[1] == "Effets":
                    scan_for_stats = True
                if scan_for_stats and tuple[1] == "Conditions" or "Catégorie" in tuple[1]:
                    scan_for_stats = False
                if scan_for_stats and rune in tuple[1]:
                    try:
                        self.stats.append({"name": rune, "rune": data[0][rune],
                                           "amount": int(''.join(x for x in tuple[1] if x.isdigit()))})
                    except:
                        self.stats.append({"name": rune, "rune": data[0][rune], "amount": 1})
                elif "Niveau" in tuple[1]:
                    try:
                        self.level = int(''.join(x for x in tuple[1] if x.isdigit()))
                    except:
                        self.level = 1
                    self.name = raw_text[raw_text.index(tuple) - 1][1]

        with dpg.window(label=self.name, autosize=True):
            dpg.add_input_int(label="Coef", default_value=self.coef, max_value=100000, step=0, step_fast=0, width=50,
                              callback=self.changeStat)
            dpg.add_input_int(label="Niveau", default_value=self.level, min_value=1, max_value=200, step=0, step_fast=0,
                              width=50, callback=self.changeStat)
            for stat in self.stats:
                dpg.add_input_int(label=stat["name"], default_value=stat["amount"], min_value=0, max_value=100000,
                                  step=0, step_fast=0, width=50, callback=self.changeStat)
            dpg.add_button(label="Calculer le profit", callback=self.calculateProfit)
            self.profit_text = dpg.add_text("Profit : ")
            self.focus_profit_text = dpg.add_text("Profit avec focus Aucun : ")

    def changeStat(self, sender, app_data):
        if dpg.get_item_label(sender) == "Coef":
            self.coef = app_data
            return
        elif dpg.get_item_label(sender) == "Niveau":
            self.level = app_data
            return
        for stat in self.stats:
            if dpg.get_item_label(sender) == stat["name"]:
                stat["amoun"] = app_data

    def calculateProfit(self, sender, app_data):
        profits = []
        pdb = 0
        total_profit = 0
        best_profit_focus = {"name": "", "profit": 0}
        for stat in self.stats:
            pdb += 3 * stat["amount"] * stat["rune"]["poid"] * self.level / 200 + 1
            profits.append(
                (3 * stat["amount"] * stat["rune"]["poid"] * self.level / 200 + 1) / stat["rune"]["densite"] *
                stat["rune"]["prix"])
        for profit in profits:
            total_profit += profit
        for stat in self.stats:
            focus_profit = ((3 * stat["amount"] * stat["rune"]["poid"] * self.level / 200 + 1) / stat["rune"][
                "densite"] + (pdb - (3 * stat["amount"] * stat["rune"]["poid"] * self.level / 200 + 1)) / 2 /
                            stat["rune"]["densite"]) * stat["rune"]["prix"]
            if focus_profit > best_profit_focus["profit"]:
                best_profit_focus = {"name": stat["name"], "profit": focus_profit}
        dpg.set_value(self.profit_text, "Profit : " + str(total_profit * (self.coef / 100)))
        dpg.set_value(self.focus_profit_text,
                      "Profit avec focus " + best_profit_focus["name"] + " : " + str(
                          best_profit_focus["profit"] * (self.coef / 100)))


scan_item = False
scan_price = False


def on_press(key):
    global scan_item, scan_price

    if key == keyboard.Key.f1:
        scan_item = True

    if key == keyboard.Key.f3:
        scan_price = True


listener = keyboard.Listener(on_press=on_press)
listener.start()  # start to listen on a separate thread

dpg.create_context()
dpg.create_viewport(title='Calculateur Brisage', width=600, height=300)

running = False


def get_screenshot(window_handler, width, height):
    wDC = win32gui.GetWindowDC(window_handle)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (width, height), dcObj, (8, 30), win32con.SRCCOPY)

    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4)

    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(window_handler, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())

    img = img[..., :3]

    img = np.ascontiguousarray(img)

    return img


def start_stop_callback(sender, app_data):
    global running

    if running:
        running = False
        dpg.set_item_label(sender, "Start")
    else:
        running = True
        dpg.set_item_label(sender, "Stop")


def update_prices(raw_text):
    for tuple in raw_text:
        for stat in data[0]:
            if "Rune " + data[0][stat]["runes"] == tuple[1]:
                if raw_text[raw_text.index(tuple) + 2][2] > 0.90:
                    data[0][stat]["prix"] = int(''.join(x for x in (raw_text[raw_text.index(tuple) + 3][1]) if x.isdigit()))
                else:
                    data[0][stat]["prix"] = int(''.join(x for x in (raw_text[raw_text.index(tuple) + 2][1]) if x.isdigit()))

    with open('data.json', 'w', encoding="UTF8") as w:
        json.dump(data[0], w, ensure_ascii=False)


with dpg.window(label="Example Window"):
    dpg.add_text("Hello, world")
    dpg.add_button(label="Start", callback=start_stop_callback, tag="start_stop_button")

dpg.setup_dearpygui()
dpg.show_viewport()

window_handle = win32gui.FindWindow("ApolloRuntimeContentWindow", None)
window_rect = win32gui.GetWindowRect(window_handle)
reader = easyocr.Reader(['fr'], gpu=True)

items = []
while dpg.is_dearpygui_running():
    if running and win32gui.IsWindowVisible(window_handle):
        if window_rect != win32gui.GetWindowRect(window_handle):
            window_rect = win32gui.GetWindowRect(window_handle)
        screenshot = get_screenshot(window_handle, (window_rect[2] - window_rect[0] - 16),
                                    (window_rect[3] - window_rect[1] - 38))
        if scan_item:
            text_ = reader.readtext(screenshot)
            items.append(Item(text_))
            scan_item = False

        if scan_price:
            text_ = reader.readtext(screenshot)
            update_prices(text_)
            scan_price = False
        # cv.imshow('Computer Vision', screenshot)
    elif running and not win32gui.IsWindowVisible(window_handle):
        window_handle = win32gui.FindWindow("ApolloRuntimeContentWindow", None)
    dpg.render_dearpygui_frame()

dpg.destroy_context()
