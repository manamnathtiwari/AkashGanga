import 'package:flutter/material.dart';

/// AkashGanga dark "night sky" theme.
class AppTheme {
  static const Color deepSpace = Color(0xFF0A0E21);
  static const Color panel = Color(0xFF141A3C);
  static const Color star = Color(0xFF6C7BFF);
  static const Color accent = Color(0xFF9B5DE5);
  static const Color success = Color(0xFF4CE0B3);
  static const Color danger = Color(0xFFFF5D73);

  static ThemeData get dark {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: deepSpace,
      colorScheme: base.colorScheme.copyWith(
        primary: star,
        secondary: accent,
        surface: panel,
        error: danger,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: deepSpace,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardTheme(
        color: panel,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: panel,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: star,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }
}
