# ListaPro

Genera automaticamente contenido profesional para tus listados inmobiliarios: PDF, post de Instagram, historia, carrusel, email, video reel con locucion, y publicacion directa a Instagram.

---

## Antes de empezar

Instala estos 2 programas (solo la primera vez):

1. **Node.js** — Descargalo de [nodejs.org](https://nodejs.org/) (boton verde "LTS") e instala
2. **Python** — Descargalo de [python.org/downloads](https://www.python.org/downloads/) e instala
   - **En Windows**: marca la casilla **"Add Python to PATH"** antes de instalar

---

## Instalacion con Claude Code

### Paso 1: Abre Claude Code

Abre Claude Code en tu computadora. Si no lo tienes, descargalo de [claude.ai/download](https://claude.ai/download).

### Paso 2: Dile a Claude que clone el proyecto

Copia y pega esto en Claude Code:

```
Clona el repositorio https://github.com/santmun/inmobiliaria.git en mi carpeta de Documentos, instala todas las dependencias de Python (en un entorno virtual) y de Node (en la carpeta video/), y crea el archivo .env a partir de .env.example
```

Claude va a hacer todo automaticamente.

### Paso 3: Configura tus API keys

Cuando Claude termine, dile:

```
Abre el archivo .env para que yo ponga mis API keys
```

Necesitas poner al menos tu key de **OpenAI** (las demas son opcionales):

| Servicio | Para que sirve | Donde obtenerla |
|----------|---------------|-----------------|
| **OpenAI** (obligatoria) | Genera los textos y descripciones | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| ImgBB | Sube fotos para el video | [api.imgbb.com](https://api.imgbb.com/) |
| ElevenLabs | Voz del locutor en el video | [elevenlabs.io](https://elevenlabs.io/) |
| Suno | Musica original para el video | [suno.com](https://suno.com/) |
| Upload Post | Publicar directo a Instagram | [upload-post.com](https://upload-post.com/) |

> Sin las keys opcionales, el PDF, post, historia, carrusel y email funcionan perfecto. Solo el video y la publicacion a Instagram necesitan las extras.

#### Como obtener tu key de OpenAI

1. Ve a [platform.openai.com](https://platform.openai.com/) y crea una cuenta
2. En el menu, ve a **API Keys**
3. Clic en **"Create new secret key"**
4. Copia la key (empieza con `sk-proj-...`)
5. Pegala en tu archivo `.env`
6. Agrega credito en **Billing** (minimo $5 USD)

### Paso 4: Inicia ListaPro

Dile a Claude:

```
Inicia el servidor de ListaPro
```

### Paso 5: Abre tu navegador

Ve a **http://localhost:8000** y listo, ya puedes generar listados.

---

## Como usar ListaPro

### Primera vez: configura tu plantilla

1. Ve a **http://localhost:8000/plantilla**
2. Sube tu logo y foto de agente
3. Llena tus datos de contacto
4. Clic en **"Guardar Configuracion"**

> Solo se hace una vez. Se guarda para todos tus listados.

### Generar un listado

1. Ve a **http://localhost:8000**
2. Llena los datos de la propiedad
3. Sube las fotos (la primera es la portada)
4. Clic en **"Generar Listado Profesional"**
5. Descarga o copia lo que necesites desde la pagina de resultados

### Las proximas veces

Cuando quieras volver a usar ListaPro, abre Claude Code y dile:

```
Inicia el servidor de ListaPro
```

Y abre **http://localhost:8000** en tu navegador.

---

## Problemas comunes

**"Error al generar textos"** — Tu key de OpenAI no es valida o no tiene credito.

**"No se genera el video"** — Falta la key de ImgBB o Node.js no esta instalado.

**"Error de red al publicar a Instagram"** — Falta la key de Upload Post o el video no termino de generarse.

**"El servidor no inicia"** — Dile a Claude Code: `Revisa por que no inicia el servidor de ListaPro y arreglalo`.

---

## Licencia

Proyecto privado. Todos los derechos reservados.
