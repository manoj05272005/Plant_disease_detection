import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:provider/provider.dart';

import 'package:frontend/main.dart';
import 'package:frontend/screens/chatbot_page.dart';
import 'package:frontend/screens/crop_capture_page.dart';
import 'package:frontend/screens/diagnosis_result_page.dart';
import 'package:frontend/screens/home_page.dart';
import 'package:frontend/screens/profile_page.dart';
import 'package:frontend/services/app_localizations.dart';

import 'test_helpers/mock_flutter_plugins.dart';

Widget _localizedShell(Widget child) {
  return ChangeNotifierProvider(
    create: (_) => AppLanguage(),
    child: MaterialApp(home: child),
  );
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(setupIntegrationTestPluginMocks);
  tearDownAll(tearDownIntegrationTestPluginMocks);

  setUp(() {
    clearIntegrationSecureStorage();
    setIntegrationConnectivityResults(<String>['none']);
  });

  group('Auth Integration Smoke', () {
    testWidgets('App launches to login screen for logged-out user', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      expect(find.text('Sign in'), findsWidgets);
      expect(find.text('AgroScan'), findsOneWidget);
      expect(find.text('Login'), findsOneWidget);
      expect(find.text('Create account'), findsOneWidget);
      expect(find.text('Forgot password?'), findsOneWidget);
    });

    testWidgets('Navigate from login to register and back', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Create account').last);
      await tester.pumpAndSettle();

      expect(find.text('Join the community'), findsOneWidget);
      expect(find.text('Full name'), findsOneWidget);

      await tester.pageBack();
      await tester.pumpAndSettle();

      expect(find.text('Sign in'), findsWidgets);
      expect(find.text('Login'), findsOneWidget);
    });

    testWidgets('Navigate from login to forgot password and back', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Forgot password?'));
      await tester.pumpAndSettle();

      expect(find.text('Reset password'), findsWidgets);
      expect(find.text('Send reset code'), findsOneWidget);

      await tester.pageBack();
      await tester.pumpAndSettle();

      expect(find.text('Sign in'), findsWidgets);
      expect(find.text('Login'), findsOneWidget);
    });

    testWidgets('Login form shows validation errors for empty submit', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Login'));
      await tester.pumpAndSettle();

      expect(find.text('Email is required.'), findsOneWidget);
      expect(find.text('Password is required.'), findsOneWidget);
    });
  });

  group('Whole App Integration Smoke', () {
    testWidgets('Home dashboard renders with offline-safe data flow', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      PlantDiseaseApp.navigatorKey.currentState!.pushNamed(HomePage.routeName);
      await tester.pumpAndSettle();

      expect(find.text('AgroScan'), findsOneWidget);
      expect(find.text('Current weather'), findsOneWidget);
      expect(find.text('History analytics'), findsOneWidget);
      expect(find.text('History records'), findsOneWidget);
      expect(find.text('No history yet.'), findsOneWidget);
      expect(find.byIcon(Icons.camera_alt), findsOneWidget);
      expect(find.byIcon(Icons.smart_toy), findsOneWidget);
    });

    testWidgets('Home -> Chatbot flow renders assistant UI', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      PlantDiseaseApp.navigatorKey.currentState!.pushNamed(HomePage.routeName);
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.smart_toy));
      await tester.pumpAndSettle();

      expect(find.byType(ChatbotPage), findsOneWidget);
      expect(find.text('AI Farm Assistant'), findsOneWidget);
      expect(find.text('Type your message...'), findsOneWidget);
      expect(find.byIcon(Icons.send), findsOneWidget);
    });

    testWidgets('Home -> Crop capture flow renders crop grid', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      PlantDiseaseApp.navigatorKey.currentState!.pushNamed(HomePage.routeName);
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.camera_alt));
      await tester.pumpAndSettle();

      expect(find.byType(CropCapturePage), findsOneWidget);
      expect(find.text('Choose crop'), findsOneWidget);
      expect(find.text('Apple'), findsOneWidget);
      expect(find.text('Corn'), findsOneWidget);
    });

    testWidgets('Home profile menu opens profile page', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const PlantDiseaseApp());
      await tester.pumpAndSettle();

      PlantDiseaseApp.navigatorKey.currentState!.pushNamed(HomePage.routeName);
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.account_circle));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Profile'));
      await tester.pumpAndSettle();

      expect(find.byType(ProfilePage), findsOneWidget);
      expect(find.text('Personal details'), findsOneWidget);
      expect(find.text('Update profile'), findsOneWidget);
    });

    testWidgets('Diagnosis result opens remediation guide', (
      WidgetTester tester,
    ) async {
      final diagnosisResult = <String, dynamic>{
        'crop_type': 'apple',
        'disease_name': 'Apple Scab',
        'disease_id': 'apple_scab',
        'severity': 'medium',
        'confidence': 0.86,
        'is_healthy': false,
      };

      await tester.pumpWidget(
        _localizedShell(
          DiagnosisResultPage(cropLabel: 'Apple', result: diagnosisResult),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(DiagnosisResultPage), findsOneWidget);
      expect(find.text('Diagnosis result'), findsOneWidget);
      expect(find.text('View remediation'), findsOneWidget);

      await tester.tap(find.text('View remediation'));
      await tester.pumpAndSettle();

      expect(find.text('Remediation guide'), findsOneWidget);
    });
  });
}
