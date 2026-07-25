import 'package:dio/dio.dart';

import '../api/api_client.dart';
import '../models/submission.dart';
import 'local_cache.dart';

/// Fetches submissions from the API and mirrors solved ones into the cache.
class SubmissionsRepository {
  SubmissionsRepository(this._api, this._cache);

  final ApiClient _api;
  final LocalCache _cache;

  Future<List<Submission>> list({bool offline = false}) async {
    if (offline) return _cache.all();
    try {
      final resp = await _api.dio.get('/submissions');
      final items = (resp.data as List)
          .map((e) => Submission.fromJson(e as Map<String, dynamic>))
          .toList();
      // Cache the solved ones for offline access.
      await _cache.putAll(items.where((s) => s.isSolved).toList());
      return items;
    } on DioException {
      // Fall back to whatever we have cached.
      return _cache.all();
    }
  }

  Future<Submission> get(int id) async {
    try {
      final resp = await _api.dio.get('/submissions/$id');
      final submission = Submission.fromJson(resp.data as Map<String, dynamic>);
      if (submission.isSolved) await _cache.put(submission);
      return submission;
    } on DioException {
      final cached = _cache.get(id);
      if (cached != null) return cached;
      rethrow;
    }
  }

  Future<Submission> submitUrl(String url) async {
    final resp = await _api.dio.post('/submissions/url', data: {
      'url': url,
      'options': {},
    });
    return Submission.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<Submission> submitFile(String path, String filename) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(path, filename: filename),
      'publicly_visible': true,
    });
    final resp = await _api.dio.post('/submissions/upload', data: form);
    return Submission.fromJson(resp.data as Map<String, dynamic>);
  }
}
