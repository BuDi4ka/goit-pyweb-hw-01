from collections import UserDict
from datetime import datetime, timedelta
import pickle
from abc import ABC, abstractmethod

commands = ['Hello - to start Bot',
                'Add - to add Contact',
                'Change - to change Contact',
                'Phone - to show Phone',
                'Add-Birthday - to add Birthday',
                'Show-Birthday - to show Birthday',
                'Show-Birthdays - to show all Birthdays',
                'All - to show Address Book']

class UserView(ABC):
    @abstractmethod
    def input(self, text):
        raise NotImplementedError
    @abstractmethod
    def show(self, text):
        raise NotImplementedError
    @abstractmethod
    def show_commands(self, commands):
        raise NotImplementedError

class Bot(UserView):
    def input(self, text):
        return input(text)
    def show(self, text):
        print(text)
    def show_commands(self, commands):
        for command in commands:
            print(command)


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            loaded = pickle.load(f)
            return loaded
    except FileNotFoundError:
        return AddressBook()
    except EOFError:
        print("The file is empty or corrupted, no data could be loaded.")


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError('Phone must be 10 digits')
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday_s):
        self.birthday = Birthday(birthday_s)

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in phone:
            if p.value == phone:
                self.phones.remove(p)
                return
            raise ValueError('Phone number not found')

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                self.phones.remove(p)
                self.add_phone(new_phone)
                return
            raise ValueError('Phone number not found')

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
            return None

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else 'Not set'
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        result = []
        for record in self.data.values():
            if record.birthday:
                bday_this_year = record.birthday.value.replace(year=today.year)
                if today <= bday_this_year <= next_week:
                    result.append({
                        "name": record.name.value,
                        "birthday": bday_this_year.strftime("%d.%m.%Y")
                    })
        return result

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError('Name not found')

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError as e:
            return str(e)
        except IndexError as e:
            return str(e)

    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_birthday(args, book: AddressBook):
    try:
        name, birthday = args
    except ValueError:
        raise ValueError('Give me name and birthday')
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f'Birthday added to contact - {name}'
    return 'Contact not found'


@input_error
def show_birthday(args, book: AddressBook):
    try:
        name = args[0]
    except ValueError:
        raise ValueError('Give me name')
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value.strftime("%d.%m.%Y")
    elif not record.birthday:
        return 'Birthday is not set'
    else:
        return 'Contact not found'


@input_error
def birthdays(book: AddressBook):
    next_birthday = book.get_upcoming_birthdays()
    if not next_birthday:
        return 'No birthdays will be in next 7 days'
    return f'Birthdays in next 7 days will be for\n{next_birthday}'


@input_error
def add_contact(args, book: AddressBook):
    try:
        name, phone = args
    except ValueError:
        raise ValueError('Give me name and phone')
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    try:
        name, old_phone, new_phone = args
    except ValueError:
        raise ValueError('Give me name, old phone and new phone')
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return 'Contact updated'
    else:
        return 'Contact not found'


@input_error
def show_phone(args, book: AddressBook):
    try:
        name = args[0]
    except ValueError:
        raise ValueError('Give me name')
    record = book.find(name)
    if record:
        return ",".join(p.value for p in record.phones)
    else:
        return 'Contact not found'


def show_all(book):
    return f'All contacts are \n{book}'


def main():
    book = AddressBook()
    book = load_data()
    user = Bot()
    user.show("Welcome to the assistant bot!")
    user.show_commands(commands)
    while True:
        try:
            user_input = user.input("Enter a command: ")
        except KeyboardInterrupt:
            raise SystemExit(0)
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            user.show("Good bye!")
            save_data(book)
            break
        elif command == "hello":
            user.show("How can I help you?")
        elif command == "add":
            user.show(add_contact(args, book))
        elif command == "change":
            user.show(change_contact(args, book))
        elif command == "phone":
            user.show(show_phone(args, book))
        elif command == "all":
            user.show(show_all(book))
        elif command == "add-birthday":
            user.show(add_birthday(args, book))
        elif command == "show-birthday":
            user.show(show_birthday(args, book))
        elif command == "birthdays":
            user.show(birthdays(book))
        else:
            user.show("Invalid command.")


if __name__ == "__main__":
    main()