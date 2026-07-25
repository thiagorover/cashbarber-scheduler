
# Class for custom exceptions related to booking operations
class BookingError(Exception):
    """Base class for booking-related exceptions."""

    def __init__(self, log_message: str, user_message: str = None):
        # Initialize the BookingError with log and user messages.
        super().__init__(log_message)
        self.log_message = log_message
        self.user_message = user_message


class LoginError(BookingError):
    """Raised when there is a login error."""
    pass

class BarberNotFoundError(BookingError):
    """Raised when the specified barber is not found."""
    pass

class AppointmentError(BookingError):
    """Raised when there is an error related to appointment booking."""
    pass

