# Bitácora del proyecto ReÚsalo Ibero

  

**Materia:** Tópicos Avanzados de Cómputo (LIIS1217) · Otoño 2026

**Proyecto:** API REST de un marketplace de trueque para la comunidad de la Ibero Puebla

**Corte de esta bitácora:** 18 de noviembre de 2026

  

La presente bitácora registra, en orden cronológico, las decisiones de diseño y los avances de implementación del proyecto, así como el trabajo pendiente para concluirlo. Su propósito es documentar la evolución del sistema desde la definición de la idea hasta su estado actual, de modo que cada decisión pueda rastrearse junto con la justificación que la sustentó.

  

---

  

## 1. Registro de avances

  

### 3 de noviembre de 2026 · Selección y definición del proyecto

  

Se analizaron distintas propuestas de proyecto backend vinculadas con el eje transversal de sustentabilidad del curso, entre ellas un monitor de consumo energético, un sistema de centros de acopio y un servicio de carpooling universitario. Se seleccionó un marketplace de intercambio y reúso de objetos dentro del campus, debido a que permite demostrar los contenidos evaluados en el curso (autenticación, roles, persistencia relacional y transacciones) mediante un caso de uso fácilmente comprensible y demostrable en la Expo Ibero.

  

En una primera versión se contempló un sistema de pujas basado en "eco-puntos" como moneda simbólica. Esta propuesta se descartó al precisarse que la puja debía consistir exclusivamente en el ofrecimiento de objetos, es decir, en un trueque. En consecuencia, se eliminó el sistema de puntos y se definieron dos flujos de interacción:

  

1. **Publicación con ofertas:** un usuario publica un artículo y otros le ofrecen artículos propios a cambio; el autor elige la oferta que considera conveniente.

2. **Pedido:** un usuario publica el artículo que busca, con o sin indicar lo que ofrece a cambio, y otros responden con propuestas.

  

Ese mismo día se redactó la propuesta formal del proyecto, que incluyó problemática, objetivos, reglas de negocio, alcances, limitaciones y un plan de trabajo semanal.

  

### 12 de noviembre de 2026 · Bases técnicas y modelo de datos inicial

  

Se definieron las bases técnicas del proyecto: estructura del repositorio, dependencias, entorno con Docker Compose, configuración mediante variables de entorno y un primer módulo de autenticación con JWT. Asimismo, se elaboró un modelo de datos inicial de doce entidades que representaba por separado publicaciones, pedidos, pujas, respuestas, acuerdos, calificaciones, notificaciones y denuncias.

  

### 14 de noviembre de 2026 · Simplificación del modelo e implementación

  

**Simplificación del modelo de datos.** Se determinó que el modelo de doce entidades excedía lo necesario para el alcance del proyecto. A partir del criterio de unificar los conceptos con comportamiento equivalente, el modelo se redujo a seis entidades:

  

| Decisión | Justificación |

| --- | --- |

| Publicaciones y pedidos se integran en `Post` con un campo `type` | Ambos comparten autor, categoría, estado y ciclo de vida |

| Pujas y respuestas a pedidos se integran en `Offer` | Ambas representan una propuesta de intercambio sobre un `Post` |

| El acuerdo deja de ser una tabla y se representa con la `Offer` aceptada | La oferta aceptada ya contiene las partes, los artículos y las confirmaciones |

| Calificaciones, notificaciones y denuncias quedan fuera del MVP | No son indispensables para demostrar el flujo central |

  

**Documentación formal.** Se redactó la documentación académica del proyecto (introducción, metodología, resultados esperados y conclusiones), con referencias bibliográficas sobre economía circular, consumo colaborativo y prácticas de desarrollo de software.

  

**Implementación del backend.** Se implementó la API completa con FastAPI, SQLAlchemy asíncrono y PostgreSQL. La implementación inicial incluyó pruebas automatizadas (25 casos con cobertura cercana al 99%), un Dockerfile para la API, un flujo de integración continua en GitHub Actions y un script de datos de demostración.

  

**Decisión sobre migraciones.** Se evaluó prescindir de Alembic y crear las tablas automáticamente al arrancar la aplicación. Se optó por conservar Alembic, ya que la creación automática no permite modificar tablas existentes sin pérdida de datos y el syllabus contempla el uso de migraciones.

  

**Reestructuración del proyecto.** El código se reorganizó para seguir la estructura de referencia del equipo: módulos planos dentro de `app/`, una carpeta `routes/` para los endpoints y un **patrón repositorio**, en el que `repository.py` define las interfaces abstractas de acceso a datos y `repository_sql.py` las implementa con SQLAlchemy. Con el fin de mantener un alcance intermedio en esta etapa, la versión reestructurada **no incluye** las pruebas automatizadas, el Dockerfile de la API, el flujo de CI ni el script de datos de demostración de la versión anterior.

  

La versión reestructurada se verificó contra un servidor PostgreSQL real mediante una prueba de humo de 14 escenarios, que incluyó el flujo completo de intercambio, la validación de roles y dos aceptaciones simultáneas sobre la misma publicación; todos los escenarios resultaron satisfactorios.

  

**Documentación de uso.** Se elaboró el README del proyecto con la descripción del sistema, la tabla de endpoints y las instrucciones de ejecución, y se agregó un `docker-compose.yml` que levanta PostgreSQL 16 en un contenedor.

  

### 18 de noviembre de 2026 · Documentación técnica

  

Se generaron el diagrama entidad-relación, el diagrama de arquitectura, el resumen ejecutivo del proyecto y la presente bitácora.

  

---

  

## 2. Estado actual del sistema

  

| Componente | Estado | Observaciones |

| --- | --- | --- |

| Autenticación con JWT y correo institucional | Completado | Contraseñas cifradas con bcrypt |

| Control de acceso por roles | Completado | Estudiante, moderador y administrador |

| Artículos, publicaciones y pedidos | Completado | Búsqueda con filtros y paginación |

| Ofertas multi-artículo y acuerdos | Completado | Aceptación transaccional con `SELECT … FOR UPDATE` |

| Moderación | Completado | Ocultar publicaciones y suspender cuentas |

| Indicador de impacto ambiental | Completado | Estimación por peso promedio de categoría |

| Migraciones con Alembic | Completado | Migración inicial verificada en ambos sentidos |

| PostgreSQL en Docker | Completado | Solo la base de datos; la API corre localmente |

| Documentación (README, diagramas, resumen, bitácora) | Completado | Versión del 18 de noviembre |

| Pruebas automatizadas | Pendiente | Existían en la versión anterior; deben adaptarse a la nueva estructura |

| Dockerfile de la API | Pendiente | — |

| Pipeline de CI/CD | Pendiente | — |

| Despliegue en la nube | Pendiente | — |

  

El sistema expone actualmente 26 endpoints. La lista completa se encuentra en el README.

  

---

  

## 3. Trabajo pendiente

  

Las tareas pendientes se ordenan según su prioridad y su correspondencia con las sesiones del syllabus.

  

| Prioridad | Tarea | Relación con el syllabus | Fecha objetivo |

| --- | --- | --- | --- |

| Alta | Adaptar las pruebas unitarias y de integración a la estructura con repositorios y alcanzar una cobertura superior al 70% | Sesiones 23–24 y 30 | 22 de noviembre |

| Alta | Agregar el Dockerfile de la API e incorporarla al `docker-compose.yml` junto con PostgreSQL | Sesión 26 | 23 de noviembre |

| Alta | Configurar el pipeline de GitHub Actions (black, flake8, pruebas y build) | Sesión 28 | 24 de noviembre |

| Alta | Desplegar la API en Render o Railway con variables de entorno seguras | Sesión 27 | 26 de noviembre |

| Media | Script de datos de demostración para la presentación | Sesión 31 | 29 de noviembre |

| Media | Endurecer la API: manejo de errores, límites de peticiones y revisión de seguridad | Sesión 30 | 29 de noviembre |

| Media | Actualizar la documentación técnica (arquitectura, API y despliegue) con el estado final | Sesión 31 (Documentación, 10%) | 1 de diciembre |

| Baja | Calificaciones entre usuarios para construir reputación | Extensión opcional | Según disponibilidad |

| Baja | Notificaciones de coincidencia entre pedidos y publicaciones | Extensión opcional | Según disponibilidad |

  

**Hitos de cierre:**

  

- **3 y 4 de diciembre de 2026:** presentación en la Expo Ibero, requisito obligatorio de acreditación.

- **Sesión 32:** demostración final, sesión de preguntas y entrega del repositorio, la documentación y el despliegue.

  

---

  

## 4. Riesgos identificados

  

| Riesgo | Mitigación |

| --- | --- |

| Tiempo limitado para cubrir pruebas, contenedores, CI y despliegue antes de la Expo | Priorizar estas tareas sobre cualquier extensión funcional |

| Incompatibilidades al contenerizar la API, no verificadas aún | Probar `docker compose up --build` en las máquinas del equipo antes del despliegue |

| Pérdida de cobertura al reintroducir las pruebas en la nueva estructura | Reutilizar los casos de prueba de la versión anterior, ajustando solo las importaciones |

  

---

  

## 5. Declaración de uso de inteligencia artificial

  

De conformidad con la política de transparencia del syllabus, se declara que en el proyecto se empleó un asistente de IA generativa (Claude, de Anthropic) para las siguientes actividades: 

* **Conceptualización y estructuración:** Asistencia para refinar, organizar y asentar las bases de la idea general del proyecto, la cual fue concebida y definida originalmente por el equipo de trabajo. 
* **Modelado de datos:** Apoyo en el diseño, estructuración y validación conceptual de los modelos de datos utilizados en el sistema. 
* **Propuestas de implementación:** Generación de alternativas y sugerencias técnicas para abordar la arquitectura e implementación de diversas funcionalidades. * 
* **Revisión y depuración de código:** Verificación de sintaxis, corrección de indentación y detección de errores menores en el código fuente. 

* **Nota de autoría:** Todas las decisiones críticas de diseño, la lógica central, la integración final y la validación del funcionamiento del proyecto fueron realizadas, supervisadas y verificadas íntegramente por las autoras.
  

> **Pendiente de completar por el equipo:** describir qué partes del resultado se revisaron o modificaron y con qué criterio, tal como lo exige el syllabus.