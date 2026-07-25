import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'providers.dart';
import 'screens/auth_screen.dart';
import 'screens/capture_screen.dart';
import 'screens/home_screen.dart';
import 'screens/result_screen.dart';
import 'screens/splash_screen.dart';

GoRouter buildRouter(WidgetRef ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      if (auth.loading) return '/';
      final loggingIn = state.matchedLocation == '/auth';
      final atSplash = state.matchedLocation == '/';
      if (!auth.authenticated) return loggingIn ? null : '/auth';
      if (loggingIn || atSplash) return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/auth', builder: (_, __) => const AuthScreen()),
      GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
      GoRoute(path: '/capture', builder: (_, __) => const CaptureScreen()),
      GoRoute(
        path: '/result/:id',
        builder: (_, state) => ResultScreen(
          submissionId: int.parse(state.pathParameters['id']!),
        ),
      ),
    ],
  );
}
