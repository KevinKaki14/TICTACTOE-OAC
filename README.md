# Tic Tac Toe 3D — Online

Version online del Tic Tac Toe 3D (4x4x4) original del profesor: dos
jugadores en computadoras distintas juegan la misma partida en tiempo
real usando Firebase Realtime Database. Se conserva la misma dinamica
(tablero 4x4x4, elegir X/Y/Z y "Confirmar Jugada"), con un estilo
oscuro y moderno.

Hay dos versiones, usa la que prefieras:

- **`index.html`** — version web. Se juega desde el navegador con un
  simple link, sin instalar nada. **Recomendada.**
- **`tictactoe3d_online.py`** — version de escritorio (Python +
  Tkinter), por si prefieres correrla localmente.

Ambas comparten la misma base de datos de Firebase, asi que hasta
podrias tener a un jugador en la web y al otro en la version de
escritorio, en la misma partida.

---

## Opcion recomendada: jugar desde la web (GitHub Pages)

### 1. Configurar Firebase Realtime Database

1. En la consola de Firebase de tu proyecto, ve a **Build > Realtime
   Database** y crea una base de datos si no la tienes (elige la
   region mas cercana).
2. En la pestaña **Reglas**, pega esto y publica:

```json
{
  "rules": {
    "games": {
      "$room_id": {
        ".read": true,
        ".write": true
      }
    }
  }
}
```

   Esto permite que cualquiera con el codigo de sala lea/escriba esa
   sala especifica (suficiente para jugar entre amigos por codigo).

3. `index.html` ya trae tu configuracion de Firebase incluida (la
   misma que usa la version de escritorio), no necesitas tocar nada
   mas ahi. Si en algun momento cambias de proyecto de Firebase, edita
   el objeto `firebaseConfig` dentro de `index.html`.

### 2. Subir el proyecto a GitHub

```bash
git init
git add .
git commit -m "Tic Tac Toe 3D online"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### 3. Activar GitHub Pages

1. En tu repositorio en GitHub: **Settings > Pages**.
2. En "Build and deployment" → **Source: Deploy from a branch**.
3. Elige **Branch: main**, carpeta **/ (root)** → **Save**.
4. Espera 1-2 minutos. GitHub te da un link como:
   `https://TU_USUARIO.github.io/TU_REPO/`

### 4. Jugar

Comparte ese link con el otro jugador (por WhatsApp, Discord, etc.).
Cada quien lo abre en su navegador, sin clonar ni instalar nada:

- **Jugador 1**: clic en "CREAR PARTIDA" → aparece un codigo de sala
  (ej. `K3F9A`) → se lo pasa al otro jugador. Queda como
  **Jugador 1 (ficha O)**.
- **Jugador 2**: clic en "UNIRSE A PARTIDA" → escribe el codigo →
  queda como **Jugador 2 (ficha X)**.

El tablero se sincroniza solo. Cuando es tu turno, haz clic en una
celda (se marca en dorado) y pulsa **CONFIRMAR JUGADA**. Mientras no
sea tu turno, el boton queda deshabilitado. Al terminar la partida,
cualquiera de los dos puede pulsar **NUEVA PARTIDA** para reiniciar el
mismo tablero sin salir.

> Nota de seguridad: la `apiKey` de Firebase que queda visible en
> `index.html` no es secreta (todas las apps web de Firebase la
> exponen asi); lo que realmente protege tus datos son las reglas de
> la base de datos de arriba. Con esas reglas, cualquiera que adivine
> o vea un codigo de sala de 5 caracteres podria leer/escribir esa
> sala — aceptable para una partida casual entre conocidos.

---

## Alternativa: version de escritorio (Python)

### Archivos
- `tictactoe3d_online.py` — el juego.
- `firebase_config.py` — credenciales de tu proyecto Firebase.
- `requirements.txt` — dependencias de Python.

### Instalar y correr

```bash
pip install -r requirements.txt
python tictactoe3d_online.py
```

Cada jugador necesita Python instalado y una copia de estos 3
archivos (o clonar el repo). El resto del flujo (crear/unirse con
codigo, turnos, nueva partida) es igual a la version web.

## Notas

- El codigo de sala solo vive mientras exista ese nodo en la base de
  datos; puedes borrarlo manualmente desde la consola de Firebase si
  quieres limpiar partidas viejas.
- El icono `cubo.ico` (version de escritorio) es opcional: si no
  existe en la carpeta, el juego simplemente arranca sin icono
  personalizado.
