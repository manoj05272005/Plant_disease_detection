# Testing Documentation — AgroScan Flutter Frontend

**Version:** 1.0.0  
**Date:** March 11, 2026  
**Testing Framework:** flutter_test / integration_test  
**Platform:** Android · iOS · Linux  

---

## Table of Contents

1. [Testing Overview](#1-testing-overview)
2. [Test Environment Setup](#2-test-environment-setup)
3. [Test File Structure](#3-test-file-structure)
4. [Unit Tests](#4-unit-tests)
5. [Widget Tests](#5-widget-tests)
6. [Integration Tests](#6-integration-tests)
7. [Mocking Strategy](#7-mocking-strategy)
8. [How to Run Tests](#8-how-to-run-tests)
9. [Test Summary Table](#9-test-summary-table)

---

## 1. Testing Overview

### 1.1 Testing Strategy

The frontend test suite follows the Flutter-recommended **Test Pyramid**:

```
             ╱╲
            ╱  ╲
           ╱Integration╲   ← End-to-end UI flows on a real device/emulator
          ╱──────────────╲
         ╱                ╲
        ╱  Widget Tests    ╲  ← Widget rendering and interaction
       ╱────────────────────╲
      ╱                      ╲
     ╱      Unit Tests        ╲  ← Service logic, helpers, data mapping
    ╱____________________________╲
```

### 1.2 Testing Principles

- **Isolation** — each test is independent; shared state is reset in `setUp` / `tearDown`.
- **Repeatability** — plugin dependencies (TTS, Secure Storage, Connectivity) are replaced with in-memory mocks so tests produce the same result on any machine.
- **Offline-safe** — integration tests run with `connectivity` mocked to `none`, ensuring UI degrades gracefully without a live backend.
- **Readable names** — every `testWidgets` / `test` description states the expected behaviour in plain English.

### 1.3 Test Counts

| Suite | File | Tests |
|-------|------|------:|
| Unit — TTS Service | `test/tts_service_test.dart` | 10 |
| Unit — Remediation Page TTS | `test/remediation_page_tts_test.dart` | 11 |
| Widget | `test/widget_test.dart` | 1 |
| Integration | `integration_test/full_app_flow_test.dart` | 9 |
| **Total** | | **31** |

---

## 2. Test Environment Setup

### 2.1 Prerequisites

- Flutter SDK (stable channel, 3.x+)
- Dart SDK included with Flutter
- For integration tests on Android: connected device or running emulator
- For integration tests on Linux (desktop): Linux build dependencies installed

### 2.2 Install Dependencies

```bash
flutter pub get
```

### 2.3 Relevant `pubspec.yaml` dev dependencies

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  integration_test:
    sdk: flutter
```

---

## 3. Test File Structure

```
frontend/
├── test/                                  # Unit & widget tests
│   ├── widget_test.dart                   # Root app smoke test
│   ├── tts_service_test.dart              # TtsService unit tests
│   ├── remediation_page_tts_test.dart     # Remediation TTS unit tests
│   └── test_helpers/
│       └── mock_flutter_plugins.dart      # Plugin mocks for unit tests
│
└── integration_test/                      # Full-app integration tests
    ├── full_app_flow_test.dart            # End-to-end UI flow tests
    └── test_helpers/
        └── mock_flutter_plugins.dart      # Plugin mocks for integration tests
```

---

## 4. Unit Tests

### 4.1 TTS Service Tests — `test/tts_service_test.dart`

Tests the `TtsService` singleton that wraps `flutter_tts` for reading out remediation guidance in multiple Indian languages.

**Setup:**
- `SharedPreferences.setMockInitialValues({'preferred_language': 'en'})` seeds the language preference before each test.
- `setupMockFlutterPlugins()` / `tearDownMockFlutterPlugins()` register and remove platform channel mocks.

| # | Test Name | What It Verifies |
|---|-----------|-----------------|
| 1 | TtsService should be a singleton | Two separate `TtsService()` calls return the same instance |
| 2 | TtsService should initialize successfully | `initialize()` returns a `bool` without throwing |
| 3 | TtsService should handle speak with null text gracefully | `speak(null)` completes without exception |
| 4 | TtsService should handle speak with empty text gracefully | `speak('')` completes without exception |
| 5 | TtsService should handle speak with whitespace-only text gracefully | `speak('   ')` completes without exception |
| 6 | TtsService should handle stop gracefully | `stop()` completes without exception |
| 7 | TtsService should handle dispose gracefully | `dispose()` completes without exception |
| 8 | Language mapping should be correct | Locale codes (`en`→`en-US`, `hi`→`hi-IN`, etc.) map as expected |
| 9 | TtsService should handle multiple rapid calls gracefully | Three rapid `speak()` calls followed by `stop()` do not crash |
| 10 | TtsService should work with different languages in SharedPreferences | Service initialises successfully for `hi` and `kn` language preferences |

---

### 4.2 Remediation Page TTS Tests — `test/remediation_page_tts_test.dart`

Focuses on the TTS behaviours that are exercised specifically from the Remediation page (reading out prevention tips, risk factors, and treatment instructions).

**Setup:** Same mock strategy as 4.1; verified languages include `en`, `hi`, `ta`, `te`, `kn`, `ml`.

| # | Test Name | What It Verifies |
|---|-----------|-----------------|
| 1 | TTS service should be created properly | Instance is non-null; `isInitialized` starts as `false` |
| 2 | TTS service should initialize | `initialize()` returns a `bool` |
| 3 | TTS should handle speak without initialization gracefully | `speak()` before `initialize()` does not crash |
| 4 | TTS should speak text after initialization | Speak with a realistic remediation sentence after init |
| 5 | TTS should stop speaking | `isSpeaking` is `false` after calling `stop()` |
| 6 | TTS should handle null text gracefully | `speak(null)` after init does not crash |
| 7 | TTS should handle empty text gracefully | `speak('')` after init does not crash |
| 8 | TTS should handle whitespace-only text gracefully | `speak('   ')` after init does not crash |
| 9 | TTS should handle multiple rapid calls | Three sequential `speak()` calls for different sections then `stop()` |
| 10 | TTS should dispose properly | `dispose()` after init and speak does not crash |
| 11 | TTS should work with different language preferences | Initialises successfully for all six supported locales |

---

## 5. Widget Tests

### 5.1 Root App Widget — `test/widget_test.dart`

| # | Test Name | What It Verifies |
|---|-----------|-----------------|
| 1 | PlantDiseaseApp builds root app widget | `pumpWidget(PlantDiseaseApp())` renders without error; widget tree contains `PlantDiseaseApp` |

---

## 6. Integration Tests

File: `integration_test/full_app_flow_test.dart`

The integration tests run the full compiled Flutter app with all navigation wired up. Plugin channels (Secure Storage, Connectivity) are replaced with in-memory mocks so tests pass with no real device sensors or network.

**Global setup/teardown:**

```dart
setUpAll(setupIntegrationTestPluginMocks);
tearDownAll(tearDownIntegrationTestPluginMocks);
```

**Per-test reset:**

```dart
setUp(() {
  clearIntegrationSecureStorage();             // simulates logged-out state
  setIntegrationConnectivityResults(['none']); // no network
});
```

---

### 6.1 Group: Auth Integration Smoke

Tests covering the authentication screens without requiring a live backend.

#### Test 1 — App launches to login screen for logged-out user

**Goal:** Confirm the cold-start landing screen is the login page when no session token is stored.

**Steps:**
1. Pump `PlantDiseaseApp()`.
2. `pumpAndSettle()`.

**Assertions:**
- `find.text('Sign in')` — present (header / subtitle)
- `find.text('AgroScan')` — brand name visible
- `find.text('Login')` — submit button present
- `find.text('Create account')` — registration link present
- `find.text('Forgot password?')` — password-reset link present

---

#### Test 2 — Navigate from login to register and back

**Goal:** The "Create account" link opens the registration screen; back navigation returns to login.

**Steps:**
1. Pump `PlantDiseaseApp()` → login screen.
2. Tap `find.text('Create account').last`.
3. `pumpAndSettle()` — expect registration screen.
4. Call `tester.pageBack()`.
5. `pumpAndSettle()` — expect login screen.

**Assertions (registration screen):**
- `find.text('Join the community')` — registration heading
- `find.text('Full name')` — name field label

**Assertions (after back):**
- `find.text('Sign in')` and `find.text('Login')` — back on login

---

#### Test 3 — Navigate from login to forgot password and back

**Goal:** The "Forgot password?" link opens the reset-password screen; back navigation returns to login.

**Steps:**
1. Pump `PlantDiseaseApp()` → login screen.
2. Tap `find.text('Forgot password?')`.
3. `pumpAndSettle()` — expect reset screen.
4. Call `tester.pageBack()`.
5. `pumpAndSettle()` — expect login screen.

**Assertions (reset screen):**
- `find.text('Reset password')` — screen heading
- `find.text('Send reset code')` — action button

---

#### Test 4 — Login form shows validation errors for empty submit

**Goal:** Submitting the login form without entering credentials displays inline validation messages.

**Steps:**
1. Pump `PlantDiseaseApp()` → login screen.
2. Tap `find.text('Login')` without filling any field.
3. `pumpAndSettle()`.

**Assertions:**
- `find.text('Email is required.')` — email field error
- `find.text('Password is required.')` — password field error

---

### 6.2 Group: Whole App Integration Smoke

Tests covering post-login screens. The navigator is driven directly via `PlantDiseaseApp.navigatorKey` to skip the auth flow.

#### Test 5 — Home dashboard renders with offline-safe data flow

**Goal:** Home page renders all expected sections and handles the offline/empty-history state gracefully.

**Steps:**
1. Pump `PlantDiseaseApp()`.
2. Push `HomePage.routeName` via `navigatorKey`.
3. `pumpAndSettle()`.

**Assertions:**
- `find.text('AgroScan')` — app bar brand
- `find.text('Current weather')` — weather card
- `find.text('History analytics')` — analytics card
- `find.text('History records')` — history section header
- `find.text('No history yet.')` — empty-state message
- `find.byIcon(Icons.camera_alt)` — scan FAB
- `find.byIcon(Icons.smart_toy)` — chatbot FAB

---

#### Test 6 — Home → Chatbot flow renders assistant UI

**Goal:** Tapping the chatbot icon from the home screen opens the AI Farm Assistant page with the correct UI.

**Steps:**
1. Navigate to `HomePage`.
2. Tap `find.byIcon(Icons.smart_toy)`.
3. `pumpAndSettle()`.

**Assertions:**
- `find.byType(ChatbotPage)` — correct page type
- `find.text('AI Farm Assistant')` — page heading
- `find.text('Type your message...')` — input hint
- `find.byIcon(Icons.send)` — send button

---

#### Test 7 — Home → Crop capture flow renders crop grid

**Goal:** Tapping the camera icon opens the crop selection page showing the crop grid.

**Steps:**
1. Navigate to `HomePage`.
2. Tap `find.byIcon(Icons.camera_alt)`.
3. `pumpAndSettle()`.

**Assertions:**
- `find.byType(CropCapturePage)` — correct page type
- `find.text('Choose crop')` — section heading
- `find.text('Apple')` — crop tile visible
- `find.text('Corn')` — crop tile visible

---

#### Test 8 — Home profile menu opens profile page

**Goal:** The profile icon in the home app bar opens a menu; selecting "Profile" navigates to the profile page.

**Steps:**
1. Navigate to `HomePage`.
2. Tap `find.byIcon(Icons.account_circle)`.
3. `pumpAndSettle()`.
4. Tap `find.text('Profile')`.
5. `pumpAndSettle()`.

**Assertions:**
- `find.byType(ProfilePage)` — correct page type
- `find.text('Personal details')` — section heading
- `find.text('Update profile')` — action button

---

#### Test 9 — Diagnosis result opens remediation guide

**Goal:** Given a mock diagnosis result, the "View remediation" button navigates to the remediation guide.

**Setup data:**
```dart
final diagnosisResult = {
  'crop_type': 'apple',
  'disease_name': 'Apple Scab',
  'disease_id': 'apple_scab',
  'severity': 'medium',
  'confidence': 0.86,
  'is_healthy': false,
};
```

**Steps:**
1. Pump `DiagnosisResultPage(cropLabel: 'Apple', result: diagnosisResult)` inside a `ChangeNotifierProvider<AppLanguage>` + `MaterialApp` shell.
2. `pumpAndSettle()`.
3. Tap `find.text('View remediation')`.
4. `pumpAndSettle()`.

**Assertions (result page):**
- `find.byType(DiagnosisResultPage)` — result page rendered
- `find.text('Diagnosis result')` — page heading
- `find.text('View remediation')` — navigation button

**Assertions (after tap):**
- `find.text('Remediation guide')` — guide page heading

---

## 7. Mocking Strategy

### 7.1 Unit / Widget test mocks (`test/test_helpers/mock_flutter_plugins.dart`)

Registers `TestDefaultBinaryMessengerBinding` handlers for:

| Plugin | Mock Behaviour |
|--------|---------------|
| `flutter_tts` | All method calls return `1` (success) silently |
| `flutter_secure_storage` | In-memory `Map<String, String>` |
| `connectivity_plus` | Returns configurable list of connectivity types |

### 7.2 Integration test mocks (`integration_test/test_helpers/mock_flutter_plugins.dart`)

Same plugins but wired using `IntegrationTestWidgetsFlutterBinding` messenger. Adds helpers:

| Helper | Purpose |
|--------|---------|
| `clearIntegrationSecureStorage()` | Empties the in-memory storage (simulates logged-out) |
| `setIntegrationConnectivityResults(List<String>)` | Sets the connectivity type returned by the plugin |

---

## 8. How to Run Tests

### 8.1 Unit and Widget Tests

```bash
# Run all unit/widget tests
flutter test

# Run a specific test file
flutter test test/tts_service_test.dart
flutter test test/remediation_page_tts_test.dart
flutter test test/widget_test.dart

# Run with verbose output
flutter test --reporter expanded
```

### 8.2 Integration Tests

**Android (connected device or emulator):**
```bash
flutter test integration_test/full_app_flow_test.dart
```

**Linux (desktop):**
```bash
flutter test integration_test/full_app_flow_test.dart -d linux
```

**iOS (simulator):**
```bash
flutter test integration_test/full_app_flow_test.dart -d <device-id>
```

> **Note:** Integration tests require the app to compile and launch fully. Ensure `flutter doctor` reports no issues for the target platform before running.

### 8.3 Run All Tests at Once

```bash
# Unit + widget tests only (fast, no device needed)
flutter test

# Then integration (requires device/emulator)
flutter test integration_test/full_app_flow_test.dart -d linux
```

---

## 9. Test Summary Table

| # | File | Group | Test Name | Type |
|---|------|-------|-----------|------|
| 1 | `tts_service_test.dart` | TtsService Tests | TtsService should be a singleton | Unit |
| 2 | `tts_service_test.dart` | TtsService Tests | TtsService should initialize successfully | Unit |
| 3 | `tts_service_test.dart` | TtsService Tests | Handle speak with null text gracefully | Unit |
| 4 | `tts_service_test.dart` | TtsService Tests | Handle speak with empty text gracefully | Unit |
| 5 | `tts_service_test.dart` | TtsService Tests | Handle speak with whitespace-only text gracefully | Unit |
| 6 | `tts_service_test.dart` | TtsService Tests | Handle stop gracefully | Unit |
| 7 | `tts_service_test.dart` | TtsService Tests | Handle dispose gracefully | Unit |
| 8 | `tts_service_test.dart` | TtsService Tests | Language mapping should be correct | Unit |
| 9 | `tts_service_test.dart` | TtsService Tests | Handle multiple rapid calls gracefully | Unit |
| 10 | `tts_service_test.dart` | TtsService Tests | Work with different language preferences | Unit |
| 11 | `remediation_page_tts_test.dart` | Remediation Page TTS | TTS service should be created properly | Unit |
| 12 | `remediation_page_tts_test.dart` | Remediation Page TTS | TTS service should initialize | Unit |
| 13 | `remediation_page_tts_test.dart` | Remediation Page TTS | Handle speak without initialization gracefully | Unit |
| 14 | `remediation_page_tts_test.dart` | Remediation Page TTS | Speak text after initialization | Unit |
| 15 | `remediation_page_tts_test.dart` | Remediation Page TTS | Stop speaking | Unit |
| 16 | `remediation_page_tts_test.dart` | Remediation Page TTS | Handle null text gracefully | Unit |
| 17 | `remediation_page_tts_test.dart` | Remediation Page TTS | Handle empty text gracefully | Unit |
| 18 | `remediation_page_tts_test.dart` | Remediation Page TTS | Handle whitespace-only text gracefully | Unit |
| 19 | `remediation_page_tts_test.dart` | Remediation Page TTS | Handle multiple rapid calls | Unit |
| 20 | `remediation_page_tts_test.dart` | Remediation Page TTS | Dispose properly | Unit |
| 21 | `remediation_page_tts_test.dart` | Remediation Page TTS | Work with different language preferences | Unit |
| 22 | `widget_test.dart` | — | PlantDiseaseApp builds root app widget | Widget |
| 23 | `full_app_flow_test.dart` | Auth Integration Smoke | App launches to login screen for logged-out user | Integration |
| 24 | `full_app_flow_test.dart` | Auth Integration Smoke | Navigate from login to register and back | Integration |
| 25 | `full_app_flow_test.dart` | Auth Integration Smoke | Navigate from login to forgot password and back | Integration |
| 26 | `full_app_flow_test.dart` | Auth Integration Smoke | Login form shows validation errors for empty submit | Integration |
| 27 | `full_app_flow_test.dart` | Whole App Integration Smoke | Home dashboard renders with offline-safe data flow | Integration |
| 28 | `full_app_flow_test.dart` | Whole App Integration Smoke | Home → Chatbot flow renders assistant UI | Integration |
| 29 | `full_app_flow_test.dart` | Whole App Integration Smoke | Home → Crop capture flow renders crop grid | Integration |
| 30 | `full_app_flow_test.dart` | Whole App Integration Smoke | Home profile menu opens profile page | Integration |
| 31 | `full_app_flow_test.dart` | Whole App Integration Smoke | Diagnosis result opens remediation guide | Integration |
