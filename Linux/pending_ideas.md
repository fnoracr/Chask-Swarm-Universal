# Ideas para el Proyecto Chask Swarm

Estas ideas deben recordarse diariamente vía Telegram, 5 minutos después del inicio del sistema, hasta que sean implementadas.

## 1. Red Local (Enjambre de Colaboración)
- Al instalarse en el equipo de un usuario, Enjambre debe preguntar si desea crear o unirse a un enjambre local.
- **Crear:** Generar un token único y guardarlo (consultable/modificable desde el panel web).
- **Unirse:** Solicitar el token de red y establecer contacto con otros enjambres locales.
- **Objetivo:** Colaboración entre instancias, distribución de tareas y ayuda mutua en red local.

## 2. Gestión de Usuarios y Privacidad
- Implementar perfiles: Administrador vs. Usuarios Normales.
- Derechos y herramientas diferenciadas según el tipo de usuario.
- **Diferenciación por edad:**
  - Mayores de edad: Privacidad total.
  - Menores de edad: Actividad supervisable por el administrador.

## 3. Red Mundial de Enjambres
- Opción para añadir el enjambre local a una red mundial gestionada desde servidores centrales de Chask Swarm.

---
---
## Análisis Crítico y Objeciones (Visión 10.000M€)
*Estas objeciones deben recordarse siempre que se retomen estas ideas para evitar caer en trampas técnicas y legales.*

### 1. Riesgos de la Red Local
- **Seguridad:** Superficie de ataque interna masiva. Un token robado compromete todo el enjambre local.
- **Consistencia:** Conflictos de escritura simultánea. Requiere protocolos de consenso complejos (Raft/Paxos) para evitar corrupción de datos.

### 2. Riesgos de Gestión de Usuarios
- **Deuda Técnica:** Complejidad exponencial al implementar capas de permisos tipo SO sobre scripts de IA.
- **Falsa Privacidad:** Riesgo de fugas de datos entre perfiles por bugs en el sistema de permisos (ACL).

### 3. Riesgos de la Red Mundial
- **Centralización:** Punto único de fallo y objetivo crítico para hackeos.
- **Compliance Legal:** Pesadilla de regulaciones (GDPR, CCPA) y responsabilidad civil/penal por datos de terceros.

*Estado: Ideas archivadas para visión de futuro con presupuesto masivo.*
