from cli import CLI
from command_loader import CommandLoader

def main():
    commands = CommandLoader.load_commands("commands.yaml")
    cli = CLI(commands)
    cli.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")