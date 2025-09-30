// config.js
const dotenv = require('dotenv');
const path = require('path');

// Construye la ruta al archivo .env (ajusta la ruta según tu estructura)
const envPath = path.join(__dirname, '..', '.env');

// Carga las variables de entorno desde el archivo .env
dotenv.config({ path: envPath });

module.exports = {
  rabbitmqUser: process.env.RABBITMQ_USER || 'guest',
  rabbitmqPassword: process.env.RABBITMQ_PASSWORD || 'guest',
  rabbitmqHost: process.env.RABBITMQ_HOST || 'localhost'
};