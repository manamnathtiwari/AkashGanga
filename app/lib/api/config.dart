import 'package:flutter/foundation.dart' show kIsWeb;

/// Backend base URL. Set at build time with:
///   flutter build apk --dart-define=API_BASE_URL=https://your-app.onrender.com/api
class AppConfig {
  static const String _override =
      String.fromEnvironment('API_BASE_URL', defaultValue: '');

  // Set this after deploying to Render — the URL shown in your Render dashboard.
  static const String _renderUrl = 'https://akashganga-api.onrender.com/api';

  static String get apiBaseUrl {
    if (_override.isNotEmpty) return _override;
    if (kIsWeb) return 'http://localhost:8000/api';
    return _renderUrl;
  }

  /// Base host (without /api) for building media URLs.
  static String get mediaBase => apiBaseUrl.replaceAll('/api', '');
}
