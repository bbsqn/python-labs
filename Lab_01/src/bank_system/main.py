import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_system.config import CURRENCY
from bank_system.exceptions import BankError
from bank_system.models import Account
from bank_system.services import (
    calculate_average_balance,
    calculate_total_funds,
    deposit,
    find_account,
    find_accounts_by_client,
    find_richest_client,
    sort_by_balance,
    withdraw,
)


def create_demo_accounts() -> list[Account]:
    return [
        Account("UA100001", "Олена Ткаченко", 15230.50),
        Account("UA100002", "Іван Петренко", 4800.00),
        Account("UA100003", "Марія Коваль", 980.75),
        Account("UA100004", "Олена Ткаченко", 250.00),
    ]


def print_accounts(accounts: list[Account]) -> None:
    if not accounts:
        print("Рахунків не знайдено.")
        return
    print(f"\n{'Номер':12}{'Клієнт':22}{'Баланс':>14}")
    for account in accounts:
        print(
            f"{account.account_number:12}"
            f"{account.client_name:22}"
            f"{account.balance:>10.2f} {CURRENCY}"
        )


def read_amount(prompt: str) -> float:
    while True:
        raw_value = input(prompt).strip().replace(",", ".")
        try:
            return float(raw_value)
        except ValueError:
            print("Некоректне число. Спробуйте ще раз.")


def print_menu() -> None:
    print("\n--- Система банківських рахунків ---")
    print("1. Показати всі рахунки")
    print("2. Поповнити рахунок")
    print("3. Зняти кошти")
    print("4. Перевірити баланс")
    print("5. Знайти рахунок(и)")
    print("6. Загальна сума коштів банку")
    print("7. Рахунки, відсортовані за балансом")
    print("8. Найбагатший клієнт")
    print("9. Вийти")


def run_menu(accounts: list[Account]) -> None:
    while True:
        print_menu()
        command = input("Оберіть команду: ").strip()

        if command == "1":
            print_accounts(accounts)

        elif command == "2":
            number = input("Номер рахунку: ").strip()
            account = find_account(accounts, number)
            if account is None:
                print("Рахунок не знайдено.")
                continue
            amount = read_amount("Сума поповнення: ")
            try:
                deposit(account, amount)
                print(f"Новий баланс: {account.balance:.2f} {CURRENCY}")
            except BankError as error:
                print(f"Помилка: {error}")

        elif command == "3":
            number = input("Номер рахунку: ").strip()
            account = find_account(accounts, number)
            if account is None:
                print("Рахунок не знайдено.")
                continue
            amount = read_amount("Сума списання: ")
            try:
                withdraw(account, amount)
                print(f"Новий баланс: {account.balance:.2f} {CURRENCY}")
            except BankError as error:
                print(f"Помилка: {error}")

        elif command == "4":
            number = input("Номер рахунку: ").strip()
            account = find_account(accounts, number)
            if account is None:
                print("Рахунок не знайдено.")
            else:
                print(f"Баланс рахунку {number}: {account.balance:.2f} {CURRENCY}")

        elif command == "5":
            query = input("Ім'я клієнта або номер рахунку: ").strip()
            by_number = find_account(accounts, query)
            results = (
                [by_number] if by_number is not None
                else find_accounts_by_client(accounts, query)
            )
            print_accounts(results)

        elif command == "6":
            total = calculate_total_funds(accounts)
            average = calculate_average_balance(accounts)
            print(f"Загальна сума коштів: {total:.2f} {CURRENCY}")
            print(f"Середній баланс: {average:.2f} {CURRENCY}")

        elif command == "7":
            print_accounts(sort_by_balance(accounts))

        elif command == "8":
            richest = find_richest_client(accounts)
            if richest is not None:
                print(
                    "Найбагатший клієнт:",
                    richest.client_name,
                    f"({richest.balance:.2f} {CURRENCY})",
                )

        elif command == "9":
            print("До побачення.")
            break

        else:
            print("Невідома команда. Спробуйте ще раз.")


def main() -> None:
    accounts = create_demo_accounts()
    print("Демонстраційні дані завантажено.")
    run_menu(accounts)


if __name__ == "__main__":
    main()