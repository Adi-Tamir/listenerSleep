from abc import ABC, abstractmethod

from Observer import Observer

# python openBCI gui logic from:
# https://github.com/andreaortuno/Plotting_OpenBCI_Cyton_Data_live/blob/master/Plotting%20live%20data%20with%20Cyton%20with%20pyqtgraph.ipynb

class Subject(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass