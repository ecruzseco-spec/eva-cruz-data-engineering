# Publicación segura y manifiesto público

Estado al 9 de octubre de 2026: repositorio público, CI y GitHub Pages activos. La conexión con Get on Board y la postulación siguen pendientes. Los pasos siguientes documentan la preparación original.

## Contenido que se propone publicar

Todo lo versionado por Git, y únicamente eso. El listado literal está en [public_manifest.md](public_manifest.md):

- Código bajo `src/` y `scripts/`.
- Proyectos sintéticos bajo `projects/`.
- Pruebas bajo `tests/`.
- Documentación bajo `docs/`.
- Evidencia sanitizada bajo `evidence/`.
- Workflow preparado `.github/workflows/ci.yml`.
- `README.md`, `requirements.txt`, `pyproject.toml`, `.gitignore` y `ASSISTANCE.md`.

Los datos públicos son identificadores ficticios `T1001...T1012`, clientes ficticios `C001...C010`, importes y fechas inventados por el generador. No proceden de empleadores.

## Contenido excluido

- CV, fotografía, teléfono, correos, domicilio y credenciales.
- `.venv/`, `.env*`, archivos de secretos y configuración personal.
- Bases `*.duckdb`, CSV generados, cachés y targets de dbt.
- Cualquier archivo fuera de este repositorio.

## Configuración propuesta

- Cuenta propietaria confirmada: `ecruzseco-spec`.
- Repositorio: `eva-cruz-data-engineering`.
- Visibilidad: pública.
- Descripción: `Portafolio de ingeniería de datos con Python, DuckDB y dbt: pipeline incremental, calidad, idempotencia y modelado analítico con datos sintéticos.`
- GitHub Pages: rama `main`, carpeta `/docs`.
- Licencia: ninguna por ahora; queda pendiente de elección expresa.

Antes de publicar, ejecuta:

```powershell
git status --short
git ls-files
git grep -n -I -E "password|secret|token|BEGIN .*PRIVATE KEY"
```

El nombre de Eva y la trayectoria tecnológica son intencionales. Investiga cualquier otra coincidencia antes de aprobar.

## Crear la cuenta sin compartir credenciales

1. Abre manualmente `https://github.com/signup` en tu navegador.
2. Usa un correo personal que controles; no lo compartas por chat. Confirma el correo.
3. Elige y confirma personalmente el usuario. `evacruz-data` fue solo una propuesta: no es una cuenta confirmada ni debe asumirse como propiedad de Eva.
4. Crea una contraseña única y [activa 2FA](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication) con aplicación autenticadora; después puedes agregar una passkey. Guarda los códigos de recuperación fuera del repositorio.
5. Revisa visibilidad de correo y selecciona mantenerlo privado.
6. Copia la dirección `noreply` que GitHub muestra para commits privados; en cuentas nuevas normalmente incluye `ID+USERNAME`, según la [referencia oficial de correos](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference).

## Preparar Git local después de conocer el usuario

El repositorio queda en `main` sin un correo local inventado. Antes del primer commit, configura la dirección **exacta** que GitHub muestre para la cuenta confirmada:

```powershell
git config user.name "Eva Cruz Valdovinos"
git config user.email "ID+USUARIO@users.noreply.github.com"
git branch -M main
git status --short
```

## Publicar, solo después de revisar y autorizar

1. Crea en GitHub un repositorio público vacío llamado `eva-cruz-data-engineering`; no agregues README remoto.
2. Revisa otra vez `git status`, `git diff --cached` y `git ls-files`.
3. Crea el commit y configura el remoto sin incluir tokens en la URL.
4. Autentícate con Git Credential Manager o `gh auth login` en la interfaz segura; nunca pegues el token en archivos o chat.
5. Haz push a `main`.
6. Verifica que GitHub Actions pase. Solo entonces cambia la frase “preparado, no ejecutado” por evidencia del run real.
7. En Settings > Pages selecciona “Deploy from a branch”, `main`, carpeta `/docs`, siguiendo la [configuración oficial de la fuente](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). Confirma la URL pública.
8. Recorre desde la página los enlaces a ambos proyectos en una sesión privada del navegador.

## Licencia pendiente de elección

El manifiesto actual no incluye `LICENSE`. Elegir MIT permitiría a terceros usar, copiar, modificar y redistribuir el código conservando el aviso de copyright y sin garantías. Sin una licencia explícita se mantienen los derechos reservados por defecto. Agrega una licencia solo después de que Eva elija conscientemente una opción.

## Get on Board y candidatura

Conecta GitHub únicamente cuando el correo de la cuenta esté confirmado, Actions esté revisado, Pages sea público y hayas inspeccionado el perfil final. Mantén sin enviar la postulación de Grupo Mariposa hasta revisar todos los campos y autorizar expresamente el envío.

## Aprobación solicitada

Antes de cualquier publicación, confirma todo en una sola respuesta: la cuenta de GitHub que es propiedad de Eva; la publicación del manifiesto exacto; el nombre, visibilidad y descripción anteriores; que el nombre “Eva Cruz Valdovinos” quede visible; que no se incluya licencia por ahora; y que Pages use `main` con `/docs`. Conectar GitHub a una plataforma de postulación o enviar una candidatura requiere una autorización posterior e independiente.
