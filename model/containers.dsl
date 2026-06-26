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

        eventsAPI = softwareSystem "Events API" {
            description "External API that provides information about local events, which can influence demand."
        }

        oauth = softwareSystem "OAuth Provider" {
            description "External service that handles user authentication and authorization."
        }

        system = softwareSystem "TapCast" {
            description "A system that forecasts the demand of products/categories of products in a bar"

            frontend = container "Frontend" "Provides the user interface." "React TS + nginx" {
                upload = component "Upload" "Allows users to upload POS data in XSLX format." "React component"
                dashboard = component "Dashboard" "Displays demand forecasts and insights." "React component"
                auth = component "Authentication" "Allows users to authenticate and authorize access." "React component"
            }

            backend = container "Backend" "Handles API requests, scheduling, and background external API polling (weather, events)." "Go API + Scheduler" {
                api = component "API" "Handles REST API requests from the frontend." "Go Chi router"
                scheduler = component "Scheduler" "Schedules external API polling." "Go Cron job scheduler"
                batchDownloader = component "Batch Downloader" "Downloads batch data for model training." "Go service"
                auth = component "Authentication" "Handles user authentication and authorization." "Go service"
                spreadsheetIngestor = component "Spreadsheet Ingestor" "Uploads the XSLX files to S3, waiting for deferred parsing"
                spreadsheetParser = component "Spreadsheet Parser" "Parses uploaded XSLX files and extracts relevant data." "Go service"
                inference_service = component "Inference Service" "Handles gRPC requests for predictions from the inference service." "Go gRPC client"
                weather_facade = component "Weather Facade" "Facilitates communication with the Weather API." "Go service"
                events_facade = component "Events Facade" "Facilitates communication with the Events API." "Go service"


                frontend -> backend.api "Sends API requests to" "REST"
                frontend.upload -> backend.api "Sends uploaded file to" "REST"
                frontend.dashboard -> backend.api "Requests forecasts and insights from" "REST"
                frontend.auth -> backend.api "Authenticates users with" "REST"

                api -> auth "Delegates authentication to"
                api -> inference_service "Requests predictions from"
                api -> spreadsheetIngestor "Sends uploaded XSLX data to" "Go Structs"

                backend.auth -> oauth "Authenticates users with" "OAuth 2.0"
                backend.scheduler -> weather_facade "Polls for upcoming data from" "REST"
                backend.scheduler -> events_facade "Polls for upcoming data from" "REST"
                backend.spreadsheetIngestor -> spreadsheetParser "Sends notification to"
                backend.batchDownloader -> weather_facade "Requests historical data from" "REST"
                backend.batchDownloader -> events_facade "Requests historical data from" "REST"

                weather_facade -> weatherAPI "Fetches weather data from" "REST"
                events_facade -> eventsAPI "Fetches event data from" "REST"
            }

            database = container "Database" "Stores raw data, current data, and job queues." "Postgres, PGMQ" {
                training = component "Training data storage" "Stores historical data used for model training." "Postgres tables"
                current = component "Current data storage" "Stores the most recent data used for inference." "Postgres tables"
                job_queue = component "Job queue" "Stores jobs for model training and data processing." "PGMQ"

                backend -> database.job_queue "Publishes training data updates to" "PGMQ"
                backend.spreadsheetParser -> database.training "Writes parsed POS data to" "GORM"
                backend.batchDownloader -> database.training "Writes historical external data to" "GORM"
                backend.scheduler -> database.current "Writes upcoming external data to" "GORM"
            }

            training = container "Training" "Executes model training jobs." "Python service" {
                job_consumer = component "Job Consumer" "Initiates training toolchain based on jobs from the job queue." "Python service"
                parser = component "Parser" "Fetches and parses DB's SQL data to Python objects." "SQL -> Python"
                feature_extractor = component "Feature Extractor" "Extracts features from data" "Python service"
                splitter = component "Splitter" "Splits data into sets." "Python service"
                model_trainer = component "Model Trainer" "Trains machine learning models using the extracted features." "Python service"
                exporter = component "Model Exporter" "Exports trained models to S3." "Python service"

                job_consumer -> database.job_queue "Consumes training jobs from" "PGMQ"
                
                job_consumer -> parser "Initiates pipeline" "Python call"

                parser -> database.training "Fetches training data from" "SQL"
                parser -> feature_extractor "Provides parsed data to" "Python objects"
                feature_extractor -> splitter "Provides extracted features to" "Python objects"
                splitter -> model_trainer "Provides training, validation, and test sets to" "Python objects"
                model_trainer -> exporter "Provides trained model to" "Python objects"
            }

            inference = container "Inference" "Serves forecasting predictions." "Python service" {
                grpc_server = component "gRPC Server" "Handles gRPC requests for predictions from the backend." "Python gRPC server"
                model_loader = component "Model Loader" "Loads the latest trained model." "Python service"                
                parser = component "Parser" "Fetches and parses DB's SQL data to Python objects." "SQL -> Python"
                feature_extractor = component "Feature Extractor" "Extracts features from data" "Python service"
                predictor = component "Predictor" "Generates demand forecasts using the loaded model and given features" "Python service"

                manager = component "Service manager" "Manages the lifecycle of the inference service, including loading models and handling requests." "Python service"
                
                parser -> database.current "Fetches current data from" "SQL"
                backend.inference_service -> grpc_server "Sends prediction requests to" "gRPC"
                grpc_server -> manager "Sends prediction requests to" "Python call"
                manager -> grpc_server "Sends predictions to" "Python call"

                manager -> model_loader "Loads the latest model from" "Python call"
                manager -> parser "Fetches and parses current data from DB" "Python call"
                parser -> feature_extractor "Provides parsed data to" "Python objects"
                feature_extractor -> predictor "Provides loaded model and extracted features to" "Python objects"
                model_loader -> predictor "Provides loaded model to" "Python call"
                predictor -> manager "Provides predictions to" "Python objects"
            }


            s3 = container "S3" "Provides object storage for machine learning models." "MinIO" {
                backend.spreadsheetIngestor -> s3 "Uploads raw XLSX to"
                backend.spreadsheetParser -> s3 "Downloads XLSX data from"
                training.exporter -> s3 "Uploads trained model to" "MinIO API"
                inference.model_loader -> s3 "Downloads latest model from" "MinIO API"
            }
        }

        user -> system "Checks forecasts on" "HTTPS"
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

        component system.inference "inference_components" {
            include *
            autoLayout lr
        }
    }
}