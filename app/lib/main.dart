import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'data/local_cache.dart';
import 'providers.dart';
import 'router.dart';
import 'theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final cache = LocalCache();
  await cache.init();

  runApp(
    ProviderScope(
      overrides: [
        localCacheProvider.overrideWithValue(cache),
      ],
      child: const AkashGangaApp(),
    ),
  );
}

class AkashGangaApp extends ConsumerWidget {
  const AkashGangaApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Rebuild the router when auth state changes.
    ref.watch(authControllerProvider);
    final router = buildRouter(ref);
    return MaterialApp.router(
      title: 'AkashGanga',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      routerConfig: router,
    );
  }
}
