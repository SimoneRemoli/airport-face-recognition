from realface.storage import load_database
from realface.vision import enroll_person, recognize_live


def print_realface_menu() -> None:
    print("\n***** Real Face Recognition *****")
    print("1. Register a new face from webcam")
    print("2. Start live recognition")
    print("3. List registered faces")
    print("0. Back")
    print("-------------------------------")


def list_faces() -> None:
    records = load_database()
    if not records:
        print("No registered faces yet.")
        return
    print("Registered faces:")
    for item in records:
        print(f"- {item['name']} [{item['sample_path']}]")


def run_realface_menu() -> None:
    while True:
        print_realface_menu()
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            return
        if choice == "1":
            name = input("Person name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            enroll_person(name)
            continue
        if choice == "2":
            recognize_live()
            continue
        if choice == "3":
            list_faces()
            continue
        print("Invalid choice. Please try again.")
