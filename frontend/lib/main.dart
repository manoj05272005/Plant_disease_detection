import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/auth/forgot_password_page.dart';
import 'screens/auth/login_page.dart';
import 'screens/auth/register_page.dart';
import 'screens/crop_capture_page.dart';
import 'screens/home_page.dart';
import 'screens/profile_page.dart';
import 'screens/chatbot_page.dart';
import 'services/app_localizations.dart';
import 'services/dio_client.dart';
import 'services/token_storage.dart';

void main() {
  runApp(const PlantDiseaseApp());
}

class PlantDiseaseApp extends StatelessWidget {
  const PlantDiseaseApp({super.key});

  static final navigatorKey = GlobalKey<NavigatorState>();

  @override
  Widget build(BuildContext context) {
    final baseScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF1B5E20),
      brightness: Brightness.light,
    );
    final colorScheme = baseScheme.copyWith(
      primary: const Color(0xFF1B5E20),
      secondary: const Color(0xFFFFB300),
      surface: const Color(0xFFF7F4EE),
      surfaceContainerHighest: const Color(0xFFEDE6DC),
      background: const Color(0xFFF5F1EA),
      error: const Color(0xFFD32F2F),
      onSurface: const Color(0xFF1F2A1F),
      onBackground: const Color(0xFF1F2A1F),
    );

    // Initialise the shared Dio client with the navigator key for auto-logout.
    DioClient.init(navigatorKey);

    return ChangeNotifierProvider(
      create: (_) => AppLanguage()..loadFromStorage(),
      child: MaterialApp(
        navigatorKey: navigatorKey,
        title: 'AgroScan',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: colorScheme,
          useMaterial3: true,
          fontFamily: 'serif',
          scaffoldBackgroundColor: colorScheme.background,
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.transparent,
            elevation: 0,
            surfaceTintColor: Colors.transparent,
            centerTitle: false,
            titleTextStyle: TextStyle(
              color: Color(0xFF1F2A1F),
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
            iconTheme: IconThemeData(color: Color(0xFF1F2A1F)),
          ),
          cardTheme: CardThemeData(
            color: const Color(0xFFFDFBF7),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: const Color(0xFFFDFBF7),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: Color(0xFFE0D8CC)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: Color(0xFF1B5E20), width: 1.6),
            ),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1B5E20),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              textStyle: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          outlinedButtonTheme: OutlinedButtonThemeData(
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFF1B5E20),
              side: const BorderSide(color: Color(0xFF1B5E20)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
          ),
          textButtonTheme: TextButtonThemeData(
            style: TextButton.styleFrom(
              foregroundColor: const Color(0xFF1B5E20),
              textStyle: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          snackBarTheme: const SnackBarThemeData(
            behavior: SnackBarBehavior.floating,
            backgroundColor: Color(0xFF1F2A1F),
            contentTextStyle: TextStyle(color: Colors.white),
          ),
        ),
        home: const AuthGate(),
        routes: {
          LoginPage.routeName: (_) => const LoginPage(),
          RegisterPage.routeName: (_) => const RegisterPage(),
          ForgotPasswordPage.routeName: (_) => const ForgotPasswordPage(),
          HomePage.routeName: (_) => const HomePage(),
          ProfilePage.routeName: (_) => const ProfilePage(),
          CropCapturePage.routeName: (_) => const CropCapturePage(),
          ChatbotPage.routeName: (_) => const ChatbotPage(),
        },
      ),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final storage = const TokenStorage();

    return FutureBuilder<String?>(
      future: storage.readAccessToken(),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final accessToken = snapshot.data;
        if (accessToken != null && accessToken.isNotEmpty) {
          return const HomePage();
        }

        return const LoginPage();
      },
    );
  }
}
