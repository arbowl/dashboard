"""Dashboard

This is a simple web app for personal use that displays on a coffee stand in my
apartment. It runs on a Raspberry Pi 3B+ and outputs to an old screen via HDMI.

It requires an .env file with the following fields:
- ZIP
- WEATHER_API
- <user 1>_USERNAME
- <user 1>_PASSWORD
- <user 2>_USERNAME
- <user 2>_PASSWORD

For <user 1>/<user 2>, their name must be in the "USERS" list.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime
from enum import Enum
from os import getenv, getcwd
from os.path import join
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from matplotlib.axes import Axes
import matplotlib.pyplot as plt  # type: ignore
from numpy import array as nparray
from numpy import pi, inf
from requests import get
from whoop import WhoopClient

load_dotenv()

app = Flask(__name__)


USERS = ["Drew"]
ZIP = getenv("ZIP")
START_RGB = "#FF0000"
CROSS_RGB = "#FFFF00"
FINAL_RGB = "#06B025"


class Key(str, Enum):
    """Variables for WHOOP's JSON returns"""

    ID = "id"
    SCORE = "score"
    RECOVERY = "recovery_score"
    SLEEP = "sleep_performance_percentage"
    STRAIN = "strain"


class WhoopUser:
    """API for WHOOP statistics"""

    debug = False

    def __init__(self, name_of_person: str) -> None:
        self.name = name_of_person
        username = getenv(f"{name_of_person.upper()}_USERNAME", "")
        password = getenv(f"{name_of_person.upper()}_PASSWORD", "")
        self.client = WhoopClient(username, password)
        self.sleep: Optional[int] = None
        self.strain: Optional[float] = None
        self.recovery: Optional[int] = None
        self._today: Optional[str] = None

    def __enter__(self) -> WhoopUser:
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.client.close()

    @property
    def today(self) -> str:
        """Returns today's date; refreshes scores once per day"""
        today = date.today().strftime("%Y-%m-%d")
        if self._today != today:
            self.sleep = None
            self.strain = None
            self.recovery = None
            self._today = today
        return today

    @property
    def data(self) -> dict[str, str]:
        """Returns a JSON containing the user data"""
        return {
            "name": self.name,
            "sleepImage": f"http://{request.host}/static/img/{self.name.lower()}"\
            "_sleep.png",
            "recoveryImage": f"http://{request.host}/static/img/{self.name.lower()}"\
            "_recovery.png",
        }

    def get_recovery(self) -> int:
        """Returns the user's current recovery"""
        if self.recovery is not None:
            return self.recovery
        cycle_id = self.client.get_cycle_collection(self.today, self.today)[0][Key.ID]
        recovery_json = self.client.get_recovery_for_cycle(cycle_id)
        recovery = int(recovery_json[Key.SCORE][Key.RECOVERY])
        if self.debug:
            print(f"{self.name}'s Recovery: {recovery}%")
        self._generate_circle_image("Recovery", recovery, 33)
        self.recovery = recovery
        return recovery

    def get_sleep(self) -> int:
        """Returns the user's last sleep score"""
        if self.sleep is not None:
            return self.sleep
        sleep = int(
            self.client.get_sleep_collection(self.today, self.today)[0][Key.SCORE][
                Key.SLEEP
            ]
        )
        if self.debug:
            print(f"{self.name}'s Sleep: {sleep}%")
        self._generate_circle_image("Sleep", sleep, 70)
        self.sleep = sleep
        return sleep

    def get_strain(self) -> float:
        """Returns the user's current strain"""
        if self.strain is not None:
            return self.strain
        strain = round(
            self.client.get_cycle_collection(self.today, self.today)[0][Key.SCORE][
                Key.STRAIN
            ],
            1,
        )
        if self.debug:
            print(f"{self.name}'s Strain: {strain}")
        self.strain = strain
        return strain

    def _generate_circle_image(
        self, title: str, data: float, midpoint: int = 50
    ) -> None:
        """Creates a PNG of a progress bar"""
        if data <= midpoint:
            fraction = max((data - midpoint) / (100 - midpoint), 0)
            start_rgb = nparray([int(START_RGB[i : i + 2], 16) for i in (1, 3, 5)])
            middle_rgb = nparray([int(CROSS_RGB[i : i + 2], 16) for i in (1, 3, 5)])
            rgb = (start_rgb + fraction * (middle_rgb - start_rgb)).astype(int)
        else:
            fraction = max((data - midpoint) / (100 - midpoint), 0)
            middle_rgb = nparray([int(CROSS_RGB[i : i + 2], 16) for i in (1, 3, 5)])
            end_rgb = nparray([int(FINAL_RGB[i : i + 2], 16) for i in (1, 3, 5)])
            rgb = (middle_rgb + fraction * (end_rgb - middle_rgb)).astype(int)
        color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        xs_data = (data * pi * 2) / 100 if data > 2 else 100
        left = (90 * pi * 2) / 360
        axis: Axes
        fig, axis = plt.subplots(figsize=(4, 4), subplot_kw={"projection": "polar"})
        axis.barh(1, xs_data, left=left, height=0.25, color=color)
        axis.scatter(xs_data + left, 1, s=0, color=color, zorder=2)
        axis.scatter(left, 1, s=0, color=color, zorder=2)
        axis.grid(False)
        axis.spines["polar"].set_visible(False)
        axis.set_yticklabels([])
        axis.set_xticklabels([])
        axis.text(
            0,
            0,
            f"{int(data)}%",
            ha="center",
            va="center",
            fontsize=30,
            color="#222222",
        )
        axis.set_xlabel(title, fontsize=30, color="#222222")
        fig.subplots_adjust(bottom=0.2)
        fig.savefig(
            f"{join(
                getcwd(),
                'static',
                'img',
                '_'.join([self.name.casefold(), title.lower()])
            )}.png",
            transparent=True,
        )


@app.route("/")
def index() -> str:
    """Homepage"""
    return render_template("index.html")


@app.route("/weather")
def get_weather():
    """Returns weather requests"""
    key = getenv("WEATHER_API")
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    url = f"{base_url}?zip={ZIP},us&appid={key}&units=imperial"
    weather = get(url, timeout=5)
    weather.raise_for_status()
    data = weather.json()
    forecast = []
    descriptions = []
    hi, lo = -math.inf, math.inf
    # 5 day forecast with 3 hour intervals = 8 intervals per day
    for i in range(0, 5 * 8):
        timestamp = data["list"][i]["dt"]
        day_of_week = datetime.fromtimestamp(timestamp).strftime("%A")
        weather_description = data["list"][i]["weather"][0]["description"]
        low_temp = data["list"][i]["main"]["temp_min"]
        high_temp = data["list"][i]["main"]["temp_max"]
        icon = data["list"][i]["weather"][0]["icon"]
        lo = min(lo, low_temp)
        hi = max(hi, high_temp)
        descriptions.append(weather_description)
        if (i + 1) % 8 == 0:
            midday_description = descriptions[4]
            forecast.append(
                {
                    "date": day_of_week,
                    "description": midday_description.title(),
                    "low_temp": f"{round(lo)}°F",
                    "high_temp": f"{round(hi)}°F",
                    "icon_code": icon,
                }
            )
            hi, lo = -math.inf, math.inf
            descriptions = []
    return jsonify(forecast)


@app.route("/comparison")
def comparison() -> dict:
    """Returns WHOOP comparison data"""
    json_data = [user.data for user in clients]
    return jsonify(json_data)


@app.route("/tasks")
def show_tasks() -> dict:
    """Returns tasks from the local server"""
    tasks: list[str] = []
    response = get("http://192.168.0.156:5000/retrieve", timeout=5)
    if response.status_code == 200:
        task_data = response.json()
        for task in task_data:
            tasks.append([task[1], task[2]])
    task_list = []
    for task_to_add in tasks[:6]:
        date_translate = datetime.strptime(task_to_add[1], "%d-%m-%Y %H:%M:%S")
        date_translate = date_translate.strftime("%B %d, %Y")
        task_list.append(
            {
                "task": task_to_add[0],
                "date": date_translate,
            }
        )
    return jsonify(task_list)


if __name__ == "__main__":
    clients: list[WhoopUser] = []
    for name in USERS:
        with WhoopUser(name) as client:
            client.get_sleep()
            client.get_recovery()
            clients.append(client)
    with suppress(SystemExit):
        app.run(host="0.0.0.0", port=8000, debug=True, load_dotenv=True)
