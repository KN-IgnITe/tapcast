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
                api -> spreadsheetParser "Sends uploaded XSLX data to" "REST"

                backend.auth -> oauth "Authenticates users with" "OAuth 2.0"
                backend.scheduler -> weather_facade "Polls for upcoming data from" "REST"
                backend.scheduler -> events_facade "Polls for upcoming data from" "REST"
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

            s3 = container "S3" "Provides object storage for machine learning models." "MinIO"
            training = container "Training" "Executes model training jobs." "Python service"
            inference = container "Inference" "Serves forecasting predictions." "Python service"


            backend -> inference "Requests predictions from" "gRPC"
            training -> database "Reads batch data and consumes jobs from"
            training -> s3 "Writes model to"
            inference -> database "Reads current data from"
            inference -> s3 "Reads model from"
        }

        user -> system "Checks forecasts on" "HTTPS"
        user -> system "Uploads POS XSLX data to" "multipart form upload"
        user -> pos "Exports XSLX data from"
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
            autoLayout lr
        }
    }

}