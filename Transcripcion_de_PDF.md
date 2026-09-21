Aquí tienes la transcripción completa del documento proporcionado, organizada según el contenido original y citando la fuente de cada segmento según las directrices establecidas.

---

## DESARROLLO DE UN SIMULADOR DE OPERACIONES DE TRANSPORTE PÚBLICO EN UN AMBIENTE DE MICROSIMULACIÓN DE TRÁFICO

**(SIMTRANSIT)**

**Vanessa Burgos, Rodrigo Fernández y Cristián E. Cortés**
Departamento de Ingeniería Civil, Universidad de Chile
Casilla 228-3, Santiago, Fono/Fax 56-2-6894206
vburgos@ing.uchile.cl, rodferna@ing.uchile.cl, ccortes@ing.uchile.cl

### RESUMEN
245

Los modelos microscópicos de simulación de tránsito o microsimuladores de tráfico constituyen en la actualidad la herramienta más avanzada de representación de la circulación vehicular en una red de transporte. Sin embargo, la mayoría de ellos están orientados a modelar el comportamiento de los automóviles y en consecuencia, los sistemas de transporte público de ruta fija son modelados en forma complementaria, como una forma de hacer más realista la interacción entre automóviles y buses por el derecho a uso compartido de vías, pero siempre considerando al usuario de transporte privado como centro de análisis y simulación.

En la actualidad, producto del desarrollo de tecnologías de información y comunicaciones, la modelación y simulación de sistemas de transporte público de operación compleja a nivel microscópico es una necesidad, por lo cual en este trabajo se desarrolla un enfoque de simulación híbrido que permite a un nivel, simular adecuadamente la operación microscópica de los vehículos (con la ayuda de un conocido microsimulador de tráfico), y a un segundo nivel, modelar apropiadamente la operación, elementos físicos y agentes involucrados en sistemas sofisticados de transporte público, y sus interacciones. La conexión entre ambos niveles se hace vía API (Application Programming Interface). Se ilustra la aplicación de la modelación propuesta con un ejemplo sencillo, cerrando con potenciales aplicaciones y extensiones del enfoque.

Actas del XII Congreso Chileno de Ingeniería de Transporte. Valparaíso, 17 al 21 de Octubre de 2005

---

### 1. INTRODUCCIÓN

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

Los modelos microscópicos de simulación de tránsito o microsimuladores de tráfico constituyen en la actualidad la herramienta más avanzada de representación de la circulación vehicular en una red de transporte. Basados en la Teoría de Seguimiento Vehicular desarrollada en la década de 1950 (TRB, 1997), permiten, gracias a las actuales potencialidades computacionales, reproducir en detalle los comportamientos individuales de los vehículos. Un análisis de la mayoría de estos modelos se reporta en el proyecto de la Unión Europea SMARTEST (Simulation Modelling Applied to Road Transport European Scheme Tests), el que estudió las características de 32 microsimuladores de tráfico (Fox, 2000; SMARTEST, 1999).

Los microsimuladores de tráfico se utilizan en la actualidad en la planificación del tráfico, así como para evaluar sistemas de transporte inteligentes (ITS) (Boxill and Yu, 2000; Fox, 2000). Prácticamente cada grupo de investigación de tráfico en el mundo ha desarrollado o adaptado su propio software. Sin embargo, la mayoría de estos desarrollos están orientados a modelar el comportamiento de los automóviles, y en ellos los sistemas de transporte público de ruta fija son modelados en forma complementaria, como una forma de hacer más realista la interacción entre automóviles y buses por el derecho a uso compartido de vías, pero siempre considerando al usuario de transporte privado como centro de análisis y simulación. Los pasajeros de transporte público no tienen identidad propia y por ende no pueden considerarse como parte de una evaluación de uno o un grupo de proyectos estudiados en detalle con microsimulación.

En la actualidad, en parte debido al creciente desarrollo de tecnologías de información y comunicaciones (sistemas de identificación de vehículos, AVL, información en tiempo real a usuarios y operadores, interacción dinámica entre vehículos y entre vehículos y los controladores, etc.), tenemos la certeza que todos estos elementos hacen muy atractivo el desarrollo de sistemas de transporte público más eficientes, tanto para los usuarios como para los operadores, lo cual hace imprescindible desarrollar ambientes de microsimulación apropiados para modelar sistemas más completos, que consideren la interacción entre todos los agentes involucrados, cuales son usuarios y operadores de todos los modos de transporte, incluyendo todas las entidades e implementos relacionadas con la operación del transporte público (pasajeros, vehículos, terminales, paraderos, etc.).

Revisando la literatura, es fácil darse cuenta que el mayor problema para evaluar operaciones complejas de sistemas de transporte público con estas características a nivel microscópico, proviene de la pobre representación de dichos sistemas dentro de los microsimuladores de tráfico de uso comercial. Además, es un hecho que los vehículos de transporte público se comportan distinto al resto del tráfico, pero no son modelados con suficiente detalle como para reflejar estas diferencias (SMARTEST, 1999: Areas requiring improvements), lo cual nos ha motivado a desarrollar una herramienta de simulación que considere esta premisa, y que a través de un enfoque de simulación híbrido, considere en detalle las operaciones de transporte público de ruta fija en interacción con el resto del sistema. En este nuevo enfoque las decisiones respecto a estrategias de control en tiempo real, así como cualquiera decisión de itinerario, son tomadas a un nivel agregado, mientras que la operación de los vehículos y el detalle de la operación de terminales y paraderos es realizada a un nivel detallado utilizando un conocido paquete comercial de microsimulación de tráfico (PARAMICS), ambos niveles progresando en forma simultánea durante el tiempo de simulación. El enfoque propuesto se detalla en la sección 3 más adelante.

---

### DESARROLLO DE UN SIMULADOR DE OPERACIONES DE TRANSPORTE PÚBLICO EN UN AMBIENTE DE...

247

Llamaremos SIMTRANSIT al primer prototipo de un motor de simulación que permite modelar en forma detallada la interacción de las distintas componentes de los sistemas de transporte público de ruta fija, con el resto del sistema de transporte. Este enfoque recoge algunas ideas del esquema de simulación híbrido propuesto por Jayakrishnan et al. (2003) y perfeccionado más adelante por Cortés et al. (2005), que incorpora la modelación y detalles de la operación del transporte público en un nivel de simulación paralelo, pero conectado en tiempo de simulación real con la microsimulación detallada en PARAMICS. Como primer objetivo, en este artículo describiremos un primer módulo ya desarrollado de SIMTRANSIT, que permite la integración de la modelación detallada de paraderos de transporte público de superficie, tal como se sugiere en el desarrollo del microsimulador de paraderos PASSION (Fernández y Planzer, 2002), con el microsimulador de tráfico PARAMICS, por medio del uso de API (Application Programming Interface).

En lo que sigue, se revisa cómo se ha incorporado el transporte público en algunos microsimuladores de tráfico desde la perspectiva de la generación de vehículos de transporte público y el tratamiento de las operaciones en los paraderos. Posteriormente, se desarrolla nuestra proposición alternativa de modelación, basado en el primer módulo de SIMTRANSIT orientado a la modelación de paraderos, conectado con el microsimulador PARAMICS. Se presenta un ejemplo simple de aplicación, cerrando con una síntesis y una discusión de los potenciales desarrollos futuros de SIMTRANSIT.

### 2. REVISIÓN DE LA LITERATURA: MODELACIÓN DE TRANSPORTE PÚBLICO USANDO MICROSIMULACIÓN

De la revisión bibliográfica que se ha llevado a cabo, se pueden distinguir tres enfoques para enfrentar la modelación microscópica de sistemas de transporte público: en primer término, los distintos microsimuladores de tráfico comerciales cuentan actualmente con formas de modelación por defecto, de limitada flexibilidad cuando se intenta modelar operaciones complejas en paraderos y terminales, transferencia de pasajeros, etc.; un segundo enfoque, y probablemente el más utilizado en la literatura se basa en desarrollar técnicas de modelación sofisticadas para poder simular detalles de operación de transporte público no incluidas en las opciones por defecto; finalmente, existen experiencias de simulación de operaciones de transporte público utilizando funciones externas a los simuladores (a través de APIs), con lo cual es posible modelar con mucho detalle y con gran flexibilidad cualquier tipo de operación que el modelador desee, dependiendo de la flexibilidad de la interacción entre el software y las componentes externas conectadas vía API (Application Programming Interface).

A continuación se hace una breve descripción de estas tres formas de enfrentar el problema, desde lo más básico a lo más sofisticado. Con estos antecedentes, en la sección 3 se presenta el enfoque propuesto, que corresponde a una aplicación del tercer enfoque, que resulta ser el más flexible y con mayor potencialidad de desarrollo futuro.

---

248

### 2.1 Herramientas de simulación de transporte público establecidas por defecto en los microsimuladores de tráfico comerciales más relevantes

En esta sección se presentan dos aspectos fundamentales que describen la incorporación de sistemas de transporte público en los diferentes software comerciales de microsimulación disponibles en el mercado. Centraremos la discusión en la generación y manejo de vehículos, así como la operación de paraderos, en los simuladores más relevantes: AIMSUM/2 (TSS, 2004), CORSIM (CORridor SIMulation; FHWA, 1996), DRACULA (Dynamic Route Assignment Combining User Learning and microsimulAtion; Liu, 2003), VISSIM (Verkehr In Stadten SIMulation; PTV, 2003) y PARAMICS (PARAllel MICroscopic Simulation; Quadstone, 2004).

En el caso de AIMSUM/2, los vehículos de transporte público se agrupan en una "clase" que permite definir el uso de pistas exclusivas. Éstos son generados con igual frecuencia o utilizando un horario predeterminado para cada línea; en tal caso, el usuario debe definir la desviación estándar de los tiempos de entrada a la red. La longitud de los paraderos determina su capacidad de almacenamiento para albergar a los buses que se detienen al mismo tiempo. Si no caben, éstos deben esperar en las pistas asignadas al tráfico, produciendo su bloqueo.

CORSIM, por otra parte, genera los vehículos de transporte público con una frecuencia fija por línea dada por el usuario. Puede modelar pistas para vehículos de alta ocupación o HOV (High Occupancy Vehicles), por ejemplo, buses en la mediana o junto a la acera.

DRÁCULA a su vez, considera seis tipos de vehículos, incluidos buses y buses guiados, los que tienen la opción de usar vías exclusivas. Los vehículos de transporte público se generan según una frecuencia fija. Éstos tienen una capacidad ilimitada y son abordados por todos los pasajeros que esperan en un paradero, independiente de su ruta.

En VISSIM la generación de vehículos de transporte público se realiza mediante una frecuencia fija.

Finalmente en PARAMICS la generación de vehículos de transporte público puede ser efectuada a través de una frecuencia fija o un horario predefinido para cada línea. Tal como en otros microsimuladores, las líneas o recorridos tienen una ruta fija que incluye una secuencia de nodos, arcos y paraderos en los que buses se detendrán para efectuar la transferencia de pasajeros. El usuario puede definir un área de parada en la cual pueden acomodarse varios buses simultáneamente.

Respecto de la detención en paraderos, AIMSUM/2 no posee un modelo para generar la demanda de pasajeros del transporte público. Por ende, los tiempos detenidos en paraderos siguen una distribución normal, cuya media y desviación estándar debe entregarla el usuario para cada línea que utiliza un paradero dado. En consecuencia, una de las principales deficiencias del modelo es que no da cuenta de las interacciones entre la demanda de pasajeros y el flujo de vehículos de transporte público.

CORSIM tampoco posee un modelo de demanda de pasajeros, por lo que el tiempo de detención en paraderos debe definirse antes de cada corrida. Este tiempo puede tener una fluctuación aleatoria dada por alguna distribución.

En DRÁCULA la demanda de pasajeros en cada paradero se asume como un valor promedio horario. Así, el tiempo de detención de los buses se calcula como $T_{d}=a_{1}(1-p_{s})N+a_{2}p_{s}N+b$, donde N es el número de pasajeros acumulados en el paradero, $p_{s}$ es la proporción de pasajeros que usan pases estacionales, $a_{1}$ es el tiempo de subida de los pasajeros que pagan la tarifa en

---

### DESARROLLO DE UN SIMULADOR DE OPERACIONES DE TRANSPORTE PÚBLICO EN UN AMBIENTE DE...

249

efectivo, $a_{2}$ es el tiempo de subida de quienes usan pases, y b es el tiempo ocupado en abrir y cerrar las puertas del bus..Se asume, además, que no existe demora debido a los pasajeros que bajan en el paradero.

En VISSIM el tiempo detenido en paraderos se pueden calcular de tres maneras: mediante una distribución normal, con una distribución definida por el usuario, o como un cálculo explícito, que depende de la demanda promedio horaria de pasajeros por línea en cada paradero y el número de pasajeros que baja, como un porcentaje de la tasa de ocupación del vehículo. En el último caso, el modelo computa el tiempo detenido como función de los tiempos marginales de subida y bajada de pasajeros y el tiempo muerto ocupado en la apertura y cierre de puertas del bus, y es capaz de discriminar según si las operaciones de subida y bajada son secuenciales o simultáneas. Si el área de parada es suficientemente larga, puede acomodar a más de un vehículo detenido en el paradero al mismo tiempo. En tal caso, los buses se pueden adelantar unos a otro para entrar o salir del paradero. Adicionalmente, se puede dar prioridad sobre el resto del tráfico para que los vehículos de transporte público puedan salir de un paradero en bahía.

Finalmente, en PARAMICS el tiempo de detención de los buses en los paraderos depende de la demanda de pasajeros, la que sólo puede representarse por medio de una tasa de llegada constante por cada línea. Además, debe definirse para cada línea, el número de pasajero que descenderá en cada paradero, esto se hace como un porcentaje de la tasa de ocupación del bus. Por lo tanto, el tiempo de detención de los vehículos de transporte público en paraderos se calcula como $T_{g}=max\{(\frac{P_{A}t_{s}}{2}+5);(P_{B}t_{s}+5)\}$ , donde $P_{A} y P_{B}$ son el número de pasajeros que descienden y suben respectivamente y $t_{s}$ es el tiempo marginal de subida de los pasajeros. Como puede apreciarse, este modelo asume que el tiempo marginal de bajada es la mitad del tiempo marginal de subida y que las operaciones de subida y bajada de pasajeros se efectúan de manera simultánea. $T_{d}$ también puede modelarse en PARAMICS a través de un valor constante o distribuido normalmente con una media y desviación estándar entregadas por el usuario.

### 2.2 Microsimulación de sistemas de transporte público a partir de herramientas disponibles en microsimuladores de tráfico comerciales

En esta sección describimos el intento de algunos investigadores de sobrellevar las deficiencias de los paquetes comerciales, para lo que han inventado algunas técnicas aproximadas (trucos de simulación) con el objetivo de llevar a cabo simulación de sistemas de transporte público. Para la simulación de LRT (Light Rail Transit) en Venglar el al. (1995) usando NETSIM (que forma parte de CORSIM), la codificación de la red tuvo que ser modificada para tener menor cantidad de nodos y diferentes configuraciones determinando distintas preferencias en intersecciones. Para simular sistemas del tipo BRT (Bus Rapid Transit) en Inga (2001), usando VISSIM, el corredor fue dividido en secciones más cortas para modelar una pista exclusiva en la mediana de una vía. Los vehículos son codificados como un tipo de vehículo exclusivo en el modelo. Otro ejemplo de simulación de BRT usando VISSIM se encuentra en Multisystems Inc. (2000). La red fue codificada en forma similar al caso anterior, pero aquí algunos semáforos adicionales fueron incorporados para mantener a los vehículos en lugares predefinidos en la red,

---

250

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

y así mantener un intervalo constante. Otro ejemplo interesante es la simulación de un sistema de tranvías usando PARAMICS para la ciudad de Toronto (Abdulhai et al., 2002). Las líneas fueron codificadas sobre la red existente y las paradas fueron codificadas como nodos adicionales con semáforos virtuales afectando sólo a los tranvías. Por lo tanto, la duración del tiempo de parada quedó como función de la demanda.

La interacción entre modelos microscópicos y macroscópicos también ha sido reportada en la literatura. Por ejemplo, en Siegel et al. (2003) se presenta una metodología en la que se utiliza de manera integrada un enfoque micro de modelación (GETRAM) con un enfoque macro (ESTRAUS) para representar la operación de servicios de buses urbanos operando en corredores exclusivos. En general, cuando se refiere al transporte público, la microsimulación de tráfico se ha concentrado en la evaluación de semáforos actuados por buses o para analizar el efecto de pistas exclusivas en la regularidad del servicio (por ejemplo, Abdulhai et al, 2002; Lindau, 1983). Esto ha llevado a supuestos simplificatorios respecto del comportamiento de los buses en la calle. Básicamente, éstos son considerados como "autos largos" que se detienen entre intersecciones a lo largo de su ruta, provocando la misma reacción del resto del tráfico que un auto que se detiene en una pista de circulación. La realidad, no obstante, es más compleja y situaciones como el acomodo de los vehículos para adelantar a un bus detenido sin cambiar de pista son frecuentes. Esta situación, denominada "squezing behaviour", ha sido reconocida y modelada por Silva (2000, 2001).

El mismo autor (Silva, 2001), en una sistemática revisión, encontró que las operaciones en paraderos de buses son pobremente representadas en la mayoría de los microsimuladores de tráfico. Éstos asumen que un paradero es un lugar situado en la mitad de una cuadra donde los buses se detienen un tiempo fijo (o aleatorio) para transferir pasajeros; y, por ende, el tiempo detenido no está necesariamente ligado con alguna demanda de pasajeros o con su variación en cortos períodos. Este supuesto sería equivalente a aceptar que todas las demoras en las intersecciones de una red son idénticas. Igualmente inapropiado sería asumir que son aleatorias, independientes del patrón de tráfico en la intersección.

Finalmente, Chien et al. (2000) encontraron una forma de generar pasajeros según un proceso de Poisson, usando CORSIM. No obstante este avance, la dinámica de la microsimulación se pierde tras este supuesto. Como lo establecen Fernández y Tyler (2004) "se ha demostrado que las llegadas de pasajeros a los paraderos no siempre siguen un proceso de Poisson, como se suele asumir. En tal caso, una distribución genérica no sirve para modelar las interacciones en paraderos. Esto lleva a la necesidad de la simulación microscópica de las interacciones entre pasajeros, buses y tráfico para entender este problema aparentemente simple. Postulamos que el desconocimiento de este hecho ha llevado, en muchos casos, a paraderos mal diseñados".

### 2.3 Microsimulación de sistemas de transporte público usando APIs

El surgimiento de un enfoque más flexible y genérico es producto de las observaciones resumidas en el punto anterior en conjunto con otros aspectos, tales como: la necesaria definición de puntos predefinidos de parada como en todos los casos descritos en 2.2, que en el caso de sistemas de ruta y paradas variables (tales como taxis, taxis colectivos, dial a ride, etc.) no es un supuesto razonable; la imposibilidad de incorporar algoritmos y decisiones de ruteo e itinerario en tiempo real; la incapacidad de contar con una correcta modelación y evaluación de pasajeros y

---

### DESARROLLO DE UN SIMULADOR DE OPERACIONES DE TRANSPORTE PÚBLICO EN UN AMBIENTE DE...

251

conductores; etc. Todo lo anterior, debido a que finalmente los paquetes comerciales de simulación han sido generados basándose en la operación del transporte privado, y en ellos el transporte público es una componente adicional complementaria al fundamento básico de los modelos incluidos en ellos.

Motivados por esta necesidad de generar un mejor ambiente de simulación para los sistemas de transporte público, Jayakrishnan et al. (2003) propusieron un enfoque híbrido de simulación orientado a la microsimulación de sistemas personalizados de transporte público del tipo dial-a-ride, a dos niveles. Ellos definen un nivel abstracto, con una red simplificada (ABSNET), y una serie de estructuras de datos para hacerse cargo de los vehículos y de los clientes del servicio. La microsimulación se hacía a un nivel más detallado, conectado con el nivel abstracto vía funciones que son actualizadas en cada paso de tiempo de simulación, o cuando ocurre un evento relevante que afecte el estado del sistema (llegada de un nuevo cliente, llegada de un vehículo a una parada, etc.). Cortés et al. (2005) implementaron este enfoque y evaluaron varios sistemas flexibles combinados con sistemas del tipo BRT utilizando PARAMICS para la microsimulación. Los ambientes eran conectados vía el uso de APIs y sus funciones asociadas, disponibles en las últimas versiones de PARAMICS.

Este último enfoque es un punto de partida importante en el desarrollo del modelo de simulación que hemos llamado SIMTRANSIT. La diferencia de este nuevo simulador es que no hay necesidad de codificar una red abstracta paralela, pues las rutas son exógenas y las paradas están predefinidas. El objetivo entonces es modelar correctamente operaciones específicas de transporte público de ruta fija que no han sido contempladas al nivel de detalle que se requiere. A continuación se presenta el primer módulo de simulación de SIMTRANSIT, que llamaremos SIMTRANSIT_S, y que básicamente da cuenta de la correcta operación en paraderos y la interacción que allí se produce entre pasajeros y vehículos.

### 3. SIMTRANSIT: INCORPORACIÓN EN PARAMICS DE UN NUEVO ENFOQUE PARA MODELAR LA OPERACIÓN DEL TRANSPORTE PÚBLICO

El modelo SIMTRANSIT se ha concebido como una forma de mejorar significativamente tres aspectos básicos de la modelación de la operación del transporte público de ruta fija en microsimuladores de tráfico. El primero se relaciona con los vehículos de transporte público, en particular los buses, a los cuales se les asigna nuevas características que permiten incorporar nuevos modelos así como también obtener estadísticas más detalladas del nivel de servicio con el que operan. El segundo aspecto de este modelo consiste en incorporar en la simulación microscópica a los pasajeros, los que son considerados como nuevos entes individuales en la simulación y por lo tanto tienen asociadas una serie de características tales como paraderos de origen y destino, conjunto de líneas comunes o atractivas, tiempo de entrada a la red y tiempos marginales de subida y bajada de los vehículos. Esta innovación permite obtener una serie de estadísticas del nivel de servicio de los usuarios del sistema. Por último, al considerar a los pasajeros como individuos, se pueden incorporar nuevos modelos específicos para mejorar la representación de la interacción entre ellos y los vehículos, en particular, en los paraderos (terminales), así como cuantificar estadísticas individuales o bien incorporar modelos de comportamiento.

---

252

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

Este nuevo enfoque puede ser potencialmente aplicado en cualquier microsimulador de tráfico, sin embargo, para la incorporación de los nuevos modelos se requiere obtener y entregar datos a la simulación en tiempo real y por lo tanto el microsimulador escogido debe contar con estas facilidades, tales como las API con las que cuentan algunos microsimuladores. El microsimulador de tráfico escogido para aplicar el enfoque fue PARAMICS v5.0 pues se dispone de la licencia académica del módulo llamado Programmer que permite a los usuarios acceder a datos de la simulación y personalizar muchas de las características del programa. La interacción entre PARAMICS y alguna aplicación externa es hecha a través de un archivo .dll generado a partir de un programa que contiene una serie de funciones del módulo Programmer. La experiencia en la utilización de PARAMICS por parte de algunas consultoras puede ser aprovechada para obtener la calibración de los parámetros del microsimulador. Esta calibración puede ser actualizada siguiendo el enfoque propuesto en Quadstone (2003).

El nuevo módulo SIMTRANSIT_S, desarrollado para implementar parte de este nuevo enfoque y que se conecta vía API, ha sido construido en lenguaje de programación C y utiliza la misma red codificada en PARAMICS. Utiliza también los mismos buses del microsimulador y deben estar además diseñadas las líneas o recorridos que formarán el sistema de transporte público a modelar y sus respectivas rutas. Las rutas, tal como en el modelo original, deben ser fijas y comenzar y terminar en un punto de la red representado con un paradero en el que no se efectúa transferencia de pasajeros. Finalmente, deben quedar establecidos los paraderos que serán parte de las rutas de cada línea y sus características, tales como longitud e identificación.

SIMTRANSIT_S requiere además una serie de datos externos que son leídos por el programa antes de comenzar la simulación en PARAMICS desde archivos de texto y almacenados en un conjunto de estructuras. Estos datos están relacionados con características de los paraderos, con la generación y características de vehículos de transporte público y de pasajeros. Cuando los vehículos de transporte público entran a la red son etiquetados como vehículos tag con una serie de características tales como: número de identificación, el número y función de sus puertas, la capacidad nominal y disponible. Esta información es almacenada en una estructura de datos que además permite guardar la línea o recorrido a la que pertenece, los tiempos de partida y término de su recorrido por la red, los tiempos de llegada y salida de paraderos, las detenciones en colas y otras estadísticas. Además, esta estructura almacena el "head" de una lista con la identificación de los pasajeros que ocupan cada vehículo y que se modifica durante la simulación.

La información relacionada con los usuarios también es almacenada en una estructura. Los datos que caracterizan a cada pasajero como un ente más en PARAMICS son principalmente: un número de identificación, los paraderos de origen y destino que pueden estar dentro o fuera de la red, las líneas comunes o atractivas que está dispuesto a tomar para llegar a su destino, los tiempos marginales de subida y bajada y un tiempo de llegada a la red. En esta estructura es posible también almacenar estadísticas de los usuarios del sistema, por ejemplo, tiempos de espera y de viaje sobre el vehículo.

La interacción entre los usuarios y los vehículos de transporte público se efectúa en los paraderos. Cada vez que un bus llega a un paradero se verifica qué pasajeros deben descender de él y se

---

### DESARROLLO DE UN SIMULADOR DE OPERACIONES DE TRANSPORTE PÚBLICO EN UN AMBIENTE DE...

253

busca a aquellos que tienen como origen esa estación y que están ya esperando en ella. Estos usuarios subirán al bus dependiendo de la capacidad disponible del vehículo y en orden de llegada.

El tiempo de detención de cada bus en cada paradero, dependerá, por lo tanto, de cuánto demore la transferencia de pasajeros, la que a su vez depende no sólo del número de pasajeros que suben o bajan, sino que también del número y función de las puertas del vehículo, su tasa de ocupación y el grado de congestión del andén. El tiempo de detención de un bus i (ti) por transferencia de pasajeros se calcula utilizando una variación del modelo presentado y ya calibrado por Gibson et al. (1997):

$t_{i}=\beta_{o}+\beta_{o}^{\prime}\partial_{1}+max_{j}\{\sum_{pr}[\beta_{1}^{ps}+\beta_{i}^{pi}\partial_{1}+\beta_{i}^{pr^{\prime}}\partial_{2}(i)]+\sum_{pb}[\beta_{2}^{pb}exp(-\beta_{2}^{pb^{\prime}}PB_{ij})+\beta_{2}^{pb^{\prime}}\partial_{3}(i)]\}$ (1)

donde,
ps, pb: Identificación del pasajero que sube o baja
PBij: Número de pasajeros que baja del bus i por la puerta j
$\partial_{1}$: Variable muda que vale 1 si el andén está congestionado y 0 en otro caso
$\partial_{2}(i)$: Variable muda que vale 1 si al bus i suben 4 ó más pasajeros y 0 en otro caso
$\partial_{3}(i)$: Variable muda que vale 1 si el bus i va lleno y 0 en otro caso
: Vector de parámetros a calibrar que incluyen tiempos marginales de subida y bajada

Cuando finalizan estas operaciones, el bus abandona el paradero dependiendo de las condiciones de tráfico a la salida por su propia pista o por la pista adyacente, utilizando para ello los modelos aceleración y cambio de pista propios de PARAMICS. En ese instante, se modifica la capacidad disponible del bus, las estadísticas de los pasajeros que suben y bajan a él y el listado de pasajeros que lleva el vehículo.

La Figura 1 muestra un esquema de la interacción entre SIMTRANSIT_S y PARAMICS. Las flechas que ligan ambos ambientes de simulación representan aquellas funciones que se retroalimentan de una lado para otro durante la simulación, cada vez que se requiere actualizar alguna estadística, o bien trasmitirle a PARAMICS el tiempo correcto de detención de los buses en los paraderos, con el fin de que estos permanezcan en los paraderos un tiempo consistente con la operación de transferencia de pasajeros. Notar que en el ambiente de simulación del lado derecho, se han creado dos estructuras de datos, una para controlar los vehículos y la otra para trabajar con los pasajeros individualmente. En la siguiente sección, presentamos un ejemplo simple de aplicación de este módulo a un caso simulado de un tramo del corredor Av. Los Leones, entre Av. Carlos Antúnez y Av. Pocuro en Santiago.

### 4. APLICACIÓN DE SIMTRANSIT S

El siguiente ejemplo ilustra las diferencias en los resultados obtenidos utilizando PARAMICS en su versión original y los que se obtienen incluyendo el módulo de paraderos de SIMTRANSIT. Un esquema del tramo del corredor de transporte público utilizado en las simulaciones se muestra en la Figura 2.

---

**Figura 1: Interacción entre PARAMICS y SIMTRANSIT_S.**
*(Nota: El diagrama de flujo presente en el documento muestra el proceso de "INICIO SIMULACIÓN" y "GENERACIÓN DE BUSES SOBRE LA RED" en PARAMICS, que interactúa con la creación de estructura de datos (buses/pasajeros) en SIMTRANSIT_S, seguido de la modelación de transferencia y actualización de estadísticas.)*

**Figura 2: (a) Vía exclusiva de transporte público. (b) Detalle del paradero 1.**
*(Nota: El esquema muestra una vía con paradas y vehículos circulando.)*

---

254

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

Las intersecciones de la Figura 2a están reguladas por semáforo y los paraderos indicados poseen un sitio de detención. Se ha diseñado una única línea o recorrido cuyos buses son generados cada un minuto y posee una demanda total de subida de 120 y 60 [pas/h] en el primer y segundo paradero respectivamente. No existe demanda de bajada en ninguno de los dos paraderos. La llegada de los usuarios en PARAMICS sólo puede ser representada a través de una tasa constante, en cambio, utilizando SIMTRANSIT_S es posible especificar un tiempo de llegada particular para cada pasajero en cada paradero. Para reflejar con mayor detalle las diferencias, se ha simulado en SIMTRANSIT_S el efecto de llegada de pasajeros en forma de pelotón.

En la Figura 3 se muestran los intervalos de llegada y salida desde los paraderos entre dos buses sucesivos obtenidos utilizando los dos enfoques. Los buses entran a la red con un intervalo de 60

---

255

[s] que aumenta al llegar al primer paradero a 110 [s]. En PARAMICS, los buses salen del primer paradero con un intervalo muy similar al registrado a su llegada, pues son semejantes los tiempos de detención para transferencia de pasajeros de cada uno (12,5 y 14 [s] respectivamente). Por otra parte, en SIMTRANSIT_S, aunque la diferencia entre los tiempos de llegada de los buses al primer paradero es igual a la obtenida usando PARAMICS, el intervalo a la salida de él varía notoriamente. Esto es debido a que el primer bus que llega al paradero 1 no encuentra pasajeros y por lo tanto no se detiene, en cambio, el segundo bus encuentra pasajeros y debe detenerse 25 [s] para que ellos puedan subir. Esta diferencia provoca un aumento en el intervalo de salida entre los vehículos y este aumento se traduce en un incremento en el intervalo de llegada al segundo paradero y por lo tanto, en un servicio más irregular que el modelado en PARAMICS.

El presente ejemplo ilustra de alguna manera, que incluso para un caso simple la implementación de un modelo más flexible de simulación permite representar de mejor manera la simulación de operaciones complejas de transporte público, no contempladas en paquetes comerciales disponibles en el mercado.

**Figura 3: Intervalo entre buses sucesivos a la llegada y salida de dos paraderos.**
*(Nota: El gráfico muestra el intervalo en segundos (10 a 140) comparando los resultados de PARAMICS y SIMTRANSIT para las paradas 1 y 2.)*

### 5. COMENTARIOS Y CONCLUSIONES

En este artículo se resume el desarrollo la una nueva herramienta de microsimulación de transporte público flexible SIMTRANSIT, detallando el primer módulo implementado y que está orientado a la correcta modelación de operaciones en paraderos y la interacción entre vehículos y pasajeros que allí se produce. Un avance significativo producto de este enfoque consiste en considerar en la simulación microscópica de tráfico a los pasajeros como agentes involucrados en la operación del sistema. Esta innovación permite incorporar nuevos modelos para mejorar la simulación de la interacción entre los vehículos de transporte público y los usuarios y obtener así una serie de estadísticas, ya no sólo del nivel de servicio de los vehículos, sino que también de los usuarios del sistema.

Dentro de las extensiones y aplicaciones más inmediatas de este enfoque, lo que sin duda contempla generar nuevos módulos que formen parte de SIMTRANSIT, podemos mencionar las

---

256

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

siguientes: análisis de prioridades al transporte público de superficie (TPS) en arcos (cuándo usar pistas sólo bus y cuántas, cuándo usar vías exclusivas y su mejor ubicación (en mediana o en extremos, cuál es el efecto sobre la red de calles sólo bus); estudio de prioridades al TPS en semáforos (cuándo conviene tener semáforos actuados por vehículos de TPS, qué planes fijos son más adecuados para la progresión del TPS, efectividad de pistas sólo bus cortas en semáforos); evaluación del diseño de estaciones o paraderos en vías exclusivas de TPS (efecto de la distancia entre subparaderos, cuál es la mejor disposición de subparaderos, secuenciales o en paralelo, cuál es el mejor número de subparaderos por estación y con cuántos sitios; análisis global de corredores de TPS (cuál es el espaciamiento óptimo entre estaciones o paraderos, estudio de la interacción paradero - semáforo, efecto del trasbordo de pasajeros entre corredores o líneas del mismo corredor); diseño detallado de rutas del TPS considerando matrices O-D entre paraderos.

También se contempla incorporar modelación de operación de sistemas de transporte público que utilicen tecnología ITS (Intelligent Transportation Systems), con vehículos controlados en tiempo real, y donde los operadores tomen ciertas decisiones también en tiempo real, para manejar intervalos, frecuencias y optimizar ciertas medidas de rendimiento del sistema global.

### AGRADECIMIENTOS
Esta investigación ha sido parcialmente financiada por Grant GR/S84309/01 del EPSRC (Engineering and Physical Science Research Council) del Reino Unido, por el proyecto FONDECYT N° 1030700, y por el Núcleo Milenio, "Sistemas Complejos de Ingeniería".

### REFERENCIAS

* Abdulhai, B., A.S. Shalaby y A. Georgi (2002). Microsimulation Modeling and Impact Assessment of Streetcar Transit Priority Options: The Toronto Experience. Proceedings of the 81st TRB Annual Meeting. Transportation Research Board, Washington D. C.
* Boxill, S. Y L. Yu (2000). An evaluation of Traffic Simulation Models for Supporting ITS Development. Technical Report SWTTC/00/167602-1, Centre for Transportation Training and Research, Texas Southern University.
* Chien, S., S. Chowdhury, K. Mouskos y Y. Ding (2000). Enhancements of CORSIM model in simulating operations. Journal of Transportation Engineering 126, 396-404.
* Cortés, C.E., L. Pagès y R. Jayakrishnan (2005). Microsimulation of Flexible Transit System Designs in Realistic Urban Networks. Transportation Research Record, en prensa.
* Fernández, R. Y R. Planzer (2002). Review of the capacity of road-based transit system. Transport Reviews 22, 267-293.

---

257

* Fernández, R. y N. Tyler (2004). Study of Passenger-Bus-Traffic Interactions on Bus Stop Operations. Working Paper, University of London Centre for Transport Studies, London.
* FHWA (1996). CORSIM User Manual, Version 1.01. Federal Highway Administration, Washington D.C.
* Fox, K. (2000). SMARTEST new tools for evaluating ITS. Traffic Engineering and Control 41(1), 20-22.
* Gibson, J., R. Fernández y A. Albert (1997). Operación de paraderos formales en Santiago. Actas del VIII Congreso Chileno de Ingeniería de Transporte, 397-408. Noviembre, Santiago.
* Inga Note. (2001). Integration of a Center-Running Guided Busway into an Arterial Street. VISSIM User Group Meeting, Seattle.
* Jayakrishnan, R., C.E. Cortés, R. Lavanya y L. Pagès (2003). Simulation of Urban Transportation Networks with Multiple Vehicle Classes and Services: Classifications, Functional Requirements and General-Purpose Modeling Schemes. Proceedings of the 82th Transportation Research Board Annual Meeting, Washington D.C.
* Lindau, L. A. (1983). High-flow bus operation on urban arterial roads. PhD Thesis, University of Southampton.
* Liu, R. (2003). DRACULA Traffic Model User Manual, Version 2.0. Institute for Transport Studies, University of Leeds.
* Multisystems Inc. (2000). Bus Rapid Transit Simulation Model Research and Development. Report USDOT/SBIR Phase 1. October.
* PTV (2003). VISSIM User Manual, Version 3.7. Planung Transport Verkehr.
* Quadstone (2003). Quadstone PARAMICS Calibration Note, Version 4.1. Quadstone Ltd.
* Quadstone (2004). Quadstone PARAMICS Modeller and Programmer Reference Manual, Version 4.2. Quadstone Ltd.

---

258

Vanessa Burgos, Rodrigo Fernández, Cristián E. Cortés

* Siegel, J, A. Gschwender y L. De Grange (2003). Uso de un microsimulador de tráfico para la representación de corredores segregados de buses. Actas XI Congreso Chileno de Ingeniería de Transporte, 1-13. Octubre, Santiago.
* Silva, P.C.M. (2000). Simulating bus stops in mixed traffic. Traffic Engineering and Control 41, 160-167.
* Silva, P.C.M. (2001). Modelling interactions between bus operations and traffic flow. PhD Thesis, University of London (Unpublished).
* SMARTEST (1999). Simulation Modelling Applied to Road Transport European Scheme Tests. University of Leeds, Leeds. www.its.leeds.ac.uk/projects/smartest.
* TRB (1997). Traffic Flow Theory. A state-of-the-Art Report. Transportation Research Board, Special Report 165, Washington, D.C.
* TSS (2004). GETRAM/AIMSUN User Manual, Version 4.2. Transport Simulation Systems.
* Venglar, Fambro and Bauer (1995). Validation of Simulation Software for Modeling Light Rail Transit. Transportation Research Record 1494, 161-166.