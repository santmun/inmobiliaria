# ListaPro

Generador automatizado de listados inmobiliarios profesionales. Sube los datos de una propiedad y obtiene automaticamente:

- **PDF** listo para imprimir con fotos, descripcion y datos de contacto
- **Post de Instagram** optimizado con copy y hashtags
- **Historia de Instagram** en formato vertical
- **Carrusel** con multiples slides arrastrables
- **Email HTML** profesional listo para enviar
- **Video Reel** vertical (9:16) con musica IA y locucion para Instagram/TikTok
- **Publicacion directa a Instagram** desde la plataforma

---

## Requisitos previos

Necesitas instalar estas 3 cosas en tu computadora antes de empezar:

### 1. Node.js (para generar los videos)

1. Ve a [https://nodejs.org/](https://nodejs.org/)
2. Descarga la version **LTS** (el boton verde grande)
3. Abre el archivo descargado y sigue los pasos de instalacion (siguiente, siguiente, instalar)
4. Para verificar que se instalo, abre tu Terminal y escribe:
   ```
   node --version
   ```
   Debe mostrar algo como `v20.x.x`

### 2. Python 3.9+ (para el servidor)

**Mac** (ya viene instalado en la mayoria de los casos):
1. Abre Terminal
2. Escribe `python3 --version`
3. Si muestra `Python 3.9` o superior, ya lo tienes
4. Si no, descargalo de [https://www.python.org/downloads/](https://www.python.org/downloads/)

**Windows**:
1. Ve a [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Descarga la ultima version
3. **IMPORTANTE**: En el instalador, marca la casilla que dice **"Add Python to PATH"** antes de dar clic en Install
4. Verifica con `python --version` en tu terminal

### 3. Git (para descargar el proyecto)

**Mac**:
1. Abre Terminal y escribe `git --version`
2. Si no lo tienes, te pedira instalarlo automaticamente — acepta

**Windows**:
1. Descarga de [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Instala con las opciones por defecto

---

## Instalacion paso a paso

### Paso 1: Descargar el proyecto

Abre tu Terminal (Mac) o PowerShell (Windows) y escribe estos comandos uno por uno:

```bash
cd ~/Documents
git clone https://github.com/santmun/listapro.git
cd listapro
```

> Esto descarga el proyecto en tu carpeta de Documentos.

### Paso 2: Instalar dependencias de Python

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Esto crea un "entorno virtual" (una carpeta aislada) e instala todas las librerias que necesita el servidor.

### Paso 3: Instalar dependencias del video

```bash
cd video
npm install
cd ..
```

> Esto instala las librerias para generar los videos (Remotion).

### Paso 4: Configurar tus API keys

```bash
cp .env.example .env
```

> En Windows, si `cp` no funciona, usa: `copy .env.example .env`

Ahora abre el archivo `.env` con cualquier editor de texto (TextEdit en Mac, Notepad en Windows) y reemplaza los valores de ejemplo con tus keys reales:

```
OPENAI_API_KEY=sk-proj-tu-key-real-aqui
```

### Paso 5: Iniciar el servidor

**Mac/Linux:**
```bash
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Windows:**
```bash
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Paso 6: Abrir ListaPro

Abre tu navegador y ve a:

```
http://localhost:8000
```

Ya puedes empezar a generar listados.

---

## API Keys necesarias

| Servicio | Para que sirve | Obligatoria? | Donde obtenerla |
|----------|---------------|:---:|-----------------|
| **OpenAI** | Genera las descripciones, copy y textos | Si | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **ImgBB** | Sube las fotos para que el video las use | Para video | [api.imgbb.com](https://api.imgbb.com/) |
| **ElevenLabs** | Genera la voz del locutor en el video | Para locucion | [elevenlabs.io](https://elevenlabs.io/) |
| **Suno** | Genera musica original para el video | Para musica | [suno.com](https://suno.com/) |
| **Upload Post** | Publica el video directo a Instagram | Para publicar | [upload-post.com](https://upload-post.com/) |

> **Sin ninguna key opcional**: El PDF, post de Instagram, historia, carrusel y email funcionan perfectamente. Solo el video y la publicacion directa requieren las keys extras.

### Como obtener la API key de OpenAI (la unica obligatoria)

1. Ve a [platform.openai.com](https://platform.openai.com/) y crea una cuenta
2. Ve a **API Keys** en el menu de la izquierda
3. Clic en **"Create new secret key"**
4. Copia la key (empieza con `sk-proj-...`)
5. Pegala en tu archivo `.env` en la linea `OPENAI_API_KEY=`
6. Necesitas agregar credito a tu cuenta de OpenAI (minimo $5 USD) en **Billing**

---

## Como usar ListaPro

### Configurar tu plantilla (primera vez)

1. Ve a `http://localhost:8000/plantilla`
2. Sube tu **logo** y **foto de agente**
3. Llena tus datos de contacto (nombre, telefono, email)
4. Personaliza colores si quieres
5. Clic en **"Guardar Configuracion"**

> Solo necesitas hacer esto una vez. Tu plantilla se guarda y se usa en todos los listados.

### Generar un listado

1. Ve a `http://localhost:8000`
2. Llena los datos de la propiedad (tipo, precio, ubicacion, etc.)
3. Sube las fotos (la primera sera la portada)
4. Clic en **"Generar Listado Profesional"**
5. Espera mientras se generan todos los contenidos
6. En la pagina de resultados puedes:
   - Descargar el **PDF**
   - Copiar el **post de Instagram**
   - Descargar la **historia**
   - Descargar el **carrusel**
   - Copiar el **email HTML**
   - Ver y descargar el **video**
   - **Publicar directamente** a Instagram

### Ver historial

Ve a `http://localhost:8000/historial` para ver todos tus listados anteriores y acceder a sus archivos.

---

## Iniciar ListaPro despues de la primera vez

Cada vez que quieras usar ListaPro, solo necesitas:

**Mac/Linux:**
```bash
cd ~/Documents/listapro
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Windows:**
```bash
cd %USERPROFILE%\Documents\listapro
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Y abre `http://localhost:8000` en tu navegador.

> Para detener el servidor, presiona `Ctrl + C` en la terminal.

---

## Estructura del proyecto

```
listapro/
├── main.py                # Servidor principal (FastAPI)
├── config.py              # Configuracion y variables de entorno
├── ai_generator.py        # Generacion de textos con OpenAI
├── pdf_generator.py       # Generacion del PDF
├── instagram_generator.py # Generacion de post para Instagram
├── story_generator.py     # Generacion de historia para Instagram
├── carousel_generator.py  # Generacion de carrusel
├── email_generator.py     # Generacion de email HTML
├── voiceover_generator.py # Generacion de locucion con ElevenLabs
├── video_generator.py     # Renderizado de video con Remotion
├── uploadpost_client.py   # Cliente para publicar en Instagram
├── supabase_client.py     # Almacenamiento (local o Supabase)
├── template_settings.py   # Configuracion de plantilla del agente
├── templates/             # Paginas HTML (formulario, resultados, etc.)
├── static/                # CSS, fuentes e imagenes
├── video/                 # Proyecto Remotion (generador de video)
├── .env.example           # Plantilla de variables de entorno
└── requirements.txt       # Dependencias de Python
```

---

## Problemas comunes

### "No se genera el video"
- Verifica que tengas tu `IMGBB_API_KEY` en el archivo `.env`
- Verifica que Node.js este instalado (`node --version`)
- Verifica que las dependencias de video esten instaladas (`cd video && npm install`)

### "Error al generar textos"
- Verifica que tu `OPENAI_API_KEY` sea valida y tenga credito

### "El servidor no inicia"
- Asegurate de haber activado el entorno virtual (`source venv/bin/activate` o `venv\Scripts\activate`)
- Verifica que el puerto 8000 no este en uso por otra aplicacion

### "Error de red al publicar a Instagram"
- Verifica que tu `UPLOADPOST_API_KEY` sea valida
- El video debe existir y estar completamente generado antes de publicar

---

## Integracion con Supabase (opcional)

Por defecto ListaPro guarda todo localmente en tu computadora. Si quieres almacenamiento en la nube, puedes conectarlo a Supabase:

1. Crea una cuenta en [supabase.com](https://supabase.com/)
2. Crea un proyecto nuevo
3. Copia tu URL y keys de **Settings > API**
4. En tu archivo `.env`, llena los campos de Supabase y cambia `STORAGE_MODE=supabase`
5. Reinicia el servidor

---

## Licencia

Proyecto privado. Todos los derechos reservados.
