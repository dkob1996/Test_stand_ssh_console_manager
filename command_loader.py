import sys
import os
import yaml

class CommandLoader:
    @staticmethod
    def load_commands(file_path):
        '''Загружает команды и пути из YAML файла и создает функции для их сборки.'''
        if getattr(sys, 'frozen', False):  # Проверяем, запущена ли программа как исполняемый файл
            file_path = os.path.join(sys._MEIPASS, file_path)  # Используем _MEIPASS для доступа к данным в скомпилированном файле

        with open(file_path, "r") as file:
            config = yaml.safe_load(file)

        paths = config["paths"]
        base_paths = paths["base"]
        commands_template = config["commands"]

        all_commands = {}
        for stand, base_path in base_paths.items():
            src_path = f"{base_path}/src"
            logs_path = paths["logs"]
            all_commands[stand] = {
                name: template.format(
                    base_path=base_path,
                    src_path=src_path,
                    logs_path=logs_path,
                    stand=stand
                )
                for name, template in commands_template.items()
            }
        return all_commands
