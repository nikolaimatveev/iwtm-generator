# Traffic Generator for IWTM

## Установка и запуск
В рамках разработки данного приложения использовались:
- Python версии 3
- python-ldap для соответствующей версии Python

---

Для корректной работы приложения необходима установка следующих компонентов:
### python-ldap
Необходимо скачать python-ldap [здесь](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-ldap).
Затем установить библиотеку с помощью команды:

`$ pip install --only-binary=:all: python_ldap-[версия пакета для вашего Python].whl`
### openpyxl
Для установки необходимо выполнить команду:

`$ pip install openpyxl`

---

Для запуска необходимо настроить `config.ini`, а затем выполнить команду:

`$ python generator.py`
## config.ini

### [LDAP]
- `ldap_url` - адреса машин с AD через `;`.

`ldap_url=ldap://192.168.118.6;ldap://192.168.113.4`
- `domain_name` - имя домена.
- `ad_username` - имя пользователя для подключения к AD.
- `ad_password` - пароль для `ad_username`.
- `group_list` - перечень групп пользователей необходимых для генерации трафика.

### [Mail]
- `mail_host` - имена почтовых серверов через `;`.

`mail_host=mail.demo.lab;anothermail.demo.lab`
- `mail_port` - порты для `mail_host` через `;`. Каждый i-ый порт соответствует i-му `mail_host`.
- `external_email` - email адреса для External группы пользователей через `;`.
- `generation_type` - приложение поддерживает два типа генерации трафика: `config` - генерация писем на основе информации указанной в `[Directions]`, `template` - генерация писем на основе шаблона в формате `.xslx`.
- `timeout` - пауза между отправками писем в `с`.

### [Template]
- `filename` - имя шаблона для генерации в режиме `template`.

### [Directions]
- `direction.#` - отправители и получатели при генерации `config`. Вместо `#` необходимо указывать числа от 0 до бесконечности.
Отправители и получатели указываются следующим образом:
    - `IT->External`
    - `primer@yandex.ru->IT`
    - `HR->primer@yandex.ru`
- `dir.#` - папка с файлами для `direction.#`.
