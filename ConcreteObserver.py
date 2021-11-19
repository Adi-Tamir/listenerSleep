from Observer import Observer
from playsound import playsound


class ConcreteObserver(Observer):

    def update(self) -> None:
            print("Trigger: User is about to fall asleep")
            playsound('audio.mp3')
