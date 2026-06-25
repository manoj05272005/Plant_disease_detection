# Plant Disease Detection Frontend (Flutter)

Mobile client for the Plant Disease Detection platform. The app handles user auth, crop image capture, diagnosis results, remediation guidance, and profile/history views.

## Main File Structure

```
frontend/
	lib/
		main.dart
		screens/
			auth/
			crop_capture_page.dart
			diagnosis_result_page.dart
			home_page.dart
			profile_page.dart
			remediation_page.dart
		services/
			api_config.dart
			app_localizations.dart
			auth_api.dart
			blur_detector.dart
			diagnosis_api.dart
			history_api.dart
			location_service.dart
			notification_api.dart
			token_storage.dart
			user_api.dart
			weather_api.dart
	assets/
		images/
		models/
		remediation/
	android/
	ios/
	web/
	windows/
	macos/
	linux/
	pubspec.yaml
```

## Setup

### Prerequisites
- Flutter SDK installed and on PATH
- Android Studio / Xcode (for mobile builds)
- A running backend API server

### Install Dependencies

```
flutter pub get
```

### Configure API Endpoints

Update the API host and weather key in `lib/services/api_config.dart`:
- `baseHost` should point to your backend (example: `http://192.168.1.30:8000`)
- `weatherApiKey` should be a valid WeatherAPI key

### Run the App

```
flutter run
```

## Features

- Authentication (login, registration, password reset)
- Crop image capture and submission
- Diagnosis results and remediation guidance
- Profile and account management
- History of previous diagnoses
- Weather and location-aware context
- Token storage and session persistence
- Localized UI support

## Helpful Commands

```
flutter doctor
flutter clean
flutter pub get
```
