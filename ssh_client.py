import paramiko
import sys
import termios
import tty
import select


'''SSHClient: класс для управления SSH-соединением, включая методы для инициализации соединения и выполнения команд.'''
class SSHClient:
    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None

    def initialize(self):
        '''Создает и настраивает SSH-клиент.'''
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.hostname, port=self.port, username=self.username, password=self.password)

    def close(self):
        '''Закрывает SSH-соединение.'''
        if self.client:
            self.client.close()

    def execute_command(self, command, prompt):
        '''Открывает интерактивную сессию.'''
        channel = self.client.invoke_shell()
        if 'nano' in command:
            channel.send("export TERM=xterm\n")
        channel.send(command + "\n")

        old_tty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin)
            channel.settimeout(0.0)

            while True:
                if channel.recv_ready():
                    output = channel.recv(1024).decode("utf-8", errors="ignore")
                    sys.stdout.write(output)
                    sys.stdout.flush()

                    if prompt in output:
                        channel.send("exit\n")
                        break

                if channel.recv_stderr_ready():
                    sys.stderr.write(channel.recv_stderr(1024).decode("utf-8", errors="ignore"))
                    sys.stderr.flush()

                if channel.exit_status_ready():
                    break

                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    input_data = sys.stdin.read(1)
                    channel.send(input_data)

            channel.send("exit\n")

            while not channel.exit_status_ready():
                if channel.recv_ready():
                    sys.stdout.write(channel.recv(1024).decode("utf-8", errors="ignore"))
                    sys.stdout.flush()

            exit_status = channel.recv_exit_status()
            if exit_status == 0:
                print("Сессия успешно завершена.")
            else:
                print(f"Процесс завершился с кодом {exit_status}.")
        except Exception as e:
            print(f"Ошибка при завершении сессии: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            try:
                channel.close()
            except Exception as e:
                print(f"Ошибка при закрытии канала: {e}")
