# Node Editor Application
Copyright (c) 2026

Все права защищены.

Этот программный код предоставляется только для ознакомления.
Запрещается копирование, распространение, модификация или использование
в коммерческих целях без письменного разрешения правообладателя.



## Project Structure
```
project/
├── LICENSE
├── main.py                          # Точка входа
├── readme.md                        # Документация проекта
├── nodes/
│   ├── __init__.py
│   ├── base_node.py                 # Базовый класс ноды
│   ├── execution_manager.py         # Менеджер выполнения
│   ├── factory.py                   # Фабрика создания интерфейса
│   ├── registry.py                  # Реестр нод
│   ├── state_manager.py             # Сохранение/загрузка состояния
│   ├── top_menu.py                  # Верхнее меню
│   ├── llm_chat_manager.py          # Менеджер чата с LLM
│   ├── math_nodes/
│   │   ├── __init__.py
│   │   └── math_simple.py
│   ├── logic_nodes/
│   │   ├── __init__.py
│   │   └── logic_simple.py
│   ├── llm_nodes/
│   │   ├── __init__.py
│   │   ├── llama_node.py
│   │   └── output_node.py
│   ├── text/
│   │   ├── __init__.py
│   │   └── Simple.py
│   ├── tabs/
│   │   ├── __init__.py
│   │   └── tab_main.py
│   └── vector_db/
│       ├── __init__.py
│       ├── __pycache__/
│       └── qdrant_nodes.py
└── saved_states/                    # Директория для сохранения состояний
```

## Features
- Visual node-based interface
- Support for various node types (Math, Logic, LLM, Text, Vector DB)
- State saving and loading functionality
- Customizable themes
- Real-time execution

## Requirements
- Python 3.7+
- Dear PyGui
- transformers
- torch
- qdrant-client

## Usage
Run `python main.py` to start the application.