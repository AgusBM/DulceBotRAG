// index.js — ESM
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  Browsers,
} from '@whiskeysockets/baileys'
import qrcode from 'qrcode-terminal'
import pino from 'pino'
import amqplib from 'amqplib'
import process from 'node:process'

/** ========= Config ========= **/
const logger = pino({ level: 'info' })

// RabbitMQ (deben coincidir con tu docker/config)
const RABBITMQ_USER = process.env.RABBITMQ_USER || 'userapp_rabbitmq'
const RABBITMQ_PASSWORD = process.env.RABBITMQ_PASSWORD || 'dcji484hf8ft4'
const RABBITMQ_HOST = process.env.RABBITMQ_HOST || 'localhost'
const AMQP_URL = `amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST}:5672`

// Colas (¡coinciden con whatsapp_consumer.py!)
const WHATSAPP_QUEUE = 'whatsapp_queue'
const RESPONSE_QUEUE = 'response_queue'

// Auth Baileys
const { state, saveCreds } = await useMultiFileAuthState('./auth')
const { version } = await fetchLatestBaileysVersion()

/** ========= Globals ========= **/
let sock
let amqpConn
let amqpCh

// Deduplicado de mensajes entrantes (2 min)
const recentMsgIds = new Set()
const remember = (id, ms = 2 * 60 * 1000) => {
  recentMsgIds.add(id)
  setTimeout(() => recentMsgIds.delete(id), ms)
}

// Rate limit por número al enviar (2s)
const lastSentAt = new Map()
async function sendRateLimited (jid, text, minIntervalMs = 2000) {
  const phone = jid.replace('@s.whatsapp.net', '')
  const now = Date.now()
  const last = lastSentAt.get(phone) || 0
  if (now - last < minIntervalMs) {
    console.warn('[RateLimit] bloqueado envío a', phone)
    return
  }
  lastSentAt.set(phone, now)
  await sock.sendMessage(jid, { text })
}

/** ========= AMQP ========= **/
async function initAmqp () {
  amqpConn = await amqplib.connect(AMQP_URL)
  amqpCh = await amqpConn.createChannel()
  await amqpCh.assertQueue(WHATSAPP_QUEUE, { durable: true })
  await amqpCh.assertQueue(RESPONSE_QUEUE, { durable: true })
  console.log('[AMQP] conectado y colas declaradas')

  // Consumir respuestas generadas por Python y enviarlas a WhatsApp
  amqpCh.consume(RESPONSE_QUEUE, async msg => {
    if (!msg) return
    try {
      const { phone_number, text } = JSON.parse(msg.content.toString())
      if (phone_number && text) {
        const jid = phone_number.includes('@') ? phone_number : `${phone_number}@s.whatsapp.net`
        await sendRateLimited(jid, text)
        console.log('[AMQP->WA] Enviado a', jid, '::', text)
      }
      amqpCh.ack(msg)
    } catch (e) {
      console.error('Error procesando respuesta de RESPONSE_QUEUE:', e)
      // descarta mensaje malformado para evitar bucles
      amqpCh.nack(msg, false, false)
    }
  })
}

/** ========= WhatsApp ========= **/
let restartCount = 0
const MAX_RESTARTS = 5

async function startSock () {
  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    browser: Browsers.appropriate('Chrome'),
    logger,
  })

  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      qrcode.generate(qr, { small: true })
      console.log('Escanea el QR mostrado arriba.')
    }

    if (connection === 'open') {
      console.log('✅ WhatsApp conectado')
      restartCount = 0
    }

    if (connection === 'close') {
      const code = lastDisconnect?.error?.output?.statusCode
      console.log('Conexión cerrada. code=', code)

      // 401 = sesión inválida; 440 (replaced) mejor salir y evitar doble instancia
      if (code === 401) {
        console.error('Sesión inválida. Borra ./auth y vuelve a emparejar.')
        process.exit(1)
      }
      if (code === 440) {
        console.error('Cerrado por conflicto (replaced). Asegúrate de NO tener otra instancia usando ./auth.')
        process.exit(1)
      }

      if (restartCount < MAX_RESTARTS) {
        restartCount++
        const delay = Math.min(2000 * restartCount, 10000)
        console.log(`Reintentando conexión en ${delay}ms (intento ${restartCount}/${MAX_RESTARTS})...`)
        setTimeout(() => startSock(), delay)
      } else {
        console.error('Demasiados reintentos. Revisa red/NTP y relanza manualmente.')
        process.exit(1)
      }
    }
  })

  // === Entrantes -> publicar en whatsapp_queue ===
  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // Solo notificaciones nuevas
    if (type !== 'notify') return

    for (const m of messages) {
      try {
        // 1) Evita eco: ignora lo que envía este propio bot
        if (m.key?.fromMe) continue

        // 2) Dedup por ID
        const id = m.key?.id
        if (!id || recentMsgIds.has(id)) continue
        remember(id)

        // 3) Chats individuales (evita grupos/status). Quita esta línea si quieres grupos.
        const jid = m.key?.remoteJid || ''
        if (!jid.endsWith('@s.whatsapp.net')) continue

        // 4) Extrae texto
        const text =
          m.message?.conversation ||
          m.message?.extendedTextMessage?.text ||
          m.message?.imageMessage?.caption ||
          m.message?.videoMessage?.caption || ''
        if (!text.trim()) continue

        // 5) Publica en cola de entrada que consume Python
        const payload = {
          phone_number: jid.replace('@s.whatsapp.net', '').replace(':', ''),
          message: text,
          agent_id: 'default',
        }
        amqpCh.sendToQueue(WHATSAPP_QUEUE, Buffer.from(JSON.stringify(payload)), { persistent: true })
        console.log('[WA->AMQP] Publicado:', payload)
      } catch (e) {
        console.error('Error publicando mensaje entrante en AMQP:', e)
      }
    }
  })

  return sock
}

/** ========= Boot ========= **/
try {
  await startSock()
  await initAmqp()
} catch (err) {
  console.error('Fallo al iniciar:', err)
  process.exit(1)
}

// Cierre limpio
process.on('SIGINT', async () => {
  try { await amqpCh?.close(); await amqpConn?.close() } catch {}
  process.exit(0)
})
