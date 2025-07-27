# MongoDB Security Configuration Script

# 1. Create admin user
use admin
db.createUser({
  user: "cryptoAdmin",
  pwd: "secure_mongodb_password_2025", 
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})

# 2. Create application user for crypto_trader_coach database
use crypto_trader_coach
db.createUser({
  user: "cryptoApp",
  pwd: "app_specific_password_2025",
  roles: [
    { role: "readWrite", db: "crypto_trader_coach" }
  ]
})

# 3. Enable authentication in MongoDB config
# Add to /etc/mongod.conf:
# security:
#   authorization: enabled

# 4. Create indexes for security and performance
db.chat_messages.createIndex({ "user_id": 1, "timestamp": -1 })
db.trade_logs.createIndex({ "user_id": 1, "executed_at": -1 })
db.security_events.createIndex({ "timestamp": -1, "event_type": 1 })
db.portfolio_data.createIndex({ "user_id": 1, "updated_at": -1 })

# 5. Set up collection validation rules
db.createCollection("trade_logs", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "user_id", "trade_id", "symbol", "action", "amount" ],
         properties: {
            user_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            amount: {
               bsonType: "number",
               minimum: 0,
               maximum: 1000000,
               description: "must be a number between 0 and 1,000,000"
            }
         }
      }
   }
})

print("MongoDB security configuration completed!")