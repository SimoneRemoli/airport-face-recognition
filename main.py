from realface.app import run_realface_menu


def display_main_menu():
    print("***** Airport Face Recognition *****")
    print("1. Start real face recognition")
    print("0. Exit")
    print("-------------------------------\n")


def main():
    while True:
        display_main_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            print("Quitting...")
            break
        if choice == "1":
            run_realface_menu()
            continue
        print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
