import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/api_client.dart';
import 'data/local_cache.dart';
import 'data/submissions_repository.dart';
import 'models/submission.dart';

/// Provided at app startup (see main.dart) with the initialised cache.
final localCacheProvider = Provider<LocalCache>((ref) {
  throw UnimplementedError('localCacheProvider must be overridden');
});

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient.create());

final submissionsRepositoryProvider = Provider<SubmissionsRepository>((ref) {
  return SubmissionsRepository(
    ref.watch(apiClientProvider),
    ref.watch(localCacheProvider),
  );
});

/// ---- Authentication ----
class AuthState {
  final bool loading;
  final bool authenticated;
  final String? displayName;

  const AuthState({
    this.loading = true,
    this.authenticated = false,
    this.displayName,
  });

  AuthState copyWith({bool? loading, bool? authenticated, String? displayName}) =>
      AuthState(
        loading: loading ?? this.loading,
        authenticated: authenticated ?? this.authenticated,
        displayName: displayName ?? this.displayName,
      );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._api) : super(const AuthState()) {
    _bootstrap();
  }

  final ApiClient _api;

  Future<void> _bootstrap() async {
    final token = await _api.token;
    if (token == null) {
      state = const AuthState(loading: false, authenticated: false);
      return;
    }
    try {
      final me = await _api.dio.get('/auth/me');
      state = AuthState(
        loading: false,
        authenticated: true,
        displayName: me.data['display_name'] as String?,
      );
    } on DioException {
      await _api.clearToken();
      state = const AuthState(loading: false, authenticated: false);
    }
  }

  Future<void> register(String email, String name, String password) async {
    final resp = await _api.dio.post('/auth/register', data: {
      'email': email,
      'display_name': name,
      'password': password,
    });
    await _api.saveToken(resp.data['access_token'] as String);
    state = AuthState(loading: false, authenticated: true, displayName: name);
  }

  Future<void> login(String email, String password) async {
    final resp = await _api.dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    await _api.saveToken(resp.data['access_token'] as String);
    await _bootstrap();
  }

  Future<void> logout() async {
    await _api.clearToken();
    state = const AuthState(loading: false, authenticated: false);
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(apiClientProvider));
});

/// ---- Submissions list ----
final submissionsListProvider =
    FutureProvider.autoDispose<List<Submission>>((ref) async {
  return ref.watch(submissionsRepositoryProvider).list();
});
