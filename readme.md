## 0. Суть программы

Программа предназначена для удобного подключения пользователя к удаленному серверу по SSH для выполнении заранее определенных команд.<br>
В конкретном случе команда тестирования может подключаться к SSH серверу и выполнять команды на тестовых стендах:
- перезапуск стендов
- изменение настроек
- изменение визуального оформления
- просмотров логов celery, wsgi через cat, tail с возможностью grep
- запуска скриптов
<br>

Все это доступно с поддержкой интерактивного режима работы.

## A. Структура программы

### Файл: `main.py`
Основной файл программы. В нем инициализируются команды из файла `commands.yaml` и запускается CLI (интерфейс командной строки).

### Файл: `ssh_client.py`
Содержит класс `SSHClient`, который управляет SSH-соединением, включая методы для инициализации соединения, выполнения команд и завершения сессии.

#### Методы:
- `initialize()`: инициализирует SSH-клиент и устанавливает соединение.
- `close()`: закрывает SSH-соединение.
- `execute_command(command, prompt)`: выполняет команду в интерактивном режиме и обрабатывает вывод.

### Файл: `cli.py`
Содержит класс `CLI`, который управляет пользовательским интерфейсом командной строки. Он позволяет пользователю выбирать категории и команды, а затем выполняет команды с помощью SSH-клиента.

#### Методы:
- `load_login_data(file_path)`: загружает данные для подключения к SSH-серверу.
- `display_categories()`: выводит доступные категории.
- `display_commands(category)`: выводит команды для выбранной категории.
- `start()`: основной метод для запуска CLI и обработки ввода пользователя.

### Файл: `command_loader.py`
Содержит класс `CommandLoader`, который загружает команды из YAML-файла и создает их функции для выполнения в зависимости от выбранных параметров.

#### Методы:
- `load_commands(file_path)`: загружает команды и пути из YAML-файла и создает соответствующие команды для выполнения.

### Файл: `commands.yaml`
Файл конфигурации, который содержит пути и шаблоны команд для различных стендов. Он используется для генерации команд с подставленными параметрами.

### Файл: `login_data.yaml` (создавать отдельно)
Файл данных для подключения к серверу по ssh, который адрес, порт, логин, пароль.

## B. Установленные пакеты:
1. Надо войти в виртуальную среду
```python
    python3 -m venv myenv  
    source myenv/bin/activate  
```
2.  Установить пакеты
```python
    pip install paramiko
```
```python
    pip install pyyaml
```

## C. Создание файла для логина по ssh
0. В директории нет файла логина к серверу по ssh
1. Надо его создать в корне и назвать login_data.yaml
2. Занести в него данные:
```yaml
    hostname: "hostname"
    port: port
    username: "username"
    password: "password"
```

Например:
```yaml
    hostname: "dev.google.app.com"
    port: 22
    username: "test"
    password: "easypass"
```

## D. Создание файла команд
0. В директории нет файла команд для сервера
1. Надо его создать в корне и назвать commands.yaml
2. Занести в него данные:<br>

Например:

```yaml
paths:
  logs: "/var/log/supervisor"
  base:
    standA: "~/standA/root"
    standB: "~/standB"

commands:
  deploy: "cd {src_path} && ../deploy.sh"
  change settings: "cd {src_path} && nano unegui/local_settings.py"
  change visual: "cd {base_path} && nano deploy.sh"
  restart celery: "cd {src_path} && supervisorctl restart celery_{stand}"
  full celery logs: "cd {src_path} && cat {logs_path}/celery_{stand}.log"
  full wsgi logs: "cd {src_path} && cat {logs_path}/wsgi_{stand}.log"
  tail celery logs: "cd {src_path} && tail -f {logs_path}/celery_{stand}.log"
  tail wsgi logs: "cd {src_path} && tail -f {logs_path}/wsgi_{stand}.log"
  run script: "cd {src_path} && source .venv/bin/activate && python manage.py "
```

## E. Сборка исполняемого файла для mac
0. Уставнока пакета<br>
```python
    pip install pyinstaller
```

1. Выполнение команды по сборке<br>
```python
    pyinstaller --onefile --add-data "commands.yaml:." --add-data "login_data.yaml:." main.py    
```

2. В папке dist появляется исполняемый файл main
3. Его надо архивировать
4. Отправляем архив человеку с mac
5. Скачать архив
6. Распаковать
7. Открыть терминал
8. Выполнить:
```
    cd Downloads
```
9. Ввести:
```
    xattr -cr main
```
10. После этого можно пользоваться