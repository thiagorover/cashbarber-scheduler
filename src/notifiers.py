

from abc import ABC, abstractmethod


# Define a class abstract base for notification services
class Notifier(ABC):

    """
    Class abstract base for notification services.
    Demonstrates the use of abstract classes and methods.
    """

    # Method abstract to be implemented by subclasses
    @abstractmethod
    def notify(self, message: str):
        """Abstract method to send a notification with the given message."""
        pass




