import paramiko
import sys
import termios
import tty
import select
import logging
import os
import re


class SSHClient:
    def __init__(self, hostname, port, username, password, enable_logging=False):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None

        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        if enable_logging:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - %(message)s"
            )
        else:
            logging.basicConfig(level=logging.CRITICAL)  # Отключить логирование (показываются только критические ошибки)

    def initialize(self):
        '''Создает и настраивает SSH-клиент.'''
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.hostname, port=self.port, username=self.username, password=self.password)
        self.logger.info("SSH-соединение успешно установлено.")

    def close(self):
        '''Закрывает SSH-соединение.'''
        if self.client:
            self.client.close()
            self.logger.info("SSH-соединение закрыто.")
    
    def remove_control_sequences(self, text):
        '''Удаляет управляющие последовательности из текста'''
        # Это регулярное выражение удаляет escape-символы и управляющие последовательности, такие как ^[[200~ и ^[[201~
        control_sequence_pattern = r'\x1b\[[0-9;]*[A-Za-z]'
        if re.search(control_sequence_pattern, text):
            return re.sub(control_sequence_pattern, '', text)
        return text
    
    def write_to_file(self, data):
        """
        Записывает данные в указанный файл.

        :param file_path: Путь к файлу, в который будут записаны данные.
        :param data: Данные, которые нужно записать в файл (строка).
        """
        file_path = "logs.txt"
        try:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(data + '\n')
            self.logger.debug(f"Данные успешно записаны в файл: {file_path}")
        except Exception as e:
            self.logger.warning(f"Ошибка при записи в файл: {e}")

    def get_terminal_size(self):
        """Получает размеры терминала из текущего окна."""
        try:
            # Получаем размер терминала с помощью команды stty
            size = os.popen('stty size', 'r').read().split()
            height = int(size[0])
            width = int(size[1])
            return height, width
        except Exception as e:
            self.logger.error(f"Ошибка при получении размера терминала: {e}")
            return 24, 80  # Возвращаем стандартные размеры, если не удалось получить


    def execute_command(self, command, prompt):
        '''Открывает интерактивную сессию.'''
        height, width = self.get_terminal_size() # Проблема 1: дает подстроить размер окна только при запуске сессии
        channel = self.client.invoke_shell(term='xterm', width=width, height=height)
        channel.send(command + "\n")
        self.logger.info(f"Отправлена команда: {command}")

        old_tty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin)
            channel.settimeout(0.0)

            while True:
                if channel.recv_ready():
                    output = channel.recv(1024).decode("utf-8", errors="ignore")
                    self.logger.debug(f"Получено от сервера: {repr(output)}")
                    sys.stdout.write(output)
                    sys.stdout.flush()
                    if prompt in output:
                            channel.send("exit\n")
                            break

                if channel.recv_stderr_ready():
                    error_output = channel.recv_stderr(1024).decode("utf-8", errors="ignore")
                    self.logger.error(f"Получена ошибка от сервера: {repr(error_output)}")
                    sys.stderr.write(error_output)
                    sys.stderr.flush()

                if channel.exit_status_ready():
                    break

                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    input_data = sys.stdin.read(1)
                    
                    if input_data == "\x1b":
                        input_data += sys.stdin.read(2)
                        if input_data == '\x1b[2':
                            input_data += sys.stdin.read(3)
                            if input_data in ('\x1b[200~', '\x1b[201~'):
                                pass
                        elif input_data in ('\x1bOC', '\x1bOB', '\x1bOA', '\x1bOD'):
                            channel.send(input_data)

                    else:
                        channel.send(input_data)

            exit_status = channel.recv_exit_status()
            self.logger.info(f"Сессия завершена с кодом: {exit_status}")
        except Exception as e:
            self.logger.error(f"Ошибка при работе с сессией: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            try:
                channel.close()
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии канала: {e}")
