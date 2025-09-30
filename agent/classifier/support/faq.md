# FAQ - Sistema d'Agents Conversacionals per a Gestió de Consultes

## 1. Què és aquest sistema d'agents conversacionals?
Aquest sistema és una plataforma integral que permet rebre consultes per WhatsApp i gestionar-les automàticament mitjançant diversos agents especialitzats. Combina tecnologies com RabbitMQ per al repartiment de missatges, SQLite per a l'emmagatzematge de l'històric de converses i LM Studio per a la generació de respostes mitjançant IA.

## 2. Quines tecnologies s'utilitzen en aquest projecte?
- **Baileys**: Biblioteca de Node.js que permet interactuar amb l'API de WhatsApp per rebre i enviar missatges.
- **RabbitMQ**: Sistema de missatgeria que actua com a intermediari per distribuir els missatges entrants i sortints entre els agents.
- **SQLite**: Base de dades lleugera que emmagatzema l'històric de converses, facilitant la recuperació de context.
- **LM Studio**: Plataforma d'IA que genera embeddings i respostes contextualitzades basades en el contingut de la conversa i en documents de coneixement.
- **Python i Node.js**: Llenguatges utilitzats per implementar la lògica dels agents i la integració amb els altres sistemes.

## 3. Com funciona el flux de treball?
1. **Recepció de missatges**:  
   - Els missatges de WhatsApp són capturats per Baileys i enviats a la cola d'entrada de RabbitMQ (`WHATSAPP_QUEUE`).

2. **Processament de consultes**:  
   - Un component (per exemple, un agent en Python) consumeix els missatges de la cola, classifica la consulta i determina si s'ha de gestionar per l'agent d'ordres (OrderAgent) o de suport (CustomerSupportAgent).

3. **Generació de respostes**:  
   - L'agent guarda el missatge i recupera l'històric de la conversa (limitant, per exemple, als últims 10 missatges) des de SQLite.
   - També recupera context addicional a partir de documents (entrevistes, guies, etc.) que contenen metadades (ex. el personatge SOS) per generar un prompt complet.
   - Aquest prompt, que inclou el context, l'històric i la consulta actual, es envia a LM Studio per generar una resposta.

4. **Enviament de respostes**:  
   - La resposta generada es guarda a la base de dades i es publica a una altra cola de RabbitMQ (`RESPONSE_QUEUE`), des d'on s'envia finalment a WhatsApp.

## 4. Com es gestiona l'històric de converses?
Els missatges (tant del client com de l'agent) es guarden en una base de dades SQLite mitjançant la classe `ConversationHistoryDB`. Això permet recuperar el context de la conversa en qualsevol moment, incloent només els últims 10 missatges si és necessari, per a que el model LLM generi respostes coherents sense repetir informació prèvia.

## 5. Com s'utilitzen els arxius de coneixement?
Els arxius de coneixement (en format JSON o Markdown) contenen entrevistes i altres documents on apareix el personatge **SOS**. Aquests arxius inclouen metadades al principi, com ara:
- **character**: Indica que el sistema ha de respondre com SOS.
- **persona**: Defineix el to i l'estil de la resposta.
- **instructions**: Directrius per respondre en català, amb un estil concís i professional.

El sistema RAG utilitza aquesta informació per cercar preguntes similars i construir respostes que reflecteixin el to i la personalitat del personatge.

## 6. Quins avantatges ofereix aquest sistema?
- **Resposta personalitzada i contextualitzada**: Integració de l'històric de la conversa i dels documents de coneixement per evitar repeticions i proporcionar respostes coherents.
- **Escalabilitat**: Ús de RabbitMQ per gestionar múltiples agents en paral·lel, facilitant la distribució i el processament asíncron dels missatges.
- **Versatilitat**: Pot adaptar-se a diferents sectors, com la gestió de comandes, la generació de pressupostos, l'atenció al client, etc.
- **Integració amb IA**: La combinació d'embeddings i models de generació de text permet que el sistema aprengui i s'adapti a les necessitats específiques de cada entorn.

## 7. És possible personalitzar el comportament dels agents?
Sí. Cada agent pot tenir directrius pròpies, i els arxius de coneixement inclouen metadades que indiquen com ha de respondre l'agent (per exemple, responent com SOS). Això permet que diferents agents puguin gestionar diferents tipus de consultes de manera independent, tot compartint la infraestructura de missatgeria i el model d'IA.

---

Aquest sistema és el reflex d'una integració avançada de tecnologies per transformar la manera com les empreses gestionen les consultes i la comunicació amb els seus clients. Si tens interès en l'aplicació d'aquesta tecnologia, no dubtis a contactar-me o a seguir-me per conèixer més detalls sobre aquesta revolució en IA conversacional.

#IA #Chatbots #RAG #RabbitMQ #SQL #WhatsAppBot #Automatització #TransformacióDigital #InteligènciaArtificial

