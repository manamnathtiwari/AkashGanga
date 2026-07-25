import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../api/api_client.dart';
import '../providers.dart';
import '../theme.dart';

class CaptureScreen extends ConsumerStatefulWidget {
  const CaptureScreen({super.key});

  @override
  ConsumerState<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends ConsumerState<CaptureScreen> {
  final _picker = ImagePicker();
  final _urlController = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ApiClient.messageFrom(e))),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pick(ImageSource source) => _run(() async {
        final file = await _picker.pickImage(source: source, imageQuality: 95);
        if (file == null) return;
        final repo = ref.read(submissionsRepositoryProvider);
        final submission = await repo.submitFile(file.path, file.name);
        ref.invalidate(submissionsListProvider);
        if (mounted) context.pushReplacement('/result/${submission.id}');
      });

  Future<void> _submitUrl() => _run(() async {
        final url = _urlController.text.trim();
        if (url.isEmpty) return;
        final repo = ref.read(submissionsRepositoryProvider);
        final submission = await repo.submitUrl(url);
        ref.invalidate(submissionsListProvider);
        if (mounted) context.pushReplacement('/result/${submission.id}');
      });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Solve an image')),
      body: AbsorbPointer(
        absorbing: _busy,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _CaptureCard(
              icon: Icons.photo_library,
              title: 'Choose from gallery',
              subtitle: 'Pick an astrophoto you already took.',
              onTap: () => _pick(ImageSource.gallery),
            ),
            const SizedBox(height: 12),
            _CaptureCard(
              icon: Icons.camera_alt,
              title: 'Capture with camera',
              subtitle: 'Shoot the night sky right now.',
              onTap: () => _pick(ImageSource.camera),
            ),
            const SizedBox(height: 24),
            const Text('Or paste an image URL',
                style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 8),
            TextField(
              controller: _urlController,
              keyboardType: TextInputType.url,
              decoration: InputDecoration(
                hintText: 'https://...jpg',
                suffixIcon: IconButton(
                  icon: const Icon(Icons.send, color: AppTheme.star),
                  onPressed: _submitUrl,
                ),
              ),
              onSubmitted: (_) => _submitUrl(),
            ),
            if (_busy) ...[
              const SizedBox(height: 24),
              const Center(child: CircularProgressIndicator()),
            ],
          ],
        ),
      ),
    );
  }
}

class _CaptureCard extends StatelessWidget {
  const _CaptureCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(icon, size: 36, color: AppTheme.star),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 16)),
                    const SizedBox(height: 4),
                    Text(subtitle,
                        style: const TextStyle(color: Colors.white54, fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
