import yaml
import sys
import os
from ssh_client import SSHClient
import paramiko

'''CLI: главный класс, который управляет пользовательским интерфейсом командной строки. 
Он отображает категории, команды и управляет SSH-сессиями.'''
class CLI:
    def __init__(self, commands):
        self.commands = commands
        self.ssh_client = None

    def load_login_data(self, file_path):
        '''Подгружает данные для подключения к SSH-серверу и возвращает их как кортеж.'''
        
        # Если приложение собрано с PyInstaller, используем _MEIPASS для поиска файла
        if getattr(sys, 'frozen', False):  
            file_path = os.path.join(sys._MEIPASS, file_path)  # Получаем путь к файлу в скомпилированной версии

        # Загружаем данные из YAML файла
        with open(file_path, "r") as file:
            login_data = yaml.safe_load(file)

        return (
            login_data["hostname"],
            login_data["port"],
            login_data["username"],
            login_data["password"],
            login_data["postfix"],
        )
    
    def extract_path(self, command):
        '''Извлекает путь из команды, начиная с ~ и заканчивая перед &&.'''
        if '~' in command:
            start_index = command.index('~')
            if '&&' in command:
                end_index = command.index('&&')
                return command[start_index:end_index].strip()
            else:
                return command[start_index:].strip()
        return None
    
    def get_prompt_from_path(self, command, username, postfix):
        """Генерирует prompt на основе команды, используя extract_path."""
        path = self.extract_path(command)
        return f"{username}@{postfix}:{path}$" if path else f"{username}@{postfix}:~/default$"

    def display_categories(self):
        '''Выводит доступные стенды.'''
        print("\nДоступные стенды:")
        for category in self.commands:
            print(f"- {category}")

    def display_commands(self, category):
        '''Выводит доступные команды в выбранной категории.'''
        print(f"\nВы выбрали стенд '{category}'. Доступные команды:")
        for cmd_name in self.commands[category]:
            print(f"- {cmd_name}")

    def start(self):
        hostname, port, username, password, postfix = self.load_login_data("login_data.yaml")
        try:
            self.ssh_client = SSHClient(hostname, port, username, password)
            self.ssh_client.initialize()

            print("Подключение установлено. Вы можете выполнять команды.")

            while True:
                self.display_categories()
                category_input = input("Введите категорию (или 'exit' для выхода): ").strip().lower()

                if category_input == "exit":
                    print("Завершаем работу.")
                    break

                if category_input in self.commands:
                    while True:  # Цикл для работы с командами внутри категории
                        self.display_commands(category_input)
                        command_input = input("Введите команду (или 'back' для возврата, 'exit' для выхода): ").strip().lower()
                        # Дебагаю стрелочки в nano
                        #if command_input == "cat -v":
                            #self.ssh_client.execute_command(command_input, "test")

                        if command_input == "back":  # Вернуться к выбору категории
                            break

                        if command_input == "exit":  # Завершить программу
                            print("Завершаем работу.")
                            return

                        if command_input in self.commands[category_input]:
                            command_to_execute = self.commands[category_input][command_input]

                            prompt = self.get_prompt_from_path(command_to_execute, username, postfix)

                            if command_input == "run script":
                                script_name = self.ssh_client.remove_control_sequences(input("Введите название скрипта: "))
                                command_to_execute = self.commands[category_input][command_input] + script_name
                            elif command_input in ["tail celery logs", "tail wsgi logs", "full celery logs", "full wsgi logs"]:
                                print("Выход из интерактивного режима: Ctrl + C")
                                log_choice = input("Выполнить с выборкой? ('y' с параметром, 'n' или 'пусто' без параметра): ")
                                if log_choice == "y":
                                    print("Пример вывода за исключением слова: -vw слово")
                                    print("Пример вывода только со словом: -i слово")
                                    log_param = self.ssh_client.remove_control_sequences(input("Введите параметр: "))
                                    if log_param == "":
                                        command_to_execute = self.commands[category_input][command_input]
                                    else:
                                        command_to_execute = self.commands[category_input][command_input] + " | grep " + log_param
                                else:
                                    command_to_execute = self.commands[category_input][command_input]
                            elif command_input in ["change settings", "change visual"]:
                                print("Выход из интерактивного режима: Ctrl + X")
                                tmp = input("Для продолжения нажмите Enter: ")
                            else:
                                command_to_execute = self.commands[category_input][command_input]
                            self.ssh_client.execute_command(command_to_execute, prompt)
                        else:
                            print("Неверная команда. Попробуйте снова.")
                else:
                    print("Неверная категория. Попробуйте снова.")
        except paramiko.AuthenticationException:
            print("Ошибка аутентификации. Проверьте логин или пароль.")
        except paramiko.SSHException as ssh_error:
            print(f"Ошибка SSH: {ssh_error}")
        except KeyboardInterrupt:
            print("\nПрограмма завершена пользователем.")
        except Exception as e:
            print(f"Общая ошибка: {e}")
        finally:
            if self.ssh_client:
                self.ssh_client.close()
            print("Соединение закрыто.")