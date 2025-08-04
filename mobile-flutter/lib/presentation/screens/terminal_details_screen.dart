import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import '../../core/theme/app_theme.dart';

class TerminalDetailsScreen extends StatelessWidget {
  const TerminalDetailsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Terminal Details',
          style: AppTheme.heading3,
        ),
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              PhosphorIcons.computer,
              size: 80,
              color: AppTheme.primaryBlue,
            ),
            SizedBox(height: 16),
            Text(
              'Terminal Details Coming Soon',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                color: AppTheme.neutral700,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'ATM Terminal Status & Information',
              style: TextStyle(
                fontSize: 16,
                color: AppTheme.neutral500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
