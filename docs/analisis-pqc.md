# Impacto de la computación cuántica en la ciberseguridad: inventario, estándares NIST PQC 2024 y plan de migración

**Arquitectura de Computadores · Unidad 12 · Post-contenido — Parte 2**

## Resumen

Este documento analiza cómo la computación cuántica compromete la criptografía en uso y cómo debe planificarse la migración hacia criptografía post-cuántica (PQC). Se inventarían los algoritmos vulnerables al algoritmo de Shor y al de Grover, se describen los tres estándares publicados por el NIST en agosto de 2024 (FIPS 203, 204 y 205), se cuantifica el crecimiento en bytes de claves, *ciphertexts* y firmas frente a la criptografía clásica y su efecto en un *handshake* TLS 1.3 híbrido, y se formula un plan de migración para tres perfiles organizacionales con horizontes de sensibilidad de datos distintos. Las cifras de tamaño provienen de los documentos FIPS; los cálculos derivados se identifican como tales.

---

## 1. Inventario de algoritmos criptográficos vulnerables

El primer paso de cualquier migración post-cuántica es un inventario de los algoritmos en uso. La clasificación distingue dos niveles de daño: **"roto completamente"** (el algoritmo deja de ser seguro y compromete también la confidencialidad retroactiva de lo capturado hoy) y **"debilitado"** (la seguridad se reduce, pero no desaparece y se corrige aumentando parámetros).

| Algoritmo | Tipo | Vulnerabilidad cuántica | Algoritmo atacante | Estado post-cuántico / acción |
|-----------|------|-------------------------|--------------------|-------------------------------|
| RSA-2048 / 3072 / 4096 | Cifrado y firma asimétricos | **Roto completamente** | Shor (factorización, tiempo polinómico) | Reemplazar: ML-KEM (cifrado/KEX), ML-DSA o SLH-DSA (firma) |
| ECDSA (P-256, P-384) | Firma digital | **Roto completamente** | Shor (logaritmo discreto en curvas elípticas) | Reemplazar con ML-DSA (o SLH-DSA) |
| ECDH / X25519 | Intercambio de clave | **Roto completamente** | Shor (logaritmo discreto en curvas elípticas) | Reemplazar con ML-KEM; durante la transición, modo híbrido |
| DH / DSA sobre campos finitos | Intercambio de clave / firma | **Roto completamente** | Shor (logaritmo discreto) | Reemplazar con ML-KEM / ML-DSA |
| AES-128 | Cifrado simétrico | Debilitado (búsqueda de clave ≈ 2⁶⁴ iteraciones cuánticas) | Grover, O(√N) | Migrar a AES-256 donde la política lo exija |
| AES-256 | Cifrado simétrico | Aceptable (clave efectiva ≈ 128 bits) | Grover, O(√N) | Mantener |
| SHA-256 | Función hash | Debilitada (preimagen 2²⁵⁶ → ≈ 2¹²⁸) | Grover; colisiones teóricas con Brassard-Høyer-Tapp (≈ 2⁸⁵) | Migrar a SHA-384/512 en sistemas sujetos a CNSA 2.0 |
| SHA-3-256 | Función hash | Debilitada en forma equivalente a SHA-256 | Grover | SHA-3-384 o mayor cuando se requiera margen adicional |

**Lectura del inventario.**

- Todo lo **asimétrico basado en factorización o logaritmo discreto** cae por Shor: el ataque es de tiempo polinómico, por lo que subir el tamaño de la clave no es una defensa viable (Shor, 1997). Es la categoría que obliga a reemplazar el algoritmo.
- Lo **simétrico y los hash** solo sufren la aceleración cuadrática de Grover (Grover, 1996). La contramedida es duplicar el tamaño efectivo (AES-256, SHA-384/512), no cambiar de familia. NIST usa AES-128 como referencia del nivel de seguridad 1 de sus categorías PQC, lo que refleja que el debilitamiento práctico de AES-128 es menor que el teórico: las iteraciones de Grover son secuenciales y no paralelizan bien, y cada una exige un circuito reversible profundo.
- Para las colisiones en hash, el algoritmo de Brassard et al. (1998) reduce el costo teórico a ≈ 2^(n/3), pero requiere memoria cuántica enorme; por eso la preocupación práctica se centra en las preimágenes y en las exigencias regulatorias (CNSA 2.0 pide SHA-384 o SHA-512).

---

## 2. Análisis de vulnerabilidad: cuán cerca está la amenaza

El algoritmo de Shor convierte la factorización y el logaritmo discreto en problemas tratables para una computadora cuántica tolerante a fallos. Gidney y Ekerå (2021) estiman que factorizar un entero RSA de 2048 bits requeriría unos 20 millones de qubits físicos ruidosos y alrededor de 8 horas, bajo supuestos de hardware superconductor con tasa de error de puerta de 10⁻³ y corrección de errores con código de superficie. Ninguna máquina actual se acerca a esa escala, pero ese resultado ilustra dos ideas del laboratorio de la Parte 1: la amenaza depende de la **corrección de errores**, no del número de qubits físicos por sí solo, y las estimaciones de recursos han bajado de forma sostenida con cada mejora algorítmica.

La consecuencia de ciberseguridad más importante es la amenaza **HNDL (*harvest now, decrypt later*)**: un adversario puede capturar hoy tráfico cifrado con intercambios de clave clásicos (ECDH, RSA) y descifrarlo cuando exista una máquina suficiente. Esto afecta la **confidencialidad** de datos con vida útil larga. Las **firmas** no sufren HNDL de la misma forma, porque el atacante solo puede falsificarlas cuando posea la capacidad cuántica, aunque sí pierden validez a largo plazo si el algoritmo se rompe antes de que expire el documento firmado. CISA, NSA y NIST (2023) recomiendan comenzar el inventario y la planificación de la migración ya, precisamente por el tiempo que toma reemplazar la criptografía en sistemas reales.

---

## 3. Estándares NIST PQC 2024 — análisis comparativo

El NIST publicó en agosto de 2024 tres estándares federales de procesamiento de información (FIPS): ML-KEM (FIPS 203), ML-DSA (FIPS 204) y SLH-DSA (FIPS 205). Se resumen sus fundamentos, parámetros y casos de uso.

### 3.1 ML-KEM (FIPS 203, antes CRYSTALS-Kyber)

Es un mecanismo de encapsulamiento de claves (KEM) cuya seguridad se apoya en el problema **Module Learning with Errors (MLWE)** (NIST, 2024a). Reemplaza a ECDH, X25519 y RSA-KEM para establecer claves compartidas.

| Parámetro | Clave pública (encapsulación) | Clave privada (decapsulación) | Ciphertext | Nivel NIST (≈ equivalente) |
|-----------|------------------------------:|------------------------------:|-----------:|----------------------------|
| ML-KEM-512 | 800 B | 1632 B | 768 B | 1 (≈ AES-128) |
| ML-KEM-768 | 1184 B | 2400 B | 1088 B | 3 (≈ AES-192) |
| ML-KEM-1024 | 1568 B | 3168 B | 1568 B | 5 (≈ AES-256) |

*Fuente: NIST (2024a), FIPS 203.* ML-KEM-768 es el parámetro que se ha desplegado como componente de los intercambios híbridos en TLS (sección 4).

### 3.2 ML-DSA (FIPS 204, antes CRYSTALS-Dilithium)

Es un esquema de firma digital basado también en MLWE (y en el problema SIS de módulos) (NIST, 2024b). Reemplaza a ECDSA y a las firmas RSA en el uso general. Ofrece firma y verificación rápidas y tamaños moderados dentro de la PQC, con un costo en bytes mucho mayor que ECDSA.

| Parámetro | Clave pública | Clave privada | Firma | Nivel NIST |
|-----------|--------------:|--------------:|------:|------------|
| ML-DSA-44 | 1312 B | 2560 B | 2420 B | 2 |
| ML-DSA-65 | 1952 B | 4032 B | 3309 B | 3 |
| ML-DSA-87 | 2592 B | 4896 B | 4627 B | 5 |
| *ECDSA P-256 (referencia clásica)* | *64 B* | *32 B* | *≈ 70–72 B (DER)* | *≈ 128 bits clásicos, no PQC* |

*Fuente: NIST (2024b), FIPS 204; ECDSA P-256 según los tamaños usuales de la curva.* Con ML-DSA-44 la firma ya es unas 34 veces mayor que una ECDSA P-256 y con ML-DSA-65, unas 46 veces. En velocidad, ML-DSA firma y verifica en el orden de decenas a cientos de microsegundos en CPU moderna, muy por debajo de SLH-DSA al firmar (el FIPS no publica tiempos; la comparación es cualitativa y se confirma con los *benchmarks* de las implementaciones, p. ej. liboqs).

### 3.3 SLH-DSA (FIPS 205, antes SPHINCS+)

Es una firma digital **basada únicamente en funciones hash** (NIST, 2024c). Su seguridad depende solo de propiedades de la función hash subyacente (resistencia a preimagen y a segundas preimágenes, y a colisiones según el parámetro), sin asumir la dificultad de un problema algebraico estructurado como MLWE. Es **más conservador** en sus supuestos que ML-DSA: si algún día se descubre un ataque contra los retículos, SLH-DSA no se ve afectado. A cambio, las firmas son grandes y la firma es lenta, sobre todo en las variantes optimizadas por tamaño (`s`).

| Parámetro | Clave pública | Clave privada | Firma | Nivel NIST |
|-----------|--------------:|--------------:|------:|------------|
| SLH-DSA-128s | 32 B | 64 B | 7856 B | 1 |
| SLH-DSA-128f | 32 B | 64 B | 17 088 B | 1 |
| SLH-DSA-192s | 48 B | 96 B | 16 224 B | 3 |
| SLH-DSA-256s | 64 B | 128 B | 29 792 B | 5 |

*Fuente: NIST (2024c), FIPS 205.* Se recomienda como **alternativa de respaldo** (diversidad criptográfica) para certificados raíz, anclas de confianza y artefactos de vida muy larga, donde importa más la solidez del supuesto que el tamaño y la velocidad.

### 3.4 Qué reemplaza a qué

| Función | Criptografía actual | Reemplazo estandarizado |
|---------|---------------------|-------------------------|
| Establecimiento de clave / cifrado asimétrico | ECDH, X25519, RSA | **ML-KEM** (FIPS 203) |
| Firma digital de uso general | ECDSA, RSA | **ML-DSA** (FIPS 204) |
| Firma de respaldo, conservadora | ECDSA, RSA | **SLH-DSA** (FIPS 205) |
| Firma de firmware/software (estados controlados) | RSA, ECDSA | LMS/XMSS (NIST SP 800-208), según CNSA 2.0 |

ML-KEM **no** es un esquema de firma: no sirve para firmar y solo establece secretos compartidos.

---

## 4. Tamaños de clave y firma: PQC frente a criptografía clásica, e impacto en TLS 1.3 híbrido

### 4.1 Tabla comparativa

| Algoritmo | Tipo | Clave pública | Clave privada | Firma / ciphertext | Nivel de seguridad |
|-----------|------|--------------:|--------------:|-------------------:|--------------------|
| RSA-3072 | Cifrado/firma clásico | ≈ 387 B (n de 384 B + exponente) | ≈ 1.6–1.8 KB (PKCS#1) | 384 B (firma) | ≈ 128 bits clásicos (no PQC) |
| ECDSA P-256 | Firma clásica | 64 B | 32 B | ≈ 70–72 B (DER) | ≈ 128 bits clásicos (no PQC) |
| X25519 | Intercambio de clave clásico | 32 B | 32 B | N/A (KEX) | ≈ 128 bits clásicos (no PQC) |
| ML-KEM-768 (FIPS 203) | KEM post-cuántico | 1184 B | 2400 B | 1088 B (ciphertext) | Nivel NIST 3 (≈ AES-192) |
| ML-DSA-65 (FIPS 204) | Firma post-cuántica | 1952 B | 4032 B | 3309 B | Nivel NIST 3 (≈ AES-192) |
| SLH-DSA-128s (FIPS 205) | Firma post-cuántica (hash) | 32 B | 64 B | 7856 B | Nivel NIST 1 (≈ AES-128) |

*Fuentes: tamaños PQC de NIST (2024a, 2024b, 2024c); equivalencias de seguridad clásica de Barker (2020).*

### 4.2 Factores de crecimiento

Los factores siguientes son **cálculos derivados** de la tabla:

| Comparación | Cálculo | Factor |
|-------------|---------|-------:|
| Clave pública ML-KEM-768 vs. X25519 | 1184 / 32 | ≈ 37× |
| Clave pública ML-DSA-65 vs. ECDSA P-256 | 1952 / 64 | ≈ 30× |
| Firma ML-DSA-65 vs. ECDSA P-256 | 3309 / 72 | ≈ 46× |
| Firma SLH-DSA-128s vs. ECDSA P-256 | 7856 / 72 | ≈ 109× |
| Firma ML-DSA-65 vs. RSA-3072 | 3309 / 384 | ≈ 8.6× |

### 4.3 Efecto en el *handshake* TLS 1.3 híbrido X25519MLKEM768

El intercambio híbrido X25519MLKEM768 concatena un ML-KEM-768 con un X25519 y deriva el secreto con ambos, de modo que la sesión es segura mientras al menos uno de los componentes resista (Kwiatkowski et al., 2026). Los tamaños del campo `key_share` son:

| Mensaje | Composición | Tamaño |
|---------|-------------|-------:|
| ClientHello, `key_share` solo X25519 | 32 B | 32 B |
| ClientHello, `key_share` híbrido | 1184 B (ML-KEM-768) + 32 B (X25519) | **1216 B** |
| ServerHello, `key_share` solo X25519 | 32 B | 32 B |
| ServerHello, `key_share` híbrido | 1088 B (ciphertext) + 32 B (X25519) | **1120 B** |

El intercambio de clave híbrido añade en total ≈ 2.3 KB al *handshake* (1216 + 1120 = 2336 B). Eso suele caber dentro de la ventana de congestión inicial de TCP de 10 segmentos (Chu et al., 2013), cerca de 14 600 B con un MSS de 1460 B, por lo que **no añade rondas de red** en condiciones normales de conectividad. En la práctica puede hacer que el ClientHello ocupe dos segmentos, un costo pequeño.

El crecimiento mayor viene de la **autenticación**. Estimación propia de los bytes de material criptográfico (claves públicas y firmas) en una cadena de dos certificados (hoja e intermedio) más la firma de `CertificateVerify`, sin contar los demás campos X.509 ni extensiones:

| Configuración | Claves públicas | Firmas | Total aproximado |
|---------------|----------------:|-------:|-----------------:|
| ECDSA P-256 | 2 × 64 B = 128 B | 3 × ≈ 72 B = 216 B | **≈ 0.34 KB** |
| ML-DSA-65 | 2 × 1952 B = 3904 B | 3 × 3309 B = 9927 B | **≈ 13.8 KB** |

La cadena ML-DSA-65 es ≈ 40 veces mayor. Sumada al `key_share` híbrido del servidor (1120 B), el vuelo del servidor ronda los 15 KB, **por encima** de los ≈ 14.6 KB de la ventana inicial de TCP aun sin contar el resto de los campos de los certificados. En redes con alta latencia o pérdida de paquetes, ese volumen obliga a esperar una confirmación (*ACK*) antes de seguir enviando, es decir, **una ronda adicional** que sí incrementa la latencia percibida. Conclusión: el sobrecosto del **intercambio de clave** híbrido es pequeño, mientras que el de las **firmas y certificados PQC** es el factor que realmente cambia el rendimiento del *handshake*, y por eso la mayor parte del despliegue actual comienza solo por el intercambio de clave.

---

## 5. Plan de migración para tres perfiles organizacionales

Se aplica una regla común: la **urgencia la fija el horizonte de sensibilidad de los datos** (modelo de Mosca: si el tiempo de vida del dato más el tiempo de migración supera el tiempo hasta una máquina cuántica relevante, ya hay riesgo). Los plazos se expresan en fases a partir de noviembre de 2026.

### Perfil A — Hospital universitario (sensibilidad 50–75 años)

**1. Inventario de sistemas con criptografía asimétrica activa.** Portal de pacientes (TLS 1.3 con ECDHE + ECDSA), firma digital de prescripciones (ECDSA), VPN de sedes y de teletrabajo médico, integraciones HL7/FHIR entre sistemas, PKI interna, respaldo de historias clínicas y *wrapping* de claves de cifrado de datos.

**2. Clasificación por horizonte.** Historias clínicas y comunicaciones del portal: 50–75 años (críticas, expuestas a HNDL). Prescripciones firmadas: vigencia inmediata, pero valor probatorio de largo plazo. Registros administrativos: 5–10 años.

**3. Estrategia híbrida.** Intercambio de clave híbrido X25519MLKEM768 en el portal y en las VPN desde la primera fase (protege contra HNDL); datos en reposo ya con AES-256, con claves de cifrado de datos re-envueltas bajo un esquema con ML-KEM; firma de prescripciones con **ML-DSA-65**, inicialmente en paralelo con ECDSA (doble firma) hasta validar la verificación en todos los consumidores; **SLH-DSA** reservado para certificados raíz y anclas de larga vida.

**4. Cronograma con hitos verificables.**

| Fase | Plazo | Hito verificable |
|------|-------|------------------|
| 1 | 0–6 meses | Inventario completo (incluidos proveedores y dispositivos médicos); portal y VPN negocian X25519MLKEM768 (verificable con captura de `key_share` de 1216 B) |
| 2 | 6–18 meses | Doble firma ECDSA + ML-DSA-65 en prescripciones; HSM actualizados; plan de resellado de documentos firmados |
| 3 | 18–36 meses | Raíz de la PKI interna con SLH-DSA y PKI híbrida operando; todas las integraciones HL7/FHIR con TLS híbrido |
| 4 | 36–60 meses | Retiro de ECDSA/RSA en producción; pruebas de agilidad criptográfica documentadas |

**5. Riesgos y mitigaciones.** Dispositivos médicos con firmware antiguo que no admiten PQC → segmentación de red y *gateways* con terminación TLS híbrida; crecimiento de tamaño en cadenas de certificados que rompe sistemas con límites de mensaje → pruebas de carga previas; falta de agilidad criptográfica en proveedores → cláusulas contractuales de soporte PQC; validez a largo plazo de firmas → sellos de tiempo y resellado periódico.

### Perfil B — Startup de comercio electrónico (sensibilidad 5–7 años)

**1. Inventario.** Sitio y API sobre TLS 1.3 (X25519 + ECDSA), tokenización y procesamiento de pagos bajo PCI-DSS, CDN o balanceador de borde, comunicaciones internas entre microservicios, firma de *webhooks* y de artefactos de despliegue.

**2. Clasificación.** Datos de tarjeta: 5–7 años (ciclo de vida de tarjeta), cifrados con AES-256. Datos de clientes y pedidos: 3–7 años. Sesiones y tokens: minutos a días (sin riesgo HNDL relevante).

**3. Estrategia híbrida.** Activar el intercambio híbrido X25519MLKEM768 en el borde (CDN o balanceador) y en las bibliotecas cliente cuando el proveedor lo permita; mantener ECDSA en los certificados mientras las autoridades de certificación públicas y los clientes no soporten certificados PQC; incorporar la validación PQC al inventario criptográfico que PCI-DSS v4.0 exige revisar al menos cada 12 meses (requisito 12.3.3).

**4. Cronograma.**

| Fase | Plazo | Hito verificable |
|------|-------|------------------|
| 1 | 0–6 meses | Inventario criptográfico; activar híbrido en el borde y medir la latencia de *handshake* antes y después |
| 2 | 6–24 meses | Tráfico interno entre servicios con TLS híbrido; revisión anual PCI-DSS con el inventario PQC |
| 3 | 24–48 meses | Evaluar certificados y firmas PQC según madurez del ecosistema; plan de retiro del componente clásico |

**5. Riesgos y mitigaciones.** Incompatibilidad con clientes o *middleboxes* que fallan con ClientHello más grandes → monitoreo de errores de conexión y *fallback* controlado; dependencia del proveedor de CDN → contrato con hoja de ruta PQC; sobrecosto de latencia en redes móviles → medición por segmento de usuarios.

### Perfil C — Entidad gubernamental de defensa (sensibilidad 25–50 años)

**1. Inventario.** Comunicaciones clasificadas, firma de documentos oficiales sobre la PKI nacional, VPN entre agencias, firma de *firmware* y de software, módulos de seguridad de hardware (HSM) y dispositivos de red.

**2. Clasificación.** Material clasificado: 25–50 años (máxima exposición a HNDL). Documentos oficiales firmados: vigencia legal de décadas. Firmware y software de misión: ciclo largo y alto impacto si se falsifica.

**3. Estrategia.** Se toma como referencia normativa la suite **CNSA 2.0** de la NSA (2022): **ML-KEM-1024** para establecimiento de claves, **ML-DSA-87** para firmas, **LMS o XMSS** (NIST SP 800-208) para firma de software y firmware, **AES-256** y **SHA-384/512**. Se usa el modo híbrido (clásico + PQC) solo como etapa de transición donde la interoperabilidad lo exija. CNSA 2.0 no aprueba los parámetros pequeños (ML-KEM-512/768, ML-DSA-44/65) ni SLH-DSA para sistemas de seguridad nacional, de modo que el perfil prescinde de ellos aunque NIST los estandarice.

**4. Cronograma (plazos de CNSA 2.0).**

| Categoría | Soportar y preferir | Uso exclusivo |
|-----------|--------------------:|--------------:|
| Firma de software y firmware | 2025 | 2030 |
| Equipos de red (VPN, routers) | 2026 | 2030 |
| Navegadores, servidores y servicios en la nube | 2025 | 2033 |
| Sistemas operativos | 2027 | 2033 |
| Equipos especializados o personalizados | 2030 | 2033 |

La meta nacional global del memorando NSM-10 es 2035. Hitos verificables: inventario completo y priorizado (6 meses), firma de firmware con LMS/XMSS sobre HSM validados (12 meses), VPN inter-agencias con ML-KEM-1024 (24 meses), PKI nacional con ML-DSA-87 (a más tardar 2030).

**5. Riesgos y mitigaciones.** Estado de las claves LMS/XMSS (un reúso de una clave de un solo uso rompe la seguridad) → firma en HSM con respaldo de estado controlado; tamaño de claves y firmas ML-KEM-1024/ML-DSA-87 en protocolos con límites estrictos (IKEv2) → intercambios intermedios y pruebas de interoperabilidad; HSM sin soporte PQC → renovación de firmware o de hardware con presupuesto plurianual; dependencia de proveedores sin soporte → requisito de soporte CNSA 2.0 en adquisiciones.

---

## 6. Decisiones técnicas justificadas

### 6.1 Decisión — ¿qué algoritmo NIST firma las prescripciones del Perfil A?

Firmar una prescripción es un caso de uso de firma digital, no de intercambio de clave, por lo que **ML-KEM queda descartado de entrada**: es un mecanismo de encapsulamiento de claves y no existe un modo estándar de usarlo para firmar. La elección real es entre ML-DSA-65 y SLH-DSA-128s. Para un hospital universitario que emite miles de prescripciones al día, con baja latencia en el portal, **ML-DSA-65 es el candidato principal**: su firma mide 3309 bytes frente a 7856 de SLH-DSA-128s, y firma y verifica mucho más rápido porque se basa en retículos y no en miles de evaluaciones de hash. SLH-DSA tiene el supuesto de seguridad más conservador, pero ese margen extra no justifica el costo en volumen y velocidad en este caso. Además, la amenaza HNDL aplica a la **confidencialidad** de datos cifrados que se capturan hoy para leerlos después; el propósito de la firma es autenticar el momento de emisión, de modo que el horizonte de 50–75 años de la historia clínica no obliga a usar el esquema más conservador para firmar. Con una salvedad: la firma debe seguir siendo creíble en una auditoría futura, de modo que se debe planear sellado de tiempo y resellado periódico. **Recomendación:** ML-DSA-65 como algoritmo principal de firma de prescripciones, con SLH-DSA reservado como respaldo para certificados raíz y de larga vida, donde la solidez del supuesto pesa más que el rendimiento.

### 6.2 Decisión — ¿modo híbrido permanente o etapa de transición para el Perfil B?

Aunque el *key_share* híbrido añade ≈ 2.3 KB al *handshake* y rara vez agrega rondas de red, el modo híbrido es la elección correcta para el Perfil B desde ahora, porque su sobrecosto medido en la sección 4 es bajo y su beneficio de seguridad es alto. La combinación X25519 + ML-KEM-768 protege contra **dos fallas no correlacionadas**: que una computadora cuántica suficientemente grande rompa la criptografía de curvas elípticas, o que ML-KEM, mucho más joven que ECC y con muchos menos años de escrutinio público, tenga una debilidad clásica aún no descubierta. Mientras ML-KEM y ML-DSA acumulan escrutinio, esa doble protección vale más que los bytes extra. También es la práctica ya adoptada por defecto en los principales navegadores y CDN, lo que reduce el riesgo de incompatibilidad. Dado que los datos del Perfil B tienen una sensibilidad de solo 5–7 años y su exigencia regulatoria es menor que la del Perfil C, **el híbrido no debe verse como un estado permanente**: el sobrecosto de bytes y latencia, aunque pequeño, no es nulo, y mantener dos algoritmos duplica la superficie de mantenimiento. La recomendación es adoptarlo ahora como **estrategia de transición** y planear su simplificación a PQC puro hacia el final del plazo de CNSA 2.0 (2033), cuando la confianza acumulada y la adopción lo justifiquen, con el Perfil B moviéndose más tarde y con menor urgencia que el Perfil C.

---

## 7. Conclusiones

1. La criptografía **asimétrica** actual (RSA, ECDSA, ECDH, X25519) se rompe por completo con Shor; la **simétrica y los hash** solo se debilitan con Grover y se corrigen duplicando parámetros (AES-256, SHA-384/512).
2. La amenaza más inmediata es **HNDL**: afecta la confidencialidad de datos de vida larga, por eso el intercambio de clave se migra primero.
3. NIST ofrece tres estándares complementarios: **ML-KEM** (establecer claves), **ML-DSA** (firma de uso general) y **SLH-DSA** (firma conservadora de respaldo).
4. El costo de la PQC es principalmente de **tamaño**: el intercambio híbrido añade ≈ 2.3 KB y suele pasar inadvertido, mientras que una cadena de certificados ML-DSA-65 pesa ≈ 40 veces más que una ECDSA y puede añadir una ronda de red.
5. La migración se prioriza por **horizonte de sensibilidad**: híbrido inmediato para salud (Perfil A), transición gradual para comercio (Perfil B) y cumplimiento de CNSA 2.0 para defensa (Perfil C).
6. Los resultados de la Parte 1 refuerzan la lectura: la amenaza real depende de la corrección de errores a gran escala, y la migración debe planearse con anticipación, aunque la máquina que rompa RSA todavía no exista.

---

## Referencias

Barker, E. (2020). *Recommendation for key management: Part 1 – General* (NIST Special Publication 800-57 Part 1, Rev. 5). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-57pt1r5

Brassard, G., Høyer, P., & Tapp, A. (1998). Quantum cryptanalysis of hash and claw-free functions. En C. L. Lucchesi & A. V. Moura (Eds.), *LATIN'98: Theoretical informatics* (pp. 163–169). Springer.

Chu, J., Dukkipati, N., Cheng, Y., & Mathis, M. (2013). *Increasing TCP's initial window* (RFC 6928). Internet Engineering Task Force. https://doi.org/10.17487/RFC6928

Cooper, D., Apon, D., Dang, Q., Davidson, M., Dworkin, M., & Miller, C. (2020). *Recommendation for stateful hash-based signature schemes* (NIST Special Publication 800-208). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-208

Cybersecurity and Infrastructure Security Agency, National Security Agency, & National Institute of Standards and Technology. (2023). *Quantum-readiness: Migration to post-quantum cryptography* [Hoja informativa]. https://www.cisa.gov/resources-tools/resources/quantum-readiness-migration-post-quantum-cryptography

Gidney, C., & Ekerå, M. (2021). How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits. *Quantum, 5*, Artículo 433. https://doi.org/10.22331/q-2021-04-15-433

Grover, L. K. (1996). A fast quantum mechanical algorithm for database search. En *Proceedings of the 28th Annual ACM Symposium on Theory of Computing* (pp. 212–219). ACM. https://doi.org/10.1145/237814.237866

Kwiatkowski, K., Kampanakis, P., Westerbaan, B., & Stebila, D. (2026). *Post-quantum hybrid ECDHE-MLKEM key agreement for TLSv1.3* (Internet-Draft draft-ietf-tls-ecdhe-mlkem-05). Internet Engineering Task Force. https://datatracker.ietf.org/doc/draft-ietf-tls-ecdhe-mlkem/

National Institute of Standards and Technology. (2024a). *Module-lattice-based key-encapsulation mechanism standard* (FIPS 203). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.203

National Institute of Standards and Technology. (2024b). *Module-lattice-based digital signature standard* (FIPS 204). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.204

National Institute of Standards and Technology. (2024c). *Stateless hash-based digital signature standard* (FIPS 205). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.205

National Security Agency. (2022). *Commercial National Security Algorithm Suite 2.0* [Aviso de ciberseguridad]. U.S. Department of Defense.

Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer. *SIAM Journal on Computing, 26*(5), 1484–1509. https://doi.org/10.1137/S0097539795293172
