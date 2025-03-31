import os
import time
import re
from pathlib import Path
import getpass # Для безопасного ввода ключа
from langchain_community.llms import GigaChat
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

TOPICS = [
    "Травля (Буллинг)",
    "Травля в школе",
    "Интернет-травля (Кибербуллинг)",
    "Физический буллинг",
    "Словесный буллинг",
    "Социальный буллинг",
    "Агрессор (Обидчик)",
    "Жертва (Пострадавший)",
    "Свидетель",
    "Чувства жертвы",
    "Отличие буллинга от ссоры",
    "Что делать, если обижают тебя?",
    "Что делать, если видишь буллинг? (Роль свидетеля)",
    "Кому рассказать о буллинге? (Взрослые помощники)",
    "Как остановить буллинг? (Дружба и Уважение)"
]

# --- 2. Конфигурация ---
# Убедись, что путь правильный относительно места запуска скрипта
# Например, если скрипт лежит в корне репозитория:
OUTPUT_DIR = Path("./KIDBOOK/health/emotions_stress") # Путь к директории для markdown-файлов
WORK_DIR = Path("./WORK/health/emotions_stress") # Путь к рабочей директории для concepts.json и README.md
# Или укажи абсолютный путь, если нужно

API_DELAY = 2 # Секунды между запросами к API GigaChat
GIGACHAT_MODEL = "GigaChat-Max" # или GigaChat-Pro, если доступен и нужен
GIGACHAT_SCOPE = "GIGACHAT_API_PERS" # Уточни нужный scope для твоего ключа

# --- 3. Функция для создания безопасного имени файла ---
def generate_filename(topic_name):
    cyrillic_map = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
        'ж':'zh','з':'z','и':'i','й':'j','к':'k','л':'l','м':'m',
        'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
        'ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'shch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya', ' ':'_'
    }
    # Убираем текст в скобках и вопросительные знаки
    name = re.sub(r'\(.*?\)', '', topic_name).strip()
    name = re.sub(r'[?]', '', name).strip()
    # Транслитерация и замена пробелов
    name_latin = "".join(cyrillic_map.get(c, c) for c in name.lower() if c in cyrillic_map or 'a' <= c <= 'z' or '0' <= c <= '9')
    # Убираем множественные подчеркивания и по краям
    name_latin = re.sub(r'_+', '_', name_latin)
    name_latin = name_latin.strip('_')
    return f"{name_latin}.md" if name_latin else "default_topic.md"

# --- 4. Функция для генерации текста с использованием LangChain ---
def generate_text_with_langchain(llm_chain, topic):
    print(f"  Отправка запроса для темы: '{topic}' через LangChain...")
    try:
        # Используем llm_chain.invoke с правильным входным словарем
        response = llm_chain.invoke(input={"topic": topic})

        # Ответ LangChain обычно содержит ключ 'text'
        if response and isinstance(response, dict) and 'text' in response:
            generated_text = response['text']
            print(f"  Получен ответ от GigaChat.")
            return generated_text.strip()
        else:
            print(f"  ОШИБКА: Ответ от LangChain/GigaChat не содержит ключ 'text' или имеет неожиданный формат. Ответ: {response}")
            return None
    except Exception as e:
        # Ловим общие ошибки при вызове LLM через LangChain
        print(f"  ОШИБКА при запросе к GigaChat через LangChain: {e}")
        # Попробуем вывести детали, если они есть (зависит от типа ошибки)
        if hasattr(e, 'response') and e.response:
             try:
                 error_details = e.response.json()
                 print(f"  Детали ошибки API (если доступны): {error_details}")
             except Exception:
                 print(f"  Не удалось разобрать детали ошибки из ответа API: {getattr(e.response, 'text', 'Нет текстового ответа')}")
        return None

# --- 5. Основной блок ---
if __name__ == "__main__":
    print("--- Запуск скрипта генерации страниц KidBook (с LangChain) ---")

    # --- Получаем ключ БЕЗОПАСНО ---
    print("\nВАЖНО: Сейчас нужно будет ввести ваш ключ авторизации GigaChat (Authorization Key).")
    print("Ввод будет скрыт для безопасности.")
    print("НИКОГДА НЕ ВСТАВЛЯЙТЕ КЛЮЧ ПРЯМО В КОД СКРИПТА!")
    try:
        # Используем getpass для скрытого ввода
        auth_credentials = getpass.getpass("Введите ваш ключ авторизации GigaChat и нажмите Enter: ")
        if not auth_credentials:
             print("Ключ не был введен. Выход.")
             exit()
    except Exception as e:
        print(f"\nОшибка при вводе ключа: {e}. Выход.")
        exit()
    print("Ключ получен.")
    # ------------------------------

    # --- Инициализация GigaChat через LangChain ---
    try:
        print("\nИнициализация GigaChat через LangChain...")
        llm = GigaChat(
            credentials=auth_credentials, # Передаем полученный ключ
            model=GIGACHAT_MODEL,
            scope=GIGACHAT_SCOPE, # Убедись, что этот scope правильный для твоего ключа
            verify_ssl_certs=False # Может понадобиться, особенно на Windows
            # Можно добавить другие параметры GigaChat, если нужно (temperature, max_tokens и т.д.)
            # temperature=0.7
        )
        print("Клиент GigaChat LangChain успешно инициализирован.")
    except Exception as e:
        print(f"ОШИБКА при инициализации GigaChat через LangChain: {e}")
        print("Возможные причины:")
        print("- Неверный ключ авторизации (credentials)")
        print("- Неправильно указан scope")
        print("- Проблемы с сетевым доступом к API GigaChat")
        print("- Не установлены необходимые библиотеки (`langchain`, `langchain-community`, `gigachat`)")
        exit()

    # --- Создание PromptTemplate и LLMChain ---
    # Промпт должен содержать переменную {topic}, которая будет заполнена из списка TOPICS
    template = template = """
Объясни для десятилетнего ребенка простыми словами, что такое "{topic}".

Твой ответ будет использоваться для детской энциклопедии KidBook.
Пожалуйста, оформи текст в формате Markdown. Используй:
*   **Заголовки второго уровня (##)** для выделения важных подтем, если это уместно.
*   **Списки (* или -)** для перечислений или шагов.
*   **Выделение жирным шрифтом (**слово**)** для ключевых терминов или важных моментов.
*   **Выделение курсивом (*слово*)** для определений или примеров.


Сделай текст понятным, интересным и хорошо структурированным. Не используй заголовок первого уровня (#), так как он будет добавлен автоматически из названия темы.
обьем по каждой отдельной теме - 500-1000 символов
"""
    prompt_template = PromptTemplate.from_template(template)

    # Создаем цепочку (Chain), которая связывает промпт и языковую модель
    llm_chain = LLMChain(prompt=prompt_template, llm=llm)
    print("PromptTemplate и LLMChain созданы.")

    # --- Создаем директории ---
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Директория для MD-файлов: {OUTPUT_DIR.resolve()}")
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Рабочая директория: {WORK_DIR.resolve()}")
    except OSError as e:
        print(f"Ошибка при создании директории {OUTPUT_DIR} или {WORK_DIR}: {e}")
        exit()

    # --- Генерируем файлы ---
    print(f"\nНачинаем генерацию {len(TOPICS)} страниц...")
    generated_files_info = {} # Словарь для хранения информации для concepts.json

    for i, topic in enumerate(TOPICS):
        print(f"\n--- Обработка темы {i+1}/{len(TOPICS)}: '{topic}' ---")
        filename = generate_filename(topic)
        filepath = OUTPUT_DIR / filename
        print(f"  Имя файла: {filename}")

        if filepath.exists():
            print(f"  ПРЕДУПРЕЖДЕНИЕ: Файл {filename} уже существует. Пропускаем генерацию.")
            # Все равно добавляем в словарь для concepts.json
            generated_files_info[topic] = str(filepath.relative_to(Path('.'))) # Сохраняем относительный путь
            continue

        # Генерируем текст с помощью LangChain
        generated_text = generate_text_with_langchain(llm_chain, topic)

        if generated_text:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {topic}\n\n") # Добавляем заголовок Markdown
                    f.write(generated_text)
                print(f"  УСПЕХ: Текст сохранен в файл {filepath.name}")
                # Добавляем информацию о созданном файле
                generated_files_info[topic] = str(filepath.relative_to(Path('.'))) # Сохраняем относительный путь
            except IOError as e:
                print(f"  ОШИБКА: Не удалось записать в файл {filepath}: {e}")
        else:
            print(f"  НЕУДАЧА: Не удалось сгенерировать текст для '{topic}'. Файл не создан.")

        # Добавляем задержку между запросами, чтобы не превысить лимиты API
        if i < len(TOPICS) - 1:
             print(f"  Пауза {API_DELAY} сек...")
             time.sleep(API_DELAY)

    print("\n--- Генерация всех страниц завершена ---")

    # --- Сохранение concepts.json ---
    concepts_file_path = WORK_DIR / "concepts.json"
    try:
        import json
        # Преобразуем словарь в нужный формат списка объектов
        concepts_list = [{"topic": key, "file": value} for key, value in generated_files_info.items()]
        with open(concepts_file_path, 'w', encoding='utf-8') as f:
            json.dump(concepts_list, f, ensure_ascii=False, indent=4)
        print(f"\nИнформация о сгенерированных страницах сохранена в {concepts_file_path}")
    except ImportError:
        print("\nПРЕДУПРЕЖДЕНИЕ: Модуль 'json' не найден. Не удалось создать concepts.json.")
    except IOError as e:
        print(f"\nОШИБКА: Не удалось записать файл {concepts_file_path}: {e}")
    except Exception as e:
        print(f"\nНЕОЖИДАННАЯ ОШИБКА при создании concepts.json: {e}")

    print("\n--- Скрипт завершил работу ---")
