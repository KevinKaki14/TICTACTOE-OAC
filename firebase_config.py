"""
Configuracion de Firebase
=========================
Pega aqui los datos de TU proyecto de Firebase (Configuracion del
proyecto > tus apps > SDK config, en la consola de Firebase).

Como ya tienes el proyecto de Firebase y el repositorio de GitHub
creados, solo necesitas reemplazar los valores de ejemplo de abajo por
los reales. Es importante usar la "databaseURL" de Realtime Database
(no la de Firestore).

IMPORTANTE sobre GitHub: si vas a subir este repositorio, NO subas tus
credenciales reales a un repositorio publico si prefieres mantenerlas
privadas. La apiKey de un proyecto Firebase de cliente no es secreta
en si misma (esta pensada para ir en apps de escritorio/web), pero el
acceso real a tus datos lo controlan las REGLAS de la base de datos
(ver README.md). Aun asi, si el repo es publico y quieres mas
cuidado, puedes:
  - agregar este archivo a tu .gitignore, o
  - leer estos valores desde variables de entorno.
"""

FIREBASE_CONFIG = {
    apiKey: "AIzaSyDXROuMWRsacCrINp22xDuvpjZXQcQAmpI",
  authDomain: "tick-tack-toe-kaki.firebaseapp.com",
  databaseURL: "https://tick-tack-toe-kaki-default-rtdb.firebaseio.com",
  projectId: "tick-tack-toe-kaki",
  storageBucket: "tick-tack-toe-kaki.firebasestorage.app",
  messagingSenderId: "914692148423",
  appId: "1:914692148423:web:2663473b1ee6c8b2ce02e2",
  measurementId: "G-ER55E9X403"
}
