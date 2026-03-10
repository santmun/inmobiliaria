# ListaPro

Generador automatizado de listados inmobiliarios profesionales. Crea PDF, video reel, copy para Instagram y mensaje de WhatsApp a partir de los datos de una propiedad.

## Que genera

- **PDF** listo para imprimir con fotos, descripcion y datos de contacto
- **Video Reel** vertical (9:16) con musica IA para Instagram/TikTok
- **Copy para Instagram/Facebook** optimizado con hashtags
- **Mensaje de WhatsApp** listo para enviar

## Requisitos previos

- [Node.js](https://nodejs.org/) (version 18 o superior)
- [Python 3.9+](https://www.python.org/downloads/)
- Una cuenta de [OpenAI](https://platform.openai.com/) con API key

## Instalacion con Claude Code

1. Abre tu terminal y navega a donde quieras instalar el proyecto:

```
cd ~/Documents
```

2. Clona el repositorio:

```
git clone https://github.com/santmun/inmobiliaria.git
cd inmobiliaria
```

3. Abre Claude Code dentro del proyecto:

```
claude
```

4. Pidele a Claude que instale todo:

```
Instala todas las dependencias de este proyecto (Python y Node) y configura el archivo .env con mis API keys
```

Claude va a:
- Crear un entorno virtual de Python e instalar las dependencias
- Instalar las dependencias de Node para el video (Remotion)
- Crear el archivo `.env` a partir de `.env.example`
- Pedirte tus API keys para configurarlas

5. Una vez configurado, pidele que inicie el servidor:

```
Inicia el servidor de ListaPro
```

6. Abre tu navegador en `http://localhost:8000`

## API Keys necesarias

| Servicio | Para que se usa | Donde obtenerla |
|----------|----------------|-----------------|
| OpenAI | Generar descripciones y copy | https://platform.openai.com/api-keys |
| ImgBB | Subir fotos para el video | https://api.imgbb.com/ |
| Suno | Generar musica para el video | https://suno.com/ |

> Las keys de ImgBB y Suno son opcionales. Sin ellas el PDF y los textos funcionan, pero el video no se generara.

## Uso basico

1. Llena el formulario con los datos de la propiedad
2. Sube las fotos (portada + extras)
3. Haz clic en "Generar Listado Profesional"
4. Descarga tu PDF, video y copia los textos

## Estructura del proyecto

```
inmobiliaria/
├── main.py              # Servidor FastAPI (punto de entrada)
├── config.py            # Configuracion y variables de entorno
├── ai_generator.py      # Generacion de textos con OpenAI
├── pdf_generator.py     # Generacion del PDF
├── music_generator.py   # Generacion de musica con Suno
├── video_generator.py   # Renderizado de video con Remotion
├── supabase_client.py   # Cliente de base de datos (opcional)
├── template_settings.py # Configuracion de plantilla
├── templates/           # Paginas HTML
├── static/              # CSS e imagenes
├── video/               # Proyecto Remotion (video)
└── .env.example         # Plantilla de variables de entorno
```

## Integracion con Supabase (opcional)

Por defecto ListaPro guarda todo localmente. Si quieres tener un **historial de listados** y almacenamiento en la nube, puedes conectarlo a Supabase.

### 1. Crea una cuenta en Supabase

Ve a [supabase.com](https://supabase.com/) y crea un proyecto nuevo. Anota la **URL** del proyecto y las **API keys** (anon key y service role key) que aparecen en Settings > API.

### 2. Pidele a Claude que lo configure

Abre Claude Code dentro del proyecto y dile:

```
Configura Supabase para ListaPro. Mi URL es [tu-url] y mis keys son [tus-keys]
```

Claude va a:
- Actualizar tu archivo `.env` con las credenciales de Supabase
- Cambiar `STORAGE_MODE` de `local` a `supabase`
- Crear las tablas necesarias en tu base de datos
- Crear los buckets de almacenamiento para fotos y videos

### 3. Reinicia el servidor

```
Reinicia el servidor de ListaPro
```

Ahora tendras acceso al **Historial** donde puedes ver y descargar todos los listados que hayas generado.
