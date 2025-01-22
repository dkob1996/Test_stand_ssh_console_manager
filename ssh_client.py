import paramiko
import sys
import termios
import tty
import select
import logging


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

    def execute_command(self, command, prompt):
        '''Открывает интерактивную сессию.'''
        channel = self.client.invoke_shell(term='xterm')
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
                    
                    if input_data == "\x1b":  # Если это начало ESC-последовательности
                        # Считываем оставшиеся символы ESC-последовательности
                        input_data += sys.stdin.read(2)

                    self.logger.debug(f"Отправлено на сервер: {repr(input_data)}")
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
