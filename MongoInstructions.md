# Installation Instruction for Local Deployment

Download the MongoDB Community Server from
https://www.mongodb.com/try/download/community-kubernetes-operator

Follow the instructions for self-managed deployments
https://www.mongodb.com/docs/manual/administration/install-community/

To view the database, use MongoDB Compass (came together with MongoDB installation)

For Python with MongoDB, try
https://www.mongodb.com/resources/languages/pymongo-tutorial

After setting up the local mongodb, you need to add following key=value pair into your .env file

```shell
MONGO_DB_URL="mongodb://localhost:27017/"
```

## Instruction for Using remote cloud for testing

You will need the MongoDB Compass (came together with MongoDB installation)

Supply your IP Adress to be whitelisted.

Then get the MONGO_DB_URL and add it into the .env file
