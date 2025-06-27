#!/bin/bash

# Password Reset Feature - Git Commit and Push Script
echo "🚀 Deploying Password Reset Feature to GitHub..."

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository. Please run this from the project root."
    exit 1
fi

# Check git status
echo "📊 Current git status:"
git status

# Stage all password reset related files
echo "📁 Staging password reset feature files..."

# Backend files
git add backend/user_management_api.py
git add backend/email_service.py
git add backend/requirements.txt
git add backend/.env.example
git add backend/.env.production

# Frontend files
git add frontend/src/app/auth/forgot-password/page.tsx
git add frontend/src/app/auth/reset-password/page.tsx
git add frontend/src/components/ForgotPasswordForm.tsx
git add frontend/src/components/ResetPasswordForm.tsx
git add frontend/src/components/LoginForm.tsx
git add frontend/src/services/authApi.ts

# Documentation files
git add PASSWORD_RESET_IMPLEMENTATION_COMPLETE.md
git add DEPLOYMENT_PASSWORD_RESET_FEATURE.md
git add backend/MAILJET_INSTALLATION_COMPLETE.md

# Test files (optional - can be excluded from production)
git add backend/test_password_reset_debug.py

echo "✅ Files staged successfully!"

# Show what will be committed
echo "📋 Files to be committed:"
git diff --cached --name-only

# Commit with detailed message
echo "💾 Creating commit..."
git commit -m "feat: Add complete password reset functionality with email integration

🚀 Features Added:
- Password reset API endpoints (/auth/forgot-password, /auth/reset-password, /auth/verify-reset-token)
- Mailjet email service integration with professional templates
- Frontend React components for forgot/reset password flows
- Secure token generation with 24-hour expiration and single-use validation
- Updated login form with 'Forgot Password?' link
- Comprehensive error handling and user feedback
- Audit logging for security monitoring

🛠️ Technical Changes:
- Backend: Added mailjet-rest dependency and email service
- Frontend: New pages and components with form validation
- Database: Enhanced user session management
- Security: Token-based reset flow with proper validation

📚 Documentation:
- Complete implementation guide
- Deployment instructions
- Testing documentation

✅ Tested:
- Email delivery with real email addresses
- Complete user flow from request to password update
- Token security and expiration
- Error handling and edge cases

Ready for production deployment! 🎉"

# Push to GitHub
echo "🌐 Pushing to GitHub..."
read -p "Push to remote repository? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 GitHub repository updated with password reset feature"
else
    echo "⏸️ Push cancelled. Run 'git push origin main' when ready."
fi

echo "🎉 Password reset feature commit completed!"
echo "📝 Next steps:"
echo "   1. Review changes on GitHub"
echo "   2. Update production environment variables"
echo "   3. Deploy to VPS following DEPLOYMENT_PASSWORD_RESET_FEATURE.md"
echo "   4. Test email functionality in production"
