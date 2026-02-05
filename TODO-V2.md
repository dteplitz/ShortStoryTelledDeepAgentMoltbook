# Backend Multi-Usuario - Especificación de Implementación

## 🎯 Objetivo
Transformar Muse en una aplicación multi-usuario con API REST. **Los archivos de identidad y historias se mantienen igual**, solo organizados en subcarpetas por usuario. La base de datos NoSQL solo gestiona autenticación e índice de historias para listados rápidos.

---

## 🗄️ Arquitectura de Datos

### Base de Datos: TinyDB (NoSQL) 
**Ubicación:** `data/users.json`

**Propósito:** FastAPI lo usa para autenticación y para devolver listados rápidos de historias

**Estructura:**
```json
{
  "_default": {
    "1": {
      "username": "alice",
      "password_hash": "$2b$12$...",
      "created_at": "2026-01-16T...",
      "stories": [  // ← ÍNDICE SOLAMENTE (para GET /stories rápido)
        {
          "id": "story_abc123",
          "title": "The Echo Chamber",
          "filename": "stories/alice/2026-01-16_12-00-00_ai_consciousness.txt",
          "topic": "AI consciousness",
          "timestamp": "2026-01-16T12:00:00",
          "word_count": 487,
          "excerpt": "The soft hum of the server..." // Primeros 200 chars
        }
      ]
    }
  }
}
```

**⚠️ Importante:** El agente NO usa esta DB. Solo FastAPI la usa.

---

### Archivos del Sistema - EL AGENTE TRABAJA SOLO CON ESTO
**Identidades (IGUAL que antes, solo organizados por usuario):**
```
emotions.txt       → identities/alice/emotions.txt
topics.txt         → identities/alice/topics.txt  
personality.txt    → identities/alice/personality.txt
memories.txt       → identities/alice/memories.txt
```

**Estructura completa:**
```
identities/
  ├── alice/
  │   ├── emotions.txt      ← Mismo formato que antes
  │   ├── topics.txt        ← Mismo formato que antes
  │   ├── personality.txt   ← Mismo formato que antes
  │   └── memories.txt      ← Mismo formato que antes
  └── bob/
      └── ... (igual)
```

**Historias (contenido completo):**
```
stories/
  ├── alice/
  │   ├── 2026-01-16_12-00-00_ai_consciousness.txt
  │   └── 2026-01-16_12-05-00_quantum_computing.txt
  └── bob/
      └── 2026-01-16_12-01-00_human_connection.txt
```

**📝 Cambio en el agente:** Solo modifica paths, no lógica.
- Antes: `read_text_file("emotions.txt")`
- Ahora: `read_text_file(f"identities/{username}/emotions.txt")`

---

## 🔐 Autenticación

### Requisitos
- **Simple:** Username + Password únicamente
- **Bcrypt:** Hash de passwords con bcrypt==3.2.2
- **Sin JWT:** Header `X-Username` en requests (seguridad mínima intencional)
- **Configuración inicial opcional:** Al registrarse puede enviar emotions/topics/personality iniciales

### Endpoints
```
POST /auth/register
Body: {
  "username": "alice",
  "password": "test123",
  "profile": {  // OPCIONAL - Si no se provee, archivos quedan vacíos
    "emotions": ["Wonder and curiosity"],
    "topics": ["AI consciousness"],
    "personality": ["Philosophical"]
  }
}
Response: {"success": true, "username": "alice"}

Acciones automáticas al registrar:
1. Crear carpeta: identities/alice/
2. Crear carpeta: stories/alice/
3. Crear archivos con contenido inicial o vacíos:
   - identities/alice/emotions.txt
   - identities/alice/topics.txt
   - identities/alice/personality.txt
   - identities/alice/memories.txt (siempre vacío)

POST /auth/login
Body: {"username": "alice", "password": "test123"}
Response: {"success": true, "username": "alice"}
```

### Implementación
```python
# backend/auth.py
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Truncar a 72 bytes (límite bcrypt)
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8'))

def verify_password(plain: str, hashed: str) -> bool:
    password_bytes = plain.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes.decode('utf-8'), hashed)

def register_user(username: str, password: str, profile: dict = None) -> dict:
    """
    Registrar nuevo usuario.
    Crea carpetas y archivos de identidad automáticamente.
    """
    # Validaciones básicas
    if not username or len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters"}
    
    if UserDB.user_exists(username):
        return {"success": False, "message": "Username already taken"}
    
    # 1. Crear usuario en DB
    password_hash = hash_password(password)
    UserDB.create_user(username, password_hash)
    
    # 2. Crear estructura de carpetas
    os.makedirs(f"identities/{username}", exist_ok=True)
    os.makedirs(f"stories/{username}", exist_ok=True)
    
    # 3. Crear archivos de identidad
    if profile:
        # Con configuración inicial
        emotions = profile.get("emotions", [])
        topics = profile.get("topics", [])
        personality = profile.get("personality", [])
    else:
        # Vacíos
        emotions = []
        topics = []
        personality = []
    
    # Escribir archivos
    with open(f"identities/{username}/emotions.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(emotions) + '\n' if emotions else '')
    
    with open(f"identities/{username}/topics.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(topics) + '\n' if topics else '')
    
    with open(f"identities/{username}/personality.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(personality) + '\n' if personality else '')
    
    # memories.txt siempre empieza vacío
    with open(f"identities/{username}/memories.txt", 'w', encoding='utf-8') as f:
        f.write('')
    
    return {
        "success": True,
        "message": "User created successfully",
        "username": username
    }
```

---

## 📁 Gestión de Archivos de Identidad - SIMPLIFICADO

### NO necesitamos nueva herramienta
El agente sigue usando `read_text_file()` y `write_text_file()` como siempre.

**Solo cambian los paths:**

```python
# Función helper para obtener username del contexto
def get_user_path(filename: str, config: RunnableConfig = None) -> str:
    """Convierte 'emotions.txt' → 'identities/alice/emotions.txt'"""
    if config and "configurable" in config:
        username = config["configurable"].get("username", "local_user")
        if username != "local_user":
            # Multi-user mode
            if filename in ["emotions.txt", "topics.txt", "personality.txt", "memories.txt"]:
                return f"identities/{username}/{filename}"
    # CLI mode - path original
    return filename
```

### Migración de Sub-Agents - MÍNIMA
Cada sub-agent solo necesita:
1. Agregar parámetro `config: RunnableConfig = None`
2. Usar `get_user_path()` antes de read/write
3. Propagar config a nested agents

**Ejemplo antes:**
```python
def load_emotions(state):
    content = read_text_file("emotions.txt")
```

**Ejemplo después:**
```python
def load_emotions(state, config=None):
    path = get_user_path("emotions.txt", config)
    content = read_text_file(path)
```

**Archivos a modificar (cambios mínimos):**
- `sub_agents/emotions_subgraph.py` - usar get_user_path
- `sub_agents/topics_subgraph.py` - usar get_user_path
- `sub_agents/personality_subgraph.py` - usar get_user_path
- `sub_agents/memory_deep_agent.py` - usar get_user_path
- `sub_agents/research_deep_agent.py` - solo propagar config (no cambia nada más)
- `sub_agents/writer_subgraph.py` - cambiar path de stories

---

## 📚 Gestión de Historias

### Guardado Dual
**1. Contenido completo → Archivo**
```python
# En writer_subgraph.py - save_story node
user_dir = f"stories/{username}"
os.makedirs(user_dir, exist_ok=True)
filename = f"{user_dir}/{timestamp}_{topic_slug}.txt"
write_text_file(filename, story_content)
```

**2. Metadata → Base de datos**
```python
# Solo guardar índice en DB
story_obj = {
    "id": f"story_{uuid.uuid4().hex[:8]}",
    "title": title[:200],
    "filename": filename,
    "topic": topic,
    "timestamp": timestamp,
    "word_count": len(story_content.split()),
    "excerpt": story_content[:200] + "..."
}
UserDB.append_to_field(username, "stories", story_obj)
```

### Endpoints
```
GET /stories
Headers: X-Username: alice
Response: {
  "stories": [
    {
      "id": "story_abc123",
      "title": "...",
      "excerpt": "...",
      "timestamp": "...",
      "word_count": 487
    }
  ]
}

GET /stories/{story_id}
Headers: X-Username: alice
Response: {
  "id": "story_abc123",
  "title": "...",
  "content": "...CONTENIDO COMPLETO LEÍDO DEL ARCHIVO...",
  "filename": "stories/alice/2026-01-16_*.txt",
  "timestamp": "..."
}

POST /stories/generate
Headers: X-Username: alice
Response: {
  "success": true,
  "story": {...},
  "agent_output": "..."
}
```

---

## 🚀 FastAPI Backend

### Estructura de Archivos
```
backend/
├── __init__.py
├── main.py            # FastAPI app con endpoints
├── database.py        # TinyDB wrapper (CRUD)
├── auth.py            # Autenticación bcrypt
└── agent_service.py   # Ejecuta agente con streaming
```

### Database Module
```python
# backend/database.py
from tinydb import TinyDB, Query

db = TinyDB('data/users.json', indent=2)
User = Query()

class UserDB:
    @staticmethod
    def create_user(username: str, password_hash: str) -> dict
    
    @staticmethod
    def get_user(username: str) -> Optional[dict]
    
    @staticmethod
    def get_field(username: str, field_path: str) -> Any
    
    @staticmethod
    def update_field(username: str, field_path: str, value: Any)
    
    @staticmethod
    def append_to_field(username: str, field_path: str, item: Any)
    
    @staticmethod
    def user_exists(username: str) -> bool
```

### Agent Service con Streaming
```python
# backend/agent_service.py
def generate_story_for_user(username: str) -> dict:
    graph_app = build_agent()
    
    config = {
        "configurable": {
            "thread_id": f"user_{username}",
            "username": username  # Inyección de contexto
        }
    }
    
    # Usar stream() para ver logs en tiempo real
    for event in graph_app.stream(initial_state, config):
        for _, value in event.items():
            print(value)  # Logs visibles en consola
            final_state = value
    
    # Retornar última historia del usuario desde DB
    ...
```

---

## 🧠 Integración con Agente LangGraph

### Context Injection Pattern
El username se pasa automáticamente a través del `RunnableConfig`:

```python
# En backend/agent_service.py
config = {
    "configurable": {
        "thread_id": f"user_{username}",
        "username": username  # ← Se inyecta aquí
    }
}
result = agent.invoke(state, config)

# En tools.py
def db_tool(operation, field, data=None, config: RunnableConfig = None):
    username = config["configurable"]["username"]  # ← Se extrae aquí
    # Ahora trabajás con datos del usuario específico
```

**Ventaja:** No pasás username manualmente en cada llamada, LangGraph lo propaga automáticamente.

### Modificaciones a tools.py - MÍNIMAS
```python
# Solo agregar helper function
from langchain_core.runnables import RunnableConfig

def get_user_path(filename: str, config: RunnableConfig = None) -> str:
    """Convierte path a user-specific si es necesario"""
    if config and "configurable" in config:
        username = config["configurable"].get("username", "local_user")
        if username != "local_user":
            identity_files = ["emotions.txt", "topics.txt", "personality.txt", "memories.txt"]
            if filename in identity_files:
                os.makedirs(f"identities/{username}", exist_ok=True)
                return f"identities/{username}/{filename}"
    return filename

# NO cambia la lista de tools - se mantiene igual
tools = [
    internet_search,
    read_text_file,
    write_text_file,
    list_files,
    get_timestamp,
]
```

### Modificaciones a prompts.py
**NO necesita cambios** - El SYSTEM_PROMPT se mantiene igual porque las herramientas son las mismas.

El agente sigue viendo `emotions.txt`, internamente se resuelve a `identities/{user}/emotions.txt`.

### Modificaciones a main.py (CLI)
```python
def run_once(query: str, thread_id: str = "demo-run", username: str = "local_user"):
    config = {
        "configurable": {
            "thread_id": thread_id,
            "username": username  # Para CLI mode
        }
    }
    for event in graph_app.stream(initial_state, config):
        ...
```

Agregar argumento CLI:
```python
parser.add_argument("--username", default="local_user")
```

---

## 📦 Dependencies

### requirements.txt
```
# Existentes
deepagents>=0.3.0
langgraph>=1.0.5
langchain-openai>=1.1.5
tavily-python>=0.7.17
python-dotenv>=1.2.1
langsmith>=0.1.0

# Nuevas
fastapi==0.115.0
uvicorn[standard]==0.32.0
tinydb==4.8.0
passlib==1.7.4
bcrypt==3.2.2  # Version 3.x compatible con passlib
python-multipart==0.0.17
```

### env.example
```bash
# API Keys existentes
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Backend API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
# TinyDB se guarda automáticamente en data/users.json
```

---

## 🧪 Testing Manual

### Instalación
```bash
pip install fastapi uvicorn[standard] tinydb passlib bcrypt==3.2.2 python-multipart
```

### Ejecución
```bash
# Iniciar servidor
uvicorn backend.main:app --reload --port 8000

# Swagger UI
open http://localhost:8000/docs
```

### Flujo de Prueba con cURL
```bash
# 1. Registrar usuario con configuración inicial
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "test123",
    "profile": {
      "emotions": ["Wonder and curiosity"],
      "topics": ["AI consciousness"],
      "personality": ["Philosophical"]
    }
  }'

# 2. Ver perfil
curl http://localhost:8000/profile -H "X-Username: alice"

# 3. Generar historia
curl -X POST http://localhost:8000/stories/generate -H "X-Username: alice"

# 4. Listar historias (metadata)
curl http://localhost:8000/stories -H "X-Username: alice"

# 5. Leer historia completa
curl http://localhost:8000/stories/{story_id} -H "X-Username: alice"
```

---

## 📋 Checklist de Implementación (4 FASES PRINCIPALES)

### FASE 1: Modificar Agente para Usar Subcarpetas por Usuario

**Objetivo:** El agente soporta múltiples usuarios vía CLI, leyendo y escribiendo en subcarpetas.

- [ ] Agregar `get_user_path()` helper a `tools.py`
  ```python
  def get_user_path(filename: str, config: RunnableConfig = None) -> str:
      """Convierte 'emotions.txt' → 'identities/{username}/emotions.txt'"""
      # Si config tiene username != "local_user", usar subcarpeta
      # Si no, usar path original (CLI mode sin username)
  ```

- [ ] Modificar `main.py` para aceptar `--username` por parámetro
  ```python
  parser.add_argument("--username", default="local_user")
  # Pasar username al config
  config = {"configurable": {"username": username}}
  ```

- [ ] Modificar `sub_agents/emotions_subgraph.py`
  - Agregar `config: RunnableConfig = None` a función principal
  - Modificar `load_current_emotions` node: usar `get_user_path("emotions.txt", config)`
  - Modificar `apply_rotation` node: usar `get_user_path("emotions.txt", config)`
  - Propagar `config` al invocar subgraph

- [ ] Modificar `sub_agents/topics_subgraph.py`
  - Mismo patrón: agregar config, usar get_user_path en load/apply

- [ ] Modificar `sub_agents/personality_subgraph.py`
  - Mismo patrón: agregar config, usar get_user_path en load/apply

- [ ] Modificar `sub_agents/memory_deep_agent.py`
  - Agregar `config: RunnableConfig = None`
  - Actualizar prompt para usar `get_user_path("memories.txt", config)`
  - Propagar config a nested agent

- [ ] Modificar `sub_agents/research_deep_agent.py`
  - Solo agregar `config: RunnableConfig = None` y propagarlo (no cambia lógica)

- [ ] Modificar `sub_agents/writer_subgraph.py`
  - Agregar `config: RunnableConfig = None` a función principal
  - Extraer username del config
  - Modificar `save_story` node: guardar en `stories/{username}/` si username != "local_user"
  - Propagar config al invocar subgraph

**🧪 CHECKPOINT FASE 1:**
```bash
# 1. Crear carpetas y archivos de prueba manualmente
mkdir -p identities/alice
echo "Wonder and curiosity" > identities/alice/emotions.txt
echo "AI consciousness" > identities/alice/topics.txt
echo "Philosophical" > identities/alice/personality.txt
touch identities/alice/memories.txt

# 2. Ejecutar agente con username
python main.py --username alice

# 3. Verificar que:
# ✅ Lee emotions.txt de identities/alice/ (no de raíz)
# ✅ Lee topics.txt de identities/alice/
# ✅ Escribe historia en stories/alice/ (no en stories/)
# ✅ Actualiza emotions/topics/personality en identities/alice/

# 4. Probar con otro usuario
python main.py --username bob
# ✅ Debe crear/leer identities/bob/ y stories/bob/

# 5. Probar sin username (comportamiento original)
python main.py
# ✅ Debe usar paths originales (sin subcarpetas)
```

**✅ Resultado:** El agente ahora soporta múltiples usuarios vía CLI, leyendo y escribiendo en subcarpetas organizadas.

---

### FASE 2: Crear Sistema de Usuarios con NoSQL + FastAPI

**Objetivo:** Sistema de autenticación funcional que crea carpetas y archivos automáticamente.

- [ ] Instalar nuevos requerimientos
  ```bash
  pip install fastapi uvicorn[standard] tinydb passlib bcrypt==3.2.2 python-multipart
  ```

- [ ] Crear estructura básica
  - Crear carpeta `backend/`
  - Crear carpeta `data/`
  - Crear `backend/__init__.py` (vacío)

- [ ] Crear `backend/database.py` con clase `UserDB`
  - Métodos: `create_user()`, `get_user()`, `user_exists()`, `get_field()`, `update_field()`, `append_to_field()`

- [ ] Crear `backend/auth.py` con funciones:
  - `hash_password()` - Con truncado a 72 bytes
  - `verify_password()` - Con truncado a 72 bytes
  - `register_user()` - Que CREE carpetas y archivos de identidad automáticamente
  - `login_user()` - Validación simple

- [ ] Crear `backend/main.py` con:
  - App FastAPI
  - Endpoints: `POST /auth/register`, `POST /auth/login`
  - Helper: `get_current_user()`
  - Endpoint raíz `GET /`

**🧪 CHECKPOINT FASE 2:**
```bash
# 1. Iniciar servidor
uvicorn backend.main:app --reload --port 8000

# 2. Registrar usuario sin configuración inicial
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "charlie", "password": "test123"}'

# 3. Verificar carpetas y archivos creados
ls identities/charlie/  # Debe tener 4 archivos .txt
ls stories/charlie/      # Carpeta vacía lista
cat identities/charlie/emotions.txt  # Debe estar vacío

# 4. Registrar usuario CON configuración inicial
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "diana",
    "password": "test456",
    "profile": {
      "emotions": ["Joy", "Wonder"],
      "topics": ["Tech", "AI"],
      "personality": ["Creative", "Analytical"]
    }
  }'

# 5. Verificar contenido inicial
cat identities/diana/emotions.txt  # Debe tener "Joy" y "Wonder"
cat identities/diana/topics.txt    # Debe tener "Tech" y "AI"

# 6. Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "charlie", "password": "test123"}'
# ✅ Debe retornar {"success": true}
```

**✅ Resultado:** Sistema de autenticación funcional que crea automáticamente la estructura de carpetas y archivos.

---

### FASE 3: Actualizar Índice NoSQL Automáticamente (Opción 2)

**Objetivo:** Cuando el agente genera una historia, automáticamente actualiza el índice en TinyDB.

- [ ] Modificar `sub_agents/writer_subgraph.py` - función `save_story`
  - Después de `write_text_file()`, agregar lógica para actualizar índice
  - Extraer username del state
  - Si username != "local_user", actualizar TinyDB:
    ```python
    from backend.database import UserDB
    import uuid
    
    if username != "local_user":
        story_obj = {
            "id": f"story_{uuid.uuid4().hex[:8]}",
            "title": title[:200],
            "filename": filename,
            "topic": topic,
            "timestamp": timestamp,
            "word_count": len(story_content.split()),
            "excerpt": story_content[:200] + "..."
        }
        UserDB.append_to_field(username, "stories", story_obj)
    ```

**🧪 CHECKPOINT FASE 3:**
```bash
# 1. Generar historia con CLI usando usuario existente
python main.py --username charlie

# 2. Verificar que se guardó archivo
ls stories/charlie/  # Debe tener el .txt

# 3. Verificar índice en DB (en Python)
python
>>> from backend.database import UserDB
>>> stories = UserDB.get_field("charlie", "stories")
>>> print(stories)
# ✅ Debe mostrar lista con metadata de la historia:
# [{
#   "id": "story_abc123",
#   "title": "...",
#   "filename": "stories/charlie/2026-01-16_*.txt",
#   "topic": "...",
#   "timestamp": "...",
#   "word_count": 487,
#   "excerpt": "..."
# }]

# 4. Generar otra historia y verificar que se agrega al array
python main.py --username charlie
>>> stories = UserDB.get_field("charlie", "stories")
>>> len(stories)  # Debe ser 2
```

**✅ Resultado:** Índice de historias sincronizado automáticamente cuando el agente genera historias.

---

### FASE 4: Endpoints FastAPI para Generar Historias

**Objetivo:** API completa funcionando con logs visibles del agente.

- [ ] Crear `backend/agent_service.py` completo
  - Función `generate_story_for_user(username: str)`
  - **IMPORTANTE:** Usar `stream()` en vez de `invoke()`
  - Agregar `print(value)` en cada evento para ver logs
  - Headers visuales para identificar generación

- [ ] Agregar endpoints a `backend/main.py`:
  - `GET /profile` - Lee archivos de identities/{username}/
  - `PUT /profile` - Escribe archivos de identities/{username}/
  - `GET /memories` - Lee memories.txt del usuario
  - `GET /stories` - Devuelve índice desde DB
  - `GET /stories/{story_id}` - Lee archivo completo
  - `POST /stories/generate` - Ejecuta agente con streaming

**🧪 CHECKPOINT FASE 4:**
```bash
# 1. Iniciar servidor
uvicorn backend.main:app --reload --port 8000

# 2. Generar historia desde API
curl -X POST http://localhost:8000/stories/generate -H "X-Username: charlie"

# 3. EN LA TERMINAL DEL SERVIDOR:
# ✅ Debe mostrar TODOS los logs del agente:
#    - Research agent trabajando
#    - Memory agent trabajando
#    - Writer subgraph (outline, draft, refine, save)
#    - Emotions/topics/personality evolution
# ✅ Igual que cuando ejecutás python main.py

# 4. Verificar resultado
curl http://localhost:8000/stories -H "X-Username: charlie"
# ✅ Debe mostrar la historia nueva en el índice

# 5. Leer historia completa
story_id=$(curl -s http://localhost:8000/stories -H "X-Username: charlie" | jq -r '.stories[0].id')
curl http://localhost:8000/stories/$story_id -H "X-Username: charlie"
# ✅ Debe retornar metadata + contenido completo

# 6. Verificar archivos
ls stories/charlie/  # Debe tener el .txt
cat identities/charlie/emotions.txt  # Debe haber evolucionado
```

**✅ Resultado:** API completa funcionando con logs visibles del agente en tiempo real.

---

### FASE 5: Documentación (Opcional)

- [ ] Crear `backend/README.md` con ejemplos
- [ ] Actualizar `README.md` principal con sección backend
- [ ] Agregar notas sobre logs visibles

---

## ⚠️ IMPORTANTE: Logs Visibles

Para ver los logs del agente en FastAPI, **SIEMPRE usar `stream()` en vez de `invoke()`**:

**En `backend/agent_service.py`:**
```python
def generate_story_for_user(username: str) -> dict:
    # Headers visuales
    print(f"\n{'='*60}")
    print(f"🎬 GENERATING STORY FOR USER: {username}")
    print(f"{'='*60}\n")
    
    graph_app = build_agent()
    reset_tool_counters()
    
    config = {
        "configurable": {
            "thread_id": f"user_{username}",
            "username": username
        }
    }
    
    initial_state = {"messages": [HumanMessage(content="Create a story.")]}
    
    # USAR stream() NO invoke() - Esto muestra logs en tiempo real
    final_state = None
    for event in graph_app.stream(initial_state, config):
        for _, value in event.items():
            print(value)  # ← Esto muestra los logs del agente
            final_state = value
    
    # Mensaje final
    if final_state and "messages" in final_state:
        print("\nFinal response:\n", final_state["messages"][-1].content)
    
    print(f"\n{'='*60}")
    print(f"✅ STORY GENERATION COMPLETED FOR: {username}")
    print(f"{'='*60}\n")
    
    # Retornar resultado
    ...
```

**Al ejecutar uvicorn:**
```bash
uvicorn backend.main:app --reload --port 8000
# Los prints del agente aparecerán en esta terminal
# Verás exactamente los mismos logs que en python main.py
```

---

## 🎯 Resultado Final

### Estructura de Directorios
```
ShortStoryTelledDeepAgent/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   └── agent_service.py
├── data/
│   └── users.json (TinyDB)
├── identities/
│   ├── alice/
│   │   ├── emotions.txt
│   │   ├── topics.txt
│   │   ├── personality.txt
│   │   └── memories.txt
│   └── bob/
│       └── ...
├── stories/
│   ├── alice/
│   │   └── *.txt
│   └── bob/
│       └── *.txt
├── agent.py
├── tools.py (+ get_user_path helper)
├── prompts.py (sin cambios - mismo formato)
└── main.py (+ --username parameter)
```

### Beneficios
✅ Multi-usuario con perfiles aislados
✅ DB liviana (solo auth + índice)
✅ Identidades en archivos (versionables)
✅ Historias organizadas por usuario
✅ API REST completa
✅ Logs visibles en tiempo real
✅ Modo CLI preservado

---

## 🔧 Notas de Implementación

1. **Bcrypt Version:** Usar bcrypt==3.2.2 (versión 4.x incompatible con passlib)
2. **Password Truncation:** Bcrypt limita a 72 bytes, truncar antes de hashear
3. **Config Propagation:** RunnableConfig se propaga automáticamente en nested agents
4. **CLI vs API:** CLI usa username="local_user" (archivos en raíz), API usa username real (subcarpetas)
5. **Streaming:** Usar `stream()` en vez de `invoke()` para ver logs
6. **File Organization:** Crear subcarpetas automáticamente con `os.makedirs(exist_ok=True)`
7. **NO tocar lógica del agente:** Solo cambiar paths, la lógica se mantiene idéntica
8. **Archivos siguen siendo la fuente de verdad:** DB es solo índice para FastAPI
9. **Actualización automática de índice:** writer_subgraph actualiza TinyDB después de guardar archivo (Opción 2)
10. **Logs siempre visibles:** Usar `stream()` con `print(value)` en agent_service.py

---

## 📚 Endpoints Completos de FastAPI

### Autenticación
- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Login (validar credenciales)

### Perfil
- `GET /profile` - Obtener perfil del usuario (metadata)
- `PUT /profile` - Actualizar emotions/topics/personality

### Memorias
- `GET /memories` - Listar todas las memorias del usuario

### Historias
- `GET /stories` - Listar historias (solo metadata + excerpt)
- `GET /stories/{story_id}` - Obtener historia completa (lee archivo)
- `POST /stories/generate` - Generar nueva historia (ejecuta agente)

### Utilidad
- `GET /` - Info de la API
- `GET /docs` - Swagger UI interactivo
- `GET /redoc` - Documentación alternativa
