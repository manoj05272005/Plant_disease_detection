# Backend Files, Functions & Operations - Complete Reference

## Comprehensive Function Reference Table

| File Path | Function Name | Operation/Purpose |
|-----------|--------------|-------------------|
| **app/main.py** | | |
| | `create_application()` | Creates and configures FastAPI application instance |
| | `get_application()` | Returns configured FastAPI app with all routes and middleware |
| | `startup_event()` | Initializes database and AI model on server startup |
| | `shutdown_event()` | Cleanup tasks when server shuts down |
| | CORS middleware setup | Enables cross-origin requests for frontend integration |
| **app/core/config.py** | | |
| | `Settings` (class) | Loads all configuration from environment variables |
| | `get_settings()` | Returns singleton Settings instance |
| | Database configuration | DATABASE_URL, connection settings |
| | JWT configuration | SECRET_KEY, ALGORITHM, token expiration |
| | File upload settings | MAX_FILE_SIZE, ALLOWED_EXTENSIONS |
| | AI model settings | MODEL_PATH, CONFIDENCE_THRESHOLD |
| **app/core/database.py** | | |
| | `get_db()` | Provides database session for dependency injection |
| | `init_db()` | Creates all database tables on startup |
| | `engine` | SQLAlchemy database engine instance |
| | `SessionLocal` | Database session factory |
| | `Base` | Declarative base for ORM models |
| **app/core/security.py** | | |
| | `get_password_hash(password)` | Hashes password using bcrypt for secure storage |
| | `verify_password(plain, hashed)` | Verifies plain password against hashed password |
| | `create_access_token(data, expires_delta)` | Generates JWT access token with expiration |
| | `verify_token(token)` | Validates JWT token and extracts payload |
| | `get_current_user(token, db)` | Retrieves user from database using JWT token |
| | `get_current_active_user(user)` | Ensures user is active and not disabled |
| | `generate_otp(length)` | Creates random OTP for 2-factor authentication |
| | `verify_otp(user_otp, stored_otp, expiry)` | Validates OTP against stored value and expiry time |
| **app/api/v1/auth.py** | | |
| | `login(credentials, db)` | Authenticates user and returns JWT token |
| | `register(user_data, db)` | Creates new user account with hashed password |
| | `refresh_token(token, db)` | Generates new access token from refresh token |
| | `logout(token, db)` | Invalidates current user token/session |
| | `verify_otp_endpoint(otp_data, db)` | Verifies OTP for 2-factor authentication |
| | `resend_otp(user_id, db)` | Generates and sends new OTP to user |
| | `forgot_password(email, db)` | Initiates password reset process |
| | `reset_password(reset_data, db)` | Updates password using reset token |
| **app/api/v1/user.py** | | |
| | `get_current_user_profile(user, db)` | Retrieves logged-in user's profile information |
| | `update_user_profile(user_id, data, db)` | Updates user profile fields (name, email, etc.) |
| | `change_password(user, password_data, db)` | Changes user password after verification |
| | `delete_user_account(user, db)` | Soft deletes user account and associated data |
| | `get_user_stats(user, db)` | Returns user statistics (diagnoses count, etc.) |
| **app/api/v1/diagnosis.py** | | |
| | `diagnose_image(file, language, user, db)` | Main endpoint: uploads image and returns disease prediction |
| | `get_diagnosis_by_id(diagnosis_id, user, db)` | Retrieves specific diagnosis record by ID |
| | `create_diagnosis_record(user, disease, confidence, image_path, db)` | Saves diagnosis result to database |
| | `process_uploaded_image(file)` | Validates and processes uploaded image file |
| | `generate_heatmap(image, prediction)` | Creates Grad-CAM visualization for prediction |
| | `format_diagnosis_response(diagnosis, language)` | Formats diagnosis data for API response |
| **app/api/v1/history.py** | | |
| | `get_user_history(user, skip, limit, db)` | Returns paginated diagnosis history for user |
| | `get_diagnosis_details(diagnosis_id, user, db)` | Retrieves detailed diagnosis with remediation info |
| | `delete_diagnosis(diagnosis_id, user, db)` | Deletes specific diagnosis record |
| | `export_history_pdf(user, db)` | Generates PDF report of user's diagnosis history |
| | `filter_history_by_date(user, start_date, end_date, db)` | Filters diagnoses by date range |
| | `get_statistics(user, db)` | Calculates user diagnosis statistics |
| **app/api/v1/remediation.py** | | |
| | `get_remediation(disease_name, language, db)` | Retrieves treatment recommendations for disease |
| | `get_all_diseases(db)` | Lists all supported crop diseases |
| | `search_remediation(query, db)` | Searches remediation knowledge base |
| **app/api/v1/notifications.py** | | |
| | `get_user_notifications(user, db)` | Retrieves all notifications for user |
| | `mark_notification_read(notification_id, user, db)` | Marks notification as read |
| | `delete_notification(notification_id, user, db)` | Deletes specific notification |
| | `create_notification(user_id, message, type, db)` | Creates new notification for user |
| | `get_unread_count(user, db)` | Returns count of unread notifications |
| **app/services/ai_service.py** | | |
| | `AIService` (class) | Main AI service class for disease detection |
| | `load_model()` | Loads TensorFlow/Keras model from disk |
| | `load_labels()` | Loads disease label mapping from text file |
| | `preprocess_image(image_path)` | Prepares image for model input (resize, normalize) |
| | `predict(image_path)` | Performs disease prediction on image |
| | `predict_batch(image_paths)` | Batch prediction for multiple images |
| | `get_top_predictions(predictions, top_k)` | Returns top K predictions with confidence scores |
| | `generate_gradcam(image_path, prediction)` | Creates Grad-CAM heatmap visualization |
| | `calculate_confidence_level(score)` | Categorizes confidence (Very High, High, Medium, Low) |
| | `validate_prediction(prediction)` | Validates prediction meets confidence threshold |
| | `get_model_info()` | Returns model metadata (version, classes, etc.) |
| **app/services/remediation_service.py** | | |
| | `RemediationService` (class) | Service for disease treatment recommendations |
| | `load_knowledge_base()` | Loads remediation data from JSON file |
| | `get_remediation(disease_name, language)` | Retrieves treatment for specific disease |
| | `translate_remediation(remediation, language)` | Translates remediation to specified language |
| | `search_by_symptoms(symptoms)` | Finds diseases matching symptom description |
| | `get_prevention_tips(disease_name)` | Returns prevention measures for disease |
| | `get_treatment_steps(disease_name)` | Returns step-by-step treatment guide |
| | `format_remediation_response(data)` | Formats remediation data for API response |
| **app/services/notification_service.py** | | |
| | `NotificationService` (class) | Manages user notifications |
| | `create_notification(user_id, message, type, db)` | Creates new notification record |
| | `send_email_notification(user, message)` | Sends email notification to user |
| | `send_push_notification(user, message)` | Sends push notification to mobile device |
| | `get_user_notifications(user_id, db)` | Retrieves all notifications for user |
| | `mark_as_read(notification_id, db)` | Updates notification read status |
| | `delete_old_notifications(days, db)` | Cleanup: deletes notifications older than X days |
| | `get_unread_count(user_id, db)` | Counts unread notifications for user |
| **app/utils/file_handler.py** | | |
| | `save_upload_file(file, folder)` | Saves uploaded file to specified folder with UUID name |
| | `validate_image_file(file)` | Checks file type, size, and format validity |
| | `get_file_extension(filename)` | Extracts file extension from filename |
| | `is_allowed_extension(filename)` | Verifies file extension is in allowed list |
| | `get_file_size(file)` | Returns file size in bytes |
| | `delete_file(file_path)` | Removes file from filesystem |
| | `create_directory(path)` | Creates directory if it doesn't exist |
| | `cleanup_old_files(folder, days)` | Deletes files older than specified days |
| | `generate_unique_filename(original_name)` | Creates UUID-based unique filename |
| **app/utils/image_processing.py** | | |
| | `preprocess_for_model(image_path)` | Prepares image for AI model (resize, normalize) |
| | `resize_image(image, target_size)` | Resizes image to target dimensions |
| | `normalize_image(image)` | Normalizes pixel values to 0-1 range |
| | `augment_image(image)` | Applies data augmentation (rotation, flip, etc.) |
| | `convert_to_rgb(image)` | Converts image to RGB color space |
| | `remove_background(image)` | Removes background from image |
| | `enhance_image(image)` | Applies enhancement filters (contrast, brightness) |
| | `detect_edges(image)` | Edge detection for image analysis |
| | `crop_to_content(image)` | Crops image to main content area |
| | `validate_image_quality(image_path)` | Checks image quality meets requirements |
| | `create_thumbnail(image_path, size)` | Generates thumbnail version of image |
| | `apply_gradcam_overlay(image, heatmap)` | Overlays Grad-CAM heatmap on original image |
| **app/utils/localization.py** | | |
| | `get_translation(key, language)` | Retrieves translated text for given key and language |
| | `load_translations()` | Loads all translation files into memory |
| | `get_supported_languages()` | Returns list of supported language codes |
| | `validate_language_code(code)` | Checks if language code is supported |
| | `translate_diagnosis(diagnosis, language)` | Translates diagnosis result to target language |
| | `translate_remediation(remediation, language)` | Translates treatment info to target language |
| | `get_default_language()` | Returns default fallback language (English) |
| | `format_message(template, params, language)` | Formats localized message with parameters |
| **app/utils/pdf_generator.py** | | |
| | `PDFGenerator` (class) | PDF report generation service |
| | `generate_diagnosis_report(diagnosis, user)` | Creates PDF report for single diagnosis |
| | `generate_history_report(diagnoses, user)` | Creates PDF report for diagnosis history |
| | `add_header(canvas, title)` | Adds header section to PDF |
| | `add_footer(canvas, page_number)` | Adds footer with page number |
| | `add_user_info(canvas, user)` | Adds user information section |
| | `add_diagnosis_details(canvas, diagnosis)` | Adds diagnosis details with image |
| | `add_remediation_section(canvas, remediation)` | Adds treatment recommendations |
| | `add_chart(canvas, data)` | Adds data visualization chart |
| | `add_image(canvas, image_path, x, y, width, height)` | Embeds image in PDF |
| | `save_pdf(canvas, output_path)` | Saves generated PDF to file |
| **app/models/schemas.py** | | |
| | `UserCreate` (schema) | Pydantic model for user registration data |
| | `UserLogin` (schema) | Pydantic model for login credentials |
| | `UserResponse` (schema) | Pydantic model for user data response |
| | `UserUpdate` (schema) | Pydantic model for profile update data |
| | `Token` (schema) | Pydantic model for JWT token response |
| | `DiagnosisRequest` (schema) | Pydantic model for diagnosis request data |
| | `DiagnosisResponse` (schema) | Pydantic model for diagnosis result response |
| | `RemediationResponse` (schema) | Pydantic model for treatment recommendations |
| | `NotificationResponse` (schema) | Pydantic model for notification data |
| | `HistoryResponse` (schema) | Pydantic model for history list response |
| | `PaginationParams` (schema) | Pydantic model for pagination parameters |
| | `PasswordChange` (schema) | Pydantic model for password change request |
| | `OTPVerification` (schema) | Pydantic model for OTP verification data |
| | `ErrorResponse` (schema) | Pydantic model for error responses |
| **tests/conftest.py** | | |
| | `test_db()` | Fixture: Provides test database session |
| | `test_client()` | Fixture: Creates FastAPI test client |
| | `test_user()` | Fixture: Creates test user for authentication tests |
| | `auth_headers()` | Fixture: Generates authentication headers with JWT |
| | `sample_image()` | Fixture: Provides sample test image |
| | `mock_ai_service()` | Fixture: Mocks AI service for faster tests |
| | `cleanup()` | Fixture: Cleanup after tests (delete files, reset DB) |
| **tests/unit/test_security.py** | | |
| | `test_password_hashing()` | Tests bcrypt password hashing |
| | `test_password_verification()` | Tests password hash validation |
| | `test_jwt_token_creation()` | Tests JWT token generation |
| | `test_jwt_token_validation()` | Tests JWT token verification |
| | `test_jwt_token_expiration()` | Tests token expiration handling |
| | `test_otp_generation()` | Tests OTP creation with correct length |
| | `test_otp_verification()` | Tests OTP validation logic |
| | `test_invalid_token_handling()` | Tests error handling for invalid tokens |
| **tests/unit/test_file_handler.py** | | |
| | `test_file_upload()` | Tests file upload and storage |
| | `test_file_validation()` | Tests file type and size validation |
| | `test_allowed_extensions()` | Tests extension whitelist checking |
| | `test_file_size_limits()` | Tests max file size enforcement |
| | `test_unique_filename_generation()` | Tests UUID filename generation |
| | `test_file_deletion()` | Tests file removal functionality |
| | `test_directory_creation()` | Tests folder creation if not exists |
| **tests/unit/test_image_processing.py** | | |
| | `test_image_preprocessing()` | Tests image preparation for model |
| | `test_image_resizing()` | Tests image dimension changes |
| | `test_image_normalization()` | Tests pixel value normalization |
| | `test_image_augmentation()` | Tests data augmentation techniques |
| | `test_rgb_conversion()` | Tests color space conversion |
| | `test_quality_validation()` | Tests image quality checking |
| | `test_thumbnail_creation()` | Tests thumbnail generation |
| **tests/unit/test_localization.py** | | |
| | `test_translation_loading()` | Tests translation file loading |
| | `test_get_translation()` | Tests text translation retrieval |
| | `test_language_validation()` | Tests language code validation |
| | `test_fallback_language()` | Tests default language fallback |
| | `test_unsupported_language()` | Tests handling of unsupported languages |
| **tests/integration/test_auth_flow.py** | | |
| | `test_user_registration_flow()` | Tests complete registration process |
| | `test_login_flow()` | Tests full login workflow |
| | `test_token_refresh_flow()` | Tests token renewal process |
| | `test_password_reset_flow()` | Tests complete password reset |
| | `test_otp_verification_flow()` | Tests 2FA authentication flow |
| **tests/integration/test_diagnosis_flow.py** | | |
| | `test_complete_diagnosis_flow()` | Tests image upload → prediction → save |
| | `test_diagnosis_with_remediation()` | Tests diagnosis + treatment retrieval |
| | `test_diagnosis_history_retrieval()` | Tests fetching user diagnosis history |
| | `test_pdf_report_generation()` | Tests PDF report creation workflow |
| **tests/integration/test_notification_flow.py** | | |
| | `test_notification_creation()` | Tests notification creation on events |
| | `test_notification_retrieval()` | Tests fetching user notifications |
| | `test_mark_as_read()` | Tests updating notification status |
| | `test_notification_deletion()` | Tests notification removal |
| **tests/services/test_ai_service.py** | | |
| | `test_model_loading()` | Tests AI model initialization |
| | `test_image_prediction()` | Tests disease prediction accuracy |
| | `test_batch_prediction()` | Tests multiple image processing |
| | `test_gradcam_generation()` | Tests heatmap visualization creation |
| | `test_confidence_calculation()` | Tests confidence score categorization |
| | `test_prediction_validation()` | Tests threshold enforcement |
| **tests/services/test_remediation_service.py** | | |
| | `test_knowledge_base_loading()` | Tests remediation data loading |
| | `test_get_remediation()` | Tests treatment retrieval |
| | `test_translation()` | Tests multi-language remediation |
| | `test_symptom_search()` | Tests disease search by symptoms |
| | `test_prevention_tips()` | Tests prevention info retrieval |
| **tests/services/test_notification_service.py** | | |
| | `test_create_notification()` | Tests notification creation |
| | `test_email_sending()` | Tests email notification dispatch |
| | `test_unread_count()` | Tests unread notification counting |
| | `test_old_notification_cleanup()` | Tests automatic notification deletion |
| **tests/demo/test_security_standalone.py** | | |
| | `test_password_hashing_demo()` | Demo: Password hashing validation (5 tests) |
| | `test_jwt_tokens_demo()` | Demo: JWT token operations (4 tests) |
| | `test_otp_generation_demo()` | Demo: OTP creation/validation (4 tests) |
| | `test_security_validation_demo()` | Demo: Input validation (3 tests) |
| **tests/demo/test_validation_standalone.py** | | |
| | `test_file_validation_demo()` | Demo: File type/size validation (5 tests) |
| | `test_confidence_calculation_demo()` | Demo: Confidence categorization (5 tests) |
| | `test_data_formatting_demo()` | Demo: Response formatting (2 tests) |
| | `test_language_handling_demo()` | Demo: Multi-language support (4 tests) |
| | `test_pagination_demo()` | Demo: Pagination logic (4 tests) |

## Summary Statistics

| Category | File Count | Function Count |
|----------|-----------|----------------|
| **Main Application** | 1 | 4 functions |
| **Core (Config, DB, Security)** | 3 | 15 functions |
| **API Endpoints** | 6 | 35+ endpoint functions |
| **Services** | 3 | 30+ service functions |
| **Utilities** | 4 | 35+ utility functions |
| **Models/Schemas** | 1 | 15+ Pydantic models |
| **Tests** | 12 | 185+ test functions |
| **TOTAL** | **30 files** | **320+ functions** |

## File Organization Summary

```
backend/
├── app/
│   ├── main.py                 # 4 functions - App setup
│   ├── core/                   # 15 functions - Config, DB, Security
│   ├── api/v1/                 # 35+ functions - API endpoints
│   ├── services/               # 30+ functions - Business logic
│   ├── utils/                  # 35+ functions - Utilities
│   └── models/                 # 15+ schemas - Data validation
└── tests/
    ├── unit/                   # 60+ tests - Component testing
    ├── integration/            # 35+ tests - Workflow testing
    ├── services/               # 40+ tests - Service testing
    └── demo/                   # 36 tests - Quick demonstration
```
