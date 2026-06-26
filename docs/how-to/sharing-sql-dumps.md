# Sharing SQL dumps

This page describes how to share SQL dumps of your database with other people.

## 1. **Create a SQL dump**

`docker exec -t tapcast-postgres-1 pg_dump -U <username> <db_name> > data_dump.sql`

Replace `<username>` with your PostgreSQL username and `<db_name>` with the name of your database. This command will create a file named `data_dump.sql` in your current directory. Username and DB name can be found in .env file.

## 2. **Share the SQL dump**

You can share the `data_dump.sql` file using any file-sharing method you prefer.

## 3. **Importing the SQL dump**

The project is configured so that a file named `data_dump.sql` in the project root will be automatically imported into the database when you start the Docker containers.

This process may require you to put down the postgres container, but it was not tested if this is necessary. If you want to be sure, you can run the following command to stop the PostgreSQL container before importing the SQL dump:
`docker-compose down postgres`

If you want to clear the existing data before importing the new SQL dump, you can run the following command to delete the existing docker volume for PostgreSQL data:
`docker volume rm tapcast_pgdata`

To import the SQL dump, simply place the `data_dump.sql` file in the project root and run:
`docker-compose up -d postgres`

This will start the PostgreSQL container and import the SQL dump into the database. After the import is complete, you can remove the `data_dump.sql` file from the project root to prevent it from being imported again in the future.

## 4. **Verify the import**

After the import is complete, you can verify that the data has been imported correctly by connecting to the PostgreSQL database and checking the tables and data. You can use a PostgreSQL client or run the following command to connect to the database:
`docker exec -it tapcast-postgres-1 psql -U <username> -d <db_name>`

You can e.g. run `\dt` to list the tables and `SELECT * FROM <table_name>;` to view the data in a specific table.
