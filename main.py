import threading
import time
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import escape_markup


APP_NAME = "LightNet Tarkwa"

# Enter your existing ntfy topic when the app opens.
NTFY_SERVER = "https://ntfy.sh/"


class LightNetApp(App):

    def build(self):
        self.title = APP_NAME
        self.topic = ""
        self.last_id = ""
        self.running = True

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        title = Label(
            text="[b]LightNet Tarkwa[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(48),
            font_size="23sp"
        )
        root.add_widget(title)

        self.topic_input = TextInput(
            hint_text="Enter your shared ntfy topic",
            multiline=False,
            size_hint_y=None,
            height=dp(48)
        )
        root.add_widget(self.topic_input)

        connect_button = Button(
            text="Connect to Chat",
            size_hint_y=None,
            height=dp(48)
        )
        connect_button.bind(on_press=self.connect_chat)
        root.add_widget(connect_button)

        self.status = Label(
            text="Enter your topic to connect.",
            size_hint_y=None,
            height=dp(35)
        )
        root.add_widget(self.status)

        self.scroll = ScrollView()

        self.chat = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(5)
        )
        self.chat.bind(
            minimum_height=self.chat.setter("height")
        )

        self.scroll.add_widget(self.chat)
        root.add_widget(self.scroll)

        bottom = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(6)
        )

        self.message_input = TextInput(
            hint_text="Write a message...",
            multiline=False
        )
        self.message_input.bind(
            on_text_validate=self.send_message
        )

        send_button = Button(
            text="Send",
            size_hint_x=None,
            width=dp(85)
        )
        send_button.bind(on_press=self.send_message)

        bottom.add_widget(self.message_input)
        bottom.add_widget(send_button)

        root.add_widget(bottom)

        return root

    def add_message(self, sender, message):
        safe_sender = escape_markup(sender)
        safe_message = escape_markup(message)

        label = Label(
            text=f"[b]{safe_sender}[/b]\n{safe_message}",
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="middle"
        )

        label.bind(
            width=lambda obj, width: setattr(
                obj, "text_size", (width - dp(12), None)
            )
        )
        label.bind(
            texture_size=lambda obj, size: setattr(
                obj, "height", size[1] + dp(18)
            )
        )

        self.chat.add_widget(label)
        Clock.schedule_once(
            lambda dt: setattr(
                self.scroll, "scroll_y", 0
            ),
            0.1
        )

    def connect_chat(self, instance):
        topic = self.topic_input.text.strip()

        if not topic:
            self.status.text = "Enter your shared topic first."
            return

        if "/" in topic or " " in topic:
            self.status.text = "Please enter only the topic name."
            return

        self.topic = topic
        self.last_id = ""
        self.status.text = "Connecting..."

        self.add_message(
            "LightNet",
            "Connecting to the messaging service..."
        )

        threading.Thread(
            target=self.listen,
            daemon=True
        ).start()

    def listen(self):
        url = NTFY_SERVER + self.topic + "/json"

        while self.running:
            try:
                response = requests.get(
                    url,
                    params={"poll": "1", "since": "all"},
                    timeout=35
                )

                if response.ok:
                    for line in response.text.splitlines():
                        try:
                            data = __import__("json").loads(line)

                            if data.get("event") != "message":
                                continue

                            message_id = data.get("id", "")

                            if message_id and message_id == self.last_id:
                                continue

                            if message_id:
                                self.last_id = message_id

                            message = data.get("message", "")

                            Clock.schedule_once(
                                lambda dt, m=message:
                                self.add_message("Family", m)
                            )

                        except (ValueError, TypeError):
                            continue

                    Clock.schedule_once(
                        lambda dt: setattr(
                            self.status, "text", "Connected"
                        )
                    )

                else:
                    Clock.schedule_once(
                        lambda dt: setattr(
                            self.status, "text",
                            f"Service response: {response.status_code}"
                        )
                    )

            except requests.RequestException:
                Clock.schedule_once(
                    lambda dt: setattr(
                        self.status, "text",
                        "Connection problem. Retrying..."
                    )
                )
                time.sleep(3)

    def send_message(self, instance):
        message = self.message_input.text.strip()

        if not self.topic:
            self.status.text = "Connect to your chat first."
            return

        if not message:
            return

        self.message_input.text = ""

        threading.Thread(
            target=self.post_message,
            args=(message,),
            daemon=True
        ).start()

    def post_message(self, message):
        try:
            response = requests.post(
                NTFY_SERVER + self.topic,
                data=message.encode("utf-8"),
                timeout=15
            )

            if response.ok:
                Clock.schedule_once(
                    lambda dt, m=message:
                    self.add_message("You", m)
                )
                Clock.schedule_once(
                    lambda dt: setattr(
                        self.status, "text", "Message sent"
                    )
                )
            else:
                Clock.schedule_once(
                    lambda dt: setattr(
                        self.status, "text",
                        f"Send failed: {response.status_code}"
                    )
                )

        except requests.RequestException:
            Clock.schedule_once(
                lambda dt: setattr(
                    self.status, "text",
                    "Could not send. Check your internet."
                )
            )

    def on_stop(self):
        self.running = False


if __name__ == "__main__":
    LightNetApp().run()
