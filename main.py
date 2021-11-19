from __future__ import annotations
import sys

from ConcreteObserver import ConcreteObserver
from ConcreteSubject import ConcreteSubject

sys.path.append('C:/Users/oren_/AppData/Local/Programs/Python/Python310/Lib/site-packages')
if __name__ == "__main__":
    # The client code.
    subject = ConcreteSubject()

    observer_a = ConcreteObserver()
    subject.attach(observer_a)

    subject.some_business_logic()
