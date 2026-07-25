import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../models/submission.dart';
import '../providers.dart';
import '../theme.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final submissions = ref.watch(submissionsListProvider);
    final auth = ref.watch(authControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('AkashGanga'),
        actions: [
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/capture'),
        backgroundColor: AppTheme.accent,
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Solve image'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(submissionsListProvider.future),
        child: submissions.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => _EmptyState(
            icon: Icons.cloud_off,
            title: 'Could not load your images',
            subtitle: 'Pull to retry.',
          ),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                children: [
                  const SizedBox(height: 120),
                  _EmptyState(
                    icon: Icons.travel_explore,
                    title: 'Hi ${auth.displayName ?? 'stargazer'}!',
                    subtitle: 'Tap "Solve image" to map your first astrophoto.',
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              itemBuilder: (_, i) => _SubmissionTile(items[i]),
            );
          },
        ),
      ),
    );
  }
}

class _SubmissionTile extends StatelessWidget {
  const _SubmissionTile(this.submission);
  final Submission submission;

  @override
  Widget build(BuildContext context) {
    final title = submission.originalFilename ??
        submission.sourceUrl ??
        'Image #${submission.id}';
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: _StatusIcon(submission.status),
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(
          DateFormat.yMMMd().add_jm().format(submission.createdAt.toLocal()),
          style: const TextStyle(color: Colors.white38, fontSize: 12),
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/result/${submission.id}'),
      ),
    );
  }
}

class _StatusIcon extends StatelessWidget {
  const _StatusIcon(this.status);
  final String status;

  @override
  Widget build(BuildContext context) {
    switch (status) {
      case 'success':
        return const Icon(Icons.check_circle, color: AppTheme.success);
      case 'failed':
        return const Icon(Icons.error, color: AppTheme.danger);
      default:
        return const SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
    }
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.subtitle,
  });
  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: Colors.white24),
            const SizedBox(height: 16),
            Text(title, style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white54),
            ),
          ],
        ),
      ),
    );
  }
}
