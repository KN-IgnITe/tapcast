workspace "TapCast" "Bar inventory demand forecasting system" {
    !identifiers hierarchical

    model {

        user = person "User" {
            description "Bar manager/employee who needs to know the demand of products"
        }

        pos = softwareSystem "Point of Sale System" {
            description "The system that the bar uses to record sales and inventory data for tax purposes."
        }

        weatherAPI = softwareSystem "Weather API" {
            description "External API that provides weather data, which can influence demand."
        }

        system = softwareSystem "TapCast" {
            description "A system that forecasts the demand of products/categories of products in a bar"

            frontend = container "Frontend" "Provides the user interface." "React TS + nginx" {
                upload = component "Upload" "Allows users to upload POS data in XSLX format." "React component"
            }

            backend = container "Backend" "Handles API requests and external API polling (weather)." "Go API" {
                api = component "API" "Handles REST API requests from the frontend." "Go Chi router"
                batchDownloader = component "Batch Downloader" "Downloads batch data for model training." "Go service"
                spreadsheetParser = component "Spreadsheet Parser" "Parses uploaded XSLX files and extracts relevant data." "Go service"
                weather_facade = component "Weather Facade" "Facilitates communication with the Weather API." "Go service"

                frontend -> backend.api "Sends API requests to" "REST"
                frontend.upload -> backend.api "Sends uploaded file to" "REST"

                api -> spreadsheetParser "Sends uploaded XSLX data to" "REST"

                backend.batchDownloader -> weather_facade "Requests historical data from" "REST"

                weather_facade -> weatherAPI "Fetches weather data from" "REST"
            }

            database = container "Database" "Stores raw data and job queues." "Postgres, PGMQ" {
                training = component "Training data storage" "Stores historical data used for model training." "Postgres tables"
                job_queue = component "Job queue" "Stores jobs for model training and data processing." "PGMQ"

                backend -> database.job_queue "Publishes training data updates to" "PGMQ"
                backend.spreadsheetParser -> database.training "Writes parsed POS data to" "GORM"
                backend.batchDownloader -> database.training "Writes historical external data to" "GORM"
            }

            training = container "Training" "Executes model training jobs." "Python service" {
                job_consumer = component "Job Consumer" "Initiates training toolchain based on jobs from the job queue." "Python service"
                parser = component "Parser" "Fetches and parses DB's SQL data to Python objects." "SQL -> Python"
                feature_extractor = component "Feature Extractor" "Extracts features from data" "Python service"
                splitter = component "Splitter" "Splits data into sets." "Python service"
                model_trainer = component "Model Trainer" "Trains machine learning models using the extracted features." "Python service"
                exporter = component "Model Exporter" "Exports trained models to local filesystem." "Python service"

                job_consumer -> database.job_queue "Consumes training jobs from" "PGMQ"
                
                job_consumer -> parser "Initiates pipeline" "Python call"

                parser -> database.training "Fetches training data from" "SQL"
                parser -> feature_extractor "Provides parsed data to" "Python objects"
                feature_extractor -> splitter "Provides extracted features to" "Python objects"
                splitter -> model_trainer "Provides training, validation, and test sets to" "Python objects"
                model_trainer -> exporter "Provides trained model to" "Python objects"
            }
        }

        user -> system "Uploads POS XSLX data to" "multipart form upload"
        user -> pos "Exports XSLX data from" "POS system"
    }

    views {
        systemLandscape "context" {
            include *
        }
        
        container system "tapcast_containers" {
            include *
            autoLayout lr
        }

        component system.frontend "frontend_components" {
            include *
            autoLayout lr
        }

        component system.backend "backend_components" {
            include *
            autoLayout lr
        }

        component system.database "database_components" {
            include *
        }

        component system.training "training_components" {
            include *
            autoLayout lr
        }
    }
}