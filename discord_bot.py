import os
import asyncio
import discord
import logging
from database import init_db, crear_tarea, listar_tareas, stats, guardar_conversacion, obtener_historial, listar_miembros
from agent import interpretar_mensaje
from coach_agent import coach_responder
from transcriber import transcribir_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Dynamic channel/person mapping loaded from DB
CANALES: dict[int, str] = {}
ROLES_COACH: dict[str, str] = {}

# Canal coach - aqui se pregunta por tareas y se pide ayuda
CANAL_COACH = int(os.getenv("CANAL_COACH", "0"))

# Sesiones activas: canal_id -> rol identificado
sesiones_coach: dict[int, str] = {}

AUDIO_TYPES = {"audio/ogg", "audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "video/mp4"}


async def load_channels_from_db():
    """Load channel-to-person mapping from miembros table."""
    global CANALES, ROLES_COACH
    try:
        miembros = await listar_miembros(activo=True)
        new_canales = {}
        new_roles = {}
        for m in miembros:
            display_name = f"{m['nombre']} ({m['rol']})"
            if m.get("discord_canal_id"):
                try:
                    canal_id = int(m["discord_canal_id"])
                    new_canales[canal_id] = display_name
                except (ValueError, TypeError):
                    pass
            # Build coach roles mapping (lowercase role -> display name)
            if m.get("rol"):
                new_roles[m["rol"].lower()] = display_name

        # Fallback: also load from env if DB has no discord channels
        if not new_canales:
            cto_canal = os.getenv("CANAL_CTO", "0")
            ceo_canal = os.getenv("CANAL_CEO", "0")
            if cto_canal != "0":
                new_canales[int(cto_canal)] = "Alex Silvestre (CTO)"
            if ceo_canal != "0":
                new_canales[int(ceo_canal)] = "Alex Gutierrez (CEO)"

        if not new_roles:
            new_roles = {"ceo": "Alex Gutierrez (CEO)", "cto": "Alex Silvestre (CTO)"}

        CANALES = new_canales
        ROLES_COACH = new_roles
        logger.info(f"Canales cargados: {CANALES}")
        logger.info(f"Roles coach: {ROLES_COACH}")
    except Exception as e:
        logger.error(f"Error cargando canales desde DB: {e}")
        # Fallback to env vars
        CANALES[int(os.getenv("CANAL_CTO", "0"))] = "Alex Silvestre (CTO)"
        CANALES[int(os.getenv("CANAL_CEO", "0"))] = "Alex Gutierrez (CEO)"
        ROLES_COACH.update({"ceo": "Alex Gutierrez (CEO)", "cto": "Alex Silvestre (CTO)"})


@bot.event
async def on_ready():
    await init_db()
    await load_channels_from_db()
    logger.info(f"Bot conectado como {bot.user}")
    for canal_id, persona in CANALES.items():
        canal = bot.get_channel(canal_id)
        if canal:
            logger.info(f"  Canal {canal.name} -> {persona}")
        else:
            logger.warning(f"  Canal {canal_id} no encontrado para {persona}")
    if CANAL_COACH:
        canal_coach = bot.get_channel(CANAL_COACH)
        if canal_coach:
            logger.info(f"  Canal Coach: {canal_coach.name}")
        else:
            logger.warning(f"  Canal Coach {CANAL_COACH} no encontrado")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="tareas del equipo"
    ))


async def procesar_y_responder(message, texto, persona):
    """Procesa un texto (escrito o transcrito) y responde."""
    resultado = await interpretar_mensaje(texto)
    accion = resultado.get("accion", "mensaje_general")

    if accion == "crear_tarea":
        tarea_data = resultado.get("tarea", {})
        tarea = await crear_tarea(
            titulo=tarea_data.get("titulo", texto),
            descripcion=tarea_data.get("descripcion", ""),
            estado=tarea_data.get("estado", "Por hacer"),
            prioridad=tarea_data.get("prioridad", "Media"),
            fecha_limite=tarea_data.get("fecha_limite"),
            categoria=tarea_data.get("categoria", "Trabajo"),
            origen="Discord",
            asignado_a=persona,
        )

        colores = {"Alta": 0xEF4444, "Media": 0xF59E0B, "Baja": 0x22C55E}

        embed = discord.Embed(
            title="Tarea creada",
            color=colores.get(tarea["prioridad"], 0x2563EB),
        )
        embed.add_field(name="Titulo", value=tarea["titulo"], inline=False)
        if tarea["descripcion"]:
            embed.add_field(name="Descripcion", value=tarea["descripcion"], inline=False)
        embed.add_field(name="Asignada a", value=persona, inline=True)
        embed.add_field(name="Prioridad", value=tarea["prioridad"], inline=True)
        embed.add_field(name="Categoria", value=tarea["categoria"], inline=True)
        if tarea["fecha_limite"]:
            embed.add_field(name="Fecha limite", value=tarea["fecha_limite"], inline=True)
        embed.set_footer(text=f"ID: {tarea['id']}")

        await message.reply(embed=embed)

    elif accion == "listar_tareas":
        tareas = await listar_tareas(estado="Por hacer", asignado_a=persona, limite=10)

        if not tareas:
            await message.reply(f"**{persona}** no tiene tareas pendientes.")
            return

        embed = discord.Embed(
            title=f"Tareas de {persona} ({len(tareas)})",
            color=0x2563EB,
        )

        for t in tareas:
            emoji = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢"}.get(t["prioridad"], "⚪")
            fecha = f" | {t['fecha_limite']}" if t.get("fecha_limite") else ""
            embed.add_field(
                name=f"{emoji} {t['titulo']}",
                value=f"{t['categoria']}{fecha}",
                inline=False,
            )

        await message.reply(embed=embed)

    else:
        respuesta = resultado.get("respuesta", "No entendi tu mensaje.")
        await message.reply(respuesta)


def detectar_rol(texto: str) -> str | None:
    """Detecta si el usuario se identifica como CEO, CTO, o cualquier rol dinamico."""
    texto_lower = texto.lower()
    for clave, persona in ROLES_COACH.items():
        if clave in texto_lower:
            return persona
    return None


async def procesar_coach(message, texto):
    """Procesa mensajes en el canal coach."""
    canal_id = message.channel.id

    # Detectar si se identifica con un rol
    rol_detectado = detectar_rol(texto)
    if rol_detectado:
        sesiones_coach[canal_id] = rol_detectado

    # Si no hay sesion activa, pedir identificacion
    rol = sesiones_coach.get(canal_id)
    if not rol:
        roles_list = "\n".join(f"- `Soy el {clave.upper()}`" for clave in ROLES_COACH)
        await message.reply(
            f"**Hola! Primero dime quien eres.**\n"
            f"Escribe algo como:\n"
            f"{roles_list}\n\n"
            f"Asi puedo mostrarte tus tareas y ayudarte."
        )
        return

    # Obtener tareas pendientes de esta persona
    tareas = await listar_tareas(estado="Por hacer", asignado_a=rol, limite=20)

    # Obtener historial de conversaciones para contexto
    historial = await obtener_historial(str(canal_id), limite=20)

    # Generar respuesta del coach
    respuesta = await coach_responder(
        mensaje=texto,
        rol=rol,
        tareas=tareas,
        historial=historial,
    )

    # Guardar conversacion para aprendizaje
    await guardar_conversacion(
        canal_id=str(canal_id),
        rol=rol,
        mensaje_usuario=texto,
        respuesta_bot=respuesta,
    )

    # Discord tiene limite de 2000 caracteres por mensaje
    if len(respuesta) <= 2000:
        await message.reply(respuesta)
    else:
        # Dividir en chunks
        chunks = [respuesta[i:i+1900] for i in range(0, len(respuesta), 1900)]
        for chunk in chunks:
            await message.reply(chunk)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    canal_id = message.channel.id

    es_dm = isinstance(message.channel, discord.DMChannel)
    es_canal_tareas = canal_id in CANALES
    es_canal_coach = CANAL_COACH and canal_id == CANAL_COACH

    if not es_dm and not es_canal_tareas and not es_canal_coach:
        return

    # Extraer texto (comun para todos los canales)
    texto = None

    # Detectar audio (nota de voz o archivo de audio)
    audio_attachment = None
    for att in message.attachments:
        if att.content_type and any(att.content_type.startswith(t) for t in AUDIO_TYPES):
            audio_attachment = att
            break
        if att.filename and att.filename.endswith((".ogg", ".mp3", ".wav", ".m4a", ".webm", ".mp4")):
            audio_attachment = att
            break

    # También detectar voice messages de Discord
    if not audio_attachment and message.flags.value & (1 << 13):  # IS_VOICE_MESSAGE flag
        for att in message.attachments:
            audio_attachment = att
            break

    async with message.channel.typing():
        try:
            if audio_attachment:
                await message.add_reaction("🎧")
                audio_bytes = await audio_attachment.read()
                texto = await transcribir_audio(audio_bytes, audio_attachment.filename)

                if not texto.strip():
                    await message.reply("No pude entender el audio. Intenta de nuevo.")
                    return

                await message.reply(f"🎤 *\"{texto}\"*\n⏳ Procesando...")
            else:
                texto = message.content.replace(f"<@{bot.user.id}>", "").strip()

                if not texto:
                    await message.reply("Escribe o manda un audio con tu mensaje.")
                    return

            # Rutear al handler correcto
            if es_canal_coach:
                await procesar_coach(message, texto)
            else:
                persona = CANALES[canal_id] if es_canal_tareas else "Sin asignar"
                await procesar_y_responder(message, texto, persona)

            if audio_attachment:
                await message.remove_reaction("🎧", bot.user)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await message.reply("Hubo un error procesando tu mensaje. Intenta de nuevo.")


def run_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token or token == "tu_token_de_discord_aqui":
        logger.error("DISCORD_BOT_TOKEN no configurado en .env")
        return
    bot.run(token)
